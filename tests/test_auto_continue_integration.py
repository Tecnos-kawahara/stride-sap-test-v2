"""Integration tests for auto_continue_runner.py with real feature fixtures."""

import sys
from pathlib import Path

import pytest


class TestAutoContinueFull:
    """Full Mode phase transitions."""

    def test_no_approval_targets_phase_1(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-AC1", mode="full", phase=1)
            .with_approval(set())
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        try:
            from auto_continue_runner import build_plan
            plan = build_plan(project / "specs" / "FEAT-AC1")
            assert plan["target_phase"] == 1
            assert plan["target_phase_name"] == "Design"
            assert plan["complete"] is False
            # Verify evaluate step is included
            step_commands = [s["command"] for s in plan["steps"] if s["command"]]
            assert any("stride evaluate" in c or "stride-lint" in c for c in step_commands)
        finally:
            sys.path.pop(0)

    def test_gate_1_2_approved_targets_phase_2(self, specify_phase_project):
        sys.path.insert(0, str(specify_phase_project / "sdd-templates" / "tools"))
        try:
            from auto_continue_runner import build_plan
            plan = build_plan(specify_phase_project / "specs" / "FEAT-STEST")
            assert plan["target_phase"] == 2
            assert plan["target_phase_name"] == "Specify"
            assert plan["complete"] is False
        finally:
            sys.path.pop(0)

    def test_all_approved_is_complete(self, full_pass_project):
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        try:
            from auto_continue_runner import build_plan
            plan = build_plan(full_pass_project / "specs" / "FEAT-TEST")
            assert plan["complete"] is True
        finally:
            sys.path.pop(0)


class TestAutoContinueLite:
    """Lite Mode phase transitions."""

    def test_lite_no_approval_targets_phase_1(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-LAC", mode="lite", phase=1)
            .with_approval(set())
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        try:
            from auto_continue_runner import build_plan
            plan = build_plan(project / "specs" / "FEAT-LAC")
            assert plan["lite_mode"] is True
            assert plan["target_phase"] == 1
            assert plan["complete"] is False
        finally:
            sys.path.pop(0)

    def test_lite_all_approved_is_complete(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-LAC2", mode="lite", phase=4)
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        try:
            from auto_continue_runner import build_plan
            plan = build_plan(project / "specs" / "FEAT-LAC2")
            assert plan["lite_mode"] is True
            assert plan["complete"] is True
        finally:
            sys.path.pop(0)
