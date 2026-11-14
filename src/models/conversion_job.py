"""Conversion job state and batch audit summary models."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from src.models.doc_format import DocFormat


class JobStatus(str, Enum):
    """Execution lifecycle status of a single conversion job."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


@dataclass
class ConversionJob:
    """Represents a single file conversion job in the batch queue."""
    job_id: str
    source_path: str
    root_ingest_dir: Optional[str]
    source_format: DocFormat
    target_format: DocFormat
    target_path: Optional[str] = None
    source_size_bytes: int = 0
    output_size_bytes: int = 0
    status: JobStatus = JobStatus.QUEUED
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    heading_count: int = 0
    table_count: int = 0
    word_count: int = 0


@dataclass
class BatchAuditSummary:
    """Aggregate summary of a completed or cancelled batch conversion run."""
    total_jobs: int
    completed: int
    skipped: int
    failed: int
    total_duration_ms: float
    jobs: list[ConversionJob] = field(default_factory=list)
