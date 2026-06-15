---
artifact: "spec"
spec_id: "SPEC-LINT-001"
title: "speckit-lint Specification"
version: "1.2.0"
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
- SDDの成果物（basic_design / process.bpmn / spec / plan / tasks / constitution）の**形骸化防止**を目的とする。
- Gate（counts/rules/boolean）を機械評価し、進行/停止を客観化する。
- Camunda 8 (Zeebe 8.8) BPMNの最低互換条件を検証し、HITL承認後の入力正本として固定できることを担保する。

# 2. File Naming / Path Rules
- ファイル名はスネークケースを正とする（例：`basic_design.md`）。
- 参照パス（frontmatter / yaml）にハイフン名が混入してはならない。
- 想定ディレクトリ：`specs/<feature>/` と `memory/`。

# 3. Canonical YAML Extraction
各ドキュメントから、以下の YAML ブロックを抽出し parse する。

## 3.1 spec.md
- 見出し：`# 0. Canonical Spec (YAML)` 直下の ```yaml ブロック

## 3.2 plan.md
- 見出し：`# 0. Canonical Plan (YAML)` 直下の ```yaml ブロック

## 3.3 tasks.md
- 見出し：`# 1. Canonical Tasks (YAML)` 直下の ```yaml ブロック

## 3.4 basic_design.md
- 見出し：`# 0. Canonical Basic Design (YAML)` 直下の ```yaml ブロック（`basic_design`）
- セクション：`7.2 Machine-readable Gate（basic_design_gate_check）` 直下の ```yaml ブロック（`basic_design_gate_check`）

## 3.5 constitution.md
- `# 3. ID Conventions` の ```yaml ブロック（`id_conventions`）
- `# 5. Gates（Enforcement）` の ```yaml ブロック（`gates`）

# 4. ID Conventions (Single Source of Truth)
constitution の `id_conventions` を唯一の正として使用する。

## 4.1 Regex Validation Targets
### basic_design
- `basic_design.traceability_rows[].rq.id` → `requirement_id`（空文字は許容）
- `basic_design.traceability_rows[].us.id` → `use_case_id`（空文字は許容）
- `basic_design.traceability_rows[].ac.id` → `acceptance_id`（空文字は許容）
- `basic_design.open_questions[].id` → `question_id`
- `basic_design.assumptions[].id` → `assumption_id`
- `basic_design.decisions[].id` → `decision_id`

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
- `tasks.milestones[].id` → `milestone_id`
- `tasks.risks[].id` → `risk_id`

# 5. Cross Reference Validation

## 5.1 basic_design → spec
- traceability_rows[].us.id が空でない場合、そのUSは `spec.use_cases[].id` に存在すること。
- traceability_rows[].ac.id が空でない場合、そのACは `spec.use_cases[].acceptance[].id` に存在すること。

## 5.2 plan → spec
- `plan.scope.in_use_cases` は `spec.use_cases[].id` の部分集合であり、少なくとも 1 件以上含む。
- `plan.test_strategy.tests[].covers_acceptance_ids` は `spec.use_cases[].acceptance[].id` に存在する。

## 5.3 tasks → spec / plan (stable id only)
- `tasks.tasks[].spec_refs` に含まれる US/AC は spec に存在する。
- `tasks.tasks[].plan_refs` は stable id のみ許可。stable id は plan 内の以下の集合とする：
  - components: `CMP-*`
  - libraries: `LIB-*`
  - contracts: `CT-*`
  - tests: `TS-*`
  - phases: `Phase-*`
  - groups: `G-*`

## 5.4 process.bpmn linkage
- `basic_design.basic_design.flow_reference.process_bpmn_path` が空でない場合、当該パスにファイルが存在すること。
- `basic_design_gate_check.ready_for_specify == true` の場合、当該 BPMN は Chapter 12 の BPMN Validation を pass すること。

## 5.5 bpmn_refs validation (Optional but Recommended)
- plan.groups[].bpmn_refs が存在する場合、各IDが process.bpmn 内の `@id` として存在すること。
- tasks.tasks[].bpmn_refs が存在する場合、同様に存在すること。
- ただし process.bpmn が未リンクの場合は検証をスキップする（warning）。

# 6. counts Computation (Derived Fields)
counts は CI が算出し、ドキュメント記載値は信用しない（必要なら差分検出して fail する）。

## 6.1 basic_design_gate_check.counts
- `traceability_rows` = `len(basic_design.traceability_rows)`
- `integration_flows` = `len(basic_design.integration_flows)`
- `blocking_questions` = `len([q for q in basic_design.open_questions if q.blocking == true])`

## 6.2 spec_gate_check.counts
- `use_cases` = `len(spec.use_cases)`
- `acceptance_criteria` = `sum(len(uc.acceptance) for uc in spec.use_cases)`
- `integration_tagged_ac` = acceptance の `tags` に `"integration"` を含む件数
- `blocking_questions` = `len([q for q in spec.open_questions if q.blocking == true])`
- `nfr_items` = performance + availability_reliability + security_privacy + operations の総件数

## 6.3 plan_gate_check.counts
- `in_use_cases` = `len(plan.scope.in_use_cases)`
- `libraries` = `len(plan.architecture.libraries)`
- `contracts` = `len(plan.contracts.cli) + len(plan.contracts.apis_events)`
- `tests` = `len(plan.test_strategy.tests)`
- `integration_tests` = `len([t for t in tests if t.type == "integration"])`
- `groups` = `sum(len(p.groups) for p in plan.phases)`
- `exception_items` = `len(plan.exceptions)`

## 6.4 tasks_gate_check.counts
- `tasks` = `len(tasks.tasks)`
- `use_cases_referenced` = `tasks.tasks[].spec_refs` から `US-*` をユニーク抽出した数
- `acceptance_referenced` = `tasks.tasks[].spec_refs` から `AC-*` をユニーク抽出した数
- `tasks_with_plan_refs` = `len([t for t in tasks.tasks if plan_refs が空でない])`
- `dependency_edges` = `sum(len(t.depends_on) for t in tasks.tasks)`
- `milestones` = `len(tasks.milestones)`

# 7. Gate Evaluation
constitution の `gates[*].requires[]` を機械評価して pass/fail を決定する。
評価前に counts は 6章の算出値で上書きする。

# 8. Failure Codes（主要）
- `MISSING_FILE`
- `CANONICAL_BLOCK_NOT_FOUND`
- `YAML_PARSE_ERROR`
- `ID_REGEX_MISMATCH`
- `DUPLICATE_ID`
- `REF_NOT_FOUND`
- `INVALID_PLAN_REF`
- `BPMN_VALIDATION_FAILED`
- `COUNTS_DIVERGENCE`（任意）
- `GATE_FAILED`

# 9. CLI Interface (Implementation Contract)
- `speckit-lint --all`
- `speckit-lint --feature specs/<feature>/`
- `speckit-lint --changed <git-range>`

# 12. BPMN Validation (Camunda 8 / Zeebe 8.8)
目的は「HITLでレビュー可能（DIあり）」「Camunda 8で意味的に破綻しない」最小条件を担保すること。

## 12.1 File / Parse
- XMLとして parse できること（well-formed）。
- ルート要素が `bpmn:definitions` であること。

## 12.2 Namespaces
- `xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"` が存在し、プレフィックスは必ず `zeebe` であること。
- `xmlns:modeler="http://camunda.org/schema/modeler/1.0"` が存在すること。

## 12.3 Execution Platform (Camunda 8)
- `bpmn:definitions` に以下が存在すること：
  - `modeler:executionPlatform="Camunda Cloud"`
  - `modeler:executionPlatformVersion` が `8.8` で始まること（例：`8.8.0`）

## 12.4 Executable Process
- `bpmn:process` が 1つ以上存在すること（推奨は1つ）。
- `bpmn:process/@isExecutable == "true"` であること。

## 12.5 DI Required
- `bpmndi:BPMNDiagram` と `bpmndi:BPMNPlane` が存在すること。
- Planeが process を `bpmnElement` で参照していること。

## 12.6 Service Task Minimum
- `bpmn:serviceTask` が存在する場合、各 task に `zeebe:taskDefinition/@type` が存在すること。

## 12.7 XOR Gateway Minimum
- `bpmn:exclusiveGateway` の outgoing が複数ある場合、以下のいずれかを満たすこと：
  - `@default` が設定され、その flow が存在する
  - すべての条件付きフローに `bpmn:conditionExpression` が存在する

## 12.8 Message Definitions (When Used)
- `bpmn:receiveTask` または message catch を使う場合、`bpmn:message` が definitions 直下に存在すること。
- `bpmn:message` を使う場合、`zeebe:subscription/@correlationKey` が存在すること（FEEL）。

## 12.9 Timer Format (Minimum)
- `bpmn:timeDuration` を使う場合、先頭が `P` または `PT` の ISO 8601 Duration であること（簡易チェック）。

> End of speckit_lint_spec.md
