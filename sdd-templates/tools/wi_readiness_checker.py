#!/usr/bin/env python3
"""
Work Item Readiness Checker

Checks whether a specific Work Item is ready to execute its Run.
Validates gate approval, WI definition, mode policy, pre-run approvals,
cross-feature dependencies, ops pack, and state consistency.

Usage:
    python3 wi_readiness_checker.py <feature_dir> <wi_id> [--verbose]

Exit codes:
    0 = READY (may have warnings)
    1 = NOT READY (has at least one FAIL)
    2 = ERROR (missing arguments, file parse error, etc.)
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

from stride_shared_lib import extract_first_yaml_block


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


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """Result of a single readiness check."""
    status: str  # "PASS", "FAIL", "WARN"
    message: str
    details: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# File helpers (following erp_addon_exec_tracking.py patterns)
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    """Read file as UTF-8 text."""
    return path.read_text(encoding="utf-8")


def _parse_front_matter(md_text: str) -> dict[str, Any]:
    """Parse YAML front matter from markdown file."""
    if not md_text.startswith("---"):
        return {}
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


def _load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file safely."""
    if yaml is None or not path.exists():
        return {}
    try:
        return yaml.safe_load(_read_text(path)) or {}
    except Exception:
        return {}


def _parse_canonical_yaml(md_text: str) -> dict[str, Any]:
    """Parse the Canonical YAML code block from basic_design.md.

    Extracts YAML from the first ```yaml ... ``` fenced code block
    (the '# 0. Canonical Basic Design (YAML)' section). Returns an empty
    dict on any failure so callers can safely ``.get(...)`` the result.
    """
    if yaml is None:
        return {}
    block = extract_first_yaml_block(md_text)
    if block is None:
        return {}
    try:
        return yaml.safe_load(block) or {}
    except Exception:
        return {}


def _find_project_root(feature_path: Path) -> Path:
    """Find project root by looking for memory/ or sdd-templates/ directory."""
    current = feature_path.resolve()
    for _ in range(5):
        if (current / "memory").exists() or (current / "sdd-templates").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return feature_path.resolve().parent.parent


def _get_recommended_mode(risk_flags: list[str], mode_policy: dict[str, Any]) -> str:
    """Determine the recommended mode based on risk_flags and mode_policy rules.

    Supports both ``rules`` array format (fallback) and ``risk_flag_mapping``
    dict format (shared/policies/mode_policy.yaml).
    """
    best = "autopilot"

    # Format 1: risk_flag_mapping (mode -> list of flags)
    rfm = mode_policy.get("risk_flag_mapping")
    if rfm and isinstance(rfm, dict):
        flag_set = set(risk_flags)
        for mode_name, flags_list in rfm.items():
            if not isinstance(flags_list, list):
                continue
            if flag_set.intersection(set(flags_list)):
                if MODE_ORDER.get(mode_name, 0) > MODE_ORDER.get(best, 0):
                    best = mode_name
        return best

    # Format 2: rules array (legacy / fallback)
    for rule in mode_policy.get("rules", []):
        flags = set(rule.get("if_any_risk_flags", []))
        if flags.intersection(set(risk_flags)):
            candidate = rule.get("mode", "autopilot")
            if MODE_ORDER.get(candidate, 0) > MODE_ORDER.get(best, 0):
                best = candidate
    return best


def _apply_autonomy_bias(
    recommended_mode: str,
    bias: str,
    mode_policy: dict[str, Any],
    coverage_tier: str = "standard",
) -> str:
    """Apply autonomy bias shift to the recommended mode.

    After shifting, enforce tier_mode_minimum — the shifted mode must never be
    weaker than the tier minimum.
    """
    if bias == "balanced" or not bias:
        return recommended_mode

    # Look up mode_shift from policy
    ab_section = mode_policy.get("autonomy_bias") or {}
    bias_def = ab_section.get(bias) or {}
    mode_shift = bias_def.get("mode_shift")

    # Fallback: hardcoded shifts when policy section is absent
    if mode_shift is None and bias == "autonomous":
        mode_shift = {"autopilot": "autopilot", "confirm": "autopilot", "validate": "confirm"}
    elif mode_shift is None and bias == "controlled":
        mode_shift = {"autopilot": "confirm", "confirm": "validate", "validate": "validate"}
    elif mode_shift is None:
        return recommended_mode

    shifted = mode_shift.get(recommended_mode, recommended_mode)

    # Enforce tier_mode_minimum
    tier_min_section = mode_policy.get("tier_mode_minimum") or {}
    tier_min = tier_min_section.get(coverage_tier, "autopilot")
    if MODE_ORDER.get(shifted, 0) < MODE_ORDER.get(tier_min, 0):
        shifted = tier_min

    return shifted


def _required_checkpoints(mode_policy: dict[str, Any], mode: str, phase: str) -> list[str]:
    """Return required checkpoint names for a given mode and phase (pre_run/post_run)."""
    modes = mode_policy.get("modes") or {}
    mode_def = modes.get(mode) or {}
    checkpoints = mode_def.get("checkpoints") or {}
    required = checkpoints.get(phase) or []
    return list(required)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_gate5_approved(feature_path: Path) -> CheckResult:
    """Check 1: Is Gate 5 approved in APPROVAL.md?"""
    approval_path = feature_path / "APPROVAL.md"
    if not approval_path.exists():
        return CheckResult("FAIL", "APPROVAL.md not found")

    txt = _read_text(approval_path)

    # Look for Gate 5 section with checked boxes
    # Extract everything from "## Gate 5" until next "## " top-level heading or "---" divider or EOF
    # Use \n## (?!#) to avoid matching ### subsections within the Gate 5 block
    gate5_match = re.search(
        r"##\s*Gate\s*5[^\n]*\n(.*?)(?=\n---|\n## (?!#)|\Z)",
        txt,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not gate5_match:
        return CheckResult("FAIL", "Gate 5 section not found in APPROVAL.md")

    gate5_section = gate5_match.group(1)

    # Check that all checkboxes are checked
    unchecked = re.findall(r"\[\s\]", gate5_section)
    checked = re.findall(r"\[x\]", gate5_section, flags=re.IGNORECASE)

    if not checked:
        return CheckResult("FAIL", "Gate 5 has no checked items")
    if unchecked:
        return CheckResult("FAIL", f"Gate 5 has {len(unchecked)} unchecked item(s)")

    # Check for approver (non-placeholder)
    approver_match = re.search(r"承認者:\s*(.+)", gate5_section)
    if not approver_match or approver_match.group(1).strip() in ("___________", ""):
        return CheckResult("FAIL", "Gate 5 approver not set")

    return CheckResult("PASS", "Gate 5 approved")


def check_wi_definition(feature_path: Path, wi_id: str) -> tuple[CheckResult, dict[str, Any] | None, Path | None]:
    """Check 2: Does the WI file exist with required fields?

    Returns (result, front_matter_dict_or_None, wi_file_path_or_None).
    """
    work_items_dir = feature_path / "work_items"
    if not work_items_dir.exists():
        return CheckResult("FAIL", "work_items/ directory not found"), None, None

    # Find the WI file matching wi_id
    # Support both traditional WI-*.md and GitHub-synced files (e.g., SU-1.md)
    wi_files = sorted(work_items_dir.glob("*.md"))
    wi_files = [f for f in wi_files if not f.name.endswith(".approval.md")]

    target_file = None
    target_fm = None
    for wip in wi_files:
        md_text = _read_text(wip)
        fm = _parse_front_matter(md_text)
        if fm.get("wi_id") == wi_id:
            target_file = wip
            target_fm = fm
            break

    if target_file is None:
        available = []
        for wip in wi_files:
            fm = _parse_front_matter(_read_text(wip))
            if fm.get("wi_id"):
                available.append(fm["wi_id"])
        detail = f"Available WIs: {available}" if available else "No WI files found"
        return CheckResult("FAIL", f"WI file for '{wi_id}' not found", [detail]), None, None

    # Check required fields
    # GitHub-synced WIs (via stride_wi_sync) have 'github' block in front-matter
    is_github_synced = "github" in target_fm
    required_fields = ["wi_id", "mode", "risk_flags", "complexity"]
    if not is_github_synced:
        required_fields.append("spec_refs")  # GitHub-synced WIs may omit spec_refs
    missing = [k for k in required_fields if k not in target_fm]
    if missing:
        return (
            CheckResult("FAIL", f"Missing required fields: {missing}"),
            target_fm,
            target_file,
        )

    mode = target_fm.get("mode", "")
    risk_flags = target_fm.get("risk_flags") or []

    # Validate mode value
    if mode not in MODE_ORDER:
        return (
            CheckResult("FAIL", f"Invalid mode '{mode}' (must be autopilot/confirm/validate)"),
            target_fm,
            target_file,
        )

    # Validate complexity value
    complexity = target_fm.get("complexity", "")
    if complexity not in ("low", "medium", "high"):
        return (
            CheckResult("FAIL", f"Invalid complexity '{complexity}' (must be low/medium/high)"),
            target_fm,
            target_file,
        )

    flags_str = ", ".join(risk_flags) if risk_flags else "none"
    return (
        CheckResult("PASS", f"WI definition valid (mode={mode}, risk=[{flags_str}])"),
        target_fm,
        target_file,
    )


def check_mode_policy(
    feature_path: Path,
    fm: dict[str, Any],
    mode_policy: dict[str, Any],
    autonomy_bias: str = "balanced",
    coverage_tier: str = "standard",
) -> CheckResult:
    """Check 3: Is the WI mode compliant with risk_flags per mode policy?

    Applies autonomy_bias shift to the recommended mode before comparison.
    """
    mode = fm.get("mode", "autopilot")
    risk_flags = fm.get("risk_flags") or []

    recommended = _get_recommended_mode(list(risk_flags), mode_policy)
    recommended = _apply_autonomy_bias(recommended, autonomy_bias, mode_policy, coverage_tier)

    bias_label = f" (bias: {autonomy_bias})" if autonomy_bias != "balanced" else ""

    if MODE_ORDER.get(mode, 0) >= MODE_ORDER.get(recommended, 0):
        return CheckResult("PASS", f"Mode policy compliant{bias_label}")

    # Mode is weaker than recommended - check for override reason
    override = fm.get("mode_override") or {}
    reason = override.get("reason")
    if reason:
        return CheckResult(
            "WARN",
            f"Mode '{mode}' weaker than recommended '{recommended}' (override: {reason}){bias_label}",
        )

    return CheckResult(
        "FAIL",
        f"Mode '{mode}' weaker than recommended '{recommended}', no override reason provided{bias_label}",
    )


def check_pre_run_approvals(
    feature_path: Path,
    wi_id: str,
    wi_file: Path,
    fm: dict[str, Any],
    mode_policy: dict[str, Any],
) -> CheckResult:
    """Check 4: For confirm/validate modes, are pre-run approvals complete?"""
    mode = fm.get("mode", "autopilot")
    pre_required = _required_checkpoints(mode_policy, mode, "pre_run")

    if not pre_required:
        return CheckResult("PASS", "No pre-run approvals required (autopilot mode)")

    # Check the WI approval file
    work_items_dir = feature_path / "work_items"
    approval_file = work_items_dir / f"{wi_file.stem}.approval.md"

    if not approval_file.exists():
        return CheckResult(
            "WARN",
            f"Pre-run approval file not found ({approval_file.name})",
            [f"Required checkpoints: {pre_required}"],
        )

    txt = _read_text(approval_file)

    pending = []
    completed = []
    for req in pre_required:
        pattern = rf"\[x\].*{re.escape(req)}"
        if re.search(pattern, txt, flags=re.IGNORECASE):
            completed.append(req)
        else:
            pending.append(req)

    if not pending:
        return CheckResult("PASS", f"Pre-run approvals complete ({', '.join(completed)})")

    if completed:
        return CheckResult(
            "WARN",
            f"Pre-run approval: {', '.join(pending)} pending",
            [f"Completed: {', '.join(completed)}"],
        )

    return CheckResult(
        "WARN",
        f"Pre-run approval: {', '.join(pending)} pending",
    )


def check_cross_feature_dependencies(
    feature_path: Path,
    wi_id: str,
    fm: dict[str, Any],
) -> CheckResult:
    """Check 5: Are cross-feature dependencies satisfied?"""
    project_root = _find_project_root(feature_path)
    manifest_path = project_root / "cross_team_dependency_manifest.yaml"

    if not manifest_path.exists():
        # Also check in memory/ directory
        manifest_path = project_root / "memory" / "cross_team_dependency_manifest.yaml"
        if not manifest_path.exists():
            return CheckResult("PASS", "No cross-feature dependencies")

    manifest = _load_yaml_file(manifest_path)
    if not manifest:
        return CheckResult("PASS", "No cross-feature dependencies")

    # Look for dependencies that reference this WI or this feature
    dependencies = manifest.get("dependencies") or []
    if not dependencies:
        return CheckResult("PASS", "No cross-feature dependencies")

    feature_name = feature_path.name
    blocking = []

    for dep in dependencies:
        if not isinstance(dep, dict):
            continue
        # Check if this WI is the dependent (blocked by something)
        dependent = dep.get("dependent") or {}
        dep_feature = dependent.get("feature", "")
        dep_wi = dependent.get("wi_id", "")

        if dep_feature == feature_name and (dep_wi == wi_id or dep_wi == ""):
            # This WI depends on another feature's WI
            provider = dep.get("provider") or {}
            status = dep.get("status", "pending")
            if status not in ("resolved", "done", "completed"):
                provider_desc = (
                    f"{provider.get('feature', '?')}/"
                    f"{provider.get('wi_id', '?')}"
                )
                blocking.append(f"{provider_desc} ({status})")

    if blocking:
        return CheckResult(
            "FAIL",
            f"Cross-feature dependencies not satisfied: {', '.join(blocking)}",
        )

    return CheckResult("PASS", "Cross-feature dependencies satisfied")


def check_ops_pack(feature_path: Path) -> CheckResult:
    """Check 6: Are ops pack files present for ERP addons?"""
    # Check if this is an ERP addon (has execution_profile or work_items/)
    basic_design_path = feature_path / "basic_design.md"
    is_erp_addon = False

    if basic_design_path.exists():
        fm = _parse_front_matter(_read_text(basic_design_path))
        is_erp_addon = fm.get("execution_profile") == "erp_addon"

    if not is_erp_addon:
        # Also check if work_items/ exists (implicit ERP addon)
        if not (feature_path / "work_items").exists():
            return CheckResult("PASS", "Not an ERP addon (ops pack not required)")

    ops_dir = feature_path / "ops"
    if not ops_dir.exists():
        return CheckResult("FAIL", "ops/ directory not found (required for ERP addon)")

    present = []
    missing = []
    for name in FULL_OPS_PACK:
        if (ops_dir / name).exists():
            # Derive short label
            label = name.replace("_manifest.yaml", "").replace("_checklist.md", "").replace("_plan.md", "").replace("_runbook.md", "")
            present.append(label)
        else:
            missing.append(name)

    if missing:
        short_missing = [
            n.replace("_manifest.yaml", "").replace("_checklist.md", "").replace("_plan.md", "").replace("_runbook.md", "")
            for n in missing
        ]
        return CheckResult(
            "FAIL",
            f"Ops pack incomplete: missing {short_missing}",
            [f"Missing files: {missing}"],
        )

    return CheckResult(
        "PASS",
        "Ops pack: " + " \u2713 ".join(present) + " \u2713",
    )


def check_state_consistency(
    feature_path: Path,
    wi_id: str,
) -> CheckResult:
    """Check 7: Does state.yaml show this WI as pending or in_progress?"""
    state_path = feature_path / "state" / "state.yaml"
    if not state_path.exists():
        return CheckResult("WARN", "state/state.yaml not found (cannot verify state)")

    state = _load_yaml_file(state_path)
    if not state:
        return CheckResult("WARN", "state/state.yaml is empty or unparseable")

    work_items = state.get("work_items") or []

    # State may be a list of dicts with wi_id/status or a simple list of IDs
    for item in work_items:
        if isinstance(item, dict):
            if item.get("wi_id") == wi_id:
                status = item.get("status", "pending")
                if status in ("pending", "in_progress"):
                    return CheckResult("PASS", f"State: {status} (ready to start)")
                elif status == "done":
                    return CheckResult("FAIL", "State: done (already completed)")
                else:
                    return CheckResult("WARN", f"State: {status} (unrecognized status)")
        elif isinstance(item, str):
            if item == wi_id:
                # Simple list format - no status info, assume pending
                return CheckResult("PASS", "State: listed (no status field, assumed pending)")

    return CheckResult("FAIL", f"WI '{wi_id}' not found in state.yaml")


def check_execution_authority(
    fm: dict[str, Any],
    mode_policy: dict[str, Any],
    autonomy_bias: str = "balanced",
    coverage_tier: str = "standard",
) -> CheckResult:
    """Check 8: Validate WI against execution_authority declaration in mode policy.

    When execution_authority is declared, verify that the WI's mode provides
    sufficient validation scope for gated actions. Uses the same policy-driven
    _get_recommended_mode() and _apply_autonomy_bias() as Check 3 — no
    hardcoded risk flag lists.

    Distinct from Check 3:
    - Check 3: "Is mode >= recommended?" (pure policy compliance)
    - Check 8: "Does mode satisfy execution_authority's validation scope
      requirements?" (authority-aware context reporting)
    """
    ea = mode_policy.get("execution_authority")
    if not ea:
        return CheckResult("PASS", "No execution_authority declared in policy (legacy mode)")

    mode = fm.get("mode", "autopilot")
    risk_flags = fm.get("risk_flags") or []
    gate_mechanism = ea.get("gated", {}).get("gate_mechanism", "stride-lint + phase_gate.py")

    # Use the same policy-driven recommendation as Check 3
    recommended = _get_recommended_mode(list(risk_flags), mode_policy)
    recommended = _apply_autonomy_bias(recommended, autonomy_bias, mode_policy, coverage_tier)

    # When execution_authority is declared, the recommended mode represents
    # the minimum validation scope for gated actions
    if MODE_ORDER.get(mode, 0) < MODE_ORDER.get(recommended, 0):
        override = fm.get("mode_override") or {}
        reason = override.get("reason")
        if reason:
            return CheckResult(
                "WARN",
                f"Execution authority: mode='{mode}' below recommended validation scope "
                f"'{recommended}' (override: {reason}, gate: {gate_mechanism})",
            )
        return CheckResult(
            "FAIL",
            f"Execution authority violation: mode='{mode}' does not satisfy "
            f"validation scope '{recommended}' required for gated actions",
            details=[
                f"Gate mechanism: {gate_mechanism}",
                f"Recommended validation scope: {recommended} (from risk_flags + bias + tier)",
                f"Declared gated actions: {len(ea.get('gated', {}).get('actions', []))}",
                f"Declared prohibited actions: {len(ea.get('prohibited', {}).get('actions', []))}",
                "Per Article XIV, gated actions require mode >= recommended validation scope",
            ],
        )

    return CheckResult(
        "PASS",
        f"Execution authority aligned (mode={mode}, scope={recommended}, "
        f"gate={gate_mechanism})",
    )


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_readiness_checks(
    feature_dir: str,
    wi_id: str,
    verbose: bool = False,
) -> tuple[list[CheckResult], int]:
    """
    Run all readiness checks for a Work Item.

    Returns (results, exit_code) where exit_code is 0=ready, 1=not ready, 2=error.
    """
    if yaml is None:
        return [CheckResult("FAIL", "PyYAML not installed (required)")], 2

    feature_path = Path(feature_dir)
    if not feature_path.exists():
        return [CheckResult("FAIL", f"Feature directory not found: {feature_dir}")], 2

    results: list[CheckResult] = []

    # Load mode policy (try feature-local, shared/policies, then memory/ for backward compat)
    project_root = _find_project_root(feature_path)
    mode_policy = _load_yaml_file(feature_path / "erp_addon_mode_policy.yaml")
    if not mode_policy:
        mode_policy = _load_yaml_file(project_root / "shared" / "policies" / "mode_policy.yaml")
    if not mode_policy:
        mode_policy = _load_yaml_file(project_root / "memory" / "erp_addon_mode_policy.yaml")

    # Fallback defaults if policy file is missing
    if not mode_policy:
        mode_policy = {
            "modes": {
                "autopilot": {"checkpoints": {"pre_run": [], "post_run": ["walkthrough_review", "ci_pass", "ops_review"]}},
                "confirm": {"checkpoints": {"pre_run": ["plan_review"], "post_run": ["walkthrough_review", "ci_pass", "ops_review"]}},
                "validate": {"checkpoints": {"pre_run": ["design_diff_review", "plan_review"], "post_run": ["walkthrough_review", "ci_pass", "ops_review"]}},
            },
            "rules": [
                {"if_any_risk_flags": ["authz", "sod", "audit_log", "pii", "accounting_calc", "inventory_valuation"], "mode": "validate"},
                {"if_any_risk_flags": ["db_schema", "data_migration", "update_integration", "cross_module"], "mode": "validate"},
                {"if_any_risk_flags": ["new_api", "contract_change", "performance_sensitive"], "mode": "confirm"},
                {"if_any_risk_flags": ["ui_only", "message_only", "test_only", "logging_only"], "mode": "autopilot"},
            ],
            "overrides": {"require_reason_when_override": True},
            "tier_mode_minimum": {
                "critical": "confirm",
                "standard": "autopilot",
                "experimental": "autopilot",
            },
        }

    # Load autonomy_bias from state.yaml
    state = _load_yaml_file(feature_path / "state" / "state.yaml")
    autonomy_bias = state.get("autonomy_bias", "balanced") if state else "balanced"

    # Load coverage_tier from basic_design.md
    # Primary: Canonical YAML (basic_design.coverage_tier)
    # Fallback: frontmatter (coverage_tier)
    basic_design_path = feature_path / "basic_design.md"
    coverage_tier = "standard"
    if basic_design_path.exists():
        bd_text = _read_text(basic_design_path)
        canonical = _parse_canonical_yaml(bd_text)
        bd_section = canonical.get("basic_design") or {}
        coverage_tier = bd_section.get("coverage_tier", "")
        if not coverage_tier:
            bd_fm = _parse_front_matter(bd_text)
            coverage_tier = bd_fm.get("coverage_tier", "standard")
    # Normalize: strip whitespace, lowercase, reject unknown values
    coverage_tier = str(coverage_tier).strip().lower()
    if coverage_tier not in ("critical", "standard", "experimental"):
        coverage_tier = "standard"

    # Check 1: Gate 5 approved
    results.append(check_gate5_approved(feature_path))

    # Check 2: WI definition valid
    wi_result, fm, wi_file = check_wi_definition(feature_path, wi_id)
    results.append(wi_result)

    if fm is None or wi_file is None:
        # Cannot proceed without WI definition
        return results, 1

    # Check 3: Mode policy compliant (with autonomy bias)
    results.append(check_mode_policy(feature_path, fm, mode_policy, autonomy_bias, coverage_tier))

    # Check 4: Pre-run approvals
    results.append(check_pre_run_approvals(feature_path, wi_id, wi_file, fm, mode_policy))

    # Check 5: Cross-feature dependencies
    results.append(check_cross_feature_dependencies(feature_path, wi_id, fm))

    # Check 6: Ops pack
    results.append(check_ops_pack(feature_path))

    # Check 7: State consistency
    results.append(check_state_consistency(feature_path, wi_id))

    # Check 8: Execution authority alignment (v4.6.0)
    results.append(check_execution_authority(fm, mode_policy, autonomy_bias, coverage_tier))

    return results, _compute_exit_code(results)


def _compute_exit_code(results: list[CheckResult]) -> int:
    """Compute exit code from results: 0=ready, 1=not ready."""
    for r in results:
        if r.status == "FAIL":
            return 1
    return 0


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_output(wi_id: str, results: list[CheckResult], verbose: bool = False) -> str:
    """Format check results for terminal output."""
    lines = []
    lines.append(f"WI Readiness Check: {wi_id}")
    lines.append("\u2501" * 37)

    for r in results:
        tag = f"[{r.status}]"
        lines.append(f"{tag} {r.message}")
        if verbose and r.details:
            for d in r.details:
                lines.append(f"      {d}")

    # Summary
    fail_count = sum(1 for r in results if r.status == "FAIL")
    warn_count = sum(1 for r in results if r.status == "WARN")
    pass_count = sum(1 for r in results if r.status == "PASS")

    lines.append("")
    if fail_count > 0:
        parts = [f"{fail_count} failure(s)"]
        if warn_count > 0:
            parts.append(f"{warn_count} warning(s)")
        lines.append(f"Result: NOT READY ({', '.join(parts)})")
    elif warn_count > 0:
        lines.append(f"Result: READY ({warn_count} warning(s))")
    else:
        lines.append(f"Result: READY ({pass_count} check(s) passed)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check if a Work Item is ready to execute its Run.",
    )
    parser.add_argument(
        "feature_dir",
        nargs="?",
        help="Path to specs/<feature>/ directory",
    )
    parser.add_argument(
        "wi_id",
        nargs="?",
        help="Work Item ID (e.g., WI-ERP-FEAT-001)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show additional details for each check",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-tests",
    )

    args = parser.parse_args()

    if args.test:
        _run_self_tests()
        return

    if not args.feature_dir or not args.wi_id:
        parser.error("the following arguments are required: feature_dir, wi_id")

    results, exit_code = run_readiness_checks(args.feature_dir, args.wi_id, args.verbose)
    print(format_output(args.wi_id, results, args.verbose))
    sys.exit(exit_code)


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _run_self_tests() -> None:
    """Run self-tests to validate checker behavior."""
    import tempfile
    import shutil

    if yaml is None:
        print("PyYAML not available; cannot run self-tests.")
        sys.exit(2)

    print("Running self-tests...")

    # Test 1: Non-existent feature dir
    results, code = run_readiness_checks("/nonexistent/path", "WI-TEST-001")
    assert code == 2, f"Test 1 failed: expected exit code 2, got {code}"
    print("  Test 1 passed: non-existent path returns exit code 2")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create project structure
        (tmpdir / "memory").mkdir()
        feature_dir = tmpdir / "specs" / "test_feature"
        feature_dir.mkdir(parents=True)

        # Test 2: No APPROVAL.md
        (feature_dir / "work_items").mkdir()
        (feature_dir / "tasks.md").write_text("# Tasks\n")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-001")
        assert any(r.status == "FAIL" and "APPROVAL.md" in r.message for r in results), \
            f"Test 2 failed: expected APPROVAL.md FAIL, got {[(r.status, r.message) for r in results]}"
        print("  Test 2 passed: FAIL when APPROVAL.md missing")

        # Test 3: APPROVAL.md with Gate 5 approved, but no WI file
        (feature_dir / "APPROVAL.md").write_text("""# Feature Approval Record

## Gate 5: Tasking Review

### Checklist
- [x] tasks.md complete
- [x] all tasks have plan_refs

承認者: Test User
日付: 2026-02-07

---
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-MISSING-001")
        assert code == 1, f"Test 3 failed: expected exit code 1, got {code}"
        assert any(r.status == "FAIL" and "not found" in r.message for r in results), \
            f"Test 3 failed: expected WI not found FAIL"
        print("  Test 3 passed: FAIL when WI file not found")

        # Test 4: Valid WI with autopilot mode
        wi_file = feature_dir / "work_items" / "WI-TEST-001.md"
        wi_file.write_text("""---
wi_id: WI-TEST-001
title: Test Work Item
complexity: low
mode: autopilot
risk_flags: ["ui_only"]
spec_refs:
  - "spec.md"
---
# Intent
""")
        # Create state.yaml
        (feature_dir / "state").mkdir()
        (feature_dir / "state" / "state.yaml").write_text("""
work_items:
  - wi_id: WI-TEST-001
    status: pending
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-001")
        # Should pass gate, WI def, mode, pre-run, cross-dep, state
        # Ops pack may fail (no ops/)
        pass_count = sum(1 for r in results if r.status == "PASS")
        assert pass_count >= 5, f"Test 4 failed: expected >=5 PASS, got {pass_count}"
        print("  Test 4 passed: valid autopilot WI passes most checks")

        # Test 5: Mode policy violation (autopilot with authz risk flag)
        wi_file2 = feature_dir / "work_items" / "WI-TEST-002.md"
        wi_file2.write_text("""---
wi_id: WI-TEST-002
title: Auth Change
complexity: high
mode: autopilot
risk_flags: ["authz"]
spec_refs:
  - "spec.md"
---
# Intent
""")
        (feature_dir / "state" / "state.yaml").write_text("""
work_items:
  - wi_id: WI-TEST-001
    status: pending
  - wi_id: WI-TEST-002
    status: pending
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-002")
        mode_results = [r for r in results if "Mode" in r.message or "mode" in r.message.lower()]
        assert any(r.status == "FAIL" for r in mode_results), \
            f"Test 5 failed: expected mode policy FAIL, got {[(r.status, r.message) for r in mode_results]}"
        print("  Test 5 passed: mode policy violation detected")

        # Test 6: Confirm mode with pending pre-run approvals
        wi_file3 = feature_dir / "work_items" / "WI-TEST-003.md"
        wi_file3.write_text("""---
wi_id: WI-TEST-003
title: API Addition
complexity: medium
mode: confirm
risk_flags: ["new_api"]
spec_refs:
  - "spec.md"
---
# Intent
""")
        (feature_dir / "state" / "state.yaml").write_text("""
work_items:
  - wi_id: WI-TEST-003
    status: pending
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-003")
        pre_run = [r for r in results if "pre-run" in r.message.lower() or "Pre-run" in r.message]
        assert any(r.status == "WARN" for r in pre_run), \
            f"Test 6 failed: expected pre-run WARN, got {[(r.status, r.message) for r in pre_run]}"
        print("  Test 6 passed: pre-run approval WARN for confirm mode")

        # Test 7: WI already done in state
        (feature_dir / "state" / "state.yaml").write_text("""
work_items:
  - wi_id: WI-TEST-001
    status: done
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-001")
        state_results = [r for r in results if "State" in r.message or "state" in r.message.lower()]
        assert any(r.status == "FAIL" and "done" in r.message for r in state_results), \
            f"Test 7 failed: expected state FAIL for done WI"
        print("  Test 7 passed: FAIL when WI already done")

        # Test 8: Ops pack present
        ops_dir = feature_dir / "ops"
        ops_dir.mkdir()
        for name in FULL_OPS_PACK:
            (ops_dir / name).write_text("# ops\n")
        (feature_dir / "state" / "state.yaml").write_text("""
work_items:
  - wi_id: WI-TEST-001
    status: pending
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-001")
        ops_results = [r for r in results if "Ops" in r.message or "ops" in r.message.lower()]
        assert any(r.status == "PASS" for r in ops_results), \
            f"Test 8 failed: expected ops PASS, got {[(r.status, r.message) for r in ops_results]}"
        print("  Test 8 passed: ops pack check passes with all files present")

        # Test 9: Cross-feature dependency blocking
        (tmpdir / "memory" / "cross_team_dependency_manifest.yaml").write_text("""
dependencies:
  - dependent:
      feature: test_feature
      wi_id: WI-TEST-001
    provider:
      feature: other_feature
      wi_id: WI-OTHER-001
    status: pending
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-001")
        cross_results = [r for r in results if "cross" in r.message.lower() or "Cross" in r.message]
        assert any(r.status == "FAIL" for r in cross_results), \
            f"Test 9 failed: expected cross-dep FAIL, got {[(r.status, r.message) for r in cross_results]}"
        print("  Test 9 passed: cross-feature dependency blocking detected")

        # --- Autonomy Bias Tests ---

        # Clean up cross-dep manifest for bias tests
        cross_dep_file = tmpdir / "memory" / "cross_team_dependency_manifest.yaml"
        if cross_dep_file.exists():
            cross_dep_file.unlink()

        # Test 10: autonomy_bias=autonomous shifts confirm->autopilot for medium risk
        # new_api risk_flag recommends confirm; autonomous bias shifts to autopilot
        # WI mode is autopilot — should PASS with autonomous bias (would FAIL without bias)
        wi_file_t10 = feature_dir / "work_items" / "WI-TEST-010.md"
        wi_file_t10.write_text("""---
wi_id: WI-TEST-010
title: New API (autonomous bias)
complexity: medium
mode: autopilot
risk_flags: ["new_api"]
spec_refs:
  - "spec.md"
---
# Intent
""")
        (feature_dir / "state" / "state.yaml").write_text("""
autonomy_bias: autonomous
work_items:
  - wi_id: WI-TEST-010
    status: pending
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-010")
        mode_results = [r for r in results if "Mode" in r.message or "mode" in r.message.lower()]
        assert any(r.status == "PASS" and "bias: autonomous" in r.message for r in mode_results), \
            f"Test 10 failed: expected PASS with autonomous bias, got {[(r.status, r.message) for r in mode_results]}"
        print("  Test 10 passed: autonomous bias shifts confirm->autopilot")

        # Test 11: autonomy_bias=controlled shifts autopilot->confirm for low risk
        # ui_only risk_flag recommends autopilot; controlled bias shifts to confirm
        # WI mode is autopilot — should FAIL with controlled bias (would PASS without bias)
        wi_file_t11 = feature_dir / "work_items" / "WI-TEST-011.md"
        wi_file_t11.write_text("""---
wi_id: WI-TEST-011
title: UI Only (controlled bias)
complexity: low
mode: autopilot
risk_flags: ["ui_only"]
spec_refs:
  - "spec.md"
---
# Intent
""")
        (feature_dir / "state" / "state.yaml").write_text("""
autonomy_bias: controlled
work_items:
  - wi_id: WI-TEST-011
    status: pending
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-011")
        mode_results = [r for r in results if "Mode" in r.message or "mode" in r.message.lower()]
        assert any(r.status == "FAIL" and "bias: controlled" in r.message for r in mode_results), \
            f"Test 11 failed: expected FAIL with controlled bias, got {[(r.status, r.message) for r in mode_results]}"
        print("  Test 11 passed: controlled bias shifts autopilot->confirm")

        # Test 12: autonomy_bias=autonomous with critical tier still enforces minimum confirm
        # authz risk_flag recommends validate; autonomous bias shifts to confirm
        # But critical tier minimum is confirm, so confirm is allowed (not weakened to autopilot)
        # WI mode is confirm — should PASS
        (feature_dir / "basic_design.md").write_text("""---
coverage_tier: critical
execution_profile: erp_addon
---
# Basic Design
""")
        wi_file_t12 = feature_dir / "work_items" / "WI-TEST-012.md"
        wi_file_t12.write_text("""---
wi_id: WI-TEST-012
title: Auth Change (autonomous + critical tier)
complexity: high
mode: confirm
risk_flags: ["new_api"]
spec_refs:
  - "spec.md"
---
# Intent
""")
        (feature_dir / "state" / "state.yaml").write_text("""
autonomy_bias: autonomous
work_items:
  - wi_id: WI-TEST-012
    status: pending
""")
        # new_api -> confirm (recommended) -> autonomous shifts to autopilot
        # But critical tier minimum is confirm -> enforced back to confirm
        # WI mode is confirm -> PASS
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-012")
        mode_results = [r for r in results if "Mode" in r.message or "mode" in r.message.lower()]
        assert any(r.status == "PASS" and "bias: autonomous" in r.message for r in mode_results), \
            f"Test 12 failed: expected PASS (tier_mode_minimum enforced), got {[(r.status, r.message) for r in mode_results]}"
        print("  Test 12 passed: autonomous bias with critical tier enforces minimum confirm")

        # Test 13: coverage_tier read from Canonical YAML (not just frontmatter)
        # basic_design.md with coverage_tier ONLY in Canonical YAML block
        # autonomous bias + new_api -> confirm -> shifted to autopilot
        # But critical tier minimum -> confirm enforced
        # WI mode is autopilot -> FAIL (critical tier minimum is confirm)
        (feature_dir / "basic_design.md").write_text("""---
artifact: "basic_design"
feature_id: "FEAT-TEST"
---
# 0. Canonical Basic Design (YAML)
```yaml
basic_design:
  coverage_tier: "critical"
  epic_ref: null
  team_id: null
```
""")
        wi_file_t13 = feature_dir / "work_items" / "WI-TEST-013.md"
        wi_file_t13.write_text("""---
wi_id: WI-TEST-013
title: Canonical YAML tier test
complexity: medium
mode: autopilot
risk_flags: ["new_api"]
spec_refs:
  - "spec.md"
---
# Intent
""")
        (feature_dir / "state" / "state.yaml").write_text("""
autonomy_bias: autonomous
work_items:
  - wi_id: WI-TEST-013
    status: pending
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-013")
        mode_results = [r for r in results if "Mode" in r.message or "mode" in r.message.lower()]
        # autonomous + new_api -> confirm -> autonomous shifts to autopilot
        # But critical tier minimum is confirm -> enforced back to confirm
        # WI mode is autopilot -> FAIL
        assert any(r.status == "FAIL" for r in mode_results), \
            f"Test 13 failed: expected FAIL (canonical YAML critical tier), got {[(r.status, r.message) for r in mode_results]}"
        print("  Test 13 passed: coverage_tier read from Canonical YAML enforces critical minimum")

        # Test 14: coverage_tier case normalization ("Critical" -> "critical")
        (feature_dir / "basic_design.md").write_text("""---
artifact: "basic_design"
feature_id: "FEAT-TEST"
coverage_tier: "Critical"
---
# Basic Design
""")
        wi_file_t14 = feature_dir / "work_items" / "WI-TEST-014.md"
        wi_file_t14.write_text("""---
wi_id: WI-TEST-014
title: Case normalization test
complexity: medium
mode: autopilot
risk_flags: ["new_api"]
spec_refs:
  - "spec.md"
---
# Intent
""")
        (feature_dir / "state" / "state.yaml").write_text("""
autonomy_bias: autonomous
work_items:
  - wi_id: WI-TEST-014
    status: pending
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-014")
        mode_results = [r for r in results if "Mode" in r.message or "mode" in r.message.lower()]
        # "Critical" normalized to "critical" -> tier_mode_minimum = confirm
        # autonomous + new_api -> confirm -> shifted to autopilot -> enforced to confirm
        # WI mode autopilot < confirm -> FAIL
        assert any(r.status == "FAIL" for r in mode_results), \
            f"Test 14 failed: expected FAIL ('Critical' normalized to critical), got {[(r.status, r.message) for r in mode_results]}"
        print("  Test 14 passed: coverage_tier case normalization ('Critical' -> 'critical')")

        # --- Execution Authority Tests (v4.6.0) ---

        # Test 15: execution_authority check passes for valid autopilot+standard
        (feature_dir / "basic_design.md").write_text("""---
coverage_tier: standard
---
# 0. Canonical Basic Design (YAML)
```yaml
basic_design:
  coverage_tier: "standard"
```
""")
        wi_file_t15 = feature_dir / "work_items" / "WI-TEST-015.md"
        wi_file_t15.write_text("""---
wi_id: WI-TEST-015
title: Low risk standard
complexity: low
mode: autopilot
risk_flags: ["ui_only"]
spec_refs:
  - "spec.md"
---
# Intent
""")
        (feature_dir / "state" / "state.yaml").write_text("""
work_items:
  - wi_id: WI-TEST-015
    status: pending
""")
        # Create a mode_policy with execution_authority in shared/policies/
        # Uses risk_flag_mapping dict format (production format), NOT legacy rules array
        policy_dir = tmpdir / "shared" / "policies"
        policy_dir.mkdir(parents=True, exist_ok=True)
        (policy_dir / "mode_policy.yaml").write_text("""
modes:
  autopilot:
    checkpoints:
      pre_run: []
      post_run: ["walkthrough_review", "ci_pass"]
  confirm:
    checkpoints:
      pre_run: ["plan_review"]
      post_run: ["walkthrough_review", "ci_pass"]
  validate:
    checkpoints:
      pre_run: ["design_diff_review", "plan_review"]
      post_run: ["walkthrough_review", "ci_pass"]
risk_flag_mapping:
  validate:
    - "authz"
    - "sod"
    - "audit_log"
    - "pii"
    - "accounting_calc"
    - "inventory_valuation"
    - "db_schema"
    - "data_migration"
    - "update_integration"
    - "cross_module"
  confirm:
    - "new_api"
    - "contract_change"
    - "performance_sensitive"
  autopilot:
    - "ui_only"
    - "message_only"
    - "test_only"
    - "logging_only"
tier_mode_minimum:
  critical: confirm
  standard: autopilot
  experimental: autopilot
overrides:
  require_reason_when_override: true
execution_authority:
  conversational:
    description: "Free actions"
    actions: ["interpret", "propose", "auto-fix lint"]
  gated:
    description: "Schema-validated actions"
    gate_mechanism: "stride-lint + phase_gate.py"
    actions: ["create artifacts", "start WI", "create PR"]
  prohibited:
    description: "Human-only actions"
    actions: ["edit APPROVAL.md", "skip gate", "direct DB write", "override bias", "change tier"]
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-015")
        ea_results = [r for r in results if "authority" in r.message.lower() or "Authority" in r.message]
        assert any(r.status == "PASS" for r in ea_results), \
            f"Test 15 failed: expected execution_authority PASS for standard+autopilot+ui_only, got {[(r.status, r.message) for r in ea_results]}"
        print("  Test 15 passed: execution_authority PASS for valid autopilot+standard")

        # Test 16: execution_authority FAIL for autopilot with validate-level risk flags
        # authz requires validate per risk_flag_mapping, but mode is autopilot
        (feature_dir / "basic_design.md").write_text("""---
coverage_tier: standard
---
# 0. Canonical Basic Design (YAML)
```yaml
basic_design:
  coverage_tier: "standard"
```
""")
        wi_file_t16 = feature_dir / "work_items" / "WI-TEST-016.md"
        wi_file_t16.write_text("""---
wi_id: WI-TEST-016
title: Auth change with weak mode
complexity: high
mode: autopilot
risk_flags: ["authz", "pii"]
spec_refs:
  - "spec.md"
---
# Intent
""")
        (feature_dir / "state" / "state.yaml").write_text("""
work_items:
  - wi_id: WI-TEST-016
    status: pending
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-016")
        ea_results = [r for r in results if "authority" in r.message.lower() or "Authority" in r.message]
        assert any(r.status == "FAIL" for r in ea_results), \
            f"Test 16 failed: expected execution_authority FAIL for autopilot+authz, got {[(r.status, r.message) for r in ea_results]}"
        print("  Test 16 passed: execution_authority FAIL for autopilot+validate-level risk flags")

        # Test 17: execution_authority PASS when no execution_authority in policy (legacy)
        # Remove execution_authority from policy to test backward compatibility
        (policy_dir / "mode_policy.yaml").write_text("""
modes:
  autopilot:
    checkpoints:
      pre_run: []
      post_run: ["walkthrough_review", "ci_pass"]
risk_flag_mapping:
  validate:
    - "authz"
  autopilot:
    - "ui_only"
tier_mode_minimum:
  critical: confirm
  standard: autopilot
  experimental: autopilot
overrides:
  require_reason_when_override: true
""")
        wi_file_t17 = feature_dir / "work_items" / "WI-TEST-017.md"
        wi_file_t17.write_text("""---
wi_id: WI-TEST-017
title: Legacy mode (no execution_authority)
complexity: low
mode: autopilot
risk_flags: ["ui_only"]
spec_refs:
  - "spec.md"
---
# Intent
""")
        (feature_dir / "state" / "state.yaml").write_text("""
work_items:
  - wi_id: WI-TEST-017
    status: pending
""")
        results, code = run_readiness_checks(str(feature_dir), "WI-TEST-017")
        ea_results = [r for r in results if "authority" in r.message.lower() or "Authority" in r.message]
        assert any(r.status == "PASS" and "legacy" in r.message.lower() for r in ea_results), \
            f"Test 17 failed: expected legacy mode PASS, got {[(r.status, r.message) for r in ea_results]}"
        print("  Test 17 passed: execution_authority PASS for legacy policy (no declaration)")

    print("All self-tests passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
