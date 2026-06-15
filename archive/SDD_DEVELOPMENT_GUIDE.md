# SDD開発ガイド - Spec-Driven Development 実践教科書

**バージョン**: 1.1.5
**対象**: SDDテンプレート初心者
**ベース**: sdd-templates (v1.2.6-tecnos)
**ケーススタディ**: Web-EDIシステム開発
**最終更新**: 2026-01-19

---

## 目次

1. [SDDとは](#1-sddとは)
2. [テンプレートパックの構成](#2-テンプレートパックの構成)
3. [開発フロー全体像](#3-開発フロー全体像)
4. [Phase 1: Design（設計）](#4-phase-1-design設計)
5. [Phase 2: Specify（仕様定義）](#5-phase-2-specify仕様定義)
6. [Phase 3: Tasking（タスク分解）](#6-phase-3-taskingタスク分解)
7. [Phase 4: Execute（実装）](#7-phase-4-execute実装)
8. [Phase 5: Verify（検証）](#8-phase-5-verify検証)
9. [Gate承認プロセス](#9-gate承認プロセス)
10. [テストテンプレート活用](#10-テストテンプレート活用)
11. [ケーススタディ: Web-EDI開発](#11-ケーススタディ-web-edi開発)
12. [よくある問題と解決策](#12-よくある問題と解決策)
13. [ベストプラクティス](#13-ベストプラクティス)
14. [関連ドキュメント](#14-関連ドキュメント)

---

## 1. SDDとは

### 1.1 基本原則

**SDD (Spec-Driven Development)** は、「**仕様が正本、コードは成果物**」という考え方に基づく開発手法です。

```
Spec IS the Code. Code is just a compile artifact.
（仕様こそがコード。コードは単なるコンパイル成果物。）
```

### 1.2 従来開発との違い

| 観点 | 従来開発 | SDD |
|------|---------|-----|
| 正本 | コード | 仕様書（Spec） |
| 変更フロー | コード先行 → ドキュメント後追い | 仕様変更 → コード自動追従 |
| トレーサビリティ | 事後的に追加 | 最初から組み込み |
| 品質ゲート | テスト結果のみ | 仕様準拠 + テスト + 承認 |
| AI活用 | 無制限 | ガバナンス付き（RACI+） |

### 1.3 Single Source of Truth (SSoT) 階層

SDDでは、以下の階層で情報の正本が定義されます：

```
┌─────────────────────────────────────────────────┐
│ 1. Intent & Flow（意図と業務フロー）            │
│    └─ basic_design.md + process.bpmn           │
├─────────────────────────────────────────────────┤
│ 2. Specs（仕様）                                │
│    └─ spec.md + plan.md                        │
├─────────────────────────────────────────────────┤
│ 3. Contracts（契約）                            │
│    └─ contracts/openapi.yaml                   │
├─────────────────────────────────────────────────┤
│ 4. Code（コード）                               │
│    └─ src/ + tests/                            │
└─────────────────────────────────────────────────┘

★ 鉄則: #4を変更するには、必ず#1-#3を先に更新する。
        仕様に逸脱したコードは「コードのバグ」である。
```

### 1.4 RACI+ ガバナンス

SDDでは、人間とAIの役割を明確に定義します：

| 役割 | 説明 | 例 |
|------|------|-----|
| **R** (Responsible) | 作業実行者 | AI Agent, Developer |
| **A** (Accountable) | 最終責任者 | **人間のみ**（AIは不可） |
| **C** (Consulted) | 相談相手 | Tech Lead, Architect |
| **I** (Informed) | 報告先 | PMO, Stakeholders |
| **+** (CI Gate) | 自動検証 | stride-lint, Tests |

---

## 2. テンプレートパックの構成

### 2.1 ディレクトリ構造

```
sdd-templates/
├── templates/                    # テンプレートファイル
│   ├── basic_design_template.md  # 基本設計テンプレート
│   ├── spec_template.md          # 仕様テンプレート
│   ├── plan_template.md          # 計画テンプレート
│   ├── tasks_template.md         # タスクテンプレート
│   ├── evidence_pack_template.md # エビデンスパック
│   ├── APPROVAL.md               # 承認テンプレート
│   └── contracts/
│       └── openapi_template.yaml # API契約テンプレート
├── tools/                        # 品質ゲートツール
│   ├── stride-lint              # 仕様検証ツール（実行可能）
│   ├── stride_lint.py           # Lintロジック
│   ├── stride_lint_spec.md      # Lint仕様書
│   ├── phase_gate.py             # フェーズゲート管理
│   └── setup_hooks.py            # Hook自動セットアップ
├── hooks/                        # 自動化フック
│   ├── phase_gate_hook.py        # 自動ゲートチェック
│   └── settings.json             # Hook設定テンプレート
├── memory/                       # 組織記憶
│   ├── constitution.md           # 原則・ID規約（不変）
│   ├── tecnos_org_constraints.md # 組織制約
│   └── artifact_registry.md      # 成果物マスター
├── policies/                     # ポリシー定義
│   └── bpmn_generator_rules.md   # BPMN生成ルール
├── agent_docs/                   # AI/Agent向けガイド (v1.2.4 新規)
│   ├── testing.md                # テスト実行ガイド（5言語対応）
│   ├── conventions.md            # 命名規則・コーディング規約
│   └── security.md               # セキュリティガイド
├── config/                       # 設定ファイル
│   ├── id_conventions.yaml       # ID命名規則
│   └── testing/                  # テスト設定テンプレート (v1.2.4 新規)
│       ├── pyproject.toml.snippet      # pytest/coverage/mypy/ruff設定
│       └── python/
│           ├── conftest.py.template    # pytestフィクスチャ
│           └── test_api.py.template    # APIテストパターン
├── docs/                         # リファレンスドキュメント (v1.2.4 新規)
│   ├── TEST_PATTERNS.md          # 検証済みテストパターン集
│   └── CI_CD_INTEGRATION.md      # CI/CD統合ガイド
└── examples/
    └── process_bpmn_example.bpmn  # BPMNスケルトン（記入例）
```

### 2.2 フィーチャー成果物の構造

各フィーチャーは `specs/<feature>/` 配下に以下の構造で作成します：

```
specs/<feature>/
├── APPROVAL.md                   # 人間承認記録（AI編集禁止）
├── basic_design.md               # Phase 1: 基本設計
├── process.bpmn                  # Phase 1: 業務フロー
├── spec.md                       # Phase 2: 仕様書
├── plan.md                       # Phase 2: 実装計画
├── contracts/
│   └── openapi.yaml              # Phase 2: API契約
├── tasks.md                      # Phase 3: タスク一覧
├── tests/                        # Phase 4: テストコード (v1.2.4 新規)
│   ├── conftest.py               # 共通フィクスチャ
│   ├── test_contracts.py         # 契約テスト
│   ├── test_integration.py       # 統合テスト
│   └── e2e/
│       └── test_e2e_workflow.py  # E2Eテスト
└── implementation-details/
    ├── evidence_pack.md          # Phase 4: エビデンス
    └── e2e_triage.md             # Phase 4: E2E失敗分析
```

> **重要**: テストファイルは `specs/<feature>/tests/` に配置します（ルートの `tests/` ではありません）。
> `pyproject.toml` の `testpaths` は `["specs/<feature>/tests"]` に設定してください。

### 2.3 ID命名規則

SDDでは、全ての成果物に一意のIDを付与し、トレーサビリティを確保します：

| 種類 | パターン | 例 |
|------|---------|-----|
| フィーチャー | `FEAT-[A-Z0-9]{3,}` | FEAT-001, FEAT-WEBEDI |
| ユースケース | `US-FEAT[ID]-[0-9]{3}` | US-FEAT001-001 |
| 受入条件 | `AC-US-FEAT[ID]-[0-9]{3}-[0-9]{2}` | AC-US-FEAT001-001-01 |
| 契約 | `CT-(API\|CLI\|EVT\|FILE\|BATCH\|EDI\|IDOC\|DB)-[0-9]{2}` | CT-API-01, CT-EDI-01 |
| テスト | `TS-(CON\|INT\|E2E\|UT)-[0-9]{2}` | TS-E2E-01, TS-INT-05 |
| タスク | `T-[A-Z0-9]{2,}-[0-9]{3}` | T-G01-001, T-API-003 |
| BPMNエレメント | `BPMN-(TASK\|GW\|EVT\|FLOW)-[0-9]{3}` | BPMN-TASK-001 |
| DBスキーマ | `DB-FEAT-[A-Z0-9]{3,}` | DB-FEAT-001 |

---

## 3. 開発フロー全体像

### 3.1 Phase Gate システム

SDDでは、5つのGateを通過しながら段階的に開発を進めます：

```
┌──────────────────────────────────────────────────────────────────┐
│ Phase 1: DESIGN                                                  │
│ ┌──────────────────┐    ┌──────────────────┐                    │
│ │ basic_design.md  │───▶│  process.bpmn    │                    │
│ │ (WHO/WHAT/WHY)   │    │  (業務フロー)     │                    │
│ └──────────────────┘    └──────────────────┘                    │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │ Gate 1 & 2 承認    │◀── 人間のみ編集可能    │
│                    │ (APPROVAL.md)      │                        │
│                    └─────────┬─────────┘                        │
└──────────────────────────────┼──────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 2: SPECIFY                                                 │
│ ┌──────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│ │    spec.md       │───▶│    plan.md       │───▶│ openapi.yaml│ │
│ │   (WHAT/WHY)     │    │   (HOW)          │    │ (契約)       │ │
│ └──────────────────┘    └──────────────────┘    └─────────────┘ │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │ Gate 3 & 4 承認    │                        │
│                    └─────────┬─────────┘                        │
└──────────────────────────────┼──────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 3: TASKING                                                 │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │                       tasks.md                               │ │
│ │                   (実行可能タスク)                            │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   Gate 5 承認      │                        │
│                    └─────────┬─────────┘                        │
└──────────────────────────────┼──────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 4: EXECUTE & VERIFY                                        │
│ ┌──────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│ │     src/         │    │    tests/        │    │evidence_pack│ │
│ │  (実装コード)     │    │  (テストコード)  │    │  (証跡)     │ │
│ └──────────────────┘    └──────────────────┘    └─────────────┘ │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   Final 承認       │                        │
│                    └─────────┬─────────┘                        │
└──────────────────────────────┼──────────────────────────────────┘
                               ▼
                          ✅ 完了
```

### 3.2 作業フロー概要

```
1. 準備
   └─▶ テンプレートコピー & プレースホルダー置換

2. Phase 1: Design
   └─▶ basic_design.md 作成
   └─▶ process.bpmn 作成
   └─▶ stride-lint 実行
   └─▶ ⛔ APPROVAL_PENDING → 人間承認待ち
   └─▶ ✅ Gate 1 & 2 承認完了

3. Phase 2: Specify
   └─▶ spec.md 作成
   └─▶ plan.md 作成
   └─▶ openapi.yaml 作成
   └─▶ stride-lint 実行
   └─▶ ⛔ APPROVAL_PENDING → 人間承認待ち
   └─▶ ✅ Gate 3 & 4 承認完了

4. Phase 3: Tasking
   └─▶ tasks.md 作成
   └─▶ stride-lint 実行
   └─▶ ⛔ APPROVAL_PENDING → 人間承認待ち
   └─▶ ✅ Gate 5 承認完了

5. Phase 4: Execute
   └─▶ タスク実装（1つずつ）
   └─▶ テスト実装 & 実行
   └─▶ evidence_pack.md 更新
   └─▶ stride-lint 実行
   └─▶ ⛔ APPROVAL_PENDING → 人間承認待ち
   └─▶ ✅ Final 承認完了
```

---

## 4. Phase 1: Design（設計）

### 4.1 目的

- 「誰が」「何を」「なぜ」を明確化する
- 業務フローを可視化する
- 人間とAIの認識齟齬を解消する

### 4.2 作成手順

#### Step 1: プロジェクト初期化

```bash
# フィーチャーディレクトリ作成
mkdir -p specs/my_feature/{contracts,tests,implementation-details}

# テンプレートコピー
cp sdd-templates/templates/basic_design_template.md specs/my_feature/basic_design.md
cp sdd-templates/templates/APPROVAL.md specs/my_feature/APPROVAL.md

# プレースホルダー置換（macOS、サブディレクトリ含む）
sed -i '' 's/FEAT-XXX/FEAT-001/g' specs/my_feature/*.md specs/my_feature/*/*.md
sed -i '' 's/FEATXXX/001/g' specs/my_feature/*.md specs/my_feature/*/*.md
sed -i '' 's/XXX_feature_name/web_edi/g' specs/my_feature/*.md specs/my_feature/*/*.md
```

#### Step 2: basic_design.md の作成

`basic_design.md` は以下の構造で記述します：

```yaml
# 0. Canonical Basic Design (YAML)
basic_design:
  context:
    who: "発注側（バイヤー）と受注側（サプライヤー）の業務担当者"
    what: "Web-EDIシステムを通じて取引プロセスをデジタル化"
    why: "FAX・メール・電話による非効率な業務を排除"

  scope:
    in:
      - "注文登録・送信"
      - "注文請確認・返信"
      - "出荷通知"
      - "検収登録"
    out:
      - "請求・支払処理（将来）"
      - "外部ERP連携（将来）"

  traceability_rows:
    - rq:
        id: "RQ-001"
        statement: "発注側担当者が注文を登録できる"
      us:
        id: "US-FEAT001-001"
        title: "注文登録"
      ac:
        id: "AC-US-FEAT001-001-01"
        statement: "注文登録画面で品目・数量・納期を入力し保存すると注文が作成される"
        tags: ["integration", "e2e"]
      bpmn:
        id: "BPMN-TASK-001"
      contract:
        id: "CT-API-01"
      test:
        id: "TS-E2E-01"
      task:
        id: "T-G01-001"
```

**ポイント:**
- `traceability_rows` で要件→ユースケース→受入条件→BPMN→契約→テスト→タスクを紐付け
- `tags: ["e2e"]` は**重要なユーザージャーニーのみ**に付与
- `open_questions` に未確定事項を明記（推測で埋めない）

#### Step 3: process.bpmn の作成

業務フローをBPMN 2.0形式で作成します（Camunda 8互換）：

```
発注側プール                 受注側プール
┌────────────────────┐     ┌────────────────────┐
│  ◯→[注文登録]→◇   │─────▶│  ◯→[注文確認]→◇   │
│     │           │      │     │           │    │
│     ▼           │      │     ▼           │    │
│  [検収登録]←────│◀─────│  [出荷通知]────│    │
│     │                  │     │                │
│     ▼                  │     ▼                │
│    ●                   │    ●                 │
└────────────────────┘     └────────────────────┘
```

#### Step 4: stride-lint の実行

```bash
sdd-templates/tools/stride-lint specs/my_feature/
```

**期待される結果:**
- 構造エラーがなければ `APPROVAL_PENDING` が表示される
- これは正常 - Phase 1の人間承認を待っている状態

### 4.3 Gate 1 & 2 の承認条件

| 条件 | チェック内容 |
|------|-------------|
| traceability_present | トレーサビリティ行が1つ以上ある |
| integration_flows_identified | 統合フローが1つ以上定義されている |
| delivery_model_defined | 開発モデルが定義されている |
| raci_plus_defined | RACI+が定義されている |
| process_bpmn_linked | process.bpmnへの参照がある |
| blocking_questions = 0 | 未解決の質問がない |

---

## 5. Phase 2: Specify（仕様定義）

### 5.1 目的

- 「何を作るか」を詳細に定義する（spec.md）
- 「どう作るか」の方針を決める（plan.md）
- API契約を定義する（openapi.yaml）

### 5.2 作成手順

#### Step 1: Gate承認の確認

```bash
python3 sdd-templates/tools/phase_gate.py status specs/my_feature/
```

Gate 1 & 2 が承認されていることを確認してから進む。

#### Step 2: spec.md の作成

```yaml
# 0. Canonical Spec (YAML)
spec:
  overview:
    who: "発注側と受注側の担当者"
    what: "取引プロセスをデジタル化"
    why: "業務効率向上"

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
        - "取引先を選択"
        - "品目・数量・納期を入力"
        - "送信ボタンを押す"
      acceptance:
        - id: "AC-US-FEAT001-001-01"
          statement: "注文が作成され受注側に送信される"
          tags: ["integration", "e2e"]
          priority: "must"

  nfrs:
    security:
      - "ユーザー認証必須"
      - "自社取引のみアクセス可能"
    integration:
      - "リアルタイム通知"
      - "API応答 P95 < 3秒"
    data:
      - "監査ログ7年保持"
      - "取引データ整合性保証"
```

**ポイント:**
- spec.md には「HOW（実装詳細）」を書かない → plan.md へ
- 受入条件（AC）には優先度（must/should/could）を付ける
- NFRは security/integration/data の3カテゴリ必須

#### Step 3: plan.md の作成

```yaml
# 0. Canonical Plan (YAML)
plan:
  architecture:
    overview: "FastAPI + HTMX + SQLite の軽量Web構成"
    components:
      - name: "API Layer"
        technology: "FastAPI"
        responsibility: "REST API提供"
      - name: "UI Layer"
        technology: "Jinja2 + HTMX"
        responsibility: "動的Web UI"
      - name: "Data Layer"
        technology: "SQLAlchemy + SQLite"
        responsibility: "データ永続化"

  coverage_policy:
    ac_coverage: "100%"      # 全ACをテストでカバー
    ct_coverage: "100%"      # 全契約をテストでカバー
    code_coverage: "80%"     # コードカバレッジ目標

  contracts:
    - id: "CT-API-01"
      type: "REST API"
      method: "POST"
      path: "/api/orders"
      covers_ac_ids: ["AC-US-FEAT001-001-01"]

  tests:
    - id: "TS-E2E-01"
      type: "e2e"
      title: "発注側：注文登録→受注側通知"
      covers_ac_ids: ["AC-US-FEAT001-001-01"]
      covers_contract_ids: ["CT-API-01"]

  groups:
    - id: "G-01"
      name: "注文フロー実装"
      bpmn_elements: ["BPMN-TASK-001", "BPMN-TASK-002"]
      tasks_prefix: "T-G01"
```

**ポイント:**
- `coverage_policy` でカバレッジ目標を定義
- `tests` は `covers_ac_ids` と `covers_contract_ids` でトレーサビリティ確保
- `groups` でBPMNエレメントとタスクを紐付け

#### Step 4: openapi.yaml の作成

```yaml
openapi: "3.0.3"
info:
  title: "Web-EDI API"
  version: "1.0.0"
paths:
  /api/orders:
    post:
      operationId: "createOrder"
      summary: "注文登録"
      tags: ["orders"]
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
```

### 5.3 Gate 3 & 4 の承認条件

| 条件 | チェック内容 |
|------|-------------|
| min_use_cases >= 1 | ユースケースが1つ以上 |
| min_acceptance_criteria >= 3 | 受入条件が3つ以上 |
| min_integration_ac >= 1 | integration タグ付きACが1つ以上 |
| no_blocking_questions | 未解決質問がない |
| spec_as_code_defined | 契約ファイルが定義されている |
| coverage_policy_defined | カバレッジポリシーが定義されている |
| contracts_defined | 契約が定義されている |
| tests_prioritized | テストが優先度付きで定義されている |

---

## 6. Phase 3: Tasking（タスク分解）

### 6.1 目的

- plan.md を実行可能なタスクに分解する
- 依存関係を明確にする
- Definition of Done (DoD) を定義する

### 6.2 作成手順

#### Step 1: tasks.md の作成

```yaml
# 1. Canonical Tasks (YAML)
tasks:
  - id: "T-G01-001"
    title: "注文登録API実装"
    description: "POST /api/orders エンドポイント実装"
    plan_refs: ["CT-API-01", "G-01"]
    dependencies: ["T-G01-000"]  # DB設定に依存
    dod:
      - "APIが201を返す"
      - "DBに注文レコードが作成される"
      - "TS-INT-01がパスする"
    estimated_hours: 4
    assignee: "AI_Agent"
    status: "pending"

  - id: "T-G01-002"
    title: "注文登録E2Eテスト実装"
    description: "TS-E2E-01 Playwrightテスト実装"
    plan_refs: ["TS-E2E-01", "G-01"]
    dependencies: ["T-G01-001"]
    dod:
      - "Playwrightテストが実行可能"
      - "注文フロー全体を検証"
    estimated_hours: 2
    assignee: "AI_Agent"
    status: "pending"
```

**ポイント:**
- `plan_refs` は plan.md の安定ID（CT-*, TS-*, G-*）のみ参照可能
- e2e タグ付きACがある場合、E2Eテストタスクが必須
- 各タスクにDoD（完了定義）を明記

### 6.3 Gate 5 の承認条件

| 条件 | チェック内容 |
|------|-------------|
| all_tasks_have_plan_refs | 全タスクがplan_refsを持つ |
| e2e_tasks_exist | e2eタグ付きACに対応するE2Eタスクがある |
| no_orphan_tests | テスト定義に対応するタスクがある |

---

## 7. Phase 4: Execute（実装）

### 7.1 目的

- タスクを1つずつ実装する
- テストを実行し、仕様準拠を確認する
- エビデンスを収集する

### 7.2 実装フロー

```
┌─────────────────────────────────────────────────────────────┐
│                    タスク実装ループ                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│   │タスク選択│───▶│  実装   │───▶│テスト実行│───▶│DoD確認  │ │
│   └─────────┘    └─────────┘    └─────────┘    └────┬────┘ │
│        ▲                                            │      │
│        │         ┌────────────┐                     │      │
│        │    NG   │仕様/計画   │◀────────────────────┘      │
│        └─────────│  見直し    │        OK                  │
│                  └────────────┘         │                  │
│                                         ▼                  │
│                                 ┌─────────────┐            │
│                                 │ 次タスクへ   │            │
│                                 └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Inner Loop（内側ループ）

AIエージェントが実装中に繰り返すループ：

1. **タスク確認** - tasks.md から次のタスクを選択
2. **実装** - コード作成
3. **ローカルテスト** - テスト実行
4. **DoD確認** - 完了条件を満たしているか確認
5. **次へ or 修正** - OK なら次、NG なら修正

### 7.4 Outer Loop（外側ループ）

Phase 完了時に実行するチェック：

```bash
# 1. stride-lint 実行
sdd-templates/tools/stride-lint specs/my_feature/

# 2. 全テスト実行（pytest + Playwright）
pytest specs/my_feature/tests/ -v                    # Contract/Unit/Integration
npx playwright test specs/my_feature/tests/e2e/      # E2E

# 3. カバレッジ確認
pytest specs/my_feature/tests/ --cov=src --cov-report=html
```

### 7.5 仕様逸脱時の対応

実装中に仕様の問題を発見した場合：

```
⚠️ 絶対禁止: 仕様を無視してコードを書く

✅ 正しい対応:
1. 実装を一時停止
2. 逸脱内容を記録
3. spec.md / plan.md を更新
4. stride-lint を再実行
5. 承認済みGateに影響する場合は再承認を依頼
6. 実装を再開
```

---

## 8. Phase 5: Verify（検証）

### 8.1 目的

- 全テストがパスすることを確認
- エビデンスパックを完成させる
- 最終承認を取得する

### 8.2 Evidence Pack の構成

```yaml
# evidence_pack.md
evidence:
  ci_artifacts:
    - type: "pytest_report"
      path: "test-results/pytest-report.xml"
      timestamp: "2026-01-05T16:28:00Z"
      status: "passed"
      summary: "40/40 tests passed (contract: 15, unit/integration: 25)"

    - type: "playwright_report"
      path: "test-results/playwright-report.html"
      timestamp: "2026-01-05T16:30:00Z"
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
      - "src/api/routers/api.py"
      - "specs/my_feature/tests/e2e/test_e2e_workflow.py"
    human_reviewed: true
    reviewer: "Tech Lead"
```

### 8.3 Final 承認条件

| 条件 | チェック内容 |
|------|-------------|
| all_tests_pass | 全テストがパス |
| coverage_met | カバレッジ目標達成 |
| evidence_pack_complete | エビデンスパックが完成 |
| no_critical_findings | セキュリティスキャンで重大な問題なし |

---

## 9. Gate承認プロセス

### 9.1 APPROVAL.md の構造

```markdown
# APPROVAL.md - Human-Only Approval Record

## Gate 1: Basic Design
- [x] basic_design.md reviewed
- [x] WHO/WHAT/WHY is clear
- [x] Traceability rows are complete

承認者: 山田太郎
日付:   2026-01-05

## Gate 2: BPMN
- [x] process.bpmn reviewed
- [x] Flow is correct and complete

承認者: 山田太郎
日付:   2026-01-05

## Gate 3: Spec
- [x] spec.md reviewed
- [x] All ACs are clear and testable

承認者: 田中花子
日付:   2026-01-05

... (以下略)
```

### 9.2 AIの行動規則

```
⛔ APPROVAL.md はAI編集禁止

AIが取るべき行動:
1. stride-lint を実行
2. APPROVAL_PENDING が表示されたら完全停止
3. ユーザーに承認を依頼: "Gate X の承認が必要です。APPROVAL.md を編集してください。"
4. ユーザーの承認完了報告を待つ
5. 承認後、次のPhaseに進む
```

### 9.3 承認後の変更ルール

```
⚠️ 承認済み成果物の変更禁止ルール

Gate通過後、以下のファイルは変更禁止:
- Gate 1, 2 通過後: basic_design.md, process.bpmn
- Gate 3, 4 通過後: spec.md, plan.md, contracts/
- Gate 5 通過後: tasks.md

変更が必要な場合:
1. change_log.md に変更理由を記録
2. 該当Gateの再承認を依頼
3. 再承認完了後に変更を適用
```

---

## 10. テストテンプレート活用

v1.2.5-tecnos では、テスト作成を効率化するためのテンプレートとパターン集が追加されました。

### 10.1 利用可能なテストテンプレート

| テンプレート | 場所 | 用途 |
|-------------|------|------|
| `conftest.py.template` | `config/testing/python/` | pytest共通フィクスチャ |
| `test_api.py.template` | `config/testing/python/` | REST APIテストパターン |
| `pyproject.toml.snippet` | `config/testing/` | pytest/coverage/mypy/ruff設定 |
| `TEST_PATTERNS.md` | `docs/` | 検証済みテストパターン集 |

### 10.2 テストパターン集（TEST_PATTERNS.md）

`docs/TEST_PATTERNS.md` には、実プロジェクトで検証済みの7カテゴリのテストパターンが収録されています：

| カテゴリ | 内容 | 主なパターン |
|---------|------|-------------|
| 認証テスト | ログイン/ログアウト/セッション管理 | 成功・失敗・セッション切れ |
| CRUDテスト | 基本的なデータ操作 | 作成・取得・更新・削除 |
| ワークフローテスト | 状態遷移の検証 | 正常遷移・不正遷移・並行処理 |
| エラーハンドリング | エラー応答の検証 | 400/401/403/404/500系 |
| フィルタリング・ページネーション | 一覧取得の検証 | 絞り込み・並べ替え・ページング |
| 契約テスト | OpenAPI準拠の検証 | スキーマ検証・必須フィールド |
| カバレッジ改善 | 不足カバレッジの補完 | 境界値・異常系・並行処理 |

### 10.3 pyproject.toml 設定テンプレート

`config/testing/pyproject.toml.snippet` には、SDD準拠のテスト設定が含まれています。

#### 主な設定内容

```toml
[tool.pytest.ini_options]
# SDD準拠テストパス（ルートの /tests/ ではない）
testpaths = ["specs/XXX_feature_name/tests"]

# テストマーカー（選択的テスト実行用）
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (may require external services)",
    "contract: Contract tests (API schema validation)",
    "e2e: End-to-end tests (Playwright, browser-based)",
    "slow: Tests that take more than 1 second",
]

# pytest-asyncio 競合回避（重要）
# TestClientとの競合を防ぐため、asyncioプラグインを無効化
addopts = ["-v", "--strict-markers", "-p", "no:asyncio"]
```

#### pytest-asyncio 競合回避について

FastAPIの `TestClient` は同期APIを使用するため、`pytest-asyncio` との競合が発生することがあります。
`pyproject.toml.snippet` では `-p no:asyncio` オプションでこれを回避しています。

```toml
# カバレッジ設定（Layer-3 コードカバレッジ目標: 80%）
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
fail_under = 80  # 80%未満でCI失敗
```

### 10.4 conftest.py テンプレート

#### conftest.py の構成

```python
# specs/<feature>/tests/conftest.py
import pytest
from fastapi.testclient import TestClient  # 同期テスト用
from playwright.sync_api import Page        # E2Eテスト用

# === 認証フィクスチャ ===
@pytest.fixture
def auth_headers():
    """認証ヘッダーを提供"""
    return {"Authorization": "Bearer test-token"}

@pytest.fixture
def authenticated_buyer_page(page: Page):
    """認証済みバイヤーページ"""
    page.goto("/login")
    page.fill('input[name="username"]', "buyer")
    page.fill('input[name="password"]', "buyer123")
    page.click('button[type="submit"]')
    page.wait_for_url("**/orders**")
    yield page

# === テストデータフィクスチャ ===
@pytest.fixture
def sample_order():
    """サンプル注文データ"""
    return {
        "partner_id": 1,
        "items": [{"product_id": 1, "quantity": 10}],
        "delivery_date": "2026-01-15"
    }
```

### 10.5 E2Eテストのベストプラクティス

#### HTMX/SPAフォーム送信の処理

```python
# 問題: Playwrightの通常クリックではHTMXフォームが送信されない

# 解決: JavaScriptで直接submit
page.evaluate("""
    () => {
        document.querySelector('form[action="/orders/new"]').submit();
    }
""")
page.wait_for_load_state("networkidle")
```

#### Strict Mode違反の回避

```python
# 問題: 複数要素マッチでテスト失敗

# 解決1: .first を使用
expect(page.locator("text=completed").first).to_be_visible()

# 解決2: より具体的なセレクタ
expect(page.locator("[data-testid='order-status']")).to_have_text("completed")
```

#### セッション管理

```python
# ユーザー切り替え時は明示的にログアウト
page.click('button:has-text("Logout")')
page.wait_for_url("**/login**")
page.wait_for_load_state("networkidle")
```

### 10.6 5言語対応テストコマンド

`agent_docs/testing.md` には、5言語（Python/TypeScript/Rust/Java/Go）のテスト実行コマンドが定義されています：

> **注意**: SDDプロジェクトでは、テストパスは `specs/<feature>/tests/` を使用します。
> 以下は一般的なプロジェクト構成でのコマンド例です。

| 言語 | 単体テスト | 統合テスト | E2Eテスト |
|------|-----------|-----------|----------|
| Python | `pytest tests/ -v` | `pytest tests/integration/ -v` | `npx playwright test` |
| TypeScript | `npm test` | `npm run test:integration` | `npx playwright test` |
| Rust | `cargo test` | `cargo test --test integration` | `cargo test --test e2e` |
| Java | `mvn test` | `mvn verify -Pintegration` | `mvn verify -Pe2e` |
| Go | `go test ./...` | `go test ./... -tags=integration` | `go test ./... -tags=e2e` |

---

## 11. ケーススタディ: Web-EDI開発

### 11.1 プロジェクト概要

| 項目 | 内容 |
|------|------|
| システム名 | Web-EDI |
| 目的 | 発注側・受注側間の電子取引 |
| 技術スタック | FastAPI + HTMX + SQLite |
| テスト | pytest + Playwright |

### 11.2 開発タイムライン

```
Day 1: Phase 1 (Design)
├─ basic_design.md 作成（WHO/WHAT/WHY定義）
├─ 8つのトレーサビリティ行を定義
├─ process.bpmn 作成（発注・受注の2プール）
├─ stride-lint 実行 → APPROVAL_PENDING
└─ Gate 1 & 2 承認取得

Day 1: Phase 2 (Specify)
├─ spec.md 作成（8ユースケース、10受入条件）
├─ plan.md 作成（3層カバレッジポリシー）
├─ openapi.yaml 作成（8 API契約）
├─ stride-lint 実行 → APPROVAL_PENDING
└─ Gate 3 & 4 承認取得

Day 1: Phase 3 (Tasking)
├─ tasks.md 作成（20タスク）
├─ E2Eテスト仕様4件（TS-E2E-01〜04）を含む
├─ stride-lint 実行 → APPROVAL_PENDING
└─ Gate 5 承認取得

Day 1-2: Phase 4 (Execute)
├─ タスク実装（API, UI, Tests）
├─ Contract Tests 15件実装（pytest）
├─ E2E Tests 8件実装（4仕様 × 正常/異常系 = 8テスト関数、Playwright）
├─ Unit/Integration Tests 25件実装（pytest）
└─ 全テストパス（pytest: 40, Playwright: 8）

Day 2: Phase 5 (Verify)
├─ evidence_pack.md 完成
├─ スクリーンショット収集
├─ 実装マニュアル作成
└─ Final 承認取得
```

### 11.3 テスト結果

| カテゴリ | フレームワーク | テスト数 | 結果 |
|---------|---------------|---------|------|
| Contract Tests | pytest | 15 | 100% PASSED |
| Unit/Integration | pytest | 25 | 100% PASSED |
| **pytest 小計** | | **40** | **100%** |
| E2E Tests | Playwright | 8 | 100% PASSED |
| **総合計** | | **48** | **100%** |

### 11.4 学んだ教訓

#### 教訓1: トレーサビリティの価値

```
問題: テスト漏れの発見が遅れる

解決: basic_design.md のトレーサビリティ行で
      RQ → US → AC → CT → TS → Task を紐付け

効果: stride-lint が自動で漏れを検出
```

#### 教訓2: E2Eテストの範囲限定

```
問題: 全ACにe2eタグを付けるとテスト爆発

解決: e2eタグは「重要なユーザージャーニー」のみ
      - 注文登録（TS-E2E-01）→ 正常系/異常系で2テスト関数
      - 注文承諾（TS-E2E-02）→ 正常系/異常系で2テスト関数
      - 出荷通知（TS-E2E-03）→ 正常系/異常系で2テスト関数
      - 検収登録（TS-E2E-04）→ 正常系/異常系で2テスト関数

効果: E2E仕様4件（テスト関数8件）+ Integration で適切なバランス
```

#### 教訓3: Playwright E2Eテストのコツ

```python
# 問題: HTMXフォームがPlaywrightで動かない

# 解決: JavaScriptで直接submit
page.evaluate("""
    () => {
        document.querySelector('form[action="/orders/new"]').submit();
    }
""")
page.wait_for_load_state("networkidle")

# 問題: 複数要素にマッチしてstrict mode違反

# 解決: .first を使用
expect(page.locator("text=completed").first).to_be_visible()
```

---

## 12. よくある問題と解決策

### 12.1 stride-lint エラー

#### エラー: `APPROVAL_PENDING`

```
原因: Gateの承認が未完了

解決:
1. これは正常な動作（承認待ち状態）
2. ユーザーに APPROVAL.md の編集を依頼
3. 承認後、再度 stride-lint を実行
```

#### エラー: `MISSING_PLAN_REFS`

```
原因: tasks.md のタスクに plan_refs がない

解決:
tasks:
  - id: "T-G01-001"
    plan_refs: ["CT-API-01", "G-01"]  # ← これを追加
```

#### エラー: `ORPHAN_TEST`

```
原因: plan.md にテスト定義があるが tasks.md にタスクがない

解決:
tasks.md にテスト実装タスクを追加
```

### 12.2 Phase Gate エラー

#### エラー: `BLOCKED - Gate X not approved`

```
原因: 前のPhaseの承認なしに次のPhaseのファイルを作成しようとした

解決:
1. 先に APPROVAL.md で前のGateを承認
2. その後、次のPhaseのファイルを作成
```

### 12.3 承認後の変更エラー

#### エラー: `POST_APPROVAL_CHANGE_VIOLATION`

```
原因: 承認済みファイルを変更しようとした

解決:
1. change_log.md に変更理由を記録
2. 該当Gateの再承認を依頼
3. 再承認後に変更を適用
```

---

## 13. ベストプラクティス

### 13.1 設計フェーズ

| ルール | 説明 |
|--------|------|
| 推測で埋めない | 不明点は `open_questions` に記録し、確認後に埋める |
| トレーサビリティ先行 | 最初にRQ→US→ACの紐付けを完成させる |
| e2eタグは厳選 | 重要なユーザージャーニーのみに付与 |
| BPMNはシンプルに | 複雑すぎるフローは分割を検討 |

### 13.2 仕様フェーズ

| ルール | 説明 |
|--------|------|
| WHATとHOWを分離 | spec.md にHOWを書かない → plan.md へ |
| ACは検証可能に | 曖昧な表現を避け、テスト可能な条件で記述 |
| NFRは3カテゴリ必須 | security, integration, data を必ず含める |
| カバレッジポリシー明記 | AC 100%, CT 100%, Code 80% など |

### 13.3 タスキングフェーズ

| ルール | 説明 |
|--------|------|
| plan_refs必須 | 全タスクが plan.md の安定IDを参照 |
| DoD明記 | 完了条件を具体的に記述 |
| 依存関係を明確に | dependencies で順序を定義 |
| 粒度は4-8時間 | 1タスク = 半日〜1日が目安 |

### 13.4 実装フェーズ

| ルール | 説明 |
|--------|------|
| 1タスクずつ | 並行作業は避け、1つずつ完了させる |
| 仕様逸脱禁止 | コードが仕様と合わない場合は仕様を先に更新 |
| テスト先行 | 可能な限りTDDで進める |
| エビデンス収集 | テスト結果、カバレッジを evidence_pack.md に記録 |

### 13.5 検証フェーズ

| ルール | 説明 |
|--------|------|
| 全テストパス必須 | 1つでも失敗があれば承認不可 |
| カバレッジ目標達成 | plan.md で定義した目標をクリア |
| セキュリティスキャン | SAST/SCA/Secrets スキャンを実行 |
| Provenance記録 | AI生成ファイルを明記 |

---

## まとめ

SDDテンプレートを使った開発は、以下のサイクルで進めます：

```
1. Design (basic_design.md + process.bpmn)
   ↓ Gate 1, 2 承認
2. Specify (spec.md + plan.md + contracts/)
   ↓ Gate 3, 4 承認
3. Tasking (tasks.md)
   ↓ Gate 5 承認
4. Execute (src/ + tests/)
   ↓ Final 承認
5. Complete ✅
```

**覚えておくべき3つの鉄則:**

1. **Spec IS the Code** - 仕様が正本、コードは成果物
2. **Gate承認は人間のみ** - AIはAPPROVAL.mdを編集できない
3. **仕様逸脱はコードのバグ** - コードを直す前に仕様を更新

このガイドに従って開発を進めることで、トレーサビリティが確保され、品質の高いソフトウェアを効率的に開発できます。

---

## 14. 関連ドキュメント

### 14.1 テンプレートパック内ドキュメント

| ドキュメント | 場所 | 用途 |
|-------------|------|------|
| QUICKSTART.md | `sdd-templates/` | 新規参画者向け最短ルート（30分） |
| CHEATSHEET.md | `sdd-templates/` | ID規約・タグ・エラー一覧（参照用） |
| MIGRATION.md | `sdd-templates/` | v1.2.2/v1.2.3/v1.2.4→v1.2.5 移行手順 |
| TEST_PATTERNS.md | `sdd-templates/docs/` | 検証済みテストパターン集 |
| CI_CD_INTEGRATION.md | `sdd-templates/docs/` | CI/CD統合ガイド（5言語対応） |

### 14.2 Agent向けドキュメント

| ドキュメント | 場所 | 用途 |
|-------------|------|------|
| testing.md | `sdd-templates/agent_docs/` | テスト実行ガイド（5言語対応） |
| conventions.md | `sdd-templates/agent_docs/` | 命名規則・コーディング規約 |
| security.md | `sdd-templates/agent_docs/` | セキュリティガイド |
| sdd_guidelines.md | `agent_docs/` | SDD開発ガイドライン |
| sdd_templates.md | `agent_docs/` | テンプレート使用方法 |

### 14.3 ツール仕様

| ドキュメント | 場所 | 用途 |
|-------------|------|------|
| stride_lint_spec.md | `sdd-templates/tools/` | stride-lint 仕様書 |
| bpmn_generator_rules.md | `sdd-templates/policies/` | BPMN生成ルール |

### 14.4 組織記憶

| ドキュメント | 場所 | 用途 |
|-------------|------|------|
| constitution.md | `sdd-templates/memory/` | Nine Articles + ID規約（不変） |
| tecnos_org_constraints.md | `sdd-templates/memory/` | Tecnos組織制約 |
| artifact_registry.md | `sdd-templates/memory/` | 成果物マスター |

---

**バージョン履歴**

| バージョン | 日付 | 変更内容 |
|-----------|------|---------|
| 1.1.5 | 2026-01-19 | sdd-templates v1.2.6-tecnos対応: ディレクトリ名変更、VERSION SSoT導入 |
| 1.1.4 | 2026-01-07 | APPROVAL.mdサンプルをstride-lint期待値に修正（承認者:/日付:形式、Gate 2: BPMN、Gate 3: Spec） |
| 1.1.3 | 2026-01-06 | テストパスをSDD規約（specs/\<feature\>/tests/）に修正、E2E仕様4件→テスト関数8件の関係を明記、Python E2EコマンドをPlaywrightに修正 |
| 1.1.2 | 2026-01-06 | テスト結果をpytest/Playwright別に明記（48テスト→pytest 40 + Playwright 8） |
| 1.1.1 | 2026-01-05 | pyproject.toml.snippet（pytest-asyncio競合回避）の説明追加 |
| 1.1.0 | 2026-01-05 | v1.2.5-tecnos対応: テストテンプレートセクション追加、ディレクトリ構造更新、関連ドキュメント参照追加 |
| 1.0.0 | 2026-01-05 | 初版作成（Web-EDIケーススタディ含む） |
