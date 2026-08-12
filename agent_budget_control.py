import json
import time
from dataclasses import dataclass
from typing import Any,Literal

from tool_registry_allowlist import (
    ToolExecutionResult,
    ToolRegistry,
    build_registry,
)

@dataclass(frozen=True)
class AgentBudget:
    """
    Agentに許可する最大予算をまとめる
    
    これらの制限は、LLMの判断ではなくPythonアプリケーション側で強制する
    """
    
    max_turns: int
    max_tool_calls: int
    max_elapsed_seconds: float
    max_total_tokens: int
    
@dataclass
class AgentUsage:
    """Agent実行中に消費したリソースを記録する
    """
    turns: int = 0
    tool_calls: int = 0
    total_tokens: int = 0
    elapsed_seconds: float = 0.0
    
@dataclass(frozen=True)
class PlannedToolCall:
    """Plannerが次に実行すると決めたTool呼び出しを表す
    実際のLLM APIでは、tool_call.idやfunction.argumentsに相当する
    
    """
    
    call_id: str
    tool_name: str
    # JSON形式のTool引数
    raw_arguments: str
    
@dataclass(frozen=True)
class PlannerTurn:
    """１ターン分のPlanner出力を表す
    今回はLLMの代わりにあらかじめ決めた値を返す
    """
    
    # このターンで実行したいTool
    tool_calls: tuple[PlannedToolCall, ...]
    
    # このターンで消費する想定Token数
    estimated_tokens: int
    # TrueならAgentが最終回答不能になったとみなす
    is_final: bool = False
    
class ScriptedPlanner:
    """LLMの代わりに決められた順番でPlanner決kさを返す
    APIを呼ばずにAgentの停止条件だけを検証するために使う
    """
    
    def __init__(self, turns: list[PlannerTurn], response_delay_seconds: float = 0.0) -> None:
        # Plannerが返すターン一覧を保存する
        self._turns = turns
        
        # LLM APIの応答時間をシミュレーションする
        self._response_delay_seconds = response_delay_seconds
        
        # 現在何番目のターンを返すかを管理する
        self._current_index = 0
        
    def next_turn(self) -> PlannerTurn:
        """
        次のPlanner結果を１件返す
        予定したターンを使い切った場合は、最終回答可能なターンを返す
        """
        
        # API応答に時間がかかる状況をシミュレーションする
        if self._response_delay_seconds > 0.0:
            time.sleep(self._response_delay_seconds)
            
        # すべての予定を使い切った場合は終了する
        if self._current_index >= len(self._turns):
            return PlannerTurn(
                tool_calls=(),
                estimated_tokens=0,
                is_final=True,
            )
        
        # 現在のターンを取り出す
        turn = self._turns[self._current_index]
        
        # 次回は次のターンを返すように進める
        self._current_index += 1
        return turn
    
@dataclass
class AgentRunResult:
    """Agentの実行結果をまとめる
    """
    
    status: Literal["completed", "budget_exceeded", "total_error"]
    
    # 終了理由
    reason: str
    
    #　使用量の記録
    usage: AgentUsage
    
    
def make_tool_call(call_id: str, tool_name: str, arguments: dict[str, Any])->PlannedToolCall:
    """Pythonの辞書をPlannerのTool呼び出し形式へ変換する
    """
    return PlannedToolCall(
        call_id=call_id,
        tool_name=tool_name,
        raw_arguments=json.dumps(arguments, ensure_ascii=False),
    )
    
def create_result(status: Literal["completed", "budget_exceeded", "total_error"], reason: str, usage: AgentUsage, start_time: float) -> AgentRunResult:
    """Agentの実行結果を作る
    """
    usage.elapsed_seconds = time.perf_counter() - start_time
    
    return AgentRunResult(
        status=status,
        reason=reason,
        usage=usage,
    )


def run_agent(registry: ToolRegistry, planner: ScriptedPlanner, budget: AgentBudget) -> AgentRunResult:
    """
    予算制限つきでAgentを実行する
    重要な点はLLMに停止を依頼するのではなく、各制限をPython側で毎回確認すること
    確認する制限：
    
    1. ターン数
    2. 実行時間
    3. Token数
    4. Tool実行回数
    """
    
    start_time = time.perf_counter()
    
    usage = AgentUsage()
    
    while True:
        # 次のターンを開始する前にターン数を確認する
        if usage.turns >= budget.max_turns:
            return create_result(
                status="budget_exceeded",
                reason=f"ターン数が上限 {budget.max_turns} を超えたため",
                usage=usage,
                start_time=start_time,
            )
        
        # 次のLLM呼び出しを行う前に時間を確認する
        elapsed_seconds = time.perf_counter() - start_time
        if elapsed_seconds >= budget.max_elapsed_seconds:
            return create_result(
                status="budget_exceeded",
                reason=f"経過時間が上限 {budget.max_elapsed_seconds} 秒を超えたため",
                usage=usage,
                start_time=start_time,
            )
            
        # LLMの代わりにPlannerから次の判断を取得する
        
        turn = planner.next_turn()
        
        usage.turns += 1
        # Plannerから返された想定Token数を加算する
        usage.total_tokens += turn.estimated_tokens
        
        # Token予算を超えた場合はToolを実行しいない
        if usage.total_tokens > budget.max_total_tokens:
            return create_result(
                status="budget_exceeded",
                reason=f"Token数が上限 {budget.max_total_tokens} を超えたため",
                usage=usage,
                start_time=start_time,
            )
        
        # 最終回答可能という判断なら、Toolを実行せずに終了する
        if turn.is_final:
            return create_result(
                status="completed",
                reason="Plannerが最終回答可能と判断したため",
                usage=usage,
                start_time=start_time,
            )
        
        # このターンでToolを実行すると上限を超えるか確認する
        requested_tool_count = len(turn.tool_calls)
        
        if (usage.tool_calls + requested_tool_count) > budget.max_tool_calls:
            return create_result(
                status="budget_exceeded",
                reason=f"Tool実行回数が上限 {budget.max_tool_calls} を超えたため",
                usage=usage,
                start_time=start_time,
            )
            
        # このターンで要求されたToolを順番に実行する
        for tool_call in turn.tool_calls:
            # Tool実行前にも全体の時間を確認する
            elapsed_seconds = time.perf_counter() - start_time
            
            if elapsed_seconds >= budget.max_elapsed_seconds:
                return create_result(
                    status="budget_exceeded",
                    reason=f"経過時間が上限 {budget.max_elapsed_seconds} 秒を超えたため",
                    usage=usage,
                    start_time=start_time,
                )
                
            # AllowlistとPydantic検証を含むRegistryへ処理を渡す
            result = registry.execute(
                tool_name=tool_call.tool_name,
                raw_arguments=tool_call.raw_arguments,
            )
            
            # Toolを１回実行したので回数を増やす
            usage.tool_calls += 1
            
            # Toolが失敗した場合は、Agent全体を継続しない
            if result.status != "success":
                return create_result(
                    status="tool_error",
                    reason=(
                        f"{tool_call.tool_name}の実行に失敗: "
                        f"{result.error_type}"
                    ),
                    usage=usage,
                    start_time=start_time,
                )
                
        # 次のターンへ進む
        
def build_scenarios() -> list[
    tuple[str, ScriptedPlanner, AgentBudget]
]:
    """
    予算超過パターンを確認するシナリオを作成する。

    main()に大量の設定を書かないよう、
    シナリオ構築を関数へ分離する。
    """

    weather_call = make_tool_call(
        call_id="call_weather",
        tool_name="get_weather",
        arguments={
            "city": "東京",
            "days": 1,
        },
    )

    search_call = make_tool_call(
        call_id="call_search",
        tool_name="search_documents",
        arguments={
            "query": "経費精算の申請方法",
            "top_k": 3,
        },
    )

    return [
        (
            "正常終了",
            ScriptedPlanner(
                turns=[
                    PlannerTurn(
                        tool_calls=(weather_call,),
                        estimated_tokens=100,
                    ),
                    PlannerTurn(
                        tool_calls=(search_call,),
                        estimated_tokens=100,
                    ),
                    PlannerTurn(
                        tool_calls=(),
                        estimated_tokens=80,
                        is_final=True,
                    ),
                ],
            ),
            AgentBudget(
                max_turns=5,
                max_tool_calls=3,
                max_elapsed_seconds=2.0,
                max_total_tokens=500,
            ),
        ),
        (
            "最大ターン数超過",
            ScriptedPlanner(
                turns=[
                    PlannerTurn(
                        tool_calls=(weather_call,),
                        estimated_tokens=100,
                    ),
                    PlannerTurn(
                        tool_calls=(weather_call,),
                        estimated_tokens=100,
                    ),
                    PlannerTurn(
                        tool_calls=(weather_call,),
                        estimated_tokens=100,
                    ),
                ],
            ),
            AgentBudget(
                max_turns=2,
                max_tool_calls=5,
                max_elapsed_seconds=2.0,
                max_total_tokens=500,
            ),
        ),
        (
            "最大Tool回数超過",
            ScriptedPlanner(
                turns=[
                    PlannerTurn(
                        tool_calls=(weather_call,),
                        estimated_tokens=100,
                    ),
                    PlannerTurn(
                        tool_calls=(search_call,),
                        estimated_tokens=100,
                    ),
                    PlannerTurn(
                        tool_calls=(),
                        estimated_tokens=80,
                        is_final=True,
                    ),
                ],
            ),
            AgentBudget(
                max_turns=5,
                max_tool_calls=1,
                max_elapsed_seconds=2.0,
                max_total_tokens=500,
            ),
        ),
        (
            "Token予算超過",
            ScriptedPlanner(
                turns=[
                    PlannerTurn(
                        tool_calls=(weather_call,),
                        estimated_tokens=150,
                    ),
                    PlannerTurn(
                        tool_calls=(search_call,),
                        estimated_tokens=150,
                    ),
                ],
            ),
            AgentBudget(
                max_turns=5,
                max_tool_calls=5,
                max_elapsed_seconds=2.0,
                max_total_tokens=200,
            ),
        ),
        (
            "実行時間超過",
            ScriptedPlanner(
                turns=[
                    PlannerTurn(
                        tool_calls=(weather_call,),
                        estimated_tokens=100,
                    ),
                ],
                response_delay_seconds=0.1,
            ),
            AgentBudget(
                max_turns=5,
                max_tool_calls=5,
                max_elapsed_seconds=0.05,
                max_total_tokens=500,
            ),
        ),
    ]
    
    
def print_scenario_result(
    label: str,
    result: AgentRunResult,
) -> None:
    """
    シナリオ結果を確認しやすく表示する。
    """
    usage = result.usage

    print(f"\n[{label}]")
    print(f"status: {result.status}")
    print(f"reason: {result.reason}")
    print(
        "usage: "
        f"turns={usage.turns}, "
        f"tool_calls={usage.tool_calls}, "
        f"tokens={usage.total_tokens}, "
        f"elapsed={usage.elapsed_seconds:.2f}s"
    )
    
def main() -> None:
    """各予算制限が機能することを確認する"""
    
    registry = build_registry()
    
    for label, planner, budget in build_scenarios():
        result = run_agent(
            registry=registry,
            planner=planner,
            budget=budget,
        )
        
        print_scenario_result(label, result)
        
if __name__ == "__main__":
    main()

