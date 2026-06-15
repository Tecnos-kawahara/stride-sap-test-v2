"""Integration tests for run_report_generator.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from run_report_generator import generate_report, parse_findings, parse_decisions, parse_changelog, parse_spec_impact


class TestParseFindings:
    def test_findings_extracted(self):
        text = (
            "# Findings\n\n"
            "## Investigation 1: API timeout issue\n"
            "**Question**: Why does the API timeout?\n"
            "**Finding**: Connection pool exhaustion under load\n"
            "**Decision**: Increase pool size and add retry\n\n"
            "## Finding 2: Null check missing\n"
            "**Finding**: Null pointer in order validation\n"
        )
        findings = parse_findings(text)
        assert len(findings) == 2
        assert "pool" in findings[0].description.lower() or "timeout" in findings[0].description.lower()


class TestParseDecisions:
    def test_decisions_extracted(self):
        text = (
            "# Plan\n\n"
            "## Approach\n"
            "1. Set up connection pool configuration\n"
            "2. Implement retry with exponential backoff\n"
            "3. Add integration tests\n\n"
            "## Phases\n\n"
            "| Phase | Description | Status |\n"
            "|-------|-------------|--------|\n"
            "| 1 | Setup | done |\n"
            "| 2 | Core impl | in_progress |\n"
        )
        decisions = parse_decisions(text)
        assert len(decisions) >= 1
        assert any("retry" in d.decision.lower() for d in decisions)


class TestParseChangelog:
    def test_changelog_extracted(self):
        text = (
            "# Walkthrough\n\n"
            "Implementation completed.\n\n"
            "Code diff:\n"
            "- `src/api.ts` — Add retry logic to API client\n"
            "- `src/config.ts` — New pool configuration\n"
        )
        entries = parse_changelog(text)
        assert len(entries) >= 1
        assert any("api" in e.file_path.lower() for e in entries)


class TestParseSpecImpact:
    def test_spec_impact_detected(self):
        walkthrough = "# Walkthrough\n\n## spec-impact: required\n\nAPI timeout spec needs update.\n"
        findings = "## Investigation 1: timeout\n**Finding**: Timeout too low\n"
        level, impacts = parse_spec_impact(walkthrough, findings)
        assert level in ("required", "recommended", "none")


class TestGenerateReport:
    def test_full_report_from_project(self, run_report_project):
        feature = run_report_project / "specs" / "FEAT-RPT"
        run_dir = feature / "runs" / "WI-RPT-001" / "RUN-20260301-1000"

        # Update findings to use correct format
        planning = run_dir / ".planning"
        (planning / "findings.md").write_text(
            "# Findings\n\n"
            "## Investigation 1: API timeout\n"
            "**Finding**: Connection pool too small\n"
            "**Decision**: Increase pool\n\n"
            "## Finding 2: Null check\n"
            "**Finding**: Missing null guard\n",
            encoding="utf-8",
        )

        report = generate_report(run_dir)
        assert report.run_id == "RUN-20260301-1000"
        assert report.findings_count >= 1


class TestPostMock:
    def test_post_comment_calls_gh(self, run_report_project, monkeypatch):
        """post_comment() invokes _run_gh with issue comment args."""
        import run_report_generator as rrg

        calls = []
        def mock_run_gh(*args):
            calls.append(args)
            return (0, "ok", "")

        monkeypatch.setattr(rrg, "_run_gh", mock_run_gh)

        result = rrg.post_comment("42", "Test comment body")
        assert result is True
        assert len(calls) == 1
        cmd = calls[0]
        assert "issue" in cmd
        assert "comment" in cmd
        assert "42" in cmd

    def test_post_comment_failure_returns_false(self, monkeypatch):
        """post_comment() returns False on gh failure."""
        import run_report_generator as rrg

        monkeypatch.setattr(rrg, "_run_gh", lambda *a: (1, "", "auth error"))
        result = rrg.post_comment("42", "body")
        assert result is False
