from dataclasses import dataclass
from openai import OpenAI
from pydantic import BaseModel, Field
from bm25_search import BM25Index, DOCUMENTS
from rag_evaluation_dataset import EVALUATION_CASES, RetrievalEvaluationCase

MODEL_NAME = "gpt-4o-mini"

@dataclass(frozen=True)
class GeneratedAnswer:
    query: str
    context: str
    answer:str
    
class AnswerJudgeResult(BaseModel):
    # 回答がcontextの内容から導かれているか
    is_grounded: bool = Field(
        description=(
            "回答が参考情報だけに基づいていればtrue。"
            "参考情報にない内容を推測していればfalse。"
        )
    )
    
    # 質問に対する回答としてどれくらい適切か
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="質問に対する回答の適切さ。0.0〜1.0",
    )

    # 正解回答と同じ内容を回答できているか
    is_correct: bool = Field(
        description=(
            "正解回答と同じ意味の回答ができていればtrue。"
        )
    )

    reason: str = Field(
        description="判定理由を日本語で説明する。"
    )

@dataclass(frozen=True)
class AnswerEvaluationResult:
    case_id: str
    query: str
    context: str
    generated_answer: str
    judge_result: AnswerJudgeResult
    
def retrieve_context(index: BM25Index, case: RetrievalEvaluationCase)->str:
    """
    BM25で質問に関連する文書を1件取得し、
    LLMへ渡すcontext形式へ変換する。
    """
    
    search_results = index.search(query=case.query, top_k=1)
    
    # 文書が見つからない場合は、LLMに空のcontextを渡す
    if not search_results:
        return "関連する参考情報は見つかりませんでした"
    
    best_document = search_results[0].document
    
    return (
        f"文書ID: {best_document.document_id}\n"
        f"タイトル: {best_document.title}\n"
        f"本文: {best_document.text}"
    )
    
def generate_answer(client: OpenAI, query: str, context: str,)->GeneratedAnswer:
    """
    検索結果をcontextとしてLLMに渡し、回答を生成する。
    """
    
    system_prompt = """
あなたは社内文書に基づいて回答するアシスタントです。

必ず参考情報に書かれている内容だけを使ってください。
参考情報に答えがない場合は、
「参考情報に記載されていません」と回答してください。

参考情報にない事実を推測してはいけません。
""".strip()

    user_prompt = f"""
質問:
{query}

参考情報:
<context>
{context}
</context>
""".strip()

    response = client.chat.completions.create(
        model=MODEL_NAME,
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
        temperature=0.0,
    )
    
    answer = response.choices[0].message.content
    
    if not answer:
        raise RuntimeError("LLMから回答を取得できませんでした。")
    
    return GeneratedAnswer(query=query, context=context, answer=answer)

def judge_answer(
    client: OpenAI,
    case: RetrievalEvaluationCase,
    generated_answer: GeneratedAnswer,
) -> AnswerJudgeResult:
    """
    別のLLM呼び出しで、生成回答の品質を評価する。

    この評価は自動評価であり、
    最終的な正解そのものではない。
    """

    expected_answer = (
        case.expected_answer
        if case.expected_answer is not None
        else "正解文書がないため、回答を拒否する必要があります。"
    )

    system_prompt = """
あなたはRAG回答の品質評価者です。

次の3点を評価してください。

1. 回答が参考情報に基づいているか
2. 質問に対して適切に答えているか
3. 正解回答と同じ意味になっているか

参考情報にない内容を回答している場合、
is_groundedはfalseにしてください。

正解文書がないケースでは、
「情報が記載されていない」と回答できていれば正解です。
""".strip()

    user_prompt = f"""
質問:
{case.query}

参考情報:
<context>
{generated_answer.context}
</context>

生成された回答:
<answer>
{generated_answer.answer}
</answer>

期待される回答:
<expected_answer>
{expected_answer}
</expected_answer>
""".strip()

    response = client.beta.chat.completions.parse(
        model=MODEL_NAME,
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
        response_format=AnswerJudgeResult,
        temperature=0.0,
    )

    parsed = response.choices[0].message.parsed

    if parsed is None:
        raise RuntimeError(
            "回答評価結果を取得できませんでした。"
        )

    return parsed

def evaluate_case(
    client: OpenAI,
    index: BM25Index,
    case: RetrievalEvaluationCase,
) -> AnswerEvaluationResult:
    """
    1つの評価ケースについて、

    1. 文書検索
    2. 回答生成
    3. 回答評価

    を順番に実行する。
    """

    context = retrieve_context(
        index=index,
        case=case,
    )

    generated_answer = generate_answer(
        client=client,
        query=case.query,
        context=context,
    )

    judge_result = judge_answer(
        client=client,
        case=case,
        generated_answer=generated_answer,
    )

    return AnswerEvaluationResult(
        case_id=case.case_id,
        query=case.query,
        context=context,
        generated_answer=generated_answer.answer,
        judge_result=judge_result,
    )


def evaluate_all_cases(
    client: OpenAI,
    cases: list[RetrievalEvaluationCase],
) -> list[AnswerEvaluationResult]:
    """
    全評価ケースを順番に評価する。
    """

    index = BM25Index(DOCUMENTS)
    results = []

    for case in cases:
        result = evaluate_case(
            client=client,
            index=index,
            case=case,
        )

        results.append(result)

    return results


def print_results(
    results: list[AnswerEvaluationResult],
) -> None:
    """
    評価結果を読みやすく表示する。
    """

    print("回答評価結果")
    print("=" * 60)

    for result in results:
        judge = result.judge_result

        print(f"\nID: {result.case_id}")
        print(f"質問: {result.query}")
        print(f"生成回答: {result.generated_answer}")
        print(f"Grounded: {judge.is_grounded}")
        print(f"Relevance: {judge.relevance_score:.2f}")
        print(f"正解判定: {judge.is_correct}")
        print(f"理由: {judge.reason}")


def print_summary(
    results: list[AnswerEvaluationResult],
) -> None:
    """
    全ケースの平均スコアと正解率を表示する。
    """

    if not results:
        print("評価結果がありません。")
        return

    grounded_count = sum(
        1
        for result in results
        if result.judge_result.is_grounded
    )

    correct_count = sum(
        1
        for result in results
        if result.judge_result.is_correct
    )

    average_relevance = sum(
        result.judge_result.relevance_score
        for result in results
    ) / len(results)

    print("\n集計結果")
    print("=" * 60)
    print(
        f"Grounded率: "
        f"{grounded_count}/{len(results)} "
        f"({grounded_count / len(results):.2%})"
    )
    print(
        f"正解率: "
        f"{correct_count}/{len(results)} "
        f"({correct_count / len(results):.2%})"
    )
    print(
        f"平均Relevance: "
        f"{average_relevance:.2f}"
    )


def main() -> None:
    # mainは、部品を作って処理を呼び出すだけにする。
    client = OpenAI()

    results = evaluate_all_cases(
        client=client,
        cases=EVALUATION_CASES,
    )

    print_results(results)
    print_summary(results)


if __name__ == "__main__":
    main()


