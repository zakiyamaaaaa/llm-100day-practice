import time
from dataclasses import dataclass
from openai import OpenAI

from bm25_search import DOCUMENTS
from evaluate_rag import EVALUATION_CASES
from hybrid_rag_pipeline import (
    build_retrieval_context,
    retrieve_candidates
)
from llm_reranker import RerankItem, rerank_documents

CANDIDATE_COUNT = 3

@dataclass(frozen=True)
class CaseMeasurement:
    """１つの評価ケースについて、Reranker前後の結果と処理時間を保存する"""
    case_id: str
    expected_document_id: str
    rrf_ranking: list[str]
    reranked_ranking: list[str]
    retrieval_latency_ms: float
    reranker_latency_ms: float
    
def get_answerable_cases():
    """
    正解文書が存在する評価ケースだけを返す
    
    未回答ケースには正解文書がないため、Hit@1やMRRの通常評価には含めない
    """
    
    return [
        case
        for case in EVALUATION_CASES
        if case.expected_document_id is not None
    ]
    
def find_rank(document_id: str, ranking: list[str]) -> int | None:
    """
    文書IDがランキングの何位にあるかを返す。

    ランキングに存在しない場合はNoneを返す。
    """
    
    for rank, ranked_document_id in enumerate(ranking, start=1):
        if ranked_document_id == document_id:
            return rank
    return None

def get_retrieval_ranking(rrf_ranking: list[tuple[str, float]],)->list[str]:
    """
    RRF結果から文書IDだけを取り出す。

    RRFのスコア自体は表示用に使えるが、
    評価では順位だけを比較する。
    """
    
    return [
        document_id
        for document_id, score in rrf_ranking
    ]
    
def get_reranked_ranking(reranked_results: list[RerankItem],)->list[str]:
    """
    Reranker結果から文書IDだけを取り出す。

    Rerankerのスコア自体は表示用に使えるが、
    評価では順位だけを比較する。
    """
    
    return [
        result.document_id
        for result in reranked_results
    ]
    

def measure_case(client: OpenAI, context, case,) -> CaseMeasurement:
    """
    1ケースについてRetrieverとRerankerを測定する。

    処理の流れ:

    1. BM25・Vector・RRFで候補を取得する
    2. Retrieverの処理時間を測る
    3. 候補文書をRerankerへ渡す
    4. Rerankerの処理時間を測る
    5. Before/Afterのランキングを保存する
    """
    
    # Retrieverの開始時刻を記録
    retrieval_started_at = time.perf_counter()
    
    candidates, rrf_ranking = retrieve_candidates(
        client=client,
        context=context,
        query = case.query,
        candidate_count=CANDIDATE_COUNT
    )
    
    # perf_counter()は短い処理時間の測定に適した時計
    retrieval_finished_at = time.perf_counter()
    
    #　開始から終了までの秒数をミリ秒へ変換する
    retrieval_latency_ms = (retrieval_finished_at - retrieval_started_at)*1000
    
    # Retrieverが集めた候補文書だけをRerankerへ渡す
    # Rerankerは候補外の文書を新しく発見できない
    reranker_started_at = time.perf_counter()
    
    reranked_results = rerank_documents(client=client, query=case.query, candidates=candidates)
    
    reranker_finished_at = time.perf_counter()
    
    reranker_latency_ms = (reranker_finished_at - reranker_started_at)*1000
    
    return CaseMeasurement(
        case_id=case.case_id,
        expected_document_id=case.expected_document_id,
        rrf_ranking=get_retrieval_ranking(rrf_ranking),
        reranked_ranking=get_reranked_ranking(reranked_results),
        retrieval_latency_ms=retrieval_latency_ms,
        reranker_latency_ms=reranker_latency_ms
    )
    
def calculate_hit_at_1(ranking: list[str], expected_document_id: str)->bool:
    """
    正解文書がランキング1位かを判定
    """
    
    return bool(
        ranking and ranking[0] == expected_document_id
    )
    
def calculate_mrr(measurements: list[CaseMeasurement], use_reranker: bool,) -> float:
    """
    RRFまたはReranker後のMRRを計算する。

    use_rerankerがFalse:
        RRFランキングを使う

    use_rerankerがTrue:
        Reranker後のランキングを使う
    """
    
    
    reciprocal_ranks: list[float] = []

    for measurement in measurements:
        if use_reranker:
            ranking = (
                measurement.reranked_ranking
            )
        else:
            ranking = measurement.rrf_ranking

        rank = find_rank(
            document_id=(
                measurement.expected_document_id
            ),
            ranking=ranking,
        )

        if rank is None:
            reciprocal_ranks.append(0.0)
        else:
            reciprocal_ranks.append(
                1.0 / rank
            )

    if not reciprocal_ranks:
        return 0.0

    return sum(reciprocal_ranks) / len(
        reciprocal_ranks
    )

def print_case_results(
    measurements: list[CaseMeasurement],
) -> None:
    """
    ケースごとのBefore/Afterを表示する。
    """

    print("\nケース別評価")
    print("=" * 60)

    for measurement in measurements:
        rrf_hit = calculate_hit_at_1(
            ranking=measurement.rrf_ranking,
            expected_document_id=(
                measurement.expected_document_id
            ),
        )

        reranked_hit = calculate_hit_at_1(
            ranking=(
                measurement.reranked_ranking
            ),
            expected_document_id=(
                measurement.expected_document_id
            ),
        )

        print(f"\nID: {measurement.case_id}")
        print(
            f"正解文書: "
            f"{measurement.expected_document_id}"
        )
        print(
            f"RRF順位: "
            f"{measurement.rrf_ranking}"
        )
        print(
            f"Reranker順位: "
            f"{measurement.reranked_ranking}"
        )
        print(f"RRF Hit@1: {rrf_hit}")
        print(
            f"Reranker Hit@1: "
            f"{reranked_hit}"
        )
        print(
            f"Retriever latency: "
            f"{measurement.retrieval_latency_ms:.2f} ms"
        )
        print(
            f"Reranker latency: "
            f"{measurement.reranker_latency_ms:.2f} ms"
        )


def print_summary(
    measurements: list[CaseMeasurement],
) -> None:
    """
    全体指標を表示する。

    API呼び出し回数は、今回のコードの構造から数える。

    - 文書Embedding: 文書数分
    - Query Embedding: 評価ケース数分
    - Reranker API: 評価ケース数分

    リトライは考慮していない。
    """

    total_count = len(measurements)

    rrf_hit_count = sum(
        calculate_hit_at_1(
            ranking=measurement.rrf_ranking,
            expected_document_id=(
                measurement.expected_document_id
            ),
        )
        for measurement in measurements
    )

    reranked_hit_count = sum(
        calculate_hit_at_1(
            ranking=(
                measurement.reranked_ranking
            ),
            expected_document_id=(
                measurement.expected_document_id
            ),
        )
        for measurement in measurements
    )

    average_retrieval_latency = (
        sum(
            measurement.retrieval_latency_ms
            for measurement in measurements
        )
        / total_count
        if total_count > 0
        else 0.0
    )

    average_reranker_latency = (
        sum(
            measurement.reranker_latency_ms
            for measurement in measurements
        )
        / total_count
        if total_count > 0
        else 0.0
    )

    document_embedding_calls = len(DOCUMENTS)
    query_embedding_calls = total_count
    reranker_calls = total_count

    print("\n" + "=" * 60)
    print("全体評価")
    print("=" * 60)

    print(
        f"RRF Hit@1: "
        f"{rrf_hit_count}/{total_count} "
        f"({rrf_hit_count / total_count:.2%})"
    )

    print(
        f"Reranker Hit@1: "
        f"{reranked_hit_count}/{total_count} "
        f"({reranked_hit_count / total_count:.2%})"
    )

    print(
        f"RRF MRR: "
        f"{calculate_mrr(measurements, False):.4f}"
    )

    print(
        f"Reranker MRR: "
        f"{calculate_mrr(measurements, True):.4f}"
    )

    print(
        f"平均Retriever latency: "
        f"{average_retrieval_latency:.2f} ms"
    )

    print(
        f"平均Reranker latency: "
        f"{average_reranker_latency:.2f} ms"
    )

    print("\n論理API呼び出し回数")
    print(
        f"文書Embedding: "
        f"{document_embedding_calls}回"
    )
    print(
        f"Query Embedding: "
        f"{query_embedding_calls}回"
    )
    print(
        f"Reranker: "
        f"{reranker_calls}回"
    )

def main() -> None:
    """
    RRFとRerankerの定量比較を実行する。
    """
    
    client = OpenAI()
    
    answerable_cases = get_answerable_cases()
    
    # ここで文書Embeddingを作成する
    # 全評価ケースで使い回すため、ケースごとには作らない
    context = build_retrieval_context(client=client, documents=DOCUMENTS)
    
    measurements: list[
        CaseMeasurement
    ] = []

    for case in answerable_cases:
        measurement = measure_case(
            client=client,
            context=context,
            case=case,
        )

        measurements.append(measurement)

    print_case_results(measurements)
    print_summary(measurements)

if __name__ == "__main__":
    main()
