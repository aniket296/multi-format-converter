"""Unit tests verifying all 5 writers and all 20 cross-format conversion paths."""
from pathlib import Path
import pytest
from src.core.conversion_router import convert_single_file, parse_document, write_document
from src.models import DocFormat, IntermediateDocument

ALL_FORMATS = [
    DocFormat.MD,
    DocFormat.DOCX,
    DocFormat.PDF,
    DocFormat.RTF,
    DocFormat.HTML,
]

CROSS_FORMAT_PAIRS = [
    (src, tgt) for src in ALL_FORMATS for tgt in ALL_FORMATS if src != tgt
]


@pytest.mark.parametrize("target_fmt", ALL_FORMATS)
def test_writers_emit_non_empty_documents(
    tmp_path: Path,
    canonical_dom: IntermediateDocument,
    target_fmt: DocFormat,
) -> None:
    """Verifies every writer serializes canonical_dom to a valid non-empty file."""
    out_file = tmp_path / f"written.{target_fmt.value}"
    write_document(canonical_dom, str(out_file), target_format=target_fmt)

    assert out_file.exists()
    assert out_file.stat().st_size > 50

    reparsed = parse_document(str(out_file), source_format=target_fmt)
    assert reparsed.heading_count >= 1
    assert reparsed.table_count >= 1
    assert reparsed.word_count >= 20


@pytest.mark.parametrize("src_fmt,tgt_fmt", CROSS_FORMAT_PAIRS)
def test_all_20_conversion_paths(
    tmp_path: Path,
    sample_files: dict[DocFormat, Path],
    src_fmt: DocFormat,
    tgt_fmt: DocFormat,
) -> None:
    """Verifies all 20 cross-format conversion paths produce valid, parseable documents."""
    src_path = sample_files[src_fmt]
    out_path = tmp_path / f"converted_{src_fmt.value}_to_{tgt_fmt.value}.{tgt_fmt.value}"

    dom = convert_single_file(
        source_path=str(src_path),
        target_path=str(out_path),
        source_format=src_fmt,
        target_format=tgt_fmt,
    )

    assert out_path.exists()
    assert out_path.stat().st_size > 40
    assert dom.word_count >= 20

    # Parse the generated target file back into DOM to verify structural preservation
    target_dom = parse_document(str(out_path), source_format=tgt_fmt)
    assert target_dom.word_count >= 20
    assert target_dom.table_count >= 1
    assert "Quarterly Architecture Review" in target_dom.get_summary_preview()


def test_multi_hop_conversion_chains(
    tmp_path: Path,
    sample_files: dict[DocFormat, Path],
) -> None:
    """Verifies multi-hop conversion chains (MD -> DOCX -> HTML and HTML -> PDF -> MD)."""
    # Chain 1: MD -> DOCX -> HTML
    step1_docx = tmp_path / "chain1.docx"
    step2_html = tmp_path / "chain1.html"
    convert_single_file(str(sample_files[DocFormat.MD]), str(step1_docx), DocFormat.MD, DocFormat.DOCX)
    convert_single_file(str(step1_docx), str(step2_html), DocFormat.DOCX, DocFormat.HTML)
    dom_chain1 = parse_document(str(step2_html), DocFormat.HTML)
    assert dom_chain1.heading_count == 2
    assert dom_chain1.table_count == 1

    # Chain 2: HTML -> PDF -> MD
    step1_pdf = tmp_path / "chain2.pdf"
    step2_md = tmp_path / "chain2.md"
    convert_single_file(str(sample_files[DocFormat.HTML]), str(step1_pdf), DocFormat.HTML, DocFormat.PDF)
    convert_single_file(str(step1_pdf), str(step2_md), DocFormat.PDF, DocFormat.MD)
    dom_chain2 = parse_document(str(step2_md), DocFormat.MD)
    assert dom_chain2.heading_count >= 2
    assert dom_chain2.table_count == 1
