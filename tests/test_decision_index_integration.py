"""Integration tests for decision_index.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from decision_index import init_index, refresh_index, collect_adrs
from tests.project_builder import add_adr_artifacts


class TestInit:
    def test_init_creates_index(self, adr_project):
        path, count = init_index(adr_project)
        assert path.exists()
        assert count == 3
        text = path.read_text(encoding="utf-8")
        assert "ADR-001" in text
        assert "ADR-002" in text
        assert "ADR-003" in text

    def test_init_no_adrs_creates_empty(self, tmp_path):
        path, count = init_index(tmp_path)
        assert path.exists()
        assert count == 0


class TestRefresh:
    def test_refresh_after_adding_adrs(self, adr_project):
        # Init first
        path, _ = init_index(adr_project)
        # Add another ADR
        decisions = adr_project / "shared" / "decisions"
        (decisions / "ADR-004-new-decision.md").write_text(
            "---\nadr_id: ADR-004\nstatus: accepted\ndate: 2026-03-10\n"
            "title: New decision\n---\n# ADR-004: New decision\n",
            encoding="utf-8",
        )
        path, count = refresh_index(adr_project)
        assert count == 4
        text = path.read_text(encoding="utf-8")
        assert "ADR-004" in text
        assert "New decision" in text

    def test_refresh_reflects_status(self, adr_project):
        path, _ = init_index(adr_project)
        text = path.read_text(encoding="utf-8")
        assert "accepted" in text
        assert "proposed" in text

    def test_refresh_reflects_date(self, adr_project):
        path, _ = init_index(adr_project)
        text = path.read_text(encoding="utf-8")
        assert "2026-03-01" in text


class TestBrokenFrontmatter:
    def test_broken_adr_does_not_crash(self, tmp_path):
        add_adr_artifacts(tmp_path, count=2, broken_frontmatter=True)
        entries = collect_adrs(tmp_path)
        # Should still collect the valid ADRs
        valid = [e for e in entries if e.adr_id.startswith("ADR-")]
        assert len(valid) >= 2
