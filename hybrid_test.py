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
    
    # テスト用の新しいコレクションを作成
    collection = chroma_client.get_or_create_collection(
        name="hybrid_test_rules",
        embedding_function=openai_ef
    )
    
    # 型番や数字だけが違う、似たような書類の山
    documents = [
        "機密情報取扱申請書（様式第1号）の提出先は、法務部コンプライアンス課です。",
        "社外PC持出許可申請書（様式第4号）の提出先は、セキュリティチームです。",
        "出張経費事前申請書（様式第9号）の提出先は、総務部経費精算係です。"
    ]
    ids = ["doc_1", "doc_2", "doc_3"]
    
    collection.upsert(
        documents=documents, ids=ids
    )
    
    # 🔍 意地悪な質問（「様式第4号」をピンポイントで探したい）
    query = "様式第4号はどこに出せばいい？"
    print(f"👤 質問: {query}\n")
    
    # 上位３件をすべて取得して、スコアを確認する
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    
    print("🔎 検索結果:")
    for i in range(3):
        doc = results['documents'][0][i]
        distance = results['distances'][0][i]
        doc_id = results['ids'][0][i]
        print(f"  [{i+1}位] ID: {doc_id} / 距離: {distance:.4f}")
        print(f"        本文: {doc}")

if __name__ == "__main__":
    main()
