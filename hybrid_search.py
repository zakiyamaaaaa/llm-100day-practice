import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

def main():
    chroma_client = chromadb.PersistentClient(path="./.chroma_data")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    
    # 前回作成したコレクションを取得
    collection = chroma_client.get_collection(
        name="hybrid_test_rules",
        embedding_function=openai_ef
    )
    
    # ユーザーの質問と、絶対に外したくない重要キーワード
    query = "様式第4号の提出先はどこですか？"
    keyword_target = "様式第4号"
    
    print(f"👤 質問: {query}")
    print(f"🔑 必須キーワード: '{keyword_target}'\n")

    # 1. まずは通常通りベクトル検索（全3件を取得）
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    
    hybrid_results = []
    
    # 検索結果をループで回し、キーワードボーナスを計算して再スコアリング
    for i in range(3):
        doc = results['documents'][0][i]
        distance = results['distances'][0][i]
        doc_id = results['ids'][0][i]
        
        # コサイン距離（0.0=近い）を類似度スコア(1.0=近い)に反転
        base_similarity = 1.0 - distance
        
        # キーワード検索の融合：ホヌんにターゲット文字列が含まれるか判定
        bonus_score = 0.0
        if keyword_target in doc:
            bonus_score = 0.5 # キーワードが含まれる場合はボーナスを加算
        
        final_score = base_similarity + bonus_score
        
        hybrid_results.append({
            "id": doc_id,
            "text": doc,
            "base_similarity": base_similarity,
            "bonus": bonus_score,
            "final_score": final_score
        })
        
    # 最終的なハイブリッドスコアの降順で並び替え
    hybrid_results.sort(key=lambda x: x["final_score"], reverse=True)
    
    print("🔎 ハイブリッド検索結果（ベクトル検索 + キーワードボーナス）:")
    for rank, res in enumerate(hybrid_results):
        print(f"  [{rank+1}位] ID: {res['id']} / 最終スコア: {res['final_score']:.4f}")
        print(f"        (ベース意味類似度: {res['base_similarity']:.4f}, キーワードボーナス: {res['bonus']})")
        print(f"        本文: {res['text']}\n")

if __name__ == "__main__":
    main()
    