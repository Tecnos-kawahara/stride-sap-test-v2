#!/usr/bin/env python3
"""baccm_completeness_checker — BACCM 6-axis completeness judge.

Reads shared/policies/baccm_completeness.yaml and verifies that the 6 BACCM axes
(change / need / solution / stakeholder / value / context) are satisfied by
each axis's source_artifacts under specs/<feature>/upstream/phase_0_*/.

Used by `stride upstream validate` and stride_lint.lint_upstream() to fire
the BACCM_INCOMPLETE error code.

Public API:
    check_baccm_completeness(feature_dir, repo_root=None) -> dict
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
EXPECTED_AXES = {"change", "need", "solution", "stakeholder", "value", "context"}


def _find_artifact_in_upstream(feature_dir: Path, artifact_name: str) -> Optional[Path]:
    """Search specs/<feature>/upstream/<phase>/<artifact_name>."""
    upstream_dir = feature_dir / "upstream"
    if not upstream_dir.is_dir():
        return None
    for phase_dir in upstream_dir.iterdir():
        if not phase_dir.is_dir():
            continue
        candidate = phase_dir / artifact_name
        if candidate.is_file():
            return candidate
    return None


def _has_required_keys(data: dict, required_keys: list[str]) -> list[str]:
    """Return list of missing/empty keys."""
    if not isinstance(data, dict):
        return list(required_keys)
    missing = []
    for key in required_keys:
        value = data.get(key)
        if value is None or value == "" or value == [] or value == {}:
            missing.append(key)
    return missing


def _has_required_min_count(data: dict, key: str, count: int) -> bool:
    """Check that data[key] is a list of at least `count` items."""
    if not isinstance(data, dict):
        return False
    items = data.get(key)
    return isinstance(items, list) and len(items) >= count


def check_baccm_completeness(
    feature_dir: Path,
    repo_root: Optional[Path] = None,
) -> dict:
    """Evaluate BACCM 6-axis completeness for a feature.

    Returns:
        {
            "overall_pass": bool,
            "score": int (0-100),
            "axes": {
                "change":      {"pass": bool, "missing_keys": [...], "missing_min_counts": [...]},
                ...
            },
            "policy_version": "...",
        }
    """
    if yaml is None:
        raise RuntimeError("PyYAML is required")
    feature_dir = Path(feature_dir)
    repo_root = repo_root or REPO_ROOT_DEFAULT

    policy_path = repo_root / "shared" / "policies" / "baccm_completeness.yaml"
    if not policy_path.is_file():
        raise FileNotFoundError(f"policy not found: {policy_path}")
    policy = load_yaml_with_frontmatter(policy_path, strict=True)

    axes_def = policy.get("baccm_axes", {})
    actual_axes = set(axes_def.keys())
    if actual_axes != EXPECTED_AXES:
        raise ValueError(
            f"baccm_axes keys mismatch: expected {EXPECTED_AXES}, got {actual_axes}"
        )

    axes_result: dict[str, dict] = {}
    for axis_name, axis_def in axes_def.items():
        missing_keys: list[str] = []
        missing_min_counts: list[str] = []
        sources = axis_def.get("source_artifacts", [])
        # An axis passes only if ALL its source_artifacts satisfy their requirements
        sources_passed = True
        for src in sources:
            artifact_name = src["artifact"]
            artifact_path = _find_artifact_in_upstream(feature_dir, artifact_name)
            if artifact_path is None:
                # Artifact not found = treat as missing all required
                if "required_keys" in src:
                    missing_keys.extend(
                        f"{artifact_name}:{k}" for k in src["required_keys"]
                    )
                if "required_min_count" in src:
                    rmc = src["required_min_count"]
                    missing_min_counts.append(
                        f"{artifact_name}:{rmc['key']}>={rmc['count']}"
                    )
                sources_passed = False
                continue
            artifact_data = load_yaml_with_frontmatter(artifact_path, strict=True) or {}
            if not isinstance(artifact_data, dict):
                artifact_data = {}
            if "required_keys" in src:
                missing = _has_required_keys(artifact_data, src["required_keys"])
                if missing:
                    missing_keys.extend(f"{artifact_name}:{k}" for k in missing)
                    sources_passed = False
            if "required_min_count" in src:
                rmc = src["required_min_count"]
                if not _has_required_min_count(artifact_data, rmc["key"], rmc["count"]):
                    missing_min_counts.append(
                        f"{artifact_name}:{rmc['key']}>={rmc['count']}"
                    )
                    sources_passed = False
        axes_result[axis_name] = {
            "pass": sources_passed,
            "missing_keys": missing_keys,
            "missing_min_counts": missing_min_counts,
        }

    passing_axes = sum(1 for a in axes_result.values() if a["pass"])
    overall_pass = passing_axes == 6
    # Score: 0-100. Constitutional threshold = 100% (all_axes_pass_required)
    score = int(passing_axes / 6 * 100)

    return {
        "overall_pass": overall_pass,
        "score": score,
        "axes": axes_result,
        "policy_version": policy.get("version", "unknown"),
    }


def main():
    import argparse
    import json
    import sys
    parser = argparse.ArgumentParser(description="Check BACCM 6-axis completeness.")
    parser.add_argument("feature_dir", help="specs/<feature>/")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = check_baccm_completeness(Path(args.feature_dir))
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if result["overall_pass"] else "FAIL"
        print(f"BACCM completeness: {status} (score: {result['score']}%)")
        for axis, axis_data in result["axes"].items():
            mark = "✓" if axis_data["pass"] else "✗"
            print(f"  {mark} {axis}: {'PASS' if axis_data['pass'] else 'FAIL'}")
            if axis_data["missing_keys"]:
                print(f"     missing_keys: {axis_data['missing_keys']}")
            if axis_data["missing_min_counts"]:
                print(f"     missing_min_counts: {axis_data['missing_min_counts']}")
    sys.exit(0 if result["overall_pass"] else 1)


if __name__ == "__main__":  # pragma: no cover
    main()
