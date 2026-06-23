# STRIDE Symphony + GitHub Projects V2 セットアップ手順書

**対象**: Tecnos-STRIDE テンプレートを使用する新規プロジェクトリポジトリ
**最終更新**: 2026-06-18
**ステータス**: 検証済み（stride-sap-test-v2 にて E2E 検証完了）

---

## 全体フロー

```
Step 0: 前提条件の確認
Step 1: テンプレート入手 + GitHub リポジトリ作成 + push
Step 2: stride-new-project.sh でローカル初期化
Step 3: GitHub PAT の作成
Step 4: GitHub シークレット・変数の設定
Step 5: GitHub ラベルの作成
Step 6: GitHub Projects V2 ボード + カスタムフィールドの作成
Step 7: 動作検証
```

---

## Step 0: 前提条件

以下がインストール・設定済みであること:

- [ ] `git` CLI（`git --version` で確認）
- [ ] `gh` CLI（`gh --version` で確認、`gh auth status` でログイン済み）
- [ ] Python 3.11+（`python --version` で確認）
- [ ] テンプレートソースの入手（以下のいずれか）
  - 配布用リポジトリへのアクセス権がある場合: clone
  - アクセス権がない場合: 管理者から特定バージョンの zip を受領

---

## Step 1: テンプレート入手 + GitHub リポジトリ作成 + push

### 1-1: テンプレートソースの準備

テンプレートの入手方法に応じて、ローカルにファイルがある状態にする。

**パターン A: 配布用リポジトリから clone する場合**

```bash
git clone <配布用リポジトリURL>
cd <リポジトリ名>/tecnos_stride_sap
```

**パターン B: zip ファイルから展開する場合**

```bash
# 管理者から受領した zip を展開
unzip tecnos_stride_sap_vX.X.X.zip -d tecnos_stride_sap
cd tecnos_stride_sap
```

いずれの場合も、`tecnos_stride_sap/` ディレクトリ配下に `SYMPHONY.md`, `symphony/`, `scripts/`, `.github/` 等が存在する状態になる。

### 1-2: GitHub にリポジトリを作成

```bash
gh repo create <owner>/<repo-name> --private --description "<プロジェクト説明>"
```

### 1-3: git init + push

**パターン A（clone した場合）**: `tecnos_stride_sap/` は親リポジトリの一部なので、独立した git リポジトリとして初期化し直す必要がある。

```bash
cd tecnos_stride_sap

# 親リポジトリの .git を参照しない新しいディレクトリにコピー
TARGET_DIR="../<repo-name>"
mkdir -p "$TARGET_DIR"
cp -r ./* "$TARGET_DIR/"
cp -r ./.[!.]* "$TARGET_DIR/" 2>/dev/null || true
rm -rf "$TARGET_DIR/.git"       # 親リポジトリの .git 参照を除去
rm -rf "$TARGET_DIR/.symphony"  # 実行時生成物を除去（あれば）

cd "$TARGET_DIR"
git init
git branch -m master main    # デフォルトブランチを main にする
git remote add origin https://github.com/<owner>/<repo-name>.git
git add -A
git commit -m "chore: initial template import from tecnos_stride_sap"
git push -u origin main
```

**パターン B（zip 展開の場合）**: zip には `.git` が含まれないので、そのまま初期化できる。

```bash
cd tecnos_stride_sap
git init
git branch -m master main
git remote add origin https://github.com/<owner>/<repo-name>.git
git add -A
git commit -m "chore: initial template import from tecnos_stride_sap"
git push -u origin main
```

> **注意**: `git init` のデフォルトブランチが `master` になる環境があります。
> `git branch -m master main` を忘れると `git push -u origin main` が失敗します。
> 恒久対策: `git config --global init.defaultBranch main`

---

## Step 2: stride-new-project.sh でローカル初期化

```bash
bash scripts/stride-new-project.sh <project_name> \
  --no-github-project \
  --no-linear-project \
  --skip-git
```

> `--no-github-project`: Projects ボードは Step 6 で手動作成するためスキップ
> `--no-linear-project`: Linear 未使用の場合スキップ
> `--skip-git`: コミットは手動で行うためスキップ

### 実行結果の確認

- Step 1/7: サンプルファイル削除 → `Done`
- Step 2/7: プロジェクト名更新 → `Done`
  - `SYMPHONY.md tracker.repo → ...` と表示されるが、`repo: "auto"` の場合は**実際には変更されない**（正常動作）
- Step 4/7: Phase Gate hooks → `Done`

### SYMPHONY.md の確認

```bash
python -m symphony validate
```

出力に `tracker.repo: <owner>/<repo-name>` と正しいリポジトリ名が表示されること。

### コミット + push

```bash
git add -A
git commit -m "chore: initialize <project_name> via stride-new-project.sh"
git push
```

---

## Step 3: GitHub PAT の作成

### 必要なスコープ

| スコープ | 用途 |
|---------|------|
| `repo` | Issue・PR の読み書き |
| `project` | Projects V2 API アクセス |
| `read:org` | オーナータイプ（User/Organization）の判定 |

> **重要**: `read:org` がないと `gh project item-add` で `unknown owner type` エラーが発生します。

### 作成手順

1. https://github.com/settings/tokens/new にアクセス
2. **Note**: `STRIDE Project Token - <リポジトリ名>`
3. **Expiration**: 任意（推奨: 90日）
4. **Scopes**: `repo`, `project`, `read:org` にチェック
5. **Generate token** → トークンをメモ

### 組織リポジトリの場合

組織（Organization）のリポジトリでは PAT に追加承認が必要:

1. https://github.com/settings/tokens で PAT の **Configure SSO** をクリック
2. 対象組織の **Authorize** をクリック
3. 組織管理者に PAT の承認を依頼（必要な場合）

---

## Step 4: GitHub シークレット・変数の設定

```bash
# シークレット（Step 3 で作成した PAT）
gh secret set STRIDE_PROJECT_TOKEN --repo <owner>/<repo> --body "<PAT>"

# 変数（Step 6 で作成するプロジェクト番号 — Step 6 を先に実行してから設定）
gh variable set STRIDE_PROJECT_NUMBER --repo <owner>/<repo> --body "<番号>"
```

> **注意**: `STRIDE_PROJECT_NUMBER` は Step 6 でプロジェクトを作成してから設定してください。
> ここでは先にシークレットだけ設定し、変数は Step 6 の後で設定します。

### 検証

```bash
gh secret list --repo <owner>/<repo>
gh variable list --repo <owner>/<repo>
```

---

## Step 5: GitHub ラベルの作成

### 方法 A: 既存リポジトリからコピー（推奨）

ラベルが設定済みのリポジトリがある場合、一括コピーが最も確実です。

```bash
SOURCE_REPO="<source-owner>/<source-repo>"
TARGET_REPO="<owner>/<repo>"

gh label list --repo "$SOURCE_REPO" --limit 100 --json name,color,description | python -c "
import json, sys, subprocess
labels = json.load(sys.stdin)
standard = {'bug','documentation','duplicate','enhancement','good first issue',
            'help wanted','invalid','question','wontfix'}
custom = [l for l in labels if l['name'] not in standard]
repo = '$TARGET_REPO'
ok = 0
for l in custom:
    cmd = ['gh', 'label', 'create', l['name'], '--repo', repo, '--color', l['color']]
    if l.get('description'):
        cmd += ['--description', l['description']]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0: ok += 1
    else: print(f'FAIL: {l[\"name\"]} - {r.stderr.strip()}')
print(f'Created {ok}/{len(custom)} labels')
"
```

### 方法 B: 最小セットを手動作成

Symphony + Projects 連携に最低限必要なラベル（31件）:

```bash
REPO="<owner>/<repo>"

# SDD Issue タイプ（auto-add トリガー）
gh label create "epic" --repo "$REPO" --color "3E4B9E" --description "SDD Epic"
gh label create "milestone" --repo "$REPO" --color "006B75" --description "SDD Milestone"
gh label create "work-item" --repo "$REPO" --color "0075ca" --description "SDD Work Item"
gh label create "risk" --repo "$REPO" --color "D93F0B" --description "SDD Risk"
gh label create "blocker" --repo "$REPO" --color "B60205" --description "SDD Blocker"
gh label create "dependency" --repo "$REPO" --color "FBCA04" --description "SDD Dependency"

# Symphony 状態
gh label create "symphony:ready" --repo "$REPO" --color "0E8A16" --description "Symphony auto-dispatch target"
gh label create "symphony:running" --repo "$REPO" --color "1D76DB" --description "Symphony agent is executing"
gh label create "symphony:done" --repo "$REPO" --color "5319E7" --description "Symphony completed"
gh label create "symphony:blocked" --repo "$REPO" --color "D93F0B" --description "Waiting for human approval"
gh label create "symphony:failed" --repo "$REPO" --color "B60205" --description "Symphony execution failed"

# SDD Phase
gh label create "phase:design" --repo "$REPO" --color "FBCA04" --description "SDD Phase 1: Design"
gh label create "phase:specify" --repo "$REPO" --color "F9D0C4" --description "SDD Phase 2: Specify"
gh label create "phase:tasking" --repo "$REPO" --color "C5DEF5" --description "SDD Phase 3: Tasking"
gh label create "phase:execute" --repo "$REPO" --color "BFD4F2" --description "SDD Phase 4: Execute"

# Status 連動
gh label create "status:pending" --repo "$REPO" --color "c5def5" --description "Status: Pending"
gh label create "status:in-progress" --repo "$REPO" --color "fbca04" --description "Status: In Progress"
gh label create "status:done" --repo "$REPO" --color "0e8a16" --description "Status: Done"
gh label create "status:blocked" --repo "$REPO" --color "d93f0b" --description "Status: Blocked"

# Priority
gh label create "priority:high" --repo "$REPO" --color "d93f0b" --description "Priority: High"
gh label create "priority:medium" --repo "$REPO" --color "fbca04" --description "Priority: Medium"
gh label create "priority:low" --repo "$REPO" --color "c5def5" --description "Priority: Low"

# SDD Mode
gh label create "mode:autopilot" --repo "$REPO" --color "c5def5" --description "SDD Mode: Autopilot"
gh label create "mode:confirm" --repo "$REPO" --color "fbca04" --description "SDD Mode: Confirm"
gh label create "mode:validate" --repo "$REPO" --color "d93f0b" --description "SDD Mode: Validate"

# SDD Gate
gh label create "gate:1-design" --repo "$REPO" --color "bfd4f2" --description "SDD Gate 1: Design"
gh label create "gate:2-bpmn" --repo "$REPO" --color "bfd4f2" --description "SDD Gate 2: BPMN"
gh label create "gate:3-spec" --repo "$REPO" --color "bfd4f2" --description "SDD Gate 3: Spec"
gh label create "gate:4-plan" --repo "$REPO" --color "bfd4f2" --description "SDD Gate 4: Plan"
gh label create "gate:5-tasking" --repo "$REPO" --color "bfd4f2" --description "SDD Gate 5: Tasking"
gh label create "gate:final" --repo "$REPO" --color "0e8a16" --description "SDD Gate: Final"
```

---

## Step 6: GitHub Projects V2 ボード + カスタムフィールドの作成

### 6-1: プロジェクト作成

```bash
# 個人アカウントの場合
gh project create --owner <username> --title "<プロジェクト名> SDD Board" --format json

# 組織の場合
gh project create --owner <org-name> --title "<プロジェクト名> SDD Board" --format json
```

出力の `"number"` の値を控える → **Step 4 の `STRIDE_PROJECT_NUMBER` に設定**。

```bash
# ← Step 4 で保留していた変数をここで設定
gh variable set STRIDE_PROJECT_NUMBER --repo <owner>/<repo> --body "<number>"
```

### 6-2: カスタムフィールド作成

```bash
PROJECT=<number>
OWNER=<owner>

# テキストフィールド（5件）
for field in "Feature ID" "WI ID" "Risk Flags" "Gate Age (days)" "Estimate"; do
  gh project field-create "$PROJECT" --owner "$OWNER" --name "$field" --data-type TEXT
done

# 日付フィールド（2件）
for field in "Start date" "Target date"; do
  gh project field-create "$PROJECT" --owner "$OWNER" --name "$field" --data-type DATE
done

# 単一選択フィールド（9件）
gh project field-create "$PROJECT" --owner "$OWNER" --name "Priority" \
  --data-type SINGLE_SELECT --single-select-options "P0-Critical,P1-High,P2-Medium,P3-Low"
gh project field-create "$PROJECT" --owner "$OWNER" --name "Size" \
  --data-type SINGLE_SELECT --single-select-options "XS,S,M,L,XL"
gh project field-create "$PROJECT" --owner "$OWNER" --name "SDD Mode" \
  --data-type SINGLE_SELECT --single-select-options "autopilot,confirm,validate"
gh project field-create "$PROJECT" --owner "$OWNER" --name "Coverage Tier" \
  --data-type SINGLE_SELECT --single-select-options "starter,standard,enterprise"
gh project field-create "$PROJECT" --owner "$OWNER" --name "Complexity" \
  --data-type SINGLE_SELECT --single-select-options "low,medium,high,critical"
gh project field-create "$PROJECT" --owner "$OWNER" --name "SDD Gate" \
  --data-type SINGLE_SELECT --single-select-options "Gate 1,Gate 2,Gate 3,Gate 4,Gate 5,Final"
gh project field-create "$PROJECT" --owner "$OWNER" --name "WI Status" \
  --data-type SINGLE_SELECT \
  --single-select-options "pending_pre_approval,in_progress,pending_walkthrough,pending_ci,pending_ops,done"
gh project field-create "$PROJECT" --owner "$OWNER" --name "Gate" \
  --data-type SINGLE_SELECT --single-select-options "g1,g2,g3,g4,g5,evidence"
gh project field-create "$PROJECT" --owner "$OWNER" --name "Delay Risk" \
  --data-type SINGLE_SELECT --single-select-options "on_track,at_risk,overdue"
```

### 6-3: フィールド作成の検証

```bash
gh project field-list $PROJECT --owner $OWNER --format json | python -c "
import json, sys
data = json.load(sys.stdin)
expected = [
  'Priority', 'Size', 'Estimate', 'Start date', 'Target date',
  'Feature ID', 'WI ID', 'Risk Flags', 'Gate Age (days)',
  'SDD Mode', 'Coverage Tier', 'Complexity', 'SDD Gate',
  'WI Status', 'Gate', 'Delay Risk'
]
found = [f['name'] for f in data.get('fields', [])]
for e in expected:
    status = 'OK' if e in found else 'MISSING'
    print(f'  {status}: {e}')
missing = [e for e in expected if e not in found]
print(f'\nResult: {len(expected)-len(missing)}/{len(expected)} fields')
if missing: print(f'MISSING: {missing}')
"
```

---

## Step 7: 動作検証

### 7-1: symphony validate

```bash
cd <repo-root>
python -m symphony validate
```

`tracker.repo` に正しいリポジトリ名が表示され、`OK: Configuration is valid.` であること。

### 7-2: work-item auto-add テスト

```bash
gh issue create --repo <owner>/<repo> \
  --title "セットアップ検証: work-item テスト" \
  --label "work-item,mode:confirm,priority:high" \
  --body "| Field | Value |
|-------|-------|
| Feature | FEAT-TEST-001 |
| WI ID | WI-TEST-001 |
| Complexity | medium |"
```

1-2分後に CI が完了したら確認:

```bash
# CI 結果
gh run list --repo <owner>/<repo> --limit 3

# Projects ボードの確認
gh project item-list $PROJECT --owner $OWNER --format json | python -c "
import json, sys
data = json.load(sys.stdin)
for item in data.get('items', []):
    print(f\"Issue: {item.get('title','')}\")
    for k, v in sorted(item.items()):
        if k not in ('id', 'title', 'content') and v:
            print(f'  {k}: {v}')
"
```

**期待結果**: 8/8 フィールドが OK（Start date 含む）

### 7-3: Symphony dispatch テスト

Issue テンプレートは Phase 別に 4 つ用意されています:

| テンプレート | Phase | 特有の入力項目 |
|-------------|-------|---------------|
| `Symphony: Design (Phase 1)` | design | Group Spec YAML Path, Feature Spec YAML Path |
| `Symphony: Specify (Phase 2)` | specify | なし |
| `Symphony: Tasking (Phase 3)` | tasking | なし |
| `Symphony: Execute (Phase 4)` | execute | なし |

**Design Phase のテスト（仕様書 YAML あり）:**

```bash
# 仕様書 YAML を配置（仕様書エディタから出力済みの場合）
# docs/yaml/<group-id>/<group-id>.group.yaml
# docs/yaml/<group-id>/features/<feature-id>.feature.yaml

# GitHub の Issues → New Issue → "Symphony: Design (Phase 1)" テンプレートを選択
# または CLI で作成:
gh issue create --repo <owner>/<repo> \
  --title "<機能名> 設計" \
  --label "symphony:ready,phase:design,priority:P2" \
  --body "### Phase

design

### Feature Name

<feature_name>

### Priority

P2-Medium

### Description

<機能の説明>

### Group Spec YAML Path

docs/yaml/<group-id>/<group-id>.group.yaml

### Feature Spec YAML Path

docs/yaml/<group-id>/features/<feature-id>.feature.yaml

### Acceptance Criteria

_No response_"
```

```bash
# dry-run で確認
python -m symphony dispatch --issue <issue-number> --dry-run

# 実行
python -m symphony dispatch --issue <issue-number>
```

**期待結果**: `engine=claude-code`, Phase 完了後に Issue に `symphony:blocked`（承認待ち）または `symphony:done` ラベルが付与される。

---

## Symphony 運用フロー

セットアップ完了後の日常運用フローは以下の通りです。
詳細は `extensions/sap/docs/SYMPHONY_OPERATION_GUIDE.md` を参照してください。

```
1. GitHub で Issue 作成（Phase 別テンプレートを選択）
2. ローカルで stride symphony dispatch --issue <N> を実行
3. Symphony が自動で Claude Code を起動し、成果物を生成 → PR 作成
4. ローカルで symphony ブランチを checkout
5. 生成内容をレビュー（Issue コメントのトレーサビリティ報告を参照）
6. 修正が必要ならローカル Claude Code で指示 → push
7. 問題なければ APPROVAL.md で Gate 承認 → push
8. 次の Phase の Issue を作成して繰り返し
```

**重要**: Symphony の役割は「初期生成」のみ。修正・承認はローカルの Claude Code で行います。

---

## チェックリスト

| # | 設定項目 | 完了 |
|---|---------|------|
| 1 | テンプレートソース入手（clone or zip） | [ ] |
| 2 | GitHub リポジトリ作成 + push | [ ] |
| 3 | `stride-new-project.sh` 実行 | [ ] |
| 4 | PAT 作成（repo + project + read:org） | [ ] |
| 5 | STRIDE_PROJECT_TOKEN シークレット設定 | [ ] |
| 6 | ラベル作成（最低31件 or 全56件コピー） | [ ] |
| 7 | Projects V2 ボード作成 | [ ] |
| 8 | STRIDE_PROJECT_NUMBER 変数設定 | [ ] |
| 9 | カスタムフィールド作成（16件） | [ ] |
| 10 | `symphony validate` 成功 | [ ] |
| 11 | work-item auto-add 動作確認（8/8 OK） | [ ] |
| 12 | Symphony dispatch dry-run 成功 | [ ] |

---

## トラブルシューティング

### `unknown owner type` エラー（gh project item-add）

**原因**: PAT に `read:org` スコープがない
**対処**: PAT を再作成し `read:org` を追加。Step 3 参照。

### `git push -u origin main` が `src refspec main does not match any` で失敗

**原因**: `git init` のデフォルトブランチが `master`
**対処**: `git branch -m master main` を実行してから push。恒久対策: `git config --global init.defaultBranch main`

### `symphony validate` で `tracker.repo` エラー

**原因**: `repo: "auto"` だが git remote origin が未設定
**対処**: `git remote -v` で origin が正しいか確認。`git remote add origin <url>` で設定。

### `stride-new-project.sh` が `SYMPHONY.md tracker.repo → ...` と表示するが実際は変更されない

**原因**: スクリプトの sed パターンが旧値（`tecnos-japan-cbp/...`）を対象としており、`"auto"` にはマッチしない
**対処**: 正常動作。`repo: "auto"` のままで問題なし。

### 組織リポジトリで Projects API がエラー

**原因**: PAT が組織で承認されていない
**対処**: Step 3「組織リポジトリの場合」の手順を実施。

### Symphony エージェントの生成内容に誤りがある

**対処**: Symphony を再実行するのではなく、ローカルで対応する。
1. symphony ブランチを `git checkout` する
2. Issue コメントのトレーサビリティ報告を確認し、AI の判断根拠を把握する
3. ローカルの Claude Code で修正を指示する
4. 修正を commit & push する

ソース YAML 自体に問題がある場合は、YAML を修正して main にマージしてから、新しい Issue で Symphony を再実行する。
