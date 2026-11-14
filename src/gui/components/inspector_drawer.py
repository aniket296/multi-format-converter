"""Right-hand structural document inspector drawer for pre-flight and post-conversion DOM preview."""
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Optional
from src.core.conversion_router import parse_document
from src.gui.styles import (
    COLOR_BG_PANEL,
    COLOR_BG_SURFACE,
    COLOR_SLATE_HEADER,
    COLOR_TEXT_MAIN,
    FONT_MONO_SMALL,
)
from src.models import ConversionJob, IntermediateDocument


class InspectorDrawer(ttk.Frame):
    """Displays extracted IntermediateDocument metrics and structured block breakdown for a selected job."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, style="Surface.TFrame")
        self._title_var = tk.StringVar(value="No Document Selected")
        self._route_var = tk.StringVar(value="Select a row in the queue to inspect its Intermediate DOM.")
        self._headings_var = tk.StringVar(value="0")
        self._tables_var = tk.StringVar(value="0")
        self._words_var = tk.StringVar(value="0")
        self._status_badge_var = tk.StringVar(value="IDLE")

        self._build_ui()

    def _build_ui(self) -> None:
        # Header Bar
        header_bar = ttk.Frame(self, style="Surface.TFrame", padding=(12, 6))
        header_bar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(
            header_bar,
            text="STRUCTURAL DOCUMENT INSPECTOR (DOM)",
            style="SurfaceBold.TLabel",
        ).pack(side=tk.LEFT)

        self.lbl_status_badge = ttk.Label(
            header_bar,
            textvariable=self._status_badge_var,
            style="Muted.TLabel",
        )
        self.lbl_status_badge.pack(side=tk.RIGHT)

        # Metadata Card
        meta_frame = tk.Frame(self, bg=COLOR_BG_PANEL, padx=12, pady=10, highlightthickness=1, highlightbackground="#CBD5E1")
        meta_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(2, 8))

        tk.Label(
            meta_frame,
            textvariable=self._title_var,
            bg=COLOR_BG_PANEL,
            fg=COLOR_SLATE_HEADER,
            font=("Segoe UI", 11, "bold"),
            anchor=tk.W,
        ).pack(side=tk.TOP, fill=tk.X)

        tk.Label(
            meta_frame,
            textvariable=self._route_var,
            bg=COLOR_BG_PANEL,
            fg="#475569",
            font=("Segoe UI", 9),
            anchor=tk.W,
            wraplength=380,
            justify=tk.LEFT,
        ).pack(side=tk.TOP, fill=tk.X, pady=(2, 8))

        # 3 Structural Metric Badges Row
        badges_row = tk.Frame(meta_frame, bg=COLOR_BG_PANEL)
        badges_row.pack(side=tk.TOP, fill=tk.X)

        self._create_metric_badge(badges_row, "Headings", self._headings_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6)
        )
        self._create_metric_badge(badges_row, "Tables", self._tables_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6)
        )
        self._create_metric_badge(badges_row, "Words", self._words_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        # Monospace DOM Block Breakdown Viewer
        preview_container = ttk.Frame(self, style="Surface.TFrame", padding=(10, 0, 10, 10))
        preview_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.txt_preview = tk.Text(
            preview_container,
            font=FONT_MONO_SMALL,
            bg="#0F172A",
            fg="#F8FAFC",
            insertbackground="#F8FAFC",
            relief="flat",
            padx=12,
            pady=10,
            wrap=tk.WORD,
            state=tk.DISABLED,
        )
        vsb = ttk.Scrollbar(preview_container, orient=tk.VERTICAL, command=self.txt_preview.yview)
        self.txt_preview.configure(yscrollcommand=vsb.set)

        self.txt_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._set_preview_text(
            "Select any queued or converted document in the table to inspect its "
            "extracted IntermediateDocument DOM structure ([H1..H6], [PARAGRAPH], [LIST], [CODE], [TABLE])."
        )

    def _create_metric_badge(
        self,
        parent: tk.Misc,
        label_text: str,
        value_var: tk.StringVar,
    ) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=COLOR_BG_SURFACE,
            padx=8,
            pady=6,
            highlightthickness=1,
            highlightbackground="#CBD5E1",
        )
        tk.Label(
            card,
            textvariable=value_var,
            bg=COLOR_BG_SURFACE,
            fg="#1D4ED8",
            font=("Segoe UI", 12, "bold"),
        ).pack(side=tk.TOP)
        tk.Label(
            card,
            text=label_text.upper(),
            bg=COLOR_BG_SURFACE,
            fg="#64748B",
            font=("Segoe UI", 8, "bold"),
        ).pack(side=tk.TOP)
        return card

    def _set_preview_text(self, content: str) -> None:
        self.txt_preview.config(state=tk.NORMAL)
        self.txt_preview.delete("1.0", tk.END)
        self.txt_preview.insert("1.0", content)
        self.txt_preview.config(state=tk.DISABLED)

    def clear_inspector(self) -> None:
        """Resets inspector fields when no job is selected."""
        self._title_var.set("No Document Selected")
        self._route_var.set("Select a row in the queue to inspect its Intermediate DOM.")
        self._headings_var.set("0")
        self._tables_var.set("0")
        self._words_var.set("0")
        self._status_badge_var.set("IDLE")
        self._set_preview_text(
            "Select any queued or converted document in the table to inspect its "
            "extracted IntermediateDocument DOM structure."
        )

    def inspect_document_dom(
        self,
        doc: IntermediateDocument,
        job: Optional[ConversionJob] = None,
    ) -> None:
        """Directly populates the inspector from an already-parsed IntermediateDocument."""
        self._title_var.set(doc.title or "Untitled Document")
        self._headings_var.set(str(doc.heading_count))
        self._tables_var.set(str(doc.table_count))
        self._words_var.set(str(doc.word_count))

        if job:
            self._status_badge_var.set(job.status.value)
            src_name = Path(job.source_path).name
            tgt_display = Path(job.target_path).name if job.target_path else f"*.{job.target_format.value}"
            self._route_var.set(f"{src_name}  ->  {tgt_display}")
        else:
            fmt_str = doc.source_format.value.upper() if doc.source_format else "DOM"
            self._status_badge_var.set(fmt_str)
            self._route_var.set(f"Source Format: {fmt_str}")

        preview = doc.get_summary_preview(max_chars=3000)
        if job and job.error_message:
            preview = f"[JOB DIAGNOSTIC / NOTICE]\n{job.error_message}\n\n" + preview
        self._set_preview_text(preview)

    def inspect_job(self, job: Optional[ConversionJob]) -> Optional[IntermediateDocument]:
        """
        Parses and previews the selected ConversionJob's source file into the inspector drawer.

        Also updates the job's structural counts (headings, tables, words) if not yet populated.
        """
        if job is None:
            self.clear_inspector()
            return None

        self._status_badge_var.set(job.status.value)
        src_name = Path(job.source_path).name
        tgt_display = Path(job.target_path).name if job.target_path else f"{Path(job.source_path).stem}.{job.target_format.value}"
        self._route_var.set(f"{src_name}  ->  {tgt_display}")

        try:
            doc = parse_document(job.source_path, source_format=job.source_format)
            job.heading_count = doc.heading_count
            job.table_count = doc.table_count
            job.word_count = doc.word_count
            self.inspect_document_dom(doc, job=job)
            return doc
        except Exception as exc:
            self._title_var.set(src_name)
            self._headings_var.set("-")
            self._tables_var.set("-")
            self._words_var.set("-")
            err_msg = f"Failed to parse document preview:\n{exc}"
            if job.error_message:
                err_msg += f"\n\nJob Error: {job.error_message}"
            self._set_preview_text(err_msg)
            return None
