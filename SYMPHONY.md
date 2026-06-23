---
# Symphony-style Orchestration Config for Tecnos-STRIDE v1.0
version: "1.0.0"

tracker:
  kind: github
  repo: "auto"  # git remote origin / GITHUB_REPOSITORY env var から自動検出
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
  base_branch: "main"  # Issue body の Base Branch 未指定時のフォールバック

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
      engine: claude-code
      reason: "SAP拡張のMUST ASK制約（DDIC承認、TR番号確認）に対応するため"

  complexity_override:
    enabled: true
    high_complexity_engine: claude-code
    low_complexity_engine: codex

  claude_code:
    command: "claude.cmd"
    args: ["-p", "--permission-mode", "auto"]
    model: "claude-opus-4-7"
    effort_level: "xhigh"
    max_output_tokens: 65536
    timeout_ms: 3600000
  codex:
    command: "wsl"
    subcommand: "codex"
    args: ["exec", "--sandbox", "workspace-write"]
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
    BASE_BRANCH="${SYMPHONY_BASE_BRANCH:-main}"
    git pull origin "$BASE_BRANCH" --rebase 2>/dev/null || true

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
# Project override: enabled=true (template default is false).
# Scope: mode:autopilot + tier:starter のみ、リスクフラグ除外適用、自動 PR なし（Issue 提案のみ）。
# See: agent_docs/harness.md §2.4
janitor:
  enabled: true
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
- Base Branch: {{ base_branch }}
{% if attempt %}
- Attempt: {{ attempt }}（リトライ {{ attempt }} 回目）
{% endif %}

## あなたの役割
Tecnos-STRIDE SDD に従って開発するエージェントです。

**⛔ 最初に `agent_docs/sdd_bootstrap.md` を必ず読むこと。**
（CLAUDE.md の冒頭にも同じ指示があります）

**⛔ `.stride-extensions.yaml` を確認し、Extension Pack が有効な場合は以下の3つを（存在すれば）読むこと:**
1. `extensions/<ext>/CLAUDE_<EXT>.md` — 拡張固有ルール
2. `extensions/<ext>/CLAUDE_WORKFLOW_<EXT>.md` — 拡張 Phase 別手順
3. `extensions/<ext>/SYMPHONY_<EXT>.md` — Symphony 実行時の拡張入力・設定

Extension Pack の Phase 別手順は標準フローに対する代替・追加として優先適用される。
拡張パックを読まずに Phase 作業を開始してはならない。

## Issue の内容
{{ issue.description }}

## Phase別の行動指示

{% if phase == "design" %}
### Phase 1: Design

1. `sdd-templates/bin/stride init {{ feature_name }} --detect` でfeatureを初期化（未作成の場合）
1.5. **探索ラダー**（既存解の確認、新規実装の前に必ず実施）
   - [ ] **プロジェクト内:** `rg` / `grep` で既存の類似実装を検索
   - [ ] **過去の教訓:** `~/.claude/knowledge/index.json` と直近 Runs の `lessons.md` を確認
   - [ ] **パッケージ/ライブラリ:** npm / PyPI / crates.io で既存の解がないか
   - [ ] **契約との整合:** 既存の `shared/contracts/` や他 feature の `contracts/` に類似定義がないか
   → 結果を `basic_design.md` の `## B.2 契約（Contract/CLI-First）` セクションに反映
2. Issue の内容から `basic_design.md` を作成
3. `process.bpmn` を作成
4. `sdd-templates/tools/stride-lint specs/{{ feature_name }}/` を実行し、APPROVAL以外のエラーは自動修正
5. lint PASS → PR を作成:
   - ブランチ: `symphony/{{ issue.identifier }}`
   - ベースブランチ（PR base）: `{{ base_branch }}`
   - タイトル: `[Symphony][Design] {{ issue.identifier }}: {{ issue.title }}`
   - 本文に stride-lint の結果と Gate 1,2 承認依頼を含める
   - コマンド例: `gh pr create --base {{ base_branch }} ...`
6. Issue に承認依頼コメントを投稿
7. **APPROVAL.md は絶対に編集しない**

{% elif phase == "specify" %}
### Phase 2: Specify

0.5. **探索ラダー**（spec.md 作成前に実施）
   - [ ] 他 feature の `spec.md` で類似の AC/NFR パターンがないか確認
   - [ ] `shared/contracts/` の共通コントラクトとの整合を事前確認
   - [ ] 既存の `tests/scenarios.yaml` で再利用可能なシナリオがないか
   → 発見した再利用可能要素を `spec.md` の `## 1.4 Spec-as-Code` セクション内に記録
1. `spec.md` を作成（AC, NFR, spec_as_code）
2. `plan.md` を作成（3層カバレッジ, テスト戦略, evidence_pack）
3. `contracts/` 配下に OpenAPI, database_schema 等を配置
4. `tests/scenarios.yaml` を作成
5. `sdd-templates/tools/stride-lint specs/{{ feature_name }}/` を実行し、APPROVAL以外のエラーは自動修正
6. lint PASS → PR を作成:
   - ベースブランチ（PR base）: `{{ base_branch }}`
   - タイトル: `[Symphony][Specify] {{ issue.identifier }}: {{ issue.title }}`
   - 本文に Gate 3,4 承認依頼を含める
   - コマンド例: `gh pr create --base {{ base_branch }} ...`
7. **APPROVAL.md は絶対に編集しない**

{% elif phase == "tasking" %}
### Phase 3: Tasking

1. `tasks.md` を作成（全タスクに plan_refs 必須）
2. E2Eタグ付きACがあれば E2E tasks を含める
3. `sdd-templates/tools/stride-lint specs/{{ feature_name }}/` を実行し、自動修正
4. lint PASS → PR を作成:
   - ベースブランチ（PR base）: `{{ base_branch }}`
   - タイトル: `[Symphony][Tasking] {{ issue.identifier }}: {{ issue.title }}`
   - 本文に Gate 5 承認依頼を含める
   - コマンド例: `gh pr create --base {{ base_branch }} ...`
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
   - ベースブランチ（PR base）: `{{ base_branch }}`
   - タイトル: `[Symphony][Execute] {{ issue.identifier }}: {{ issue.title }}`
   - 本文に実装サマリー + WI承認依頼を含める
   - コマンド例: `gh pr create --base {{ base_branch }} ...`
9. **WI-*.approval.md は絶対に編集しない**

{% endif %}

## 共通ルール
- **Extension Pack が有効な場合、各 Phase の作業は拡張パック側の手順を適用すること**（未確認なら `.stride-extensions.yaml` を参照）
- stride-lint の FAIL（APPROVAL_PENDING 以外）は**自分で修正**してから報告
- PR本文に含めること: 実施内容サマリー, stride-lint 結果, Phase Gate 状態, 次のアクション
- Issue への紐付け: `Refs #{{ issue.number }}`（Phase 4 の最終WI完了時のみ `Closes`）
- **人間の判断が必要な場合**（MUST ASK 制約、曖昧な要件、想定外エラー等）: Issue にコメントで状況と質問を投稿し、exit code 10 で終了（注: exit code 1 は「失敗」扱いでリトライされる。10 は「人間入力待ち」）
- **承認後の再実行（auto_continue）時**: APPROVAL.md の承認チェック状態を確認し、承認済みの Gate に対応する `basic_design.md` の `gate_check` YAML フラグを `true` に更新すること（例: APPROVAL.md の Gate 1,2 に承認チェックがあれば `process_bpmn_approved: true` に更新）
