"""Main High-DPI Desktop Studio shell and multithreaded batch controller."""
import ctypes
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional
from src.core.batch_worker import BatchConversionWorker, export_audit_csv
from src.gui.components.conversion_panel import ConversionPanel
from src.gui.components.ingest_toolbar import IngestToolbar, create_demo_sample_pack
from src.gui.components.inspector_drawer import InspectorDrawer
from src.gui.components.queue_table import QueueTable
from src.gui.styles import COLOR_SLATE_HEADER, apply_cobalt_slate_theme
from src.models import (
    BatchAuditSummary,
    ConversionJob,
    DocFormat,
    JobStatus,
)
from src.utils.file_scanner import scan_path_for_documents
from src.utils.logger import get_gui_log_queue, get_logger

logger = get_logger("gui.app")


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
        self.root.geometry("1360x840")
        self.root.minsize(1080, 700)

        self._job_counter = 0
        self._active_worker: Optional[BatchConversionWorker] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._last_summary: Optional[BatchAuditSummary] = None
        self._event_queue: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self._polling_after_id: Optional[str] = None

        self._configure_window_icon()
        self.style = apply_cobalt_slate_theme(self.root)
        self._build_shell()
        self._start_ui_polling()

    def _configure_window_icon(self) -> None:
        project_root = Path(__file__).resolve().parent.parent.parent
        icon_path = project_root / "assets" / "app_icon.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(default=str(icon_path))
            except Exception:
                pass

    def _build_shell(self) -> None:
        # 1. Dark Slate Studio Header Banner
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
            text="Offline 5x5 Canonical Intermediate DOM Engine  •  Markdown (.md)  |  Word (.docx)  |  PDF (.pdf)  |  RTF (.rtf)  |  HTML5 (.html)",
            style="HeaderSub.TLabel",
        ).pack(anchor=tk.W, pady=(2, 0))

        # 2. Top Action Ingest Toolbar
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

        sep_top = tk.Frame(self.root, height=1, bg="#CBD5E1")
        sep_top.pack(side=tk.TOP, fill=tk.X)

        # 3. Bottom Status Bar & Conversion Settings Panel
        self.status_var = tk.StringVar(
            value="Ready  •  Add files, a recursive folder, or click '+ Load Demo Sample Pack' to begin."
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

        sep_bottom = tk.Frame(self.root, height=1, bg="#CBD5E1")
        sep_bottom.pack(side=tk.BOTTOM, fill=tk.X)

        self.conversion_panel = ConversionPanel(
            self.root,
            on_target_format_changed=self._on_target_format_changed,
            on_start_batch=self._on_start_batch,
            on_cancel_batch=self._on_cancel_batch,
        )
        self.conversion_panel.pack(side=tk.BOTTOM, fill=tk.X)

        sep_mid = tk.Frame(self.root, height=1, bg="#CBD5E1")
        sep_mid.pack(side=tk.BOTTOM, fill=tk.X)

        # 4. Center Split PanedWindow: QueueTable (Left) + InspectorDrawer (Right)
        self.workspace_frame = ttk.Frame(self.root, padding=(12, 10))
        self.workspace_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.paned = ttk.PanedWindow(self.workspace_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        self.queue_table = QueueTable(
            self.paned,
            on_job_selected=self._on_job_selected,
            on_delete_pressed=self._on_delete_job_ids,
        )
        self.inspector_drawer = InspectorDrawer(self.paned)

        self.paned.add(self.queue_table, weight=3)
        self.paned.add(self.inspector_drawer, weight=2)

    def _next_job_id(self) -> str:
        self._job_counter += 1
        return f"JOB-{self._job_counter:04d}"

    def ingest_paths(
        self,
        paths: list[str],
        explicit_root_dir: Optional[str] = None,
    ) -> int:
        """Scans and adds files or directories into the batch queue."""
        allowed = self.ingest_toolbar.get_allowed_formats()
        target_fmt = self.conversion_panel.get_target_format()
        existing_sources = {j.source_path for j in self.queue_table.get_all_jobs()}
        added_count = 0

        for path in paths:
            scanned = scan_path_for_documents(path, allowed_formats=allowed)
            for abs_path, detected_root, doc_fmt in scanned:
                if abs_path in existing_sources:
                    continue
                root_dir = explicit_root_dir if explicit_root_dir is not None else detected_root
                try:
                    size_bytes = os.path.getsize(abs_path)
                except OSError:
                    size_bytes = 0

                job = ConversionJob(
                    job_id=self._next_job_id(),
                    source_path=abs_path,
                    root_ingest_dir=root_dir,
                    source_format=doc_fmt,
                    target_format=target_fmt,
                    source_size_bytes=size_bytes,
                )
                self.queue_table.add_or_update_job(job)
                existing_sources.add(abs_path)
                added_count += 1

        total = len(self.queue_table.get_all_jobs())
        self.conversion_panel.update_progress(0, total)
        if added_count > 0:
            self.status_var.set(
                f"Ingested {added_count} document(s) into queue ({total} total queued)."
            )
            # Automatically select and preview the first queued item if none selected
            if not self.queue_table.get_selected_job_ids():
                all_jobs = self.queue_table.get_all_jobs()
                if all_jobs:
                    first_id = all_jobs[0].job_id
                    self.queue_table.tree.selection_set(first_id)
        else:
            self.status_var.set("No new matching documents found for current source filter.")

        return added_count

    def _on_add_files(self, paths: list[str]) -> None:
        self.ingest_paths(paths)

    def _on_add_folder(self, folder: str) -> None:
        self.ingest_paths([folder], explicit_root_dir=str(Path(folder).resolve()))

    def _on_load_demo_pack(self) -> None:
        demo_root, _ = create_demo_sample_pack()
        out_dir = str(Path(demo_root) / "converted_output")
        self.conversion_panel.set_output_dir(out_dir)
        added = self.ingest_paths([demo_root], explicit_root_dir=demo_root)
        self.status_var.set(
            f"Loaded Demo Sample Pack ({added} files in nested folders). Output folder set to: {out_dir}"
        )

    def _on_remove_selected(self) -> None:
        sel = self.queue_table.get_selected_job_ids()
        if not sel:
            self.status_var.set("Select one or more rows in the queue table to remove.")
            return
        self._on_delete_job_ids(sel)

    def _on_delete_job_ids(self, job_ids: list[str]) -> None:
        self.queue_table.remove_jobs(job_ids)
        self.inspector_drawer.clear_inspector()
        total = len(self.queue_table.get_all_jobs())
        self.conversion_panel.update_progress(0, total)
        self.status_var.set(f"Removed {len(job_ids)} item(s) from queue ({total} remaining).")

    def _on_clear_queue(self) -> None:
        self.queue_table.clear_all()
        self.inspector_drawer.clear_inspector()
        self._last_summary = None
        self.conversion_panel.update_progress(0, 0)
        self.status_var.set("Cleared all items from batch queue.")

    def _on_filter_changed(self, allowed: Optional[set[DocFormat]]) -> None:
        if allowed is None:
            self.status_var.set("Source filter set to: All Formats")
        else:
            exts = ", ".join(f".{f.value}" for f in allowed)
            self.status_var.set(f"Source filter set to: {exts} (applies to next file/folder ingest)")

    def _on_target_format_changed(self, new_format: DocFormat) -> None:
        self.queue_table.update_target_format_for_queued(new_format)
        selected_job = self.queue_table.get_selected_job()
        if selected_job:
            self.inspector_drawer.inspect_job(selected_job)
        self.status_var.set(f"Target output format updated to {new_format.label} for queued jobs.")

    def _on_job_selected(self, job: Optional[ConversionJob]) -> None:
        if job is None:
            self.inspector_drawer.clear_inspector()
            return
        dom = self.inspector_drawer.inspect_job(job)
        if dom is not None:
            # Refresh row structure column with pre-flight counts
            self.queue_table.add_or_update_job(job)

    def _on_start_batch(self) -> None:
        jobs = self.queue_table.get_all_jobs()
        if not jobs:
            messagebox.showinfo(
                "Batch Queue Empty",
                "Please add documents, a folder, or load the Demo Sample Pack before starting.",
            )
            return

        if self._worker_thread and self._worker_thread.is_alive():
            return

        config = self.conversion_panel.get_conversion_config()
        if not config.output_dir:
            messagebox.showwarning("Output Folder Required", "Please specify an output destination folder.")
            return

        # Reset statuses of all queued/previous jobs for fresh batch execution
        for job in jobs:
            job.target_format = config.target_format
            job.status = JobStatus.QUEUED
            job.duration_ms = 0.0
            job.error_message = None
            self.queue_table.add_or_update_job(job)

        self.conversion_panel.set_running_state(True)
        self.conversion_panel.update_progress(0, len(jobs))
        self.status_var.set(
            f"Running batch conversion of {len(jobs)} document(s) to {config.target_format.value.upper()} "
            f"using {config.max_workers} worker thread(s)..."
        )

        self._active_worker = BatchConversionWorker(
            config=config,
            on_job_updated=lambda j: self._event_queue.put(("job_updated", j)),
            on_batch_completed=lambda s: self._event_queue.put(("batch_completed", s)),
        )

        self._worker_thread = threading.Thread(
            target=self._active_worker.run_batch,
            args=(jobs,),
            daemon=True,
        )
        self._worker_thread.start()

    def _on_cancel_batch(self) -> None:
        if self._active_worker:
            self._active_worker.cancel()
            self.status_var.set("Cancelling active batch conversion...")

    def _on_export_csv(self) -> None:
        jobs = self.queue_table.get_all_jobs()
        if not jobs and not self._last_summary:
            messagebox.showinfo(
                "No Audit Data",
                "Queue is empty. Run a batch conversion or add jobs before exporting an audit CSV.",
            )
            return

        summary = self._last_summary or BatchAuditSummary(
            total_jobs=len(jobs),
            completed=sum(1 for j in jobs if j.status == JobStatus.COMPLETED),
            skipped=sum(1 for j in jobs if j.status == JobStatus.SKIPPED),
            failed=sum(1 for j in jobs if j.status == JobStatus.FAILED),
            total_duration_ms=sum(j.duration_ms for j in jobs),
            jobs=jobs,
        )

        csv_path = filedialog.asksaveasfilename(
            title="Export Batch Audit Report CSV",
            defaultextension=".csv",
            initialfile="batch_conversion_audit.csv",
            filetypes=[("CSV Audit Report (*.csv)", "*.csv")],
        )
        if not csv_path:
            return

        try:
            export_audit_csv(summary, csv_path)
            self.status_var.set(f"Exported CSV audit report to: {csv_path}")
        except Exception as exc:
            messagebox.showerror("CSV Export Error", f"Failed to write CSV audit report:\n{exc}")

    def _start_ui_polling(self) -> None:
        """Polls the background worker event queue every 100ms for smooth, non-blocking UI updates."""
        self._drain_event_queue()
        try:
            if self.root.winfo_exists():
                self._polling_after_id = self.root.after(100, self._start_ui_polling)
        except tk.TclError:
            pass

    def _drain_event_queue(self) -> None:
        while True:
            try:
                event_type, payload = self._event_queue.get_nowait()
            except queue.Empty:
                break

            if event_type == "job_updated" and isinstance(payload, ConversionJob):
                self.queue_table.add_or_update_job(payload)
                all_jobs = self.queue_table.get_all_jobs()
                done_count = sum(
                    1
                    for j in all_jobs
                    if j.status in (JobStatus.COMPLETED, JobStatus.SKIPPED, JobStatus.FAILED)
                )
                self.conversion_panel.update_progress(done_count, len(all_jobs))

                sel = self.queue_table.get_selected_job()
                if sel and sel.job_id == payload.job_id:
                    self.inspector_drawer.inspect_job(payload)

            elif event_type == "batch_completed" and isinstance(payload, BatchAuditSummary):
                self._last_summary = payload
                self.conversion_panel.set_running_state(False)
                done_count = payload.completed + payload.skipped + payload.failed
                self.conversion_panel.update_progress(done_count, payload.total_jobs)
                self.status_var.set(
                    f"Batch Complete in {payload.total_duration_ms:.0f} ms  •  "
                    f"Completed: {payload.completed}  |  Skipped: {payload.skipped}  |  Failed: {payload.failed}"
                )

        # Also drain log queue so it doesn't accumulate unboundedly
        log_q = get_gui_log_queue()
        while not log_q.empty():
            try:
                log_q.get_nowait()
            except queue.Empty:
                break

    def run(self) -> None:
        """Starts the Tkinter main event loop."""
        self.root.mainloop()
