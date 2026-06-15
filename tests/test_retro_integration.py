"""Integration tests for stride_retro.py with real project fixtures."""

import json
import sys
from pathlib import Path

import pytest

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tools_path():
    """Path to sdd-templates/tools/."""
    return Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"


@pytest.fixture
def _import_retro(tools_path):
    """Import stride_retro module."""
    sys.path.insert(0, str(tools_path))
    try:
        import stride_retro
        yield stride_retro
    finally:
        sys.path.pop(0)
        if "stride_retro" in sys.modules:
            del sys.modules["stride_retro"]


def _make_approval_md(feature_dir: Path, gates: dict, format_ja: bool = True):
    """Create APPROVAL.md with gate dates.

    gates: {"Gate 1": "2026-01-10", "Gate 3": "2026-01-15", ...}
    format_ja: True for '日付:', False for 'Date:'
    """
    lines = []
    for gate, date in gates.items():
        title = gate if gate.startswith("Gate") or gate == "Final" else f"Gate {gate}"
        lines.append(f"## {title}: Review")
        lines.append("- [x] Review complete")
        lines.append(f"承認者: Test Approver")
        date_label = "日付" if format_ja else "Date"
        lines.append(f"{date_label}: {date}")
        lines.append("")
    (feature_dir / "APPROVAL.md").write_text("\n".join(lines), encoding="utf-8")


def _make_state_yaml(feature_dir: Path, work_items: list):
    """Create state/state.yaml with work items."""
    state_dir = feature_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "state.yaml").write_text(
        yaml.dump({"work_items": work_items}, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


def _make_lessons_md(feature_dir: Path, wi_id: str, run_id: str, content: str):
    """Create a lessons.md file under runs/<wi_id>/<run_id>/.planning/."""
    lessons_dir = feature_dir / "runs" / wi_id / run_id / ".planning"
    lessons_dir.mkdir(parents=True, exist_ok=True)
    (lessons_dir / "lessons.md").write_text(content, encoding="utf-8")


def _make_spec_md(feature_dir: Path, spec_yaml: dict):
    """Create spec.md with canonical YAML block."""
    yaml_str = yaml.dump(spec_yaml, default_flow_style=False, allow_unicode=True)
    (feature_dir / "spec.md").write_text(
        f"# 0. Canonical Spec (YAML)\n```yaml\n{yaml_str}```\n",
        encoding="utf-8",
    )


def _make_scenarios_yaml(feature_dir: Path, scenarios: list):
    """Create tests/scenarios.yaml."""
    tests_dir = feature_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "scenarios.yaml").write_text(
        yaml.dump({"scenarios": scenarios}, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
class TestRetroIntegration:

    def test_approval_parsing_japanese_format(self, tmp_path, _import_retro):
        """Parse APPROVAL.md with '日付:' format."""
        mod = _import_retro
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)
        _make_approval_md(feature, {
            "Gate 1": "2026-03-01",
            "Gate 3": "2026-03-05",
            "Gate 5": "2026-03-08",
            "Final": "2026-03-15",
        }, format_ja=True)

        dates = mod._parse_approval_dates(feature / "APPROVAL.md")
        assert dates["Gate 1"] == "2026-03-01"
        assert dates["Gate 3"] == "2026-03-05"
        assert dates["Final"] == "2026-03-15"

        durations = mod._compute_phase_durations(dates)
        assert durations["design_to_specify"] == "4d"
        assert durations["total_lead_time"] == "14d"

    def test_wi_stats_from_state_yaml(self, tmp_path, _import_retro):
        """Correctly aggregate WI statistics from state.yaml."""
        mod = _import_retro
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)
        _make_state_yaml(feature, [
            {"wi_id": "WI-001", "status": "done", "mode": "autopilot"},
            {"wi_id": "WI-002", "status": "done", "mode": "autopilot"},
            {"wi_id": "WI-003", "status": "pending", "mode": "validate"},
            {"wi_id": "WI-004", "status": "blocked", "mode": "confirm"},
            {"wi_id": "WI-005", "status": "in_progress", "mode": "autopilot"},
        ])

        stats = mod._collect_wi_stats(feature)
        assert stats["total"] == 5
        assert stats["mode_breakdown"]["autopilot"] == 3
        assert stats["mode_breakdown"]["validate"] == 1
        assert stats["status_breakdown"]["done"] == 2
        assert stats["status_breakdown"]["blocked"] == 1

    def test_ac_coverage_from_scenarios_and_spec(self, tmp_path, _import_retro):
        """Calculate AC coverage from scenarios.yaml and spec.md."""
        mod = _import_retro
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)

        _make_spec_md(feature, {
            "spec": {
                "use_cases": [
                    {
                        "uc_id": "UC-001",
                        "acceptance": [
                            {"ac_id": "AC-001", "tags": []},
                            {"ac_id": "AC-002", "tags": []},
                            {"ac_id": "AC-003", "tags": []},
                        ],
                    },
                ],
            },
        })

        _make_scenarios_yaml(feature, [
            {"scenario_id": "S-001", "covers_ac": ["AC-001"]},
            {"scenario_id": "S-002", "covers_ac": ["AC-002"]},
        ])

        stats = mod._collect_test_stats(feature)
        assert stats["scenario_count"] == 2
        assert stats["ac_total"] == 3
        assert stats["ac_covered"] == 2
        assert stats["ac_coverage_pct"] == pytest.approx(66.7, abs=0.1)

    def test_lessons_counting(self, tmp_path, _import_retro):
        """Count lessons from .planning/lessons.md files."""
        mod = _import_retro
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)

        _make_lessons_md(feature, "WI-001", "RUN-20260301-1000",
            "## Best Practices\n- Always validate input\n- Use retry pattern\n\n"
            "## Troubles\n- API timeout issue\n\n"
            "## Technical Knowledge\n- mcframe uses correlation ID\n"
        )

        lessons = mod._collect_lessons(feature)
        assert lessons["total"] == 4
        assert lessons["categories"]["best_practice"] == 2
        assert lessons["categories"]["trouble"] == 1
        assert lessons["categories"]["technical"] == 1

    def test_epic_cross_feature_aggregation(self, tmp_path, _import_retro):
        """Epic retro aggregates across features from epic_design.md."""
        mod = _import_retro

        # Create epic
        epic_dir = tmp_path / "epics" / "EPIC-TEST"
        epic_dir.mkdir(parents=True)
        (epic_dir / "epic_design.md").write_text(
            "# 0. Canonical Epic Design (YAML)\n```yaml\nepic:\n  features:\n"
            "    - feature_id: FEAT-A\n    - feature_id: FEAT-B\n```\n"
        )

        # Create two features
        for fid in ("FEAT-A", "FEAT-B"):
            fdir = tmp_path / "specs" / fid
            fdir.mkdir(parents=True)
            _make_state_yaml(fdir, [
                {"wi_id": f"WI-{fid}-001", "status": "done", "mode": "autopilot"},
                {"wi_id": f"WI-{fid}-002", "status": "pending", "mode": "confirm"},
            ])
            _make_approval_md(fdir, {"Gate 1": "2026-03-01"})

        retro = mod.generate_epic_retro(epic_dir)
        assert retro["kind"] == "epic"
        assert retro["feature_count"] == 2
        assert retro["aggregate"]["total_wis"] == 4

    def test_json_output_structure(self, tmp_path, _import_retro):
        """JSON output has all required keys."""
        mod = _import_retro
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)

        _make_approval_md(feature, {"Gate 1": "2026-03-01"})
        _make_state_yaml(feature, [
            {"wi_id": "WI-001", "status": "done", "mode": "autopilot"},
        ])

        retro = mod.generate_feature_retro(feature)
        json_str = json.dumps(retro, ensure_ascii=False)
        parsed = json.loads(json_str)

        for key in ("target", "kind", "phase_durations", "wi_stats", "test_stats", "lessons", "insights"):
            assert key in parsed, f"missing key '{key}' in JSON output"

        assert parsed["kind"] == "feature"
        assert isinstance(parsed["wi_stats"]["total"], int)

    def test_per_wi_attempts_and_feature_insight(self, tmp_path, _import_retro):
        """per_wi_attempts tracks individual WI run counts and feature insight names the WI."""
        mod = _import_retro
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)

        _make_state_yaml(feature, [
            {"wi_id": "WI-001", "status": "done", "mode": "autopilot"},
            {"wi_id": "WI-002", "status": "done", "mode": "validate"},
        ])
        _make_approval_md(feature, {"Gate 1": "2026-03-01"})

        # WI-002 has 3 RUN dirs, WI-001 has 1
        for i in range(3):
            (feature / "runs" / "WI-002" / f"RUN-{i:03d}").mkdir(parents=True)
        (feature / "runs" / "WI-001" / "RUN-001").mkdir(parents=True)

        retro = mod.generate_feature_retro(feature)
        pwa = retro["wi_stats"]["per_wi_attempts"]

        # per_wi_attempts sorted descending — WI-002 first
        assert pwa[0]["wi_id"] == "WI-002"
        assert pwa[0]["attempts"] == 3
        assert pwa[0]["mode"] == "validate"

        assert retro["wi_stats"]["avg_attempts"] == 2.0  # 4 runs / 2 WIs

        # Feature-level insight must name the specific WI
        assert any("WI-002" in i and "3 attempts" in i for i in retro["insights"]), (
            f"Expected 'Highest retry WI: WI-002 (3 attempts, ...)' in {retro['insights']}"
        )
        # validate mode triggers recommendation
        assert any("validate" in i and "Recommendation" in i for i in retro["insights"])

    def test_epic_highest_retry_wi_insight(self, tmp_path, _import_retro):
        """Epic retro identifies the highest-retry WI across features."""
        mod = _import_retro

        epic_dir = tmp_path / "epics" / "EPIC-TEST"
        epic_dir.mkdir(parents=True)
        (epic_dir / "epic_design.md").write_text(
            "# 0. Canonical Epic Design (YAML)\n```yaml\nepic:\n  features:\n"
            "    - feature_id: FEAT-A\n    - feature_id: FEAT-B\n```\n"
        )

        # FEAT-A: WI-A-001 has 1 run
        fa = tmp_path / "specs" / "FEAT-A"
        fa.mkdir(parents=True)
        _make_state_yaml(fa, [{"wi_id": "WI-A-001", "status": "done", "mode": "autopilot"}])
        _make_approval_md(fa, {"Gate 1": "2026-03-01"})
        (fa / "runs" / "WI-A-001" / "RUN-001").mkdir(parents=True)

        # FEAT-B: WI-B-001 has 4 runs (the highest)
        fb = tmp_path / "specs" / "FEAT-B"
        fb.mkdir(parents=True)
        _make_state_yaml(fb, [{"wi_id": "WI-B-001", "status": "done", "mode": "validate"}])
        _make_approval_md(fb, {"Gate 1": "2026-03-01"})
        for i in range(4):
            (fb / "runs" / "WI-B-001" / f"RUN-{i:03d}").mkdir(parents=True)

        retro = mod.generate_epic_retro(epic_dir)
        epic_insights = retro.get("insights", [])

        assert any("WI-B-001" in i and "4 attempts" in i for i in epic_insights), (
            f"Expected 'Highest retry WI: WI-B-001 (4 attempts, ...)' in {epic_insights}"
        )
