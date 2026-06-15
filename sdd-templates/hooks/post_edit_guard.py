#!/usr/bin/env python3
"""
Post-Edit Quality Guard for Claude Code (PostToolUse hook)

Lightweight, per-file quality checks after Write/Edit operations on specs/ files.
Runs in < 2s. Fail-open: always returns {"decision": "allow"} on stdout.
Warnings are emitted to stderr (visible in Claude Code context).

Claude Code PostToolUse Hook Protocol:
- stdin: JSON with tool_name, tool_input, tool_result
- stdout: JSON {"decision": "allow"} (always — PostToolUse cannot block)
- stderr: warning messages (visible to the agent)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

# sdd-templates/hooks and sdd-templates/tools are siblings; make the shared
# library importable without adding a package marker.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from stride_shared_lib import extract_first_yaml_block  # noqa: E402


# =============================================================================
# Windows Console Encoding Fix (same as phase_gate_hook.py)
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


try:
    import yaml as _yaml
except ImportError:
    _yaml = None  # type: ignore[assignment]

ALLOW = json.dumps({"decision": "allow"})


# =============================================================================
# Per-file checks
# =============================================================================

def _warn(file_path: str, msg: str) -> None:
    """Emit a warning to stderr."""
    print(f"\u26a0 post_edit_guard: {file_path} \u2014 {msg}", file=sys.stderr)


def check_yaml_syntax(file_path: str) -> None:
    """YAML syntax check for contracts/*.yaml files."""
    if _yaml is None:
        return
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        _yaml.safe_load(content)
    except _yaml.YAMLError as e:
        _warn(file_path, f"YAML parse error: {e}")
    except OSError:
        pass


def check_canonical_yaml(file_path: str) -> None:
    """Check that a spec file has a parseable canonical YAML block."""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except OSError:
        return

    yaml_text = extract_first_yaml_block(content)
    if yaml_text is None:
        _warn(file_path, "No canonical YAML block found (expected ```yaml ... ```)")
        return

    if _yaml is not None:
        try:
            _yaml.safe_load(yaml_text)
        except _yaml.YAMLError as e:
            _warn(file_path, f"Canonical YAML parse error: {e}")


def check_basic_design(file_path: str) -> None:
    """Check basic_design.md has traceability and delivery_model in canonical YAML."""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except OSError:
        return

    yaml_text = extract_first_yaml_block(content)
    if yaml_text is None:
        _warn(file_path, "No canonical YAML block found")
        return

    if _yaml is not None:
        try:
            data = _yaml.safe_load(yaml_text)
        except _yaml.YAMLError as e:
            _warn(file_path, f"Canonical YAML parse error: {e}")
            return
        if isinstance(data, dict):
            bd = data.get("basic_design", data)
            if not bd.get("traceability_rows") and not bd.get("traceability"):
                _warn(file_path, "Missing traceability_rows in canonical YAML")
            if not bd.get("delivery_model"):
                _warn(file_path, "Missing delivery_model in canonical YAML")


def check_plan_coverage_policy(file_path: str) -> None:
    """Check plan.md has coverage_policy in canonical YAML.

    Real structure: plan.test_strategy.coverage_policy
    (matches stride_lint.py L1449)
    """
    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except OSError:
        return

    yaml_text = extract_first_yaml_block(content)
    if yaml_text is None:
        _warn(file_path, "No canonical YAML block found")
        return

    if _yaml is not None:
        try:
            data = _yaml.safe_load(yaml_text)
        except _yaml.YAMLError as e:
            _warn(file_path, f"Canonical YAML parse error: {e}")
            return
        if isinstance(data, dict):
            plan = data.get("plan", data)
            test_strategy = plan.get("test_strategy", {})
            if isinstance(test_strategy, dict) and not test_strategy.get("coverage_policy"):
                _warn(file_path, "Missing test_strategy.coverage_policy in canonical YAML")


def check_tasks_plan_refs(file_path: str) -> None:
    """Check tasks.md: all tasks should have plan_refs.

    Real structure: tasks.tasks[*].plan_refs
    (matches stride_lint.py compute_tasks_counts / L1436)
    """
    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except OSError:
        return

    yaml_text = extract_first_yaml_block(content)
    if yaml_text is None:
        return  # Not critical enough to warn if no YAML block

    if _yaml is not None:
        try:
            data = _yaml.safe_load(yaml_text)
        except _yaml.YAMLError:
            return
        if isinstance(data, dict):
            tasks_data = data.get("tasks", data)
            # tasks.tasks is the real key (not task_list)
            task_list = tasks_data.get("tasks", []) if isinstance(tasks_data, dict) else []
            if isinstance(task_list, list):
                missing = []
                for task in task_list:
                    if isinstance(task, dict):
                        tid = task.get("id", task.get("task_id", "?"))
                        if not task.get("plan_refs"):
                            missing.append(str(tid))
                if missing:
                    _warn(file_path, f"Tasks missing plan_refs: {', '.join(missing[:5])}")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        # Invalid input — fail-open
        print(ALLOW)
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name not in ("Write", "Edit"):
        print(ALLOW)
        return

    file_path = tool_input.get("file_path", "")

    # Only check specs/ files
    if "specs/" not in file_path and "specs\\" not in file_path:
        print(ALLOW)
        return

    # Determine check type from file path
    basename = Path(file_path).name
    try:
        if "/contracts/" in file_path or "\\contracts\\" in file_path:
            if basename.endswith((".yaml", ".yml")):
                check_yaml_syntax(file_path)
        elif basename == "spec.md":
            check_canonical_yaml(file_path)
        elif basename == "plan.md":
            check_plan_coverage_policy(file_path)
        elif basename == "tasks.md":
            check_tasks_plan_refs(file_path)
        elif basename == "basic_design.md":
            check_basic_design(file_path)
    except Exception:
        pass  # fail-open: never crash the hook

    # Always allow (PostToolUse cannot block)
    print(ALLOW)


def run_tests() -> bool:
    """Self-tests for post_edit_guard.py."""
    import tempfile
    import shutil

    print("Running post_edit_guard.py self-tests...\n")
    tmpdir = Path(tempfile.mkdtemp())
    specs = tmpdir / "specs" / "test"

    try:
        # --- Test 1: Valid YAML contract → no warning ---
        print("Test 1: Valid YAML contract")
        contracts = specs / "contracts"
        contracts.mkdir(parents=True)
        (contracts / "openapi.yaml").write_text("openapi: '3.0.0'\ninfo:\n  title: Test\n")
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        check_yaml_syntax(str(contracts / "openapi.yaml"))
        stderr_out = sys.stderr.getvalue()
        sys.stderr = old_stderr
        assert stderr_out == "", f"Expected no warning, got: {stderr_out}"
        print("  PASS: Valid YAML → no warning")

        # --- Test 2: Broken YAML contract → stderr warning ---
        print("\nTest 2: Broken YAML contract")
        (contracts / "broken.yaml").write_text("key: [invalid\n")
        sys.stderr = io.StringIO()
        check_yaml_syntax(str(contracts / "broken.yaml"))
        stderr_out = sys.stderr.getvalue()
        sys.stderr = old_stderr
        assert "YAML parse error" in stderr_out, f"Expected YAML warning, got: {stderr_out}"
        print("  PASS: Broken YAML → warning")

        # --- Test 3: spec.md with canonical YAML → no warning ---
        print("\nTest 3: spec.md with canonical YAML")
        specs.mkdir(parents=True, exist_ok=True)
        (specs / "spec.md").write_text("# Spec\n```yaml\nspec:\n  overview: test\n```\n")
        sys.stderr = io.StringIO()
        check_canonical_yaml(str(specs / "spec.md"))
        stderr_out = sys.stderr.getvalue()
        sys.stderr = old_stderr
        assert stderr_out == "", f"Expected no warning, got: {stderr_out}"
        print("  PASS: Valid canonical YAML → no warning")

        # --- Test 4: spec.md without canonical YAML → warning ---
        print("\nTest 4: spec.md without canonical YAML")
        (specs / "spec_bad.md").write_text("# Spec\nNo yaml here\n")
        sys.stderr = io.StringIO()
        check_canonical_yaml(str(specs / "spec_bad.md"))
        stderr_out = sys.stderr.getvalue()
        sys.stderr = old_stderr
        assert "No canonical YAML" in stderr_out, f"Expected warning, got: {stderr_out}"
        print("  PASS: Missing canonical YAML → warning")

        # --- Test 5: plan.md with test_strategy.coverage_policy → no warning ---
        print("\nTest 5: plan.md with test_strategy.coverage_policy")
        (specs / "plan.md").write_text(
            "# Plan\n```yaml\nplan:\n  test_strategy:\n    coverage_policy:\n"
            "      acceptance_coverage_required: true\n```\n"
        )
        sys.stderr = io.StringIO()
        check_plan_coverage_policy(str(specs / "plan.md"))
        stderr_out = sys.stderr.getvalue()
        sys.stderr = old_stderr
        assert stderr_out == "", f"Expected no warning, got: {stderr_out}"
        print("  PASS: Valid coverage_policy → no warning")

        # --- Test 6: plan.md missing coverage_policy → warning ---
        print("\nTest 6: plan.md missing coverage_policy")
        (specs / "plan_bad.md").write_text(
            "# Plan\n```yaml\nplan:\n  test_strategy:\n    principles: [test-first]\n```\n"
        )
        sys.stderr = io.StringIO()
        check_plan_coverage_policy(str(specs / "plan_bad.md"))
        stderr_out = sys.stderr.getvalue()
        sys.stderr = old_stderr
        assert "coverage_policy" in stderr_out, f"Expected warning, got: {stderr_out}"
        print("  PASS: Missing coverage_policy → warning")

        # --- Test 7: tasks.md with plan_refs → no warning ---
        print("\nTest 7: tasks.md all tasks have plan_refs")
        (specs / "tasks.md").write_text(
            '# Tasks\n```yaml\ntasks:\n  tasks:\n    - id: "T-001"\n'
            '      plan_refs: ["CMP-01"]\n```\n'
        )
        sys.stderr = io.StringIO()
        check_tasks_plan_refs(str(specs / "tasks.md"))
        stderr_out = sys.stderr.getvalue()
        sys.stderr = old_stderr
        assert stderr_out == "", f"Expected no warning, got: {stderr_out}"
        print("  PASS: All tasks have plan_refs → no warning")

        # --- Test 8: tasks.md with missing plan_refs → warning ---
        print("\nTest 8: tasks.md with missing plan_refs")
        (specs / "tasks_bad.md").write_text(
            '# Tasks\n```yaml\ntasks:\n  tasks:\n    - id: "T-001"\n'
            '      plan_refs: ["CMP-01"]\n    - id: "T-002"\n'
            '      title: "No refs"\n```\n'
        )
        sys.stderr = io.StringIO()
        check_tasks_plan_refs(str(specs / "tasks_bad.md"))
        stderr_out = sys.stderr.getvalue()
        sys.stderr = old_stderr
        assert "T-002" in stderr_out, f"Expected T-002 warning, got: {stderr_out}"
        print("  PASS: Missing plan_refs → warning with task ID")

        print("\nAll self-tests passed.")
        return True

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = run_tests()
        sys.exit(0 if success else 1)
    main()
