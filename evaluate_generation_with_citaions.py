import re
from dataclasses import dataclass

#1. 評価ケース

@dataclass(frozen=True)
class CitationCase:
    """
    引用評価用のケース。

    expected_document_ids:
        正解として引用すべき文書ID。
        未回答ケースではNone。

    context_document_ids:
        LLMに渡した参考情報に含まれる文書ID。
    """
    case_id: str
    question: str
    generated_answer: str
    expected_document_ids: set[str] | None
    context_document_ids: set[str]
    
@dataclass(frozen=True)
class CitationResult:
    """引用評価の結果"""
    case_id:str
    cited_document_ids: set[str]
    unsupported_citations: set[str]
    citation_precision: float | None
    citation_recall: float|None
    is_citation_supported: bool
    is_citation_correct: bool
    
# 2. 引用を抽出する
def extract_citations(answer: str) -> set[str]:
    """
    回答文からdoc_数字形式の引用を抽出する。

    例:
        "提出先はセキュリティチームです。[doc_2]"
        → {"doc_2"}
    """
    
    return set( re.findall(r"\bdoc_\d+\b",
            answer,))

# 3. 引用を評価する
def evaluate_citation(case: CitationCase) -> CitationResult:
    """
    回答中の引用を評価する。

    citation_precision:
        引用した文書のうち、正解文書が占める割合。

    citation_recall:
        引用すべき正解文書のうち、
        実際に引用できた割合。
    """
    
    cited_document_ids = extract_citations(case.generated_answer)
    unsupported_citations = cited_document_ids - case.context_document_ids
    is_citation_supported = len(unsupported_citations) == 0
    
    # 未回答ケース
    if case.expected_document_ids is None:
        # 未回答なのに引用があるのは不適切
        is_citation_correct = len(cited_document_ids) == 0
        
        return CitationResult(
            case_id=case.case_id,
            cited_document_ids=cited_document_ids,
            unsupported_citations=unsupported_citations,
            citation_precision=None,
            citation_recall=None,
            is_citation_supported=is_citation_supported,
            is_citation_correct=is_citation_correct,
        )
    
    relevant_document_ids = case.expected_document_ids
    correct_citations = cited_document_ids & relevant_document_ids
    citation_precision = len(correct_citations)/len(cited_document_ids) if cited_document_ids else 0.0
    
    # 必要な正解文書を引用できたか
    citation_recall = len(correct_citations)/len(relevant_document_ids)
    
    is_citation_correct = is_citation_supported and cited_document_ids == relevant_document_ids
    
    return CitationResult(
        case_id=case.case_id,
        cited_document_ids=cited_document_ids,
        unsupported_citations=unsupported_citations,
        citation_precision=citation_precision,
        citation_recall=citation_recall,
        is_citation_supported=is_citation_supported,
        is_citation_correct=is_citation_correct,
    )
    
# ============================================================
# 4. 評価ケース
# ============================================================

CASES = [
    CitationCase(
        case_id="correct_citation",
        question="様式第4号の提出先はどこですか？",
        generated_answer=(
            "提出先はセキュリティチームです。[doc_2]"
        ),
        expected_document_ids={"doc_2"},
        context_document_ids={"doc_2"},
    ),
    CitationCase(
        case_id="missing_citation",
        question="様式第4号の提出先はどこですか？",
        generated_answer=(
            "提出先はセキュリティチームです。"
        ),
        expected_document_ids={"doc_2"},
        context_document_ids={"doc_2"},
    ),
    CitationCase(
        case_id="wrong_citation",
        question="様式第4号の提出先はどこですか？",
        generated_answer=(
            "提出先はセキュリティチームです。[doc_1]"
        ),
        expected_document_ids={"doc_2"},
        context_document_ids={"doc_2"},
    ),
    CitationCase(
        case_id="extra_citation",
        question="様式第4号の提出先はどこですか？",
        generated_answer=(
            "提出先はセキュリティチームです。"
            "[doc_1][doc_2]"
        ),
        expected_document_ids={"doc_2"},
        context_document_ids={"doc_1", "doc_2"},
    ),
    CitationCase(
        case_id="unknown_without_citation",
        question="経費精算の締め日はいつですか？",
        generated_answer=(
            "参考情報に記載されていません。"
        ),
        expected_document_ids=None,
        context_document_ids={"doc_1", "doc_2", "doc_3"},
    ),
    CitationCase(
        case_id="unknown_with_citation",
        question="経費精算の締め日はいつですか？",
        generated_answer=(
            "参考情報に記載されていません。[doc_2]"
        ),
        expected_document_ids=None,
        context_document_ids={"doc_1", "doc_2", "doc_3"},
    ),
]

# ============================================================
# 5. 結果を表示する
# ============================================================

def print_result(result: CitationResult) -> None:
    """1ケースの評価結果を表示する。"""

    print("=" * 60)
    print(f"ID: {result.case_id}")
    print(
        f"引用文書: "
        f"{sorted(result.cited_document_ids)}"
    )
    print(
        f"contextにない引用: "
        f"{sorted(result.unsupported_citations)}"
    )
    print(
        f"引用の根拠性: "
        f"{result.is_citation_supported}"
    )
    print(
        f"引用の正確性: "
        f"{result.is_citation_correct}"
    )

    if result.citation_precision is not None:
        print(
            f"Citation Precision: "
            f"{result.citation_precision:.2f}"
        )
        print(
            f"Citation Recall: "
            f"{result.citation_recall:.2f}"
        )


# ============================================================
# 6. 集計結果を表示する
# ============================================================

def print_summary(
    results: list[CitationResult],
) -> None:
    """引用評価の集計結果を表示する。"""

    correct_count = sum(
        result.is_citation_correct
        for result in results
    )

    supported_count = sum(
        result.is_citation_supported
        for result in results
    )

    print()
    print("=" * 60)
    print("引用評価の集計")
    print("=" * 60)
    print(
        f"引用正解率: "
        f"{correct_count}/{len(results)} "
        f"({correct_count / len(results):.2%})"
    )
    print(
        f"引用根拠性: "
        f"{supported_count}/{len(results)} "
        f"({supported_count / len(results):.2%})"
    )


# ============================================================
# 7. mainは呼び出しだけにする
# ============================================================

def main() -> None:
    results = [
        evaluate_citation(case)
        for case in CASES
    ]

    for result in results:
        print_result(result)

    print_summary(results)


if __name__ == "__main__":
    main()
