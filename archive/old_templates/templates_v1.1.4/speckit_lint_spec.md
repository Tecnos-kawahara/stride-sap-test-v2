---
artifact: "spec"
spec_id: "SPEC-LINT-001"
title: "speckit-lint Specification"
version: "1.1.1"
status: "active" # draft | active | deprecated
owners:
  - { name: "Architecture Board", role: "Owner" }
  - { name: "DevEx", role: "Maintainer" }
applies_to:
  - "specs/**/basic_design.md"
  - "specs/**/process.bpmn"
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
- process.bpmn は HITL でレビュー可能（DI必須）かつ Camunda 8 (Zeebe) 前提の最低条件を満たすことを機械検証する。

# 2. Repository Assumptions
## 2.1 Required Paths (Per Feature Directory)
`specs/<feature>/` 配下に以下が存在すること。
- `basic_design.md`
- `process.bpmn`（Phase 1.5 以降。ready_for_specify==true の場合は必須）
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

## 5.4 basic_design → process.bpmn (Linkage)
- `basic_design.md` の frontmatter `related_artifacts.process_bpmn` が存在すること（パス文字列）。
- `basic_design_gate_check.process_bpmn_linked == true` の場合、当該パスにファイルが存在すること。
- `basic_design_gate_check.ready_for_specify == true` の場合、当該 BPMN が Chapter 12 の BPMN Validation を pass すること。

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

# 10. CI Enforcement
- PR で `speckit-lint --all` を必須化し、fail はマージ不可（branch protection）。
- counts は CI 算出を正とし、差分があれば fail（推奨）。

# 11. Done Definition (Perfect State)
- counts が CI で算出され Gate が機械評価される
- 参照不整合／ID違反／Gate未達が PR で必ず fail する
- exceptions は空配列が標準で、例外のみ reason/mitigation が強制される
- process.bpmn が DI を含み、Camunda 8 前提の最低条件を満たし、HITL承認後に spec/plan/tasks の入力として固定される

# 12. BPMN Validation (Camunda 8 / Zeebe)
本章は `specs/<feature>/process.bpmn` の機械検証仕様である。
目的は「HITLでレビュー可能（DIあり）」「Camunda 8で意味的に破綻しない」最小条件を担保すること。

## 12.1 File / Parse
- XML として parse できること（well-formed）。
- ルート要素が `bpmn:definitions` であること。

## 12.2 Namespaces (Prefix Requirements)
- `xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"` が存在し、プレフィックスは必ず `zeebe` であること。
  - 失敗コード: `BPMN_NAMESPACE_INVALID`

## 12.3 Executable Process
- `bpmn:process` が 1つ以上存在すること（推奨は1つ）。
- `bpmn:process/@isExecutable == "true"` であること。
  - 失敗コード: `BPMN_PROCESS_INVALID`

## 12.4 DI (Diagram Interchange) Required for HITL
- `bpmndi:BPMNDiagram` が存在すること。
- `bpmndi:BPMNPlane/@bpmnElement` が、対象 `bpmn:process/@id` を参照すること。
  - 失敗コード: `BPMN_DI_MISSING`

## 12.5 Service Task Requirements (Zeebe)
- `bpmn:serviceTask` は必ず `zeebe:taskDefinition` を持つこと。
- `zeebe:taskDefinition/@type` が空でないこと（ハイレベルでは `tbd.*` を許容）。
  - 失敗コード: `BPMN_SERVICE_TASK_INVALID`

## 12.6 XOR Gateway Minimum Condition
- `bpmn:exclusiveGateway` の outgoing が複数ある場合、以下のいずれかを満たすこと。
  - `@default` が設定され、その flow が存在する
  - すべての条件付きフローに `bpmn:conditionExpression` が存在する
  - 失敗コード: `BPMN_GATEWAY_INVALID`

## 12.7 Message Definitions (When Used)
- `bpmn:receiveTask` または message catch を使う場合、`bpmn:message` が definitions 直下に存在すること。
- `bpmn:message` を使う場合、`zeebe:subscription/@correlationKey` が存在すること（FEEL）。
  - 失敗コード: `BPMN_MESSAGE_INVALID`

## 12.8 Timer Format (Minimum)
- `bpmn:timeDuration` を使う場合、先頭が `P` または `PT` の ISO 8601 Duration であること（簡易チェック）。
  - 失敗コード: `BPMN_TIMER_INVALID`

## 12.9 BPMN Error Codes
追加エラーコード：
- `BPMN_NAMESPACE_INVALID`
- `BPMN_PROCESS_INVALID`
- `BPMN_DI_MISSING`
- `BPMN_SERVICE_TASK_INVALID`
- `BPMN_GATEWAY_INVALID`
- `BPMN_MESSAGE_INVALID`
- `BPMN_TIMER_INVALID`
