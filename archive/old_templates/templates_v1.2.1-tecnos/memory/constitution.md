---
artifact: "constitution"
constitution_id: "CONST-TECNOS-001"
title: "SDD Development Constitution (Tecnos Edition)"
version: "1.2.1-tecnos"
status: "active" # draft | in_review | active | superseded
owners:
  - { name: "Tecnos Architecture Board", role: "Owner" }
  - { name: "Tecnos PMO / Business Promotion", role: "Co-maintainer" }
last_reviewed_at: "YYYY-MM-DD"
amendment_history:
  - { date: "2025-12-17", version: "1.2.0-tecnos", note: "Tecnos org constraints + Camunda 8 + Basic Design hub + stable IDs" }
  - { date: "2025-12-30", version: "1.2.1-tecnos", note: "Coverage Policy (AC/CT/Code) + Tagged AC enforcement + E2E Playwright + AgentOps triage flow" }
---

# 1. Purpose
- Tecnos Japan における **Specification-Driven Development (SDD)** を実務で破綻させないための「不変原則（Constitution）」を定義する。
- 仕様（Spec）が一次成果物であり、計画（Plan）・タスク（Tasks）・コードは仕様からの生成物である。
- Gate（機械可読）により、生成・実装の進行/停止を**客観基準**で判断できるようにする。
- 例外は例外として**明示**し、憲法（Article）に紐付けて記録する。
- **Coverage Policy**（AC/CT/Code）により、テストの網羅性を3層で管理する。

# 2. Definitions
- **basic_design**: 人間⇄AIの認識齟齬を潰すハブ（HITLで修正可能）
- **process.bpmn**: Camunda 8 (Zeebe 8.8) 前提の業務フロー正本（HITLで承認）
- **Spec**: WHAT/WHY（実装詳細や技術選定は含めない）
- **Plan**: HOW（技術判断・分解・順序。ただしコードは禁止）
- **Tasks**: 実行可能な作業単位（並列性・依存・DoDを明示）
- **Tecnos Org Constraints**: Tecnos固有の運用制約（ERP/SCM/CRM統合、監査・運用、AgentOpsガードレール）
  - 参照: `memory/tecnos_org_constraints.md`
  - 本書は不変原則ではないが、Tecnosプロジェクトでは必須参照とする。
- **Coverage Policy**: テストカバレッジの3層管理方針（Plan `coverage_policy` で定義）
  - Layer-1: **Spec Coverage（AC Coverage）** = 全ACがTSでカバーされる（100%必須）
  - Layer-2: **Contract Coverage（CT Coverage）** = 全CTがTS-CONでカバーされる（原則100%）
  - Layer-3: **Code Coverage** = 行/分岐カバレッジ（目標値＋例外管理）

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

  # Tecnos: ERP/SCM/CRM統合では File/Batch/EDI/IDoc が現実に必要になるため拡張する
  contract_id: "^CT-(API|CLI|EVT|FILE|BATCH|EDI|IDOC)-[0-9]{2}$"
  test_id: "^TS-(CON|INT|E2E|UT)-[0-9]{2}$"

  task_id: "^T-[A-Z0-9]{2,}-[0-9]{3}$"
  milestone_id: "^M-[0-9]{2}$"
  risk_id: "^R-[0-9]{3}$"

  # Camunda 8 (Zeebe) BPMN element IDs（推奨：安定IDでトレーサブルにする）
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
    summary: "契約（API/CLI/EVT/FILE/BATCH/EDI/IDOC）を実装より先に定義する"
    rules:
      - "契約は contracts/ に置く"
      - "CLI は text-in/text-out を基本とし JSON をサポートする"
      - "FILE/BATCH/EDI/IDOC も契約として入出力・再実行性・監査観点を明文化する"
      - "全CTはTS-CON（契約テスト）でカバーされる（Coverage Policy Layer-2）"
    criteria:
      - "CT-* がPlanに列挙され、Tasksに落ちている"
      - "契約テスト（TS-CON-*）が存在し、全CTをカバーしている"

  - id: "III"
    name: "Test-First"
    summary: "テストを仕様の一部として先に定義する"
    rules:
      - "契約テスト → 統合テスト → E2E → ユニットの順に優先する"
      - "Acceptance Criteria はテストへトレースされる（Coverage Policy Layer-1）"
      - "integrationタグ付きACはTS-INTでカバーされる"
      - "e2eタグ付きACはTS-E2Eでカバーされる"
    criteria:
      - "AC-* が TS-* でカバーされている（100%）"
      - "integration タグ付きACが統合テストで優先されている"
      - "e2e タグ付きACがE2Eテストでカバーされている"

  - id: "IV"
    name: "Documentation-First"
    summary: "仕様・計画・タスクの更新が実装変更に先行する"
    rules:
      - "コードは一次成果物ではない（仕様が先）"
    criteria:
      - "Spec/Plan/Tasks の Gate が通っている"

  - id: "V"
    name: "Modularity"
    summary: "境界を明確にし、変更影響を局所化する（ERP境界を破らない）"
    rules:
      - "境界を越えるのは契約のみ"
      - "ERP本体DB直結などの境界破りは原則禁止（例外は記録）"
    criteria:
      - "責務境界・契約・依存がPlanに明示されている"

  - id: "VI"
    name: "Automation"
    summary: "生成・検証・反復を自動化する"
    rules:
      - "counts はCIが算出し、差分があれば失敗させる"
      - "lintにより形骸化を防ぐ"
      - "Coverage Policyに基づくテスト網羅性をCIで検証する"
    criteria:
      - "speckit-lint が通る"
      - "derived_fields.counts_are_computed が true"
      - "Tagged AC Coverage / Contract Coverage が pass"

  - id: "VII"
    name: "Simplicity"
    summary: "最小構成から始め、必要性が証明されるまで増やさない"
    rules:
      - "初期は ≤3 project を原則（例外は記録）"
      - "future-proofing を禁止"
      - "E2Eは重要ユーザージャーニー（e2eタグ付きAC）に限定する"
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
    summary: "実環境に近い統合テストを優先する（ERP/外部連携前提）"
    rules:
      - "契約を先に固め、統合テストで回帰を担保する"
      - "E2Eは「統合クリティカルフロー／Mustのユーザージャーニー」に限定したスモーク＋回帰として運用する"
    criteria:
      - "integration タグACが統合テストでカバーされている"
      - "e2e タグACがE2Eテストでカバーされている"
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

  # Tecnos: BPMN承認を「下流生成の前提」として客観化（HITL承認が前提）
  - name: "BPMN Approval Gate"
    artifact: "basic_design"
    requires:
      - "basic_design_gate_check.process_bpmn_linked == true"
      - "basic_design_gate_check.process_bpmn_approved == true"
      - "basic_design_gate_check.ready_for_specify == true"

  - name: "Spec Gate"
    artifact: "spec"
    requires:
      - "spec_gate_check.no_blocking_open_questions == true"
      - "spec_gate_check.counts.use_cases >= spec_gate_check.rules.min_use_cases"
      - "spec_gate_check.counts.acceptance_criteria >= spec_gate_check.rules.min_total_acceptance_criteria"
      - "spec_gate_check.counts.integration_tagged_ac >= spec_gate_check.rules.min_integration_acceptance_criteria"
      - "spec_gate_check.counts.blocking_questions <= spec_gate_check.rules.max_blocking_questions"
      - "spec_gate_check.counts.nfr_items >= spec_gate_check.rules.min_nfr_items"
      - "spec_gate_check.counts.security_items >= spec_gate_check.rules.min_security_items"
      - "spec_gate_check.counts.integration_items >= spec_gate_check.rules.min_integration_items"
      - "spec_gate_check.counts.data_items >= spec_gate_check.rules.min_data_items"
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
  2) `Basic Design Gate` pass → `process.bpmn` を作成・HITL承認（Camunda 8 / DI必須）
  3) `BPMN Approval Gate` pass → `spec/plan/tasks` を生成
  4) `speckit-lint` で Gate を機械評価し、差し戻し/進行を決める

- 推奨：Spec/Plan/Tasks は Canonical YAML を AI の正本とする（人間向け文章は補助）。
- 推奨：Planの主要要素（component/library/contract/test/phase/group）は stable id を付与し、Tasks は stable id 参照のみを使う。
- 推奨：例外は必ず `{article, reason, mitigation}` の3点セットで記録する（例外が無いなら空配列）。
- 必須：Tecnosの統合・監査・運用要件は `memory/tecnos_org_constraints.md` を参照し、basic_design/spec/plan/tasks に反映する。
- 必須：Coverage Policy（AC/CT/Code）を Plan に定義し、speckit-lint で検証する。

# 7. Amendment Process
- 変更理由・影響範囲・Owners承認・SemVer更新・last_reviewed_at 記録を必須とする。
- 改訂は小さく、テンプレ参照の密結合を避ける。

> End of constitution.md
