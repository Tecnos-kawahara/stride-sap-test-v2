"""Tests for symphony.parallel."""
from __future__ import annotations

import time
import threading
from unittest.mock import MagicMock

import pytest

from symphony.models import RunResult
from symphony.parallel import run_parallel


def _make_run_result(issue_id: int = 1, status: str = "success") -> RunResult:
    return RunResult(
        issue_id=issue_id, phase="execute", attempt=1,
        started_at=0.0, ended_at=1.0, status=status,
    )


def _dummy_runner(*args, **kwargs) -> RunResult:
    """A simple runner that returns success."""
    return _make_run_result(issue_id=args[0] if args else 1)


class TestRunParallel:
    def test_single_task(self):
        tasks = {
            "WI-001": (_dummy_runner, (1,), {}),
        }
        results = run_parallel(tasks, max_concurrent=2)
        assert "WI-001" in results
        assert results["WI-001"].status == "success"

    def test_results_collected_per_wi(self):
        tasks = {
            "WI-001": (_dummy_runner, (10,), {}),
            "WI-002": (_dummy_runner, (20,), {}),
            "WI-003": (_dummy_runner, (30,), {}),
        }
        results = run_parallel(tasks, max_concurrent=4)
        assert len(results) == 3
        assert "WI-001" in results
        assert "WI-002" in results
        assert "WI-003" in results
        assert results["WI-001"].issue_id == 10
        assert results["WI-002"].issue_id == 20
        assert results["WI-003"].issue_id == 30

    def test_max_concurrent_semaphore_limits_concurrency(self):
        """Verify that max_concurrent limits the number of concurrent tasks."""
        max_concurrent = 2
        concurrent_count = {"current": 0, "peak": 0}
        lock = threading.Lock()

        def slow_runner(issue_id: int) -> RunResult:
            with lock:
                concurrent_count["current"] += 1
                if concurrent_count["current"] > concurrent_count["peak"]:
                    concurrent_count["peak"] = concurrent_count["current"]
            time.sleep(0.1)
            with lock:
                concurrent_count["current"] -= 1
            return _make_run_result(issue_id=issue_id)

        tasks = {
            f"WI-{i:03d}": (slow_runner, (i,), {})
            for i in range(5)
        }
        results = run_parallel(tasks, max_concurrent=max_concurrent)

        assert len(results) == 5
        assert concurrent_count["peak"] <= max_concurrent

    def test_shared_runner_fn(self):
        """Test the runner_fn shorthand form."""
        tasks = {
            "WI-001": ((10,), {}),
            "WI-002": ((20,), {}),
        }
        results = run_parallel(tasks, max_concurrent=2, runner_fn=_dummy_runner)
        assert len(results) == 2
        assert results["WI-001"].issue_id == 10
        assert results["WI-002"].issue_id == 20

    def test_exception_returns_error_result_instead_of_dropping(self):
        """If a runner_fn raises, run_parallel must return an error result, not drop it."""
        def crashing_runner(issue_id: int) -> RunResult:
            raise RuntimeError(f"Agent crash for #{issue_id}")

        tasks = {
            "42": (crashing_runner, (42,), {}),
            "43": (_dummy_runner, (43,), {}),
        }
        results = run_parallel(tasks, max_concurrent=2)

        # Both tasks must have results — no dropped entries
        assert len(results) == 2
        assert results["42"].status == "error"
        assert "crash" in results["42"].error.lower()
        assert results["43"].status == "success"
