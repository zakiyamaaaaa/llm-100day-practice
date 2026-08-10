import json
from dataclasses import dataclass
from typing import Any, Callable, Literal
from pydantic import BaseModel, Field, ValidationError

# Toolの実行結果を統一した形式で表すモデル
class ToolExecutionResult(BaseModel):
    """successなら実行成功、errorなら何らかの理由で実行失敗
    """
    
    status: Literal["success", "error"]
    tool_name: str
    result: Any | None = None
    error_type: str | None = None
    error_message: str | None = None
    
# Toolに登録する情報をまとめるデータクラス
@dataclass(frozen=True)
class RegisteredTool:
    """LLMが指定するTool名"""
    name: str
    description: str
    arguments_model: type[BaseModel]
    handler: Callable[[BaseModel], Any]

# 天気取得Toolの引数を定義するPydanticモデル
class WeatherArguments(BaseModel):
    city: str = Field(
        min_length=1,
        max_length=50,
        description="天気を取得したい都市名",
    )
    
    days: int = Field(
        default=1,
        ge=1,
        le=7,
        description="予報日数、1~7を指定する"
    )
    
    
# 文書検索Toolの引数を定義するPydanticモデル
class SearchDocumentsArguments(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=200,
        description="検索したい質問やキーワード"
    )
    
    # 一度に取得する件数を1~10件に制限する
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="取得する文書数"
    )
    
def get_weather(arguments: WeatherArguments) -> dict[str, Any]:
    """天気取得Toolの本体
    外部APIを呼ばず、固定値を返すモックとして実装"""
    
    return {
        "city" : arguments.city,
        "days": arguments.days,
        "forecast": "晴れ"
    }
    
def search_documents(arguments: SearchDocumentsArguments)->dict[str, Any]:
    """文書検索Toolの本体
    
    実際のRAG検索はDay63行うため、今回は検索条件を確認するだけのモックにする
    """
    
    return {
        "query" : arguments.query,
        "top_k": arguments.top_k,
        "sources": ["doc_1", "doc_2"]
    }
    
class ToolRegistry:
    """実行可能なToolを一元管理するクラス
    LLMが任意の関数名を出力しても、Registryに登録されていないToolは実行しない
    """
    
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}
        
    def register(self, name: str, description: str, arguments_model: type[BaseModel], handler: Callable[[BaseModel],Any],) -> None:
        """
        ToolをRegistryへ登録する
        
        同じ名前のToolを上書きすると危険なので、重複登録はエラーになる
        """
        
        if not name:
            raise ValueError("Tool名は空にできません")
        
        if name in self._tools:
            raise ValueError(f"Tool名 {name} はすでに登録済みです")
        
        self._tools[name] = RegisteredTool(
            name=name,
            description=description,
            arguments_model=arguments_model,
            handler=handler,
        )
    
    def allowed_tool_names(self) -> list[str]:
        """現在許可されているTool名の一覧を返す"""
        
        return list(self._tools.keys())
    
    def to_openai_tools(self) -> list[dict[str, Any]]:
        """
        Registryの情報をOpenAI APIへ渡せる形式に変換する。

        PydanticのモデルからJSON Schemaを自動生成するため、
        API用の引数定義を手書きする必要がない。
        """
        tools = []
        
        for tool in self._tools.values():
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.arguments_model.model_json_schema(),
                    },
                }
            )

        return tools
    
    def execute(self, tool_name: str, raw_arguments: str) -> ToolExecutionResult:
        """
        Tool名とJSON形式の引数を受け取り、安全にToolを実行する。

        処理順序は重要。

        1. Tool名が許可されているか確認
        2. JSONをPydanticモデルで検証
        3. 検証済みの引数で関数を実行
        """
        
        # Registryに登録されていないToolは絶対に実行しない
        registered_tool = self._tools.get(tool_name)
        
        if registered_tool is None:
            return ToolExecutionResult(
                status="error",
                tool_name=tool_name,
                error_type="unknown_tool",
                error_message=f"Tool名 {tool_name} は許可されていません",
            )
        
        try: 
            # LLMが出力したJSON文字列をPydanticモデルへ変換する
            # 型、必須項目、数値の範囲などがここで検証される
            typed_arguments = (
                registered_tool.arguments_model.model_validate_json(
                    raw_arguments
                )
            )
            
        except (ValidationError, ValueError) as error:
            # JSON不正やPydanticのバリデーションエラーを、
            # Tool実行前にエラーとして返す
            return ToolExecutionResult(
                status="error",
                tool_name=tool_name,
                error_type="invalid_arguments",
                error_message=str(error),
            )

        try:
            # 検証済みのPydanticモデルをTool本体へ渡す
            tool_result = registered_tool.handler(typed_arguments)

        except Exception as error:
            # Tool本体で例外が起きても、アプリ全体を落とさず、
            # 統一されたエラー結果として返す
            return ToolExecutionResult(
                status="error",
                tool_name=tool_name,
                error_type="tool_execution_error",
                error_message=str(error),
            )

        # すべて成功した場合の結果
        return ToolExecutionResult(
            status="success",
            tool_name=tool_name,
            result=tool_result,
        )
        
def build_registry() -> ToolRegistry:
    """アプリケーションで使用可能なTool一覧を構築する
    
    この関数に登録したToolだけが実行可能になる。"""
    
    registry = ToolRegistry()
    
    registry.register(
        name="get_weather",
        description="指定した都市の天気予報を取得する",
        arguments_model=WeatherArguments,
        handler=get_weather,
    )
    
    registry.register(
        name="search_documents",
        description="社内文書を検索する",
        arguments_model=SearchDocumentsArguments,
        handler=search_documents,
    )

    return registry

def print_result(label: str, result: ToolExecutionResult) -> None:
    """
    Toolの実行結果を確認しやすい形式で表示する。
    """
    print(f"\n[{label}]")
    print(result.model_dump_json(indent=2, ensure_ascii=False))
    
    
def main() -> None:
    """Allowlistと引数検証の動作を確認する"""
    
    registry = build_registry()
    
    print("許可されたTool:")
    print(registry.allowed_tool_names())
    
    # 正しいTool名・正しい引数の場合
    valid_weather = registry.execute(
        tool_name="get_weather",
        raw_arguments=json.dumps(
            {
                "city": "東京",
                "days": 3,
            },
            ensure_ascii=False,
        ),
    )
    print_result("正常な天気検索", valid_weather)
    
    # 別の正しいToolを実行する
    valid_search = registry.execute(
        tool_name="search_documents",
        raw_arguments=json.dumps(
            {
                "query": "経費精算の申請方法",
                "top_k": 3,
            },
            ensure_ascii=False,
        ),
    )
    print_result("正常な文書検索", valid_search)
    
    # daysが7を超えているため、Pydanticで拒否される
    invalid_arguments = registry.execute(
        tool_name="get_weather",
        raw_arguments=json.dumps(
            {
                "city": "東京",
                "days": 30,
            },
            ensure_ascii=False,
        ),
    )
    print_result("不正な引数", invalid_arguments)

    # Registryに存在しないToolなので、関数は実行されない
    unknown_tool = registry.execute(
        tool_name="delete_all_data",
        raw_arguments=json.dumps(
            {
                "target": "all",
            },
            ensure_ascii=False,
        ),
    )
    print_result("未許可のTool", unknown_tool)

if __name__ == "__main__":
    main()
