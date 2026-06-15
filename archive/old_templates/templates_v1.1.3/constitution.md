---
artifact: "constitution"
constitution_id: "CONST-001"
title: "SDD Development Constitution (Nine Articles)"
version: "1.1.3"
status: "active" # draft | in_review | active | superseded
owners:
  - { name: "Architecture Board", role: "Owner" }
  - { name: "AI Guild", role: "Co-maintainer" }
last_reviewed_at: "YYYY-MM-DD"
amendment_history: []
---

# 1. Purpose
- Spec（WHAT/WHY）を Source of Truth とし、human/AI の行動を揃える。
- Gate（機械可読）により、生成・実装の進行/停止を客観基準で判断できるようにする。
- “原則（安定）”と“テンプレ依存（変動）”を分離し、陳腐化耐性を確保する。
- ID規約は本書に一元化し、他ドキュメントは参照（ref）で追従する。

# 2. Definitions（最小用語）
- Spec: WHAT/WHY（HOW禁止）
- Plan: HOW方針・分解・順序（コード禁止）
- Tasks: 実行可能タスク（YAML正本）
- Contracts: OpenAPI/proto/CLIなどの契約ファイル群
- Gate: *_gate_check による進行可否判定（counts/rules/boolean）
- counts: 派生フィールド（CIが算出）。人手編集を禁止する。

# 3. ID Conventions（唯一の正）
```yaml
id_conventions:
  feature_id: "^FEAT-[A-Z0-9]{3,}$"
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
```

# 4. Nine Articles（Principles & Evaluation Criteria）

> 各 Article は「Rules（守ること）」と「Criteria（評価基準）」で構成する。
> 例示は理解補助であり規範ではない。

```yaml
nine_articles:
  - id: "I"
    name: "Library-First"
    summary: "すべての機能はライブラリから始める"
    rules:
      - "ビジネスロジックはライブラリ境界に集約する"
    criteria:
      - "UI/Controller層にビジネスロジックが分散していない"
      - "主要概念がライブラリ/エンティティ名と対応している"

  - id: "II"
    name: "Contract/CLI-First"
    summary: "契約(API/CLI)を実装より先に定義する"
    rules:
      - "契約ファイルを先に作り、実装/テストはそれに従う"
    criteria:
      - "コンシューマは契約だけで利用方法を理解できる"

  - id: "III"
    name: "Test-First"
    summary: "テストを先に書き実装を導く"
    rules:
      - "主要振る舞いはテストから再現可能にする"
    criteria:
      - "主要フローが Contract/Integration/E2E のいずれかで検証される"

  - id: "IV"
    name: "Documentation-First"
    summary: "Spec/Plan/Tasks をコード前に用意する"
    rules:
      - "仕様変更は spec→plan→tasks の順で反映する"
    criteria:
      - "実装にしか存在しない要求がない"

  - id: "V"
    name: "Modularity"
    summary: "責務分離と境界の明確化"
    rules:
      - "責務が識別できる単位で分割する"
    criteria:
      - "1コンポーネントが過剰な責務を負っていない"

  - id: "VI"
    name: "Automation"
    summary: "自動化しやすい形に保つ"
    rules:
      - "spec/plan/tasks は必ず *_gate_check を持つ（counts/rules/boolean）"
      - "counts はCI算出（人手編集禁止）とする"
      - "ai_agent_config に使用コマンドを宣言する"
    criteria:
      - "CI/AIが Gate を読み取り進行可否を判定できる"

  - id: "VII"
    name: "Simplicity"
    summary: "過剰な複雑化を避ける"
    rules:
      - "複雑化は問題が顕在化するまで延期する"
    criteria:
      - "不要な多層構造・過剰分散がない"

  - id: "VIII"
    name: "Anti-Abstraction"
    summary: "不要な抽象化・ラッパーを禁止"
    rules:
      - "将来不確実性だけを根拠にラッパーを作らない"
    criteria:
      - "抽象化に明確な根拠と利用実績がある"

  - id: "IX"
    name: "Integration-First"
    summary: "統合・実環境テストを優先"
    rules:
      - "統合テスト観点（integration）が spec/plan/tasks に存在する"
    criteria:
      - "主要ユーザーフローが Integration/E2E でカバーされている"
```

# 5. Gates（Enforcement）

> Gateは「counts/rules/boolean」を持つ。
> booleanのみでの通過を禁止し、最低限の客観条件基準を rules で定義する。

```yaml
gates:
  - name: "Spec Gate"
    artifact: "spec"
    requires:
      - "spec_gate_check.no_blocking_open_questions == true"
      - "spec_gate_check.integration_critical_ac_present == true"
      - "spec_gate_check.nfr_covered == true"
      - "spec_gate_check.what_only_no_how == true"
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

* 推奨：spec/plan/tasks は Canonical YAML を AI の正本とする（人間向け文章は補助）。
* 推奨：例外は必ず `{article, reason, mitigation}` の3点セットで記録する（例外が無いなら空配列）。
* 推奨：planの主要要素（component/library/contract/test/phase/group）は stable id を付与し、tasksはID参照のみを使う。
* 推奨：countsはCIが算出し、ドキュメントとの差分があればCIで失敗させる（形骸化防止）。
* 推奨：ファイル名はスネークケースに統一する（例：`basic_design.md`）。

# 7. Amendment Process

* 変更理由・影響範囲・Owners承認・SemVer更新・last_reviewed_at記録を必須とする。
* 改訂は小さく、テンプレ参照の密結合を避ける。

> End of constitution.md