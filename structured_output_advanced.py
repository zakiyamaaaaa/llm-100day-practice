from typing import Literal
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError, model_validator

# 1. LLMの構造化出力モデル
class StructuredAnswer(BaseModel):
    """
    LLMの回答形式を定義する。

    statusによって、回答成功と回答拒否を区別する。
    """
    
    # 回答できたか、拒否したかを限定する
    status: Literal["answered", "refused"]
    
    # 回答できない場合はNoneになる
    answer: str | None = None
    
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    
    # 参照した文書ID
    sources: list[str] = Field(
        default_factory=list,
    )
    
    refusal_reason: str | None = None
    
    @model_validator(mode="after")
    def validate_answer_state(self) -> "StructuredAnswer":
        """
        フィールド同士の整合性を検証する。

        PydanticのFieldだけでは、
        statusとanswerの関係までは検証できない。
        そのため、model_validatorを使う。
        """
        
        if self.status == "answered":
            # 回答成功なのに回答本文がない状態は禁止する
            if not self.answer:
                raise ValueError("answeredの場合、answerは必須です")
            
            # 回答成功なのに拒否理由がある状態も禁止する
            if self.refusal_reason is not None:
                raise ValueError("answeredの場合、refusal_reasonはNoneにしてください")
            
        if self.status == "refused":
            # 回答拒否なのに回答本文がある状態は禁止する
            if self.answer is not None:
                raise ValueError(
                    "refusedの場合、answerはNoneにしてください"
                )

            # 拒否理由がない拒否は不十分なので禁止する
            if not self.refusal_reason:
                raise ValueError(
                    "refusedの場合、refusal_reasonは必須です"
                )
        return self
        
# ============================================================
# 2. 参考情報
# ============================================================

KNOWLEDGE_CONTEXT = """
[doc_1]
機密情報取扱申請書（様式第1号）の提出先は、
法務部コンプライアンス課です。

[doc_2]
社外PC持出許可申請書（様式第4号）の提出先は、
セキュリティチームです。

[doc_3]
出張経費事前申請書（様式第9号）の提出先は、
総務部経費精算係です。
"""

# ============================================================
# 3. 質問と参考情報の組み合わせ
# ============================================================

EXAMPLES = [
    {
        "id": "answerable",
        "question": "様式第4号の提出先はどこですか？",
    },
    {
        "id": "unanswerable",
        "question": "経費精算の締め日はいつですか？",
    },
]

# ============================================================
# 4. LLMに構造化回答を生成させる
# ============================================================

def generate_structured_answer(
    client: OpenAI,
    question: str,
) -> StructuredAnswer | None:
    """
    質問に対する構造化回答を生成する。

    戻り値がNoneになるのは、
    APIレベルでモデルが拒否した場合。
    """

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        temperature=0,
        response_format=StructuredAnswer,
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたは社内文書の回答アシスタントです。\n"
                    "必ず参考情報だけを根拠にしてください。\n"
                    "参考情報に回答がある場合は、"
                    "statusをansweredにしてください。\n"
                    "参考情報に回答がない場合は、"
                    "statusをrefusedにしてください。\n"
                    "refusedの場合、answerはnullにし、"
                    "refusal_reasonに理由を書いてください。\n"
                    "sourcesには参照した文書IDを入れてください。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"質問:\n{question}\n\n"
                    f"参考情報:\n{KNOWLEDGE_CONTEXT}"
                ),
            },
        ],
    )

    message = response.choices[0].message

    # APIレベルでモデルが拒否した場合
    if message.refusal:
        print(f"モデルによる拒否: {message.refusal}")
        return None

    # Structured Outputとして解析できなかった場合
    if message.parsed is None:
        print("Structured Outputの解析に失敗しました")
        print(f"finish_reason: {response.choices[0].finish_reason}")
        print(f"message.content: {message.content}")
        print(f"message.refusal: {message.refusal}")

        raise ValueError(
            "Structured Outputを取得できませんでした"
        )

    return message.parsed

# ============================================================
# 5. 結果を表示する
# ============================================================

def print_result(
    example_id: str,
    question: str,
    result: StructuredAnswer | None,
) -> None:
    """構造化された結果を見やすく表示する。"""

    print("=" * 60)
    print(f"ID: {example_id}")
    print(f"質問: {question}")

    if result is None:
        print("結果: APIレベルで拒否されました")
        return

    print(f"status: {result.status}")
    print(f"answer: {result.answer}")
    print(f"confidence: {result.confidence}")
    print(f"sources: {result.sources}")
    print(f"refusal_reason: {result.refusal_reason}")
    
def demonstrate_validation_error() -> None:
    """
    意図的に不正なデータを作り、Pydanticが検出することを確認する。
    """

    print()
    print("=" * 60)
    print("バリデーションエラーの確認")
    print("=" * 60)

    try:
        # refusedなのにanswerを入れているため不正
        StructuredAnswer(
            status="refused",
            answer="セキュリティチームです",
            refusal_reason="参考情報がありません",
        )

    except ValidationError as error:
        print("不正なデータを検出しました")
        print(error)

# ============================================================
# 7. 実験全体を実行する
# ============================================================

def run_examples(client: OpenAI) -> None:
    """複数の質問でStructured Outputを確認する。"""

    for example in EXAMPLES:
        result = generate_structured_answer(
            client=client,
            question=example["question"],
        )

        print_result(
            example_id=example["id"],
            question=example["question"],
            result=result,
        )


# ============================================================
# 8. mainは処理の呼び出しだけにする
# ============================================================

def main() -> None:
    client = OpenAI(
        timeout=60.0,
        max_retries=0,
    )

    run_examples(client)
    demonstrate_validation_error()


if __name__ == "__main__":
    main()
