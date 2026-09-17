from typing import Any

from pydantic import BaseModel, Field

from mcp_rag_server import read_document, search_documents as mcp_search_documents
from tool_registry_allowlist import SearchDocumentsArguments, ToolRegistry


class AuditEvent(BaseModel):
    """Agentの処理経路を後から確認するための監査ログ。"""

    step: int
    node: str
    event: str
    tool_name: str | None = None
    status: str
    detail: str


class AgentState(BaseModel):
    """Agent実行中に共有する最小限の状態。"""

    thread_id: str
    question: str
    max_tool_calls: int = 1
    tool_calls: int = 0
    answer: str | None = None
    audit_log: list[AuditEvent] = Field(default_factory=list)


def add_audit_event(
    state: AgentState,
    *,
    node: str,
    event: str,
    status: str,
    detail: str,
    tool_name: str | None = None,
) -> None:
    """Agentの状態に、1件の監査ログを追加する。"""

    state.audit_log.append(
        AuditEvent(
            step=len(state.audit_log) + 1,
            node=node,
            event=event,
            tool_name=tool_name,
            status=status,
            detail=detail,
        )
    )


def search_handler(arguments: BaseModel) -> dict[str, Any]:
    """既存のMCP RAG ToolをTool Registryから呼び出すためのAdapter。"""

    # Registryが検証済みのSearchDocumentsArgumentsを渡しているか確認する
    if not isinstance(arguments, SearchDocumentsArguments):
        raise ValueError("arguments must be SearchDocumentsArguments")

    # RAG検索の中身は作り直さず、Day69のMCP Toolを再利用する
    return mcp_search_documents(
        query=arguments.query,
        top_k=arguments.top_k,
    )


def build_search_registry() -> ToolRegistry:
    """検索Toolだけを許可したRegistryを構築する。"""

    registry = ToolRegistry()
    registry.register(
        name="search_documents",
        description="社内文書を検索する",
        arguments_model=SearchDocumentsArguments,
        handler=search_handler,
    )
    return registry


def run_search_agent(
    question: str,
    *,
    thread_id: str,
    max_tool_calls: int = 1,
) -> AgentState:
    """RAG検索経路を、制限と監査ログ付きで実行する。"""

    state = AgentState(
        thread_id=thread_id,
        question=question,
        max_tool_calls=max_tool_calls,
    )

    # 実際のLLM Agentでは、ここがPlannerの判断に相当する
    add_audit_event(
        state,
        node="plan",
        event="plan_created",
        status="success",
        detail="search_documentsを使って質問を検索する",
        tool_name="search_documents",
    )

    # Tool実行前に、アプリケーション側で予算を強制する
    if state.tool_calls >= state.max_tool_calls:
        state.answer = "Tool実行回数の上限に達したため、処理を終了しました。"
        add_audit_event(
            state,
            node="budget_guard",
            event="tool_call_blocked",
            status="budget_exceeded",
            detail="max_tool_callsを超えるため実行しない",
            tool_name="search_documents",
        )
        return state

    registry = build_search_registry()
    state.tool_calls += 1

    add_audit_event(
        state,
        node="retrieve",
        event="tool_call",
        status="started",
        detail="Tool Registry経由でRAG検索を実行する",
        tool_name="search_documents",
    )

    result = registry.execute(
        tool_name="search_documents",
        raw_arguments=SearchDocumentsArguments(
            query=question,
            top_k=3,
        ).model_dump_json(),
    )

    if result.status == "error":
        state.answer = "検索に失敗したため、回答できません。"
        add_audit_event(
            state,
            node="retrieve",
            event="tool_result",
            status="error",
            detail=result.error_message or "Tool実行エラー",
            tool_name="search_documents",
        )
        return state

    payload = result.result or {}
    results = payload.get("results", [])

    add_audit_event(
        state,
        node="retrieve",
        event="tool_result",
        status="success",
        detail=f"検索結果を{len(results)}件取得した",
        tool_name="search_documents",
    )

    if not results:
        state.answer = "参考情報が見つからないため、回答できません。"
        add_audit_event(
            state,
            node="fallback",
            event="finalized",
            status="refused",
            detail="検索結果が空のため拒否した",
        )
        return state

    # 検索結果のsourceを使い、MCP Resourceから本文を読み取る
    top_result = results[0]
    source = top_result["source"]
    resource_text = read_document(source)

    add_audit_event(
        state,
        node="context",
        event="resource_read",
        status="success",
        detail=f"{source}をResourceから取得した",
    )

    # Day58で検証済みの回答生成の代わりに、今回は接続確認用の回答を作る
    state.answer = f"{top_result['text']} [source: {source}]"
    add_audit_event(
        state,
        node="answer",
        event="finalized",
        status="success",
        detail="検索結果とResource本文を使って回答した",
    )

    return state


def print_run_result(state: AgentState) -> None:
    """Agentの回答と監査ログを表示する。"""

    print("=" * 60)
    print(f"thread_id: {state.thread_id}")
    print(f"質問: {state.question}")
    print(f"回答: {state.answer}")
    print(f"Tool実行回数: {state.tool_calls}/{state.max_tool_calls}")
    print("\n[監査ログ]")

    for event in state.audit_log:
        print(
            f"{event.step}. node={event.node} "
            f"event={event.event} status={event.status} "
            f"tool={event.tool_name} detail={event.detail}"
        )


def main() -> None:
    """Agent v1の検索経路を1件だけ実行する。"""

    state = run_search_agent(
        question="様式第4号の提出先はどこですか？",
        thread_id="day70-search-001",
    )
    print_run_result(state)


if __name__ == "__main__":
    main()
