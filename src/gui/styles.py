"""Corporate Cobalt-Slate TTK theme and typography configuration."""
import tkinter as tk
from tkinter import ttk

# Color Palette Constants
COLOR_SLATE_HEADER = "#0F172A"
COLOR_SLATE_SUBHEADER = "#1E293B"
COLOR_COBALT_PRIMARY = "#1D4ED8"
COLOR_COBALT_HOVER = "#2563EB"
COLOR_BG_MAIN = "#F8FAFC"
COLOR_BG_SURFACE = "#FFFFFF"
COLOR_BG_PANEL = "#F1F5F9"
COLOR_TEXT_MAIN = "#1E293B"
COLOR_TEXT_MUTED = "#64748B"
COLOR_BORDER = "#CBD5E1"

# Status Colors
COLOR_EMERALD_OK = "#10B981"
COLOR_AMBER_WARN = "#F59E0B"
COLOR_ROSE_ERR = "#EF4444"
COLOR_BLUE_ACTIVE = "#3B82F6"

# Typography
FONT_UI = ("Segoe UI", 10)
FONT_UI_BOLD = ("Segoe UI", 10, "bold")
FONT_UI_SMALL = ("Segoe UI", 9)
FONT_HEADER_TITLE = ("Segoe UI", 14, "bold")
FONT_HEADER_SUB = ("Segoe UI", 9)
FONT_SECTION_TITLE = ("Segoe UI", 10, "bold")
FONT_MONO = ("Consolas", 10)
FONT_MONO_SMALL = ("Consolas", 9)


def apply_cobalt_slate_theme(root: tk.Misc) -> ttk.Style:
    """Applies the corporate Cobalt-Slate theme to a Tkinter root or Toplevel window."""
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    # Base widget configuration
    style.configure(
        ".",
        background=COLOR_BG_MAIN,
        foreground=COLOR_TEXT_MAIN,
        font=FONT_UI,
    )

    style.configure("TFrame", background=COLOR_BG_MAIN)
    style.configure("Surface.TFrame", background=COLOR_BG_SURFACE)
    style.configure("Panel.TFrame", background=COLOR_BG_PANEL)
    style.configure("Header.TFrame", background=COLOR_SLATE_HEADER)

    style.configure(
        "TLabel",
        background=COLOR_BG_MAIN,
        foreground=COLOR_TEXT_MAIN,
        font=FONT_UI,
    )
    style.configure(
        "Muted.TLabel",
        background=COLOR_BG_MAIN,
        foreground=COLOR_TEXT_MUTED,
        font=FONT_UI_SMALL,
    )
    style.configure(
        "Surface.TLabel",
        background=COLOR_BG_SURFACE,
        foreground=COLOR_TEXT_MAIN,
        font=FONT_UI,
    )
    style.configure(
        "SurfaceBold.TLabel",
        background=COLOR_BG_SURFACE,
        foreground=COLOR_TEXT_MAIN,
        font=FONT_UI_BOLD,
    )
    style.configure(
        "HeaderTitle.TLabel",
        background=COLOR_SLATE_HEADER,
        foreground="#FFFFFF",
        font=FONT_HEADER_TITLE,
    )
    style.configure(
        "HeaderSub.TLabel",
        background=COLOR_SLATE_HEADER,
        foreground="#94A3B8",
        font=FONT_HEADER_SUB,
    )
    style.configure(
        "Section.TLabel",
        background=COLOR_BG_MAIN,
        foreground=COLOR_SLATE_HEADER,
        font=FONT_SECTION_TITLE,
    )

    # Labelframes
    style.configure(
        "TLabelframe",
        background=COLOR_BG_SURFACE,
        bordercolor=COLOR_BORDER,
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "TLabelframe.Label",
        background=COLOR_BG_SURFACE,
        foreground=COLOR_SLATE_HEADER,
        font=FONT_SECTION_TITLE,
    )

    # Primary Cobalt Action Button
    style.configure(
        "Primary.TButton",
        background=COLOR_COBALT_PRIMARY,
        foreground="#FFFFFF",
        font=FONT_UI_BOLD,
        padding=(14, 7),
        borderwidth=0,
    )
    style.map(
        "Primary.TButton",
        background=[
            ("active", COLOR_COBALT_HOVER),
            ("disabled", "#94A3B8"),
        ],
        foreground=[("disabled", "#E2E8F0")],
    )

    # Standard Secondary Button
    style.configure(
        "Secondary.TButton",
        background="#E2E8F0",
        foreground=COLOR_SLATE_HEADER,
        font=FONT_UI,
        padding=(10, 6),
        borderwidth=1,
    )
    style.map(
        "Secondary.TButton",
        background=[
            ("active", "#CBD5E1"),
            ("disabled", "#F1F5F9"),
        ],
        foreground=[("disabled", "#94A3B8")],
    )

    # Danger / Cancel Button
    style.configure(
        "Danger.TButton",
        background=COLOR_ROSE_ERR,
        foreground="#FFFFFF",
        font=FONT_UI_BOLD,
        padding=(12, 7),
        borderwidth=0,
    )
    style.map(
        "Danger.TButton",
        background=[
            ("active", "#DC2626"),
            ("disabled", "#FCA5A5"),
        ],
        foreground=[("disabled", "#FFF1F2")],
    )

    # Treeview (Queue Table)
    style.configure(
        "Treeview",
        background=COLOR_BG_SURFACE,
        fieldbackground=COLOR_BG_SURFACE,
        foreground=COLOR_TEXT_MAIN,
        rowheight=28,
        font=FONT_UI,
        borderwidth=1,
    )
    style.configure(
        "Treeview.Heading",
        background=COLOR_SLATE_SUBHEADER,
        foreground="#FFFFFF",
        font=FONT_UI_BOLD,
        padding=(8, 6),
        relief="flat",
    )
    style.map(
        "Treeview.Heading",
        background=[("active", COLOR_SLATE_HEADER)],
    )
    style.map(
        "Treeview",
        background=[("selected", "#DBEAFE")],
        foreground=[("selected", COLOR_SLATE_HEADER)],
    )

    # Progressbar
    style.configure(
        "Cobalt.Horizontal.TProgressbar",
        troughcolor="#E2E8F0",
        background=COLOR_EMERALD_OK,
        bordercolor="#E2E8F0",
        lightcolor=COLOR_EMERALD_OK,
        darkcolor=COLOR_EMERALD_OK,
        thickness=16,
    )

    # Checkbutton & Radiobutton on white surface
    style.configure(
        "Surface.TCheckbutton",
        background=COLOR_BG_SURFACE,
        foreground=COLOR_TEXT_MAIN,
        font=FONT_UI,
    )
    style.configure(
        "Surface.TRadiobutton",
        background=COLOR_BG_SURFACE,
        foreground=COLOR_TEXT_MAIN,
        font=FONT_UI_BOLD,
    )

    return style
