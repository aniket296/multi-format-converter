"""DOCX writer building native Microsoft Word (.docx) files from IntermediateDocument DOM."""
import os
from pathlib import Path
import docx
from docx.shared import Pt, RGBColor
from src.models.intermediate_dom import (
    BlockType,
    IntermediateDocument,
    TextSpan,
)


def _populate_docx_runs(paragraph, spans: list[TextSpan]) -> None:
    """Appends styled runs to a python-docx paragraph from a list of TextSpans."""
    for sp in spans:
        if not sp.text:
            continue
        run = paragraph.add_run(sp.text)
        run.bold = sp.bold
        run.italic = sp.italic
        if sp.code:
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)


def write_docx_file(doc: IntermediateDocument, output_path: str) -> None:
    """Writes an IntermediateDocument to a native Microsoft Word (.docx) file."""
    out = Path(output_path)
    os.makedirs(out.parent, exist_ok=True)

    word_doc = docx.Document()
    if doc.title:
        word_doc.core_properties.title = doc.title

    # Configure default Normal style font
    normal_style = word_doc.styles["Normal"]
    normal_style.font.name = "Segoe UI"
    normal_style.font.size = Pt(11)

    for block in doc.blocks:
        if block.block_type == BlockType.HEADING:
            lvl = max(1, min(6, block.level))
            text = block.plain_text
            if text:
                word_doc.add_heading(text, level=lvl)
        elif block.block_type == BlockType.PARAGRAPH:
            if not block.plain_text:
                continue
            p = word_doc.add_paragraph()
            _populate_docx_runs(p, block.spans)
        elif block.block_type == BlockType.CODE_BLOCK:
            p = word_doc.add_paragraph()
            run = p.add_run(block.code_text.strip("\r\n"))
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        elif block.block_type == BlockType.LIST:
            style_name = "List Number" if block.ordered else "List Bullet"
            for item in block.list_items:
                if item.strip():
                    word_doc.add_paragraph(item.strip(), style=style_name)
        elif block.block_type == BlockType.TABLE:
            if not block.table_rows:
                continue
            row_count = len(block.table_rows)
            col_count = max((len(r) for r in block.table_rows), default=0)
            if col_count == 0:
                continue
            table = word_doc.add_table(rows=row_count, cols=col_count)
            table.style = "Table Grid"
            for r_idx, row_data in enumerate(block.table_rows):
                row_cells = table.rows[r_idx].cells
                for c_idx in range(col_count):
                    val = row_data[c_idx] if c_idx < len(row_data) else ""
                    row_cells[c_idx].text = val
                    if r_idx == 0 and row_cells[c_idx].paragraphs:
                        for run in row_cells[c_idx].paragraphs[0].runs:
                            run.bold = True
        elif block.block_type == BlockType.HORIZONTAL_RULE:
            p = word_doc.add_paragraph()
            run = p.add_run("─" * 48)
            run.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    word_doc.save(str(out))
