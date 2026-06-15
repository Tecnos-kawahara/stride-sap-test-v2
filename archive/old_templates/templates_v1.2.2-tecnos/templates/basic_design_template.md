---
artifact: "basic_design"
template_id: "TPL-BD-TECNOS-001"
feature_id: "FEAT-XXX"
basic_design_id: "BD-XXX"
title: "Basic Design - <Feature Name>"
version: "1.2.2-tecnos"
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
  process_bpmn_ref: "specs/XXX_feature_name/process.bpmn"
  spec_md_ref: "specs/XXX_feature_name/spec.md"
  plan_md_ref: "specs/XXX_feature_name/plan.md"
  tasks_md_ref: "specs/XXX_feature_name/tasks.md"
  constitution_ref: "memory/constitution.md"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: このドキュメントの正本は **#0 Canonical Basic Design (YAML)**。以下の説明文は補助。
> Purpose: 人間の任意テキスト入力を、AIがSDD（BPMN→Spec/Plan/Tasks）へ落とす前に「認識齟齬」を潰すハブ。
> Tecnos: 統合・監査・運用・AgentOpsの最低要件は `{{ links.org_constraints_ref }}` を参照。
> v1.2.2: E2Eタグ対象フローの明示とCoverage Policyの方針決定を含む。

# 0. Canonical Basic Design (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.2.2-tecnos"

policy_refs:
  org_constraints_ref: "memory/tecnos_org_constraints.md"

derived_fields:
  counts_are_computed: true
  counts:
    traceability_rows: 0
    integration_flows: 0
    blocking_questions: 0

basic_design:
  organization:
    company: "Tecnos Japan"
    strategy_alignment:
      mid_term_plan: "2027-2032"
      target_state: "SI → CBP → AgentOps"
    program_ref:
      portfolio_items: []   # 例: ["2-11", "2-21"]（全社横断PJ番号など）
    delivery_methods:
      - "TEIM 6×6"
      - "PMBOK"
      - "SAP Activate"
    ai_governance:
      guideline_ref: "AI Guidelines v6 (ISO/IEC 42001 series)"
      human_in_the_loop: true

  context:
    who: ""     # 想定ユーザー/ステークホルダー（業務・IT・監査を含む）
    what: ""    # 何を実現するか（価値）
    why: ""     # なぜ今それが必要か（背景・課題）

  business_domain:
    value_chain: ""     # 例: O2C / P2P / M2O / R2R
    capability: ""      # 例: 調達DX / 生産DX / 営業DX / 原価管理
    cbp_alignment:
      cbp_version: "CBP-v3"
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

  data_policy:
    contains_personal_data: false
    data_classes: ["Public", "Internal", "Confidential", "Regulated(PII/契約/財務)"]
    audit_log_required: true
    retention_policy: ""  # 例: "7 years (accounting)", "90 days (logs)"

  agentops_policy:
    enabled: true
    allowed_action_categories: ["read", "draft", "propose"]  # read | draft | propose | execute
    production_execute_requires: "human approval"
    kill_switch:
      enabled: true
      conditions: []   # 例: ["unexpected write", "policy violation", "security incident"]

  # v1.2.2: E2E/AIエージェントループ方針
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

  flow_reference:
    process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
    bpmn_element_id_convention: "BPMN-(TASK|GW|EVT|FLOW)-NNN"

  # Integration critical flows（SLO/KPIが絡む重要フロー）
  integration_flows:
    - id: "FLOW-001"
      name: ""
      summary: ""
      kpi_slo: ""  # 例: "月次締め遅延=0 / 受注登録P95<3s"
      e2e_target: true  # v1.2.2: E2Eスモーク回帰の対象にするか

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
      test:
        id: "TS-INT-01"          # 未確定なら "" でも可
        type: "integration"
      task:
        id: "T-G01-001"          # 未確定なら "" でも可
    # v1.2.2: E2Eタグ付きACの例
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

---

# 2. Traceability（最重要：抜け漏れ検出のビュー）
> NOTE: 本表は #0 YAML の `basic_design.traceability_rows` のビュー。差分が出ないように更新する。

| RQ | US | AC | Tags | BPMN | Contract | Test | Task |
|---|---|---|---|---|---|---|---|
| RQ-001 | US-FEATXXX-001 | AC-US-FEATXXX-001-01 | integration | BPMN-TASK-001 | CT-API-01 | TS-INT-01 | T-G01-001 |
| RQ-002 | US-FEATXXX-001 | AC-US-FEATXXX-001-02 | e2e | BPMN-TASK-001 | CT-API-01 | TS-E2E-01 | T-G04-002 |
| ... | ... | ... | ... | ... | ... | ... | ... |

---

# 3. Part A. WHAT/WHY Summary（Specに落とす前の理解合わせ）
- Who:
- What:
- Why:
- Goals:
- Non-goals:
- Value metric（例：工数削減/リードタイム短縮/品質改善）:

---

# 4. Part B. HOW Policy（BPMN/Planに渡す"実装方針"インターフェース）
## B.1 境界（ERP/SCM/CRM/CBP）
- SoR（System of Record: データ所有）:
- 境界を越える契約（CT-*）:
- 直接DB連携など禁止事項の例外有無（あれば exceptions へ）:

## B.2 契約（Contract/CLI-First）
- Contract list（ID/名称/目的だけ）:
  - CT-API-01:
  - CT-EVT-01:
  - CT-FILE-01:
  - CT-IDOC-01:
- Versioning policy:
- 統合クリティカル契約（KPI/SLOに影響するもの）:

## B.3 テスト戦略（Test/Integration-First）
- Contract tests (TS-CON-*): 全CTをカバー
- Integration tests (TS-INT-*): integrationタグ付きACをカバー（可能なら実システム/実コネクタ）
- E2E tests (TS-E2E-*): **e2eタグ付きAC（重要ユーザージャーニー）のみ**
- Unit tests (TS-UT-*):

### B.3.1 Coverage Policy（v1.2.2）
- **AC Coverage**: 100%（全ACが少なくとも1つのTSでカバー）
- **CT Coverage**: 100%（全CTがTS-CONでカバー）
- **Code Coverage**: LIB=85%/75%、CMP=60%/50%（目標、例外は記録）
- **E2E対象選定**: e2eタグは「integration_flows で e2e_target=true のもの」に限定

## B.4 Ops / Audit（監査・運用）
- 監査ログ：対象操作・項目・保持期間
- SoD：権限と承認（だれが実行/承認するか）
- 障害時：再実行性（冪等性）とリカバリ手順

## B.5 Automation / AgentOps
- Agents（想定）:
- Allowed operations:
- Forbidden operations:
- Human approval points:
- Kill switch conditions:

### B.5.1 E2E Testing Policy（v1.2.2）
- **二重ループ設計**:
  - 内側ループ（高速反復）: AI + Playwright MCP で探索・再現・テスト骨格生成・失敗解析
  - 外側ループ（品質ゲート）: CIで決定論的にPlaywright Test（E2E）を実行
- **MCPの位置付け**: 生成/triage/再現に限定、CIゲートでは使わない
- **Triage手順**: `specs/<feature>/implementation-details/e2e-triage.md` に定義

## B.6 例外管理（Simplicity / Anti-Abstraction）
- Exceptions（Article / reason / mitigation）:
  - (none)

---

# 5. Part C. Operations / Feedback Loop（運用から仕様へ還流）
- Observability（metrics/logs/traces）:
- SLO/KPI:
- Incident feedback → Spec/Plan update rule:
- Security feedback → Constraints:
- Release/rollback policy:
- **E2E failure feedback**: 分類（product_bug/spec_gap/test_bug/flake）→ Spec/Plan/Tasksへ還流

---

# 6. Decision Log（判断の根拠）
- DR-001: <Decision>
- DR-002: ...

---

# 7. Checks（HITL/AI両対応のGate）
## 7.1 Human Review Checklist（最小）
- [ ] Traceability に重大な欠落がない（空欄が多い場合は差し戻し）
- [ ] 未確定事項が明示され、推測で埋めていない
- [ ] Integration critical flow が明確（KPI/SLO含む）
- [ ] 監査・SoD・運用の最低要件が触れられている（`tecnos_org_constraints`準拠）
- [ ] 例外は reason/mitigation がセット（例外が無いなら exceptions は空配列）
- [ ] process.bpmn は Camunda 8 (Zeebe) 互換・DIありでレビュー可能
- [ ] **E2Eタグ付きACは「重要ユーザージャーニー」に限定されている**（v1.2.2）
- [ ] **Coverage Policyの方針が決定されている**（v1.2.2）

## 7.2 Machine-readable Gate（basic_design_gate_check）
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.2.2-tecnos"

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

  ready_for_bpmn: false            # Basic Design Gate の最終フラグ（BPMN作成へ進める）
  process_bpmn_linked: false       # process_bpmn_path が確定したら true
  process_bpmn_approved: false     # HITLでBPMN承認後に true
  ready_for_specify: false         # BPMN承認後に true（spec/plan/tasks生成へ進める）
```

> End of basic_design.md
