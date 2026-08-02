import os
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI
from bm25_search import BM25Index, DOCUMENTS
from rag_evaluation_dataset import EVALUATION_CASES, RetrievalEvaluationCase

# 今回の学習では、既存コードと同じモデルを固定する。
# モデルを毎回変えると、Rewrite結果の比較が難しくなる。
REWRITE_MODEL = "gpt-4o-mini"

@dataclass(frozen=True)
class RewriteEvaluationResult:
    """Query Rewrite前後の検索結果を保持する"""
    case_id: str
    original_query: str
    rewritten_query: str
    expected_document_id: str
    original_document_ids: list[str]
    rewritten_document_ids: list[str]

def create_openai_client() -> OpenAI:
    """OpenAIクライアントを作成する"""
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables.")

    return OpenAI(api_key=api_key)

def build_allowed_vocabulary()->list[str]:
    """
    文書に実際に存在するタイトル一覧を作成する。

    Rewrite時に、LLMが存在しない文書名を
    勝手に作らないようにするために使う。
    """
    return [
        document.title for document in DOCUMENTS
    ]

def rewrite_query(client: OpenAI, query: str, allowed_vocabulary: list[str])->str:
    """
    ユーザーの質問を検索用Queryへ書き換える。

    LLMに回答を生成させるのではなく、
    検索に使う単語の並びだけを作らせる。

    処理の流れ:

    1. Rewriteの役割をSystem Promptで指定する
    2. 文書タイトルを参考語彙として渡す
    3. 元の質問をUser Promptで渡す
    4. LLMからRewrite後のQueryだけを受け取る
    5. 前後の空白と改行を削除する
    """

    vocabulary_text = "\n".join(f"- {term}"
        for term in allowed_vocabulary)

    system_prompt = """あなたは社内文書検索用のQuery Rewrite担当です。

ユーザーの質問を、文書検索で使いやすい
短い日本語の検索Queryへ書き換えてください。

ルール:
- 質問への回答は書かない
- 理由や説明は書かない
- 検索Queryを1行だけ返す
- ユーザーの意図を変えない
- 文書タイトルにある正確な表記を優先する
- 文書タイトルにない固有名詞を勝手に作らない
- 情報が追加できない場合は元の質問を返す
"""
    user_prompt = f"""
元の質問:
{query}

検索に利用できる文書タイトル:
{vocabulary_text}

検索Queryだけを返してください。
"""
    response = client.chat.completions.create(
        model=REWRITE_MODEL,
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
        max_tokens=80,
    )

    rewritten_query = (
        response.choices[0]
        .message
        .content
    )

    if not rewritten_query:
        raise ValueError("LLM did not return a rewritten query.")

    # LLMが複数行を返した場合でも、検索Queryとしては１行にまとめる
    return " ".join(
        rewritten_query.split()
    )

def find_failed_cases(index: BM25Index, cases: list[RetrievalEvaluationCase],)->list[RetrievalEvaluationCase]:
    """
    元のQueryで検索に失敗するケースを抽出する。

    未回答ケースはRewrite対象にしない。
    未回答QueryをRewriteすると、
    本来ない文書を検索してしまう可能性があるため。
    """

    failed_cases: list[RetreivalEvaluationCase] = []

    for case in cases:
        # 正解文書がないケースは対象外
        if case.expected_document_id is None:
            continue

        results = index.search(
            query=case.query,
            top_k=3,
        )

        retrieved_ids = [
            result.document.document_id
            for result in results
        ]

        # 検索結果に正解文書がないケースだけを対象にする
        if case.expected_document_id not in retrieved_ids:
            failed_cases.append(case)
    return failed_cases

def search_document_ids(index: BM25Index, query: str,)->list[str]:
    """
    Queryで検索し、文書IDだけを返す
    """

    results = index.search(
        query=query,
        top_k=3,
    )

    return [
        result.document.document_id
        for result in results
    ]

def evaluate_rewrite_case(client: OpenAI, index: BM25Index, case: RetrievalEvaluationCase, allowed_vocabulary: list[str],) -> RewriteEvaluationResult:
    """１つの失敗ケースに対してRewrite前後を比較する"""

    original_document_ids = search_document_ids(index=index, query=case.query)

    rewritten_query = rewrite_query(
        client=client,
        query=case.query,
        allowed_vocabulary=allowed_vocabulary
    )

    rewritten_document_ids = search_document_ids(index=index, query=rewritten_query)

    return RewriteEvaluationResult(
        case_id=case.case_id,
        original_query=case.query,
        rewritten_query=rewritten_query,
        expected_document_id=(
            case.expected_document_id
        ),
        original_document_ids=(
            original_document_ids
        ),
        rewritten_document_ids=(
            rewritten_document_ids
        ),
    )


def print_result(
    result: RewriteEvaluationResult,
) -> None:
    """Rewrite前後の結果を表示する"""

    original_hit = (
        result.expected_document_id
        in result.original_document_ids
    )

    rewritten_hit = (
        result.expected_document_id
        in result.rewritten_document_ids
    )

    print("\n" + "=" * 60)
    print(f"ID: {result.case_id}")
    print(f"正解文書: {result.expected_document_id}")
    print(f"Rewrite前: {result.original_query}")
    print(
        f"Rewrite前の検索結果: "
        f"{result.original_document_ids}"
    )
    print(f"Rewrite前の正解: {original_hit}")

    print(f"\nRewrite後: {result.rewritten_query}")
    print(
        f"Rewrite後の検索結果: "
        f"{result.rewritten_document_ids}"
    )
    print(f"Rewrite後の正解: {rewritten_hit}")

def main() -> None:
    """検索失敗ケースのRewrite前後を比較する"""
    load_dotenv()

    client = create_openai_client()
    index = BM25Index(DOCUMENTS)
    allowed_vocabulary = build_allowed_vocabulary()

    failed_cases = find_failed_cases(index=index, cases=EVALUATION_CASES)

    print(
        f"Rewrite対象ケース数: "
        f"{len(failed_cases)}"
    )

    for case in failed_cases:
        result = evaluate_rewrite_case(
            client=client,
            index=index,
            case=case,
            allowed_vocabulary=allowed_vocabulary
        )
        print_result(result)

if __name__ == "__main__":
    main()
