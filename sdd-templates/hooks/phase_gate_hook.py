#!/usr/bin/env python3
"""
Phase Gate Hook for Claude Code

This script is used as a PreToolUse hook to intercept Write/Edit operations
on specs/ files and enforce Phase Gate requirements.

Supports both Full Mode (Gates 1-5 + Final) and Lite Mode (Gates A, B, C).

Claude Code Hook Protocol:
- Receives JSON on stdin with tool_name and tool_input
- Outputs JSON with decision: "block" | "allow" and optional reason

Usage (configured in .claude/settings.json):
    PreToolUse hooks are triggered before Write/Edit operations.
"""

import io
import json
import re
import sys
from pathlib import Path


# =============================================================================
# Windows Console Encoding Fix
# =============================================================================
def _configure_console_encoding():
    """Configure stdout/stderr for UTF-8 with safe fallback on Windows."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
                return
            except Exception:
                pass
        try:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True
            )
        except Exception:
            pass


_configure_console_encoding()


# =============================================================================
# Phase Definitions
# =============================================================================

# Full Mode: Gates 1-5 + Final
PHASE_DEFINITIONS_FULL = {
    1: {
        "name": "Design",
        "required_gates": [1, 2],
        "allowed_files": ["basic_design.md", "process.bpmn", "APPROVAL.md"],
    },
    2: {
        "name": "Specify",
        "required_gates": [3, 4],
        "allowed_files": [
            "spec.md",
            "plan.md",
            "contracts/*",
            "implementation-details/*",
            "tests/scenarios.yaml",
        ],
    },
    3: {
        "name": "Tasking",
        "required_gates": [5],
        "allowed_files": [
            "tasks.md",
            "tests/*",
            # STRIDE: Work Items, State, Runs, Ops (Post-Gate 5)
            "work_items/*",
            "state/*",
            "runs/*",
            "ops/*",
        ],
    },
    4: {
        "name": "Execute",
        "required_gates": ["final"],
        "allowed_files": ["src/*"],
    },
}

# Lite Mode: Gates A, B, C
PHASE_DEFINITIONS_LITE = {
    1: {
        "name": "Design & Flow",
        "required_gates": ["A"],
        "allowed_files": ["basic_design.md", "process.bpmn", "APPROVAL.md"],
    },
    2: {
        "name": "Spec & Plan",
        "required_gates": ["B"],
        "allowed_files": [
            "spec.md",
            "plan.md",
            "contracts/*",
            "implementation-details/*",
            "tests/*",
            # STRIDE: Work Items, State, Runs, Ops (Post-Gate B)
            "work_items/*",
            "state/*",
            "runs/*",
            "ops/*",
        ],
    },
    3: {
        "name": "Implementation & Verification",
        "required_gates": ["C"],
        "allowed_files": ["tasks.md", "src/*"],
    },
}

# Gate patterns for parsing APPROVAL.md
# Use negative lookahead to stop at next ## (but not ###)
GATE_PATTERNS_FULL = {
    1: r"##\s*Gate 1.*?(?=\n## [^#]|\Z)",
    2: r"##\s*Gate 2.*?(?=\n## [^#]|\Z)",
    3: r"##\s*Gate 3.*?(?=\n## [^#]|\Z)",
    4: r"##\s*Gate 4.*?(?=\n## [^#]|\Z)",
    5: r"##\s*Gate 5.*?(?=\n## [^#]|\Z)",
    "final": r"##\s*Final.*?(?=\n## [^#]|\Z)",
}

GATE_PATTERNS_LITE = {
    "A": r"##\s*Gate A.*?(?=\n## [^#]|\Z)",
    "B": r"##\s*Gate B.*?(?=\n## [^#]|\Z)",
    "C": r"##\s*Gate C.*?(?=\n## [^#]|\Z)",
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_feature_dir(file_path: str) -> Path | None:
    """Extract feature directory from file path."""
    path = Path(file_path)
    parts = path.parts

    if "specs" not in parts:
        return None

    specs_idx = parts.index("specs")
    if len(parts) <= specs_idx + 1:
        return None

    return Path(*parts[:specs_idx + 2])


def detect_lite_mode(feature_dir: Path) -> bool:
    """Detect if the feature is using Lite Mode."""
    approval_path = feature_dir / "APPROVAL.md"

    if not approval_path.exists():
        return False

    content = approval_path.read_text(encoding="utf-8")

    if "Lite Mode" in content:
        return True

    if re.search(r"##\s*Gate [ABC]", content, re.IGNORECASE):
        return True

    return False


def get_approved_gates(feature_dir: Path) -> tuple[set, bool]:
    """Get list of approved gates from APPROVAL.md."""
    approval_path = feature_dir / "APPROVAL.md"

    if not approval_path.exists():
        return set(), False

    content = approval_path.read_text(encoding="utf-8")
    lite_mode = detect_lite_mode(feature_dir)

    gate_patterns = GATE_PATTERNS_LITE if lite_mode else GATE_PATTERNS_FULL
    approved = set()

    for gate_key, pattern in gate_patterns.items():
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            section = match.group(0)

            checked = len(re.findall(r"\[x\]", section, re.IGNORECASE))
            unchecked = len(re.findall(r"\[ \]", section))

            approver_match = re.search(r"承認者:\s*([^\n]+)", section)
            approver_filled = False
            if approver_match:
                name = approver_match.group(1).strip()
                approver_filled = name and not re.match(r"^_+$", name)

            if unchecked == 0 and checked > 0 and approver_filled:
                approved.add(gate_key)

    return approved, lite_mode


def get_current_phase(approved_gates: set, lite_mode: bool) -> int:
    """Determine current approved phase based on approved gates."""
    phase_defs = PHASE_DEFINITIONS_LITE if lite_mode else PHASE_DEFINITIONS_FULL
    current_phase = 0

    for phase_num, phase_def in phase_defs.items():
        required = set(phase_def["required_gates"])
        if required.issubset(approved_gates):
            current_phase = phase_num
        else:
            break

    return current_phase


def get_file_phase(file_path: str, feature_dir: Path, lite_mode: bool) -> int | None:
    """Determine which phase a file belongs to."""
    phase_defs = PHASE_DEFINITIONS_LITE if lite_mode else PHASE_DEFINITIONS_FULL

    try:
        rel_path = Path(file_path).relative_to(feature_dir)
    except ValueError:
        return None

    rel_str = str(rel_path)
    # Get first directory component for nested paths (e.g., runs/WI-001/RUN-001/*)
    first_dir = rel_path.parts[0] if rel_path.parts else ""

    for phase_num, phase_def in phase_defs.items():
        for pattern in phase_def["allowed_files"]:
            if pattern.endswith("/*"):
                dir_name = pattern[:-2]
                # Match exact directory or any nested path under it
                if rel_str.startswith(dir_name + "/") or rel_str == dir_name:
                    return phase_num
                # Also match by first directory component for deeply nested paths
                if first_dir == dir_name:
                    return phase_num
            else:
                if rel_str == pattern:
                    return phase_num

    return None


def check_file_allowed(file_path: str) -> tuple[bool, str]:
    """Check if a file operation is allowed.

    SECURITY: Unknown file types are BLOCKED by default (INVIOLABLE).
    """
    feature_dir = get_feature_dir(file_path)

    if feature_dir is None:
        return True, "File is not in specs directory"

    approved_gates, lite_mode = get_approved_gates(feature_dir)
    file_phase = get_file_phase(file_path, feature_dir, lite_mode)

    # SECURITY: Unknown file types are BLOCKED (INVIOLABLE)
    if file_phase is None:
        try:
            rel_path = str(Path(file_path).relative_to(feature_dir))
        except ValueError:
            rel_path = file_path
        return False, (
            f"BLOCKED: Unknown file type '{rel_path}' in specs directory. "
            f"Only files defined in Phase Definitions are allowed."
        )

    current_phase = get_current_phase(approved_gates, lite_mode)
    phase_defs = PHASE_DEFINITIONS_LITE if lite_mode else PHASE_DEFINITIONS_FULL
    mode_name = "Lite" if lite_mode else "Full"

    # Phase 1 files are always allowed (bootstrap)
    if file_phase == 1:
        return True, f"Phase 1 files always allowed [{mode_name}]"

    # Check if previous phase is approved
    required_phase = file_phase - 1

    if current_phase >= required_phase:
        return True, f"Phase {file_phase} allowed [{mode_name}]"
    else:
        phase_name = phase_defs[file_phase]["name"]
        required_gates = phase_defs[required_phase]["required_gates"]
        return False, (
            f"BLOCKED: Phase {file_phase} ({phase_name}) requires "
            f"Gate(s) {required_gates} approval [{mode_name}]"
        )


def main():
    try:
        # Read hook input from stdin
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Invalid input - allow operation (fail open for non-hook usage)
        print(json.dumps({"decision": "allow", "reason": "Invalid hook input"}))
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only check Write and Edit operations
    if tool_name not in ("Write", "Edit"):
        print(json.dumps({"decision": "allow"}))
        return

    file_path = tool_input.get("file_path", "")

    # Skip if not in specs directory
    if "specs" not in file_path:
        print(json.dumps({"decision": "allow"}))
        return

    # Check if file operation is allowed
    allowed, message = check_file_allowed(file_path)

    if allowed:
        print(json.dumps({"decision": "allow", "reason": message}))
    else:
        print(json.dumps({"decision": "block", "reason": message}))


if __name__ == "__main__":
    main()
