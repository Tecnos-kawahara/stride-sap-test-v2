---
artifact: "basic_design"
template_id: "TPL-BD-TECNOS-001"
feature_id: "FEAT-XXX"
basic_design_id: "BD-XXX"
title: "Basic Design - <Feature Name>"
version: "{{TEMPLATE_VERSION}}"
status: "draft" # draft | in_review | approved | released | deprecated
owners:
  - { name: "<Business Owner>", role: "Product Owner / Business" }
  - { name: "<Tech Lead>", role: "Tech Lead / Architect" }
  - { name: "<PMO>", role: "PMO (TEIM)" }
reviewers:
  - { name: "QA Lead", role: "Quality" }
  - { name: "Security Lead", role: "Security" }
  - { name: "ERP/Integration Lead", role: "ERP/Integration" }
links:
  org_constraints_ref: "memory/tecnos_org_constraints.md"
  artifact_registry_ref: "memory/artifact_registry.md"
  ai_policy_ref: "memory/tecnos_org_constraints.md#6.3"
  raci_plus_ref: "memory/tecnos_org_constraints.md#6.4"
  process_bpmn_ref: "specs/XXX_feature_name/process.bpmn"
  spec_md_ref: "specs/XXX_feature_name/spec.md"
  plan_md_ref: "specs/XXX_feature_name/plan.md"
  tasks_md_ref: "specs/XXX_feature_name/tasks.md"
  constitution_ref: "memory/constitution.md"
  # v6.0 Phase C: VALUE Upstream Extension references — populated by `stride upstream-bridge --apply`
  upstream_dir_ref: "specs/XXX_feature_name/upstream/"
  upstream_policy_ref: "shared/policies/upstream_policy.yaml"
  baccm_completeness_ref: "shared/policies/baccm_completeness.yaml"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> **Rule-0**: このドキュメントの正本は **#0 Canonical Basic Design (YAML)**。
>
> ## ドキュメント構造
> | セクション | 種別 | 編集方法 |
> |-----------|------|----------|
> | #0 YAML | **正本（SSoT）** | 直接編集可 |
> | #1 Document Intent | 読み方ガイド | 固定（編集不要） |
> | #2 Traceability | AI生成ビュー | YAML変更後にAIが再生成 |
> | #3 Part A | AI生成ビュー | YAML変更後にAIが再生成 |
> | #4 Part B | AI生成ビュー | YAML変更後にAIが再生成 |
> | #5 Part C | AI生成ビュー | YAML変更後にAIが再生成 |
> | #6 Decision Log | AI生成ビュー | YAML変更後にAIが再生成 |
> | #7 Checks | **ゲート状態** | 手動管理（AIは再生成しない） |
>
> ## 修正ワークフロー
> ```
> 1. #0 YAML セクションを編集
> 2. AIに「YAMLを更新したので、ビューを再生成して」と依頼
> 3. AI が #2～#6 を YAML に基づいて再生成
>    ⚠️ #7 Checks はゲート状態のため再生成しない
> 4. stride lint で検証
> ```
>
> ## 推奨ワークフロー（新規作成時）
> 1. `stride intake <feature>` で簡易入力フォームを作成
> 2. `basic_design_intake.md` を記入（10-15分）
> 3. AIに「この intake から basic_design.md を生成」と依頼
> 4. 生成された本ファイルをレビュー・承認
>
> **Purpose**: 人間の任意テキスト入力を、AIがSDD（BPMN→Spec/Plan/Tasks）へ落とす前に「認識齟齬」を潰すハブ。
> **Tecnos**: 統合・監査・運用・AgentOpsの最低要件は `{{ links.org_constraints_ref }}` を参照。
> **v1.2.5**: Intake-First ワークフロー、Database Schema 対応、RACI+/AI Policy/Artifact Registry/Delivery Model を明示。

# 0. Canonical Basic Design (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "{{TEMPLATE_VERSION}}"

policy_refs:
  org_constraints_ref: "memory/tecnos_org_constraints.md"
  artifact_registry_ref: "memory/artifact_registry.md"
  ai_policy_ref: "memory/tecnos_org_constraints.md#6.3"
  raci_plus_ref: "memory/tecnos_org_constraints.md#6.4"

derived_fields:
  counts_are_computed: true
  counts:
    traceability_rows: 0
    integration_flows: 0
    blocking_questions: 0

basic_design:
  # Profile (v5.4) — 報告粒度 + Completeness 閾値の切替軸（SSoT）
  # enterprise-erp | saas-integration | prototype
  # Profile で切り替わるのは「Task Completion Report のフォーマット」と
  # 「湖/海判定の閾値」のみ。BPMN / Evidence / SEC-006 / Ops Pack /
  # Epic-Feature Hierarchy / Coverage Tier 宣言 は全 Profile 共通（現行正本を維持）。
  # 詳細: shared/policies/profile_policy.yaml
  profile: "enterprise-erp"   # enterprise-erp (default) | saas-integration | prototype

  # Enterprise Extension Fields (v1.2.6)
  # epic_ref: Epicに属する場合のみ設定（任意）
  # team_id: チーム割り当て（エンタープライズモード時は必須）
  # coverage_tier: critical | standard | experimental（デフォルト: standard）
  epic_ref: null              # 例: "EPIC-ORDER" - Epicに属する場合
  team_id: null               # 例: "TEAM-A" - チーム割り当て
  coverage_tier: "standard"   # critical | standard | experimental

  # Autonomy Bias (v3.1) - Project-level mode adjustment preference
  # Controls how strictly STRIDE enforces mode checkpoints
  # autonomous: fewer checkpoints (AI trusted more)
  # balanced: standard behavior (default)
  # controlled: more checkpoints (more human oversight)
  autonomy_bias: "balanced"    # autonomous | balanced | controlled

  # ED/CF Score (v4.6.0) - Execution Determinism / Conversational Flexibility tradeoff
  # Reference: Cook et al. (2026) arXiv:2603.06394
  # execution_determinism: 実行の決定性・再現性（1=低, 5=高）
  # conversational_flexibility: 対話的探索の柔軟性（1=低, 5=高）
  # Recommended defaults by coverage_tier:
  #   critical:     ED=5, CF=2 (maximum reproducibility, minimal flexibility)
  #   standard:     ED=4, CF=3 (balanced)
  #   experimental: ED=3, CF=4 (more exploration, less gate enforcement)
  ed_cf_score:
    execution_determinism: 4     # 1-5
    conversational_flexibility: 3  # 1-5

  # Escalation Flags (v1.2.6) - triggers additional approval requirements
  # These flags trigger escalation rules defined in approval_matrix.yaml:
  # - security_sensitive + critical tier → SECURITY_OFFICER
  # - erp_integration (any tier) → ARCH_BOARD
  security_sensitive: false   # true if handles PII, authentication, encryption
  erp_integration: false      # true if direct ERP DB/API integration

  organization:
    company: "Tecnos Japan"
    strategy_alignment:
      mid_term_plan: "2027-2032"
      target_state: ""  # 例: "現状 → 目標状態"
    program_ref:
      portfolio_items: []   # 例: ["2-11", "2-21"]（全社横断PJ番号など）
    delivery_methods:
      - "TEIM"
      - "PMBOK"
      - "SAP Activate"
    ai_governance:
      guideline_ref: "AI Guidelines v6 (ISO/IEC 42001 series)"
      policy_ref: "memory/tecnos_org_constraints.md#6.3"
      human_in_the_loop: true
      provenance_required: true

  delivery_model:
    type: "requirements-driven"   # requirements-driven | ftos | hybrid | ddd
    rationale: ""
    ftos_exit_criteria:
      enabled: false
      criteria:
        - ""
    ddd_policy:
      enabled: false
      activation_mode: "validate"  # autopilot | confirm | validate
      domain_model_ref: "specs/XXX_feature_name/implementation-details/domain_model.md"
      technical_design_ref: "specs/XXX_feature_name/implementation-details/technical_design.md"
      adr_index_ref: "shared/decisions/decision-index.md"

  raci_plus:
    actors:
      - "TJ_Human_PM"
      - "TJ_Human_TechLead"
      - "TJ_AI_CodingAgent"
      - "TJ_CI_Gate"
      - "Customer_BizOwner"
      - "Customer_ITOwner"
    rules:
      - "AIはAccountableになれない（Aは人間のみ）"
      - "Merge/Release/GoNoGoはHuman A + CI passが前提"
      - "AI生成物はProvenanceを必須記録"

  context:
    who: ""     # 想定ユーザー/ステークホルダー（業務・IT・監査を含む）
    what: ""    # 何を実現するか（価値）
    why: ""     # なぜ今それが必要か（背景・課題）

  business_domain:
    value_chain: ""     # 例: O2C / P2P / M2O / R2R
    capability: ""      # 例: 調達DX / 生産DX / 営業DX / 原価管理
    domain_objects: []  # 例: ["Customer", "Vendor", "Material", "Order", "PurchaseOrder"]

  scope:
    in: []
    out: []

  # 対象システム（統合・監査の前提）
  systems:
    - system: "SAP"
      category: "ERP"
      owner: ""
      integration_modes: ["API(OData/REST/SOAP)", "IDoc", "File/Batch"]
    - system: "mcframe"
      category: "ERP/Manufacturing"
      owner: ""
      integration_modes: ["API", "File/Batch"]
    - system: "Salesforce"
      category: "CRM"
      owner: ""
      integration_modes: ["API", "Event"]

  # データベース仕様（v1.2.5追加・任意 / v4.8.0拡張: ライフサイクル管理）
  database:
    enabled: false  # false の場合は外部システムのみ
    schema_ref: "specs/XXX_feature_name/contracts/database_schema.yaml"  # enabled=falseなら空でも可
    dialect: "postgresql"  # postgresql | mysql | oracle | sqlserver | sqlite
    sor_tables: []  # このfeatureがSoR(System of Record)となるテーブル
    referenced_tables: []  # 他featureから参照するテーブル
    migration_strategy: "versioned"  # versioned | state-based
    migration_tool: ""  # alembic | flyway | liquibase | prisma | drizzle | atlas | custom

    # v4.8.0: SSOT Model & AI Metadata
    ssot_model: "db-first"  # db-first | orm-driven | declarative
    #   db-first:     migrations/ が設計と配備の両方を兼ねる（エンタープライズ/Polyglot標準）
    #   orm-driven:   ORM schema（Prisma/Drizzle等）が設計SSOT、migrations/ が配備SSOT
    #   declarative:  宣言的DDL（Atlas等）が設計SSOT、migrations/ が配備SSOT
    design_ssot: ""           # 設計SSOTのパス（orm-driven/declarative時に記入）
                              #   例: "prisma/schema.prisma", "src/db/schema.ts", "schema.hcl"
                              #   db-first の場合は空（migrations/ が兼ねる）
    deployment_ssot: ""       # 配備SSOTのパス（例: "migrations/", "prisma/migrations/"）
    ai_metadata:
      enabled: false          # AI向けメタデータ自動生成を使用するか
      generator: ""           # tbls | custom
      config_path: ""         # .tbls.yml のパス（generator=tbls時）
      outputs: []
      #   - type: "markdown"  # markdown | mermaid | json | dbml
      #     path: "docs/schema/XXX_feature_name/"
      #   - type: "mermaid"
      #     path: "docs/schema/XXX_feature_name/erd.mmd"
      #   - type: "json"
      #     path: "docs/schema/XXX_feature_name/schema.json"
      #   - type: "dbml"      # optional: 外部共有用
      #     path: "docs/schema/XXX_feature_name/database.dbml"
      ci_regenerate: false    # CI（PR マージ時等）で自動再生成するか
      lint_rules:
        # NOTE: ここは設計意図の宣言。stride-lint の実際の閾値は
        # database_schema.yaml の database_schema_gate_check.rules が正本。
        # 両者の値を一致させること。
        description_coverage_min: 0.95  # テーブル・カラム説明の網羅率（0.0〜1.0）
        migration_forward_only: true    # 適用済み migration の書き換え禁止

  data_policy:
    contains_personal_data: false
    data_classes: ["Public", "Internal", "Confidential", "Regulated(PII/契約/財務)"]
    audit_log_required: true
    retention_policy: ""  # 例: "7 years (accounting)", "90 days (logs)"

  agentops_policy:
    enabled: true
    allowed_action_categories: ["read", "draft", "propose"]  # read | draft | propose | execute
    production_execute_requires: "human approval"
    provenance_required: true
    evidence_pack_required: true
    kill_switch:
      enabled: true
      conditions: []   # 例: ["unexpected write", "policy violation", "security incident"]

  # v1.2.3: E2E/AIエージェントループ方針
  e2e_policy:
    scope: "critical-user-journeys"  # critical-user-journeys | smoke-only | none
    playwright_mcp:
      enabled: true
      usage: ["explore", "generate_test_skeleton", "reproduce_failure", "triage_report"]
      prohibited_in_ci_gate: true
    ci_gate:
      deterministic: true
      runner: "playwright-test"
    triage_flow:
      categories: ["product_bug", "spec_gap", "test_bug", "flake"]
      feedback_to: ["spec", "plan", "tasks"]

  # BPMN 業務記述正本: BPMN 要素ごとの業務説明（traceability_rows は AC/Contract/Test 正本として別管理）
  # ⚠️ MUST: 以下の bpmn_id / process_id は process.bpmn 内の実 id と完全一致させる。
  # AI はルール literal-follow: process.bpmn の <bpmn:userTask id="BPMN-TASK-001"> を書いたら
  # ここの elements[].bpmn_id も "BPMN-TASK-001" にする。ID を勝手に変えるな。
  # 参照: agent_docs/sdd_bootstrap.md §4-BPMN, sdd-templates/docs/bpmn_quick_reference.md
  bpmn_descriptions:
    process:
      process_id: "BPMN-PROC-XXX"
      purpose: "{{プロセス概要}}"
      start_condition: "{{開始条件}}"
      end_condition: "{{完了条件}}"
      business_outcome: "{{ビジネス成果}}"
      primary_actors: ["{{主要アクター}}"]
    elements:
      - bpmn_id: "BPMN-TASK-001"
        name: "{{ユーザータスク名}}"
        type: "userTask"
        purpose: "{{業務目的}}"
        business_role: "{{業務上の役割}}"
        trigger: "{{トリガー条件}}"
        inputs: ["{{主入力}}"]
        outputs: ["{{主出力}}"]
        business_rules: []
        exceptions: []
      - bpmn_id: "BPMN-TASK-002"
        name: "{{サービスタスク名}}"
        type: "serviceTask"
        purpose: "{{業務目的}}"
        business_role: "{{業務上の役割}}"
        trigger: "{{トリガー条件}}"
        inputs: ["{{主入力}}"]
        outputs: ["{{主出力}}"]
        business_rules: []
        exceptions: []
      - bpmn_id: "BPMN-GW-001"
        name: "{{分岐条件名}}"
        type: "exclusiveGateway"
        purpose: "{{分岐の業務意味}}"
        business_role: "{{判定基準}}"
        trigger: "{{判定のトリガー}}"
        inputs: ["{{判定対象データ}}"]
        outputs: ["{{判定結果}}"]
        business_rules: ["{{ビジネスルール}}"]
        exceptions: []

  flow_reference:
    process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
    bpmn_element_id_convention: "BPMN-(TASK|GW|EVT|FLOW)-NNN"

  # Integration critical flows（SLO/KPIが絡む重要フロー）
  integration_flows:
    - id: "FLOW-001"
      name: ""
      summary: ""
      kpi_slo: ""  # 例: "月次締め遅延=0 / 受注登録P95<3s"
      e2e_target: true  # v1.2.3: E2Eスモーク回帰の対象にするか

  # 最重要：抜け漏れ検出（空欄は許容。ただし ready_for_bpmn/ready_for_specify を立てる前に埋める）
  traceability_rows:
    - rq:
        id: "RQ-001"
        statement: ""
      us:
        id: "US-FEATXXX-001"     # 未確定なら "" でも可
        title: ""
      ac:
        id: "AC-US-FEATXXX-001-01"  # 未確定なら "" でも可
        statement: ""
        tags: ["integration"]
      bpmn:
        id: "BPMN-TASK-001"      # 未確定なら "" でも可
        name: ""
      contract:
        id: "CT-API-01"          # 未確定なら "" でも可（FILE/BATCH/EDI/IDOCも可）
      database:                   # v1.2.5追加：関連DBテーブル
        tables: []               # 例: ["orders", "order_items"]
        operations: []           # 例: ["INSERT", "UPDATE", "SELECT"]
      test:
        id: "TS-INT-01"          # 未確定なら "" でも可
        type: "integration"
      task:
        id: "T-G01-001"          # 未確定なら "" でも可
    # v1.2.3: E2Eタグ付きACの例
    - rq:
        id: "RQ-002"
        statement: ""
      us:
        id: "US-FEATXXX-001"
        title: ""
      ac:
        id: "AC-US-FEATXXX-001-02"
        statement: ""
        tags: ["e2e"]             # E2Eスモーク回帰の対象
      bpmn:
        id: "BPMN-TASK-001"
        name: ""
      contract:
        id: "CT-API-01"
      database:                   # v1.2.5追加
        tables: []
        operations: []
      test:
        id: "TS-E2E-01"           # E2Eテスト
        type: "e2e"
      task:
        id: "T-G04-002"

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

  decisions:
    - id: "DR-001"
      context: ""
      options:
        - ""
      decision: ""
      consequences: ""

  # 例外は必ず憲法（Article）に紐付け、reason/mitigation をセットで残す
  exceptions: []
  # - article: "V"
  #   reason: "ERP本体DB直結が避けられない"
  #   mitigation: "Read-only view + 監査ログ + 期間限定 + 移行計画"
```

---

# 1. Document Intent（読み方）
## 1.1 推奨読み順（レビュー最短経路）
1) **2. Traceability（要件→US→AC→BPMN→契約→テスト→タスク）**
2) 3. Part A（WHAT/WHY要約）
3) 4. Part B（HOW方針：境界・契約・テスト・統合・例外）
4) 5. Part C（運用・フィードバックループ）
5) 6. Decision Log（判断の根拠）

## 1.2 アーティファクト対応（ハブ）
| Artifact | Path | Role | Owner |
|---|---|---|---|
| process.bpmn | {{ links.process_bpmn_ref }} | 業務フロー正本（Camunda 8形式、HITL承認） | PO/TL |
| spec.md | {{ links.spec_md_ref }} | WHAT/WHY（HOW禁止） | PO |
| plan.md | {{ links.plan_md_ref }} | HOW方針・分解・順序（コード禁止） | TL |
| tasks.md | {{ links.tasks_md_ref }} | 実行可能タスク（実装前の正本） | TL |
| constitution.md | {{ links.constitution_ref }} | 原則 / ID規約 / Gate | Arch |
| tecnos_org_constraints.md | {{ links.org_constraints_ref }} | 組織制約（統合/監査/運用/AgentOps/E2E） | PMO/Arch |
| artifact_registry.md | {{ links.artifact_registry_ref }} | 成果物マスター（ID/版/保管先） | PMO |

---

# 2. Traceability（最重要：抜け漏れ検出のビュー）
> ⚠️ **AI生成ビュー**: このセクションは `#0 YAML` の `basic_design.traceability_rows` から自動生成されます。
> 直接編集しないでください。変更は YAML セクションで行い、AIに再生成を依頼してください。

<!-- AI-GENERATED: traceability_rows から自動生成 -->
| RQ | US | AC | Tags | BPMN | Contract | Database | Test | Task |
|---|---|---|---|---|---|---|---|---|
| RQ-001 | US-FEATXXX-001 | AC-US-FEATXXX-001-01 | integration | BPMN-TASK-001 | CT-API-01 | (tables) | TS-INT-01 | T-G01-001 |
| RQ-002 | US-FEATXXX-001 | AC-US-FEATXXX-001-02 | e2e | BPMN-TASK-001 | CT-API-01 | (tables) | TS-E2E-01 | T-G04-002 |
<!-- END AI-GENERATED -->

---

# 3. Part A. WHAT/WHY Summary（Specに落とす前の理解合わせ）
> ⚠️ **AI生成ビュー**: このセクションは `#0 YAML` の `basic_design.context`, `scope` から自動生成されます。
> 直接編集しないでください。変更は YAML セクションで行い、AIに再生成を依頼してください。

<!-- AI-GENERATED: basic_design.context, scope から自動生成 -->
- **Who**: `{{ basic_design.context.who }}`
- **What**: `{{ basic_design.context.what }}`
- **Why**: `{{ basic_design.context.why }}`
- **Goals (In Scope)**: `{{ basic_design.scope.in | join(", ") }}`
- **Non-goals (Out of Scope)**: `{{ basic_design.scope.out | join(", ") }}`
- **Value metric**: `{{ basic_design.business_domain.capability }}` による価値創出
<!-- END AI-GENERATED -->

---

# 4. Part B. HOW Policy（BPMN/Planに渡す"実装方針"インターフェース）
> ⚠️ **AI生成ビュー**: このセクションは `#0 YAML` の `systems`, `database`, `integration_flows`, `data_policy`, `agentops_policy`, `e2e_policy` から自動生成されます。
> 直接編集しないでください。変更は YAML セクションで行い、AIに再生成を依頼してください。

<!-- AI-GENERATED: basic_design.systems, database, etc. から自動生成 -->
## B.1 境界（ERP/SCM/CRM）
- **SoR（System of Record: データ所有）**: `{{ basic_design.systems | selectattr("category", "equalto", "ERP") | map(attribute="system") | join(", ") }}`
- **対象システム**: `{{ basic_design.systems | map(attribute="system") | join(", ") }}`
- **統合モード**: 各システムの `integration_modes` を参照
- **直接DB連携など禁止事項の例外有無**: `{{ "あり（exceptionsを参照）" if basic_design.exceptions else "なし" }}`

## B.2 契約（Contract/CLI-First）
- **Contract list**:
  - CT-API-*: REST/OData API契約
  - CT-EVT-*: イベント契約
  - CT-FILE-*: ファイル連携契約
  - CT-IDOC-*: IDoc連携契約
- **Versioning policy**: セマンティックバージョニング
- **統合クリティカル契約**: `{{ basic_design.integration_flows | selectattr("kpi_slo") | map(attribute="name") | join(", ") }}`

## B.2.1 データベース設計（v1.2.5追加）
- **Database enabled**: `{{ basic_design.database.enabled }}`
- **Schema ref**: `{{ basic_design.database.schema_ref }}`
- **Dialect**: `{{ basic_design.database.dialect }}`
- **SoRテーブル**: `{{ basic_design.database.sor_tables | join(", ") }}`
- **参照テーブル**: `{{ basic_design.database.referenced_tables | join(", ") }}`
- **マイグレーション戦略**: `{{ basic_design.database.migration_strategy }}`
- **マイグレーションツール**: `{{ basic_design.database.migration_tool }}`
- **監査カラム**: 必須（created_at, updated_at, created_by, updated_by）
- **SSOTモデル**: `{{ basic_design.database.get("ssot_model") or "db-first" }}`
- **設計SSOT**: `{{ basic_design.database.get("design_ssot") or "(migrations/が兼ねる)" }}`
- **配備SSOT**: `{{ basic_design.database.get("deployment_ssot") or "(未定義)" }}`
- **AIメタデータ生成**: `{{ "有効 (" + basic_design.database.get("ai_metadata", {}).get("generator", "") + ")" if basic_design.database.get("ai_metadata", {}).get("enabled") else "無効" }}`
- **説明網羅率ゲート**: `{{ (basic_design.database.get("ai_metadata", {}).get("lint_rules", {}).get("description_coverage_min", 0.95) * 100) | int }}%`（※stride-lint の実閾値は `database_schema_gate_check.rules` が正本）

## B.3 テスト戦略（Test/Integration-First）
- **Contract tests (TS-CON-*)**: 全CTをカバー
- **Integration tests (TS-INT-*)**: integrationタグ付きACをカバー（可能なら実システム/実コネクタ）
- **E2E tests (TS-E2E-*)**: **e2eタグ付きAC（重要ユーザージャーニー）のみ**
- **Unit tests (TS-UT-*)**: ビジネスロジック層をカバー

### B.3.1 Coverage Policy（v1.2.3）
- **AC Coverage**: 100%（全ACが少なくとも1つのTSでカバー）
- **CT Coverage**: 100%（全CTがTS-CONでカバー）
- **Code Coverage**: LIB=85%/75%、CMP=60%/50%（目標、例外は記録）
- **E2E対象選定**: e2eタグは「integration_flows で e2e_target=true のもの」に限定

## B.4 Ops / Audit（監査・運用）
- **監査ログ**: `{{ "必須" if basic_design.data_policy.audit_log_required else "任意" }}`
- **データ分類**: `{{ basic_design.data_policy.data_classes | join(", ") }}`
- **保持期間**: `{{ basic_design.data_policy.retention_policy }}`
- **SoD**: RACI+定義に基づく（`{{ links.raci_plus_ref }}`）
- **障害時**: 冪等性を確保し、再実行可能な設計

## B.5 Automation / AgentOps
- **Agents（想定）**: `{{ basic_design.agentops_policy.allowed_action_categories | join(", ") }}` 操作を許可
- **Allowed operations**: `{{ basic_design.agentops_policy.allowed_action_categories | join(", ") }}`
- **Forbidden operations**: execute（本番環境への直接実行は `{{ basic_design.agentops_policy.production_execute_requires }}` が必要）
- **Human approval points**: Merge/Release/GoNoGo
- **Kill switch**: `{{ "有効" if basic_design.agentops_policy.kill_switch.enabled else "無効" }}`

### B.5.1 E2E Testing Policy（v1.2.3）
- **二重ループ設計**:
  - 内側ループ（高速反復）: AI + Playwright MCP で探索・再現・テスト骨格生成・失敗解析
  - 外側ループ（品質ゲート）: CIで決定論的にPlaywright Test（E2E）を実行
- **E2Eスコープ**: `{{ basic_design.e2e_policy.scope }}`
- **MCPの位置付け**: `{{ basic_design.e2e_policy.playwright_mcp.usage | join(", ") }}`（CIゲートでは使わない）
- **Triage手順**: `specs/<feature>/implementation-details/e2e-triage.md` に定義

## B.6 例外管理（Simplicity / Anti-Abstraction）
- **Exceptions**: `{{ basic_design.exceptions | length }}` 件
<!-- exceptions があれば以下に展開 -->
<!-- END AI-GENERATED -->

---

# 5. Part C. Operations / Feedback Loop（運用から仕様へ還流）
> ⚠️ **AI生成ビュー**: このセクションは `#0 YAML` の `e2e_policy.triage_flow`, `integration_flows` から自動生成されます。
> 直接編集しないでください。変更は YAML セクションで行い、AIに再生成を依頼してください。

<!-- AI-GENERATED: e2e_policy, integration_flows から自動生成 -->
- **Observability**: metrics/logs/traces（各 integration_flow のKPI/SLOに基づく）
- **SLO/KPI**: `{{ basic_design.integration_flows | map(attribute="kpi_slo") | select | join("; ") }}`
- **Incident feedback**: Spec/Plan への還流ルール（triage_flow.feedback_to に基づく）
- **Security feedback**: `{{ links.org_constraints_ref }}` を更新
- **Release/rollback policy**: CI Gate + Human Approval
- **E2E failure feedback**: `{{ basic_design.e2e_policy.triage_flow.categories | join("/") }}` → `{{ basic_design.e2e_policy.triage_flow.feedback_to | join("/") }}` へ還流
<!-- END AI-GENERATED -->

---

# 6. Decision Log（判断の根拠）
> ⚠️ **AI生成ビュー**: このセクションは `#0 YAML` の `basic_design.decisions` から自動生成されます。
> 直接編集しないでください。変更は YAML セクションで行い、AIに再生成を依頼してください。

<!-- AI-GENERATED: basic_design.decisions から自動生成 -->
| ID | Context | Options | Decision | Consequences |
|---|---|---|---|---|
| DR-001 | `{{ decisions[0].context }}` | `{{ decisions[0].options | join(", ") }}` | `{{ decisions[0].decision }}` | `{{ decisions[0].consequences }}` |
<!-- END AI-GENERATED -->

---

# 7. Checks（HITL/AI両対応のGate）
## 7.1 Human Review Checklist（最小）
- [ ] Traceability に重大な欠落がない（空欄が多い場合は差し戻し）
- [ ] 未確定事項が明示され、推測で埋めていない
- [ ] Integration critical flow が明確（KPI/SLO含む）
- [ ] 監査・SoD・運用の最低要件が触れられている（`tecnos_org_constraints`準拠）
- [ ] 例外は reason/mitigation がセット（例外が無いなら exceptions は空配列）
- [ ] process.bpmn は Camunda 8 (Zeebe) 互換・DIありでレビュー可能
- [ ] **Delivery Model（requirements-driven / ftos / hybrid / ddd）が決まっている**
- [ ] **FtoS適用時のExit Criteriaが明示されている**
- [ ] **DDD適用時（validate推奨）に Domain Model / Technical Design / ADR 方針が明示されている**
- [ ] **RACI+（Human/AI/CI）が定義されている**
- [ ] **AI Policy（入力制御/ライセンス/監査）が明示されている**
- [ ] **Artifact Registry（成果物ID/版/保管先）が確定している**
- [ ] **E2Eタグ付きACは「重要ユーザージャーニー」に限定されている**（v1.2.3）
- [ ] **Coverage Policyの方針が決定されている**（v1.2.3）

## 7.2 Machine-readable Gate（basic_design_gate_check）
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "{{TEMPLATE_VERSION}}"

basic_design_gate_check:
  counts:
    traceability_rows: 0
    integration_flows: 0
    blocking_questions: 0
  rules:
    min_traceability_rows: 1
    min_integration_flows: 1
    max_blocking_questions: 0

  traceability_present: false
  integration_flows_identified: false
  exceptions_documented: true  # exceptions が空でも true（方針として空を明示できていればOK）
  delivery_model_defined: false
  ddd_artifacts_ready: true    # ddd未採用ならtrue。採用時はDomain/Technical/ADR参照が必要
  raci_plus_defined: false
  ai_policy_defined: false
  artifact_registry_defined: false

  ready_for_bpmn: false            # Basic Design Gate の最終フラグ（BPMN作成へ進める）
  process_bpmn_linked: false       # process_bpmn_path が確定したら true
  process_bpmn_approved: false     # HITLでBPMN承認後に true
  ready_for_specify: false         # BPMN承認後に true（spec/plan/tasks生成へ進める）
```

> End of basic_design.md
