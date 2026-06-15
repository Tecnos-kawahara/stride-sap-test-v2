---
artifact: "spec"
spec_id: "SPEC-LINT-TECNOS-001"
title: "stride-lint Specification (Tecnos Edition)"
version: "5.3.3-tecnos-stride"
status: "active" # draft | active | deprecated
owners:
  - { name: "Tecnos Architecture Board", role: "Owner" }
  - { name: "DevEx", role: "Maintainer" }
applies_to:
  - "specs/**/basic_design.md"
  - "specs/**/process.bpmn"
  - "specs/**/spec.md"
  - "specs/**/plan.md"
  - "specs/**/tasks.md"
  - "memory/constitution.md"
  - "memory/tecnos_org_constraints.md"
  - "memory/artifact_registry.md"
---

# 1. Purpose
- SDDの成果物（basic_design / process.bpmn / spec / plan / tasks / constitution）の**形骸化防止**を目的とする。
- Gate（counts/rules/boolean）を機械評価し、進行/停止を客観化する。
- Camunda 8 (Zeebe 8.8) BPMNの最低互換条件を検証し、HITL承認後の入力正本として固定できることを担保する。
- Tecnos固有の最低要件（統合・監査・運用・AgentOpsガードレール）は `memory/tecnos_org_constraints.md` を参照し、少なくとも Spec/Plan/Tasks に論点が現れることを期待する（内容の妥当性評価はプロジェクトレビューで行う）。
- **v1.2.3**: Spec-as-Code / Evidence Pack / RACI+ を含め、AI/HITLでの品質証跡を担保する。

# 2. File Naming / Path Rules
- ファイル名はスネークケースを正とする（例：`basic_design.md`）。
- 参照パス（frontmatter / yaml）にハイフン名が混入してはならない。
- 想定ディレクトリ：`specs/<feature>/` と `memory/`。

# 3. Canonical YAML Extraction
各ドキュメントから、以下の YAML ブロックを抽出し parse する。

> **実装の集約（v5.1 チューンナップ）**: Canonical YAML 抽出ロジックは
> `sdd-templates/tools/stride_shared_lib.py` に一本化されている
> (`extract_yaml_blocks` / `extract_yaml_after_marker` / `extract_frontmatter`
> と、パス受取りの高水準 API `extract_canonical_yaml` / `extract_frontmatter_yaml`
> / `find_all_canonical_blocks`)。stride_lint / multi_model_evaluator /
> wi_readiness_checker / sdd_planning_bridge / post_edit_guard はいずれもこの
> 共有ライブラリを import して使用するため、抽出規則（フェンス認識・ヘッダ
> 部分一致・frontmatter 対応）は 1 箇所で保守される。

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

### 5.2.1 Acceptance Coverage Completeness（v1.2.2 追加・必須）
> AC Coverage = 100% を機械強制する。

- spec上の全AC集合 `ALL_AC` を抽出：`spec.use_cases[].acceptance[].id`
- plan上の `covers_acceptance_ids` の和集合 `COVERED_AC` を抽出：`plan.test_strategy.tests[].covers_acceptance_ids`
- `ALL_AC - COVERED_AC` が空でない場合 **FAIL**（未カバーAC一覧を出力）
- Failure Code: `AC_NOT_COVERED`

### 5.2.2 Tagged Acceptance Coverage（v1.2.2 追加・Tecnos推奨）
> タグ付きACが対応するテスト種別でカバーされていることを検証する。
> `coverage_policy.tagged_acceptance_requirements.<tag>.enforce` で有効化。

- `coverage_policy` が無い場合は **warning**（後方互換のため）。
- `enforce=true` の場合は **fail**（形骸化防止）。
- `enforce=false` の場合は検証をスキップする（例外は plan.exceptions に記録することを推奨）。

**integration タグ検証**：
- `tags` に `"integration"` を含むAC集合 `INTEGRATION_AC` を抽出
- `type: "integration"` テスト（TS-INT-*）の `covers_acceptance_ids` 和集合 `COVERED_BY_INT` を抽出
- `INTEGRATION_AC - COVERED_BY_INT` が空でない場合 **FAIL**
- Failure Code: `TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE`

**e2e タグ検証**：
- `tags` に `"e2e"` を含むAC集合 `E2E_AC` を抽出
- `type: "e2e"` テスト（TS-E2E-*）の `covers_acceptance_ids` 和集合 `COVERED_BY_E2E` を抽出
- `E2E_AC - COVERED_BY_E2E` が空でない場合 **FAIL**
- Failure Code: `TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE`

### 5.2.3 covers_contract_ids Validation（v1.2.2 追加・任意）
- `plan.test_strategy.tests[].covers_contract_ids` が存在する場合、各IDが plan の contracts（`plan.contracts.cli[].id` / `plan.contracts.apis_events[].id`）として存在すること。
- Failure Code: `REF_NOT_FOUND`

### 5.2.4 Contract Coverage Completeness（v1.2.2 追加・coverage_policyで有効化）
> CT Coverage = 100% を機械強制する（契約テストの網羅性）。

- `plan.test_strategy.coverage_policy.contract_coverage_required == true` の場合に検証
- plan内の全CT集合 `ALL_CT` を抽出：`plan.contracts.cli[].id` + `plan.contracts.apis_events[].id`
- `type: "contract"` テスト（TS-CON-*）の `covers_contract_ids` 和集合 `COVERED_CT` を抽出
- `ALL_CT - COVERED_CT` が空でない場合 **FAIL**（未カバーCT一覧を出力）
- Failure Code: `CONTRACT_COVERAGE_INCOMPLETE`

### 5.2.5 E2E Reporting Baseline（v1.2.2 追加・推奨）
- `type: "e2e"` のテストが 1 件以上存在する場合、`plan.test_strategy.reporting.e2e.artifacts_dir` が空でないこと。
- 空の場合 **warning** または **fail**（運用で決定）
- Failure Code: `E2E_REPORTING_NOT_CONFIGURED`

### 5.2.6 Spec-as-Code Completeness（v1.2.3 追加・必須）
- `spec_gate_check.spec_as_code_defined == true` の場合、`spec.spec_as_code.artifacts` が 1 件以上存在すること。
- `artifacts[].path` は空でないこと。
- Failure Code: `SPEC_AS_CODE_MISSING`

### 5.2.7 Evidence Pack Baseline（v1.2.3 追加・必須）
- `plan_gate_check.evidence_pack_defined == true` の場合、`plan.test_strategy.evidence_pack.required_artifacts` が空でないこと。
- `plan.test_strategy.evidence_pack.storage.path` が空でないこと。
- Failure Code: `EVIDENCE_PACK_NOT_DEFINED`

## 5.3 tasks → spec / plan (stable id only)
- `tasks.tasks[].spec_refs` に含まれる US/AC は spec に存在する。
- `tasks.tasks[].plan_refs` は stable id のみ許可。stable id は plan 内の以下の集合とする：
  - components: `CMP-*`
  - libraries: `LIB-*`
  - contracts: `CT-*`
  - tests: `TS-*`
  - phases: `Phase-*`
  - groups: `G-*`

### 5.3.1 Plan Tests Must Be Tasked（v1.2.2 追加・coverage_policyで有効化）
> PlanのTSがTasksに落ちていることを機械強制する（計画倒れ防止）。

- `plan.test_strategy.coverage_policy.tests_must_be_tasked == true` の場合に検証
- plan の `plan.test_strategy.tests[].id`（TS-*）を全て抽出 → `ALL_TS`
- tasks の `tasks.tasks[].plan_refs` に含まれる TS-* を抽出 → `TASKED_TS`
- `ALL_TS - TASKED_TS` が空でない場合 **FAIL**（未タスク化TS一覧を出力）
- 推奨：その tasks item の `type` は `test` であること（warning→fail は段階導入）
- Failure Code: `TEST_NOT_TASKED`

### 5.3.2 E2E Feedback Loop Artifact（v1.2.2 追加・推奨）
- `type: "e2e"` のテストが存在する場合、Tasks の outputs に `e2e-triage.md` 相当の成果物が現れること
- パターン例：`specs/<feature>/implementation-details/e2e-triage.md`
- 存在しない場合 **warning**（fail は任意）
- Failure Code: `E2E_TRIAGE_NOT_DEFINED`

## 5.4 process.bpmn linkage
- `basic_design.basic_design.flow_reference.process_bpmn_path` が空でない場合、当該パスにファイルが存在すること。
- `basic_design_gate_check.ready_for_specify == true` の場合、当該 BPMN は Chapter 12 の BPMN Validation を pass すること。

## 5.5 bpmn_refs validation (Optional but Recommended)
- plan.groups[].bpmn_refs が存在する場合、各IDが process.bpmn 内の `@id` として存在すること。
- tasks.tasks[].bpmn_refs が存在する場合、同様に存在すること。
- ただし process.bpmn が未リンクの場合は検証をスキップする（warning）。

## 5.6 Placeholder Token Detection（v1.2.3 追加・推奨）
- Canonical YAML 内に以下のプレースホルダが残っている場合は warning。
  - `FEAT-XXX` / `FEATXXX`
  - `SPEC-XXX` / `PLAN-XXX` / `TASKS-XXX` / `BD-XXX`
  - `US-FEATXXX-*` / `AC-US-FEATXXX-*`
  - `CT-*-XX` / `TS-*-XX` / `T-GXX-XXX`
  - `specs/XXX_feature_name/`
- Failure Code: `PLACEHOLDER_VALUE_PRESENT`

## 5.7 Artifact Registry Validation（v1.2.3 追加・推奨）
- `memory/artifact_registry.md` の `artifact_registry` が空でないこと。
- 各エントリに以下が存在すること：
  - `artifact_id`, `name`, `phase`, `domains`, `owner_role`, `approver_role`
  - `storage.canonical_path`, `storage.single_source_of_truth == true`
- Failure Code: `ARTIFACT_REGISTRY_INVALID`

# 6. counts Computation (Derived Fields)
counts は CI が算出し、ドキュメント記載値は信用しない（必要なら差分検出して fail する）。

## 6.1 basic_design_gate_check.counts
- `traceability_rows` = `len(basic_design.traceability_rows)`
- `integration_flows` = `len(basic_design.integration_flows)`
- `blocking_questions` = `len([q for q in basic_design.open_questions if q.blocking == true])`

## 6.2 spec_gate_check.counts（Tecnos拡張 + v1.2.3）
- `use_cases` = `len(spec.use_cases)`
- `acceptance_criteria` = `sum(len(uc.acceptance) for uc in spec.use_cases)`
- `integration_tagged_ac` = acceptance の `tags` に `"integration"` を含む件数
- `e2e_tagged_ac` = acceptance の `tags` に `"e2e"` を含む件数（v1.2.2追加）
- `blocking_questions` = `len([q for q in spec.open_questions if q.blocking == true])`
- `security_items` = `len(spec.requirements.security_privacy)`
- `integration_items` = `len(spec.requirements.integration)`
- `data_items` = `len(spec.requirements.data_governance)`
- `nfr_items` = integration + data_governance + performance + availability_reliability + security_privacy + operations の総件数
- `spec_as_code_artifacts` = `len(spec.spec_as_code.artifacts)`（v1.2.3追加）

## 6.3 plan_gate_check.counts（v1.2.2 拡張）
- `in_use_cases` = `len(plan.scope.in_use_cases)`
- `libraries` = `len(plan.architecture.libraries)`
- `contracts` = `len(plan.contracts.cli) + len(plan.contracts.apis_events)`
- `tests` = `len(plan.test_strategy.tests)`
- `integration_tests` = `len([t for t in tests if t.type == "integration"])`
- `e2e_tests` = `len([t for t in tests if t.type == "e2e"])`（v1.2.2追加）
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

# 7.1 BDD Acceptance Criteria Lint ルール (v4.5追加)

## AC-001: acceptance_criteria フィールドの存在確認
- **対象:** tasks.md内の全タスク（`bdd_mode: "required"` の場合）
- **条件:** `acceptance_criteria` フィールドが存在すること
- **違反時:** WARNING（移行期間中はERRORにしない）
- **Failure Code:** `BDD_AC_MISSING`

## AC-002: BDD構造の完全性
- **対象:** 各 acceptance_criteria エントリ
- **条件:** `id`, `scenario`, `given`, `when`, `then`, `verification` が全て存在すること
- **違反時:** ERROR
- **Failure Code:** `BDD_AC_INCOMPLETE`

## AC-003: verification値の妥当性
- **対象:** `verification` フィールド
- **条件:** `automated` | `manual` | `hitl` のいずれか
- **違反時:** ERROR
- **Failure Code:** `BDD_AC_INVALID_VERIFICATION`

## AC-004: escalation_trigger設定の確認
- **対象:** auth/payment/schema/security キーワードを含むタスクのdescription
- **条件:** 該当キーワードが含まれる場合、少なくとも1つの `acceptance_criteria` エントリに `escalation_trigger: true` が設定されていること
- **違反時:** WARNING
- **Failure Code:** `BDD_ESCALATION_MISSING`

## AC-005: automated比率の確認
- **対象:** tasks.md全体
- **条件:** `verification: "automated"` の比率が `verification_matrix.automated_ratio_target` 以上
- **違反時:** WARNING（INFO表示）
- **Failure Code:** `BDD_AUTOMATED_RATIO_LOW`

# 8. Failure Codes（主要 + v1.2.3追加）
- `MISSING_FILE`
- `CANONICAL_BLOCK_NOT_FOUND`
- `YAML_PARSE_ERROR`
- `ID_REGEX_MISMATCH`
- `DUPLICATE_ID`
- `REF_NOT_FOUND`
- `INVALID_PLAN_REF`
- `AC_NOT_COVERED` (v1.2.2)
- `TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE` (v1.2.2)
- `CONTRACT_COVERAGE_INCOMPLETE` (v1.2.2)
- `TEST_NOT_TASKED` (v1.2.2)
- `E2E_REPORTING_NOT_CONFIGURED` (v1.2.2)
- `E2E_TRIAGE_NOT_DEFINED` (v1.2.2)
- `SPEC_AS_CODE_MISSING` (v1.2.3)
- `EVIDENCE_PACK_NOT_DEFINED` (v1.2.3)
- `PLACEHOLDER_VALUE_PRESENT` (v1.2.3)
- `ARTIFACT_REGISTRY_INVALID` (v1.2.3)
- `BPMN_VALIDATION_FAILED`
- `COUNTS_MISMATCH`（任意）
- `GATE_FAILED`
- `BDD_AC_MISSING` (v4.5)
- `BDD_AC_INCOMPLETE` (v4.5)
- `BDD_AC_INVALID_VERIFICATION` (v4.5)
- `BDD_ESCALATION_MISSING` (v4.5)
- `BDD_AUTOMATED_RATIO_LOW` (v4.5)

# 9. CLI Interface (Implementation Contract)
- `stride lint specs/<feature>/`
- `stride lint --all`
- `stride lint --changed <git-range>`
- `stride lint specs/<feature>/ --coverage-report` (AC/CT/Code coverage summary)
- `stride lint specs/<feature>/ --enterprise` (Enterprise Hierarchy 有効時のみ)
- `stride lint --all --enterprise` (Feature + Epic の一括検証)
- 互換ラッパー: `sdd-templates/tools/stride-lint ...`

# 10. Coverage Report Output（v1.2.2 追加）
`stride-lint --coverage-report` 実行時に以下を出力する。

```yaml
coverage_report:
  timestamp: "YYYY-MM-DDTHH:MM:SSZ"
  feature: "FEAT-XXX"

  acceptance_coverage:
    total_ac: 0
    covered_ac: 0
    coverage_pct: 0.0
    uncovered: []

  tagged_coverage:
    integration:
      total_tagged: 0
      covered_by_int: 0
      coverage_pct: 0.0
      uncovered: []
    e2e:
      total_tagged: 0
      covered_by_e2e: 0
      coverage_pct: 0.0
      uncovered: []

  contract_coverage:
    total_ct: 0
    covered_ct: 0
    coverage_pct: 0.0
    uncovered: []

  test_tasking:
    total_ts: 0
    tasked_ts: 0
    coverage_pct: 0.0
    untasked: []

  summary:
    ac_coverage_pass: false
    tagged_coverage_pass: false
    contract_coverage_pass: false
    test_tasking_pass: false
    overall_pass: false
```

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

> End of stride_lint_spec.md
