"""
catalogs_consistency_validator.py
参照仕様: 03_lint §3-2 (R1-R9)

CHK→MSG 紐付け、process body 内の ID 参照整合性を検証する。
R9: spec.sap_specifics.message_class ↔ catalogs.messages[].t100.class 一致検証。
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from basic_design_completeness_validator import (
    ValidationError, ValidationResult, ValidatorContext
)

CALC_PATTERN = re.compile(r"CALC-\d{2,3}")
CHK_PATTERN = re.compile(r"CHK-\d{2,3}")
MSG_PATTERN = re.compile(r"MSG-\d{2,3}")


def _collect_ids(items: list[dict], key: str = "id") -> set[str]:
    return {item.get(key, "") for item in items if isinstance(item, dict)}


def _extract_refs(text: str, pattern: re.Pattern) -> set[str]:
    return set(pattern.findall(text))


def validate_catalogs_consistency(
    context: ValidatorContext,
) -> ValidationResult:
    result = ValidationResult()
    bd = context.basic_design
    bd_file = str(context.feature_dir / "basic_design.md")

    catalogs = bd.get("catalogs", {})
    calcs = catalogs.get("calculations", [])
    checks = catalogs.get("checks", [])
    messages = catalogs.get("messages", [])
    processes = bd.get("process_definitions", [])
    objects = bd.get("object_definitions", {})

    calc_ids = _collect_ids(calcs)
    chk_ids = _collect_ids(checks)
    msg_ids = _collect_ids(messages)

    # Track referenced IDs for orphan detection (R6)
    all_referenced: set[str] = set()

    # R1-R3: process body references
    for proc in processes:
        body = proc.get("body", "")
        if not body:
            continue

        for ref in _extract_refs(body, CALC_PATTERN):
            all_referenced.add(ref)
            if ref not in calc_ids:
                result.errors.append(ValidationError(
                    code="CATALOG_REF_MISSING",
                    message=f"Process '{proc.get('id','?')}' body references {ref} but it's not in catalogs.calculations",
                    severity="ERROR", file=bd_file,
                    suggestion=f"Add {ref} to catalogs.calculations or fix the reference",
                ))

        for ref in _extract_refs(body, CHK_PATTERN):
            all_referenced.add(ref)
            if ref not in chk_ids:
                result.errors.append(ValidationError(
                    code="CATALOG_REF_MISSING",
                    message=f"Process '{proc.get('id','?')}' body references {ref} but it's not in catalogs.checks",
                    severity="ERROR", file=bd_file,
                    suggestion=f"Add {ref} to catalogs.checks or fix the reference",
                ))

        for ref in _extract_refs(body, MSG_PATTERN):
            all_referenced.add(ref)
            if ref not in msg_ids:
                result.errors.append(ValidationError(
                    code="CATALOG_REF_MISSING",
                    message=f"Process '{proc.get('id','?')}' body references {ref} but it's not in catalogs.messages",
                    severity="ERROR", file=bd_file,
                    suggestion=f"Add {ref} to catalogs.messages or fix the reference",
                ))

    # R4-R5: object field references
    for obj_type, obj_list in objects.items():
        if not isinstance(obj_list, list):
            continue
        for obj in obj_list:
            if not isinstance(obj, dict):
                continue
            for block in obj.get("blocks", []):
                for fld in block.get("fields", []):
                    calc_ref = fld.get("calc_ref")
                    if calc_ref and calc_ref not in calc_ids:
                        all_referenced.add(calc_ref)
                        result.errors.append(ValidationError(
                            code="CATALOG_REF_MISSING",
                            message=f"Field '{fld.get('id','?')}' calc_ref={calc_ref} not in catalogs.calculations",
                            severity="ERROR", file=bd_file,
                        ))
                    elif calc_ref:
                        all_referenced.add(calc_ref)

    # checks[].message_ref → messages
    for chk in checks:
        msg_ref = chk.get("message_ref", "")
        if msg_ref:
            all_referenced.add(msg_ref)
            if msg_ref not in msg_ids:
                result.errors.append(ValidationError(
                    code="CATALOG_REF_MISSING",
                    message=f"Check '{chk.get('id','?')}' message_ref={msg_ref} not in catalogs.messages",
                    severity="ERROR", file=bd_file,
                ))

    # R6: orphan detection
    for calc in calcs:
        cid = calc.get("id", "")
        if cid and cid not in all_referenced:
            result.warnings.append(ValidationError(
                code="CATALOG_ORPHAN",
                message=f"Calculation {cid} is not referenced by any process or object",
                severity="WARNING", file=bd_file,
            ))
    for chk in checks:
        cid = chk.get("id", "")
        if cid and cid not in all_referenced:
            result.warnings.append(ValidationError(
                code="CATALOG_ORPHAN",
                message=f"Check {cid} is not referenced by any process",
                severity="WARNING", file=bd_file,
            ))

    # R7: BAPI / DB_WRITE success log message check
    # processes with BAPI/DB_WRITE tags must have a corresponding success message
    success_msg_ids: set[str] = set()
    for msg in messages:
        mtype = msg.get("type", "")
        if mtype == "success":
            success_msg_ids.add(msg.get("id", ""))

    for proc in processes:
        body = proc.get("body", "")
        if not body:
            continue
        has_write = ("BAPI" in body or "DB_WRITE" in body.upper()
                     or "INSERT" in body.upper() or "UPDATE" in body.upper()
                     or "COMMIT" in body.upper())
        if has_write:
            # Check if process references at least one success message
            body_msg_refs = _extract_refs(body, MSG_PATTERN)
            has_success = any(ref in success_msg_ids for ref in body_msg_refs)
            if not has_success:
                result.warnings.append(ValidationError(
                    code="CATALOG_SUCCESS_MSG_MISSING",
                    message=f"Process '{proc.get('id','?')}' has BAPI/DB_WRITE but no success message reference",
                    severity="WARNING", file=bd_file,
                    suggestion="Add a type:'success' message to catalogs.messages and reference it in the process body",
                ))

    # R8: spec message_mapping type match (if spec available)
    if context.spec:
        msg_mapping = context.spec.get("message_mapping", [])
        msg_type_map = {m.get("id", ""): m.get("type", "") for m in messages}
        for mapping in msg_mapping:
            mid = mapping.get("id", "")
            mtype = mapping.get("type", "")
            if mid in msg_type_map and mtype and msg_type_map[mid]:
                if mtype != msg_type_map[mid]:
                    result.errors.append(ValidationError(
                        code="CATALOG_REF_MISSING",
                        message=f"spec message_mapping type '{mtype}' for {mid} doesn't match catalogs.messages type '{msg_type_map[mid]}'",
                        severity="ERROR", file=bd_file,
                    ))

    # R9: spec.sap_specifics.message_class ↔ catalogs.messages[].t100.class
    if context.spec:
        spec_msg_class = context.spec.get("sap_specifics", {}).get("message_class", "")
        if spec_msg_class and messages:
            for msg in messages:
                t100 = msg.get("t100", {})
                t100_class = t100.get("class", "") if isinstance(t100, dict) else ""
                if t100_class and t100_class != spec_msg_class:
                    result.errors.append(ValidationError(
                        code="CATALOG_MSG_CLASS_MISMATCH",
                        message=(
                            f"catalogs.messages '{msg.get('id','?')}' t100.class='{t100_class}' "
                            f"doesn't match spec.sap_specifics.message_class='{spec_msg_class}'"
                        ),
                        severity="ERROR", file=bd_file,
                        suggestion=f"Align t100.class to '{spec_msg_class}' or update spec.sap_specifics.message_class",
                    ))

    return result
