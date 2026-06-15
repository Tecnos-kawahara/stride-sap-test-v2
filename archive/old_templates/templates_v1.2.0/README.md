# SDD Template Pack (Best v1.2.0)

This pack contains a coherent, Camunda 8 (Zeebe 8.8) aware set of SDD templates:

- `templates/basic_design_template.md` : HITL hub (human-editable canonical YAML + gate)
- `templates/spec_template.md` : WHAT/WHY (canonical YAML + spec gate)
- `templates/plan_template.md` : HOW (canonical YAML + plan gate, includes BPMN mapping)
- `templates/tasks_template.md` : executable tasks (canonical YAML + tasks gate)
- `policies/bpmn_generator_rules.md` : Camunda 8 BPMN 2.0 generation rules (executionPlatform enforced)
- `examples/process_bpmn_template.bpmn` : minimal Camunda 8 BPMN skeleton with DI
- `memory/constitution.md` : Nine Articles + ID conventions + gates (includes Basic Design Gate)
- `tools/speckit_lint_spec.md` : speckit-lint specification updated for Basic Design + Camunda platform checks

## Recommended Workflow
1. Create/update `basic_design.md` using the template. Fill Canonical YAML and set:
   - `basic_design_gate_check.traceability_present = true` etc.
   - When ready: `ready_for_bpmn = true`
2. Generate `process.bpmn` (Camunda 8) and get HITL approval:
   - Set `process_bpmn_linked = true` and `process_bpmn_approved = true`
   - When ready to generate downstream: `ready_for_specify = true`
3. Generate/update `spec.md` (WHAT/WHY), then set `spec_gate_check.ai_plan_ready = true`
4. Generate/update `plan.md` (HOW), then set `plan_gate_check.ai_tasks_ready = true`
5. Generate/update `tasks.md`, then set `tasks_gate_check.tasks_ready_for_code = true`
6. Run `speckit-lint` to validate all gates and cross-references.

