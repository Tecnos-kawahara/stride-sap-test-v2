#!/usr/bin/env python3
"""technique_library_query — BABOK 50 technique catalog query interface.

Reads shared/policies/technique_library.yaml and provides lookup/filter API
for the 50 BABOK techniques. Used by elicitation_plan generation and
technique recommendation logic.

Public API:
    lookup_technique(technique_id) -> dict
    list_techniques(typical_phase=None) -> list[dict]
    technique_count() -> int
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


REPO_ROOT_DEFAULT = Path(__file__).resolve().parent.parent.parent

VALID_PHASES = {
    "phase_0_discovery",
    "phase_0_3_elicit",
    "phase_0_5_context_modelling",
    "stride_core",
}


def _load_library(repo_root: Path) -> list[dict]:
    if yaml is None:
        raise RuntimeError("PyYAML is required")
    path = repo_root / "shared" / "policies" / "technique_library.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"technique_library not found: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("techniques", [])


def lookup_technique(
    technique_id: str,
    repo_root: Optional[Path] = None,
) -> dict:
    """Look up a single technique by id.

    Raises:
        KeyError: technique_id not found
    """
    repo_root = repo_root or REPO_ROOT_DEFAULT
    techniques = _load_library(repo_root)
    for t in techniques:
        if t.get("id") == technique_id:
            return dict(t)
    raise KeyError(f"technique not found: {technique_id}")


def list_techniques(
    typical_phase: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> list[dict]:
    """Return all techniques, optionally filtered by typical_phase."""
    repo_root = repo_root or REPO_ROOT_DEFAULT
    techniques = _load_library(repo_root)
    if typical_phase is None:
        return [dict(t) for t in techniques]
    if typical_phase not in VALID_PHASES:
        raise ValueError(f"invalid typical_phase: {typical_phase} (allowed: {VALID_PHASES})")
    return [
        dict(t) for t in techniques
        if typical_phase in (t.get("typical_phase") or [])
    ]


def technique_count(repo_root: Optional[Path] = None) -> int:
    repo_root = repo_root or REPO_ROOT_DEFAULT
    return len(_load_library(repo_root))


def main():
    import argparse
    import json
    import sys
    parser = argparse.ArgumentParser(description="Query BABOK 50 technique library.")
    parser.add_argument("--id", help="lookup a specific technique by id")
    parser.add_argument(
        "--phase",
        choices=sorted(VALID_PHASES),
        help="filter by typical_phase",
    )
    parser.add_argument("--count", action="store_true", help="print total count")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        if args.count:
            n = technique_count()
            print(n if not args.json else json.dumps({"count": n}))
            return
        if args.id:
            result = lookup_technique(args.id)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"id: {result['id']}")
                print(f"name_en: {result.get('name_en')}")
                print(f"name_ja: {result.get('name_ja')}")
                print(f"purpose: {result.get('purpose')}")
                print(f"babok_section: {result.get('babok_section')}")
                print(f"typical_phase: {result.get('typical_phase')}")
            return
        results = list_techniques(args.phase)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for t in results:
                print(f"  {t['id']:40s} {t.get('babok_section', ''):>6s}  {t.get('name_ja', '')}")
            print(f"({len(results)} techniques)")
    except (KeyError, ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
