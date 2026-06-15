#!/usr/bin/env python3
"""stride method audit — Method Store snapshot generator + IP boundary checker.

Generates `method-store.lock.json` (CT-FILE-01 / method-store-schema.json compliant)
that captures plane labeling, INTERNAL_* marker counts, attribution audit and
element-level git short-sha across the Method content surface.

Usage:
    python3 sdd-templates/tools/method_audit.py [--root .] [--output method-store.lock.json] [--format text|json] [--strict]

Exit codes (per contracts/cli_method_subcommand.yaml):
    0 — Audit passed (no violations) / lock.json emitted
    1 — Violation detected (severity=error, or --strict + warning)
    2 — Usage error
    3 — Feature/root dir not found
    4 — Method content parse error

This is a deliberately small, dependency-light implementation. Helper modules
under sdd-templates/tools/method_labeling/ provide frontmatter parsing,
classification (rule-based), and git sha computation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT_DEFAULT = THIS_DIR.parent.parent  # sdd-templates/tools/ → repo root
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from method_labeling.classifier import Classifier  # noqa: E402
from method_labeling.frontmatter import has_method_labels, parse  # noqa: E402
from method_labeling.sha import git_blob_sha  # noqa: E402

INTERNAL_MARKER_RE = re.compile(
    r"<INTERNAL_(METHOD|PROMPT|RUBRIC)>(?:.*?)</INTERNAL_\1>", re.DOTALL
)
INTERNAL_MARKER_OPEN_RE = re.compile(r"<INTERNAL_(METHOD|PROMPT|RUBRIC)>")
INTERNAL_MARKER_CLOSE_RE = re.compile(r"</INTERNAL_(METHOD|PROMPT|RUBRIC)>")

# Method content paths to scan (matches plane_classification_ruleset_v1.yaml RULE-* coverage).
SCAN_PATTERNS = [
    "sdd-templates/templates/**/*.md",
    "sdd-templates/templates/**/*.yaml",
    "sdd-templates/templates/**/*.yml",
    "sdd-templates/templates/**/*.json",
    "sdd-templates/policies/**/*.yaml",
    "sdd-templates/policies/**/*.yml",
    "sdd-templates/policies/**/*.md",
    "sdd-templates/hooks/**/*.py",
    "sdd-templates/tools/**/*.py",
    "shared/policies/**/*.yaml",
    "cowork-plugin/skills/**/SKILL.md",
    "cowork-plugin/commands/**/*.md",
    "cowork-plugin/reference_files/**/*.md",
    "cowork-plugin/reference_files/**/*.yaml",
    "cowork-plugin/reference_files/**/*.yml",
    "memory/lessons_learned/**/*.md",
    "memory/lessons_learned/**/*.yaml",
    "memory/constitution.md",
    "memory/tecnos_org_constraints.md",
    "memory/artifact_registry.md",
    "memory/constitution_amendments/**/*.md",
    "bpmn/validators/**/*.py",
    "bpmn/spec/**/*.md",
    "bpmn/templates/**",
    "bpmn/examples/**",
    "bpmn/rules/**/*.md",
    "docs/**/*.md",
    "archive/sample-specs/**/*.md",
]


def collect_paths(root: Path) -> list[Path]:
    seen: set[Path] = set()
    for pattern in SCAN_PATTERNS:
        for p in root.glob(pattern):
            if p.is_file() and ".git" not in p.parts and ".venv" not in p.parts:
                seen.add(p)
    return sorted(seen)


def make_element_id(rel_path: str, element_type: str) -> str:
    slug = rel_path.replace("/", ".").replace("\\", ".")
    slug = re.sub(r"\.[a-z0-9]+$", "", slug, flags=re.IGNORECASE)
    slug = re.sub(r"[^a-zA-Z0-9_./-]", "-", slug).lower()
    return f"{_short(element_type)}.{slug}.v1"


def _short(element_type: str) -> str:
    table = {
        "template": "tpl",
        "skill": "skill",
        "policy": "policy",
        "hook": "hook",
        "validator": "validator",
        "lesson": "lesson",
        "reference": "reference",
    }
    return table.get(element_type, "reference")


def audit(root: Path, strict: bool = False) -> tuple[dict, list[dict]]:
    classifier = Classifier(root / "shared" / "policies" / "plane_classification_ruleset_v1.yaml")
    elements: list[dict] = []
    violations: list[dict] = []

    method_version = (root / "sdd-templates" / "VERSION").read_text(encoding="utf-8").strip()

    for path in collect_paths(root):
        rel = path.relative_to(root).as_posix()
        try:
            fm = parse(path)
        except Exception as exc:  # pragma: no cover
            violations.append({"path": rel, "code": "PARSE_ERROR", "message": str(exc), "severity": "error"})
            continue

        cls = classifier.classify(rel)
        labeled = has_method_labels(fm.data)
        if not labeled:
            # Python / BPMN / XML / JSON files cannot easily carry YAML frontmatter.
            # We classify them at the manifest level (sufficient for IP boundary
            # enforcement at the Output Guard layer) but only warn on the source.
            unsupported_inline = path.suffix.lower() in {".py", ".bpmn", ".xml", ".json"}
            severity = "warning" if unsupported_inline or cls.plane != "internal" else "error"
            violations.append({
                "path": rel,
                "code": "MISSING_FRONTMATTER",
                "message": f"plane labeling missing (suggest: plane={cls.plane}, visibility={cls.visibility})",
                "severity": severity,
            })

        body_text = fm.body_after if fm.style != "yaml" else ""
        opens = INTERNAL_MARKER_OPEN_RE.findall(body_text)
        closes = INTERNAL_MARKER_CLOSE_RE.findall(body_text)
        if len(opens) != len(closes):
            violations.append({
                "path": rel,
                "code": "MARKER_UNCLOSED",
                "message": f"unbalanced INTERNAL_* markers: opens={len(opens)} closes={len(closes)}",
                "severity": "error",
            })
        if cls.plane == "internal" and labeled and not opens and fm.data.get("visibility") == "redacted":
            violations.append({
                "path": rel,
                "code": "INTERNAL_MARKER_INCONSISTENT",
                "message": "plane=internal/visibility=redacted requires at least one INTERNAL_* marker",
                "severity": "warning",
            })

        sha = git_blob_sha(path, root)
        plane = fm.data.get("plane", cls.plane)
        visibility = fm.data.get("visibility", cls.visibility)
        return_policy = fm.data.get("return_policy", cls.return_policy)

        elements.append({
            "id": make_element_id(rel, cls.element_type),
            "type": cls.element_type,
            "path": rel,
            "plane": plane,
            "visibility": visibility,
            "return_policy": return_policy,
            "sha": sha,
            "method_version": method_version,
        })

    no_unintended_exposure = not any(v["severity"] == "error" for v in violations)
    if strict:
        no_unintended_exposure = no_unintended_exposure and not violations

    audit_block = {
        "internal_markers_count": sum(
            1 for el in elements if el.get("plane") == "internal"
        ),
        "public_elements": sum(1 for el in elements if el.get("plane") == "public"),
        "sample_elements": sum(1 for el in elements if el.get("plane") == "sample"),
        "redacted_elements": sum(
            1 for el in elements if el.get("visibility") == "redacted"
        ),
        "no_unintended_exposure": no_unintended_exposure,
        "violations": violations,
    }

    manifest = {
        "schema_version": "1.0",
        "root_version": method_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feature_id": "all",
        "elements": elements,
        "ip_boundary_audit": audit_block,
    }
    return manifest, violations


def main() -> int:
    parser = argparse.ArgumentParser(prog="stride method audit")
    parser.add_argument("--root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--output", default="")
    parser.add_argument("--format", choices=["text", "json", "ndjson"], default="text")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"BLOCKED: root not found: {root}", file=sys.stderr)
        return 3

    try:
        manifest, violations = audit(root, strict=args.strict)
    except Exception as exc:
        print(f"PARSE_ERROR: {exc}", file=sys.stderr)
        return 4

    if args.output:
        Path(args.output).write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    elif args.format == "ndjson":
        for el in manifest["elements"]:
            print(json.dumps(el, ensure_ascii=False))
        print(json.dumps({"ip_boundary_audit": manifest["ip_boundary_audit"]}, ensure_ascii=False))
    else:
        ipa = manifest["ip_boundary_audit"]
        print("Method audit:", "PASS" if ipa["no_unintended_exposure"] else "FAIL")
        print(f"  elements:               {len(manifest['elements'])}")
        print(f"  plane.internal:         {sum(1 for el in manifest['elements'] if el['plane'] == 'internal')}")
        print(f"  plane.public:           {ipa['public_elements']}")
        print(f"  plane.sample:           {ipa['sample_elements']}")
        print(f"  redacted_elements:      {ipa['redacted_elements']}")
        print(f"  violations:             {len(violations)}")
        print(f"  no_unintended_exposure: {ipa['no_unintended_exposure']}")
        print(f"  method_version:         {manifest['root_version']}")
        if violations:
            for v in violations[:5]:
                print(f"    [{v['severity']}] {v['code']}: {v['path']} — {v['message']}")
            if len(violations) > 5:
                print(f"    ... ({len(violations) - 5} more)")
        if args.output:
            print(f"  output:                 {args.output}")

    has_error = any(v["severity"] == "error" for v in violations)
    if has_error or (args.strict and violations):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
