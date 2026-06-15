---
artifact: "spec"
template_id: "TPL-SPEC-TECNOS-001"
feature_id: "FEAT-001"
spec_id: "SPEC-001"
version: "{{TEMPLATE_VERSION}}"
title: "Web-EDI受注受付 Specification"
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
id_conventions_version: "{{TEMPLATE_VERSION}}"

derived_fields:
  counts_are_computed: true
  counts:
    use_cases: 1
    acceptance_criteria: 3
    integration_tagged_ac: 3
    e2e_tagged_ac: 1
    blocking_questions: 0
    nfr_items: 6
    security_items: 1
    integration_items: 1
    data_items: 1
    spec_as_code_artifacts: 4

spec_gate_check:
  counts:
    use_cases: 1
    acceptance_criteria: 3
    integration_tagged_ac: 3
    e2e_tagged_ac: 1
    blocking_questions: 0
    nfr_items: 6
    security_items: 1
    integration_items: 1
    data_items: 1
    spec_as_code_artifacts: 4
  rules:
    min_use_cases: 1
    min_total_acceptance_criteria: 3
    min_integration_acceptance_criteria: 1
    max_blocking_questions: 0
    min_nfr_items: 6
    min_security_items: 1
    min_integration_items: 1
    min_data_items: 1
    min_spec_as_code_artifacts: 1
  no_blocking_open_questions: true
  spec_as_code_defined: true
  ai_plan_ready: true

spec:
  overview:
    who: "取引先の購買担当者が、Web-EDIポータルから発注する"
    what: "発注データを送信し、受注番号と納期回答を受け取る"
    why: "手入力と確認作業を減らし、受注処理のスピードと正確性を高める"

  business_value:
    kpis:
      - "受注登録時間: 20分 → 5分（75%削減）"
      - "誤入力率: 1.0% → 0.1%"
      - "問い合わせ件数: 月200件 → 月80件"
    financial_hypotheses:
      revenue_uplift: "納期回答の早期化による取りこぼし削減（売上+2%を期待）"
      cost_reduction: "受注入力工数削減（年間600時間）"
      risk_reduction: "誤入力による出荷トラブルの低減"

  flow_reference:
    process_bpmn_path: "specs/sample_feature/process.bpmn"
    notes: ""

  goals:
    - "Web-EDI発注受付"
    - "受注番号と納期回答の即時返却"
    - "発注データの自動登録"

  non_goals:
    - "請求書発行・入金処理"
    - "EDI標準(JCA/EDI)との相互接続"
    - "モバイルアプリ対応"
    - "出荷通知の自動連携（Phase 2）"

  domain_terms:
    - term: "Web-EDI"
      definition: "取引先がブラウザから発注を入力・送信できる仕組み"
    - term: "受注番号"
      definition: "ERPで発番される受注の識別子"
    - term: "取引先コード"
      definition: "ERP上で取引先を識別するID"
    - term: "SoR"
      definition: "System of Record - データの正本を保持するシステム"

  use_cases:
    - id: "US-FEAT001-001"
      title: "Web-EDI発注送信"
      primary_actor: "取引先購買担当者"
      trigger: "Web-EDIで発注を送信"
      preconditions:
        - "取引先が有効な取引先コードでログイン済み"
        - "商品マスタがERPに登録済み"
      main_flow:
        - "取引先が発注データを入力またはCSVアップロードする"
        - "システムが必須項目と商品コードを検証する"
        - "システムがERPに受注を登録する"
        - "システムが受注番号と納期回答を表示する"
      alternate_flows:
        - "商品コードが無効な場合、エラーメッセージを表示する"
      postconditions:
        - "受注番号と納期回答が画面に表示されている"
      acceptance:
        - id: "AC-US-FEAT001-001-01"
          statement: "取引先ID「P-1001」で発注CSV(10行)をアップロードすると、60秒以内に受注番号「SO-2025-000123」が表示される"
          tags: ["integration", "performance"]  # integration | e2e | security | performance | data | ops
          priority: "must"       # must | should | could
        - id: "AC-US-FEAT001-001-02"
          statement: "発注数量が在庫不足の場合、納期回答日（YYYY-MM-DD）が表示される"
          tags: ["integration", "e2e"]          # e2eタグ：重要ユーザージャーニー（スモーク回帰対象）
          priority: "must"
        - id: "AC-US-FEAT001-001-03"
          statement: "未登録商品コードを含む発注は、「商品コードが無効です」エラーが表示され、受注は登録されない"
          tags: ["integration"]
          priority: "must"

  requirements:
    # Tecnos: 統合・データ・監査の明文化を必須に寄せる
    integration:
      - "ERP受注登録APIは最大3回リトライし、Correlation IDを付与する"
    # - "外部入力は冪等で再送可能（idempotency key など）"
    # - "Correlation ID をログ/監査へ必ず出力できる"

    data_governance:
      - "受注データのSoRはERPとする"
    # - "SoR（System of Record）をマスタ単位で定義する"
    # - "保持期間（retention）と削除方針を明記する"

    performance:
      - "P95 < 60秒"
    availability_reliability:
      - "可用性99.5%（月間ダウンタイム3.6時間以内）"
    security_privacy:
      - "取引先コード単位でアクセス制御する"
    operations:
      - "監査ログは7年間保持する"

  spec_as_code:
    artifacts:
      - type: "openapi"
        path: "specs/sample_feature/contracts/openapi.yaml"
        schema_version: "3.1.0"
        status: "draft"
      - type: "migration_mapping"
        path: "specs/sample_feature/implementation-details/migration_mapping.yaml"
        schema_version: "1.0"
        status: "draft"
      - type: "authz_matrix"
        path: "specs/sample_feature/implementation-details/authz_matrix.yaml"
        schema_version: "1.0"
        status: "draft"
      - type: "test_scenarios"
        path: "specs/sample_feature/tests/scenarios.yaml"
        schema_version: "1.0"
        status: "draft"
    validation:
      schema_validation: true
      lint_required: true

  out_of_scope: []

  open_questions: []

  assumptions:
    - id: "A-001"
      assumption: "取引先マスタがERPに登録済み"
      rationale: "未登録の取引先は受注登録できない"
      risk_if_false: "マスタ整備が先行タスクになり、開始が遅れる"
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

## 1.4 Spec-as-Code（AI/HITL前提）
- OpenAPI / 移行マッピング / 権限マトリクス / テストシナリオを **機械可読（YAML/JSON）** で用意する。
- `spec.spec_as_code.artifacts` に **必ずパスを列挙** する。

> End of spec.md
