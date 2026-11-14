"""Application logging with rotating file handler and thread-safe GUI event queue."""
import logging
import os
import queue
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from src.utils.config import get_app_log_level

_gui_log_queue: "queue.Queue[str]" = queue.Queue(maxsize=2000)
_logger_initialized = False


class QueueLogHandler(logging.Handler):
    """Pushes formatted log records into a thread-safe queue for GUI consumption."""

    def __init__(self, log_queue: "queue.Queue[str]") -> None:
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            try:
                self.log_queue.put_nowait(msg)
            except queue.Full:
                try:
                    self.log_queue.get_nowait()
                    self.log_queue.put_nowait(msg)
                except queue.Empty:
                    pass
        except Exception:
            self.handleError(record)


def get_gui_log_queue() -> "queue.Queue[str]":
    """Returns the shared thread-safe queue receiving log events."""
    return _gui_log_queue


def get_logger(name: str = "multi_format_converter") -> logging.Logger:
    """Configures and returns the application logger."""
    global _logger_initialized
    root_logger = logging.getLogger("multi_format_converter")

    if not _logger_initialized:
        level_name = get_app_log_level()
        level = getattr(logging, level_name, logging.INFO)
        root_logger.setLevel(level)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Rotating file handler in ~/.multi_format_converter/app.log
        try:
            log_dir = Path.home() / ".multi_format_converter"
            os.makedirs(log_dir, exist_ok=True)
            log_file = log_dir / "app.log"
            file_handler = RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except OSError:
            # Fallback if home directory is read-only in restricted environments
            pass

        # Thread-safe queue handler for GUI status bar / log drawer
        queue_handler = QueueLogHandler(_gui_log_queue)
        queue_handler.setFormatter(
            logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
        )
        root_logger.addHandler(queue_handler)

        _logger_initialized = True

    if name == "multi_format_converter":
        return root_logger
    return root_logger.getChild(name)
