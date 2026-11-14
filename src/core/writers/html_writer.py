"""HTML5 writer serializing IntermediateDocument DOM to styled standalone or fragment HTML."""
import html
import os
from pathlib import Path
from src.models.intermediate_dom import (
    BlockType,
    DocBlock,
    IntermediateDocument,
    TextSpan,
)

_EMBEDDED_CSS = """
:root {
    --bg-body: #F8FAFC;
    --bg-sheet: #FFFFFF;
    --text-main: #0F172A;
    --text-muted: #475569;
    --accent: #1D4ED8;
    --border-color: #CBD5E1;
    --code-bg: #F1F5F9;
}
* { box-sizing: border-box; }
body {
    margin: 0;
    padding: 32px 16px;
    background-color: var(--bg-body);
    color: var(--text-main);
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.65;
    font-size: 11pt;
}
.document-container {
    max-width: 860px;
    margin: 0 auto;
    background: var(--bg-sheet);
    padding: 48px 56px;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(15, 23, 42, 0.08);
}
h1, h2, h3, h4, h5, h6 {
    color: #0F172A;
    margin-top: 1.4em;
    margin-bottom: 0.5em;
    line-height: 1.25;
    font-weight: 700;
}
h1 { font-size: 22pt; border-bottom: 2px solid #E2E8F0; padding-bottom: 8px; margin-top: 0; }
h2 { font-size: 16pt; color: #1E3A8A; }
h3 { font-size: 13.5pt; }
h4 { font-size: 12pt; }
p { margin: 0 0 1em 0; }
code {
    font-family: Consolas, "Courier New", monospace;
    background-color: var(--code-bg);
    padding: 2px 5px;
    border-radius: 4px;
    font-size: 0.92em;
}
pre {
    background-color: #0F172A;
    color: #F8FAFC;
    padding: 14px 18px;
    border-radius: 6px;
    overflow-x: auto;
    font-family: Consolas, "Courier New", monospace;
    font-size: 9.5pt;
    line-height: 1.5;
    margin: 0 0 1.2em 0;
}
pre code {
    background: transparent;
    color: inherit;
    padding: 0;
}
ul, ol {
    margin: 0 0 1.1em 0;
    padding-left: 26px;
}
li { margin-bottom: 0.35em; }
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.2em 0;
    font-size: 10pt;
}
th, td {
    border: 1px solid var(--border-color);
    padding: 8px 12px;
    text-align: left;
    vertical-align: top;
}
th {
    background-color: #1E293B;
    color: #FFFFFF;
    font-weight: 600;
}
tr:nth-child(even) td {
    background-color: #F8FAFC;
}
hr {
    border: none;
    border-top: 1px solid var(--border-color);
    margin: 1.8em 0;
}
@media print {
    body { background: #FFFFFF; padding: 0; }
    .document-container { box-shadow: none; padding: 0; max-width: 100%; }
}
""".strip()


def _render_spans_html(spans: list[TextSpan]) -> str:
    """Renders inline TextSpans into HTML with proper entity escaping."""
    parts: list[str] = []
    for sp in spans:
        escaped = html.escape(sp.text)
        if sp.code:
            escaped = f"<code>{escaped}</code>"
        if sp.italic:
            escaped = f"<em>{escaped}</em>"
        if sp.bold:
            escaped = f"<strong>{escaped}</strong>"
        parts.append(escaped)
    return "".join(parts)


def render_dom_to_html(doc: IntermediateDocument, standalone: bool = True) -> str:
    """Renders an IntermediateDocument to an HTML5 document or body fragment."""
    body_lines: list[str] = []

    for block in doc.blocks:
        if block.block_type == BlockType.HEADING:
            lvl = max(1, min(6, block.level))
            inner = _render_spans_html(block.spans) or html.escape(block.plain_text)
            if inner.strip():
                body_lines.append(f"<h{lvl}>{inner}</h{lvl}>")
        elif block.block_type == BlockType.PARAGRAPH:
            inner = _render_spans_html(block.spans)
            if inner.strip():
                body_lines.append(f"<p>{inner}</p>")
        elif block.block_type == BlockType.CODE_BLOCK:
            escaped_code = html.escape(block.code_text)
            body_lines.append(f"<pre><code>{escaped_code}</code></pre>")
        elif block.block_type == BlockType.LIST:
            tag = "ol" if block.ordered else "ul"
            body_lines.append(f"<{tag}>")
            for item in block.list_items:
                body_lines.append(f"  <li>{html.escape(item)}</li>")
            body_lines.append(f"</{tag}>")
        elif block.block_type == BlockType.TABLE:
            if not block.table_rows:
                continue
            body_lines.append('<table border="1" cellspacing="0" cellpadding="6">')
            for r_idx, row in enumerate(block.table_rows):
                body_lines.append("  <tr>")
                cell_tag = "th" if r_idx == 0 else "td"
                for cell in row:
                    body_lines.append(f"    <{cell_tag}>{html.escape(cell)}</{cell_tag}>")
                body_lines.append("  </tr>")
            body_lines.append("</table>")
        elif block.block_type == BlockType.HORIZONTAL_RULE:
            body_lines.append("<hr />")

    inner_html = "\n".join(body_lines)
    if not standalone:
        return inner_html

    safe_title = html.escape(doc.title or "Document")
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8" />\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
        f"  <title>{safe_title}</title>\n"
        f"  <style>\n{_EMBEDDED_CSS}\n  </style>\n"
        "</head>\n"
        "<body>\n"
        '  <main class="document-container">\n'
        f"{inner_html}\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )


def write_html_file(doc: IntermediateDocument, output_path: str) -> None:
    """Writes an IntermediateDocument to a standalone UTF-8 HTML5 file."""
    out = Path(output_path)
    os.makedirs(out.parent, exist_ok=True)
    html_str = render_dom_to_html(doc, standalone=True)
    out.write_text(html_str, encoding="utf-8")
