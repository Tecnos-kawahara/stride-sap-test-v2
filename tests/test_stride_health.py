"""Tests for stride_health.py (v5.1 harness marker)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))
from stride_health import (
    detect_dead_code,
    detect_coverage_decay,
    compute_alert,
    run_health_check,
    _DEFAULT_COVERAGE_DECAY_THRESHOLD as COVERAGE_DECAY_THRESHOLD_PCT,
)


pytestmark = pytest.mark.harness


# ---------------------------------------------------------------------------
# dead code detection
# ---------------------------------------------------------------------------

def test_dead_code_no_tools_dir():
    with tempfile.TemporaryDirectory() as d:
        r = detect_dead_code(Path(d))
    assert r["count"] == 0
    assert "not found" in r["detail"].lower()


def test_dead_code_no_python_files():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        tools = p / "sdd-templates" / "tools"
        tools.mkdir(parents=True)
        r = detect_dead_code(p)
    assert r["count"] == 0


def test_dead_code_pylint_not_found():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        tools = p / "sdd-templates" / "tools"
        tools.mkdir(parents=True)
        (tools / "sample.py").write_text("x = 1\n")
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            r = detect_dead_code(p)
    assert r["count"] == 0
    assert "pylint not found" in r["detail"].lower()


def test_dead_code_pylint_timeout():
    import subprocess
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        tools = p / "sdd-templates" / "tools"
        tools.mkdir(parents=True)
        (tools / "sample.py").write_text("import os\n")
        with mock.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pylint", 60)):
            r = detect_dead_code(p)
    assert r["count"] == 0
    assert "timed out" in r["detail"].lower()


def test_dead_code_detected():
    """Fake pylint output with W0611 produces count > 0."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        tools = p / "sdd-templates" / "tools"
        tools.mkdir(parents=True)
        (tools / "sample.py").write_text("import os\nx = 1\n")

        fake_output = "sample.py:1:0: W0611(unused-import) Unused import os\n"
        fake_result = mock.MagicMock()
        fake_result.stdout = fake_output
        fake_result.stderr = ""
        fake_result.returncode = 4  # pylint returns non-zero when findings

        with mock.patch("subprocess.run", return_value=fake_result):
            r = detect_dead_code(p)
    assert r["count"] == 1
    assert "1 dead code" in r["detail"].lower()


# ---------------------------------------------------------------------------
# coverage decay detection
# ---------------------------------------------------------------------------

def test_coverage_no_file():
    with tempfile.TemporaryDirectory() as d:
        r = detect_coverage_decay(Path(d))
    assert r["current_pct"] is None
    assert "no coverage" in r["detail"].lower()


def test_coverage_baseline_created():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "coverage").mkdir()
        (p / "coverage" / "coverage-summary.json").write_text(
            json.dumps({"total": {"lines": {"pct": 82.0}}})
        )
        r = detect_coverage_decay(p)
    assert r["current_pct"] == 82.0
    assert "baseline established" in r["detail"].lower()


def test_coverage_decay_computed():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "coverage").mkdir()
        (p / "coverage" / "coverage-summary.json").write_text(
            json.dumps({"total": {"lines": {"pct": 70.0}}})
        )
        (p / ".coverage_baseline").write_text("82.0\n")
        r = detect_coverage_decay(p)
    assert r["decay_pct"] == 12.0


def test_coverage_stable_no_alert():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "coverage").mkdir()
        (p / "coverage" / "coverage-summary.json").write_text(
            json.dumps({"total": {"lines": {"pct": 85.0}}})
        )
        (p / ".coverage_baseline").write_text("84.0\n")
        r = detect_coverage_decay(p)
    assert compute_alert({"count": 0}, r) is False


# ---------------------------------------------------------------------------
# alert and health check
# ---------------------------------------------------------------------------

def test_compute_alert_dead_code():
    assert compute_alert({"count": 3}, {"decay_pct": 0.0}) is True


def test_compute_alert_decay_above_threshold():
    # Default threshold is 5.0
    assert compute_alert({"count": 0}, {"decay_pct": 6.0}) is True


def test_compute_alert_ok():
    assert compute_alert({"count": 0}, {"decay_pct": 1.0}) is False


def test_run_health_check_no_runtime():
    with tempfile.TemporaryDirectory() as d:
        r = run_health_check(Path(d), runtime=False)
    assert r["alert"] is False
    assert "note" in r["sensors"]


def test_run_health_check_runtime_empty_project():
    """Empty project: dead_code returns 0 (no files), coverage_decay returns None."""
    with tempfile.TemporaryDirectory() as d:
        r = run_health_check(Path(d), runtime=True)
    # No dead code + no coverage file -> alert stays False
    assert r["alert"] is False
    assert "dead_code" in r["sensors"]
    assert "coverage_decay" in r["sensors"]
