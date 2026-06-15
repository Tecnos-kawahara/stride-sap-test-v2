# STRIDE × GitHub Projects セットアップガイド

## 概要

このガイドでは、Tecnos-STRIDE の Work Item / Run / State を GitHub Projects と双方向同期するための設定手順を説明します。

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
│  Option B: Hybrid（双方向同期）                                 │
│  ・ファイルが正本だが、Projects からも更新可能                  │
│  ・競合時は新しい方を採用（または明示的に選択）                 │
└─────────────────────────────────────────────────────────────────┘
```

## 同期モード

| モード | 方向 | 用途 |
|--------|------|------|
| **Forward** (ファイル→Projects) | `push` で自動 | ファイル更新を Projects に反映 |
| **Reverse** (Projects→ファイル) | 手動 or 定期 | PM が Projects で更新した内容をファイルに反映 |

## 1. GitHub Project 作成

### 1.1 新規プロジェクト作成

1. GitHub Organization → Projects タブ → **New project**
2. **Board** テンプレートを選択
3. 名前: `STRIDE Work Items` (任意)
4. **Create project**

### 1.2 カスタムフィールド追加

以下のフィールドを追加（+ → New field）：

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

### 1.3 ボードビュー設定

1. **Group by**: Status
2. 列の順序:
   - `pending_pre_approval`
   - `in_progress`
   - `pending_walkthrough`
   - `pending_ci`
   - `pending_ops`
   - `done`

## 2. GitHub Secrets/Variables 設定

### 2.1 Personal Access Token (PAT) 作成

1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens**
2. **Generate new token**
3. 権限設定:
   - **Repository access**: 対象リポジトリ
   - **Permissions**:
     - Repository permissions → Contents: Read
     - Organization permissions → Projects: Read and write
4. **Generate token** → コピー

### 2.2 リポジトリ設定

1. リポジトリ → Settings → Secrets and variables → Actions

**Secrets:**
| Name | Value |
|------|-------|
| `STRIDE_PROJECT_TOKEN` | (上記で作成した PAT) |

**Variables:**
| Name | Value |
|------|-------|
| `STRIDE_PROJECT_NUMBER` | (Project番号: URL の `/projects/N` の N) |

## 3. 動作確認

### 3.1 ローカルテスト

```bash
# 環境変数設定
export GH_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_PROJECT_NUMBER="1"
export GITHUB_OWNER="your-org"
export GITHUB_OWNER_TYPE="organization"  # or "user"

# ドライラン（変更なし）
python scripts/sync_stride_to_projects.py --dry-run specs/my_feature/

# ローカルデータ表示のみ
python scripts/sync_stride_to_projects.py --local-only specs/my_feature/

# 実際に同期
python scripts/sync_stride_to_projects.py specs/my_feature/
```

### 3.2 GitHub Actions トリガー

**自動トリガー:**
- `specs/**/state/state.yaml` を変更して push
- `specs/**/work_items/*.md` を変更して push
- `specs/**/runs/**/*.md` を変更して push

**手動トリガー:**
1. Actions タブ → **Sync STRIDE to GitHub Projects**
2. **Run workflow**
3. Feature: `all` または `specs/my_feature/`
4. Dry run: チェックで変更なし確認

## 4. 運用フロー

### 4.1 日常の流れ（Forward Sync）

```
1. WI ファイルを作成/更新 (specs/<feature>/work_items/WI-*.md)
2. git add && git commit && git push
3. GitHub Actions が自動で Projects を更新
4. Projects ボードで進捗確認
```

### 4.2 逆方向同期（Reverse Sync）

PM が Projects で直接変更した場合、ファイルに反映する。

**手動実行:**
```bash
# ドライラン（確認のみ）
python scripts/sync_projects_to_stride.py --feature specs/my_feature/ --dry-run

# 実行（auto: 新しい方を採用）
python scripts/sync_projects_to_stride.py --feature specs/my_feature/ --prefer auto

# ファイル優先
python scripts/sync_projects_to_stride.py --feature specs/my_feature/ --prefer file

# Projects 優先
python scripts/sync_projects_to_stride.py --feature specs/my_feature/ --prefer projects
```

**GitHub Actions から実行:**
1. Actions タブ → **Sync Projects to STRIDE (Reverse)**
2. **Run workflow**
3. Feature, prefer, dry_run を指定

### 4.3 競合解決

```
┌─────────────────────────────────────────────────────────────────┐
│  競合検出: ファイルと Projects の両方が更新された場合           │
├─────────────────────────────────────────────────────────────────┤
│  --prefer auto    : mtime / updatedAt を比較し、新しい方を採用  │
│  --prefer file    : ファイルを優先（Projects 変更を破棄）       │
│  --prefer projects: Projects を優先（ファイル変更を上書き）     │
└─────────────────────────────────────────────────────────────────┘
```

**推奨フロー:**
1. 変更前に `--dry-run` で確認
2. 競合がなければ `--prefer auto` で実行
3. 競合があれば内容を確認して `--prefer file` or `--prefer projects`

### 4.2 ボードの見方

| 列 | 意味 | 次のアクション |
|----|------|---------------|
| `pending_pre_approval` | confirm/validate モードで事前承認待ち | TL が承認票を確認 |
| `in_progress` | 実装中 | Dev が Run を実行 |
| `pending_walkthrough` | ウォークスルーレビュー待ち | TL/QA がレビュー |
| `pending_ci` | CI 結果待ち | CI パス確認 |
| `pending_ops` | Ops レビュー待ち | Ops が確認 |
| `done` | 完了 | 次の WI へ |

### 4.3 フィルタ例

```
# 自分担当の WI
assignee:@me

# validate モードのみ
mode:validate

# 承認待ち
status:pending_pre_approval,pending_walkthrough,pending_ci,pending_ops
```

## 5. トラブルシューティング

### Q: 同期されない

1. **Actions ログ確認**: Actions タブ → 最新の実行 → ログ
2. **Secret 確認**: `STRIDE_PROJECT_TOKEN` が正しく設定されているか
3. **パス確認**: 変更したファイルが `specs/**/` 配下か

### Q: フィールドが更新されない

1. **フィールド名確認**: 大文字小文字が完全一致しているか
2. **オプション値確認**: Single select のオプション名が一致しているか

### Q: Permission denied

1. PAT の権限に `Projects: Read and write` があるか確認
2. Organization の場合、PAT が Organization にアクセス可能か確認

## 6. カスタマイズ

### 6.1 フィールド追加

`scripts/sync_stride_to_projects.py` の `field_updates` を編集：

```python
field_updates = {
    "WI ID": (wi_id, "text"),
    "Mode": (wi["mode"], "single_select"),
    # 追加フィールド
    "PM": (wi.get("owners", {}).get("pm", ""), "text"),
}
```

### 6.2 ステータス判定ロジック変更

`determine_status()` 関数を編集してステータス判定をカスタマイズ。

---

## 参考

- [GitHub Projects Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [GraphQL API - Projects](https://docs.github.com/en/graphql/reference/objects#projectv2)
- `agent_docs/sdd_guidelines.md` - STRIDE 運用ガイドライン
