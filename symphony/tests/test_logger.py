"""Tests for symphony.logger."""
from __future__ import annotations

import json
import logging
from unittest.mock import patch

import pytest

import symphony.logger as logger_mod
from symphony.logger import (
    HumanFormatter,
    JSONFormatter,
    get_issue_logger,
    get_logger,
    setup_logging,
)


def _reset_logging_state() -> None:
    """Remove all handlers from the symphony logger and reset module state."""
    root = logging.getLogger("symphony")
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    # Also clean up any child loggers' file handlers
    for name in list(logging.Logger.manager.loggerDict):
        if name.startswith("symphony.issue."):
            child = logging.getLogger(name)
            for handler in child.handlers[:]:
                child.removeHandler(handler)
                handler.close()
    logger_mod._INITIALIZED = False
    logger_mod._CURRENT_LOG_DIR = ".symphony/logs"


class TestJSONFormatter:
    def test_format_produces_valid_json_with_required_fields(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="symphony.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="hello %s",
            args=("world",),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert "ts" in data
        assert data["level"] == "INFO"
        assert data["logger"] == "symphony.test"
        assert data["message"] == "hello world"


class TestHumanFormatter:
    def test_format_produces_human_readable_string(self):
        formatter = HumanFormatter()
        record = logging.LogRecord(
            name="symphony.test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="something went wrong",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert "WARNING" in output
        assert "symphony.test" in output
        assert "something went wrong" in output


class TestSetupLogging:
    def test_initializes_symphony_logger_with_handlers(self, tmp_path):
        _reset_logging_state()
        try:
            log_dir = str(tmp_path / "logs")
            setup_logging(log_dir=log_dir)

            root = logging.getLogger("symphony")
            assert root.level == logging.DEBUG
            assert root.propagate is False
            # Should have at least a console handler and a file handler
            handler_types = [type(h) for h in root.handlers]
            assert logging.StreamHandler in handler_types
            assert logging.FileHandler in handler_types
        finally:
            _reset_logging_state()


class TestGetLogger:
    def test_returns_child_logger_under_symphony_namespace(self, tmp_path):
        _reset_logging_state()
        try:
            # Patch the default log dir so setup_logging uses tmp_path
            with patch.object(logger_mod, "_CURRENT_LOG_DIR", str(tmp_path / "logs")):
                child = get_logger("mymodule")
            assert child.name == "symphony.mymodule"
            assert isinstance(child, logging.Logger)
        finally:
            _reset_logging_state()


class TestGetIssueLogger:
    def test_creates_file_handler_in_log_dir(self, tmp_path):
        _reset_logging_state()
        try:
            log_dir = str(tmp_path / "logs")
            issue_logger = get_issue_logger(42, log_dir=log_dir)

            assert issue_logger.name == "symphony.issue.42"
            # Should have at least one FileHandler
            file_handlers = [
                h for h in issue_logger.handlers
                if isinstance(h, logging.FileHandler)
            ]
            assert len(file_handlers) >= 1
            # The file handler path should contain the issue id
            assert "42.jsonl" in file_handlers[0].baseFilename
        finally:
            _reset_logging_state()
