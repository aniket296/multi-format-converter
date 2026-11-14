"""Universal 20-path conversion router dispatching between 5 parsers and 5 writers."""
from pathlib import Path
from typing import Optional
from src.core.parsers import (
    parse_docx_file,
    parse_html_file,
    parse_md_file,
    parse_pdf_file,
    parse_rtf_file,
)
from src.core.writers import (
    write_docx_file,
    write_html_file,
    write_md_file,
    write_pdf_file,
    write_rtf_file,
)
from src.models.doc_format import DocFormat
from src.models.intermediate_dom import IntermediateDocument


def parse_document(
    source_path: str,
    source_format: Optional[DocFormat] = None,
) -> IntermediateDocument:
    """Dispatches source file parsing to the appropriate format parser."""
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    fmt = source_format or DocFormat.from_extension(path.suffix)
    if fmt is None:
        raise ValueError(f"Unsupported source file format for path: {source_path}")

    if fmt == DocFormat.HTML:
        return parse_html_file(str(path))
    if fmt == DocFormat.MD:
        return parse_md_file(str(path))
    if fmt == DocFormat.DOCX:
        return parse_docx_file(str(path))
    if fmt == DocFormat.PDF:
        return parse_pdf_file(str(path))
    if fmt == DocFormat.RTF:
        return parse_rtf_file(str(path))

    raise ValueError(f"No parser registered for format: {fmt}")


def write_document(
    doc: IntermediateDocument,
    target_path: str,
    target_format: DocFormat,
    page_size: str = "A4",
) -> None:
    """Dispatches IntermediateDocument serialization to the matching format writer."""
    if target_format == DocFormat.HTML:
        write_html_file(doc, target_path)
    elif target_format == DocFormat.MD:
        write_md_file(doc, target_path)
    elif target_format == DocFormat.DOCX:
        write_docx_file(doc, target_path)
    elif target_format == DocFormat.PDF:
        write_pdf_file(doc, target_path, page_size=page_size)
    elif target_format == DocFormat.RTF:
        write_rtf_file(doc, target_path)
    else:
        raise ValueError(f"No writer registered for format: {target_format}")


def convert_single_file(
    source_path: str,
    target_path: str,
    source_format: DocFormat,
    target_format: DocFormat,
    page_size: str = "A4",
) -> IntermediateDocument:
    """
    Executes a complete single-file conversion through the IntermediateDocument DOM.

    Returns the parsed IntermediateDocument so structural metrics can be inspected.
    """
    doc = parse_document(source_path, source_format=source_format)
    write_document(doc, target_path, target_format=target_format, page_size=page_size)
    return doc
