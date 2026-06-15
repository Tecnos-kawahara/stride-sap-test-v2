"""
plan_quality_validator.py
参照仕様: 03_lint §3-7 (PQ-01〜PQ-15)

plan.md 品質検証。PQ-09: test_matrix 全件カバレッジを含む。
PQ-10: scenarios.yaml test_suite.feature_id の front matter 一致検証。
PQ-11〜15: plan SAP fields ↔ basic_design クロスファイル整合性。
test_matrix はマトリクス形式（columns + test_cases）固定、test_cases[].id は数値型。
"""

import yaml

from basic_design_completeness_validator import (
    ValidationError, ValidationResult, ValidatorContext
)


def validate_plan_quality(
    context: ValidatorContext,
) -> ValidationResult:
    result = ValidationResult()
    if not context.plan:
        return result

    plan = context.plan
    spec = context.spec or {}
    bd = context.basic_design
    plan_file = str(context.feature_dir / "plan.md")

    scenarios = plan.get("scenarios", [])

    # PQ-01: covers_ts format — ac_id + verification_method required
    for i, sc in enumerate(scenarios):
        for j, cts in enumerate(sc.get("covers_ts", [])):
            if not cts.get("ac_id"):
                result.errors.append(ValidationError(
                    code="PQ_COVERS_TS_MISSING_AC_ID",
                    message=f"scenarios[{i}].covers_ts[{j}] missing ac_id",
                    severity="ERROR", file=plan_file,
                ))
            if not cts.get("verification_method"):
                result.errors.append(ValidationError(
                    code="PQ_COVERS_TS_MISSING_METHOD",
                    message=f"scenarios[{i}].covers_ts[{j}] missing verification_method",
                    severity="ERROR", file=plan_file,
                ))

    # PQ-02: tests[].covers_acceptance_ids required
    for i, test in enumerate(plan.get("tests", [])):
        if not test.get("covers_acceptance_ids"):
            result.errors.append(ValidationError(
                code="PQ_TS_MISSING_COVERS",
                message=f"tests[{i}] missing covers_acceptance_ids",
                severity="ERROR", file=plan_file,
            ))

    # PQ-03: bidirectional coverage TS↔scenario
    all_scenario_ac_ids: set[str] = set()
    for sc in scenarios:
        for cts in sc.get("covers_ts", []):
            ac_id = cts.get("ac_id", "")
            if ac_id:
                all_scenario_ac_ids.add(ac_id)

    for i, test in enumerate(plan.get("tests", [])):
        for ac_id in test.get("covers_acceptance_ids", []):
            if ac_id and ac_id not in all_scenario_ac_ids:
                result.warnings.append(ValidationError(
                    code="PQ_TS_AC_NOT_IN_SCENARIO",
                    message=f"tests[{i}] covers AC '{ac_id}' but no scenario covers it",
                    severity="WARNING", file=plan_file,
                ))

    # PQ-04: covers_ts path filter — only ACs from steps the scenario traverses
    for i, sc in enumerate(scenarios):
        steps = sc.get("steps", [])
        if not steps:
            continue
        # Collect all catalog/AC refs reachable from this scenario's steps
        step_ac_refs: set[str] = set()
        for step in steps:
            for ref in step.get("catalog_refs", []):
                step_ac_refs.add(ref)
            for ref in step.get("ac_refs", []):
                step_ac_refs.add(ref)
        if not step_ac_refs:
            continue
        # Check that covers_ts only references ACs that appear in traversed steps
        for j, cts in enumerate(sc.get("covers_ts", [])):
            ac_id = cts.get("ac_id", "")
            if ac_id and step_ac_refs and ac_id not in step_ac_refs:
                result.warnings.append(ValidationError(
                    code="PQ_COVERS_TS_WRONG_PATH",
                    message=f"scenarios[{i}].covers_ts[{j}].ac_id='{ac_id}' is not reachable from scenario steps",
                    severity="WARNING", file=plan_file,
                    suggestion=f"Remove {ac_id} from covers_ts or add the step that covers it",
                ))

    # PQ-05: e2e AC full coverage
    e2e_ac_ids: set[str] = set()
    for uc in spec.get("use_cases", []):
        for ac in uc.get("acceptance", []):
            tags = ac.get("tags", [])
            if "e2e" in tags:
                ac_id = ac.get("id", "")
                if ac_id:
                    e2e_ac_ids.add(ac_id)

    for ac_id in e2e_ac_ids:
        if ac_id not in all_scenario_ac_ids:
            result.errors.append(ValidationError(
                code="PQ_AC_NOT_COVERED",
                message=f"e2e AC '{ac_id}' is not covered by any scenario's covers_ts",
                severity="ERROR", file=plan_file,
            ))

    # PQ-06: checkbox type
    for i, sc in enumerate(scenarios):
        for j, sf in enumerate(sc.get("selection_fields", [])):
            if sf.get("as_checkbox") and not sf.get("type"):
                result.warnings.append(ValidationError(
                    code="PQ_CHECKBOX_TYPE_MISSING",
                    message=f"scenarios[{i}].selection_fields[{j}] AS CHECKBOX without type:'checkbox'",
                    severity="WARNING", file=plan_file,
                ))

    # PQ-07: INSERT scenario test_setup
    for i, sc in enumerate(scenarios):
        branch_type = sc.get("branch_type", "")
        desc = sc.get("description", "")
        if branch_type == "insert" or "登録" in desc or "INSERT" in desc.upper():
            setup = sc.get("test_setup", {})
            if not setup.get("run_program"):
                result.warnings.append(ValidationError(
                    code="PQ_INSERT_NO_SETUP",
                    message=f"scenarios[{i}] is INSERT but missing test_setup.run_program",
                    severity="WARNING", file=plan_file,
                ))

    # PQ-08: unit_test_coverage dynamic
    unit_ac_exists = False
    for uc in spec.get("use_cases", []):
        for ac in uc.get("acceptance", []):
            if "unit" in ac.get("tags", []):
                unit_ac_exists = True
                break
    if unit_ac_exists and not plan.get("unit_test_coverage"):
        result.warnings.append(ValidationError(
            code="PQ_UNIT_COVERAGE_MISSING",
            message="spec has unit-tagged ACs but plan.md has no unit_test_coverage section",
            severity="WARNING", file=plan_file,
        ))

    # PQ-09: test_matrix full coverage
    # All basic_design.test_matrix.test_cases[].id must be covered
    # by >= 1 scenario's test_matrix_ref
    test_matrix = bd.get("test_matrix", {})
    test_cases = test_matrix.get("test_cases", [])
    if test_cases:
        tc_ids: set = set()
        for tc in test_cases:
            tc_id = tc.get("id")
            if tc_id is not None:
                tc_ids.add(tc_id)

        # Collect all test_matrix_ref from scenarios
        covered_tm_ids: set = set()
        for sc in scenarios:
            tm_ref = sc.get("test_matrix_ref")
            if tm_ref is not None:
                if isinstance(tm_ref, list):
                    covered_tm_ids.update(tm_ref)
                else:
                    covered_tm_ids.add(tm_ref)

        for tc_id in tc_ids:
            if tc_id not in covered_tm_ids:
                result.errors.append(ValidationError(
                    code="PQ_TEST_MATRIX_NOT_COVERED",
                    message=f"test_matrix.test_cases[].id={tc_id} is not covered by any scenario's test_matrix_ref",
                    severity="ERROR", file=plan_file,
                    suggestion=f"Add a Type B scenario with test_matrix_ref: {tc_id}",
                ))

    # PQ-11: plan.sap_components ↔ basic_design.sap_context.dev_objects
    plan_comps = plan.get("sap_components", [])
    bd_dev_objects = bd.get("sap_context", {}).get("dev_objects", [])
    if plan_comps and bd_dev_objects:
        # Build sets of (type, name) tuples
        plan_obj_set: set[tuple[str, str]] = set()
        for comp in plan_comps:
            otype = comp.get("object_type", "")
            oname = comp.get("object_name", "")
            if otype and oname:
                plan_obj_set.add((otype, oname))

        bd_obj_set: set[tuple[str, str]] = set()
        for obj in bd_dev_objects:
            otype = obj.get("type", "")
            oname = obj.get("name", "")
            if otype and oname:
                bd_obj_set.add((otype, oname))

        for otype, oname in plan_obj_set - bd_obj_set:
            result.errors.append(ValidationError(
                code="PQ_SAP_COMP_NOT_IN_BD",
                message=f"plan.sap_components {otype}:{oname} not in basic_design.sap_context.dev_objects",
                severity="ERROR", file=plan_file,
            ))
        for otype, oname in bd_obj_set - plan_obj_set:
            result.errors.append(ValidationError(
                code="PQ_BD_DEV_OBJ_NOT_IN_PLAN",
                message=f"basic_design.sap_context.dev_objects {otype}:{oname} not in plan.sap_components",
                severity="ERROR", file=plan_file,
            ))

    # PQ-12: plan.selection_fields ↔ basic_design screens fields
    plan_sel_fields = plan.get("selection_fields", [])
    if plan_sel_fields:
        bd_field_names: set[str] = set()
        for screen in bd.get("object_definitions", {}).get("screens", []):
            for block in screen.get("blocks", []):
                for fld in block.get("fields", []):
                    fname = fld.get("name", "")
                    if fname:
                        bd_field_names.add(fname)

        for i, sf in enumerate(plan_sel_fields):
            sf_name = sf.get("name", "")
            if sf_name and bd_field_names and sf_name not in bd_field_names:
                result.errors.append(ValidationError(
                    code="PQ_SEL_FIELD_NOT_IN_BD",
                    message=f"plan.selection_fields[{i}] name='{sf_name}' not in basic_design screens fields",
                    severity="ERROR", file=plan_file,
                ))

    # PQ-13: plan.tests[].covers_bpmn_element_ids ↔ basic_design bpmn elements
    bd_bpmn_ids: set[str] = set()
    for elem in bd.get("bpmn_descriptions", {}).get("elements", []):
        bid = elem.get("bpmn_id", "")
        if bid:
            bd_bpmn_ids.add(bid)

    if bd_bpmn_ids:
        for i, test in enumerate(plan.get("tests", [])):
            for bpmn_id in test.get("covers_bpmn_element_ids", []):
                if bpmn_id and bpmn_id not in bd_bpmn_ids:
                    result.warnings.append(ValidationError(
                        code="PQ_BPMN_REF_NOT_IN_BD",
                        message=f"tests[{i}].covers_bpmn_element_ids '{bpmn_id}' not in basic_design.bpmn_descriptions.elements",
                        severity="WARNING", file=plan_file,
                    ))

    # PQ-14: plan.transport_strategy.sequence[].objects ↔ dev_objects types
    transport = plan.get("transport_strategy", {})
    sequence = transport.get("sequence", [])
    if sequence and bd_dev_objects:
        bd_obj_types: set[str] = {obj.get("type", "") for obj in bd_dev_objects if obj.get("type")}
        transport_types: set[str] = set()
        for step in sequence:
            for obj_type in step.get("objects", []):
                if obj_type:
                    transport_types.add(obj_type)

        for otype in transport_types - bd_obj_types:
            result.errors.append(ValidationError(
                code="PQ_TRANSPORT_TYPE_NOT_IN_BD",
                message=f"plan.transport_strategy object type '{otype}' not in basic_design.sap_context.dev_objects",
                severity="ERROR", file=plan_file,
            ))
        for otype in bd_obj_types - transport_types:
            result.warnings.append(ValidationError(
                code="PQ_BD_TYPE_NOT_IN_TRANSPORT",
                message=f"basic_design dev_objects type '{otype}' not in plan.transport_strategy.sequence",
                severity="WARNING", file=plan_file,
            ))

    # PQ-15: plan.sap_components[].task_ref ↔ tasks (when tasks.md exists)
    tasks_path = context.feature_dir / "tasks.md"
    if tasks_path.exists() and plan_comps:
        # Read tasks.md and extract task IDs (lightweight check)
        try:
            tasks_text = tasks_path.read_text(encoding="utf-8")
            # Extract task IDs from YAML block
            task_ids: set[str] = set()
            import re
            for m in re.finditer(r'id:\s*"?(T-[^"\s]+)"?', tasks_text):
                task_ids.add(m.group(1))

            for comp in plan_comps:
                tref = comp.get("task_ref", "")
                if tref and task_ids and tref not in task_ids:
                    result.errors.append(ValidationError(
                        code="PQ_TASK_REF_NOT_FOUND",
                        message=f"plan.sap_components task_ref='{tref}' not found in tasks.md",
                        severity="ERROR", file=plan_file,
                    ))
        except Exception:
            pass

    # PQ-10: scenarios.yaml test_suite.feature_id consistency
    # test_suite.feature_id must match the front matter feature_id
    scenarios_path = context.feature_dir / "tests" / "scenarios.yaml"
    if scenarios_path.exists():
        try:
            scenarios_data = yaml.safe_load(scenarios_path.read_text(encoding="utf-8"))
            if isinstance(scenarios_data, dict):
                ts_fid = scenarios_data.get("test_suite", {}).get("feature_id", "")
                fm_fid = bd.get("front_matter", {}).get("feature_id", "") or ""
                if ts_fid and fm_fid and ts_fid != fm_fid:
                    result.errors.append(ValidationError(
                        code="PQ_SCENARIO_FEATURE_ID_MISMATCH",
                        message=(
                            f"scenarios.yaml test_suite.feature_id='{ts_fid}' "
                            f"does not match front matter feature_id='{fm_fid}'"
                        ),
                        severity="ERROR",
                        file=str(scenarios_path),
                        suggestion=f"Update test_suite.feature_id to '{fm_fid}'",
                    ))
        except Exception:
            pass  # scenarios.yaml parse failure is not this validator's concern

    return result
