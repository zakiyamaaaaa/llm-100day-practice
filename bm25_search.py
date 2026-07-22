from collections import Counter
from dataclasses import dataclass
import math
import re

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[ぁ-んァ-ン一-龯]+")

def tokenize(text: str) -> list[str]:
    """英数字・日本語の連続部分をtokenに分割する"""
    return [
        match.group(0).lower()
        for match in TOKEN_PATTERN.finditer(text)
    ]

@dataclass(frozen=True)
class Document:
    document_id: str
    title: str
    text: str
    

@dataclass(frozen=True)
class SearchResult:
    document: Document
    score: float

class BM25Index:
    def __init__(
        self,
        documents: list[Document],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if not documents:
            raise ValueError("documents must not be empty")
        if k1 < 0:
            raise ValueError("k1 must be non-negative")
        if not 0.0 <= b <= 1.0:
            raise ValueError("b must be in the range [0.0, 1.0]")
        
        self.documents = documents
        self.k1 = k1
        self.b = b
        
        self.tokenized_documents = [tokenize(doc.text) for doc in documents]
        self.document_lengths = [len(tokens) for tokens in self.tokenized_documents]
        self.average_document_length = sum(self.document_lengths) / len(self.document_lengths)
        self.document_frequencies = self._build_document_frequencies()
        
    def _build_document_frequencies(self) -> Counter[str]:
        frequencies: Counter[str] = Counter()
        
        for tokens in self.tokenized_documents:
            # 1文書内で同じ単語が何回でても、文書頻度は1回だけ増やす
            frequencies.update(set(tokens))
        
        return frequencies
    
    def _inverse_document_frequency(self, token: str) -> float:
        document_count = len(self.documents)
        document_frequency = self.document_frequencies.get(token, 0)
        return math.log(
            1.0 + ( document_count - document_frequency + 0.5)/(document_frequency + 0.5)
        )
        
    def _score_document(self, query_tokens: list[str], document_index: int,) -> float:
        document_tokens = self.tokenized_documents[document_index]
        term_frequencies = Counter(document_tokens)
        
        document_length = self.document_lengths[document_index]
        score = 0.0
        
        for token in set(query_tokens):
            term_frequency = term_frequencies.get(token, 0)
            if term_frequency == 0:
                continue
            
            idf = self._inverse_document_frequency(token)
            
            length_normalizer = (1.0 - self.b + self.b*document_length/ self.average_document_length)
            
            numerator = term_frequency + (self.k1 + 1.0)
            denominator = (term_frequency + self.k1 + length_normalizer)
            
            score += idf * numerator /denominator
        
        return score
    
    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if not query.strip():
            raise ValueError("query must not be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        
        results = []
        
        for index, document in enumerate(self.documents):
            score = self._score_document(query_tokens= query_tokens, document_index=index)
            
            if score > 0.0:
                results.append(SearchResult(document=document, score=score))
        
        return sorted(results, key=lambda x: x.score, reverse=True)[:top_k]
    

DOCUMENTS = [
    Document(
        document_id="doc_1",
        title="機密情報取扱申請書",
        text=(
            "機密情報取扱申請書（様式第1号）の"
            "提出先は、法務部コンプライアンス課です。"
        ),
    ),
    Document(
        document_id="doc_2",
        title="社外PC持出許可申請書",
        text=(
            "社外PC持出許可申請書（様式第4号）の"
            "提出先は、セキュリティチームです。"
        ),
    ),
    Document(
        document_id="doc_3",
        title="出張経費事前申請書",
        text=(
            "出張経費事前申請書（様式第9号）の"
            "提出先は、総務部経費精算係です。"
        ),
    ),
]

def main() -> None:
    index = BM25Index(DOCUMENTS)
    
    queries = [
        "様式第4号の提出先はどこですか？",
        "社外PCを持ち出す申請先は？",
        "本を買うには誰の承認が必要ですか？",
    ]
    
    for query in queries:
        print(f"\n質問: {query}")
        print(tokenize(query))
        results = index.search(query, top_k=3)
        
        for rank, result in enumerate(results, start=1):
            print(
                f"{rank}位: "
                f"{result.document.document_id} "
                f"score={result.score:.4f} "
                f"{result.document.title}"
            )

if __name__ == "__main__":
    main()
