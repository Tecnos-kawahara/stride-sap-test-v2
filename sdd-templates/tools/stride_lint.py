#!/usr/bin/env python3
"""
stride-lint: Linting tool for SDD (Specification-Driven Development) documents.
"""
import argparse
import difflib
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from stride_shared_lib import (
    extract_frontmatter,
    extract_yaml_after_marker,
    extract_yaml_blocks,
)


# =============================================================================
# Windows Console Encoding Fix
# =============================================================================
# Windows console (cmd.exe, PowerShell) defaults to cp1252 or similar encoding
# which cannot handle UTF-8 characters (Japanese, symbols, etc.).
# This fix ensures proper UTF-8 output on all platforms.

def _configure_console_encoding():
    """Configure stdout/stderr for UTF-8 with safe fallback on Windows."""
    if sys.platform == "win32":
        # Method 1: Use reconfigure (Python 3.7+)
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
                return
            except Exception:
                pass
        # Method 2: Wrap with TextIOWrapper
        try:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True
            )
        except Exception:
            pass  # Fall back to default encoding if all else fails


_configure_console_encoding()

# =============================================================================
# Color output (respects NO_COLOR, --no-color, non-TTY)
# =============================================================================

def _should_colorize():
    """Determine if output should be colorized.

    Checks stdout (not stderr) because lint results go to stdout.
    Respects NO_COLOR (https://no-color.org/) and TERM=dumb.
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    return True

_USE_COLOR = _should_colorize()

def _color(text, code):
    """Wrap text in ANSI color if color is enabled."""
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"

def _red(text):
    return _color(text, "31")

def _yellow(text):
    return _color(text, "33")

def _green(text):
    return _color(text, "32")

def _bold(text):
    return _color(text, "1")

def _dim(text):
    return _color(text, "2")

# =============================================================================
# Actor tracking (audit trail)
# =============================================================================

def _detect_actor():
    """Build actor metadata for JSON/NDJSON output.

    STRIDE_ACTOR env var is the authoritative actor identity.
    When absent, invocation_mode is inferred as a hint (not assertion).
    """
    explicit = os.environ.get("STRIDE_ACTOR", "")
    if explicit:
        return {"actor": explicit, "invocation_mode": "explicit"}

    # Heuristic invocation mode (informational, not authoritative)
    ci_indicators = ["CI", "GITHUB_ACTIONS", "JENKINS_URL", "GITLAB_CI", "CIRCLECI"]
    for indicator in ci_indicators:
        if os.environ.get(indicator):
            return {"invocation_mode": f"ci:{indicator.lower()}"}

    if sys.stdout.isatty():
        return {"invocation_mode": "interactive"}

    return {"invocation_mode": "non-interactive"}

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


# v1.2.4: ID conventions are now defined in config/id_conventions.yaml
# This allows for centralized management of ID patterns and validation rules.
# The PLACEHOLDER_PATTERNS below are still used for placeholder detection.
# Future: Replace hardcoded patterns with dynamic loading from id_conventions.yaml

PLACEHOLDER_PATTERNS = [
    r"\bFEAT-XXX\b",
    r"\bFEATXXX\b",
    r"\bSPEC-XXX\b",
    r"\bPLAN-XXX\b",
    r"\bTASKS-XXX\b",
    r"\bBD-XXX\b",
    r"\bEVID-XXX\b",
    r"\bUS-FEATXXX-\d{3}\b",
    r"\bAC-US-FEATXXX-\d{3}-\d{2}\b",
    r"\bBPMN-(TASK|GW|EVT|FLOW)-XXX\b",
    r"\bCT-[A-Z]+-XX\b",
    r"\bTS-(CON|INT|E2E|UT)-XX\b",
    r"\bT-GXX-XXX\b",
    r"specs/XXX_feature_name/",
    # v1.2.4: Date and name placeholders
    r"\bYYYY-MM-DD\b",
    r"<[A-Za-z\s]+>",               # <Business Owner>, <Tech Lead>, etc.
    r"_____+",                       # Underscore runs (signature fields)
]


def load_id_conventions():
    """Load ID conventions from config/id_conventions.yaml.

    Returns the parsed YAML or None if file doesn't exist or YAML is unavailable.
    This is provided for future ID validation enhancements.
    """
    if yaml is None:
        return None

    # Find config file relative to this script
    script_dir = Path(__file__).parent.parent
    config_path = script_dir / "config" / "id_conventions.yaml"

    if not config_path.exists():
        return None

    try:
        return yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception:
        return None

ALLOWED_HYPHEN_BASENAMES = {"e2e-triage.md"}

# Approval gate mapping: gate number -> (section title, required checkboxes count)
APPROVAL_GATES = {
    1: ("Gate 1: Basic Design", 3),
    2: ("Gate 2: BPMN", 2),
    3: ("Gate 3: Spec", 3),
    4: ("Gate 4: Plan", 3),
    5: ("Gate 5: Tasks", 3),
    "final": ("Final: Implementation", 3),
}

# v1.2.4: Lite mode approval gates (3-stage instead of 6-stage)
# For small projects, PoC, and single-developer workflows
APPROVAL_GATES_LITE = {
    "A": ("Gate A: Design & Flow", 3),      # Replaces Gate 1 + 2
    "B": ("Gate B: Spec & Plan", 3),        # Replaces Gate 3 + 4
    "C": ("Gate C: Implementation & Verification", 3),  # Replaces Gate 5 + Final
}

# Mapping from full mode gates to lite mode gates
GATE_FULL_TO_LITE = {
    1: "A", 2: "A",
    3: "B", 4: "B",
    5: "C", "final": "C",
}


# Agent-friendly: default suggested actions for error codes
SUGGESTED_ACTIONS = {
    "MISSING_FILE": "該当ファイルをtemplateからコピーして作成してください: stride init <feature>",
    "YAML_PARSE_ERROR": "YAMLの構文を確認してください。インデントとコロンの後のスペースが原因の場合が多いです",
    "ID_REGEX_MISMATCH": "config/id_conventions.yamlのパターンを確認し、IDを修正してください",
    "DUPLICATE_ID": "重複しているIDを一意になるよう連番で修正してください",
    "AC_NOT_COVERED": "plan.mdのテスト定義にcovers_acceptance_idsを追記してください",
    "GATE_FAILED": "全エラーを解消してから stride lint を再実行してください（stride phase-status で状態確認可）",
    "CANONICAL_BLOCK_NOT_FOUND": "該当ドキュメントの正しいセクションにYAMLブロックを追加してください",
    "CONTRACT_COVERAGE_INCOMPLETE": "plan.mdにcontract testを追加してCTをカバーしてください",
    "REF_NOT_FOUND": "参照先のIDがspec/plan/tasksに存在するか確認してください",
    "INVALID_PLAN_REF": "plan_refsにはstable IDのみ使用してください (CMP/LIB/CT/TS/Phase/G)",
    "BPMN_VALIDATION_FAILED": "process.bpmnをCamunda 8形式に修正してください",
    "BPMN_PLACEHOLDER_PRESENT": "process.bpmnの{{...}}プレースホルダを実際の値に置換してください",
    "PLACEHOLDER_VALUE_PRESENT": "プレースホルダ値を実際の値に置換してください",
    "COUNTS_MISMATCH": "表示された正しい値でcountsを更新してください",
    "APPROVAL_PENDING": "APPROVAL.mdの該当Gateを承認してください（人間のみ）",
    "TEST_NOT_TASKED": "tasks.mdにテストタスクを追加してください",
    "TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE": "該当タグに対応するテスト種別を追加してください",
    "E2E_REPORTING_NOT_CONFIGURED": "plan.mdのtest_strategy.reporting.e2eを設定してください",
    "E2E_TRIAGE_NOT_DEFINED": "implementation-details/e2e-triage.mdを作成してください",
    "SPEC_AS_CODE_MISSING": "spec.mdのspec_as_code.artifactsを定義してください",
    "EVIDENCE_PACK_NOT_DEFINED": "plan.mdのevidence_pack設定を追加してください",
    # v5.4: Profile consistency (reporting granularity + completeness thresholds only)
    "PROFILE_UNKNOWN": "basic_design.profile の値を enterprise-erp / saas-integration / prototype のいずれかにしてください。詳細: shared/policies/profile_policy.yaml",
    "PROFILE_MISMATCH": "basic_design.md の basic_design.profile と state.yaml の top-level profile を一致させてください（SSoT は basic_design.md 側）。",
    # Extension Pack
    "EXTENSIONS_NOT_CONFIGURED": ".stride-extensions.yaml を作成してください",
    "EVIDENCE_PACK_EXTENSION_NOT_DEFINED": "拡張パックの evidence_pack 設定が不足しています",
    "EVIDENCE_PACK_CATEGORY_MAPPING_MISSING": "拡張パックの category_mapping ファイルが見つかりません",
    "PROFILE_MISSING": "basic_design.md の basic_design: ブロックに profile を追加してください（省略時は enterprise-erp 扱い）。",
    # v5.5 Phase B: VALUE Upstream Extension lint codes (lint_upstream() emits these when specs/<feature>/upstream/ exists)
    "BACCM_INCOMPLETE": "Run 'stride upstream init <feature> --phase discovery' to scaffold missing BACCM artifacts. See manual/40_baccm_guide.md.",
    "BROKEN_LAYER_LINK": "Check cross_layer_links references in requirements_architecture.yaml. See manual/41_layered_requirements_modeling_guide.md.",
    "UPSTREAM_TEMPLATE_DRIFT": "Update artifact's template_id to match upstream/<template>.yaml frontmatter (^TPL-UP-[A-Z]{3,4}-[0-9]{3}$).",
    "BABOK_TECHNIQUE_UNKNOWN": "Check technique_id against shared/policies/technique_library.yaml. See manual/40_baccm_guide.md.",
}

# v5.4: Profile enum (reporting + completeness threshold switch only)
# SSoT: shared/policies/profile_policy.yaml
KNOWN_PROFILES = ("enterprise-erp", "saas-integration", "prototype")
DEFAULT_PROFILE = "enterprise-erp"


class LintResult:
    def __init__(self, feature_path):
        self.feature_path = str(feature_path)
        self.errors = []
        self.warnings = []
        self.coverage_report = None
        self.coverage_summary = None  # v1.2.4: Always show brief summary

    def add_error(self, code, message, suggested_action=None, retryable=False):
        if suggested_action is None:
            suggested_action = SUGGESTED_ACTIONS.get(code)
        self.errors.append({
            "code": code,
            "message": message,
            "suggested_action": suggested_action,  # Agent-friendly: actionable hint for AI agents
            "retryable": retryable,
        })

    def add_warning(self, code, message, suggested_action=None, retryable=False):
        if suggested_action is None:
            suggested_action = SUGGESTED_ACTIONS.get(code)
        self.warnings.append({
            "code": code,
            "message": message,
            "suggested_action": suggested_action,
            "retryable": retryable,
        })

    def has_issues(self):
        return bool(self.errors or self.warnings)


class LintConfig:
    def __init__(self, warn_only=False, coverage_report=False, fmt="text", verbose=False, fail_on=None, lite_mode=False, enterprise=False, plain=False):
        self.warn_only = warn_only
        self.coverage_report = coverage_report
        self.format = fmt
        self.verbose = verbose
        self.fail_on = set(fail_on or [])
        self.lite_mode = lite_mode  # v1.2.4: Lite mode for small projects
        self.enterprise = enterprise
        self.plain = plain


def load_enterprise_config():
    """Load enterprise configuration from config/enterprise.yaml.

    Returns True if enterprise mode is enabled, False otherwise.
    """
    try:
        import yaml as _yaml
    except ImportError:
        return False

    script_dir = Path(__file__).parent.parent
    config_path = script_dir / "config" / "enterprise.yaml"

    if not config_path.exists():
        return False

    try:
        data = _yaml.safe_load(config_path.read_text(encoding="utf-8"))
        return bool(data.get("enterprise", {}).get("enabled", False))
    except Exception:
        return False


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def load_yaml(block, path_label, result):
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install with `pip install pyyaml`.")
    try:
        data = yaml.safe_load(block)
    except Exception as exc:  # pragma: no cover
        result.add_error("YAML_PARSE_ERROR", f"{path_label}: {exc}")
        return None
    return data or {}


def as_list(value):
    return value if isinstance(value, list) else []


def compile_regex(pattern):
    return re.compile(pattern)


def check_profile_consistency(feature_dir, basic_section, result):
    """v5.4: Validate Profile declaration consistency.

    Canonical schema:
      - basic_design.md → basic_design.profile (SSoT, flat under basic_design:*)
      - state.yaml      → top-level `profile` (sync cache, flat, NOT workspace.*)

    Emits:
      - PROFILE_UNKNOWN   (error)  value outside KNOWN_PROFILES
      - PROFILE_MISSING   (warn)   basic_design.profile absent  (fallback: enterprise-erp)
      - PROFILE_MISMATCH  (error)  basic_design.profile != state.yaml top-level profile
    """
    bd_profile = basic_section.get("profile")

    if bd_profile is None:
        result.add_warning(
            "PROFILE_MISSING",
            "basic_design.profile not set (default 'enterprise-erp' will be used)",
        )
    elif bd_profile not in KNOWN_PROFILES:
        result.add_error(
            "PROFILE_UNKNOWN",
            f"basic_design.profile: '{bd_profile}' "
            f"(expected one of {', '.join(KNOWN_PROFILES)})",
        )

    # Compare with state.yaml top-level profile (flat schema cache)
    state_path = Path(feature_dir) / "state" / "state.yaml"
    if not state_path.exists():
        return  # state.yaml may not exist yet (pre-Phase 4); consistency check is a no-op

    if yaml is None:
        return
    try:
        state_data = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return  # parse errors are reported by other checks

    state_profile = state_data.get("profile") if isinstance(state_data, dict) else None
    if state_profile is None:
        return  # state.yaml has not adopted the profile field yet; treat as not-yet-synced

    if state_profile not in KNOWN_PROFILES:
        result.add_error(
            "PROFILE_UNKNOWN",
            f"state.yaml profile: '{state_profile}' "
            f"(expected one of {', '.join(KNOWN_PROFILES)})",
        )
        return

    if bd_profile is not None and state_profile != bd_profile:
        result.add_error(
            "PROFILE_MISMATCH",
            f"basic_design.profile='{bd_profile}' vs state.yaml profile='{state_profile}' "
            "(basic_design.md is SSoT — update state.yaml to match)",
        )


def check_placeholders(label, block_text, result):
    matches = set()
    for pattern in PLACEHOLDER_PATTERNS:
        for match in re.finditer(pattern, block_text):
            matches.add(match.group(0))
    if matches:
        result.add_warning(
            "PLACEHOLDER_VALUE_PRESENT",
            f"{label}: {', '.join(sorted(matches))}",
        )


def parse_approval_section(content, gate_key, lite_mode=False):
    """Parse an approval section from APPROVAL.md and check its status.

    v1.2.4: Added lite_mode parameter for 3-stage approval.
    v1.2.5: Added multi-language support for approver/date fields (Japanese/English).
    """
    gates = APPROVAL_GATES_LITE if lite_mode else APPROVAL_GATES
    if gate_key not in gates:
        return None, "Invalid gate key"

    section_title, expected_checkboxes = gates[gate_key]

    # Find the section
    section_pattern = rf"##\s*{re.escape(section_title)}"
    section_match = re.search(section_pattern, content)
    if not section_match:
        return False, f"Section '{section_title}' not found"

    # Find the next section or end of file
    next_section = re.search(r"\n##\s+", content[section_match.end():])
    if next_section:
        section_content = content[section_match.start():section_match.end() + next_section.start()]
    else:
        section_content = content[section_match.start():]

    # Count checked boxes [x] vs unchecked [ ]
    checked = len(re.findall(r"\[x\]", section_content, re.IGNORECASE))
    unchecked = len(re.findall(r"\[ \]", section_content))
    total_checkboxes = checked + unchecked

    if total_checkboxes == 0:
        return False, f"No checkboxes found in '{section_title}'"

    if unchecked > 0:
        return False, f"Unchecked items remain ({unchecked}/{total_checkboxes})"

    # v1.2.5: Multi-language approver field detection (Japanese/English)
    approver_patterns = [
        r"承認者:\s*([^\n]+)",      # Japanese
        r"Approver:\s*([^\n]+)",    # English
    ]
    approver_found = False
    for approver_pattern in approver_patterns:
        approver_match = re.search(approver_pattern, section_content, re.IGNORECASE)
        if approver_match:
            approver_name = approver_match.group(1).strip()
            if re.match(r"^_+$", approver_name) or not approver_name:
                return False, "Approver name not filled in"
            approver_found = True
            break

    return True, "Approved"


def detect_lite_mode(feature_path):
    """Detect if the feature is using lite mode based on APPROVAL.md content.

    v1.2.4: Auto-detect lite mode from APPROVAL.md structure.
    Note: Only APPROVAL.md is read. APPROVAL_LITE.md template should be
    copied to APPROVAL.md using 'stride init --lite'.
    """
    approval_path = Path(feature_path) / "APPROVAL.md"
    if not approval_path.exists():
        return False

    content = read_text(approval_path)
    # Lite mode uses "Gate A", "Gate B", "Gate C" sections
    return "## Gate A:" in content or "Lite Mode" in content


def check_approval(feature_path, gates_to_check, result, lite_mode=None):
    """Check APPROVAL.md for human approval status.

    Args:
        feature_path: Path to the feature directory
        gates_to_check: List of gate numbers to check (1-5 or "final" for full, A/B/C for lite)
        result: LintResult object to add errors to
        lite_mode: If None, auto-detect. If True/False, use specified mode.

    Returns:
        dict: Approval status for each gate
    """
    # v1.2.4: Auto-detect or use specified lite mode
    if lite_mode is None:
        lite_mode = detect_lite_mode(feature_path)

    # Only read APPROVAL.md (APPROVAL_LITE.md template should be copied to APPROVAL.md)
    approval_path = Path(feature_path) / "APPROVAL.md"

    if not approval_path.exists():
        result.add_error(
            "APPROVAL_FILE_MISSING",
            f"APPROVAL.md not found at {feature_path}. Human approval is required."
        )
        return {gate: False for gate in gates_to_check}

    content = read_text(approval_path)
    statuses = {}

    # v1.2.4: Convert gates to lite mode if needed
    if lite_mode:
        gates_to_check_actual = list(set(GATE_FULL_TO_LITE.get(g, g) for g in gates_to_check))
    else:
        gates_to_check_actual = gates_to_check

    gates = APPROVAL_GATES_LITE if lite_mode else APPROVAL_GATES

    for gate in gates_to_check_actual:
        approved, message = parse_approval_section(content, gate, lite_mode)
        statuses[gate] = approved

        if not approved:
            gate_name = gates.get(gate, (f"Gate {gate}", 0))[0]
            result.add_error(
                "APPROVAL_PENDING",
                f"{gate_name}: {message}. Human approval required."
            )

    return statuses


def get_approval_date(content, gate_key):
    """Extract approval date from APPROVAL.md section.

    v1.2.4: Added for post-approval change detection.
    v1.2.5: Added multi-language support for date fields (Japanese/English).
    """
    if gate_key not in APPROVAL_GATES:
        return None

    section_title = APPROVAL_GATES[gate_key][0]
    section_pattern = rf"##\s*{re.escape(section_title)}"
    section_match = re.search(section_pattern, content)
    if not section_match:
        return None

    next_section = re.search(r"\n##\s+", content[section_match.end():])
    if next_section:
        section_content = content[section_match.start():section_match.end() + next_section.start()]
    else:
        section_content = content[section_match.start():]

    # v1.2.5: Multi-language date patterns (Japanese/English)
    date_patterns = [
        r"日付:\s*(\d{4}-\d{2}-\d{2})",      # Japanese
        r"Date:\s*(\d{4}-\d{2}-\d{2})",      # English
    ]
    for date_pattern in date_patterns:
        date_match = re.search(date_pattern, section_content, re.IGNORECASE)
        if date_match:
            try:
                return datetime.strptime(date_match.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def get_file_last_modified_git(file_path):
    """Get last modified timestamp of a file from git.

    v1.2.4: Added for post-approval change detection.
    v1.2.5: Added better error handling with debug info.
    """
    try:
        output = subprocess.check_output(
            ["git", "log", "-1", "--format=%aI", "--", str(file_path)],
            cwd=Path(file_path).parent,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        if output.strip():
            return datetime.fromisoformat(output.strip().replace("Z", "+00:00"))
    except subprocess.CalledProcessError:
        # Git command failed (not a git repo, file not tracked, etc.)
        pass
    except FileNotFoundError:
        # Git not installed
        pass
    except Exception:
        # Other unexpected errors
        pass
    return None


def check_post_approval_changes(feature_path, approved_gates, result):
    """Check if files were modified after their gate was approved.

    v1.2.4: Post-Approval Change Rule enforcement.
    """
    approval_path = Path(feature_path) / "APPROVAL.md"
    if not approval_path.exists():
        return

    content = read_text(approval_path)

    # Map gates to files that should not change after approval
    gate_file_map = {
        1: ["basic_design.md"],
        2: ["process.bpmn"],
        3: ["spec.md"],
        4: ["plan.md"],
        5: ["tasks.md"],
    }

    for gate, files in gate_file_map.items():
        if gate not in approved_gates:
            continue

        approval_date = get_approval_date(content, gate)
        if not approval_date:
            continue

        for filename in files:
            file_path = Path(feature_path) / filename
            if not file_path.exists():
                continue

            file_modified = get_file_last_modified_git(file_path)
            if file_modified and file_modified > approval_date:
                gate_name = APPROVAL_GATES[gate][0]
                result.add_warning(
                    "POST_APPROVAL_CHANGE",
                    f"{filename} was modified after {gate_name} approval. "
                    f"Re-approval may be required. "
                    f"(approved: {approval_date.date()}, modified: {file_modified.date()})"
                )


def check_id(regex, value, allow_empty, result, context):
    if value is None:
        result.add_error("ID_REGEX_MISMATCH", f"{context}: missing id")
        return
    if value == "" and allow_empty:
        return
    if not regex.match(value):
        result.add_error("ID_REGEX_MISMATCH", f"{context}: {value}")


def check_duplicates(values, result, context):
    seen = set()
    dups = set()
    for value in values:
        if value in seen:
            dups.add(value)
        else:
            seen.add(value)
    if dups:
        result.add_error("DUPLICATE_ID", f"{context}: {', '.join(sorted(dups))}")


def count_blocking_questions(questions):
    return sum(1 for q in as_list(questions) if q.get("blocking") is True)


def compute_basic_counts(basic_doc):
    trace_rows = as_list(basic_doc.get("traceability_rows"))
    integration_flows = as_list(basic_doc.get("integration_flows"))
    counts = {
        "traceability_rows": len(trace_rows),
        "integration_flows": len(integration_flows),
        "blocking_questions": count_blocking_questions(basic_doc.get("open_questions")),
    }
    return counts, trace_rows


def compute_spec_counts(spec_doc):
    use_cases = as_list(spec_doc.get("use_cases"))
    ac_items = []
    for uc in use_cases:
        ac_items.extend(as_list(uc.get("acceptance")))
    spec_as_code = spec_doc.get("spec_as_code", {})
    spec_as_code_artifacts = as_list(spec_as_code.get("artifacts"))
    integration_tagged = sum(1 for ac in ac_items if "integration" in as_list(ac.get("tags")))
    e2e_tagged = sum(1 for ac in ac_items if "e2e" in as_list(ac.get("tags")))
    requirements = spec_doc.get("requirements", {})
    integration = as_list(requirements.get("integration"))
    data_governance = as_list(requirements.get("data_governance"))
    performance = as_list(requirements.get("performance"))
    availability = as_list(requirements.get("availability_reliability"))
    security = as_list(requirements.get("security_privacy"))
    operations = as_list(requirements.get("operations"))
    nfr_items = sum(len(items) for items in [
        integration,
        data_governance,
        performance,
        availability,
        security,
        operations,
    ])
    counts = {
        "use_cases": len(use_cases),
        "acceptance_criteria": len(ac_items),
        "integration_tagged_ac": integration_tagged,
        "e2e_tagged_ac": e2e_tagged,
        "blocking_questions": count_blocking_questions(spec_doc.get("open_questions")),
        "nfr_items": nfr_items,
        "security_items": len(security),
        "integration_items": len(integration),
        "data_items": len(data_governance),
        "spec_as_code_artifacts": len(spec_as_code_artifacts),
    }
    return counts, use_cases, ac_items, spec_as_code_artifacts


def compute_plan_counts(plan_doc):
    scope = plan_doc.get("scope", {})
    architecture = plan_doc.get("architecture", {})
    contracts = plan_doc.get("contracts", {})
    test_strategy = plan_doc.get("test_strategy", {})
    phases = as_list(plan_doc.get("phases"))
    cli_contracts = as_list(contracts.get("cli"))
    api_contracts = as_list(contracts.get("apis_events"))
    database_contracts = as_list(contracts.get("database", {}).get("tables"))
    # File-kind contracts (CT-FILE-*): YAML config/policy files (e.g. Output Guard rules).
    # T2.6 (Round 3 Sprint 15 P1, 2026-05-22): added so stable_ids recognises plan.contracts.file IDs.
    file_contracts = as_list(contracts.get("file"))
    tests = as_list(test_strategy.get("tests"))
    integration_tests = [t for t in tests if t.get("type") == "integration"]
    e2e_tests = [t for t in tests if t.get("type") == "e2e"]
    group_count = sum(len(as_list(p.get("groups"))) for p in phases)
    counts = {
        "in_use_cases": len(as_list(scope.get("in_use_cases"))),
        "libraries": len(as_list(architecture.get("libraries"))),
        "contracts": len(cli_contracts) + len(api_contracts) + len(database_contracts) + len(file_contracts),
        "tests": len(tests),
        "integration_tests": len(integration_tests),
        "e2e_tests": len(e2e_tests),
        "groups": group_count,
        "exception_items": len(as_list(plan_doc.get("exceptions"))),
    }
    return counts, cli_contracts + api_contracts + database_contracts + file_contracts, tests, phases


def compute_tasks_counts(tasks_doc):
    task_items = as_list(tasks_doc.get("tasks"))
    milestones = as_list(tasks_doc.get("milestones"))
    spec_refs = []
    tasks_with_plan_refs = 0
    dependency_edges = 0
    for task in task_items:
        spec_refs.extend(as_list(task.get("spec_refs")))
        plan_refs = as_list(task.get("plan_refs"))
        if plan_refs:
            tasks_with_plan_refs += 1
        dependency_edges += len(as_list(task.get("depends_on")))
    use_cases_referenced = len({ref for ref in spec_refs if ref.startswith("US-")})
    acceptance_referenced = len({ref for ref in spec_refs if ref.startswith("AC-")})
    counts = {
        "tasks": len(task_items),
        "use_cases_referenced": use_cases_referenced,
        "acceptance_referenced": acceptance_referenced,
        "tasks_with_plan_refs": tasks_with_plan_refs,
        "dependency_edges": dependency_edges,
        "milestones": len(milestones),
    }
    return counts, task_items


def compare_counts(label, expected, actual, result, show_all_mismatches=True):
    """Compare declared counts vs computed counts.

    v1.2.4: Enhanced to show correct values for easy copy-paste.
    """
    mismatches = []
    for key, value in expected.items():
        if key in actual and actual[key] != value:
            mismatches.append((key, value, actual[key]))

    if mismatches:
        for key, declared, computed in mismatches:
            result.add_warning(
                "COUNTS_MISMATCH",
                f"{label}.counts.{key}: declared={declared}, should be={computed}",
            )
        if show_all_mismatches and len(mismatches) > 0:
            # v1.2.4: Show all correct values in YAML format for easy copy-paste
            correct_yaml = "    counts:\n"
            for key in sorted(actual.keys()):
                correct_yaml += f"      {key}: {actual[key]}\n"
            result.add_warning(
                "COUNTS_SUGGESTION",
                f"{label}: Correct counts (copy-paste ready):\n{correct_yaml}",
            )


def normalize_path(root, path_value):
    if not path_value:
        return None
    path = Path(path_value)
    if path.is_absolute():
        return path
    return (root / path_value).resolve()


def check_path_naming(data, result, context):
    for value in iter_string_values(data):
        if not looks_like_path(value):
            continue
        basename = value.split("/")[-1]
        if "-" in basename and basename not in ALLOWED_HYPHEN_BASENAMES:
            result.add_warning(
                "INVALID_PATH_NAMING",
                f"{context}: {value}",
            )


def looks_like_path(value):
    if not isinstance(value, str):
        return False
    if "/" not in value:
        return False
    lowered = value.lower()
    return any(ext in lowered for ext in [".md", ".bpmn", ".yaml", ".yml", ".json"])


def iter_string_values(data):
    if isinstance(data, dict):
        for value in data.values():
            yield from iter_string_values(value)
    elif isinstance(data, list):
        for value in data:
            yield from iter_string_values(value)
    elif isinstance(data, str):
        yield data


def extract_namespaces(root):
    ns = {}
    for key, value in root.attrib.items():
        if key.startswith("{http://www.w3.org/2000/xmlns/}"):
            prefix = key.split("}", 1)[1]
            ns[prefix] = value

    def add_namespace(prefix, uri):
        if prefix and uri and prefix not in ns:
            ns[prefix] = uri

    if root.tag.startswith("{"):
        root_ns = root.tag.split("}", 1)[0][1:]
        add_namespace("bpmn", root_ns)

    for elem in root.iter():
        if elem.tag.startswith("{"):
            uri = elem.tag.split("}", 1)[0][1:]
            if uri == "http://www.omg.org/spec/BPMN/20100524/MODEL":
                add_namespace("bpmn", uri)
            elif uri == "http://www.omg.org/spec/BPMN/20100524/DI":
                add_namespace("bpmndi", uri)
            elif uri == "http://camunda.org/schema/zeebe/1.0":
                add_namespace("zeebe", uri)
        for attr in elem.attrib:
            if attr.startswith("{"):
                attr_uri = attr.split("}", 1)[0][1:]
                if attr_uri == "http://camunda.org/schema/modeler/1.0":
                    add_namespace("modeler", attr_uri)
    return ns


def validate_bpmn(path, result):
    try:
        tree = ET.parse(path)
    except Exception as exc:
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: {exc}")
        return False
    root = tree.getroot()
    if not root.tag.endswith("definitions"):
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: root is not definitions")
        return False

    ns = extract_namespaces(root)
    zeebe_ns = ns.get("zeebe")
    modeler_ns = ns.get("modeler")
    bpmn_ns = ns.get("bpmn")
    bpmndi_ns = ns.get("bpmndi")

    if zeebe_ns != "http://camunda.org/schema/zeebe/1.0":
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: missing zeebe namespace")
    if modeler_ns != "http://camunda.org/schema/modeler/1.0":
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: missing modeler namespace")

    modeler_exec = root.attrib.get(f"{{{modeler_ns}}}executionPlatform") if modeler_ns else None
    modeler_version = root.attrib.get(f"{{{modeler_ns}}}executionPlatformVersion") if modeler_ns else None
    if modeler_exec != "Camunda Cloud":
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: executionPlatform not Camunda Cloud")
    # v1.2.4: Relaxed version check - accept any 8.x version
    if not (modeler_version and modeler_version.startswith("8.")):
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: executionPlatformVersion not 8.x (found: {modeler_version})")
    elif not modeler_version.startswith("8.8"):
        result.add_warning("BPMN_VERSION_MISMATCH", f"{path}: recommended 8.8.*, found {modeler_version}")

    if not bpmn_ns:
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: missing bpmn namespace")
        return False

    nsmap = {
        "bpmn": bpmn_ns,
        "bpmndi": bpmndi_ns or "",
        "zeebe": zeebe_ns or "",
    }

    processes = root.findall("bpmn:process", nsmap)
    if not processes:
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: no bpmn:process")
        return False
    for process in processes:
        if process.get("isExecutable") != "true":
            result.add_error("BPMN_VALIDATION_FAILED", f"{path}: process not executable")

    diagrams = root.findall("bpmndi:BPMNDiagram", nsmap)
    planes = root.findall(".//bpmndi:BPMNPlane", nsmap)
    if not diagrams or not planes:
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: missing BPMNDiagram/BPMNPlane")
    else:
        # BPMNPlane can reference either a process or a collaboration
        process_ids = {p.get("id") for p in processes if p.get("id")}
        collab_ids = {c.get("id") for c in root.findall("bpmn:collaboration", nsmap) if c.get("id")}
        valid_refs = process_ids | collab_ids
        if not any(plane.get("bpmnElement") in valid_refs for plane in planes):
            result.add_error("BPMN_VALIDATION_FAILED", f"{path}: plane does not reference process or collaboration")

    service_tasks = root.findall(".//bpmn:serviceTask", nsmap)
    for task in service_tasks:
        task_defs = task.findall(".//zeebe:taskDefinition", nsmap)
        if not task_defs:
            result.add_error("BPMN_VALIDATION_FAILED", f"{path}: serviceTask missing zeebe:taskDefinition")
        else:
            for task_def in task_defs:
                if not task_def.get("type"):
                    result.add_error("BPMN_VALIDATION_FAILED", f"{path}: serviceTask missing taskDefinition type")

    seq_flows = {flow.get("id"): flow for flow in root.findall(".//bpmn:sequenceFlow", nsmap) if flow.get("id")}
    for gw in root.findall(".//bpmn:exclusiveGateway", nsmap):
        outgoing = [o.text for o in gw.findall("bpmn:outgoing", nsmap) if o.text]
        if len(outgoing) <= 1:
            continue
        default_flow = gw.get("default")
        if default_flow:
            if default_flow not in seq_flows:
                result.add_error("BPMN_VALIDATION_FAILED", f"{path}: default flow not found {default_flow}")
        else:
            missing = []
            for flow_id in outgoing:
                flow = seq_flows.get(flow_id)
                if flow is None:
                    missing.append(flow_id)
                    continue
                cond = flow.find("bpmn:conditionExpression", nsmap)
                if cond is None or not (cond.text and cond.text.strip()):
                    missing.append(flow_id)
            if missing:
                result.add_error("BPMN_VALIDATION_FAILED", f"{path}: XOR missing condition {', '.join(missing)}")

    uses_message = False
    if root.findall(".//bpmn:receiveTask", nsmap):
        uses_message = True
    if root.findall(".//bpmn:messageEventDefinition", nsmap):
        uses_message = True
    if uses_message:
        messages = root.findall("bpmn:message", nsmap)
        if not messages:
            result.add_error("BPMN_VALIDATION_FAILED", f"{path}: message used but bpmn:message missing")
        subscriptions = root.findall(".//zeebe:subscription", nsmap)
        if not any(sub.get("correlationKey") for sub in subscriptions):
            result.add_error("BPMN_VALIDATION_FAILED", f"{path}: zeebe:subscription correlationKey missing")

    for duration in root.findall(".//bpmn:timeDuration", nsmap):
        text = (duration.text or "").strip()
        if text and not (text.startswith("P") or text.startswith("PT")):
            result.add_error("BPMN_VALIDATION_FAILED", f"{path}: timeDuration not ISO-8601 {text}")

    # --- Phase 1 新規チェック: FlowNode incoming/outgoing 整合 ---
    flow_node_tags = ["startEvent", "endEvent", "serviceTask", "userTask",
                      "exclusiveGateway", "parallelGateway", "inclusiveGateway",
                      "intermediateCatchEvent", "intermediateThrowEvent",
                      "callActivity", "subProcess", "businessRuleTask",
                      "sendTask", "receiveTask", "scriptTask", "manualTask"]
    for process in processes:
        for tag in flow_node_tags:
            for node in process.findall(f"bpmn:{tag}", nsmap):
                node_id = node.get("id", "?")
                incoming = node.findall("bpmn:incoming", nsmap)
                outgoing = node.findall("bpmn:outgoing", nsmap)
                is_start = tag == "startEvent"
                is_end = tag == "endEvent"
                # Compensation handlers (isForCompensation="true") have no
                # incoming/outgoing — they are linked via association.
                is_compensation = node.get("isForCompensation") == "true"
                # Event subprocesses (triggeredByEvent="true") are triggered by
                # their start event, not by sequence flow.
                is_event_subprocess = (tag == "subProcess"
                                       and node.get("triggeredByEvent") == "true")
                if is_compensation or is_event_subprocess:
                    continue
                if not is_start and not incoming:
                    result.add_error("BPMN_VALIDATION_FAILED",
                                     f"{path}: {tag} '{node_id}' missing <incoming>")
                if not is_end and not outgoing:
                    result.add_error("BPMN_VALIDATION_FAILED",
                                     f"{path}: {tag} '{node_id}' missing <outgoing>")
                if is_start and incoming:
                    result.add_warning("BPMN_VALIDATION_FAILED",
                                       f"{path}: startEvent '{node_id}' should not have <incoming>")

    # --- Phase 1 新規チェック: boundaryEvent の attachedToRef ---
    for be in root.findall(".//bpmn:boundaryEvent", nsmap):
        be_id = be.get("id", "?")
        if not be.get("attachedToRef"):
            result.add_error("BPMN_VALIDATION_FAILED",
                             f"{path}: boundaryEvent '{be_id}' missing attachedToRef")
        # Compensation boundary events use association instead of outgoing flow
        is_compensation_boundary = be.find("bpmn:compensationEventDefinition", nsmap) is not None
        if not is_compensation_boundary and not be.findall("bpmn:outgoing", nsmap):
            result.add_error("BPMN_VALIDATION_FAILED",
                             f"{path}: boundaryEvent '{be_id}' missing <outgoing>")

    # --- v5.3.3 新規チェック: sequenceFlow の sourceRef / targetRef が実在する node を指すか ---
    for process in processes:
        process_node_ids = set()
        for tag in flow_node_tags + ["boundaryEvent"]:
            for node in process.findall(f"bpmn:{tag}", nsmap):
                nid = node.get("id")
                if nid:
                    process_node_ids.add(nid)
        for flow in process.findall("bpmn:sequenceFlow", nsmap):
            fid = flow.get("id", "?")
            src = flow.get("sourceRef")
            tgt = flow.get("targetRef")
            if src and src not in process_node_ids:
                result.add_error("BPMN_VALIDATION_FAILED",
                                 f"{path}: sequenceFlow '{fid}' sourceRef='{src}' not found in process")
            if tgt and tgt not in process_node_ids:
                result.add_error("BPMN_VALIDATION_FAILED",
                                 f"{path}: sequenceFlow '{fid}' targetRef='{tgt}' not found in process")

    # --- Phase 1 新規チェック: conditionExpression の xsi:type と空値 ---
    xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"
    for flow in root.findall(".//bpmn:sequenceFlow", nsmap):
        cond = flow.find("bpmn:conditionExpression", nsmap)
        if cond is not None:
            flow_id = flow.get("id", "?")
            cond_text = (cond.text or "").strip()
            if not cond_text:
                result.add_error("BPMN_VALIDATION_FAILED",
                                 f"{path}: conditionExpression empty on flow '{flow_id}'")
            xsi_type = cond.get(f"{{{xsi_ns}}}type")
            if not xsi_type:
                result.add_warning("BPMN_VALIDATION_FAILED",
                                   f"{path}: conditionExpression missing xsi:type on flow '{flow_id}'")
            elif xsi_type != "bpmn:tFormalExpression":
                result.add_warning("BPMN_VALIDATION_FAILED",
                                   f"{path}: conditionExpression xsi:type should be 'bpmn:tFormalExpression', found '{xsi_type}' on flow '{flow_id}'")

    # --- Phase 1 新規チェック: BPMNShape / BPMNEdge 完全性 ---
    if bpmndi_ns:
        di_nsmap = {"bpmndi": bpmndi_ns}
        shape_refs = set()
        for shape in root.findall(".//bpmndi:BPMNShape", di_nsmap):
            ref = shape.get("bpmnElement")
            if ref:
                shape_refs.add(ref)
        edge_refs = set()
        for edge in root.findall(".//bpmndi:BPMNEdge", di_nsmap):
            ref = edge.get("bpmnElement")
            if ref:
                edge_refs.add(ref)

        # Collect all flow node IDs and sequence flow IDs from process
        for process in processes:
            for tag in flow_node_tags + ["boundaryEvent"]:
                for node in process.findall(f"bpmn:{tag}", nsmap):
                    nid = node.get("id")
                    if nid and nid not in shape_refs:
                        result.add_error("BPMN_VALIDATION_FAILED",
                                         f"{path}: {tag} '{nid}' has no BPMNShape in diagram")
            for flow in process.findall("bpmn:sequenceFlow", nsmap):
                fid = flow.get("id")
                if fid and fid not in edge_refs:
                    result.add_error("BPMN_VALIDATION_FAILED",
                                     f"{path}: sequenceFlow '{fid}' has no BPMNEdge in diagram")

    # --- vertical swimlane enforcement: participant shapes must have isHorizontal="false" ---
    if bpmndi_ns:
        di_nsmap_local = {"bpmndi": bpmndi_ns}
        for shape in root.findall(".//bpmndi:BPMNShape", di_nsmap_local):
            # Check if this shape references a participant
            ref = shape.get("bpmnElement", "")
            is_participant = False
            for collab in root.findall("bpmn:collaboration", nsmap):
                for p in collab.findall("bpmn:participant", nsmap):
                    if p.get("id") == ref:
                        is_participant = True
                        break
            if is_participant:
                horiz = shape.get("isHorizontal")
                if horiz != "false":
                    result.add_error("BPMN_VALIDATION_FAILED",
                                     f"{path}: participant shape '{ref}' must have isHorizontal=\"false\" (vertical swimlane required)")

    # --- documentation missing warnings ---
    for process in processes:
        doc = process.find("bpmn:documentation", nsmap)
        if doc is None or not (doc.text and doc.text.strip()):
            result.add_warning("BPMN_DOCUMENTATION_MISSING",
                               f"{path}: process '{process.get('id', '?')}' has no <documentation>")
        doc_tags = ["userTask", "serviceTask", "businessRuleTask", "callActivity"]
        for tag in doc_tags:
            for node in process.findall(f"bpmn:{tag}", nsmap):
                nid = node.get("id", "?")
                d = node.find("bpmn:documentation", nsmap)
                if d is None or not (d.text and d.text.strip()):
                    result.add_warning("BPMN_DOCUMENTATION_MISSING",
                                       f"{path}: {tag} '{nid}' has no <documentation>")
        for gw in process.findall("bpmn:exclusiveGateway", nsmap):
            gid = gw.get("id", "?")
            outgoing = [o.text for o in gw.findall("bpmn:outgoing", nsmap) if o.text]
            if len(outgoing) > 1:
                d = gw.find("bpmn:documentation", nsmap)
                if d is None or not (d.text and d.text.strip()):
                    result.add_warning("BPMN_DOCUMENTATION_MISSING",
                                       f"{path}: exclusiveGateway '{gid}' has no <documentation>")
        for flow in process.findall("bpmn:sequenceFlow", nsmap):
            cond = flow.find("bpmn:conditionExpression", nsmap)
            if cond is not None:
                fid = flow.get("id", "?")
                d = flow.find("bpmn:documentation", nsmap)
                if d is None or not (d.text and d.text.strip()):
                    result.add_warning("BPMN_DOCUMENTATION_MISSING",
                                       f"{path}: conditional sequenceFlow '{fid}' has no <documentation>")

    return True


def _check_bpmn_placeholders(path, result):
    """Check for unresolved placeholders in BPMN files.

    Runs unconditionally (even before gate approval) so that users are warned
    about template tokens that must be replaced before deploy.
    """
    bpmn_placeholder_patterns = [
        r"\{\{[^}]+\}\}",            # {{プロセス名}}, {{form-id}}, {{job-type}} etc.
        r"BPMN-PROC-XXX",            # 未置換のプロセスID
    ]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            bpmn_text = fh.read()
        bpmn_placeholders = set()
        for pat in bpmn_placeholder_patterns:
            for m in re.finditer(pat, bpmn_text):
                bpmn_placeholders.add(m.group(0))
        if bpmn_placeholders:
            result.add_warning(
                "BPMN_PLACEHOLDER_PRESENT",
                f"{path}: unresolved placeholders: {', '.join(sorted(bpmn_placeholders))}",
            )
    except Exception:
        pass


def parse_bpmn_ids(path, result):
    try:
        tree = ET.parse(path)
    except Exception as exc:
        result.add_warning("BPMN_VALIDATION_FAILED", f"{path}: {exc}")
        return set()
    root = tree.getroot()
    ns = extract_namespaces(root)
    bpmn_ns = ns.get("bpmn")
    if not bpmn_ns:
        result.add_warning("BPMN_VALIDATION_FAILED", f"{path}: missing bpmn namespace")
        return set()
    nsmap = {"bpmn": bpmn_ns}
    ids = set()
    for elem in root.findall(".//*[@id]", nsmap):
        if elem.get("id"):
            ids.add(elem.get("id"))
    return ids


def validate_artifact_registry(path, result):
    if not path.exists():
        result.add_warning("MISSING_FILE", f"{path}")
        return
    blocks = extract_yaml_blocks(read_text(path))
    registry_block = next((b for b in blocks if "artifact_registry:" in b), None)
    if registry_block is None:
        result.add_warning("ARTIFACT_REGISTRY_INVALID", "artifact_registry block not found")
        return
    registry_doc = load_yaml(registry_block, str(path), result)
    if registry_doc is None:
        return
    registry_items = as_list(registry_doc.get("artifact_registry"))
    if not registry_items:
        result.add_warning("ARTIFACT_REGISTRY_INVALID", "artifact_registry is empty")
        return
    required_fields = ["artifact_id", "name", "phase", "owner_role", "approver_role"]
    for i, item in enumerate(registry_items):
        for field in required_fields:
            if not item.get(field):
                result.add_warning("ARTIFACT_REGISTRY_INVALID", f"item[{i}].{field} missing")
        if not as_list(item.get("domains")):
            result.add_warning("ARTIFACT_REGISTRY_INVALID", f"item[{i}].domains missing")
        storage = item.get("storage", {})
        if not storage.get("canonical_path"):
            result.add_warning("ARTIFACT_REGISTRY_INVALID", f"item[{i}].storage.canonical_path missing")
        if storage.get("single_source_of_truth") is not True:
            result.add_warning("ARTIFACT_REGISTRY_INVALID", f"item[{i}].storage.single_source_of_truth not true")


def validate_database_schema(path, result, id_conventions=None):
    """Validate database_schema.yaml (v1.2.5).

    Checks:
    - File exists and is valid YAML
    - Required sections: meta, tables
    - Each table has: name, columns, at least one column with primary_key
    - Audit columns (created_at, updated_at) if required
    - Foreign key references are valid
    - v1.2.5: schema_id regex validation against constitution.md
    """
    if not path.exists():
        # Database schema is optional
        return None

    try:
        content = read_text(path)
    except Exception as exc:
        result.add_error("DATABASE_SCHEMA_READ_ERROR", f"{path}: {exc}")
        return None

    schema_doc = load_yaml(content, str(path), result)
    if schema_doc is None:
        return None

    db_schema = schema_doc.get("database_schema", {})
    if not db_schema:
        result.add_warning("DATABASE_SCHEMA_INVALID", f"{path}: database_schema block not found")
        return None

    # Check meta
    meta = db_schema.get("meta", {})
    schema_id = meta.get("schema_id")
    if not schema_id:
        result.add_warning("DATABASE_SCHEMA_INVALID", f"{path}: meta.schema_id missing")
    elif id_conventions and "database_schema_id" in id_conventions:
        # v1.2.5: Validate schema_id against constitution regex
        db_schema_regex = compile_regex(id_conventions["database_schema_id"])
        if not db_schema_regex.match(schema_id):
            result.add_error("ID_REGEX_MISMATCH", f"database_schema.meta.schema_id: {schema_id} (expected pattern: {id_conventions['database_schema_id']})")
    if not meta.get("dialect"):
        result.add_warning("DATABASE_SCHEMA_INVALID", f"{path}: meta.dialect missing")

    # Check traceability
    traceability = db_schema.get("traceability", {})
    if not traceability.get("basic_design_ref"):
        result.add_warning("DATABASE_SCHEMA_INVALID", f"{path}: traceability.basic_design_ref missing")

    # Check tables
    tables = as_list(db_schema.get("tables"))
    if not tables:
        result.add_warning("DATABASE_SCHEMA_INVALID", f"{path}: no tables defined")
        return db_schema

    table_names = set()
    for i, table in enumerate(tables):
        table_name = table.get("name")
        if not table_name:
            result.add_error("DATABASE_SCHEMA_INVALID", f"{path}: tables[{i}].name missing")
            continue

        table_names.add(table_name)

        columns = as_list(table.get("columns"))
        if not columns:
            result.add_error("DATABASE_SCHEMA_INVALID", f"{path}: tables[{i}] ({table_name}) has no columns")
            continue

        # Check for primary key
        has_pk = any(col.get("primary_key") for col in columns)
        if not has_pk:
            result.add_warning("DATABASE_SCHEMA_INVALID", f"{path}: tables[{i}] ({table_name}) has no primary key")

        # Check column definitions
        col_names = set()
        for j, col in enumerate(columns):
            col_name = col.get("name")
            if not col_name:
                result.add_error("DATABASE_SCHEMA_INVALID", f"{path}: tables[{i}].columns[{j}].name missing")
                continue
            if col_name in col_names:
                result.add_error("DATABASE_SCHEMA_INVALID", f"{path}: tables[{i}] ({table_name}) duplicate column: {col_name}")
            col_names.add(col_name)

            if not col.get("type"):
                result.add_error("DATABASE_SCHEMA_INVALID", f"{path}: tables[{i}].columns[{j}] ({col_name}).type missing")

        # Check audit columns (optional warning)
        gate_check = schema_doc.get("database_schema_gate_check", {})
        rules = gate_check.get("rules", {})
        if rules.get("audit_columns_required"):
            audit_cols = {"created_at", "updated_at"}
            missing_audit = audit_cols - col_names
            if missing_audit:
                result.add_warning("DATABASE_SCHEMA_AUDIT_COLUMNS", f"{path}: tables[{i}] ({table_name}) missing audit columns: {', '.join(missing_audit)}")

    # Check relationships reference valid tables
    relationships = as_list(db_schema.get("relationships"))
    for i, rel in enumerate(relationships):
        from_table = rel.get("from_table")
        to_table = rel.get("to_table")
        if from_table and from_table not in table_names:
            result.add_warning("DATABASE_SCHEMA_INVALID", f"{path}: relationships[{i}].from_table '{from_table}' not found")
        if to_table and to_table not in table_names:
            result.add_warning("DATABASE_SCHEMA_INVALID", f"{path}: relationships[{i}].to_table '{to_table}' not found (may be external)")

    # v4.8.0: Description coverage check
    gate_check = schema_doc.get("database_schema_gate_check", {})
    rules = gate_check.get("rules", {}) if gate_check else {}

    check_table_desc = rules.get("all_tables_have_description")
    check_col_desc = rules.get("all_columns_have_description")

    if check_table_desc or check_col_desc:
        total_describable = 0
        total_described = 0

        for i, table in enumerate(tables):
            table_name = table.get("name", f"tables[{i}]")

            if check_table_desc:
                total_describable += 1
                if table.get("description"):
                    total_described += 1
                else:
                    result.add_warning(
                        "DATABASE_SCHEMA_MISSING_DESCRIPTION",
                        f"{path}: table '{table_name}' has no description"
                    )

            if check_col_desc:
                for j, col in enumerate(as_list(table.get("columns"))):
                    col_name = col.get("name", f"columns[{j}]")
                    total_describable += 1

                    if col.get("description"):
                        total_described += 1
                    else:
                        result.add_warning(
                            "DATABASE_SCHEMA_MISSING_DESCRIPTION",
                            f"{path}: table '{table_name}'.column '{col_name}' has no description"
                        )

        # Coverage ratio check — ERROR (gate) when below threshold
        min_coverage = rules.get("description_coverage_min", 0)
        if total_describable > 0 and min_coverage > 0:
            actual_coverage = total_described / total_describable
            if actual_coverage < min_coverage:
                result.add_error(
                    "DATABASE_SCHEMA_LOW_DESCRIPTION_COVERAGE",
                    f"{path}: description coverage {actual_coverage:.0%} < required {min_coverage:.0%} "
                    f"({total_described}/{total_describable} items described)"
                )

    return db_schema


def resolve_path(context, path):
    value = context
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def parse_expression(expr, context):
    match = re.match(r"^(.+?)\s*(==|!=|>=|<=|>|<)\s*(.+)$", expr)
    if not match:
        return None
    left_path, op, right_raw = match.groups()
    left = resolve_path(context, left_path.strip())
    right_raw = right_raw.strip()
    if right_raw in ("true", "false"):
        right = right_raw == "true"
    else:
        try:
            right = int(right_raw)
        except ValueError:
            try:
                right = float(right_raw)
            except ValueError:
                if re.match(r"^[A-Za-z_][A-Za-z0-9_\.]*$", right_raw):
                    right = resolve_path(context, right_raw)
                else:
                    right = right_raw.strip("\"'")
    return left, op, right


def evaluate_expression(expr, context, result=None):
    """Evaluate a gate expression.

    v1.2.5: Added result parameter for better error reporting.
    """
    parsed = parse_expression(expr, context)
    if parsed is None:
        if result:
            result.add_warning("GATE_EXPRESSION_PARSE_FAILED", f"Could not parse expression: {expr}")
        return False
    left, op, right = parsed

    # v1.2.5: Check for unresolved paths (None values)
    if left is None:
        if result:
            result.add_warning("GATE_EXPRESSION_UNRESOLVED", f"Left side of expression resolved to None: {expr}")
        return False

    try:
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == ">=":
            return left >= right
        if op == "<=":
            return left <= right
        if op == ">":
            return left > right
        if op == "<":
            return left < right
    except TypeError as e:
        if result:
            result.add_warning("GATE_EXPRESSION_TYPE_ERROR", f"Type error evaluating expression '{expr}': {e}")
        return False
    return False


def build_coverage_summary(spec_ac_items, plan_tests, plan_contracts):
    """Build a brief coverage summary (always shown, regardless of --coverage-report flag)."""
    all_ac = {ac.get("id") for ac in spec_ac_items if ac.get("id")}
    covered_ac = set()
    for test in plan_tests:
        covered_ac.update(as_list(test.get("covers_acceptance_ids")))
    covered_ac = {ac_id for ac_id in covered_ac if ac_id in all_ac}

    ac_total = len(all_ac)
    ac_covered = len(covered_ac)
    ac_pct = 0.0 if ac_total == 0 else round((ac_covered / ac_total) * 100.0, 1)

    all_ct = {c.get("id") for c in plan_contracts if c.get("id")}
    covered_ct = set()
    for test in plan_tests:
        if test.get("type") == "contract":
            covered_ct.update(as_list(test.get("covers_contract_ids")))
    covered_ct = {ct_id for ct_id in covered_ct if ct_id in all_ct}

    ct_total = len(all_ct)
    ct_covered = len(covered_ct)
    ct_pct = 0.0 if ct_total == 0 else round((ct_covered / ct_total) * 100.0, 1)

    return {
        "ac_covered": ac_covered,
        "ac_total": ac_total,
        "ac_pct": ac_pct,
        "ct_covered": ct_covered,
        "ct_total": ct_total,
        "ct_pct": ct_pct,
    }


def build_coverage_report(feature_id, spec_ac_items, plan_tests, plan_contracts, tasks):
    all_ac = {ac.get("id") for ac in spec_ac_items if ac.get("id")}
    covered_ac = set()
    for test in plan_tests:
        covered_ac.update(as_list(test.get("covers_acceptance_ids")))
    covered_ac = {ac_id for ac_id in covered_ac if ac_id in all_ac}
    uncovered_ac = sorted(all_ac - covered_ac)
    ac_total = len(all_ac)
    ac_covered = len(covered_ac)

    def pct(part, total):
        return 0.0 if total == 0 else round((part / total) * 100.0, 1)

    tagged = {
        "integration": {
            ac.get("id")
            for ac in spec_ac_items
            if ac.get("id") and "integration" in as_list(ac.get("tags", []))
        },
        "e2e": {
            ac.get("id")
            for ac in spec_ac_items
            if ac.get("id") and "e2e" in as_list(ac.get("tags", []))
        },
    }

    integration_covered = set()
    e2e_covered = set()
    for test in plan_tests:
        if test.get("type") == "integration":
            integration_covered.update(as_list(test.get("covers_acceptance_ids")))
        if test.get("type") == "e2e":
            e2e_covered.update(as_list(test.get("covers_acceptance_ids")))

    tagged_integration = sorted(tagged["integration"] - integration_covered)
    tagged_e2e = sorted(tagged["e2e"] - e2e_covered)

    all_ct = {c.get("id") for c in plan_contracts if c.get("id")}
    covered_ct = set()
    for test in plan_tests:
        if test.get("type") == "contract":
            covered_ct.update(as_list(test.get("covers_contract_ids")))
    uncovered_ct = sorted(all_ct - covered_ct)

    all_ts = {t.get("id") for t in plan_tests if t.get("id")}
    tasked_ts = set()
    for task in tasks:
        for ref in as_list(task.get("plan_refs")):
            if ref.startswith("TS-"):
                tasked_ts.add(ref)
    untasked_ts = sorted(all_ts - tasked_ts)

    report = {
        "coverage_report": {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "feature": feature_id,
            "acceptance_coverage": {
                "total_ac": ac_total,
                "covered_ac": ac_covered,
                "coverage_pct": pct(ac_covered, ac_total),
                "uncovered": uncovered_ac,
            },
            "tagged_coverage": {
                "integration": {
                    "total_tagged": len(tagged["integration"]),
                    "covered_by_int": len(tagged["integration"] & integration_covered),
                    "coverage_pct": pct(len(tagged["integration"] & integration_covered), len(tagged["integration"])),
                    "uncovered": tagged_integration,
                },
                "e2e": {
                    "total_tagged": len(tagged["e2e"]),
                    "covered_by_e2e": len(tagged["e2e"] & e2e_covered),
                    "coverage_pct": pct(len(tagged["e2e"] & e2e_covered), len(tagged["e2e"])),
                    "uncovered": tagged_e2e,
                },
            },
            "contract_coverage": {
                "total_ct": len(all_ct),
                "covered_ct": len(all_ct - set(uncovered_ct)),
                "coverage_pct": pct(len(all_ct) - len(uncovered_ct), len(all_ct)),
                "uncovered": uncovered_ct,
            },
            "test_tasking": {
                "total_ts": len(all_ts),
                "tasked_ts": len(all_ts - set(untasked_ts)),
                "coverage_pct": pct(len(all_ts) - len(untasked_ts), len(all_ts)),
                "untasked": untasked_ts,
            },
            "summary": {
                "ac_coverage_pass": not uncovered_ac,
                "tagged_coverage_pass": not tagged_integration and not tagged_e2e,
                "contract_coverage_pass": not uncovered_ct,
                "test_tasking_pass": not untasked_ts,
                "overall_pass": not (uncovered_ac or tagged_integration or tagged_e2e or uncovered_ct or untasked_ts),
            },
        }
    }
    return report


def lint_feature(feature_dir, config):
    result = LintResult(feature_dir)
    feature_dir = Path(feature_dir)
    if not feature_dir.exists():
        result.add_error("MISSING_FILE", f"{feature_dir} not found")
        return result

    basic_design_path = feature_dir / "basic_design.md"
    spec_path = feature_dir / "spec.md"
    plan_path = feature_dir / "plan.md"
    tasks_path = feature_dir / "tasks.md"
    bpmn_path = feature_dir / "process.bpmn"

    for path in [basic_design_path, spec_path, plan_path, tasks_path]:
        if not path.exists():
            result.add_error("MISSING_FILE", f"{path}")

    if result.errors:
        return result

    root_dir = feature_dir.parent.parent
    constitution_path = root_dir / "memory" / "constitution.md"
    artifact_registry_path = root_dir / "memory" / "artifact_registry.md"

    if not constitution_path.exists():
        result.add_error("MISSING_FILE", f"{constitution_path}")
        return result

    constitution_text = read_text(constitution_path)
    constitution_blocks = extract_yaml_blocks(constitution_text)
    id_block = next((b for b in constitution_blocks if "id_conventions:" in b), None)
    gates_block = next((b for b in constitution_blocks if "gates:" in b), None)
    if id_block is None:
        result.add_error("CANONICAL_BLOCK_NOT_FOUND", "constitution id_conventions")
        return result
    id_conventions = load_yaml(id_block, "constitution id_conventions", result)
    if id_conventions is None:
        return result
    id_conventions = id_conventions.get("id_conventions", {})
    gates = []
    if gates_block is None:
        result.add_error("CANONICAL_BLOCK_NOT_FOUND", "constitution gates")
    else:
        gates_doc = load_yaml(gates_block, "constitution gates", result)
        if gates_doc is not None:
            gates = as_list(gates_doc.get("gates"))

    validate_artifact_registry(artifact_registry_path, result)

    # --- Extension Pack check (generic) ---
    ext_config_path = root_dir / ".stride-extensions.yaml"
    active_ext_names = []
    if ext_config_path.is_file():
        try:
            ext_config = yaml.safe_load(ext_config_path.read_text(encoding="utf-8")) or {}
            active_ext_names = ext_config.get("active_extensions") or []
        except Exception:
            pass
    else:
        extensions_check_dir = root_dir / "extensions"
        if extensions_check_dir.is_dir():
            available_exts = [
                d.name for d in sorted(extensions_check_dir.iterdir())
                if d.is_dir() and (d / "MANIFEST.yaml").is_file()
            ]
            if available_exts:
                result.add_warning(
                    "EXTENSIONS_NOT_CONFIGURED",
                    f".stride-extensions.yaml が存在しません。利用可能な拡張パック: {available_exts}。"
                    f"`stride init` を実行するか、手動で .stride-extensions.yaml を作成してください"
                )

    _extension_tools = []  # [(func, ext_name), ...]

    extensions_dir = root_dir / "extensions"
    if active_ext_names and extensions_dir.is_dir():
        for ext_dir in sorted(extensions_dir.iterdir()):
            if ext_dir.name not in active_ext_names:
                continue
            manifest_path = ext_dir / "MANIFEST.yaml"
            if not manifest_path.is_file():
                continue
            try:
                manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
            except Exception:
                continue
            ext_cfg = manifest.get("extension", {})

            ep_cfg = ext_cfg.get("evidence_pack", {})
            if ep_cfg:
                ext_name = ext_cfg.get("name", ext_dir.name)
                ext_storage_key = ep_cfg.get("storage_key")
                if ext_storage_key:
                    ep_md_path = feature_dir / "implementation-details" / "evidence_pack.md"
                    if not ep_md_path.is_file():
                        result.add_error("MISSING_FILE",
                            f"implementation-details/evidence_pack.md (required by extension '{ext_name}')")
                    else:
                        ep_md_blocks = extract_yaml_blocks(read_text(ep_md_path))
                        ep_md_doc = {}
                        for blk in ep_md_blocks:
                            parsed = load_yaml(blk, "evidence_pack.md", result)
                            if parsed:
                                ep_md_doc.update(parsed)
                        ep_md_storage = ep_md_doc.get("evidence_pack", {}).get("storage", {})
                        ext_path = ep_md_storage.get(ext_storage_key)
                        if not ext_path:
                            result.add_error("EVIDENCE_PACK_EXTENSION_NOT_DEFINED",
                                f"Extension '{ext_name}' requires evidence_pack.storage.{ext_storage_key} in evidence_pack.md")

                mapping_rel = ep_cfg.get("category_mapping")
                if mapping_rel:
                    mapping_file = ext_dir / mapping_rel
                    if not mapping_file.is_file():
                        result.add_error("EVIDENCE_PACK_CATEGORY_MAPPING_MISSING",
                            f"Extension '{ext_name}': {mapping_rel} not found")

            tools_dir = ext_dir / "tools"
            if tools_dir.is_dir() and str(tools_dir) not in sys.path:
                sys.path.insert(0, str(tools_dir))
            for tool_cfg in ext_cfg.get("tools", []):
                trigger = tool_cfg.get("trigger", "always")
                if trigger != "always":
                    continue
                try:
                    mod = __import__(tool_cfg["module"])
                    func = getattr(mod, tool_cfg["function"])
                    tool_ext_name = ext_cfg.get("name", ext_dir.name)
                    _extension_tools.append((func, tool_ext_name))
                except (ImportError, AttributeError, KeyError):
                    pass
    # --- End Extension Pack check ---

    # v1.2.5: Validate database schema if exists (with id_conventions for regex validation)
    db_schema_path = feature_dir / "contracts" / "database_schema.yaml"
    db_schema = validate_database_schema(db_schema_path, result, id_conventions)

    basic_design_text = read_text(basic_design_path)
    basic_block = extract_yaml_after_marker(basic_design_text, "Canonical Basic Design")
    basic_gate_block = extract_yaml_after_marker(basic_design_text, "basic_design_gate_check")
    if basic_block is None or basic_gate_block is None:
        result.add_error("CANONICAL_BLOCK_NOT_FOUND", "basic_design")
        return result

    check_placeholders("basic_design", basic_block, result)
    basic_doc = load_yaml(basic_block, str(basic_design_path), result)
    basic_gate_doc = load_yaml(basic_gate_block, str(basic_design_path), result)
    if basic_doc is None or basic_gate_doc is None:
        return result

    spec_block = extract_yaml_after_marker(read_text(spec_path), "Canonical Spec")
    plan_block = extract_yaml_after_marker(read_text(plan_path), "Canonical Plan")
    tasks_block = extract_yaml_after_marker(read_text(tasks_path), "Canonical Tasks")
    if spec_block is None or plan_block is None or tasks_block is None:
        result.add_error("CANONICAL_BLOCK_NOT_FOUND", "spec/plan/tasks")
        return result

    check_placeholders("spec", spec_block, result)
    check_placeholders("plan", plan_block, result)
    check_placeholders("tasks", tasks_block, result)

    spec_doc = load_yaml(spec_block, str(spec_path), result)
    plan_doc = load_yaml(plan_block, str(plan_path), result)
    tasks_doc = load_yaml(tasks_block, str(tasks_path), result)
    if spec_doc is None or plan_doc is None or tasks_doc is None:
        return result

    check_path_naming(basic_doc, result, "basic_design")
    check_path_naming(spec_doc, result, "spec")
    check_path_naming(plan_doc, result, "plan")
    check_path_naming(tasks_doc, result, "tasks")

    frontmatter = extract_frontmatter(read_text(spec_path))
    feature_id = None
    if frontmatter:
        front_doc = load_yaml(frontmatter, f"{spec_path} frontmatter", result)
        if front_doc:
            feature_id = front_doc.get("feature_id")

    regex = {k: compile_regex(v) for k, v in id_conventions.items()}

    # v1.2.5: Validate feature_id from frontmatter
    if feature_id and "feature_id" in regex:
        if not regex["feature_id"].match(feature_id):
            result.add_error("ID_REGEX_MISMATCH", f"frontmatter.feature_id: {feature_id} (expected pattern: {id_conventions['feature_id']})")

    basic_section = basic_doc.get("basic_design", {})

    # v5.4: Profile consistency (basic_design.profile SSoT + state.yaml top-level cache)
    check_profile_consistency(feature_dir, basic_section, result)

    basic_counts, trace_rows = compute_basic_counts(basic_section)
    for i, row in enumerate(trace_rows):
        rq = row.get("rq", {}).get("id")
        us = row.get("us", {}).get("id")
        ac = row.get("ac", {}).get("id")
        check_id(regex["requirement_id"], rq, True, result, f"traceability_rows[{i}].rq.id")
        check_id(regex["use_case_id"], us, True, result, f"traceability_rows[{i}].us.id")
        check_id(regex["acceptance_id"], ac, True, result, f"traceability_rows[{i}].ac.id")
    for i, q in enumerate(as_list(basic_section.get("open_questions"))):
        check_id(regex["question_id"], q.get("id"), False, result, f"basic_design.open_questions[{i}].id")
    for i, a in enumerate(as_list(basic_section.get("assumptions"))):
        check_id(regex["assumption_id"], a.get("id"), False, result, f"basic_design.assumptions[{i}].id")
    for i, d in enumerate(as_list(basic_section.get("decisions"))):
        check_id(regex["decision_id"], d.get("id"), False, result, f"basic_design.decisions[{i}].id")

    spec_counts, spec_use_cases, spec_ac_items, spec_as_code_artifacts = compute_spec_counts(spec_doc.get("spec", {}))
    spec_use_case_ids = [uc.get("id") for uc in spec_use_cases if uc.get("id")]
    spec_ac_ids = [ac.get("id") for ac in spec_ac_items if ac.get("id")]
    check_duplicates(spec_use_case_ids, result, "spec.use_cases")
    check_duplicates(spec_ac_ids, result, "spec.acceptance")
    for i, uc in enumerate(spec_use_cases):
        check_id(regex["use_case_id"], uc.get("id"), False, result, f"spec.use_cases[{i}].id")
        for j, ac in enumerate(as_list(uc.get("acceptance"))):
            check_id(regex["acceptance_id"], ac.get("id"), False, result, f"spec.use_cases[{i}].acceptance[{j}].id")
    for i, q in enumerate(as_list(spec_doc.get("spec", {}).get("open_questions"))):
        check_id(regex["question_id"], q.get("id"), False, result, f"spec.open_questions[{i}].id")
    for i, a in enumerate(as_list(spec_doc.get("spec", {}).get("assumptions"))):
        check_id(regex["assumption_id"], a.get("id"), False, result, f"spec.assumptions[{i}].id")

    plan_counts, plan_contracts, plan_tests, plan_phases = compute_plan_counts(plan_doc.get("plan", {}))
    plan_contract_ids = [c.get("id") for c in plan_contracts if c.get("id")]
    plan_test_ids = [t.get("id") for t in plan_tests if t.get("id")]
    check_duplicates(plan_contract_ids, result, "plan.contracts")
    check_duplicates(plan_test_ids, result, "plan.tests")
    for i, c in enumerate(as_list(plan_doc.get("plan", {}).get("architecture", {}).get("components"))):
        check_id(regex["component_id"], c.get("id"), False, result, f"plan.components[{i}].id")
    for i, l in enumerate(as_list(plan_doc.get("plan", {}).get("architecture", {}).get("libraries"))):
        check_id(regex["library_id"], l.get("id"), False, result, f"plan.libraries[{i}].id")
    for i, c in enumerate(as_list(plan_doc.get("plan", {}).get("contracts", {}).get("cli"))):
        check_id(regex["contract_id"], c.get("id"), False, result, f"plan.contracts.cli[{i}].id")
    for i, c in enumerate(as_list(plan_doc.get("plan", {}).get("contracts", {}).get("apis_events"))):
        check_id(regex["contract_id"], c.get("id"), False, result, f"plan.contracts.apis_events[{i}].id")
    for i, c in enumerate(as_list(plan_doc.get("plan", {}).get("contracts", {}).get("database", {}).get("tables"))):
        check_id(regex["contract_id"], c.get("id"), False, result, f"plan.contracts.database.tables[{i}].id")
    for i, t in enumerate(plan_tests):
        check_id(regex["test_id"], t.get("id"), False, result, f"plan.tests[{i}].id")
    for i, phase in enumerate(plan_phases):
        check_id(regex["phase_id"], phase.get("id"), False, result, f"plan.phases[{i}].id")
        group_ids = [g.get("id") for g in as_list(phase.get("groups")) if g.get("id")]
        check_duplicates(group_ids, result, f"plan.phases[{i}].groups")
        for j, group in enumerate(as_list(phase.get("groups"))):
            check_id(regex["group_id"], group.get("id"), False, result, f"plan.phases[{i}].groups[{j}].id")

    tasks_counts, task_items = compute_tasks_counts(tasks_doc.get("tasks", {}))
    task_ids = [t.get("id") for t in task_items if t.get("id")]
    check_duplicates(task_ids, result, "tasks.tasks")
    for i, task in enumerate(task_items):
        check_id(regex["task_id"], task.get("id"), False, result, f"tasks.tasks[{i}].id")
    for i, milestone in enumerate(as_list(tasks_doc.get("tasks", {}).get("milestones"))):
        check_id(regex["milestone_id"], milestone.get("id"), False, result, f"tasks.milestones[{i}].id")
    for i, risk in enumerate(as_list(tasks_doc.get("tasks", {}).get("risks"))):
        check_id(regex["risk_id"], risk.get("id"), False, result, f"tasks.risks[{i}].id")

    spec_use_case_set = set(spec_use_case_ids)
    spec_ac_set = set(spec_ac_ids)
    for i, row in enumerate(trace_rows):
        us_id = row.get("us", {}).get("id")
        ac_id = row.get("ac", {}).get("id")
        if us_id and us_id not in spec_use_case_set:
            result.add_error("REF_NOT_FOUND", f"traceability_rows[{i}].us.id {us_id}")
        if ac_id and ac_id not in spec_ac_set:
            result.add_error("REF_NOT_FOUND", f"traceability_rows[{i}].ac.id {ac_id}")

    plan_scope = as_list(plan_doc.get("plan", {}).get("scope", {}).get("in_use_cases"))
    if not plan_scope:
        result.add_error("GATE_FAILED", "plan.scope.in_use_cases is empty")
    for us_id in plan_scope:
        if us_id not in spec_use_case_set:
            result.add_error("REF_NOT_FOUND", f"plan.scope.in_use_cases {us_id}")

    for i, test in enumerate(plan_tests):
        for ac_id in as_list(test.get("covers_acceptance_ids")):
            if ac_id not in spec_ac_set:
                result.add_error("REF_NOT_FOUND", f"plan.tests[{i}].covers_acceptance_ids {ac_id}")
        for ct_id in as_list(test.get("covers_contract_ids")):
            if ct_id not in plan_contract_ids:
                result.add_error("REF_NOT_FOUND", f"plan.tests[{i}].covers_contract_ids {ct_id}")

    for i, task in enumerate(task_items):
        for ref in as_list(task.get("spec_refs")):
            if ref.startswith("US-") and ref not in spec_use_case_set:
                result.add_error("REF_NOT_FOUND", f"tasks.tasks[{i}].spec_refs {ref}")
            if ref.startswith("AC-") and ref not in spec_ac_set:
                result.add_error("REF_NOT_FOUND", f"tasks.tasks[{i}].spec_refs {ref}")

    stable_ids = set()
    stable_ids.update({c.get("id") for c in as_list(plan_doc.get("plan", {}).get("architecture", {}).get("components"))})
    stable_ids.update({l.get("id") for l in as_list(plan_doc.get("plan", {}).get("architecture", {}).get("libraries"))})
    stable_ids.update({c.get("id") for c in plan_contracts})
    stable_ids.update({t.get("id") for t in plan_tests})
    stable_ids.update({p.get("id") for p in plan_phases})
    for phase in plan_phases:
        stable_ids.update({g.get("id") for g in as_list(phase.get("groups"))})
    for i, task in enumerate(task_items):
        for ref in as_list(task.get("plan_refs")):
            if ref not in stable_ids:
                result.add_error("INVALID_PLAN_REF", f"tasks.tasks[{i}].plan_refs {ref}")

    all_ac = set(spec_ac_set)
    covered_ac = set()
    for test in plan_tests:
        covered_ac.update(as_list(test.get("covers_acceptance_ids")))
    missing_ac = sorted(all_ac - covered_ac)
    if missing_ac:
        result.add_error("AC_NOT_COVERED", f"Missing AC: {', '.join(missing_ac)}")

    coverage_policy = plan_doc.get("plan", {}).get("test_strategy", {}).get("coverage_policy")
    if coverage_policy is None:
        result.add_warning("COVERAGE_POLICY_NOT_DEFINED", "plan.test_strategy.coverage_policy is missing")
        coverage_policy = {}

    tagged_requirements = coverage_policy.get("tagged_acceptance_requirements", {})
    ac_by_tag = {
        "integration": {ac.get("id") for ac in spec_ac_items if "integration" in as_list(ac.get("tags"))},
        "e2e": {ac.get("id") for ac in spec_ac_items if "e2e" in as_list(ac.get("tags"))},
    }

    # v1.2.4: E2E tag limit warning (Issue-009)
    # E2E tests are expensive; warn if too many ACs are tagged as e2e
    e2e_count = len(ac_by_tag.get("e2e", set()))
    total_ac_count = len(spec_ac_items)
    e2e_pct = (e2e_count / total_ac_count * 100) if total_ac_count > 0 else 0

    E2E_MAX_COUNT = 5
    E2E_MAX_PCT = 20

    if e2e_count > E2E_MAX_COUNT or e2e_pct > E2E_MAX_PCT:
        result.add_warning(
            "E2E_TAG_OVERUSE",
            f"e2e tag applied to {e2e_count}/{total_ac_count} ACs ({e2e_pct:.1f}%). "
            f"E2E tests are expensive; consider limiting to critical user journeys only "
            f"(recommended: max {E2E_MAX_COUNT} or {E2E_MAX_PCT}%)"
        )

    for tag, requirement in tagged_requirements.items():
        if requirement.get("enforce") is True:
            required_type = requirement.get("required_test_type")
            covered = set()
            for test in plan_tests:
                if test.get("type") == required_type:
                    covered.update(as_list(test.get("covers_acceptance_ids")))
            missing = sorted(ac_by_tag.get(tag, set()) - covered)
            if missing:
                result.add_error("TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE", f"{tag}: {', '.join(missing)}")

    if coverage_policy.get("contract_coverage_required") is True:
        all_ct = set(plan_contract_ids)
        covered_ct = set()
        for test in plan_tests:
            if test.get("type") == "contract":
                covered_ct.update(as_list(test.get("covers_contract_ids")))
        missing_ct = sorted(all_ct - covered_ct)
        if missing_ct:
            result.add_error("CONTRACT_COVERAGE_INCOMPLETE", f"Missing CT: {', '.join(missing_ct)}")

    if coverage_policy.get("tests_must_be_tasked") is True:
        all_ts = {t.get("id") for t in plan_tests}
        tasked_ts = set()
        for task in task_items:
            for ref in as_list(task.get("plan_refs")):
                if ref.startswith("TS-"):
                    tasked_ts.add(ref)
        missing_ts = sorted(all_ts - tasked_ts)
        if missing_ts:
            result.add_error("TEST_NOT_TASKED", f"Missing TS: {', '.join(missing_ts)}")

    has_e2e = any(t.get("type") == "e2e" for t in plan_tests)
    reporting = plan_doc.get("plan", {}).get("test_strategy", {}).get("reporting", {}).get("e2e", {})
    if has_e2e and not reporting.get("artifacts_dir"):
        result.add_warning("E2E_REPORTING_NOT_CONFIGURED", "reporting.e2e.artifacts_dir is empty")

    if has_e2e:
        triage_found = False
        for task in task_items:
            for output in as_list(task.get("outputs")):
                if isinstance(output, str) and output.endswith("e2e-triage.md"):
                    triage_found = True
        triage_path = feature_dir / "implementation-details" / "e2e-triage.md"
        if not triage_found and not triage_path.exists():
            result.add_warning("E2E_TRIAGE_NOT_DEFINED", f"{triage_path} missing")

    spec_gate = spec_doc.get("spec_gate_check", {})
    plan_gate = plan_doc.get("plan_gate_check", {})
    tasks_gate = tasks_doc.get("tasks_gate_check", {})
    basic_gate = basic_gate_doc.get("basic_design_gate_check", {})

    # v1.2.4: Show suggestion only for derived_fields (first call), not for gate_check
    compare_counts("basic_design.derived_fields", basic_doc.get("derived_fields", {}).get("counts", {}), basic_counts, result, show_all_mismatches=True)
    compare_counts("basic_design.gate_check", basic_gate.get("counts", {}), basic_counts, result, show_all_mismatches=False)
    compare_counts("spec.derived_fields", spec_doc.get("derived_fields", {}).get("counts", {}), spec_counts, result, show_all_mismatches=True)
    compare_counts("spec.gate_check", spec_gate.get("counts", {}), spec_counts, result, show_all_mismatches=False)
    compare_counts("plan.derived_fields", plan_doc.get("derived_fields", {}).get("counts", {}), plan_counts, result, show_all_mismatches=True)
    compare_counts("plan.gate_check", plan_gate.get("counts", {}), plan_counts, result, show_all_mismatches=False)
    compare_counts("tasks.derived_fields", tasks_doc.get("derived_fields", {}).get("counts", {}), tasks_counts, result, show_all_mismatches=True)
    compare_counts("tasks.gate_check", tasks_gate.get("counts", {}), tasks_counts, result, show_all_mismatches=False)

    if spec_gate.get("spec_as_code_defined") is True:
        if not spec_as_code_artifacts:
            result.add_error("SPEC_AS_CODE_MISSING", "spec.spec_as_code.artifacts is empty")
        for i, artifact in enumerate(spec_as_code_artifacts):
            if not artifact.get("path"):
                result.add_error("SPEC_AS_CODE_MISSING", f"spec.spec_as_code.artifacts[{i}].path is empty")

    evidence_pack = plan_doc.get("plan", {}).get("test_strategy", {}).get("evidence_pack", {})
    if plan_gate.get("evidence_pack_defined") is True:
        required_artifacts = as_list(evidence_pack.get("required_artifacts"))
        storage_path = evidence_pack.get("storage", {}).get("path")
        if not required_artifacts or not storage_path:
            result.add_error("EVIDENCE_PACK_NOT_DEFINED", "plan.test_strategy.evidence_pack is incomplete")

    # testreport integration check
    try:
        from stride_testreport_bridge import check_testreport_integration
        tr_result = check_testreport_integration(feature_dir)
        if tr_result:
            if tr_result.get("report_missing"):
                result.add_warning("TESTREPORT_REPORT_MISSING",
                    "testreport cases.json found but report.html is missing (run: testreport generate)")
            if tr_result.get("validate_failed"):
                result.add_warning("TESTREPORT_VALIDATE_FAILED",
                    f"testreport validate failed: {tr_result.get('validate_message', '')}")
            if tr_result.get("unmapped_cases"):
                unmapped = ", ".join(tr_result["unmapped_cases"])
                result.add_warning("TESTREPORT_UNMAPPED_CASES",
                    f"testreport cases not mapped to STRIDE ACs: {unmapped}")
    except ImportError:
        pass

    process_path_ref = basic_section.get("flow_reference", {}).get("process_bpmn_path")
    if process_path_ref:
        resolved = normalize_path(root_dir, process_path_ref)
        if not resolved.exists():
            result.add_error("MISSING_FILE", f"{process_path_ref}")

    if bpmn_path.exists():
        # Placeholder check runs unconditionally (even before gate approval)
        _check_bpmn_placeholders(bpmn_path, result)
        if basic_gate.get("ready_for_specify") is True:
            validate_bpmn(bpmn_path, result)
        bpmn_ids = parse_bpmn_ids(bpmn_path, result)
        for phase in plan_phases:
            for group in as_list(phase.get("groups")):
                for ref in as_list(group.get("bpmn_refs")):
                    if ref not in bpmn_ids:
                        result.add_warning("REF_NOT_FOUND", f"plan.groups.bpmn_refs {ref}")
        for i, task in enumerate(task_items):
            for ref in as_list(task.get("bpmn_refs")):
                if ref not in bpmn_ids:
                    result.add_warning("REF_NOT_FOUND", f"tasks.tasks[{i}].bpmn_refs {ref}")
        # --- YAML↔BPMN 双方向連動チェック ---
        bd_bpmn_descs = basic_section.get("bpmn_descriptions") if basic_section else None
        yaml_described_ids = set()
        if bd_bpmn_descs:
            # Forward: process_id check
            proc_id = bd_bpmn_descs.get("process", {}).get("process_id", "")
            if proc_id and proc_id not in bpmn_ids:
                result.add_warning("BPMN_ID_MISMATCH",
                                   f"bpmn_descriptions.process.process_id '{proc_id}' not found in process.bpmn")
            # Forward: elements check
            for elem in as_list(bd_bpmn_descs.get("elements")):
                bid = elem.get("bpmn_id", "")
                if bid:
                    yaml_described_ids.add(bid)
                    if bid not in bpmn_ids:
                        result.add_warning("BPMN_ID_MISMATCH",
                                           f"bpmn_descriptions.elements bpmn_id '{bid}' not found in process.bpmn")
        # Forward: traceability_rows bpmn.id check (separate from bpmn_descriptions coverage)
        for i, row in enumerate(trace_rows):
            bpmn_ref = row.get("bpmn", {})
            bid = bpmn_ref.get("id", "") if isinstance(bpmn_ref, dict) else ""
            if bid and bid not in bpmn_ids:
                result.add_warning("BPMN_ID_MISMATCH",
                                   f"traceability_rows[{i}].bpmn.id '{bid}' not found in process.bpmn")
        # Reverse: BPMN business elements not described in bpmn_descriptions
        # Note: yaml_described_ids contains ONLY bpmn_descriptions entries (not traceability_rows),
        # because bpmn_descriptions is the business description SSoT, while traceability_rows
        # is the AC/Contract/Test SSoT — different responsibilities per design.
        if bd_bpmn_descs and bpmn_ids:
            try:
                tree = ET.parse(bpmn_path)
                root = tree.getroot()
                ns_local = extract_namespaces(root)
                bpmn_ns_local = ns_local.get("bpmn")
            except Exception:
                bpmn_ns_local = None
            if bpmn_ns_local:
                nsm = {"bpmn": bpmn_ns_local}
                business_tags = ["userTask", "serviceTask", "businessRuleTask",
                                 "exclusiveGateway", "callActivity"]
                for proc in root.findall("bpmn:process", nsm):
                    for tag in business_tags:
                        for node in proc.findall(f"bpmn:{tag}", nsm):
                            nid = node.get("id", "")
                            # Skip merge gateways (single outgoing) — structural, not business decisions
                            if tag == "exclusiveGateway":
                                outgoing = node.findall("bpmn:outgoing", nsm)
                                if len(outgoing) <= 1:
                                    continue
                            if nid and nid not in yaml_described_ids:
                                result.add_warning("BPMN_ID_NOT_DESCRIBED",
                                                   f"{tag} '{nid}' in process.bpmn has no entry in bpmn_descriptions")
    else:
        result.add_warning("MISSING_FILE", f"{bpmn_path}")

    gate_context = {
        "basic_design_gate_check": dict(basic_gate, counts=basic_counts),
        "spec_gate_check": dict(spec_gate, counts=spec_counts),
        "plan_gate_check": dict(plan_gate, counts=plan_counts),
        "tasks_gate_check": dict(tasks_gate, counts=tasks_counts),
    }

    for gate in gates:
        name = gate.get("name", "Gate")
        for expr in as_list(gate.get("requires")):
            # v4.7.0: Only evaluate expressions whose root key exists in gate_context.
            # Epic-level gates (epic_gate_check, breakdown_gate_check, etc.) are not
            # resolvable during feature lint — skip them to avoid false GATE_FAILED errors
            # while preserving enforcement for feature-level gates.
            root_key = expr.split(".")[0] if isinstance(expr, str) else ""
            if root_key and root_key not in gate_context:
                continue  # Not applicable to this lint scope
            if not evaluate_expression(expr, gate_context, result):
                result.add_error("GATE_FAILED", f"{name}: {expr}")

    # v1.2.4: Always build coverage summary (shown by default)
    result.coverage_summary = build_coverage_summary(spec_ac_items, plan_tests, plan_contracts)

    if config.coverage_report:
        result.coverage_report = build_coverage_report(
            feature_id or feature_dir.name,
            spec_ac_items,
            plan_tests,
            plan_contracts,
            task_items,
        )

    # Human Approval Check (HITL)
    # Check approval status for all gates that should have passed by now
    # Gate progression: 1 (Basic) -> 2 (BPMN) -> 3 (Spec) -> 4 (Plan) -> 5 (Tasks) -> Final
    gates_to_check = []

    # Determine which gates to check based on document readiness
    if basic_gate.get("ready_for_bpmn") is True:
        gates_to_check.append(1)
    if basic_gate.get("ready_for_specify") is True:
        gates_to_check.append(2)
    if spec_gate.get("ai_plan_ready") is True:
        gates_to_check.append(3)
    if plan_gate.get("ai_tasks_ready") is True:
        gates_to_check.append(4)
    if tasks_gate.get("tasks_ready_for_code") is True:
        gates_to_check.append(5)

    # Only check approval if there are gates marked as ready
    approval_statuses = {}
    if gates_to_check:
        approval_statuses = check_approval(feature_dir, gates_to_check, result)

        # v1.2.4: Check for post-approval changes
        approved_gates = {gate for gate, approved in approval_statuses.items() if approved}
        check_post_approval_changes(feature_dir, approved_gates, result)

    # v2.1.0: ERP Addon execution tracking validation (opt-in)
    # Activates when work_items/ exists or execution_profile: erp_addon is set
    try:
        from erp_addon_exec_tracking import validate_erp_addon_execution_tracking
        # Extract coverage_tier from basic_design (default: standard)
        bd = basic_doc.get("basic_design", {})
        coverage_tier = bd.get("coverage_tier") or "standard"

        # v4.5.1: Tier mismatch detection
        # Warn if existing flags suggest a different tier than what's declared
        if coverage_tier == "standard":
            _tier_hints = []
            if bd.get("security_sensitive"):
                _tier_hints.append("security_sensitive=true")
            if bd.get("erp_integration"):
                _tier_hints.append("erp_integration=true")
            if _tier_hints:
                result.add_warning(
                    "TIER_MISMATCH",
                    f"coverage_tier is 'standard' but {', '.join(_tier_hints)} "
                    f"suggests 'critical'. Consider updating coverage_tier."
                )

        # Run ERP Addon validation (returns (errors, warnings) tuple)
        addon_errors, addon_warnings = validate_erp_addon_execution_tracking(
            feature_dir, approval_statuses, coverage_tier
        )
        for code, msg, details in addon_errors:
            result.add_error(code, msg)
        for code, msg, details in addon_warnings:
            result.add_warning(f"WARN_{code}", msg)
    except ImportError:
        pass  # ERP Addon module not available, skip

    # v5.5 Phase B: VALUE Upstream Extension lint (only when specs/<feature>/upstream/ exists)
    try:
        from upstream_lint import lint_upstream
        lint_upstream(feature_dir, config, result)
    except ImportError:
        pass  # upstream_lint module not available, skip

    # --- Extension tool execution (generic) ---
    if _extension_tools:
        bd = basic_doc.get("basic_design", {})
        coverage_tier = bd.get("coverage_tier") or "standard"

        for ext_func, ext_tool_name in _extension_tools:
            try:
                tool_errors, tool_warnings = ext_func(
                    feature_dir, approval_statuses, coverage_tier
                )
                for code, msg, details in tool_errors:
                    result.add_error(code, msg)
                for code, msg, details in tool_warnings:
                    result.add_warning(f"WARN_{code}", msg)
            except Exception:
                pass  # Tool execution failed, skip gracefully
    # --- End Extension tool execution ---

    return result


def discover_features(base_dir):
    candidates = []
    specs_dir = base_dir / "specs"
    if specs_dir.exists():
        candidates.append(specs_dir)
    templates_specs = base_dir / "sdd-templates" / "specs"
    if templates_specs.exists():
        candidates.append(templates_specs)
    features = []
    for specs_root in candidates:
        for child in specs_root.iterdir():
            if not child.is_dir():
                continue
            if (child / "basic_design.md").exists():
                features.append(child)
    return features


def features_from_changed(base_dir, git_range):
    try:
        output = subprocess.check_output(
            ["git", "diff", "--name-only", git_range],
            cwd=base_dir,
            text=True,
        )
    except Exception:
        return []

    paths = [line.strip() for line in output.splitlines() if line.strip()]
    if any(p.startswith("memory/") for p in paths) or any("/memory/" in p for p in paths):
        return discover_features(base_dir)

    feature_dirs = set()
    for path in paths:
        parts = Path(path).parts
        if "specs" not in parts:
            continue
        idx = parts.index("specs")
        if len(parts) <= idx + 1:
            continue
        feature = Path(*parts[: idx + 2])
        feature_dirs.add(base_dir / feature)
    return sorted(feature_dirs)


def report_results(results, config):
    # NDJSON: one JSON object per line per feature (pipe-friendly)
    if config.format == "ndjson":
        actor_info = _detect_actor()
        for res in results:
            entry = {
                "feature": res.feature_path,
                "errors": res.errors,
                "warnings": res.warnings,
                "meta": actor_info,
            }
            if res.coverage_report:
                entry["coverage_report"] = res.coverage_report.get("coverage_report")
            print(json.dumps(entry, ensure_ascii=False))
        return

    if config.format == "json":
        payload = []
        for res in results:
            entry = {
                "feature": res.feature_path,
                "errors": res.errors,
                "warnings": res.warnings,
            }
            if res.coverage_report:
                entry["coverage_report"] = res.coverage_report.get("coverage_report")
            payload.append(entry)
        output = {
            "results": payload,
            "meta": {
                **_detect_actor(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Plain TSV output: feature\tseverity\tcode\tmessage (grep/awk/CI)
    if config.plain:
        for res in results:
            feature = Path(res.feature_path).name
            for err in res.errors:
                print(f"{feature}\tERROR\t{err['code']}\t{err['message']}")
            for warn in res.warnings:
                print(f"{feature}\tWARN\t{warn['code']}\t{warn['message']}")
        return

    for res in results:
        header = f"Feature: {res.feature_path}"
        print(header)
        print("-" * len(header))

        # v1.2.4: Always show brief coverage summary
        if res.coverage_summary:
            s = res.coverage_summary
            ac_icon = "[x]" if s["ac_covered"] == s["ac_total"] and s["ac_total"] > 0 else "[ ]"
            ct_icon = "[x]" if s["ct_covered"] == s["ct_total"] and s["ct_total"] > 0 else "[ ]"
            print(f"Coverage: {ac_icon} AC {s['ac_covered']}/{s['ac_total']} ({s['ac_pct']}%)  {ct_icon} CT {s['ct_covered']}/{s['ct_total']} ({s['ct_pct']}%)")

        if res.errors:
            print(_bold("Errors:"))
            for err in res.errors:
                print(f"  {_red('✗')} {err['code']}: {err['message']}")
                if err.get('suggested_action'):
                    print(f"    {_dim('→')} {_dim(err['suggested_action'])}")
        if res.warnings:
            print(_bold("Warnings:"))
            for warn in res.warnings:
                print(f"  {_yellow('⚠')} {warn['code']}: {warn['message']}")
                if warn.get('suggested_action'):
                    print(f"    {_dim('→')} {_dim(warn['suggested_action'])}")
        if res.coverage_report:
            print(yaml.safe_dump(res.coverage_report, sort_keys=False))
        if not res.errors and not res.warnings and not res.coverage_report:
            print(f"  {_green('✓')} stride-lint checks passed")

        # Next step suggestion
        if not res.errors and res.coverage_summary:
            s = res.coverage_summary
            all_covered = (s["ac_covered"] == s["ac_total"] and s["ac_total"] > 0
                           and s["ct_covered"] == s["ct_total"])
            if all_covered:
                print(f"  {_dim('→ Next: stride auto-continue で次の作業を確認してください')}")
            elif s["ac_total"] > 0:
                print(f"  {_dim('→ Next: 未カバーのAC/CTをplan.mdのtestsに追加してください')}")
        elif res.errors:
            feature_name = Path(res.feature_path).name
            print(f"  {_dim(f'→ Fix errors, then re-run: stride lint specs/{feature_name}/')}")
        print("")


def exit_code(results, config):
    # Agent-friendly: exit code 4 — config/YAML parse failure
    for res in results:
        for err in res.errors:
            if err["code"] == "YAML_PARSE_ERROR":
                return 4

    # --warn-only overrides validation errors (code 1) but NOT infrastructure errors (2/3/4)
    if config.warn_only:
        return 0
    if config.fail_on:
        for res in results:
            for issue in res.errors + res.warnings:
                if issue["code"] in config.fail_on:
                    return 1
        return 0
    for res in results:
        if res.errors:
            return 1
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="stride-lint",
        description="stride-lint: SDD文書の整合性チェッカー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  stride-lint specs/FEAT-ORDER/              1つのfeatureを検証
  stride-lint --all                          全featureを検証
  stride-lint --all -o json                  CI/エージェント向けJSON出力
  stride-lint --all -o ndjson                1feature1行JSON（パイプ向け）
  stride-lint --changed HEAD~1..HEAD         変更featureのみ検証
  stride-lint specs/FEAT-ORDER/ --coverage-report  カバレッジ詳細レポート
  stride-lint --all --enterprise             エンタープライズ検証も含む

exit codes:
  0  lint passed
  1  lint errors found
  2  usage error (bad arguments)
  3  feature directory not found
  4  YAML parse error""",
    )
    parser.add_argument("feature_dir", nargs="?", help="Path to specs/<feature>")
    parser.add_argument("--feature", dest="feature", help="Path to specs/<feature>")
    parser.add_argument("--all", action="store_true", help="Lint all features under specs/")
    parser.add_argument("--changed", help="Lint features changed in git range")
    parser.add_argument("--coverage-report", action="store_true", help="Output coverage report")
    parser.add_argument("--warn-only", action="store_true", help="Exit 0 even when errors exist")
    parser.add_argument("-o", "--format", choices=["text", "json", "ndjson"], default="text",
                       help="出力フォーマット (text/json/ndjson)")
    parser.add_argument("--plain", action="store_true",
                       help="1行1レコードのTSV出力（grep/awk/CI向け）")
    parser.add_argument("--no-color", action="store_true",
                       help="カラー出力を無効化")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--fail-on", help="Comma-separated failure codes")
    parser.add_argument("--lite-mode", action="store_true", help="Use Lite Mode (3-stage approval for small projects)")
    parser.add_argument("--enterprise", action="store_true",
                       help="Also run enterprise validation (epic_ref, coverage_tier, shared contracts)")
    parser.add_argument("--upstream", metavar="FEATURE_PATH",
                       help="v5.5 Phase B: Alias for 'stride upstream validate' — focuses lint on specs/<feature>/upstream/")
    args = parser.parse_args()

    # v5.5 Phase B: --upstream <feature_path> is an alias overriding positional feature_dir
    if args.upstream:
        args.feature_dir = args.upstream

    # Mutual exclusion: --plain and -o json/ndjson
    if args.plain and args.format in ("json", "ndjson"):
        parser.error("--plain cannot be combined with -o json or -o ndjson")

    # --verbose emits progress to stdout which breaks machine-readable output
    if args.verbose and (args.format in ("json", "ndjson") or args.plain):
        parser.error("--verbose cannot be combined with machine-readable output (-o json, -o ndjson, --plain)")

    global _USE_COLOR
    if args.no_color:
        _USE_COLOR = False

    fail_on = []
    if args.fail_on:
        fail_on = [code.strip() for code in args.fail_on.split(",") if code.strip()]

    config = LintConfig(
        warn_only=args.warn_only,
        coverage_report=args.coverage_report,
        fmt=args.format,
        verbose=args.verbose,
        fail_on=fail_on,
        lite_mode=args.lite_mode,
        enterprise=args.enterprise,
        plain=args.plain,
    )

    base_dir = Path.cwd()
    features = []
    if args.all:
        features = discover_features(base_dir)
    elif args.changed:
        features = features_from_changed(base_dir, args.changed)
    else:
        feature_path = args.feature or args.feature_dir
        if feature_path is None:
            parser.error("specify a feature path or --all/--changed")
        features = [Path(feature_path)]

    # Agent-friendly: exit code 3 — feature directory not found
    for feature in features:
        if not Path(feature).is_dir():
            msg = f"ERROR: Feature directory not found: {feature}"
            # Suggest similar directories
            parent = Path(feature).parent
            if parent.is_dir():
                candidates = [str(d) for d in parent.iterdir() if d.is_dir()]
                matches = difflib.get_close_matches(str(feature), candidates, n=1, cutoff=0.6)
                if matches:
                    msg += f"\n  Did you mean: {matches[0]} ?"
            print(msg, file=sys.stderr)
            return 3

    # Fail-fast: pre-validate canonical YAML blocks before full lint (原則4: 事前検証)
    # Uses the same extract_yaml_after_marker() that lint_feature() uses,
    # so we only check blocks that the linter will actually parse.
    # Also uses load_yaml() which handles yaml=None (PyYAML missing) gracefully.
    _PREFLIGHT_MARKERS = [
        ("basic_design.md", ["Canonical Basic Design", "basic_design_gate_check"]),
        ("spec.md", ["Canonical Spec"]),
        ("plan.md", ["Canonical Plan"]),
        ("tasks.md", ["Canonical Tasks"]),
    ]
    if yaml is None:
        # PyYAML not installed — skip preflight (lint_feature will raise RuntimeError)
        pass
    else:
        for feature in features:
            for filename, markers in _PREFLIGHT_MARKERS:
                fpath = Path(feature) / filename
                if not fpath.exists():
                    continue
                text = fpath.read_text(encoding="utf-8")
                for marker in markers:
                    block = extract_yaml_after_marker(text, marker)
                    if block is None:
                        continue  # Missing block is caught by lint_feature() as CANONICAL_BLOCK_NOT_FOUND
                    # Use a temporary LintResult to leverage load_yaml()'s error handling
                    _preflight_result = LintResult(str(fpath))
                    if load_yaml(block, f"{fpath} [{marker}]", _preflight_result) is None:
                        # load_yaml already added YAML_PARSE_ERROR to _preflight_result
                        err = _preflight_result.errors[0]
                        print(f"ERROR: {err['message']}", file=sys.stderr)
                        if err.get('suggested_action'):
                            print(f"  → {err['suggested_action']}", file=sys.stderr)
                        return 4

    results = []
    for feature in features:
        if config.verbose:
            print(f"Linting {feature}...")
        results.append(lint_feature(feature, config))


    # Enterprise validation (when --enterprise flag is explicitly set)
    if args.enterprise:
        enterprise_enabled = load_enterprise_config()
        if not enterprise_enabled:
            print("Error: --enterprise flag requires enterprise.enabled: true in "
                  "sdd-templates/config/enterprise.yaml", file=sys.stderr)
            return 1
        else:
            try:
                tools_dir = Path(__file__).parent
                if str(tools_dir) not in sys.path:
                    sys.path.insert(0, str(tools_dir))

                # --- Feature-level enterprise checks ---
                from stride_lint_enterprise import EnterpriseValidator
                validator = EnterpriseValidator(base_dir)

                for feature in features:
                    ent_result = validator.validate_feature_enterprise(feature)
                    if ent_result.errors or ent_result.warnings:
                        feature_resolved = str(Path(feature).resolve())
                        for res in results:
                            if str(Path(res.feature_path).resolve()) == feature_resolved:
                                for err in ent_result.errors:
                                    res.add_error(err["code"], f"[Enterprise] {err['message']}")
                                for warn in ent_result.warnings:
                                    res.add_warning(warn["code"], f"[Enterprise] {warn['message']}")
                                break

                # --- Epic-level checks (--all only) ---
                if args.all:
                    from epic_validator import EpicValidator
                    epics_dir = base_dir / "epics"
                    if epics_dir.exists():
                        for epic_dir in sorted(epics_dir.iterdir()):
                            if epic_dir.is_dir() and (epic_dir / "epic_design.md").exists():
                                ev = EpicValidator(epic_dir)
                                ev_result = ev.validate()
                                epic_lint_result = LintResult(str(epic_dir))
                                for err_msg in ev_result.errors:
                                    parts = err_msg.split(": ", 1)
                                    code = parts[0] if len(parts) > 1 else "EPIC_ERROR"
                                    msg = parts[1] if len(parts) > 1 else err_msg
                                    epic_lint_result.add_error(code, f"[Epic] {msg}")
                                for warn_msg in ev_result.warnings:
                                    parts = warn_msg.split(": ", 1)
                                    code = parts[0] if len(parts) > 1 else "EPIC_WARNING"
                                    msg = parts[1] if len(parts) > 1 else warn_msg
                                    epic_lint_result.add_warning(code, f"[Epic] {msg}")
                                if epic_lint_result.errors or epic_lint_result.warnings:
                                    results.append(epic_lint_result)

            except ImportError as e:
                print(f"Error: Enterprise module not found ({e}). "
                      f"Cannot run --enterprise validation.", file=sys.stderr)
                return 1

    report_results(results, config)
    return exit_code(results, config)


if __name__ == "__main__":
    raise SystemExit(main())
