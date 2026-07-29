from dataclasses import dataclass
from chanking_rag import LONG_DOCUMENT, split_text_recursive

@dataclass(frozen=True)
class BoundaryAuditResult:
    """１つのChunkの境界監査結果"""
    chunk_number: int
    length: int
    starts_on_unit_boundary: bool
    ends_on_unit_boundary: bool
    ends_with_heading: bool
    
def extract_semantic_units(text: str) -> list[str]:
    """
    文章を意味単位の候補へ分割する。

    今回の教材では、元文書の改行を文・見出しの境界として扱う。
    形態素1個をChunkにするのではなく、
    見出しとその直後の説明を1つの単位として扱う。
    """
    
    new_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]
    
    units: list[str] = []
    pending_heading: str | None = None
    for line in new_lines:
        if line.startswith("#"):
            if pending_heading is not None:
                units.append(pending_heading)
            
            pending_heading = line
            continue
        
        if pending_heading is not None:
            units.append(f"{pending_heading}\n{line}")
            pending_heading = None
        else:
            units.append(line)
    
    if pending_heading is not None:
        units.append(pending_heading)
    
    return units

def split_preserving_units(text: str, max_chars: int = 150) -> list[str]:
    """
    意味単位を途中で分割しないChunker
    これは最終盤ではなく、
    文字途中で切る方式と比較するための基準実装
    """
    
    units = extract_semantic_units(text)
    
    chunks: list[str] = []
    current_units: list[str] = []
    
    for unit in units:
        candidate = "\n".join(
            [*current_units, unit]
        )
        
        # 既存Chunkに追加すると上限を超える場合、
        # 現在のChunkを確定する。
        if (
            current_units
            and len(candidate) > max_chars
        ):
            chunks.append(
                "\n".join(current_units)
            )
            current_units = [unit]
        else:
            current_units.append(unit)
    
    if current_units:
        chunks.append(
            "\n".join(current_units)
        )

    return chunks

def audit_chunks( chunks: list[str], units: list[str],) -> list[BoundaryAuditResult]:
    """Chunkの開始・終了位置が意味単位に揃ってるか監査する"""
    
    results: list[BoundaryAuditResult] = []
    
    for chunk_number, chunk in enumerate(chunks, start=1):
        normalized_chunk = chunk.strip()
        lines = normalized_chunk.splitlines()

        starts_on_boundary = any(
            normalized_chunk.startswith(unit)
            for unit in units
        )

        ends_on_boundary = any(
            normalized_chunk.endswith(unit)
            for unit in units
        )

        ends_with_heading = bool(
            lines
            and lines[-1].startswith("#")
        )
        
        results.append(
            BoundaryAuditResult(
                chunk_number=chunk_number,
                length=len(normalized_chunk),
                starts_on_unit_boundary=(
                    starts_on_boundary
                ),
                ends_on_unit_boundary=(
                    ends_on_boundary
                ),
                ends_with_heading=(
                    ends_with_heading
                ),
            )
        )
    return results

def print_audit_result(
    strategy_name: str,
    chunks: list[str],
    units: list[str],
) -> None:
    """1つの分割方式の監査結果を表示する"""

    audit_results = audit_chunks(
        chunks=chunks,
        units=units,
    )

    valid_count = sum(
        1
        for result in audit_results
        if (
            result.starts_on_unit_boundary
            and result.ends_on_unit_boundary
            and not result.ends_with_heading
        )
    )

    print("\n" + "=" * 60)
    print(f"分割方式: {strategy_name}")
    print(f"Chunk数: {len(chunks)}")
    print(
        f"意味境界を維持したChunk: "
        f"{valid_count}/{len(chunks)}"
    )

    for result in audit_results:
        print(
            f"Chunk {result.chunk_number}: "
            f"length={result.length}, "
            f"開始境界={result.starts_on_unit_boundary}, "
            f"終了境界={result.ends_on_unit_boundary}, "
            f"見出しで終了={result.ends_with_heading}"
        )
        
def main() -> None:
    """既存方式と意味境界方式を比較する"""
    
    semantic_units = extract_semantic_units(LONG_DOCUMENT)
    
    strategies = {
        "current_char_overlap": (
            split_text_recursive(
                text=LONG_DOCUMENT,
                chunk_size=150,
                chunk_overlap=30,
            )
        ),
        "boundary_preserving": (
                    split_preserving_units(
                        text=LONG_DOCUMENT,
                        max_chars=150,
                    )
                )
        }
    
    for strategy_name, chunks in strategies.items():
        print_audit_result(
            strategy_name=strategy_name,
            chunks=chunks,
            units=semantic_units,
        )

if __name__ == "__main__":
    main()
