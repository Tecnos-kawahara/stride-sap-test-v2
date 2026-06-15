"""Integration tests for evidence_metrics_collector.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from evidence_metrics_collector import (
    collect_coverage,
    collect_test_results,
    collect_cache_stats,
    collect_gate_lead_time,
    collect_all_metrics,
    format_human_readable,
)
from tests.project_builder import add_coverage_summary, add_junit_xml, add_turbo_cache


class TestCollectCoverage:
    def test_reads_istanbul_json(self, evidence_project):
        result = collect_coverage(evidence_project)
        assert result["found"] is True
        assert result["line_pct"] == 85.0
        assert result["branch_pct"] == 70.0
        assert result["function_pct"] == 90.0

    def test_missing_coverage_returns_not_found(self, tmp_path):
        result = collect_coverage(tmp_path)
        assert result["found"] is False


class TestCollectTestResults:
    def test_reads_junit_xml(self, evidence_project):
        result = collect_test_results(evidence_project)
        assert result["found"] is True
        assert result["total"] == 20
        assert result["failed"] == 2

    def test_missing_results_returns_not_found(self, tmp_path):
        result = collect_test_results(tmp_path)
        assert result["found"] is False


class TestCollectCacheStats:
    def test_reads_turbo_cache(self, evidence_project):
        result = collect_cache_stats(evidence_project)
        assert result["found"] is True
        assert result["total_tasks"] == 10
        # Tool counts all .json files as cached (file existence = cache hit)
        assert result["cached_tasks"] == 10
        assert result["cache_hit_rate"] == 100.0

    def test_missing_turbo_returns_not_found(self, tmp_path):
        result = collect_cache_stats(tmp_path)
        assert result["found"] is False


class TestCollectGateLeadTime:
    def test_reads_approval_dates(self, evidence_project):
        result = collect_gate_lead_time(evidence_project)
        assert result["found"] is True
        assert len(result["gate_timestamps"]) >= 2
        assert result["total_lead_time_hours"] > 0


class TestCollectAllMetrics:
    def test_returns_all_sections(self, evidence_project):
        metrics = collect_all_metrics(evidence_project)
        assert "coverage" in metrics
        assert "tests" in metrics
        assert "cache" in metrics
        assert "gate_lead_time" in metrics
        assert "summary" in metrics
        assert metrics["summary"]["cache_hit_rate"] == 100.0
        assert metrics["coverage"]["found"] is True


class TestFormatHumanReadable:
    def test_contains_section_headings(self, evidence_project):
        metrics = collect_all_metrics(evidence_project)
        text = format_human_readable(metrics)
        assert "Coverage" in text or "coverage" in text
        assert "Test" in text or "test" in text


class TestJsonOutput:
    def test_json_format_valid(self, evidence_project):
        result = subprocess.run(
            [sys.executable, "sdd-templates/tools/evidence_metrics_collector.py",
             str(evidence_project), "--json"],
            cwd=str(evidence_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "coverage" in data
        assert "summary" in data


class TestGracefulDegradation:
    def test_all_missing_still_works(self, tmp_path):
        metrics = collect_all_metrics(tmp_path)
        assert metrics["coverage"]["found"] is False
        assert metrics["tests"]["found"] is False
        assert metrics["cache"]["found"] is False


import subprocess
