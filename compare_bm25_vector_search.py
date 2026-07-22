from math import sqrt
from openai import OpenAI
from bm25_search import BM25Index, DOCUMENTS

EMBEDDING_MODEL = "text-embedding-3-small"

client = OpenAI()

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

def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    
    return response.data[0].embedding

def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    dot_product = sum(value_a * value_b for value_a, value_b in zip(vector_a, vector_b))
    
    norm_a = sqrt(sum(value * value for value in vector_a))
    norm_b = sqrt(sum(value * value for value in vector_b))
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)

def vector_search(query: str, document_embeddings: dict[str, list[float]], top_k:int = 3,) -> list[tuple[str,float]]:
    query_embedding = get_embedding(query)
    
    scored_documents = []
    
    for document_id, document_embedding in document_embeddings.items():
        score = cosine_similarity(
            query_embedding,document_embedding,
        )
        
        scored_documents.append((document_id, score))
        
    scored_documents.sort(
        key=lambda item: item[1],
        reverse=True,
    )
    return scored_documents[:top_k]

def main() -> None:
    bm25_index = BM25Index(DOCUMENTS)
    
    print("文書Embeddingを作成します。")
    print("文書数:", len(DOCUMENTS))
    
    document_embeddings = {}
    
    for document in DOCUMENTS:
        document_embeddings[document.document_id] = (
            get_embedding(document.text)
        )
        
    bm25_correct = 0
    vector_correct = 0
    
    for case in EVALUATION_CASES:
        query = case["query"]
        expected_id = case["expected_id"]
        
        print("\n" + "=" * 60)
        print("質問:", query)
        print("正解文書:", expected_id)
        
        bm25_results = bm25_index.search(
            query=query, top_k=3
        )
        
        vector_results = vector_search(query=query, document_embeddings=document_embeddings, top_k=3)
        
        print("\n[BM25検索]")
        
        for rank, result in enumerate(bm25_results, start = 1):
            document_id = result.document.document_id
            
            print(
                f"{rank}位: "
                f"{document_id} "
                f"score={result.score:.4f}"
            )
        
        print("\n[ベクトル検索]")
        
        for rank, (document_id, score) in enumerate(vector_results, start=1,):
            print(
                f"{rank}位: "
                f"{document_id} "
                f"score={score:.4f}"
            )
            
        if bm25_results:
            bm25_top_id = (bm25_results[0].document.document_id)
            
            if bm25_top_id == expected_id:
                bm25_correct += 1
                
        if vector_results:
            vector_top_id = vector_results[0][0]

            if vector_top_id == expected_id:
                vector_correct += 1
    
    total = len(EVALUATION_CASES)
    
    print("\n" + "=" * 60)
    print("評価結果")
    print("=" * 60)

    print(
        f"BM25 Top1正解率: "
        f"{bm25_correct}/{total} "
        f"({bm25_correct / total:.2%})"
    )

    print(
        f"ベクトル検索 Top1正解率: "
        f"{vector_correct}/{total} "
        f"({vector_correct / total:.2%})"
    )
    
if __name__ == "__main__":
    main()

        
