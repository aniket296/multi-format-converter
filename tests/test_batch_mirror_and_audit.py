"""Unit tests for BatchConversionWorker, recursive tree mirroring, collision policies, and CSV audit."""
import csv
from pathlib import Path
from src.core.batch_worker import BatchConversionWorker, export_audit_csv
from src.core.writers import write_docx_file, write_html_file, write_md_file
from src.models import (
    CollisionPolicy,
    ConversionConfig,
    ConversionJob,
    DocFormat,
    IntermediateDocument,
    JobStatus,
)
from src.utils.file_scanner import scan_path_for_documents


def test_batch_folder_tree_mirroring_and_csv_audit(
    tmp_path: Path,
    canonical_dom: IntermediateDocument,
) -> None:
    """Verifies nested folder structure mirroring in output directory and CSV audit generation."""
    ingest_root = tmp_path / "ingest_source"
    output_root = tmp_path / "batch_output"

    dept_legal = ingest_root / "legal" / "contracts"
    dept_eng = ingest_root / "engineering" / "specs"
    dept_legal.mkdir(parents=True)
    dept_eng.mkdir(parents=True)

    f_md = dept_legal / "nda_template.md"
    f_docx = dept_eng / "architecture.docx"
    f_html = ingest_root / "overview.html"

    write_md_file(canonical_dom, str(f_md))
    write_docx_file(canonical_dom, str(f_docx))
    write_html_file(canonical_dom, str(f_html))

    scanned = scan_path_for_documents(str(ingest_root))
    assert len(scanned) == 3

    jobs = [
        ConversionJob(
            job_id=f"JOB-{idx:03d}",
            source_path=src_path,
            root_ingest_dir=root_dir,
            source_format=fmt,
            target_format=DocFormat.PDF,
        )
        for idx, (src_path, root_dir, fmt) in enumerate(scanned, start=1)
    ]

    config = ConversionConfig(
        target_format=DocFormat.PDF,
        output_dir=str(output_root),
        preserve_folder_tree=True,
        collision_policy=CollisionPolicy.RENAME,
        max_workers=3,
    )

    updated_ids: list[str] = []
    worker = BatchConversionWorker(
        config=config,
        on_job_updated=lambda j: updated_ids.append(j.job_id),
    )
    summary = worker.run_batch(jobs)

    assert summary.total_jobs == 3
    assert summary.completed == 3
    assert summary.failed == 0
    assert summary.skipped == 0
    assert len(updated_ids) >= 3

    # Verify mirrored directory hierarchy in output_root
    assert (output_root / "legal" / "contracts" / "nda_template.pdf").exists()
    assert (output_root / "engineering" / "specs" / "architecture.pdf").exists()
    assert (output_root / "overview.pdf").exists()

    # Export and verify CSV audit report
    csv_path = tmp_path / "audit_report.csv"
    export_audit_csv(summary, str(csv_path))
    assert csv_path.exists()

    with csv_path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    assert {r["Status"] for r in rows} == {JobStatus.COMPLETED.value}
    assert all(int(r["Output_Bytes"]) > 0 for r in rows)
    assert all(int(r["Headings"]) >= 1 for r in rows)
    assert all(int(r["Tables"]) == 1 for r in rows)


def test_collision_policies_rename_and_skip(
    tmp_path: Path,
    canonical_dom: IntermediateDocument,
) -> None:
    """Verifies CollisionPolicy.RENAME (_1 suffix) and CollisionPolicy.SKIP behavior."""
    src_dir = tmp_path / "src"
    out_dir = tmp_path / "out"
    src_dir.mkdir()
    out_dir.mkdir()

    src_md = src_dir / "report.md"
    write_md_file(canonical_dom, str(src_md))

    # Pre-create existing report.html in out_dir
    existing_target = out_dir / "report.html"
    existing_target.write_text("<html><body>Existing</body></html>", encoding="utf-8")

    # 1. Test CollisionPolicy.SKIP
    skip_job = ConversionJob(
        job_id="JOB-SKIP",
        source_path=str(src_md),
        root_ingest_dir=str(src_dir),
        source_format=DocFormat.MD,
        target_format=DocFormat.HTML,
    )
    skip_cfg = ConversionConfig(
        target_format=DocFormat.HTML,
        output_dir=str(out_dir),
        preserve_folder_tree=True,
        collision_policy=CollisionPolicy.SKIP,
        max_workers=1,
    )
    skip_summary = BatchConversionWorker(skip_cfg).run_batch([skip_job])
    assert skip_summary.skipped == 1
    assert skip_job.status == JobStatus.SKIPPED

    # 2. Test CollisionPolicy.RENAME
    rename_job = ConversionJob(
        job_id="JOB-RENAME",
        source_path=str(src_md),
        root_ingest_dir=str(src_dir),
        source_format=DocFormat.MD,
        target_format=DocFormat.HTML,
    )
    rename_cfg = ConversionConfig(
        target_format=DocFormat.HTML,
        output_dir=str(out_dir),
        preserve_folder_tree=True,
        collision_policy=CollisionPolicy.RENAME,
        max_workers=1,
    )
    rename_summary = BatchConversionWorker(rename_cfg).run_batch([rename_job])
    assert rename_summary.completed == 1
    assert rename_job.status == JobStatus.COMPLETED
    assert rename_job.target_path is not None
    assert Path(rename_job.target_path).name == "report_1.html"
    assert Path(rename_job.target_path).exists()
