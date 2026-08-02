import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from metadata_ingest_rag import build_chunk_records

DOCS_DIR = Path("docs")
CHROMA_PATH = "./.chroma_data"
COLLECTION_NAME = "document_lifecycle_rules"

@dataclass(frozen=True)
class VersionedChunk:
    """1つのChunkと、そのバージョン情報を保持するデータ
    content_hashを持つことで、
    文書が更新されたかどうかを判定できる
    """
    chunk_id: str
    text: str
    source: str
    section: str
    chunk_index: int
    content_hash: str

    def to_metadata(self) -> dict[str, str | int]:
        """
        Chroma保存用のMetadataへ変換する

        Metadataは本文とは別に保存される
        後で出店表示、更新、削除、ACL管理に利用する
        """

        return {
            "source": self.source,
            "section": self.section,
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "content_hash": self.content_hash,
        }

def calculate_content_hash(content: str) -> str:
    """
    文書本文からContent Hashを作成する。

    処理の流れ
    1. 改行コードを統一する
    2. 文書の前後の不要な空白を削除
    3. UTG-8のバイト列へ変換する
    4. SHA-256でHashを計算する
    5. IDを短くするため、先頭16文字だけ返す

    改行コードの違いだけでHashが変わらないように、
    改行を統一してから計算する。
    """

    normalized_content = (
        content.replace("\r\n", "\n").strip()
    )

    return hashlib.sha1(normalized_content.encode("utf-8")).hexdigest()[:16]

def create_embedding_function():
    "OpenAI Embedding関数を作成する"

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEYが設定されていません"
        )

    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small",
    )

def create_collection():
    """
    永続Collectionを取得する。

    get_or_create_collectionを使うことで、
    スクリプトを再実行してもCollection作成エラーにならない。
    """

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=(
            create_embedding_function()
        ),
    )

def build_versioned_chunks(file_path: Path,) -> list[VersionedChunk]:
    """
    ファイルを読み込み、Hash付きChunkへ変換する

    1. ファイル本文を読み込む
    2. 文書全体のContent Hashを計算する
    3. Chunking関数を呼び出す
    4. Chunkごとの一意なIDを作る
    5. Chunk本文とMetadataをまとめる
    """
    content = file_path.read_text(encoding="utf-8")

    # 文書全体からHashを作る
    # 同じファイル内容なら同じHashになる
    content_hash = calculate_content_hash(content)

    # Chunking処理は既存関数を再利用する
    base_records = build_chunk_records(file_path)

    versioned_chunks: list[VersionedChunk] = []

    for record in base_records:
        # sourceとcontent_hashをIDに含める
        chunk_id = (
            f"{record.source}"
            f"::{content_hash}"
            f"::chunk-{record.chunk_index}"
        )

        versioned_chunks.append(
            VersionedChunk(
                chunk_id=chunk_id,
                text=record.text,
                source=record.source,
                section=record.section,
                chunk_index=record.chunk_index,
                content_hash=content_hash,
            )
        )
    return versioned_chunks

def get_existing_source_data(collection, source: str) -> dict:
    """
    既存のCollectionから、指定sourceのデータを取得する。

    sourceは、docs配下のファイル名と一致する。
    """

    existing_data = collection.get(
        where={"source": source},
        include=["metadatas"],
    )

    return existing_data

def sync_file(collection, file_path: Path) -> str:
    """
    1ファイルをCollectionへ同期する。

    戻り値:
    - inserted: 新規登録
    - updated: 変更後に更新
    - unchanged: 内容に変更なし
    """
    source = file_path.name
    content = file_path.read_text(encoding="utf-8")
    current_hash = calculate_content_hash(content)

    existing_data = get_existing_source_data(collection, source)
    existing_ids = existing_data["ids"]
    existing_metadatas = existing_data["metadatas"] or []
    existing_hashes = {metadata.get("content_hash") for metadata in existing_metadatas}

    # 同じHashのChunkがすでにある場合、Embedding APIを呼ばずに処理を終了する
    if existing_ids and existing_hashes == {current_hash}:
        return "unchanged"

    # 内容が変わった場合は、先に同じsourceの古いChunkを削除する
    if existing_ids:
        collection.delete(ids=existing_ids)
    new_chunks = build_versioned_chunks(file_path)
    collection.upsert(ids=[chunk.chunk_id for chunk in new_chunks],
                      metadatas=[chunk.to_metadata() for chunk in new_chunks],
                      documents=[chunk.text for chunk in new_chunks])
    if existing_ids:
        return "updated"
    return "inserted"

def delete_removed_sources(
    collection,
    current_sources: set[str],
) -> int:
    """
    docsフォルダから消えたsourceのChunkを削除する。

    Chromaのupsertだけでは削除を検出できないため、
    現在のファイル一覧とMetadataを比較する。
    """

    all_data = collection.get(include=["metadatas"])
    all_ids = all_data["ids"]
    all_metadatas = all_data["metadatas"] or []
    removed_ids = [
        chunk_id
        for chunk_id, metadata in zip(
            all_ids,
            all_metadatas,
        )
        if (
            metadata is not None
            and metadata.get("source")
            not in current_sources
        )
    ]
    if removed_ids:
        collection.delete(ids=removed_ids)
    return len(removed_ids)

def sync_directory(collection, docs_dir: Path) -> dict[str, int]:
    """docsフォルダ全体を同期する"""
    file_paths = sorted(docs_dir.glob("*.txt"))
    current_sources = {file_path.name for file_path in file_paths}
    counts = {
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
        "deleted_chunks": 0,
    }

    for file_path in file_paths:
        result = sync_file(collection, file_path)
        counts[result] += 1

    counts["deleted_chunks"] = delete_removed_sources(
        collection,
        current_sources=current_sources,
    )

    return counts

def main() -> None:
    """文書同期を２回実行し、重複しないことを確認する"""

    load_dotenv()
    collection = create_collection()

    print("=== 1回目の同期 ===")
    counts1 = sync_directory(collection, DOCS_DIR)
    print(counts1)

    print("\n=== 2回目の同期 ===")
    counts2 = sync_directory(collection, DOCS_DIR)
    print(counts2)

if __name__ == "__main__":
    main()
