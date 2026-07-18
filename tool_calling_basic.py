import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# 1. LLMにこんな関数が使えるよと教えるための定義
# これをToolsとしてAPIリクエストに含める
my_tools = [
     {
        "type": "function",
        "function": {
            "name": "get_running_course_info",
            "description": "指定された場所やエリアの、おすすめのランニングコースの情報を取得する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "ランニングをしたいエリアや場所の名称（例: '皇居', '代々木公園'）"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

def main():
    # ユーザーからの質問
    user_query = "明日の朝、皇居の周辺をランニングしたいんだけど、おすすめのコース情報はある？"
    print(f"👤 ユーザー: {user_query}\n")

    print("🤖 LLMが適切なツール（関数）を選択中...")
    
    # OPENAI APIを呼び出す
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": user_query}
        ],
        tools=my_tools,          # 使えるツールを教えてあげる
        tool_choice="auto"       # 使うかどうか、どれを使うかはLLMに自動判断させる
    )
    
    response_message = response.choices[0].message
    
    # 3.LLMが関数を呼び出したいと判断したかチェック
    if response_message.tool_calls:
        print("🎯 LLMがツール（関数呼び出し）が必要だと判断しました！\n")
        
        # 呼び出すべき関数の情報を抽出
        tool_call = response_message.tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        print("📊 --- LLMが出力した関数呼び出し命令 ---")
        print(f"  実行すべき関数名: {function_name}")
        print(f"  抽出された引数(Arguments): {function_args}")
        print(f"  具体的な引数の値 (location): {function_args.get('location')}")
        print("--------------------------------------")
    else:
        # 関数を呼ぶ必要がない普通の雑談などの場合
        print("🤖 LLMの通常の回答:")
        print(response_message.content)
        
if __name__ == "__main__":
    main()
