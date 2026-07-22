import json

# 1.エージェント全体が共有する状態の定義
# モバイルアプリでいう、画面を駆動するためのViewModelのStateやReduxのStateと同じ思想
class AgentState:
    def __init__(self, user_query: str):
        self.user_query = user_query
        self.messages = [{"role": "user", "content": user_query}]  # ユーザーの質問を最初のメッセージとして追加
        self.current_step = 0
        self.is_finished = False
        self.logs = []
        
    def add_log(self, text: str):
        self.logs.append(f"[Step {self.current_step}] {text}")
    
    def print_status(self):
        print(f"\n--- 📊 AgentState Snapshot (Step: {self.current_step}) ---")
        print(f"  完了フラグ: {self.is_finished}")
        print(f"  履歴メッセージ数: {len(self.messages)}")
        print(f"  直近の内部ログ: {self.logs[-1] if self.logs else 'なし'}")
        print("--------------------------------------------------")
        

def main():
    # ユーザーの入力を受けて、最初の状態（State）を生成
    state = AgentState("明日の朝、皇居を走りたい。雨なら代々木公園に変更で。")
    state.add_log("エージェントが初期化されました。")
    state.print_status()
    
    # step 1: LLMノードが天気を調べろと判断した
    state.current_step += 1
    state.messages.append({"role": "assistant", "content": "get_weather(location='皇居') を呼び出します。"})
    state.add_log("LLMノード：皇居の天気を調査するアクションを要求。")
    state.print_status()
    
    # step 2: アクションオードが関数を実行し、雨だとわかった
    state.current_step += 1
    state.messages.append({"role": "tool", "content": json.dumps({"weather": "雨"})})
    state.add_log("アクションノード：天気情報を取得し、雨であることを確認。")
    state.print_status()
    

if __name__ == "__main__":
    main()
