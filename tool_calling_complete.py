import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# 1. Python側の実装の関数（APIやDBからデータを取ってくる想定のモック）
def get_running_course_info(location: str) -> str:
    """実際のシステムや外部API、あるいはRAGからデータを引っ張ってくる関数"""
    if "皇居" in location:
        return json.dumps({
            "status": "available",
            "distance": "約5.0km (1周)",
            "highlights": "信号待ちがなく、桜田門や千鳥ヶ淵などの歴史的景観を楽しめる。夜間も明るく安全。",
            "note": "歩行者優先。半時計回りの走行がローカルルールとして定着しています。"
        }, ensure_ascii=False)
    elif "代々木公園" in location:
        return json.dumps({
            "status": "available",
            "distance": "約1.2km〜2.4km (内周・外周コース)",
            "highlights": "豊かな緑に囲まれたフラットなコース。土日はやや混雑。",
            "note": "サイクリングロードへの進入は禁止されています。"
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "unavailable",
            "message": f"指定された場所「{location}」のランニングコース情報は見つかりませんでした。"
        }, ensure_ascii=False)
        
# 2. LLMへ渡す関数の説明書（スキーマ定義）
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
    user_query = "明日の朝、皇居の周辺をランニングしたいんだけど、おすすめのコース情報はある？"
    print(f"👤 ユーザー: {user_query}\n")

    # メッセージ履歴の管理を開始
    messages = [{"role": "user", "content": user_query}]
    
    # 🌟 [STEP 1] LLMに質問を投げて、ツールを使うべきか判断させる（片道）
    print("🤖 LLM：対話のコンテキストを評価中...")
    first_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=my_tools,
        tool_choice="auto"
    )
    
    first_message = first_response.choices[0].message
    # LLMの回答履歴をメッセージに追加（たとえ本文が空でもtool_calls情報が含まれているため必須）
    messages.append(first_message)
    
    # 🌟 [STEP 2] LLMがツール呼び出しを希望しているか確認
    if first_message.tool_calls:
        tool_call = first_message.tool_calls[0]
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)
        
        print(f"🎯 LLMから要求された関数: {func_name}")
        print(f"🧩 抽出された引数: {func_args}")
        
        # 🌟 [STEP 3] Python側で関数を実行して結果を取
        if func_name == "get_running_course_info":
            target_location = func_args.get("location")
            print(f"⚙️ アプリ：ローカル関数 '{func_name}' を実行中...")
            
            # 実際に関数を実行して、文字列の実行結果を得る
            function_result = get_running_course_info(location=target_location)
            print(f"📥 関数からの返り値: {function_result}\n")
            
            # 🌟 [STEP 4] 関数の「実行結果」をメッセージ履歴に追加（role: 'tool' がポイント）
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": func_name,
                "content": function_result
            })
            
            # 🌟 [STEP 5] 実行結果を引っ提げて、LLMに「最終回答」を作らせる（復路）
            print("🤖 LLM：関数の実行結果を基に、ユーザーへの最終回答を生成中...")
            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            
            print("\n🤖 LLMの最終回答:")
            print(final_response.choices[0].message.content)
            
    else:
        # ツール呼び出しが不要な場合（雑談など）
        print("🤖 LLMの通常の回答:")
        print(first_message.content)

if __name__ == "__main__":
    main()
