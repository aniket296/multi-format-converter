"""Markdown parser converting UTF-8 Markdown files into IntermediateDocument DOM."""
from pathlib import Path
import markdown
from src.core.parsers.html_parser import parse_html_string
from src.models.doc_format import DocFormat
from src.models.intermediate_dom import IntermediateDocument


def parse_md_file(file_path: str) -> IntermediateDocument:
    """Reads a UTF-8 Markdown file and converts it into an IntermediateDocument."""
    path = Path(file_path)
    md_text = path.read_text(encoding="utf-8", errors="replace")

    html_fragment = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"],
    )
    doc = parse_html_string(
        html_text=html_fragment,
        default_title=path.stem,
        source_format=DocFormat.MD,
    )
    doc.source_format = DocFormat.MD
    return doc
