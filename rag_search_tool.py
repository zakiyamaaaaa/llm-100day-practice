import json
from typing import Any
from openai import OpenAI
from pydantic import BaseModel, Field
from bm25_search import DOCUMENTS, Document
from hybrid_rag_pipeline import (
    RetrievalContext,
    build_retrieval_context,
    run_pipeline
)
from tool_registry_allowlist import (
    SearchDocumentsArguments,
    ToolExecutionResult,
    ToolRegistry
)

class SearchHit(BaseModel):
    """
    RAG検索で見つかった１文書分の結果
    
    sourceを必ず含めることで、あとから引用元を追跡できるようにする
    """
    
    # 引用に使う文書ID
    source: str
    title: str
    # LLMが回答のこんきょとして読む本文
    text: str
    
    # Rerankerによる関連度
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
    )
    
class SearchToolOutput(BaseModel):
    """
    search_documents Toolの戻り値
    
    results: LLMが内容を読むための検索結果
    sources: 引用元だけを簡単に取得するための文書ID一覧
    """
    
    # 実行された検索質問
    query: str
    #　関連度順に並んだ検索結果
    results: list[SearchHit]
    
    # 検索結果に含まれる文書ID
    sources: list[str]
    
    
def maker_search_handler(client: OpenAI, retrieval_context: RetrievalContext):
    """
    Production RAGをToolのhandlerへ変換する
    
    
    handlerはTOolRegistryから呼び出される関数
    この関数を使うことで、RAG検索に必要なclientとretrieval_contextをあらかじめ保持できる
    """
    
    def search_documents(arguments: BaseModel) -> dict[str, Any]:
        """
        Agentから呼び出されるsearch_documents Tool
        
        処理順序：
        1. 引数がSearchDocumentsArgumentsか確認
        2. 既存のRAG Pipelineを実行
        3. 文書IDから本文とタイトルを取得
        4. sourceつきJSONに変換
        """
        
        # Registryが正しいPydanticモデルを渡していることを確認する
        if not isinstance(arguments, SearchDocumentsArguments):
            raise ValueError("arguments must be an instance of SearchDocumentsArguments")
        
        # 既存のProduction RAGを呼び出す
        # ここでBM25, Vector, RRF, Rerankerが実行される
        pipeline_result = run_pipeline(
            client=client,
            context = retrieval_context,
            query = arguments.query,
            candidate_count=arguments.top_k,
        )
        
        search_hits: list[SearchHit] = []
        
        # Reranker後の結果をToolの戻り値に変換する
        for rerank_item in pipeline_result.reranked_results:
            # Rerankerが返した文書IDから本文を取得する
            document = retrieval_context.documents_by_id.get(rerank_item.document_id)
            
            # IDに対応する本文がない場合は、不完全な検索結果としてエラーにする
            if document is None:
                raise ValueError(f"Document with ID {rerank_item.document_id} not found in retrieval context")
            
            # 文書ID・タイトル・本文・関連度を保持する
            search_hits.append(
                SearchHit(
                    source=document.document_id,
                    title = document.title,
                    text = document.text,
                    relevance_score=rerank_item.relevance_score
                )
            )
        # 結果に含まれる文書IDからsourcesを作る
        # 別途手入力せず、resultsから生成することで不整合を防ぐ
        sources = [search_hit.source for search_hit in search_hits]
        
        # Toolの戻り値をPydanticで構造化する
        tool_output = SearchToolOutput(
            query=arguments.query,
            results=search_hits,
            sources=sources
        )
        
        # ToolRegistryが扱える辞書へ変換する
        return tool_output.model_dump()
    return search_documents


def build_rag_tool_registry(client: OpenAI, retrieval_context: RetrievalContext)->ToolRegistry:
    """
    RAG検索Toolだけを登録したRegistryを作る
    
    Day59のbuild_registry()にはモックのsearch_documentsが登録されているため、
    今回は新しいRegistryを作って、本物のRAG handlerを登録する
    """
    
    registry = ToolRegistry()
    
    registry.register(
        name="search_documents",
        description="RAG検索を実行するTool。質問に関連する文書を検索し、引用元を返す。",
        arguments_model=SearchDocumentsArguments,
        handler=maker_search_handler(client, retrieval_context),
    )
    
    return registry

def execute_search_tool(registry: ToolRegistry, query: str, top_k: int,)->ToolExecutionResult:
    """
    search_docuemts Toolを実行する
    LLMが生成した場合と同じように、引数をJSON文字列にしてRegistryにわたす
    """
    
    raw_arguments = json.dumps(
        {
            "query" : query,
            "top_k" : top_k,
        },
        ensure_ascii=False
    )
    
    return registry.execute(
        tool_name="search_documents",
        raw_arguments=raw_arguments,
    )
    
    

def print_search_result(
    result: ToolExecutionResult,
) -> None:
    """
    Toolの実行結果を表示する。

    エラーの場合はエラー情報だけを表示し、
    成功時はsource付き検索結果を表示する。
    """

    print("\n[Tool実行結果]")
    print(f"status: {result.status}")
    print(f"tool_name: {result.tool_name}")

    if result.status == "error":
        print(f"error_type: {result.error_type}")
        print(f"error_message: {result.error_message}")
        return

    payload = result.result or {}

    print(f"query: {payload['query']}")
    print(f"sources: {payload['sources']}")

    print("\n[検索結果]")

    for rank, item in enumerate(
        payload["results"],
        start=1,
    ):
        print(f"{rank}位")
        print(f"source: {item['source']}")
        print(f"title: {item['title']}")
        print(f"score: {item['relevance_score']:.2f}")
        print(f"text: {item['text']}")
        
        
        
def main()-> None:
    """RAG検索Toolを構築して、１件の質問を実行する
    """
    
    client = OpenAI()
    
    # BM25Indexと文書Embeddingを一度だけ作成する
    retrieval_context = build_retrieval_context(
        client=client,
        documents=DOCUMENTS,
    )
    
    # Production RAGをToolとして登録する
    registry = build_rag_tool_registry(
        client=client,
        retrieval_context=retrieval_context,
    )
    
    # Agentが質問した想定でToolを実行する
    result = execute_search_tool(
        registry=registry,
        query="様式打４号の提出先はどこですか",
        top_k=3,
    )
    
    print_search_result(result=result)
    
if __name__ == "__main__":
    main()
        
