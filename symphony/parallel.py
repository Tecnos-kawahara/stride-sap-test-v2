"""Parallel execution of Phase-4 Work Items using asyncio."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from symphony.models import RunResult
from symphony.logger import get_logger

logger = get_logger(__name__)


async def _run_with_semaphore(
    sem: asyncio.Semaphore,
    executor: ThreadPoolExecutor,
    task_id: str,
    runner_fn: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> tuple[str, Any]:
    """Acquire semaphore, run *runner_fn* in a thread, release semaphore.

    If *runner_fn* raises, the exception is caught and returned as a
    sentinel RunResult with status="error" so the caller always receives
    a result for every task.
    """
    async with sem:
        logger.info("Semaphore acquired for task %s", task_id)
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                executor,
                lambda: runner_fn(*args, **kwargs),
            )
        except Exception as exc:
            logger.error("Task %s raised: %s", task_id, exc)
            import time as _time
            result = RunResult(
                issue_id=int(task_id) if task_id.isdigit() else 0,
                phase="unknown",
                attempt=1,
                started_at=_time.time(),
                ended_at=_time.time(),
                status="error",
                error=str(exc),
            )
        else:
            if hasattr(result, "status"):
                logger.info("Task %s completed with status=%s", task_id, result.status)
        return (task_id, result)


async def _gather_parallel(
    tasks: dict[str, tuple[Callable[..., Any], tuple, dict]],
    max_concurrent: int,
) -> dict[str, Any]:
    """Internal async implementation.

    Args:
        tasks: mapping from task_id to (runner_fn, args, kwargs)
        max_concurrent: maximum number of concurrent agent runs

    Returns:
        dict mapping task_id to its result (RunResult or whatever runner_fn returns).
        Every submitted task is guaranteed to have an entry — exceptions inside
        runner_fn are caught by ``_run_with_semaphore`` and converted to a
        sentinel RunResult with ``status="error"``.
    """
    sem = asyncio.Semaphore(max_concurrent)
    executor = ThreadPoolExecutor(max_workers=max_concurrent)
    results: dict[str, Any] = {}

    try:
        coros = [
            _run_with_semaphore(sem, executor, tid, fn, *args, **kwargs)
            for tid, (fn, args, kwargs) in tasks.items()
        ]
        gathered = await asyncio.gather(*coros, return_exceptions=True)

        for item in gathered:
            if isinstance(item, Exception):
                # Should not happen since _run_with_semaphore catches,
                # but guard against asyncio-level failures
                logger.error("Parallel gather-level exception: %s", item)
                continue
            task_id, run_result = item
            results[task_id] = run_result
    finally:
        executor.shutdown(wait=False)

    return results


def run_parallel(
    tasks: dict[str, tuple[Callable[..., RunResult], tuple, dict]],
    max_concurrent: int,
    runner_fn: Callable[..., RunResult] | None = None,
) -> dict[str, RunResult]:
    """Execute multiple agent tasks in parallel with bounded concurrency.

    Args:
        tasks: mapping of task_id → (callable, args_tuple, kwargs_dict).
               If runner_fn is provided, tasks should be
               task_id → (args_tuple, kwargs_dict) and runner_fn is used
               for all tasks.
        max_concurrent: max simultaneous agent runs
        runner_fn: optional shared runner function for all tasks.
                   If provided, task values are treated as (args, kwargs).

    Returns:
        dict mapping task_id to RunResult
    """
    if runner_fn is not None:
        # Normalize: wrap the shared runner_fn into each task entry
        normalized: dict[str, tuple[Callable[..., RunResult], tuple, dict]] = {}
        for tid, value in tasks.items():
            if isinstance(value, tuple) and len(value) == 2:
                args, kwargs = value
                normalized[tid] = (runner_fn, args, kwargs)
            else:
                # Already in full form
                normalized[tid] = value  # type: ignore[assignment]
        tasks = normalized

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        # We are inside an existing event loop — use nest_asyncio or thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, _gather_parallel(tasks, max_concurrent))
            return future.result()
    else:
        return asyncio.run(_gather_parallel(tasks, max_concurrent))
