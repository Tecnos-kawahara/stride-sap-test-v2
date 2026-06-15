# 指示プロンプト: STRIDE 統合テストフレームワーク Phase 1

**作業ディレクトリ:** `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

---

## 背景と目的

Tecnos-STRIDE テンプレートには 26 個の Python ツールと bash CLI（1,738行）があるが、
ツール間連携の統合テストがほぼゼロである。

**既知の実不具合:** `pr_readiness_checker.py:130` が `lint_feature(str(feature_dir), {})` と
`dict` を渡しているが、`lint_feature()` の第2引数は `LintConfig` オブジェクトを期待する。
内部で `config.coverage_report`（L1888）にアクセスした時点で
`'dict' object has no attribute 'coverage_report'` が発生し、
`stride pr-check .` の stride-lint チェックが常に `WARN` に降格する。

**Phase 1 の目標:**
1. `tmp_path` に isolated な mini project root を構築する `ProjectBuilder` を作る
2. stride-lint の import 経路（`check_stride_lint()` 経由）の回帰テストを最初に作る
3. phase_gate, auto_continue, pr_readiness の統合テストを作る
4. 既存の 242 テスト（symphony/tests/）に影響を与えない

---

## 実装前に必ず読むこと

```bash
# 1. 実不具合の確認
grep -n "lint_mod.lint_feature" sdd-templates/tools/pr_readiness_checker.py
# → L130: lint_mod.lint_feature(str(feature_dir), {})  ← {} が問題

# 2. lint_feature() のシグネチャと LintConfig を確認
grep -n "def lint_feature\|class LintConfig\|class LintResult" sdd-templates/tools/stride_lint.py

# 3. phase_gate.py が Full/Lite のみであることを確認（Enterprise は別）
grep -n "PHASE_DEFINITIONS" sdd-templates/tools/phase_gate.py

# 4. auto_continue_runner.py の FULL_WORKFLOW / LITE_WORKFLOW を確認
grep -A2 "phase_name" sdd-templates/tools/auto_continue_runner.py

# 5. lint_feature() が期待する project root 構造を確認
grep -n "constitution_path\|artifact_registry_path\|root_dir" sdd-templates/tools/stride_lint.py | head -10

# 6. memory/ の中身（lint が依存する）
ls memory/

# 7. 既存テスト配置を確認
cat pyproject.toml
ls symphony/tests/

# 8. pr_readiness_checker.py の全チェック関数を確認
grep "^def check_" sdd-templates/tools/pr_readiness_checker.py

# 9. spec_drift_detector.py が project root を前提にしていることを確認
grep -n "project_root\|specs_dir\|src_dir" sdd-templates/tools/spec_drift_detector.py | head -10
```

---

## Step 1: `pyproject.toml` を更新する

```toml
[tool.pytest.ini_options]
testpaths = ["symphony/tests", "tests"]
pythonpath = ["."]
markers = [
    "api: tests that call external APIs (deselect with -m 'not api')",
    "slow: slow tests (deselect with -m 'not slow')",
    "e2e: end-to-end workflow tests (deselect with -m 'not e2e')",
]
```

---

## Step 2: `tests/project_builder.py` — mini project root 生成器

### 設計原則

1. **全テストは `tmp_path` 内で完結する。** repo 直下を一切触らない
2. **read-only リソースは symlink、mutable リソースは copy。**
   - **symlink 可:** `sdd-templates/tools/`, `sdd-templates/templates/`, `sdd-templates/hooks/`, `sdd-templates/bin/`
   - **copy 必須:** `sdd-templates/config/`, `memory/`, `shared/`, `.github/`
   - 理由: `enterprise.yaml` のフラグ変更や `memory/constitution.md` の編集がテスト間で干渉しないようにする
3. **FEAT-ERPSAMPLE をテンプレートとして使い、diff ベースで最小変更する。** 丸ごとコピーではない
4. **`state/` ディレクトリの timestamp 付きファイルはコピーしない。** fixture の正本に不適

### ProjectBuilder クラス

```python
"""Mini project root generator for integration tests."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Self


# Path to the real repo root (resolved at import time)
_REPO_ROOT = Path(__file__).resolve().parent.parent


class ProjectBuilder:
    """Build an isolated STRIDE project root in a temporary directory.

    Usage:
        project = (
            ProjectBuilder(tmp_path)
            .add_feature("FEAT-TEST", mode="full", phase=2, coverage_tier="standard")
            .build()
        )
        # project is a Path to the mini project root
    """

    def __init__(self, root: Path):
        self.root = root
        self._features: list[FeatureBuilder] = []
        self._epics: list[dict] = []
        self._enterprise_enabled: bool = False

    def add_feature(self, feature_id: str, **kwargs) -> FeatureBuilder:
        """Add a feature and return its builder for further customization."""
        fb = FeatureBuilder(self, feature_id, **kwargs)
        self._features.append(fb)
        return fb

    def enable_enterprise(self) -> Self:
        """Enable enterprise mode in config."""
        self._enterprise_enabled = True
        return self

    def build(self) -> Path:
        """Construct the project root and return its path."""
        self._setup_sdd_templates()
        self._setup_memory()
        self._setup_shared()
        self._setup_config()
        self._create_specs_dir()

        for fb in self._features:
            fb._build()

        return self.root

    def _setup_sdd_templates(self) -> None:
        """Symlink read-only dirs, copy mutable ones."""
        sdd = self.root / "sdd-templates"
        sdd.mkdir(parents=True, exist_ok=True)

        # Symlink: read-only resources
        for name in ("tools", "templates", "hooks", "bin", "specs"):
            src = _REPO_ROOT / "sdd-templates" / name
            if src.exists():
                dst = sdd / name
                dst.symlink_to(src)

        # Copy: mutable resources
        for name in ("config",):
            src = _REPO_ROOT / "sdd-templates" / name
            if src.exists():
                shutil.copytree(src, sdd / name)

        # VERSION file (if exists)
        version_file = _REPO_ROOT / "sdd-templates" / "VERSION"
        if version_file.exists():
            shutil.copy2(version_file, sdd / "VERSION")

        # requirements files
        for req in _REPO_ROOT.glob("sdd-templates/requirements*.txt"):
            shutil.copy2(req, sdd / req.name)

    def _setup_memory(self) -> None:
        """Copy memory/ — lint_feature() requires constitution.md and artifact_registry.md."""
        src = _REPO_ROOT / "memory"
        if src.exists():
            shutil.copytree(src, self.root / "memory")

    def _setup_shared(self) -> None:
        """Copy shared/ — enterprise and dependency tools need this."""
        src = _REPO_ROOT / "shared"
        if src.exists():
            shutil.copytree(src, self.root / "shared")

    def _setup_config(self) -> None:
        """Adjust enterprise config if needed."""
        if self._enterprise_enabled:
            config_path = self.root / "sdd-templates" / "config" / "enterprise.yaml"
            if config_path.exists():
                text = config_path.read_text(encoding="utf-8")
                text = re.sub(r"enabled:\s*false", "enabled: true", text)
                config_path.write_text(text, encoding="utf-8")

    def _create_specs_dir(self) -> None:
        (self.root / "specs").mkdir(exist_ok=True)
```

### FeatureBuilder クラス

```python
class FeatureBuilder:
    """Build a feature directory inside a ProjectBuilder project."""

    # Gate sets for each phase level
    _FULL_GATES = {
        0: set(),
        1: set(),             # Phase 1 in progress (no gates approved yet)
        2: {1, 2},            # Design approved → Specify in progress
        3: {1, 2, 3, 4},      # Specify approved → Tasking in progress
        4: {1, 2, 3, 4, 5},   # Tasking approved → Execute in progress
        5: {1, 2, 3, 4, 5, "final"},  # All approved
    }
    _LITE_GATES = {
        0: set(),
        1: set(),
        2: {"A"},
        3: {"A", "B"},
        4: {"A", "B", "C"},  # All approved
    }

    def __init__(
        self,
        project: ProjectBuilder,
        feature_id: str,
        mode: str = "full",
        phase: int = 5,  # default: fully approved
        coverage_tier: str = "standard",
    ):
        self._project = project
        self.feature_id = feature_id
        self.mode = mode
        self.phase = phase
        self.coverage_tier = coverage_tier
        self._erp_addon = False
        self._epic_ref: str | None = None
        self._team_id: str | None = None
        self._lint_mutations: list[str] = []
        self._custom_gates: set | None = None

    def with_erp_addon(self) -> Self:
        self._erp_addon = True
        return self

    def with_enterprise(self, epic_id: str, team_id: str = "TEAM-TEST") -> Self:
        self._epic_ref = epic_id
        self._team_id = team_id
        return self

    def mutate_lint_error(self, error_type: str) -> Self:
        """Queue a mutation that will break the feature in a specific way.

        error_types:
            'missing_ac' — remove acceptance criteria from spec
            'broken_traceability' — break spec_refs in tasks
            'missing_nfr' — remove NFR section from spec
            'missing_bpmn' — delete process.bpmn
            'phase_violation' — create Phase 2 files without Gate 1,2 approval
        """
        self._lint_mutations.append(error_type)
        return self

    def with_approval(self, gates: set) -> Self:
        """Override auto-calculated gates with explicit set."""
        self._custom_gates = gates
        return self

    def done(self) -> ProjectBuilder:
        """Return to the parent ProjectBuilder for chaining."""
        return self._project

    def _build(self) -> Path:
        """Generate the feature directory."""
        feature_dir = self._project.root / "specs" / self.feature_id
        sample_dir = _REPO_ROOT / "specs" / "FEAT-ERPSAMPLE"

        # Copy base files from FEAT-ERPSAMPLE (excluding state/)
        for item in sample_dir.iterdir():
            if item.name == "state":
                continue  # Skip timestamp-bearing evaluator outputs
            dst = feature_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dst)

        # state/ dir (empty, for tools that write to it)
        (feature_dir / "state").mkdir(exist_ok=True)

        # Rewrite feature_id in all files
        self._rewrite_ids(feature_dir)

        # Set coverage_tier in basic_design
        self._set_coverage_tier(feature_dir)

        # Set enterprise fields
        if self._epic_ref:
            self._set_enterprise_fields(feature_dir)

        # Set APPROVAL.md based on mode and phase
        self._write_approval(feature_dir)

        # Apply lint error mutations
        for mutation in self._lint_mutations:
            self._apply_mutation(feature_dir, mutation)

        # ERP Addon
        if not self._erp_addon:
            # Remove ERP addon dirs if they exist (copied from sample)
            for d in ("work_items", "runs", "ops"):
                p = feature_dir / d
                if p.exists():
                    shutil.rmtree(p)
            for f in ("erp_addon_mode_policy.yaml", "erp_addon_risk_taxonomy.yaml"):
                p = feature_dir / f
                if p.exists():
                    p.unlink()

        return feature_dir

    def _rewrite_ids(self, feature_dir: Path) -> None:
        """Replace FEAT-ERPSAMPLE / FEATERPOMS with the new feature_id."""
        old_ids = ["FEAT-ERPSAMPLE", "FEATERPOMS", "ERPSAMPLE"]
        new_id = self.feature_id
        short_id = new_id.replace("FEAT-", "").replace("-", "")

        for p in feature_dir.rglob("*"):
            if p.is_file() and p.suffix in (".md", ".yaml", ".yml", ".bpmn"):
                try:
                    text = p.read_text(encoding="utf-8")
                    text = text.replace("FEAT-ERPSAMPLE", new_id)
                    text = text.replace("FEATERPOMS", short_id)
                    text = text.replace("ERPSAMPLE", short_id)
                    p.write_text(text, encoding="utf-8")
                except UnicodeDecodeError:
                    pass

    def _set_coverage_tier(self, feature_dir: Path) -> None:
        bd = feature_dir / "basic_design.md"
        if bd.exists():
            text = bd.read_text(encoding="utf-8")
            text = re.sub(r'coverage_tier:\s*"\w+"', f'coverage_tier: "{self.coverage_tier}"', text)
            bd.write_text(text, encoding="utf-8")

    def _set_enterprise_fields(self, feature_dir: Path) -> None:
        bd = feature_dir / "basic_design.md"
        if bd.exists():
            text = bd.read_text(encoding="utf-8")
            text = re.sub(r'epic_ref:\s*"[^"]*"', f'epic_ref: "{self._epic_ref}"', text)
            text = re.sub(r'team_id:\s*"[^"]*"', f'team_id: "{self._team_id}"', text)
            bd.write_text(text, encoding="utf-8")

    def _write_approval(self, feature_dir: Path) -> None:
        """Generate APPROVAL.md with correct mode and gate approvals."""
        if self._custom_gates is not None:
            approved = self._custom_gates
        elif self.mode == "lite":
            approved = self._LITE_GATES.get(self.phase, set())
        else:
            approved = self._FULL_GATES.get(self.phase, set())

        lines: list[str] = []
        if self.mode == "lite":
            lines.append("# APPROVAL (Lite Mode)\n")
            for gate in ("A", "B", "C"):
                check = "x" if gate in approved else " "
                lines.append(f"## Gate {gate}\n- [{check}] Review complete")
                if gate in approved:
                    lines.append("承認者: Test Approver\n")
                else:
                    lines.append("承認者: ___________\n")
        else:
            lines.append("# APPROVAL\n")
            for gate in (1, 2, 3, 4, 5, "final"):
                title = "Final" if gate == "final" else f"Gate {gate}"
                check = "x" if gate in approved else " "
                lines.append(f"## {title}\n- [{check}] Review complete")
                if gate in approved:
                    lines.append("承認者: Test Approver\n")
                else:
                    lines.append("承認者: ___________\n")

        (feature_dir / "APPROVAL.md").write_text("\n".join(lines), encoding="utf-8")

    def _apply_mutation(self, feature_dir: Path, mutation: str) -> None:
        """Apply a destructive mutation for error testing."""
        if mutation == "missing_ac":
            spec = feature_dir / "spec.md"
            if spec.exists():
                text = spec.read_text(encoding="utf-8")
                # Remove acceptance criteria from canonical YAML
                text = re.sub(r"acceptance:\n(\s+-.*\n)+", "acceptance: []\n", text)
                spec.write_text(text, encoding="utf-8")

        elif mutation == "broken_traceability":
            tasks = feature_dir / "tasks.md"
            if tasks.exists():
                text = tasks.read_text(encoding="utf-8")
                text = text.replace("spec_refs:", "spec_refs_BROKEN:")
                tasks.write_text(text, encoding="utf-8")

        elif mutation == "missing_nfr":
            spec = feature_dir / "spec.md"
            if spec.exists():
                text = spec.read_text(encoding="utf-8")
                text = re.sub(r"requirements:\n(\s+\w+:.*\n(\s+-.*\n)*)+", "requirements: {}\n", text)
                spec.write_text(text, encoding="utf-8")

        elif mutation == "missing_bpmn":
            bpmn = feature_dir / "process.bpmn"
            if bpmn.exists():
                bpmn.unlink()

        elif mutation == "phase_violation":
            # Create Phase 2 file when Phase 1 not approved
            if self._custom_gates is None:
                self._custom_gates = set()  # No gates approved
            self._write_approval(feature_dir)  # Rewrite with no gates
            # spec.md already exists (copied from sample) — this IS the violation
```

### conftest.py

```python
"""Shared fixtures for integration tests."""

import pytest
from tests.project_builder import ProjectBuilder


@pytest.fixture
def full_pass_project(tmp_path) -> Path:
    """Full Mode project with all gates approved. stride lint should PASS."""
    return (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-TEST", mode="full", phase=5, coverage_tier="standard")
        .done()
        .build()
    )


@pytest.fixture
def lite_pass_project(tmp_path) -> Path:
    """Lite Mode project with all gates approved."""
    return (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-LTEST", mode="lite", phase=4, coverage_tier="standard")
        .done()
        .build()
    )


@pytest.fixture
def design_phase_project(tmp_path) -> Path:
    """Full Mode, Phase 1 in progress (no gates approved)."""
    return (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-DTEST", mode="full", phase=1, coverage_tier="standard")
        .done()
        .build()
    )


@pytest.fixture
def specify_phase_project(tmp_path) -> Path:
    """Full Mode, Phase 2 in progress (Gate 1,2 approved)."""
    return (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-STEST", mode="full", phase=2, coverage_tier="standard")
        .done()
        .build()
    )


@pytest.fixture
def project_builder(tmp_path):
    """Return a fresh ProjectBuilder for custom test setups."""
    return ProjectBuilder(tmp_path)
```

---

## Step 3: `tests/test_stride_lint_integration.py`

**最優先:** `check_stride_lint()` 経由の回帰テスト（既知の実不具合を最初にカバー）

```python
"""Integration tests for stride-lint: import API + CLI smoke."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestCheckStrideLint:
    """Test the import path used by pr_readiness_checker.

    This is the highest-priority test: pr_readiness_checker.py:130 calls
    lint_feature(str(feature_dir), {}) with a bare dict instead of LintConfig.
    That causes 'dict' object has no attribute 'coverage_report' at stride_lint.py:1888.
    """

    def test_check_stride_lint_returns_pass_for_valid_feature(self, full_pass_project):
        """check_stride_lint() must return PASS (not WARN) for a valid project."""
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        from pr_readiness_checker import check_stride_lint
        result = check_stride_lint(full_pass_project)
        assert result["status"] in ("PASS", "FAIL"), (
            f"Expected PASS or FAIL but got '{result['status']}': {result.get('detail')}"
        )

    def test_check_stride_lint_not_warn_due_to_config_error(self, full_pass_project):
        """Regression: check_stride_lint must not WARN due to lint_feature(dir, {})."""
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        from pr_readiness_checker import check_stride_lint
        result = check_stride_lint(full_pass_project)
        if result["status"] == "WARN":
            detail = result.get("detail", "")
            assert "attribute" not in detail.lower(), (
                f"WARN caused by attribute error (likely dict vs LintConfig): {detail}"
            )


class TestLintFeatureImportAPI:
    """Test lint_feature() with correct LintConfig."""

    def test_lint_feature_with_lint_config(self, full_pass_project):
        """lint_feature() called with LintConfig returns LintResult with expected attrs."""
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        from stride_lint import LintConfig, LintResult, lint_feature
        config = LintConfig()
        result = lint_feature(str(full_pass_project / "specs" / "FEAT-TEST"), config)
        assert isinstance(result, LintResult)
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "coverage_report")

    def test_lint_feature_pass_no_errors(self, full_pass_project):
        """A fully approved feature should have zero non-APPROVAL errors."""
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
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
        from stride_lint import LintConfig, lint_feature
        result = lint_feature(str(project / "specs" / "FEAT-NOBPMN"), LintConfig())
        error_codes = [e["code"] for e in result.errors]
        assert any("MISSING" in c for c in error_codes)


class TestStrideLintCLI:
    """Smoke tests for stride-lint CLI via subprocess."""

    def test_stride_lint_cli_exit_code(self, full_pass_project):
        result = subprocess.run(
            ["sdd-templates/tools/stride-lint", "specs/FEAT-TEST/"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        # May have APPROVAL_PENDING but should not crash
        assert result.returncode in (0, 1), f"Unexpected exit {result.returncode}: {result.stderr}"

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
```

---

## Step 4: `tests/test_phase_gate_integration.py`

```python
"""Integration tests for phase_gate.py: Full Mode and Lite Mode."""

import sys
from pathlib import Path

import pytest


class TestPhaseGateFull:
    """Full Mode (Gates 1-5 + Final)."""

    def test_no_gates_approved_is_phase_0(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-PG", mode="full", phase=1)
            .with_approval(set())
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        from phase_gate import get_approved_gates, get_current_phase
        gates, lite = get_approved_gates(project / "specs" / "FEAT-PG")
        assert lite is False
        phase = get_current_phase(gates, lite)
        assert phase == 0

    def test_gate_1_2_approved_is_phase_1(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-PG2", mode="full", phase=1)
            .with_approval({1, 2})
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        from phase_gate import get_approved_gates, get_current_phase
        gates, lite = get_approved_gates(project / "specs" / "FEAT-PG2")
        phase = get_current_phase(gates, lite)
        assert phase == 1

    def test_all_gates_approved_is_phase_4(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-PG3", mode="full", phase=5)
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        from phase_gate import get_approved_gates, get_current_phase
        gates, lite = get_approved_gates(project / "specs" / "FEAT-PG3")
        phase = get_current_phase(gates, lite)
        assert phase == 4  # All phases complete


class TestPhaseGateLite:
    """Lite Mode (Gates A, B, C)."""

    def test_lite_mode_detected(self, lite_pass_project):
        sys.path.insert(0, str(lite_pass_project / "sdd-templates" / "tools"))
        from phase_gate import get_approved_gates
        _, lite = get_approved_gates(lite_pass_project / "specs" / "FEAT-LTEST")
        assert lite is True

    def test_gate_a_approved_is_phase_1(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-LPG", mode="lite", phase=2)
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        from phase_gate import get_approved_gates, get_current_phase
        gates, lite = get_approved_gates(project / "specs" / "FEAT-LPG")
        assert lite is True
        phase = get_current_phase(gates, lite)
        assert phase == 1
```

---

## Step 5: `tests/test_auto_continue_integration.py`

```python
"""Integration tests for auto_continue_runner.py with real feature fixtures."""

import sys
from pathlib import Path

import pytest


class TestAutoContinnueFull:
    """Full Mode phase transitions."""

    def test_no_approval_targets_phase_1(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-AC1", mode="full", phase=1)
            .with_approval(set())
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        from auto_continue_runner import build_plan
        plan = build_plan(project / "specs" / "FEAT-AC1")
        assert plan["target_phase"] == 1
        assert plan["target_phase_name"] == "Design"
        # Verify evaluate step is included
        step_commands = [s["command"] for s in plan["steps"] if s["command"]]
        assert any("stride evaluate" in c for c in step_commands)

    def test_gate_1_2_approved_targets_phase_2(self, specify_phase_project):
        sys.path.insert(0, str(specify_phase_project / "sdd-templates" / "tools"))
        from auto_continue_runner import build_plan
        plan = build_plan(specify_phase_project / "specs" / "FEAT-STEST")
        assert plan["target_phase"] == 2
        assert plan["target_phase_name"] == "Specify"

    def test_all_approved_is_complete(self, full_pass_project):
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        from auto_continue_runner import build_plan
        plan = build_plan(full_pass_project / "specs" / "FEAT-TEST")
        assert plan["complete"] is True


class TestAutoContinnueLite:
    """Lite Mode phase transitions."""

    def test_lite_no_approval_targets_phase_1(self, project_builder):
        project = (
            project_builder
            .add_feature("FEAT-LAC", mode="lite", phase=1)
            .with_approval(set())
            .done()
            .build()
        )
        sys.path.insert(0, str(project / "sdd-templates" / "tools"))
        from auto_continue_runner import build_plan
        plan = build_plan(project / "specs" / "FEAT-LAC")
        assert plan["lite_mode"] is True
        assert plan["target_phase"] == 1
```

---

## Step 6: `tests/test_pr_readiness_integration.py`

```python
"""Integration tests for pr_readiness_checker.py with real project fixtures."""

import subprocess
import sys
from pathlib import Path

import pytest


class TestPRReadinessImport:
    """Import API tests for pr_readiness_checker."""

    def test_check_stride_lint_valid_project(self, full_pass_project):
        """The 7-check pipeline should not crash on a valid project."""
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        from pr_readiness_checker import check_stride_lint
        result = check_stride_lint(full_pass_project)
        assert result["status"] in ("PASS", "FAIL", "WARN")
        # If WARN, it must NOT be due to attribute error
        if result["status"] == "WARN":
            assert "attribute" not in result.get("detail", "").lower()

    def test_check_spec_drift_valid_project(self, full_pass_project):
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        from pr_readiness_checker import check_spec_drift
        result = check_spec_drift(full_pass_project)
        assert result["status"] in ("PASS", "FAIL", "WARN", "SKIP")


class TestPRReadinessCLI:
    """CLI smoke tests for stride pr-check."""

    def test_stride_pr_check_does_not_crash(self, full_pass_project):
        result = subprocess.run(
            ["sdd-templates/bin/stride", "pr-check", str(full_pass_project)],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        # Should not crash with unhandled exception
        assert "Traceback" not in result.stderr
```

---

## Step 7: `tests/test_stride_cli_integration.py`

```python
"""Integration tests for stride CLI subcommands via subprocess."""

import subprocess
from pathlib import Path

import pytest


class TestStrideHelp:
    def test_stride_help_exit_zero(self, full_pass_project):
        result = subprocess.run(
            ["sdd-templates/bin/stride", "help"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "stride" in result.stdout.lower()


class TestStridePhaseStatus:
    def test_phase_status_shows_gates(self, full_pass_project):
        result = subprocess.run(
            ["sdd-templates/bin/stride", "phase-status", "specs/FEAT-TEST/"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 0


class TestStrideAutoContinnue:
    def test_auto_continue_shows_plan(self, design_phase_project):
        result = subprocess.run(
            ["sdd-templates/bin/stride", "auto-continue", "specs/FEAT-DTEST/"],
            cwd=str(design_phase_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Design" in result.stdout or "HITL" in result.stdout


class TestStrideEvaluate:
    def test_evaluate_config_error_without_api_keys(self, full_pass_project, monkeypatch):
        """stride evaluate should exit 2 when API keys are not configured."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        result = subprocess.run(
            ["sdd-templates/bin/stride", "evaluate", "specs/FEAT-TEST/", "--phase", "design"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
            env={**dict(__import__("os").environ), "OPENAI_API_KEY": "", "OPENAI_MODEL": ""},
        )
        assert result.returncode == 2

    def test_evaluate_rejects_lite_mode_flag(self, full_pass_project):
        result = subprocess.run(
            ["sdd-templates/bin/stride", "evaluate", "specs/FEAT-TEST/", "--lite-mode"],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "not yet supported" in result.stderr.lower() or "not yet supported" in result.stdout.lower()
```

---

## Step 8: 検証チェックリスト

```
□ pyproject.toml に testpaths = ["symphony/tests", "tests"] と markers が追加されている
□ tests/project_builder.py が存在し、ProjectBuilder + FeatureBuilder が動作する
□ tests/conftest.py が存在し、full_pass_project 等の fixture が提供される
□ test_stride_lint_integration.py:
  □ check_stride_lint(full_pass_project) が WARN でないことを検証する（既知の実不具合検出）
  □ lint_feature() を LintConfig で呼んで LintResult が返ることを検証する
  □ CLI smoke (stride-lint, stride lint) が crash しないことを検証する
□ test_phase_gate_integration.py:
  □ Full Mode: 4パターン（no gate, gate 1-2, gate 1-5, all gates）
  □ Lite Mode: auto-detect + gate progression
□ test_auto_continue_integration.py:
  □ Full Mode: 3パターン（no approval → phase 1, gate 1-2 → phase 2, all → complete）
  □ Lite Mode: 1パターン
  □ evaluate ステップが plan に含まれることの検証
□ test_pr_readiness_integration.py:
  □ check_stride_lint() が attribute error で WARN にならないこと
  □ check_spec_drift() が crash しないこと
  □ stride pr-check CLI が Traceback を出さないこと
□ test_stride_cli_integration.py:
  □ stride help, phase-status, auto-continue, evaluate の4コマンド
  □ evaluate --lite-mode が拒否されること
□ 既存テスト（symphony/tests/）が引き続き全件 PASS すること
□ repo 直下のファイルが一切変更されていないこと（テストは全て tmp_path 内）
```

---

## 完了したら

```bash
# 全テスト実行
python3 -m pytest tests/ -v
python3 -m pytest symphony/tests/ -v

# 既存の self-test も確認
python3 sdd-templates/tools/auto_continue_runner.py --test

# OpenClaw に完了通知
openclaw system event --text "Done: STRIDE 統合テストフレームワーク Phase 1 実装完了（ProjectBuilder + 4テストファイル + 既知不具合の回帰テスト）" --mode now
```

---

## 制約・注意事項

- **repo 直下のファイルを変更してはならない**（テストは全て `tmp_path` 内）
- **`sdd-templates/tools/` のソースコードは変更してはならない**（テストフレームワークのみ追加）
  - ただし `pr_readiness_checker.py:130` の `{}` → `LintConfig()` 修正は、テストで不具合を検出した後に別途修正してよい
- **`symphony/tests/` の既存テストに影響を与えてはならない**
- **静的 fixture（golden/）は Phase 2 で追加する。** Phase 1 では ProjectBuilder の動的生成のみ使う
- **symlink と copy の使い分けを守ること:**
  - symlink 可: `tools/`, `templates/`, `hooks/`, `bin/`, `specs/`（sdd-templates 内の sample）
  - copy 必須: `config/`, `memory/`, `shared/`
