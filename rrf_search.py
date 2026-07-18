def calculate_rrf_scores(vector_rankings: list, bm25_rankings: list, k: int = 60) -> dict:
    """
    2つの異なる検索結果の『順位リスト』を受け取り、RRFスコアを計算して統合する。
    リストは先頭(インデックス0)が1位であると仮定します。
    """
    
    rrf_scores = {}
    
    #1. ベクトル検索の順位をスコア化
    for rank, doc_id in enumerate(vector_rankings):
        actual_rank = rank + 1 #　１位、２位、３位・・・
        if doc_id not in rrf_scores:
            rrf_scores[doc_id] = 0.0
        rrf_scores[doc_id] += 1.0 / (k + actual_rank)
        
    #2. BM25検索の順位をスコア化
    for rank, doc_id in enumerate(bm25_rankings):
        actual_rank = rank + 1
        if doc_id not in rrf_scores:
            rrf_scores[doc_id] = 0.0
        rrf_scores[doc_id] += 1/(k + actual_rank)
    return rrf_scores

def main():
    #テスト用ドキュメントのIDと中身のマッピング
    doc_mapping = {
        "doc_1": "機密情報取扱申請書（様式第1号）の提出先は、法務部コンプライアンス課です。",
        "doc_2": "社外PC持出許可申請書（様式第4号）の提出先は、セキュリティチームです。",
        "doc_3": "出張経費事前申請書（様式第9号）の提出先は、総務部経費精算係です。"
    }
    
    # 🔍 ユーザーの質問: 「様式第4号の提出先はどこ？」
    # 各検索エンジンが以下のような順位を返してきたと仮定します（前回の実験結果をシミュレート）
    
    # ベクトル検索は文脈が似ているため、僅差でdoc_3を1位にしてしまったと仮定（誤検知シミュレーション）
    vector_results = ["doc_3", "doc_2", "doc_1"]
    
    # BM 25は様式第４号の文字完全一致で、doc_2を圧倒的１位、ほかは文字がないので順不同とする
    bm25_results = ["doc_2", "doc_1", "doc_3"]
    print("🏃‍♂️ RRF (Reciprocal Rank Fusion) で2つの検索結果を統合中...\n")
    
    # RRFスコアを計算
    final_rrf_scores = calculate_rrf_scores(vector_results, bm25_results, k=60)
    
    #スコアの高い順にソートしてランキングを確定
    sorted_ranking = sorted(final_rrf_scores.items(), key=lambda x: x[1], reverse=True)
    print("📊 --- RRF 最終統合ランキング ---")
    for rank, (doc_id, score) in enumerate(sorted_ranking):
        v_rank = vector_results.index(doc_id) + 1
        b_rank = bm25_results.index(doc_id) + 1
        print(f"  [{rank+1}位] ID: {doc_id} / RRFスコア: {score:.5f}")
        print(f"        (ベクトル順位: {v_rank}位, BM25順位: {b_rank}位)")
        print(f"        本文: {doc_mapping[doc_id]}\n")
        
if __name__ == "__main__":
    main()
