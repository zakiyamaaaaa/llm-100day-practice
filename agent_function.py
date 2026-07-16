import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# 🛠️ 1. LLMに使わせたい「手足（関数）」を普通にPythonで定義する
# ※この関数の中身は、LLMが直接実行するのではなく、ローカルのPython環境で実行されます。
def encrypt_text(text: str, shift: int = 3) -> str:
    result = []
    for char in text:
        if char.isalpha():
            start = ord('a') if char.islower() else ord('A')
            
            new_char = chr((ord(char) - start + shift) % 26 + start)
            result.append(new_char)
        else:
            result.append(char)
    return ''.join(result)

def main():
    user_instruction = "私の秘密のコード 'Hello World' を、5文字ずらす設定で暗号化してシステムに保存してください。"
    print(f"👤 ユーザーの指示: {user_instruction}\n")
    
    # 会話の履歴を保存する配列（モバイルのチャット履歴と同じです）
    messages = [
        {"role": "user", "content": user_instruction}
    ]

    # 📝 2. LLMに対して「あなたが使える関数の説明（仕様書）」をJSONで定義する
    # ※この詳細な説明文を元に、LLMは「今、この関数を使うべきか？」を判断します。
    tools = [
        {
            "type": "function",
            "function": {
                "name": "encrypt_text",
                "description": "与えられたテキストをシーザー暗号を用いて指定された文字数（shift）だけずらして暗号化します。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "暗号化したい生のテキスト文字列（例: 'Hello'）"
                        },
                        "shift": {
                            "type": "integer",
                            "description": "文字をずらす数。デフォルトは3。"
                        }
                    },
                    "required": ["text"]
                }
            }
        }
    ]
    
    # 🤖 3. LLMにツール（関数仕様書）を渡して、1回目の問い合わせ
    print("🤖 AIエージェントが思考中（ツールを使うべきか判断しています）...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": user_instruction}
        ],
        tools=tools, # ここでツールの仕様書を渡す
        tool_choice="auto" # 自動で判断させる
    )
    
    response_message = response.choices[0].message
    messages.append(response_message)
    tool_calls = response_message.tool_calls
    
    # LLMが関数を呼びたい、と合図してきた場合の処理
    if tool_calls:
        print("💡 LLMが『encrypt_text』関数の実行を要求しました！")
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"  - 呼び出す関数名: {function_name}")
            print(f"  - 生成された引数: {function_args}")
            
            if function_name == "encrypt_text":
                execution_result = encrypt_text(
                    text=function_args.get("text"),
                    shift=function_args.get("shift",3)
                )
                print(f"🟢 関数実行成功。結果: '{execution_result}'")
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": execution_result
                })
        # 🤖 3. 2回目の問い合わせ（関数の結果をLLMに渡して、ユーザーへの最終回答を作らせる）
        print("\n🤖 2. 関数の実行結果をエージェントに伝達し、最終回答を生成中...")
        second_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages, # 関数結果が含まれた履歴を丸ごと渡す
        )
        print(f"\n🤖 エージェントの最終回答:\n{second_response.choices[0].message.content}")
    else:
        print("🤖 LLMは関数を呼び出す必要はありませんでした。")
        print(f"LLMの回答: {response_message.content}")
        
if __name__ == "__main__":
    main()
