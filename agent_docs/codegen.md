# Spec-as-Code and Schema Rules
# This repo treats spec_as_code artifacts as the source of truth.

## 1) Required artifacts
- OpenAPI (or equivalent contract).
- migration_mapping.
- authz_matrix.
- test_scenarios.

## 2) Rules
- List artifacts in `spec.spec_as_code.artifacts` with valid paths.
- Store artifacts under `specs/<feature>/contracts/` or `specs/<feature>/implementation-details/`.
- If code generation is introduced, document it in `plan.md` and the Evidence Pack.

## 3) Validation
- `stride-lint` validates presence and references.
