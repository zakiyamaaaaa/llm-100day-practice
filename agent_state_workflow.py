from dataclasses import dataclass
from typing import Literal
from openai import OpenAI
from pydantic import BaseModel

# 1. LLMに質問の種類を判定させるための型

class RouteDecision(BaseModel):
    route: Literal["search", "unsupported"]
    reason: str
    
# 2. エージェントが処理中に持ち回る状態
@dataclass
class AgentState:
    question: str
    route: str = ""
    context: str = ""
    answer: str = ""
    current_node:str = ""
    
# 3. 今回使用する簡易的な文書データ

DOCUMENTS = [
    {
        "id": "doc_1",
        "keywords": ["機密情報", "様式第1号"],
        "text": (
            "機密情報取扱申請書（様式第1号）の提出先は、"
            "法務部コンプライアンス課です。"
        ),
    },
    {
        "id": "doc_2",
        "keywords": ["社外PC", "様式第4号"],
        "text": (
            "社外PC持出許可申請書（様式第4号）の提出先は、"
            "セキュリティチームです。"
        ),
    },
    {
        "id": "doc_3",
        "keywords": ["出張経費", "様式第9号"],
        "text": (
            "出張経費事前申請書（様式第9号）の提出先は、"
            "総務部経費精算係です。"
        ),
    },
]

# 4. Node: 質問のルートをLLMに判断させる
def classify_question(client: OpenAI, question: str) -> RouteDecision:
    """
    質問を分類する。

    今回は、社内文書を検索すべき質問かどうかだけを判定する。
    Structured Outputを使うことで、routeの値を制限している。
    """
    
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        temperature=0,
        response_format=RouteDecision,
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたは質問ルーターです。"
                    "社内申請書や社内手続きに関する質問ならsearch、"
                    "それ以外ならunsupportedを返してください。"
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )
    
    parsed_result = response.choices[0].message.parsed
    
    if parsed_result is None:
        raise ValueError("質問分類の結果を取得できませんでした。")
    
    return parsed_result

# 5. Node: 簡易検索を実行する

def retrieve_context(question: str) -> str:
    """
    質問に含まれるキーワードを使って文書を検索する。

    ここではDay41の目的を「状態と分岐」に絞るため、
    BM25やベクトル検索ではなく簡易検索にしている。
    """
    matched_documents = []
    
    for document in DOCUMENTS:
        is_matched = any(keyword in question for keyword in document["keywords"] )
        
        if is_matched:
            matched_documents.append(f'[{document["id"]}] {document["text"]}')
            
    return "\n".join(matched_documents)

# 6. Node: 参考情報を使って回答を生成する
def generate_answer(client: OpenAI, question: str, context: str) -> str:
    """
    検索で得たcontextだけを根拠に回答を生成する。

    contextに書かれていない情報を推測しないように指示する。
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたは社内文書回答アシスタントです。"
                    "必ず参考情報だけを根拠に回答してください。"
                    "参考情報にない場合は、"
                    "「参考情報に記載されていません」と回答してください。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"質問:\n{question}\n\n"
                    f"参考情報:\n{context}"
                ),
            },
        ],
    )
    
    return response.choices[0].message.content or ""

# 7. Node: 質問分類を実行する
def classify_node(client: OpenAI, state: AgentState) -> str:
    """
    質問分類ノード。

    戻り値が次のノード名になる。
    これがエッジ、つまり処理の分岐に相当する。
    """
    
    decision = classify_question(client, state.question)
    state.route = decision.route
    if decision.route == "search":
        return "retrieve"
    return "fallback"

# 8. Node: 検索を実行する
def retrieve_node(client: OpenAI, state: AgentState) -> str:
    """
    検索ノード。

    contextが見つかればgenerateへ進み、
    見つからなければfallbackへ進む。
    """
    state.context = retrieve_context(state.question)
    if state.context:
        return "generate"
    return "fallback"

# 9. Node: 回答生成を実行する
def generate_node(client: OpenAI, state: AgentState) -> str:
    """
    回答生成ノード。

    回答をstateに保存して終了する。
    """
    
    state.answer = generate_answer(client = client, question = state.question, context = state.context)
    return "end"

# 10. Node: 回答できない場合の処理
def fallback_node(client: OpenAI, state: AgentState) -> str:
    """
    検索対象外、または文書が見つからない場合の終了処理。
    """
    state.answer = "参考情報に記載されていないため、回答できません。"
    return "end"

# 11. ワークフロー全体を実行する
def run_workflow(client: OpenAI, question: str) -> AgentState:
    """
    ノードを順番に実行する。

    node_handlersが、ノード名と処理関数の対応表になる。
    """
    state = AgentState(question=question)
    node_handlers = {
        "classify": classify_node,
        "retrieve": retrieve_node,
        "generate": generate_node,
        "fallback": fallback_node,
    }
    
    next_node = "classify"
    
    # next_nodeがendになるまで、ノードを順番に実行する
    while next_node != "end":
        state.current_node = next_node

        handler = node_handlers[next_node]
        next_node = handler(client, state)

    state.current_node = "end"

    return state

# 12. 実行結果を表示する
def print_result(state: AgentState) -> None:
    """エージェントの処理結果を表示する。"""

    print("=" * 60)
    print(f"質問: {state.question}")
    print(f"ルート: {state.route}")
    print(f"最終ノード: {state.current_node}")
    print(f"回答: {state.answer}")
    
# 13. mainは処理の呼び出しだけにする
def main() -> None:
    client = OpenAI()
    
    question = "様式第4号の提出先はどこですか？"
    
    result = run_workflow(client=client, question=question)
    print_result(result)
    
if __name__ == "__main__":
    main()

