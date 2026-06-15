#!/usr/bin/env python3
"""upstream_scaffolder — Phase B implementation of `stride upstream init`.

Scaffolds Phase 0 (discovery) / Phase 0.3 (elicit) / Phase 0.5 (context_modelling)
artifacts under specs/<feature>/upstream/<phase>/ from
sdd-templates/templates/upstream/.

Reads shared/policies/upstream_policy.yaml to determine which artifacts to
generate per phase, and respects profile applicability (lite mode for prototype).

Public API:
    scaffold_upstream(feature, phase, profile=None, repo_root=None) -> dict
"""
from __future__ import annotations

import shutil
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

# Phase name normalization: kebab-case -> snake_case (CLI accepts both)
_PHASE_NORMALIZE = {
    "discovery": "phase_0_discovery",
    "elicit": "phase_0_3_elicit",
    "context_modelling": "phase_0_5_context_modelling",
    "context-modelling": "phase_0_5_context_modelling",
}

VALID_PHASES = set(_PHASE_NORMALIZE.keys())
VALID_PROFILES = {"enterprise-erp", "saas-integration", "prototype"}

# Lite mode (prototype profile) only generates these in discovery
_LITE_DISCOVERY_ARTIFACTS = {"stakeholder_map.yaml", "value_canvas.yaml"}


def _load_upstream_policy(repo_root: Path) -> dict:
    policy_path = repo_root / "shared" / "policies" / "upstream_policy.yaml"
    if not policy_path.is_file():
        raise FileNotFoundError(f"upstream_policy not found: {policy_path}")
    return load_yaml_with_frontmatter(policy_path, strict=True)


def _resolve_profile(feature_dir: Path, override: Optional[str]) -> str:
    """Resolve profile per shared/policies/profile_policy.yaml resolution order."""
    if override:
        if override not in VALID_PROFILES:
            raise ValueError(f"Invalid profile: {override} (allowed: {VALID_PROFILES})")
        return override
    # Try basic_design.md
    bd = feature_dir / "basic_design.md"
    if bd.is_file():
        text = bd.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("profile:"):
                value = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                if value.startswith("#"):
                    continue
                value = value.split("#", 1)[0].strip().strip('"').strip("'")
                if value in VALID_PROFILES:
                    return value
    # Try state.yaml (state.yaml has no frontmatter so the helper still works)
    state = feature_dir / "state" / "state.yaml"
    if state.is_file():
        data = load_yaml_with_frontmatter(state, strict=True) or {}
        if data.get("profile") in VALID_PROFILES:
            return data["profile"]
    return "enterprise-erp"


def scaffold_upstream(
    feature: str,
    phase: str,
    profile: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> dict:
    """Scaffold upstream artifacts for a feature.

    Args:
        feature: feature_name (snake_case)
        phase: discovery | elicit | context_modelling | context-modelling
        profile: optional override; defaults to basic_design.md profile
        repo_root: optional repo root override (for testing)

    Returns:
        {
            "feature_id": "FEAT-...",
            "phase": "phase_0_discovery",
            "profile": "enterprise-erp",
            "generated_files": [...],
            "skipped_files": [...],
        }
    """
    if yaml is None:
        raise RuntimeError("PyYAML is required (pip install pyyaml)")
    if phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase: {phase} (allowed: {VALID_PHASES})")

    repo_root = repo_root or REPO_ROOT_DEFAULT
    feature_dir = repo_root / "specs" / feature
    if not feature_dir.is_dir():
        raise FileNotFoundError(f"feature dir not found: {feature_dir}")

    canonical_phase = _PHASE_NORMALIZE[phase]
    resolved_profile = _resolve_profile(feature_dir, profile)
    policy = _load_upstream_policy(repo_root)

    phase_def = policy.get("phases", {}).get(canonical_phase)
    if phase_def is None:
        raise ValueError(f"Unknown phase in policy: {canonical_phase}")
    artifacts = phase_def.get("artifacts", [])

    # Lite mode filter for prototype profile (discovery only)
    if resolved_profile == "prototype" and canonical_phase == "phase_0_discovery":
        artifacts = [a for a in artifacts if a.get("artifact") in _LITE_DISCOVERY_ARTIFACTS]

    templates_dir = repo_root / "sdd-templates" / "templates" / "upstream"
    out_dir = feature_dir / "upstream" / canonical_phase
    out_dir.mkdir(parents=True, exist_ok=True)

    feature_id = "FEAT-" + feature.upper().replace("-", "").replace("_", "")
    generated: list[str] = []
    skipped: list[str] = []

    for art in artifacts:
        artifact_name = art["artifact"]
        template_name = art["template"]
        src = templates_dir / template_name
        dst = out_dir / artifact_name
        if not src.is_file():
            raise FileNotFoundError(f"template not found: {src}")
        if dst.exists():
            skipped.append(str(dst.relative_to(repo_root)))
            continue
        # Copy + simple placeholder substitution
        text = src.read_text(encoding="utf-8")
        text = text.replace("FEAT-XXX", feature_id)
        dst.write_text(text, encoding="utf-8")
        generated.append(str(dst.relative_to(repo_root)))

    return {
        "feature_id": feature_id,
        "phase": canonical_phase,
        "profile": resolved_profile,
        "generated_files": generated,
        "skipped_files": skipped,
    }


# CLI entrypoint
def main():
    import argparse
    import json
    import sys
    parser = argparse.ArgumentParser(description="Scaffold upstream artifacts (Phase B).")
    parser.add_argument("feature", help="feature_name (snake_case)")
    parser.add_argument(
        "--phase",
        required=True,
        choices=sorted(VALID_PHASES),
    )
    parser.add_argument("--profile", choices=sorted(VALID_PROFILES))
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    try:
        result = scaffold_upstream(args.feature, args.phase, args.profile)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"feature_id: {result['feature_id']}")
        print(f"phase: {result['phase']}")
        print(f"profile: {result['profile']}")
        print(f"generated: {len(result['generated_files'])}")
        for p in result["generated_files"]:
            print(f"  + {p}")
        if result["skipped_files"]:
            print(f"skipped: {len(result['skipped_files'])}")
            for p in result["skipped_files"]:
                print(f"  - {p}")


if __name__ == "__main__":  # pragma: no cover
    main()
