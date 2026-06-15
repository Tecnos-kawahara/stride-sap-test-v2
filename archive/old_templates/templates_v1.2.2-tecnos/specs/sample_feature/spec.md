---
artifact: "spec"
template_id: "TPL-SPEC-TECNOS-001"
feature_id: "FEAT-001"
spec_id: "SPEC-001"
version: "1.2.2-tecnos"
title: "Sample Feature Specification"
status: "draft" # draft | in_review | approved | ai_reviewed | human_approved | deprecated
owners:
  - { name: "<Business Owner>", role: "Product Owner / Business" }
  - { name: "<Tech Lead>", role: "Tech Lead" }
links:
  org_constraints_ref: "memory/tecnos_org_constraints.md"
  basic_design_ref: "specs/sample_feature/basic_design.md"
  process_bpmn_ref: "specs/sample_feature/process.bpmn"
  plan_md_ref: "specs/sample_feature/plan.md"
  tasks_md_ref: "specs/sample_feature/tasks.md"
  constitution_ref: "memory/constitution.md"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: このドキュメントの正本は **#0 Canonical Spec (YAML)**。説明文は補助。
> Constraint: ここには HOW（実装・技術選定・API設計詳細）を書かない。Planへ。
> Tecnos: 監査・統合・運用の最低要件は `{{ links.org_constraints_ref }}` を参照。

# 0. Canonical Spec (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.2.2-tecnos"

derived_fields:
  counts_are_computed: true
  counts:
    use_cases: 1
    acceptance_criteria: 3
    integration_tagged_ac: 1
    e2e_tagged_ac: 1
    blocking_questions: 0
    nfr_items: 6
    security_items: 1
    integration_items: 1
    data_items: 1

spec_gate_check:
  counts:
    use_cases: 1
    acceptance_criteria: 3
    integration_tagged_ac: 1
    e2e_tagged_ac: 1
    blocking_questions: 0
    nfr_items: 6
    security_items: 1
    integration_items: 1
    data_items: 1
  rules:
    min_use_cases: 1
    min_total_acceptance_criteria: 3
    min_integration_acceptance_criteria: 1
    max_blocking_questions: 0
    min_nfr_items: 6
    min_security_items: 1
    min_integration_items: 1
    min_data_items: 1
  no_blocking_open_questions: true
  ai_plan_ready: true

spec:
  overview:
    who: "Operations users"
    what: "Sync order data across systems"
    why: "Provide a minimal lintable spec sample"

  business_value:
    kpis: []  # 例: ["受注登録リードタイム -30%", "月次締め遅延=0"]
    financial_hypotheses:
      revenue_uplift: ""    # 例: "ARPU +X / Upsell"
      cost_reduction: ""    # 例: "工数 -Y"
      risk_reduction: ""    # 例: "監査指摘ゼロ"

  flow_reference:
    process_bpmn_path: "specs/sample_feature/process.bpmn"
    notes: ""

  goals: []
  non_goals: []

  domain_terms: []
  # - term: ""
  #   definition: ""

  use_cases:
    - id: "US-FEAT001-001"
      title: "Submit order sync request"
      primary_actor: "Operations user"
      trigger: "Order sync is requested"
      preconditions: []
      main_flow: []
      alternate_flows: []
      postconditions: []
      acceptance:
        - id: "AC-US-FEAT001-001-01"
          statement: "Integration flow completes successfully"
          tags: ["integration"]  # integration | e2e | security | performance | data | ops
          priority: "must"       # must | should | could
        - id: "AC-US-FEAT001-001-02"
          statement: "Critical journey is validated end-to-end"
          tags: ["e2e"]          # e2eタグ：重要ユーザージャーニー（スモーク回帰対象）
          priority: "must"
        - id: "AC-US-FEAT001-001-03"
          statement: "Operational logging is available"
          tags: ["ops"]
          priority: "should"

  requirements:
    # Tecnos: 統合・データ・監査の明文化を必須に寄せる
    integration:
      - "External inputs are idempotent"
    # - "外部入力は冪等で再送可能（idempotency key など）"
    # - "Correlation ID をログ/監査へ必ず出力できる"

    data_governance:
      - "SoR is defined for order data"
    # - "SoR（System of Record）をマスタ単位で定義する"
    # - "保持期間（retention）と削除方針を明記する"

    performance:
      - "P95 latency under 3s"
    availability_reliability:
      - "Retry policy is documented"
    security_privacy:
      - "Access is RBAC enforced"
    operations:
      - "Audit logs retained for 90 days"

  out_of_scope: []

  open_questions: []

  assumptions:
    - id: "A-001"
      assumption: ""
      rationale: ""
      risk_if_false: ""
```

---

# 1. Human-readable Spec（任意）
## 1.1 Goals / Non-goals
- Goals:
- Non-goals:

## 1.2 Acceptance Criteria（重要）
- ACは **テスト可能**、**曖昧語禁止**、**否定形も明確**。
- **integration** タグは統合テスト優先の印（TS-INT-* でカバー必須）。
- **e2e** タグは「重要ユーザージャーニー（スモーク回帰の対象）」の印（TS-E2E-* でカバー必須）。
  - 前提条件・テストデータ・期待結果が曖昧にならないように書く（UIセレクタ等のHOWはPlanへ）。
  - Simplicity原則に従い、全ACをe2e化しない。重要フローに限定する。

## 1.3 Non-Functional Requirements（Tecnos最小）
- **integration / data_governance / security_privacy** は最低1件ずつ。
- 監査・SoD・運用（ログ/監視/再実行性）は、外部連携の有無に関わらず論点化する。

> End of spec.md
