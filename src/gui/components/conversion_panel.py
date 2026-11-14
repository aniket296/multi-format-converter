"""Bottom conversion settings and batch execution control panel."""
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional
from src.models import CollisionPolicy, ConversionConfig, DocFormat
from src.utils.config import (
    get_default_collision_policy,
    get_default_target_format,
    get_max_worker_threads,
)

COLLISION_POLICY_LABELS: list[tuple[str, CollisionPolicy]] = [
    ("Auto-Rename (file_1.ext)", CollisionPolicy.RENAME),
    ("Overwrite Existing", CollisionPolicy.OVERWRITE),
    ("Skip Existing", CollisionPolicy.SKIP),
]

TARGET_FORMAT_OPTIONS: list[tuple[str, DocFormat]] = [
    ("PDF (.pdf)", DocFormat.PDF),
    ("Word (.docx)", DocFormat.DOCX),
    ("Markdown (.md)", DocFormat.MD),
    ("HTML5 (.html)", DocFormat.HTML),
    ("Rich Text (.rtf)", DocFormat.RTF),
]


class ConversionPanel(ttk.Frame):
    """Control panel for target format, output folder, tree mirroring, collision rules, and execution."""

    def __init__(
        self,
        parent: tk.Misc,
        on_target_format_changed: Callable[[DocFormat], None],
        on_start_batch: Callable[[], None],
        on_cancel_batch: Callable[[], None],
        default_output_dir: Optional[str] = None,
    ) -> None:
        super().__init__(parent, style="Surface.TFrame", padding=(14, 10))
        self.on_target_format_changed = on_target_format_changed
        self.on_start_batch = on_start_batch
        self.on_cancel_batch = on_cancel_batch

        default_fmt = get_default_target_format()
        self._target_fmt_var = tk.StringVar(value=default_fmt.value)

        initial_out = default_output_dir or str((Path.cwd() / "converted_output").resolve())
        self._output_dir_var = tk.StringVar(value=initial_out)

        self._preserve_tree_var = tk.BooleanVar(value=True)

        default_pol = get_default_collision_policy()
        default_pol_label = next(
            (lbl for lbl, pol in COLLISION_POLICY_LABELS if pol == default_pol),
            COLLISION_POLICY_LABELS[0][0],
        )
        self._collision_var = tk.StringVar(value=default_pol_label)
        self._workers_var = tk.IntVar(value=get_max_worker_threads())
        self._progress_var = tk.DoubleVar(value=0.0)
        self._counter_var = tk.StringVar(value="0 / 0 completed")

        self._build_ui()

    def _build_ui(self) -> None:
        # Row 1: Target Format Radio Selector + Directory & Collision Rules
        top_row = ttk.Frame(self, style="Surface.TFrame")
        top_row.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))

        # Target Format Labelframe
        fmt_group = ttk.LabelFrame(top_row, text=" 1. Target Output Format ", padding=(12, 6))
        fmt_group.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        for label, doc_fmt in TARGET_FORMAT_OPTIONS:
            rb = ttk.Radiobutton(
                fmt_group,
                text=label,
                value=doc_fmt.value,
                variable=self._target_fmt_var,
                style="Surface.TRadiobutton",
                command=self._handle_format_change,
            )
            rb.pack(side=tk.LEFT, padx=(0, 12))

        # Directory & Collision Rules Labelframe
        rules_group = ttk.LabelFrame(
            top_row,
            text=" 2. Directory Mirroring, Collision Policy & Concurrency ",
            padding=(12, 6),
        )
        rules_group.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chk_preserve_tree = ttk.Checkbutton(
            rules_group,
            text="Preserve Sub-Folder Hierarchy in Output",
            variable=self._preserve_tree_var,
            style="Surface.TCheckbutton",
        )
        self.chk_preserve_tree.pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(rules_group, text="Collision Policy:", style="SurfaceBold.TLabel").pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self.cmb_collision = ttk.Combobox(
            rules_group,
            textvariable=self._collision_var,
            values=[lbl for lbl, _ in COLLISION_POLICY_LABELS],
            state="readonly",
            width=22,
        )
        self.cmb_collision.pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(rules_group, text="Worker Threads:", style="SurfaceBold.TLabel").pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self.spn_workers = ttk.Spinbox(
            rules_group,
            from_=1,
            to=16,
            textvariable=self._workers_var,
            width=5,
        )
        self.spn_workers.pack(side=tk.LEFT)

        # Row 2: Output Destination + Execution Controls
        bottom_row = ttk.Frame(self, style="Surface.TFrame")
        bottom_row.pack(side=tk.TOP, fill=tk.X)

        # Output Folder Picker
        dest_frame = ttk.Frame(bottom_row, style="Surface.TFrame")
        dest_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 16))

        ttk.Label(dest_frame, text="Output Folder:", style="SurfaceBold.TLabel").pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self.ent_output_dir = ttk.Entry(dest_frame, textvariable=self._output_dir_var)
        self.ent_output_dir.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.btn_browse = ttk.Button(
            dest_frame,
            text="Browse...",
            style="Secondary.TButton",
            command=self._handle_browse_output,
        )
        self.btn_browse.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_open_folder = ttk.Button(
            dest_frame,
            text="Open Output Folder",
            style="Secondary.TButton",
            command=self._handle_open_output_folder,
        )
        self.btn_open_folder.pack(side=tk.LEFT)

        # Execution Progress & Action Buttons
        exec_frame = ttk.Frame(bottom_row, style="Surface.TFrame")
        exec_frame.pack(side=tk.RIGHT)

        self.lbl_counter = ttk.Label(
            exec_frame,
            textvariable=self._counter_var,
            style="SurfaceBold.TLabel",
        )
        self.lbl_counter.pack(side=tk.LEFT, padx=(0, 10))

        self.progress_bar = ttk.Progressbar(
            exec_frame,
            variable=self._progress_var,
            maximum=100.0,
            length=170,
            mode="determinate",
            style="Cobalt.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(side=tk.LEFT, padx=(0, 12))

        self.btn_start = ttk.Button(
            exec_frame,
            text="🚀 Start Batch Conversion",
            style="Primary.TButton",
            command=self.on_start_batch,
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_cancel = ttk.Button(
            exec_frame,
            text="⏹ Cancel",
            style="Danger.TButton",
            command=self.on_cancel_batch,
            state=tk.DISABLED,
        )
        self.btn_cancel.pack(side=tk.LEFT)

    def get_target_format(self) -> DocFormat:
        """Returns the currently selected target DocFormat."""
        raw = self._target_fmt_var.get()
        fmt = DocFormat.from_extension(raw)
        return fmt if fmt is not None else DocFormat.PDF

    def get_collision_policy(self) -> CollisionPolicy:
        """Returns the currently selected CollisionPolicy."""
        selected_lbl = self._collision_var.get()
        for lbl, pol in COLLISION_POLICY_LABELS:
            if lbl == selected_lbl:
                return pol
        return CollisionPolicy.RENAME

    def get_conversion_config(self) -> ConversionConfig:
        """Builds a strongly-typed ConversionConfig snapshot from the current UI controls."""
        try:
            workers = max(1, min(16, int(self._workers_var.get())))
        except (ValueError, tk.TclError):
            workers = 4

        return ConversionConfig(
            target_format=self.get_target_format(),
            output_dir=self._output_dir_var.get().strip(),
            preserve_folder_tree=bool(self._preserve_tree_var.get()),
            collision_policy=self.get_collision_policy(),
            max_workers=workers,
        )

    def set_output_dir(self, path: str) -> None:
        """Sets the output destination directory path."""
        self._output_dir_var.set(path)

    def update_progress(self, completed_or_done: int, total: int) -> None:
        """Updates the batch progress bar and completion counter."""
        self._counter_var.set(f"{completed_or_done} / {total} completed")
        if total > 0:
            pct = min(100.0, (completed_or_done / total) * 100.0)
            self._progress_var.set(pct)
        else:
            self._progress_var.set(0.0)

    def set_running_state(self, is_running: bool) -> None:
        """Enables or disables start/cancel buttons during batch processing."""
        if is_running:
            self.btn_start.config(state=tk.DISABLED)
            self.btn_cancel.config(state=tk.NORMAL)
        else:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_cancel.config(state=tk.DISABLED)

    def _handle_format_change(self) -> None:
        self.on_target_format_changed(self.get_target_format())

    def _handle_browse_output(self) -> None:
        chosen = filedialog.askdirectory(
            title="Select Destination Folder for Converted Documents",
            initialdir=self._output_dir_var.get() or str(Path.cwd()),
        )
        if chosen:
            self._output_dir_var.set(chosen)

    def _handle_open_output_folder(self) -> None:
        out_dir = Path(self._output_dir_var.get().strip())
        try:
            os.makedirs(out_dir, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(str(out_dir))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(out_dir)])
            else:
                subprocess.Popen(["xdg-open", str(out_dir)])
        except Exception as exc:
            messagebox.showerror("Open Folder Error", f"Could not open output folder:\n{exc}")
