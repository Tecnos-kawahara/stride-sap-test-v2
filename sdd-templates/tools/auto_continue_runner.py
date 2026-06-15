#!/usr/bin/env python3
"""
Auto-Continue Planner

Generates the next executable phase sequence for a feature and explicitly
stops at the next HITL checkpoint (approval gate).

Usage:
    python3 auto_continue_runner.py <feature_dir> [--json]

Exit codes:
    0 = Plan generated successfully
    1 = Invalid feature path or other runtime error
    2 = Argument error
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import phase_gate


@dataclass
class PlanStep:
    """One actionable step in the auto-continue sequence."""

    index: int
    total: int
    status: str  # PASS | WARN | FAIL | SKIP
    action: str
    command: str = ""


FULL_WORKFLOW: dict[int, dict[str, object]] = {
    1: {
        "phase_name": "Design",
        "steps": [
            ("PASS", "Update `basic_design.md` and `process.bpmn` using current intent.", ""),
            ("PASS", "Run pre-approval lint and resolve structural issues.", "sdd-templates/tools/stride-lint {feature} --warn-only"),
            ("PASS", "Run strict lint and fix all errors except `APPROVAL_PENDING`.", "sdd-templates/tools/stride-lint {feature}"),
            ("PASS", "Run multi-model semantic evaluation. Fix findings and re-run until PASS.", "sdd-templates/bin/stride evaluate {feature} --phase design"),
            ("WARN", "HITL checkpoint: request Gate 1, 2 approval in `APPROVAL.md`.", ""),
        ],
    },
    2: {
        "phase_name": "Specify",
        "steps": [
            ("PASS", "Update `spec.md`, `plan.md`, and required contract artifacts.", ""),
            ("PASS", "Update `tests/scenarios.yaml` for new/changed acceptance criteria.", ""),
            ("PASS", "Run strict lint and resolve non-approval errors.", "sdd-templates/tools/stride-lint {feature}"),
            ("PASS", "Run multi-model semantic evaluation. Fix findings and re-run until PASS.", "sdd-templates/bin/stride evaluate {feature} --phase specify"),
            ("WARN", "HITL checkpoint: request Gate 3, 4 approval in `APPROVAL.md`.", ""),
        ],
    },
    3: {
        "phase_name": "Tasking",
        "steps": [
            ("PASS", "Update `tasks.md` and ensure all `plan_refs` are linked.", ""),
            ("PASS", "Create/adjust test tasks for integration/e2e tagged ACs.", ""),
            ("PASS", "Run strict lint and resolve non-approval errors.", "sdd-templates/tools/stride-lint {feature}"),
            ("PASS", "Run multi-model semantic evaluation. Fix findings and re-run until PASS.", "sdd-templates/bin/stride evaluate {feature} --phase tasking"),
            ("WARN", "HITL checkpoint: request Gate 5 approval in `APPROVAL.md`.", ""),
        ],
    },
    4: {
        "phase_name": "Execute",
        "steps": [
            ("PASS", "Execute tasks one by one and keep spec/plan/task traceability in sync.", ""),
            ("PASS", "Update Run artifacts (`.planning/`, `test_results.md`, `walkthrough.md`).", ""),
            ("PASS", "Run lint and project tests before requesting final approval.", "sdd-templates/tools/stride-lint {feature}"),
            ("WARN", "HITL checkpoint: request Final approval in `APPROVAL.md`.", ""),
        ],
    },
}

LITE_WORKFLOW: dict[int, dict[str, object]] = {
    1: {
        "phase_name": "Design & Flow",
        "steps": [
            ("PASS", "Update `basic_design.md` and `process.bpmn`.", ""),
            ("PASS", "Run strict lint and resolve non-approval errors.", "sdd-templates/tools/stride-lint {feature}"),
            ("PASS", "Run multi-model semantic evaluation. Fix findings and re-run until PASS.", "sdd-templates/bin/stride evaluate {feature} --phase design"),
            ("WARN", "HITL checkpoint: request Gate A approval in `APPROVAL.md`.", ""),
        ],
    },
    2: {
        "phase_name": "Spec & Plan",
        "steps": [
            ("PASS", "Update `spec.md`, `plan.md`, `contracts/*`, and `tests/*` artifacts.", ""),
            ("PASS", "Run strict lint and resolve non-approval errors.", "sdd-templates/tools/stride-lint {feature}"),
            ("PASS", "Run multi-model semantic evaluation. Fix findings and re-run until PASS.", "sdd-templates/bin/stride evaluate {feature} --phase specify"),
            ("WARN", "HITL checkpoint: request Gate B approval in `APPROVAL.md`.", ""),
        ],
    },
    3: {
        "phase_name": "Implementation & Verification",
        "steps": [
            ("PASS", "Update `tasks.md` and execute implementation changes.", ""),
            ("PASS", "Run lint/tests and gather evidence artifacts.", "sdd-templates/tools/stride-lint {feature}"),
            ("WARN", "HITL checkpoint: request Gate C approval in `APPROVAL.md`.", ""),
        ],
    },
}


def _sorted_gate_labels(gates: set[object]) -> list[str]:
    """Sort gate labels consistently for human output."""
    numeric = sorted([g for g in gates if isinstance(g, int)])
    symbolic = sorted([str(g) for g in gates if not isinstance(g, int)])
    return [str(n) for n in numeric] + symbolic


def build_plan(feature_dir: Path) -> dict[str, object]:
    """Build auto-continue plan until the next HITL checkpoint."""
    if not feature_dir.exists() or not feature_dir.is_dir():
        raise FileNotFoundError(f"Feature directory not found: {feature_dir}")

    approved_gates, lite_mode = phase_gate.get_approved_gates(feature_dir)
    current_phase = phase_gate.get_current_phase(approved_gates, lite_mode)
    phase_defs = phase_gate.PHASE_DEFINITIONS_LITE if lite_mode else phase_gate.PHASE_DEFINITIONS_FULL
    workflow = LITE_WORKFLOW if lite_mode else FULL_WORKFLOW
    max_phase = max(phase_defs.keys())

    if current_phase >= max_phase:
        return {
            "feature_dir": feature_dir.as_posix(),
            "lite_mode": lite_mode,
            "approved_gates": _sorted_gate_labels(approved_gates),
            "current_phase": current_phase,
            "complete": True,
            "target_phase": current_phase,
            "target_phase_name": phase_defs[current_phase]["name"],
            "target_gates": [],
            "steps": [],
        }

    target_phase = current_phase + 1
    target_meta = workflow[target_phase]
    raw_steps = target_meta["steps"]
    total = len(raw_steps)
    steps: list[PlanStep] = []
    for idx, (status, action, command_tpl) in enumerate(raw_steps, start=1):
        command = command_tpl.format(feature=feature_dir.as_posix()) if command_tpl else ""
        steps.append(PlanStep(index=idx, total=total, status=status, action=action, command=command))

    target_gates = [str(g) for g in phase_defs[target_phase]["required_gates"]]

    return {
        "feature_dir": feature_dir.as_posix(),
        "lite_mode": lite_mode,
        "approved_gates": _sorted_gate_labels(approved_gates),
        "current_phase": current_phase,
        "complete": False,
        "target_phase": target_phase,
        "target_phase_name": target_meta["phase_name"],
        "target_gates": target_gates,
        "steps": [asdict(s) for s in steps],
    }


def format_text(plan: dict[str, object]) -> str:
    """Render human-readable output in mandatory status/progress format."""
    lines: list[str] = []
    lines.append(f"Auto-Continue Plan: {plan['feature_dir']}")
    lines.append(f"Mode: {'Lite Mode' if plan['lite_mode'] else 'Full Mode'}")
    approved = plan["approved_gates"]
    approved_text = ", ".join(approved) if approved else "none"
    lines.append(f"Approved Gates: {approved_text}")
    lines.append(f"Current Approved Phase: {plan['current_phase']}")

    if plan["complete"]:
        lines.append("Status: PASS - All phases are already approved.")
        return "\n".join(lines)

    lines.append(f"Target Work Phase: {plan['target_phase']} ({plan['target_phase_name']})")
    lines.append(f"Stop Condition: Human approval for gate(s) {', '.join(plan['target_gates'])}")
    lines.append("")

    steps = plan["steps"]
    for step in steps:
        lines.append(f"[{step['index']}/{step['total']}] {step['status']} - {step['action']}")
        if step["command"]:
            lines.append(f"      Command: {step['command']}")

    return "\n".join(lines)


def _write_approval(feature_dir: Path, approved: set[object], lite_mode: bool = False) -> None:
    """Create a minimal APPROVAL.md fixture for tests."""
    if lite_mode:
        sections = ["A", "B", "C"]
        lines = ["# APPROVAL (Lite Mode)"]
        for gate in sections:
            if gate in approved:
                lines += [f"## Gate {gate}", "- [x] Review complete", "承認者: Reviewer", ""]
            else:
                lines += [f"## Gate {gate}", "- [ ] Review complete", "承認者: ___________", ""]
    else:
        sections: list[object] = [1, 2, 3, 4, 5, "final"]
        lines = ["# APPROVAL"]
        for gate in sections:
            title = "Final" if gate == "final" else f"Gate {gate}"
            if gate in approved:
                lines += [f"## {title}", "- [x] Review complete", "承認者: Reviewer", ""]
            else:
                lines += [f"## {title}", "- [ ] Review complete", "承認者: ___________", ""]
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "APPROVAL.md").write_text("\n".join(lines), encoding="utf-8")


def _run_self_tests() -> None:
    """Run self-tests."""
    import tempfile

    print("Running self-tests...")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        feature_dir = root / "specs" / "sample"

        # Test 1: No approvals -> target phase 1
        _write_approval(feature_dir, approved=set(), lite_mode=False)
        plan = build_plan(feature_dir)
        assert plan["target_phase"] == 1, f"expected target phase 1, got {plan['target_phase']}"
        print("  Test 1 passed: no approval -> target phase 1")

        # Test 2: Gate 1/2 approved -> target phase 2
        _write_approval(feature_dir, approved={1, 2}, lite_mode=False)
        plan = build_plan(feature_dir)
        assert plan["target_phase"] == 2, f"expected target phase 2, got {plan['target_phase']}"
        assert plan["target_gates"] == ["3", "4"], f"unexpected gates: {plan['target_gates']}"
        print("  Test 2 passed: Gate 1/2 approved -> target phase 2")

        # Test 3: All full-mode approvals complete
        _write_approval(feature_dir, approved={1, 2, 3, 4, 5, "final"}, lite_mode=False)
        plan = build_plan(feature_dir)
        assert plan["complete"] is True, "expected complete=True"
        print("  Test 3 passed: all approvals complete -> no pending phase")

        # Test 4: Lite mode detection + phase progression
        _write_approval(feature_dir, approved={"A"}, lite_mode=True)
        plan = build_plan(feature_dir)
        assert plan["lite_mode"] is True, "expected lite_mode=True"
        assert plan["target_phase"] == 2, f"expected target phase 2, got {plan['target_phase']}"
        assert plan["target_gates"] == ["B"], f"unexpected lite gates: {plan['target_gates']}"
        print("  Test 4 passed: lite mode gate progression")

    print("All 4 self-tests passed.")
    sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate next-phase auto-continue sequence.")
    parser.add_argument("feature_dir", nargs="?", help="Path to specs/<feature>/ directory")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    args = parser.parse_args()

    if args.test:
        _run_self_tests()
        return

    if not args.feature_dir:
        parser.error("the following arguments are required: feature_dir")

    feature_dir = Path(args.feature_dir)
    try:
        plan = build_plan(feature_dir)
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        print(f"FAIL: Unexpected error: {exc}")
        sys.exit(1)

    if args.json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        print(format_text(plan))
    sys.exit(0)


if __name__ == "__main__":
    main()
