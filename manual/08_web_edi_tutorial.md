# 08. Web-EDI 実践チュートリアル（Simple-SDD）

> **⚠️ 本チュートリアルは Simple-SDD（基本の5 Phase Gate モデル）に基づいています。**
> Tecnos-STRIDE 固有の概念（Work Item / Run / Mode / Autonomy Bias 等）は扱いません。
> STRIDE の実践例は [§07 実施担当者ガイド](07_practitioner_execution_guide.md) の §2 シナリオを参照してください。

---

## はじめに

このチュートリアルでは、**Web-EDIシステム** を題材に、SDD テンプレートの基本的な開発フロー（Simple-SDD）をステップバイステップで解説します。

### 完成イメージ

| 項目 | 内容 |
|------|------|
| システム名 | Web-EDI（電子データ交換） |
| 利用者 | 発注側（バイヤー）、受注側（サプライヤー） |
| 主要機能 | 注文登録、注文確認、出荷通知、検収登録 |
| 技術スタック | FastAPI + HTMX + SQLite |
| テスト | pytest（Contract/Unit/Integration）+ Playwright（E2E） |

### 所要時間の目安

| フェーズ | 手動 | Claude Code 併用 | 主な作業 |
|---------|------|-----------------|---------|
| Phase 1: Design | 1-2時間 | 15-30分 | 要件伝達 → レビュー → Gate 1,2 承認 |
| Phase 2: Specify | 1-2時間 | 20-40分 | AC/NFR レビュー → Gate 3,4 承認 |
| Phase 3: Tasking | 30分-1時間 | 10-20分 | 粒度・依存確認 → Gate 5 承認 |
| Phase 4: Execute | 2-4時間 | 30分-1時間 | 実装レビュー → テスト確認 → 承認 |
| Phase 5: Verify | 30分-1時間 | 10-20分 | Evidence Pack 確認 → Final 承認 |
| **合計** | **5-10時間** | **1.5-3時間** | |

---

## Step 0: 環境準備

### 0.1 必要なツール

```bash
# Python 3.11以上
python3 --version

# Node.js（Playwright用）
node --version

# Git
git --version
```

### 0.2 プロジェクトのクローン

```bash
# SDDテンプレートリポジトリをクローン
git clone https://github.com/Tecnos-Japan-NGB/tecnos-sdd-templates.git
cd tecnos-sdd-templates
```

### 0.3 フィーチャーディレクトリの作成

```bash
# Web-EDIフィーチャー用ディレクトリ作成
mkdir -p specs/web_edi/{contracts,tests/e2e,implementation-details}

# 確認
tree specs/web_edi/
```

**期待される出力:**

```
specs/web_edi/
├── contracts/
├── implementation-details/
└── tests/
    └── e2e/
```

### 0.4 テンプレートのコピー

```bash
# 基本テンプレートをコピー
cp sdd-templates/templates/basic_design_template.md specs/web_edi/basic_design.md
cp sdd-templates/templates/spec_template.md specs/web_edi/spec.md
cp sdd-templates/templates/plan_template.md specs/web_edi/plan.md
cp sdd-templates/templates/tasks_template.md specs/web_edi/tasks.md
cp sdd-templates/templates/APPROVAL.md specs/web_edi/APPROVAL.md
cp sdd-templates/templates/evidence_pack_template.md specs/web_edi/implementation-details/evidence_pack.md
cp sdd-templates/templates/contracts/openapi_template.yaml specs/web_edi/contracts/openapi.yaml

# プレースホルダー置換（macOS、サブディレクトリ含む）
sed -i '' 's/FEAT-XXX/FEAT-001/g' specs/web_edi/*.md specs/web_edi/*/*.md specs/web_edi/*/*.yaml
sed -i '' 's/FEATXXX/001/g' specs/web_edi/*.md specs/web_edi/*/*.md specs/web_edi/*/*.yaml
sed -i '' 's/XXX_feature_name/web_edi/g' specs/web_edi/*.md specs/web_edi/*/*.md specs/web_edi/*/*.yaml
sed -i '' 's/{{FEATURE_NAME}}/web_edi/g' specs/web_edi/*.md specs/web_edi/*/*.md specs/web_edi/*/*.yaml
sed -i '' 's/{{FEATURE_ID}}/001/g' specs/web_edi/*.md specs/web_edi/*/*.md specs/web_edi/*/*.yaml
```

> **Linux の場合**: `sed -i 's/...' ...`（`''` なし）

---

## Step 1: Phase 1 - Design（設計）

### 1.1 目標

- WHO（誰が）、WHAT（何を）、WHY（なぜ）を明確化
- 業務フローの可視化（BPMN）
- トレーサビリティの確立

### 1.2 basic_design.md の作成

`specs/web_edi/basic_design.md` を以下の内容で置き換えます：

```markdown
# FEAT-001: Web-EDI システム基本設計

## 0. Canonical Basic Design (YAML)

```yaml
basic_design:
  feature_id: "FEAT-001"
  title: "Web-EDIシステム"
  version: "1.0.0"
  last_updated: "2026-01-06"

  # WHO / WHAT / WHY
  context:
    who: "発注側（バイヤー）担当者と受注側（サプライヤー）担当者"
    what: "Web-EDIシステムを通じて取引プロセス（注文→確認→出荷→検収）をデジタル化する"
    why: "FAX・メール・電話による非効率な業務プロセスを排除し、リアルタイムな取引情報共有を実現する"

  # スコープ
  scope:
    in:
      - "注文登録・送信（発注側）"
      - "注文確認・承諾/拒否（受注側）"
      - "出荷通知登録（受注側）"
      - "検収登録（発注側）"
      - "取引履歴照会（両者）"
    out:
      - "請求・支払処理（将来フェーズ）"
      - "外部ERP連携（将来フェーズ）"
      - "在庫管理機能"

  # 開発モデル
  delivery_model:
    type: "agile_with_gates"
    iteration_length: "1 week"
    gates: ["design", "spec", "plan", "tasks", "final"]

  # RACI+
  raci_plus:
    roles:
      - name: "AI_Agent"
        r: true   # Responsible
        a: false  # NOT Accountable
        c: true   # Consulted
        i: true   # Informed
      - name: "Human_Reviewer"
        r: false
        a: true   # Accountable（人間のみ）
        c: true
        i: true
    ci_gate: "stride-lint + pytest + playwright"

  # トレーサビリティ行
  traceability_rows:
    # === 発注側フロー ===
    - rq:
        id: "RQ-001"
        statement: "発注側担当者が注文を登録できる"
      us:
        id: "US-FEAT001-001"
        title: "注文登録"
      ac:
        id: "AC-US-FEAT001-001-01"
        statement: "注文登録画面で取引先・品目・数量・納期を入力し送信すると、注文が作成され受注側に通知される"
        tags: ["integration", "e2e"]
      bpmn:
        id: "BPMN-TASK-001"
      contract:
        id: "CT-API-01"
      test:
        id: "TS-E2E-01"
      task:
        id: "T-G01-001"

    - rq:
        id: "RQ-002"
        statement: "発注側担当者が検収を登録できる"
      us:
        id: "US-FEAT001-002"
        title: "検収登録"
      ac:
        id: "AC-US-FEAT001-002-01"
        statement: "出荷済み注文に対して検収情報を入力し登録すると、検収が完了し受注側に通知される"
        tags: ["integration", "e2e"]
      bpmn:
        id: "BPMN-TASK-004"
      contract:
        id: "CT-API-04"
      test:
        id: "TS-E2E-04"
      task:
        id: "T-G01-004"

    # === 受注側フロー ===
    - rq:
        id: "RQ-003"
        statement: "受注側担当者が注文を確認・承諾できる"
      us:
        id: "US-FEAT001-003"
        title: "注文確認・承諾"
      ac:
        id: "AC-US-FEAT001-003-01"
        statement: "受信した注文を確認し、承諾または拒否を選択すると、その結果が発注側に通知される"
        tags: ["integration", "e2e"]
      bpmn:
        id: "BPMN-TASK-002"
      contract:
        id: "CT-API-02"
      test:
        id: "TS-E2E-02"
      task:
        id: "T-G01-002"

    - rq:
        id: "RQ-004"
        statement: "受注側担当者が出荷通知を登録できる"
      us:
        id: "US-FEAT001-004"
        title: "出荷通知"
      ac:
        id: "AC-US-FEAT001-004-01"
        statement: "承諾済み注文に対して出荷情報を入力し登録すると、出荷通知が発注側に送信される"
        tags: ["integration", "e2e"]
      bpmn:
        id: "BPMN-TASK-003"
      contract:
        id: "CT-API-03"
      test:
        id: "TS-E2E-03"
      task:
        id: "T-G01-003"

    # === 共通機能 ===
    - rq:
        id: "RQ-005"
        statement: "ユーザーがログイン/ログアウトできる"
      us:
        id: "US-FEAT001-005"
        title: "認証"
      ac:
        id: "AC-US-FEAT001-005-01"
        statement: "正しい認証情報でログインするとダッシュボードが表示される"
        tags: ["integration"]
      bpmn:
        id: "BPMN-TASK-000"
      contract:
        id: "CT-API-05"
      test:
        id: "TS-INT-01"
      task:
        id: "T-G00-001"

    - rq:
        id: "RQ-006"
        statement: "ユーザーが取引履歴を照会できる"
      us:
        id: "US-FEAT001-006"
        title: "取引履歴照会"
      ac:
        id: "AC-US-FEAT001-006-01"
        statement: "取引履歴画面で日付範囲やステータスでフィルタリングして注文一覧を表示できる"
        tags: ["integration"]
      bpmn:
        id: "BPMN-TASK-005"
      contract:
        id: "CT-API-06"
      test:
        id: "TS-INT-02"
      task:
        id: "T-G02-001"

  # 未解決の質問
  open_questions:
    blocking: []  # ブロッキングなし
    non_blocking:
      - id: "OQ-001"
        question: "通知方法はメールか画面内通知か？"
        status: "resolved"
        answer: "初期は画面内通知のみ。メール通知は将来フェーズ。"

  # Gateチェック（AI編集禁止）
  basic_design_gate_check:
    traceability_present: true
    integration_flows_identified: true
    delivery_model_defined: true
    raci_plus_defined: true
    blocking_questions_zero: true
    process_bpmn_linked: true
    ready_for_specify: false  # Gate承認後にtrueにする
```

---

## 1. Overview

### 1.1 誰が（WHO）
- **発注側（バイヤー）担当者**: 注文を登録し、検収を行う
- **受注側（サプライヤー）担当者**: 注文を確認・承諾し、出荷通知を登録する

### 1.2 何を（WHAT）
Web-EDIシステムを通じて、発注から検収までの取引プロセスをデジタル化する。

### 1.3 なぜ（WHY）
従来のFAX・メール・電話ベースの業務では：
- 情報の即時性がない
- 転記ミスが発生する
- 履歴管理が困難
- 監査対応に時間がかかる

---

## 2. Business Flow Reference

```
BPMN参照: process.bpmn

発注側プール               受注側プール
┌─────────────────┐      ┌─────────────────┐
│ ○→[注文登録]    │──────▶│   [注文確認]    │
│      │          │      │      │          │
│      ▼          │      │      ▼          │
│  [検収登録]◀────│◀─────│  [出荷通知]     │
│      │          │      │      │          │
│      ▼          │      │      ▼          │
│     ●           │      │     ●           │
└─────────────────┘      └─────────────────┘
```

---

## 3. Traceability Summary

| RQ | US | AC | BPMN | CT | TS | Task |
|----|----|----|------|----|----|------|
| RQ-001 | US-FEAT001-001 | AC-...-01 | BPMN-TASK-001 | CT-API-01 | TS-E2E-01 | T-G01-001 |
| RQ-002 | US-FEAT001-002 | AC-...-01 | BPMN-TASK-004 | CT-API-04 | TS-E2E-04 | T-G01-004 |
| RQ-003 | US-FEAT001-003 | AC-...-01 | BPMN-TASK-002 | CT-API-02 | TS-E2E-02 | T-G01-002 |
| RQ-004 | US-FEAT001-004 | AC-...-01 | BPMN-TASK-003 | CT-API-03 | TS-E2E-03 | T-G01-003 |
| RQ-005 | US-FEAT001-005 | AC-...-01 | BPMN-TASK-000 | CT-API-05 | TS-INT-01 | T-G00-001 |
| RQ-006 | US-FEAT001-006 | AC-...-01 | BPMN-TASK-005 | CT-API-06 | TS-INT-02 | T-G02-001 |
```

### 1.3 業務全体像の概念BPMN

> **v4.8.0 以降の標準**:
> 以下の 2 participant collaboration は、現行標準では **EPIC 側の `epic_flow.bpmn`** に相当する概念図です。
> 実案件では、チーム間・システム間の受け渡しは `epics/<EPIC>/epic_flow.bpmn` に置き、各 Feature の `specs/<feature>/process.bpmn` は **laneSet ベースの単一 Feature BPMN** に分解してください。

`epics/EPIC-WEB-EDI/epic_flow.bpmn` の概念例：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  id="Definitions_WebEDI"
                  targetNamespace="http://tecnos.co.jp/bpmn/web-edi">

  <bpmn:collaboration id="Collaboration_WebEDI">
    <bpmn:participant id="Pool_Buyer" name="発注側（バイヤー）" processRef="Process_Buyer"/>
    <bpmn:participant id="Pool_Supplier" name="受注側（サプライヤー）" processRef="Process_Supplier"/>
    <bpmn:messageFlow id="Flow_Order" name="注文送信" sourceRef="Task_CreateOrder" targetRef="Task_ConfirmOrder"/>
    <bpmn:messageFlow id="Flow_Accept" name="承諾通知" sourceRef="Task_ConfirmOrder" targetRef="Gateway_CheckAccept"/>
    <bpmn:messageFlow id="Flow_Ship" name="出荷通知" sourceRef="Task_ShipNotify" targetRef="Task_Receipt"/>
    <bpmn:messageFlow id="Flow_Receipt" name="検収通知" sourceRef="Task_Receipt" targetRef="Event_End_Supplier"/>
  </bpmn:collaboration>

  <!-- 発注側プロセス -->
  <bpmn:process id="Process_Buyer" isExecutable="true">
    <bpmn:startEvent id="Event_Start_Buyer" name="取引開始">
      <bpmn:outgoing>Flow_ToBuyerLogin</bpmn:outgoing>
    </bpmn:startEvent>

    <bpmn:task id="Task_BuyerLogin" name="ログイン">
      <bpmn:incoming>Flow_ToBuyerLogin</bpmn:incoming>
      <bpmn:outgoing>Flow_ToCreateOrder</bpmn:outgoing>
    </bpmn:task>

    <bpmn:task id="Task_CreateOrder" name="注文登録">
      <bpmn:documentation>BPMN-TASK-001: 発注側が注文を登録する</bpmn:documentation>
      <bpmn:incoming>Flow_ToCreateOrder</bpmn:incoming>
      <bpmn:outgoing>Flow_ToWaitAccept</bpmn:outgoing>
    </bpmn:task>

    <bpmn:intermediateCatchEvent id="Event_WaitAccept" name="承諾待ち">
      <bpmn:incoming>Flow_ToWaitAccept</bpmn:incoming>
      <bpmn:outgoing>Flow_ToCheckAccept</bpmn:outgoing>
    </bpmn:intermediateCatchEvent>

    <bpmn:exclusiveGateway id="Gateway_CheckAccept" name="承諾確認">
      <bpmn:incoming>Flow_ToCheckAccept</bpmn:incoming>
      <bpmn:outgoing>Flow_Accepted</bpmn:outgoing>
      <bpmn:outgoing>Flow_Rejected</bpmn:outgoing>
    </bpmn:exclusiveGateway>

    <bpmn:task id="Task_Receipt" name="検収登録">
      <bpmn:documentation>BPMN-TASK-004: 発注側が検収を登録する</bpmn:documentation>
      <bpmn:incoming>Flow_ToReceipt</bpmn:incoming>
      <bpmn:outgoing>Flow_ToEndBuyer</bpmn:outgoing>
    </bpmn:task>

    <bpmn:endEvent id="Event_End_Buyer" name="取引完了">
      <bpmn:incoming>Flow_ToEndBuyer</bpmn:incoming>
      <bpmn:incoming>Flow_Rejected</bpmn:incoming>
    </bpmn:endEvent>

    <!-- シーケンスフロー -->
    <bpmn:sequenceFlow id="Flow_ToBuyerLogin" sourceRef="Event_Start_Buyer" targetRef="Task_BuyerLogin"/>
    <bpmn:sequenceFlow id="Flow_ToCreateOrder" sourceRef="Task_BuyerLogin" targetRef="Task_CreateOrder"/>
    <bpmn:sequenceFlow id="Flow_ToWaitAccept" sourceRef="Task_CreateOrder" targetRef="Event_WaitAccept"/>
    <bpmn:sequenceFlow id="Flow_ToCheckAccept" sourceRef="Event_WaitAccept" targetRef="Gateway_CheckAccept"/>
    <bpmn:sequenceFlow id="Flow_Accepted" name="承諾" sourceRef="Gateway_CheckAccept" targetRef="Task_Receipt"/>
    <bpmn:sequenceFlow id="Flow_Rejected" name="拒否" sourceRef="Gateway_CheckAccept" targetRef="Event_End_Buyer"/>
    <bpmn:sequenceFlow id="Flow_ToReceipt" sourceRef="Gateway_CheckAccept" targetRef="Task_Receipt"/>
    <bpmn:sequenceFlow id="Flow_ToEndBuyer" sourceRef="Task_Receipt" targetRef="Event_End_Buyer"/>
  </bpmn:process>

  <!-- 受注側プロセス -->
  <bpmn:process id="Process_Supplier" isExecutable="true">
    <bpmn:startEvent id="Event_Start_Supplier" name="注文受信">
      <bpmn:outgoing>Flow_ToSupplierLogin</bpmn:outgoing>
    </bpmn:startEvent>

    <bpmn:task id="Task_SupplierLogin" name="ログイン">
      <bpmn:incoming>Flow_ToSupplierLogin</bpmn:incoming>
      <bpmn:outgoing>Flow_ToConfirmOrder</bpmn:outgoing>
    </bpmn:task>

    <bpmn:task id="Task_ConfirmOrder" name="注文確認・承諾">
      <bpmn:documentation>BPMN-TASK-002: 受注側が注文を確認し承諾/拒否する</bpmn:documentation>
      <bpmn:incoming>Flow_ToConfirmOrder</bpmn:incoming>
      <bpmn:outgoing>Flow_ToShipNotify</bpmn:outgoing>
    </bpmn:task>

    <bpmn:task id="Task_ShipNotify" name="出荷通知">
      <bpmn:documentation>BPMN-TASK-003: 受注側が出荷通知を登録する</bpmn:documentation>
      <bpmn:incoming>Flow_ToShipNotify</bpmn:incoming>
      <bpmn:outgoing>Flow_ToWaitReceipt</bpmn:outgoing>
    </bpmn:task>

    <bpmn:intermediateCatchEvent id="Event_WaitReceipt" name="検収待ち">
      <bpmn:incoming>Flow_ToWaitReceipt</bpmn:incoming>
      <bpmn:outgoing>Flow_ToEndSupplier</bpmn:outgoing>
    </bpmn:intermediateCatchEvent>

    <bpmn:endEvent id="Event_End_Supplier" name="取引完了">
      <bpmn:incoming>Flow_ToEndSupplier</bpmn:incoming>
    </bpmn:endEvent>

    <!-- シーケンスフロー -->
    <bpmn:sequenceFlow id="Flow_ToSupplierLogin" sourceRef="Event_Start_Supplier" targetRef="Task_SupplierLogin"/>
    <bpmn:sequenceFlow id="Flow_ToConfirmOrder" sourceRef="Task_SupplierLogin" targetRef="Task_ConfirmOrder"/>
    <bpmn:sequenceFlow id="Flow_ToShipNotify" sourceRef="Task_ConfirmOrder" targetRef="Task_ShipNotify"/>
    <bpmn:sequenceFlow id="Flow_ToWaitReceipt" sourceRef="Task_ShipNotify" targetRef="Event_WaitReceipt"/>
    <bpmn:sequenceFlow id="Flow_ToEndSupplier" sourceRef="Event_WaitReceipt" targetRef="Event_End_Supplier"/>
  </bpmn:process>

</bpmn:definitions>
```

### 1.4 現行標準での検証

```bash
# EPIC overview の検証
stride epic validate EPIC-WEB-EDI

# FEAT の process.bpmn を検証
stride lint specs/web_edi/
```

- EPIC 側は `epic_validator.py` が collaboration / participant / messageFlow / `epic_flow_descriptions` を軽量検証します
- FEAT 側は `stride_lint.py` が laneSet executable BPMN と `bpmn_descriptions` の整合を検証します

### 1.5 Gate 1 & 2 の承認

`specs/web_edi/APPROVAL.md` を編集します（**人間のみ**）：

```markdown
# APPROVAL.md - Human-Only Approval Record

## Gate 1: Basic Design
- [x] basic_design.md reviewed
- [x] WHO/WHAT/WHY is clear
- [x] Traceability rows are complete (6 rows)
- [x] No blocking questions

承認者: 山田太郎
日付:   2026-01-06

## Gate 2: BPMN
- [x] process.bpmn reviewed
- [x] FEAT の process.bpmn は laneSet で業務フローを表現している
- [x] 必要な cross-team / cross-system の受け渡しは EPIC の epic_flow.bpmn に切り出されている

承認者: 山田太郎
日付:   2026-01-06
```

承認後、`basic_design.md` の `ready_for_specify: true` に更新し、再度 lint を実行：

```bash
sdd-templates/tools/stride-lint specs/web_edi/
```

---

## Step 2: Phase 2 - Specify（仕様定義）

### 2.1 spec.md の作成

`specs/web_edi/spec.md` を以下の内容で置き換えます：

```markdown
# FEAT-001: Web-EDI システム仕様書

## 0. Canonical Spec (YAML)

```yaml
spec:
  feature_id: "FEAT-001"
  title: "Web-EDIシステム仕様"
  version: "1.0.0"
  last_updated: "2026-01-06"

  overview:
    who: "発注側（バイヤー）担当者と受注側（サプライヤー）担当者"
    what: "取引プロセス（注文→確認→出荷→検収）をWebアプリで実現"
    why: "業務効率化とリアルタイム情報共有"

  use_cases:
    - id: "US-FEAT001-001"
      title: "注文登録"
      primary_actor: "発注側担当者"
      trigger: "新規注文を作成したい"
      preconditions:
        - "ログイン済み"
        - "取引先が登録済み"
      main_flow:
        - "注文登録画面を開く"
        - "取引先を選択する"
        - "品目・数量・納期を入力する"
        - "送信ボタンを押す"
        - "確認ダイアログで確定する"
      postconditions:
        - "注文が作成される"
        - "受注側に通知される"
      acceptance:
        - id: "AC-US-FEAT001-001-01"
          statement: "注文登録画面で取引先・品目・数量・納期を入力し送信すると、注文が作成され受注側に通知される"
          tags: ["integration", "e2e"]
          priority: "must"
        - id: "AC-US-FEAT001-001-02"
          statement: "必須項目が未入力の場合、エラーメッセージが表示される"
          tags: ["integration"]
          priority: "must"

    - id: "US-FEAT001-002"
      title: "検収登録"
      primary_actor: "発注側担当者"
      trigger: "出荷された商品を検収したい"
      preconditions:
        - "ログイン済み"
        - "出荷通知済みの注文がある"
      main_flow:
        - "注文詳細画面を開く"
        - "検収情報を入力する"
        - "検収登録ボタンを押す"
      postconditions:
        - "検収が完了する"
        - "受注側に通知される"
      acceptance:
        - id: "AC-US-FEAT001-002-01"
          statement: "出荷済み注文に対して検収情報を入力し登録すると、検収が完了し受注側に通知される"
          tags: ["integration", "e2e"]
          priority: "must"

    - id: "US-FEAT001-003"
      title: "注文確認・承諾"
      primary_actor: "受注側担当者"
      trigger: "受信した注文を処理したい"
      preconditions:
        - "ログイン済み"
        - "未処理の注文がある"
      main_flow:
        - "注文一覧画面を開く"
        - "注文詳細を確認する"
        - "承諾または拒否を選択する"
        - "確認ボタンを押す"
      postconditions:
        - "注文ステータスが更新される"
        - "発注側に通知される"
      acceptance:
        - id: "AC-US-FEAT001-003-01"
          statement: "受信した注文を確認し、承諾または拒否を選択すると、その結果が発注側に通知される"
          tags: ["integration", "e2e"]
          priority: "must"

    - id: "US-FEAT001-004"
      title: "出荷通知"
      primary_actor: "受注側担当者"
      trigger: "商品を出荷したことを通知したい"
      preconditions:
        - "ログイン済み"
        - "承諾済みの注文がある"
      main_flow:
        - "注文詳細画面を開く"
        - "出荷情報を入力する"
        - "出荷通知ボタンを押す"
      postconditions:
        - "出荷通知が登録される"
        - "発注側に通知される"
      acceptance:
        - id: "AC-US-FEAT001-004-01"
          statement: "承諾済み注文に対して出荷情報を入力し登録すると、出荷通知が発注側に送信される"
          tags: ["integration", "e2e"]
          priority: "must"

    - id: "US-FEAT001-005"
      title: "認証"
      primary_actor: "ユーザー"
      trigger: "システムにアクセスしたい"
      preconditions:
        - "有効なアカウントがある"
      main_flow:
        - "ログイン画面を開く"
        - "ユーザー名とパスワードを入力する"
        - "ログインボタンを押す"
      postconditions:
        - "ダッシュボードが表示される"
      acceptance:
        - id: "AC-US-FEAT001-005-01"
          statement: "正しい認証情報でログインするとダッシュボードが表示される"
          tags: ["integration"]
          priority: "must"
        - id: "AC-US-FEAT001-005-02"
          statement: "誤った認証情報でログインするとエラーメッセージが表示される"
          tags: ["integration"]
          priority: "must"

    - id: "US-FEAT001-006"
      title: "取引履歴照会"
      primary_actor: "ユーザー"
      trigger: "過去の取引を確認したい"
      preconditions:
        - "ログイン済み"
      main_flow:
        - "取引履歴画面を開く"
        - "検索条件を入力する"
        - "検索ボタンを押す"
      postconditions:
        - "条件に合う注文一覧が表示される"
      acceptance:
        - id: "AC-US-FEAT001-006-01"
          statement: "取引履歴画面で日付範囲やステータスでフィルタリングして注文一覧を表示できる"
          tags: ["integration"]
          priority: "should"

  nfrs:
    security:
      - "ユーザー認証必須（セッションベース）"
      - "自社取引データのみアクセス可能"
      - "パスワードはハッシュ化して保存"
    integration:
      - "画面内リアルタイム通知"
      - "API応答時間 P95 < 3秒"
    data:
      - "監査ログ7年保持"
      - "取引データ整合性保証（トランザクション）"
      - "日次バックアップ"

  open_questions:
    blocking: []
    non_blocking: []

  spec_gate_check:
    min_use_cases: 6
    min_acceptance_criteria: 10
    min_integration_ac: 6
    no_blocking_open_questions: true
    spec_as_code_defined: true
    ready_for_plan: false  # Gate承認後にtrueにする
```

---

## 1. Use Cases Summary

| ID | Title | Actor | Priority |
|----|-------|-------|----------|
| US-FEAT001-001 | 注文登録 | 発注側 | Must |
| US-FEAT001-002 | 検収登録 | 発注側 | Must |
| US-FEAT001-003 | 注文確認・承諾 | 受注側 | Must |
| US-FEAT001-004 | 出荷通知 | 受注側 | Must |
| US-FEAT001-005 | 認証 | 両者 | Must |
| US-FEAT001-006 | 取引履歴照会 | 両者 | Should |

---

## 2. Acceptance Criteria Summary

| AC ID | Tags | Priority |
|-------|------|----------|
| AC-US-FEAT001-001-01 | integration, e2e | must |
| AC-US-FEAT001-001-02 | integration | must |
| AC-US-FEAT001-002-01 | integration, e2e | must |
| AC-US-FEAT001-003-01 | integration, e2e | must |
| AC-US-FEAT001-004-01 | integration, e2e | must |
| AC-US-FEAT001-005-01 | integration | must |
| AC-US-FEAT001-005-02 | integration | must |
| AC-US-FEAT001-006-01 | integration | should |

**e2eタグ付きAC**: 4件（重要なユーザージャーニー）
```

### 2.2 plan.md の作成

`specs/web_edi/plan.md` を以下の内容で置き換えます：

```markdown
# FEAT-001: Web-EDI システム実装計画

## 0. Canonical Plan (YAML)

```yaml
plan:
  feature_id: "FEAT-001"
  title: "Web-EDIシステム実装計画"
  version: "1.0.0"
  last_updated: "2026-01-06"

  architecture:
    overview: "FastAPI + HTMX + SQLite の軽量Web構成"
    components:
      - name: "API Layer"
        technology: "FastAPI"
        responsibility: "REST API提供、認証処理"
      - name: "UI Layer"
        technology: "Jinja2 + HTMX"
        responsibility: "動的Web UI、フォーム処理"
      - name: "Data Layer"
        technology: "SQLAlchemy + SQLite"
        responsibility: "データ永続化、トランザクション管理"

  coverage_policy:
    layer_1_ac_coverage: "100%"     # 全ACをテストでカバー
    layer_2_ct_coverage: "100%"     # 全契約をテストでカバー
    layer_3_code_coverage: "80%"    # コードカバレッジ目標

  contracts:
    - id: "CT-API-01"
      type: "REST API"
      method: "POST"
      path: "/api/orders"
      description: "注文登録API"
      covers_ac_ids: ["AC-US-FEAT001-001-01"]
    - id: "CT-API-02"
      type: "REST API"
      method: "PUT"
      path: "/api/orders/{id}/accept"
      description: "注文承諾API"
      covers_ac_ids: ["AC-US-FEAT001-003-01"]
    - id: "CT-API-03"
      type: "REST API"
      method: "POST"
      path: "/api/orders/{id}/ship"
      description: "出荷通知API"
      covers_ac_ids: ["AC-US-FEAT001-004-01"]
    - id: "CT-API-04"
      type: "REST API"
      method: "POST"
      path: "/api/orders/{id}/receipt"
      description: "検収登録API"
      covers_ac_ids: ["AC-US-FEAT001-002-01"]
    - id: "CT-API-05"
      type: "REST API"
      method: "POST"
      path: "/api/auth/login"
      description: "ログインAPI"
      covers_ac_ids: ["AC-US-FEAT001-005-01", "AC-US-FEAT001-005-02"]
    - id: "CT-API-06"
      type: "REST API"
      method: "GET"
      path: "/api/orders"
      description: "注文一覧取得API"
      covers_ac_ids: ["AC-US-FEAT001-006-01"]
    - id: "CT-API-07"
      type: "REST API"
      method: "GET"
      path: "/api/orders/{id}"
      description: "注文詳細取得API"
      covers_ac_ids: []
    - id: "CT-API-08"
      type: "REST API"
      method: "POST"
      path: "/api/auth/logout"
      description: "ログアウトAPI"
      covers_ac_ids: []

  tests:
    # E2Eテスト（Playwright）- 重要ユーザージャーニー
    - id: "TS-E2E-01"
      type: "e2e"
      title: "発注側：注文登録→受注側通知"
      covers_ac_ids: ["AC-US-FEAT001-001-01"]
      covers_contract_ids: ["CT-API-01"]
    - id: "TS-E2E-02"
      type: "e2e"
      title: "受注側：注文確認→承諾→発注側通知"
      covers_ac_ids: ["AC-US-FEAT001-003-01"]
      covers_contract_ids: ["CT-API-02"]
    - id: "TS-E2E-03"
      type: "e2e"
      title: "受注側：出荷通知→発注側通知"
      covers_ac_ids: ["AC-US-FEAT001-004-01"]
      covers_contract_ids: ["CT-API-03"]
    - id: "TS-E2E-04"
      type: "e2e"
      title: "発注側：検収登録→受注側通知"
      covers_ac_ids: ["AC-US-FEAT001-002-01"]
      covers_contract_ids: ["CT-API-04"]

    # 統合テスト（pytest）
    - id: "TS-INT-01"
      type: "integration"
      title: "認証フロー（ログイン/ログアウト）"
      covers_ac_ids: ["AC-US-FEAT001-005-01", "AC-US-FEAT001-005-02"]
      covers_contract_ids: ["CT-API-05", "CT-API-08"]
    - id: "TS-INT-02"
      type: "integration"
      title: "取引履歴照会（フィルタリング）"
      covers_ac_ids: ["AC-US-FEAT001-006-01"]
      covers_contract_ids: ["CT-API-06"]
    - id: "TS-INT-03"
      type: "integration"
      title: "注文バリデーション"
      covers_ac_ids: ["AC-US-FEAT001-001-02"]
      covers_contract_ids: ["CT-API-01"]
    - id: "TS-INT-04"
      type: "integration"
      title: "注文詳細取得"
      covers_ac_ids: []
      covers_contract_ids: ["CT-API-07"]

    # 契約テスト（pytest）
    - id: "TS-CON-01"
      type: "contract"
      title: "POST /api/orders スキーマ検証"
      covers_contract_ids: ["CT-API-01"]
    - id: "TS-CON-02"
      type: "contract"
      title: "PUT /api/orders/{id}/accept スキーマ検証"
      covers_contract_ids: ["CT-API-02"]
    - id: "TS-CON-03"
      type: "contract"
      title: "POST /api/orders/{id}/ship スキーマ検証"
      covers_contract_ids: ["CT-API-03"]
    - id: "TS-CON-04"
      type: "contract"
      title: "POST /api/orders/{id}/receipt スキーマ検証"
      covers_contract_ids: ["CT-API-04"]
    - id: "TS-CON-05"
      type: "contract"
      title: "POST /api/auth/login スキーマ検証"
      covers_contract_ids: ["CT-API-05"]
    - id: "TS-CON-06"
      type: "contract"
      title: "GET /api/orders スキーマ検証"
      covers_contract_ids: ["CT-API-06"]
    - id: "TS-CON-07"
      type: "contract"
      title: "GET /api/orders/{id} スキーマ検証"
      covers_contract_ids: ["CT-API-07"]
    - id: "TS-CON-08"
      type: "contract"
      title: "POST /api/auth/logout スキーマ検証"
      covers_contract_ids: ["CT-API-08"]

  groups:
    - id: "G-00"
      name: "認証・共通基盤"
      bpmn_elements: ["BPMN-TASK-000"]
      tasks_prefix: "T-G00"
    - id: "G-01"
      name: "取引フロー（注文→検収）"
      bpmn_elements: ["BPMN-TASK-001", "BPMN-TASK-002", "BPMN-TASK-003", "BPMN-TASK-004"]
      tasks_prefix: "T-G01"
    - id: "G-02"
      name: "照会・レポート"
      bpmn_elements: ["BPMN-TASK-005"]
      tasks_prefix: "T-G02"

  plan_gate_check:
    contracts_defined: true
    tests_prioritized: true
    coverage_policy_defined: true
    integration_first_gate_passed: true
    evidence_pack_defined: true
    ready_for_tasks: false  # Gate承認後にtrueにする
```

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                               │
│                    (HTMX + Jinja2)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Server                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Routes    │  │   Models    │  │    Business Logic   │ │
│  │ (REST API)  │  │ (Pydantic)  │  │    (Order Service)  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   SQLAlchemy + SQLite                        │
│                     (Data Layer)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Test Summary

| Type | Count | Framework |
|------|-------|-----------|
| E2E | 4 specs (8 functions) | Playwright |
| Integration | 4 | pytest |
| Contract | 8 | pytest |
| **Total** | **16 specs (20 functions)** | |
```

### 2.3 openapi.yaml の作成

`specs/web_edi/contracts/openapi.yaml` を以下の内容で置き換えます：

```yaml
openapi: "3.0.3"
info:
  title: "Web-EDI API"
  description: "電子データ交換システムAPI"
  version: "1.0.0"
  contact:
    name: "Tecnos Japan"

servers:
  - url: "http://localhost:8000"
    description: "Development"

paths:
  /api/auth/login:
    post:
      operationId: "login"
      summary: "ログイン"
      tags: ["auth"]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/LoginRequest"
      responses:
        "200":
          description: "ログイン成功"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/UserResponse"
        "401":
          description: "認証失敗"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"

  /api/auth/logout:
    post:
      operationId: "logout"
      summary: "ログアウト"
      tags: ["auth"]
      security:
        - sessionAuth: []
      responses:
        "200":
          description: "ログアウト成功"

  /api/orders:
    get:
      operationId: "listOrders"
      summary: "注文一覧取得"
      tags: ["orders"]
      security:
        - sessionAuth: []
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: ["pending", "accepted", "rejected", "shipped", "received"]
        - name: from_date
          in: query
          schema:
            type: string
            format: date
        - name: to_date
          in: query
          schema:
            type: string
            format: date
      responses:
        "200":
          description: "注文一覧"
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/OrderSummary"

    post:
      operationId: "createOrder"
      summary: "注文登録"
      tags: ["orders"]
      security:
        - sessionAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CreateOrderRequest"
      responses:
        "201":
          description: "注文作成成功"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderResponse"
        "400":
          description: "バリデーションエラー"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"

  /api/orders/{id}:
    get:
      operationId: "getOrder"
      summary: "注文詳細取得"
      tags: ["orders"]
      security:
        - sessionAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: "注文詳細"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderResponse"
        "404":
          description: "注文が見つからない"

  /api/orders/{id}/accept:
    put:
      operationId: "acceptOrder"
      summary: "注文承諾/拒否"
      tags: ["orders"]
      security:
        - sessionAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/AcceptOrderRequest"
      responses:
        "200":
          description: "承諾/拒否完了"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderResponse"

  /api/orders/{id}/ship:
    post:
      operationId: "shipOrder"
      summary: "出荷通知"
      tags: ["orders"]
      security:
        - sessionAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ShipOrderRequest"
      responses:
        "200":
          description: "出荷通知完了"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderResponse"

  /api/orders/{id}/receipt:
    post:
      operationId: "receiptOrder"
      summary: "検収登録"
      tags: ["orders"]
      security:
        - sessionAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ReceiptOrderRequest"
      responses:
        "200":
          description: "検収完了"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderResponse"

components:
  securitySchemes:
    sessionAuth:
      type: apiKey
      in: cookie
      name: session_id

  schemas:
    LoginRequest:
      type: object
      required:
        - username
        - password
      properties:
        username:
          type: string
          minLength: 1
        password:
          type: string
          minLength: 1

    UserResponse:
      type: object
      properties:
        id:
          type: integer
        username:
          type: string
        role:
          type: string
          enum: ["buyer", "supplier"]
        company_name:
          type: string

    CreateOrderRequest:
      type: object
      required:
        - partner_id
        - items
        - delivery_date
      properties:
        partner_id:
          type: integer
        items:
          type: array
          items:
            $ref: "#/components/schemas/OrderItem"
          minItems: 1
        delivery_date:
          type: string
          format: date
        notes:
          type: string

    OrderItem:
      type: object
      required:
        - product_id
        - quantity
      properties:
        product_id:
          type: integer
        quantity:
          type: integer
          minimum: 1

    AcceptOrderRequest:
      type: object
      required:
        - accepted
      properties:
        accepted:
          type: boolean
        reject_reason:
          type: string

    ShipOrderRequest:
      type: object
      required:
        - shipped_date
      properties:
        shipped_date:
          type: string
          format: date
        tracking_number:
          type: string

    ReceiptOrderRequest:
      type: object
      required:
        - received_date
      properties:
        received_date:
          type: string
          format: date
        notes:
          type: string

    OrderSummary:
      type: object
      properties:
        id:
          type: integer
        order_number:
          type: string
        partner_name:
          type: string
        status:
          type: string
        created_at:
          type: string
          format: date-time
        total_amount:
          type: number

    OrderResponse:
      type: object
      properties:
        id:
          type: integer
        order_number:
          type: string
        buyer_id:
          type: integer
        supplier_id:
          type: integer
        status:
          type: string
          enum: ["pending", "accepted", "rejected", "shipped", "received"]
        items:
          type: array
          items:
            $ref: "#/components/schemas/OrderItem"
        delivery_date:
          type: string
          format: date
        shipped_date:
          type: string
          format: date
        received_date:
          type: string
          format: date
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    ErrorResponse:
      type: object
      properties:
        detail:
          type: string
        errors:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              message:
                type: string
```

### 2.4 Gate 3 & 4 の承認

`specs/web_edi/APPROVAL.md` に追記します（**人間のみ**）：

```markdown
## Gate 3: Spec
- [x] spec.md reviewed
- [x] All use cases defined (6)
- [x] All acceptance criteria defined (8)
- [x] e2e tags applied to critical journeys (4)
- [x] No blocking questions

承認者: 田中花子
日付:   2026-01-06

## Gate 4: Plan
- [x] plan.md reviewed
- [x] Architecture defined
- [x] All contracts defined (8)
- [x] All tests defined (16)
- [x] Coverage policy: AC 100%, CT 100%, Code 80%

承認者: 田中花子
日付:   2026-01-06
```

---

## Step 3: Phase 3 - Tasking（タスク分解）

### 3.1 tasks.md の作成

`specs/web_edi/tasks.md` を以下の内容で置き換えます：

```markdown
# FEAT-001: Web-EDI システムタスク

## 0. Canonical Tasks (YAML)

```yaml
tasks:
  # === G-00: 認証・共通基盤 ===
  - id: "T-G00-001"
    title: "プロジェクト初期セットアップ"
    description: "FastAPI, SQLAlchemy, Alembic, pytest, playwright の設定"
    plan_refs: ["G-00"]
    dependencies: []
    dod:
      - "pyproject.toml 作成"
      - "ディレクトリ構造作成"
      - "pytest実行可能"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G00-002"
    title: "データベーススキーマ設計・作成"
    description: "User, Order, OrderItem テーブル作成"
    plan_refs: ["G-00"]
    dependencies: ["T-G00-001"]
    dod:
      - "マイグレーションファイル作成"
      - "初期データ投入スクリプト作成"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G00-003"
    title: "認証API実装"
    description: "ログイン/ログアウトAPI実装"
    plan_refs: ["CT-API-05", "CT-API-08", "G-00"]
    dependencies: ["T-G00-002"]
    dod:
      - "POST /api/auth/login 実装"
      - "POST /api/auth/logout 実装"
      - "セッション管理実装"
      - "TS-CON-05, TS-CON-08 パス"
    estimated_hours: 3
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G00-004"
    title: "認証テスト実装"
    description: "TS-INT-01 統合テスト実装"
    plan_refs: ["TS-INT-01", "G-00"]
    dependencies: ["T-G00-003"]
    dod:
      - "ログイン成功テスト"
      - "ログイン失敗テスト"
      - "ログアウトテスト"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  # === G-01: 取引フロー ===
  - id: "T-G01-001"
    title: "注文登録API実装"
    description: "POST /api/orders エンドポイント実装"
    plan_refs: ["CT-API-01", "G-01"]
    dependencies: ["T-G00-003"]
    dod:
      - "注文作成ロジック実装"
      - "バリデーション実装"
      - "TS-CON-01 パス"
    estimated_hours: 3
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G01-002"
    title: "注文承諾API実装"
    description: "PUT /api/orders/{id}/accept エンドポイント実装"
    plan_refs: ["CT-API-02", "G-01"]
    dependencies: ["T-G01-001"]
    dod:
      - "承諾/拒否ロジック実装"
      - "ステータス更新実装"
      - "TS-CON-02 パス"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G01-003"
    title: "出荷通知API実装"
    description: "POST /api/orders/{id}/ship エンドポイント実装"
    plan_refs: ["CT-API-03", "G-01"]
    dependencies: ["T-G01-002"]
    dod:
      - "出荷情報登録ロジック実装"
      - "TS-CON-03 パス"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G01-004"
    title: "検収登録API実装"
    description: "POST /api/orders/{id}/receipt エンドポイント実装"
    plan_refs: ["CT-API-04", "G-01"]
    dependencies: ["T-G01-003"]
    dod:
      - "検収情報登録ロジック実装"
      - "TS-CON-04 パス"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G01-005"
    title: "注文統合テスト実装"
    description: "TS-INT-03, TS-INT-04 実装"
    plan_refs: ["TS-INT-03", "TS-INT-04", "G-01"]
    dependencies: ["T-G01-004"]
    dod:
      - "バリデーションテスト"
      - "注文詳細取得テスト"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G01-006"
    title: "UI実装（注文関連画面）"
    description: "注文登録/一覧/詳細画面のJinja2テンプレート作成"
    plan_refs: ["G-01"]
    dependencies: ["T-G01-004"]
    dod:
      - "注文登録フォーム"
      - "注文一覧画面"
      - "注文詳細画面"
      - "HTMXによる動的更新"
    estimated_hours: 4
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G01-007"
    title: "E2Eテスト実装（注文登録）"
    description: "TS-E2E-01 Playwrightテスト実装"
    plan_refs: ["TS-E2E-01", "G-01"]
    dependencies: ["T-G01-006"]
    dod:
      - "注文登録正常系テスト"
      - "注文登録異常系テスト"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G01-008"
    title: "E2Eテスト実装（注文承諾）"
    description: "TS-E2E-02 Playwrightテスト実装"
    plan_refs: ["TS-E2E-02", "G-01"]
    dependencies: ["T-G01-006"]
    dod:
      - "注文承諾正常系テスト"
      - "注文拒否テスト"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G01-009"
    title: "E2Eテスト実装（出荷通知）"
    description: "TS-E2E-03 Playwrightテスト実装"
    plan_refs: ["TS-E2E-03", "G-01"]
    dependencies: ["T-G01-006"]
    dod:
      - "出荷通知正常系テスト"
      - "出荷通知異常系テスト"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G01-010"
    title: "E2Eテスト実装（検収登録）"
    description: "TS-E2E-04 Playwrightテスト実装"
    plan_refs: ["TS-E2E-04", "G-01"]
    dependencies: ["T-G01-006"]
    dod:
      - "検収登録正常系テスト"
      - "検収登録異常系テスト"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  # === G-02: 照会・レポート ===
  - id: "T-G02-001"
    title: "注文一覧API実装"
    description: "GET /api/orders エンドポイント（フィルタリング対応）"
    plan_refs: ["CT-API-06", "CT-API-07", "G-02"]
    dependencies: ["T-G01-001"]
    dod:
      - "一覧取得実装"
      - "ステータスフィルター"
      - "日付範囲フィルター"
      - "TS-CON-06, TS-CON-07 パス"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G02-002"
    title: "取引履歴照会テスト実装"
    description: "TS-INT-02 統合テスト実装"
    plan_refs: ["TS-INT-02", "G-02"]
    dependencies: ["T-G02-001"]
    dod:
      - "フィルタリングテスト"
      - "ページネーションテスト"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"

  # === 最終検証 ===
  - id: "T-FINAL-001"
    title: "全テスト実行・カバレッジ確認"
    description: "pytest + Playwright 全テスト実行"
    plan_refs: []
    dependencies: ["T-G01-010", "T-G02-002"]
    dod:
      - "pytest 40/40 パス"
      - "Playwright 8/8 パス"
      - "カバレッジ 80%以上"
    estimated_hours: 1
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-FINAL-002"
    title: "エビデンスパック作成"
    description: "テスト結果、カバレッジレポート収集"
    plan_refs: []
    dependencies: ["T-FINAL-001"]
    dod:
      - "pytest-report.xml 生成"
      - "playwright-report.html 生成"
      - "coverage.html 生成"
      - "evidence_pack.md 更新"
    estimated_hours: 1
    assignee: "AI_Agent"
    status: "pending"

  tasks_gate_check:
    all_tasks_have_plan_refs: true
    e2e_tasks_exist: true
    no_orphan_tests: true
    tasks_ready_for_code: false  # Gate承認後にtrueにする
```

---

## 1. Task Dependency Graph

```
T-G00-001 (Setup)
    │
    ▼
T-G00-002 (DB Schema)
    │
    ▼
T-G00-003 (Auth API)
    │
    ├────────────────────────────────┐
    ▼                                ▼
T-G00-004 (Auth Test)           T-G01-001 (Order Create)
                                     │
                                     ├─────────────────────┐
                                     ▼                     ▼
                                T-G01-002 (Accept)    T-G02-001 (List)
                                     │                     │
                                     ▼                     ▼
                                T-G01-003 (Ship)      T-G02-002 (History Test)
                                     │
                                     ▼
                                T-G01-004 (Receipt)
                                     │
                                     ▼
                                T-G01-005 (Integration Tests)
                                     │
                                     ▼
                                T-G01-006 (UI)
                                     │
    ┌────────────┬────────────┬──────┴──────┐
    ▼            ▼            ▼             ▼
T-G01-007   T-G01-008   T-G01-009   T-G01-010
(E2E-01)    (E2E-02)    (E2E-03)    (E2E-04)
    │            │            │             │
    └────────────┴────────────┴──────┬──────┘
                                     ▼
                              T-FINAL-001 (All Tests)
                                     │
                                     ▼
                              T-FINAL-002 (Evidence)
```

---

## 2. Task Summary

| Group | Tasks | Total Hours |
|-------|-------|-------------|
| G-00 (認証) | 4 | 9h |
| G-01 (取引) | 10 | 21h |
| G-02 (照会) | 2 | 4h |
| FINAL | 2 | 2h |
| **合計** | **18** | **36h** |
```

### 3.2 Gate 5 の承認

`specs/web_edi/APPROVAL.md` に追記します（**人間のみ**）：

```markdown
## Gate 5: Tasks
- [x] tasks.md reviewed
- [x] All tasks have plan_refs
- [x] E2E tasks exist for e2e-tagged ACs (4 tasks)
- [x] Dependencies are clear
- [x] DoDs are specific and testable

承認者: 佐藤一郎
日付:   2026-01-06
```

---

## Step 4: Phase 4 - Execute（実装）

### 4.1 実装の進め方

タスクを依存関係順に1つずつ実装します。

```bash
# タスク状態の更新例（tasks.md を編集）
# status: "pending" → "in_progress" → "completed"
```

### 4.2 テスト実行コマンド

```bash
# pytest（Contract/Integration/Unit）
pytest specs/web_edi/tests/ -v

# Playwright（E2E）
npx playwright test specs/web_edi/tests/e2e/

# カバレッジ付き
pytest specs/web_edi/tests/ --cov=src --cov-report=html
```

### 4.3 実装完了の確認

各タスク完了時：

1. DoD の全項目を確認
2. 関連テストがパスすることを確認
3. tasks.md の status を `completed` に更新

---

## Step 5: Phase 5 - Verify（検証）

### 5.1 全テスト実行

```bash
# 1. pytest 実行
pytest specs/web_edi/tests/ -v --junitxml=test-results/pytest-report.xml

# 2. Playwright 実行
npx playwright test specs/web_edi/tests/e2e/ --reporter=html

# 3. カバレッジ確認
pytest specs/web_edi/tests/ --cov=src --cov-report=html --cov-fail-under=80
```

### 5.2 evidence_pack.md の更新

`specs/web_edi/implementation-details/evidence_pack.md` を更新：

```yaml
evidence:
  ci_artifacts:
    - type: "pytest_report"
      path: "test-results/pytest-report.xml"
      timestamp: "2026-01-06T16:00:00Z"
      status: "passed"
      summary: "40/40 tests passed (contract: 8, integration: 4, unit: 28)"

    - type: "playwright_report"
      path: "test-results/playwright-report.html"
      timestamp: "2026-01-06T16:10:00Z"
      status: "passed"
      summary: "8/8 e2e tests passed"

    - type: "coverage_report"
      path: "test-results/coverage.html"
      coverage: "85%"

    - type: "lint_report"
      path: "stride-lint-output.txt"
      status: "passed"

  security_scans:
    - type: "SAST"
      tool: "bandit"
      status: "passed"
      findings: 0

  provenance:
    ai_generated_files:
      - "src/api/routers/orders.py"
      - "src/api/routers/auth.py"
      - "specs/web_edi/tests/e2e/test_order_flow.py"
    human_reviewed: true
    reviewer: "Tech Lead"
```

### 5.3 Final 承認

`specs/web_edi/APPROVAL.md` に追記します（**人間のみ**）：

```markdown
## Final: Implementation
- [x] All tests passed (pytest: 40/40, Playwright: 8/8)
- [x] Code coverage >= 80% (actual: 85%)
- [x] Evidence pack complete
- [x] No critical security findings
- [x] AI-generated code reviewed

承認者: 山田太郎
日付:   2026-01-06
```

---

## チェックリスト

### Phase 1: Design
- [ ] basic_design.md 作成（WHO/WHAT/WHY）
- [ ] process.bpmn 作成（業務フロー）
- [ ] traceability_rows 定義（6行以上）
- [ ] stride-lint パス
- [ ] Gate 1 & 2 承認取得

### Phase 2: Specify
- [ ] spec.md 作成（ユースケース、AC）
- [ ] plan.md 作成（アーキテクチャ、テスト）
- [ ] openapi.yaml 作成（API契約）
- [ ] stride-lint パス
- [ ] Gate 3 & 4 承認取得

### Phase 3: Tasking
- [ ] tasks.md 作成（全タスク、DoD）
- [ ] 依存関係の定義
- [ ] stride-lint パス
- [ ] Gate 5 承認取得

### Phase 4: Execute
- [ ] タスク実装（1つずつ）
- [ ] テスト実装（Contract → Integration → E2E）
- [ ] カバレッジ確認（80%以上）

### Phase 5: Verify
- [ ] 全テストパス
- [ ] evidence_pack.md 完成
- [ ] Final 承認取得

---

## トラブルシューティング

### Q: stride-lint が失敗する

```bash
# エラーメッセージを確認
sdd-templates/tools/stride-lint specs/web_edi/ --verbose

# よくある原因:
# - YAML構文エラー
# - 必須フィールドの欠落
# - ID形式の不一致
```

### Q: E2Eテストがタイムアウトする

```python
# Playwrightのタイムアウトを延長
page.set_default_timeout(30000)  # 30秒

# ネットワーク待機を追加
page.wait_for_load_state("networkidle")
```

### Q: HTMXフォームが送信されない

```python
# JavaScriptで直接submit
page.evaluate("""
    () => {
        document.querySelector('form').submit();
    }
""")
```

---

## 参考リンク

- [SDDテンプレート GitHub](https://github.com/Tecnos-Japan-NGB/tecnos-sdd-templates)
- [stride-lint ガイド](appendix_b_stride_lint.md)
- [ID命名規則](appendix_a_id_conventions.md)
- [カバレッジポリシー](19_coverage_policy.md)

---

> SDD Templates Manual - Appendix B: Web-EDI 実践チュートリアル
