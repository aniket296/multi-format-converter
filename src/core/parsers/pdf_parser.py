"""PDF parser extracting structured headings, paragraphs, lists, and tables via PyMuPDF."""
import re
import statistics
from pathlib import Path
import fitz
from src.models.doc_format import DocFormat
from src.models.intermediate_dom import (
    BlockType,
    DocBlock,
    IntermediateDocument,
    TextSpan,
)

_PAGE_FOOTER_RE = re.compile(r"^Page\s+\d+\s+of\s+\d+$", re.IGNORECASE)
_BULLET_RE = re.compile(r"^(?:[•●▪◦\-*]|\d+[.)])\s+(.*)$")


def _rects_overlap(r1: tuple[float, float, float, float], r2: tuple[float, float, float, float]) -> bool:
    """Checks if two bounding boxes (x0, y0, x1, y1) overlap significantly."""
    x_left = max(r1[0], r2[0])
    y_top = max(r1[1], r2[1])
    x_right = min(r1[2], r2[2])
    y_bottom = min(r1[3], r2[3])
    if x_right <= x_left or y_bottom <= y_top:
        return False
    inter_area = (x_right - x_left) * (y_bottom - y_top)
    r1_area = max(1.0, (r1[2] - r1[0]) * (r1[3] - r1[1]))
    return (inter_area / r1_area) > 0.35


def parse_pdf_file(file_path: str) -> IntermediateDocument:
    """Parses a PDF file into a canonical IntermediateDocument using PyMuPDF."""
    path = Path(file_path)
    pdf_doc = fitz.open(str(path))

    title = path.stem
    meta = pdf_doc.metadata or {}
    if meta.get("title") and meta["title"].strip():
        title = meta["title"].strip()

    # Collect font sizes across all pages to determine baseline body font size
    all_font_sizes: list[float] = []
    for page in pdf_doc:
        text_dict = page.get_text("dict")
        for b in text_dict.get("blocks", []):
            if b.get("type") != 0:
                continue
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    txt = span.get("text", "").strip()
                    if txt:
                        all_font_sizes.append(float(span.get("size", 11.0)))

    median_size = statistics.median(all_font_sizes) if all_font_sizes else 11.0
    h1_threshold = max(16.0, median_size * 1.40)
    h2_threshold = max(13.5, median_size * 1.18)

    blocks: list[DocBlock] = []

    for page in pdf_doc:
        # 1. Find tables on the page and record their bounding boxes & y-positions
        page_items: list[tuple[float, DocBlock]] = []
        table_bboxes: list[tuple[float, float, float, float]] = []

        try:
            finder = page.find_tables()
            for tbl in finder.tables:
                bbox = tuple(tbl.bbox)
                extracted = tbl.extract()
                if extracted:
                    cleaned_rows: list[list[str]] = []
                    for r in extracted:
                        row_cells = [
                            " ".join(str(c or "").split()).strip() for c in r
                        ]
                        if any(row_cells):
                            cleaned_rows.append(row_cells)
                    if len(cleaned_rows) >= 1 and max((len(r) for r in cleaned_rows), default=0) >= 2:
                        table_bboxes.append(bbox)
                        page_items.append(
                            (
                                bbox[1],
                                DocBlock(
                                    block_type=BlockType.TABLE,
                                    table_rows=cleaned_rows,
                                ),
                            )
                        )
        except Exception:
            pass

        # 2. Extract text blocks outside table bounding boxes
        text_dict = page.get_text("dict")
        for b in text_dict.get("blocks", []):
            if b.get("type") != 0:
                continue
            b_bbox = tuple(b.get("bbox", (0, 0, 0, 0)))
            if any(_rects_overlap(b_bbox, tb) for tb in table_bboxes):
                continue

            lines = b.get("lines", [])
            if not lines:
                continue

            block_spans: list[TextSpan] = []
            max_line_size = 0.0
            line_texts: list[str] = []
            all_mono = True

            for line in lines:
                l_parts: list[str] = []
                for sp in line.get("spans", []):
                    raw_txt = sp.get("text", "")
                    if not raw_txt:
                        continue
                    l_parts.append(raw_txt)
                    sz = float(sp.get("size", median_size))
                    if sz > max_line_size:
                        max_line_size = sz
                    font_name = (sp.get("font") or "").lower()
                    flags = int(sp.get("flags", 0))
                    is_bold = bool(flags & 16) or "bold" in font_name
                    is_italic = bool(flags & 2) or "italic" in font_name or "oblique" in font_name
                    is_mono = any(m in font_name for m in ("courier", "consolas", "mono", "code"))
                    if raw_txt.strip() and not is_mono:
                        all_mono = False

                    block_spans.append(
                        TextSpan(
                            text=raw_txt,
                            bold=is_bold,
                            italic=is_italic,
                            code=is_mono,
                        )
                    )
                joined_line = "".join(l_parts).strip()
                if joined_line:
                    line_texts.append(joined_line)
                if block_spans and block_spans[-1].text and not block_spans[-1].text.endswith(" "):
                    block_spans[-1].text += " "

            combined_text = " ".join(line_texts).strip()
            if not combined_text or _PAGE_FOOTER_RE.match(combined_text):
                continue

            y_top = float(b_bbox[1])

            # Check if block is a heading
            if max_line_size >= h1_threshold and len(combined_text) < 180:
                if title == path.stem:
                    title = combined_text
                page_items.append(
                    (
                        y_top,
                        DocBlock(
                            block_type=BlockType.HEADING,
                            spans=[TextSpan(text=combined_text, bold=True)],
                            level=1,
                        ),
                    )
                )
            elif max_line_size >= h2_threshold and len(combined_text) < 180:
                page_items.append(
                    (
                        y_top,
                        DocBlock(
                            block_type=BlockType.HEADING,
                            spans=[TextSpan(text=combined_text, bold=True)],
                            level=2,
                        ),
                    )
                )
            elif all_mono and len(line_texts) >= 1:
                page_items.append(
                    (
                        y_top,
                        DocBlock(
                            block_type=BlockType.CODE_BLOCK,
                            code_text="\n".join(line_texts),
                        ),
                    )
                )
            elif all(_BULLET_RE.match(lt) for lt in line_texts):
                items = [_BULLET_RE.match(lt).group(1).strip() for lt in line_texts if _BULLET_RE.match(lt)]
                is_ordered = bool(re.match(r"^\d+[.)]", line_texts[0]))
                page_items.append(
                    (
                        y_top,
                        DocBlock(
                            block_type=BlockType.LIST,
                            list_items=items,
                            ordered=is_ordered,
                        ),
                    )
                )
            else:
                # Trim trailing space on last span
                if block_spans:
                    block_spans[-1].text = block_spans[-1].text.rstrip()
                page_items.append(
                    (
                        y_top,
                        DocBlock(
                            block_type=BlockType.PARAGRAPH,
                            spans=block_spans if block_spans else [TextSpan(text=combined_text)],
                        ),
                    )
                )

        # Sort page items top-to-bottom and merge consecutive single-item lists
        page_items.sort(key=lambda pair: pair[0])
        for _, blk in page_items:
            if (
                blk.block_type == BlockType.LIST
                and blocks
                and blocks[-1].block_type == BlockType.LIST
                and blocks[-1].ordered == blk.ordered
            ):
                blocks[-1].list_items.extend(blk.list_items)
            else:
                blocks.append(blk)

    pdf_doc.close()

    return IntermediateDocument(
        title=title,
        source_format=DocFormat.PDF,
        blocks=blocks,
    )
