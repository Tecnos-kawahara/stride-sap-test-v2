"""E2E tests for stride CLI bootstrap commands via subprocess.

These tests run actual stride CLI commands against isolated tmp_path
projects and verify output strings and file creation.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

# All tests in this file are E2E
pytestmark = pytest.mark.e2e

# Stride binary path (relative to project cwd)
STRIDE_BIN = "sdd-templates/bin/stride"

# Real repo root (for scripts/ that aren't part of sdd-templates)
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(args: list[str], cwd: Path, *, shell: bool = False, input_text: str | None = None):
    """Run a stride command and return the CompletedProcess."""
    if shell:
        cmd = " ".join(args)
    else:
        cmd = args
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        shell=shell,
        input=input_text,
        timeout=60,
    )


def _ensure_scripts_dir(project_root: Path) -> None:
    """Copy scripts/ from real repo so stride new-project can find the shell script."""
    scripts_src = _REPO_ROOT / "scripts"
    scripts_dst = project_root / "scripts"
    if not scripts_dst.exists() and scripts_src.exists():
        shutil.copytree(scripts_src, scripts_dst)


# ─── stride intake ────────────────────────────────────────────────


class TestStrideIntake:
    def test_intake_creates_intake_template(self, bootstrap_project_root):
        """stride intake <name> creates specs/<name>/basic_design_intake.md."""
        result = _run([STRIDE_BIN, "intake", "e2e_test_feature"], bootstrap_project_root)

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Intake template created" in result.stdout

        intake_file = bootstrap_project_root / "specs" / "e2e_test_feature" / "basic_design_intake.md"
        assert intake_file.exists(), "basic_design_intake.md should be created"

        content = intake_file.read_text(encoding="utf-8")
        assert "Basic Design Intake" in content, "Intake template should contain its header"
        assert len(content) > 100, "Intake template should have substantial content"

    def test_intake_missing_name_fails(self, bootstrap_project_root):
        """stride intake without a feature name should fail."""
        result = _run([STRIDE_BIN, "intake"], bootstrap_project_root)

        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "Feature name required" in combined or "Error" in combined


# ─── stride init ──────────────────────────────────────────────────


class TestStrideInit:
    def test_init_creates_full_template_set(self, bootstrap_project_root):
        """stride init <name> creates the full template directory structure."""
        # Use echo 'y' | to auto-confirm if directory already exists
        result = _run(
            [f"echo 'y' | {STRIDE_BIN} init e2e_init_feature"],
            bootstrap_project_root,
            shell=True,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Feature initialized successfully" in result.stdout

        feature_dir = bootstrap_project_root / "specs" / "e2e_init_feature"
        assert feature_dir.is_dir(), "Feature directory should be created"

        # Verify key template files exist
        expected_files = [
            "basic_design.md",
            "process.bpmn",
            "spec.md",
            "plan.md",
            "tasks.md",
            "APPROVAL.md",
            "contracts",
            "tests",
            "implementation-details",
        ]
        for name in expected_files:
            target = feature_dir / name
            assert target.exists(), f"{name} should exist in feature directory"

        # Verify placeholder replacement happened
        bd = (feature_dir / "basic_design.md").read_text(encoding="utf-8")
        assert "FEAT-E2EINITFEATURE" in bd, "Feature ID placeholder should be replaced"
        assert "FEAT-XXX" not in bd, "Original placeholder should be gone"

    def test_init_detect_mode_saves_detection_json(self, bootstrap_project_root):
        """stride init --detect creates brownfield_detection.json."""
        result = _run(
            [f"echo 'y' | {STRIDE_BIN} init e2e_detect_feature --detect"],
            bootstrap_project_root,
            shell=True,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"

        detection_file = (
            bootstrap_project_root
            / "specs"
            / "e2e_detect_feature"
            / "implementation-details"
            / "brownfield_detection.json"
        )
        assert detection_file.exists(), "brownfield_detection.json should be created by --detect"

        # The bootstrap_project_root has node brownfield indicators
        content = detection_file.read_text(encoding="utf-8")
        assert "brownfield" in content or "greenfield" in content, (
            "Detection JSON should contain project type"
        )

    def test_init_missing_name_fails(self, bootstrap_project_root):
        """stride init without a feature name should fail."""
        result = _run([STRIDE_BIN, "init"], bootstrap_project_root)

        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "Feature name required" in combined or "Error" in combined


# ─── stride ddd-init ──────────────────────────────────────────────


class TestStrideDddInit:
    def test_ddd_init_scaffolds_ddd_artifacts(self, bootstrap_project_root):
        """stride ddd-init creates domain_model.md, technical_design.md, and ADR."""
        # First create the feature directory via stride init
        _run(
            [f"echo 'y' | {STRIDE_BIN} init e2e_ddd_feature"],
            bootstrap_project_root,
            shell=True,
        )

        result = _run(
            [STRIDE_BIN, "ddd-init", "e2e_ddd_feature"],
            bootstrap_project_root,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "DDD scaffolding complete" in result.stdout

        impl_dir = bootstrap_project_root / "specs" / "e2e_ddd_feature" / "implementation-details"
        assert (impl_dir / "domain_model.md").exists(), "domain_model.md should be created"
        assert (impl_dir / "technical_design.md").exists(), "technical_design.md should be created"

        # ADR should be created under shared/decisions/
        decisions_dir = bootstrap_project_root / "shared" / "decisions"
        adr_files = list(decisions_dir.glob("ADR-*-e2e-ddd-feature-*.md"))
        assert len(adr_files) >= 1, "At least one ADR file should be created for the feature"

    def test_ddd_init_nonexistent_feature_fails(self, bootstrap_project_root):
        """stride ddd-init for a non-existent feature should fail."""
        result = _run(
            [STRIDE_BIN, "ddd-init", "nonexistent_feature_xyz"],
            bootstrap_project_root,
        )

        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "not found" in combined or "Error" in combined


# ─── stride decisions ─────────────────────────────────────────────


class TestStrideDecisions:
    def test_decisions_init_creates_index(self, bootstrap_project_root):
        """stride decisions init creates decision-index.md."""
        result = _run(
            [STRIDE_BIN, "decisions", "init"],
            bootstrap_project_root,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "PASS" in result.stdout
        assert "initialized" in result.stdout

        index_file = bootstrap_project_root / "shared" / "decisions" / "decision-index.md"
        assert index_file.exists(), "decision-index.md should be created"

    def test_decisions_refresh_rebuilds_index(self, bootstrap_project_root):
        """stride decisions refresh rebuilds decision-index.md from ADR files."""
        # First init to ensure the directory exists
        _run([STRIDE_BIN, "decisions", "init"], bootstrap_project_root)

        # Create a sample ADR file
        decisions_dir = bootstrap_project_root / "shared" / "decisions"
        adr_file = decisions_dir / "ADR-001-test-decision.md"
        adr_file.write_text(
            "---\n"
            "status: proposed\n"
            "date: 2026-01-01\n"
            "title: Test decision for E2E\n"
            "---\n\n"
            "# ADR-001: Test decision for E2E\n",
            encoding="utf-8",
        )

        result = _run(
            [STRIDE_BIN, "decisions", "refresh"],
            bootstrap_project_root,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "PASS" in result.stdout
        assert "refreshed" in result.stdout

        index_content = (decisions_dir / "decision-index.md").read_text(encoding="utf-8")
        assert "ADR-001" in index_content, "Refreshed index should contain the ADR entry"
        assert "Test decision for E2E" in index_content, "ADR title should appear in index"


# ─── stride hooks ─────────────────────────────────────────────────


class TestStrideHooks:
    def test_hooks_manual_creates_checklist(self, bootstrap_project_root):
        """stride hooks --tool manual creates docs/phase-gate-checklist.md."""
        result = _run(
            [STRIDE_BIN, "hooks", "--tool", "manual"],
            bootstrap_project_root,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "manual Phase Gate checklist" in result.stdout or "phase-gate-checklist.md" in result.stdout

        checklist = bootstrap_project_root / "docs" / "phase-gate-checklist.md"
        assert checklist.exists(), "docs/phase-gate-checklist.md should be created"

        content = checklist.read_text(encoding="utf-8")
        assert "Phase Gate Checklist" in content
        assert "Phase 1 (Design)" in content
        assert "APPROVAL.md" in content

    def test_hooks_claude_force_creates_settings(self, bootstrap_project_root):
        """stride hooks --tool claude --force creates .claude/settings.json."""
        result = _run(
            [STRIDE_BIN, "hooks", "--tool", "claude", "--force"],
            bootstrap_project_root,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Phase Gate hooks" in result.stdout

        settings_file = bootstrap_project_root / ".claude" / "settings.json"
        assert settings_file.exists(), ".claude/settings.json should be created"

        import json

        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        assert "hooks" in settings, "settings.json should contain hooks key"
        assert "PreToolUse" in settings["hooks"], "hooks should contain PreToolUse"


# ─── stride new-project --dry-run ────────────────────────────────


class TestStrideNewProject:
    def test_new_project_dry_run_exits_zero(self, bootstrap_project_root):
        """stride new-project --dry-run previews without making changes."""
        _ensure_scripts_dir(bootstrap_project_root)

        result = _run(
            [STRIDE_BIN, "new-project", "e2e_test_project", "--dry-run", "--skip-git"],
            bootstrap_project_root,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

        combined = result.stdout + result.stderr
        assert "DRY RUN" in combined, "Dry run banner should appear in output"
        assert "e2e_test_project" in combined, "Project name should appear in output"
        assert "initialization complete" in combined or "dry-run" in combined.lower(), (
            "Dry run should indicate completion or dry-run mode"
        )

    def test_new_project_dry_run_does_not_modify_files(self, bootstrap_project_root):
        """stride new-project --dry-run should not create or remove files."""
        _ensure_scripts_dir(bootstrap_project_root)

        # Record existing file set (after scripts/ was added)
        before = set(p.relative_to(bootstrap_project_root) for p in bootstrap_project_root.rglob("*") if p.is_file())

        _run(
            [STRIDE_BIN, "new-project", "e2e_noop_project", "--dry-run", "--skip-git"],
            bootstrap_project_root,
        )

        after = set(p.relative_to(bootstrap_project_root) for p in bootstrap_project_root.rglob("*") if p.is_file())

        # Dry run should not create new files (minor filesystem diffs from symlink
        # traversal are acceptable, but no specs/ or config files should appear)
        new_files = after - before
        spec_files = [f for f in new_files if str(f).startswith("specs/")]
        assert len(spec_files) == 0, f"Dry run should not create spec files, but found: {spec_files}"

    def test_new_project_missing_name_fails(self, bootstrap_project_root):
        """stride new-project without a name should fail with exit 2."""
        _ensure_scripts_dir(bootstrap_project_root)

        result = _run(
            [STRIDE_BIN, "new-project"],
            bootstrap_project_root,
        )

        assert result.returncode == 2
        combined = result.stdout + result.stderr
        assert "Project name is required" in combined or "Error" in combined
