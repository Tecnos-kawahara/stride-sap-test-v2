# Appendix A. ID規約リファレンス

---

## このガイドについて

SDDテンプレートで使用する全てのID規約をまとめたリファレンスです。

---

## 1. ID規約の正本

ID規約の正本は `memory/constitution.md` の `# 3. ID Conventions` セクションです。
他のドキュメントに同様の記載があっても、それは参照情報であり、規約本体は常に constitution から読みます。

### 現行の YAML 設定ファイル

ID規約は `sdd-templates/config/id_conventions.yaml` にも同期されています：

```yaml
# sdd-templates/config/id_conventions.yaml
id_conventions:
  feature_id:
    pattern: "^FEAT-(?:[A-Z]{2,4}-)?[A-Z0-9]{3,}$"
    example: "FEAT-ORD-001"
  use_case_id:
    pattern: "^US-FEAT[A-Z0-9]{3,}-[0-9]{3}$"
    example: "US-FEATORD001-001"
  acceptance_id:
    pattern: "^AC-US-FEAT[A-Z0-9]{3,}-[0-9]{3}-[0-9]{2}$"
    example: "AC-US-FEATORD001-001-01"
  # ... 他のID規約
```

**用途**:
- プログラムからのID規約読み込み
- カスタムID規約の定義
- CIでのID検証自動化

### 初心者向けのコツ

- **迷ったら既存IDをコピーして末尾だけ増やす**（例: `...-01` → `...-02`）  
- **一度使ったIDは再利用しない**（削除しても欠番のまま）  
- **大小文字とハイフン位置**は規約どおりに固定する

---

## 2. 機能・設計関連

| カテゴリ | パターン | 例 | 説明 |
|----------|----------|-----|------|
| Feature ID | `FEAT-(?:[A-Z]{2,4}-)?[A-Z0-9]{3,}` | FEAT-001, FEAT-ORD-001 | 機能ID（team prefix は任意） |
| Requirement ID | `RQ-[0-9]{3}` | RQ-001, RQ-002 | 要件ID |
| Decision ID | `DR-[0-9]{3}` | DR-001, DR-002 | 意思決定ID |
| Flow ID | `FLOW-[0-9]{3}` | FLOW-001 | 統合フローID |

> **注**: Feature ID は最小3文字必要です。`stride init ab` のような短すぎる名前はエラーになります。

---

## 3. ユースケース・受入条件

| カテゴリ | パターン | 例 | 説明 |
|----------|----------|-----|------|
| Use Case ID | `US-FEAT[A-Z0-9]{3,}-[0-9]{3}` | US-FEATORD001-001 | ユースケースID |
| Acceptance ID | `AC-US-FEAT[A-Z0-9]{3,}-[0-9]{3}-[0-9]{2}` | AC-US-FEATORD001-001-01 | 受入条件ID |
| Question ID | `Q-[0-9]{3}` | Q-001 | 質問ID |
| Assumption ID | `A-[0-9]{3}` | A-001 | 前提条件ID |

### 命名規則の図解

```
機能ID: FEAT-ORD-001
           │
           ▼
ユースケースID: US-FEATORD001-001
                        │        │
                        │        └── 連番（001, 002, ...）
                        └── 機能IDの英数字部（FEATORD001）
                                   │
                                   ▼
受入条件ID: AC-US-FEATORD001-001-01
                   │           │    │
                   │           │    └── 連番（01, 02, ...）
                   │           └── ユースケース連番（001）
                   └── ユースケースID参照
```

---

## 4. アーキテクチャ・ライブラリ

| カテゴリ | パターン | 例 | 説明 |
|----------|----------|-----|------|
| Component ID | `CMP-[0-9]{2}` | CMP-01, CMP-02 | コンポーネントID |
| Library ID | `LIB-[0-9]{2}` | LIB-01, LIB-02 | ライブラリID |

---

## 5. 契約（Contract）

| カテゴリ | パターン | 例 | 説明 |
|----------|----------|-----|------|
| CLI Contract | `CT-CLI-[0-9]{2}` | CT-CLI-01 | CLIインターフェース契約 |
| API Contract | `CT-API-[0-9]{2}` | CT-API-01 | REST/OData/SOAP等の契約 |
| Event Contract | `CT-EVT-[0-9]{2}` | CT-EVT-01 | イベント/メッセージング契約 |
| File Contract | `CT-FILE-[0-9]{2}` | CT-FILE-01 | ファイル連携契約 |
| Batch Contract | `CT-BATCH-[0-9]{2}` | CT-BATCH-01 | バッチ処理契約 |
| EDI Contract | `CT-EDI-[0-9]{2}` | CT-EDI-01 | EDI契約 |
| IDoc Contract | `CT-IDOC-[0-9]{2}` | CT-IDOC-01 | SAP IDoc契約 |
| DB Contract | `CT-DB-[0-9]{2}` | CT-DB-01 | データベース契約 |

### 契約種別の選び方

| シナリオ | 契約種別 |
|----------|----------|
| コマンドラインツール | CT-CLI-* |
| REST API | CT-API-* |
| GraphQL | CT-API-* |
| gRPC | CT-API-* |
| Kafka/EventHub | CT-EVT-* |
| SFTP連携 | CT-FILE-* |
| 日次バッチ | CT-BATCH-* |
| EDI/B2B | CT-EDI-* |
| SAP連携 | CT-IDOC-* |
| DBスキーマ/テーブル契約 | CT-DB-* |

---

## 6. データベーススキーマ

| カテゴリ | パターン | 例 | 説明 |
|----------|----------|-----|------|
| Database Schema ID | `DB-FEAT-[A-Z0-9]{3,}` | DB-FEAT-ORD001 | DBスキーマID |

### database_schema.yaml の構造（v1.2.5）

```yaml
database_schema:
  meta:
    schema_id: "DB-FEAT-ORD001"  # ← このID
    feature_id: "FEAT-ORD-001"
    dialect: "postgresql"        # postgresql | mysql | oracle | sqlserver | sqlite
    status: "draft"

  traceability:
    spec_ref: "specs/<feature>/spec.md"
    related_contracts: ["CT-API-01", "CT-DB-01"]
    related_use_cases: ["US-FEATORD001-001"]
    related_acceptance_criteria: ["AC-US-FEATORD001-001-01"]

  data_governance:
    data_classification: "Internal"  # Public | Internal | Confidential | Regulated
    contains_pii: false
    audit_log_required: true
    retention_policy: "7 years"

  tables:
    - name: "table_name"
      domain_object: "Order"    # ドメインオブジェクト名
      sor: "ERP"                # System of Record
      columns: [...]
      indexes: [...]
      constraints: [...]
```

### ID の連鎖

```
FEAT-ORD-001 (機能)
    │
    ├── DB-FEAT-ORD001 (スキーマ)
    │       │
    │       └── tables[].name (テーブル名)
    │
    └── CT-DB-01 (DB契約)
            │
            └── TS-CON-03 (契約テスト)
```

### Enterprise 拡張で追加される ID

| カテゴリ | パターン | 例 | 説明 |
|----------|----------|-----|------|
| Epic ID | `EPIC-[A-Z]{3,}` | EPIC-ORDER | Epic 単位の管理ID |
| Team ID | `TEAM-[A-Z]{1,3}` | TEAM-ORD, TEAM-SLS | 所有チームID |
| Epic Milestone ID | `EM-[0-9]{2}` | EM-01 | Epic マイルストーン |
| Dependency ID | `DEP-[0-9]{3}` | DEP-001 | チーム間依存ID |
| Shared Contract ID | `SC-(API\|EVT\|FILE)-[A-Z0-9]{3,}` | SC-API-ORDER | 共有契約ID |
| CCP ID | `CCP-[0-9]{3}` | CCP-001 | Contract Change Proposal |

> Enterprise 運用では `feature_id` / `epic_id` / `team_id` の整合性が `stride lint specs/<feature>/ --enterprise` または `stride lint --all --enterprise` と `stride epic validate` で検証されます。

### 配置場所

| ファイル | パス |
|----------|------|
| テンプレート | `sdd-templates/templates/contracts/database_schema_template.yaml` |
| 配置先 | `specs/<feature>/contracts/database_schema.yaml` |

---

## 7. テスト

| カテゴリ | パターン | 例 | 説明 |
|----------|----------|-----|------|
| Contract Test | `TS-CON-[0-9]{2}` | TS-CON-01 | 契約テスト |
| Integration Test | `TS-INT-[0-9]{2}` | TS-INT-01 | 統合テスト |
| E2E Test | `TS-E2E-[0-9]{2}` | TS-E2E-01 | E2Eテスト |
| Unit Test | `TS-UT-[0-9]{2}` | TS-UT-01 | ユニットテスト |

### テスト種別とACタグの対応

| ACタグ | 必要なテスト種別 |
|--------|-----------------|
| `integration` | TS-INT-* |
| `e2e` | TS-E2E-* |
| (その他) | TS-CON-* または TS-UT-* |

---

## 8. 計画・タスク

| カテゴリ | パターン | 例 | 説明 |
|----------|----------|-----|------|
| Phase ID | `Phase-[0-9]+` | Phase-1, Phase-2 | フェーズID |
| Group ID | `G-[0-9]{2}-[a-z0-9-]+` | G-01-contracts | グループID |
| Task ID | `T-[A-Z0-9]{2,}-[0-9]{3}` | T-G01-001 | タスクID |
| Milestone ID | `M-[0-9]{2}` | M-01, M-02 | マイルストーンID |
| Risk ID | `R-[0-9]{3}` | R-001 | リスクID |

### タスクID の構成

```
T-G01-001
│  │   │
│  │   └── 連番（001, 002, ...）
│  └── グループ参照（G01 = G-01-*）
└── Task を示す接頭辞
```

---

## 9. BPMN要素

| カテゴリ | パターン | 例 | 説明 |
|----------|----------|-----|------|
| Process ID | `BPMN-PROC-[A-Z0-9]{3,}` | BPMN-PROC-001 | プロセスID |
| Task | `BPMN-TASK-[0-9]{3}` | BPMN-TASK-001 | タスクID |
| Gateway | `BPMN-GW-[0-9]{3}` | BPMN-GW-001 | ゲートウェイID |
| Event | `BPMN-EVT-[0-9]{3}` | BPMN-EVT-001 | イベントID |
| Flow | `BPMN-FLOW-[0-9]{3}` | BPMN-FLOW-001 | フローID |

---

## 10. TEIM テストプロセス

| ID | テストプロセス |
|-----|---------------|
| T04 | 機能連携 |
| T05 | アドオン顧客確認 |
| T06 | 権限 |
| T07 | ジョブ |
| T08 | IF |
| T09 | 機能単位性能 |
| T10 | 機能単位障害 |
| T11 | 結合 |
| T12 | 業務場面想定性能 |
| T13 | 総合（業務/非機能） |
| T14 | 業務運用 |
| T15 | システム運用 |

**注意**: Phase番号（4.*, 5.*）と混同しないように Txx 形式を使用

---

## 11. よくある間違い

### 間違い1: 大文字/小文字の誤り

```yaml
# ❌ 間違い
feature_id: "feat-001"   # 小文字

# ✅ 正しい
feature_id: "FEAT-001"   # 大文字
```

### 間違い2: 連番の桁数不足

```yaml
# ❌ 間違い
use_case_id: "US-FEAT001-1"   # 1桁

# ✅ 正しい
use_case_id: "US-FEAT001-001" # 3桁
```

### 間違い3: ハイフンの欠落

```yaml
# ❌ 間違い
acceptance_id: "ACUSFEAT001001-01"  # ハイフンなし

# ✅ 正しい
acceptance_id: "AC-US-FEAT001-001-01"  # 正しいハイフン位置
```

---

## 12. ID生成のベストプラクティス

1. **コピペを推奨** - 手入力でのタイポを防ぐ
2. **連番は自動生成** - 可能であればスクリプトで採番
3. **正規表現で検証** - stride-lint で自動チェック
4. **一意性を保証** - 同じIDを複数箇所で使わない

---

## 13. 検証コマンド

```bash
# stride-lint でID規約を検証
sdd-templates/bin/stride lint specs/my_feature/

# 特定のエラーコードを確認
# ID_REGEX_MISMATCH - ID形式が不正
# DUPLICATE_ID - IDが重複
```

---

## クイックリファレンス

```
FEAT-XXX / FEAT-ORD-001  機能
RQ-NNN                要件
DR-NNN                意思決定
FLOW-NNN              フロー

US-FEATXXX-NNN        ユースケース
AC-US-FEATXXX-NNN-NN  受入条件

CMP-NN                コンポーネント
LIB-NN                ライブラリ

CT-API-NN             API契約
CT-CLI-NN             CLI契約
CT-EVT-NN             イベント契約
CT-FILE-NN            ファイル契約
CT-BATCH-NN           バッチ契約
CT-EDI-NN             EDI契約
CT-IDOC-NN            IDoc契約

TS-CON-NN             契約テスト
TS-INT-NN             統合テスト
TS-E2E-NN             E2Eテスト
TS-UT-NN              ユニットテスト

Phase-N               フェーズ
G-NN-name             グループ
T-GNN-NNN             タスク
M-NN                  マイルストーン

BPMN-PROC-XXX         BPMNプロセス
BPMN-TASK-NNN         BPMNタスク
BPMN-GW-NNN           BPMNゲートウェイ
BPMN-EVT-NNN          BPMNイベント
BPMN-FLOW-NNN         BPMNフロー

EPIC-XXX              Epic
TEAM-XXX              Team
EM-NN                 Epicマイルストーン
DEP-NNN               チーム間依存
SC-API-XXX            共有契約
CCP-NNN               契約変更提案
```

---

> SDD Templates Manual - Appendix A. ID Conventions Reference
