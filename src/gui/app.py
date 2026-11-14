"""Main High-DPI Desktop Studio shell for Multi-Format Document Batch Converter."""
import ctypes
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Optional
from src.gui.components.ingest_toolbar import IngestToolbar
from src.gui.styles import COLOR_SLATE_HEADER, apply_cobalt_slate_theme
from src.models import DocFormat


def enable_windows_high_dpi() -> None:
    """Enables per-monitor High-DPI awareness on Windows 10/11."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


class MultiFormatConverterApp:
    """Primary desktop application controller and studio window."""

    def __init__(self, root: Optional[tk.Tk] = None) -> None:
        enable_windows_high_dpi()
        self.root = root if root is not None else tk.Tk()
        self.root.title("Multi-Format Document Batch Converter — Universal Offline DOM Studio")
        self.root.geometry("1340x820")
        self.root.minsize(1060, 680)

        self._configure_window_icon()
        self.style = apply_cobalt_slate_theme(self.root)
        self._build_shell()

    def _configure_window_icon(self) -> None:
        project_root = Path(__file__).resolve().parent.parent.parent
        icon_path = project_root / "assets" / "app_icon.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(default=str(icon_path))
            except Exception:
                pass

    def _build_shell(self) -> None:
        # Dark Slate Studio Header Banner
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(18, 12))
        header.pack(side=tk.TOP, fill=tk.X)

        title_box = ttk.Frame(header, style="Header.TFrame")
        title_box.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(
            title_box,
            text="MULTI-FORMAT DOCUMENT BATCH CONVERTER",
            style="HeaderTitle.TLabel",
        ).pack(anchor=tk.W)

        ttk.Label(
            title_box,
            text="Offline 5x5 Canonical Intermediate DOM Engine  •  Markdown  |  Word (.docx)  |  PDF  |  RTF  |  HTML5",
            style="HeaderSub.TLabel",
        ).pack(anchor=tk.W, pady=(2, 0))

        # Top Action Ingest Toolbar
        self.ingest_toolbar = IngestToolbar(
            self.root,
            on_add_files=self._on_add_files,
            on_add_folder=self._on_add_folder,
            on_load_demo_pack=self._on_load_demo_pack,
            on_remove_selected=self._on_remove_selected,
            on_clear_queue=self._on_clear_queue,
            on_export_csv=self._on_export_csv,
            on_filter_changed=self._on_filter_changed,
        )
        self.ingest_toolbar.pack(side=tk.TOP, fill=tk.X)

        # Separator line
        sep = tk.Frame(self.root, height=1, bg="#CBD5E1")
        sep.pack(side=tk.TOP, fill=tk.X)

        # Main workspace container (populated in Sub-Phases 3.2 - 3.4)
        self.workspace_frame = ttk.Frame(self.root, padding=(12, 10))
        self.workspace_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Status Bar
        self.status_var = tk.StringVar(
            value="Ready  •  Add files or a folder to begin offline batch conversion."
        )
        status_bar = tk.Frame(self.root, bg=COLOR_SLATE_HEADER, padx=14, pady=6)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            status_bar,
            textvariable=self.status_var,
            bg=COLOR_SLATE_HEADER,
            fg="#E2E8F0",
            font=("Segoe UI", 9),
            anchor=tk.W,
        ).pack(side=tk.LEFT, fill=tk.X)

    def _on_add_files(self, paths: list[str]) -> None:
        self.status_var.set(f"Selected {len(paths)} file(s) for ingestion.")

    def _on_add_folder(self, folder: str) -> None:
        self.status_var.set(f"Selected folder: {folder}")

    def _on_load_demo_pack(self) -> None:
        self.status_var.set("Demo sample pack requested.")

    def _on_remove_selected(self) -> None:
        self.status_var.set("Remove selected requested.")

    def _on_clear_queue(self) -> None:
        self.status_var.set("Queue cleared.")

    def _on_export_csv(self) -> None:
        self.status_var.set("Export audit CSV requested.")

    def _on_filter_changed(self, allowed: Optional[set[DocFormat]]) -> None:
        if allowed is None:
            self.status_var.set("Source filter set to: All Formats")
        else:
            exts = ", ".join(f".{f.value}" for f in allowed)
            self.status_var.set(f"Source filter set to: {exts}")

    def run(self) -> None:
        """Starts the Tkinter main event loop."""
        self.root.mainloop()
