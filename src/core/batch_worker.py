"""Multi-threaded batch conversion worker pool and CSV audit exporter."""
import csv
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional
from src.core.conversion_router import convert_single_file
from src.models.conversion_job import BatchAuditSummary, ConversionJob, JobStatus
from src.models.doc_format import CollisionPolicy, ConversionConfig
from src.utils.file_scanner import resolve_output_path
from src.utils.logger import get_logger

logger = get_logger("batch_worker")


class BatchConversionWorker:
    """Executes a batch of ConversionJobs concurrently using a ThreadPoolExecutor."""

    def __init__(
        self,
        config: ConversionConfig,
        on_job_updated: Optional[Callable[[ConversionJob], None]] = None,
        on_batch_completed: Optional[Callable[[BatchAuditSummary], None]] = None,
    ) -> None:
        self.config = config
        self.on_job_updated = on_job_updated
        self.on_batch_completed = on_batch_completed
        self._cancel_event = threading.Event()
        self._path_lock = threading.Lock()

    def cancel(self) -> None:
        """Signals active and pending worker tasks to abort."""
        logger.warning("Cancellation requested for active batch conversion.")
        self._cancel_event.set()

    @property
    def is_cancelled(self) -> bool:
        """Returns True if cancellation has been requested."""
        return self._cancel_event.is_set()

    def _notify_job(self, job: ConversionJob) -> None:
        if self.on_job_updated:
            try:
                self.on_job_updated(job)
            except Exception as exc:
                logger.error("Error in on_job_updated callback: %s", exc)

    def _process_single_job(self, job: ConversionJob) -> ConversionJob:
        """Processes a single ConversionJob inside a worker thread."""
        t0 = time.perf_counter()

        if self._cancel_event.is_set():
            job.status = JobStatus.SKIPPED
            job.error_message = "Cancelled by user"
            self._notify_job(job)
            return job

        job.target_format = self.config.target_format

        # Populate source size if not already set
        try:
            if job.source_size_bytes <= 0 and os.path.exists(job.source_path):
                job.source_size_bytes = os.path.getsize(job.source_path)
        except OSError:
            pass

        # Skip if source and target formats are identical
        if job.source_format == self.config.target_format:
            job.status = JobStatus.SKIPPED
            job.error_message = "Source and target formats are identical"
            job.duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            logger.info("Skipped %s (identical format: %s)", job.source_path, job.source_format.value)
            self._notify_job(job)
            return job

        # Resolve target path under lock to prevent race conditions on RENAME
        with self._path_lock:
            target_path, should_skip = resolve_output_path(
                source_path=job.source_path,
                root_ingest_dir=job.root_ingest_dir,
                output_dir=self.config.output_dir,
                target_format=self.config.target_format,
                preserve_tree=self.config.preserve_folder_tree,
                collision_policy=self.config.collision_policy,
            )
            job.target_path = target_path
            if not should_skip and self.config.collision_policy == CollisionPolicy.RENAME:
                # Touch an empty placeholder file so concurrent threads see the reserved name
                try:
                    Path(target_path).touch(exist_ok=True)
                except OSError:
                    pass

        if should_skip:
            job.status = JobStatus.SKIPPED
            job.error_message = "Target file already exists (CollisionPolicy.SKIP)"
            job.duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            logger.info("Skipped existing file: %s", target_path)
            self._notify_job(job)
            return job

        job.status = JobStatus.PROCESSING
        job.error_message = None
        self._notify_job(job)

        try:
            dom = convert_single_file(
                source_path=job.source_path,
                target_path=target_path,
                source_format=job.source_format,
                target_format=self.config.target_format,
                page_size=self.config.pdf_page_size,
            )
            job.heading_count = dom.heading_count
            job.table_count = dom.table_count
            job.word_count = dom.word_count
            if os.path.exists(target_path):
                job.output_size_bytes = os.path.getsize(target_path)
            job.duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            job.status = JobStatus.COMPLETED
            logger.info(
                "Converted %s -> %s (%d words, %.1f ms)",
                Path(job.source_path).name,
                Path(target_path).name,
                job.word_count,
                job.duration_ms,
            )
        except Exception as exc:
            job.duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            logger.error("Failed converting %s: %s", job.source_path, exc)

        self._notify_job(job)
        return job

    def run_batch(self, jobs: list[ConversionJob]) -> BatchAuditSummary:
        """Executes all jobs in the batch across the thread pool and returns a BatchAuditSummary."""
        self._cancel_event.clear()
        batch_start = time.perf_counter()
        max_workers = max(1, min(16, self.config.max_workers))

        logger.info(
            "Starting batch conversion: %d jobs -> %s (workers=%d, tree=%s, collision=%s)",
            len(jobs),
            self.config.target_format.value.upper(),
            max_workers,
            self.config.preserve_folder_tree,
            self.config.collision_policy.value,
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._process_single_job, job) for job in jobs]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    logger.error("Unhandled worker exception: %s", exc)

        total_duration_ms = round((time.perf_counter() - batch_start) * 1000.0, 2)
        completed = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
        skipped = sum(1 for j in jobs if j.status == JobStatus.SKIPPED)
        failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)

        summary = BatchAuditSummary(
            total_jobs=len(jobs),
            completed=completed,
            skipped=skipped,
            failed=failed,
            total_duration_ms=total_duration_ms,
            jobs=list(jobs),
        )

        logger.info(
            "Batch finished in %.1f ms: %d completed, %d skipped, %d failed.",
            total_duration_ms,
            completed,
            skipped,
            failed,
        )

        if self.on_batch_completed:
            try:
                self.on_batch_completed(summary)
            except Exception as exc:
                logger.error("Error in on_batch_completed callback: %s", exc)

        return summary


def export_audit_csv(summary: BatchAuditSummary, csv_path: str) -> None:
    """Writes a detailed UTF-8 CSV audit report for the completed batch."""
    out = Path(csv_path)
    os.makedirs(out.parent, exist_ok=True)

    headers = [
        "Job_ID",
        "Source_Path",
        "Source_Format",
        "Target_Path",
        "Target_Format",
        "Status",
        "Source_Bytes",
        "Output_Bytes",
        "Headings",
        "Tables",
        "Words",
        "Duration_MS",
        "Error_Message",
    ]

    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for job in summary.jobs:
            writer.writerow(
                [
                    job.job_id,
                    job.source_path,
                    job.source_format.value.upper(),
                    job.target_path or "",
                    job.target_format.value.upper(),
                    job.status.value,
                    job.source_size_bytes,
                    job.output_size_bytes,
                    job.heading_count,
                    job.table_count,
                    job.word_count,
                    f"{job.duration_ms:.2f}",
                    job.error_message or "",
                ]
            )
