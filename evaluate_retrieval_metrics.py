from evaluate_bm25_retrieval import (
    CaseEvaluationResult,
    TOP_K,
    evaluate_all_cases,
    hit_at_k,
    mean_reciprocal_rank,
    no_answer_accuracy
)
from rag_evaluation_dataset import EVALUATION_CASES

# 1.Recall@kを計算する
def recall_at_k(relevant_document_ids: set[str], retrieved_document_ids: list[str], k:int) -> float | None:
    """
    上位k件に含まれる関連文書の割合を計算する。

    relevant_document_ids:
        正解として扱うすべての文書ID

    retrieved_document_ids:
        検索で取得した文書IDのランキング

    k:
        上位何件まで見るか
    """
    
    retrieved_top_k = set(retrieved_document_ids[:k])
    retrieved_relevant_count = len(relevant_document_ids & retrieved_top_k)
    return ( retrieved_relevant_count/ len(relevant_document_ids))

# 2. 現在の評価結果をRecall@k用に変換する
def recall_for_case(result: CaseEvaluationResult, k: int) -> float | None:
    """
    現在のデータ構造に合わせてRecall@kを計算する。

    今回は1ケースにつき正解文書が1件なので、
    expected_document_idを集合に変換する。
    """
    
    if result.expected_document_id is None:
        return None

    relevant_document_ids = {
        result.expected_document_id
    }
    
    return recall_at_k(
        relevant_document_ids=relevant_document_ids,
        retrieved_document_ids=result.retrieved_document_ids,
        k=k,
    )
    
# 3. Recall@kの平均を計算する
def mean_recall_at_k(results: list[CaseEvaluationResult], k: int) -> float:
    """
    回答可能ケースのRecall@k平均を計算する。
    """
    
    recall_values = [recall_for_case(result, k) for result in results]
    # 未回答ケースのNoneを除外する
    valid_values = [value for value in recall_values if value is not None]
    if not valid_values:
        return 0.0
    
    return sum(valid_values) / len(valid_values)

# 4. ケース別のRecallを表示する
def print_case_metrics(results: list[CaseEvaluationResult])-> None:
    """ケースごとのHit@kとRecall@kを表示する。"""

    print("=" * 60)
    print("ケース別Retrieval指標")
    print("=" * 60)

    for result in results:
        print(f"\nID: {result.case_id}")
        print(
            f"検索結果: "
            f"{result.retrieved_document_ids}"
        )

        for k in [1, 3]:
            hit = hit_at_k(result, k)
            recall = recall_for_case(result, k)

            print(f"Hit@{k}: {hit}")
            print(f"Recall@{k}: {recall}")

# 5. 全体の指標を表示する
def print_summary(
    results: list[CaseEvaluationResult],
) -> None:
    """全体のRetrieval指標を表示する。"""

    answerable_count = sum(
        1
        for result in results
        if result.expected_document_id is not None
    )

    print()
    print("=" * 60)
    print("全体のRetrieval指標")
    print("=" * 60)
    print(f"回答可能ケース数: {answerable_count}")

    for k in [1, 3]:
        recall = mean_recall_at_k(
            results=results,
            k=k,
        )

        print(
            f"平均Recall@{k}: "
            f"{recall:.4f}"
        )

    print(
        f"MRR: "
        f"{mean_reciprocal_rank(results):.4f}"
    )

    print(
        f"未回答正解率: "
        f"{no_answer_accuracy(results):.2%}"
    )
    
# ============================================================
# 6. mainは評価の実行だけにする
# ============================================================

def main() -> None:
    results = evaluate_all_cases(
        cases=EVALUATION_CASES,
        top_k=TOP_K,
    )

    print_case_metrics(results)
    print_summary(results)


if __name__ == "__main__":
    main()

