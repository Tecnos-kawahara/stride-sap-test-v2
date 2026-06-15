# テンプレート利用ガイド

> **sdd_template_enterprise** を使って新プロジェクトを始める方法

---

## 概要

このリポジトリは **GitHub Template Repository** として使えます。
新プロジェクトを始めるときは、テンプレートからリポジトリを作成し、
`stride new-project` コマンドで初期設定を自動化します。

```
┌──────────────────────────────┐
│  sdd_template_enterprise     │  ← テンプレートリポジトリ（このリポジトリ）
│  (GitHub Template Repository)│
└──────────────┬───────────────┘
               │  "Use this template"
               ▼
┌──────────────────────────────┐
│  my-new-project              │  ← 新プロジェクトリポジトリ
│  (from template)             │
└──────────────┬───────────────┘
               │  stride new-project
               ▼
┌──────────────────────────────┐
│  my-new-project (initialized)│  ← サンプル削除・名前置換・初期設定完了
│  - Clean specs/              │
│  - Configured CI             │
│  - Phase Gate hooks active   │
└──────────────────────────────┘
```

---

## Step 1: テンプレートからリポジトリを作成

### GitHub UI から

1. [tecnos-sdd-template-enterprise](https://github.com/tecnos-japan-cbp/tecnos-sdd-template-enterprise) を開く
2. **"Use this template"** → **"Create a new repository"**
3. リポジトリ名・組織・可視性を設定
4. **"Create repository"**

### GitHub CLI から

```bash
gh repo create my-org/my-new-project \
  --template tecnos-japan-cbp/tecnos-sdd-template-enterprise \
  --private \
  --clone
cd my-new-project
```

---

## Step 2: プロジェクト初期設定

```bash
# 基本（最小限）
sdd-templates/bin/stride new-project my_project_name

# 組織・スケール指定
sdd-templates/bin/stride new-project my_erp_addon \
  --org tecnos-japan-cbp \
  --scale enterprise

# 初期フィーチャーも一緒に作成
sdd-templates/bin/stride new-project cbp_marketplace \
  --org tecnos-japan-cbp \
  --scale standard \
  --first-feature order_import \
  --epic-prefix MKT

# 何が起きるか確認（ドライラン）
sdd-templates/bin/stride new-project my_project --dry-run
```

### `new-project` が行うこと

| Step | 内容 | 詳細 |
|------|------|------|
| 1 | サンプル削除 | `specs/sample_*`, `epics/EPIC-*`, `archive/` を削除 |
| 2 | プロジェクト名設定 | CLAUDE.md, README.md, label_feature_map.json を更新 |
| 3 | Monorepo設定 | turbo.json, tsconfig, CI workflow をスケールに応じて配置 |
| 4 | Phase Gate hooks | `.claude/settings.json` を設定 |
| 5 | 初期フィーチャー | `--first-feature` 指定時、`stride init` を実行 |
| 6 | Git commit | 初期化コミットを作成 |

---

## Step 3: 開発を始める

### フィーチャーの追加

```bash
# 推奨: Intake（簡易ヒアリング）から始める
sdd-templates/bin/stride intake my_feature

# または: フルテンプレートで初期化
sdd-templates/bin/stride init my_feature --scale standard
```

### 開発フロー

```
1. basic_design.md を記入         ← WHAT/WHY を明確に
2. stride lint → Gate 1,2 承認    ← APPROVAL.md を人間が編集
3. spec.md / plan.md を作成       ← AI が自律実行
4. stride lint → Gate 3,4 承認
5. tasks.md を作成                ← WI分解
6. stride lint → Gate 5 承認
7. 実装 → テスト → Evidence       ← AI が自律実行
8. stride lint → Final 承認
```

---

## オプション一覧

### `--scale` (Monorepo スケール)

| Scale | turbo.json | vitest.workspace | CI | 想定規模 |
|-------|-----------|-----------------|-----|---------|
| `starter` | 基本パイプライン | なし | 基本 | 1-3パッケージ |
| `standard` | リモートキャッシュ対応 | あり | 並列ビルド | 4-15パッケージ |
| `enterprise` | フルパイプライン | あり | マトリクス | 16+パッケージ |

### `--epic-prefix`

Work Item ID の接頭辞。省略するとプロジェクト名から自動生成。

```
--epic-prefix MKT  → WI-MKT-001, WI-MKT-002, ...
--epic-prefix ERP  → WI-ERP-001, WI-ERP-002, ...
```

---

## テンプレート更新の取り込み

テンプレートリポジトリが更新された場合、必要な変更を手動で取り込みます。

```bash
# テンプレートリポジトリをリモートに追加（初回のみ）
git remote add template https://github.com/tecnos-japan-cbp/tecnos-sdd-template-enterprise.git

# テンプレートの最新を取得
git fetch template main

# 差分を確認
git diff HEAD..template/main -- sdd-templates/ manual/ agent_docs/

# 必要な部分だけcherry-pickまたはマージ
# （プロジェクト固有のspecs/やepics/は競合しない構造）
git checkout template/main -- sdd-templates/VERSION
git checkout template/main -- sdd-templates/tools/stride_lint.py
# etc.
```

> **Note:** `specs/`, `epics/`, `CLAUDE.md` はプロジェクト固有なので、
> テンプレート更新では触れません。`sdd-templates/` 配下と `manual/` が主な更新対象です。

---

## ディレクトリ構造（初期化後）

```
my-new-project/
├── .claude/
│   └── settings.json          # Phase Gate hooks
├── .github/
│   ├── ISSUE_TEMPLATE/        # WI, Epic, Milestone, Risk
│   └── workflows/
│       ├── ci.yml             # スケール別CI
│       ├── stride-lint.yml    # SDD lint
│       └── stride-sync.yml   # Issues ↔ WI sync
├── CLAUDE.md                  # AI実行モデル（プロジェクト名入り）
├── CLAUDE_WORKFLOW.md         # Claude Code固有ワークフロー
├── SDD_MANIFESTO.md           # SDD原則（ツール非依存）
├── README.md                  # プロジェクト概要
├── agent_docs/                # AIエージェント用ドキュメント
├── docs/                      # 人間向けドキュメント
├── epics/                     # Epic設計・進捗管理
│   └── .gitkeep
├── manual/                    # SDDマニュアル（28章+付録）
├── memory/                    # Constitution, 組織制約
├── sdd-templates/             # テンプレート・ツール・設定
│   ├── bin/stride             # CLI
│   ├── config/                # Monorepo, Docker, K8s, Terraform...
│   ├── hooks/                 # Phase Gate hook
│   ├── policies/              # BPMN rules, Camunda dictionary
│   ├── templates/             # 全テンプレート (40+)
│   └── tools/                 # stride-lint, wi-sync, etc. (17+)
├── shared/
│   ├── decisions/             # ADR (Architecture Decision Records)
│   └── policies/              # Coverage, dependency, mode
├── specs/                     # Feature specs（ここに開発成果物が入る）
│   └── .gitkeep
└── scripts/
    └── stride-new-project.sh  # プロジェクト初期化スクリプト
```

---

## FAQ

### Q: テンプレートを使わず既存リポジトリに導入できる？

はい。`sdd-templates/` ディレクトリだけコピーする方法があります：

```bash
# 既存リポジトリに sdd-templates をサブツリーとして追加
git subtree add --prefix sdd-templates \
  https://github.com/tecnos-japan-cbp/tecnos-sdd-template-enterprise.git main \
  --squash
```

その後、必要なファイルを手動コピー：
- `CLAUDE.md`, `CLAUDE_WORKFLOW.md`, `SDD_MANIFESTO.md`
- `.github/ISSUE_TEMPLATE/`, `.github/workflows/stride-*.yml`
- `agent_docs/`, `manual/`, `memory/`

### Q: サンプルを残したまま使える？

`--keep-samples` フラグを使えば、サンプルスペック・エピックが参考として残ります。

```bash
stride new-project my_project --keep-samples
```

### Q: Cursor / Copilot でも使える？

はい。Phase Gate hooks はClaude Code以外にも対応しています：

```bash
sdd-templates/bin/stride hooks --tool cursor   # Cursor rules生成
sdd-templates/bin/stride hooks --tool copilot  # Copilot instructions生成
sdd-templates/bin/stride hooks --tool manual   # チェックリスト生成
```

### Q: GitHub Template Repository の設定方法は？

1. tecnos-sdd-template-enterprise リポジトリの Settings を開く
2. General → **☑ Template repository** にチェック
3. 保存

これで他のユーザーが **"Use this template"** ボタンからリポジトリを作成できるようになります。
