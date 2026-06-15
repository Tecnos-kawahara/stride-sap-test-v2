---
# Symphony-style Orchestration Config for Tecnos-STRIDE v1.0
version: "1.0.0"

tracker:
  kind: github
  repo: "{{GITHUB_REPO}}"
  trigger_label: "symphony:ready"
  done_label: "symphony:done"
  blocked_label: "symphony:blocked"
  running_label: "symphony:running"
  failed_label: "symphony:failed"

polling:
  interval_seconds: 60

workspace:
  strategy: "worktree"  # reserved for future use (currently always worktree)
  root: ".symphony/workspaces"
  branch_prefix: "symphony/"

agent:
  # routing.*.reason is documentation-only (not used at runtime)
  routing:
    design:
      engine: claude-code
      reason: "基本設計・BPMNは深い判断力と文脈理解が必要"
    specify:
      engine: claude-code
      reason: "spec_as_code・NFR・契約定義は判断力が必要"
    tasking:
      engine: claude-code
      reason: "Plan IDとの整合性・タスク分解は判断が重要"
    execute:
      engine: codex
      reason: "tasks.md/WI単位で明確、速度×並列を優先"
      parallel: true
      max_concurrent: 4

  complexity_override:
    enabled: true
    high_complexity_engine: claude-code
    low_complexity_engine: codex

  claude_code:
    command: "claude"
    args: ["-p", "--dangerously-skip-permissions"]
    model: "claude-opus-4-7"
    effort_level: "xhigh"
    max_output_tokens: 65536
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
    if [ ! -d "sdd-templates" ]; then
      ln -s "$(git rev-parse --show-toplevel)/sdd-templates" sdd-templates
    fi

  before_run: |
    git pull origin main --rebase 2>/dev/null || true

  after_run: |
    if [ -n "$SYMPHONY_FEATURE" ] && [ -d "specs/$SYMPHONY_FEATURE/" ]; then
      sdd-templates/tools/stride-lint "specs/$SYMPHONY_FEATURE/" --warn-only 2>/dev/null || true
    fi

observability:
  log_dir: ".symphony/logs"
  structured: true  # reserved for future use
  stride_board:
    enabled: false
    project: null
    owner: null

# Janitor Proposals (v5.1.0 — Harness Maturity)
# Safe default: enabled=false. Project may override to true after review.
# See: agent_docs/harness.md §2.4
janitor:
  enabled: false
  interval_hours: 6
  exclude_recent_pr_days: 7
  risk_flags_exclude:
    - risk:authz
    - risk:pii
    - risk:external_api
    - risk:sod
---

# Symphony Task: {{ issue.identifier }} — {{ issue.title }}

## コンテキスト
- Issue: {{ issue.url }}
- Priority: {{ issue.priority }}
- Phase: {{ phase }}
- Feature: {{ feature_name }}
{% if attempt %}
- Attempt: {{ attempt }}（リトライ {{ attempt }} 回目）
{% endif %}

## あなたの役割
Tecnos-STRIDE SDD に従って開発するエージェントです。

**⛔ 最初に `agent_docs/sdd_bootstrap.md` を必ず読むこと。**
（CLAUDE.md の冒頭にも同じ指示があります）

## Issue の内容
{{ issue.description }}

## Phase別の行動指示

{% if phase == "design" %}
### Phase 1: Design

1. `sdd-templates/bin/stride init {{ feature_name }} --detect` でfeatureを初期化（未作成の場合）
2. Issue の内容から `basic_design.md` を作成
3. `process.bpmn` を作成
4. `sdd-templates/tools/stride-lint specs/{{ feature_name }}/` を実行し、APPROVAL以外のエラーは自動修正
5. lint PASS → PR を作成:
   - ブランチ: `symphony/{{ issue.identifier }}`
   - タイトル: `[Symphony][Design] {{ issue.identifier }}: {{ issue.title }}`
   - 本文に stride-lint の結果と Gate 1,2 承認依頼を含める
6. Issue に承認依頼コメントを投稿
7. **APPROVAL.md は絶対に編集しない**

{% elif phase == "specify" %}
### Phase 2: Specify

1. `spec.md` を作成（AC, NFR, spec_as_code）
2. `plan.md` を作成（3層カバレッジ, テスト戦略, evidence_pack）
3. `contracts/` 配下に OpenAPI, database_schema 等を配置
4. `tests/scenarios.yaml` を作成
5. `sdd-templates/tools/stride-lint specs/{{ feature_name }}/` を実行し、APPROVAL以外のエラーは自動修正
6. lint PASS → PR を作成:
   - タイトル: `[Symphony][Specify] {{ issue.identifier }}: {{ issue.title }}`
   - 本文に Gate 3,4 承認依頼を含める
7. **APPROVAL.md は絶対に編集しない**

{% elif phase == "tasking" %}
### Phase 3: Tasking

1. `tasks.md` を作成（全タスクに plan_refs 必須）
2. E2Eタグ付きACがあれば E2E tasks を含める
3. `sdd-templates/tools/stride-lint specs/{{ feature_name }}/` を実行し、自動修正
4. lint PASS → PR を作成:
   - タイトル: `[Symphony][Tasking] {{ issue.identifier }}: {{ issue.title }}`
   - 本文に Gate 5 承認依頼を含める
5. **APPROVAL.md は絶対に編集しない**

{% elif phase == "execute" %}
### Phase 4: Execute

**WI 管理方式**: GitHub Issues（`work-item` ラベル）で管理。

1. Issue に紐づく WI の `tasks.md` タスクを確認
2. WI 実行準備チェック: `python3 sdd-templates/tools/wi_readiness_checker.py specs/{{ feature_name }}/ <WI-ID>`
3. Run 開始: `python3 sdd-templates/tools/sdd_planning_bridge.py init specs/{{ feature_name }}/ <WI-ID>`
4. タスクを1つずつ実装:
   - **完了前の必須確認**: spec_refs の全AC再読 + tests/scenarios.yaml の全expected検証
   - 「動いた」≠「完了」。ACの全要素を満たして初めて完了
5. `sdd-templates/tools/stride-lint specs/{{ feature_name }}/` 実行
6. `python3 sdd-templates/tools/sdd_planning_bridge.py sync specs/{{ feature_name }}/` でFAILを反映
7. `python3 sdd-templates/tools/sdd_planning_bridge.py evidence specs/{{ feature_name }}/ <WI-ID>` で walkthrough に Planning Evidence 挿入
8. PR を作成:
   - タイトル: `[Symphony][Execute] {{ issue.identifier }}: {{ issue.title }}`
   - 本文に実装サマリー + WI承認依頼を含める
9. **WI-*.approval.md は絶対に編集しない**

{% endif %}

## 共通ルール
- stride-lint の FAIL（APPROVAL_PENDING 以外）は**自分で修正**してから報告
- PR本文に含めること: 実施内容サマリー, stride-lint 結果, Phase Gate 状態, 次のアクション
- Issue への紐付け: `Refs #{{ issue.number }}`（Phase 4 の最終WI完了時のみ `Closes`）
