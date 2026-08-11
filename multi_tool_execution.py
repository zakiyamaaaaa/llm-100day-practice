import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from tool_registry_allowlist import (
    SearchDocumentsArguments,
    ToolExecutionResult,
    WeatherArguments,
    ToolRegistry,
    build_registry
)

# Toolの実行要求を表すデータクラス
@dataclass(frozen=True)
class ToolCallRequest:
    """LLMから要求された１件分のTool呼び出しを表す
    
    実際のOpenAI APIでは、tool_call.id,function.name, function.argumentsに相当する。"""
    
    # Tool呼び出しを識別するID
    call_id: str
    
    # 実行するTool名
    tool_name: str
    
    # JSON形式の引数
    raw_arguments: str
    

class CourseArguments(BaseModel):
    """ランニングコース検索Tookの引数
    """
    
    location: str = Field(
        min_length= 1,
        description="ランニングしたい場所"
    )
    
def slow_weather(arguments: WeatherArguments) -> dict[str, Any]:
    """少し時間のかかる天気取得Tool
    並列実行の効果を確認するため、意図的に0.4 秒のスリープを入れる
    """
    time.sleep(0.4)
    
    return {
        "city":arguments.city,
        "weather": "雨",
        "precipitation_probability": "80%",
    }
    
def slow_search_documents(arguments: SearchDocumentsArguments) -> dict[str, Any]:
    """少し時間のかかる文書検索Tool
    天気Toolとは独立しているため並列実行できるToolとして使用する"""
    
    time.sleep(0.4)
    
    return {
        "query":arguments.query,
        "sources": ["doc_1","doc_2"],
    }
    
def get_running_course(arguments: CourseArguments) -> dict[str, Any]:
    """
    ランニングコースを取得するTool。

    天気の結果を見てから呼び出すため、
    今回は依存Toolとして使用する。
    """
    
    time.sleep(0.4)
    
    return {
        "location" : arguments.location,
        "course": f"{arguments.location}のランニングコース",
    }
    
def build_demo_registry()->ToolRegistry:
    """
    Day59のRegistryに、Day61で使用するToolを追加する。

    既存のRegistryを再利用するため、
    Toolの登録処理を最初から書き直さない。
    """
    
    registry = build_registry()
    
    registry.register(
        name="slow_weather",
        description="指定都市の天気を取得する",
        arguments_model=WeatherArguments,
        handler=slow_weather,
    )
    
    registry.register(
         name="slow_search_documents",
        description="社内文書を検索する",
        arguments_model=SearchDocumentsArguments,
        handler=slow_search_documents,
    )
    
    registry.register(
        name="get_running_course",
        description="指定場所のランニングコースを取得する",
        arguments_model=CourseArguments,
        handler=get_running_course,
    )

    return registry
    
def create_tool_call(call_id: str, tool_name:str, arguments: dict[str, Any])->ToolCallRequest:
    """
    Pythonの辞書を、Tool呼び出し要求へ変換する。

    OpenAI APIではargumentsがJSON文字列として渡されるため、
    json.dumps()で同じ形式を再現する。
    """
    
    return ToolCallRequest(
        call_id=call_id,
        tool_name=tool_name,
        raw_arguments=json.dumps(arguments,ensure_ascii=False)
    )
    
def execute_one_tool(registry: ToolRegistry, request: ToolCallRequest) -> tuple[str, ToolExecutionResult]:
    """
    1件のTool呼び出しを実行する。

    call_idを結果と一緒に返すことで、
    複数Toolの結果を元の呼び出しと対応付けられる。
    """
    
    result = registry.execute(
        tool_name=request.tool_name,
        raw_arguments=request.raw_arguments,
    )
    
    return request.call_id, result
    
def execute_independent_tools(registry: ToolRegistry, requests: list[ToolCallRequest])->list[tuple[str, ToolExecutionResult]]:
    """
    依存関係のないTool呼び出しを並列実行する。

    例えば、天気取得と文書検索は、
    一方の結果をもう一方が必要としないため、
    同時に開始できる。
    """
    
    if not requests:
        return []
    
    # Tool要求の件数分だけWorkerを用意する
    with ThreadPoolExecutor(max_workers=len(requests)) as executor:
        # 各Toolを同時に実行する
        future_by_call_id = {
            request.call_id: executor.submit(
                execute_one_tool,
                registry,
                request
            )
            for request in requests
        }
        
        # 結果を元のTool要求順に取り出す
        # 実際の完了順ではなく、呼び出し順を維持する
        results = [
            future_by_call_id[request.call_id].result()
            for request in requests
        ]
    return results

def run_independent_demo(registry: ToolRegistry) -> None:
    """
    独立したToolを並列実行するでも
    
    天気取得と文書検索は、どちらも0.4秒かかる
    並列実行なら全体も0.4秒になる
    """
    
    requests = [
        create_tool_call(
            call_id="call_weather",
            tool_name="slow_weather",
            arguments={
                "city": "東京",
                "days":1,
            }
        ),
        create_tool_call(
            call_id="call_search",
            tool_name="slow_search_documents",
            arguments={
                "query":"経費精算の申請方法",
                "top_k":3,
            }
        )
    ]
    
    start_time = time.perf_counter()
    
    results = execute_independent_tools(
        registry,requests
    )
    
    elapsed_seconds = time.perf_counter() - start_time
    print("\n[独立Toolの並列実行]")
    print(f"実行時間: {elapsed_seconds:.2f}秒")

    for call_id, result in results:
        print(f"{call_id}: {result.model_dump()}")
    

def run_dependent_demo(registry: ToolRegistry) -> None:
    """依存関係のあるToolを順番に実行するデモ
    1. 天気を取得する
    2. 雨なら代々木公園を選ぶ
    3. 選択した場所のコースを取得する
    
    2番目のToolは、１番目の結果を必要とするため、並列実行してはいけない
    """
    
    start_time = time.perf_counter()
    
    # 最初に天気を取得する
    weather_result = registry.execute(
        tool_name="slow_weather",
        raw_arguments=json.dumps(
            {
                "city": "東京",
                "days": 1,
            },
            ensure_ascii=False,
        ),
    )
    
    # 天気取得に失敗した場合は、
    # その結果を使う後続Toolを実行しない
    if weather_result.status != "success":
        print("\n[依存Toolの順次実行]")
        print("天気取得に失敗したため、コース検索を中止しました")
        print(weather_result.model_dump())
        return
    
    # 天気Toolの結果から天候を取り出す
    weather_data = weather_result.result or {}
    weather = weather_data.get("weather")
    
    # 天候の結果に応じて、次に検索する場所を決める
    if weather == "雨":
        selected_location = "代々木公園"
    else:
        selected_location = "皇居周辺"
        
    # 天気の結果を使って、次のToolを実行する
    course_result = registry.execute(
        tool_name="get_running_course",
        raw_arguments=json.dumps(
            {
                "location": selected_location,
            },
            ensure_ascii=False,
        ),
    )
    
    elapsed_seconds = time.perf_counter() - start_time
    
    print("\n[依存Toolの順次実行]")
    print(f"実行時間: {elapsed_seconds:.2f}秒")
    print(f"天気: {weather}")
    print(f"選択した場所: {selected_location}")
    print(f"天気結果: {weather_result.model_dump()}")
    print(f"コース結果: {course_result.model_dump()}")

def main() -> None:
    """並列実行と順次実行のデモを呼び出す"""
    
    registry = build_demo_registry()
    
    run_independent_demo(registry)
    run_dependent_demo(registry)
    
if __name__ == "__main__":
    main()
