"""Integration tests for amendment_generator.py (deterministic, no gh calls)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

import amendment_generator as ag


def _mock_run_gh(*args, **kwargs):
    """Mock _run_gh to avoid actual GitHub calls."""
    return (1, "", "gh not found")


def _mock_search_issues(label, limit=50):
    """Mock _search_issues_by_label to return empty."""
    return []


def _mock_detect_risk_dep(feature_id):
    """Mock _detect_related_risk_dep to return empty."""
    return []


def _mock_detect_affected_wis(feature_id):
    """Mock _detect_affected_wis to return empty."""
    return []


def _mock_next_amd_id(feature_id):
    """Mock _next_amd_id to return deterministic ID."""
    return "AMD-001"


class TestAnalyze:
    """Tests for cmd_analyze (findings/decisions extraction)."""

    def test_analyze_extracts_findings(self, amendment_project, monkeypatch, capsys):
        """analyze detects findings from run artifacts."""
        monkeypatch.setattr(ag, "_run_gh", _mock_run_gh)
        monkeypatch.setattr(ag, "_search_issues_by_label", _mock_search_issues)
        monkeypatch.setattr(ag, "_detect_related_risk_dep", _mock_detect_risk_dep)
        monkeypatch.setattr(ag, "_detect_affected_wis", _mock_detect_affected_wis)

        args = argparse.Namespace(
            feature="FEAT-AMD",
            topic="API timeout",
        )
        monkeypatch.chdir(amendment_project)
        rc = ag.cmd_analyze(args)
        assert rc == 0
        captured = capsys.readouterr()
        assert "Amendment Impact Analysis" in captured.out
        assert "FEAT-AMD" in captured.out


class TestDraft:
    """Tests for cmd_draft (AMD body generation)."""

    def test_draft_contains_required_sections(self, amendment_project, monkeypatch, capsys):
        """draft output contains AMD ID, title, scope, and approval sections."""
        monkeypatch.setattr(ag, "_run_gh", _mock_run_gh)
        monkeypatch.setattr(ag, "_next_amd_id", _mock_next_amd_id)

        args = argparse.Namespace(
            feature="FEAT-AMD",
            title="Increase API timeout for mcframe",
            scope="spec.md NFR section",
            spec_sections="requirements.performance",
            findings="F-1",
            decisions="D-1",
        )
        monkeypatch.chdir(amendment_project)
        rc = ag.cmd_draft(args)
        assert rc == 0
        captured = capsys.readouterr()
        assert "AMD-001" in captured.out
        assert "FEAT-AMD" in captured.out


class TestApplyDryRun:
    """Tests for cmd_apply --dry-run."""

    def test_apply_dry_run_unapproved_returns_1(self, amendment_project, monkeypatch, capsys):
        """apply --dry-run with unapproved body hits early return (rc=1)."""
        monkeypatch.setattr(ag, "_run_gh", _mock_run_gh)

        mock_body = (
            "**AMD ID:** AMD-001\n"
            "**Feature:** FEAT-AMD\n\n"
            "## Spec Diff Candidates\n\n"
            "### Diff 1\n"
            "**File:** spec.md\n"
            "**Section:** requirements.performance\n"
            "**Change:** Update P95 timeout from 3s to 5s\n\n"
            "## Approval\n- [ ] Approved\n"
        )
        monkeypatch.setattr(ag, "_get_issue_body", lambda n: mock_body)
        monkeypatch.setattr(ag, "_get_issue_labels", lambda n: ["amendment"])

        args = argparse.Namespace(issue=999, dry_run=True)
        monkeypatch.chdir(amendment_project)
        rc = ag.cmd_apply(args)
        assert rc == 1, "Unapproved amendment should return 1"
        captured = capsys.readouterr()
        assert "ERROR" in captured.err or "チェックボックス" in captured.err

    def test_apply_dry_run_approved_reaches_patch_phase(self, amendment_project, monkeypatch, capsys):
        """apply --dry-run with approved body reaches spec patch phase (rc=0)."""
        monkeypatch.setattr(ag, "_run_gh", _mock_run_gh)

        mock_body = (
            "**AMD ID:** AMD-001\n"
            "**Feature:** FEAT-AMD\n\n"
            "## Spec Diff Candidates\n\n"
            "### Diff 1\n"
            "**File:** spec.md\n"
            "**Section:** requirements.performance\n"
            "**Change:** Update P95 timeout from 3s to 5s\n\n"
            "## Approval\n- [x] PM承認\n承認者: tanaka\n日付: 2026-03-01\n"
        )
        monkeypatch.setattr(ag, "_get_issue_body", lambda n: mock_body)
        monkeypatch.setattr(ag, "_get_issue_labels", lambda n: ["amendment"])

        args = argparse.Namespace(issue=999, dry_run=True)
        monkeypatch.chdir(amendment_project)
        rc = ag.cmd_apply(args)
        assert rc == 0, f"Approved dry-run apply should return 0, got {rc}"
        captured = capsys.readouterr()
        assert "Applying amendment" in captured.out


class TestFinalizeDryRun:
    """Tests for cmd_finalize --dry-run."""

    def test_finalize_dry_run_without_applying_label_returns_1(self, amendment_project, monkeypatch, capsys):
        """finalize --dry-run without amendment:applying label hits early return."""
        monkeypatch.setattr(ag, "_run_gh", _mock_run_gh)

        mock_body = (
            "**AMD ID:** AMD-001\n"
            "**Feature:** FEAT-AMD\n\n"
            "## Derived Work Items\n\n"
            "### WI 1\n"
            "**Title:** Update spec NFR timeout\n"
            "**Feature:** FEAT-AMD\n"
            "**Scope:** spec.md\n\n"
            "## Approval\n- [x] Approved\n承認者: test\n"
        )
        monkeypatch.setattr(ag, "_get_issue_body", lambda n: mock_body)
        monkeypatch.setattr(ag, "_get_issue_labels", lambda n: ["amendment"])  # NO applying label

        args = argparse.Namespace(issue=999, dry_run=True, force=False)
        monkeypatch.chdir(amendment_project)
        rc = ag.cmd_finalize(args)
        assert rc == 1, "Missing amendment:applying label should return 1"

    def test_finalize_dry_run_with_applying_label_succeeds(self, amendment_project, monkeypatch, capsys):
        """finalize --dry-run with correct label reaches WI creation phase."""
        monkeypatch.setattr(ag, "_run_gh", _mock_run_gh)
        monkeypatch.setattr(ag, "_detect_affected_wis", _mock_detect_affected_wis)

        mock_body = (
            "**AMD ID:** AMD-001\n"
            "**Feature:** FEAT-AMD\n\n"
            "## Derived Work Items\n\n"
            "### WI 1\n"
            "**Title:** Update spec NFR timeout\n"
            "**Feature:** FEAT-AMD\n"
            "**Scope:** spec.md\n\n"
            "## Approval\n- [x] Approved\n承認者: test\n"
        )
        monkeypatch.setattr(ag, "_get_issue_body", lambda n: mock_body)
        monkeypatch.setattr(ag, "_get_issue_labels", lambda n: ["amendment", "amendment:applying"])

        args = argparse.Namespace(issue=999, dry_run=True, force=False)
        monkeypatch.chdir(amendment_project)
        rc = ag.cmd_finalize(args)
        assert rc == 0, f"Finalize dry-run with applying label should return 0, got {rc}"
        captured = capsys.readouterr()
        assert "Finalizing amendment" in captured.out
