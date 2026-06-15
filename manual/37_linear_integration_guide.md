# 37. Linear Integration — Run 成果物を Linear で追跡する (v5.3)

> Tecnos-STRIDE が生成する Work Item / Run 実行証跡を、Linear の Issue と
> 同期して一元可視化する仕組み。GitHub Issues ハイブリッド WI 管理とは独立で、
> 両立運用可能（GitHub = merge ゲート、Linear = 実行証跡 + 進捗ボード）。

---

## 1. なぜ Linear も必要か

GitHub Issues だけでは十分でない理由:

| 目的 | GitHub | Linear |
|------|--------|--------|
| PR 連動 (Fixes #N → merge) | ✅ | △ |
| Merge Queue / レビュー | ✅ | — |
| **週次/日次の進捗ボード** | △ | ✅ |
| **Cycle / Velocity 管理** | — | ✅ |
| **モバイル + デスクトップ UX** | △ | ✅ |
| **Roadmap / Milestone** | Projects V2 | Projects + Roadmap |
| **AI エージェントからの CLI 更新** | `gh` CLI | Linear GraphQL |

**Tecnos-STRIDE v5.3** は Linear GraphQL API を直接叩く薄いブリッジ
（`sdd-templates/tools/linear_bridge.py`）を提供し、Run の findings / walkthrough /
test_results / lessons を Linear Issue コメントとして自動投下する。

---

## 2. セットアップ（5 分）

### 2.1 Linear API Key の取得

1. https://linear.app/settings/account/security → **Personal API keys**
2. "Create new key" → ラベル（例: `tecnos-stride-bridge`）
3. 生成された Key をコピー（`lin_api_xxx...`）

### 2.2 環境変数設定

`.env.local`（**gitignore 済**）に追加:

```bash
# Linear Integration (v5.3)
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxxxxxx
LINEAR_TEAM_KEY=TEC                 # 既定: "TEC"（Tecnos AI）
LINEAR_PROJECT_ID=                   # 任意。指定すれば Issue を特定 Project に紐付け

# planning_bridge からの自動 Linear 同期を有効化（任意）
STRIDE_LINEAR_AUTO=1
```

Claude Code / CLI セッション開始前に shell に読込む:

```bash
set -a; source .env.local; set +a
```

### 2.3 動作確認

```bash
# オフライン self-test（API key 不要、19 tests）
sdd-templates/bin/stride linear --test

# ドライラン（API 呼出しなし、プレビューのみ）
sdd-templates/bin/stride linear --dry-run init specs/FEAT-ERPSAMPLE WI-ERP-SAMPLE-001

# 実 API（LINEAR_API_KEY が有効な場合）
sdd-templates/bin/stride linear status specs/FEAT-ERPSAMPLE
```

> **💡 API key なしで使うとどうなるか:** 全コマンドが graceful skip（exit 0、"LINEAR_API_KEY unset" メッセージ）。SDD 本体フローは止まらない。

---

## 3. CLI サブコマンド一覧

```
stride linear <subcommand> [options]

Subcommands:
  init <feature_dir> <wi_id>       Create/find Linear Issue for a Work Item
  findings <run_dir>               Post .planning/findings.md as Linear comment
  evidence <run_dir>               Post walkthrough + test_results as comment
  learn <run_dir>                  Post .planning/lessons.md as comment
  sync <run_dir>                   Idempotent: findings + evidence + learn
  close <feature_dir> <wi_id>      Transition Linear Issue to Done
  status <feature_dir> [<wi_id>]   Show WI → Linear Issue mapping

Flags:
  --dry-run                        Preview actions without calling the API
  --test                           Run 19 offline self-tests

Environment:
  LINEAR_API_KEY      Personal API key (required; unset → graceful skip)
  LINEAR_TEAM_KEY     Default team key (default: TEC)
  LINEAR_PROJECT_ID   Optional default project
  STRIDE_LINEAR_AUTO  "1" to let sdd_planning_bridge auto-invoke linear sync
```

---

## 4. 推奨ワークフロー

### 4.1 手動運用（各 Run で明示的に Linear 投下）

```bash
# Phase 4 (Execute) — WI 開始時
sdd-templates/bin/stride linear init specs/FEAT-ORDER WI-ORD-001
  # → Linear Issue "TEC-123" 作成（または既存検索）
  # → state.yaml の work_items[WI-ORD-001].linear_issue_id = "TEC-123" を記録

# Run 中（findings が増えたら適宜）
sdd-templates/bin/stride linear findings specs/FEAT-ORDER/runs/WI-ORD-001/RUN-20260419-0900

# Run 完了時（walkthrough + test_results 完成後）
sdd-templates/bin/stride linear evidence specs/FEAT-ORDER/runs/WI-ORD-001/RUN-20260419-0900
sdd-templates/bin/stride linear learn specs/FEAT-ORDER/runs/WI-ORD-001/RUN-20260419-0900

# または一括
sdd-templates/bin/stride linear sync specs/FEAT-ORDER/runs/WI-ORD-001/RUN-20260419-0900

# WI 承認完了後
sdd-templates/bin/stride linear close specs/FEAT-ORDER WI-ORD-001
```

### 4.2 自動運用（STRIDE_LINEAR_AUTO=1）

`.env.local` に `STRIDE_LINEAR_AUTO=1` を設定すると、`sdd_planning_bridge.py` の
`init` と `evidence` 呼出し時に自動的に Linear 同期が走る。

```bash
# AI が自律実行する通常の Run フローだけで Linear に反映される
sdd-templates/bin/stride auto-continue specs/FEAT-ORDER
```

裏で何が起きるか:

```
bridge init  → .planning/ 作成 → linear_bridge init  (Issue 作成/再利用)
    ↓
実装 + stride-lint
    ↓
bridge sync  → lint FAIL → plan.md Errors
    ↓
bridge evidence → walkthrough.md に Planning Evidence 挿入 → linear_bridge sync
                                                              (findings + evidence + lessons を Linear にコメント)
    ↓
/planning:archive → lessons → グローバル知識
    ↓
(人間が WI-*.approval.md で承認)
    ↓
stride linear close specs/FEAT-ORDER WI-ORD-001  ← 手動で明示クローズ（state.yaml 手更新でも可）
```

### 4.3 Claude Code セッションでの自然言語運用

```
あなた: 「WI-ORD-001 の Run 結果を Linear に反映して」
Claude: stride linear sync specs/FEAT-ORDER/runs/WI-ORD-001/RUN-... を実行
```

`CLAUDE.md` Linear Integration セクションの naturallanguage プロンプトを併用すれば、
Mac 版 Linear アプリで視覚確認 + Claude Code で更新、の分業が自然に回る。

---

## 5. Linear Issue の構造

### 5.1 Issue タイトル / 本文（`init` で作成）

- **Title**: `[WI-ORD-001] 受注登録画面の UI 改善`
- **Description**: WI / Feature / Mode / Coverage Tier / Risk Flags / Spec Refs / Intent / DoD を Markdown で自動生成

### 5.2 コメント（Run 証跡）

`sync` 実行ごとに、以下の Markdown ブロックがコメントとして追加される:

```markdown
## 🔎 Findings (from `.planning/findings.md`)
_Run: `RUN-20260419-0900`_

<findings.md の先頭 40 行の要約>

---

## 🧪 Run Evidence
_Run: `RUN-20260419-0900`_

### Walkthrough
<walkthrough.md の先頭 50 行>

### Test Results
<test_results.md の先頭 30 行>

---

## 📚 Lessons Learned
_Run: `RUN-20260419-0900`_

<lessons.md の先頭 60 行>
```

### 5.3 State transition

| WI 状態 | Linear State |
|---------|-------------|
| pending | Todo / Backlog（自動設定せず、人が Issue 作成後に決めてよい）|
| in_progress | In Progress（`init` 時に Linear 側が自動判定、または手動） |
| done | Done（`stride linear close` で遷移） |

`close` コマンドは `--state` で Canceled / Done を選択可能。

---

## 6. state.yaml との連携

`state.yaml` の `work_items[]` エントリに `linear_issue_id` フィールドが追加される:

```yaml
work_items:
  - wi_id: WI-ORD-001
    status: in_progress
    mode: confirm
    risk_flags: [new_api]
    linear_issue_id: "TEC-123"    # stride linear init で自動設定
```

この SSoT により、`stride linear status <feature>` で即座に WI → Linear 対応表が出力される:

```bash
$ stride linear status specs/FEAT-ORDER
  WI-ORD-001  → TEC-123
  WI-ORD-002  → —
```

---

## 7. GitHub Issues ハイブリッド WI 管理との併用

Tecnos-STRIDE はすでに GitHub Issues を WI の主管理先としている（`stride_wi_sync.py`）。
Linear 統合はこれを**置き換えない** — 以下のように役割分担する:

| 観点 | GitHub (work-item ラベル) | Linear (`[WI-*]` タイトル) |
|------|--------------------------|---------------------------|
| 起票 / merge ゲート | ✅（Fixes #N 連動）| — |
| CI 連携 / PR チェック | ✅ | — |
| 日次スタンドアップ | △ | ✅（Cycle / Board） |
| Run ごとの証跡閲覧 | run_report_generator が投稿 | linear_bridge が投稿 |
| Mobile / push 通知 | △ | ✅ |

どちらにも同じ WI-ID がタイトル prefix として入るため、横断検索で相互参照可能。

---

## 8. トラブルシュート

### 8.1 `stride linear init` が "LINEAR_API_KEY unset" でスキップする

**原因**: `.env.local` が shell に読込まれていない。
**対応**: `set -a; source .env.local; set +a` → 再実行。

### 8.2 `Linear API error: team not found: key=TEC`

**原因**: `LINEAR_TEAM_KEY` がワークスペースに存在しない。
**対応**: Linear の Team settings で key を確認（Tecnos AI は `TEC`）。

### 8.3 同じ WI で Issue が重複作成される

**原因**: `linear_bridge.find_issue_by_wi` は `[WI-XXX]` 形式タイトル prefix で検索する。
Issue タイトルを手動で変更した場合、自動検出できず新規作成される。
**対応**:
- 手動変更した Issue のタイトルに `[WI-XXX]` を戻す、OR
- `state.yaml` の `linear_issue_id` を手編集してから `sync` を呼ぶ

### 8.4 Linear Issue の状態遷移で `workflow state 'Done' not found`

**原因**: ワークスペースで Done ワークフロー状態の name が異なる（"Completed" 等）。
**対応**: `stride linear close <feature> <wi> --state Completed` でカスタム state 名を指定。

### 8.5 `STRIDE_LINEAR_AUTO=1` なのに planning_bridge 実行時に Linear が更新されない

**原因**: `STRIDE_LINEAR_AUTO` 変数がサブプロセスに伝播していない。
**対応**: shell セッションで `export STRIDE_LINEAR_AUTO=1` を実行。

### 8.6 `stride linear status` が何も表示しない

**原因**: `state.yaml` の `work_items` が空、または対象 WI が含まれない。
**対応**: WI 定義ファイル（`work_items/<WI>.md`）が存在することを確認し、`stride linear init` を実行。

---

## 9. よくある質問

**Q. API key を `.env.local` 以外に置いてもよい？**
A. `direnv` / `1Password CLI` / `op read` 等と併用可能。重要なのは `LINEAR_API_KEY` env
が `stride linear` 実行シェルで有効であること。コミットしないこと。

**Q. Linear の Project（Linear 側の Project。GitHub Projects ではない）に紐付けたい**
A. `LINEAR_PROJECT_ID` 環境変数を設定すれば `init` 時に自動で `projectId` を付与する。
Project ID は Linear の Project URL 末尾 UUID から取得可能。

**Q. 既存の Linear Issue (自分で作成済) に WI を紐付けたい**
A. `state.yaml` の `work_items[].linear_issue_id` に手動で Issue identifier（例 `TEC-123`）を書き、
以降の `sync` / `close` はそれを使う。`init` を走らせなければ重複は作られない。

**Q. Linear なしで SDD 運用を続けたい**
A. `LINEAR_API_KEY` を設定しなければ全コマンドが graceful skip（exit 0）する。
SDD 本体フローへの影響ゼロ。

---

## 11. Per-Project Linear Project 自動作成 (v5.3.1)

STRIDE テンプレートを**新しいプロジェクトに clone するたびに専用の Linear Project を作成**し、
全 Issue をそこに自動紐付ける。これにより複数 STRIDE プロジェクトが同じ team backlog に
混在するのを防ぐ。

### 11.1 自動化（推奨）

`stride new-project` 実行時に Linear Project も同時作成される:

```bash
stride new-project my_erp --org my-org \
  --linear-project "My ERP"             # Linear Project 名
# または：--linear-project - で明示的にスキップ
# または：--no-linear-project で完全スキップ
```

前提:
- `.env.local` に `LINEAR_API_KEY` が設定済み
- 未設定時は graceful skip（警告を出して継続、SDD 本体フローに影響なし）

実行結果: `memory/linear.yaml` に binding 情報が永続化される:

```yaml
team_key: "TEC"
project_id: "uuid-xxx..."
project_name: "My ERP"
url: "https://linear.app/tecnos-ai/project/..."
```

### 11.2 手動管理

新規プロジェクトで Linear Project を後付けで作る場合:

```bash
stride linear project create "My ERP"              # 作成 + memory/linear.yaml 永続化
stride linear project use <uuid>                   # 既存 Project に紐付け
stride linear project list                         # team 内の Project 一覧
stride linear project status                       # 現在の binding 確認
```

### 11.3 解決順位（precedence）

`stride linear init` 時、Issue を紐付ける Project ID は以下の優先順で解決:

1. CLI `--project-id` フラグ（存在すれば最優先、テスト用）
2. `LINEAR_PROJECT_ID` 環境変数
3. `memory/linear.yaml` の `project_id`
4. 未解決 → Issue は team backlog 直入れ（Project 未紐付け、後で手動ドラッグ）

実務上は **2 か 3** を採用する。一時的に別 Project に流したい場合のみ env で override。

### 11.4 複数 STRIDE プロジェクトの運用

```
Template repo (sdd_template_enterprise)
  ↓ clone
Project "alpha-erp"           Project "beta-crm"
  memory/linear.yaml           memory/linear.yaml
  project_id: uuid-α           project_id: uuid-β
  ↓ stride linear init         ↓ stride linear init
Linear Project α              Linear Project β
  [WI-ERP-001]                  [WI-CRM-001]
  [WI-ERP-002]                  [WI-CRM-002]
```

→ Linear UI 上で各 Project のボード / サイクルが分離される。Team (TEC) は共通のまま。

### 11.5 既存運用からの移行

v5.3.0 までに Linear に Issue を作ってしまっている場合:
1. Linear UI で該当 Project を手動作成（または既存を利用）
2. Project UUID を取得（URL 末尾）
3. `stride linear project use <uuid>` で `memory/linear.yaml` に永続化
4. 既存 Issue はドラッグ & ドロップで新 Project に集約

---

## 10. 関連ドキュメント

- `agent_docs/commands.md §12` — Linear CLI コマンド SSoT
- `CLAUDE.md` Linear Integration セクション — ユーザーレベルの自然言語運用
- `CLAUDE_WORKFLOW.md` — Claude Code 固有の MCP fallback（`mcp__claude_ai_Linear__*`）
- `sdd-templates/tools/linear_bridge.py` — 実装（urllib ベース、19 self-tests）
- `tests/test_linear_bridge_integration.py` — 10 integration tests

---

*Linear Integration は v5.3.0 で追加された機能です。`LINEAR_API_KEY` 未設定環境でも
SDD コアフローは従来通り動作するため、段階的に導入できます。*
