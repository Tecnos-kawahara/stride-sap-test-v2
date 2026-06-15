"""E2E tests for enterprise CLI commands via subprocess."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STRIDE = "sdd-templates/bin/stride"


def _run(args: list[str], cwd: Path, **kwargs) -> subprocess.CompletedProcess:
    """Run stride with the given arguments inside *cwd*."""
    return subprocess.run(
        [STRIDE, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        **kwargs,
    )


def _write_enterprise_config(root: Path, *, enabled: bool) -> None:
    """Write enterprise config inside the tmp project (never touches the real file)."""
    config_path = root / "sdd-templates" / "config" / "enterprise.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        f"enterprise:\n  enabled: {'true' if enabled else 'false'}\n",
        encoding="utf-8",
    )


def _init_epic(root: Path, epic_id: str = "EPIC-TEST") -> subprocess.CompletedProcess:
    """Create an epic via `stride epic init`."""
    return _run(["epic", "init", epic_id], cwd=root)


# ---------------------------------------------------------------------------
# Tests: enterprise gate — epic commands blocked / allowed
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestEpicListGating:
    """epic list must be blocked when enterprise is off, allowed when on."""

    def test_epic_list_blocked_when_enterprise_off(self, bootstrap_project_root: Path):
        """epic list exits non-zero when enterprise.enabled is false."""
        _write_enterprise_config(bootstrap_project_root, enabled=False)

        result = _run(["epic", "list"], cwd=bootstrap_project_root)

        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "enterprise" in combined.lower() or "not enabled" in combined.lower()

    def test_epic_list_passes_when_enterprise_on(self, bootstrap_project_root: Path):
        """epic list exits 0 when enterprise.enabled is true."""
        _write_enterprise_config(bootstrap_project_root, enabled=True)

        result = _run(["epic", "list"], cwd=bootstrap_project_root)

        assert result.returncode == 0
        assert "Epics" in result.stdout or "epics" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Tests: epic init — directory / file creation
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestEpicInit:
    """stride epic init should scaffold the epic directory."""

    def test_epic_init_creates_files(self, bootstrap_project_root: Path):
        """epic init EPIC-ORDER creates epics/EPIC-ORDER/ with expected files."""
        result = _init_epic(bootstrap_project_root, "EPIC-ORDER")

        assert result.returncode == 0, (
            f"epic init failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )

        epic_dir = bootstrap_project_root / "epics" / "EPIC-ORDER"
        assert epic_dir.is_dir(), "epics/EPIC-ORDER/ directory not created"

        # Core files produced by cmd_epic_init
        assert (epic_dir / "epic_design.md").is_file(), "epic_design.md missing"
        assert (epic_dir / "EPIC_APPROVAL.md").is_file(), "EPIC_APPROVAL.md missing"

        # Content: epic_design.md should contain the epic ID
        design_text = (epic_dir / "epic_design.md").read_text(encoding="utf-8")
        assert "EPIC-ORDER" in design_text


# ---------------------------------------------------------------------------
# Tests: epic validate
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestEpicValidate:
    """stride epic validate should run without crashing."""

    def test_epic_validate_runs(self, bootstrap_project_root: Path):
        """epic validate on a freshly-init'd epic exits 0 and produces validation output."""
        _init_epic(bootstrap_project_root, "EPIC-VALTEST")
        result = _run(["epic", "validate", "EPIC-VALTEST"], cwd=bootstrap_project_root)

        combined = result.stdout + result.stderr
        assert "Traceback" not in combined, f"epic validate crashed:\n{combined}"
        assert result.returncode == 0, f"epic validate failed (exit {result.returncode}):\n{combined}"
        # Should produce validation-related output
        assert "EPIC-VALTEST" in combined or "Validation" in combined or "Epic" in combined


# ---------------------------------------------------------------------------
# Tests: init --epic without --team fails for multi-team epic
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestInitEpicRequiresTeam:
    """init --epic on a multi-team epic must fail if --team is omitted."""

    def test_init_epic_without_team_fails_multi_team(self, bootstrap_project_root: Path):
        """When the epic has multiple teams, --team is required."""
        # Create the epic first
        _init_epic(bootstrap_project_root, "EPIC-MTEAM")

        # The default epic_design_template.md has TEAM-A and TEAM-B,
        # so it is a multi-team epic by default.
        result = _run(
            ["init", "my_feature", "--epic", "EPIC-MTEAM"],
            cwd=bootstrap_project_root,
        )

        assert result.returncode != 0, (
            "init --epic without --team should fail for multi-team epic"
        )
        combined = result.stdout + result.stderr
        assert "team" in combined.lower(), (
            f"Error message should mention team: {combined}"
        )


# ---------------------------------------------------------------------------
# Tests: init --epic --team sets epic_ref & team_id
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestInitEpicTeam:
    """init --epic --team should scaffold a feature with epic_ref & team_id."""

    def test_init_epic_team_sets_fields(self, bootstrap_project_root: Path):
        """basic_design.md should contain the specified epic_ref and team_id."""
        # Create the epic first
        _init_epic(bootstrap_project_root, "EPIC-SETREF")

        result = _run(
            ["init", "set_ref_feat", "--epic", "EPIC-SETREF", "--team", "TEAM-A"],
            cwd=bootstrap_project_root,
            input="y\n",  # confirm overwrite if dir already exists
        )

        assert result.returncode == 0, (
            f"init --epic --team failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )

        feature_dir = bootstrap_project_root / "specs" / "set_ref_feat"
        assert feature_dir.is_dir(), "Feature directory not created"

        basic_design = feature_dir / "basic_design.md"
        assert basic_design.is_file(), "basic_design.md not created"

        bd_text = basic_design.read_text(encoding="utf-8")
        assert "EPIC-SETREF" in bd_text, (
            f"epic_ref not found in basic_design.md:\n{bd_text[:500]}"
        )
        assert "TEAM-A" in bd_text, (
            f"team_id not found in basic_design.md:\n{bd_text[:500]}"
        )

    def test_init_creates_standard_artifacts(self, bootstrap_project_root: Path):
        """Feature scaffolded with --epic should still contain standard files."""
        _init_epic(bootstrap_project_root, "EPIC-ARTIF")

        result = _run(
            ["init", "artif_feat", "--epic", "EPIC-ARTIF", "--team", "TEAM-A"],
            cwd=bootstrap_project_root,
            input="y\n",
        )

        assert result.returncode == 0, (
            f"init failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )

        feature_dir = bootstrap_project_root / "specs" / "artif_feat"
        for fname in ("basic_design.md", "process.bpmn", "spec.md", "APPROVAL.md"):
            assert (feature_dir / fname).is_file(), f"{fname} missing from feature dir"


# ---------------------------------------------------------------------------
# Tests: epic gates / features / progress
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestEpicSubcommands:
    """epic gates, epic features, epic progress should exit cleanly."""

    def _setup_epic(self, root: Path, epic_id: str = "EPIC-SUBCMD") -> None:
        """Helper: ensure an epic exists."""
        res = _init_epic(root, epic_id)
        assert res.returncode == 0, f"epic init failed: {res.stderr}"

    def test_epic_gates(self, bootstrap_project_root: Path):
        """epic gates exits 0 and mentions gate status."""
        self._setup_epic(bootstrap_project_root)

        result = _run(
            ["epic", "gates", "EPIC-SUBCMD"], cwd=bootstrap_project_root
        )

        combined = result.stdout + result.stderr
        assert "Traceback" not in combined, f"epic gates crashed:\n{combined}"
        assert result.returncode == 0, f"epic gates failed (exit {result.returncode}):\n{combined}"
        assert "EPIC-SUBCMD" in combined or "Gate" in combined or "gate" in combined

    def test_epic_features(self, bootstrap_project_root: Path):
        """epic features exits 0 and produces output."""
        self._setup_epic(bootstrap_project_root)

        result = _run(
            ["epic", "features", "EPIC-SUBCMD"], cwd=bootstrap_project_root
        )

        combined = result.stdout + result.stderr
        assert "Traceback" not in combined, f"epic features crashed:\n{combined}"
        assert result.returncode == 0, f"epic features failed (exit {result.returncode}):\n{combined}"

    def test_epic_progress(self, bootstrap_project_root: Path):
        """epic progress exits 0 and mentions epic ID."""
        self._setup_epic(bootstrap_project_root)

        result = _run(
            ["epic", "progress", "EPIC-SUBCMD"], cwd=bootstrap_project_root
        )

        combined = result.stdout + result.stderr
        assert "Traceback" not in combined, f"epic progress crashed:\n{combined}"
        assert result.returncode == 0, f"epic progress failed (exit {result.returncode}):\n{combined}"
        assert "EPIC-SUBCMD" in combined


# ---------------------------------------------------------------------------
# Tests: stride lint --enterprise
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestLintEnterprise:
    """stride lint --enterprise on a feature linked to an epic."""

    def test_lint_enterprise_on_linked_feature(self, bootstrap_project_root: Path):
        """lint --enterprise exits 0 or 1 (not 2) and produces enterprise output."""
        epic_id = "EPIC-LNTENT"
        _init_epic(bootstrap_project_root, epic_id)

        # Create feature linked to epic with valid team
        result = _run(
            ["init", "lint_ent_feat", "--epic", epic_id, "--team", "TEAM-A"],
            cwd=bootstrap_project_root,
            input="y\n",
        )
        assert result.returncode == 0, f"init --epic failed: {result.stderr}"

        # Run lint --enterprise
        result = _run(
            ["lint", "specs/lint_ent_feat/", "--enterprise"],
            cwd=bootstrap_project_root,
        )
        combined = result.stdout + result.stderr
        assert "Traceback" not in combined, f"lint --enterprise crashed:\n{combined}"
        # Exit 0 (PASS) or 1 (lint errors) are both valid; exit 2+ means config/runtime error
        assert result.returncode in (0, 1), \
            f"lint --enterprise unexpected exit {result.returncode}:\n{combined}"
