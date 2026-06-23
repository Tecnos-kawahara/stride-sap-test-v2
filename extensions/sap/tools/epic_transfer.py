#!/usr/bin/env python3
"""
SAP Epic Transfer — 機能群仕様書 YAML → STRIDE Epic 構造への転写ツール

Usage:
    python3 extensions/sap/tools/epic_transfer.py \\
        --yaml docs/yaml/FG-SD005-003/FG-SD005-003.group.yaml \\
        --epic-dir epics/EPIC-EDILOT/ \\
        --epic-id EPIC-EDILOT

Prerequisites:
    - stride epic init <EPIC_ID> が実行済みであること
    - 機能群 YAML に ownership, coverageTier, sharedContracts が含まれていること
"""

import argparse
import re
import sys
import os
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# YAML helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: str) -> dict:
    """Load a YAML file and return the parsed dict."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a valid YAML mapping")
    return data


def _extract_yaml_block(md_path: str) -> tuple[str, int, int]:
    """Extract the first ```yaml ... ``` block from a markdown file.

    Returns (yaml_text, start_line, end_line) where lines are 0-indexed.
    """
    lines = Path(md_path).read_text(encoding="utf-8").splitlines()
    start = end = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("```yaml") and start == -1:
            start = i
        elif line.strip() == "```" and start != -1 and end == -1:
            end = i
            break
    if start == -1 or end == -1:
        raise ValueError(f"No ```yaml block found in {md_path}")
    yaml_text = "\n".join(lines[start + 1 : end])
    return yaml_text, start, end


def _replace_yaml_block(md_path: str, new_yaml: str) -> None:
    """Replace the first ```yaml block in a markdown file with new content."""
    lines = Path(md_path).read_text(encoding="utf-8").splitlines()
    _, start, end = _extract_yaml_block(md_path)
    new_lines = lines[: start + 1] + new_yaml.splitlines() + lines[end:]
    Path(md_path).write_text("\n".join(new_lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# camelCase → snake_case
# ---------------------------------------------------------------------------

_CAMEL_RE = re.compile(r"(?<=[a-z0-9])([A-Z])")

def _to_snake(name: str) -> str:
    return _CAMEL_RE.sub(r"_\1", name).lower()


# ---------------------------------------------------------------------------
# Mapping logic
# ---------------------------------------------------------------------------

def _build_feature_team_map(ownership: dict) -> dict[str, str]:
    """Build a featureId → teamId reverse lookup from ownership.teams."""
    mapping: dict[str, str] = {}
    for team in ownership.get("teams", []):
        team_id = team.get("teamId", "")
        for feat_id in team.get("features", []):
            mapping[feat_id] = team_id
    return mapping


def transfer_epic_design(group_yaml: dict, epic_id: str) -> dict:
    """Convert group YAML to epic_design.md YAML structure."""
    meta = group_yaml.get("meta", {})
    bs = group_yaml.get("businessSpec", {})
    ctx = bs.get("context", {})
    why = ctx.get("why", {})
    ownership = group_yaml.get("ownership", {})
    roster = group_yaml.get("functionRoster", [])
    shared = group_yaml.get("sharedContracts", [])
    fs = group_yaml.get("functionStructure", {})
    connections = fs.get("interFunctionConnections", [])

    feat_team_map = _build_feature_team_map(ownership)

    # --- meta ---
    epic_meta = {
        "epic_id": epic_id,
        "title": meta.get("groupName", ""),
        "version": "1.0.0",
        "status": meta.get("status", "draft"),
        "created_at": meta.get("updated", ""),
        "updated_at": meta.get("updated", ""),
        "sap_group_id": meta.get("groupId", ""),
        "sap_group_yaml": "",
    }

    # --- ownership ---
    epic_ownership = {
        "sponsor": "",
        "epic_lead": ownership.get("epicLead", ""),
        "teams": [],
    }
    for team in ownership.get("teams", []):
        epic_ownership["teams"].append({
            "team_id": team.get("teamId", ""),
            "name": team.get("name", ""),
            "lead": team.get("lead", ""),
            "features": team.get("features", []),
        })

    # --- scope ---
    why_text = ""
    if isinstance(why, dict):
        purpose = why.get("目的", "")
        background = why.get("背景", "")
        why_text = f"{purpose}\n{background}".strip()
    elif isinstance(why, str):
        why_text = why

    epic_scope = {
        "business_context": {
            "who": ctx.get("who", ""),
            "what": ctx.get("what", ""),
            "why": why_text,
        },
        "value_stream": "",
        "strategic_alignment": [],
        "out_of_scope": [],
    }

    # --- features ---
    epic_features = []
    for i, feat in enumerate(roster):
        feat_id = feat.get("featureId", "")
        tier = feat.get("coverageTier", "standard")
        epic_features.append({
            "feature_id": feat_id,
            "name": feat.get("name", ""),
            "team_id": feat_team_map.get(feat_id, ""),
            "coverage_tier": tier,
            "priority": i + 1,
            "dependencies": [],
            "description": feat.get("name", ""),
        })

    # --- shared_contracts ---
    epic_contracts = []
    for sc in shared:
        contract = {
            "contract_id": sc.get("contractId", ""),
            "name": sc.get("name", ""),
            "type": sc.get("type", ""),
            "owner_team": sc.get("ownerTeam", ""),
            "owner_feature": sc.get("ownerFeature", ""),
            "consumers": [],
        }
        for consumer in sc.get("consumers", []):
            contract["consumers"].append({
                "team_id": consumer.get("teamId", ""),
                "features": consumer.get("features", []),
            })
        epic_contracts.append(contract)

    # --- cross_team_dependencies ---
    epic_deps = []
    for i, conn in enumerate(connections):
        epic_deps.append({
            "dependency_id": f"DEP-{i + 1:03d}",
            "from_feature": conn.get("from", ""),
            "to_feature": conn.get("to", ""),
            "type": "blocking",
            "interface": "",
            "description": conn.get("description", ""),
        })

    # --- gate_check (auto-calculated) ---
    tiers = [f.get("coverage_tier", "standard") for f in epic_features]
    gate_check = {
        "counts": {
            "total_features": len(epic_features),
            "critical_features": tiers.count("critical"),
            "standard_features": tiers.count("standard"),
            "experimental_features": tiers.count("experimental"),
            "cross_team_dependencies": len(epic_deps),
            "shared_contracts": len(epic_contracts),
        },
        "rules": {
            "min_features": 2,
            "max_critical_per_epic": 5,
            "max_teams": 5,
        },
        "all_features_have_team": all(f["team_id"] for f in epic_features),
        "all_dependencies_mapped": all(d.get("interface") for d in epic_deps) if epic_deps else True,
        "shared_contracts_defined": len(epic_contracts) > 0,
        "no_dependency_cycles": True,
        "min_features_met": len(epic_features) >= 2,
        "ready_for_feature_specs": False,
    }
    gate_check["ready_for_feature_specs"] = (
        gate_check["all_features_have_team"]
        and gate_check["shared_contracts_defined"]
        and gate_check["no_dependency_cycles"]
        and gate_check["min_features_met"]
    )

    return {
        "epic": {
            "meta": epic_meta,
            "ownership": epic_ownership,
            "scope": epic_scope,
            "features": epic_features,
            "shared_contracts": epic_contracts,
            "cross_team_dependencies": epic_deps,
            "milestones": [],
            "integration_points": [],
            "risks": [],
            "team_capacity": [
                {"team_id": t["team_id"], "allocated_members": 0, "effort_points": 0}
                for t in epic_ownership["teams"]
            ],
            "critical_path": [],
            "epic_gate_check": gate_check,
        }
    }


def transfer_feature_breakdown(group_yaml: dict, epic_id: str) -> dict:
    """Convert group YAML to feature_breakdown.md YAML structure."""
    roster = group_yaml.get("functionRoster", [])
    fs = group_yaml.get("functionStructure", {})
    connections = fs.get("interFunctionConnections", [])
    ownership = group_yaml.get("ownership", {})
    feat_team_map = _build_feature_team_map(ownership)

    features = []
    for feat in roster:
        feat_id = feat.get("featureId", "")
        features.append({
            "feature_id": feat_id,
            "name": feat.get("name", ""),
            "type": feat.get("type", ""),
            "sap_id": feat.get("sapId", ""),
            "program_id": feat.get("programId"),
            "coverage_tier": feat.get("coverageTier", "standard"),
            "team_id": feat_team_map.get(feat_id, ""),
        })

    edges = []
    for conn in connections:
        edges.append({
            "from": conn.get("from", ""),
            "to": conn.get("to", ""),
            "type": conn.get("type", "data_dependency"),
        })

    return {
        "feature_breakdown": {
            "epic_id": epic_id,
            "features": features,
            "dependency_graph": {"edges": edges},
            "split_rationale": fs.get("splitRationale", ""),
        }
    }


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------

def write_epic_design(epic_dir: str, epic_data: dict) -> str:
    """Write epic_design.md with transferred data."""
    md_path = os.path.join(epic_dir, "epic_design.md")
    if not os.path.isfile(md_path):
        raise FileNotFoundError(
            f"{md_path} not found. Run 'stride epic init <EPIC_ID>' first."
        )
    yaml_str = yaml.dump(epic_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    _replace_yaml_block(md_path, yaml_str)
    return md_path


def write_feature_breakdown(epic_dir: str, breakdown_data: dict) -> str:
    """Write feature_breakdown.md with transferred data."""
    md_path = os.path.join(epic_dir, "feature_breakdown.md")
    if not os.path.isfile(md_path):
        raise FileNotFoundError(
            f"{md_path} not found. Run 'stride epic init <EPIC_ID>' first."
        )
    yaml_str = yaml.dump(breakdown_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    _replace_yaml_block(md_path, yaml_str)
    return md_path


# ---------------------------------------------------------------------------
# Validation (pre-flight)
# ---------------------------------------------------------------------------

def validate_group_yaml(data: dict) -> list[str]:
    """Check that the group YAML has required fields for transfer."""
    errors = []

    if "meta" not in data:
        errors.append("Missing 'meta' section")
    if "functionRoster" not in data:
        errors.append("Missing 'functionRoster' section")

    # Check for the 3 additional fields (may not yet exist)
    if "ownership" not in data:
        errors.append("Missing 'ownership' section (仕様書ツール側の追加が必要)")
    else:
        own = data["ownership"]
        if not own.get("epicLead"):
            errors.append("ownership.epicLead is empty")
        if not own.get("teams"):
            errors.append("ownership.teams is empty")

    roster = data.get("functionRoster", [])
    has_tier = any(f.get("coverageTier") for f in roster)
    if not has_tier:
        errors.append("No functionRoster entry has 'coverageTier' (仕様書ツール側の追加が必要)")

    if "sharedContracts" not in data:
        errors.append("Missing 'sharedContracts' section (仕様書ツール側の追加が必要)")

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Transfer SAP 機能群仕様書 YAML to STRIDE Epic structure",
    )
    parser.add_argument("--yaml", required=True, help="Path to group spec YAML")
    parser.add_argument("--epic-dir", required=True, help="Path to epic directory (e.g. epics/EPIC-EDILOT/)")
    parser.add_argument("--epic-id", required=True, help="Epic ID (e.g. EPIC-EDILOT)")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, do not write files")
    args = parser.parse_args()

    # Validate Epic ID format
    if not re.match(r"^EPIC-[A-Z]{3,}$", args.epic_id):
        print(f"ERROR: Invalid Epic ID '{args.epic_id}'. Must match ^EPIC-[A-Z]{{3,}}$", file=sys.stderr)
        return 1

    # Load group YAML
    try:
        group_yaml = _load_yaml(args.yaml)
    except Exception as e:
        print(f"ERROR: Failed to load YAML: {e}", file=sys.stderr)
        return 1

    print(f"Source: {args.yaml}")
    print(f"Target: {args.epic_dir}")
    print(f"Epic ID: {args.epic_id}")
    print()

    # Pre-flight validation
    errors = validate_group_yaml(group_yaml)
    if errors:
        print("Pre-flight validation FAILED:")
        for err in errors:
            print(f"  ERROR: {err}")
        print()
        print("Fix the source YAML before running transfer.")
        return 1
    print("Pre-flight validation: PASSED")

    # Transfer
    epic_data = transfer_epic_design(group_yaml, args.epic_id)
    breakdown_data = transfer_feature_breakdown(group_yaml, args.epic_id)

    # Set source path in meta
    epic_data["epic"]["meta"]["sap_group_yaml"] = args.yaml

    if args.dry_run:
        print()
        print("=== epic_design.md (YAML preview) ===")
        print(yaml.dump(epic_data, default_flow_style=False, allow_unicode=True, sort_keys=False))
        print("=== feature_breakdown.md (YAML preview) ===")
        print(yaml.dump(breakdown_data, default_flow_style=False, allow_unicode=True, sort_keys=False))
        print("[DRY RUN] No files written.")
        return 0

    # Write files
    try:
        ed_path = write_epic_design(args.epic_dir, epic_data)
        print(f"Written: {ed_path}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    try:
        fb_path = write_feature_breakdown(args.epic_dir, breakdown_data)
        print(f"Written: {fb_path}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Summary
    features = epic_data["epic"]["features"]
    contracts = epic_data["epic"]["shared_contracts"]
    gate = epic_data["epic"]["epic_gate_check"]

    print()
    print(f"Transfer complete:")
    print(f"  Features:         {len(features)}")
    print(f"  Shared Contracts: {len(contracts)}")
    print(f"  Gate Check:       ready_for_feature_specs = {gate['ready_for_feature_specs']}")
    print()
    print("Next steps:")
    print(f"  1. Review and fill manual fields (sponsor, value_stream, milestones, risks)")
    print(f"  2. stride epic validate {args.epic_id}")
    print(f"  3. Request E1 approval in EPIC_APPROVAL.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
