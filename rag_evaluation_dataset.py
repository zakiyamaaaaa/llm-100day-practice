from dataclasses import dataclass
from collections import Counter

from bm25_search import DOCUMENTS

@dataclass(frozen=True)
class RetrievalEvaluationCase:
    case_id: str
    category: str
    query: str
    expected_document_id: str | None
    expected_answer: str| None
    

EVALUATION_CASES = [
    RetrievalEvaluationCase(
        case_id="exact_form_number",
        category="完全一致",
        query="様式第4号の提出先はどこですか？",
        expected_document_id="doc_2",
        expected_answer=(
            "セキュリティチームです。"
        ),
    ),
    RetrievalEvaluationCase(
        case_id="pc_procedure",
        category="言い換え",
        query="社外PCを外に持ち出すときの手続きは？",
        expected_document_id="doc_2",
        expected_answer=(
            "社外PC持出許可申請書（様式第4号）を提出し、"
            "承認を得る必要があります。"
        ),
    ),
    RetrievalEvaluationCase(
        case_id="confidential_information",
        category="意味検索",
        query="機密情報を扱う申請書の提出先は？",
        expected_document_id="doc_1",
        expected_answer=(
            "法務部コンプライアンス課です。"
        ),
    ),
    RetrievalEvaluationCase(
        case_id="travel_expense",
        category="言い換え",
        query="出張経費の事前申請書はどこに提出しますか？",
        expected_document_id="doc_3",
        expected_answer=(
            "総務部経費精算係です。"
        ),
    ),
    RetrievalEvaluationCase(
        case_id="travel_form_number",
        category="完全一致",
        query="様式第9号の提出先はどこですか？",
        expected_document_id="doc_3",
        expected_answer=(
            "総務部経費精算係です。"
        ),
    ),
    RetrievalEvaluationCase(
        case_id="unknown_deadline",
        category="未回答",
        query="経費精算の締め日はいつですか？",
        expected_document_id=None,
        expected_answer=None,
    ),
    RetrievalEvaluationCase(
        case_id="unknown_book",
        category="未回答",
        query="会社で読む本を購入するには誰の承認が必要ですか？",
        expected_document_id=None,
        expected_answer=None,
    ),
    RetrievalEvaluationCase(
        case_id="security_team",
        category="完全一致",
        query="社外PC持出許可申請書の提出先は？",
        expected_document_id="doc_2",
        expected_answer=(
            "セキュリティチームです。"
        ),
    ),
]

def get_document_ids() -> set[str]:
    return { document.document_id for document in DOCUMENTS}

def validate_cases(cases: list[RetrievalEvaluationCase])-> None:
    document_ids = get_document_ids()
    case_ids = set()
    
    for case in cases:
        if not case.case_id:
            raise ValueError(
                "case_idが空の評価ケースがあります。"
            )

        if case.case_id in case_ids:
            raise ValueError(
                f"case_idが重複しています: {case.case_id}"
            )

        case_ids.add(case.case_id)

        if not case.query.strip():
            raise ValueError(
                f"質問が空です: {case.case_id}"
            )

        if (
            case.expected_document_id is not None
            and case.expected_document_id not in document_ids
        ):
            raise ValueError(
                f"存在しない文書IDです: "
                f"{case.expected_document_id}"
            )

        if (
            case.expected_document_id is None
            and case.expected_answer is not None
        ):
            raise ValueError(
                f"未回答ケースに正解回答があります: "
                f"{case.case_id}"
            )
            
def summarize_cases( cases: list[RetrievalEvaluationCase]) -> dict[str, int]:
    category_counts = Counter(case.category for case in cases)
    return dict(category_counts)

def print_cases(
    cases: list[RetrievalEvaluationCase],
) -> None:
    print("評価ケース一覧")
    print("=" * 60)

    for case in cases:
        expected = (
            case.expected_document_id
            if case.expected_document_id is not None
            else "該当文書なし"
        )

        print(f"\nID: {case.case_id}")
        print(f"分類: {case.category}")
        print(f"質問: {case.query}")
        print(f"正解文書: {expected}")
        

def main() -> None:
    validate_cases(EVALUATION_CASES)
    print_cases(EVALUATION_CASES)

    summary = summarize_cases(EVALUATION_CASES)

    print(f"評価ケース数: {len(EVALUATION_CASES)}")
    print("分類ごとの件数:")

    for category, count in summary.items():
        print(f"{category}: {count}件")
        
    print()
    print_cases(EVALUATION_CASES)
    
if __name__ == "__main__":
    main()
