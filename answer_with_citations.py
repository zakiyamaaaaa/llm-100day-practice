from dataclasses import dataclass
from typing import Literal
from openai import OpenAI
from pydantic import BaseModel, Field, model_validator
from bm25_search import DOCUMENTS
from context_builder import ContextBuildResult, build_context
from hybrid_rag_pipeline import RetrievalContext, build_retrieval_context, run_pipeline

MODEL_NAME = "gpt-4o-mini"
MAX_CONTEXT_TOKENS = 60

class GroundedAnswer(BaseModel):
    """
    LLMが返す最終回答の形式

    answered: 回答本文と引用元を返す
    
    refused: 回答本文を返さず、拒否理由だけを返す
    """
    
    status: Literal["answered", "refused"]
    
    answer: str | None = None
    
    # 回答の根拠として使用した文書ID
    sources: list[str] = Field(default_factory=list)
    
    refusal_reason: str | None = None
    
    @model_validator(mode="after")
    def validate_answer_state(self) -> "GroundedAnswer":
        """
        statusと他のフィールドの組み合わせを検証する。

        LLMが次のような不整合データを返さないようにする。

        - answeredなのにanswerがない
        - refusedなのにanswerがある
        - refusedなのに拒否理由がない
        """
        
        if self.status == "answered":
            if not self.answer:
                raise ValueError(
                    "answeredの場合、answerは必須です"
                )
            if not self.sources:
                raise ValueError(
                    "answeredの場合、sourcesは必須です"
                )

            if self.refusal_reason is not None:
                raise ValueError(
                    "answeredの場合、refusal_reasonはNoneにしてください"
                )
        if self.status == "refused":
            if self.answer is not None:
                raise ValueError(
                    "refusedの場合、answerはNoneにしてください"
                )

            if self.sources:
                raise ValueError(
                    "refusedの場合、sourcesは空にしてください"
                )

            if not self.refusal_reason:
                raise ValueError(
                    "refusedの場合、refusal_reasonは必須です"
                )
        return self
                
def create_refusal(reason: str) -> GroundedAnswer:
    """
    回答拒否の結果を作成する
    
    回答できいない場合はanswerをNoneにし、引用元もつけない
    """
    
    return GroundedAnswer(
        status="refused",
        answer=None,
        sources=[],
        refusal_reason=reason,
    )
    
def validate_sources(answer: GroundedAnswer, allowed_source_ids: set[str]) -> GroundedAnswer:
    """
    LLMが返したsourcesをContextと照合する
    
    LLMがContextに存在しない文書を引用した場合は、安全のために回答を拒否する
    
    これは引用元がContext内に存在するかの検証であり、引用内容が本当に回答を裏付けているかという意味評価は、別途Groundedness評価で確認する
    """
    
    # refusedの場合は、Pydanticでsourcesが空であることを検証済
    if answer.status == "refused":
        return answer
    
    cited_source_ids = set(answer.sources)
    
    # Contextに存在しない引用元を抽出する
    unsupported_source_ids = cited_source_ids - allowed_source_ids
    
    if unsupported_source_ids:
        return create_refusal(
            reason=(
                "Contextに存在しない文書を引用しようとしたため。"
                f"不正な引用: {sorted(unsupported_source_ids)}"
            )
        )
    return answer

def generate_grounded_answer(client: OpenAI, query: str, context_result: ContextBuildResult)->GroundedAnswer:
    """
    Contextを使って回答または拒否を生成する。

    処理内容:

    1. Contextが空なら、LLMを呼ばずに拒否する
    2. 質問とContextをLLMへ渡す
    3. 回答とsourcesをStructured Outputで取得する
    4. sourcesがContext内に存在するかPythonで検証する
    """
    
    # Contextが無い場合、LLMに推測させずに即座に拒否する
    if not context_result.context_text.strip():
        return create_refusal(
            reason="回答に使える参考情報がありません"
        )
        
    allowed_source_ids = set(context_result.included_document_ids)
    
    system_prompt = """
あなたは社内文書に基づいて回答するアシスタントです。

必ず参考情報に書かれている内容だけを使ってください。
参考情報から回答できない場合は、statusをrefusedにしてください。

answeredの場合:
- answerに回答本文を書く
- sourcesに、根拠として使った文書IDを入れる
- sourcesには、参考情報に存在する文書IDだけを入れる

refusedの場合:
- answerはnullにする
- sourcesは空の配列にする
- refusal_reasonに拒否理由を書く

参考情報にない部署名、申請書名、日付などを推測してはいけません。
""".strip()

    user_prompt = f"""
質問:
{query}

参考情報:
<context>
{context_result.context_text}
</context>
""".strip()
    response = client.beta.chat.completions.parse(
        model=MODEL_NAME,
        temperature=0.0,
        response_format=GroundedAnswer,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )
    
    message = response.choices[0].message
    
    # APIレベルでモデルが拒否した場合。
    if message.refusal:
        return create_refusal(
            reason=f"モデルによる拒否: {message.refusal}"
        )

    # Structured Outputを取得できなかった場合。
    if message.parsed is None:
        raise RuntimeError(
            "Structured Outputを取得できませんでした"
        )

    parsed_answer = message.parsed

    # LLMが返したsourcesを、実際のContextと照合する。
    return validate_sources(
        answer=parsed_answer,
        allowed_source_ids=allowed_source_ids,
    )

def answer_question(
    client: OpenAI,
    retrieval_context: RetrievalContext,
    query: str,
    candidate_count: int = 3,
) -> GroundedAnswer:
    """
    検索から最終回答までの処理をまとめる
    
    main()には細かい処理を書かず、この関数のなかでpipeline全体を実行する
    """
    
    # RRFで候補を集め、Rerankerで順位を再評価する。
    # APIから受け取った候補数を、既存のRAG Pipelineへ渡す。
    # これにより、HTTP APIの入力と検索処理の設定が分離しない。
    pipeline_result = run_pipeline(
        client=client,
        context=retrieval_context,
        query=query,
        candidate_count=candidate_count,
    )
    
    # 回答生成に使う文書だけを選び、Contextを作る
    context_result = build_context(
        reranked_results=pipeline_result.reranked_results,
        documents_by_id=retrieval_context.documents_by_id,
        max_tokens=MAX_CONTEXT_TOKENS,
    )
    
    return generate_grounded_answer(
        client=client,
        query=query,
        context_result=context_result,
    )
    
def print_answer(
    query: str,
    result: GroundedAnswer,
) -> None:
    """最終回答を確認しやすい形式で表示する。"""

    print("=" * 60)
    print(f"質問: {query}")
    print(f"status: {result.status}")
    print(f"answer: {result.answer}")
    print(f"sources: {result.sources}")
    print(f"refusal_reason: {result.refusal_reason}")
    
def main() -> None:
    """
    RetrievalContextを一度だけつくり、回答可能・未回答の２ケースを実行する
    """
    
    client = OpenAI()
    
    # BM25のインデックスと文書Embeddingを準備する
    retrieval_context = build_retrieval_context(client=client, documents=DOCUMENTS)
    
    queries = [
        "様式第4号の提出先はどこですか？",
        "経費精算の締め日はいつですか？",
    ]
    
    for query in queries:
        result = answer_question(
            client=client,
            retrieval_context=retrieval_context,
            query=query,
        )
        print_answer(
            query=query,
            result=result,
        )

if __name__ == "__main__":
    main()
