"""RTF 1.5 writer serializing IntermediateDocument DOM to standards-compliant Rich Text Format."""
import os
from pathlib import Path
from src.models.intermediate_dom import (
    BlockType,
    IntermediateDocument,
    TextSpan,
)

# Heading level to half-point font size (\fsN where N = 2 * pt)
_HEADING_FS_MAP = {
    1: 36,  # 18pt
    2: 30,  # 15pt
    3: 26,  # 13pt
    4: 24,  # 12pt
    5: 22,  # 11pt
    6: 20,  # 10pt
}


def _escape_rtf_text(text: str) -> str:
    """Escapes special RTF characters and encodes non-ASCII codepoints as \\uN?."""
    out: list[str] = []
    for ch in text:
        code = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == "{":
            out.append("\\{")
        elif ch == "}":
            out.append("\\}")
        elif ch == "\n":
            out.append("\\line ")
        elif ch == "\t":
            out.append("\\tab ")
        elif 32 <= code <= 126:
            out.append(ch)
        elif code > 126:
            # RTF 16-bit signed integer Unicode escape
            signed = code if code < 32768 else code - 65536
            out.append(f"\\u{signed}?")
    return "".join(out)


def _render_spans_rtf(spans: list[TextSpan]) -> str:
    """Renders inline TextSpans into RTF runs."""
    parts: list[str] = []
    for sp in spans:
        if not sp.text:
            continue
        escaped = _escape_rtf_text(sp.text)
        prefix = ""
        suffix = ""
        if sp.code:
            prefix += "\\f1\\fs19 "
            suffix = "\\f0\\fs22 " + suffix
        if sp.bold:
            prefix += "\\b "
            suffix = "\\b0 " + suffix
        if sp.italic:
            prefix += "\\i "
            suffix = "\\i0 " + suffix
        parts.append(f"{{{prefix}{escaped}{suffix}}}")
    return "".join(parts)


def write_rtf_file(doc: IntermediateDocument, output_path: str) -> None:
    """Writes an IntermediateDocument to a standards-compliant RTF 1.5 file."""
    out = Path(output_path)
    os.makedirs(out.parent, exist_ok=True)

    lines: list[str] = [
        r"{\rtf1\ansi\ansicpg1252\deff0\nouicompat",
        r"{\fonttbl{\f0\fnil\fcharset0 Segoe UI;}{\f1\fmodern\fcharset0 Consolas;}}",
        r"{\colortbl ;\red15\green23\blue42;\red29\green78\blue216;\red100\green116\blue139;}",
        r"\viewkind4\uc1\pard\f0\fs22\cf1",
    ]

    if doc.title:
        safe_title = _escape_rtf_text(doc.title)
        lines.append(f"{{\\info{{\\title {safe_title}}}}}")

    for block in doc.blocks:
        if block.block_type == BlockType.HEADING:
            lvl = max(1, min(6, block.level))
            fs = _HEADING_FS_MAP.get(lvl, 24)
            text = _escape_rtf_text(block.plain_text)
            if text:
                lines.append(f"\\pard\\sa180\\sb240\\b\\fs{fs}\\cf2 {text}\\b0\\fs22\\cf1\\par")
                lines.append("\\par")
        elif block.block_type == BlockType.PARAGRAPH:
            rendered = _render_spans_rtf(block.spans)
            if rendered.strip():
                lines.append(f"\\pard\\sa160\\fs22\\cf1 {rendered}\\par")
                lines.append("\\par")
        elif block.block_type == BlockType.CODE_BLOCK:
            code_escaped = _escape_rtf_text(block.code_text.strip("\r\n"))
            lines.append("\\pard\\sa160\\f1\\fs19 ```\\line " + code_escaped + "\\line ```\\f0\\fs22\\par")
            lines.append("\\par")
        elif block.block_type == BlockType.LIST:
            for idx, item in enumerate(block.list_items, start=1):
                marker = f"{idx}. " if block.ordered else "\\u8226? "
                escaped_item = _escape_rtf_text(item.strip())
                lines.append(f"\\pard\\li360\\sa80\\fs22 {marker}{escaped_item}\\par")
            lines.append("\\par")
        elif block.block_type == BlockType.TABLE:
            if not block.table_rows:
                continue
            col_count = max((len(r) for r in block.table_rows), default=0)
            if col_count == 0:
                continue
            # Total width ~ 9000 twips (6.25 inches)
            col_width = max(1200, int(9000 / col_count))
            for r_idx, row in enumerate(block.table_rows):
                cell_defs = "".join(
                    f"\\clbrdrt\\brdrs\\brdrw10\\clbrdrl\\brdrs\\brdrw10"
                    f"\\clbrdrb\\brdrs\\brdrw10\\clbrdrr\\brdrs\\brdrw10\\cellx{col_width * (c + 1)}"
                    for c in range(col_count)
                )
                row_cells_rtf: list[str] = []
                for c in range(col_count):
                    val = row[c] if c < len(row) else ""
                    esc = _escape_rtf_text(val)
                    if r_idx == 0:
                        row_cells_rtf.append(f"\\pard\\intbl\\b {esc}\\b0\\cell")
                    else:
                        row_cells_rtf.append(f"\\pard\\intbl {esc}\\cell")
                lines.append(f"\\trowd\\trgaph108{cell_defs} " + " ".join(row_cells_rtf) + "\\row")
            lines.append("\\pard\\sa160\\par")
        elif block.block_type == BlockType.HORIZONTAL_RULE:
            lines.append("\\pard\\sa160\\cf3 ----------------------------------------\\cf1\\par")

    lines.append("}")
    out.write_text("\n".join(lines), encoding="utf-8")
