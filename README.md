# Multi-Format Document Batch Converter

<div align="center">

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Matrix](https://img.shields.io/badge/Conversion%20Matrix-5x5%20%2820%20Paths%29-1D4ED8?style=for-the-badge)
![Privacy](https://img.shields.io/badge/Architecture-100%25%20Offline%20DOM-10B981?style=for-the-badge)
![Packaging](https://img.shields.io/badge/Packaging-PyInstaller%20%2B%20Inno%20Setup-F59E0B?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-64748B?style=for-the-badge)

**An enterprise-grade, 100% offline Windows desktop studio for high-throughput batch document migration across Markdown (`.md`), Microsoft Word (`.docx`), Vector PDF (`.pdf`), Rich Text Format (`.rtf`), and HTML5 (`.html`).**

</div>

---

## Why This Exists (Real-World Impact)

Organizations, legal teams, engineering departments, and academic researchers routinely need to migrate hundreds or thousands of documents across formats—such as converting nested repositories of Markdown technical specs into formatted Word (`.docx`) or PDF deliverables, or archiving legacy `.rtf` and `.docx` contracts into clean Markdown and HTML5.

Most existing tools force a painful tradeoff:
1. **Cloud Conversion Portals** impose strict file-count/size limits, throttle bandwidth, and expose confidential legal, financial, or proprietary engineering documents to third-party servers.
2. **Brittle Point-to-Point Scripts** lose document structure (dropping tables, flattening headings, or corrupting inline code/bold runs) and flatten nested folder hierarchies into a single messy output folder.

**Multi-Format Document Batch Converter** solves both problems by running **100% offline** on your local machine using a canonical **Intermediate Document DOM (`IntermediateDocument`)**. Every input file is parsed into a strongly-typed structural tree and synthesized into any target format while mirroring your original sub-folder hierarchy and generating a compliance-ready CSV audit log.

---

## The 5×5 Universal Intermediate DOM Matrix (20 Conversion Paths)

Instead of maintaining 20 fragile point-to-point translators, the engine parses all 5 formats into `IntermediateDocument` and serializes to all 5 target formats:

| Source \ Target | **Markdown (`.md`)** | **Word (`.docx`)** | **Vector PDF (`.pdf`)** | **Rich Text (`.rtf`)** | **HTML5 (`.html`)** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Markdown (`.md`)** | *Skip (Identical)* | ✅ `MD -> DOCX` | ✅ `MD -> PDF` | ✅ `MD -> RTF` | ✅ `MD -> HTML` |
| **Word (`.docx`)** | ✅ `DOCX -> MD` | *Skip (Identical)* | ✅ `DOCX -> PDF` | ✅ `DOCX -> RTF` | ✅ `DOCX -> HTML` |
| **Vector PDF (`.pdf`)** | ✅ `PDF -> MD` | ✅ `PDF -> DOCX` | *Skip (Identical)* | ✅ `PDF -> RTF` | ✅ `PDF -> HTML` |
| **Rich Text (`.rtf`)** | ✅ `RTF -> MD` | ✅ `RTF -> DOCX` | ✅ `RTF -> PDF` | *Skip (Identical)* | ✅ `RTF -> HTML` |
| **HTML5 (`.html`)** | ✅ `HTML -> MD` | ✅ `HTML -> DOCX` | ✅ `HTML -> PDF` | ✅ `HTML -> RTF` | *Skip (Identical)* |

### Preserved Structural DOM Elements
* **Document Metadata & Title:** Extracted from document properties, `<title>`, or top-level `H1` headings.
* **Hierarchical Headings (`H1`–`H6`):** Mapped accurately across Markdown `#` headers, Word Heading styles, HTML `<h1..h6>`, scaled RTF typography, and PDF font-size tiers.
* **Paragraphs & Inline Runs (`TextSpan`):** Preserves **bold**, *italic*, and `inline code` spans.
* **Ordered & Unordered Lists:** Bullet (`•` / `-`) and numbered (`1.`) lists.
* **Fenced Code Blocks:** Monospace (`Consolas`) blocks with syntax-safe escaping.
* **2D Grid Tables:** Preserves multi-row/column tables across GFM pipe tables, Word `"Table Grid"`, HTML5 zebra tables, PyMuPDF vector tables, and native RTF `\trowd...\row` cells.

---

## Key Features

* **Multi-Threaded Batch Worker Pool (`ThreadPoolExecutor`):** Configurable concurrency (`1` to `16` worker threads) processes large document batches in parallel while keeping the High-DPI studio interface responsive at 60 FPS.
* **Recursive Sub-Folder Tree Mirroring:** Ingest an entire multi-level directory tree (e.g., `ingest/legal/2026/nda.docx`) and automatically mirror the exact relative folder hierarchy inside your chosen output folder (`output/legal/2026/nda.pdf`).
* **Mixed-Source Batch Ingestion & Extension Filtering:** Combine `.md`, `.docx`, `.pdf`, `.rtf`, and `.html` files in a single batch queue, or filter recursive folder scans to a specific source extension.
* **Pre-Flight & Post-Conversion Structural Inspector Drawer:** Click any queued or completed job to inspect its extracted `IntermediateDocument` DOM—including live counts of **Headings**, **Tables**, and **Words**, plus a block-by-block (`[H1]`, `[PARAGRAPH]`, `[LIST]`, `[CODE]`, `[TABLE RxC]`) diagnostic preview.
* **Deterministic File Collision Policies:** Choose between **Auto-Rename (`file_1.ext`)**, **Overwrite Existing**, or **Skip Existing** with thread-safe path reservation.
* **One-Click Demo Sample Pack:** Built-in `+ Load Demo Sample Pack` button generates sample `.md`, `.docx`, and `.html` documents in nested sub-folders so you can test the full pipeline immediately.
* **CSV Batch Audit Report Exporter:** Export a detailed UTF-8 CSV report containing `Job_ID`, `Source_Path`, `Source_Format`, `Target_Path`, `Target_Format`, `Status`, `Source_Bytes`, `Output_Bytes`, `Headings`, `Tables`, `Words`, `Duration_MS`, and `Error_Message`.

---

## Visual Architecture & Directory Tree

```text
multi-format-converter/
├── .gitignore
├── .env.example
├── README.md
├── pyproject.toml
├── requirements.txt
├── run_local.bat                   # One-click local virtual-env bootstrapper & launcher
├── build_windows.spec              # PyInstaller standalone Windows .exe specification
├── assets/
│   └── app_icon.ico                # Multi-resolution (16..256px) Cobalt-Slate studio icon
├── installer/
│   └── setup.iss                   # Inno Setup 6 Windows installer script
├── scripts/
│   ├── generate_icon.py            # Programmatic Pillow icon generator
│   ├── build_exe.bat               # Automated pytest + PyInstaller .exe build pipeline
│   └── build_installer.bat         # Automated Windows Setup.exe compiler with graceful fallback
├── src/
│   ├── main.py                     # High-DPI application entrypoint
│   ├── core/
│   │   ├── conversion_router.py    # 20-path universal dispatcher (parse_document / write_document)
│   │   ├── batch_worker.py         # ThreadPoolExecutor batch engine & CSV audit exporter
│   │   ├── parsers/                # 5 format parsers -> IntermediateDocument DOM
│   │   │   ├── html_parser.py
│   │   │   ├── md_parser.py
│   │   │   ├── docx_parser.py
│   │   │   ├── pdf_parser.py
│   │   │   └── rtf_parser.py
│   │   └── writers/                # 5 format writers <- IntermediateDocument DOM
│   │       ├── html_writer.py
│   │       ├── md_writer.py
│   │       ├── docx_writer.py
│   │       ├── pdf_writer.py
│   │       └── rtf_writer.py
│   ├── gui/
│   │   ├── app.py                  # Main High-DPI studio controller & event queue poller
│   │   ├── styles.py               # Corporate Cobalt-Slate TTK theme & typography
│   │   └── components/
│   │       ├── ingest_toolbar.py   # File/Folder ingest, extension filter & demo sample generator
│   │       ├── queue_table.py      # Multi-column live Treeview table
│   │       ├── conversion_panel.py # Target format, tree-mirror, collision & worker controls
│   │       └── inspector_drawer.py # Structural DOM metrics & block preview drawer
│   ├── models/
│   │   ├── doc_format.py           # DocFormat, CollisionPolicy, ConversionConfig
│   │   ├── intermediate_dom.py     # BlockType, TextSpan, DocBlock, IntermediateDocument
│   │   └── conversion_job.py       # JobStatus, ConversionJob, BatchAuditSummary
│   └── utils/
│       ├── config.py               # .env loader with typed defaults
│       ├── file_scanner.py         # Recursive scanner & tree-mirror path resolver
│       └── logger.py               # Rotating file logger & thread-safe GUI log queue
└── tests/
    ├── conftest.py                 # Canonical DOM & 5-format sample fixtures
    ├── test_parsers_to_dom.py      # Unit tests for all 5 format parsers
    ├── test_writers_matrix.py      # Unit tests for all 5 writers & 20 conversion paths
    └── test_batch_mirror_and_audit.py # Tree mirroring, collision policy & CSV audit tests
```

---

## Quickstart Guide (4 Options)

### Option 1: Windows Installer (`MultiFormatConverter_Setup.exe`)
1. Download `MultiFormatConverter_Setup.exe` from the repository's **Releases** page (or build it locally via Option 4).
2. Run the installer wizard to install **Multi-Format Document Batch Converter**, create Start Menu / Desktop shortcuts, and launch the studio—no Python installation required.

### Option 2: One-Click Local Source Launcher (`run_local.bat`)
Double-click `run_local.bat` or run it from Command Prompt / PowerShell:
```bat
.\run_local.bat
```
*Automatically creates `.venv` if missing, installs `requirements.txt`, generates `assets\app_icon.ico`, and launches the High-DPI desktop studio.*

### Option 3: Developer Terminal Setup
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .[dev]
python scripts/generate_icon.py
python -m src.main
```

### Option 4: Rebuilding the Standalone `.exe` & Windows Installer
To run the full test suite and compile the standalone portable executable (`dist\MultiFormatConverter.exe`):
```bat
scripts\build_exe.bat
```
To compile both the standalone `.exe` and the Inno Setup Windows installer (`dist_installer\MultiFormatConverter_Setup.exe`):
```bat
scripts\build_installer.bat
```

---

## Technology Stack

| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Desktop UI** | Python `tkinter` / `ttk` (`clam`) | High-DPI Windows 10/11 studio shell with Cobalt-Slate theme |
| **PDF Engine** | `PyMuPDF` (`fitz` / `Story`) | Vector PDF typesetting (`fitz.Story`) and table/text extraction |
| **Word Engine** | `python-docx` | Native `.docx` paragraph, run, heading, list, and `"Table Grid"` synthesis |
| **Markdown Engine** | `Markdown` | GFM table, fenced code, and list parsing |
| **HTML5 Engine** | `beautifulsoup4` | Semantic DOM traversal and responsive CSS HTML5 rendering |
| **RTF Engine** | `striprtf` + Native RTF 1.5 Writer | Standards-compliant RTF 1.5 synthesis (`\trowd`, Unicode escapes) & parsing |
| **Concurrency** | `concurrent.futures.ThreadPoolExecutor` | Non-blocking multi-threaded batch worker pool |
| **Packaging** | `PyInstaller` + `Inno Setup 6` | Standalone `MultiFormatConverter.exe` & Windows Setup Wizard |

---

## Automated Testing

Run the complete unit and integration test suite (covering all 5 parsers, all 5 writers, all 20 cross-format conversion paths, multi-hop chains, recursive directory mirroring, collision policies, and CSV audit export):

```powershell
.\.venv\Scripts\pytest.exe -v
```
