"""Multi-column scrollable batch queue table with live row updates and status color tags."""
import os
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, Optional
from src.gui.styles import (
    COLOR_AMBER_WARN,
    COLOR_BLUE_ACTIVE,
    COLOR_EMERALD_OK,
    COLOR_ROSE_ERR,
    COLOR_TEXT_MAIN,
)
from src.models import ConversionJob, DocFormat, JobStatus


class QueueTable(ttk.Frame):
    """Scrollable Treeview table displaying queued and active ConversionJobs."""

    COLUMNS = (
        "file_name",
        "relative_folder",
        "from_fmt",
        "to_fmt",
        "source_size",
        "structure",
        "status",
        "time_ms",
    )

    def __init__(
        self,
        parent: tk.Misc,
        on_job_selected: Optional[Callable[[Optional[ConversionJob]], None]] = None,
        on_delete_pressed: Optional[Callable[[list[str]], None]] = None,
    ) -> None:
        super().__init__(parent, style="Surface.TFrame")
        self.on_job_selected = on_job_selected
        self.on_delete_pressed = on_delete_pressed
        self._jobs_by_id: dict[str, ConversionJob] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        # Header bar above table
        header_bar = ttk.Frame(self, style="Surface.TFrame", padding=(10, 6))
        header_bar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(
            header_bar,
            text="BATCH CONVERSION QUEUE",
            style="SurfaceBold.TLabel",
        ).pack(side=tk.LEFT)

        self.lbl_count = ttk.Label(
            header_bar,
            text="0 documents queued",
            style="Muted.TLabel",
        )
        self.lbl_count.pack(side=tk.RIGHT)

        # Treeview + Scrollbars container
        table_container = ttk.Frame(self, style="Surface.TFrame")
        table_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            table_container,
            columns=self.COLUMNS,
            show="headings",
            selectmode="extended",
        )

        vsb = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_container.rowconfigure(0, weight=1)
        table_container.columnconfigure(0, weight=1)

        # Configure headings & widths
        headings = {
            "file_name": ("File Name", 210, tk.W),
            "relative_folder": ("Relative Folder", 160, tk.W),
            "from_fmt": ("From", 65, tk.CENTER),
            "to_fmt": ("To", 65, tk.CENTER),
            "source_size": ("Source Size", 95, tk.E),
            "structure": ("Structure", 145, tk.CENTER),
            "status": ("Status", 105, tk.CENTER),
            "time_ms": ("Time (ms)", 85, tk.E),
        }
        for col_id, (title, width, anchor) in headings.items():
            self.tree.heading(col_id, text=title, anchor=anchor)
            self.tree.column(col_id, width=width, minwidth=55, anchor=anchor, stretch=(col_id in ("file_name", "relative_folder")))

        # Configure status row color tags
        self.tree.tag_configure(JobStatus.QUEUED.value, foreground=COLOR_TEXT_MAIN)
        self.tree.tag_configure(JobStatus.PROCESSING.value, foreground=COLOR_BLUE_ACTIVE)
        self.tree.tag_configure(JobStatus.COMPLETED.value, foreground=COLOR_EMERALD_OK)
        self.tree.tag_configure(JobStatus.SKIPPED.value, foreground=COLOR_AMBER_WARN)
        self.tree.tag_configure(JobStatus.FAILED.value, foreground=COLOR_ROSE_ERR)

        # Bindings
        self.tree.bind("<<TreeviewSelect>>", self._handle_select)
        self.tree.bind("<Delete>", self._handle_delete_key)

    @staticmethod
    def _format_row_values(job: ConversionJob) -> tuple[str, ...]:
        src_path = Path(job.source_path)
        file_name = src_path.name

        rel_folder = "."
        if job.root_ingest_dir:
            try:
                rel_p = src_path.parent.relative_to(Path(job.root_ingest_dir))
                rel_folder = str(rel_p) if str(rel_p) != "." else "(root)"
            except ValueError:
                rel_folder = str(src_path.parent.name or ".")
        else:
            rel_folder = str(src_path.parent.name or ".")

        size_bytes = job.source_size_bytes
        if size_bytes <= 0 and src_path.exists():
            try:
                size_bytes = os.path.getsize(src_path)
                job.source_size_bytes = size_bytes
            except OSError:
                pass
        size_kb = f"{max(0.1, size_bytes / 1024.0):.1f} KB" if size_bytes > 0 else "0.0 KB"

        if job.word_count > 0 or job.heading_count > 0 or job.table_count > 0:
            structure_str = f"H: {job.heading_count} | T: {job.table_count} | W: {job.word_count}"
        else:
            structure_str = "H: - | T: - | W: -"

        time_str = f"{job.duration_ms:.1f}" if job.duration_ms > 0 else "-"

        return (
            file_name,
            rel_folder,
            job.source_format.value.upper(),
            f"-> {job.target_format.value.upper()}",
            size_kb,
            structure_str,
            job.status.value,
            time_str,
        )

    def add_or_update_job(self, job: ConversionJob) -> None:
        """Inserts a new job row or updates an existing job row in-place without flicker."""
        self._jobs_by_id[job.job_id] = job
        values = self._format_row_values(job)
        tag = job.status.value

        if self.tree.exists(job.job_id):
            self.tree.item(job.job_id, values=values, tags=(tag,))
        else:
            self.tree.insert("", tk.END, iid=job.job_id, values=values, tags=(tag,))

        self._refresh_count_label()

    def update_target_format_for_queued(self, target_format: DocFormat) -> None:
        """Updates the target format badge across all non-running jobs in the queue."""
        for job_id, job in self._jobs_by_id.items():
            if job.status != JobStatus.PROCESSING:
                job.target_format = target_format
                if job.status != JobStatus.QUEUED:
                    job.status = JobStatus.QUEUED
                    job.error_message = None
                if self.tree.exists(job_id):
                    self.tree.item(
                        job_id,
                        values=self._format_row_values(job),
                        tags=(job.status.value,),
                    )

    def get_selected_job_ids(self) -> list[str]:
        """Returns the list of currently selected job IDs."""
        return list(self.tree.selection())

    def get_selected_job(self) -> Optional[ConversionJob]:
        """Returns the primary selected ConversionJob, or None."""
        sel = self.tree.selection()
        if not sel:
            return None
        return self._jobs_by_id.get(sel[0])

    def remove_jobs(self, job_ids: list[str]) -> None:
        """Removes the specified job IDs from the table."""
        for jid in job_ids:
            self._jobs_by_id.pop(jid, None)
            if self.tree.exists(jid):
                self.tree.delete(jid)
        self._refresh_count_label()

    def clear_all(self) -> None:
        """Clears all jobs from the queue table."""
        self._jobs_by_id.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._refresh_count_label()

    def get_all_jobs(self) -> list[ConversionJob]:
        """Returns all jobs in visual table order."""
        return [
            self._jobs_by_id[iid]
            for iid in self.tree.get_children()
            if iid in self._jobs_by_id
        ]

    def _refresh_count_label(self) -> None:
        n = len(self._jobs_by_id)
        self.lbl_count.config(text=f"{n} document{'s' if n != 1 else ''} queued")

    def _handle_select(self, _event: object = None) -> None:
        if self.on_job_selected:
            self.on_job_selected(self.get_selected_job())

    def _handle_delete_key(self, _event: object = None) -> None:
        sel = self.get_selected_job_ids()
        if sel and self.on_delete_pressed:
            self.on_delete_pressed(sel)
