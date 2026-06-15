"""Regression tests for pr_readiness_checker tool integration."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


TOOLS_DIR = Path(__file__).resolve().parent.parent.parent / "sdd-templates" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import pr_readiness_checker as prc


def test_check_stride_lint_uses_lint_config(monkeypatch, tmp_path):
    project_root = tmp_path / "project"
    feature_dir = project_root / "specs" / "feat"
    feature_dir.mkdir(parents=True)
    (feature_dir / "basic_design.md").write_text("# basic design\n", encoding="utf-8")

    seen = {}

    class LintConfig:
        def __init__(self):
            seen["config_created"] = True

    def lint_feature(path, config):
        seen["path"] = path
        seen["config_type"] = type(config).__name__
        return SimpleNamespace(errors=[], warnings=[])

    fake_module = SimpleNamespace(LintConfig=LintConfig, lint_feature=lint_feature)
    monkeypatch.setattr(prc, "_import_sibling", lambda _: fake_module)

    result = prc.check_stride_lint(project_root)

    assert result["status"] == prc.STATUS_PASS
    assert seen["config_created"] is True
    assert seen["config_type"] == "LintConfig"
    assert seen["path"] == str(feature_dir)


def test_check_stride_lint_returns_fail_not_warn_for_invalid_feature(tmp_path):
    project_root = tmp_path / "project"
    feature_dir = project_root / "specs" / "feat"
    feature_dir.mkdir(parents=True)
    (feature_dir / "basic_design.md").write_text("# incomplete\n", encoding="utf-8")

    result = prc.check_stride_lint(project_root)

    assert result["status"] == prc.STATUS_FAIL
    assert "errors" in result["detail"]
