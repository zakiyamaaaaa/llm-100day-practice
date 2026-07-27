from argparse import ArgumentParser, Namespace
from pathlib import Path

from openai import OpenAI

from evaluate_bm25_retrieval import CaseEvaluationResult, TOP_K, evaluate_all_cases as evaluate_retrieval, hit_at_k, mean_reciprocal_rank, no_answer_accuracy
from evaluate_rag_answers import AnswerEvaluationResult, evaluate_all_cases as evaluate_answers
from rag_evaluation_dataset import EVALUATION_CASES, RetrievalEvaluationCase, validate_cases

def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="RAGの検索・回答評価を実行します")
    
    parser.add_argument(
        "--mode",
        choices=["retrieval", "answers", "all"],
        default="retrieval",
        help=(
            "retrieval: 検索評価のみ / "
            "answers: 回答評価のみ / "
            "all: 両方"
        ),
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "評価するケース数。"
            "APIを使う場合は、最初は2件程度に制限する"
        ),
    )

    parser.add_argument(
        "--report",
        default="rag_evaluation_report.md",
        help="Markdownレポートの出力先",
    )

    return parser

# 2. 評価ケースの準備
def select_cases(
    limit: int | None
) -> list[RetrievalEvaluationCase]:
    """
    評価ケースを選択する。

    limit=Noneなら全ケース、
    limit=2なら先頭2ケースだけを使用する。
    """
    
    if limit is None:
        return EVALUATION_CASES
    
    if limit <= 0:
        raise ValueError("limitは1以上の整数で指定してください")
    
    return EVALUATION_CASES[:limit]
    
    
# 3. Retrieval評価のレポートを作る
def build_retrieval_report(results: list[CaseEvaluationResult]) -> list[str]:
    """検索評価結果をMarkdown形式に変換する。"""

    lines = [
        "## Retrieval評価",
        "",
        f"- 評価ケース数: {len(results)}",
        "",
        "### ケース別結果",
        "",
        "| ID | 正解文書 | 検索結果 | 正解順位 |",
        "|---|---|---|---:|",
    ]
    
    for result in results:
        expected = (
            result.expected_document_id
            if result.expected_document_id is not None
            else "該当文書なし"
        )

        retrieved = ", ".join(
            result.retrieved_document_ids
        ) or "なし"

        rank = (
            f"{result.correct_rank}位"
            if result.correct_rank is not None
            else "見つからない"
        )

        lines.append(
            f"| {result.case_id} | "
            f"{expected} | {retrieved} | {rank} |"
        )

    answerable_results = [
        result
        for result in results
        if result.expected_document_id is not None
    ]
    
    lines.extend(
        [
            "",
            "### 指標",
            "",
        ]
    )

    for k in [1, 3]:
        hit_count = sum(
            1
            for result in answerable_results
            if hit_at_k(result, k)
        )

        total_count = len(answerable_results)

        score = (
            hit_count / total_count
            if total_count > 0
            else 0.0
        )

        lines.append(
            f"- Hit@{k}: "
            f"{hit_count}/{total_count} "
            f"({score:.2%})"
        )

    lines.append(
        f"- MRR: {mean_reciprocal_rank(results):.4f}"
    )

    lines.append(
        f"- 未回答正解率: {no_answer_accuracy(results):.2%}"
    )

    return lines


# 4. Generation評価のレポートを作る
def build_answer_report(results: list[AnswerEvaluationResult]) -> list[str]:
    """回答評価結果をMarkdown形式に変換する。"""

    lines = [
        "## Generation評価",
        "",
        f"- 評価ケース数: {len(results)}",
        "",
        "### ケース別結果",
        "",
        "| ID | 生成回答 | Grounded | Relevance | 正解 |",
        "|---|---|:---:|---:|:---:|",
    ]

    for result in results:
        judge = result.judge_result

        # Markdownの表が崩れないように改行を空白へ変換する
        answer = result.generated_answer.replace(
            "\n",
            " ",
        )

        lines.append(
            f"| {result.case_id} | "
            f"{answer} | "
            f"{judge.is_grounded} | "
            f"{judge.relevance_score:.2f} | "
            f"{judge.is_correct} |"
        )

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

    average_relevance = (
        sum(
            result.judge_result.relevance_score
            for result in results
        )
        / len(results)
        if results
        else 0.0
    )

    lines.extend(
        [
            "",
            "### 指標",
            "",
            f"- Grounded率: "
            f"{grounded_count}/{len(results)} "
            f"({grounded_count / len(results):.2%})",
            f"- 正解率: "
            f"{correct_count}/{len(results)} "
            f"({correct_count / len(results):.2%})",
            f"- 平均Relevance: "
            f"{average_relevance:.2f}",
        ]
    )

    return lines

# 5. Markdownレポートを組み立てる
def build_report(mode: str, retrieval_results: list[CaseEvaluationResult], answer_results: list[AnswerEvaluationResult]) -> list[str]:
    """評価結果を1つのMarkdownレポートにまとめる。"""

    lines = [
        "# RAG評価レポート",
        "",
        f"- 評価モード: `{mode}`",
        "",
    ]

    if retrieval_results is not None:
        lines.extend(
            build_retrieval_report(retrieval_results)
        )

    if answer_results is not None:
        lines.extend(
            [
                "",
                "---",
                "",
            ]
        )

        lines.extend(
            build_answer_report(answer_results)
        )

    return "\n".join(lines) + "\n"

# 6. レポートを保存する
def save_report(report: str, report_path: str) -> None:
    """
    Markdownレポートを保存する。

    これは学習プログラムが生成する評価結果であり、
    memo.mdは変更しない。
    """
    
    path = Path(report_path)
    path.write_text(report, encoding="utf-8")
    print()
    print(f"レポートを保存しました: {path}")
    
    
# ============================================================
# 7. 全体の実行処理
# ============================================================

def run_evaluation(args: Namespace) -> str:
    """指定されたモードで評価を実行する。"""

    cases = select_cases(args.limit)

    # 評価データが壊れていないか、最初に確認する
    validate_cases(cases)

    retrieval_results = None
    answer_results = None

    if args.mode in ["retrieval", "all"]:
        print("Retrieval評価を実行します")

        retrieval_results = evaluate_retrieval(
            cases=cases,
            top_k=TOP_K,
        )

    if args.mode in ["answers", "all"]:
        print("Generation評価を実行します")

        client = OpenAI(
            timeout=60.0,
            max_retries=0,
        )

        answer_results = evaluate_answers(
            client=client,
            cases=cases,
        )

    report = build_report(
        mode=args.mode,
        retrieval_results=retrieval_results,
        answer_results=answer_results,
    )

    save_report(
        report=report,
        report_path=args.report,
    )

    return report

# ============================================================
# 8. mainは引数解析と実行だけにする
# ============================================================

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    report = run_evaluation(args)

    print()
    print(report)


if __name__ == "__main__":
    main()
