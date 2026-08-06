from dataclasses import dataclass
from enum import StrEnum

class FailureType(StrEnum):
    """
    RAG処理の最終判定。

    SUCCESS:
        正しく回答できた。

    EXPECTED_NO_ANSWER:
        文書に情報がなく、正しく拒否できた。

    RETRIEVAL_FAILURE:
        回答に必要な文書を取得できなかった。

    GENERATION_FAILURE:
        Contextはあるが、回答生成に失敗した。

    CITATION_FAILURE:
        回答は生成されたが、引用に問題がある。
    """

    SUCCESS = "success"
    EXPECTED_NO_ANSWER = "expected_no_answer"
    RETRIEVAL_FAILURE = "retrieval_failure"
    GENERATION_FAILURE = "generation_failure"
    CITATION_FAILURE = "citation_failure"
    
@dataclass(frozen=True)
class FailureThresholds:
    """
    解答を許可するための閾値
    
    reranker_score: 候補文書と質問の関連度
    relevance_score: 生成された「解答が質問にどれくらい適切に答えているか
    """
    min_reranker_score: float = 0.70
    min_relevance_score: float = 0.70
    
@dataclass(frozen=True)
class EvaluationSignals:
    """
    1ケース分の評価シグナル
    実際の検索・生成・引用処理から、判定に必要な情報だけを集めたもの
    """
    
    case_id:str
    
    # 正解文書が存在するか。Noneの場合は、正解文書なしの未回答ケース
    expected_document_id: str | None
    #検索で取得した文書ID一覧
    retrieved_document_ids: list[str]
    
    # Rerankerの１位文書の関連度スコア
    top_reranker_score: float | None
    
    # Generation評価の結果
    is_grounded: bool
    relevance_score: float
    is_answer_correct: bool
    
    # Citation評価の結果
    # 引用評価をまだ実行していない場合はNoneにする
    citation_supported: bool | None
    citation_correct: bool | None
    
@dataclass(frozen=True)
class FailureClassification:
    """失敗分類の結果"""
    case_id: str
    failure_type: FailureType
    should_refuse: bool
    reason: str
    
def classify_failure(signals: EvaluationSignals, thresholds: FailureThresholds,) -> FailureClassification:
    """
    1ケース分の評価シグナルから、失敗分類を行う。
    
     判定順序:

    1. 検索失敗を確認する
    2. 生成失敗を確認する
    3. 引用失敗を確認する
    4. 問題がなければ成功と判定する

    検索に失敗している場合は、
    後続の生成・引用を評価しても根本原因が分かりづらい。
    そのため、検索失敗を最初に確認する
    """

    # 正解文書が存在するケースの場合
    if signals.expected_document_id is not None:
        expected_document_id = signals.expected_document_id
        
        # 正解文書が検索結果に含まれていない場合、LLMへ正しい情報を渡せないため検索失敗とする
        if expected_document_id not in signals.retrieved_document_ids:
            return FailureClassification(
                case_id=signals.case_id,
                failure_type=FailureType.RETRIEVAL_FAILURE,
                should_refuse=True,
                reason=f"Expected document '{expected_document_id}' not found in retrieved documents: {signals.retrieved_document_ids}"
            )
        # Rerankerスコアが存在し、閾値未満の場合、Contextの関連性が低いと判断する
        if signals.top_reranker_score is not None and signals.top_reranker_score < thresholds.min_reranker_score:
            return FailureClassification(
                case_id=signals.case_id,
                failure_type=FailureType.RETRIEVAL_FAILURE,
                should_refuse=True,
                reason=f"Top reranker score {signals.top_reranker_score} is below threshold {thresholds.min_reranker_score}"
            )
            
        # Contextは取得できたが、LLMの解答が根拠に基づいていない場合は生成失敗
        if not signals.is_grounded:
            return FailureClassification(
                case_id=signals.case_id,
                failure_type=FailureType.GENERATION_FAILURE,
                should_refuse=True,
                reason="Generated answer is not grounded in the provided context"
            )
            
        # 質問への適切さが閾値未満の場合も生成失敗
        if signals.relevance_score < thresholds.min_relevance_score:
            return FailureClassification(
                case_id=signals.case_id,
                failure_type=FailureType.GENERATION_FAILURE,
                should_refuse=True,
                reason=f"Relevance score {signals.relevance_score} is below threshold {thresholds.min_relevance_score}"
            )
            
        # 正解と同じ意味の解答になっていない場合
        if not signals.is_answer_correct:
            return FailureClassification(
                case_id=signals.case_id,
                failure_type=FailureType.GENERATION_FAILURE,
                should_refuse=True,
                reason="Generated answer is not semantically equivalent to the expected answer"
            )
    # 正解文書がない未回答ケースの場合
    else:
        # 文書がない質問に対し、正しく拒否できた場合は失敗ではない
        if signals.is_answer_correct and not signals.is_grounded:
            if signals.citation_correct is False:
                return FailureClassification(
                    case_id=signals.case_id,
                    failure_type=FailureType.CITATION_FAILURE,
                    should_refuse=True,
                    reason="Answer is correct but citation is incorrect"
                )
            return FailureClassification(
                case_id=signals.case_id,
                failure_type=FailureType.EXPECTED_NO_ANSWER,
                should_refuse=True,
                reason="Correctly refused to answer a question with no expected document"
            )
    # Citation評価を実行済の場合だけ確認する
    if signals.citation_supported is False or signals.citation_correct is False:
        return FailureClassification(
            case_id=signals.case_id,
            failure_type=FailureType.CITATION_FAILURE,
            should_refuse=True,
            reason="Citation evaluation failed"
        )
    # ここまで問題がなければ成功。
    return FailureClassification(
        case_id=signals.case_id,
        failure_type=FailureType.SUCCESS,
        should_refuse=False,
        reason="検索・生成・引用に問題ありません。",
    )
    

def print_classification(classification: FailureClassification):
    """失敗分類を表示する。"""

    print("=" * 60)
    print(f"ID: {classification.case_id}")
    print(f"分類: {classification.failure_type.value}")
    print(f"拒否するか: {classification.should_refuse}")
    print(f"理由: {classification.reason}")

def main() -> None:
    """
    例として3種類のケースを分類する。

    実務では、ここに固定データを書くのではなく、
    Retrieval・Generation・Citationの実測結果を渡す。
    """
    
    thresholds = FailureThresholds(
        min_reranker_score=0.70,
        min_relevance_score=0.70,
    )
    
    examples = [
        EvaluationSignals(
            case_id="retrieval_failure",
            expected_document_id="doc_2",
            retrieved_document_ids=[],
            top_reranker_score=None,
            is_grounded=False,
            relevance_score=0.0,
            is_answer_correct=False,
            citation_supported=None,
            citation_correct=None,
        ),
        EvaluationSignals(
            case_id="generation_failure",
            expected_document_id="doc_2",
            retrieved_document_ids=["doc_2"],
            top_reranker_score=0.95,
            is_grounded=False,
            relevance_score=0.40,
            is_answer_correct=False,
            citation_supported=True,
            citation_correct=True,
        ),
        EvaluationSignals(
            case_id="unknown_correct_refusal",
            expected_document_id=None,
            retrieved_document_ids=[],
            top_reranker_score=None,
            is_grounded=False,
            relevance_score=1.0,
            is_answer_correct=True,
            citation_supported=True,
            citation_correct=True,
        ),
    ]
    
    for signals in examples:
        result = classify_failure(signals, thresholds)
        print_classification(result)
        
if __name__ == "__main__":
    main()
