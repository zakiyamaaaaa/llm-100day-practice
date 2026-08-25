import sqlite3
import sys
from langgraph.checkpoint.sqlite import SqliteSaver


from typing import Callable, Literal, TypedDict

from openai import OpenAI
from langgraph.graph import END, START, StateGraph

from agent_state_workflow import (
    classify_question,
    generate_answer,
    retrieve_context,
)


class GraphState(TypedDict, total=False):
    """
    LangGraphがNode間で受け渡す状態。

    LangGraphでは、各NodeがこのStateを読み取り、
    更新したいフィールドだけを辞書で返す。
    """

    # ユーザーから受け取った質問
    question: str

    # LLMが分類した質問の種類
    route: str

    # LLMが返した分類理由
    reason: str

    # 検索で取得した参考情報
    context: str

    # 最終的に生成された回答
    answer: str

    # 現在実行されたNode名
    current_node: str
    
    node_history: list[str]


def make_classify_node(
    client: OpenAI,
) -> Callable[[GraphState], dict[str, str]]:
    """
    LLMによる質問分類Nodeを作成する。

    clientを閉じ込めた関数を返すことで、
    Nodeの実行時に同じOpenAIクライアントを再利用できる。
    """

    def classify_node(
        state: GraphState,
    ) -> dict[str, str]:
        """
        質問をLLMへ渡し、Structured OutputをStateへ保存する。

        LLMの自由文をそのまま分岐に使わず、
        RouteDecisionで検証されたrouteだけを利用する。
        """

        # 既存のLLM分類処理を再利用する
        decision = classify_question(
            client=client,
            question=state["question"],
        )

        # Nodeは次のNode名を返すのではなく、
        # Graphが使うStateの更新内容を返す
        return {
            "route": decision.route,
            "reason": decision.reason,
            "current_node": "classify",
            "node_history": state.get("node_history", []) + ["classify"],
        }

    return classify_node


def route_after_classify(
    state: GraphState,
) -> Literal["retrieve", "fallback"]:
    """
    classify後のConditional Edge。

    LLMがStructured Outputとして返したrouteを読み、
    次のNode名を返す。
    """

    # 社内文書を検索すべき質問ならretrieveへ進む
    if state.get("route") == "search":
        return "retrieve"

    # それ以外の質問はfallbackで終了する
    return "fallback"


def retrieve_node(
    state: GraphState,
) -> dict[str, str]:
    """
    文書検索Node。

    既存のretrieve_context()を再利用し、
    検索結果だけをStateへ保存する。
    """

    # 質問を使って既存の検索処理を呼び出す
    context = retrieve_context(
        question=state["question"],
    )

    # 検索結果をStateへ返す
    return {
        "context": context,
        "current_node": "retrieve",
        "node_history": state.get("node_history", []) + ["retrieve"],
    }


def route_after_retrieve(
    state: GraphState,
) -> Literal["generate", "fallback"]:
    """
    retrieve後のConditional Edge。

    検索結果があるかどうかで、
    回答生成または拒否へ分岐する。
    """

    # contextが空文字や空白だけでない場合は回答生成へ進む
    if state.get("context", "").strip():
        return "generate"

    # 検索結果がない場合は推測せずfallbackへ進む
    return "fallback"


def make_generate_node(
    client: OpenAI,
) -> Callable[[GraphState], dict[str, str]]:
    """
    LLM回答生成Nodeを作成する。
    """

    def generate_node(
        state: GraphState,
    ) -> dict[str, str]:
        """
        検索Contextを根拠に最終回答を生成する。
        """

        # 既存の回答生成処理を再利用する
        answer = generate_answer(
            client=client,
            question=state["question"],
            context=state["context"],
        )

        # 生成結果をStateへ保存する
        return {
            "answer": answer,
            "current_node": "generate",
            "node_history": state.get("node_history", []) + ["generate"],
        }

    return generate_node


def fallback_node(
    state: GraphState,
) -> dict[str, str]:
    """
    回答できない場合のNode。

    Contextがない状態でLLMに推測させない。
    """

    return {
        "answer": "参考情報に記載されていないため、回答できません。",
        "current_node": "fallback",
        "node_history": state.get("node_history", []) + ["fallback"],
    }


def build_graph(
    client: OpenAI,
    checkpointer,
     *,
    interrupt_before: list[str] | None = None,
):
    """
    LangGraphの構造を構築する。

    Node:
        classify、retrieve、generate、fallback

    Edge:
        固定EdgeとConditional Edgeを使い分ける。
    """

    # GraphStateを扱うStateGraphを作成する
    builder = StateGraph(GraphState)

    # LLM分類Nodeを登録する
    builder.add_node(
        "classify",
        make_classify_node(client),
    )

    # 文書検索Nodeを登録する
    builder.add_node(
        "retrieve",
        retrieve_node,
    )

    # LLM回答生成Nodeを登録する
    builder.add_node(
        "generate",
        make_generate_node(client),
    )

    # 回答拒否Nodeを登録する
    builder.add_node(
        "fallback",
        fallback_node,
    )

    # Graph開始時はclassifyから始める
    builder.add_edge(
        START,
        "classify",
    )

    # classify後はrouteによってretrieve/fallbackへ分岐する
    builder.add_conditional_edges(
        "classify",
        route_after_classify,
    )

    # retrieve後はcontextの有無によってgenerate/fallbackへ分岐する
    builder.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
    )

    # 回答生成後は終了する
    builder.add_edge(
        "generate",
        END,
    )

    # fallback後も終了する
    builder.add_edge(
        "fallback",
        END,
    )

    # 定義したGraphを実行可能な形へコンパイルする
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before,
    )


def print_result(
    question: str,
    result: GraphState,
) -> None:
    """
    Graph実行結果を表示する。
    """

    print("=" * 60)
    print(f"質問: {question}")
    print(f"route: {result.get('route')}")
    print(f"current_node: {result.get('current_node')}")
    print(f"回答: {result.get('answer')}")
    print(f"node_history: {result.get('node_history')}")


def main() -> None:
    """
    LangGraphを構築し、2種類の質問を実行する。

    1件目:
        社内文書があるためgenerateへ進む

    2件目:
        対象外質問のためfallbackへ進む
    """

    # OpenAIクライアントを作成する
    client = OpenAI()
    
    connection = sqlite3.connect(
        "agent_checkpoints.db",
        check_same_thread=False
    )
    
    # SQLite接続をLangGraph用の保存担当へ渡す
    checkpointer = SqliteSaver(connection)
    
    # CheckPointerを接続したGraphを構築する
    pause_graph = build_graph(
    client=client,
    checkpointer=checkpointer,
    interrupt_before=["generate"],
)

    resume_graph = build_graph(
        client=client,
        checkpointer=checkpointer,
    )

    mode = sys.argv[1] if len(sys.argv) > 1 else "pause"

    question = "様式第4号の提出先はどこですか？"

    config = {
        "configurable": {
            "thread_id": "day66-process-resume-01",
        }
    }

    if mode == "pause":
        # generate直前で停止し、SQLiteへStateを保存する
        result = pause_graph.invoke(
            {"question": question},
            config=config,
        )

        print("停止しました")
        print_result(
            question=question,
            result=result,
        )

    elif mode == "resume":
        # SQLiteからStateを読み出し、generateから再開する
        result = resume_graph.invoke(
        None,
        config=config,
    )

    print("再開しました")
    print_result(
        question=question,
        result=result,
    )


if __name__ == "__main__":
    main()
