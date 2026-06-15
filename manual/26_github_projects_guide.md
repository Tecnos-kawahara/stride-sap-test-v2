# 26. GitHub Projects 連携ガイド

> Tecnos-STRIDE の Work Item を GitHub Projects で可視化・管理する

---

## 1. 概要

### 1.1 なぜ GitHub Projects と連携するのか

Tecnos-STRIDE では、Work Item の進捗をファイル（state.yaml, work_items/*.md）で管理します。
GitHub Projects と連携することで、以下のメリットが得られます：

| メリット | 説明 |
|---------|------|
| **可視化** | かんばんボードで進捗を一目で把握 |
| **コラボレーション** | PM/TL がファイルを編集せずに状態を確認・更新 |
| **フィルタリング** | Mode、Risk、Status でフィルタ |
| **レポーティング** | Insights でバーンダウンチャート作成 |

### 1.2 同期アーキテクチャ（Option B: Hybrid）

```
┌─────────────────────────────────────────────────────────────────┐
│  [Source of Truth]           [Collaboration Layer]              │
│                                                                 │
│  specs/<feature>/            GitHub Projects                    │
│    state/state.yaml   ◄───►  ┌─────────────────────┐           │
│    work_items/*.md    ◄───►  │  WI Board View      │           │
│    runs/**/*          ────►  │  ┌────┬────┬────┐  │           │
│                              │  │TODO│PROG│DONE│  │           │
│                              │  └────┴────┴────┘  │           │
│                              └─────────────────────┘           │
│                                                                 │
│  双方向同期:                                                    │
│  ・Forward: git push → Projects 自動更新                       │
│  ・Reverse: Projects 変更 → ファイル手動同期                   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 同期モード

| モード | 方向 | トリガー | 用途 |
|--------|------|----------|------|
| **Forward** | ファイル → Projects | `git push` 時に自動 | 開発者がファイルを更新 |
| **Reverse** | Projects → ファイル | 手動 or 定期実行 | PM が Projects で更新 |

---

## 2. セットアップ

### 2.1 GitHub Project 作成

1. **Organization → Projects → New project**
2. テンプレート: **Board** を選択
3. 名前: `STRIDE Work Items` (任意)
4. **Create project**

### 2.2 カスタムフィールド追加

Project 設定でフィールドを追加します（+ → New field）：

| フィールド名 | 型 | オプション値 |
|-------------|----|----|
| **WI ID** | Text | - |
| **Mode** | Single select | `autopilot`, `confirm`, `validate` |
| **Complexity** | Single select | `low`, `medium`, `high` |
| **Status** | Single select | `pending_pre_approval`, `in_progress`, `pending_walkthrough`, `pending_ci`, `pending_ops`, `done` |
| **Risk Flags** | Text | - |
| **Walkthrough** | Single select | `Yes`, `No` |
| **Run ID** | Text | - |
| **Feature** | Text | - |

### 2.3 ボードビュー設定

1. **Group by**: Status
2. 列の順序を設定:

```
pending_pre_approval → in_progress → pending_walkthrough → pending_ci → pending_ops → done
```

3. 各列に色を設定（推奨）:
   - `pending_*`: 黄色系
   - `in_progress`: 青系
   - `done`: 緑系

### 2.4 Secrets/Variables 設定

リポジトリ → Settings → Secrets and variables → Actions:

**Secrets:**

| Name | Value | 取得方法 |
|------|-------|----------|
| `STRIDE_PROJECT_TOKEN` | Personal Access Token | [2.5 PAT 作成](#25-pat-作成)参照 |

**Variables:**

| Name | Value | 例 |
|------|-------|-----|
| `STRIDE_PROJECT_NUMBER` | Project の番号 | `1` (URL の `/projects/1` から取得) |

### 2.5 PAT（Personal Access Token）作成

1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens**
2. **Generate new token**
3. 設定:
   - Name: `STRIDE Project Sync`
   - Expiration: 90 days (or custom)
   - Repository access: 対象リポジトリを選択
4. Permissions:
   - **Repository permissions**:
     - Contents: Read
   - **Organization permissions**:
     - Projects: Read and write
5. **Generate token** → コピーして Secret に設定

---

## 3. Forward Sync（ファイル → Projects）

### 3.1 自動トリガー

以下のファイルを変更して `git push` すると、GitHub Actions が自動実行：

- `specs/**/state/state.yaml`
- `specs/**/work_items/*.md`
- `specs/**/runs/**/*.md`

### 3.2 手動実行

GitHub → Actions → **Sync STRIDE to GitHub Projects** → **Run workflow**:

| パラメータ | 説明 | 例 |
|-----------|------|-----|
| Feature | Feature ディレクトリ or `all` | `specs/my_feature/` |
| Dry run | チェックで変更なしプレビュー | ✓ |

### 3.3 ローカル実行

```bash
# 環境変数設定
export GH_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_PROJECT_NUMBER="1"
export GITHUB_OWNER="your-org"
export GITHUB_OWNER_TYPE="organization"

# ドライラン（変更なし）
python scripts/sync_stride_to_projects.py --dry-run specs/my_feature/

# ローカルデータ表示のみ（API 不要）
python scripts/sync_stride_to_projects.py --local-only specs/my_feature/

# 実際に同期
python scripts/sync_stride_to_projects.py specs/my_feature/

# 全 Feature 同期
python scripts/sync_stride_to_projects.py --all
```

---

## 4. Reverse Sync（Projects → ファイル）

### 4.1 ユースケース

- PM が Projects で WI の Status を変更した
- TL が Projects で Mode を変更した
- ボード上で直接編集した内容をファイルに反映したい

### 4.2 手動実行（GitHub Actions）

GitHub → Actions → **Sync Projects to STRIDE (Reverse)** → **Run workflow**:

| パラメータ | 説明 | 推奨値 |
|-----------|------|--------|
| Feature | 対象 Feature | `specs/my_feature/` |
| WI ID | 特定の WI のみ（空欄で全て） | `WI-ERP-FEAT-001` |
| Prefer | 競合時の優先 | `auto` |
| Dry run | プレビューモード | 最初は `✓` |

### 4.3 ローカル実行

```bash
# ドライラン（確認のみ）
python scripts/sync_projects_to_stride.py --feature specs/my_feature/ --dry-run

# 実行（auto: 新しい方を採用）
python scripts/sync_projects_to_stride.py --feature specs/my_feature/ --prefer auto

# ファイル優先（Projects の変更を無視）
python scripts/sync_projects_to_stride.py --feature specs/my_feature/ --prefer file

# Projects 優先（ファイルを上書き）
python scripts/sync_projects_to_stride.py --feature specs/my_feature/ --prefer projects

# 特定の WI のみ
python scripts/sync_projects_to_stride.py --wi-id WI-ERP-FEAT-001
```

### 4.4 競合解決

ファイルと Projects の両方が更新された場合：

```
┌─────────────────────────────────────────────────────────────────┐
│  競合検出（v1.2.4 以降）                                        │
│                                                                 │
│  比較対象:                                                      │
│  ・WI ファイル (work_items/WI-*.md) の mtime                    │
│  ・state.yaml の mtime                                          │
│  ・Projects の updatedAt                                        │
│                                                                 │
│  ※ WI ファイルと state.yaml の両方を考慮（新しい方を採用）     │
│                                                                 │
│  差異検出:                                                      │
│  ・mode の違い                                                  │
│  ・complexity の違い                                            │
│  ・status の違い（state.yaml vs Projects）                      │
├─────────────────────────────────────────────────────────────────┤
│  --prefer auto    : 新しい方を採用（推奨）                      │
│  --prefer file    : ファイルを優先（Mode/Status 含め全て保持）  │
│  --prefer projects: Projects を優先（ファイルを上書き）         │
└─────────────────────────────────────────────────────────────────┘
```

**注意**: `--prefer file` は Mode だけでなく Status も保護します。Projects で Status を変更しても、ファイル側のステータスが維持されます。

**推奨フロー:**
1. 変更前に `--dry-run` で確認
2. 競合がなければ `--prefer auto` で実行
3. 競合があれば内容を確認して判断

---

## 5. Projects の活用

### 5.1 ボードビューの見方

| 列 | 意味 | 次のアクション |
|----|------|---------------|
| `pending_pre_approval` | confirm/validate モードで事前承認待ち | TL が承認票を確認 |
| `in_progress` | 実装中 | Dev が Run を実行 |
| `pending_walkthrough` | ウォークスルーレビュー待ち | TL/QA がレビュー |
| `pending_ci` | CI 結果待ち | CI パス確認 |
| `pending_ops` | Ops レビュー待ち | Ops が確認 |
| `done` | 完了 | 次の WI へ |

### 5.2 フィルタ例

```
# 自分担当の WI
assignee:@me

# validate モードのみ
mode:validate

# 承認待ち
status:pending_pre_approval,pending_walkthrough,pending_ci,pending_ops

# 高リスク
risk-flags:authz,sod,audit_log

# 特定の Feature
feature:my_erp_addon
```

### 5.3 Insights（分析）

1. Project → Insights → New chart
2. Chart type: **Bar** or **Line**
3. X-axis: **Time** (for historical)
4. Y-axis: **Count of items**
5. Group by: **Status**

**有用なチャート:**
- バーンダウン: 残 WI 数の推移
- Status 分布: 現在の進捗状況
- Mode 分布: リスク傾向

---

## 6. ベストプラクティス

### 6.1 日常の運用フロー

```
[開発者]
1. WI ファイルを編集
2. git commit && git push
3. → 自動で Projects に反映

[PM/TL]
1. Projects ボードで進捗確認
2. 必要に応じて Projects で編集
3. Reverse Sync で変更をファイルに反映
```

### 6.2 同期のタイミング

| シナリオ | 推奨アクション |
|----------|---------------|
| 日常の開発 | Forward Sync のみ（自動） |
| PM がボードを編集した | Reverse Sync（手動） |
| 週次レビュー前 | Forward + Reverse で同期確認 |
| リリース前 | 両方向同期して整合性確認 |

### 6.3 注意事項

- **ファイルが正本**: 監査証跡はファイルに残る
- **Projects は可視化層**: 編集は可能だが、最終的にはファイルに反映
- **競合は早めに解決**: 長期間放置すると解決が困難に

---

## 7. トラブルシューティング

### 7.1 同期されない

**確認項目:**
1. Actions ログを確認（Actions タブ → 最新の実行）
2. `STRIDE_PROJECT_TOKEN` が正しく設定されているか
3. 変更したファイルが `specs/**/` 配下か
4. PAT の有効期限が切れていないか

### 7.2 フィールドが更新されない

**確認項目:**
1. フィールド名が完全一致しているか（大文字小文字を含む）
2. Single select のオプション名が一致しているか
3. フィールドが非表示になっていないか

### 7.3 Permission denied

**確認項目:**
1. PAT に `Projects: Read and write` 権限があるか
2. Organization の場合、PAT が Organization にアクセス可能か
3. Project が PAT の Repository access に含まれているか

### 7.4 競合が頻発する

**対策:**
1. チームで編集ルールを決める（ファイル優先 or Projects 優先）
2. 編集前に最新状態を確認
3. 同期頻度を上げる（定期実行を有効化）

---

## 8. 高度な設定

### 8.1 定期同期の有効化

`.github/workflows/stride-reverse-sync.yml` を編集:

```yaml
on:
  # 30分ごとに自動同期
  schedule:
    - cron: '*/30 * * * *'
```

### 8.2 Webhook による即座同期

Project の変更を即座に反映したい場合は、GitHub App + Webhook を設定します。
（詳細は GitHub Docs を参照）

### 8.3 カスタムフィールドの追加

`scripts/sync_stride_to_projects.py` の `field_updates` を編集:

```python
field_updates = {
    "WI ID": (wi_id, "text"),
    "Mode": (wi["mode"], "single_select"),
    # 追加フィールド
    "PM": (wi.get("owners", {}).get("pm", ""), "text"),
    "Due Date": (wi.get("due_date", ""), "text"),
}
```

---

## 9. Per-Project Project V2 自動作成 (v5.3.1)

STRIDE テンプレートをクローンして新規プロジェクトを立ち上げるたびに、専用の
GitHub Project V2 ボードを自動作成できる（複数 STRIDE プロジェクトが同じ
Project に混在する事故を防止）。

### 9.1 新規プロジェクト初期化時の自動作成

```bash
stride new-project my_erp --org my-org \
  --github-project "my_erp SDD Board"    # 既定: "<project_title> SDD Board"
# または：--no-github-project で明示スキップ
```

前提:
- `gh auth status` が成功（未認証 → graceful skip、警告のみで継続）
- 未認証でもテンプレ本体のセットアップ（ラベル / マイルストーン等）は従来通り動作

実行結果:
- GitHub Project V2 が `--owner` 配下に作成（既存の同名 Project があれば再利用）
- `memory/github_project.yaml` に binding が永続化される（SSoT）

```yaml
# memory/github_project.yaml
owner: "my-org"
project_number: 7
project_id: "PVT_kwDO..."
project_title: "my_erp SDD Board"
url: "https://github.com/orgs/my-org/projects/7"
```

### 9.2 手動管理コマンド

既存プロジェクトに後付けで binding する / 別 Project に切替える場合:

```bash
stride project create "My ERP SDD Board" --owner my-org   # 作成 + memory/github_project.yaml 永続化
stride project list --owner my-org                         # owner の Project 一覧
stride project use 7 --owner my-org                         # 既存 #7 に binding
stride project status                                       # 現在の binding 確認
```

### 9.3 解決順位（precedence）

`stride_wi_sync` / `sync_projects_to_stride` / GitHub Actions ワークフローが
Project 番号を解決する際の優先順:

1. 環境変数 `GITHUB_PROJECT_NUMBER`（一時的な上書き）
2. `memory/github_project.yaml` の `project_number`（プロジェクト SSoT）
3. なし → env 未設定時はエラー、または env 経由のレガシー運用

### 9.4 複数 STRIDE プロジェクトの運用図

```
Template repo (sdd_template_enterprise)
  ↓ clone
Project alpha-erp                 Project beta-crm
  memory/github_project.yaml        memory/github_project.yaml
    project_number: 5                 project_number: 6
  ↓ WI Issue 起票                    ↓ WI Issue 起票
GitHub Project V2 #5              GitHub Project V2 #6
  (alpha-erp 専用)                  (beta-crm 専用)
```

→ 各プロジェクトが独立したかんばん / サイクル / Insights を持つ。

### 9.5 gh CLI 未認証時の扱い

`stride project create` / `stride project use` は `gh auth status` で認証確認し、
未認証なら **graceful skip (exit 0)**。SDD 本体フローに影響なし。後で
`gh auth login` を実行してから再度 `stride project create` を走らせれば OK。

---

## 関連ドキュメント

- [Tecnos-STRIDE メソッド](27_erp_addon_playbook.md)
- [RACI+ (AI時代の責務分担)](16_raci_plus.md)
- [stride-lint ガイド](appendix_b_stride_lint.md)
- [Linear Integration](37_linear_integration_guide.md) - Linear 側の対応機能
- [docs/stride_github_projects_setup.md](../docs/stride_github_projects_setup.md) - 詳細セットアップガイド
