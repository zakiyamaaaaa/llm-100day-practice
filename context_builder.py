from dataclasses import dataclass
import tiktoken
from bm25_search import DOCUMENTS, Document
from hybrid_rag_pipeline import build_retrieval_context, run_pipeline
from llm_reranker import RerankItem
from openai import OpenAI

MODEL_NAME = "gpt-4o-mini"

@dataclass(frozen=True)
class ContextBuildResult:
    """
    回答生成用Contextを作成した結果。

    context_text:
        LLMへ渡す最終的な文字列。

    included_document_ids:
        Contextに採用した文書ID。

    skipped_document_ids:
        Token上限などの理由で除外した文書ID。

    used_tokens:
        作成したContextのおおよそのToken数。
    """
    context_text: str
    included_document_ids: list[str]
    skipped_document_ids: list[str]
    used_tokens: int
    
def count_tokens(text: str, model_name: str = MODEL_NAME) -> int:
    """
    文字列をモデル用Tokenizerで分割し、Token数を数える。

    len(text)は文字数であり、LLMが実際に消費するToken数ではない。
    そのため、モデルに合わせたTokenizerを使って数える。
    """
    
    encoding = tiktoken.encoding_for_model(model_name)
    # encode()は文字列をモデルが扱うToken IDの配列へ変換する。
    # 配列の長さが、その文字列のおおよそのToken数になる。
    token_ids = encoding.encode(text)
    return len(token_ids)

def format_document_for_context(document: Document) -> str:
    """
    1文書を、LLMへ渡すContextの形式へ変換する。

    document_idを含めることで、
    後から「どの文書を根拠にしたか」を追跡しやすくする。
    """
    
    return (
        f"[source: {document.document_id}]\n"
        f"title: {document.title}\n"
        f"text: {document.text}"
    )
    
def build_context(reranked_results: list[RerankItem], documents_by_id: dict[str, Document], max_tokens: int)->ContextBuildResult:
    """
    Rerankerの結果から、回答生成用Contextを作成する。

    処理内容:

    1. 関連度スコアの高い順に並べる
    2. 同じ文書IDの重複を除去する
    3. 文書をContext用の文字列へ変換する
    4. Token上限を超えない文書だけ採用する
    5. 採用文書・除外文書・使用Token数を返す
    """
    
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    
    # Rerankerの結果を関連度の高い順に並べる
    # document_idを第２条件にすることで、同点時の順位を安定させる
    sorted_results = sorted(reranked_results, key=lambda result: (
        -result.relevance_score,
        result.document_id
    ))
    
    context_blocks: list[str] = []
    included_document_ids: list[str] = []
    skipped_document_ids: list[str] = []
    
    # 同じ文書が複数回登場した場合に重複登録しないための集合
    seen_document_ids: set[str] = set()
    
    for result in sorted_results:
        document_id = result.document_id
        
        # すでに採用または処理した文書ならスキップｓる
        if document_id in seen_document_ids:
            skipped_document_ids.append(document_id)
            continue
        
        seen_document_ids.add(document_id)
        
        # Rerankerが返したIDに対応する文書本文を取得する
        document = documents_by_id.get(document_id)
        
        if document is None:
            raise ValueError(f"Document with ID '{document_id}' not found in documents_by_id.")
        
        # 文書ID・タイトル・本文を、Context用の１ブロックへ変換する
        document_block = format_document_for_context(document)
        
        # 既存のContextに今回の文書を追加した場合の文字列を作る
        # 実際にLLMへ渡す形に近い状態でToken数を計測する
        candidate_blocks = [
            *context_blocks,document_block
        ]
        candidate_context = "\n\n".join(candidate_blocks)
        
        candidate_token_count = count_tokens(candidate_context)
        
        # Token上限を超える場合は、今回の文書を採用しない
        # 本文を途中で切らず、文書単位で除外する
        if candidate_token_count > max_tokens:
            skipped_document_ids.append(document_id)
            continue
        
        # 上限以内に収まる場合だけContextへ追加する
        context_blocks.append(document_block)
        included_document_ids.append(document_id)
    final_context = "\n\n".join(context_blocks)
    used_token = count_tokens(final_context)
    
    return ContextBuildResult(
        context_text=final_context,
        included_document_ids=included_document_ids,
        skipped_document_ids=skipped_document_ids,
        used_tokens=used_token,
    )
    

def print_context_result(result: ContextBuildResult) -> None:
    """Context Builderの結果を確認用に表示する。"""

    print("\n[Context Builder結果]")
    print(f"採用文書: {result.included_document_ids}")
    print(f"除外文書: {result.skipped_document_ids}")
    print(f"使用Token数: {result.used_tokens}")
    print("\n[LLMへ渡すContext]")
    print(result.context_text)

def main() -> None:
    """
    Retriever → Reranker → Context Builderを実行する。

    main()には処理の詳細を書かず、
    各処理を関数へ分離して呼び出すだけにする。
    """
    
    client = OpenAI()
    
    # BM25のインデックスと文書Embeddingを準備する
    retrieval_context = build_retrieval_context(client=client, documents=DOCUMENTS)
    
    query = "出張費用の申請書はどこに提出しますか？"
    
    # RRFで候補を集め、Rerankerで順位を再評価する
    pipeline_result = run_pipeline(
        client=client,
        context=retrieval_context,
        query=query,
        candidate_count=3,
    )
    
    # Rerankerの結果から、回答生成用Contextを作成する
    context_result = build_context(
        reranked_results=pipeline_result.reranked_results,
        documents_by_id=retrieval_context.documents_by_id,
        max_tokens=60,
    )
    
    print_context_result(context_result)
    
if __name__ == "__main__":
    main()
