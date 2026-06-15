"""Shared fixtures for integration tests."""

from pathlib import Path

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


# --- Phase 2: Enterprise / ERP / Dependency / Amendment fixtures ---


@pytest.fixture
def enterprise_project(tmp_path) -> Path:
    """Enterprise project with epic + feature linked via epic_ref/team_id."""
    return (
        ProjectBuilder(tmp_path)
        .enable_enterprise()
        .add_epic("EPIC-TEST", feature_ids=["FEAT-ETEST"])
        .with_features("FEAT-ETEST")
        .with_approval({"E1", "E2"})
        .done()
        .add_feature("FEAT-ETEST", mode="full", phase=5, coverage_tier="critical")
        .with_enterprise("EPIC-TEST", "TEAM-SLS")
        .done()
        .build()
    )


@pytest.fixture
def enterprise_project_with_cycle(tmp_path) -> Path:
    """Enterprise project with two features that have circular dependencies."""
    return (
        ProjectBuilder(tmp_path)
        .enable_enterprise()
        .add_epic("EPIC-CYCLE", feature_ids=["FEAT-CYC1", "FEAT-CYC2"])
        .with_features("FEAT-CYC1", "FEAT-CYC2")
        .with_approval({"E1", "E2"})
        .done()
        .add_feature("FEAT-CYC1", mode="full", phase=5, coverage_tier="standard")
        .with_enterprise("EPIC-CYCLE", "TEAM-AAA")
        .with_dependency_manifest([
            {"owner_feature": "FEAT-CYC2", "dependency_type": "data", "criticality": "high"},
        ])
        .done()
        .add_feature("FEAT-CYC2", mode="full", phase=5, coverage_tier="standard")
        .with_enterprise("EPIC-CYCLE", "TEAM-BBB")
        .with_dependency_manifest([
            {"owner_feature": "FEAT-CYC1", "dependency_type": "api", "criticality": "high"},
        ])
        .done()
        .build()
    )


@pytest.fixture
def erp_addon_project(tmp_path) -> Path:
    """Full-mode project with ERP Addon active (all gates approved)."""
    return (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-ERP", mode="full", phase=5, coverage_tier="critical")
        .with_erp_addon()
        .done()
        .build()
    )


@pytest.fixture
def erp_addon_project_invalid_mode(tmp_path) -> Path:
    """ERP project where WI mode is too low for its risk flags."""
    project = (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-ERPBAD", mode="full", phase=5, coverage_tier="critical")
        .with_erp_addon()
        .done()
        .build()
    )
    feature_dir = project / "specs" / "FEAT-ERPBAD"
    # Ensure state.yaml exists (validator requires it after Gate 5)
    state_dir = feature_dir / "state"
    state_dir.mkdir(exist_ok=True)
    src_state = Path(__file__).resolve().parent.parent / "specs" / "FEAT-ERPSAMPLE" / "state" / "state.yaml"
    if src_state.exists():
        import shutil
        dst = state_dir / "state.yaml"
        if not dst.exists():
            shutil.copy2(src_state, dst)
            text = dst.read_text(encoding="utf-8")
            text = text.replace("FEAT-ERPSAMPLE", "FEAT-ERPBAD")
            text = text.replace("ERP-SAMPLE", "ERPBAD")
            dst.write_text(text, encoding="utf-8")

    # Mutate the WI to have a mode mismatch: autopilot with authz risk flag
    wi_dir = feature_dir / "work_items"
    for wi_file in wi_dir.glob("WI-*.md"):
        if wi_file.name.endswith(".approval.md"):
            continue
        text = wi_file.read_text(encoding="utf-8")
        text = text.replace("risk_flags: [ui_only]", "risk_flags: [authz, sod]")
        wi_file.write_text(text, encoding="utf-8")
        break  # Only mutate the first WI
    return project


@pytest.fixture
def amendment_project(tmp_path) -> Path:
    """Project with run artifacts for amendment analysis."""
    return (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-AMD", mode="full", phase=5, coverage_tier="standard")
        .with_erp_addon()
        .with_amendment_artifacts()
        .done()
        .build()
    )


# --- Phase 3: CLI / Analysis / Governance / Run Lifecycle fixtures ---

from tests.project_builder import (
    add_brownfield_indicators,
    add_spec_drift_artifacts,
    add_adr_artifacts,
    add_hooks_settings,
    add_run_lifecycle,
    add_coverage_summary,
    add_junit_xml,
    add_turbo_cache,
    add_testreport_artifacts,
    add_state_yaml,
    add_pm_dashboard,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def brownfield_project(tmp_path) -> Path:
    """Node.js brownfield project for brownfield_detector tests."""
    root = ProjectBuilder(tmp_path).build()
    add_brownfield_indicators(root, lang="node", monorepo=False)
    return root


@pytest.fixture
def spec_drift_project(tmp_path) -> Path:
    """Project with contracts and routes for spec_drift_detector tests."""
    root = ProjectBuilder(tmp_path).add_feature("FEAT-DRIFT", mode="full", phase=5).done().build()
    add_spec_drift_artifacts(root, missing_impl=True, extra_impl=True)
    return root


@pytest.fixture
def adr_project(tmp_path) -> Path:
    """Project with ADR files for decision_index tests."""
    root = ProjectBuilder(tmp_path).build()
    add_adr_artifacts(root, count=3)
    return root


@pytest.fixture
def hooks_project(tmp_path) -> Path:
    """Project with .claude/ dir for setup_hooks tests."""
    root = ProjectBuilder(tmp_path).build()
    add_hooks_settings(root, state="missing")
    return root


@pytest.fixture
def wi_ready_project(tmp_path) -> Path:
    """Feature with full ops pack and state for WI readiness checks."""
    root = (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-ERPSAMPLE", mode="full", phase=5, coverage_tier="critical")
        .with_erp_addon()
        .done()
        .build()
    )
    # Copy state.yaml from real sample
    import shutil
    feature_dir = root / "specs" / "FEAT-ERPSAMPLE"
    real_state = _REPO_ROOT / "specs" / "FEAT-ERPSAMPLE" / "state" / "state.yaml"
    state_dir = feature_dir / "state"
    state_dir.mkdir(exist_ok=True)
    if real_state.exists():
        shutil.copy2(real_state, state_dir / "state.yaml")
    return root


@pytest.fixture
def interrupted_run_project(tmp_path) -> Path:
    """Feature with partially completed run for run_resume_detector tests."""
    root = (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-RUN", mode="full", phase=5)
        .done()
        .build()
    )
    feature_dir = root / "specs" / "FEAT-RUN"
    add_run_lifecycle(feature_dir, "WI-RUN-001", "RUN-20260301-1000",
                      artifacts=["findings", "plan", "decision_log"])
    return root


@pytest.fixture
def run_report_project(tmp_path) -> Path:
    """Feature with complete run for run_report_generator tests."""
    root = (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-RPT", mode="full", phase=5)
        .done()
        .build()
    )
    feature_dir = root / "specs" / "FEAT-RPT"
    add_run_lifecycle(feature_dir, "WI-RPT-001", "RUN-20260301-1000",
                      artifacts=["findings", "plan", "decision_log", "test_results", "walkthrough"])
    return root


@pytest.fixture
def planning_bridge_project(tmp_path) -> Path:
    """Feature with WI/run structure for sdd_planning_bridge tests."""
    root = (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-PBR", mode="full", phase=5)
        .with_erp_addon()
        .done()
        .build()
    )
    feature_dir = root / "specs" / "FEAT-PBR"
    add_run_lifecycle(feature_dir, "WI-PBR-001", "RUN-20260301-1000",
                      artifacts=["findings", "plan"])
    return root


@pytest.fixture
def wi_sync_project(tmp_path) -> Path:
    """Minimal project for stride_wi_sync tests."""
    root = (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-SYNC", mode="full", phase=5)
        .done()
        .build()
    )
    return root


# --- Phase 4: Evidence / Process Metrics / Testreport fixtures ---


@pytest.fixture
def evidence_project(tmp_path) -> Path:
    """Project with coverage, test results, gate approvals, and turbo cache."""
    root = (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-EVI", mode="full", phase=5, coverage_tier="critical")
        .with_approval_dates({
            1: "2026-01-10", 2: "2026-01-12", 3: "2026-01-20",
            4: "2026-01-25", 5: "2026-02-01", "final": "2026-02-10",
        })
        .done()
        .build()
    )
    add_coverage_summary(root, line_pct=85.0, branch_pct=70.0, func_pct=90.0)
    add_junit_xml(root, total=20, failures=2, errors=0, skipped=1, time_sec=5.3)
    add_turbo_cache(root, total=10, cached=7)
    return root


@pytest.fixture
def process_metrics_project(tmp_path) -> Path:
    """Project with approval dates, WI state, tasks.md canonical YAML, and epic dashboard."""
    root = (
        ProjectBuilder(tmp_path)
        .enable_enterprise()
        .add_epic("EPIC-PM")
        .with_features("FEAT-PM")
        .with_approval({"E1", "E2"})
        .done()
        .add_feature("FEAT-PM", mode="full", phase=5, coverage_tier="standard")
        .with_enterprise("EPIC-PM", "TEAM-DEV")
        .with_approval_dates({
            1: "2026-01-10", 2: "2026-01-12", 3: "2026-01-20",
            4: "2026-01-25", 5: "2026-02-01",
        })
        .done()
        .build()
    )
    feature_dir = root / "specs" / "FEAT-PM"

    # state/state.yaml with work_items and epic_ref
    add_state_yaml(feature_dir, epic_ref="EPIC-PM", work_items=[
        {"wi_id": "WI-PM-001", "status": "done", "complexity": "medium"},
        {"wi_id": "WI-PM-002", "status": "in_progress", "complexity": "high"},
    ])

    # tasks.md with Canonical YAML (tasks_gate_check + tasks.tasks)
    (feature_dir / "tasks.md").write_text(
        "# Tasks\n\n"
        "# 1. Canonical Tasks (YAML)\n"
        "```yaml\n"
        "tasks_gate_check:\n"
        "  counts:\n"
        "    tasks: 5\n"
        "tasks:\n"
        "  tasks:\n"
        "    - id: T-PM-001\n"
        "      spec_refs: [AC-US-FEATPM-001-01]\n"
        "    - id: T-PM-002\n"
        "      spec_refs: [AC-US-FEATPM-001-02]\n"
        "    - id: T-PM-003\n"
        "      spec_refs: [AC-US-FEATPM-002-01]\n"
        "    - id: T-PM-004\n"
        "      spec_refs: []\n"
        "    - id: T-PM-005\n"
        "      spec_refs: []\n"
        "    - id: T-PM-006\n"
        "      spec_refs: []\n"
        "```\n",
        encoding="utf-8",
    )

    # PM_DASHBOARD.md in epic dir
    add_pm_dashboard(root / "epics" / "EPIC-PM")

    return root


@pytest.fixture
def testreport_project(tmp_path) -> Path:
    """Feature with testreport/cases.json + stride_mapping.yaml."""
    root = (
        ProjectBuilder(tmp_path)
        .add_feature("FEAT-TR", mode="full", phase=5)
        .done()
        .build()
    )
    feature_dir = root / "specs" / "FEAT-TR"
    add_testreport_artifacts(
        feature_dir,
        cases=[
            {"id": "01_login", "name": "Login flow", "status": "passed"},
            {"id": "02_order", "name": "Order creation", "status": "passed"},
            {"id": "03_unmapped", "name": "Unmapped test", "status": "passed"},
        ],
        mapping=[
            {"case_id": "01_login", "stride_refs": ["AC-US-FEATTEST-001-01"]},
            {"case_id": "02_order", "stride_refs": ["AC-US-FEATTEST-001-02", "AC-US-FEATTEST-002-01"]},
        ],
        report_html=True,
    )
    return root


@pytest.fixture
def bootstrap_project_root(tmp_path) -> Path:
    """Isolated root for CLI bootstrap E2E tests (stride init, intake, etc.)."""
    root = ProjectBuilder(tmp_path).enable_enterprise().build()
    add_brownfield_indicators(root, lang="node")
    return root
