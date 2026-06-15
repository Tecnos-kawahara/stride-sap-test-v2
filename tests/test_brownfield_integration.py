"""Integration tests for brownfield_detector.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from brownfield_detector import detect_workspace
from tests.project_builder import add_brownfield_indicators


class TestGreenfield:
    def test_empty_project_is_greenfield(self, tmp_path):
        result = detect_workspace(tmp_path)
        assert result["type"] == "greenfield"

    def test_specs_only_is_greenfield(self, full_pass_project):
        result = detect_workspace(full_pass_project)
        assert result["type"] == "greenfield"


class TestBrownfield:
    def test_node_project_detected(self, tmp_path):
        add_brownfield_indicators(tmp_path, lang="node")
        result = detect_workspace(tmp_path)
        assert result["type"] == "brownfield"
        langs = [l.lower() for l in result.get("languages", [])]
        assert "typescript" in langs or "javascript" in langs, f"Expected TS/JS, got: {langs}"

    def test_python_project_detected(self, tmp_path):
        add_brownfield_indicators(tmp_path, lang="python")
        result = detect_workspace(tmp_path)
        assert result["type"] == "brownfield"
        assert "python" in [l.lower() for l in result.get("languages", [])]

    def test_go_project_detected(self, tmp_path):
        add_brownfield_indicators(tmp_path, lang="go")
        result = detect_workspace(tmp_path)
        assert result["type"] == "brownfield"
        assert "go" in [l.lower() for l in result.get("languages", [])]


class TestMonorepo:
    def test_monorepo_indicator_detected(self, tmp_path):
        add_brownfield_indicators(tmp_path, lang="node", monorepo=True)
        result = detect_workspace(tmp_path)
        assert result["structure"] == "monorepo"


class TestJsonOutput:
    def test_json_format(self, brownfield_project):
        import subprocess
        result = subprocess.run(
            [sys.executable, "sdd-templates/tools/brownfield_detector.py", str(brownfield_project), "--json"],
            cwd=str(brownfield_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "type" in data
        assert data["type"] in ("greenfield", "brownfield")
