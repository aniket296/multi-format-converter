"""RTF parser converting Rich Text Format (.rtf) files into IntermediateDocument DOM."""
import re
from pathlib import Path
from striprtf.striprtf import rtf_to_text
from src.models.doc_format import DocFormat
from src.models.intermediate_dom import (
    BlockType,
    DocBlock,
    IntermediateDocument,
    TextSpan,
)

_BULLET_LINE_RE = re.compile(r"^(?:[•●▪◦\-*]|\d+[.)])\s+(.*)$")
_MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def parse_rtf_file(file_path: str) -> IntermediateDocument:
    """Parses a .rtf file into a canonical IntermediateDocument."""
    path = Path(file_path)
    raw_rtf = path.read_text(encoding="utf-8", errors="replace")
    plain = rtf_to_text(raw_rtf, errors="ignore")

    lines = [line.rstrip() for line in plain.splitlines()]
    title = path.stem
    blocks: list[DocBlock] = []

    idx = 0
    n = len(lines)

    while idx < n:
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue

        # 1. Check for pipe-delimited or tab-delimited table rows
        if ("|" in line and line.count("|") >= 1) or ("\t" in line):
            table_rows: list[list[str]] = []
            while idx < n:
                cur = lines[idx].strip()
                if not cur:
                    break
                if "|" in cur:
                    parts = [c.strip() for c in cur.strip("|").split("|")]
                    # Skip Markdown separator lines like --- | ---
                    if all(re.match(r"^:?-{2,}:?$", p) for p in parts if p):
                        idx += 1
                        continue
                    if len(parts) >= 2:
                        table_rows.append(parts)
                        idx += 1
                        continue
                elif "\t" in cur:
                    parts = [c.strip() for c in cur.split("\t")]
                    if len(parts) >= 2:
                        table_rows.append(parts)
                        idx += 1
                        continue
                break

            if table_rows:
                blocks.append(
                    DocBlock(
                        block_type=BlockType.TABLE,
                        table_rows=table_rows,
                    )
                )
                continue

        # 2. Check for fenced code block markers
        if line.startswith("```"):
            idx += 1
            code_lines: list[str] = []
            while idx < n and not lines[idx].strip().startswith("```"):
                code_lines.append(lines[idx])
                idx += 1
            if idx < n and lines[idx].strip().startswith("```"):
                idx += 1
            blocks.append(
                DocBlock(
                    block_type=BlockType.CODE_BLOCK,
                    code_text="\n".join(code_lines),
                )
            )
            continue

        # 3. Check for bullet or numbered list items
        bullet_match = _BULLET_LINE_RE.match(line)
        if bullet_match:
            list_items: list[str] = []
            is_ordered = bool(re.match(r"^\d+[.)]", line))
            while idx < n:
                cur = lines[idx].strip()
                m = _BULLET_LINE_RE.match(cur)
                if not m:
                    break
                list_items.append(m.group(1).strip())
                idx += 1
            blocks.append(
                DocBlock(
                    block_type=BlockType.LIST,
                    list_items=list_items,
                    ordered=is_ordered,
                )
            )
            continue

        # 4. Check for Markdown-style heading (# Heading) or short top-level title/section header
        md_h = _MD_HEADING_RE.match(line)
        if md_h:
            lvl = len(md_h.group(1))
            h_text = md_h.group(2).strip()
            if title == path.stem and lvl == 1:
                title = h_text
            blocks.append(
                DocBlock(
                    block_type=BlockType.HEADING,
                    spans=[TextSpan(text=h_text, bold=True)],
                    level=lvl,
                )
            )
            idx += 1
            continue

        # Heuristic: First non-empty short line or uppercase short line without trailing period -> Heading
        is_first_block = len(blocks) == 0
        next_line_blank = (idx + 1 == n) or (not lines[idx + 1].strip())
        if (
            len(line) <= 90
            and not line.endswith(".")
            and next_line_blank
            and (is_first_block or line.isupper() or line.istitle())
        ):
            lvl = 1 if is_first_block else 2
            if is_first_block and title == path.stem:
                title = line
            blocks.append(
                DocBlock(
                    block_type=BlockType.HEADING,
                    spans=[TextSpan(text=line, bold=True)],
                    level=lvl,
                )
            )
            idx += 1
            continue

        # 5. Standard paragraph: collect consecutive non-empty standard lines
        para_lines: list[str] = [line]
        idx += 1
        while idx < n:
            nxt = lines[idx].strip()
            if (
                not nxt
                or "|" in nxt
                or "\t" in nxt
                or _BULLET_LINE_RE.match(nxt)
                or _MD_HEADING_RE.match(nxt)
                or nxt.startswith("```")
            ):
                break
            para_lines.append(nxt)
            idx += 1

        joined_para = " ".join(para_lines).strip()
        if joined_para:
            blocks.append(
                DocBlock(
                    block_type=BlockType.PARAGRAPH,
                    spans=[TextSpan(text=joined_para)],
                )
            )

    return IntermediateDocument(
        title=title,
        source_format=DocFormat.RTF,
        blocks=blocks,
    )
