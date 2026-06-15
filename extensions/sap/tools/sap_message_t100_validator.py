"""
sap_message_t100_validator.py
参照仕様: 03_lint §3-4 (R1-R5)

T100 メッセージクラス/番号の形式検証 + ステータス値セット検証。
VALID_STATUSES = {"ok", "empty"} — registered/unregistered/pending は旧仕様で使用禁止。
"""

from basic_design_completeness_validator import (
    ValidationError, ValidationResult, ValidatorContext
)

# §3-4 修正後の正しい値セット
VALID_STATUSES = {"ok", "empty"}


def validate_sap_message_t100(
    context: ValidatorContext,
) -> ValidationResult:
    result = ValidationResult()
    bd = context.basic_design
    bd_file = str(context.feature_dir / "basic_design.md")

    messages = bd.get("catalogs", {}).get("messages", [])
    if not messages:
        return result

    for i, msg in enumerate(messages):
        msg_id = msg.get("id", f"messages[{i}]")
        t100 = msg.get("t100", {})
        if not isinstance(t100, dict):
            continue

        # R1: class non-empty
        t100_class = t100.get("class")
        if not t100_class:
            result.errors.append(ValidationError(
                code="T100_CLASS_MISSING",
                message=f"{msg_id}: t100.class is empty or missing",
                severity="ERROR", file=bd_file,
                suggestion="Set t100.class to the T100 message class name",
            ))

        # R2: number non-empty (null allowed for unassigned)
        # number can be null (未引当) but must be present as key
        if "number" not in t100:
            result.errors.append(ValidationError(
                code="T100_NUMBER_MISSING",
                message=f"{msg_id}: t100.number key is missing",
                severity="ERROR", file=bd_file,
                suggestion="Set t100.number (null for 未引当)",
            ))

        # R3: status value check — must be "ok" or "empty"
        status = t100.get("status", "")
        if status and status not in VALID_STATUSES:
            result.errors.append(ValidationError(
                code="T100_STATUS_INVALID",
                message=f"{msg_id}: t100.status='{status}' is invalid. Must be 'ok' or 'empty'",
                severity="ERROR", file=bd_file,
                suggestion="Change t100.status to 'ok' (引当済) or 'empty' (未引当)",
            ))

        # R4: Empty warning — recommend SE91 registration
        if status == "empty":
            result.warnings.append(ValidationError(
                code="T100_EMPTY",
                message=f"{msg_id}: t100.status='empty' — SE91 でのメッセージ登録を推奨します",
                severity="WARNING", file=bd_file,
                suggestion="Register message in SE91 and set status to 'ok'",
            ))

        # R5: SAP T100 existence check (Phase 1.5 only)
        if context.sap_connection and t100_class and t100.get("number") is not None:
            # SAP online check would go here
            # For offline/mock: graceful skip
            pass

    return result
