#!/usr/bin/env python3
"""
Phase Gate Checker for SDD Workflow

This script checks if a file operation is allowed based on the current
approved phase in APPROVAL.md.

Supports both Full Mode (Gates 1-5 + Final) and Lite Mode (Gates A, B, C).
Lite Mode is auto-detected from APPROVAL.md content (looks for "Gate A/B/C" sections).

Usage:
    python3 phase_gate.py <operation> <file_path>

Operations:
    check  - Check if file can be created/edited
    status - Show current phase status
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path


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
            "implementation-details/*",  # spec_as_code artifacts
            "tests/scenarios.yaml",       # test scenarios
        ],
    },
    3: {
        "name": "Tasking",
        "required_gates": [5],
        "allowed_files": [
            "tasks.md",
            "tests/*",  # Test files can be created during tasking
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
        ],
    },
    3: {
        "name": "Implementation & Verification",
        "required_gates": ["C"],
        "allowed_files": ["tasks.md", "src/*"],
    },
}

# Gate patterns for parsing APPROVAL.md
GATE_PATTERNS_FULL = {
    1: r"##\s*Gate 1.*?(?=##|$)",
    2: r"##\s*Gate 2.*?(?=##|$)",
    3: r"##\s*Gate 3.*?(?=##|$)",
    4: r"##\s*Gate 4.*?(?=##|$)",
    5: r"##\s*Gate 5.*?(?=##|$)",
    "final": r"##\s*Final.*?(?=##|$)",
}

GATE_PATTERNS_LITE = {
    "A": r"##\s*Gate A.*?(?=##|$)",
    "B": r"##\s*Gate B.*?(?=##|$)",
    "C": r"##\s*Gate C.*?(?=##|$)",
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

    # specs/<feature>/...
    return Path(*parts[:specs_idx + 2])


def detect_lite_mode(feature_dir: Path) -> bool:
    """Detect if the feature is using Lite Mode.

    Checks for:
    1. APPROVAL.md contains 'Lite Mode' header
    2. APPROVAL.md contains Gate A/B/C sections
    """
    approval_path = feature_dir / "APPROVAL.md"

    if not approval_path.exists():
        return False

    content = approval_path.read_text(encoding="utf-8")

    # Check for Lite Mode indicators
    if "Lite Mode" in content:
        return True

    # Check for Gate A/B/C sections
    if re.search(r"##\s*Gate [ABC]", content, re.IGNORECASE):
        return True

    return False


def get_approved_gates(feature_dir: Path) -> tuple[set, bool]:
    """Get list of approved gates from APPROVAL.md.

    Returns:
        Tuple of (approved_gates_set, is_lite_mode)
    """
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

            # Count checked boxes [x] vs unchecked [ ]
            checked = len(re.findall(r"\[x\]", section, re.IGNORECASE))
            unchecked = len(re.findall(r"\[ \]", section))

            # v1.2.5: Multi-language approver field detection (Japanese/English)
            approver_patterns = [
                r"承認者:\s*([^\n]+)",      # Japanese
                r"Approver:\s*([^\n]+)",    # English
            ]
            approver_filled = False
            for approver_pattern in approver_patterns:
                approver_match = re.search(approver_pattern, section, re.IGNORECASE)
                if approver_match:
                    name = approver_match.group(1).strip()
                    if name and not re.match(r"^_+$", name):
                        approver_filled = True
                        break

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

    # Get relative path from feature directory
    try:
        rel_path = Path(file_path).relative_to(feature_dir)
    except ValueError:
        return None

    rel_str = str(rel_path)

    for phase_num, phase_def in phase_defs.items():
        for pattern in phase_def["allowed_files"]:
            if pattern.endswith("/*"):
                # Directory pattern
                dir_name = pattern[:-2]
                if rel_str.startswith(dir_name + "/") or rel_str == dir_name:
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
        # Not in specs directory, allow
        return True, "File is not in specs directory"

    approved_gates, lite_mode = get_approved_gates(feature_dir)
    file_phase = get_file_phase(file_path, feature_dir, lite_mode)

    # SECURITY: Unknown file types are BLOCKED
    if file_phase is None:
        rel_path = Path(file_path).relative_to(feature_dir) if feature_dir else file_path
        return False, (
            f"BLOCKED: Unknown file type '{rel_path}' in specs directory.\n"
            f"Only files defined in Phase Definitions are allowed.\n"
            f"Allowed patterns: {_get_all_allowed_patterns(lite_mode)}"
        )

    current_phase = get_current_phase(approved_gates, lite_mode)
    phase_defs = PHASE_DEFINITIONS_LITE if lite_mode else PHASE_DEFINITIONS_FULL
    mode_name = "Lite Mode" if lite_mode else "Full Mode"

    # Phase 1 files are always allowed (bootstrap)
    if file_phase == 1:
        return True, f"Phase 1 ({phase_defs[1]['name']}) files are always allowed [{mode_name}]"

    # Check if previous phase is approved
    required_phase = file_phase - 1

    if current_phase >= required_phase:
        return True, f"Phase {file_phase} file allowed (Phase {required_phase} approved) [{mode_name}]"
    else:
        phase_name = phase_defs[file_phase]["name"]
        prev_phase_name = phase_defs[required_phase]["name"]
        required_gates = phase_defs[required_phase]["required_gates"]
        return False, (
            f"BLOCKED: Cannot create Phase {file_phase} ({phase_name}) file.\n"
            f"Phase {required_phase} ({prev_phase_name}) must be approved first.\n"
            f"Please approve Gate(s) {required_gates} in APPROVAL.md [{mode_name}]"
        )


def _get_all_allowed_patterns(lite_mode: bool) -> list[str]:
    """Get all allowed file patterns for documentation."""
    phase_defs = PHASE_DEFINITIONS_LITE if lite_mode else PHASE_DEFINITIONS_FULL
    patterns = []
    for phase_def in phase_defs.values():
        patterns.extend(phase_def["allowed_files"])
    return patterns


def show_status(feature_dir: Path):
    """Show current phase status."""
    approved_gates, lite_mode = get_approved_gates(feature_dir)
    current_phase = get_current_phase(approved_gates, lite_mode)
    phase_defs = PHASE_DEFINITIONS_LITE if lite_mode else PHASE_DEFINITIONS_FULL
    mode_name = "Lite Mode" if lite_mode else "Full Mode"

    print(f"Feature: {feature_dir}")
    print(f"Mode: {mode_name}")
    print(f"Approved Gates: {sorted(approved_gates, key=str) if approved_gates else 'None'}")
    print(f"Current Phase: {current_phase}")
    print()

    for phase_num, phase_def in phase_defs.items():
        required = set(phase_def["required_gates"])
        approved = required.issubset(approved_gates)
        status = "[x] Approved" if approved else "[ ] Pending"
        print(f"  Phase {phase_num} ({phase_def['name']}): {status}")
        print(f"    Required gates: {phase_def['required_gates']}")
        print(f"    Allowed files: {phase_def['allowed_files']}")
        print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 phase_gate.py <operation> [file_path]")
        print("Operations: check, status")
        sys.exit(1)

    operation = sys.argv[1]

    if operation == "check":
        if len(sys.argv) < 3:
            print("Usage: python3 phase_gate.py check <file_path>")
            sys.exit(1)

        file_path = sys.argv[2]
        allowed, message = check_file_allowed(file_path)

        print(message)
        sys.exit(0 if allowed else 1)

    elif operation == "status":
        if len(sys.argv) < 3:
            # Try to find feature directory
            cwd = Path.cwd()
            if (cwd / "specs").exists():
                for feature in (cwd / "specs").iterdir():
                    if feature.is_dir():
                        show_status(feature)
            else:
                print("No specs directory found")
                sys.exit(1)
        else:
            feature_dir = Path(sys.argv[2])
            show_status(feature_dir)

    else:
        print(f"Unknown operation: {operation}")
        sys.exit(1)


if __name__ == "__main__":
    main()
