#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - handled at runtime
    yaml = None


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def extract_yaml_blocks(text):
    blocks = []
    lines = text.splitlines()
    in_block = False
    buf = []
    for line in lines:
        if line.strip().startswith("```yaml"):
            in_block = True
            buf = []
            continue
        if in_block and line.strip().startswith("```"):
            blocks.append("\n".join(buf))
            in_block = False
            buf = []
            continue
        if in_block:
            buf.append(line)
    return blocks


def extract_yaml_after_marker(text, marker):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if marker in line:
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith("```yaml"):
                    start = j + 1
                    for k in range(start, len(lines)):
                        if lines[k].strip().startswith("```"):
                            return "\n".join(lines[start:k])
    return None


def load_yaml(block, path_label):
    if yaml is None:
        raise RuntimeError("PyYAML is required to run speckit-lite. Install with `pip install pyyaml`.")
    try:
        return yaml.safe_load(block)
    except Exception as exc:  # pragma: no cover - handled at runtime
        raise RuntimeError(f"YAML parse error in {path_label}: {exc}") from exc


def as_list(value):
    if isinstance(value, list):
        return value
    return []


def add_error(errors, code, message):
    errors.append(f"{code}: {message}")


def add_warning(warnings, code, message):
    warnings.append(f"{code}: {message}")


def compile_regex(pattern):
    return re.compile(pattern)


def check_id(regex, value, allow_empty, errors, context):
    if value is None:
        add_error(errors, "ID_REGEX_MISMATCH", f"{context}: missing id")
        return
    if value == "" and allow_empty:
        return
    if not regex.match(value):
        add_error(errors, "ID_REGEX_MISMATCH", f"{context}: {value}")


def count_blocking_questions(questions):
    return sum(1 for q in as_list(questions) if q.get("blocking") is True)


def compute_spec_counts(spec_doc):
    use_cases = as_list(spec_doc.get("use_cases"))
    ac_items = []
    for uc in use_cases:
        ac_items.extend(as_list(uc.get("acceptance")))
    integration_tagged = sum(1 for ac in ac_items if "integration" in as_list(ac.get("tags")))
    e2e_tagged = sum(1 for ac in ac_items if "e2e" in as_list(ac.get("tags")))
    requirements = spec_doc.get("requirements", {})
    integration = as_list(requirements.get("integration"))
    data_governance = as_list(requirements.get("data_governance"))
    performance = as_list(requirements.get("performance"))
    availability = as_list(requirements.get("availability_reliability"))
    security = as_list(requirements.get("security_privacy"))
    operations = as_list(requirements.get("operations"))
    nfr_items = sum(len(items) for items in [
        integration,
        data_governance,
        performance,
        availability,
        security,
        operations,
    ])
    counts = {
        "use_cases": len(use_cases),
        "acceptance_criteria": len(ac_items),
        "integration_tagged_ac": integration_tagged,
        "e2e_tagged_ac": e2e_tagged,
        "blocking_questions": count_blocking_questions(spec_doc.get("open_questions")),
        "nfr_items": nfr_items,
        "security_items": len(security),
        "integration_items": len(integration),
        "data_items": len(data_governance),
    }
    return counts, use_cases, ac_items


def compute_plan_counts(plan_doc):
    scope = plan_doc.get("scope", {})
    architecture = plan_doc.get("architecture", {})
    contracts = plan_doc.get("contracts", {})
    test_strategy = plan_doc.get("test_strategy", {})
    phases = as_list(plan_doc.get("phases"))
    cli_contracts = as_list(contracts.get("cli"))
    api_contracts = as_list(contracts.get("apis_events"))
    tests = as_list(test_strategy.get("tests"))
    integration_tests = [t for t in tests if t.get("type") == "integration"]
    e2e_tests = [t for t in tests if t.get("type") == "e2e"]
    group_count = sum(len(as_list(p.get("groups"))) for p in phases)
    counts = {
        "in_use_cases": len(as_list(scope.get("in_use_cases"))),
        "libraries": len(as_list(architecture.get("libraries"))),
        "contracts": len(cli_contracts) + len(api_contracts),
        "tests": len(tests),
        "integration_tests": len(integration_tests),
        "e2e_tests": len(e2e_tests),
        "groups": group_count,
        "exception_items": len(as_list(plan_doc.get("exceptions"))),
    }
    return counts, cli_contracts + api_contracts, tests, phases


def compute_tasks_counts(tasks_doc):
    task_items = as_list(tasks_doc.get("tasks"))
    milestones = as_list(tasks_doc.get("milestones"))
    spec_refs = []
    tasks_with_plan_refs = 0
    dependency_edges = 0
    for task in task_items:
        spec_refs.extend(as_list(task.get("spec_refs")))
        plan_refs = as_list(task.get("plan_refs"))
        if plan_refs:
            tasks_with_plan_refs += 1
        dependency_edges += len(as_list(task.get("depends_on")))
    use_cases_referenced = len({ref for ref in spec_refs if ref.startswith("US-")})
    acceptance_referenced = len({ref for ref in spec_refs if ref.startswith("AC-")})
    counts = {
        "tasks": len(task_items),
        "use_cases_referenced": use_cases_referenced,
        "acceptance_referenced": acceptance_referenced,
        "tasks_with_plan_refs": tasks_with_plan_refs,
        "dependency_edges": dependency_edges,
        "milestones": len(milestones),
    }
    return counts, task_items


def compare_counts(label, expected, actual, warnings):
    for key, value in expected.items():
        if key in actual and actual[key] != value:
            add_warning(
                warnings,
                "COUNTS_DIVERGENCE",
                f"{label}: {key} expected={value} actual={actual[key]}",
            )


def validate_bpmn(path, errors, warnings):
    text = read_text(path)
    if "xmlns:zeebe=" not in text or "xmlns:modeler=" not in text:
        add_error(errors, "BPMN_VALIDATION_FAILED", "Missing zeebe/modeler namespaces")
        return
    if 'modeler:executionPlatform="Camunda Cloud"' not in text:
        add_error(errors, "BPMN_VALIDATION_FAILED", "Missing executionPlatform")
    if "modeler:executionPlatformVersion" not in text:
        add_error(errors, "BPMN_VALIDATION_FAILED", "Missing executionPlatformVersion")
    if "bpmndi:BPMNDiagram" not in text or "bpmndi:BPMNPlane" not in text:
        add_error(errors, "BPMN_VALIDATION_FAILED", "Missing DI elements")
    if 'isExecutable="true"' not in text:
        add_error(errors, "BPMN_VALIDATION_FAILED", "Process is not executable")
    if "<bpmn:serviceTask" in text and "zeebe:taskDefinition" not in text:
        add_error(errors, "BPMN_VALIDATION_FAILED", "ServiceTask missing zeebe:taskDefinition")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("feature_dir", help="Path to specs/<feature>")
    parser.add_argument("--warn-only", action="store_true", help="Do not fail on warnings")
    args = parser.parse_args()

    errors = []
    warnings = []

    feature_dir = Path(args.feature_dir)
    if not feature_dir.exists():
        add_error(errors, "MISSING_FILE", f"{feature_dir} not found")
        report(errors, warnings, args.warn_only)
        return 1

    basic_design_path = feature_dir / "basic_design.md"
    spec_path = feature_dir / "spec.md"
    plan_path = feature_dir / "plan.md"
    tasks_path = feature_dir / "tasks.md"
    bpmn_path = feature_dir / "process.bpmn"

    for path in [basic_design_path, spec_path, plan_path, tasks_path]:
        if not path.exists():
            add_error(errors, "MISSING_FILE", f"{path}")

    if errors:
        report(errors, warnings, args.warn_only)
        return 1

    # Load constitution
    constitution_path = feature_dir.parent.parent / "memory" / "constitution.md"
    if not constitution_path.exists():
        add_error(errors, "MISSING_FILE", f"{constitution_path}")
        report(errors, warnings, args.warn_only)
        return 1
    constitution_text = read_text(constitution_path)
    constitution_blocks = extract_yaml_blocks(constitution_text)
    id_block = next((b for b in constitution_blocks if "id_conventions:" in b), None)
    gates_block = next((b for b in constitution_blocks if "gates:" in b), None)
    if id_block is None:
        add_error(errors, "CANONICAL_BLOCK_NOT_FOUND", "constitution id_conventions")
        report(errors, warnings, args.warn_only)
        return 1
    id_conventions = load_yaml(id_block, "constitution id_conventions").get("id_conventions", {})

    # Load basic_design
    basic_design_text = read_text(basic_design_path)
    basic_block = extract_yaml_after_marker(basic_design_text, "Canonical Basic Design")
    basic_gate_block = extract_yaml_after_marker(basic_design_text, "basic_design_gate_check")
    if basic_block is None or basic_gate_block is None:
        add_error(errors, "CANONICAL_BLOCK_NOT_FOUND", "basic_design")
        report(errors, warnings, args.warn_only)
        return 1
    basic_doc = load_yaml(basic_block, str(basic_design_path))
    basic_gate_doc = load_yaml(basic_gate_block, str(basic_design_path))

    # Load spec/plan/tasks
    spec_block = extract_yaml_after_marker(read_text(spec_path), "Canonical Spec")
    plan_block = extract_yaml_after_marker(read_text(plan_path), "Canonical Plan")
    tasks_block = extract_yaml_after_marker(read_text(tasks_path), "Canonical Tasks")
    if spec_block is None or plan_block is None or tasks_block is None:
        add_error(errors, "CANONICAL_BLOCK_NOT_FOUND", "spec/plan/tasks")
        report(errors, warnings, args.warn_only)
        return 1
    spec_doc = load_yaml(spec_block, str(spec_path))
    plan_doc = load_yaml(plan_block, str(plan_path))
    tasks_doc = load_yaml(tasks_block, str(tasks_path))

    # ID validation
    regex = {k: compile_regex(v) for k, v in id_conventions.items()}
    trace_rows = as_list(basic_doc.get("basic_design", {}).get("traceability_rows"))
    for i, row in enumerate(trace_rows):
        rq = row.get("rq", {}).get("id")
        us = row.get("us", {}).get("id")
        ac = row.get("ac", {}).get("id")
        check_id(regex["requirement_id"], rq, True, errors, f"traceability_rows[{i}].rq.id")
        check_id(regex["use_case_id"], us, True, errors, f"traceability_rows[{i}].us.id")
        check_id(regex["acceptance_id"], ac, True, errors, f"traceability_rows[{i}].ac.id")
    for i, q in enumerate(as_list(basic_doc.get("basic_design", {}).get("open_questions"))):
        check_id(regex["question_id"], q.get("id"), False, errors, f"basic_design.open_questions[{i}].id")
    for i, a in enumerate(as_list(basic_doc.get("basic_design", {}).get("assumptions"))):
        check_id(regex["assumption_id"], a.get("id"), False, errors, f"basic_design.assumptions[{i}].id")
    for i, d in enumerate(as_list(basic_doc.get("basic_design", {}).get("decisions"))):
        check_id(regex["decision_id"], d.get("id"), False, errors, f"basic_design.decisions[{i}].id")

    spec_counts, spec_use_cases, spec_ac_items = compute_spec_counts(spec_doc.get("spec", {}))
    for i, uc in enumerate(spec_use_cases):
        check_id(regex["use_case_id"], uc.get("id"), False, errors, f"spec.use_cases[{i}].id")
        for j, ac in enumerate(as_list(uc.get("acceptance"))):
            check_id(regex["acceptance_id"], ac.get("id"), False, errors, f"spec.use_cases[{i}].acceptance[{j}].id")
    for i, q in enumerate(as_list(spec_doc.get("spec", {}).get("open_questions"))):
        check_id(regex["question_id"], q.get("id"), False, errors, f"spec.open_questions[{i}].id")
    for i, a in enumerate(as_list(spec_doc.get("spec", {}).get("assumptions"))):
        check_id(regex["assumption_id"], a.get("id"), False, errors, f"spec.assumptions[{i}].id")

    plan_counts, plan_contracts, plan_tests, plan_phases = compute_plan_counts(plan_doc.get("plan", {}))
    for i, c in enumerate(as_list(plan_doc.get("plan", {}).get("architecture", {}).get("components"))):
        check_id(regex["component_id"], c.get("id"), False, errors, f"plan.components[{i}].id")
    for i, l in enumerate(as_list(plan_doc.get("plan", {}).get("architecture", {}).get("libraries"))):
        check_id(regex["library_id"], l.get("id"), False, errors, f"plan.libraries[{i}].id")
    for i, c in enumerate(as_list(plan_doc.get("plan", {}).get("contracts", {}).get("cli"))):
        check_id(regex["contract_id"], c.get("id"), False, errors, f"plan.contracts.cli[{i}].id")
    for i, c in enumerate(as_list(plan_doc.get("plan", {}).get("contracts", {}).get("apis_events"))):
        check_id(regex["contract_id"], c.get("id"), False, errors, f"plan.contracts.apis_events[{i}].id")
    for i, t in enumerate(plan_tests):
        check_id(regex["test_id"], t.get("id"), False, errors, f"plan.tests[{i}].id")
    for i, phase in enumerate(plan_phases):
        check_id(regex["phase_id"], phase.get("id"), False, errors, f"plan.phases[{i}].id")
        for j, group in enumerate(as_list(phase.get("groups"))):
            check_id(regex["group_id"], group.get("id"), False, errors, f"plan.phases[{i}].groups[{j}].id")

    tasks_counts, task_items = compute_tasks_counts(tasks_doc.get("tasks", {}))
    for i, task in enumerate(task_items):
        check_id(regex["task_id"], task.get("id"), False, errors, f"tasks.tasks[{i}].id")
    for i, milestone in enumerate(as_list(tasks_doc.get("tasks", {}).get("milestones"))):
        check_id(regex["milestone_id"], milestone.get("id"), False, errors, f"tasks.milestones[{i}].id")
    for i, risk in enumerate(as_list(tasks_doc.get("tasks", {}).get("risks"))):
        check_id(regex["risk_id"], risk.get("id"), False, errors, f"tasks.risks[{i}].id")

    # Cross references
    spec_use_case_ids = {uc.get("id") for uc in spec_use_cases}
    spec_ac_ids = {ac.get("id") for ac in spec_ac_items}
    for i, row in enumerate(trace_rows):
        us_id = row.get("us", {}).get("id")
        ac_id = row.get("ac", {}).get("id")
        if us_id and us_id not in spec_use_case_ids:
            add_error(errors, "REF_NOT_FOUND", f"traceability_rows[{i}].us.id {us_id}")
        if ac_id and ac_id not in spec_ac_ids:
            add_error(errors, "REF_NOT_FOUND", f"traceability_rows[{i}].ac.id {ac_id}")

    plan_scope = as_list(plan_doc.get("plan", {}).get("scope", {}).get("in_use_cases"))
    for us_id in plan_scope:
        if us_id not in spec_use_case_ids:
            add_error(errors, "REF_NOT_FOUND", f"plan.scope.in_use_cases {us_id}")
    for i, test in enumerate(plan_tests):
        for ac_id in as_list(test.get("covers_acceptance_ids")):
            if ac_id not in spec_ac_ids:
                add_error(errors, "REF_NOT_FOUND", f"plan.tests[{i}].covers_acceptance_ids {ac_id}")
        for ct_id in as_list(test.get("covers_contract_ids")):
            contract_ids = {c.get("id") for c in plan_contracts}
            if ct_id not in contract_ids:
                add_error(errors, "REF_NOT_FOUND", f"plan.tests[{i}].covers_contract_ids {ct_id}")

    for i, task in enumerate(task_items):
        for ref in as_list(task.get("spec_refs")):
            if ref.startswith("US-") and ref not in spec_use_case_ids:
                add_error(errors, "REF_NOT_FOUND", f"tasks.tasks[{i}].spec_refs {ref}")
            if ref.startswith("AC-") and ref not in spec_ac_ids:
                add_error(errors, "REF_NOT_FOUND", f"tasks.tasks[{i}].spec_refs {ref}")

    stable_ids = set()
    stable_ids.update({c.get("id") for c in as_list(plan_doc.get("plan", {}).get("architecture", {}).get("components"))})
    stable_ids.update({l.get("id") for l in as_list(plan_doc.get("plan", {}).get("architecture", {}).get("libraries"))})
    stable_ids.update({c.get("id") for c in plan_contracts})
    stable_ids.update({t.get("id") for t in plan_tests})
    stable_ids.update({p.get("id") for p in plan_phases})
    for phase in plan_phases:
        stable_ids.update({g.get("id") for g in as_list(phase.get("groups"))})
    for i, task in enumerate(task_items):
        for ref in as_list(task.get("plan_refs")):
            if ref not in stable_ids:
                add_error(errors, "INVALID_PLAN_REF", f"tasks.tasks[{i}].plan_refs {ref}")

    # Coverage checks
    all_ac = spec_ac_ids
    covered_ac = set()
    for test in plan_tests:
        covered_ac.update(as_list(test.get("covers_acceptance_ids")))
    missing_ac = sorted(all_ac - covered_ac)
    if missing_ac:
        add_error(errors, "AC_NOT_COVERED", f"Missing AC: {', '.join(missing_ac)}")

    coverage_policy = plan_doc.get("plan", {}).get("test_strategy", {}).get("coverage_policy", {})
    tagged_requirements = coverage_policy.get("tagged_acceptance_requirements", {})
    ac_by_tag = {
        "integration": {ac.get("id") for ac in spec_ac_items if "integration" in as_list(ac.get("tags"))},
        "e2e": {ac.get("id") for ac in spec_ac_items if "e2e" in as_list(ac.get("tags"))},
    }
    for tag, requirement in tagged_requirements.items():
        if requirement.get("enforce") is True:
            required_type = requirement.get("required_test_type")
            covered = set()
            for test in plan_tests:
                if test.get("type") == required_type:
                    covered.update(as_list(test.get("covers_acceptance_ids")))
            missing = sorted(ac_by_tag.get(tag, set()) - covered)
            if missing:
                add_error(errors, "TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE", f"{tag}: {', '.join(missing)}")

    if coverage_policy.get("contract_coverage_required") is True:
        all_ct = {c.get("id") for c in plan_contracts}
        covered_ct = set()
        for test in plan_tests:
            if test.get("type") == "contract":
                covered_ct.update(as_list(test.get("covers_contract_ids")))
        missing_ct = sorted(all_ct - covered_ct)
        if missing_ct:
            add_error(errors, "CONTRACT_COVERAGE_INCOMPLETE", f"Missing CT: {', '.join(missing_ct)}")

    if coverage_policy.get("tests_must_be_tasked") is True:
        all_ts = {t.get("id") for t in plan_tests}
        tasked_ts = set()
        for task in task_items:
            for ref in as_list(task.get("plan_refs")):
                if ref.startswith("TS-"):
                    tasked_ts.add(ref)
        missing_ts = sorted(all_ts - tasked_ts)
        if missing_ts:
            add_error(errors, "TEST_NOT_TASKED", f"Missing TS: {', '.join(missing_ts)}")

    # Optional E2E checks
    has_e2e = any(t.get("type") == "e2e" for t in plan_tests)
    reporting = plan_doc.get("plan", {}).get("test_strategy", {}).get("reporting", {}).get("e2e", {})
    if has_e2e and not reporting.get("artifacts_dir"):
        add_warning(warnings, "E2E_REPORTING_NOT_CONFIGURED", "reporting.e2e.artifacts_dir is empty")
    triage_path = feature_dir / "implementation-details" / "e2e-triage.md"
    if has_e2e and not triage_path.exists():
        add_warning(warnings, "E2E_TRIAGE_NOT_DEFINED", f"{triage_path} missing")

    # Gate checks
    basic_gate = basic_gate_doc.get("basic_design_gate_check", {})
    basic_counts = {
        "traceability_rows": len(trace_rows),
        "integration_flows": len(as_list(basic_doc.get("basic_design", {}).get("integration_flows"))),
        "blocking_questions": count_blocking_questions(basic_doc.get("basic_design", {}).get("open_questions")),
    }
    compare_counts("basic_design", basic_doc.get("derived_fields", {}).get("counts", {}), basic_counts, warnings)
    compare_counts("basic_design_gate", basic_gate.get("counts", {}), basic_counts, warnings)
    basic_rules = basic_gate.get("rules", {})
    if basic_counts["traceability_rows"] < basic_rules.get("min_traceability_rows", 0):
        add_error(errors, "GATE_FAILED", "basic_design traceability_rows below minimum")
    if basic_counts["integration_flows"] < basic_rules.get("min_integration_flows", 0):
        add_error(errors, "GATE_FAILED", "basic_design integration_flows below minimum")
    if basic_counts["blocking_questions"] > basic_rules.get("max_blocking_questions", 0):
        add_error(errors, "GATE_FAILED", "basic_design blocking_questions above maximum")
    for flag in ["traceability_present", "integration_flows_identified", "exceptions_documented", "ready_for_bpmn"]:
        if basic_gate.get(flag) is not True:
            add_error(errors, "GATE_FAILED", f"basic_design gate flag {flag} is not true")
    for flag in ["process_bpmn_linked", "process_bpmn_approved", "ready_for_specify"]:
        if basic_gate.get(flag) is not True:
            add_error(errors, "GATE_FAILED", f"basic_design BPMN flag {flag} is not true")

    spec_gate = spec_doc.get("spec_gate_check", {})
    compare_counts("spec", spec_doc.get("derived_fields", {}).get("counts", {}), spec_counts, warnings)
    compare_counts("spec_gate", spec_gate.get("counts", {}), spec_counts, warnings)
    spec_rules = spec_gate.get("rules", {})
    if spec_counts["use_cases"] < spec_rules.get("min_use_cases", 0):
        add_error(errors, "GATE_FAILED", "spec use_cases below minimum")
    if spec_counts["acceptance_criteria"] < spec_rules.get("min_total_acceptance_criteria", 0):
        add_error(errors, "GATE_FAILED", "spec acceptance_criteria below minimum")
    if spec_counts["integration_tagged_ac"] < spec_rules.get("min_integration_acceptance_criteria", 0):
        add_error(errors, "GATE_FAILED", "spec integration_tagged_ac below minimum")
    if spec_counts["blocking_questions"] > spec_rules.get("max_blocking_questions", 0):
        add_error(errors, "GATE_FAILED", "spec blocking_questions above maximum")
    if spec_counts["nfr_items"] < spec_rules.get("min_nfr_items", 0):
        add_error(errors, "GATE_FAILED", "spec nfr_items below minimum")
    if spec_counts["security_items"] < spec_rules.get("min_security_items", 0):
        add_error(errors, "GATE_FAILED", "spec security_items below minimum")
    if spec_counts["integration_items"] < spec_rules.get("min_integration_items", 0):
        add_error(errors, "GATE_FAILED", "spec integration_items below minimum")
    if spec_counts["data_items"] < spec_rules.get("min_data_items", 0):
        add_error(errors, "GATE_FAILED", "spec data_items below minimum")
    for flag in ["no_blocking_open_questions", "ai_plan_ready"]:
        if spec_gate.get(flag) is not True:
            add_error(errors, "GATE_FAILED", f"spec gate flag {flag} is not true")

    plan_gate = plan_doc.get("plan_gate_check", {})
    compare_counts("plan", plan_doc.get("derived_fields", {}).get("counts", {}), plan_counts, warnings)
    compare_counts("plan_gate", plan_gate.get("counts", {}), plan_counts, warnings)
    plan_rules = plan_gate.get("rules", {})
    if plan_counts["in_use_cases"] < plan_rules.get("min_in_use_cases", 0):
        add_error(errors, "GATE_FAILED", "plan in_use_cases below minimum")
    if plan_counts["libraries"] < plan_rules.get("min_libraries", 0):
        add_error(errors, "GATE_FAILED", "plan libraries below minimum")
    if plan_counts["contracts"] < plan_rules.get("min_contracts", 0):
        add_error(errors, "GATE_FAILED", "plan contracts below minimum")
    if plan_counts["tests"] < plan_rules.get("min_tests", 0):
        add_error(errors, "GATE_FAILED", "plan tests below minimum")
    if plan_counts["integration_tests"] < plan_rules.get("min_integration_tests", 0):
        add_error(errors, "GATE_FAILED", "plan integration_tests below minimum")
    if plan_counts["groups"] < plan_rules.get("min_groups", 0):
        add_error(errors, "GATE_FAILED", "plan groups below minimum")
    for flag in ["contracts_defined", "tests_prioritized", "integration_first_gate_passed", "ai_tasks_ready"]:
        if plan_gate.get(flag) is not True:
            add_error(errors, "GATE_FAILED", f"plan gate flag {flag} is not true")

    tasks_gate = tasks_doc.get("tasks_gate_check", {})
    compare_counts("tasks", tasks_doc.get("derived_fields", {}).get("counts", {}), tasks_counts, warnings)
    compare_counts("tasks_gate", tasks_gate.get("counts", {}), tasks_counts, warnings)
    tasks_rules = tasks_gate.get("rules", {})
    if tasks_counts["tasks"] < tasks_rules.get("min_tasks", 0):
        add_error(errors, "GATE_FAILED", "tasks count below minimum")
    if tasks_counts["use_cases_referenced"] < tasks_rules.get("min_use_cases_referenced", 0):
        add_error(errors, "GATE_FAILED", "tasks use_cases_referenced below minimum")
    if tasks_counts["acceptance_referenced"] < tasks_rules.get("min_acceptance_referenced", 0):
        add_error(errors, "GATE_FAILED", "tasks acceptance_referenced below minimum")
    if tasks_counts["tasks_with_plan_refs"] != tasks_counts["tasks"]:
        add_error(errors, "GATE_FAILED", "tasks_with_plan_refs does not match tasks count")
    for flag in ["no_dependency_errors", "tasks_ready_for_code"]:
        if tasks_gate.get(flag) is not True:
            add_error(errors, "GATE_FAILED", f"tasks gate flag {flag} is not true")

    # BPMN validation (optional)
    if bpmn_path.exists():
        validate_bpmn(bpmn_path, errors, warnings)
    else:
        add_warning(warnings, "MISSING_FILE", f"{bpmn_path}")

    report(errors, warnings, args.warn_only)
    return 0 if not errors else 1


def report(errors, warnings, warn_only):
    if errors:
        print("Errors:")
        for err in errors:
            print(f"  - {err}")
    if warnings:
        print("Warnings:")
        for warn in warnings:
            print(f"  - {warn}")
    if not errors and not warnings:
        print("OK: speckit-lite checks passed")
    if errors:
        sys.exit(1)
    if warnings and not warn_only:
        sys.exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
