from argparse import ArgumentParser
from openai import OpenAI
from answer_with_citations import GroundedAnswer, answer_question
from bm25_search import DOCUMENTS
from hybrid_rag_pipeline import RetrievalContext, build_retrieval_context
from rag_evaluation_dataset import EVALUATION_CASES, RetrievalEvaluationCase

DEFAULT_EVALUATION_LIMIT = 2

def build_application(client: OpenAI) -> RetrievalContext:
    """
    Production RAGで共有する検索Contextを作成する
    
    文書EmbeddingやBM25Indexは質問ごとに作り直さない
    アプr起動時に一度だけ作成し、複数の質問で再利用する。
    """
    
    return build_retrieval_context(client, documents=DOCUMENTS)

def run_query(
    client: OpenAI,
    retrieval_context: RetrievalContext,
    query: str,
    candidate_count: int = 3,
) -> GroundedAnswer:
    """
    1つの質問をRAG Pipelineへ渡す
    
    answer_question()の中で、次の処理が実行される
    
    1. BM25,Vector検索
    2. RRF
    3. Reranker
    4. Context Builder
    5. LLM解答生成
    6. 引用元検証
    """
    
    # APIやCLIごとにRAGの内部処理を書き直さず、共通関数へ委譲する。
    return answer_question(
        client=client,
        retrieval_context=retrieval_context,
        query=query,
        candidate_count=candidate_count,
    )
    
def is_smoke_test_passed(case: RetrievalEvaluationCase, answer: GroundedAnswer) -> bool:
    """
    RAGの基本的な契約を確認する
    
    回答可能ケース：answeredで正解文書をsourcesに含むこと
    
    未回答ケース：refusedでsourcesが空であること
    
    これは簡易的なSmoke Testであり、回答内容の意味評価は別のGeneration評価を行う
    """
    
    # 正解文書がないケース
    if case.expected_document_id is None:
        return answer.status == "refused" and answer.sources == []
    
    # 正解文書があるケース
    return (answer.status == "answered" and case.expected_document_id in answer.sources)

def run_smoke_evaluation(client: OpenAI, retrieval_context: RetrievalContext, cases: list[RetrievalEvaluationCase])->None:
    """
    複数の評価ケースを統合住みPipelineで実行する
    
    各ケースでAPIを使用するため、最初は２件程度に制限して実行する
    """
    
    passed_count = 0
    
    print("\n[Smoke Test開始]")
    
    for case in cases:
        answer = run_query(
            client=client,
            retrieval_context=retrieval_context,
            query = case.query
        )
        
        passed = is_smoke_test_passed(case, answer)
        
        if passed:
            passed_count += 1
            
        expected = (
            case.expected_document_id
            if case.expected_document_id is not None
            else "正解文書なし"
        )
        
        print("=" * 60)
        print(f"ID: {case.case_id}")
        print(f"期待する文書: {expected}")
        print(f"status: {answer.status}")
        print(f"sources: {answer.sources}")
        print(f"判定: {'PASS' if passed else 'FAIL'}")

        if answer.refusal_reason:
            print(f"拒否理由: {answer.refusal_reason}")
            
    print("\n[Smoke Evaluation Summary]")
    print(
        f"{passed_count}/{len(cases)} "
        f"({passed_count / len(cases):.2%})"
    )
    
def build_parser() -> ArgumentParser:
    """
    コマンドライン引数を定義する
    """
    
    parser = ArgumentParser(
        description="Production RAG v1を実行する"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_EVALUATION_LIMIT,
        help=(
            "実行する評価ケース数。"
            "API費用を抑えるため、初期値は2件。"
        ),
    )

    return parser

def select_cases(limit: int)->list[RetrievalEvaluationCase]:
    """
    評価ケースを先頭から指定件数だけ取得する
    """
    
    if limit <= 0:
        raise ValueError("limitは1以上の整数である必要があります")
    return EVALUATION_CASES[:limit]

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    
    client = OpenAI()
    
    retrieval_context = build_application(client)
    
    case = select_cases(args.limit)
    
    run_smoke_evaluation(
        client=client,
        retrieval_context=retrieval_context,
        cases=case,
    )
    
if __name__ == "__main__":
    main()
