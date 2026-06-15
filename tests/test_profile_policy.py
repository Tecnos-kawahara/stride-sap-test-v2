"""Tests for v5.4 Profile Policy (reporting + completeness threshold switch).

Scope:
  - profile_policy.yaml is well-formed and defines the 3 canonical profiles
  - invariants_across_profiles uses `preserve_current` + canonical_source references
    (no new numeric fixation for BPMN / Evidence / SEC-006 / Ops / Epic-Feature / Coverage Tier)
  - stride init --profile propagates to basic_design.profile (NOT meta.profile)
  - stride init default remains enterprise-erp (no breaking change)
  - stride-lint surfaces PROFILE_UNKNOWN / PROFILE_MISSING / PROFILE_MISSING / PROFILE_MISMATCH
  - Canonical schema: basic_design.profile under basic_design: block (NOT meta.*),
    state.yaml profile at top-level (NOT workspace.*)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tests.project_builder import ProjectBuilder


_REPO_ROOT = Path(__file__).resolve().parent.parent
_POLICY_PATH = _REPO_ROOT / "shared" / "policies" / "profile_policy.yaml"
_BASIC_TEMPLATE = _REPO_ROOT / "sdd-templates" / "templates" / "basic_design_template.md"
_STATE_TEMPLATE = _REPO_ROOT / "sdd-templates" / "templates" / "state_template.yaml"
_STRIDE_BIN = _REPO_ROOT / "sdd-templates" / "bin" / "stride"
_STRIDE_LINT_DIR = _REPO_ROOT / "sdd-templates" / "tools"

KNOWN_PROFILES = ("enterprise-erp", "saas-integration", "prototype")
EXPECTED_THRESHOLDS = {
    "enterprise-erp": {"lines": 200, "files": 5},
    "saas-integration": {"lines": 150, "files": 4},
    "prototype": {"lines": 100, "files": 3},
}


# ---------------------------------------------------------------------------
# Policy file structure
# ---------------------------------------------------------------------------


class TestProfilePolicyFile:
    """profile_policy.yaml shape and invariants."""

    def test_policy_file_exists(self):
        assert _POLICY_PATH.exists(), "shared/policies/profile_policy.yaml is missing"

    def test_policy_defines_three_profiles(self):
        data = yaml.safe_load(_POLICY_PATH.read_text(encoding="utf-8"))
        profiles = data.get("profiles", {})
        assert set(profiles.keys()) == set(KNOWN_PROFILES), (
            f"profile_policy.profiles must define exactly {KNOWN_PROFILES}, "
            f"got {sorted(profiles.keys())}"
        )

    def test_profile_thresholds_match_plan(self):
        """Each profile has the exact line / file thresholds agreed in v5.4."""
        data = yaml.safe_load(_POLICY_PATH.read_text(encoding="utf-8"))
        profiles = data["profiles"]
        for name, expected in EXPECTED_THRESHOLDS.items():
            got_lines = profiles[name]["completeness_lake_max_lines"]
            got_files = profiles[name]["completeness_lake_max_files"]
            assert got_lines == expected["lines"], (
                f"profile {name}: max_lines expected {expected['lines']}, got {got_lines}"
            )
            assert got_files == expected["files"], (
                f"profile {name}: max_files expected {expected['files']}, got {got_files}"
            )

    def test_profile_reporting_formats(self):
        """Reporting format per profile matches the v5.4 agreement."""
        data = yaml.safe_load(_POLICY_PATH.read_text(encoding="utf-8"))
        assert data["profiles"]["enterprise-erp"]["task_completion_report"] == "full_5_step"
        assert data["profiles"]["saas-integration"]["task_completion_report"] == "critical_only"
        assert data["profiles"]["prototype"]["task_completion_report"] == "one_line"

    def test_invariants_preserve_current_without_new_numbers(self):
        """BPMN / Evidence / SEC-006 / Ops Pack / Epic-Feature hierarchy / Coverage Tier
        must be declared `preserve_current` with a canonical_source — not new numbers.
        """
        data = yaml.safe_load(_POLICY_PATH.read_text(encoding="utf-8"))
        inv = data.get("invariants_across_profiles", {})
        required_keys = {
            "bpmn_required",
            "evidence_pack",
            "coverage_tier_declaration",
            "epic_feature_hierarchy",
            "sec_006_provenance",
            "ops_pack",
        }
        assert required_keys.issubset(inv.keys()), (
            f"invariants_across_profiles must declare {required_keys}, "
            f"got {sorted(inv.keys())}"
        )
        for key in required_keys:
            entry = inv[key]
            assert entry.get("rule") == "preserve_current", (
                f"invariant {key}: rule must be 'preserve_current', got {entry.get('rule')!r}"
            )
            cs = entry.get("canonical_source")
            assert cs, f"invariant {key}: canonical_source must be non-empty"

    def test_profile_resolution_order_names_basic_design(self):
        data = yaml.safe_load(_POLICY_PATH.read_text(encoding="utf-8"))
        order_text = "\n".join(data["profile_resolution"]["order"])
        # SSoT is basic_design.profile (not meta.profile, not workspace.profile)
        assert "basic_design.profile" in order_text
        assert "meta.profile" not in order_text
        assert "workspace.profile" not in order_text


# ---------------------------------------------------------------------------
# Template shape
# ---------------------------------------------------------------------------


class TestTemplateSchemaCanonical:
    """basic_design.profile lives under basic_design: (NOT meta.*).
    state.yaml profile lives at top-level (NOT workspace.*).
    """

    def test_basic_design_template_has_profile_under_basic_design(self):
        text = _BASIC_TEMPLATE.read_text(encoding="utf-8")
        # Extract the canonical YAML block (between '```yaml' and closing '```')
        m = re.search(r"# 0\. Canonical Basic Design.*?```yaml\s*(.*?)```", text, re.DOTALL)
        assert m, "Could not find Canonical Basic Design YAML block"
        data = yaml.safe_load(m.group(1))
        assert "basic_design" in data
        assert "profile" in data["basic_design"], (
            "basic_design.profile must exist under the basic_design: block"
        )
        assert data["basic_design"]["profile"] == "enterprise-erp", (
            "Template default profile must be enterprise-erp (backward-compat default)"
        )
        # MUST NOT introduce meta.profile nesting
        assert "meta" not in data or "profile" not in (data.get("meta") or {}), (
            "meta.profile must NOT exist (profile is a basic_design.* field, not meta.*)"
        )

    def test_state_template_has_top_level_profile(self):
        data = yaml.safe_load(_STATE_TEMPLATE.read_text(encoding="utf-8"))
        assert "profile" in data, "state_template.yaml must have top-level `profile`"
        assert data["profile"] == "enterprise-erp"
        # Flat schema: workspace.* must NOT exist
        assert "workspace" not in data, (
            "state_template.yaml uses flat schema — workspace.* nesting is forbidden"
        )


# ---------------------------------------------------------------------------
# stride init CLI — --profile flag
# ---------------------------------------------------------------------------


def _run_stride_init(cwd: Path, *extra: str, overwrite: bool = False) -> subprocess.CompletedProcess:
    """Run `stride init <feature>` inside cwd and return the completed process.

    When overwrite=False (default), stdin declines the "Overwrite templates?" prompt
    so a first-run succeeds and a re-run on an existing feature aborts cleanly.
    When overwrite=True, stdin answers 'y' so stride init re-scaffolds the feature
    (used to test re-run behaviour like state.yaml preservation).
    """
    cmd = [str(_STRIDE_BIN), "init", *extra]
    stdin = "y\n" if overwrite else "\n"
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        input=stdin,
        timeout=120,
        env={**os.environ, "STRIDE_ACTOR": "test"},
    )


class TestStrideInitProfileFlag:
    """stride init --profile propagates to BOTH sides of the SSoT + cache contract:
    - basic_design.md → basic_design.profile (SSoT, under basic_design:, NOT meta.*)
    - state.yaml      → top-level `profile` (flat schema cache, NOT workspace.*)

    Both must be set with the same value so stride-lint never emits PROFILE_MISMATCH
    immediately after init (regression guard for the P1 bug where only basic_design
    was being updated).
    """

    @pytest.mark.parametrize("profile", KNOWN_PROFILES)
    def test_init_with_each_profile(self, tmp_path, profile):
        root = ProjectBuilder(tmp_path).build()
        result = _run_stride_init(root, "profiletest", "--profile", profile)
        assert result.returncode == 0, (
            f"stride init --profile {profile} failed:\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )

        # (a) basic_design.md side (SSoT)
        bd_path = root / "specs" / "profiletest" / "basic_design.md"
        assert bd_path.exists(), "basic_design.md not created"
        bd_text = bd_path.read_text(encoding="utf-8")
        assert f'profile: "{profile}"' in bd_text, (
            f"basic_design.profile not set to {profile!r}\n{bd_text[:2000]}"
        )
        # meta.profile must NEVER appear (canonical schema compliance)
        assert "meta.profile" not in bd_text

        # (b) state.yaml side (cache) — critical regression guard
        state_path = root / "specs" / "profiletest" / "state" / "state.yaml"
        assert state_path.exists(), (
            f"state/state.yaml must be created by stride init so the profile cache "
            f"is synchronised with basic_design.profile from day one "
            f"(SSoT + cache contract per shared/policies/profile_policy.yaml)"
        )
        state_data = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        assert isinstance(state_data, dict), "state.yaml must parse to a mapping"
        assert state_data.get("profile") == profile, (
            f"state.yaml top-level profile expected {profile!r}, "
            f"got {state_data.get('profile')!r} — mismatch would trigger PROFILE_MISMATCH"
        )
        # Flat schema: workspace.* must NOT appear
        assert "workspace" not in state_data, (
            "state.yaml must use flat schema — workspace.* nesting is forbidden"
        )

        # (c) Cross-file consistency — same value on both sides means no PROFILE_MISMATCH
        bd_profile_match = re.search(r'profile:\s*"([^"]+)"', bd_text)
        assert bd_profile_match and bd_profile_match.group(1) == state_data["profile"], (
            f"basic_design.profile ({bd_profile_match.group(1) if bd_profile_match else None}) "
            f"must equal state.yaml profile ({state_data.get('profile')}) — "
            f"drift would be caught by stride-lint as PROFILE_MISMATCH"
        )

    def test_init_without_profile_defaults_enterprise_erp(self, tmp_path):
        root = ProjectBuilder(tmp_path).build()
        result = _run_stride_init(root, "defaultfeat")
        assert result.returncode == 0, (
            f"stride init without --profile failed:\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )

        # Both sides must reflect the default (enterprise-erp) — backward compat
        bd_path = root / "specs" / "defaultfeat" / "basic_design.md"
        assert 'profile: "enterprise-erp"' in bd_path.read_text(encoding="utf-8")

        state_path = root / "specs" / "defaultfeat" / "state" / "state.yaml"
        assert state_path.exists(), (
            "state/state.yaml must be created even without --profile "
            "(the cache must exist and match basic_design default)"
        )
        state_data = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        assert state_data.get("profile") == "enterprise-erp", (
            f"Default path: state.yaml profile expected 'enterprise-erp', "
            f"got {state_data.get('profile')!r}"
        )

    def test_init_rejects_unknown_profile(self, tmp_path):
        root = ProjectBuilder(tmp_path).build()
        result = _run_stride_init(root, "badprofilefeat", "--profile", "bogus-tier")
        assert result.returncode != 0, (
            "stride init must reject unknown --profile values"
        )
        combined = (result.stdout + result.stderr).lower()
        assert "invalid profile" in combined or "bogus-tier" in combined

    def test_init_upgrades_pre_v54_state_yaml_without_profile(self, tmp_path):
        """Pre-v5.4 state.yaml has no `profile` field. Re-running stride init must
        append the field (not fail, not clobber the file) so existing projects can
        adopt v5.4 without losing data.
        """
        root = ProjectBuilder(tmp_path).build()
        first = _run_stride_init(root, "legacyfeat", "--profile", "enterprise-erp")
        assert first.returncode == 0

        # Simulate a pre-v5.4 state.yaml: no profile field, only legacy fields
        state_path = root / "specs" / "legacyfeat" / "state" / "state.yaml"
        state_path.write_text(
            "feature: FEAT-LEGACYFEAT\n"
            "current_gate: Gate3\n"
            "autonomy_bias: balanced\n"
            "work_items:\n"
            "  - wi_id: WI-LEG-001\n"
            "    status: done\n"
            "run_index:\n"
            "  WI-LEG-001: RUN-001\n",
            encoding="utf-8",
        )
        assert "profile" not in yaml.safe_load(state_path.read_text(encoding="utf-8"))

        # Re-run init — profile must be appended without destroying legacy fields
        second = _run_stride_init(root, "legacyfeat", "--profile", "saas-integration", overwrite=True)
        assert second.returncode == 0, (
            f"Re-run on legacy state.yaml failed:\n"
            f"stdout={second.stdout}\nstderr={second.stderr}"
        )
        after = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        assert after.get("profile") == "saas-integration"
        assert after.get("current_gate") == "Gate3", (
            "Legacy current_gate must survive the profile upgrade"
        )
        assert after.get("work_items") == [{"wi_id": "WI-LEG-001", "status": "done"}]
        assert after.get("run_index") == {"WI-LEG-001": "RUN-001"}

    def test_init_preserves_existing_state_yaml_work_items(self, tmp_path):
        """Re-running stride init must update profile cache WITHOUT clobbering
        user-authored work_items or run_index in an existing state.yaml.
        """
        root = ProjectBuilder(tmp_path).build()
        # First init creates state.yaml
        first = _run_stride_init(root, "preservefeat", "--profile", "enterprise-erp")
        assert first.returncode == 0

        # User-authored work_items in state.yaml
        state_path = root / "specs" / "preservefeat" / "state" / "state.yaml"
        original_data = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        original_data["work_items"] = [
            {"wi_id": "WI-PRESERVE-001", "status": "done", "mode": "autopilot"},
        ]
        original_data["run_index"] = {"WI-PRESERVE-001": "RUN-001"}
        state_path.write_text(yaml.dump(original_data, allow_unicode=True), encoding="utf-8")

        # Re-run init with a different profile — profile must update, work_items must survive
        second = _run_stride_init(root, "preservefeat", "--profile", "prototype", overwrite=True)
        assert second.returncode == 0, (
            f"Re-run of stride init failed:\n"
            f"stdout={second.stdout}\nstderr={second.stderr}"
        )

        after_data = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        assert after_data.get("profile") == "prototype", (
            "Re-run must update profile cache to match new basic_design.profile"
        )
        assert after_data.get("work_items") == [
            {"wi_id": "WI-PRESERVE-001", "status": "done", "mode": "autopilot"},
        ], "User-authored work_items must be preserved across stride init re-runs"
        assert after_data.get("run_index") == {"WI-PRESERVE-001": "RUN-001"}, (
            "User-authored run_index must be preserved across stride init re-runs"
        )


# ---------------------------------------------------------------------------
# stride-lint — PROFILE_UNKNOWN / PROFILE_MISSING / PROFILE_MISMATCH
# ---------------------------------------------------------------------------


@pytest.fixture
def lint_mod(monkeypatch):
    """Import stride_lint from sdd-templates/tools/ on a clean path."""
    if str(_STRIDE_LINT_DIR) not in sys.path:
        sys.path.insert(0, str(_STRIDE_LINT_DIR))
    import importlib
    import stride_lint as mod
    importlib.reload(mod)
    return mod


class TestLintProfileChecks:

    def test_known_profiles_constant(self, lint_mod):
        assert set(lint_mod.KNOWN_PROFILES) == set(KNOWN_PROFILES)
        assert lint_mod.DEFAULT_PROFILE == "enterprise-erp"

    def test_profile_missing_warns(self, lint_mod, tmp_path):
        """basic_design.profile absent → PROFILE_MISSING warning, not error."""
        project = (
            ProjectBuilder(tmp_path)
            .add_feature("FEAT-NOPROF", mode="full", phase=5, coverage_tier="standard")
            .done()
            .build()
        )
        feature_dir = project / "specs" / "FEAT-NOPROF"
        bd = feature_dir / "basic_design.md"
        text = bd.read_text(encoding="utf-8")
        # Remove the profile line from the canonical YAML
        text = re.sub(r"^\s*profile:\s*\"enterprise-erp\".*\n", "", text, flags=re.MULTILINE)
        bd.write_text(text, encoding="utf-8")

        result = lint_mod.lint_feature(str(feature_dir), lint_mod.LintConfig())
        warn_codes = {w["code"] for w in result.warnings}
        assert "PROFILE_MISSING" in warn_codes, (
            f"Expected PROFILE_MISSING warning, got warnings={warn_codes}, "
            f"errors={[e['code'] for e in result.errors]}"
        )

    def test_profile_unknown_errors(self, lint_mod, tmp_path):
        """basic_design.profile with an invalid value → PROFILE_UNKNOWN error."""
        project = (
            ProjectBuilder(tmp_path)
            .add_feature("FEAT-BADPROF", mode="full", phase=5, coverage_tier="standard")
            .done()
            .build()
        )
        feature_dir = project / "specs" / "FEAT-BADPROF"
        bd = feature_dir / "basic_design.md"
        text = bd.read_text(encoding="utf-8")
        text = re.sub(
            r'profile:\s*"enterprise-erp"',
            'profile: "not-a-real-profile"',
            text,
            count=1,
        )
        bd.write_text(text, encoding="utf-8")

        result = lint_mod.lint_feature(str(feature_dir), lint_mod.LintConfig())
        err_codes = {e["code"] for e in result.errors}
        assert "PROFILE_UNKNOWN" in err_codes

    def test_profile_mismatch_errors(self, lint_mod, tmp_path):
        """basic_design.profile != state.yaml top-level profile → PROFILE_MISMATCH."""
        project = (
            ProjectBuilder(tmp_path)
            .add_feature("FEAT-MISMATCH", mode="full", phase=5, coverage_tier="standard")
            .done()
            .build()
        )
        feature_dir = project / "specs" / "FEAT-MISMATCH"

        # Set basic_design.profile = saas-integration
        bd = feature_dir / "basic_design.md"
        text = bd.read_text(encoding="utf-8")
        text = re.sub(
            r'profile:\s*"enterprise-erp"',
            'profile: "saas-integration"',
            text,
            count=1,
        )
        bd.write_text(text, encoding="utf-8")

        # Write state.yaml with DIFFERENT top-level profile
        state_dir = feature_dir / "state"
        state_dir.mkdir(exist_ok=True)
        (state_dir / "state.yaml").write_text(
            "feature: FEAT-MISMATCH\n"
            "profile: prototype\n"  # mismatch (basic_design says saas-integration)
            "work_items: []\n",
            encoding="utf-8",
        )

        result = lint_mod.lint_feature(str(feature_dir), lint_mod.LintConfig())
        err_codes = {e["code"] for e in result.errors}
        assert "PROFILE_MISMATCH" in err_codes, (
            f"Expected PROFILE_MISMATCH, got errors={err_codes}"
        )

    def test_profile_match_passes_profile_check(self, lint_mod, tmp_path):
        """basic_design.profile == state.yaml profile → no PROFILE_* issues from profile check."""
        project = (
            ProjectBuilder(tmp_path)
            .add_feature("FEAT-OK", mode="full", phase=5, coverage_tier="standard")
            .done()
            .build()
        )
        feature_dir = project / "specs" / "FEAT-OK"
        state_dir = feature_dir / "state"
        state_dir.mkdir(exist_ok=True)
        (state_dir / "state.yaml").write_text(
            "feature: FEAT-OK\n"
            "profile: enterprise-erp\n"
            "work_items: []\n",
            encoding="utf-8",
        )

        result = lint_mod.lint_feature(str(feature_dir), lint_mod.LintConfig())
        profile_codes = {
            issue["code"]
            for issue in (result.errors + result.warnings)
            if issue["code"].startswith("PROFILE_")
        }
        assert profile_codes == set(), (
            f"Profile-consistent project should have zero PROFILE_* issues, "
            f"got {profile_codes}"
        )
