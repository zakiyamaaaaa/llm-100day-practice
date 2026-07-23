from dataclasses import dataclass
from openai import OpenAI
from bm25_search import BM25Index, DOCUMENTS, Document
from hybrid_rrf_search import build_document_embeddings, calculate_rrf_scores, search_by_vector, sort_rrf_scores
from llm_reranker import rerank_documents, RerankItem

@dataclass(frozen=True)
class RetrievalContext:
    bm25_index: BM25Index
    document_embeddings: dict[str, list[float]]
    documents_by_id: dict[str, Document]

@dataclass(frozen=True)
class PipelineResult:
    query: str
    rrf_ranking: list[tuple[str, float]]
    reranked_results: list[RerankItem]
    

def build_retrieval_context(client: OpenAI, documents: list[Document]) -> RetrievalContext:
    bm25_index = BM25Index(documents)
    
    document_embeddings = build_document_embeddings(
        client=client,
        documents=documents,
    )
    
    documents_by_id = {
        document.document_id: document
        for document in documents
    }
    
    return RetrievalContext(
        bm25_index=bm25_index,
        document_embeddings=document_embeddings,
        documents_by_id=documents_by_id,
    )
    
def retrieve_candidates(client: OpenAI, context: RetrievalContext, query: str, candidate_count: int = 3,) -> tuple[list[Document], list[tuple[str, float]]]:
    bm25_results = context.bm25_index.search(
        query=query,
        top_k=candidate_count,
    )

    bm25_ranking = [
        result.document.document_id
        for result in bm25_results
    ]

    vector_results = search_by_vector(
        client=client,
        query=query,
        document_embeddings=context.document_embeddings,
        top_k=candidate_count,
    )

    vector_ranking = [
        document_id
        for document_id, score in vector_results
    ]

    rrf_scores = calculate_rrf_scores(
        rankings=[
            bm25_ranking,
            vector_ranking,
        ]
    )

    rrf_ranking = sort_rrf_scores(rrf_scores)

    candidate_ids = [
        document_id
        for document_id, score in rrf_ranking[:candidate_count]
    ]

    candidates = [
        context.documents_by_id[document_id]
        for document_id in candidate_ids
    ]

    return candidates, rrf_ranking

def run_pipeline(
    client: OpenAI,
    context: RetrievalContext,
    query: str,
    candidate_count: int = 3,
) -> PipelineResult:
    candidates, rrf_ranking = retrieve_candidates(
        client=client,
        context=context,
        query=query,
        candidate_count=candidate_count,
    )

    reranked_results = rerank_documents(
        client=client,
        query=query,
        candidates=candidates,
    )

    return PipelineResult(
        query=query,
        rrf_ranking=rrf_ranking,
        reranked_results=reranked_results,
    )


def print_pipeline_result(
    result: PipelineResult,
    documents_by_id: dict[str, Document],
) -> None:
    print("=" * 60)
    print(f"質問: {result.query}")

    print("\n[RRFランキング]")

    for rank, (document_id, score) in enumerate(
        result.rrf_ranking,
        start=1,
    ):
        document = documents_by_id[document_id]

        print(
            f"{rank}位: "
            f"{document_id} "
            f"score={score:.5f} "
            f"{document.title}"
        )

    print("\n[リランキング後]")

    for rank, rerank_item in enumerate(
        result.reranked_results,
        start=1,
    ):
        document = documents_by_id[
            rerank_item.document_id
        ]

        print(
            f"{rank}位: "
            f"{rerank_item.document_id} "
            f"score={rerank_item.relevance_score:.2f} "
            f"{document.title}"
        )

        print(f"理由: {rerank_item.reason}")


def main() -> None:
    client = OpenAI()

    context = build_retrieval_context(
        client=client,
        documents=DOCUMENTS,
    )

    query = "出張費用の申請書はどこに提出しますか？"

    result = run_pipeline(
        client=client,
        context=context,
        query=query,
        candidate_count=3,
    )

    print_pipeline_result(
        result=result,
        documents_by_id=context.documents_by_id,
    )


if __name__ == "__main__":
    main()
