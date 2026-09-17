"""同期Embeddingと非同期Embeddingを比較するDay73のベンチマーク。"""

import asyncio
from time import perf_counter

from openai import AsyncOpenAI, OpenAI

from bm25_search import DOCUMENTS, Document
from hybrid_rrf_search import EMBEDDING_MODEL, build_document_embeddings


async def get_embedding_async(
    client: AsyncOpenAI,
    text: str,
) -> list[float]:
    """1つの文書を非同期でEmbeddingする。"""

    # AsyncOpenAIとawaitを使うことで、APIの応答待ち中に
    # event loopが別のEmbeddingリクエストを処理できる。
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )

    return response.data[0].embedding


async def build_document_embeddings_async(
    client: AsyncOpenAI,
    documents: list[Document],
) -> dict[str, list[float]]:
    """複数文書のEmbedding APIを並列に呼び出す。"""

    # 各文書のEmbeddingは他の文書の結果に依存しないため、並列実行できる。
    embeddings = await asyncio.gather(
        *(
            get_embedding_async(
                client=client,
                text=document.text,
            )
            for document in documents
        )
    )

    # gatherの結果と元の文書をzipし、既存RAGと同じ辞書形式へ戻す。
    return {
        document.document_id: embedding
        for document, embedding in zip(documents, embeddings)
    }


def benchmark_sync(
    client: OpenAI,
    documents: list[Document],
) -> tuple[dict[str, list[float]], float]:
    """既存の同期Embedding処理と経過時間を計測する。"""

    started_at = perf_counter()

    # 既存のProduction RAGで使っている同期関数をそのまま再利用する。
    embeddings = build_document_embeddings(
        client=client,
        documents=documents,
    )

    elapsed_seconds = perf_counter() - started_at
    return embeddings, elapsed_seconds


async def benchmark_async(
    client: AsyncOpenAI,
    documents: list[Document],
) -> tuple[dict[str, list[float]], float]:
    """非同期Embedding処理と経過時間を計測する。"""

    started_at = perf_counter()

    embeddings = await build_document_embeddings_async(
        client=client,
        documents=documents,
    )

    elapsed_seconds = perf_counter() - started_at
    return embeddings, elapsed_seconds


async def run_async_benchmark(
    documents: list[Document],
) -> tuple[dict[str, list[float]], float]:
    """非同期クライアントの生成から終了までを同じイベントループで管理する。"""

    # AsyncOpenAIをasyncio.runの外で作ると、接続のライフサイクルが
    # 別イベントループにまたがる可能性があるため、ここで生成する。
    client = AsyncOpenAI()
    try:
        return await benchmark_async(
            client=client,
            documents=documents,
        )
    finally:
        # 非同期HTTP接続を、同じイベントループ内で明示的に閉じる。
        await client.close()


def print_benchmark_result(
    documents: list[Document],
    sync_embeddings: dict[str, list[float]],
    sync_elapsed: float,
    async_embeddings: dict[str, list[float]],
    async_elapsed: float,
) -> None:
    """同期・非同期の結果を比較し、同じEmbedding結果か確認する。"""

    # 実行方式を変えても、同じ文書IDとベクトル次元数になる必要がある。
    same_document_ids = set(sync_embeddings) == set(async_embeddings)
    same_dimensions = all(
        len(sync_embeddings[document.document_id])
        == len(async_embeddings[document.document_id])
        for document in documents
    )

    print("=" * 60)
    print("Embedding同期・非同期比較")
    print(f"文書数: {len(documents)}")
    print(f"同期処理時間: {sync_elapsed:.2f}秒")
    print(f"非同期処理時間: {async_elapsed:.2f}秒")

    if async_elapsed > 0:
        print(f"時間比（同期 / 非同期）: {sync_elapsed / async_elapsed:.2f}倍")

    print(f"文書ID一致: {same_document_ids}")
    print(f"Embedding次元数一致: {same_dimensions}")
    print(f"Embedding API呼び出し数（各方式）: {len(documents)}回")
    print("費用は呼び出し回数とToken数で決まり、非同期化だけでは減少しない")


def main() -> None:
    """既存文書を使い、同期Embeddingと非同期Embeddingを比較する。"""

    # 同じ文書集合・同じモデルで比較し、方式以外の条件を揃える。
    sync_embeddings, sync_elapsed = benchmark_sync(
        client=OpenAI(),
        documents=DOCUMENTS,
    )

    async_embeddings, async_elapsed = asyncio.run(
        run_async_benchmark(documents=DOCUMENTS)
    )

    print_benchmark_result(
        documents=DOCUMENTS,
        sync_embeddings=sync_embeddings,
        sync_elapsed=sync_elapsed,
        async_embeddings=async_embeddings,
        async_elapsed=async_elapsed,
    )


if __name__ == "__main__":
    main()
