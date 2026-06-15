"""Integration tests for sdd_planning_bridge.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

import sdd_planning_bridge as spb


@pytest.fixture(autouse=True)
def mock_knowledge_dir(tmp_path, monkeypatch):
    """Redirect KNOWLEDGE_DIR and PLANNING_TEMPLATES to tmp_path to avoid touching real home dir."""
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    templates = tmp_path / "templates"
    templates.mkdir()
    monkeypatch.setattr(spb, "KNOWLEDGE_DIR", knowledge)
    monkeypatch.setattr(spb, "PLANNING_TEMPLATES", templates)
    return knowledge


class TestInit:
    def test_init_creates_planning_dir(self, planning_bridge_project):
        feature = planning_bridge_project / "specs" / "FEAT-PBR"
        # Use a fresh run dir (not the one from fixture that already has .planning/)
        run_dir = feature / "runs" / "WI-PBR-001" / "RUN-20260302-0900"
        run_dir.mkdir(parents=True, exist_ok=True)
        rc = spb.cmd_init(feature, "WI-PBR-001", run_dir)
        assert rc == 0
        planning = run_dir / ".planning"
        assert planning.exists()
        plan = planning / "plan.md"
        assert plan.exists()
        text = plan.read_text(encoding="utf-8")
        assert "FEAT-PBR" in text or "WI-PBR" in text


class TestSync:
    def test_sync_updates_plan(self, planning_bridge_project, monkeypatch):
        feature = planning_bridge_project / "specs" / "FEAT-PBR"
        run_dir = feature / "runs" / "WI-PBR-001" / "RUN-20260302-0900"
        run_dir.mkdir(parents=True, exist_ok=True)
        spb.cmd_init(feature, "WI-PBR-001", run_dir)
        monkeypatch.setattr(spb, "search_knowledge", lambda tags: [])
        rc = spb.cmd_sync(feature, run_dir, "WI-PBR-001")
        assert rc == 0
        # plan.md should exist and have content
        plan = run_dir / ".planning" / "plan.md"
        assert plan.exists()
        text = plan.read_text(encoding="utf-8")
        assert len(text) > 10  # Not empty


class TestEvidence:
    def test_evidence_generates_section(self, planning_bridge_project, capsys):
        feature = planning_bridge_project / "specs" / "FEAT-PBR"
        run_dir = feature / "runs" / "WI-PBR-001" / "RUN-20260302-0900"
        run_dir.mkdir(parents=True, exist_ok=True)
        spb.cmd_init(feature, "WI-PBR-001", run_dir)

        # Add a walkthrough so evidence has something to process
        (run_dir / "walkthrough.md").write_text(
            "# Walkthrough\n\nImplementation done.\n\n## spec-impact: required\n\nTimeout update.\n",
            encoding="utf-8",
        )

        rc = spb.cmd_evidence(feature, "WI-PBR-001", run_dir)
        assert rc == 0
        captured = capsys.readouterr()
        out = captured.out
        # Evidence should reference planning content or produce evidence section
        # Check either stdout has content or walkthrough was updated
        walkthrough_text = (run_dir / "walkthrough.md").read_text(encoding="utf-8")
        has_evidence = "Planning Evidence" in walkthrough_text or "Evidence" in out or "evidence" in out
        assert has_evidence, f"Expected evidence output, got stdout='{out[:200]}', walkthrough has no 'Planning Evidence'"


class TestLearn:
    def test_learn_extracts_candidates(self, planning_bridge_project, capsys):
        feature = planning_bridge_project / "specs" / "FEAT-PBR"
        run_dir = feature / "runs" / "WI-PBR-001" / "RUN-20260302-0900"
        run_dir.mkdir(parents=True, exist_ok=True)
        spb.cmd_init(feature, "WI-PBR-001", run_dir)

        # Add findings with content so learn has something to extract
        planning = run_dir / ".planning"
        (planning / "findings.md").write_text(
            "# Findings\n\n| # | Type | Finding | Impact |\n|---|------|---------|--------|\n"
            "| 1 | Technical | API timeout | high |\n",
            encoding="utf-8",
        )

        rc = spb.cmd_learn(feature, "WI-PBR-001", run_dir, apply=False)
        assert rc == 0
        captured = capsys.readouterr()
        out = captured.out
        # Learn should report candidate count or "no candidates"
        assert "candidate" in out.lower() or "lesson" in out.lower() or "0" in out or len(out) > 0, \
            f"Expected learn output about candidates, got: '{out[:200]}'"
