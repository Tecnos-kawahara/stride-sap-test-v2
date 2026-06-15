"""tenant_policy_validator — validate sdd_tenant_policy YAML/JSON against CT-FILE-03.

Lightweight pure-Python validator that does not require the `jsonschema`
package; covers the schema rules emitted by Feature ② while remaining
re-usable from Feature ③ master-admin DB hooks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - PyYAML is part of the project deps
    yaml = None  # type: ignore


SCHEMA_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+(\.[0-9]+)?$")
SEMVER_PIN_RE = re.compile(
    r"^(~|\^|>=|<=|>|<)?"
    r"[0-9]+(\.(?:[0-9]+|x|\*)){0,2}"
    r"(-[a-zA-Z0-9.-]+)?$"
)
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

ALLOWED_CHANNELS = {"edge", "staging", "stable"}
ALLOWED_AUTO_UPGRADE = {"none", "patch", "minor"}
ALLOWED_NOTIFY_ON = {"upgrade_available", "upgraded", "rollback", "skipped_due_to_pin"}
ALLOWED_PLANS = {"trial", "standard", "enterprise"}

REQUIRED_TOP_FIELDS = ("schema_version", "tenant_id", "channel", "auto_upgrade")


@dataclass
class ValidationReport:
    valid: bool
    errors: list[str] = field(default_factory=list)


def _validate_instance(inst: Any, label: str = "instance") -> ValidationReport:
    rep = ValidationReport(valid=True)
    if not isinstance(inst, dict):
        rep.valid = False
        rep.errors.append(f"{label}: must be an object")
        return rep

    for f in REQUIRED_TOP_FIELDS:
        if f not in inst:
            rep.errors.append(f"{label}: missing required field '{f}'")

    schema_version = inst.get("schema_version")
    if isinstance(schema_version, str) and not SCHEMA_VERSION_RE.match(schema_version):
        rep.errors.append(f"{label}: schema_version '{schema_version}' must match {SCHEMA_VERSION_RE.pattern}")

    tenant_id = inst.get("tenant_id")
    if isinstance(tenant_id, str) and not UUID_RE.match(tenant_id):
        rep.errors.append(f"{label}: tenant_id '{tenant_id}' must be a UUID")

    channel = inst.get("channel")
    if channel not in ALLOWED_CHANNELS:
        rep.errors.append(f"{label}: channel '{channel}' must be one of {sorted(ALLOWED_CHANNELS)}")

    auto_upgrade = inst.get("auto_upgrade")
    if auto_upgrade not in ALLOWED_AUTO_UPGRADE:
        rep.errors.append(f"{label}: auto_upgrade '{auto_upgrade}' must be one of {sorted(ALLOWED_AUTO_UPGRADE)}")

    pin = inst.get("pin")
    if pin is not None and (not isinstance(pin, str) or not SEMVER_PIN_RE.match(pin)):
        rep.errors.append(f"{label}: pin '{pin}' must match {SEMVER_PIN_RE.pattern}")

    notif = inst.get("notifications") or {}
    if not isinstance(notif, dict):
        rep.errors.append(f"{label}: notifications must be an object when present")
    else:
        for evt in (notif.get("notify_on") or []):
            if evt not in ALLOWED_NOTIFY_ON:
                rep.errors.append(f"{label}: notify_on item '{evt}' must be one of {sorted(ALLOWED_NOTIFY_ON)}")
        email = notif.get("email")
        if email and (not isinstance(email, str) or not EMAIL_RE.match(email)):
            rep.errors.append(f"{label}: notifications.email '{email}' is not a valid email")

    metadata = inst.get("metadata") or {}
    if isinstance(metadata, dict):
        plan = metadata.get("plan")
        if plan is not None and plan not in ALLOWED_PLANS:
            rep.errors.append(f"{label}: metadata.plan '{plan}' must be one of {sorted(ALLOWED_PLANS)}")

    rep.valid = not rep.errors
    return rep


def validate_policy(payload: Any) -> ValidationReport:
    """Validate a single tenant policy instance (dict)."""
    return _validate_instance(payload)


def validate_schema_examples(schema_path: Path) -> tuple[ValidationReport, list[ValidationReport]]:
    """Load the schema YAML, validate it self-references valid metadata,
    and validate every instance under the top-level `examples:` key."""
    text = schema_path.read_text(encoding="utf-8")
    if yaml is None:  # pragma: no cover
        return ValidationReport(False, ["PyYAML not installed"]), []
    schema = yaml.safe_load(text) or {}

    schema_report = ValidationReport(valid=True)
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        schema_report.valid = False
        schema_report.errors.append("schema $schema must be JSON Schema Draft 2020-12")
    if "properties" not in schema:
        schema_report.valid = False
        schema_report.errors.append("schema is missing properties block")

    example_reports = []
    for idx, ex in enumerate(schema.get("examples") or []):
        example_reports.append(_validate_instance(ex, label=f"example[{idx}]"))
    return schema_report, example_reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tenant_policy_validator")
    parser.add_argument("--schema",
                        default="shared/policies/sdd_tenant_policy_schema.yaml",
                        help="Path to the schema YAML")
    parser.add_argument("--instance", default="",
                        help="Optional path to a single tenant policy instance to validate")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    schema_path = Path(args.schema).resolve()
    if not schema_path.exists():
        print(f"Error: schema not found at {schema_path}", file=sys.stderr)
        return 2

    schema_rep, example_reps = validate_schema_examples(schema_path)

    instance_rep = None
    if args.instance:
        path = Path(args.instance).resolve()
        if not path.exists():
            print(f"Error: instance not found at {path}", file=sys.stderr)
            return 2
        if path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) if yaml else None
        else:
            data = json.loads(path.read_text(encoding="utf-8"))
        instance_rep = _validate_instance(data, label="user_instance")

    summary = {
        "schema_path": str(schema_path),
        "schema_valid": schema_rep.valid,
        "schema_errors": schema_rep.errors,
        "examples": [
            {"label": f"example[{i}]", "valid": r.valid, "errors": r.errors}
            for i, r in enumerate(example_reps)
        ],
    }
    if instance_rep is not None:
        summary["instance"] = {"valid": instance_rep.valid, "errors": instance_rep.errors}

    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("=== tenant_policy_validator ===")
        print(f"  schema_valid: {schema_rep.valid}")
        for r in example_reps:
            print(f"  {r}")
        if instance_rep is not None:
            print(f"  instance: {instance_rep}")

    all_pass = schema_rep.valid and all(r.valid for r in example_reps) and (
        instance_rep is None or instance_rep.valid
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
