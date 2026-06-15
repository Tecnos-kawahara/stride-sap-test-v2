"""Integration tests for setup_project_labels.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from setup_project_labels import (
    create_labels,
    create_symphony_labels,
    STRIDE_LABELS,
    SYMPHONY_LABELS,
    _run_gh,
)


class TestLabelConstants:
    def test_stride_labels_not_empty(self):
        assert len(STRIDE_LABELS) > 0
        for label in STRIDE_LABELS:
            assert len(label) == 3  # (name, color, description)
            assert label[0]  # name not empty
            assert label[1]  # color not empty

    def test_symphony_labels_not_empty(self):
        assert len(SYMPHONY_LABELS) > 0
        for label in SYMPHONY_LABELS:
            assert len(label) == 3


class TestDryRun:
    def test_dry_run_reports_all_labels(self):
        result = create_labels("test/repo", dry_run=True)
        assert result["created"] == len(STRIDE_LABELS)
        assert result["exists"] == 0
        assert result["failed"] == 0
        for detail in result["details"]:
            assert "DRY-RUN" in detail

    def test_dry_run_does_not_call_gh(self, monkeypatch):
        calls = []
        monkeypatch.setattr("setup_project_labels._run_gh", lambda *a: (calls.append(a), (0, "", ""))[1])
        create_labels("test/repo", dry_run=True)
        assert len(calls) == 0

    def test_symphony_dry_run(self):
        result = create_symphony_labels("test/repo", dry_run=True)
        assert result["created"] == len(SYMPHONY_LABELS)
        for detail in result["details"]:
            assert "DRY-RUN" in detail


class TestGhMockCreated:
    def test_created_count_increments(self, monkeypatch):
        monkeypatch.setattr("setup_project_labels._run_gh", lambda *a: (0, "", ""))
        result = create_labels("test/repo", dry_run=False)
        assert result["created"] == len(STRIDE_LABELS)
        assert result["exists"] == 0
        assert result["failed"] == 0


class TestGhMockExists:
    def test_already_exists_count(self, monkeypatch):
        monkeypatch.setattr("setup_project_labels._run_gh", lambda *a: (1, "", "already exists"))
        result = create_labels("test/repo", dry_run=False)
        assert result["exists"] == len(STRIDE_LABELS)
        assert result["created"] == 0


class TestGhMockFailed:
    def test_permission_denied_count(self, monkeypatch):
        monkeypatch.setattr("setup_project_labels._run_gh", lambda *a: (1, "", "permission denied"))
        result = create_labels("test/repo", dry_run=False)
        assert result["failed"] == len(STRIDE_LABELS)
        assert result["created"] == 0
        assert result["exists"] == 0


class TestSymphonyLabels:
    def test_symphony_created(self, monkeypatch):
        monkeypatch.setattr("setup_project_labels._run_gh", lambda *a: (0, "", ""))
        result = create_symphony_labels("test/repo", dry_run=False)
        assert result["created"] == len(SYMPHONY_LABELS)
