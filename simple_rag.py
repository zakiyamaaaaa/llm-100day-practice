import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# 📝 1. LLMが絶対に知らない「架空の独自ドキュメント（知識ベース）」
# ※実務では、ここがPDFだったり、データベースだったりします。
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

# 2.ユーザーの質問から、関連する「カンニングペーパー」を検索する関数（最もシンプルな簡易検索）
def retrieve_relevant_docs(query: str) -> str:
    print(f"🔎 独自の知識ベースから「{query}」に関連する情報を検索中...")
    relevant_texts = []
    
    # 今回はシンプルに、質問に含まれるキーワードがドキュメントに含まれているかで簡易判定します
    for doc in KNOWLEDGE_BASE:
        keywords = ["PC", "持ち出し", "貸出", "解錠", "入館", "書籍", "本", "購入"]
        for kw in keywords:
            if kw in query and kw in doc["content"]:
                relevant_texts.append(f"【参考情報: {doc['title']}】\n{doc['content']}")
                break # 重複を避けるため
    
    if not relevant_texts:
        return "関連する情報は見つかりませんでした。"
    
    # 見つかった複数のドキュメントを１つのテキストに結合して返す
    return "\n\n".join(relevant_texts)

# 3.カンニングペパーを元に、LLMに回答させる関数
def ask_with_rag(user_query: str):
    context = retrieve_relevant_docs(user_query)
    # ステップ2: 拡張（Augmentation）と生成（Generation）
    # LLMに渡すシステムプロンプトに「提供された参考情報（コンテキスト）だけを読め」とルールを縛る
    system_prompt = f"""
    あなたは親切な社内ヘルプデスクAIです。
    必ず以下の【提供された参考情報】に書かれている事実のみに基づいて、ユーザーの質問に回答してください。
    もし情報が不足していて回答できない場合は、知ったかぶりをせず「社内ドキュメントにその情報は記載されていません」と正直に答えてください。

    【提供された参考情報】
    {context}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0.0 # RAGでは、LLMのクリエイティビティ（妄想）を極限まで抑えるため「0.0」にするのが鉄則です
    )
    
    return response.choices[0].message.content

def main():
    # 🧪 テストパターンA：独自知識がないと答えられない質問
    query_a = "新しく発売された技術書（4,500円）を買いたいのですが、誰の承認が必要ですか？"
    print(f"質問: {query_a}")
    answer_a = ask_with_rag(query_a)
    print(f"AIの回答:\n{answer_a}\n")
    print("-" * 50 + "\n")

    # 🧪 テストパターンB：知識ベースにない、答えられないはずの質問
    query_b = "経費精算の締め日はいつですか？"
    print(f"質問: {query_b}")
    answer_b = ask_with_rag(query_b)
    print(f"AIの回答:\n{answer_b}\n")

if __name__ == "__main__":
    main()
