"""Integration tests for stride_testreport_bridge.py."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from stride_testreport_bridge import (
    find_cases_json,
    load_cases,
    build_mapping_index,
    analyze,
    check_report_html,
    run_testreport_validate,
    format_text,
)
from tests.project_builder import add_testreport_artifacts


class TestFindCasesJson:
    def test_finds_in_testreport_dir(self, testreport_project):
        feature = testreport_project / "specs" / "FEAT-TR"
        path = find_cases_json(feature)
        assert path is not None
        assert "testreport" in str(path)

    def test_fallback_to_evidence_dir(self, tmp_path):
        feature = tmp_path / "specs" / "FEAT-FB"
        feature.mkdir(parents=True)
        add_testreport_artifacts(feature, use_evidence_dir=True)
        path = find_cases_json(feature)
        assert path is not None
        assert "evidence" in str(path)

    def test_returns_none_when_absent(self, tmp_path):
        path = find_cases_json(tmp_path)
        assert path is None


class TestLoadCases:
    def test_loads_direct_list(self, testreport_project):
        feature = testreport_project / "specs" / "FEAT-TR"
        path = find_cases_json(feature)
        cases = load_cases(path)
        assert len(cases) == 3
        assert cases[0]["id"] == "01_login"

    def test_loads_nested_object(self, tmp_path):
        import json
        cases_path = tmp_path / "cases.json"
        cases_path.write_text(json.dumps({"cases": [{"id": "a"}, {"id": "b"}]}))
        cases = load_cases(cases_path)
        assert len(cases) == 2


class TestBuildMappingIndex:
    def test_builds_index(self):
        mapping = {
            "mappings": [
                {"case_id": "01_login", "stride_refs": ["AC-001", "AC-002"]},
                {"case_id": "02_order", "stride_refs": ["AC-003"]},
            ]
        }
        index = build_mapping_index(mapping)
        assert "01_login" in index
        assert len(index["01_login"]) == 2
        assert "AC-001" in index["01_login"]

    def test_empty_mappings(self):
        index = build_mapping_index({"mappings": []})
        assert len(index) == 0


class TestAnalyze:
    def test_detects_coverage_and_gaps(self, testreport_project):
        feature = testreport_project / "specs" / "FEAT-TR"
        result = analyze(feature)
        assert result is not None
        assert result["cases_count"] == 3
        assert result["mapped_ac_count"] == 3  # AC-001, AC-002, AC-003
        assert "03_unmapped" in result["unmapped_cases"]

    def test_returns_none_without_cases(self, tmp_path):
        result = analyze(tmp_path)
        assert result is None


class TestCheckReportHtml:
    def test_exists(self, testreport_project):
        feature = testreport_project / "specs" / "FEAT-TR"
        result = check_report_html(feature / "testreport")
        assert result["exists"] is True

    def test_not_exists(self, tmp_path):
        result = check_report_html(tmp_path)
        assert result["exists"] is False


class TestRunTestreportValidate:
    def test_unavailable_when_cli_missing(self, testreport_project):
        feature = testreport_project / "specs" / "FEAT-TR"
        # testreport CLI should not be installed in test env
        result = run_testreport_validate(feature / "testreport")
        assert result["available"] is False

    def test_available_when_mocked(self, testreport_project, monkeypatch):
        import stride_testreport_bridge as stb
        monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/bin/testreport" if cmd == "testreport" else None)
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock.Mock(
            returncode=0, stdout="OK", stderr=""))
        feature = testreport_project / "specs" / "FEAT-TR"
        result = run_testreport_validate(feature / "testreport")
        assert result["available"] is True
        assert result["success"] is True


class TestFormatText:
    def test_contains_sections(self, testreport_project):
        feature = testreport_project / "specs" / "FEAT-TR"
        result = analyze(feature)
        text = format_text(result)
        assert "Test cases" in text or "cases" in text.lower()
        assert "Unmapped" in text or "unmapped" in text.lower()
        assert "Report" in text or "report" in text.lower()
