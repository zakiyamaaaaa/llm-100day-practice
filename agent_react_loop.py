import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# エージェントが使える２つのツール
def get_weather(location: str) -> str:
    if "皇居" in location:
        return json.dumps({"weather": "雨", "precipitation_probability": "80%"}, ensure_ascii=False)
    return json.dumps({"weather": "晴れ", "precipitation_probability": "10%"}, ensure_ascii=False)

def get_running_course_info(location: str) -> str:
    if "代々木公園" in location:
        return json.dumps({"course": "代々木公園", "distance": "約1.2km〜2.4km", "note": "緑豊かなフラットなコースです。"}, ensure_ascii=False)
    return json.dumps({"course": "皇居", "distance": "約5.0km", "note": "半時計回りがルールです。"}, ensure_ascii=False)

# 2つの関数スキーマを定義
my_tools = [
     {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "指定された場所の天気を取得する。",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_running_course_info",
            "description": "指定された場所のランニングコース情報を取得する。",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"]
            }
        }
    }
]

def main():
    # ユーザーからの複雑な複合質問
    user_query = "明日の朝、皇居を走りたい。もし雨が降りそうなら、代わりに代々木公園のコース情報を教えて。"
    print(f"👤 ユーザー: {user_query}\n")
    
    messages = [{"role": "user","content": user_query}]
    
    # 最大3回までLLMに自律的なループを許可する
    MAX_ITERATIONS = 3
    
    for iteration in range(MAX_ITERATIONS):
        print(f"🔄 --- 【ループ {iteration + 1} 回目】 エージェントが思考中... ---")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=my_tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        messages.append(message)
        
        # LLMがツールを呼び出したいと判断した場合（Act）
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            target_location = func_args.get("location")
            
            print(f"🎯 行動 (Act): 関数 '{func_name}' を引数 {func_args} で実行命令を受けました。")
            
            # 関数の振り分けと実行
            if func_name == "get_weather":
                result = get_weather(location=target_location)
            elif func_name == "get_running_course_info":
                result = get_running_course_info(location=target_location)
            else:
                result = json.dumps({"error": "不明な関数です。"}, ensure_ascii=False)
                
            print(f"📥 観察 (Observation): 関数の実行結果 -> {result}\n")
            
            # 実行結果を履歴にフィードバックして、次のループをつなぐ
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name":func_name,
                "content": result
            })
            
        # LLMがもうツールを呼ぶ必要はない（結論が出た）と判断した場合
        else:
            print("🏁 エージェントが『最終回答可能』と判断しました。")
            print("\n🤖 LLMの最終回答:")
            print(message.content)
            break

if __name__ == "__main__":
    main()
