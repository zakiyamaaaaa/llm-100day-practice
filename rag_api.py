"""既存のProduction RAGをHTTP APIとして公開するDay71の最小実装。"""
import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import Query
from fastapi.responses import StreamingResponse

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

from answer_with_citations import GroundedAnswer
from bm25_search import DOCUMENTS
from document_lifecycle_ingest import (
    build_versioned_chunks,
    create_collection as create_ingest_collection,
    sync_file,
)
from hybrid_rag_pipeline import RetrievalContext
from productioin_rag_v1 import build_application, run_query


INGEST_DIRECTORY = Path("api_ingested_docs")


class QueryRequest(BaseModel):
    """クライアントから受け取る質問の契約。"""

    # 空文字や極端に長い質問を、RAG検索より前に拒否する。
    question: str = Field(min_length=1, max_length=500)

    # 検索候補数をAPIから指定できるようにする。
    # 上限を設け、過剰な検索・Reranker処理を防ぐ。
    top_k: int = Field(default=3, ge=1, le=5)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        """空白だけの質問を、Embeddingや検索へ渡さない。"""

        cleaned = value.strip()
        if not cleaned:
            raise ValueError("questionは空白以外の文字を1文字以上指定してください")
        return cleaned


class QueryResponse(BaseModel):
    """API利用者へ返すRAG回答の契約。"""

    # 回答可能かどうかを、HTTPステータスとは別に表す。
    status: Literal["answered", "refused"]
    answer: str | None = None
    sources: list[str] = Field(default_factory=list)
    refusal_reason: str | None = None


class IngestRequest(BaseModel):
    """クライアントから受け取る文書登録の契約。"""

    # パスではなく、サーバーが管理するファイル名だけを受け取る。
    source: str = Field(min_length=1, max_length=100)

    # Embedding前に、空本文や極端に大きい本文を拒否する。
    content: str = Field(min_length=1, max_length=20_000)

    # 省略時は本文先頭の【見出し】、なければファイル名から推測される。
    section: str | None = Field(default=None, max_length=100)

    @field_validator("source")
    @classmethod
    def source_must_be_safe_filename(cls, value: str) -> str:
        """任意のサーバーパスを受け取らないように検証する。"""

        cleaned = value.strip()
        path = Path(cleaned)

        # sourceはファイル名だけに限定し、../などのパス移動を防ぐ。
        if (
            path.name != cleaned
            or "\\" in cleaned
            or path.suffix.lower() != ".txt"
        ):
            raise ValueError("sourceは.txt拡張子のファイル名だけを指定してください")

        return cleaned

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        """空白だけの本文をChunkingやEmbeddingへ渡さない。"""

        cleaned = value.strip()
        if not cleaned:
            raise ValueError("contentは空白以外の文字を1文字以上指定してください")
        return cleaned

    @field_validator("section")
    @classmethod
    def section_must_be_single_line(cls, value: str | None) -> str | None:
        """Metadataとして扱うsectionに改行を混ぜない。"""

        if value is None:
            return None

        cleaned = value.strip()
        if not cleaned or "\n" in cleaned or "\r" in cleaned:
            raise ValueError("sectionは改行を含まない文字列で指定してください")
        return cleaned


class IngestResponse(BaseModel):
    """文書登録の結果を返すAPI契約。"""

    # inserted/updated/unchangedは、Ingest処理の業務上の結果を表す。
    status: Literal["inserted", "updated", "unchanged"]
    source: str
    chunk_count: int = Field(ge=1)


@dataclass
class Application:
    """複数のHTTPリクエストで再利用するRAG依存関係。"""

    client: OpenAI
    retrieval_context: RetrievalContext


app = FastAPI(
    title="Production RAG API",
    version="1.0.0",
    description="既存のRAG PipelineをHTTP APIとして提供するDay71デモ",
)

_application: Application | None = None
_ingest_collection: Any | None = None


def get_application() -> Application:
    """RAGの重い初期化を一度だけ行い、以降のリクエストで再利用する。"""

    global _application

    if _application is None:
        # 文書Embeddingは質問ごとに作り直すと、API費用と遅延が増える。
        # そのため、最初の/query呼び出し時に一度だけ初期化する。
        client = OpenAI()
        retrieval_context = build_application(client)
        _application = Application(
            client=client,
            retrieval_context=retrieval_context,
        )

    return _application


def convert_response(answer: GroundedAnswer) -> QueryResponse:
    """内部のGroundedAnswerを、公開APIのレスポンス型へ変換する。"""

    # API専用モデルを挟むことで、内部モデルの変更を外部契約へ直接波及させない。
    return QueryResponse.model_validate(answer.model_dump())


def get_ingest_collection() -> Any:
    """文書登録用のVector DB Collectionを一度だけ初期化する。"""

    global _ingest_collection

    if _ingest_collection is None:
        # CollectionとEmbedding関数をリクエストごとに作り直さない。
        _ingest_collection = create_ingest_collection()

    return _ingest_collection


def build_stored_content(request: IngestRequest) -> str:
    """API入力を、既存のMetadata付きIngestが扱える本文へ変換する。"""

    # sectionを明示された場合、既存のsection抽出規約に合わせて見出し化する。
    if request.section and not request.content.startswith("【"):
        return f"【{request.section}】\n{request.content}"

    return request.content

@app.get("/health")
def health() -> dict[str, str]:
    """APIが起動しているかを確認する。LLM APIは呼び出さない。"""

    return {
        "status": "ok",
        "service": "production-rag-api",
    }


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    """質問を既存RAGへ渡し、回答・引用・拒否理由をJSONで返す。"""

    application = get_application()

    # RAGのBM25、Vector、RRF、Reranker、Context、LLM回答を既存部品へ委譲する。
    answer = run_query(
        client=application.client,
        retrieval_context=application.retrieval_context,
        query=request.question,
        candidate_count=request.top_k,
    )

    return convert_response(answer)

@app.get("/query/stream")
async def query_stream(
    question: str = Query(..., min_length=1, max_length=500),
) -> StreamingResponse:
    """SSE形式でEventを逐次返す。"""

    return StreamingResponse(
        stream_demo_events(question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )

def format_sse(event_name: str, payload: dict) -> str:
    """データをSSE形式の文字列へ変換する。"""

    # Eventの種類を指定する。
    # 例：progress、token、done
    data = json.dumps(payload, ensure_ascii=False)

    # 空行までが1つのSSE Eventになる。
    return f"event: {event_name}\ndata: {data}\n\n"


async def stream_demo_events(question: str) -> AsyncIterator[str]:
    """SSE Eventを順番に生成する。"""

    yield format_sse(
        "progress",
        {"message": "質問を受け付けました"},
    )

    await asyncio.sleep(0.5)

    yield format_sse(
        "progress",
        {"message": "関連文書を検索しています"},
    )

    await asyncio.sleep(0.5)

    # 今回はStreamingの構造確認用に、回答断片を固定している。
    chunks = [
        "様式第4号の",
        "提出先は、",
        "セキュリティチームです。",
    ]

    for chunk in chunks:
        # 回答断片を1つずつクライアントへ送る。
        yield format_sse(
            "token",
            {"text": chunk},
        )

        await asyncio.sleep(0.5)

    # 全チャンク送信後、完了を通知する。
    yield format_sse(
        "done",
        {
            "status": "answered",
            "sources": ["doc_2"],
        },
    )

@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    """文書を保存し、Chunking・Hash判定・Vector DB同期を実行する。"""

    # sourceは検証済みのファイル名なので、管理下のディレクトリから外へ出ない。
    INGEST_DIRECTORY.mkdir(parents=True, exist_ok=True)
    file_path = INGEST_DIRECTORY / request.source

    # APIで受け取った本文をサーバー管理下へ保存する。
    file_path.write_text(
        build_stored_content(request),
        encoding="utf-8",
    )

    collection = get_ingest_collection()

    try:
        # Chunk数を先に計算し、レスポンスに登録単位の情報を含める。
        chunks = build_versioned_chunks(file_path)

        # Day51の同期処理を再利用する。
        # 同じHashならEmbeddingを作らず、更新時は古いChunkを削除する。
        sync_status = sync_file(
            collection=collection,
            file_path=file_path,
        )
    except Exception as error:
        # 内部エラーの詳細を外部へ漏らさず、APIエラーとして返す。
        raise HTTPException(
            status_code=500,
            detail="文書のIngest処理に失敗しました",
        ) from error

    return IngestResponse(
        status=sync_status,
        source=request.source,
        chunk_count=len(chunks),
    )


def main() -> None:
    """Uvicornから起動する方法を表示する。"""

    print("uv run uvicorn rag_api:app --reload")


if __name__ == "__main__":
    main()
