import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# 📝 1. 独自の知識ベース（simple_rag.pyと同じもの）
KNOWLEDGE_BASE = [
    {
        "id": "doc_1",
        "title": "社内PCの貸出ルール",
        "content": "社内PCを社外に持ち出す際は、必ずセキュリティチームへ貸出申請書（様式第4号）を提出し、承認を得る必要があります。貸出期間は原則最大14日間です。"
    },
    {
        "id": "doc_2",
        "title": "オフィス解錠方法",
        "content": "新宿オフィスの解錠時間は午前7:30です。それより前の時間帯は、セキュリティカードをかざしても入館できませんのでご注意ください。"
    },
    {
        "id": "doc_3",
        "title": "技術書籍の購入申請",
        "content": "1冊5,000円未満の技術書籍は、各チームのテックリードの承認のみで購入可能です。5,000円以上の場合は、部門長（VP）の最終承認が必要になります。"
    }
]

# 2. テキストを1536次元のベクトルに変換する関数
def get_embedding(text: str) -> List[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# 3. 2つのベクトルの内積（コサイン類似度）を計算する関数
def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    return sum(a * b for a, b in zip(vec_a, vec_b))

# 4. ベクトルを用いたセマンティック検索関数
def retrieve_relevant_docs_vector(query: str, threshold: float = 0.3) -> str:
    print(f"🔎 独自の知識ベースから「{query}」に関連する情報をベクトル検索中...")
    
    # step1: ユーザーの質問をベクトル化
    query_embedding = get_embedding(query)
    relevant_texts = []
    
    # step2: 知識ベース内でのすべてのドキュメントと類似度を比較
    for doc in KNOWLEDGE_BASE:
        # 本文をベクトル化
        # 実務では、ドキュメントのベクトルは事前に計算してDBに保存する
        doc_embedding = get_embedding(doc["content"])
        
        # 類似度を計算
        similarity = cosine_similarity(query_embedding, doc_embedding)
        
        # 一定の類似度を超えたものだけを候補にする
        if similarity >= threshold:
            relevant_texts.append((similarity, doc))
    
    relevant_texts.sort(key=lambda x: x[0], reverse=True)  # 類似度の高い順にソート
    
    if not relevant_texts:
        return "関連する情報は見つかりませんでした。"
    
    #　最も類似度が高かったドキュメントの本文を返す
    best_doc = relevant_texts[0][1]
    return f"【参考情報: {best_doc['title']}】\n{best_doc['content']}"
    
    
# 5. RAG実行関数
def ask_with_vector_rag(user_query: str):
    # step1: ベクトルによる意味検索
    context = retrieve_relevant_docs_vector(user_query)
    
    # step2: LLMへの問い合わせ
    system_prompt = f"""
    必ず以下の【提供された参考情報】に書かれている事実のみに基づいて、ユーザーの質問に回答してください。
    【提供された参考情報】
    {context}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0.0
    )
    return response.choices[0].message.content

def main():
    # 🧪 昨日「記載されていません」とフラれた、表記ゆれだらけの質問
    query = "新しく発売された技術書（4,500円）を買いたいのですが、誰の承認が必要ですか？"
    
    print(f"ユーザーの質問: {query}")
    answer = ask_with_vector_rag(query)
    print(f"\n🤖 AIの回答:\n{answer}")

if __name__ == "__main__":
    main()
