---
artifact: "basic_design"
template_id: "TPL-BD-TECNOS-001"
feature_id: "FEAT-001"
basic_design_id: "BD-001"
title: "Basic Design - Web-EDI受注受付"
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
  process_bpmn_ref: "specs/sample_feature/process.bpmn"
  spec_md_ref: "specs/sample_feature/spec.md"
  plan_md_ref: "specs/sample_feature/plan.md"
  tasks_md_ref: "specs/sample_feature/tasks.md"
  constitution_ref: "memory/constitution.md"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: このドキュメントの正本は **#0 Canonical Basic Design (YAML)**。以下の説明文は補助。
> Purpose: 人間の任意テキスト入力を、AIがSDD（BPMN→Spec/Plan/Tasks）へ落とす前に「認識齟齬」を潰すハブ。
> Tecnos: 統合・監査・運用・AgentOpsの最低要件は `{{ links.org_constraints_ref }}` を参照。
> v1.2.3: RACI+（Human/AI/CI）、AI Policy、Artifact Registry、Delivery Model（FtoS判定）を明示する。

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
    traceability_rows: 2
    integration_flows: 1
    blocking_questions: 0

basic_design:
  organization:
    company: "Tecnos Japan"
    strategy_alignment:
      mid_term_plan: "2027-2032"
      target_state: ""
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
    type: "requirements-driven"
    rationale: "取引先ごとの運用差異があるため、要件重視型を採用"
    ftos_exit_criteria:
      enabled: false
      criteria:
        - ""

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
    who: "取引先の購買担当者（約80社）が、Web-EDIポータルから発注を送信し、社内受注担当者が内容を確認するために使用する"
    what: "Web-EDIで発注データを受け付け、ERPに自動登録し、受注番号と納期回答を返す"
    why: "現状はメール/Excelで受注を手入力しており、1件20分・誤入力1%が発生。受付〜確認を5分以内に短縮し、誤入力を0.1%以下にしたい"

  business_domain:
    value_chain: "O2C"
    capability: "受注DX"
    domain_objects: ["Customer", "SalesOrder", "Material"]

  scope:
    in:
      - "Web-EDI発注入力/CSVアップロード"
      - "発注内容のバリデーション"
      - "ERPへの受注登録"
      - "受注番号・納期回答の通知"
    out:
      - "請求書発行"
      - "支払処理"
      - "EDI標準(JCA/EDI)との相互接続"
      - "モバイルアプリ対応"

  # 対象システム（統合・監査の前提）
  systems:
    - system: "SAP S/4HANA"
      category: "ERP"
      owner: "経理部"
      integration_modes: ["API(OData V4)", "IDoc"]
    - system: "Web-EDI Portal"
      category: "B2B Portal"
      owner: "営業企画部"
      integration_modes: ["Web UI", "CSV Upload", "API(REST)"]

  data_policy:
    contains_personal_data: true
    data_classes: ["Public", "Internal", "Confidential", "Regulated(PII/契約/財務)"]
    audit_log_required: true
    retention_policy: "7 years (accounting)"

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

  flow_reference:
    process_bpmn_path: "specs/sample_feature/process.bpmn"
    bpmn_element_id_convention: "BPMN-(TASK|GW|EVT|FLOW)-NNN"

  # Integration critical flows（SLO/KPIが絡む重要フロー）
  integration_flows:
    - id: "FLOW-001"
      name: "Web-EDI受注受付フロー"
      summary: "Web-EDIポータルで受注を受付し、ERPへ登録、受注番号/納期回答を返却"
      kpi_slo: "P95 < 60s, Availability 99.5%"
      e2e_target: true  # v1.2.3: E2Eスモーク回帰の対象にするか

  # 最重要：抜け漏れ検出（空欄は許容。ただし ready_for_bpmn/ready_for_specify を立てる前に埋める）
  traceability_rows:
    - rq:
        id: "RQ-001"
        statement: "Web-EDIで発注後、5分以内に受注番号と納期回答を返却できること"
      us:
        id: "US-FEAT001-001"
        title: "Web-EDI発注送信"
      ac:
        id: "AC-US-FEAT001-001-01"
        statement: "取引先ID「P-1001」で発注CSV(10行)をアップロードすると、60秒以内に受注番号と納期が表示される"
        tags: ["integration", "performance"]
      bpmn:
        id: "BPMN-TASK-001"
        name: "受注登録"
      contract:
        id: "CT-API-01"
      test:
        id: "TS-INT-01"
        type: "integration"
      task:
        id: "T-G01-001"
    # v1.2.3: E2Eタグ付きACの例
    - rq:
        id: "RQ-002"
        statement: "在庫不足時でも納期回答が返ること"
      us:
        id: "US-FEAT001-001"
        title: "Web-EDI発注送信"
      ac:
        id: "AC-US-FEAT001-001-02"
        statement: "発注数量が在庫不足の場合、納期回答日（YYYY-MM-DD）が表示される"
        tags: ["integration", "e2e"]
      bpmn:
        id: "BPMN-TASK-001"
        name: "受注登録"
      contract:
        id: "CT-API-01"
      test:
        id: "TS-E2E-01"
        type: "e2e"
      task:
        id: "T-G04-002"

  open_questions: []

  assumptions:
    - id: "A-001"
      assumption: "取引先マスタがERPに登録済み"
      rationale: "未登録の取引先は受注登録できない"
      risk_if_false: "マスタ整備が先行タスクになり、開始が遅れる"

  decisions:
    - id: "DR-001"
      context: "発注データの受領方式"
      options:
        - "Webフォーム入力"
        - "CSVアップロード"
        - "EDI(JCA)連携"
      decision: "Webフォーム入力 + CSVアップロード"
      consequences: "CSV仕様の固定化と入力バリデーションが必要"

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
> NOTE: 本表は #0 YAML の `basic_design.traceability_rows` のビュー。差分が出ないように更新する。

| RQ | US | AC | Tags | BPMN | Contract | Test | Task |
|---|---|---|---|---|---|---|---|
| RQ-001 | US-FEAT001-001 | AC-US-FEAT001-001-01 | integration | BPMN-TASK-001 | CT-API-01 | TS-INT-01 | T-G01-001 |
| RQ-002 | US-FEAT001-001 | AC-US-FEAT001-001-02 | e2e | BPMN-TASK-001 | CT-API-01 | TS-E2E-01 | T-G04-002 |
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
## B.1 境界（ERP/SCM/CRM）
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

### B.3.1 Coverage Policy（v1.2.3）
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

### B.5.1 E2E Testing Policy（v1.2.3）
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
- [ ] **Delivery Model（requirements-driven / ftos / hybrid）が決まっている**
- [ ] **FtoS適用時のExit Criteriaが明示されている**
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
    traceability_rows: 2
    integration_flows: 1
    blocking_questions: 0
  rules:
    min_traceability_rows: 1
    min_integration_flows: 1
    max_blocking_questions: 0

  traceability_present: true
  integration_flows_identified: true
  exceptions_documented: true  # exceptions が空でも true（方針として空を明示できていればOK）
  delivery_model_defined: true
  raci_plus_defined: true
  ai_policy_defined: true
  artifact_registry_defined: true

  ready_for_bpmn: true             # Basic Design Gate の最終フラグ（BPMN作成へ進める）
  process_bpmn_linked: true        # process_bpmn_path が確定したら true
  process_bpmn_approved: true      # HITLでBPMN承認後に true
  ready_for_specify: true          # BPMN承認後に true（spec/plan/tasks生成へ進める）
```

> End of basic_design.md
