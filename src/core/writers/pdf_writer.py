"""PDF writer typesetting multi-page vector PDFs from IntermediateDocument DOM via PyMuPDF."""
import io
import os
from pathlib import Path
import fitz
from src.core.writers.html_writer import render_dom_to_html
from src.models.intermediate_dom import IntermediateDocument

_PDF_STORY_CSS = """
body {
    font-family: sans-serif;
    font-size: 10.5pt;
    line-height: 1.45;
    color: #0F172A;
}
h1 { font-size: 20pt; font-weight: bold; color: #0F172A; margin-top: 10pt; margin-bottom: 6pt; }
h2 { font-size: 15.5pt; font-weight: bold; color: #1E3A8A; margin-top: 9pt; margin-bottom: 5pt; }
h3 { font-size: 13pt; font-weight: bold; color: #1E293B; margin-top: 8pt; margin-bottom: 4pt; }
h4, h5, h6 { font-size: 11.5pt; font-weight: bold; margin-top: 6pt; margin-bottom: 3pt; }
p { margin-top: 0pt; margin-bottom: 7pt; }
pre, code {
    font-family: monospace;
    font-size: 9pt;
    background-color: #F1F5F9;
}
pre {
    padding: 6pt;
    margin-bottom: 8pt;
}
ul, ol {
    margin-top: 2pt;
    margin-bottom: 8pt;
    padding-left: 16pt;
}
li { margin-bottom: 3pt; }
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 6pt;
    margin-bottom: 10pt;
}
th, td {
    border: 1pt solid #64748B;
    padding: 4pt 6pt;
    text-align: left;
}
th {
    background-color: #E2E8F0;
    font-weight: bold;
}
""".strip()


def write_pdf_file(
    doc: IntermediateDocument,
    output_path: str,
    page_size: str = "A4",
) -> None:
    """Typesets an IntermediateDocument into a multi-page vector PDF with footers."""
    out = Path(output_path)
    os.makedirs(out.parent, exist_ok=True)

    html_fragment = render_dom_to_html(doc, standalone=False)
    if not html_fragment.strip():
        html_fragment = f"<h1>{doc.title or 'Untitled Document'}</h1>"

    full_story_html = (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        f"<body>{html_fragment}</body></html>"
    )

    mediabox = fitz.paper_rect(page_size if page_size in ("A4", "letter", "legal") else "A4")
    margin = 50.0
    where = mediabox + (margin, margin, -margin, -margin)

    story = fitz.Story(html=full_story_html, user_css=_PDF_STORY_CSS)
    bio = io.BytesIO()
    writer = fitz.DocumentWriter(bio)

    more = 1
    while more:
        device = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
    writer.close()

    # Re-open with fitz to stamp metadata and "Page X of Y" footers
    bio.seek(0)
    pdf_doc = fitz.open("pdf", bio.read())
    pdf_doc.set_metadata(
        {
            "title": doc.title or out.stem,
            "creator": "Multi-Format Document Batch Converter",
            "producer": "PyMuPDF Story Engine",
        }
    )

    total_pages = len(pdf_doc)
    for idx, page in enumerate(pdf_doc, start=1):
        footer_text = f"Page {idx} of {total_pages}"
        footer_rect = fitz.Rect(
            margin,
            mediabox.height - 34,
            mediabox.width - margin,
            mediabox.height - 14,
        )
        page.insert_textbox(
            footer_rect,
            footer_text,
            fontsize=8.5,
            fontname="helv",
            color=(0.40, 0.45, 0.55),
            align=fitz.TEXT_ALIGN_RIGHT,
        )

    pdf_doc.save(str(out), garbage=3, deflate=True)
    pdf_doc.close()
