#!/usr/bin/env python3
"""
ERP Addon Execution Tracking Validator

This module validates Work Item, Run, State, and Mode structures
for ERP addon projects that opt-in to execution tracking.

Activation conditions:
1. specs/<feature>/work_items/ directory exists OR
   basic_design.md has execution_profile: erp_addon
2. AND Gate 5 or later (tasks.md exists or Gate 5 approved)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


# Mode severity order for policy comparison
MODE_ORDER = {"autopilot": 0, "confirm": 1, "validate": 2}

# Low-risk flags that allow autopilot even at critical tier
LOW_RISK_FLAGS = {"ui_only", "message_only", "test_only", "logging_only"}

# Full ops pack files (4 items)
FULL_OPS_PACK = [
    "transport_manifest.yaml",
    "release_checklist.md",
    "rollback_plan.md",
    "hypercare_runbook.md",
]


@dataclass
class ValidationError:
    """A single validation error with code, message, and optional details."""
    code: str
    message: str
    details: list[str] = field(default_factory=list)


@dataclass
class ValidationWarning:
    """A single validation warning (non-blocking)."""
    code: str
    message: str
    details: list[str] = field(default_factory=list)


def _read_text(path: Path) -> str:
    """Read file as UTF-8 text."""
    return path.read_text(encoding="utf-8")


def _parse_front_matter(md_text: str) -> dict[str, Any]:
    """Parse YAML front matter from markdown file."""
    if not md_text.startswith("---"):
        return {}
    # Split by '\n---' (front matter terminator)
    parts = md_text.split("\n---", 2)
    if len(parts) < 2:
        return {}
    yml = parts[0].lstrip("-").strip()
    if yaml is None:
        return {}
    try:
        return yaml.safe_load(yml) or {}
    except Exception:
        return {}


def _extract_body(md_text: str) -> str:
    """Extract markdown body after YAML front matter."""
    if not md_text.startswith("---"):
        return md_text
    parts = md_text.split("\n---", 2)
    if len(parts) < 2:
        return ""
    return parts[1]


def _load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file safely."""
    if yaml is None or not path.exists():
        return {}
    try:
        return yaml.safe_load(_read_text(path)) or {}
    except Exception:
        return {}


def _find_project_root(feature_path: Path) -> Path:
    """Find project root by looking for memory/ or sdd-templates/ directory."""
    # feature_path is typically specs/<feature>/
    # Project root is 2 levels up, or search upward
    current = feature_path.resolve()
    for _ in range(5):  # Max 5 levels up
        if (current / "memory").exists() or (current / "sdd-templates").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    # Fallback: assume specs/<feature>/ -> 2 levels up
    return feature_path.resolve().parent.parent


def _get_recommended_mode(risk_flags: list[str], mode_policy: dict[str, Any]) -> str:
    """Determine the recommended mode based on risk_flags and mode_policy rules."""
    best = "autopilot"
    for rule in mode_policy.get("rules", []):
        flags = set(rule.get("if_any_risk_flags", []))
        if flags.intersection(set(risk_flags)):
            candidate = rule.get("mode", "autopilot")
            if MODE_ORDER.get(candidate, 0) > MODE_ORDER.get(best, 0):
                best = candidate
    return best


def _required_checkpoints(mode_policy: dict[str, Any], mode: str, phase: str) -> list[str]:
    """Return required checkpoint names for a given mode and phase (pre_run/post_run)."""
    modes = mode_policy.get("modes") or {}
    mode_def = modes.get(mode) or {}
    checkpoints = mode_def.get("checkpoints") or {}
    required = checkpoints.get(phase) or []
    return list(required)


def _check_pre_run_approval(approval_path: Path, required: list[str]) -> list[str]:
    """Check if required pre-run approval checkboxes are completed."""
    missing = []
    if not approval_path.exists():
        return ["approval_file_missing"]

    txt = _read_text(approval_path)

    for req in required:
        pattern = rf"\[x\].*{re.escape(req)}"
        if not re.search(pattern, txt, flags=re.IGNORECASE):
            missing.append(f"pre_run:{req}")

    return missing


def _check_post_run_approval(approval_path: Path, required: list[str]) -> list[str]:
    """Check if required post-run approval checkboxes are completed."""
    missing = []
    if not approval_path.exists():
        return ["approval_file_missing"]

    txt = _read_text(approval_path)

    for req in required:
        pattern = rf"\[x\].*{re.escape(req)}"
        if not re.search(pattern, txt, flags=re.IGNORECASE):
            missing.append(f"post_run:{req}")

    return missing


def validate_erp_addon_execution_tracking(
    feature_path: str | Path,
    approval_status: dict[str | int, bool],
    coverage_tier: str,
) -> tuple[list[tuple[str, str, list[str]]], list[tuple[str, str, list[str]]]]:
    """
    Validate ERP Addon execution tracking for a feature.

    Args:
        feature_path: Path to specs/<feature>/ directory
        approval_status: Dict mapping gate numbers to approval status
        coverage_tier: Coverage tier (critical, standard, experimental)

    Returns:
        Tuple of (errors, warnings) where each is a list of (code, message, details) tuples
    """
    fp = Path(feature_path)
    errors: list[tuple[str, str, list[str]]] = []
    warnings: list[tuple[str, str, list[str]]] = []

    # Check if ERP Addon is active
    work_items_dir = fp / "work_items"
    basic_design_path = fp / "basic_design.md"

    profile_on = False
    if basic_design_path.exists():
        fm = _parse_front_matter(_read_text(basic_design_path))
        profile_on = fm.get("execution_profile") == "erp_addon"

    active = work_items_dir.exists() or profile_on
    if not active:
        return errors, warnings  # ERP Addon not active, skip validation

    # Check if Gate 5+ (tasks.md exists or Gate 5 approved)
    tasks_exists = (fp / "tasks.md").exists()
    gate_5_approved = approval_status.get(5, False) or approval_status.get("5", False)

    if not tasks_exists and not gate_5_approved:
        return errors, warnings  # Not yet at Gate 5, skip validation

    # Find project root and load policy files
    # Try feature-local first (specs/<feature>/), then memory/ for backward compat
    project_root = _find_project_root(fp)
    mode_policy = _load_yaml_file(fp / "erp_addon_mode_policy.yaml")
    if not mode_policy:
        mode_policy = _load_yaml_file(project_root / "memory" / "erp_addon_mode_policy.yaml")
    taxonomy = _load_yaml_file(fp / "erp_addon_risk_taxonomy.yaml")
    if not taxonomy:
        taxonomy = _load_yaml_file(project_root / "memory" / "erp_addon_risk_taxonomy.yaml")
    known_flags = set((taxonomy.get("risk_flags") or {}).keys())

    # Fallback defaults if policy files are missing
    if not mode_policy:
        mode_policy = {
            "modes": {
                "autopilot": {
                    "checkpoints": {
                        "pre_run": [],
                        "post_run": ["walkthrough_review", "ci_pass", "ops_review"],
                    },
                },
                "confirm": {
                    "checkpoints": {
                        "pre_run": ["plan_review"],
                        "post_run": ["walkthrough_review", "ci_pass", "ops_review"],
                    },
                },
                "validate": {
                    "checkpoints": {
                        "pre_run": ["design_diff_review", "plan_review"],
                        "post_run": ["walkthrough_review", "ci_pass", "ops_review"],
                    },
                },
            },
            "rules": [
                {"if_any_risk_flags": ["authz", "sod", "audit_log", "pii", "accounting_calc", "inventory_valuation"], "mode": "validate"},
                {"if_any_risk_flags": ["db_schema", "data_migration", "update_integration", "cross_module"], "mode": "validate"},
                {"if_any_risk_flags": ["new_api", "contract_change", "performance_sensitive"], "mode": "confirm"},
                {"if_any_risk_flags": ["ui_only", "message_only", "test_only", "logging_only"], "mode": "autopilot"},
            ],
            "overrides": {"require_reason_when_override": True},
        }

    # Validate work_items/ directory exists
    if not work_items_dir.exists():
        errors.append((
            "WI_DIR_MISSING",
            "work_items/ is required after Gate5 for ERP addon execution tracking.",
            [],
        ))
        return errors, warnings

    # Find Work Item files
    wi_files = sorted(work_items_dir.glob("WI-*.md"))
    wi_files = [f for f in wi_files if not f.name.endswith(".approval.md")]

    if not wi_files:
        errors.append((
            "WI_SCHEMA_INVALID",
            "No Work Item files found (WI-*.md) in work_items/.",
            [],
        ))
        return errors, warnings

    # Load state.yaml
    state_path = fp / "state" / "state.yaml"
    if not state_path.exists():
        errors.append((
            "STATE_MISSING",
            "state/state.yaml is required after Gate5.",
            [],
        ))
        state = {}
    else:
        state = _load_yaml_file(state_path)

    # Build set of WI IDs from state and files
    state_wis: set[str] = set()
    state_wi_status: dict[str, str] = {}
    state_wi_mode: dict[str, str] = {}
    for sw in (state.get("work_items") or []):
        if isinstance(sw, dict) and sw.get("wi_id"):
            state_wis.add(sw["wi_id"])
            state_wi_status[sw["wi_id"]] = sw.get("status", "pending")
            state_wi_mode[sw["wi_id"]] = sw.get("mode", "autopilot")

    file_wi_ids: set[str] = set()
    wi_mode_map: dict[str, str] = {}  # wi_id -> mode from WI file
    wi_file_map: dict[str, Path] = {}  # wi_id -> WI file path

    # Validate each Work Item
    for wip in wi_files:
        md_text = _read_text(wip)
        fm = _parse_front_matter(md_text)
        body = _extract_body(md_text)

        # Check required fields (github.issue_number is optional — present when synced from GitHub Issues)
        required_fields = ["wi_id", "title", "mode", "risk_flags", "complexity"]
        # If synced from GitHub Issues via stride_wi_sync, 'github' block is present
        is_github_synced = "github" in fm
        missing = [k for k in required_fields if k not in fm]
        if missing:
            errors.append((
                "WI_SCHEMA_INVALID",
                f"{wip.name}: missing required fields {missing}",
                [],
            ))
            continue

        wi_id = fm.get("wi_id")
        mode = fm.get("mode")
        complexity = fm.get("complexity")
        risk_flags = fm.get("risk_flags") or []

        if wi_id:
            file_wi_ids.add(wi_id)
            wi_mode_map[wi_id] = mode
            wi_file_map[wi_id] = wip


        # Validate mode value
        if mode not in MODE_ORDER:
            errors.append((
                "WI_MODE_INVALID",
                f"{wip.name}: invalid mode '{mode}'. Must be autopilot, confirm, or validate.",
                [],
            ))

        # Validate complexity value
        if complexity not in ("low", "medium", "high"):
            errors.append((
                "WI_SCHEMA_INVALID",
                f"{wip.name}: invalid complexity '{complexity}'. Must be low, medium, or high.",
                [],
            ))

        # Validate risk_flags against taxonomy
        if known_flags:
            bad_flags = [f for f in risk_flags if f not in known_flags]
            if bad_flags:
                errors.append((
                    "WI_RISK_FLAG_INVALID",
                    f"{wip.name}: unknown risk_flags {bad_flags}",
                    list(known_flags),
                ))

        # Validate Spec Links presence and non-empty values
        # GitHub-synced WIs use Intent/Scope/Plan sections instead of Spec Links/DoD
        spec_link_patterns = {
            "UI": r"^\s*-\s*UI:\s*(.+)$",
            "IO": r"^\s*-\s*IO:\s*(.+)$",
            "API/電文": r"^\s*-\s*API/電文:\s*(.+)$",
            "MSG": r"^\s*-\s*MSG:\s*(.+)$",
            "TEST": r"^\s*-\s*TEST:\s*(.+)$",
        }
        if not is_github_synced:
            # Traditional WI files require Spec Links
            missing_links = []
            for label, pattern in spec_link_patterns.items():
                match = re.search(pattern, body, flags=re.MULTILINE)
                if not match or not match.group(1).strip():
                    missing_links.append(label)
            if missing_links:
                errors.append((
                    "WI_SCHEMA_INVALID",
                    f"{wip.name}: missing Spec Links {missing_links}",
                    [],
                ))
        else:
            # GitHub-synced WIs: require Intent and Scope sections instead
            has_intent = bool(re.search(r'^#\s*Intent', body, re.MULTILINE))
            has_scope = bool(re.search(r'^#\s*Scope', body, re.MULTILINE))
            if not has_intent or not has_scope:
                missing_sections = []
                if not has_intent:
                    missing_sections.append("Intent")
                if not has_scope:
                    missing_sections.append("Scope")
                errors.append((
                    "WI_SCHEMA_INVALID",
                    f"{wip.name}: missing required sections {missing_sections} (GitHub-synced WI)",
                    [],
                ))

        # Validate Spec Links file existence (SSoT integrity)
        for label, pattern in spec_link_patterns.items():
            match = re.search(pattern, body, flags=re.MULTILINE)
            if match and match.group(1).strip():
                link_value = match.group(1).strip()
                # Skip if it's a placeholder like "N/A" or "-"
                if link_value.lower() in ("n/a", "-", "なし", "none", "該当なし"):
                    continue
                # Extract file paths from the link value (comma or space separated)
                paths = re.split(r"[,\s]+", link_value)
                for p in paths:
                    p = p.strip()
                    if not p or p.lower() in ("n/a", "-", "なし", "none"):
                        continue
                    # Check relative to feature path first, then project root
                    candidate_paths = [
                        fp / p,
                        project_root / p,
                        fp / "contracts" / p,
                        fp / "implementation-details" / p,
                    ]
                    exists = any(cp.exists() for cp in candidate_paths)
                    if not exists:
                        warnings.append((
                            "SPEC_LINK_NOT_FOUND",
                            f"{wip.name}: Spec Link '{label}' references '{p}' but file not found",
                            [f"Checked: {fp}, {project_root}"],
                        ))

        # Validate spec_refs file existence
        spec_refs = fm.get("spec_refs") or []
        for ref in spec_refs:
            if not isinstance(ref, str):
                continue
            ref_value = ref.strip()
            if not ref_value:
                continue
            if ref_value.lower() in ("n/a", "-", "なし", "none", "該当なし"):
                continue
            ref_path = Path(ref_value)
            candidate_paths = []
            if ref_path.is_absolute():
                candidate_paths = [ref_path]
            else:
                candidate_paths = [
                    fp / ref_value,
                    project_root / ref_value,
                    fp / "contracts" / ref_value,
                    fp / "implementation-details" / ref_value,
                ]
            if not any(cp.exists() for cp in candidate_paths):
                warnings.append((
                    "SPEC_REF_NOT_FOUND",
                    f"{wip.name}: spec_refs '{ref_value}' not found",
                    [f"Checked: {', '.join(str(cp) for cp in candidate_paths)}"],
                ))

        # Validate DoD checklist presence
        if not is_github_synced:
            # Traditional WI files require Japanese DoD items
            dod_items = [
                "Spec差分レビュー完了",
                "実装完了（影響箇所列挙）",
                "テスト追加/更新（契約＋例外＋メッセージ）",
                "walkthrough（変更点・理由・検証手順）レビュー完了",
                "CI合格",
                "Ops更新（輸送/rollback/監視）",
            ]
            missing_dod = [item for item in dod_items if item not in body]
            if missing_dod:
                errors.append((
                    "WI_SCHEMA_INVALID",
                    f"{wip.name}: missing DoD items {missing_dod}",
                    [],
                ))
        else:
            # GitHub-synced WIs: check for Risk Flags and Acceptance Criteria sections
            has_risk = bool(re.search(r'^##?\s*Risk Flags', body, re.MULTILINE))
            has_ac = bool(re.search(r'^#\s*Acceptance Criteria', body, re.MULTILINE))
            if not has_risk or not has_ac:
                missing_sections = []
                if not has_risk:
                    missing_sections.append("Risk Flags")
                if not has_ac:
                    missing_sections.append("Acceptance Criteria")
                warnings.append((
                    "WI_DOD_INCOMPLETE",
                    f"{wip.name}: missing sections {missing_sections} (GitHub-synced WI)",
                    [],
                ))

        # Check state.yaml consistency: WI file must be in state
        if state_path.exists() and wi_id and wi_id not in state_wis:
            errors.append((
                "STATE_WI_MISMATCH",
                f"state.yaml is missing wi_id '{wi_id}'",
                [],
            ))

        # Critical tier restrictions on autopilot
        if coverage_tier == "critical" and mode == "autopilot":
            if not set(risk_flags).issubset(LOW_RISK_FLAGS):
                errors.append((
                    "AUTOPILOT_FORBIDDEN_BY_TIER",
                    f"{wi_id}: critical tier forbids autopilot for risk_flags={risk_flags}",
                    [f"Allowed for autopilot in critical tier: {list(LOW_RISK_FLAGS)}"],
                ))

        # Check mode against policy recommendation
        if mode in MODE_ORDER:
            recommended = _get_recommended_mode(list(risk_flags), mode_policy)
            if MODE_ORDER.get(mode, 0) < MODE_ORDER.get(recommended, 0):
                override = fm.get("mode_override") or {}
                reason = override.get("reason")
                if not reason:
                    errors.append((
                        "MODE_OVERRIDE_REASON_MISSING",
                        f"{wi_id}: mode '{mode}' is weaker than recommended '{recommended}' and no override reason provided.",
                        ["Add mode_override.reason field with justification"],
                    ))
                else:
                    # With reason: emit as WARNING, not error
                    warnings.append((
                        "WI_MODE_POLICY_VIOLATION",
                        f"{wi_id}: mode '{mode}' weaker than recommended '{recommended}'.",
                        [f"override.reason: {reason}"],
                    ))

        # Check pre-run approval for confirm/validate modes when in_progress or done
        status = state_wi_status.get(wi_id, "pending")
        has_runs = (fp / "runs" / str(wi_id)).exists() if wi_id else False

        pre_required = _required_checkpoints(mode_policy, mode, "pre_run")
        need_pre = bool(pre_required) and (status in ("in_progress", "done") or has_runs)
        if need_pre:
            approval_file = work_items_dir / f"{wip.stem}.approval.md"
            if not approval_file.exists():
                errors.append((
                    "WI_APPROVAL_PENDING",
                    f"{wi_id}: missing approval file {approval_file.name}",
                    [],
                ))
            else:
                missing_approvals = _check_pre_run_approval(approval_file, pre_required)
                for ma in missing_approvals:
                    if ma == "approval_file_missing":
                        continue
                    errors.append((
                        "WI_APPROVAL_PENDING",
                        f"{wi_id}: approval '{ma}' not completed in {approval_file.name}",
                        [],
                    ))

    # Check reverse consistency: state.yaml should not have orphan WIs
    if state_path.exists():
        orphan_wis = state_wis - file_wi_ids
        for orphan in orphan_wis:
            errors.append((
                "STATE_WI_MISMATCH",
                f"state.yaml contains wi_id '{orphan}' but no WI file exists",
                [],
            ))

    # Validate Run evidence and post-run approvals for done Work Items
    for sw in (state.get("work_items") or []):
        if not isinstance(sw, dict):
            continue
        wi_id = sw.get("wi_id")
        if sw.get("status") != "done" or not wi_id:
            continue

        mode = wi_mode_map.get(wi_id, sw.get("mode", "autopilot"))

        wi_run_dir = fp / "runs" / str(wi_id)
        if not wi_run_dir.exists():
            errors.append((
                "RUN_MISSING",
                f"{wi_id}: status is 'done' but no runs/ directory found",
                [],
            ))
            continue

        run_dirs = sorted([p for p in wi_run_dir.glob("RUN-*") if p.is_dir()])
        if not run_dirs:
            errors.append((
                "RUN_MISSING",
                f"{wi_id}: status is 'done' but no RUN-* directories found",
                [],
            ))
            continue

        if len(run_dirs) > 1:
            errors.append((
                "RUN_MULTIPLE",
                f"{wi_id}: multiple RUN-* directories found ({len(run_dirs)}). Each Work Item must complete in a single Run.",
                [],
            ))

        # Check latest run for required evidence
        latest_run = run_dirs[-1]

        if not (latest_run / "walkthrough.md").exists():
            errors.append((
                "WALKTHROUGH_MISSING",
                f"{wi_id}: missing walkthrough.md in {latest_run.name}",
                [],
            ))

        if coverage_tier in ("critical", "standard"):
            if not (latest_run / "test_results.md").exists():
                errors.append((
                    "TEST_RESULTS_MISSING",
                    f"{wi_id}: missing test_results.md in {latest_run.name} (required for {coverage_tier} tier)",
                    [],
                ))

        # Check post-run approval for ALL modes (including autopilot)
        post_required = _required_checkpoints(mode_policy, mode, "post_run")
        if post_required:
            wi_file = wi_file_map.get(wi_id)
            if not wi_file:
                errors.append((
                    "WI_APPROVAL_PENDING",
                    f"{wi_id}: missing WI file to resolve approval file",
                    [],
                ))
            else:
                approval_file = work_items_dir / f"{wi_file.stem}.approval.md"
                if not approval_file.exists():
                    errors.append((
                        "WI_APPROVAL_PENDING",
                        f"{wi_id}: missing post-run approval file {approval_file.name}",
                        [],
                    ))
                else:
                    missing_post_run = _check_post_run_approval(approval_file, post_required)
                    for ma in missing_post_run:
                        if ma == "approval_file_missing":
                            continue
                        errors.append((
                            "WI_APPROVAL_PENDING",
                            f"{wi_id}: post-run approval '{ma}' not completed in {approval_file.name}",
                            [],
                        ))

    # Check Ops Pack requirements (ERP addon requires full ops pack)
    ops_dir = fp / "ops"
    missing_ops = [r for r in FULL_OPS_PACK if not (ops_dir / r).exists()]
    if missing_ops:
        errors.append((
            "OPS_PACK_MISSING",
            f"ERP addon requires full ops pack: missing {missing_ops}",
            [],
        ))

    return errors, warnings


# Backward compatibility wrapper
def validate_erp_addon_execution_tracking_compat(
    feature_path: str | Path,
    approval_status: dict[str | int, bool],
    coverage_tier: str,
) -> list[tuple[str, str, list[str]]]:
    """
    Backward-compatible wrapper that returns only errors.
    Warnings are included with code prefix 'WARN_'.
    """
    errors, warnings = validate_erp_addon_execution_tracking(
        feature_path, approval_status, coverage_tier
    )
    # Add warnings with WARN_ prefix for visibility
    for code, msg, details in warnings:
        errors.append((f"WARN_{code}", msg, details))
    return errors


def main():
    """Self-test entry point."""
    import sys
    import tempfile
    import shutil

    if len(sys.argv) < 2:
        print("Usage: erp_addon_exec_tracking.py <feature_path> [coverage_tier]")
        print("       erp_addon_exec_tracking.py --test")
        sys.exit(1)

    if sys.argv[1] == "--test":
        print("Running self-tests...")

        # Test 1: Non-existent path returns empty
        errors, warnings = validate_erp_addon_execution_tracking(
            "/nonexistent/path",
            {},
            "standard",
        )
        assert errors == [], f"Test 1 failed: expected empty errors, got {errors}"
        assert warnings == [], f"Test 1 failed: expected empty warnings, got {warnings}"
        print("  Test 1 passed: non-existent path returns empty")

        if yaml is None:
            print("  PyYAML not available; skipping YAML-dependent tests.")
            sys.exit(0)

        # Test 2: Create minimal ERP addon structure and validate
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # Create memory/ for policies
            (tmpdir / "memory").mkdir()
            # Create specs/test_feature/
            feature_dir = tmpdir / "specs" / "test_feature"
            feature_dir.mkdir(parents=True)
            # Create work_items/
            (feature_dir / "work_items").mkdir()
            # Create tasks.md (Gate 5+)
            (feature_dir / "tasks.md").write_text("# Tasks\n")
            # Create ops pack (avoid OPS_PACK_MISSING for unrelated tests)
            ops_dir = feature_dir / "ops"
            ops_dir.mkdir()
            for name in FULL_OPS_PACK:
                (ops_dir / name).write_text("# ops\n")

            # Should get WI_SCHEMA_INVALID (no WI files)
            errors, warnings = validate_erp_addon_execution_tracking(
                str(feature_dir), {5: True}, "standard"
            )
            assert any(e[0] == "WI_SCHEMA_INVALID" for e in errors), \
                f"Test 2 failed: expected WI_SCHEMA_INVALID, got {[e[0] for e in errors]}"
            print("  Test 2 passed: WI_SCHEMA_INVALID for empty work_items/")

            # Test 3: Add WI file but no state.yaml
            wi_file = feature_dir / "work_items" / "WI-TEST-001.md"
            wi_file.write_text("""---
wi_id: WI-TEST-001
title: Test Work Item
complexity: low
mode: autopilot
risk_flags: ["ui_only"]
---
# Intent

## Spec Links (Single source of truth)
- UI: ui.md
- IO: io.md
- API/電文: api.md
- MSG: msg.md
- TEST: tests.md

## Definition of Done
- [ ] Spec差分レビュー完了
- [ ] 実装完了（影響箇所列挙）
- [ ] テスト追加/更新（契約＋例外＋メッセージ）
- [ ] walkthrough（変更点・理由・検証手順）レビュー完了
- [ ] CI合格
- [ ] Ops更新（輸送/rollback/監視）
""")
            errors, warnings = validate_erp_addon_execution_tracking(
                str(feature_dir), {5: True}, "standard"
            )
            assert any(e[0] == "STATE_MISSING" for e in errors), \
                f"Test 3 failed: expected STATE_MISSING, got {[e[0] for e in errors]}"
            print("  Test 3 passed: STATE_MISSING when state.yaml absent")

            # Test 4: Add state.yaml with WI, check consistency
            (feature_dir / "state").mkdir()
            (feature_dir / "state" / "state.yaml").write_text("""
work_items:
  - wi_id: WI-TEST-001
    status: pending
  - wi_id: WI-ORPHAN
    status: pending
""")
            errors, warnings = validate_erp_addon_execution_tracking(
                str(feature_dir), {5: True}, "standard"
            )
            # Should detect orphan WI in state
            assert any("WI-ORPHAN" in e[1] for e in errors if e[0] == "STATE_WI_MISMATCH"), \
                f"Test 4 failed: expected orphan WI detection, got {errors}"
            print("  Test 4 passed: STATE_WI_MISMATCH for orphan WI in state")

            # Test 5: Check ops pack required for ERP addon
            shutil.rmtree(ops_dir)
            wi_validate = feature_dir / "work_items" / "WI-TEST-002.md"
            wi_validate.write_text("""---
wi_id: WI-TEST-002
title: Validate Mode WI
complexity: high
mode: validate
risk_flags: ["authz"]
---
# Intent

## Spec Links (Single source of truth)
- UI: ui.md
- IO: io.md
- API/電文: api.md
- MSG: msg.md
- TEST: tests.md

## Definition of Done
- [ ] Spec差分レビュー完了
- [ ] 実装完了（影響箇所列挙）
- [ ] テスト追加/更新（契約＋例外＋メッセージ）
- [ ] walkthrough（変更点・理由・検証手順）レビュー完了
- [ ] CI合格
- [ ] Ops更新（輸送/rollback/監視）
""")
            (feature_dir / "state" / "state.yaml").write_text("""
work_items:
  - wi_id: WI-TEST-001
    status: pending
  - wi_id: WI-TEST-002
    status: pending
""")
            errors, warnings = validate_erp_addon_execution_tracking(
                str(feature_dir), {5: True}, "standard"
            )
            ops_errors = [e for e in errors if e[0] == "OPS_PACK_MISSING"]
            assert len(ops_errors) > 0, f"Test 5 failed: expected OPS_PACK_MISSING, got {[e[0] for e in errors]}"
            assert "hypercare_runbook.md" in str(ops_errors), \
                f"Test 5 failed: expected hypercare_runbook.md in ops pack, got {ops_errors}"
            print("  Test 5 passed: OPS_PACK_MISSING requires full ops pack for ERP addon")

            # Restore ops pack for remaining tests
            ops_dir.mkdir()
            for name in FULL_OPS_PACK:
                (ops_dir / name).write_text("# ops\n")

            # Test 6: SPEC_LINK_NOT_FOUND warning for non-existent file
            # WI-TEST-001 references ui.md, io.md etc. which don't exist
            errors, warnings = validate_erp_addon_execution_tracking(
                str(feature_dir), {5: True}, "standard"
            )
            spec_link_warnings = [w for w in warnings if w[0] == "SPEC_LINK_NOT_FOUND"]
            assert len(spec_link_warnings) > 0, \
                f"Test 6 failed: expected SPEC_LINK_NOT_FOUND warnings, got {[w[0] for w in warnings]}"
            print("  Test 6 passed: SPEC_LINK_NOT_FOUND for non-existent Spec Links")

            # Test 7: SPEC_REF_NOT_FOUND warning for non-existent spec_refs
            wi_with_refs = feature_dir / "work_items" / "WI-TEST-003.md"
            wi_with_refs.write_text("""---
wi_id: WI-TEST-003
title: WI with spec_refs
complexity: low
mode: autopilot
risk_flags: ["ui_only"]
spec_refs:
  - "nonexistent_spec.md"
---
# Intent

## Spec Links (Single source of truth)
- UI: N/A
- IO: N/A
- API/電文: N/A
- MSG: N/A
- TEST: N/A

## Definition of Done
- [ ] Spec差分レビュー完了
- [ ] 実装完了（影響箇所列挙）
- [ ] テスト追加/更新（契約＋例外＋メッセージ）
- [ ] walkthrough（変更点・理由・検証手順）レビュー完了
- [ ] CI合格
- [ ] Ops更新（輸送/rollback/監視）
""")
            (feature_dir / "state" / "state.yaml").write_text("""
work_items:
  - wi_id: WI-TEST-001
    status: pending
  - wi_id: WI-TEST-002
    status: pending
  - wi_id: WI-TEST-003
    status: pending
""")
            errors, warnings = validate_erp_addon_execution_tracking(
                str(feature_dir), {5: True}, "standard"
            )
            spec_ref_warnings = [w for w in warnings if w[0] == "SPEC_REF_NOT_FOUND"]
            assert len(spec_ref_warnings) > 0, \
                f"Test 7 failed: expected SPEC_REF_NOT_FOUND warnings, got {[w[0] for w in warnings]}"
            print("  Test 7 passed: SPEC_REF_NOT_FOUND for non-existent spec_refs")

            # Test 8: RUN_MULTIPLE error for multiple RUN-* directories
            (feature_dir / "state" / "state.yaml").write_text("""
work_items:
  - wi_id: WI-TEST-001
    status: done
  - wi_id: WI-TEST-002
    status: pending
  - wi_id: WI-TEST-003
    status: pending
""")
            runs_dir = feature_dir / "runs" / "WI-TEST-001"
            runs_dir.mkdir(parents=True)
            (runs_dir / "RUN-001").mkdir()
            (runs_dir / "RUN-001" / "walkthrough.md").write_text("# Walkthrough\n")
            (runs_dir / "RUN-002").mkdir()
            (runs_dir / "RUN-002" / "walkthrough.md").write_text("# Walkthrough\n")
            errors, warnings = validate_erp_addon_execution_tracking(
                str(feature_dir), {5: True}, "standard"
            )
            run_multiple_errors = [e for e in errors if e[0] == "RUN_MULTIPLE"]
            assert len(run_multiple_errors) > 0, \
                f"Test 8 failed: expected RUN_MULTIPLE error, got {[e[0] for e in errors]}"
            print("  Test 8 passed: RUN_MULTIPLE for multiple RUN-* directories")

        print("All self-tests passed.")
        sys.exit(0)

    feature_path = sys.argv[1]
    coverage_tier = sys.argv[2] if len(sys.argv) > 2 else "standard"

    errors, warnings = validate_erp_addon_execution_tracking(
        feature_path,
        {5: True},  # Assume Gate 5 approved for standalone testing
        coverage_tier,
    )

    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for code, msg, details in warnings:
            print(f"  - {code}: {msg}")
            for d in details:
                print(f"      {d}")

    if not errors:
        print("OK: ERP Addon execution tracking validation passed")
        sys.exit(0)

    print(f"Errors ({len(errors)}):")
    for code, msg, details in errors:
        print(f"  - {code}: {msg}")
        for d in details:
            print(f"      {d}")
    sys.exit(1)


if __name__ == "__main__":
    main()
