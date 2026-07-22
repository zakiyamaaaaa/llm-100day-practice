from dataclasses import dataclass
from math import sqrt
from openai import OpenAI
from bm25_search import BM25Index, DOCUMENTS, Document

EMBEDDING_MODEL = "text-embedding-3-small"
RRF_K = 60

EVALUATION_CASES = [
    {
        "query": "様式第4号の提出先はどこですか？",
        "expected_id": "doc_2",
    },
    {
        "query": "社外PCを外に持ち出すときの手続きは？",
        "expected_id": "doc_2",
    },
    {
        "query": "会社で読む本を購入したい。誰の承認が必要ですか？",
        "expected_id": "doc_3",
    },
    {
        "query": "出張費用の申請書はどこに提出しますか？",
        "expected_id": "doc_3",
    },
]

@dataclass(frozen=True)
class EvaluationResult:
    query: str
    expected_id: str
    bm25_ranking: list[str]
    vector_ranking: list[str]
    rrf_ranking: list[tuple[str,float]]
    
def get_embedding(client: OpenAI, text: str) -> list[float]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text,)
    return response.data[0].embedding

def build_document_embeddings(client: OpenAI, documents: list[Document],) -> dict[str, list[float]]:
    embeddings = {}
    
    for document in documents:
        embeddings[document.document_id] = get_embedding(client=client, text=document.text)
    
    return embeddings

def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    dot_product = sum(
        value_a * value_b
        for value_a, value_b in zip(vector_a, vector_b)
    )

    norm_a = sqrt(
        sum(value * value for value in vector_a)
    )

    norm_b = sqrt(
        sum(value * value for value in vector_b)
    )

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)

def search_by_vector(
    client: OpenAI,
    query: str,
    document_embeddings: dict[str, list[float]],
    top_k: int = 3,
) -> list[tuple[str, float]]:
    query_embedding = get_embedding(
        client=client,
        text=query,
    )

    scored_documents = []

    for document_id, document_embedding in (
        document_embeddings.items()
    ):
        score = cosine_similarity(
            query_embedding,
            document_embedding,
        )

        scored_documents.append(
            (document_id, score)
        )

    scored_documents.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return scored_documents[:top_k]

def calculate_rrf_scores(rankings: list[list[str]], k: int = RRF_K,)->dict[str, float]:
    rrf_scores: dict[str, float] = {}
    
    for ranking in rankings:
        for rank, document_id in enumerate(ranking, start=1):
            rrf_scores[document_id] = (rrf_scores.get(document_id,0.0)) + 1.0/(k+rank)
    return rrf_scores

def sort_rrf_scores(rrf_scores: dict[str, float],) -> list[tuple[str, float]]:
    return sorted(rrf_scores.items(),key=lambda item: item[1], reverse=True,)

def evaluate_case(client: OpenAI, bm25_index: BM25Index, document_embeddings: dict[str, list[float],], query: str, expected_id: str)-> EvaluationResult:
    bm25_results = bm25_index.search(query=query, top_k=3)
    
    bm25_ranking = [
        result.document.document_id
        for result in bm25_results
    ]

    vector_results = search_by_vector(
        client=client,
        query=query,
        document_embeddings=document_embeddings,
        top_k=3,
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

    return EvaluationResult(
        query=query,
        expected_id=expected_id,
        bm25_ranking=bm25_ranking,
        vector_ranking=vector_ranking,
        rrf_ranking=rrf_ranking,
    )

def evaluate_all_cases(
    client: OpenAI,
    documents: list[Document],
    evaluation_cases: list[dict[str, str]],
) -> list[EvaluationResult]:
    bm25_index = BM25Index(documents)

    document_embeddings = build_document_embeddings(
        client=client,
        documents=documents,
    )

    results = []

    for case in evaluation_cases:
        result = evaluate_case(
            client=client,
            bm25_index=bm25_index,
            document_embeddings=document_embeddings,
            query=case["query"],
            expected_id=case["expected_id"],
        )

        results.append(result)

    return results

def format_result(
    result: EvaluationResult,
    document_titles: dict[str, str],
) -> str:
    lines = [
        "=" * 60,
        f"質問: {result.query}",
        f"正解文書: {result.expected_id}",
        "",
        f"BM25ランキング: {result.bm25_ranking}",
        f"ベクトルランキング: {result.vector_ranking}",
        "",
        "[RRF統合結果]",
    ]

    for rank, (document_id, score) in enumerate(
        result.rrf_ranking,
        start=1,
    ):
        title = document_titles[document_id]

        lines.append(
            f"{rank}位: "
            f"{document_id} "
            f"score={score:.5f} "
            f"{title}"
        )

    return "\n".join(lines)


def print_report(
    results: list[EvaluationResult],
    documents: list[Document],
) -> None:
    document_titles = {
        document.document_id: document.title
        for document in documents
    }

    for result in results:
        print(
            format_result(
                result=result,
                document_titles=document_titles,
            )
        )

def main()->None:
    client = OpenAI()
    
    results = evaluate_all_cases(client=client, documents=DOCUMENTS, evaluation_cases=EVALUATION_CASES)
    print_report(results=results, documents=DOCUMENTS)
    

if __name__ == "__main__":
    main()
