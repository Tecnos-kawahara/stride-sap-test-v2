#!/usr/bin/env python3
"""
Setup Phase Gate Hooks for SDD Projects

This script sets up the .claude/settings.json file to enable automatic
Phase Gate enforcement using Claude Code hooks.

Usage:
    python3 sdd-templates/tools/setup_hooks.py

This will:
1. Create .claude/ directory if it doesn't exist
2. Create or update .claude/settings.json with Phase Gate hook configuration
"""

import io
import json
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


HOOK_CONFIG = {
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "Write|Edit",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python3 \"$CLAUDE_PROJECT_DIR/sdd-templates/hooks/phase_gate_hook.py\""
                    }
                ]
            }
        ]
    }
}


def main():
    # Find project root (where .claude/ should be created)
    project_root = Path.cwd()

    # Check if we're in the right directory
    if not (project_root / "sdd-templates").exists():
        print("Error: sdd-templates not found in current directory.")
        print("Please run this script from the project root directory.")
        sys.exit(1)

    # Check if hook script exists
    hook_script = project_root / "sdd-templates" / "hooks" / "phase_gate_hook.py"
    if not hook_script.exists():
        print(f"Error: Hook script not found at {hook_script}")
        sys.exit(1)

    # Create .claude directory
    claude_dir = project_root / ".claude"
    claude_dir.mkdir(exist_ok=True)
    print(f"Created directory: {claude_dir}")

    # Check if settings.json already exists
    settings_path = claude_dir / "settings.json"
    if settings_path.exists():
        # Merge with existing settings
        try:
            existing = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}

        # Check if hooks already configured
        if "hooks" in existing and "PreToolUse" in existing["hooks"]:
            print("Warning: PreToolUse hooks already configured.")
            response = input("Overwrite existing hook configuration? [y/N]: ")
            if response.lower() != "y":
                print("Aborted.")
                sys.exit(0)

        # Merge hooks
        existing.setdefault("hooks", {})
        existing["hooks"]["PreToolUse"] = HOOK_CONFIG["hooks"]["PreToolUse"]
        config = existing
    else:
        config = HOOK_CONFIG

    # Write settings.json
    settings_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    print(f"Created: {settings_path}")

    print()
    print("Phase Gate hooks have been configured successfully!")
    print()
    print("How it works:")
    print("  - When you try to Write/Edit files in specs/ directory,")
    print("    the hook will check APPROVAL.md for gate approvals.")
    print("  - Phase 1 files (basic_design.md, process.bpmn) are always allowed.")
    print("  - Phase 2+ files require previous phase gates to be approved.")
    print()
    print("To check current phase status:")
    print("  python3 sdd-templates/tools/phase_gate.py status specs/<feature>/")


if __name__ == "__main__":
    main()
