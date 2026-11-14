"""HTML parser converting HTML5 documents or fragments into IntermediateDocument DOM."""
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag
from src.models.doc_format import DocFormat
from src.models.intermediate_dom import (
    BlockType,
    DocBlock,
    IntermediateDocument,
    TextSpan,
)


def _extract_inline_spans(
    node: Tag | NavigableString,
    bold: bool = False,
    italic: bool = False,
    code: bool = False,
) -> list[TextSpan]:
    """Recursively extracts styled TextSpans from an HTML element tree."""
    spans: list[TextSpan] = []

    if isinstance(node, NavigableString):
        text = str(node)
        if text:
            # Collapse internal newlines to spaces for flow elements
            normalized = " ".join(text.splitlines())
            if normalized:
                spans.append(TextSpan(text=normalized, bold=bold, italic=italic, code=code))
        return spans

    if isinstance(node, Tag):
        tag_name = node.name.lower() if node.name else ""
        if tag_name == "br":
            spans.append(TextSpan(text="\n", bold=bold, italic=italic, code=code))
            return spans

        cur_bold = bold or tag_name in ("b", "strong")
        cur_italic = italic or tag_name in ("i", "em")
        cur_code = code or tag_name in ("code", "kbd", "samp", "tt")

        for child in node.children:
            spans.extend(_extract_inline_spans(child, cur_bold, cur_italic, cur_code))

    return _merge_adjacent_spans(spans)


def _merge_adjacent_spans(spans: list[TextSpan]) -> list[TextSpan]:
    """Merges consecutive TextSpans that share identical inline formatting."""
    if not spans:
        return []
    merged: list[TextSpan] = [spans[0]]
    for sp in spans[1:]:
        prev = merged[-1]
        if prev.bold == sp.bold and prev.italic == sp.italic and prev.code == sp.code:
            prev.text += sp.text
        else:
            merged.append(sp)
    return merged


def parse_html_string(
    html_text: str,
    default_title: str = "Document",
    source_format: DocFormat = DocFormat.HTML,
) -> IntermediateDocument:
    """Parses an HTML string into a canonical IntermediateDocument."""
    soup = BeautifulSoup(html_text, "html.parser")

    # Remove non-visible metadata/script elements
    for unwanted in soup(["script", "style", "noscript", "meta", "link"]):
        unwanted.decompose()

    title = default_title
    if soup.title and soup.title.string and soup.title.string.strip():
        title = soup.title.string.strip()

    blocks: list[DocBlock] = []
    root = soup.body if soup.body else soup

    def walk_container(container: Tag) -> None:
        for child in container.children:
            if isinstance(child, NavigableString):
                raw = str(child).strip()
                if raw:
                    blocks.append(
                        DocBlock(
                            block_type=BlockType.PARAGRAPH,
                            spans=[TextSpan(text=raw)],
                        )
                    )
                continue

            if not isinstance(child, Tag) or not child.name:
                continue

            tag = child.name.lower()

            if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                level = int(tag[1])
                spans = _extract_inline_spans(child)
                text = "".join(s.text for s in spans).strip()
                if text:
                    blocks.append(
                        DocBlock(
                            block_type=BlockType.HEADING,
                            spans=spans,
                            level=level,
                        )
                    )
            elif tag == "p":
                spans = _extract_inline_spans(child)
                if "".join(s.text for s in spans).strip():
                    blocks.append(
                        DocBlock(
                            block_type=BlockType.PARAGRAPH,
                            spans=spans,
                        )
                    )
            elif tag == "pre":
                code_str = child.get_text()
                if code_str.strip():
                    blocks.append(
                        DocBlock(
                            block_type=BlockType.CODE_BLOCK,
                            code_text=code_str.strip("\r\n"),
                        )
                    )
            elif tag in ("ul", "ol"):
                items: list[str] = []
                for li in child.find_all("li", recursive=False):
                    li_text = " ".join(li.get_text().split()).strip()
                    if li_text:
                        items.append(li_text)
                if items:
                    blocks.append(
                        DocBlock(
                            block_type=BlockType.LIST,
                            list_items=items,
                            ordered=(tag == "ol"),
                        )
                    )
            elif tag == "table":
                rows: list[list[str]] = []
                for tr in child.find_all("tr"):
                    cells = tr.find_all(["th", "td"], recursive=False)
                    if cells:
                        row_vals = [" ".join(c.get_text().split()).strip() for c in cells]
                        rows.append(row_vals)
                if rows:
                    blocks.append(
                        DocBlock(
                            block_type=BlockType.TABLE,
                            table_rows=rows,
                        )
                    )
            elif tag == "hr":
                blocks.append(DocBlock(block_type=BlockType.HORIZONTAL_RULE))
            elif tag == "blockquote":
                spans = _extract_inline_spans(child, italic=True)
                if "".join(s.text for s in spans).strip():
                    blocks.append(
                        DocBlock(
                            block_type=BlockType.PARAGRAPH,
                            spans=spans,
                        )
                    )
            elif tag in ("div", "section", "article", "main", "header", "footer", "aside"):
                walk_container(child)
            else:
                spans = _extract_inline_spans(child)
                if "".join(s.text for s in spans).strip():
                    blocks.append(
                        DocBlock(
                            block_type=BlockType.PARAGRAPH,
                            spans=spans,
                        )
                    )

    walk_container(root)

    # Promote first H1 as document title if default title was used
    if title == default_title:
        for blk in blocks:
            if blk.block_type == BlockType.HEADING and blk.level == 1 and blk.plain_text:
                title = blk.plain_text
                break

    return IntermediateDocument(
        title=title,
        source_format=source_format,
        blocks=blocks,
    )


def parse_html_file(file_path: str) -> IntermediateDocument:
    """Reads an HTML file from disk and parses it into an IntermediateDocument."""
    path = Path(file_path)
    html_text = path.read_text(encoding="utf-8", errors="replace")
    return parse_html_string(
        html_text=html_text,
        default_title=path.stem,
        source_format=DocFormat.HTML,
    )
