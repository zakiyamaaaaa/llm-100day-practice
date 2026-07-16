import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

def main():
    # 1. Chromaのクライアント初期化
    # プロジェクト内に.chroma_dataフォルダが作られ、そこに保存される
    chroma_client = chromadb.PersistentClient(path="./.chroma_data")
    
    # 2. OpenAIの埋め込みモデルを使う設定
    # これによって、Chromaに生テキストを渡すだけで、裏で勝手にOpenAI APIを叩いて、ベクトル化してくれる
    
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    
    # 3. コレクションを作成、または取得
    # embedding_functionを指定しておくことで、このコレクションへの出し入れはすべて自動でベクトル化される
    collection = chroma_client.get_or_create_collection(
        name="company_rules",
        embedding_function=openai_ef
    )
    
    # 📝 テスト用の独自ドキュメント（以前使ったもの）
    documents = [
        "社内PCを社外に持ち出す際は、必ずセキュリティチームへ貸出申請書（様式第4号）を提出し、承認を得る必要があります。貸出期間は原則最大14日間です。",
        "新宿オフィスの解錠時間は午前7:30です。それより前の時間帯は、セキュリティカードをかざしても入館できませんのでご注意ください。",
        "1冊5,000円未満の技術書籍は、各チームのテックリードの承認のみで購入可能です。5,000円以上の場合は、部門長（VP）の最終承認が必要になります。"
    ]
    
    # 各ドキュメントの一意なキー（ID）とメタデータ
    ids = ["doc_pc", "doc_office", "doc_book"]
    metadatas = [
        {"category": "security"},
        {"category": "facility"},
        {"category": "purchase"}
    ]
    
    # 🌟 4. データベースにデータを登録（初回のみ登録されます）
    # ※Chromaは重複するIDがある場合、自動で上書き（Upsert）してくれます。
    print("📥 ベクトルデータベースに社内ルールを登録中...")
    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print("✅ 登録完了！")
    
    # 🔍 5. セキュリティ検索（クエリ）の実行
    query = "会社で読むための4,000円の本を買いたいです。"
    print(f"👤 質問: {query}")

    # Chromaに直接「生の質問テキスト」を投げます。
    # 類似度計算（コサイン距離）と、上位 N 件（n_results）の絞り込みをすべてDB側が超高速で行います。
    results = collection.query(
        query_texts=[query],
        n_results=1 #最も類似度が高い１件を取得
    )
    
    # 🛠️ 6. 検索結果の展開
    # results['documents'][0][0] に、最も意味が近かった生テキストが入っています。
    # results['distances'][0][0] には「距離（L2距離など）」が入ります（数値が小さいほど似ている）
    best_match_doc = results["documents"][0][0]
    distance = results["distances"][0][0]
    
    print("\n🔎 Chroma DB からの検索結果:")
    print(f"  - 類似ドキュメント: {best_match_doc}")
    print(f"  - 距離スコア (小さいほど近い): {distance:.4f}")

if __name__ == "__main__":
    main()
