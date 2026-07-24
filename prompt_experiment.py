from dataclasses import dataclass
from typing import Optional
from openai import OpenAI

# 1. 評価ケースの定義
@dataclass(frozen=True)
class ExperimentCase:
    case_id: str
    question: str
    expected_keywords: Optional[tuple[str, ...]]
    
@dataclass(frozen=True)
class ExperimentResult:
    prompt_name: str
    case: ExperimentCase
    answer: str
    is_correct: bool
    
# 2. すべてのpromptで共通して使う参考情報
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

# 3. Promptの比較対象
PROMPT_VARIANTS = {
    "minimal": """
あなたは社内文書の質問に回答するアシスタントです。
質問に答えてください。
""",
    "grounded": """
あなたは社内文書の質問に回答するアシスタントです。

必ず参考情報だけを根拠に回答してください。
参考情報に記載されていない内容は推測しないでください。
回答できない場合は、
「参考情報に記載されていません」と回答してください。
""",
    "grounded_few_shot": """
あなたは社内文書の質問に回答するアシスタントです。

必ず参考情報だけを根拠に回答してください。
参考情報に記載されていない内容は推測しないでください。

参考情報に回答がある場合は、簡潔に答えてください。
参考情報に回答がない場合は、
「参考情報に記載されていません」と回答してください。

回答例:
質問: 経費精算の締め日はいつですか？
参考情報: 様式に関する提出先だけが記載されています。
回答: 参考情報に記載されていません。
""",
}

# 4. 実験ケース
EXPERIMENT_CASES = [
    ExperimentCase(
        case_id="exact_form_number",
        question="様式第4号の提出先はどこですか？",
        expected_keywords=("セキュリティチーム",),
    ),
    ExperimentCase(
        case_id="pc_procedure",
        question="社外PCを外に持ち出すときの手続きは？",
        expected_keywords=("セキュリティチーム",),
    ),
    ExperimentCase(
        case_id="confidential_information",
        question="機密情報を扱う申請書の提出先は？",
        expected_keywords=("法務部コンプライアンス課",),
    ),
    ExperimentCase(
        case_id="travel_expense",
        question="出張経費の事前申請書はどこに提出しますか？",
        expected_keywords=("総務部経費精算係",),
    ),
    ExperimentCase(
        case_id="travel_form_number",
        question="様式第9号の提出先はどこですか？",
        expected_keywords=("総務部経費精算係",),
    ),
    ExperimentCase(
        case_id="unknown_deadline",
        question="経費精算の締め日はいつですか？",
        expected_keywords=None,
    ),
    ExperimentCase(
        case_id="unknown_book",
        question="会社で読む本を購入するには誰の承認が必要ですか？",
        expected_keywords=None,
    ),
    ExperimentCase(
        case_id="security_team",
        question="社外PC持出許可申請書の提出先は？",
        expected_keywords=("セキュリティチーム",),
    ),
    ExperimentCase(
        case_id="form_one",
        question="様式第1号の提出先を教えてください。",
        expected_keywords=("法務部コンプライアンス課",),
    ),
    ExperimentCase(
        case_id="form_nine",
        question="出張経費の申請書を提出する部署はどこですか？",
        expected_keywords=("総務部経費精算係",),
    ),
]


# 5.Promptと質問をLLMにわたす
def generate_answer(client: OpenAI, prompt_instruction: str, case: ExperimentCase) -> str:
    """
    1つのPromptで、1つの質問に回答する。

    実験では、Prompt以外の条件をできるだけ同じにする。
    そのため、モデル・temperature・参考情報は全ケースで統一する。
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": prompt_instruction,
            },
            {
                "role": "user",
                "content": (
                    f"質問:\n{case.question}\n\n"
                    f"参考情報:\n{KNOWLEDGE_CONTEXT}"
                ),
            },
        ],
    )
    
    return response.choices[0].message.content or ""

# 6. 簡易的な回答評価

ABSTENTION_MARKERS = (
    "参考情報に記載されていません",
    "情報がありません",
    "回答できません",
)

def evaluate_answer(case: ExperimentCase, answer: str) -> bool:
    """
    生成回答を簡易的に評価する。

    今回はLLMを評価者として追加使用せず、
    正解キーワードが含まれているかを確認する。

    未回答ケースでは、
    「情報がない」と適切に回答できたかを確認する。
    """

    if case.expected_keywords is None:
        return any(
            marker in answer
            for marker in ABSTENTION_MARKERS
        )

    return any(
        keyword in answer
        for keyword in case.expected_keywords
    )
    
# 7. 全Promptで実験する
def run_experiment(client: OpenAI, cases: list[ExperimentCase]) ->list[ExperimentResult]:
    """
    Promptごと、ケースごとに回答を生成する。

    Promptが3種類、ケースが3件なら、
    API呼び出しは3 × 3 = 9回になる。
    """

    results = []

    for prompt_name, prompt_instruction in PROMPT_VARIANTS.items():
        for case in cases:
            answer = generate_answer(
                client=client,
                prompt_instruction=prompt_instruction,
                case=case,
            )

            is_correct = evaluate_answer(
                case=case,
                answer=answer,
            )

            results.append(
                ExperimentResult(
                    prompt_name=prompt_name,
                    case=case,
                    answer=answer,
                    is_correct=is_correct,
                )
            )

    return results

# 8. ケースごとの結果を表示する
def print_results(
    results: list[ExperimentResult],
) -> None:
    """Promptごとの生成結果を表示する。"""

    current_prompt = None

    for result in results:
        if result.prompt_name != current_prompt:
            current_prompt = result.prompt_name

            print()
            print("=" * 60)
            print(f"Prompt: {current_prompt}")
            print("=" * 60)

        print(f"\nID: {result.case.case_id}")
        print(f"質問: {result.case.question}")
        print(f"回答: {result.answer}")
        print(f"簡易判定: {result.is_correct}")


# ============================================================
# 9. Promptごとの集計結果を表示する
# ============================================================

def print_summary(
    results: list[ExperimentResult],
) -> None:
    """Promptごとの正解率を表示する。"""

    print()
    print("=" * 60)
    print("Prompt比較結果")
    print("=" * 60)

    for prompt_name in PROMPT_VARIANTS:
        prompt_results = [
            result
            for result in results
            if result.prompt_name == prompt_name
        ]

        correct_count = sum(
            result.is_correct
            for result in prompt_results
        )

        total_count = len(prompt_results)
        accuracy = correct_count / total_count

        print(
            f"{prompt_name}: "
            f"{correct_count}/{total_count} "
            f"({accuracy:.2%})"
        )
        
# ============================================================
# 10. mainは実験の呼び出しだけにする
# ============================================================

def main() -> None:
    # timeoutを設定して、API応答待ちで処理が長時間止まらないようにする
    client = OpenAI(
        timeout=60.0,
        max_retries=0,
    )

    # 最初は3ケースで動作確認する
    # 成功したら、EXPERIMENT_CASESに変更して10ケース実行する
    cases = EXPERIMENT_CASES

    results = run_experiment(
        client=client,
        cases=cases,
    )

    print_results(results)
    print_summary(results)


if __name__ == "__main__":
    main()
