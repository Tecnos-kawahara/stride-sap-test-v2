"""Integration tests for phase_gate.py: Full Mode and Lite Mode."""

import sys
from pathlib import Path

import pytest


class TestPhaseGateFull:
    """Full Mode (Gates 1-5 + Final).

    Phase definitions:
        Phase 1 (Design):  requires gates {1, 2}
        Phase 2 (Specify): requires gates {3, 4}
        Phase 3 (Tasking): requires gates {5}
        Phase 4 (Execute): requires gates {"final"}
    """

    def test_no_gates_approved_is_phase_0(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-PG", mode="full", phase=1)
            .with_approval(set())
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        try:
            from phase_gate import get_approved_gates, get_current_phase
            gates, lite = get_approved_gates(project / "specs" / "FEAT-PG")
            assert lite is False
            phase = get_current_phase(gates, lite)
            assert phase == 0
        finally:
            sys.path.pop(0)

    def test_gate_1_2_approved_is_phase_1(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-PG2", mode="full", phase=1)
            .with_approval({1, 2})
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        try:
            from phase_gate import get_approved_gates, get_current_phase
            gates, lite = get_approved_gates(project / "specs" / "FEAT-PG2")
            phase = get_current_phase(gates, lite)
            assert phase == 1
        finally:
            sys.path.pop(0)

    def test_gate_1_through_4_approved_is_phase_2(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-PG3", mode="full", phase=1)
            .with_approval({1, 2, 3, 4})
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        try:
            from phase_gate import get_approved_gates, get_current_phase
            gates, lite = get_approved_gates(project / "specs" / "FEAT-PG3")
            phase = get_current_phase(gates, lite)
            assert phase == 2
        finally:
            sys.path.pop(0)

    def test_all_gates_approved_is_phase_4(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-PG4", mode="full", phase=5)
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        try:
            from phase_gate import get_approved_gates, get_current_phase
            gates, lite = get_approved_gates(project / "specs" / "FEAT-PG4")
            phase = get_current_phase(gates, lite)
            assert phase == 4  # All phases complete
        finally:
            sys.path.pop(0)


class TestPhaseGateLite:
    """Lite Mode (Gates A, B, C).

    Phase definitions:
        Phase 1 (Design & Flow):                  requires gates {"A"}
        Phase 2 (Spec & Plan):                     requires gates {"B"}
        Phase 3 (Implementation & Verification):   requires gates {"C"}
    """

    def test_lite_mode_detected(self, lite_pass_project):
        sys.path.insert(0, str(lite_pass_project / "sdd-templates" / "tools"))
        try:
            from phase_gate import get_approved_gates
            _, lite = get_approved_gates(lite_pass_project / "specs" / "FEAT-LTEST")
            assert lite is True
        finally:
            sys.path.pop(0)

    def test_gate_a_approved_is_phase_1(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-LPG", mode="lite", phase=2)
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        try:
            from phase_gate import get_approved_gates, get_current_phase
            gates, lite = get_approved_gates(project / "specs" / "FEAT-LPG")
            assert lite is True
            phase = get_current_phase(gates, lite)
            assert phase == 1
        finally:
            sys.path.pop(0)

    def test_all_lite_gates_approved_is_phase_3(self, lite_pass_project):
        sys.path.insert(0, str(lite_pass_project / "sdd-templates" / "tools"))
        try:
            from phase_gate import get_approved_gates, get_current_phase
            gates, lite = get_approved_gates(lite_pass_project / "specs" / "FEAT-LTEST")
            phase = get_current_phase(gates, lite)
            assert phase == 3  # All lite phases complete
        finally:
            sys.path.pop(0)
