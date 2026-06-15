# 30. Symphony Orchestration ガイド

> **Version**: v5.4.0-tecnos-stride
>
> GitHub Issues をトリガーとした SDD Phase 自動実行パイプライン。
> Issue にラベルを付けるだけで、エージェントが Design → Specify → Tasking → Execute を自律実行します。
>
> **v5.1 の追加**: Symphony Janitor — autopilot + starter tier + リスクフラグなしの Issue にクリーンアップ提案を生成
> **v5.2 の追加**: `stride symphony` CLI 統合 — `bin/stride` から run / dispatch / status / validate / janitor の 5 subcommand を完全 dispatch（従来の `python3 -m symphony.cli` を stride CLI 経由で統一）

---

## 概要

**Symphony** は、GitHub Issues を入力として SDD の各 Phase をエージェント（Claude Code / Codex）に自動実行させるオーケストレーションエンジンです。

```
GitHub Issue          Symphony Orchestrator              Agent (Claude Code / Codex)
─────────────         ─────────────────────              ─────────────────────────────

[Issue作成]
[symphony:ready 付与] ──→ ポーリングで検出
                          ├── Phase 判定
                          ├── Engine 選択 (routing)
                          ├── Workspace 作成 (worktree)
                          ├── Prompt 生成 (Jinja2)
                          └── Agent 起動 ──────────────→ [SDD成果物作成]
                                                          [stride-lint 実行]
                                                          [PR 作成]
                          ←─ 結果受取 ←─────────────────
                          ├── 成功 → symphony:done
                          ├── 承認待ち → symphony:blocked
                          └── 失敗 → リトライ or symphony:failed
```

### 主要コンポーネント

| モジュール | 役割 |
|-----------|------|
| `symphony/cli.py` | CLI エントリポイント（run, dispatch, status, validate） |
| `symphony/config.py` | SYMPHONY.md の YAML 設定ロード |
| `symphony/router.py` | Phase × Complexity に基づくエンジン選択 |
| `symphony/reconciler.py` | GitHub との状態ドリフト検出・自動修復 |
| `symphony/parallel.py` | Phase 4 の並列 WI 実行（asyncio + ThreadPool） |
| `symphony/prompt.py` | Jinja2 テンプレートレンダリング |
| `symphony/runner.py` | Claude Code / Codex プロセス起動 |
| `symphony/workspace.py` | Git worktree ベースのワークスペース管理 |
| `symphony/tracker.py` | GitHub Issues API ラッパー（ラベル操作, コメント投稿） |
| `symphony/stride_bridge.py` | stride-lint, auto-continue, run-report 連携 |

---

## セットアップ

### 1. SYMPHONY.md を配置

プロジェクトルートに `SYMPHONY.md` を作成します。`stride-new-project.sh` を使うと自動生成されます。

```bash
# 新規プロジェクトの場合
scripts/stride-new-project.sh my-project --org my-org
# → SYMPHONY.md の tracker.repo が "my-org/my-project" に設定される
```

手動の場合は `sdd-templates/templates/SYMPHONY_template.md` をコピーし、`tracker.repo` を `owner/repo` 形式で設定してください。

### 2. GitHub ラベルを作成

```bash
# Step 1: GitHub Projects ラベル（mode/tier/symphony/phase 等 43件）
cat sdd-templates/templates/github-projects/labels.json | jq -c '.[]' | while read label; do
  gh label create "$(echo $label | jq -r .name)" \
    --color "$(echo $label | jq -r .color)" \
    --description "$(echo $label | jq -r .description)" --force
done

# Step 2: STRIDE Learning Loop ラベル（findings/amendment/sentry 等 20件）
python3 sdd-templates/tools/setup_project_labels.py --repo owner/repo
```

これにより以下の Symphony 用ラベルが作成されます（step 1 の `labels.json` から）:

| ラベル | 色 | 用途 |
|--------|-----|------|
| `symphony:ready` | 青 | オーケストレーターに実行を指示 |
| `symphony:running` | 黄 | エージェント実行中 |
| `symphony:done` | 緑 | Phase 完了 |
| `symphony:blocked` | オレンジ | 承認待ち（APPROVAL_PENDING） |
| `symphony:failed` | 赤 | 失敗（リトライ上限到達） |
| `symphony:janitor` | 薄緑 | Janitor クリーンアップ提案 |
| `phase:design` | 黄 | SDD Phase 1: Design |
| `phase:specify` | 桃 | SDD Phase 2: Specify |
| `phase:tasking` | 水色 | SDD Phase 3: Tasking |
| `phase:execute` | 薄青 | SDD Phase 4: Execute |

### 3. 設定を検証

```bash
sdd-templates/bin/stride symphony validate
```

---

## SYMPHONY.md 設定リファレンス

SYMPHONY.md は **YAML フロントマター + Jinja2 プロンプトテンプレート** の構造です。

### フロントマター（設定）

```yaml
---
version: "1.0.0"

tracker:
  kind: github
  repo: "owner/repo"              # 必須: owner/repo 形式
  trigger_label: "symphony:ready"
  running_label: "symphony:running"
  done_label: "symphony:done"
  blocked_label: "symphony:blocked"
  failed_label: "symphony:failed"

polling:
  interval_seconds: 60            # ポーリング間隔（秒）

workspace:
  strategy: "worktree"            # reserved（将来拡張用）
  root: ".symphony/workspaces"
  branch_prefix: "symphony/"

agent:
  routing:
    design:
      engine: claude-code
      reason: "基本設計・BPMNは判断力が必要"  # documentation-only
    specify:
      engine: claude-code
      reason: "spec_as_code・NFR・契約定義は判断力が必要"
    tasking:
      engine: claude-code
      reason: "Plan IDとの整合性が重要"
    execute:
      engine: codex
      reason: "WI 単位で明確、速度×並列を優先"
      parallel: true
      max_concurrent: 4

  complexity_override:
    enabled: true
    high_complexity_engine: claude-code
    low_complexity_engine: codex

  claude_code:
    command: "claude"
    args: ["-p", "--dangerously-skip-permissions"]
    model: "claude-opus-4-7"   # Claude phases を固定
    effort_level: "xhigh"      # low | medium | high | xhigh | max
    max_output_tokens: 65536   # Claude Code env に反映
    timeout_ms: 3600000
  codex:
    command: "codex"
    subcommand: "exec"
    args: ["--full-auto"]
    timeout_ms: 1800000

  retry:
    max_attempts: 3
    backoff_base_ms: 10000
    backoff_max_ms: 300000

hooks:
  after_create: |
    # ワークスペース作成後に実行
  before_run: |
    # エージェント実行前に実行
  after_run: |
    # エージェント実行後に実行

observability:
  log_dir: ".symphony/logs"
  structured: true                # reserved（将来拡張用）
  stride_board:
    enabled: false
    project: null
    owner: null
---
```

`claude_code.model` / `effort_level` / `max_output_tokens` は、Design・Specify・Tasking の再現性を確保するための固定値です。特に Opus 4.7 系では effort 差分が出やすいため、プロジェクトごとに明示設定してください。

### プロンプトテンプレート（本文）

フロントマターの後に Jinja2 テンプレートとして Phase 別の行動指示を記述します。利用可能な変数:

| 変数 | 型 | 説明 |
|------|----|------|
| `{{ issue.identifier }}` | str | `#42` 形式の Issue 参照 |
| `{{ issue.title }}` | str | Issue タイトル |
| `{{ issue.url }}` | str | Issue の URL |
| `{{ issue.priority }}` | str | 優先度 |
| `{{ issue.description }}` | str | Issue 本文 |
| `{{ phase }}` | str | SDD Phase 名（design/specify/tasking/execute） |
| `{{ feature_name }}` | str | Feature 識別子 |
| `{{ attempt }}` | int/None | リトライ回数（初回は None） |

```jinja2
# Symphony Task: {{ issue.identifier }} — {{ issue.title }}

{% if phase == "design" %}
### Phase 1: Design
1. stride init {{ feature_name }} --detect
2. basic_design.md を作成
3. process.bpmn を作成
4. stride-lint 実行
5. PR 作成
{% elif phase == "execute" %}
### Phase 4: Execute
1. tasks.md のタスクを実装
...
{% endif %}
```

---

## CLI コマンド

すべてのコマンドは `stride symphony` サブコマンドとして実行します。

### `stride symphony run`

メインのポーリングループ。`symphony:ready` ラベルの Issue を検出して自動実行。

```bash
sdd-templates/bin/stride symphony run              # 永続ポーリング
sdd-templates/bin/stride symphony run --once        # 1サイクルのみ
sdd-templates/bin/stride symphony run --once --dry-run  # シミュレーション
```

**オプション:**

| フラグ | 説明 |
|--------|------|
| `--once` | 1ポーリングサイクル実行後に終了 |
| `--dry-run` | エージェントを実際には起動せずシミュレーション |
| `--config <path>` | SYMPHONY.md のパス（デフォルト: `SYMPHONY.md`） |

### `stride symphony dispatch`

単一 Issue を即座にディスパッチ。

```bash
sdd-templates/bin/stride symphony dispatch --issue 42
sdd-templates/bin/stride symphony dispatch --issue 42 --dry-run
```

### `stride symphony status`

`symphony:ready` ラベルの Issue 一覧を表示。

```bash
sdd-templates/bin/stride symphony status
```

出力例:
```
Repo:          owner/repo
Trigger label: symphony:ready

Ready issues (2):
  #  42  [P1] design       auth-module          [Design] 認証モジュール基本設計
  #  43  [P2] execute      order-form           [Execute] WI-ORD-001: 受注登録
```

### `stride symphony validate`

SYMPHONY.md の設定を検証。

```bash
sdd-templates/bin/stride symphony validate
```

検証内容:
- YAML フロントマターの構文
- `tracker.repo` の `owner/repo` 形式チェック
- `agent.routing.*.engine` のエンジン名ホワイトリスト（`claude-code`, `codex`）
- `agent.complexity_override` のエンジン名ホワイトリスト
- `agent.claude_code.effort_level` の値チェック（`low|medium|high|xhigh|max`）
- `agent.claude_code.max_output_tokens` の正数チェック
- プロンプトテンプレートの Jinja2 構文チェック
- プロンプトテンプレートの長さ
- routing phases の一覧
- stride_board 設定の整合性
- **v5.1+: `janitor:` セクション（enabled / interval_hours / exclude_recent_pr_days / risk_flags_exclude）**

### `stride symphony janitor` (v5.1 追加、v5.2 で bin/stride 統合)

Symphony Janitor の単発スキャン実行。`mode:autopilot + tier:starter` のフィーチャに対し、
リスクフラグのない低影響エリアに限定してクリーンアップ提案 Issue を生成する。

```bash
sdd-templates/bin/stride symphony janitor              # 1サイクルだけ実行
sdd-templates/bin/stride symphony janitor --dry-run    # 設定・スコープ表示のみ
```

- `janitor.enabled=false` の場合は "skipped" を出力して exit 0 で終了
- 除外対象: `risk:authz`, `risk:pii`, `risk:external_api`, `risk:sod`
- 直近 PR があるフィーチャも除外（`exclude_recent_pr_days`、既定 7 日）
- 自動 PR は発行しない（**提案 Issue のみ**）
- `stride symphony run` のポーリングループは同じ内部スキャンを `interval_hours` 間隔で呼び出す

---

## エンジンルーティング

Symphony はエージェントエンジン（Claude Code / Codex）を Phase と Complexity に基づいて選択します。

### 選択ロジック（優先順）

```
1. Complexity Override（有効かつ Issue に complexity 情報あり）
   → high → high_complexity_engine (claude-code)
   → low/medium → low_complexity_engine (codex)

2. Phase-based Routing（SYMPHONY.md の routing 設定）
   → design → claude-code
   → specify → claude-code
   → tasking → claude-code
   → execute → codex

3. フォールバック → claude-code
```

### Phase 別の推奨エンジン

| Phase | 推奨 Engine | 理由 |
|-------|------------|------|
| Design | Claude Code | 基本設計・BPMN は深い判断力と文脈理解が必要 |
| Specify | Claude Code | spec_as_code・NFR・契約定義は判断力が必要 |
| Tasking | Claude Code | Plan ID との整合性・タスク分解は判断が重要 |
| Execute | Codex（並列） | tasks.md/WI 単位で明確、速度×並列を優先 |

---

## ラベルライフサイクル

Issue のラベルは Symphony が自動管理します。

```
                    ┌─────────────────────────┐
                    │   symphony:ready        │  ← 人間が付与
                    └────────────┬────────────┘
                                 │ 検出
                    ┌────────────▼────────────┐
                    │   symphony:running      │  ← 自動付与
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
    ┌─────────▼──────┐ ┌────────▼───────┐ ┌────────▼────────┐
    │ symphony:done  │ │symphony:blocked│ │symphony:failed  │
    │ (成功)         │ │ (承認待ち)     │ │(最終失敗)       │
    └────────────────┘ └────────┬───────┘ └─────────────────┘
                                │
                       承認完了 → auto-continue
                                │
                    ┌───────────▼──────────┐
                    │  symphony:running    │  ← 再開
                    └──────────────────────┘
```

**重要:** `symphony:ready` ラベルの付与は **人間のみ** が行います。これが Phase 実行のトリガーです。

---

## Reconciler（状態整合）

オーケストレーターは各ポーリングサイクルで GitHub との状態ドリフトを検出し、自動修復します。

### 検出パターン

| パターン | 条件 | アクション |
|---------|------|----------|
| **Cleanup** | Issue がクローズ済み、またはトリガーラベルが除去済み | セッション破棄 + running/blocked ラベル除去 |
| **Unblock** | blocked セッションの APPROVAL_PENDING が解消 | status を running に戻し auto-continue |
| **Stale Claims** | claimed だが running でも retry でもない | claim を解放し running ラベル除去 |

### リトライ戦略

```yaml
retry:
  max_attempts: 3           # 最大リトライ回数
  backoff_base_ms: 10000    # 初回待機時間（10秒）
  backoff_max_ms: 300000    # 最大待機時間（5分）
```

指数バックオフ: `min(base_ms * 2^(attempt-1), backoff_max_ms)`

---

## 並列実行（Phase 4）

Execute Phase は `parallel: true` を設定することで、複数 WI を並列実行できます。

### 仕組み

- `asyncio.Semaphore` で同時実行数を `max_concurrent` に制限
- `ThreadPoolExecutor` で各エージェントプロセスを非同期実行
- Phase ごとにグルーピングし、それぞれの `max_concurrent` を適用

```yaml
agent:
  routing:
    execute:
      engine: codex
      parallel: true
      max_concurrent: 4    # 同時に最大4つの WI を実行
```

### 注意事項

- 並列実行は `--dry-run` 時は無効（シリアル実行にフォールバック）
- 並列タスク内でエラーが発生した場合、個別にリトライキューに投入
- Design/Specify/Tasking Phase は判断の一貫性のためシリアル実行推奨

---

## Hooks

SYMPHONY.md の `hooks` セクションで、ワークスペースライフサイクルにシェルスクリプトをフックできます。

| Hook | タイミング | ユースケース |
|------|----------|------------|
| `after_create` | ワークスペース作成直後 | symlink 作成、依存ファイルコピー |
| `before_run` | エージェント起動前 | `git pull --rebase` で最新化 |
| `after_run` | エージェント完了後 | stride-lint 実行、結果検証 |

Hook 実行時の環境変数:

| 変数 | 値 |
|------|----|
| `SYMPHONY_FEATURE` | Feature 識別子 |
| `SYMPHONY_ISSUE` | Issue 番号 |

---

## ワークスペース管理

Symphony は Issue ごとに **Git worktree** でワークスペースを作成します。

```
.symphony/workspaces/
├── <issue_id>/                       # worktree ディレクトリ（Issue 番号）
│   ├── sdd-templates/                # (symlink or copy)
│   ├── specs/
│   └── ...
└── ...
```

- ブランチ名: `symphony/<feature_name>-<issue_number>`
- リトライ時は既存ワークスペースを再利用（worktree/branch の衝突を回避）
- 成功/最終失敗後にワークスペースは自動クリーンアップ
- `after_create` hook で sdd-templates の symlink を作成可能

---

## ログ

ログは `observability.log_dir`（デフォルト: `.symphony/logs`）に出力されます。

```
.symphony/logs/
└── 2026-03-10/
    ├── orchestrator.jsonl            # オーケストレーター全体ログ (JSON Lines)
    ├── 42.jsonl                      # Issue #42 専用ログ (JSON Lines)
    ├── 43.jsonl                      # Issue #43 専用ログ
    ├── issue-42-attempt-1.log        # エージェント stdout/stderr
    ├── issue-42-attempt-2.log        # リトライ時のログ
    └── issue-43-attempt-1.log
```

---

## 運用シナリオ

### シナリオ 1: Design Phase の実行

```bash
# 1. GitHub Issue を作成
#    タイトル: [Design] FEAT-AUTH: 認証モジュール基本設計
#    ラベル: symphony:ready, phase:design

# 2. Symphony が検出して自動実行
sdd-templates/bin/stride symphony run --once

# 3. エージェントが以下を実行:
#    - stride init auth-module --detect
#    - basic_design.md + process.bpmn 作成
#    - stride-lint 実行
#    - PR 作成
#    - APPROVAL_PENDING → symphony:blocked

# 4. 人間が APPROVAL.md で Gate 1,2 を承認
# 5. 次のポーリングで Reconciler が検出 → auto-continue → symphony:done
```

### シナリオ 2: Execute Phase の並列実行

```bash
# 1. 複数の WI Issue に symphony:ready を付与
#    Issue #101: [Execute] WI-AUTH-001
#    Issue #102: [Execute] WI-AUTH-002
#    Issue #103: [Execute] WI-AUTH-003

# 2. Symphony が3つとも検出し、max_concurrent=4 で並列実行
# 3. 各 WI が独立したワークスペースで実装 → PR
```

### シナリオ 3: 失敗とリトライ

```bash
# 1. エージェントがエラーで失敗
#    → Issue にコメント: "Run attempt 1 failed. Retrying in 10s."
#    → symphony:running のまま（リトライ待ち）

# 2. 10秒後にリトライ（attempt 2）
# 3. 3回失敗 → symphony:failed + 手動介入要求コメント
```

---

## APPROVAL.md との連携

Symphony は SDD の Phase Gate ルールを厳守します。

- エージェントの実行結果が `APPROVAL_PENDING`（stride-lint 判定）の場合、`symphony:blocked` ラベルを付与して停止
- 人間が `APPROVAL.md` で Gate を承認すると、次のポーリングで Reconciler が検出し auto-continue
- **APPROVAL.md / WI-*.approval.md をエージェントが編集することは絶対禁止**（SDD INVIOLABLE ルール）

---

## トラブルシューティング

### Issue が検出されない

- `symphony:ready` ラベルが正しく付与されているか確認
- `stride symphony status` で検出可能な Issue を確認
- `stride symphony validate` で `tracker.repo` が正しいか確認

### エージェントがタイムアウトする

- `agent.claude_code.timeout_ms` / `agent.codex.timeout_ms` を増やす
- ログファイル（`.symphony/logs/`）でエージェントの進捗を確認

### Claude 側の出力が浅い / 途中で切れる

- `agent.claude_code.model` が想定モデルに固定されているか確認
- 深い設計判断が必要なら `agent.claude_code.effort_level` を `high` 以上に上げる
- 出力途中で切れる場合は `agent.claude_code.max_output_tokens` を増やす

### GitHub コメント投稿に失敗する

Symphony は Issue へのコメント投稿（`gh issue comment`）に失敗しても、オーケストレーション自体は停止しません（v4.5.1）。GitHub API のレートリミットや一時的なネットワーク障害が発生した場合、警告をログに出力して処理を続行します。

- ログに `WARNING: Failed to post comment to issue #N` が出ている場合は GitHub API の状態を確認
- コメントが欠落していても、ラベル遷移とエージェント実行は正常に動作します

### symphony:blocked のまま進まない

- `APPROVAL.md` で該当 Gate が承認済みか確認
- Reconciler は各ポーリングサイクルで `stride-lint` を実行して承認状態を再チェック
- `symphony:blocked` ラベルを手動で除去し、`symphony:ready` を再付与して再実行も可能

### SYMPHONY.md の設定エラー

```bash
sdd-templates/bin/stride symphony validate
```

代表的なエラー:
- `tracker.repo is empty or still set to placeholder '{{GITHUB_REPO}}'`
- `tracker.repo is not in 'owner/repo' format`
- `agent.routing.*.engine '...' is not a valid engine`
- `Prompt template has invalid Jinja2 syntax: ...`
- `stride_board.enabled=true requires 'project' and 'owner' to be set`

---

> **📌 このガイドは SDD v4.8.0-tecnos-stride に基づいています。**
>
> 関連ファイル:
> - `SYMPHONY.md` — オーケストレーション設定 + プロンプトテンプレート
> - `sdd-templates/templates/SYMPHONY_template.md` — テンプレート版
> - `symphony/` — Python モジュール群
> - `agent_docs/commands.md` §8 — Symphony コマンド一覧
