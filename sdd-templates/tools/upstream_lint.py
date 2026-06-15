#!/usr/bin/env python3
"""upstream_lint — emits the 4 Phase B lint error codes.

Called from stride_lint.py's lint_feature() at the end (when upstream/ exists).
Adds these error codes to lint result:
  - BACCM_INCOMPLETE         (BACCM 6 axes not all PASS)
  - BROKEN_LAYER_LINK         (requirements_architecture cross_layer_links broken)
  - UPSTREAM_TEMPLATE_DRIFT  (artifact's template_id mismatches frontmatter)
  - BABOK_TECHNIQUE_UNKNOWN  (elicitation_plan technique_id not in 50-library)

Public API:
    lint_upstream(feature_dir, config, result) -> None
        result is the lint Result object that exposes add_error / add_warning.
"""
from __future__ import annotations

import re
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

# Error code constants (UPPER_SNAKE_CASE per existing stride_lint.py convention)
BACCM_INCOMPLETE = "BACCM_INCOMPLETE"
BROKEN_LAYER_LINK = "BROKEN_LAYER_LINK"
UPSTREAM_TEMPLATE_DRIFT = "UPSTREAM_TEMPLATE_DRIFT"
BABOK_TECHNIQUE_UNKNOWN = "BABOK_TECHNIQUE_UNKNOWN"

SUGGESTED_ACTIONS = {
    BACCM_INCOMPLETE: (
        "Run 'stride upstream init <feature> --phase discovery' to scaffold "
        "missing BACCM artifacts. See manual/40_baccm_guide.md."
    ),
    BROKEN_LAYER_LINK: (
        "Check cross_layer_links references in requirements_architecture.yaml. "
        "See manual/41_layered_requirements_modeling_guide.md."
    ),
    UPSTREAM_TEMPLATE_DRIFT: (
        "Update artifact's template_id to match upstream/<template>.yaml frontmatter."
    ),
    BABOK_TECHNIQUE_UNKNOWN: (
        "Check technique_id against shared/policies/technique_library.yaml. "
        "See manual/40_baccm_guide.md."
    ),
}

_TEMPLATE_ID_PATTERN = re.compile(r"^TPL-UP-[A-Z]{3,4}-[0-9]{3}$")


def _load_yaml_with_frontmatter(path: Path) -> Optional[dict]:
    """Parse a YAML file with optional --- frontmatter wrapper.

    v6.0 bugfix01: stride_shared_lib.load_yaml_with_frontmatter(strict=False) に統一.
    既存挙動 (parse error → None で握りつぶし、lint 継続) を strict=False で維持.
    """
    return load_yaml_with_frontmatter(path, strict=False)


def _load_technique_ids(repo_root: Path) -> set[str]:
    path = repo_root / "shared" / "policies" / "technique_library.yaml"
    if not path.is_file() or yaml is None:
        return set()
    data = load_yaml_with_frontmatter(path, strict=False) or {}
    return {t["id"] for t in data.get("techniques", []) if "id" in t}


def _load_valid_template_ids(repo_root: Path) -> set[str]:
    """Collect template_id values from sdd-templates/templates/upstream/*.yaml."""
    ids: set[str] = set()
    templates_dir = repo_root / "sdd-templates" / "templates" / "upstream"
    if not templates_dir.is_dir():
        return ids
    for tpl in templates_dir.glob("*_template.yaml"):
        data = _load_yaml_with_frontmatter(tpl)
        if isinstance(data, dict) and "template_id" in data:
            ids.add(data["template_id"])
    return ids


class _ErrorAccumulator:
    """Minimal duck-type for `result` in case the caller passes a list-like object."""
    def __init__(self):
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    def add_error(self, code: str, message: str, suggested_action: str = "", **kwargs):
        self.errors.append({
            "code": code,
            "message": message,
            "suggested_action": suggested_action,
            **kwargs,
        })

    def add_warning(self, code: str, message: str, **kwargs):
        self.warnings.append({"code": code, "message": message, **kwargs})


def _check_baccm(feature_dir: Path, repo_root: Path, result) -> None:
    """Check BACCM 6-axis completeness (delegates to baccm_completeness_checker)."""
    try:
        from baccm_completeness_checker import check_baccm_completeness
    except ImportError:
        # When called from stride_lint.py the tools/ dir is on sys.path; otherwise import locally.
        import sys
        sys.path.insert(0, str(repo_root / "sdd-templates" / "tools"))
        from baccm_completeness_checker import check_baccm_completeness

    try:
        baccm = check_baccm_completeness(feature_dir, repo_root=repo_root)
    except (FileNotFoundError, RuntimeError, ValueError):
        return  # silently skip if policy missing
    if baccm["overall_pass"]:
        return
    for axis_name, axis_data in baccm["axes"].items():
        if axis_data["pass"]:
            continue
        msg_parts = []
        if axis_data["missing_keys"]:
            msg_parts.append(f"missing_keys={axis_data['missing_keys']}")
        if axis_data["missing_min_counts"]:
            msg_parts.append(f"missing_min_counts={axis_data['missing_min_counts']}")
        message = f"BACCM axis '{axis_name}' incomplete: " + "; ".join(msg_parts)
        result.add_error(
            BACCM_INCOMPLETE,
            message,
            suggested_action=SUGGESTED_ACTIONS[BACCM_INCOMPLETE],
        )


def _check_layered_links(feature_dir: Path, result) -> None:
    """Check requirements_architecture.yaml cross_layer_links integrity."""
    upstream_dir = feature_dir / "upstream"
    if not upstream_dir.is_dir():
        return
    rar_paths = list(upstream_dir.glob("**/requirements_architecture.yaml"))
    for rar_path in rar_paths:
        data = _load_yaml_with_frontmatter(rar_path)
        if not isinstance(data, dict):
            continue
        layers = data.get("layers", [])
        # Build set of all item ids per layer
        layer_ids: dict[str, set[str]] = {}
        for layer in layers:
            if not isinstance(layer, dict):
                continue
            lid = layer.get("id")
            if not lid:
                continue
            items = layer.get("items") or []
            layer_ids[lid] = {str(i) for i in items if i}
        # Verify every cross_layer_link target exists in a layer
        for link in data.get("cross_layer_links") or []:
            if not isinstance(link, dict):
                continue
            from_layer = link.get("from_layer")
            from_id = link.get("from_id")
            to_layer = link.get("to_layer")
            to_id = link.get("to_id")
            if from_layer and from_id is not None:
                if from_id not in layer_ids.get(from_layer, set()):
                    result.add_error(
                        BROKEN_LAYER_LINK,
                        f"cross_layer_link from {from_layer}/{from_id} not found in layer items",
                        suggested_action=SUGGESTED_ACTIONS[BROKEN_LAYER_LINK],
                    )
            if to_layer and to_id is not None:
                if to_id not in layer_ids.get(to_layer, set()):
                    result.add_error(
                        BROKEN_LAYER_LINK,
                        f"cross_layer_link to {to_layer}/{to_id} not found in layer items",
                        suggested_action=SUGGESTED_ACTIONS[BROKEN_LAYER_LINK],
                    )


def _check_template_drift(feature_dir: Path, repo_root: Path, result) -> None:
    """Check upstream artifact's template_id matches a known template."""
    upstream_dir = feature_dir / "upstream"
    if not upstream_dir.is_dir():
        return
    valid_ids = _load_valid_template_ids(repo_root)
    if not valid_ids:
        return
    for artifact in upstream_dir.glob("**/*.yaml"):
        data = _load_yaml_with_frontmatter(artifact)
        if not isinstance(data, dict):
            continue
        tpl_id = data.get("template_id")
        if not tpl_id:
            continue
        if not _TEMPLATE_ID_PATTERN.match(tpl_id):
            result.add_error(
                UPSTREAM_TEMPLATE_DRIFT,
                f"{artifact.name}: template_id={tpl_id} does not match pattern TPL-UP-XXX-NNN",
                suggested_action=SUGGESTED_ACTIONS[UPSTREAM_TEMPLATE_DRIFT],
            )
        elif tpl_id not in valid_ids:
            result.add_error(
                UPSTREAM_TEMPLATE_DRIFT,
                f"{artifact.name}: template_id={tpl_id} not registered in upstream templates",
                suggested_action=SUGGESTED_ACTIONS[UPSTREAM_TEMPLATE_DRIFT],
            )


def _check_technique_unknown(feature_dir: Path, repo_root: Path, result) -> None:
    """Check elicitation_plan.yaml technique_id values against the 50-technique library."""
    upstream_dir = feature_dir / "upstream"
    if not upstream_dir.is_dir():
        return
    valid_ids = _load_technique_ids(repo_root)
    if not valid_ids:
        return
    for plan_path in upstream_dir.glob("**/elicitation_plan.yaml"):
        data = _load_yaml_with_frontmatter(plan_path)
        if not isinstance(data, dict):
            continue
        for tid in data.get("techniques") or []:
            if isinstance(tid, str) and tid not in valid_ids:
                result.add_error(
                    BABOK_TECHNIQUE_UNKNOWN,
                    f"elicitation_plan.yaml: unknown technique_id '{tid}'",
                    suggested_action=SUGGESTED_ACTIONS[BABOK_TECHNIQUE_UNKNOWN],
                )


def lint_upstream(feature_dir, config=None, result=None, repo_root: Optional[Path] = None):
    """Main entrypoint. config is currently unused; reserved for future flags."""
    feature_dir = Path(feature_dir)
    repo_root = repo_root or REPO_ROOT_DEFAULT
    if result is None:
        result = _ErrorAccumulator()
    upstream_dir = feature_dir / "upstream"
    if not upstream_dir.is_dir():
        # No upstream artifacts → nothing to lint
        return result
    _check_baccm(feature_dir, repo_root, result)
    _check_layered_links(feature_dir, result)
    _check_template_drift(feature_dir, repo_root, result)
    _check_technique_unknown(feature_dir, repo_root, result)
    return result


def main():
    import argparse
    import json
    import sys
    parser = argparse.ArgumentParser(description="Lint upstream artifacts (Phase B).")
    parser.add_argument("feature_dir")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = lint_upstream(Path(args.feature_dir))
    payload = {
        "errors": result.errors,
        "warnings": result.warnings,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for e in result.errors:
            print(f"  ✗ {e['code']}: {e['message']}")
        for w in result.warnings:
            print(f"  ⚠ {w['code']}: {w['message']}")
        if not result.errors and not result.warnings:
            print("upstream lint: PASS (no findings)")
    sys.exit(1 if result.errors else 0)


if __name__ == "__main__":  # pragma: no cover
    main()
