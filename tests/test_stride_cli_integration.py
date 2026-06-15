"""Integration tests for stride CLI subcommands via subprocess."""

import os
import subprocess
from pathlib import Path

import pytest


class TestStrideHelp:
    def test_stride_help_exit_zero(self, full_pass_project):
        result = subprocess.run(
            ["sdd-templates/bin/stride", "help"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "stride" in result.stdout.lower()


class TestStridePhaseStatus:
    def test_phase_status_shows_gates(self, full_pass_project):
        result = subprocess.run(
            ["sdd-templates/bin/stride", "phase-status", "specs/FEAT-TEST/"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 0


class TestStrideAutoContinue:
    def test_auto_continue_shows_plan(self, design_phase_project):
        result = subprocess.run(
            ["sdd-templates/bin/stride", "auto-continue", "specs/FEAT-DTEST/"],
            cwd=str(design_phase_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Design" in result.stdout or "HITL" in result.stdout


class TestStrideEvaluate:
    def test_evaluate_config_error_without_api_keys(self, full_pass_project, monkeypatch):
        """stride evaluate should exit 2 when API keys are not configured."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        result = subprocess.run(
            ["sdd-templates/bin/stride", "evaluate", "specs/FEAT-TEST/", "--phase", "design"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
            env={**dict(os.environ), "OPENAI_API_KEY": "", "OPENAI_MODEL": ""},
        )
        assert result.returncode == 2

    def test_evaluate_rejects_lite_mode_flag(self, full_pass_project):
        result = subprocess.run(
            ["sdd-templates/bin/stride", "evaluate", "specs/FEAT-TEST/", "--lite-mode"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        combined = (result.stderr + result.stdout).lower()
        assert "not yet supported" in combined
