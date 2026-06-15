"""Integration tests for setup_hooks.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

import setup_hooks
from tests.project_builder import add_hooks_settings

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _ensure_sdd_templates(root: Path) -> None:
    """setup_hooks requires sdd-templates/ in cwd."""
    sdd = root / "sdd-templates"
    if not sdd.exists():
        sdd.mkdir(parents=True)
    hooks_dir = sdd / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_script = hooks_dir / "phase_gate_hook.py"
    if not hook_script.exists():
        real = _REPO_ROOT / "sdd-templates" / "hooks" / "phase_gate_hook.py"
        if real.exists():
            hook_script.write_text(real.read_text(), encoding="utf-8")
        else:
            hook_script.write_text("# placeholder", encoding="utf-8")


class TestCreateFromMissing:
    def test_creates_settings_json(self, hooks_project, monkeypatch):
        _ensure_sdd_templates(hooks_project)
        monkeypatch.chdir(hooks_project)
        setup_hooks.main()
        settings = hooks_project / ".claude" / "settings.json"
        assert settings.exists()
        data = json.loads(settings.read_text())
        assert "hooks" in data
        assert "PreToolUse" in data["hooks"]

    def test_output_contains_phase_gate(self, hooks_project, monkeypatch):
        _ensure_sdd_templates(hooks_project)
        monkeypatch.chdir(hooks_project)
        setup_hooks.main()
        text = (hooks_project / ".claude" / "settings.json").read_text()
        assert "phase_gate" in text


class TestCreateFromEmpty:
    def test_empty_file_recovers(self, tmp_path, monkeypatch):
        add_hooks_settings(tmp_path, state="empty")
        _ensure_sdd_templates(tmp_path)
        monkeypatch.chdir(tmp_path)
        setup_hooks.main()
        settings = tmp_path / ".claude" / "settings.json"
        data = json.loads(settings.read_text())
        assert "hooks" in data


class TestBrokenJson:
    def test_broken_json_handled(self, tmp_path, monkeypatch):
        add_hooks_settings(tmp_path, state="broken")
        _ensure_sdd_templates(tmp_path)
        monkeypatch.chdir(tmp_path)
        setup_hooks.main()
        settings = tmp_path / ".claude" / "settings.json"
        data = json.loads(settings.read_text())
        assert "hooks" in data


class TestExistingHooks:
    def test_no_duplicate_hooks(self, tmp_path, monkeypatch):
        add_hooks_settings(tmp_path, state="existing")
        _ensure_sdd_templates(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("builtins.input", lambda _: "y")
        setup_hooks.main()
        settings = tmp_path / ".claude" / "settings.json"
        data = json.loads(settings.read_text())
        pre_tool = data.get("hooks", {}).get("PreToolUse", [])
        gate_count = sum(1 for h in pre_tool for hk in h.get("hooks", [])
                         if "phase_gate" in hk.get("command", ""))
        assert gate_count <= 1, f"phase_gate hook duplicated: {gate_count} times"
