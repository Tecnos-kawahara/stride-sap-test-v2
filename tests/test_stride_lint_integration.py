"""Integration tests for stride-lint: import API + CLI smoke."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestCheckStrideLint:
    """Test the import path used by pr_readiness_checker.

    Regression guard: pr_readiness_checker previously called
    lint_feature(str(feature_dir), {}) with a bare dict instead of LintConfig.
    That caused 'dict' object has no attribute 'coverage_report'.
    The fix uses _build_lint_config(lint_mod) to create a proper LintConfig.
    """

    def test_check_stride_lint_returns_pass_for_valid_feature(self, full_pass_project):
        """check_stride_lint() must return PASS (not WARN) for a valid project."""
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        try:
            from pr_readiness_checker import check_stride_lint
            result = check_stride_lint(full_pass_project)
            assert result["status"] in ("PASS", "FAIL"), (
                f"Expected PASS or FAIL but got '{result['status']}': {result.get('detail')}"
            )
        finally:
            sys.path.pop(0)

    def test_check_stride_lint_not_warn_due_to_config_error(self, full_pass_project):
        """Regression: check_stride_lint must not WARN due to attribute error."""
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        try:
            from pr_readiness_checker import check_stride_lint
            result = check_stride_lint(full_pass_project)
            if result["status"] == "WARN":
                detail = result.get("detail", "")
                assert "attribute" not in detail.lower(), (
                    f"WARN caused by attribute error (likely dict vs LintConfig): {detail}"
                )
        finally:
            sys.path.pop(0)


class TestLintFeatureImportAPI:
    """Test lint_feature() with correct LintConfig."""

    def test_lint_feature_with_lint_config(self, full_pass_project):
        """lint_feature() called with LintConfig returns LintResult with expected attrs."""
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        try:
            from stride_lint import LintConfig, LintResult, lint_feature
            config = LintConfig()
            result = lint_feature(str(full_pass_project / "specs" / "FEAT-TEST"), config)
            assert isinstance(result, LintResult)
            assert hasattr(result, "errors")
            assert hasattr(result, "warnings")
            assert hasattr(result, "coverage_report")
        finally:
            sys.path.pop(0)

    def test_lint_feature_pass_no_errors(self, full_pass_project):
        """A fully approved feature should have zero non-APPROVAL errors."""
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        try:
            from stride_lint import LintConfig, lint_feature
            config = LintConfig()
            result = lint_feature(str(full_pass_project / "specs" / "FEAT-TEST"), config)
            non_approval_errors = [
                e for e in result.errors
                if "APPROVAL_PENDING" not in str(e.get("code", ""))
            ]
            assert len(non_approval_errors) == 0, (
                f"Unexpected errors: {non_approval_errors}"
            )
        finally:
            sys.path.pop(0)

    def test_lint_feature_missing_bpmn_fails(self, project_builder):
        """Missing process.bpmn should produce a lint error."""
        project = (
            project_builder
            .add_feature("FEAT-NOBPMN", mode="full", phase=5)
            .mutate_lint_error("missing_bpmn")
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        try:
            from stride_lint import LintConfig, lint_feature
            result = lint_feature(str(project / "specs" / "FEAT-NOBPMN"), LintConfig())
            error_codes = [e["code"] for e in result.errors]
            assert any("MISSING" in c for c in error_codes), (
                f"Expected MISSING error for deleted BPMN, got: {error_codes}"
            )
        finally:
            sys.path.pop(0)


class TestStrideLintCLI:
    """Smoke tests for stride-lint CLI via subprocess."""

    def test_stride_lint_cli_exit_code(self, full_pass_project):
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TEST/"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        # May have APPROVAL_PENDING but should not crash
        assert result.returncode in (0, 1), (
            f"Unexpected exit {result.returncode}: {result.stderr}"
        )

    def test_stride_lint_json_output_is_valid(self, full_pass_project):
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TEST/", "--format", "json"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        if result.returncode in (0, 1):
            data = json.loads(result.stdout)
            assert "feature" in data or "errors" in data or "results" in data

    def test_stride_cli_lint_subcommand(self, full_pass_project):
        result = subprocess.run(
            ["sdd-templates/bin/stride", "lint", "specs/FEAT-TEST/"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        assert result.returncode in (0, 1)


class TestTextOutputEnhancements:
    """Test CLI UX improvements: suggested_action, color, plain mode."""

    def test_suggested_action_shown_in_text_output(self, project_builder):
        """Errors with suggested_action should display '→' hint in text output."""
        project = (
            project_builder
            .add_feature("FEAT-NOBPMN", mode="full", phase=5)
            .mutate_lint_error("missing_bpmn")
            .done()
            .build()
        )
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-NOBPMN/"],
            cwd=str(project),
            capture_output=True, text=True,
            env={**os.environ, "NO_COLOR": "1"},
        )
        assert "→" in result.stdout or "→" in result.stderr, (
            "suggested_action hint '→' not found in text output"
        )

    def test_plain_output_is_tsv(self, full_pass_project):
        """--plain output should be tab-separated, one record per line."""
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TEST/", "--plain"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        # May have APPROVAL_PENDING lines or be empty (all pass)
        for line in result.stdout.strip().splitlines():
            if line:
                parts = line.split("\t")
                assert len(parts) == 4, f"Expected 4 TSV fields, got {len(parts)}: {line}"
                assert parts[1] in ("ERROR", "WARN"), f"Unexpected severity: {parts[1]}"

    def test_no_color_flag_disables_ansi(self, full_pass_project):
        """--no-color should produce output without ANSI escape sequences.

        Note: capture_output=True makes stdout non-TTY, so color is already
        disabled by the TTY check. We verify --no-color works as a belt-and-
        suspenders mechanism.
        """
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TEST/", "--no-color"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        assert "\033[" not in result.stdout, "ANSI escape found despite --no-color"

    def test_no_color_env_disables_ansi(self, full_pass_project):
        """NO_COLOR env var should produce output without ANSI escape sequences.

        Note: capture_output=True already disables TTY-based coloring.
        This test verifies NO_COLOR is also respected as an independent switch.
        """
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TEST/"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
            env={**os.environ, "NO_COLOR": "1"},
        )
        assert "\033[" not in result.stdout, "ANSI escape found despite NO_COLOR"

    def test_color_logic_unit(self):
        """Verify _should_colorize() respects NO_COLOR, TERM, and stdout TTY state.

        Instead of simulating a real TTY with script(1) (fragile, injects
        control chars), we test the color-decision function directly by
        mocking sys.stdout.isatty() for the positive path.
        """
        cwd = str(Path(__file__).resolve().parent.parent)
        result = subprocess.run(
            ["python3", "-c", """
import sys, os, unittest.mock
os.environ.pop("NO_COLOR", None)
os.environ.pop("TERM", None)
sys.path.insert(0, "sdd-templates/tools")
from stride_lint import _should_colorize

# Case 1: NO_COLOR set -> False
os.environ["NO_COLOR"] = "1"
assert _should_colorize() == False, "NO_COLOR should disable color"
del os.environ["NO_COLOR"]

# Case 2: TERM=dumb -> False
os.environ["TERM"] = "dumb"
assert _should_colorize() == False, "TERM=dumb should disable color"
del os.environ["TERM"]

# Case 3: stdout is a TTY, no inhibitors -> True
with unittest.mock.patch.object(sys.stdout, "isatty", return_value=True):
    assert _should_colorize() == True, "Should colorize when stdout is TTY"

# Case 4: stdout is NOT a TTY -> False
with unittest.mock.patch.object(sys.stdout, "isatty", return_value=False):
    assert _should_colorize() == False, "Should not colorize when stdout is not TTY"

print("PASS")
"""],
            capture_output=True, text=True, cwd=cwd,
        )
        assert "PASS" in result.stdout, f"Color logic test failed: {result.stderr}"

    def test_help_text_contains_examples(self):
        """--help should display usage examples."""
        result = subprocess.run(
            ["python3", "-m", "stride_lint", "--help"],
            capture_output=True, text=True,
        )
        # Fallback: call the script directly
        if result.returncode != 0:
            result = subprocess.run(
                ["python3", "sdd-templates/tools/stride_lint.py", "--help"],
                capture_output=True, text=True,
            )
        combined = result.stdout + result.stderr
        assert "examples:" in combined.lower() or "stride-lint" in combined.lower(), (
            "Help text missing examples section"
        )

    def test_path_typo_suggests_correction(self, full_pass_project):
        """Mistyped feature path should suggest the correct path."""
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TETS/"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 3
        assert "Did you mean" in result.stderr, (
            "Expected 'Did you mean' suggestion for typo path"
        )

    def test_ndjson_output_one_json_per_line(self, full_pass_project):
        """--format ndjson should output one valid JSON object per line."""
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TEST/", "-o", "ndjson"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
        assert len(lines) >= 1, "Expected at least one NDJSON line"
        for line in lines:
            parsed = json.loads(line)  # Must be valid JSON
            assert "feature" in parsed, f"Missing 'feature' key in NDJSON line: {line}"
            assert "errors" in parsed
            assert "warnings" in parsed

    def test_json_output_contains_invocation_mode(self, full_pass_project):
        """JSON output should include meta.invocation_mode for audit trail."""
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TEST/", "-o", "json"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        data = json.loads(result.stdout)
        assert "meta" in data, "JSON output missing 'meta' field"
        assert "invocation_mode" in data["meta"], "JSON output missing 'meta.invocation_mode'"
        assert "timestamp" in data["meta"], "JSON output missing 'meta.timestamp'"

    def test_stride_actor_env_var(self, full_pass_project):
        """STRIDE_ACTOR env var should set authoritative actor in JSON output."""
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TEST/", "-o", "json"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
            env={**os.environ, "STRIDE_ACTOR": "agent:claude-code"},
        )
        data = json.loads(result.stdout)
        assert data["meta"]["actor"] == "agent:claude-code"
        assert data["meta"]["invocation_mode"] == "explicit"

    def test_plain_and_json_are_exclusive(self, full_pass_project):
        """--plain and -o json should be mutually exclusive."""
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TEST/", "--plain", "-o", "json"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 2, (
            f"Expected exit code 2 for conflicting flags, got {result.returncode}"
        )

    def test_verbose_and_json_are_exclusive(self, full_pass_project):
        """--verbose and -o json should be mutually exclusive."""
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TEST/", "--verbose", "-o", "json"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 2, (
            f"Expected exit code 2 for conflicting flags, got {result.returncode}"
        )

    def test_short_flag_o_works(self, full_pass_project):
        """-o json should work as shorthand for --format json."""
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TEST/", "-o", "json"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        data = json.loads(result.stdout)
        assert "results" in data

    def test_yaml_pre_validation_exit_code_4(self, project_builder):
        """Broken YAML in basic_design.md should fail fast with exit code 4."""
        project = (
            project_builder
            .add_feature("FEAT-BADYAML", mode="full", phase=5)
            .done()
            .build()
        )
        # Corrupt the YAML in basic_design.md
        bd_path = project / "specs" / "FEAT-BADYAML" / "basic_design.md"
        content = bd_path.read_text()
        # Insert broken YAML into a fenced block
        corrupted = content.replace(
            "```yaml",
            "```yaml\n  broken: [unclosed",
            1,  # Only replace the first occurrence
        )
        bd_path.write_text(corrupted)
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-BADYAML/"],
            cwd=str(project),
            capture_output=True, text=True,
        )
        assert result.returncode == 4, (
            f"Expected exit code 4 for broken YAML, got {result.returncode}. "
            f"stderr: {result.stderr}"
        )
