"""Structured logging for the Symphony orchestrator."""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Include extra fields if set via extra={}
        for key in ("issue_id", "phase", "engine", "workspace", "event"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val
        return json.dumps(log_entry, ensure_ascii=False)


class HumanFormatter(logging.Formatter):
    """Human-readable console formatter."""

    FMT = "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s"
    DATE_FMT = "%H:%M:%S"

    def __init__(self) -> None:
        super().__init__(fmt=self.FMT, datefmt=self.DATE_FMT)


def _ensure_file_handler(
    logger: logging.Logger,
    log_dir: str,
    issue_id: Optional[int] = None,
) -> None:
    """Lazily add a file handler that writes JSONL to the date-partitioned log dir."""
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    day_dir = Path(log_dir) / today
    day_dir.mkdir(parents=True, exist_ok=True)

    if issue_id is not None:
        log_file = day_dir / f"{issue_id}.jsonl"
    else:
        log_file = day_dir / "orchestrator.jsonl"

    # Avoid duplicate handlers for the same file
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == str(log_file):
            return

    fh = logging.FileHandler(str(log_file), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(JSONFormatter())
    logger.addHandler(fh)


_INITIALIZED = False
_CURRENT_LOG_DIR: str = ".symphony/logs"


def setup_logging(
    log_dir: str = ".symphony/logs",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> None:
    """Initialize the symphony logger with console and file handlers.

    Safe to call multiple times. Re-initializes the file handler if
    *log_dir* changes from the previously configured value.
    """
    global _INITIALIZED, _CURRENT_LOG_DIR

    root_logger = logging.getLogger("symphony")

    if not _INITIALIZED:
        _INITIALIZED = True
        root_logger.setLevel(logging.DEBUG)
        root_logger.propagate = False

        # Console handler (only once)
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(console_level)
        ch.setFormatter(HumanFormatter())
        root_logger.addHandler(ch)

        # File handler (orchestrator-level)
        _ensure_file_handler(root_logger, log_dir)
        _CURRENT_LOG_DIR = log_dir

    elif log_dir != _CURRENT_LOG_DIR:
        # log_dir changed — replace file handler
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                root_logger.removeHandler(handler)
                handler.close()
        _ensure_file_handler(root_logger, log_dir)
        _CURRENT_LOG_DIR = log_dir


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'symphony' namespace.

    Automatically initializes the root logger if not done yet.
    """
    setup_logging()
    return logging.getLogger(f"symphony.{name}")


def get_issue_logger(issue_id: int, log_dir: str = ".symphony/logs") -> logging.Logger:
    """Return a logger with a dedicated JSONL file handler for a specific issue.

    If *log_dir* differs from previously attached file handlers, old handlers
    are removed so logs are not duplicated into both locations.
    """
    setup_logging(log_dir=log_dir)
    logger = logging.getLogger(f"symphony.issue.{issue_id}")

    # Remove stale file handlers that point to a different log_dir
    log_dir_resolved = str(Path(log_dir).resolve())
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler_dir = str(Path(handler.baseFilename).resolve().parent.parent)
            if handler_dir != log_dir_resolved:
                logger.removeHandler(handler)
                handler.close()

    _ensure_file_handler(logger, log_dir, issue_id=issue_id)
    return logger
