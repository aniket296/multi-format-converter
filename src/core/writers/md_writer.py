"""Markdown writer serializing IntermediateDocument DOM to GitHub-Flavored Markdown (GFM)."""
import os
from pathlib import Path
from src.models.intermediate_dom import (
    BlockType,
    IntermediateDocument,
    TextSpan,
)


def _render_spans_md(spans: list[TextSpan]) -> str:
    """Renders inline TextSpans into Markdown syntax."""
    parts: list[str] = []
    for sp in spans:
        txt = sp.text
        if not txt:
            continue
        # Preserve leading/trailing spaces outside markers
        lead = txt[: len(txt) - len(txt.lstrip())]
        trail = txt[len(txt.rstrip()) :]
        core = txt.strip()
        if not core:
            parts.append(txt)
            continue

        if sp.code:
            core = f"`{core}`"
        if sp.italic:
            core = f"*{core}*"
        if sp.bold:
            core = f"**{core}**"
        parts.append(f"{lead}{core}{trail}")
    return "".join(parts).strip()


def _render_table_md(rows: list[list[str]]) -> str:
    """Renders a 2D table grid into an aligned Markdown pipe table."""
    if not rows:
        return ""
    col_count = max(len(r) for r in rows)
    if col_count == 0:
        return ""

    normalized: list[list[str]] = []
    col_widths = [3] * col_count

    for row in rows:
        padded = [
            row[c].replace("|", "\\|").replace("\n", " ").strip() if c < len(row) else ""
            for c in range(col_count)
        ]
        for c, val in enumerate(padded):
            if len(val) > col_widths[c]:
                col_widths[c] = len(val)
        normalized.append(padded)

    lines: list[str] = []
    header = normalized[0]
    header_line = "| " + " | ".join(header[c].ljust(col_widths[c]) for c in range(col_count)) + " |"
    sep_line = "| " + " | ".join("-" * col_widths[c] for c in range(col_count)) + " |"
    lines.append(header_line)
    lines.append(sep_line)

    for data_row in normalized[1:]:
        row_line = "| " + " | ".join(data_row[c].ljust(col_widths[c]) for c in range(col_count)) + " |"
        lines.append(row_line)

    return "\n".join(lines)


def write_md_file(doc: IntermediateDocument, output_path: str) -> None:
    """Serializes an IntermediateDocument into a UTF-8 GitHub-Flavored Markdown file."""
    out = Path(output_path)
    os.makedirs(out.parent, exist_ok=True)

    md_blocks: list[str] = []

    for block in doc.blocks:
        if block.block_type == BlockType.HEADING:
            lvl = max(1, min(6, block.level))
            hashes = "#" * lvl
            heading_txt = block.plain_text
            if heading_txt:
                md_blocks.append(f"{hashes} {heading_txt}")
        elif block.block_type == BlockType.PARAGRAPH:
            para_txt = _render_spans_md(block.spans)
            if para_txt:
                md_blocks.append(para_txt)
        elif block.block_type == BlockType.CODE_BLOCK:
            code = block.code_text.strip("\r\n")
            md_blocks.append(f"```\n{code}\n```")
        elif block.block_type == BlockType.LIST:
            list_lines: list[str] = []
            for idx, item in enumerate(block.list_items, start=1):
                prefix = f"{idx}." if block.ordered else "-"
                list_lines.append(f"{prefix} {item.strip()}")
            if list_lines:
                md_blocks.append("\n".join(list_lines))
        elif block.block_type == BlockType.TABLE:
            tbl_md = _render_table_md(block.table_rows)
            if tbl_md:
                md_blocks.append(tbl_md)
        elif block.block_type == BlockType.HORIZONTAL_RULE:
            md_blocks.append("---")

    content = "\n\n".join(md_blocks).strip() + "\n"
    out.write_text(content, encoding="utf-8")
