"""
sap_ddic_gate_validator.py
参照仕様: 03_lint §3-5 (R1-R3)

database.data_references[].tables の存在確認 + 重複検出。
"""

from basic_design_completeness_validator import (
    ValidationError, ValidationResult, ValidatorContext
)


def validate_sap_ddic_gate(
    context: ValidatorContext,
) -> ValidationResult:
    result = ValidationResult()
    bd = context.basic_design
    bd_file = str(context.feature_dir / "basic_design.md")

    data_refs = bd.get("database", {}).get("data_references", [])
    if not data_refs:
        return result

    all_tables: list[tuple[str, int, int]] = []  # (table_name, ref_idx, table_idx)

    for i, ref in enumerate(data_refs):
        ref_id = ref.get("id", f"data_references[{i}]")
        tables = ref.get("tables", [])
        if not isinstance(tables, list):
            continue

        for j, table in enumerate(tables):
            # R1: table name non-empty
            if not table or (isinstance(table, str) and not table.strip()):
                result.errors.append(ValidationError(
                    code="DDIC_TABLE_EMPTY",
                    message=f"database.data_references[{i}].tables[{j}] のテーブル名が空です",
                    severity="ERROR", file=bd_file,
                    suggestion=f"Set a valid table name for {ref_id}.tables[{j}]",
                ))
            else:
                all_tables.append((table, i, j))

    # R2: duplicate detection
    table_counts: dict[str, int] = {}
    for table_name, _, _ in all_tables:
        table_counts[table_name] = table_counts.get(table_name, 0) + 1

    for table_name, count in table_counts.items():
        if count > 1:
            result.warnings.append(ValidationError(
                code="DDIC_TABLE_DUPLICATE",
                message=f'テーブル "{table_name}" が database.data_references 内で重複しています（{count}件）',
                severity="WARNING", file=bd_file,
                suggestion=f"Remove duplicate references to {table_name}",
            ))

    # R3: SAP DDIC existence check (Phase 2 前準備 only)
    if context.sap_connection:
        # SAP online check would go here (DD02L lookup)
        pass

    return result
