"""Environment configuration loader with safe typed getters."""
import os
from pathlib import Path
from dotenv import load_dotenv
from src.models.doc_format import CollisionPolicy, DocFormat

# Load .env from project root if present
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def get_app_log_level() -> str:
    """Returns configured logging level (default: INFO)."""
    level = os.getenv("APP_LOG_LEVEL", "INFO").strip().upper()
    if level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        return "INFO"
    return level


def get_max_worker_threads() -> int:
    """Returns configured maximum worker threads (default: 4, clamped 1..16)."""
    raw = os.getenv("MAX_WORKER_THREADS", "4").strip()
    try:
        val = int(raw)
        return max(1, min(16, val))
    except ValueError:
        return 4


def get_default_collision_policy() -> CollisionPolicy:
    """Returns configured default collision policy (default: RENAME)."""
    raw = os.getenv("DEFAULT_COLLISION_POLICY", "RENAME").strip().upper()
    try:
        return CollisionPolicy(raw)
    except ValueError:
        return CollisionPolicy.RENAME


def get_default_target_format() -> DocFormat:
    """Returns configured default target format (default: PDF)."""
    raw = os.getenv("DEFAULT_TARGET_FORMAT", "PDF").strip().lower()
    fmt = DocFormat.from_extension(raw)
    return fmt if fmt is not None else DocFormat.PDF
