"""Tests for mutation_check() in pr_readiness_checker.py (v5.1 harness marker)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))
from pr_readiness_checker import mutation_check, run_all_checks, format_human_readable, STATUS_PASS, STATUS_WARN, STATUS_FAIL


pytestmark = pytest.mark.harness


# ---------------------------------------------------------------------------
# mutation_check unit tests
# ---------------------------------------------------------------------------

def test_mutation_no_cosmic_ray():
    """When cosmic-ray is not installed, mutation_check returns WARN."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        with mock.patch("shutil.which", return_value=None):
            r = mutation_check(p)
    assert r["status"] == STATUS_WARN
    assert "cosmic-ray" in r["detail"].lower()


def test_mutation_no_tools_dir():
    """When sdd-templates/tools/ is absent, mutation_check returns WARN."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        with mock.patch("shutil.which", return_value="/usr/bin/cosmic-ray"):
            r = mutation_check(p)
    assert r["status"] == STATUS_WARN
    assert "not found" in r["detail"].lower() or "absent" in r["detail"].lower() or r["status"] == STATUS_WARN


def test_mutation_threshold_from_env():
    """MUTATION_THRESHOLD env var controls default threshold."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        with mock.patch.dict(os.environ, {"MUTATION_THRESHOLD": "90"}):
            with mock.patch("shutil.which", return_value=None):
                r = mutation_check(p)
    assert r["threshold"] == 90


def test_mutation_threshold_explicit():
    """Explicit threshold parameter overrides env var."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        with mock.patch("shutil.which", return_value=None):
            r = mutation_check(p, threshold=75)
    assert r["threshold"] == 75


def test_mutation_subprocess_timeout():
    """Subprocess timeout produces WARN status."""
    import subprocess
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        tools = p / "sdd-templates" / "tools"
        tools.mkdir(parents=True)
        with mock.patch("shutil.which", return_value="/usr/bin/cosmic-ray"):
            with mock.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cosmic-ray", 300)):
                r = mutation_check(p)
    assert r["status"] == STATUS_WARN
    assert "timed out" in r["detail"].lower()


def test_run_all_checks_without_mutation():
    """run_all_checks by default does NOT include mutation check."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        result = run_all_checks(p)
    check_names = [c["name"] for c in result["checks"]]
    assert "mutation testing" not in check_names
    assert len(result["checks"]) == 7


def test_run_all_checks_with_mutation():
    """run_all_checks with include_mutation=True includes mutation check."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        with mock.patch("shutil.which", return_value=None):
            result = run_all_checks(p, include_mutation=True)
    check_names = [c["name"] for c in result["checks"]]
    assert "mutation testing" in check_names
    assert len(result["checks"]) == 8


def test_format_human_readable_dynamic_total_7():
    """format_human_readable uses [idx/7] when 7 checks."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        result = run_all_checks(p)
    output = format_human_readable(result)
    assert "[1/7]" in output
    assert "[7/7]" in output
    assert "[1/8]" not in output


def test_format_human_readable_dynamic_total_8():
    """format_human_readable uses [idx/8] when 8 checks (with mutation)."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        with mock.patch("shutil.which", return_value=None):
            result = run_all_checks(p, include_mutation=True)
    output = format_human_readable(result)
    assert "[8/8]" in output
    assert "[7/8]" in output


def test_mutation_check_pass_high_kill_rate():
    """mutation_check returns PASS when kill_rate >= threshold."""
    import subprocess

    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        tools = p / "sdd-templates" / "tools"
        tools.mkdir(parents=True)

        def fake_run(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            cmd_str = " ".join(str(c) for c in cmd)
            result = mock.MagicMock()
            result.returncode = 0
            if "init" in cmd_str:
                result.stdout = ""
                result.stderr = ""
            elif "exec" in cmd_str:
                result.stdout = ""
                result.stderr = ""
            elif "cr-report" in cmd_str:
                result.stdout = "kill rate: 85.0%\n"
                result.stderr = ""
            else:
                result.stdout = ""
                result.stderr = ""
            return result

        with mock.patch("shutil.which", return_value="/usr/bin/cosmic-ray"):
            with mock.patch("subprocess.run", side_effect=fake_run):
                r = mutation_check(p, threshold=80)

    assert r["status"] == STATUS_PASS
    assert r["kill_rate"] == 85.0
