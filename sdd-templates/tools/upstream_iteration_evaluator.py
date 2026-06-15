#!/usr/bin/env python3
"""upstream_iteration_evaluator — 3-iteration progress judge.

Reads shared/policies/upstream_iteration_policy.yaml and determines how far the
Phase 0 / 0.3 / 0.5 artifacts have progressed through the bootstrap → structure →
refinement iteration pattern.

Used by `stride evaluate --phase discovery` (Phase B's multi_model_evaluator
extension) for human-readable iteration progress.

Public API:
    evaluate_iteration(feature_dir, iteration_num=None, repo_root=None) -> dict
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from stride_shared_lib import load_yaml_with_frontmatter


REPO_ROOT_DEFAULT = Path(__file__).resolve().parent.parent.parent

# Heuristic mapping: which artifacts indicate which iteration is reached
# Iteration 1 (bootstrap): stakeholder_map + value_canvas exist
# Iteration 2 (structure): + goal_tree + change_strategy
# Iteration 3 (refinement): + condition_variation OR information_state with states
_ITERATION_INDICATORS = {
    1: ["stakeholder_map.yaml", "value_canvas.yaml"],
    2: ["goal_tree.yaml", "change_strategy.yaml"],
    3: ["condition_variation.yaml", "information_state.yaml"],
}

MAX_ITERATIONS = 3


def _file_exists_in_upstream(feature_dir: Path, artifact_name: str) -> bool:
    upstream_dir = feature_dir / "upstream"
    if not upstream_dir.is_dir():
        return False
    for phase_dir in upstream_dir.iterdir():
        if (phase_dir / artifact_name).is_file():
            return True
    return False


def evaluate_iteration(
    feature_dir: Path,
    iteration_num: Optional[int] = None,
    repo_root: Optional[Path] = None,
) -> dict:
    """Evaluate which iteration the feature has reached.

    Args:
        feature_dir: specs/<feature>/
        iteration_num: optional — verify a specific iteration is reachable.
                       If > MAX_ITERATIONS, returns error.
        repo_root: optional override

    Returns:
        {
            "iteration_complete": int (0..3),
            "max_iterations": 3,
            "iteration_details": {1: {...}, 2: {...}, 3: {...}},
            "policy_version": "...",
            "error": str | None,
        }
    """
    if yaml is None:
        raise RuntimeError("PyYAML is required")
    feature_dir = Path(feature_dir)
    repo_root = repo_root or REPO_ROOT_DEFAULT

    policy_path = repo_root / "shared" / "policies" / "upstream_iteration_policy.yaml"
    if not policy_path.is_file():
        raise FileNotFoundError(f"policy not found: {policy_path}")
    policy = load_yaml_with_frontmatter(policy_path, strict=True)

    pattern = policy.get("iteration_pattern", {})
    bound = pattern.get("loop_bound", {})
    max_iter = bound.get("max_iterations", MAX_ITERATIONS)

    # Validate iteration_num if provided
    error: Optional[str] = None
    if iteration_num is not None:
        if iteration_num < 1 or iteration_num > max_iter:
            error = (
                f"iteration_num={iteration_num} exceeds max_iterations={max_iter} "
                f"(policy violation)"
            )

    details: dict[int, dict] = {}
    iteration_complete = 0
    for it_num in (1, 2, 3):
        indicators = _ITERATION_INDICATORS[it_num]
        present = [a for a in indicators if _file_exists_in_upstream(feature_dir, a)]
        # iteration is "reached" if at least one indicator is present
        reached = len(present) > 0
        # Iteration N complete = all indicators present AND prior iterations complete
        complete = len(present) == len(indicators)
        details[it_num] = {
            "indicators": indicators,
            "present": present,
            "reached": reached,
            "complete": complete,
        }
        if complete and iteration_complete == it_num - 1:
            iteration_complete = it_num

    return {
        "iteration_complete": iteration_complete,
        "max_iterations": max_iter,
        "iteration_details": details,
        "policy_version": policy.get("version", "unknown"),
        "error": error,
    }


def main():
    import argparse
    import json
    import sys
    parser = argparse.ArgumentParser(description="Evaluate upstream iteration progress.")
    parser.add_argument("feature_dir")
    parser.add_argument("--iteration", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = evaluate_iteration(Path(args.feature_dir), args.iteration)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["error"]:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"iteration_complete: {result['iteration_complete']} / {result['max_iterations']}")
        for n, d in result["iteration_details"].items():
            mark = "✓" if d["complete"] else ("◐" if d["reached"] else "○")
            print(f"  {mark} iteration {n}: present={d['present']}")


if __name__ == "__main__":  # pragma: no cover
    main()
