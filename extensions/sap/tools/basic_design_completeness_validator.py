"""
basic_design_completeness_validator.py
参照仕様: 03_lint §3-1 (Level 1: 18 mapping + Level 2: field check + Level 3: cross-doc)
共通インターフェース: 03_lint §2 (ValidatorContext → ValidationResult)

yaml の全要素が basic_design.md に存在するか検証する。
L3-01: spec AC IDs → traceability_rows AC IDs 逆方向一致検証。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationError:
    code: str
    message: str
    severity: str  # "ERROR" | "WARNING"
    file: str
    line: int | None = None
    suggestion: str = ""


@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)


@dataclass
class ValidatorContext:
    feature_dir: Path
    basic_design: dict
    spec: dict | None = None
    plan: dict | None = None
    config: dict = field(default_factory=dict)
    sap_connection: Any = None
    source_yaml: dict | None = None  # parsed yaml spec


# ── Level 1: 18 mapping entries (03_lint §3-1, 04 §A-1 準拠) ──
# (yaml_path, basic_design_paths, description)
LEVEL1_MAPPINGS: list[tuple[str, list[str], str]] = [
    ("meta", ["front_matter"], "meta → front_matter"),
    ("businessSpec.context", ["context"], "businessSpec.context → context"),
    ("businessSpec.overview", ["scope", "bpmn_descriptions.process.purpose"],
     "businessSpec.overview → scope + bpmn_descriptions"),
    ("businessSpec.executionConditions",
     ["bpmn_descriptions.process", "business_requirements.performance"],
     "executionConditions → bpmn_descriptions + performance"),
    ("businessSpec.prerequisites", ["assumptions"],
     "prerequisites → assumptions"),
    ("businessSpec.users",
     ["raci_plus.actors", "bpmn_descriptions.process.primary_actors",
      "business_requirements.localization"],
     "users → raci_plus + bpmn + localization"),
    ("businessSpec.recovery",
     ["business_requirements.availability_reliability"],
     "recovery → availability_reliability"),
    ("businessSpec.businessValue", ["business_value"],
     "businessValue → business_value"),
    ("functionStructure",
     ["scope.in", "decisions", "integration_flows"],
     "functionStructure → scope.in + decisions + integration_flows"),
    ("header",
     ["front_matter", "sap_context", "bpmn_descriptions.process",
      "business_requirements.performance"],
     "header → front_matter + sap_context + bpmn + performance"),
    ("processes", ["process_definitions"],
     "processes → process_definitions"),
    ("calculations", ["catalogs.calculations"],
     "calculations → catalogs.calculations"),
    ("checks", ["catalogs.checks"],
     "checks → catalogs.checks"),
    ("messages", ["catalogs.messages"],
     "messages → catalogs.messages"),
    ("objects",
     ["object_definitions", "database.data_references"],
     "objects → object_definitions + database.data_references"),
    ("testMatrix", ["test_matrix"],
     "testMatrix → test_matrix"),
    ("devObjects", ["sap_context.dev_objects"],
     "devObjects → sap_context.dev_objects"),
    ("sapContext",
     ["sap_context", "systems"],
     "sapContext → sap_context + systems"),
]


# ── Level 2: field completeness (03_lint §3-1 Level 2) ──
# (basic_design section path, required fields when yaml has data)
LEVEL2_CHECKS: list[tuple[str, list[str]]] = [
    ("catalogs.checks[]",
     ["id", "category", "condition", "continue_processing",
      "data_handling", "message_ref", "priority"]),
    ("catalogs.calculations[]",
     ["id", "name", "inputs", "logic", "outputs"]),
    ("catalogs.messages[]",
     ["id", "type", "text", "t100.class", "t100.status"]),
    ("object_definitions.screens[]",
     ["id", "name", "kind"]),
    ("database.data_references[]",
     ["id", "name", "purpose", "tables"]),
    ("business_requirements.availability_reliability",
     ["recovery_method", "concurrency_constraint", "duplicate_prevention"]),
    ("sap_context",
     ["program_type", "program_id", "package", "namespace"]),
]

# ── Level 2-B: nested array checks (screens[].blocks[].fields[]) ──
LEVEL2_NESTED_CHECKS: list[tuple[str, str, list[str]]] = [
    ("object_definitions.screens[]", "blocks[].fields[]",
     ["id", "name", "type", "max_length", "input_method", "io", "required"]),
]


def _get_nested(data: dict, dotted_path: str) -> Any:
    """Resolve dotted path like 'a.b.c' in nested dict."""
    parts = dotted_path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _get_yaml_value(yaml_data: dict, dotted_path: str) -> Any:
    """Resolve a yaml path; supports top-level and nested."""
    return _get_nested(yaml_data, dotted_path)


def _is_present(value: Any) -> bool:
    """Check if a value is meaningfully present (not None, not empty)."""
    if value is None:
        return False
    if isinstance(value, (list, dict, str)) and len(value) == 0:
        return False
    return True


def _check_level1(
    yaml_data: dict, bd: dict, bd_file: str
) -> tuple[list[ValidationError], list[ValidationError]]:
    """Level 1: section existence check."""
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []

    for yaml_path, bd_paths, desc in LEVEL1_MAPPINGS:
        yaml_value = _get_yaml_value(yaml_data, yaml_path)
        if not _is_present(yaml_value):
            continue  # optional — yaml doesn't have data, skip

        for bd_path in bd_paths:
            bd_value = _get_nested(bd, bd_path)
            section_name = bd_path.replace(".", "_").upper()

            if bd_value is None:
                errors.append(ValidationError(
                    code=f"BD_COMPLETENESS_MISSING_{section_name}",
                    message=f"yaml.{yaml_path} has data but basic_design.{bd_path} is missing ({desc})",
                    severity="ERROR",
                    file=bd_file,
                    suggestion=f"Add {bd_path} section to basic_design per 04 §A-1 mapping",
                ))
            elif not _is_present(bd_value):
                warnings.append(ValidationError(
                    code=f"BD_COMPLETENESS_EMPTY_{section_name}",
                    message=f"basic_design.{bd_path} exists but is empty ({desc})",
                    severity="WARNING",
                    file=bd_file,
                    suggestion=f"Fill in {bd_path} from yaml.{yaml_path}",
                ))

    return errors, warnings


def _check_level2(
    bd: dict, bd_file: str
) -> list[ValidationError]:
    """Level 2: field-level completeness within sections."""
    errors: list[ValidationError] = []

    for section_spec, required_fields in LEVEL2_CHECKS:
        if section_spec.endswith("[]"):
            # Array section: check each item
            base_path = section_spec[:-2]
            items = _get_nested(bd, base_path)
            if not isinstance(items, list) or not items:
                continue
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                for fld in required_fields:
                    if "." in fld:
                        # nested field like t100.class
                        val = _get_nested(item, fld)
                    else:
                        val = item.get(fld)
                    if val is None:
                        sec = base_path.replace(".", "_").upper()
                        fld_code = fld.replace(".", "_").upper()
                        errors.append(ValidationError(
                            code=f"BD_COMPLETENESS_MISSING_FIELD_{sec}_{fld_code}",
                            message=f"basic_design.{base_path}[{i}].{fld} is missing",
                            severity="ERROR",
                            file=bd_file,
                            suggestion=f"Add field '{fld}' to {base_path}[{i}]",
                        ))
        else:
            # Scalar section: check directly
            section = _get_nested(bd, section_spec)
            if not isinstance(section, dict) or not section:
                continue
            for fld in required_fields:
                val = section.get(fld)
                if val is None:
                    sec = section_spec.replace(".", "_").upper()
                    fld_code = fld.upper()
                    errors.append(ValidationError(
                        code=f"BD_COMPLETENESS_MISSING_FIELD_{sec}_{fld_code}",
                        message=f"basic_design.{section_spec}.{fld} is missing",
                        severity="ERROR",
                        file=bd_file,
                        suggestion=f"Add field '{fld}' to {section_spec}",
                    ))

    # Level 2-B: nested array checks (e.g., screens[].blocks[].fields[])
    for parent_spec, nested_spec, required_fields in LEVEL2_NESTED_CHECKS:
        parent_path = parent_spec[:-2]  # strip "[]"
        parent_items = _get_nested(bd, parent_path)
        if not isinstance(parent_items, list):
            continue
        # Parse nested_spec: "blocks[].fields[]"
        nested_parts = nested_spec.split("[].")
        for pi, parent_item in enumerate(parent_items):
            if not isinstance(parent_item, dict):
                continue
            # Navigate nested: blocks → fields
            mid_key = nested_parts[0].rstrip("[]")
            leaf_key = nested_parts[1].rstrip("[]") if len(nested_parts) > 1 else None
            mid_items = parent_item.get(mid_key, [])
            if not isinstance(mid_items, list):
                continue
            for bi, block in enumerate(mid_items):
                if not isinstance(block, dict):
                    continue
                leaf_items = block.get(leaf_key, []) if leaf_key else [block]
                if not isinstance(leaf_items, list):
                    continue
                for fi, leaf in enumerate(leaf_items):
                    if not isinstance(leaf, dict):
                        continue
                    for fld in required_fields:
                        if leaf.get(fld) is None:
                            sec = parent_path.replace(".", "_").upper()
                            errors.append(ValidationError(
                                code=f"BD_COMPLETENESS_MISSING_FIELD_{sec}_BLOCKS_FIELDS_{fld.upper()}",
                                message=f"basic_design.{parent_path}[{pi}].{mid_key}[{bi}].{leaf_key}[{fi}].{fld} is missing",
                                severity="ERROR",
                                file=bd_file,
                                suggestion=f"Add field '{fld}' to {parent_path}[{pi}].{mid_key}[{bi}].{leaf_key}[{fi}]",
                            ))

    return errors


def validate_basic_design_completeness(
    context: ValidatorContext,
) -> ValidationResult:
    """
    Main entry point.
    Validates that all yaml elements are present in basic_design.
    """
    result = ValidationResult()
    bd = context.basic_design
    bd_file = str(context.feature_dir / "basic_design.md")
    yaml_data = context.source_yaml or {}

    if not bd:
        result.errors.append(ValidationError(
            code="BD_COMPLETENESS_NO_BASIC_DESIGN",
            message="basic_design is empty or not parsed",
            severity="ERROR",
            file=bd_file,
            suggestion="Ensure basic_design.md has valid #0 YAML canonical section",
        ))
        return result

    if not yaml_data:
        # If no yaml source provided, skip Level 1 (can only do Level 2)
        pass
    else:
        # Level 1: section existence
        l1_errors, l1_warnings = _check_level1(yaml_data, bd, bd_file)
        result.errors.extend(l1_errors)
        result.warnings.extend(l1_warnings)

    # Level 2: field completeness
    l2_errors = _check_level2(bd, bd_file)
    result.errors.extend(l2_errors)

    # Level 3: cross-document consistency

    # L3-01: spec AC IDs → traceability_rows AC IDs (reverse direction)
    # stride_lint already checks forward (traceability → spec).
    # This checks reverse: every AC in spec must appear in traceability_rows.
    if context.spec:
        spec_ac_ids: set[str] = set()
        for uc in context.spec.get("use_cases", []):
            for ac in uc.get("acceptance", []):
                ac_id = ac.get("id", "")
                if ac_id:
                    spec_ac_ids.add(ac_id)

        tr_ac_ids: set[str] = set()
        for row in bd.get("traceability_rows", []):
            ac_section = row.get("ac", {})
            ac_id = ac_section.get("id", "") if isinstance(ac_section, dict) else ""
            if ac_id:
                tr_ac_ids.add(ac_id)

        if spec_ac_ids and tr_ac_ids:
            for ac_id in spec_ac_ids - tr_ac_ids:
                result.warnings.append(ValidationError(
                    code="BD_AC_NOT_IN_TRACEABILITY",
                    message=(
                        f"spec AC '{ac_id}' not found in "
                        f"basic_design.traceability_rows[].ac.id"
                    ),
                    severity="WARNING",
                    file=bd_file,
                    suggestion=f"Add a traceability_row for {ac_id}",
                ))

    return result
