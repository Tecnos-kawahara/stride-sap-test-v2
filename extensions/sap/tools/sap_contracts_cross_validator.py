"""
sap_contracts_cross_validator.py
参照仕様: 03_lint §3 拡張 (CX-01〜CX-05)

contracts/ ファイルと basic_design / spec のクロスファイル整合性を検証する。
CX-01: selection_screen.yaml fields ↔ basic_design.object_definitions.screens[].blocks[].fields[]
CX-02: report_output.yaml columns ↔ basic_design.object_definitions.reports[].columns[]
CX-03: database_schema.yaml tables ↔ basic_design.database.data_references[].tables[]
CX-04: authz_matrix.yaml authorization_objects ↔ spec.sap_specifics.authorization_objects
CX-05: selection_screen.yaml validation_ref ↔ catalogs.checks[].id
"""

import yaml

from basic_design_completeness_validator import (
    ValidationError, ValidationResult, ValidatorContext
)


def validate_contracts_cross(
    context: ValidatorContext,
) -> ValidationResult:
    result = ValidationResult()
    bd = context.basic_design
    spec = context.spec or {}
    feature_dir = context.feature_dir

    # ── CX-01: selection_screen.yaml ↔ basic_design screens ──

    ss_path = feature_dir / "contracts" / "selection_screen.yaml"
    if ss_path.exists():
        try:
            ss_data = yaml.safe_load(ss_path.read_text(encoding="utf-8"))
        except Exception:
            ss_data = None

        if isinstance(ss_data, dict):
            ss_fields: dict[str, dict] = {}
            for screen in ss_data.get("screens", []):
                for fld in screen.get("fields", []):
                    tname = fld.get("technical_name", "")
                    if tname:
                        ss_fields[tname] = fld

            # Collect basic_design fields
            bd_fields: dict[str, dict] = {}
            for screen in bd.get("object_definitions", {}).get("screens", []):
                for block in screen.get("blocks", []):
                    for fld in block.get("fields", []):
                        fname = fld.get("name", "")
                        if fname:
                            bd_fields[fname] = fld

            # Cross-check: contract fields must exist in basic_design (by name matching)
            # Build a name↔technical_name map from plan.selection_fields or contract itself
            for tname, ss_fld in ss_fields.items():
                field_name = ss_fld.get("name", "")
                if field_name and field_name not in bd_fields:
                    result.errors.append(ValidationError(
                        code="CX_SCREEN_FIELD_NOT_IN_BD",
                        message=(
                            f"selection_screen.yaml field '{field_name}' ({tname}) "
                            f"not found in basic_design.object_definitions.screens[].blocks[].fields[]"
                        ),
                        severity="ERROR",
                        file=str(ss_path),
                    ))
                elif field_name and field_name in bd_fields:
                    bd_fld = bd_fields[field_name]
                    # required flag check
                    ss_req = ss_fld.get("required")
                    bd_req = bd_fld.get("required")
                    if ss_req is not None and bd_req is not None and ss_req != bd_req:
                        result.errors.append(ValidationError(
                            code="CX_SCREEN_FIELD_REQUIRED_MISMATCH",
                            message=(
                                f"selection_screen.yaml '{field_name}' required={ss_req} "
                                f"but basic_design says required={bd_req}"
                            ),
                            severity="ERROR",
                            file=str(ss_path),
                        ))

            # Reverse: basic_design fields must exist in contract
            for fname in bd_fields:
                if not any(f.get("name") == fname for f in ss_fields.values()):
                    result.errors.append(ValidationError(
                        code="CX_BD_FIELD_NOT_IN_CONTRACT",
                        message=(
                            f"basic_design screen field '{fname}' "
                            f"not found in selection_screen.yaml"
                        ),
                        severity="ERROR",
                        file=str(ss_path),
                    ))

            # CX-05: validation_ref → catalogs.checks
            chk_ids: set[str] = set()
            for chk in bd.get("catalogs", {}).get("checks", []):
                cid = chk.get("id", "")
                if cid:
                    chk_ids.add(cid)

            for tname, ss_fld in ss_fields.items():
                vref = ss_fld.get("validation_ref", "")
                if vref and vref not in chk_ids:
                    result.errors.append(ValidationError(
                        code="CX_VALIDATION_REF_NOT_IN_CATALOGS",
                        message=(
                            f"selection_screen.yaml '{tname}' validation_ref='{vref}' "
                            f"not found in catalogs.checks"
                        ),
                        severity="ERROR",
                        file=str(ss_path),
                        suggestion=f"Add {vref} to catalogs.checks or fix the reference",
                    ))

    # ── CX-02: report_output.yaml ↔ basic_design reports ──

    rpt_path = feature_dir / "contracts" / "report_output.yaml"
    if rpt_path.exists():
        try:
            rpt_data = yaml.safe_load(rpt_path.read_text(encoding="utf-8"))
        except Exception:
            rpt_data = None

        if isinstance(rpt_data, dict):
            # Collect contract columns by fieldname
            rpt_cols: dict[str, dict] = {}
            for report in rpt_data.get("reports", []):
                for col in report.get("columns", []):
                    fname = col.get("fieldname", "")
                    if fname:
                        rpt_cols[fname] = col

            # Collect basic_design report columns
            bd_cols: dict[str, dict] = {}
            for report in bd.get("object_definitions", {}).get("reports", []):
                for col in report.get("columns", []):
                    # basic_design uses "name" for display name; match via column
                    # position or via a field mapping. Use column id's field attr
                    # if present, otherwise name.
                    # The yaml has field= VBELN etc., BD may not have field directly
                    # but the column order and name should correspond.
                    col_name = col.get("name", "")
                    if col_name:
                        bd_cols[col_name] = col

            # Build fieldname↔display_name map from contract
            for fieldname, rpt_col in rpt_cols.items():
                col_text = rpt_col.get("column_text", "")
                if col_text and col_text not in bd_cols:
                    result.errors.append(ValidationError(
                        code="CX_REPORT_COL_NOT_IN_BD",
                        message=(
                            f"report_output.yaml column '{fieldname}' (column_text='{col_text}') "
                            f"not found in basic_design.object_definitions.reports[].columns[] by name"
                        ),
                        severity="ERROR",
                        file=str(rpt_path),
                    ))
                elif col_text and col_text in bd_cols:
                    bd_col = bd_cols[col_text]
                    # key flag check
                    rpt_key = rpt_col.get("key")
                    bd_key = bd_col.get("key")
                    if rpt_key is not None and bd_key is not None and rpt_key != bd_key:
                        result.errors.append(ValidationError(
                            code="CX_REPORT_COL_KEY_MISMATCH",
                            message=(
                                f"report_output.yaml '{fieldname}' key={rpt_key} "
                                f"but basic_design says key={bd_key}"
                            ),
                            severity="ERROR",
                            file=str(rpt_path),
                        ))

            # Reverse: BD columns must exist in contract
            for col_name in bd_cols:
                if not any(c.get("column_text") == col_name for c in rpt_cols.values()):
                    result.errors.append(ValidationError(
                        code="CX_BD_COL_NOT_IN_CONTRACT",
                        message=(
                            f"basic_design report column '{col_name}' "
                            f"not found in report_output.yaml"
                        ),
                        severity="ERROR",
                        file=str(rpt_path),
                    ))

    # ── CX-03: database_schema.yaml ↔ basic_design data_references ──

    db_path = feature_dir / "contracts" / "database_schema.yaml"
    if db_path.exists():
        try:
            db_data = yaml.safe_load(db_path.read_text(encoding="utf-8"))
        except Exception:
            db_data = None

        if isinstance(db_data, dict):
            tables = db_data.get("tables", {})
            contract_tables: set[str] = set()
            for tbl in tables.get("custom_tables", []):
                name = tbl.get("name", "") if isinstance(tbl, dict) else ""
                if name:
                    contract_tables.add(name)
            for tbl in tables.get("referenced_tables", []):
                name = tbl.get("name", "") if isinstance(tbl, dict) else ""
                if name:
                    contract_tables.add(name)

            # Collect basic_design tables
            bd_tables: set[str] = set()
            for dref in bd.get("database", {}).get("data_references", []):
                for tbl in dref.get("tables", []):
                    if isinstance(tbl, str) and tbl:
                        bd_tables.add(tbl)

            # Contract tables not in BD
            for tbl in contract_tables - bd_tables:
                result.errors.append(ValidationError(
                    code="CX_DB_TABLE_NOT_IN_BD",
                    message=(
                        f"database_schema.yaml table '{tbl}' "
                        f"not found in basic_design.database.data_references[].tables[]"
                    ),
                    severity="ERROR",
                    file=str(db_path),
                ))

            # BD tables not in contract
            for tbl in bd_tables - contract_tables:
                result.errors.append(ValidationError(
                    code="CX_BD_TABLE_NOT_IN_CONTRACT",
                    message=(
                        f"basic_design data_references table '{tbl}' "
                        f"not found in database_schema.yaml"
                    ),
                    severity="ERROR",
                    file=str(db_path),
                ))

    # ── CX-04: authz_matrix.yaml ↔ spec.sap_specifics.authorization_objects ──

    authz_path = feature_dir / "implementation-details" / "authz_matrix.yaml"
    if authz_path.exists() and spec:
        try:
            authz_data = yaml.safe_load(authz_path.read_text(encoding="utf-8"))
        except Exception:
            authz_data = None

        if isinstance(authz_data, dict):
            # Collect authz_matrix objects
            matrix_objects: set[str] = set()
            for obj in authz_data.get("authorization_objects", []):
                oname = obj.get("object", "")
                if oname:
                    matrix_objects.add(oname)

            # Collect spec sap_specifics objects
            spec_objects: set[str] = set()
            for obj in spec.get("sap_specifics", {}).get("authorization_objects", []):
                oname = obj.get("object", "")
                if oname:
                    spec_objects.add(oname)

            # Matrix objects not in spec
            for obj in matrix_objects - spec_objects:
                result.errors.append(ValidationError(
                    code="CX_AUTHZ_NOT_IN_SPEC",
                    message=(
                        f"authz_matrix.yaml object '{obj}' "
                        f"not found in spec.sap_specifics.authorization_objects"
                    ),
                    severity="ERROR",
                    file=str(authz_path),
                ))

            # Spec objects not in matrix
            for obj in spec_objects - matrix_objects:
                result.errors.append(ValidationError(
                    code="CX_SPEC_AUTHZ_NOT_IN_MATRIX",
                    message=(
                        f"spec.sap_specifics authorization object '{obj}' "
                        f"not found in authz_matrix.yaml"
                    ),
                    severity="ERROR",
                    file=str(authz_path),
                ))

    return result
