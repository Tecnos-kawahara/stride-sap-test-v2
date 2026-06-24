---
artifact: "spec"
template_id: "TPL-SPEC-TECNOS-001"
feature_id: "FEAT-XXX"
spec_id: "SPEC-XXX"
version: "{{TEMPLATE_VERSION}}"
title: "<Feature Name> Specification"
status: "draft" # draft | in_review | approved | ai_reviewed | human_approved | deprecated
owners:
  - { name: "<Business Owner>", role: "Product Owner / Business" }
  - { name: "<Tech Lead>", role: "Tech Lead" }
links:
  org_constraints_ref: "memory/tecnos_org_constraints.md"
  basic_design_ref: "specs/XXX_feature_name/basic_design.md"
  process_bpmn_ref: "specs/XXX_feature_name/process.bpmn"
  plan_md_ref: "specs/XXX_feature_name/plan.md"
  tasks_md_ref: "specs/XXX_feature_name/tasks.md"
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
    use_cases: 0
    acceptance_criteria: 0
    integration_tagged_ac: 0
    e2e_tagged_ac: 0
    blocking_questions: 0
    nfr_items: 0
    security_items: 0
    integration_items: 0
    data_items: 0
    spec_as_code_artifacts: 0

spec_gate_check:
  counts:
    use_cases: 0
    acceptance_criteria: 0
    integration_tagged_ac: 0
    e2e_tagged_ac: 0
    blocking_questions: 0
    nfr_items: 0
    security_items: 0
    integration_items: 0
    data_items: 0
    spec_as_code_artifacts: 0
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
  no_blocking_open_questions: false
  spec_as_code_defined: false
  ai_plan_ready: false

spec:
  overview:
    who: ""
    what: ""
    why: ""

  business_value:
    kpis: []  # 例: ["受注登録リードタイム -30%", "月次締め遅延=0"]
    financial_hypotheses:
      revenue_uplift: ""    # 例: "ARPU +X / Upsell"
      cost_reduction: ""    # 例: "工数 -Y"
      risk_reduction: ""    # 例: "監査指摘ゼロ"

  flow_reference:
    process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
    notes: ""

  goals: []
  non_goals: []

  # --- SAP Extension: localization ---
  localization:
    primary_language: "JA"          # SAP ログオン言語
    date_format: "YYYY/MM/DD"      # 日付表示形式
    decimal_notation: "X"           # 小数点表記（X=1.234,56 / Y=1,234.56）
    currency_format: "JPY"         # 通貨

  domain_terms: []
  # - term: ""
  #   definition: ""

  # --- SAP Extension: domain_terms_ref ---
  domain_terms_ref: []
  # - sap_term: ""
  #   business_term: ""
  #   table: ""                     # 関連 SAP テーブル

  use_cases:
    - id: "US-FEATXXX-001"
      title: ""
      primary_actor: ""
      trigger: ""
      preconditions: []
      main_flow: []
      alternate_flows: []
      postconditions: []
      acceptance:
        - id: "AC-US-FEATXXX-001-01"
          statement: ""
          tags: ["integration"]  # integration | e2e | security | performance | data | ops
          priority: "must"       # must | should | could
          catalog_refs: []       # SAP Extension: テストカタログ参照
        - id: "AC-US-FEATXXX-001-02"
          statement: ""
          tags: ["e2e"]          # e2eタグ：重要ユーザージャーニー（スモーク回帰対象）
          priority: "must"
          catalog_refs: []       # SAP Extension: テストカタログ参照
        - id: "AC-US-FEATXXX-001-03"
          statement: ""
          tags: ["ops"]
          priority: "should"
          catalog_refs: []       # SAP Extension: テストカタログ参照

  requirements:
    # Tecnos: 統合・データ・監査の明文化を必須に寄せる
    integration: []
    # - "外部入力は冪等で再送可能（idempotency key など）"
    # - "Correlation ID をログ/監査へ必ず出力できる"

    data_governance: []
    # - "SoR（System of Record）をマスタ単位で定義する"
    # - "保持期間（retention）と削除方針を明記する"

    performance: []
    availability_reliability: []
    security_privacy: []
    operations: []

  # --- SAP Extension: sap_specifics ---
  sap_specifics:
    authorization_objects:
      - object: ""                  # 権限オブジェクト名
        fields: []                  # 権限フィールド
        description: ""
    message_class: ""               # メッセージクラス名
    enhancement_points: []          # 拡張ポイント一覧

  spec_as_code:
    # Spec-as-Code minimum (Tecnos): machine-readable artifacts for AI/HITL validation
    artifacts:
      - type: "openapi"
        path: "specs/XXX_feature_name/contracts/openapi.yaml"
        schema_version: "3.1.0"
        status: "draft"
      - type: "database_schema"    # v1.2.5追加（DB未使用なら削除可）
        path: "specs/XXX_feature_name/contracts/database_schema.yaml"
        schema_version: "1.0"
        status: "draft"
      - type: "schema_json"        # v4.8.0追加（AI/RAG向け自動生成物、DB使用+ai_metadata有効時）
        path: "docs/schema/XXX_feature_name/schema.json"
        schema_version: "1.0"
        status: "not_applicable"    # ai_metadata有効化後に "generated" へ変更
      - type: "migration_mapping"
        path: "specs/XXX_feature_name/implementation-details/migration_mapping.yaml"
        schema_version: "1.0"
        status: "draft"
      - type: "authz_matrix"
        path: "specs/XXX_feature_name/implementation-details/authz_matrix.yaml"
        schema_version: "1.0"
        status: "draft"
      - type: "test_scenarios"
        path: "specs/XXX_feature_name/tests/scenarios.yaml"
        schema_version: "1.0"
        status: "draft"
    validation:
      schema_validation: true
      lint_required: true

  out_of_scope: []

  open_questions:
    - id: "Q-001"
      question: ""
      blocking: true
      owner: ""
      due: "YYYY-MM-DD"

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
- **catalog_refs** は各ACに対応するSAPテストカタログエントリを参照する（SAP Extension）。

## 1.3 Non-Functional Requirements（Tecnos最小）
- **integration / data_governance / security_privacy** は最低1件ずつ。
- 監査・SoD・運用（ログ/監視/再実行性）は、外部連携の有無に関わらず論点化する。

## 1.4 Spec-as-Code（AI/HITL前提）
- OpenAPI / 移行マッピング / 権限マトリクス / テストシナリオを **機械可読（YAML/JSON）** で用意する。
- `spec.spec_as_code.artifacts` に **必ずパスを列挙** し、schema/lint で検証可能にする。

## 1.5 SAP Extension セクション
- **localization**: SAP ログオン言語・日付形式・通貨形式・数値形式を定義する。basic_design.business_requirements.localization を源泉とし、spec レベルで具体化する。
- **domain_terms_ref**: SAP 標準用語と業務用語のマッピング。glossary_ref_validator が参照先存在を検証する。
- **sap_specifics**: 権限オブジェクト（authorization_objects）、メッセージクラス（message_class）、拡張ポイント（enhancement_points）を定義する。

> End of spec.md
