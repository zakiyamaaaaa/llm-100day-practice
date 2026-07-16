import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

load_dotenv()
client = OpenAI()

def main():
    #1. Chroma DBクライアント初期化
    chroma_client = chromadb.PersistentClient(path="./.chroma_data")
    
    #2. OpenAIの埋め込み関数を定義
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    
    #3, company_resultsコレクションを取得
    collection = chroma_client.get_collection(
        name="company_rules",
        embedding_function=openai_ef
    )
    
    # ユーザーからの質問
    query = "会社で読むための4,000円の技術書を買いたいのですが、どうすればいいですか？"
    print(f"👤 質問: {query}")
    
    #4. Chroma DBから最も関連度の高い情報を１件検索
    results = collection.query(
        query_texts=[query],
        n_results=1
    )
    
    # 検索されたコンテキストを抽出
    if results['documents'] and results['documents'][0]:
        context = results['documents'][0][0]
        distance = results['distances'][0][0]
        print(f"🔎 データベースから関連ドキュメントを検出しました。 (コサイン距離: {distance:.4f})")
    else:
        context = "関連情報が見つかりませんでした。"
        print("⚠️ 関連ドキュメントが見つかりませんでした。")
    
    # 🌟 5. 取得したコンテキストを元に、LLM用のプロンプトを構築 (Augmentation & Generation)
    system_prompt = f"""
    あなたは親切な社内ヘルプデスクAIです。
    必ず以下の【提供された参考情報】に書かれている事実のみに基づいて、ユーザーの質問に回答してください。
    もし情報が不足していて回答できない場合は、知ったかぶりをせず「社内ドキュメントにその情報は記載されていません」と正直に答えてください。

    【提供された参考情報】
    {context}
    """
    
    print("🤖 AIがデータベースの情報に基づいて回答を生成中...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.0 # RAGでは妄想を防ぐために0.0にするのが鉄則です
    )
    
    # 🌟 6. 最終回答を出力
    print("\n🤖 AIの回答:")
    print(response.choices[0].message.content)
    
if __name__ == "__main__":
    main()
