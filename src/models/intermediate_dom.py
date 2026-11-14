"""Canonical Intermediate Document DOM for lossless structural cross-format conversion."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from src.models.doc_format import DocFormat


class BlockType(str, Enum):
    """Structural block types in an IntermediateDocument."""
    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    CODE_BLOCK = "CODE_BLOCK"
    LIST = "LIST"
    TABLE = "TABLE"
    HORIZONTAL_RULE = "HORIZONTAL_RULE"


@dataclass
class TextSpan:
    """Inline styled text run inside a heading or paragraph."""
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False


@dataclass
class DocBlock:
    """Single structural block within an IntermediateDocument."""
    block_type: BlockType
    spans: list[TextSpan] = field(default_factory=list)
    level: int = 1
    code_text: str = ""
    list_items: list[str] = field(default_factory=list)
    ordered: bool = False
    table_rows: list[list[str]] = field(default_factory=list)

    @property
    def plain_text(self) -> str:
        """Returns the combined plain text content of the block."""
        if self.block_type in (BlockType.HEADING, BlockType.PARAGRAPH):
            return "".join(span.text for span in self.spans).strip()
        if self.block_type == BlockType.CODE_BLOCK:
            return self.code_text.strip()
        if self.block_type == BlockType.LIST:
            return "\n".join(item.strip() for item in self.list_items if item.strip())
        if self.block_type == BlockType.TABLE:
            return "\n".join(
                " | ".join(cell.strip() for cell in row)
                for row in self.table_rows
            )
        if self.block_type == BlockType.HORIZONTAL_RULE:
            return "---"
        return ""


@dataclass
class IntermediateDocument:
    """Canonical Intermediate Document DOM representing parsed content from any of the 5 formats."""
    title: str = "Untitled Document"
    source_format: Optional[DocFormat] = None
    blocks: list[DocBlock] = field(default_factory=list)

    @property
    def heading_count(self) -> int:
        """Total number of heading blocks in the document."""
        return sum(1 for b in self.blocks if b.block_type == BlockType.HEADING)

    @property
    def table_count(self) -> int:
        """Total number of table blocks in the document."""
        return sum(1 for b in self.blocks if b.block_type == BlockType.TABLE)

    @property
    def word_count(self) -> int:
        """Total word count across all blocks in the document."""
        total = 0
        for block in self.blocks:
            if block.block_type == BlockType.HORIZONTAL_RULE:
                continue
            if block.block_type == BlockType.TABLE:
                for row in block.table_rows:
                    for cell in row:
                        total += len(cell.split())
            else:
                text = block.plain_text
                if text:
                    total += len(text.split())
        return total

    def get_summary_preview(self, max_chars: int = 1500) -> str:
        """Generates a structured plain-text diagnostic preview of the DOM blocks."""
        lines: list[str] = []
        lines.append(f"Title: {self.title}")
        if self.source_format:
            lines.append(f"Source Format: {self.source_format.value.upper()}")
        lines.append(
            f"Structure: {self.heading_count} Headings | {self.table_count} Tables | {self.word_count} Words"
        )
        lines.append("=" * 60)

        for block in self.blocks:
            if block.block_type == BlockType.HEADING:
                lvl = max(1, min(6, block.level))
                lines.append(f"\n[H{lvl}] {block.plain_text}")
            elif block.block_type == BlockType.PARAGRAPH:
                text = block.plain_text
                if text:
                    lines.append(f"[PARAGRAPH] {text}")
            elif block.block_type == BlockType.CODE_BLOCK:
                lines.append(f"[CODE]\n{block.code_text.strip()}")
            elif block.block_type == BlockType.LIST:
                kind = "ORDERED LIST" if block.ordered else "BULLET LIST"
                lines.append(f"[{kind} ({len(block.list_items)} items)]")
                for idx, item in enumerate(block.list_items, start=1):
                    prefix = f"  {idx}." if block.ordered else "  •"
                    lines.append(f"{prefix} {item}")
            elif block.block_type == BlockType.TABLE:
                row_cnt = len(block.table_rows)
                col_cnt = max((len(r) for r in block.table_rows), default=0)
                lines.append(f"[TABLE {row_cnt}x{col_cnt}]")
                for row in block.table_rows[:6]:
                    lines.append("  | " + " | ".join(row) + " |")
                if row_cnt > 6:
                    lines.append(f"  ... ({row_cnt - 6} more rows)")
            elif block.block_type == BlockType.HORIZONTAL_RULE:
                lines.append("[HR] ----------------------------------------")

        full_preview = "\n".join(lines)
        if len(full_preview) > max_chars:
            return full_preview[:max_chars] + "\n... [Preview Truncated]"
        return full_preview
