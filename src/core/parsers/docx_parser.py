"""DOCX parser converting Microsoft Word (.docx) files into IntermediateDocument DOM."""
from pathlib import Path
import docx
from docx.document import Document as DocxDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
from src.models.doc_format import DocFormat
from src.models.intermediate_dom import (
    BlockType,
    DocBlock,
    IntermediateDocument,
    TextSpan,
)


def _iter_docx_block_items(doc: DocxDocument):
    """Yields Paragraph and Table instances in exact document body order."""
    body = doc.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


def _extract_paragraph_spans(para: Paragraph) -> list[TextSpan]:
    """Extracts inline TextSpans from a Word Paragraph's runs."""
    spans: list[TextSpan] = []
    for run in para.runs:
        txt = run.text
        if not txt:
            continue
        is_bold = bool(run.bold)
        is_italic = bool(run.italic)
        font_name = (run.font.name or "").lower() if run.font else ""
        is_code = font_name in ("consolas", "courier new", "monospace", "lucida console")

        if spans and (
            spans[-1].bold == is_bold
            and spans[-1].italic == is_italic
            and spans[-1].code == is_code
        ):
            spans[-1].text += txt
        else:
            spans.append(TextSpan(text=txt, bold=is_bold, italic=is_italic, code=is_code))

    if not spans and para.text.strip():
        spans.append(TextSpan(text=para.text.strip()))
    return spans


def parse_docx_file(file_path: str) -> IntermediateDocument:
    """Parses a .docx file into a canonical IntermediateDocument."""
    path = Path(file_path)
    doc = docx.Document(str(path))

    title = path.stem
    if doc.core_properties and doc.core_properties.title and doc.core_properties.title.strip():
        title = doc.core_properties.title.strip()

    blocks: list[DocBlock] = []
    pending_list_items: list[str] = []
    pending_list_ordered: bool = False

    def flush_pending_list() -> None:
        nonlocal pending_list_items
        if pending_list_items:
            blocks.append(
                DocBlock(
                    block_type=BlockType.LIST,
                    list_items=list(pending_list_items),
                    ordered=pending_list_ordered,
                )
            )
            pending_list_items = []

    for item in _iter_docx_block_items(doc):
        if isinstance(item, Paragraph):
            text = item.text.strip()
            if not text:
                flush_pending_list()
                continue

            style_name = (item.style.name if item.style and item.style.name else "Normal").strip()
            style_lower = style_name.lower()

            # Check for list styles or XML numbering properties
            has_numpr = item._p.pPr is not None and item._p.pPr.numPr is not None
            if "list bullet" in style_lower or "list number" in style_lower or has_numpr:
                is_ordered = "number" in style_lower
                if pending_list_items and pending_list_ordered != is_ordered:
                    flush_pending_list()
                pending_list_ordered = is_ordered
                pending_list_items.append(text)
                continue

            flush_pending_list()

            # Check for Title / Heading styles
            if style_lower == "title":
                if title == path.stem:
                    title = text
                blocks.append(
                    DocBlock(
                        block_type=BlockType.HEADING,
                        spans=[TextSpan(text=text, bold=True)],
                        level=1,
                    )
                )
            elif style_lower.startswith("heading"):
                parts = style_lower.split()
                level = 1
                if len(parts) >= 2 and parts[1].isdigit():
                    level = max(1, min(6, int(parts[1])))
                spans = _extract_paragraph_spans(item)
                if title == path.stem and level == 1:
                    title = text
                blocks.append(
                    DocBlock(
                        block_type=BlockType.HEADING,
                        spans=spans,
                        level=level,
                    )
                )
            elif "code" in style_lower or (
                item.runs
                and all(
                    (r.font.name or "").lower() in ("consolas", "courier new")
                    for r in item.runs
                    if r.text.strip()
                )
                and "\n" in item.text
            ):
                blocks.append(
                    DocBlock(
                        block_type=BlockType.CODE_BLOCK,
                        code_text=item.text.strip("\r\n"),
                    )
                )
            else:
                spans = _extract_paragraph_spans(item)
                blocks.append(
                    DocBlock(
                        block_type=BlockType.PARAGRAPH,
                        spans=spans,
                    )
                )

        elif isinstance(item, Table):
            flush_pending_list()
            rows_data: list[list[str]] = []
            for row in item.rows:
                row_cells = [" ".join(cell.text.split()).strip() for cell in row.cells]
                if any(row_cells):
                    rows_data.append(row_cells)
            if rows_data:
                blocks.append(
                    DocBlock(
                        block_type=BlockType.TABLE,
                        table_rows=rows_data,
                    )
                )

    flush_pending_list()

    return IntermediateDocument(
        title=title,
        source_format=DocFormat.DOCX,
        blocks=blocks,
    )
