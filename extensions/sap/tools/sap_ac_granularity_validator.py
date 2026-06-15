"""
sap_ac_granularity_validator.py
参照仕様: 03_lint §3-6

AC の catalog_refs カバレッジ（全 CHK/CALC/FILE/IF → AC）+ 独立性検証。
MASTER_CHECK_NOT_COVERED / PARTIAL_FETCH_NOT_COVERED を含む。
"""

import re
from basic_design_completeness_validator import (
    ValidationError, ValidationResult, ValidatorContext
)


def _collect_catalog_ids(bd: dict) -> set[str]:
    """Collect all catalog IDs that need AC coverage."""
    ids: set[str] = set()
    catalogs = bd.get("catalogs", {})
    for chk in catalogs.get("checks", []):
        if chk.get("id"):
            ids.add(chk["id"])
    for calc in catalogs.get("calculations", []):
        if calc.get("id"):
            ids.add(calc["id"])
    objects = bd.get("object_definitions", {})
    for f in objects.get("files", []):
        if f.get("id"):
            ids.add(f["id"])
    for i in objects.get("interfaces", []):
        if i.get("id"):
            ids.add(i["id"])
    return ids


def _collect_ac_catalog_refs(spec: dict) -> dict[str, list[str]]:
    """Collect AC → catalog_refs mapping from spec."""
    ac_refs: dict[str, list[str]] = {}
    for uc in spec.get("use_cases", []):
        for ac in uc.get("acceptance", []):
            ac_id = ac.get("id", "")
            refs = ac.get("catalog_refs", [])
            if ac_id:
                ac_refs[ac_id] = refs if isinstance(refs, list) else []
    return ac_refs


def validate_sap_ac_granularity(
    context: ValidatorContext,
) -> ValidationResult:
    result = ValidationResult()
    if not context.spec:
        return result

    bd = context.basic_design
    spec = context.spec
    spec_file = str(context.feature_dir / "spec.md")

    catalog_ids = _collect_catalog_ids(bd)
    ac_refs = _collect_ac_catalog_refs(spec)

    # Collect all covered catalog IDs
    covered_ids: set[str] = set()
    for ac_id, refs in ac_refs.items():
        covered_ids.update(refs)

    # Coverage check: each catalog ID must be covered by >= 1 AC
    for cid in catalog_ids:
        if cid not in covered_ids:
            result.errors.append(ValidationError(
                code="CATALOG_ITEM_NOT_COVERED",
                message=f"Catalog item {cid} is not covered by any AC's catalog_refs",
                severity="ERROR", file=spec_file,
                suggestion=f"Add {cid} to an AC's catalog_refs in spec.md",
            ))

    # catalog_refs field requirement
    for uc in spec.get("use_cases", []):
        for ac in uc.get("acceptance", []):
            ac_id = ac.get("id", "")
            if "catalog_refs" not in ac:
                result.errors.append(ValidationError(
                    code="CATALOG_REFS_MISSING",
                    message=f"AC {ac_id} is missing catalog_refs field",
                    severity="ERROR", file=spec_file,
                    suggestion=f"Add catalog_refs: [] to AC {ac_id}",
                ))

    # Independence check: no single AC has multiple independent items from same category
    chk_ids = {c.get("id", "") for c in bd.get("catalogs", {}).get("checks", [])}
    calc_ids = {c.get("id", "") for c in bd.get("catalogs", {}).get("calculations", [])}
    for ac_id, refs in ac_refs.items():
        chk_count = sum(1 for r in refs if r in chk_ids)
        calc_count = sum(1 for r in refs if r in calc_ids)
        if chk_count > 1:
            result.errors.append(ValidationError(
                code="AC_OVER_MERGED",
                message=f"AC {ac_id} contains {chk_count} independent checks — split required",
                severity="ERROR", file=spec_file,
                suggestion=f"Split AC {ac_id} into separate ACs for each check",
            ))
        if calc_count > 1:
            result.errors.append(ValidationError(
                code="AC_OVER_MERGED",
                message=f"AC {ac_id} contains {calc_count} independent calculations — split required",
                severity="ERROR", file=spec_file,
            ))

    # MASTER_CHECK_NOT_COVERED: DB_READ with table → existence check required
    processes = bd.get("process_definitions", [])
    checks = bd.get("catalogs", {}).get("checks", [])
    exist_check_tables: set[str] = set()
    for chk in checks:
        condition = chk.get("condition", "")
        if "存在" in condition or "EXIST" in condition.upper():
            # Extract table refs from the check
            data_refs = bd.get("database", {}).get("data_references", [])
            for dr in data_refs:
                exist_check_tables.update(dr.get("tables", []))

    for proc in processes:
        body = proc.get("body", "")
        if "DB_READ" in body or "SELECT" in body.upper():
            data_refs = bd.get("database", {}).get("data_references", [])
            for dr in data_refs:
                for table in dr.get("tables", []):
                    if table and table not in exist_check_tables:
                        result.warnings.append(ValidationError(
                            code="MASTER_CHECK_NOT_COVERED",
                            message=f"Table {table} read in process but no existence check defined",
                            severity="WARNING", file=spec_file,
                            suggestion=f"Add existence check for {table} in catalogs.checks",
                        ))

    # PARTIAL_FETCH_NOT_COVERED: multi-step DB_READ chains where later step
    # depends on earlier results (e.g., FOR ALL ENTRIES, IN gt_*)
    partial_fetch_pattern = re.compile(
        r"(?:FOR\s+ALL\s+ENTRIES|IN\s+gt_|IN\s+lt_|INNER\s+JOIN)",
        re.IGNORECASE,
    )
    db_read_procs: list[dict] = []
    for proc in processes:
        body = proc.get("body", "")
        if "DB_READ" in body or "SELECT" in body.upper():
            db_read_procs.append(proc)

    if len(db_read_procs) >= 2:
        for proc in db_read_procs:
            body = proc.get("body", "")
            if partial_fetch_pattern.search(body):
                proc_id = proc.get("id", "?")
                # Check if there's a corresponding "partial result" scenario/check
                has_partial_check = False
                for chk in checks:
                    cond = chk.get("condition", "")
                    if ("部分" in cond or "partial" in cond.lower()
                            or "0件" in cond or "empty" in cond.lower()):
                        has_partial_check = True
                        break
                if not has_partial_check:
                    result.warnings.append(ValidationError(
                        code="PARTIAL_FETCH_NOT_COVERED",
                        message=f"Process {proc_id} uses dependent DB_READ (FOR ALL ENTRIES/JOIN) but no partial-result check exists",
                        severity="WARNING", file=spec_file,
                        suggestion="Add a check for partial/empty result in catalogs.checks (e.g., 'first query found, dependent query empty')",
                    ))

    return result
