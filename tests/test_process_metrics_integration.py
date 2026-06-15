"""Integration tests for stride_process_metrics.py."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from stride_process_metrics import (
    parse_approval_dates,
    compute_gate_process_times,
    determine_current_gate,
    compute_current_gate_age,
    assess_delay_risk,
    compute_inject_rates,
    analyze_feature,
    format_json,
    format_table,
    format_markdown,
    find_dashboard_path,
    update_dashboard,
    FeatureMetrics,
)
from tests.project_builder import add_state_yaml, add_pm_dashboard


class TestParseApprovalDates:
    def test_extracts_dates(self, process_metrics_project):
        feature = process_metrics_project / "specs" / "FEAT-PM"
        dates = parse_approval_dates(feature / "APPROVAL.md")
        assert dates.get("gate1_design") == "2026-01-10"
        assert dates.get("gate2_bpmn") == "2026-01-12"
        assert dates.get("gate5_tasks") == "2026-02-01"
        # Final not approved → None
        assert dates.get("evidence") is None


class TestComputeGateProcessTimes:
    def test_gate_times(self, process_metrics_project):
        feature = process_metrics_project / "specs" / "FEAT-PM"
        dates = parse_approval_dates(feature / "APPROVAL.md")
        times = compute_gate_process_times(dates)
        assert "gate1_design" in times
        assert "gate2_bpmn" in times
        # Gate 2 should be 2 days after Gate 1 (Jan 10 → Jan 12)
        assert times["gate2_bpmn"].days == 2


class TestDetermineCurrentGate:
    def test_returns_unapproved_gate(self, process_metrics_project):
        feature = process_metrics_project / "specs" / "FEAT-PM"
        dates = parse_approval_dates(feature / "APPROVAL.md")
        current = determine_current_gate(dates)
        assert current == "evidence"


class TestAssessDelayRisk:
    def test_on_track(self):
        assert assess_delay_risk(1, "medium") == "on_track"

    def test_at_risk(self):
        assert assess_delay_risk(3, "medium") == "at_risk"

    def test_overdue(self):
        assert assess_delay_risk(6, "medium") == "overdue"

    def test_none_age(self):
        assert assess_delay_risk(None, "medium") == "on_track"


class TestComputeInjectRates:
    def test_inject_rate_calculated(self, process_metrics_project):
        feature = process_metrics_project / "specs" / "FEAT-PM"
        import yaml
        state = yaml.safe_load((feature / "state" / "state.yaml").read_text())
        rates = compute_inject_rates(state, feature)
        # Initial: 5 tasks, current: 6 tasks, 2 WIs → distributed per-WI
        # WI-PM-001: init=3, curr=3 → 0%; WI-PM-002: init=2, curr=3 → 50%
        assert len(rates) == 2
        assert rates[0].inject_rate_pct == 0.0
        assert rates[1].inject_rate_pct == 50.0


class TestAnalyzeFeature:
    def test_returns_feature_metrics(self, process_metrics_project):
        feature = process_metrics_project / "specs" / "FEAT-PM"
        metrics = analyze_feature(feature, today=date(2026, 2, 15))
        assert isinstance(metrics, FeatureMetrics)
        assert metrics.feature == "FEAT-PM"
        assert metrics.total_days > 0
        assert metrics.current_gate == "evidence"


class TestFormatters:
    def test_format_json_valid(self, process_metrics_project):
        feature = process_metrics_project / "specs" / "FEAT-PM"
        metrics = analyze_feature(feature, today=date(2026, 2, 15))
        import json
        out = format_json([metrics])
        data = json.loads(out)
        # format_json with 1 item may return dict or list
        if isinstance(data, list):
            assert len(data) >= 1
            assert "feature" in data[0]
        else:
            assert "feature" in data or "gate_process_times" in data

    def test_format_table_has_content(self, process_metrics_project):
        feature = process_metrics_project / "specs" / "FEAT-PM"
        metrics = analyze_feature(feature, today=date(2026, 2, 15))
        out = format_table([metrics])
        assert "FEAT-PM" in out or "Gate" in out or "gate" in out

    def test_format_markdown_has_sections(self, process_metrics_project):
        feature = process_metrics_project / "specs" / "FEAT-PM"
        metrics = analyze_feature(feature, today=date(2026, 2, 15))
        out = format_markdown([metrics])
        assert "##" in out
        assert "Process" in out or "Gate" in out or "gate" in out


class TestFindDashboardPath:
    def test_finds_dashboard_via_state_yaml(self, process_metrics_project):
        feature = process_metrics_project / "specs" / "FEAT-PM"
        path = find_dashboard_path(feature)
        assert path is not None
        assert "EPIC-PM" in str(path)
        assert "PM_DASHBOARD.md" in str(path)

    def test_returns_none_without_state(self, tmp_path):
        path = find_dashboard_path(tmp_path)
        assert path is None


class TestUpdateDashboard:
    def test_dry_run_does_not_modify(self, process_metrics_project):
        feature = process_metrics_project / "specs" / "FEAT-PM"
        dashboard = process_metrics_project / "epics" / "EPIC-PM" / "PM_DASHBOARD.md"
        before = dashboard.read_text(encoding="utf-8")
        result = update_dashboard(dashboard, "## Process Metrics\n\nNew content\n", dry_run=True)
        assert result is True
        after = dashboard.read_text(encoding="utf-8")
        assert before == after

    def test_actual_update_writes_content(self, process_metrics_project):
        feature = process_metrics_project / "specs" / "FEAT-PM"
        dashboard = process_metrics_project / "epics" / "EPIC-PM" / "PM_DASHBOARD.md"
        result = update_dashboard(dashboard, "## Process Metrics\n\nUpdated content\n", dry_run=False)
        assert result is True
        text = dashboard.read_text(encoding="utf-8")
        assert "Updated content" in text
