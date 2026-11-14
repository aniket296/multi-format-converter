"""Unit tests verifying all 5 format parsers into IntermediateDocument DOM."""
from pathlib import Path
from src.core.parsers import (
    parse_docx_file,
    parse_html_file,
    parse_md_file,
    parse_pdf_file,
    parse_rtf_file,
)
from src.models import BlockType, DocFormat


def test_parse_md_file_to_dom(sample_files: dict[DocFormat, Path]) -> None:
    """Verifies Markdown parser extracts headings, inline spans, lists, code blocks, and tables."""
    doc = parse_md_file(str(sample_files[DocFormat.MD]))
    assert doc.source_format == DocFormat.MD
    assert doc.title == "Quarterly Architecture Review"
    assert doc.heading_count == 2
    assert doc.table_count == 1
    assert doc.word_count >= 30

    block_types = [b.block_type for b in doc.blocks]
    assert BlockType.HEADING in block_types
    assert BlockType.PARAGRAPH in block_types
    assert BlockType.LIST in block_types
    assert BlockType.CODE_BLOCK in block_types
    assert BlockType.TABLE in block_types

    # Check inline formatting spans on first paragraph
    first_para = next(b for b in doc.blocks if b.block_type == BlockType.PARAGRAPH)
    assert any(s.bold and "universal offline conversion" in s.text for s in first_para.spans)
    assert any(s.italic and "structural fidelity" in s.text for s in first_para.spans)
    assert any(s.code and "dom_router()" in s.text for s in first_para.spans)


def test_parse_html_file_to_dom(sample_files: dict[DocFormat, Path]) -> None:
    """Verifies HTML parser extracts semantic blocks, inline spans, and tables."""
    doc = parse_html_file(str(sample_files[DocFormat.HTML]))
    assert doc.source_format == DocFormat.HTML
    assert doc.title == "Quarterly Architecture Review"
    assert doc.heading_count == 2
    assert doc.table_count == 1
    assert doc.word_count >= 30

    tbl_block = next(b for b in doc.blocks if b.block_type == BlockType.TABLE)
    assert len(tbl_block.table_rows) == 3
    assert tbl_block.table_rows[0] == ["Format", "Parser", "Writer"]


def test_parse_docx_file_to_dom(sample_files: dict[DocFormat, Path]) -> None:
    """Verifies DOCX parser extracts Word headings, runs, lists, and tables in order."""
    doc = parse_docx_file(str(sample_files[DocFormat.DOCX]))
    assert doc.source_format == DocFormat.DOCX
    assert doc.title == "Quarterly Architecture Review"
    assert doc.heading_count == 2
    assert doc.table_count == 1
    assert doc.word_count >= 30

    list_block = next(b for b in doc.blocks if b.block_type == BlockType.LIST)
    assert len(list_block.list_items) == 3
    assert "Recursive folder hierarchy mirroring" in list_block.list_items


def test_parse_pdf_file_to_dom(sample_files: dict[DocFormat, Path]) -> None:
    """Verifies PDF parser extracts headings, body text, and bordered grid tables."""
    doc = parse_pdf_file(str(sample_files[DocFormat.PDF]))
    assert doc.source_format == DocFormat.PDF
    assert doc.heading_count >= 2
    assert doc.table_count == 1
    assert doc.word_count >= 25
    preview = doc.get_summary_preview()
    assert "Quarterly Architecture Review" in preview
    assert "TABLE" in preview


def test_parse_rtf_file_to_dom(sample_files: dict[DocFormat, Path]) -> None:
    """Verifies RTF parser extracts headings, paragraphs, lists, code, and table rows."""
    doc = parse_rtf_file(str(sample_files[DocFormat.RTF]))
    assert doc.source_format == DocFormat.RTF
    assert doc.heading_count >= 2
    assert doc.table_count == 1
    assert doc.word_count >= 25
    tbl_block = next(b for b in doc.blocks if b.block_type == BlockType.TABLE)
    assert len(tbl_block.table_rows) == 3
    assert "Markdown" in tbl_block.table_rows[1]
