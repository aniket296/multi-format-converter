"""Top action bar for batch file/folder ingestion, source filtering, and queue management."""
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Callable, Optional
from src.core.writers import write_docx_file, write_html_file, write_md_file
from src.models import (
    BlockType,
    DocBlock,
    DocFormat,
    IntermediateDocument,
    TextSpan,
)

FILTER_OPTIONS: list[tuple[str, Optional[set[DocFormat]]]] = [
    ("All Formats", None),
    ("Only .md", {DocFormat.MD}),
    ("Only .docx", {DocFormat.DOCX}),
    ("Only .pdf", {DocFormat.PDF}),
    ("Only .rtf", {DocFormat.RTF}),
    ("Only .html", {DocFormat.HTML}),
]


def create_demo_sample_pack(target_dir: Optional[str] = None) -> tuple[str, list[str]]:
    """
    Generates a ready-to-test Demo Sample Pack (.md, .docx, and .html) in a folder
    so users can immediately test cross-format batch conversion and tree mirroring.

    Returns (root_folder_path, list_of_created_file_paths).
    """
    base_dir = Path(target_dir) if target_dir else Path(tempfile.mkdtemp(prefix="mfc_demo_pack_"))
    sub_eng = base_dir / "engineering_specs"
    sub_exec = base_dir / "executive_briefs"
    sub_eng.mkdir(parents=True, exist_ok=True)
    sub_exec.mkdir(parents=True, exist_ok=True)

    dom_spec = IntermediateDocument(
        title="Platform Security & Batch Architecture",
        source_format=DocFormat.MD,
        blocks=[
            DocBlock(
                block_type=BlockType.HEADING,
                spans=[TextSpan(text="Platform Security & Batch Architecture", bold=True)],
                level=1,
            ),
            DocBlock(
                block_type=BlockType.PARAGRAPH,
                spans=[
                    TextSpan(text="This specification outlines the "),
                    TextSpan(text="100% offline Intermediate DOM", bold=True),
                    TextSpan(text=" document pipeline with "),
                    TextSpan(text="zero cloud telemetry", italic=True),
                    TextSpan(text=" and deterministic "),
                    TextSpan(text="ThreadPoolExecutor", code=True),
                    TextSpan(text=" worker concurrency."),
                ],
            ),
            DocBlock(
                block_type=BlockType.HEADING,
                spans=[TextSpan(text="Supported Conversion Matrix", bold=True)],
                level=2,
            ),
            DocBlock(
                block_type=BlockType.LIST,
                list_items=[
                    "Markdown (.md) <-> Word, PDF, RTF, HTML5",
                    "Microsoft Word (.docx) <-> Markdown, PDF, RTF, HTML5",
                    "Vector PDF (.pdf) & Rich Text (.rtf) bidirectional synthesis",
                ],
                ordered=False,
            ),
            DocBlock(
                block_type=BlockType.CODE_BLOCK,
                code_text="def batch_convert(files, target_format='pdf'):\n    return [ router.convert(f, target_format) for f in files ]",
            ),
            DocBlock(
                block_type=BlockType.TABLE,
                table_rows=[
                    ["Format", "Engine", "Fidelity", "Offline"],
                    ["Markdown", "Python-Markdown", "High", "Yes"],
                    ["Word DOCX", "python-docx", "High", "Yes"],
                    ["PDF", "PyMuPDF Story", "Vector", "Yes"],
                ],
            ),
        ],
    )

    md_path = sub_eng / "architecture_spec.md"
    docx_path = sub_exec / "quarterly_briefing.docx"
    html_path = base_dir / "release_notes.html"

    write_md_file(dom_spec, str(md_path))

    dom_docx = IntermediateDocument(
        title="Executive Quarterly Briefing",
        source_format=DocFormat.DOCX,
        blocks=[
            DocBlock(
                block_type=BlockType.HEADING,
                spans=[TextSpan(text="Executive Quarterly Briefing", bold=True)],
                level=1,
            ),
            DocBlock(
                block_type=BlockType.PARAGRAPH,
                spans=[
                    TextSpan(text="All departmental deliverables have been validated for "),
                    TextSpan(text="Q4 compliance", bold=True),
                    TextSpan(text=" across regional operations."),
                ],
            ),
            DocBlock(
                block_type=BlockType.TABLE,
                table_rows=[
                    ["Region", "Documents Processed", "Status"],
                    ["North America", "14,200", "Verified"],
                    ["Europe", "9,850", "Verified"],
                ],
            ),
        ],
    )
    write_docx_file(dom_docx, str(docx_path))

    dom_html = IntermediateDocument(
        title="Release Notes v1.0",
        source_format=DocFormat.HTML,
        blocks=[
            DocBlock(
                block_type=BlockType.HEADING,
                spans=[TextSpan(text="Release Notes v1.0", bold=True)],
                level=1,
            ),
            DocBlock(
                block_type=BlockType.PARAGRAPH,
                spans=[
                    TextSpan(text="Welcome to the "),
                    TextSpan(text="Multi-Format Document Batch Converter", bold=True),
                    TextSpan(text=" desktop studio for Windows 10/11."),
                ],
            ),
            DocBlock(
                block_type=BlockType.LIST,
                list_items=[
                    "Added 5x5 canonical Intermediate Document DOM",
                    "Added recursive sub-folder hierarchy mirroring",
                    "Added pre-flight structural inspector drawer",
                ],
                ordered=True,
            ),
        ],
    )
    write_html_file(dom_html, str(html_path))

    return str(base_dir), [str(md_path), str(docx_path), str(html_path)]


class IngestToolbar(ttk.Frame):
    """Top studio toolbar for file/folder ingestion, extension filtering, and queue actions."""

    def __init__(
        self,
        parent: tk.Misc,
        on_add_files: Callable[[list[str]], None],
        on_add_folder: Callable[[str], None],
        on_load_demo_pack: Callable[[], None],
        on_remove_selected: Callable[[], None],
        on_clear_queue: Callable[[], None],
        on_export_csv: Callable[[], None],
        on_filter_changed: Optional[Callable[[Optional[set[DocFormat]]], None]] = None,
    ) -> None:
        super().__init__(parent, style="Surface.TFrame", padding=(12, 8))
        self.on_add_files = on_add_files
        self.on_add_folder = on_add_folder
        self.on_load_demo_pack = on_load_demo_pack
        self.on_remove_selected = on_remove_selected
        self.on_clear_queue = on_clear_queue
        self.on_export_csv = on_export_csv
        self.on_filter_changed = on_filter_changed

        self._filter_var = tk.StringVar(value=FILTER_OPTIONS[0][0])
        self._build_ui()

    def _build_ui(self) -> None:
        # Left Group: Ingest Actions
        ingest_frame = ttk.Frame(self, style="Surface.TFrame")
        ingest_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.btn_add_files = ttk.Button(
            ingest_frame,
            text="+ Add Files...",
            style="Primary.TButton",
            command=self._handle_add_files,
        )
        self.btn_add_files.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_add_folder = ttk.Button(
            ingest_frame,
            text="+ Add Folder (Recursive)...",
            style="Primary.TButton",
            command=self._handle_add_folder,
        )
        self.btn_add_folder.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_demo_pack = ttk.Button(
            ingest_frame,
            text="+ Load Demo Sample Pack",
            style="Secondary.TButton",
            command=self.on_load_demo_pack,
        )
        self.btn_demo_pack.pack(side=tk.LEFT, padx=(0, 14))

        # Center Group: Source Extension Filter
        filter_frame = ttk.Frame(self, style="Surface.TFrame")
        filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(4, 14))

        ttk.Label(
            filter_frame,
            text="Source Filter:",
            style="SurfaceBold.TLabel",
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.cmb_filter = ttk.Combobox(
            filter_frame,
            textvariable=self._filter_var,
            values=[opt[0] for opt in FILTER_OPTIONS],
            state="readonly",
            width=15,
        )
        self.cmb_filter.pack(side=tk.LEFT)
        self.cmb_filter.bind("<<ComboboxSelected>>", self._handle_filter_change)

        # Right Group: Queue Management
        queue_frame = ttk.Frame(self, style="Surface.TFrame")
        queue_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.btn_remove = ttk.Button(
            queue_frame,
            text="Remove Selected",
            style="Secondary.TButton",
            command=self.on_remove_selected,
        )
        self.btn_remove.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_clear = ttk.Button(
            queue_frame,
            text="Clear Queue",
            style="Secondary.TButton",
            command=self.on_clear_queue,
        )
        self.btn_clear.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_export_csv = ttk.Button(
            queue_frame,
            text="Export Audit CSV...",
            style="Secondary.TButton",
            command=self.on_export_csv,
        )
        self.btn_export_csv.pack(side=tk.LEFT)

    def get_allowed_formats(self) -> Optional[set[DocFormat]]:
        """Returns the currently selected set of allowed DocFormats, or None for All Formats."""
        current = self._filter_var.get()
        for label, fmt_set in FILTER_OPTIONS:
            if label == current:
                return fmt_set
        return None

    def _handle_filter_change(self, _event: object = None) -> None:
        if self.on_filter_changed:
            self.on_filter_changed(self.get_allowed_formats())

    def _handle_add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select Documents to Convert",
            filetypes=[
                ("All Supported Documents", "*.md *.markdown *.docx *.pdf *.rtf *.html *.htm"),
                ("Markdown Files (*.md)", "*.md *.markdown"),
                ("Microsoft Word (*.docx)", "*.docx"),
                ("PDF Documents (*.pdf)", "*.pdf"),
                ("Rich Text Format (*.rtf)", "*.rtf"),
                ("HTML Documents (*.html)", "*.html *.htm"),
            ],
        )
        if paths:
            self.on_add_files(list(paths))

    def _handle_add_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select Root Folder for Recursive Batch Ingestion")
        if folder:
            self.on_add_folder(folder)
