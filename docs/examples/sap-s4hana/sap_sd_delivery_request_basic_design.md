---
artifact: "basic_design"
template_id: "TPL-BD-TECNOS-001"
feature_id: "FEAT-SAPSD-DELREQ-SAMPLE"
basic_design_id: "BD-SAPSD-DELREQ-SAMPLE"
title: "Basic Design Sample - SAP SD 出庫依頼送信アドオンフロー"
version: "4.8.0-tecnos-stride"
status: "sample"
owners:
  - { name: "Sample Owner", role: "Product Owner / Business" }
  - { name: "Sample Architect", role: "Tech Lead / Architect" }
reviewers:
  - { name: "Sample QA", role: "Quality" }
  - { name: "Sample Integration Lead", role: "ERP/Integration" }
links:
  process_bpmn_ref: "sap_sd_delivery_request_process.bpmn"
  epic_flow_ref: "sap_sd_order_to_cash_epic_flow.bpmn"
created_at: "2026-03-23"
updated_at: "2026-03-23"
---

> **Rule-0**: このサンプルの正本は **#0 Canonical Basic Design (YAML)**。
>
> この文書は [sap_sd_delivery_request_process.bpmn](/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise/sap_sd_delivery_request_process.bpmn) に完全整合するように作成した、`basic_design.md` 形式のサンプルです。

# 0. Canonical Basic Design (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "4.8.0-tecnos-stride"

basic_design:
  epic_ref: "EPIC-SAPSD-O2C-SAMPLE"
  team_id: "TEAM-SAP-SD"
  coverage_tier: "critical"
  autonomy_bias: "balanced"
  security_sensitive: false
  erp_integration: true

  organization:
    company: "Tecnos Japan"
    strategy_alignment:
      mid_term_plan: "2027-2032"
      target_state: "出荷管理の手作業判断を減らし、SAP SD と物流倉庫の出庫連携を標準化する"

  context:
    who: "SAP SD 運用担当、出荷管理担当、物流連携運用担当"
    what: "ATP確定後の出庫依頼送信プロセスを詳細化し、WMS 連携と ACK 管理を標準化する"
    why: "出庫依頼の送信可否判断、例外確認、ACK異常時の保留処理を明文化しないと、PGI 遅延や再送漏れが発生するため"

  business_domain:
    value_chain: "O2C"
    capability: "SAP SD / 出荷実行"
    domain_objects:
      - "SalesOrder"
      - "DeliveryDocument"
      - "DeliveryRequest"
      - "WarehouseAck"
      - "ShippingCondition"

  scope:
    in:
      - "ATP確定後の納品伝票生成"
      - "出庫依頼メッセージ組成"
      - "例外条件の手動確認"
      - "WMS への出庫依頼送信"
      - "ACK 受信と状態更新"
      - "ACK 異常時の保留処理"
    out:
      - "ATP 計算ロジックそのもの"
      - "物流倉庫側のピッキング/PGI 実行"
      - "得意先への納品・検収・請求"

  systems:
    - system: "SAP SD"
      category: "ERP"
      owner: "TEAM-SAP-SD"
      integration_modes: ["API", "IDoc", "Queue"]
    - system: "WMS"
      category: "Warehouse Management"
      owner: "TEAM-WMS"
      integration_modes: ["API", "Message Queue"]

  database:
    enabled: true
    schema_ref: "docs/sample_contracts/sap_sd_delivery_request_database_schema.yaml"
    dialect: "sap-hana"
    sor_tables: ["LIKP", "LIPS", "ZSD_DELREQ_LOG"]
    referenced_tables: ["VBAK", "VBAP", "TVST"]
    migration_strategy: "versioned"
    migration_tool: "custom"

  data_policy:
    contains_personal_data: false
    data_classes: ["Internal", "Confidential"]
    audit_log_required: true
    retention_policy: "1 year for interface logs / 7 years for shipment audit trail"

  agentops_policy:
    enabled: true
    allowed_action_categories: ["read", "draft", "propose"]
    production_execute_requires: "human approval"
    provenance_required: true
    evidence_pack_required: true

  e2e_policy:
    scope: "critical-user-journeys"
    playwright_mcp:
      enabled: false
      usage: []
      prohibited_in_ci_gate: true
    ci_gate:
      deterministic: true
      runner: "pytest"
    triage_flow:
      categories: ["product_bug", "spec_gap", "test_bug", "flake"]
      feedback_to: ["spec", "plan", "tasks"]

  bpmn_descriptions:
    process:
      process_id: "BPMN-PROC-SAPSD-DELREQ"
      purpose: "SAP SD の ATP/在庫引当確定後、納品伝票生成から出庫依頼送信、ACK 受信、状態更新までを標準化する"
      start_condition: "ATP/在庫引当が確定し、出荷対象の受注であること"
      end_condition: "倉庫連携 ACK を受けて出庫依頼が送信完了または保留状態になること"
      business_outcome: "出庫依頼の送信・例外確認・ACK 異常対応が統制された状態で運用される"
      primary_actors: ["SAP SD 運用担当", "出荷管理担当", "物流連携運用担当"]
    elements:
      - bpmn_id: "BPMN-TASK-001"
        name: "納品伝票生成"
        type: "serviceTask"
        purpose: "出荷対象の受注から納品伝票を起票し、倉庫連携の起点情報を用意する"
        business_role: "出荷対象受注の物理出荷準備"
        trigger: "ATP確定"
        inputs: ["受注伝票", "ATP確定結果", "出荷条件"]
        outputs: ["納品伝票", "出荷対象明細"]
        business_rules: ["出荷停止フラグのある受注は納品伝票生成不可"]
        exceptions: ["必須出荷条件が不足している場合は保留"]
      - bpmn_id: "BPMN-TASK-002"
        name: "出庫依頼データ組成"
        type: "serviceTask"
        purpose: "WMS へ送る出庫依頼ペイロードを組み立てる"
        business_role: "SAP SD と WMS のインターフェース正規化"
        trigger: "納品伝票生成完了"
        inputs: ["納品伝票", "出荷対象明細", "出荷拠点マスタ"]
        outputs: ["出庫依頼データ"]
        business_rules: ["倉庫コード、積載日、便種別は必須"]
        exceptions: ["出荷拠点マスタ不整合時は連携不可"]
      - bpmn_id: "BPMN-GW-001"
        name: "手動確認要否"
        type: "exclusiveGateway"
        purpose: "例外条件に該当する出庫依頼かを判定する"
        business_role: "自動送信可否の判定"
        trigger: "出庫依頼データ組成完了"
        inputs: ["出庫依頼データ", "危険物区分", "分納フラグ", "代替倉庫フラグ", "緊急便フラグ"]
        outputs: ["手動確認要/不要"]
        business_rules: ["危険物、分納、代替倉庫、緊急便は手動確認"]
        exceptions: []
      - bpmn_id: "BPMN-TASK-003"
        name: "出庫依頼内容確認"
        type: "userTask"
        purpose: "例外ケースの出庫依頼を出荷管理担当がレビューする"
        business_role: "手動統制による誤送信防止"
        trigger: "手動確認要と判定"
        inputs: ["出庫依頼データ", "例外判定理由"]
        outputs: ["送信承認済み出庫依頼"]
        business_rules: ["承認者は shipping controller ロールのみ"]
        exceptions: ["却下時は再組成または出荷停止判断が必要"]
      - bpmn_id: "BPMN-TASK-004"
        name: "倉庫連携メッセージ送信"
        type: "serviceTask"
        purpose: "WMS に対して正式な出庫依頼を送信する"
        business_role: "物流連携の実行"
        trigger: "自動送信可または手動確認完了"
        inputs: ["出庫依頼データ"]
        outputs: ["送信要求", "連携トランザクションID"]
        business_rules: ["1 納品伝票につき 1 トランザクションID を採番"]
        exceptions: ["送信失敗時は ACK 受信待ちに進まず即保留"]
      - bpmn_id: "BPMN-TASK-005"
        name: "送信ACK受信"
        type: "serviceTask"
        purpose: "WMS 側の受付 ACK を取得する"
        business_role: "外部システム受付結果の確認"
        trigger: "出庫依頼送信完了"
        inputs: ["連携トランザクションID"]
        outputs: ["ACKステータス", "エラーコード"]
        business_rules: ["ACK は 5 回までポーリング取得する"]
        exceptions: ["タイムアウト時は保留/再送待ちへ遷移"]
      - bpmn_id: "BPMN-GW-002"
        name: "ACK判定"
        type: "exclusiveGateway"
        purpose: "WMS が出庫依頼を正常受付したかを判定する"
        business_role: "後続 PGI 待ちへの遷移可否判断"
        trigger: "ACK受信完了"
        inputs: ["ACKステータス", "エラーコード"]
        outputs: ["受付成功/異常"]
        business_rules: ["ACK = ACCEPTED の場合のみ成功"]
        exceptions: ["REJECTED や TIMEOUT は保留処理へ送る"]
      - bpmn_id: "BPMN-TASK-006"
        name: "出庫依頼状態更新"
        type: "serviceTask"
        purpose: "受付成功した出庫依頼を送信済みへ更新する"
        business_role: "後続出荷実行への橋渡し"
        trigger: "ACK成功"
        inputs: ["ACKステータス", "連携トランザクションID"]
        outputs: ["送信済み出庫依頼状態"]
        business_rules: ["送信済み更新後のみ PGI 待ちに進める"]
        exceptions: ["状態更新失敗時は運用通知を上げる"]
      - bpmn_id: "BPMN-TASK-007"
        name: "エラー記録・保留"
        type: "serviceTask"
        purpose: "ACK 異常時の記録と再送待ち制御を行う"
        business_role: "物流連携異常時の運用統制"
        trigger: "ACK異常"
        inputs: ["ACKステータス", "エラーコード"]
        outputs: ["保留状態", "運用通知"]
        business_rules: ["保留時は監視通知を必ず発報"]
        exceptions: ["通知失敗時はジョブログへ残し手動監視へ回す"]

  flow_reference:
    process_bpmn_path: "sap_sd_delivery_request_process.bpmn"
    bpmn_element_id_convention: "BPMN-(TASK|GW|EVT|FLOW)-NNN"

  integration_flows:
    - id: "FLOW-DELREQ-001"
      name: "SAP SD → WMS 出庫依頼送信"
      summary: "納品伝票をもとに出庫依頼を組成し、WMS へ送信する"
      kpi_slo: "出庫依頼送信開始まで P95 < 15分"
      e2e_target: true
    - id: "FLOW-DELREQ-002"
      name: "WMS ACK 受信"
      summary: "WMS の受付 ACK を取得して送信済み/保留を判定する"
      kpi_slo: "ACK 受信まで P95 < 5分"
      e2e_target: true
    - id: "FLOW-DELREQ-003"
      name: "例外出庫依頼レビュー"
      summary: "危険物・分納・代替倉庫などの例外ケースを手動確認する"
      kpi_slo: "レビュー開始まで P95 < 30分"
      e2e_target: false

  traceability_rows:
    - rq: { id: "RQ-DELREQ-001", statement: "ATP確定後に納品伝票を生成できること" }
      us: { id: "US-FEAT-SAPSD-DELREQ-001", title: "出庫依頼起票" }
      ac: { id: "AC-US-FEAT-SAPSD-DELREQ-001-01", statement: "ATP確定後、対象受注から納品伝票が生成される", tags: ["integration"] }
      bpmn: { id: "BPMN-TASK-001", name: "納品伝票生成" }
      contract: { id: "CT-DELREQ-01" }
      database: { tables: ["LIKP", "LIPS"], operations: ["INSERT"] }
      test: { id: "TS-INT-DELREQ-01", type: "integration" }
      task: { id: "T-DELREQ-001" }

    - rq: { id: "RQ-DELREQ-002", statement: "出庫依頼データを WMS 連携形式で組成できること" }
      us: { id: "US-FEAT-SAPSD-DELREQ-001", title: "出庫依頼起票" }
      ac: { id: "AC-US-FEAT-SAPSD-DELREQ-001-02", statement: "納品伝票から出庫依頼データが組成される", tags: ["integration"] }
      bpmn: { id: "BPMN-TASK-002", name: "出庫依頼データ組成" }
      contract: { id: "CT-DELREQ-01" }
      database: { tables: ["LIKP", "LIPS", "TVST"], operations: ["SELECT"] }
      test: { id: "TS-INT-DELREQ-02", type: "integration" }
      task: { id: "T-DELREQ-002" }

    - rq: { id: "RQ-DELREQ-003", statement: "例外条件の出庫依頼は手動確認へ回ること" }
      us: { id: "US-FEAT-SAPSD-DELREQ-002", title: "例外出庫依頼レビュー" }
      ac: { id: "AC-US-FEAT-SAPSD-DELREQ-002-01", statement: "危険物・分納・代替倉庫・緊急便は手動確認に遷移する", tags: ["ops"] }
      bpmn: { id: "BPMN-GW-001", name: "手動確認要否" }
      contract: { id: "CT-UI-DELREQ-01" }
      database: { tables: ["ZSD_DELREQ_LOG"], operations: ["INSERT"] }
      test: { id: "TS-INT-DELREQ-03", type: "integration" }
      task: { id: "T-DELREQ-003" }

    - rq: { id: "RQ-DELREQ-004", statement: "例外ケースを出荷管理担当がレビューできること" }
      us: { id: "US-FEAT-SAPSD-DELREQ-002", title: "例外出庫依頼レビュー" }
      ac: { id: "AC-US-FEAT-SAPSD-DELREQ-002-02", statement: "例外ケースの出庫依頼を shipping controller が承認できる", tags: ["security"] }
      bpmn: { id: "BPMN-TASK-003", name: "出庫依頼内容確認" }
      contract: { id: "CT-UI-DELREQ-01" }
      database: { tables: ["ZSD_DELREQ_LOG"], operations: ["UPDATE"] }
      test: { id: "TS-E2E-DELREQ-01", type: "e2e" }
      task: { id: "T-DELREQ-004" }

    - rq: { id: "RQ-DELREQ-005", statement: "承認済み出庫依頼を WMS に送信できること" }
      us: { id: "US-FEAT-SAPSD-DELREQ-003", title: "倉庫連携送信" }
      ac: { id: "AC-US-FEAT-SAPSD-DELREQ-003-01", statement: "出庫依頼が WMS に送信され、連携トランザクションID が採番される", tags: ["integration"] }
      bpmn: { id: "BPMN-TASK-004", name: "倉庫連携メッセージ送信" }
      contract: { id: "CT-DELREQ-01" }
      database: { tables: ["ZSD_DELREQ_LOG"], operations: ["INSERT", "UPDATE"] }
      test: { id: "TS-INT-DELREQ-04", type: "integration" }
      task: { id: "T-DELREQ-005" }

    - rq: { id: "RQ-DELREQ-006", statement: "WMS の ACK を受信して受付結果を判定できること" }
      us: { id: "US-FEAT-SAPSD-DELREQ-003", title: "倉庫連携送信" }
      ac: { id: "AC-US-FEAT-SAPSD-DELREQ-003-02", statement: "WMS ACK を受信し、ACCEPTED か異常かを判定できる", tags: ["integration"] }
      bpmn: { id: "BPMN-TASK-005", name: "送信ACK受信" }
      contract: { id: "CT-DELREQ-02" }
      database: { tables: ["ZSD_DELREQ_LOG"], operations: ["UPDATE"] }
      test: { id: "TS-INT-DELREQ-05", type: "integration" }
      task: { id: "T-DELREQ-006" }

    - rq: { id: "RQ-DELREQ-007", statement: "ACK成功時は出庫依頼を送信済みへ更新できること" }
      us: { id: "US-FEAT-SAPSD-DELREQ-004", title: "ACK結果反映" }
      ac: { id: "AC-US-FEAT-SAPSD-DELREQ-004-01", statement: "ACK=ACCEPTED の場合、出庫依頼状態が送信済みになる", tags: ["ops"] }
      bpmn: { id: "BPMN-GW-002", name: "ACK判定" }
      contract: { id: "CT-DELREQ-02" }
      database: { tables: ["ZSD_DELREQ_LOG"], operations: ["UPDATE"] }
      test: { id: "TS-INT-DELREQ-06", type: "integration" }
      task: { id: "T-DELREQ-007" }

    - rq: { id: "RQ-DELREQ-008", statement: "ACK成功後に出庫依頼状態を更新できること" }
      us: { id: "US-FEAT-SAPSD-DELREQ-004", title: "ACK結果反映" }
      ac: { id: "AC-US-FEAT-SAPSD-DELREQ-004-02", statement: "ACK成功時に送信済み状態へ更新し、後続 PGI 待ちへ進める", tags: ["ops"] }
      bpmn: { id: "BPMN-TASK-006", name: "出庫依頼状態更新" }
      contract: { id: "CT-DELREQ-02" }
      database: { tables: ["ZSD_DELREQ_LOG"], operations: ["UPDATE"] }
      test: { id: "TS-INT-DELREQ-07", type: "integration" }
      task: { id: "T-DELREQ-008" }

    - rq: { id: "RQ-DELREQ-009", statement: "ACK異常時は保留と通知が行われること" }
      us: { id: "US-FEAT-SAPSD-DELREQ-004", title: "ACK結果反映" }
      ac: { id: "AC-US-FEAT-SAPSD-DELREQ-004-03", statement: "ACK異常時は保留状態へ更新し運用通知を行う", tags: ["ops"] }
      bpmn: { id: "BPMN-TASK-007", name: "エラー記録・保留" }
      contract: { id: "CT-DELREQ-02" }
      database: { tables: ["ZSD_DELREQ_LOG"], operations: ["INSERT", "UPDATE"] }
      test: { id: "TS-INT-DELREQ-08", type: "integration" }
      task: { id: "T-DELREQ-009" }

  open_questions:
    - id: "Q-DELREQ-001"
      question: "ACK の最大待機時間を 5 分で固定するか、倉庫別パラメータにするか"
      blocking: false
      owner: "TEAM-SAP-SD"
      due: "2026-04-10"

  assumptions:
    - id: "A-DELREQ-001"
      assumption: "WMS は出庫依頼送信後 5 分以内に少なくとも受付 ACK を返す"
      rationale: "既存倉庫連携の運用実績"
      risk_if_false: "ACK 待機ジョブと保留判定閾値の再設計が必要"
    - id: "A-DELREQ-002"
      assumption: "手動確認が必要な例外判定条件は危険物・分納・代替倉庫・緊急便に限定する"
      rationale: "現行出荷管理標準に基づく"
      risk_if_false: "例外判定ロジックと UI 項目の追加が必要"

  decisions:
    - id: "DR-DELREQ-001"
      context: "出庫依頼送信前の手動統制要否"
      options: ["全件自動送信", "例外条件のみ手動確認"]
      decision: "例外条件のみ手動確認"
      consequences: "通常ケースの遅延を抑えつつ、リスク案件のみ人が統制する"
    - id: "DR-DELREQ-002"
      context: "ACK 異常時の扱い"
      options: ["即時再送", "保留して運用判断", "出荷取消"]
      decision: "保留して運用判断"
      consequences: "誤再送を避けられるが、運用通知と監視が必須"

  exceptions: []
```

---

# 2. Traceability

| RQ | US | AC | Tags | BPMN | Contract | Database | Test | Task |
|---|---|---|---|---|---|---|---|---|
| RQ-DELREQ-001 | US-FEAT-SAPSD-DELREQ-001 | AC-US-FEAT-SAPSD-DELREQ-001-01 | integration | BPMN-TASK-001 | CT-DELREQ-01 | LIKP, LIPS (INSERT) | TS-INT-DELREQ-01 | T-DELREQ-001 |
| RQ-DELREQ-002 | US-FEAT-SAPSD-DELREQ-001 | AC-US-FEAT-SAPSD-DELREQ-001-02 | integration | BPMN-TASK-002 | CT-DELREQ-01 | LIKP, LIPS, TVST (SELECT) | TS-INT-DELREQ-02 | T-DELREQ-002 |
| RQ-DELREQ-003 | US-FEAT-SAPSD-DELREQ-002 | AC-US-FEAT-SAPSD-DELREQ-002-01 | ops | BPMN-GW-001 | CT-UI-DELREQ-01 | ZSD_DELREQ_LOG (INSERT) | TS-INT-DELREQ-03 | T-DELREQ-003 |
| RQ-DELREQ-004 | US-FEAT-SAPSD-DELREQ-002 | AC-US-FEAT-SAPSD-DELREQ-002-02 | security | BPMN-TASK-003 | CT-UI-DELREQ-01 | ZSD_DELREQ_LOG (UPDATE) | TS-E2E-DELREQ-01 | T-DELREQ-004 |
| RQ-DELREQ-005 | US-FEAT-SAPSD-DELREQ-003 | AC-US-FEAT-SAPSD-DELREQ-003-01 | integration | BPMN-TASK-004 | CT-DELREQ-01 | ZSD_DELREQ_LOG (INSERT, UPDATE) | TS-INT-DELREQ-04 | T-DELREQ-005 |
| RQ-DELREQ-006 | US-FEAT-SAPSD-DELREQ-003 | AC-US-FEAT-SAPSD-DELREQ-003-02 | integration | BPMN-TASK-005 | CT-DELREQ-02 | ZSD_DELREQ_LOG (UPDATE) | TS-INT-DELREQ-05 | T-DELREQ-006 |
| RQ-DELREQ-007 | US-FEAT-SAPSD-DELREQ-004 | AC-US-FEAT-SAPSD-DELREQ-004-01 | ops | BPMN-GW-002 | CT-DELREQ-02 | ZSD_DELREQ_LOG (UPDATE) | TS-INT-DELREQ-06 | T-DELREQ-007 |
| RQ-DELREQ-008 | US-FEAT-SAPSD-DELREQ-004 | AC-US-FEAT-SAPSD-DELREQ-004-02 | ops | BPMN-TASK-006 | CT-DELREQ-02 | ZSD_DELREQ_LOG (UPDATE) | TS-INT-DELREQ-07 | T-DELREQ-008 |
| RQ-DELREQ-009 | US-FEAT-SAPSD-DELREQ-004 | AC-US-FEAT-SAPSD-DELREQ-004-03 | ops | BPMN-TASK-007 | CT-DELREQ-02 | ZSD_DELREQ_LOG (INSERT, UPDATE) | TS-INT-DELREQ-08 | T-DELREQ-009 |

---

# 3. Part A. WHAT/WHY Summary

- **Who**: SAP SD 運用担当、出荷管理担当、物流連携運用担当
- **What**: ATP確定後の出庫依頼送信と ACK 管理を詳細化した SAP SD アドオンフロー
- **Why**: 出庫依頼送信、例外確認、ACK 異常時の保留制御を明文化し、PGI 遅延や誤再送を防ぐ
- **Goals (In Scope)**: 納品伝票生成、出庫依頼組成、手動確認、WMS送信、ACK判定、状態更新、保留制御
- **Non-goals (Out of Scope)**: ATP計算そのもの、倉庫側 PGI 実行、得意先納品/検収/請求
- **Aligned Epic**: [sap_sd_order_to_cash_epic_flow.bpmn](/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise/sap_sd_order_to_cash_epic_flow.bpmn)

---

# 4. Part B. HOW Policy

## B.1 境界
- **SoR**: SAP SD 受注/納品伝票、WMS は受付結果提供、`ZSD_DELREQ_LOG` は連携監査補助
- **統合モード**: SAP SD → WMS 出庫依頼 API / メッセージ、WMS → SAP SD ACK 応答
- **直接DB連携**: なし

## B.2 契約
- `CT-DELREQ-01`: SAP SD から WMS への出庫依頼送信契約
- `CT-DELREQ-02`: WMS から SAP SD への ACK 応答契約
- `CT-UI-DELREQ-01`: 出荷管理担当による手動確認 UI 契約

## B.3 重要フロー
- `FLOW-DELREQ-001`: 出庫依頼送信
- `FLOW-DELREQ-002`: WMS ACK 受信
- `FLOW-DELREQ-003`: 例外出庫依頼レビュー

## B.4 Ops / Audit
- ACK 異常時は即時再送せず、まず保留と運用通知を行う
- 手動確認対象は `危険物 / 分納 / 代替倉庫 / 緊急便`
- 出庫依頼送信と ACK 判定は `ZSD_DELREQ_LOG` に記録する

---

# 5. BPMN Alignment Notes

- 対象 BPMN: [sap_sd_delivery_request_process.bpmn](/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise/sap_sd_delivery_request_process.bpmn)
- `bpmn_descriptions.process.process_id` は `BPMN-PROC-SAPSD-DELREQ`
- `bpmn_descriptions.elements` は BPMN の全業務ブロックに対応
  - `BPMN-TASK-001` から `BPMN-TASK-007`
  - `BPMN-GW-001`
  - `BPMN-GW-002`
- 条件付き Sequence Flow の意味
  - `BPMN-FLOW-004`: `requiresManualReview = true`
  - `BPMN-FLOW-009`: `ackStatus = "ACCEPTED"`
- EPIC 対応
  - BPMN 内の `TextAnnotation_EpicLink`
  - EPIC 側の `Task_SD_SendDeliveryReq`
  - EPIC 側の `MsgFlow_SDToWarehouse_DeliveryReq`

---

# 7. Checks

## 7.1 Human Review Checklist
- [x] BPMN の全業務ブロックが `bpmn_descriptions` に存在する
- [x] `traceability_rows` の BPMN ID が実 BPMN と一致する
- [x] 出庫依頼送信と ACK 受信の契約境界が明記されている
- [x] 例外レビューと保留制御の運用が定義されている
- [x] EPIC との対応箇所が明記されている

## 7.2 Machine-readable Gate (sample)
```yaml
basic_design_gate_check:
  counts:
    traceability_rows: 9
    integration_flows: 3
    blocking_questions: 0
  rules:
    min_traceability_rows: 1
    min_integration_flows: 1
    max_blocking_questions: 0
  traceability_present: true
  integration_flows_identified: true
  ready_for_bpmn: true
  process_bpmn_linked: true
  process_bpmn_approved: true
```
