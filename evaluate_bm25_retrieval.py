from dataclasses import dataclass
from bm25_search import BM25Index, DOCUMENTS
from rag_evaluation_dataset import EVALUATION_CASES, RetrievalEvaluationCase

TOP_K = 3

@dataclass(frozen=True)
class CaseEvaluationResult:
    case_id: str
    query: str
    expected_document_id: str | None
    retrieved_document_ids: list[str]
    correct_rank: int | None
    
def find_correct_rank(expected_document_id: str | None, retrieved_document_ids: list[str],) -> int | None:
    if expected_document_id is None:
        return None
    
    for rank, document_id in enumerate(retrieved_document_ids, start=1):
        if document_id == expected_document_id:
            return rank
    return None


def evaluate_case(index: BM25Index, case: RetrievalEvaluationCase, top_k: int = TOP_K)->CaseEvaluationResult:
    search_results = index.search(
        query=case.query,
        top_k=top_k,
    )
    
    retrieved_document_ids = [
        result.document.document_id
        for result in search_results
    ]

    correct_rank = find_correct_rank(
        expected_document_id=case.expected_document_id,
        retrieved_document_ids=retrieved_document_ids,
    )

    return CaseEvaluationResult(
        case_id=case.case_id,
        query=case.query,
        expected_document_id=case.expected_document_id,
        retrieved_document_ids=retrieved_document_ids,
        correct_rank=correct_rank,
    )

def evaluate_all_cases(
    cases: list[RetrievalEvaluationCase],
    top_k: int = TOP_K,
) -> list[CaseEvaluationResult]:
    index = BM25Index(DOCUMENTS)

    return [
        evaluate_case(
            index=index,
            case=case,
            top_k=top_k,
        )
        for case in cases
    ]


def hit_at_k(
    result: CaseEvaluationResult,
    k: int,
) -> bool | None:
    """
    正解文書がk位以内にあるかを返す。

    未回答ケースは通常のHit@kの対象外なのでNoneにする。
    """
    
    if result.expected_document_id is None:
        return None

    return result.correct_rank is not None and (
        result.correct_rank <= k
    )
    
def mean_reciprocal_rank(results: list[CaseEvaluationResult])->float:
    answerable_results = [result for result in results if result.expected_document_id is not None]
    
    if not answerable_results:
        return 0.0

    reciprocal_ranks = []
    
    for result in answerable_results:
        if result.correct_rank is None:
            reciprocal_ranks.append(0.0)
        else:
            reciprocal_ranks.append(
                1.0 / result.correct_rank
            )

    return sum(reciprocal_ranks) / len(
        reciprocal_ranks
    )

def no_answer_accuracy(
    results: list[CaseEvaluationResult],
) -> float:
    unknown_results = [
        result
        for result in results
        if result.expected_document_id is None
    ]

    if not unknown_results:
        return 0.0

    correct_count = sum(
        1
        for result in unknown_results
        if not result.retrieved_document_ids
    )

    return correct_count / len(unknown_results)

def print_case_results(
    results: list[CaseEvaluationResult],
) -> None:
    print("\nケース別評価")
    print("=" * 60)

    for result in results:
        expected = (
            result.expected_document_id
            if result.expected_document_id is not None
            else "該当文書なし"
        )

        rank = (
            f"{result.correct_rank}位"
            if result.correct_rank is not None
            else "見つからない"
        )

        print(f"\nID: {result.case_id}")
        print(f"正解: {expected}")
        print(
            f"検索結果: "
            f"{result.retrieved_document_ids}"
        )
        print(f"正解文書の順位: {rank}")

def print_metrics(
    results: list[CaseEvaluationResult],
) -> None:
    answerable_results = [
        result
        for result in results
        if result.expected_document_id is not None
    ]

    print("\n評価指標")
    print("=" * 60)

    for k in [1, 3]:
        hit_results = [
            hit_at_k(result, k)
            for result in answerable_results
        ]

        hit_count = sum(
            1
            for hit in hit_results
            if hit
        )

        total_count = len(hit_results)

        score = (
            hit_count / total_count
            if total_count > 0
            else 0.0
        )

        print(
            f"Hit@{k}: "
            f"{hit_count}/{total_count} "
            f"({score:.2%})"
        )

    mrr = mean_reciprocal_rank(results)

    print(f"MRR: {mrr:.4f}")

    no_answer_score = no_answer_accuracy(results)

    print(
        f"未回答正解率: "
        f"{no_answer_score:.2%}"
    )
    
def main() -> None:
    results = evaluate_all_cases(
        cases=EVALUATION_CASES,
        top_k=TOP_K,
    )

    print_case_results(results)
    print_metrics(results)


if __name__ == "__main__":
    main()
