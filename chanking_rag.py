import os
from typing import List
from dotenv import load_dotenv

# 📝 1. 実務を想定した「長文の社内ガイドライン」
LONG_DOCUMENT = """
# リモートワーク制度に関するガイドライン

## 1. 対象者と実施頻度
原則として、試用期間を経過したすべての正社員および契約社員がリモートワーク制度の対象となります。
実施頻度は週最大3日までとし、各チームのテックリードまたはマネージャーの事前承認を得る必要があります。
なお、新入社員のオンボーディング期間中（入社後3ヶ月間）は、チームワーク向上と業務習得のため、原則週4日以上のオフィス出社を推奨しています。

## 2. ネットワークセキュリティ
リモートワークの実施に際しては、会社より貸与されたPC（社内PC）および指定のセキュアVPNを必ず使用して社内ネットワークに接続してください。
自宅以外のカフェや公共のWi-Fi環境から直接社内システムにアクセスすることは、情報漏洩のリスクがあるため厳重に禁止します。
万が一、PCの紛失や盗難、あるいはマルウェア感染の疑いが発生した場合は、1時間以内にセキュリティチーム（emergency-security@company.com）へ即時報告してください。

## 3. リモートワーク手当の支給
リモートワークに伴う電気代やインターネット通信費の補助として、リモートワーク実施日数に応じた手当を支給します。
1日あたり200円を一律で支給し、毎月の経費申請時に勤務実績に基づいて申請を行ってください（月額上限4,000円）。
なお、ネットワーク環境の構築に関わる初期費用（ルーターの購入など）については、手当の支給対象外となりますのでご留意ください。
"""

# 📐 2. 再帰的チャンキングロジックの簡易実装
def split_text_recursive(text: str, chunk_size: int = 150, chunk_overlap: int = 30) -> List[str]:
    """
    文章を「段落(\n\n)」や「改行(\n)」で分割しつつ、
    chunk_sizeを超えないように結合しながらチャンクを生成する。
    隣接するチャンク間で chunk_overlap 文字分を重複させる。
    """
    
    # 簡易的に、まず段落・改行単位で分割
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    chunks = []
    current_chunk = ""
    
    for line in lines:
        # 現在のチャンクに新しい行を足しても制限サイズ以下に収まる場合
        if len(current_chunk) + len(line) <= chunk_size:
            current_chunk += ("\n" if current_chunk else "") + line
        else:
            # 制限サイズを超える場合、現在のチャンクを登録
            if current_chunk:
                chunks.append(current_chunk)
                
            # オーバーラップを考慮して次のチャンクの介して地点を作る
            # 現在のチャンクの末尾から、指定文字数分を次のチャンクの頭にする
            overlap_start = max(0, len(current_chunk) - chunk_overlap)
            overlap_text = current_chunk[overlap_start:] if current_chunk else ""
            
            #新しい行をセット
            current_chunk = (overlap_text + "\n" if overlap_text else "") + line
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def main():
    print("✂️ 長文ドキュメントを『チャンキング（分割）』します...")
    
    # 1チャンク最大150文字、オーバーラップ30文字で分割
    chunks = split_text_recursive(LONG_DOCUMENT, chunk_size=150, chunk_overlap=30)
    print(f"📊 分割完了！ 合計チャンク数: {len(chunks)} 個\n")
    
    # 分割された中身を確認
    for i, chunk in enumerate(chunks):
        print(f"--- [チャンク {i+1}] (文字数: {len(chunk)}) ---")
        print(chunk)
        print()
        

if __name__ == "__main__":
    main()
