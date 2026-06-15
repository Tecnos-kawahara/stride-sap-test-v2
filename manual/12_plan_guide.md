# 12. 実装計画ガイド - plan.md の書き方

**所要時間**: 約30分

---

## このガイドで学ぶこと

1. plan.md の目的
2. 契約（Contract）の定義
3. テスト戦略とCoverage Policy
4. Evidence Pack
5. フェーズとグループ

---

**サンプル参照**: `sdd-templates/specs/sample_feature` に Web-EDI の参考サンプルがあります（未承認/プレースホルダあり）。  
**注**: パスは例なので、自分の機能では `specs/<feature>` に置き換えます。

## 1. plan.md の目的

### 何を書くか

**plan.md** は「HOW（どのように）」を定義する実装計画です。

| 書くこと | 書かないこと |
|----------|-------------|
| 契約（API/CLI/Event等） | ビジネス要件（→ spec） |
| テスト戦略 | 実装コード |
| アーキテクチャ | 詳細設計 |
| フェーズ・グループ | |
| Evidence Pack | |

**補足**: 日程や担当の割り当ては tasks.md やプロジェクト管理ツールで扱います。

### 重要な原則

```
「コード」は書かない → 判断・分解・順序のみ
```

### 初心者向けの書き方の順序

1. **contracts（CT）** を列挙する  
2. **tests（TS）** を定義し、AC/CTをカバーする  
3. **coverage_policy** を設定する  
4. **evidence_pack** を定義する  
5. **architecture / phases / groups** を整理する

### このパートの引き渡し（次の成果物との関係）

plan は「実行と検証の設計図」です。どの契約を作り、どのテストで合否を確認するかを定義します。

```
plan
  -> tasks.md        : CT/TSを作業に落とす
  -> evidence_pack   : 収集すべき証跡を確定
  -> 実装/テスト      : 実行の優先順位と順序を決める
```

**最低限引き渡すべき項目**:
- contracts（CT）
- test_strategy.tests（TS）
- coverage_policy（テスト網羅のルール）
- evidence_pack（証跡の定義）
- phases / groups（作業の順序）

---

## 2. 契約（Contract）の定義

> **💡 「契約」とは？**
>
> SDDで使う「契約」は法的な契約書ではありません。
> **システム同士が通信するときの「約束事」を文書化したもの**です。
>
> 例えば「POST /orders を呼ぶと、受注番号がJSON形式で返る」というルールを
> OpenAPI形式で文書化したものが「API契約」です。
>
> 詳しくは [index.md の「契約とは何か」](index.md#-契約contractとは何か) を参照してください。

**補足（初心者向け）**: 外部連携が無い場合でも、  
**「入力と出力の約束事」** があるならCTとして記録します。  
例: 内部API、バッチ入出力、CSVフォーマットなど。

### 2.1 契約の種類

| ID接頭辞 | 種類 | 説明 | 例 |
|----------|------|------|-----|
| CT-CLI-* | CLI | コマンドラインインターフェース | データエクスポートコマンド |
| CT-API-* | API | REST/OData/SOAP等 | 顧客一覧API |
| CT-EVT-* | Event | メッセージング/イベント | 注文作成イベント |
| CT-FILE-* | File | ファイル連携 | 日次マスタ連携 |
| CT-BATCH-* | Batch | バッチ処理 | 月次集計バッチ |
| CT-EDI-* | EDI | 電子データ交換 | 受注データ連携 |
| CT-IDOC-* | IDoc | SAP IDoc | SAP顧客マスタ連携 |
| CT-DB-* | DB | データベース契約 | DBスキーマ/テーブル定義 |

### 2.2 API契約の定義

```yaml
  contracts:
    apis_events:
      - id: "CT-API-01"
        name: "Web-EDI受注受付API"
        kind: "api"
        direction: "inbound"
        target_system: "Web-EDI Portal"
        protocol: "REST"
        data_format: "JSON"
        purpose: "発注データを受け付ける"
        versioning: "semver"
        owner_component: "CMP-01"
        audit_notes: "取引先コード/受注番号をログに記録"

      - id: "CT-API-02"
        name: "ERP受注登録API"
        kind: "api"
        direction: "inbound"
        target_system: "SAP S/4HANA"
        protocol: "OData V4"
        data_format: "JSON"
        purpose: "ERPに受注を登録する"
        versioning: "semver"
        owner_component: "CMP-01"
        audit_notes: "受注番号と取引先コードをログに記録"
```

### 2.3 CLI契約の定義

```yaml
    cli:
      - id: "CT-CLI-01"
        name: "受注再送CLI"
        purpose: "失敗した受注データを再送する"
        io_profile: "text-in/text-out + JSON"
        versioning: "semver"
        owner_component: "CMP-01"
```

### 2.4 イベント契約の定義

```yaml
      - id: "CT-EVT-01"
        name: "受注受付完了イベント"
        kind: "event"
        direction: "outbound"
        target_system: "EventHub"
        protocol: "CloudEvents"
        data_format: "JSON"
        purpose: "受注受付完了を通知基盤へ送信"
```

### 2.5 DB契約とdatabase_schema（v1.2.5新規）

DB契約（CT-DB-*）は、データベーススキーマ・テーブル定義の契約です。`database_schema.yaml` で詳細を定義します。

#### セットアップ

```bash
# テンプレートをコピー
cp sdd-templates/templates/contracts/database_schema_template.yaml \
   specs/<feature>/contracts/database_schema.yaml
```

#### plan.md での参照

```yaml
  contracts:
    databases:
      - id: "CT-DB-01"
        name: "受注スキーマ"
        kind: "database"
        target_system: "PostgreSQL 15"
        data_format: "SQL DDL"
        purpose: "受注ドメインのテーブル定義"
        owner_component: "CMP-01"
        schema_ref: "contracts/database_schema.yaml"  # ← 詳細定義への参照
```

#### database_schema.yaml の主要セクション

| セクション | 説明 |
|-----------|------|
| `meta` | スキーマID、Dialect、ステータス |
| `traceability` | spec/plan/契約への参照 |
| `data_governance` | データ分類、PII、監査、暗号化 |
| `tables` | テーブル定義（カラム、インデックス、制約） |
| `views` | ビュー定義 |
| `relationships` | テーブル間リレーション |

#### CT-DB-* とテストの関係

```
CT-DB-01 (DB契約)
    │
    └── TS-CON-03 (契約テスト)
            │
            ├── スキーマ検証（DDL実行可能か）
            ├── マイグレーション検証
            └── 制約テスト（FK、UK等）
```

> **参照**: ID規約の詳細は [08. ID規約リファレンス](appendix_a_id_conventions.md) セクション6参照

---

## 3. テスト戦略とCoverage Policy

### 3.1 テスト戦略の原則

```yaml
  test_strategy:
    principles:
      - "Contract-first"        # 契約を先に定義
      - "Integration-first"     # 統合テストを優先
      - "Trace AC-* to TS-*"    # ACからTSへのトレース
      - "E2E is smoke/regression for e2e-tagged AC only"  # E2Eは限定的
      - "Deterministic CI gate"  # CIは決定論的
```

### 3.2 Coverage Policy（3層モデル）

```yaml
    coverage_policy:
      # Layer-1: AC Coverage（必須・100%）
      acceptance_coverage_required: true
      acceptance_coverage_target_pct: 100

      # タグ付きACの強制
      tagged_acceptance_requirements:
        integration:
          enforce: true
          required_test_type: "integration"  # TS-INT-*
        e2e:
          enforce: true
          required_test_type: "e2e"          # TS-E2E-*

      # Layer-2: CT Coverage（原則100%）
      contract_coverage_required: true
      contract_coverage_target_pct: 100

      # Layer-3: Code Coverage（目標＋例外）
      code_coverage_targets:
        - scope: "LIB-*"
          line_pct: 85
          branch_pct: 75
        - scope: "CMP-*"
          line_pct: 60
          branch_pct: 50

      code_coverage_exclusions:
        - path_glob: "**/generated/**"
          reason: "Generated code"
          mitigation: "Contract tests cover behavior"

      # 計画の規律
      tests_must_be_tasked: true   # 全TSをタスク化必須
```

### 3.3 Coverage Policyの図解

```
┌─────────────────────────────────────────────────────────┐
│                  Coverage Policy 3層                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Layer-1: AC Coverage（必須）                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 全てのAC → 少なくとも1つのTS でカバー (100%)        │ │
│  │                                                     │ │
│  │ integration タグ → TS-INT-* 必須                   │ │
│  │ e2e タグ → TS-E2E-* 必須                           │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Layer-2: CT Coverage（原則必須）                        │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 全てのCT → TS-CON-* でカバー (100%)                │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Layer-3: Code Coverage（目標＋例外）                    │
│  ┌────────────────────────────────────────────────────┐ │
│  │ LIB-*: line 85% / branch 75%                       │ │
│  │ CMP-*: line 60% / branch 50%                       │ │
│  │ 例外: **/generated/** は除外                        │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 3.4 テストの定義

```yaml
    tests:
      # 契約テスト
      - id: "TS-CON-01"
        type: "contract"
        scope: "Web-EDI受注受付API契約検証"
        covers_acceptance_ids: ["AC-US-FEAT001-001-01"]
        covers_contract_ids: ["CT-API-01"]
        covers_bpmn_element_ids: ["BPMN-TASK-001"]

      # 統合テスト
      - id: "TS-INT-01"
        type: "integration"
        scope: "Web-EDI→ERP連携テスト"
        covers_acceptance_ids: ["AC-US-FEAT001-001-01", "AC-US-FEAT001-001-03"]
        covers_contract_ids: ["CT-API-01", "CT-API-02"]
        covers_bpmn_element_ids: ["BPMN-TASK-001", "BPMN-TASK-002"]

      # E2Eテスト
      - id: "TS-E2E-01"
        type: "e2e"
        scope: "Web-EDI受注受付主要フロー"
        covers_acceptance_ids: ["AC-US-FEAT001-001-02"]
        covers_contract_ids: ["CT-API-01", "CT-API-02"]
        covers_bpmn_element_ids: ["BPMN-TASK-001"]
```

### 3.5 テストIDの命名規則

| 接頭辞 | 種類 | 用途 |
|--------|------|------|
| TS-CON-* | 契約テスト | CT（契約）をカバー |
| TS-INT-* | 統合テスト | integrationタグ付きACをカバー |
| TS-E2E-* | E2Eテスト | e2eタグ付きACをカバー |
| TS-UT-* | ユニットテスト | 個別機能 |

---

## 4. Evidence Pack

### 4.1 目的

**Evidence Pack** は、ゲート判定の証跡を管理します。

### 4.2 定義

```yaml
    evidence_pack:
      required_artifacts:
        - "ci_results"      # CI実行結果
        - "test_reports"    # テストレポート
        - "sast"            # 静的解析
        - "sca"             # 依存関係スキャン
        - "secrets_scan"    # 機密情報スキャン
        - "ai_provenance"   # AIの出自記録

      storage:
        path: "sdd-templates/specs/sample_feature/implementation-details/evidence_pack.md"

      provenance:
        record_provider_surface: true        # 利用 surface / provider
        record_model_id: true                # モデル ID
        record_model_version: true           # モデルの版
        record_prompt_version: true          # プロンプトの版
        record_inputs_hash: true             # 入力のハッシュ
        record_execution_settings: true      # effort / reasoning / max_output_tokens
        record_budget_controls: true         # task budget / beta header
        record_tokenizer_notes: true         # トークナイザ再計測メモ
        record_cyber_safeguards_status: true # cyber safeguards / CVP
```

### 4.3 E2Eレポート設定

```yaml
    reporting:
      e2e:
        html_report: true
        junit_xml: true
        trace: "on-first-retry"
        screenshot: "only-on-failure"
        video: "retain-on-failure"
        artifacts_dir: "sdd-templates/specs/sample_feature/tests/reports/e2e/"
```

---

## 5. アーキテクチャ

### 5.1 コンポーネント

```yaml
  architecture:
    components:
      - id: "CMP-01"
        name: "WebEdiOrderService"
        responsibility: "受注受付・検証・ERP登録"
        boundaries: "Web-EDI Portal/ERP境界は契約越しのみ"
```

### 5.2 ライブラリ

```yaml
    libraries:
      - id: "LIB-01"
        name: "OrderValidationLib"
        responsibility: "受注データの検証・変換ロジック"
        public_interfaces: ["CT-CLI-01", "CT-API-01"]
        dependencies: []
```

---

## 6. フェーズとグループ

### 6.1 フェーズの定義

```yaml
  phases:
    - id: "Phase-1"
      name: "Contracts & Test Skeleton"
      objective: "契約を定義し、テストの骨格を作成"
      groups:
        # ← 6.2 で詳細説明

    - id: "Phase-2"
      name: "Integration & E2E"
      objective: "統合テストとE2Eテストを整備"
      groups:
        # ...
```

### 6.2 グループの定義

```yaml
      groups:
        - id: "G-01-contracts"
          name: "契約定義"
          objective: "OpenAPI/契約をレビュー可能な形にする"
          deliverables:
            - "sdd-templates/specs/sample_feature/contracts/"
          stable_refs:
            components: ["CMP-01"]
            libraries: ["LIB-01"]
            contracts: ["CT-API-01", "CT-API-02"]
            tests: ["TS-CON-01"]
            phases: ["Phase-1"]
            groups: ["G-01-contracts"]
          bpmn_refs: ["BPMN-TASK-001"]
          depends_on_groups: []

        - id: "G-02-security-ops"
          name: "セキュリティ/運用ベースライン"
          objective: "監査・SoD・運用の最低要件を定義"
          deliverables:
            - "sdd-templates/specs/sample_feature/implementation-details/ops.md"
          stable_refs:
            components: ["CMP-01"]
            libraries: ["LIB-01"]
            contracts: ["CT-API-01"]
            tests: []
            phases: ["Phase-1"]
            groups: ["G-02-security-ops"]
          depends_on_groups: ["G-01-contracts"]
```

### 6.3 グループID命名規則

```
G-<番号>-<名前>

例: G-01-contracts, G-02-security-ops, G-03-integration-tests
```

---

## 7. counts の更新

```yaml
derived_fields:
  counts:
    in_use_cases: 1          # スコープ内のUS数
    libraries: 1             # ライブラリ数
    contracts: 3             # 契約数
    tests: 4                 # テスト数
    integration_tests: 1     # 統合テスト数
    e2e_tests: 1            # E2Eテスト数
    groups: 4               # グループ数
    exception_items: 0       # 例外数
```

---

## 8. ゲート通過条件

### Plan Gate の条件

```yaml
plan_gate_check:
  rules:
    min_in_use_cases: 1      # スコープ内US最低1件
    min_libraries: 1         # ライブラリ最低1件
    min_contracts: 1         # 契約最低1件
    min_tests: 2             # テスト最低2件
    min_integration_tests: 1 # 統合テスト最低1件
    min_groups: 3            # グループ最低3件

  # 必須フラグ
  contracts_defined: true
  tests_prioritized: true
  evidence_pack_defined: true
  ai_tasks_ready: true
```

---

## 9. よくある間違いと対処法

### 間違い1: コードを書いてしまう

```yaml
# ❌ 間違い（コードを書いている）
implementation_details: |
  const registerOrder = async (payload) => {
    return await api.post(`/orders`, payload);
  };

# ✅ 正しい（判断・方針のみ）
implementation_notes: "ERP受注登録APIで登録。リトライは3回まで。"
```

### 間違い2: ACとTSの紐付け漏れ

```yaml
# ❌ 間違い（ACがTSでカバーされていない）
# spec.md: AC-US-FEAT001-001-01 (tags: ["integration"])
# plan.md: covers_acceptance_ids に含まれていない

# ✅ 正しい
tests:
  - id: "TS-INT-01"
    covers_acceptance_ids: ["AC-US-FEAT001-001-01"]  # ← 必ず含める
```

### 間違い3: Evidence Pack未定義

```yaml
# ❌ 間違い
evidence_pack: {}  # ← 空

# ✅ 正しい
evidence_pack:
  required_artifacts: ["ci_results", "sast", ...]
  storage:
    path: "specs/.../evidence_pack.md"
```

---

## チェックリスト

- [ ] 契約（CT-*）を定義した
- [ ] テスト（TS-*）を定義した
- [ ] 全ACがTSでカバーされている
- [ ] integrationタグ付きACがTS-INT-*でカバーされている
- [ ] e2eタグ付きACがTS-E2E-*でカバーされている
- [ ] 全CTがTS-CON-*でカバーされている
- [ ] Coverage Policyを設定した
- [ ] Evidence Packを定義した
- [ ] フェーズとグループを定義した
- [ ] counts を更新した

---

## 次のステップ

→ [06. タスクガイド](13_tasks_guide.md)

---

> SDD Templates Manual - 05. Plan Guide
