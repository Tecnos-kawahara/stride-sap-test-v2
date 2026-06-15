---
artifact: "constitution"
constitution_id: "CONST-001"
title: "SDD Development Constitution (Nine Articles)"
version: "1.2.0"
status: "active" # draft | in_review | active | superseded
owners:
  - { name: "Architecture Board", role: "Owner" }
  - { name: "AI Guild", role: "Co-maintainer" }
last_reviewed_at: "YYYY-MM-DD"
amendment_history: []
---

# 1. Purpose
- **Specification-Driven Development (SDD)** を実務で破綻させないための「不変原則（Constitution）」を定義する。
- 仕様（Spec）が一次成果物であり、計画（Plan）・タスク（Tasks）・コードは仕様からの生成物である。
- Gate（機械可読）により、生成・実装の進行/停止を**客観基準**で判断できるようにする。
- 例外は例外として**明示**し、憲法（Article）に紐付けて記録する。

# 2. Definitions
- **Spec**: WHAT/WHY（実装詳細や技術選定は含めない）
- **Plan**: HOW（技術判断・分解・順序。ただしコードは禁止）
- **Tasks**: 実行可能な作業単位（並列性・依存・DoDを明示）
- **process.bpmn**: Camunda 8 (Zeebe) 前提の業務フロー正本（HITLで承認）
- **basic_design**: 人間⇄AIの認識齟齬を潰すハブ（HITLで修正可能）

# 3. ID Conventions（唯一の正）
この章の `id_conventions` が唯一の正である。テンプレや他ドキュメントに同様の正規表現が存在しても参照情報であり、規約本体は常に本書から読む。

```yaml
id_conventions:
  feature_id: "^FEAT-[A-Z0-9]{3,}$"

  requirement_id: "^RQ-[0-9]{3}$"
  decision_id: "^DR-[0-9]{3}$"
  flow_id: "^FLOW-[0-9]{3}$"

  use_case_id: "^US-FEAT[A-Z0-9]{3,}-[0-9]{3}$"
  acceptance_id: "^AC-US-FEAT[A-Z0-9]{3,}-[0-9]{3}-[0-9]{2}$"
  question_id: "^Q-[0-9]{3}$"
  assumption_id: "^A-[0-9]{3}$"

  phase_id: "^Phase-[0-9]+$"
  group_id: "^G-[0-9]{2}-[a-z0-9-]+$"

  component_id: "^CMP-[0-9]{2}$"
  library_id: "^LIB-[0-9]{2}$"

  contract_id: "^CT-(API|CLI|EVT)-[0-9]{2}$"
  test_id: "^TS-(CON|INT|E2E|UT)-[0-9]{2}$"

  task_id: "^T-[A-Z0-9]{2,}-[0-9]{3}$"
  milestone_id: "^M-[0-9]{2}$"
  risk_id: "^R-[0-9]{3}$"

  # Camunda 8 (Zeebe) BPMN element IDs (推奨：安定IDでトレーサブルにする)
  bpmn_process_id: "^BPMN-PROC-[A-Z0-9]{3,}$"
  bpmn_element_id: "^BPMN-(TASK|GW|EVT|FLOW)-[0-9]{3}$"
```

# 4. Nine Articles（Principles & Evaluation Criteria）
> 各 Article は「Rules（守ること）」と「Criteria（評価基準）」で構成する。
> 例示は理解補助であり規範ではない。

```yaml
nine_articles:
  - id: "I"
    name: "Library-First"
    summary: "すべての機能はライブラリ境界から始める"
    rules:
      - "ビジネスロジックはライブラリ境界に集約する"
      - "UI/アプリ層はオーケストレーションに留める"
    criteria:
      - "主要概念が library/component と対応している"
      - "責務境界がPlanで明示されている"

  - id: "II"
    name: "Contract/CLI-First"
    summary: "契約（API/CLI/EVT）を実装より先に定義する"
    rules:
      - "契約は contracts/ に置く"
      - "CLI は text-in/text-out を基本とし JSON をサポートする"
    criteria:
      - "CT-* がPlanに列挙され、Tasksに落ちている"
      - "契約テスト（TS-CON-*）が存在する"

  - id: "III"
    name: "Test-First"
    summary: "テストを仕様の一部として先に定義する"
    rules:
      - "契約テスト → 統合テスト → E2E → ユニットの順に優先する"
      - "Acceptance Criteria はテストへトレースされる"
    criteria:
      - "AC-* が TS-* でカバーされている"
      - "integration タグ付きACが統合テストで優先されている"

  - id: "IV"
    name: "Documentation-First"
    summary: "仕様・計画・タスクの更新が実装変更に先行する"
    rules:
      - "コードは一次成果物ではない（仕様が先）"
    criteria:
      - "Spec/Plan/Tasks の Gate が通っている"

  - id: "V"
    name: "Modularity"
    summary: "境界を明確にし、変更影響を局所化する"
    rules:
      - "境界を越えるのは契約のみ"
    criteria:
      - "責務境界・契約・依存がPlanに明示されている"

  - id: "VI"
    name: "Automation"
    summary: "生成・検証・反復を自動化する"
    rules:
      - "counts はCIが算出し、差分があれば失敗させる"
      - "lintにより形骸化を防ぐ"
    criteria:
      - "speckit-lint が通る"
      - "derived_fields.counts_are_computed が true"

  - id: "VII"
    name: "Simplicity"
    summary: "最小構成から始め、必要性が証明されるまで増やさない"
    rules:
      - "初期は ≤3 project を原則（例外は記録）"
      - "future-proofing を禁止"
    criteria:
      - "例外が DR/Exceptions に記録されている"

  - id: "VIII"
    name: "Anti-Abstraction"
    summary: "フレームワークを信頼し、不要な抽象化を作らない"
    rules:
      - "薄いラッパーや重複モデルを禁止"
    criteria:
      - "単一表現（Single Source of Model）が守られている"

  - id: "IX"
    name: "Integration-First"
    summary: "実環境に近い統合テストを優先する"
    rules:
      - "契約を先に固め、統合テストで回帰を担保する"
    criteria:
      - "integration タグACが統合テストでカバーされている"
```

# 5. Gates（Enforcement）
> Gateは「counts/rules/boolean」を持つ。
> booleanのみでの通過を禁止し、最低限の客観条件基準を rules で定義する。

```yaml
gates:
  - name: "Basic Design Gate"
    artifact: "basic_design"
    requires:
      - "basic_design_gate_check.traceability_present == true"
      - "basic_design_gate_check.integration_flows_identified == true"
      - "basic_design_gate_check.exceptions_documented == true"
      - "basic_design_gate_check.counts.traceability_rows >= basic_design_gate_check.rules.min_traceability_rows"
      - "basic_design_gate_check.counts.integration_flows >= basic_design_gate_check.rules.min_integration_flows"
      - "basic_design_gate_check.counts.blocking_questions <= basic_design_gate_check.rules.max_blocking_questions"
      - "basic_design_gate_check.ready_for_bpmn == true"

  - name: "Spec Gate"
    artifact: "spec"
    requires:
      - "spec_gate_check.no_blocking_open_questions == true"
      - "spec_gate_check.counts.use_cases >= spec_gate_check.rules.min_use_cases"
      - "spec_gate_check.counts.acceptance_criteria >= spec_gate_check.rules.min_total_acceptance_criteria"
      - "spec_gate_check.counts.integration_tagged_ac >= spec_gate_check.rules.min_integration_acceptance_criteria"
      - "spec_gate_check.counts.blocking_questions <= spec_gate_check.rules.max_blocking_questions"
      - "spec_gate_check.counts.nfr_items >= spec_gate_check.rules.min_nfr_items"
      - "spec_gate_check.ai_plan_ready == true"

  - name: "Plan Gate"
    artifact: "plan"
    requires:
      - "plan_gate_check.contracts_defined == true"
      - "plan_gate_check.tests_prioritized == true"
      - "plan_gate_check.integration_first_gate_passed == true"
      - "plan_gate_check.counts.in_use_cases >= plan_gate_check.rules.min_in_use_cases"
      - "plan_gate_check.counts.libraries >= plan_gate_check.rules.min_libraries"
      - "plan_gate_check.counts.contracts >= plan_gate_check.rules.min_contracts"
      - "plan_gate_check.counts.tests >= plan_gate_check.rules.min_tests"
      - "plan_gate_check.counts.integration_tests >= plan_gate_check.rules.min_integration_tests"
      - "plan_gate_check.counts.groups >= plan_gate_check.rules.min_groups"
      - "plan_gate_check.ai_tasks_ready == true"

  - name: "Tasks Gate"
    artifact: "tasks"
    requires:
      - "tasks_gate_check.no_dependency_errors == true"
      - "tasks_gate_check.counts.tasks >= tasks_gate_check.rules.min_tasks"
      - "tasks_gate_check.counts.use_cases_referenced >= tasks_gate_check.rules.min_use_cases_referenced"
      - "tasks_gate_check.counts.acceptance_referenced >= tasks_gate_check.rules.min_acceptance_referenced"
      - "tasks_gate_check.counts.tasks_with_plan_refs == tasks_gate_check.counts.tasks"
      - "tasks_gate_check.tasks_ready_for_code == true"
```

# 6. Implementation Notes（テンプレ依存：変動しやすいので隔離）
- 推奨フロー：
  1) 人間の任意テキスト → `basic_design.md`（HITLで修正/承認）
  2) `basic_design_gate_check.ready_for_bpmn = true` → `process.bpmn` を生成・HITL承認
  3) `basic_design_gate_check.process_bpmn_approved = true` → `spec/plan/tasks` を生成
  4) `speckit-lint` で Gate を機械評価し、差し戻し/進行を決める

- 推奨：Spec/Plan/Tasks は Canonical YAML を AI の正本とする（人間向け文章は補助）。
- 推奨：Planの主要要素（component/library/contract/test/phase/group）は stable id を付与し、Tasks は stable id 参照のみを使う。
- 推奨：例外は必ず `{article, reason, mitigation}` の3点セットで記録する（例外が無いなら空配列）。
- 推奨：BPMN 2.0 は Camunda 8 (Zeebe) 仕様に準拠し、`modeler:executionPlatform="Camunda Cloud"` と `modeler:executionPlatformVersion="8.8.0"` を明示する。

# 7. Amendment Process
- 変更理由・影響範囲・Owners承認・SemVer更新・last_reviewed_at 記録を必須とする。
- 改訂は小さく、テンプレ参照の密結合を避ける。

> End of constitution.md
