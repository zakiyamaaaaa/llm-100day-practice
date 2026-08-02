import os
from dataclasses import dataclass
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from chanking_rag import split_text_recursive

DOCS_DIR = Path("docs")
CHROMA_PATH = "./.chroma_data"
COLLECTION_NAME ="metadata_file_ingest_rules"

@dataclass(frozen=True)
class ChunkRecord:
    """１つのChunkの情報"""
    chunk_id: str
    text: str
    source: str
    section: str
    chunk_index: int

    def to_metadata(self) -> dict[str, str | int]:
        """
        Chromaに保存するMetadataへ変換する

        Metadataは本文とは別に保存され、あとで引用やアクセス制御に利用できる
        """

        return {
            "source": self.source,
            "section": self.section,
            "chunk_id": self.chunk_id,
            "chunk_index":self.chunk_index,
        }


def create_embedding_function():
    """OpenAI Embedding関数を作成する"""
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables.")

    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small"
    )

def extra_section(content: str, source: str) -> str:
    """
    文書の先頭行からセクション名を取得する。

    今回のdocsは、
    【経費精算ガイドライン】
    のような形式を使用している。
    """

    for lin in content.splitlines():
        line = lin.strip()
        if line.startswith("【") and line.endswith("】"):
            return line[1:-1]
    return Path(source).stem

def build_chunk_records(file_path: Path, chunk_size: int = 100, chunk_overlap:int = 20,) -> list[ChunkRecord]:
    """"1ファイルを読み込み、MetadataつきChunkへ変換する"""

    content = file_path.read_text(encoding="utf-8")

    source = file_path.name
    section = extra_section(content, source)

    chunks = split_text_recursive(text=content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    records: list[ChunkRecord] = []

    for chunk_index, chunk in enumerate(chunks, start=1):
        chunk_id = f"{source}__{chunk_index}"
        record = ChunkRecord(
            chunk_id=chunk_id,
            text=chunk,
            source=source,
            section=section,
            chunk_index=chunk_index
        )
        records.append(record)
    return records

def build_all_chunk_records(docs_dir: Path)->list[ChunkRecord]:
    """docs_dir配下のすべてのテキストファイルを読み込み、MetadataつきChunkへ変換する"""

    all_records: list[ChunkRecord] = []

    for file_path in sorted(docs_dir.glob("*.txt")):
        records = build_chunk_records(file_path)
        all_records.extend(records)

    return all_records

def create_collection():
    """Metadata保存用のChroma Collectionを作成する"""
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    embedding_function = create_embedding_function()

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )

    return collection

def ingest_records(collection, records: list[ChunkRecord])->None:
    """Chunk本文とMetadataをChromaへ登録する"""

    if not records:
        raise ValueError(
            "登録するChunkがありません"
        )

    collection.upsert(
        ids=[
            record.chunk_id
            for record in records
        ],
        documents=[
            record.text
            for record in records
        ],
        metadatas=[
            record.to_metadata()
            for record in records
        ],
    )

def search_documents(
    collection,
    query: str,
    top_k: int = 3,
) -> None:
    """検索結果とMetadataが保持されていることを確認する"""

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    print(f"\n質問: {query}")

    for rank, (
        document,
        metadata,
        distance,
    ) in enumerate(
        zip(
            documents,
            metadatas,
            distances,
        ),
        start=1,
    ):
        print(f"\n{rank}位")
        print(f"distance: {distance:.4f}")
        print(f"source: {metadata['source']}")
        print(f"section: {metadata['section']}")
        print(f"chunk_id: {metadata['chunk_id']}")
        print(f"本文: {document}")

def main() -> None:
    """MetadataつきIngestと検索を実行する"""

    load_dotenv()

    records = build_all_chunk_records(DOCS_DIR)
    collection = create_collection()
    ingest_records(collection, records)

    print(f"登録Chunk数: {len(records)}")

    search_documents(
        collection,
        query="経費精算の申請方法を教えてください",
        top_k=3,
    )

if __name__ == "__main__":
    main()
