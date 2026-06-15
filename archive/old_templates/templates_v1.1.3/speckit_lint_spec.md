---
artifact: "spec"
spec_id: "SPEC-LINT-001"
title: "speckit-lint Specification"
version: "1.0.0"
status: "active" # draft | active | deprecated
owners:
  - { name: "Architecture Board", role: "Owner" }
  - { name: "DevEx", role: "Maintainer" }
applies_to:
  - "specs/**/basic_design.md"
  - "specs/**/spec.md"
  - "specs/**/plan.md"
  - "specs/**/tasks.md"
  - "memory/constitution.md"
---

# 1. Purpose
本仕様は、SDDテンプレ運用を「形骸化しない統制システム」にするための lint / gate 評価仕様である。
- counts は派生フィールドとして CI が算出し、人手編集を禁止する。
- ID規約は constitution を唯一の正とし、参照整合を機械検証する。
- constitution の Gate requires を機械評価し、未達は PR を fail させる。

# 2. Repository Assumptions
## 2.1 Required Paths (Per Feature Directory)
`specs/<feature>/` 配下に以下が存在すること。
- `basic_design.md`
- `spec.md`
- `plan.md`
- `tasks.md`

必須：`memory/constitution.md`

## 2.2 Naming Convention
- ファイル名はスネークケースを正とする（例：`basic_design.md`）。
- 参照パス（frontmatter / yaml）にハイフン名が混入してはならない。

# 3. Canonical YAML Extraction
各ドキュメントから、以下の YAML ブロックを抽出し parse する（最初に一致したものを採用）。

## 3.1 spec.md
- 見出し：`# 0. Canonical Spec (YAML)` 直下の ```yaml ブロック

## 3.2 plan.md
- 見出し：`# 0. Canonical Plan (YAML)` 直下の ```yaml ブロック

## 3.3 tasks.md
- 見出し：`# 1. Canonical Tasks (YAML)` 直下の ```yaml ブロック

## 3.4 basic_design.md
- セクション：`D.2 Machine-readable Gate（basic_design_gate_check）` 直下の ```yaml ブロック

## 3.5 constitution.md
- `# 3. ID Conventions` の ```yaml ブロック（`id_conventions`）
- `# 5. Gates（Enforcement）` の ```yaml ブロック（`gates`）

# 4. ID Conventions (Single Source of Truth)
constitution の `id_conventions` を唯一の正として使用する。
他ドキュメントの `id_conventions_ref` / `id_conventions_version` は参照情報であり、規約本体は constitution から読む。

## 4.1 Regex Validation Targets
### spec
- `spec.use_cases[].id` → `use_case_id`
- `spec.use_cases[].acceptance[].id` → `acceptance_id`
- `spec.open_questions[].id` → `question_id`
- `spec.assumptions[].id` → `assumption_id`

### plan
- `plan.architecture.components[].id` → `component_id`
- `plan.architecture.libraries[].id` → `library_id`
- `plan.contracts.cli[].id` / `plan.contracts.apis_events[].id` → `contract_id`
- `plan.test_strategy.tests[].id` → `test_id`
- `plan.phases[].id` → `phase_id`
- `plan.phases[].groups[].id` → `group_id`

### tasks
- `tasks.tasks[].id` → `task_id`
- `tasks.tasks[].phase` → `phase_id`
- `tasks.tasks[].group` → `group_id`
- `tasks.milestones[].id` → `milestone_id`
- `tasks.risks[].id` → `risk_id`

## 4.2 Uniqueness
同一 feature 配下で以下は一意であること（重複禁止）。
- US / AC / CMP / LIB / CT / TS / Phase / Group / Task / Milestone / Risk

# 5. Cross-Reference Validation
## 5.1 spec → plan
- `plan.scope.in_use_cases` は `spec.use_cases[].id` の部分集合であり、少なくとも 1 件以上含む。
- `plan.test_strategy.tests[].covers_acceptance_ids` は `spec.use_cases[].acceptance[].id` に存在する。

## 5.2 plan → tasks (stable id only)
tasks の `plan_refs` は「stable id」のみ許可。stable id は plan 内の以下の集合とする。
- components: `CMP-*`
- libraries: `LIB-*`
- contracts: `CT-*`
- tests: `TS-*`
- phases: `Phase-*`
- groups: `G-*`

## 5.3 spec → tasks
- `tasks.tasks[].spec_refs` に含まれる US/AC は spec に存在する。

# 6. counts Computation (Derived Fields)
counts は CI が算出し、ドキュメント記載値は信用しない（必要なら差分検出して fail する）。

## 6.1 spec_gate_check.counts
- `use_cases` = `len(spec.use_cases)`
- `acceptance_criteria` = `sum(len(uc.acceptance) for uc in spec.use_cases)`
- `integration_tagged_ac` = acceptance の `tags` に `"integration"` を含む件数
- `blocking_questions` = `len([q for q in open_questions if q.blocking == true])`
- `nfr_items` = 各 `requirements` 配列の総件数（performance + availability_reliability + security_privacy + operations）

## 6.2 plan_gate_check.counts
- `in_use_cases` = `len(plan.scope.in_use_cases)`
- `libraries` = `len(plan.architecture.libraries)`
- `contracts` = `len(plan.contracts.cli) + len(plan.contracts.apis_events)`
- `tests` = `len(plan.test_strategy.tests)`
- `integration_tests` = `len([t for t in tests if t.type == "integration"])`
- `groups` = `sum(len(p.groups) for p in plan.phases)`
- `exception_items` = `len(plan.exceptions)`（空配列なら 0）

## 6.3 tasks_gate_check.counts
- `tasks` = `len(tasks.tasks)`
- `use_cases_referenced` = `tasks.tasks[].spec_refs` から `US-*` をユニーク抽出した数
- `acceptance_referenced` = `tasks.tasks[].spec_refs` から `AC-*` をユニーク抽出した数
- `tasks_with_plan_refs` = `len([t for t in tasks if plan_refs が空でない])`
- `dependency_edges` = `sum(len(t.depends_on) for t in tasks.tasks)`
- `milestones` = `len(tasks.milestones)`

# 7. Gate Evaluation
constitution の `gates[*].requires[]` を機械評価して pass/fail を決定する。
評価前に counts は 6章の算出値で上書きする。

## 7.1 Supported Expression Grammar (Minimum)
- Boolean: `X == true` / `X == false`
- Numeric: `X >= Y`, `X <= Y`, `X == Y`
- Dot-path: `spec_gate_check.counts.use_cases` のような参照

## 7.2 Failure Output
NG の場合、以下を必ず出力する。
- gate 名
- 失敗した requires 式
- actual / expected（比較演算の場合）

# 8. Error Codes
- `MISSING_FILE`
- `CANONICAL_BLOCK_NOT_FOUND`
- `YAML_PARSE_ERROR`
- `ID_REGEX_MISMATCH`
- `DUPLICATE_ID`
- `REF_NOT_FOUND`
- `INVALID_PLAN_REF`（stable id 以外を検出）
- `COUNTS_DIVERGENCE`（任意：記載値と算出値の差）
- `GATE_FAILED`

# 9. CLI Interface (Implementation Contract)
## 9.1 Commands
- `speckit-lint --all`
- `speckit-lint --feature specs/<feature>/`
- `speckit-lint --changed`（任意：git diff ベース）

## 9.2 Outputs
- human readable (stdout)
- machine readable JSON (stdout or file)

JSON例（概形）：
```json
{
  "result": "fail",
  "feature": "specs/XXX_feature_name/",
  "errors": [
    {"code":"REF_NOT_FOUND","from":"tasks.tasks[0].plan_refs[0]","ref":"LIB-99"}
  ],
  "gates": [
    {
      "name":"Spec Gate",
      "pass":false,
      "failed_requires":[
        {"expr":"spec_gate_check.counts.nfr_items >= spec_gate_check.rules.min_nfr_items","actual":0,"expected":1}
      ]
    }
  ]
}
```

# 10. CI Enforcement

* PR で `speckit-lint --all` を必須化し、fail はマージ不可（branch protection）。
* counts は CI 算出を正とし、差分があれば fail（推奨）。

# 11. Done Definition (Perfect State)

* counts が CI で算出され Gate が機械評価される
* 参照不整合／ID違反／Gate未達が PR で必ず fail する
* exceptions は空配列が標準で、例外のみ reason/mitigation が強制される