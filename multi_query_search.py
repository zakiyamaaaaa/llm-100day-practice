import os
import re
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI
from bm25_search import BM25Index, DOCUMENTS
from hybrid_rrf_search import (
    build_document_embeddings,
    calculate_rrf_scores,
    search_by_vector,
    sort_rrf_scores,
)

from rag_evaluation_dataset import EVALUATION_CASES, RetrievalEvaluationCase

QUERY_MODEL = "gpt-4o-mini"

# 1つの質問に対して、元のQuery + ２つの代替Queryを使う
ALTERNATIVE_QUERY_COUNT = 2

TOP_K = 3

@dataclass(frozen=True)
class QueryRanking:
    """1つのQueryによる検索結果"""
    query: str
    bm25_ranking: list[str]
    vector_ranking: list[str]

@dataclass(frozen=True)
class MultiQueryResult:
    """Multi-query検索全体の結果"""
    case_id: str
    original_query: str
    queries: list[str]
    rankings: list[QueryRanking]
    rrf_ranking: list[tuple[str, float]]
    expected_document_id: str

def create_openai_client() -> OpenAI:
    """OpenAIクライアントを作成する"""
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables.")

    return OpenAI(api_key=api_key)

def parse_query_lines(content: str,) -> list[str]:
    """LLMの出力くぉQueryのりすとへ　変換する
    LLMが次のような形式で返す可能性があるため、
    箇条書き記号や番号を取り除く。

    - Query A
    - Query B

    1. Query A
    2. Query B
    """

    queries: list[str] = []

    for line in content.splitlines():
        cleaned_line = re.sub(
            pattern=r"^\s*(?:[-*]|\d+[.)])\s*",
            repl="",
            string=line,
        ).strip()

        if cleaned_line:
            queries.append(cleaned_line)
    return queries

def remove_duplicate_queries(queries: list[str]) -> list[str]:
    """
    Queryの重複を削除する。

    同じQueryを複数回検索しても、
    同じ結果が重複して加点されるだけなので、
    先に重複を取り除く。
    """

    unique_queries: list[str] = []

    # すでに登場したQueryを記録する集合
    # setを使うことで、高速に重複確認できる。
    seen_queries: set[str] = set()

    for query in queries:
        # LLMが余分な改行や空白を返す可能性があるため、
        # 検索前に空白を1つへ整える。
        normalized_query = " ".join(query.split())
        # 空文字のQueryは検索に使えないため除外する。
        if not normalized_query:
            continue
         # すでに同じQueryが登録されていれば、
        # 2回目は追加しない。
        if normalized_query in seen_queries:
            continue
        # 初めて登場したQueryとして記録する
        seen_queries.add(normalized_query)
        unique_queries.append(normalized_query)

    return unique_queries

def generate_multi_queries(client: OpenAI, original_query: str,)->list[str]:
    """
    1つの質問から複数の検索Queryを作成する。

    元のQueryは必ず残す。
    LLMには、次の2種類のQueryを作らせる。

    1. 文書名・固有語を重視したQuery
    2. 元の質問とは異なる自然な言い換えQuery

    LLMに回答を書かせず、
    あくまで検索用のQueryだけを作らせる。
    """

    system_prompt = """
あなたは文書検索用のQuery生成担当です。

ユーザーの質問を、検索に使える
2種類のQueryへ言い換えてください。

ルール:
- 回答は書かない
- 理由や説明は書かない
- Queryを2行だけ返す
- 各Queryは短くする
- 元の質問の意図を変えない
- 文書に書かれていない固有名詞や事実を追加しない
- 1つは重要なキーワードを重視する
- 1つは自然な言い換えを重視する
"""

    user_prompt = f"""
元の質問:
{original_query}

検索Queryを2行で返してください。
"""
    response = client.chat.completions.create(
        model=QUERY_MODEL,
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
        max_tokens=120,
    )

    content = (
        response.choices[0]
        .message
        .content
    )

    if not content:
        raise ValueError(
            "Multi-queryの生成結果が空です"
        )
    # LLMの出力は文字列なので、
    # 改行で分割してQueryのリストに変換する。

    alternative_queries = parse_query_lines(content)

    # 元のQueryを必ず先頭に残す。
    #
    # LLMのRewriteが不適切でも、
    # 元のQueryによる検索結果を失わないため。

    all_queries = [original_query, *alternative_queries[
            :ALTERNATIVE_QUERY_COUNT
        ], ]
    # 元のQueryと生成Queryが同じだった場合に備え、
    # 検索前に重複を削除する。

    unique_queries = remove_duplicate_queries(all_queries)

    if not unique_queries:
        raise ValueError(
            "Multi-queryの生成結果が空です"
        )
    return unique_queries

def find_failed_cases(index: BM25Index, cases: list[RetrievalEvaluationCase])->list[RetrievalEvaluationCase]:
    """
    元のBM25検索で正解文書を取得できないケースを探す。

    未回答ケースは対象外にする。

    未回答QueryをMulti-query化すると、
    本来存在しない文書を無理に検索する
    危険があるため。
    """

    failed_cases: list[RetrievalEvaluationCase] = []

    for case in cases:
        # 正解文書がない未回答ケースはスキップする。
        if case.expected_document_id is None:
            continue

        results = index.search(
            query=case.query,
            top_k=TOP_K,
        )

        # BM25の検索結果から、文書IDだけを取り出す。
        retrieved_ids = [
            result.document.document_id for result in results
        ]

        # 正解文書が検索結果に含まれていなければ、
        # Multi-queryによる改善対象に追加する
        if case.expected_document_id not in (
            retrieved_ids
        ):
            failed_cases.append(case)
    return failed_cases

def search_by_bm25(index: BM25Index, query: str,)->list[str]:
    """
    BM25検索を行い、文書IDだけを返す
    """

    results = index.search(
        query=query,
        top_k=TOP_K,
    )

    return [
        result.document.document_id
        for result in results
    ]

def search_by_vector_ids(
    client: OpenAI,
    query: str,
    document_embeddings: dict[str, list[float]],
) -> list[str]:
    """
    Vector検索を実行し、文書IDの順位だけを返す。

    既存のvector検索関数を再利用する。
    """

    results = search_by_vector(
        client=client,
        query=query,
        document_embeddings=(
            document_embeddings
        ),
        top_k=TOP_K,
    )

    return [
        document_id
        for document_id, score in results
    ]

def run_multi_query_search(client: OpenAI, index: BM25Index, document_embeddings: dict[str, list[float]], queries: list[str])->tuple[list[QueryRanking],list[tuple[str,float]]]:
    """
    複数Queryの検索結果をRRFで統合する。

    処理の流れ:

    1. QueryごとにBM25検索する
    2. QueryごとにVector検索する
    3. すべてのランキングを1つのリストにまとめる
    4. RRFで文書ごとのスコアを計算する
    5. スコア順に並べる

    同じ文書が複数のランキングに登場すると、
    RRFスコアが加算されて上位に来やすくなる。
    """

    query_rankings: list[QueryRanking] = []
    # すべてのランキングをここへ集める。
    # 後でRRFへまとめて渡す
    all_rankings: list[list[str]] = []

    for query in queries:
        # 1つ目の検索方法としてBM25を実行する。
        # 完全一致やキーワード一致に強い。
        bm25_ranking = search_by_bm25(
            index=index,query=query
        )

        # 2つ目の検索方法としてVector検索を実行する。
        # 表現が異なっていても意味が近い文書を探せる。
        vector_ranking = search_by_vector_ids(
            client=client,
            query=query,
            document_embeddings=document_embeddings
        )

        # Queryごとの検索結果を保存する。
        # 後で、Query単位の結果を表示するために使う。

        query_rankings.append(
            QueryRanking(
                query=query,
                bm25_ranking=bm25_ranking,
                vector_ranking=vector_ranking,
            )
        )

        # BM25とVectorのランキングを、
        # RRFの入力用リストへ追加する。
        #
        # ここではスコアを統合せず、
        # 順位のリストだけを渡す。

        all_rankings.append(bm25_ranking)
        all_rankings.append(vector_ranking)
    # 各ランキングでの順位を使って、
    # 文書ごとのRRFスコアを計算する。
    #
    # 同じ文書が複数のランキングに登場すると、
    # その文書のスコアが複数回加算される。
    rrf_scores = calculate_rrf_scores(all_rankings)
    # RRFスコアの高い順に文書を並べる。

    rrf_ranking = sort_rrf_scores(rrf_scores)

    return query_rankings, rrf_ranking

def evaluate_cases(client: OpenAI, index: BM25Index, document_embeddings: dict[str, list[float]], case: RetrievalEvaluationCase) -> MultiQueryResult:
    """1つの評価ケースをMulti-query検索する"""

    queries = generate_multi_queries(client=client, original_query=case.query)
    rankings, rrf_ranking = run_multi_query_search(
        client=client,
        index=index,
        document_embeddings=document_embeddings,
        queries=queries,
    )
    return MultiQueryResult(
        case_id=case.case_id,
        original_query=case.query,
        queries=queries,
        rankings=rankings,
        rrf_ranking=rrf_ranking,
        expected_document_id=(
            case.expected_document_id
        ),
    )

def print_result(
    result: MultiQueryResult,
) -> None:
    """Multi-query検索結果を表示する"""

    print("\n" + "=" * 60)
    print(f"ID: {result.case_id}")
    print(
        f"正解文書: "
        f"{result.expected_document_id}"
    )

    print("\n生成されたQuery:")
    for index, query in enumerate(
        result.queries,
        start=1,
    ):
        print(f"{index}. {query}")

    print("\nQueryごとのランキング:")
    for ranking in result.rankings:
        print(f"\nQuery: {ranking.query}")
        print(
            f"BM25: "
            f"{ranking.bm25_ranking}"
        )
        print(
            f"Vector: "
            f"{ranking.vector_ranking}"
        )

    print("\n[RRF統合結果]")
    for rank, (
        document_id,
        score,
    ) in enumerate(
        result.rrf_ranking,
        start=1,
    ):
        is_correct = (
            document_id
            == result.expected_document_id
        )

        print(
            f"{rank}位: "
            f"{document_id} "
            f"score={score:.5f} "
            f"正解={is_correct}"
        )

def main() -> None:
    """BM25失敗ケースをMulti-queryで評価する"""

    load_dotenv()

    client = create_openai_client()
    index = BM25Index(DOCUMENTS)
    # 文書Embeddingは1回だけ作成し、
    # 複数Queryで使い回す。
    document_embeddings = build_document_embeddings(
        client=client,
        documents=DOCUMENTS,
    )
    failed_cases = find_failed_cases(
        index=index,
        cases=EVALUATION_CASES,
    )

    print(
        f"Multi-query対象ケース数: "
        f"{len(failed_cases)}"
    )

    for case in failed_cases:
        result = evaluate_cases(
            client=client,
            index=index,
            document_embeddings=document_embeddings,
            case=case,
        )
        print_result(result=result)

if __name__ == "__main__":
    main()
