"""Pytest fixtures providing canonical IntermediateDocument DOM and 5-format sample files."""
import warnings
from pathlib import Path
import pytest

warnings.filterwarnings("ignore", category=FutureWarning)

from src.core.writers import (
    write_docx_file,
    write_html_file,
    write_md_file,
    write_pdf_file,
    write_rtf_file,
)
from src.models import (
    BlockType,
    DocBlock,
    DocFormat,
    IntermediateDocument,
    TextSpan,
)


@pytest.fixture
def canonical_dom() -> IntermediateDocument:
    """Returns a rich canonical IntermediateDocument with headings, spans, list, code, and 3x3 table."""
    return IntermediateDocument(
        title="Quarterly Architecture Review",
        source_format=DocFormat.MD,
        blocks=[
            DocBlock(
                block_type=BlockType.HEADING,
                spans=[TextSpan(text="Quarterly Architecture Review", bold=True)],
                level=1,
            ),
            DocBlock(
                block_type=BlockType.PARAGRAPH,
                spans=[
                    TextSpan(text="This technical specification validates "),
                    TextSpan(text="universal offline conversion", bold=True),
                    TextSpan(text=" with "),
                    TextSpan(text="structural fidelity", italic=True),
                    TextSpan(text=" and "),
                    TextSpan(text="dom_router()", code=True),
                    TextSpan(text=" execution."),
                ],
            ),
            DocBlock(
                block_type=BlockType.HEADING,
                spans=[TextSpan(text="Core Capabilities", bold=True)],
                level=2,
            ),
            DocBlock(
                block_type=BlockType.LIST,
                list_items=[
                    "Multi-threaded worker pool execution",
                    "Recursive folder hierarchy mirroring",
                    "Deterministic collision policies",
                ],
                ordered=False,
            ),
            DocBlock(
                block_type=BlockType.CODE_BLOCK,
                code_text="def verify_pipeline(status: str) -> bool:\n    return status == 'COMPLETED'",
            ),
            DocBlock(
                block_type=BlockType.TABLE,
                table_rows=[
                    ["Format", "Parser", "Writer"],
                    ["Markdown", "Active", "Verified"],
                    ["PDF", "PyMuPDF", "Vector Story"],
                ],
            ),
        ],
    )


@pytest.fixture
def sample_files(tmp_path: Path, canonical_dom: IntermediateDocument) -> dict[DocFormat, Path]:
    """Generates sample .md, .html, .docx, .pdf, and .rtf files on disk from canonical_dom."""
    paths: dict[DocFormat, Path] = {
        DocFormat.MD: tmp_path / "sample.md",
        DocFormat.HTML: tmp_path / "sample.html",
        DocFormat.DOCX: tmp_path / "sample.docx",
        DocFormat.PDF: tmp_path / "sample.pdf",
        DocFormat.RTF: tmp_path / "sample.rtf",
    }
    write_md_file(canonical_dom, str(paths[DocFormat.MD]))
    write_html_file(canonical_dom, str(paths[DocFormat.HTML]))
    write_docx_file(canonical_dom, str(paths[DocFormat.DOCX]))
    write_pdf_file(canonical_dom, str(paths[DocFormat.PDF]))
    write_rtf_file(canonical_dom, str(paths[DocFormat.RTF]))
    return paths
