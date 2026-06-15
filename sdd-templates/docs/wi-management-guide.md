# Work Item 管理ガイド（Tecnos-STRIDE ハイブリッド方式）

**Version:** 1.0.0  
**Date:** 2026-02-17  
**Status:** Active

---

## 概要

Tecnos-STRIDE における Work Item (WI) は **GitHub Issues を Single Source of Truth（正）** とし、
**Gate 審査時にファイルスナップショット**を生成するハイブリッド方式で管理する。

```
┌──────────────────────────────────────────────────────┐
│                    Day-to-Day                         │
│                                                      │
│  GitHub Issues (label: work-item)                    │
│    ├── Issue Template (YAML metadata 必須)           │
│    ├── GitHub Projects Board で進捗可視化            │
│    └── PR に Issue 番号紐付け (#123)                 │
│                                                      │
├──────────────────────────────────────────────────────┤
│                    Gate 審査時                         │
│                                                      │
│  stride wi sync                                      │
│    ├── Issues → specs/*/work_items/WI-*.md 生成      │
│    ├── stride-lint (erp_addon_exec_tracking) 検証    │
│    └── APPROVAL.md 更新 → Gate 通過                  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## なぜハイブリッドか

| 方式 | メリット | デメリット |
|------|---------|----------|
| ファイルのみ | lint で厳密検証可能 | 開発者の日常ワークフローに合わない |
| Issues のみ | 開発者に自然、Board 連携 | lint/Gate 検証が困難 |
| **ハイブリッド** | **両方の長所** | 同期の仕組みが必要（→ stride wi sync で解決） |

## WI の作成

### 方法 1: GitHub Issue Form（推奨）

GitHub の "New Issue" → "SDD Work Item" テンプレートを選択。
UI フォームでメタデータを入力する。

**ファイル:** `.github/ISSUE_TEMPLATE/work-item.yml`

### 方法 2: Markdown テンプレート

Issue 本文に YAML メタデータブロックを含める。

**ファイル:** `sdd-templates/templates/github-projects/ISSUE_TEMPLATE/work-item.md`

```markdown
```yaml
# === SDD Metadata (required) ===
wi_id: "WI-ERP-MAU-001"
feature_id: "master-admin-ui"
complexity: "medium"
mode: "autopilot"
priority: "P2-Medium"
risk_flags: ["ui_only"]
spec_refs: ["basic_design.md", "spec.md"]
contract_refs:
  acceptance_ids: ["AC-MAU-001"]
  contract_ids: ["CT-MAU-API-001"]
test_refs: ["TS-INT-MAU-001"]
owners:
  pm: "@okazaki"
  tech_lead: "@okazaki"
  dev: "@ai-agent"
  qa: "@ai-agent"
```　
```

### 必須メタデータ

| フィールド | 説明 | 値 |
|-----------|------|-----|
| `wi_id` | WI の一意識別子 | `WI-ERP-XXX-NNN` or `SU-N` |
| `feature_id` | specs/ 配下のディレクトリ名 | `master-admin-ui` 等 |
| `complexity` | 複雑度 | `low` / `medium` / `high` |
| `mode` | 実行モード | `autopilot` / `confirm` / `validate` |
| `priority` | 優先度 | `P0-Critical` ～ `P3-Low` |
| `risk_flags` | リスクフラグ | 配列（下記参照） |

### Risk Flags 一覧

| フラグ | 推奨モード | 説明 |
|--------|-----------|------|
| `authz` | validate | 認可ロジックの変更 |
| `audit_log` | validate | 監査ログへの影響 |
| `db_schema` | validate | DBスキーマ変更 |
| `data_migration` | validate | データ移行を伴う |
| `cross_module` | validate | モジュール横断 |
| `new_api` | confirm | API追加・契約変更 |
| `performance_sensitive` | confirm | パフォーマンス影響 |
| `ui_only` | autopilot | UI変更のみ（低リスク） |

## WI の進捗管理

### GitHub Projects Board

推奨カラム構成:

| カラム | 説明 |
|--------|------|
| `Backlog` | 作成済み、未着手 |
| `Ready` | メタデータ完備、着手可能 |
| `In Progress` | 実装中 |
| `In Review` | PR レビュー中 |
| `Done` | マージ済み、AC 達成 |

### ラベル体系

| ラベル | 用途 |
|--------|------|
| `work-item` | WI 識別（stride wi sync のフィルタ） |
| `status:pending` | 未着手 |
| `status:in-progress` | 実装中 |
| `status:done` | 完了 |
| `priority:P0` ～ `priority:P3` | 優先度 |
| `risk:authz`, `risk:db_schema` 等 | リスク種別 |
| `mode:autopilot` / `mode:confirm` / `mode:validate` | 実行モード |

### PR との紐付け

PR の本文またはコミットメッセージに Issue 番号を含める:

```
Fix #42: WI-ERP-MAU-001 Knowledge Manager upload fix
```

## Gate 審査フロー

### Step 1: stride wi sync 実行

```bash
# リポジトリルートで実行
cd /path/to/cbp-core

# 全 WI を同期
python3 sdd-templates/tools/stride_wi_sync.py

# 特定 feature のみ
python3 sdd-templates/tools/stride_wi_sync.py --feature master-admin-ui

# プレビュー（ファイル書き込みなし）
python3 sdd-templates/tools/stride_wi_sync.py --feature master-admin-ui --dry-run

# open な Issue のみ
python3 sdd-templates/tools/stride_wi_sync.py --status open
```

### Step 2: stride-lint 検証

```bash
# erp_addon_exec_tracking.py で検証
python3 sdd-templates/tools/erp_addon_exec_tracking.py specs/master-admin-ui/
```

stride wi sync で生成された WI ファイルは `github` ブロック付きで生成されるため、
バリデーターは GitHub-synced WI として認識し、以下を検証する:

- **必須フィールド:** wi_id, title, mode, risk_flags, complexity
- **必須セクション:** Intent, Scope（Spec Links の代替）
- **Risk Flags / Acceptance Criteria:** 存在チェック（警告レベル）
- **モードポリシー:** risk_flags に対して mode が適切か

### Step 3: Gate 承認

```bash
# コミット
git add specs/*/work_items/
git commit -m "Gate: stride wi sync snapshot for Gate N review"
```

APPROVAL.md を更新して Gate を通過。

## ファイル構成

```
cbp-core/
├── .github/
│   └── ISSUE_TEMPLATE/
│       └── work-item.yml          # GitHub Issue Form（UI入力用）
├── sdd-templates/
│   ├── templates/
│   │   ├── work_item_template.md           # ファイル直接作成用テンプレート
│   │   ├── work_item_approval_template.md  # 承認記録テンプレート
│   │   └── github-projects/
│   │       └── ISSUE_TEMPLATE/
│   │           └── work-item.md            # Issue Markdown テンプレート
│   ├── tools/
│   │   ├── stride_wi_sync.py               # Issues → ファイル同期 CLI
│   │   └── erp_addon_exec_tracking.py      # WI バリデーター
│   └── docs/
│       └── wi-management-guide.md          # このドキュメント
└── specs/
    └── <feature>/
        └── work_items/                     # stride wi sync が生成（Gate 時）
            ├── WI-ERP-XXX-001.md
            ├── WI-ERP-XXX-001.approval.md
            └── ...
```

## FAQ

### Q: 既存のファイルベース WI はどうなる？

`work_item_template.md` と `work_item_approval_template.md` は残します。
ファイルベースで WI を管理したいプロジェクトは引き続き利用可能です。
`erp_addon_exec_tracking.py` は両方式に対応しています。

### Q: stride wi sync はいつ実行すべき？

**Gate 審査の前に1回**。日常的に実行する必要はありません。
Gate 前に最新の Issue 状態をスナップショットとして固めるのが目的です。

### Q: Issue にメタデータを書き忘れたら？

stride wi sync はメタデータが不足している Issue にデフォルト値を割り当てますが、
lint 検証で警告が出ます。Gate 前に Issue を更新してください。

### Q: feature_id はどうやって決める？

`specs/` ディレクトリの直下のフォルダ名と一致させます。
例: `specs/sample_erp_addon/` → `feature_id: "sample_erp_addon"`

### Q: label_feature_map はどうカスタマイズする？

`sdd-templates/config/label_feature_map.json` にマッピングを定義できます:

```json
{
  "FEAT-OMS": "erp_order_management",
  "FEAT-INV": "erp_inventory",
  "FEAT-FIN": "erp_finance"
}
```

未定義の場合は `specs/` ディレクトリ名から自動推論します。
