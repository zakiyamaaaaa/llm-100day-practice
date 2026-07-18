import os
import glob
from typing import List
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

#前回のチャンキングロジックを使用
def split_text_recursive(text: str, chunk_size: int = 150, chunk_overlap: int = 30) -> List[str]:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    chunks = []
    current_chunk = ""
    for line in lines:
        if len(current_chunk) + len(line) <= chunk_size:
            current_chunk += ("\n" if current_chunk else "") + line
        else:
            if current_chunk:
                chunks.append(current_chunk)
            overlap_start = max(0, len(current_chunk) - chunk_overlap)
            overlap_text = current_chunk[overlap_start:] if current_chunk else ""
            current_chunk = (overlap_text + "\n" if overlap_text else "") + line
    if current_chunk:
        chunks.append(current_chunk)
        return chunks
    

def main():
    chroma_client = chromadb.PersistentClient(path="./.chroma_data")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    collection = chroma_client.get_or_create_collection(
        name="file_ingest_rules",
        embedding_function=openai_ef
    )
    
    # docsフォルダ内のテキストファイルを自動スキャン
    target_dir = "./docs"
    # 指定したパターンにマッチするファイルパスをまとめて取得
    file_paths = glob.glob(os.path.join(target_dir, "*.txt"))
    
    print(f"📂 {len(file_paths)} 件のテキストファイルを検出しました。")
    
    all_chunks = []
    all_ids = []
    all_metadatas = []
    
    # 各ファイルをループで読み込み、チャンキング
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        print(f"✂️ ファイル '{file_name}' をチャンキング中...")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # ファイルの中身をチャンクに分割
        chunks = split_text_recursive(content, chunk_size=100, chunk_overlap=20)
        
        # 一括登録用のリストにデータを詰める
        for i, chunk in enumerate(chunks):
            chunk_id = f"{file_name}_chunk_{i+1}" #ファイル名も含んだユニークなid
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadatas.append({"source_file": file_name})

    # まとめてデータベースに登録（バルクインサート）
    if all_chunks:
        print(f"📥 合計 {len(all_chunks)} 個のチャンクをChroma DBに同期中...")
        collection.upsert(
            documents=all_chunks,
            ids=all_ids,
            metadatas=all_metadatas
        )
        print("✅ 登録完了！")
    else:
        print("⚠️ チャンクが生成されませんでした。")
        return
    
    # テスト検索（新しく取り込んだ経費精算について質問）
    query = "経費精算はいつまでに申請すればいいですか？"
    print(f"👤 質問: {query}")
    
    results = collection.query(
        query_texts=[query],
        n_results=1
    )
    
    print("\n🔎 検索結果:")
    print(f"  - 該当ファイル: {results['metadatas'][0][0]['source_file']}")
    print(f"  - 距離スコア: {results['distances'][0][0]:.4f}")
    print(f"  - 本文:\n{results['documents'][0][0]}")
        

if __name__ == "__main__":
    main()
