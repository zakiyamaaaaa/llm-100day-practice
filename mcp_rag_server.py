from typing import Any

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, Field

from bm25_search import DOCUMENTS, BM25Index


# MCP Serverは、既存のRAG機能を外部のMCP Clientへ公開する窓口になる
mcp = MCPServer("RAG Search Server")

# 文書とBM25インデックスはServer起動時に一度だけ準備する
index = BM25Index(DOCUMENTS)
documents_by_id = {
    document.document_id: document
    for document in DOCUMENTS
}


class SearchHit(BaseModel):
    """MCP Toolが返す検索結果1件分。"""

    source: str = Field(description="文書ID")
    title: str = Field(description="文書タイトル")
    text: str = Field(description="文書本文")
    score: float = Field(description="BM25スコア")


class SearchResponse(BaseModel):
    """RAG検索Toolの戻り値。"""

    query: str = Field(description="実行した検索Query")
    results: list[SearchHit] = Field(description="関連度順の検索結果")


@mcp.tool()
def search_documents(query: str, top_k: int = 3) -> dict[str, Any]:
    """既存のBM25 RAG検索をMCP Toolとして実行する。"""

    # Toolの引数をサーバー側でも検証し、安全な範囲に制限する
    if not query.strip():
        raise ValueError("query must not be empty")

    if not 1 <= top_k <= 3:
        raise ValueError("top_k must be between 1 and 3")

    # MCP固有の検索処理は書かず、既存のBM25Indexを再利用する
    search_results = index.search(query=query, top_k=top_k)

    response = SearchResponse(
        query=query,
        results=[
            SearchHit(
                source=result.document.document_id,
                title=result.document.title,
                text=result.document.text,
                score=result.score,
            )
            for result in search_results
        ],
    )

    # PydanticモデルをMCPが扱える辞書へ変換する
    return response.model_dump()


@mcp.resource("rag://documents/{document_id}")
def read_document(document_id: str) -> str:
    """指定された文書IDの本文をMCP Resourceとして読み取る。"""

    # URIから受け取ったIDを、許可された文書一覧から検索する
    document = documents_by_id.get(document_id)

    if document is None:
        raise ValueError(f"Document not found: {document_id}")

    # Resourceは、特定文書の本文を読み取り専用で返す
    return (
        f"source: {document.document_id}\n"
        f"title: {document.title}\n"
        f"text: {document.text}"
    )


def main() -> None:
    """MCP Serverをstdioで起動する。"""

    # MCP Clientからのlist/call/read要求を標準入出力で受け付ける
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
