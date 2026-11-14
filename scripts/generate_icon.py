"""Programmatic icon generator for Multi-Format Document Batch Converter."""
import os
from pathlib import Path
from PIL import Image, ImageDraw


def draw_icon_base(size: int = 256) -> Image.Image:
    """Draws a Cobalt-Blue (#1D4ED8) and Slate (#0F172A) dual-document conversion badge."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer rounded badge background in Dark Slate (#0F172A)
    margin = int(size * 0.04)
    radius = int(size * 0.22)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill="#0F172A",
        outline="#3B82F6",
        width=max(2, int(size * 0.025)),
    )

    # Back document sheet (Slate/Light Blue tint)
    doc1_l = int(size * 0.20)
    doc1_t = int(size * 0.16)
    doc1_r = int(size * 0.62)
    doc1_b = int(size * 0.68)
    draw.rounded_rectangle(
        [doc1_l, doc1_t, doc1_r, doc1_b],
        radius=int(size * 0.05),
        fill="#94A3B8",
        outline="#E2E8F0",
        width=max(1, int(size * 0.015)),
    )
    # Horizontal lines on back document
    for idx in range(3):
        y = doc1_t + int(size * (0.14 + idx * 0.11))
        draw.line(
            [(doc1_l + int(size * 0.08), y), (doc1_r - int(size * 0.08), y)],
            fill="#1E293B",
            width=max(1, int(size * 0.028)),
        )

    # Front document sheet in Cobalt Blue (#1D4ED8)
    doc2_l = int(size * 0.38)
    doc2_t = int(size * 0.32)
    doc2_r = int(size * 0.82)
    doc2_b = int(size * 0.84)
    draw.rounded_rectangle(
        [doc2_l, doc2_t, doc2_r, doc2_b],
        radius=int(size * 0.05),
        fill="#1D4ED8",
        outline="#93C5FD",
        width=max(1, int(size * 0.018)),
    )

    # Lines inside front document
    for idx in range(3):
        y = doc2_t + int(size * (0.13 + idx * 0.10))
        draw.line(
            [(doc2_l + int(size * 0.08), y), (doc2_r - int(size * 0.08), y)],
            fill="#F8FAFC",
            width=max(1, int(size * 0.03)),
        )

    # Conversion arrow badge in Emerald (#10B981) at bottom-left/center overlap
    badge_cx = int(size * 0.34)
    badge_cy = int(size * 0.68)
    badge_r = int(size * 0.15)
    draw.ellipse(
        [badge_cx - badge_r, badge_cy - badge_r, badge_cx + badge_r, badge_cy + badge_r],
        fill="#10B981",
        outline="#0F172A",
        width=max(1, int(size * 0.02)),
    )

    # Rightward conversion arrow inside badge
    arrow_w = int(badge_r * 0.55)
    arrow_h = int(badge_r * 0.45)
    draw.line(
        [(badge_cx - arrow_w, badge_cy), (badge_cx + arrow_w * 0.5, badge_cy)],
        fill="#FFFFFF",
        width=max(1, int(size * 0.035)),
    )
    draw.polygon(
        [
            (badge_cx + arrow_w * 0.85, badge_cy),
            (badge_cx + arrow_w * 0.1, badge_cy - arrow_h),
            (badge_cx + arrow_w * 0.1, badge_cy + arrow_h),
        ],
        fill="#FFFFFF",
    )

    return img


def generate_app_icon(output_path: str | Path | None = None) -> Path:
    """Generates a multi-resolution .ico file at assets/app_icon.ico."""
    project_root = Path(__file__).resolve().parent.parent
    target = Path(output_path) if output_path else project_root / "assets" / "app_icon.ico"
    os.makedirs(target.parent, exist_ok=True)

    base_img = draw_icon_base(256)
    resolutions = [(16, 16), (32, 32), (48, 48), (256, 256)]
    base_img.save(target, format="ICO", sizes=resolutions)
    return target


if __name__ == "__main__":
    out = generate_app_icon()
    print(f"Generated multi-resolution icon at: {out} ({out.stat().st_size} bytes)")
