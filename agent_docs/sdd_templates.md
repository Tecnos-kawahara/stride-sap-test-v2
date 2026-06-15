# SDD Templates (Tecnos v4.4.0)
# Use canonical templates, not ad-hoc markdown.

## 1) Template sources
- `sdd-templates/templates/basic_design_template.md`
- `sdd-templates/templates/spec_template.md`
- `sdd-templates/templates/plan_template.md`
- `sdd-templates/templates/tasks_template.md`
- `sdd-templates/templates/evidence_pack_template.md`

## 2) Minimal setup
- Use `CREATE_FEATURE_DIRS` and `COPY_TEMPLATES` from `agent_docs/commands.md`.
- Replace placeholders (FEAT-XXX, FEATXXX, XXX_feature_name).

## 3) Canonical YAML blocks (lint extraction)
- `basic_design.md`: `# 0. Canonical Basic Design (YAML)`
- `spec.md`: `# 0. Canonical Spec (YAML)`
- `plan.md`: `# 0. Canonical Plan (YAML)`
- `tasks.md`: `# 1. Canonical Tasks (YAML)`

## 4) Gates
- Use gate flags in each document; `stride-lint` is authoritative.
