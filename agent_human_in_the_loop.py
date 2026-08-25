import json
import sqlite3
import sys
import uuid
from typing import Any, Callable, Literal, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from openai import OpenAI
from pydantic import BaseModel, Field
from tool_registry_allowlist import (
    ToolRegistry,
    build_registry,
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
    
    # LLMが提案したTool名
    tool_name: str
    # LLMが提案したTool引数
    tool_arguments: dict[str, Any]
    
    #　人間の承認結果
    human_decision: str
    
    # Toolを実行した結果
    tool_result: dict[str, Any]
    
    approval_reason: str | None

class WriteDocumentArguments(BaseModel):
    """
    書き込みToolへ渡す引数
    
    Tool実行前に文書IDと本文を検証する
    """
    document_id: str = Field(min_length=1,description="更新対象の文書ID")
    content: str = Field(min_length=1, description="更新後の本文")
    
class WriteProposal(BaseModel):
    """
    LLMが作成するTool実行提案
    LLMは実行そのものではなく、実行したいToolと引数だけを提案する
    """
    tool_name: Literal["write_document"]
    arguments: WriteDocumentArguments
    

class HumanDecision(BaseModel):
    """
    人間が承認画面で返す判断
    
    approve: 提案どおり実行
    edit: 修正した引数で実行
    reject: 実行しない
    """
    
    decision: Literal["approve", "edit", "reject"]
    edited_arguments: WriteDocumentArguments | None = None
    reason: str | None = None
    
def propose_write_request(
    client: OpenAI,
    question: str,
) -> WriteProposal:
    """
    ユーザーの依頼をLLMへ渡し、
    書き込みToolの実行案をStructured Outputで取得する。

    この関数ではToolを実行しない。
    あくまで実行候補を作るだけである。
    """

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        temperature=0,
        response_format=WriteProposal,
        messages=[
            {
                "role": "system",
                "content": (
                    "あなたはTool実行計画を作るAgentです。"
                    "ユーザーの文書更新依頼から、"
                    "write_documentのTool名と引数を抽出してください。"
                    "この段階ではToolを実行してはいけません。"
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    proposal = response.choices[0].message.parsed

    if proposal is None:
        raise ValueError(
            "Tool実行提案をStructured Outputから取得できませんでした"
        )

    return proposal

def make_propose_write_node(
    client: OpenAI,
) -> Callable[[GraphState], dict[str, Any]]:
    """
    LLMに書き込みToolの実行案を作らせるNodeを作成する。

    このNodeは提案をStateへ保存するだけで、
    書き込みTool自体は実行しない。
    """

    def propose_write_node(
        state: GraphState,
    ) -> dict[str, Any]:
        """
        ユーザーの依頼からTool名と引数を抽出し、
        GraphStateへ保存する。
        """

        # LLMからStructured Output形式のTool提案を取得する
        proposal = propose_write_request(
            client=client,
            question=state["question"],
        )

        # 次のapproval Nodeが確認できるよう、
        # 提案内容をStateへ保存する
        return {
            "tool_name": proposal.tool_name,
            "tool_arguments": proposal.arguments.model_dump(),
            "current_node": "propose_write",
            "node_history": (
                state.get("node_history", [])
                + ["propose_write"]
            ),
        }

    return propose_write_node

def approval_node(
    state: GraphState,
) -> dict[str, Any]:
    """
    書き込みToolを実行する前に、人間の判断を待つNode。

    interrupt()が呼ばれた時点でGraphは停止し、
    CheckpointへStateが保存される。
    """

    # 承認画面へ表示する情報を作る
    approval_payload = {
        "question": "このToolを実行してよいですか？",
        "tool_name": state["tool_name"],
        "arguments": state["tool_arguments"],
    }

    # ここでGraphが停止する。
    # 再開時にはCommand(resume=...)の値が返る
    raw_decision = interrupt(approval_payload)

    # 人間から渡された判断をPydanticで検証する
    decision = HumanDecision.model_validate(raw_decision)

    updates: dict[str, Any] = {
        "human_decision": decision.decision,
        "approval_reason": decision.reason,
        "current_node": "approval",
        "node_history": (
            state.get("node_history", [])
            + ["approval"]
        ),
    }

    # editの場合は、修正後の引数をStateへ保存する
    if decision.decision == "edit":
        if decision.edited_arguments is None:
            raise ValueError(
                "editの場合、edited_argumentsが必要です"
            )

        updates["tool_arguments"] = (
            decision.edited_arguments.model_dump()
        )

    return updates

def route_after_approval(
    state: GraphState,
) -> Literal["execute_write", "reject"]:
    """
    人間の判断に応じて、次のNodeを決める。

    approveとeditはTool実行へ進み、
    rejectは実行せず終了する。
    """

    if state.get("human_decision") in {"approve", "edit"}:
        return "execute_write"

    return "reject"

def reject_node(
    state: GraphState,
) -> dict[str, Any]:
    """
    人間が拒否した場合のNode。

    書き込みToolは実行せず、
    拒否されたことだけを結果として保存する。
    """

    return {
        "tool_result": {
            "status": "rejected",
            "reason": (
                state.get("approval_reason")
                or "人間によって実行が拒否されました"
            ),
        },
        "current_node": "reject",
        "node_history": (
            state.get("node_history", [])
            + ["reject"]
        ),
    }

def write_document(
    arguments: WriteDocumentArguments,
) -> dict[str, Any]:
    """
    文書を書き込むToolのモック。

    実際のファイルやDBは変更せず、
    実行された内容だけを結果として返す。
    """

    return {
        "status": "success",
        "document_id": arguments.document_id,
        "content": arguments.content,
        "message": "文書更新をシミュレートしました",
    }
    
def build_day67_registry() -> ToolRegistry:
    """
    Day59のTool Registryを再利用し、
    Day67の書き込みToolを追加する。

    Registryに登録されたToolだけが実行可能になる。
    """

    registry = build_registry()

    registry.register(
        name="write_document",
        description="指定された文書の内容を更新する",
        arguments_model=WriteDocumentArguments,
        handler=write_document,
    )

    return registry

def make_execute_write_node(
    registry: ToolRegistry,
) -> Callable[[GraphState], dict[str, Any]]:
    """
    承認済みの書き込みToolを実行するNodeを作成する。
    """

    def execute_write_node(
        state: GraphState,
    ) -> dict[str, Any]:
        """
        Stateに保存されたTool名と引数を使って実行する。

        実行前にRegistryでAllowlistと引数を再検証する。
        """

        # Stateの引数をJSONへ変換する
        raw_arguments = json.dumps(
            state["tool_arguments"],
            ensure_ascii=False,
        )

        # Allowlist確認・Pydantic検証・Tool実行をまとめて行う
        result = registry.execute(
            tool_name=state["tool_name"],
            raw_arguments=raw_arguments,
        )

        return {
            "tool_result": result.model_dump(),
            "current_node": "execute_write",
            "node_history": (
                state.get("node_history", [])
                + ["execute_write"]
            ),
        }

    return execute_write_node


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

def build_approval_graph(
    client: OpenAI,
    checkpointer,
    registry: ToolRegistry,
):
    """
    Human-in-the-Loop用のGraphを構築する。

    LLMのTool提案後、書き込み前に人間の承認を待つ。
    """

    # GraphStateを共有するStateGraphを作成する
    builder = StateGraph(GraphState)

    # LLMにTool実行案を作らせるNode
    builder.add_node(
        "propose_write",
        make_propose_write_node(client),
    )

    # 人間の承認を待つNode
    builder.add_node(
        "approval",
        approval_node,
    )

    # 承認後に書き込みToolを実行するNode
    builder.add_node(
        "execute_write",
        make_execute_write_node(registry),
    )

    # 拒否時に終了するNode
    builder.add_node(
        "reject",
        reject_node,
    )

    # Graph開始時は、まずLLMにTool実行案を作らせる
    builder.add_edge(
        START,
        "propose_write",
    )

    # Tool提案後は、必ず人間の承認へ進む
    builder.add_edge(
        "propose_write",
        "approval",
    )

    # 承認結果によって、実行または拒否へ分岐する
    builder.add_conditional_edges(
        "approval",
        route_after_approval,
    )

    # Tool実行後は終了する
    builder.add_edge(
        "execute_write",
        END,
    )

    # 拒否後も終了する
    builder.add_edge(
        "reject",
        END,
    )

    # interrupt()のStateを保存するため、
    # Checkpointerを接続してコンパイルする
    return builder.compile(
        checkpointer=checkpointer,
    )

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

def make_resume_payload(
    decision_mode: str,
) -> dict[str, Any]:
    """
    人間の判断をCommand(resume=...)へ渡す形式に変換する。
    """

    if decision_mode == "approve":
        return {
            "decision": "approve",
        }

    if decision_mode == "edit":
        return {
            "decision": "edit",
            "edited_arguments": {
                "document_id": "doc_2",
                "content": "修正後の本文です。",
            },
        }

    if decision_mode == "reject":
        return {
            "decision": "reject",
            "reason": "更新内容を確認できないため拒否しました。",
        }

    raise ValueError(
        "decision_modeはapprove、edit、rejectのいずれかです"
    )

def main() -> None:
    """
    Human-in-the-Loopの承認フローを実行する。

    コマンドライン引数:
        approve: 提案どおり実行
        edit:    引数を修正して実行
        reject:  実行せず終了
    """
    
    # 実行する承認経路を取得する
    decision_mode = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "approve"
    )
    
    client = OpenAI()
    
    # Checkpoint保存先のSQLiteへ接続する
    connection = sqlite3.connect(
        "agent_checkpoints.db",
        check_same_thread=False,
    )
    
    # SQLite接続をLangGraphのCheckpointerへ渡す
    checkpointer = SqliteSaver(connection)

    # Day59のTool Registryへ書き込みToolを登録する
    registry = build_day67_registry()
    
    # Human-in-the-Loop用Graphを構築する
    graph = build_approval_graph(
        client=client,
        checkpointer=checkpointer,
        registry=registry,
    )
    
    question = (
        "doc_2の本文を、"
        "「社外PC持出許可申請書（様式第4号）の提出先は、"
        "セキュリティチームです。」に更新してください。"
    )

    # 実行ごとに新しいthread_idを作る
    # 過去のCheckpointとの混在を防ぐ
    thread_id = (
        f"day67-{decision_mode}-{uuid.uuid4().hex[:8]}"
    )

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # 1回目:
    # LLMがTool実行案を作り、approval Nodeで停止する
    initial_result = graph.invoke(
        {"question": question},
        config=config,
    )

    print("=== 承認待ち ===")
    print(f"thread_id: {thread_id}")
    print(f"interrupt: {initial_result.get('__interrupt__')}")
    print(f"node_history: {initial_result.get('node_history')}")

    # 人間の判断を作る
    resume_payload = make_resume_payload(
        decision_mode
    )

    # 2回目:
    # 同じthread_idでCheckpointから再開する
    final_result = graph.invoke(
        Command(resume=resume_payload),
        config=config,
    )

    print("\n=== 最終結果 ===")
    print(f"current_node: {final_result.get('current_node')}")
    print(f"human_decision: {final_result.get('human_decision')}")
    print(f"tool_result: {final_result.get('tool_result')}")
    print(f"node_history: {final_result.get('node_history')}")


if __name__ == "__main__":
    main()
