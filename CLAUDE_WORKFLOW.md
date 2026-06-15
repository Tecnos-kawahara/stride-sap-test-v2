# CLAUDE_WORKFLOW.md
# Claude Code 固有の設定・補足のみを集約する（SDD フロー本体は sdd_bootstrap.md が SSoT）。
# 版数: v5.3.3-tecnos-stride

## このファイルの範囲 (Opus 4.7 literal-follow 指針)

**このファイルには Claude Code 固有の設定のみ記載する。**
SDD Phase フロー / Gate ルール / 自律実行ルール / 自動修正の上限値 / Task Completion Checklist は
`agent_docs/sdd_bootstrap.md` が SSoT。矛盾した場合は bootstrap を優先する。

- 実行モデル（AI=R / 人間=A）: see `agent_docs/sdd_bootstrap.md` §1
- AI Action Boundary（MUST DO/ASK/NOT DO）: see `agent_docs/sdd_bootstrap.md` §2
- Phase 1-4 の詳細フロー: see `agent_docs/sdd_bootstrap.md` §3-6
- 自動修正の loop bound: see `agent_docs/sdd_bootstrap.md` §1 末尾
- Task Completion Checklist: see `agent_docs/sdd_bootstrap.md` §5

---

## 1. Agent Docs 読み込み順序 (Claude Code)

Claude Code は新規セッション開始時に以下を順に読む:

1. `CLAUDE.md` (プロジェクトルート) — このリポジトリの第一読本
2. `agent_docs/sdd_bootstrap.md` — SDD 実行 SSoT（全必須ルール集約、277 行）
3. 必要時のみ:
   - `agent_docs/commands.md` — 全 CLI コマンドの詳細
   - `agent_docs/sdd_guidelines.md` — 実装時の詳細ガイドライン
   - `agent_docs/testing.md` — テスト詳細（Execute Phase）
   - `agent_docs/security.md` — セキュリティ設計時
   - `agent_docs/harness.md` — Harness 成熟度 (v5.1)
   - `agent_docs/conventions.md` — 命名規約詳細
   - `memory/constitution.md` / `memory/tecnos_org_constraints.md` — 制約確認時
   - `SDD_MANIFESTO.md` — ツール非依存コア（他 AI ツール併用時）

## 2. Tooling Setup (Claude Code 固有)

- `stride-lint` ラッパー: `sdd-templates/tools/stride-lint` （shell wrapper → stride_lint.py）
- `stride` CLI: `sdd-templates/bin/stride` （Python、`.venv/bin/python` 優先、なければ `python3`）
- `stride wi sync`: `python3 sdd-templates/tools/stride_wi_sync.py --feature <feature_id>` (GitHub Issues → work_items/WI-*.md 同期)
- PostToolUse guard: `sdd-templates/hooks/post_edit_guard.py` — Write/Edit 後に軽量 YAML/canonical 検証 (fail-open)

## 3. Phase Gate Hook Configuration (Claude Code 固有)

### 3.1 設定方法（推奨）

```bash
sdd-templates/bin/stride hooks --tool claude
```

### 3.2 手動設定（上記で失敗した場合）

`.claude/settings.json` に以下を追記:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/sdd-templates/hooks/phase_gate_hook.py\""
          }
        ]
      }
    ]
  }
}
```

この設定により、Write/Edit 操作が `specs/` 内のファイルに対して自動 Phase Gate チェックを実行し、
未承認の Phase ファイルをブロックする（fail-closed）。

### 3.3 他 AI ツール向けの同機能

- Cursor: `sdd-templates/bin/stride hooks --tool cursor`
- Copilot: `sdd-templates/bin/stride hooks --tool copilot`
- Manual checklist: `sdd-templates/bin/stride hooks --tool manual`

## 4. WI 管理（ハイブリッド方式、Claude Code 操作）

- **日常:** GitHub Issues で WI を管理（テンプレート: `.github/ISSUE_TEMPLATE/work-item.yml`、ラベル: `work-item` + `FEAT-<ID>`）
- **Gate 時:** `python3 sdd-templates/tools/stride_wi_sync.py --feature <feature_id>` でスナップショット生成（`specs/*/work_items/WI-*.md`）
- **ラベル→feature_id マッピング:** `sdd-templates/config/label_feature_map.json`
- **詳細:** `sdd-templates/docs/wi-management-guide.md`

## 5. Planning Rule — Auto-Invocation (Claude Code 固有)

> ユーザーレベル `~/.claude/CLAUDE.md` の Planning スキル設定が存在する場合、
> Claude Code は複雑タスクで `/planning` スキルを自動起動する。

### 自動起動条件（ANY 該当で起動）

1. 3 ファイル以上の変更が予想される
2. 3 ステップ以上の作業が必要
3. 未知の API / ライブラリ / コードベース領域の調査が必要
4. アーキテクチャまたは技術選定の判断が含まれる
5. 新機能実装（新しいエンドポイント / サービス / コンポーネントの追加）
6. 大規模リファクタリング（既存コード構造変更）
7. 原因不明のバグ調査

### 自動起動しない条件

- typo 修正、1-2 行の変更
- 単一ファイルの軽微な修正
- 明確な手順が既にわかっている小タスク
- ドキュメントの軽微な更新

### SDD 文脈統合

Run 実行中の Planning は **Run 内の `.planning/`** に保存する（ユーザーレベル Planning v5.0 と独立）。
詳細は `agent_docs/sdd_bootstrap.md` §6 (WI フロー 5, 8, 10, 12, 13 ステップ) 参照。

## 6. Amendment Phase（仕様改訂の Claude Code 操作）

仕様ライフサイクル全体は `agent_docs/sdd_guidelines.md §7` が SSoT。
Claude Code からの呼出しは以下:

### 6.1 自動トリガー（spec-impact 蓄積）

Execute Phase で spec-impact:required ラベル付き Issue が同一 Feature に **2 件以上** 蓄積:

```bash
python3 sdd-templates/tools/amendment_generator.py auto-check --feature <FEAT-ID>
```

→ ドラフト生成し PM に通知。

### 6.2 PM 主導トリガー（対話型）

1. `analyze --feature <FEAT> --topic <...>` — 影響分析（Findings / Decisions 収集）
2. 対話で PM に選択肢提示 → PM 確認後のみ Issue 作成
3. `create --feature <FEAT> --draft <file>` — Amendment Issue 作成 (`amendment:draft` ラベル)
4. **人間が承認チェックボックスを編集** — AI 絶対禁止
5. `apply --issue <N>` — Spec 更新 + spec-impact 解消 + Issue close
6. `finalize --issue <N>` — WI 作成 + finalize close

### 6.3 Claude Code 動作ルール

- Amendment Issue の**チェックボックス編集を AI が行うことは禁止**（INVIOLABLE）
- 対話中は PM の「これでよい」という明示的合意を取得してから Issue 作成する
- `.planning/` は gitignored → `analyze` は local のみ、`auto-check` は GitHub labels 経由

## 7. Symphony 連携（Claude Code = Design/Specify/Tasking ルーター）

Symphony オーケストレーション時、Claude Code は Phase 1-3 の担当エンジンとして起動される。
詳細設定は `SYMPHONY.md` を参照。Claude Code 側のコマンド形式:

```
claude -p --dangerously-skip-permissions
```

（SYMPHONY.md の `agent.claude_code.args` で定義）

## 8. Linear Integration (v5.3)

Linear を Run 証跡ボードとして併用する場合の Claude Code 固有ポイント。
詳細は `manual/37_linear_integration_guide.md` と `agent_docs/commands.md §12` を参照。

### 8.1 CLI と MCP の使い分け

| シチュエーション | 推奨 | 理由 |
|-----------------|------|------|
| Run フロー内の定型同期 | `stride linear <subcmd>` CLI | バッチ/スクリプタブル、CI 親和性、subprocess 実行 |
| 対話的な Issue 探索 / 手動更新 | `mcp__claude_ai_Linear__*` MCP | Claude Code セッション内の操作に最適、コンテキスト保持 |

### 8.2 自動モードの有効化

```bash
# .env.local
LINEAR_API_KEY=lin_api_xxx...
LINEAR_TEAM_KEY=TEC
STRIDE_LINEAR_AUTO=1
```

`STRIDE_LINEAR_AUTO=1` かつ `LINEAR_API_KEY` 設定時、`sdd_planning_bridge.py` の
`init` と `evidence` が完了直後に `linear_bridge.py` を subprocess で呼び出す。
失敗しても SDD 本体フローは停止しない（非致命的フォールバック）。

### 8.3 Linear を使わない運用

`LINEAR_API_KEY` 未設定なら全 `stride linear` コマンドが graceful skip（exit 0）。
既存ユーザーに影響なし、v5.3 は純粋な opt-in 機能。

---

## 9. Skills / Plugins との共存

本プロジェクトでは以下の skill/plugin 既定動作を**上書き**する:

- `superpowers:brainstorming` — SDD Intake-First モードが優先（`stride intake` が brainstorm の役割を担う）
- `superpowers:writing-plans` — SDD Planning Bridge が `.planning/` を管理（`sdd_planning_bridge.py init`）
- `superpowers:test-driven-development` — SDD では Phase 2 で scenarios.yaml / Phase 3 で test tasks を定義。厳密な先テスト原則は SDD の「Spec→Contract→Test」順序で代替
- `byterover:memory` — プロジェクト知識は `specs/<feature>/runs/<WI>/RUN-*/.planning/lessons.md` → `/planning:archive` → `~/.claude/knowledge/` の経路が正。brv curate は補助

優先順位詳細は `CLAUDE.md` の Instruction Precedence を参照。
