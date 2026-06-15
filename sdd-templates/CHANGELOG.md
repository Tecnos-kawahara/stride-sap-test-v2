# Changelog - sdd-templates (Tecnos Edition)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [6.0.1-tecnos-stride-extension-pack] - 2026-05-26

### Added — Extension Pack 機構の移植

v5.0.0 系で SAP 拡張パック（`extensions/sap/`）を実現するために追加されていた汎用 Extension Pack 検出・読込・lint 統合機構を、v6.0.0 本体に移植した。これにより `extensions/<ext>/` ディレクトリに拡張パックを配置し、`.stride-extensions.yaml` で有効化することで、STRIDE 本体を変更せずにドメイン固有の拡張（テンプレート上書き、追加バリデータ、Phase ワークフロー拡張）を横付けできる。

**背景:** v6.0.0 では ERP Addon 実行追跡（`erp_addon_exec_tracking.py`）と Upstream Extension lint（`upstream_lint.py`）が本体にハードコード import されている。Extension Pack 機構はこれらと共存し、MANIFEST.yaml の `tools[]` に登録された拡張バリデータを動的にロード・実行する汎用的な仕組みを提供する。既存のハードコード import は変更していない。

### 変更ファイル

- **`CLAUDE.md`** — Bootstrap セクション直後に「Extension Pack（MANDATORY）」セクションを追加。`.stride-extensions.yaml` の確認手順、`extensions/<ext>/CLAUDE_<EXT>.md` および `CLAUDE_WORKFLOW_<EXT>.md` の読込指示を記載
- **`agent_docs/sdd_bootstrap.md`**
  - §2 と §3 の間に §2b「拡張パック検出（MANDATORY）」を追加。`.stride-extensions.yaml` → `active_extensions` → 拡張ドキュメント読込手順を記載
  - §4 の Phase 1 / Phase 2 / Phase 3 / Phase 4 各冒頭に「⛔ 拡張パック確認」警告を追加。`CLAUDE_WORKFLOW_<EXT>.md` の該当 Phase の代替・追加ステップ適用を指示
- **`sdd-templates/tools/stride_lint.py`**
  - エラーメッセージ 3 件追加：`EXTENSIONS_NOT_CONFIGURED` / `EVIDENCE_PACK_EXTENSION_NOT_DEFINED` / `EVIDENCE_PACK_CATEGORY_MAPPING_MISSING`
  - `validate_artifact_registry()` 呼び出し直後に Extension Pack 検出コードを追加：`.stride-extensions.yaml` 読込 → `extensions/*/MANIFEST.yaml` パース → evidence_pack 設定検証（storage_key / category_mapping）→ 動的バリデータ関数ロード
  - `return result` 直前に Extension tool 実行コードを追加：ロード済みバリデータを `(feature_dir, approval_statuses, coverage_tier)` 引数で実行し、errors/warnings を結果に統合

### Extension Pack の利用方法

1. プロジェクトルートに `.stride-extensions.yaml` を作成：
   ```yaml
   active_extensions:
     - sap
   ```
2. `extensions/sap/MANIFEST.yaml` に拡張パック定義を配置：
   ```yaml
   extension:
     name: sap
     version: "2.0.0"
     evidence_pack:
       storage_key: sap_evidence
       category_mapping: templates/evidence_pack_category_mapping.yaml
     tools:
       - module: my_validator
         function: validate_my_feature
         trigger: always
   ```
3. `extensions/sap/CLAUDE_SAP.md` / `CLAUDE_WORKFLOW_SAP.md` に拡張固有ルール・ワークフローを記載
4. `stride lint` 実行時に MANIFEST.yaml の tools が自動ロード・実行される

### 既存コードへの影響

- `erp_addon_exec_tracking.py` のハードコード import（L2143-2172）：**変更なし**
- `upstream_lint.py` のハードコード import（L2174-2179）：**変更なし**
- 上記のハードコード import と Extension Pack 機構は共存する。将来的にこれらを MANIFEST.yaml 経由に統合する場合は、ハードコード import 側を削除して MANIFEST に登録する形で移行可能

---

## [5.4.0-tecnos-stride] - 2026-04-24

### Added — Reporting Lightening (Profile-Aware)

**スコープ:** 報告粒度と Completeness 閾値のみ。ガバナンス定義（14 Articles / BPMN / Evidence / SEC-006 / Ops Pack / Epic-Feature Hierarchy / Coverage Tier）は不変。

v5.2 の Opus 4.7 literal-follow 対応は ERP 領域で正しく機能する一方、連携業務 SaaS や社内プロトタイプでは報告の冗長さが過剰となっていた。v5.4 は「撤回ではなく軽量化」として、次の 3 点のみを追加する:

1. **Profile 軸の新設** — `enterprise-erp` (default) / `saas-integration` / `prototype` の 3 分類。報告粒度と湖/海判定閾値のみを切り替える
2. **`stride pr-check --summary-line`** — project-level の 1 行サマリ出力（7 base checks + optional mutation）
3. **Completeness Principle の Profile-aware 閾値** — 200/150/100 行 × 5/4/3 ファイル（AND）

### 追加ファイル

- `shared/policies/profile_policy.yaml` — 3 Profile 定義 + `invariants_across_profiles`（preserve_current + canonical_source 参照）
- `tests/test_profile_policy.py` — 20 tests（policy 構造、テンプレート schema、CLI --profile 伝搬で basic_design.profile と state.yaml top-level profile の両方を検証、再実行時の work_items/run_index 保持、pre-v5.4 state.yaml の profile 追記 upgrade、stride-lint PROFILE_* 検出）
- `manual/38_profile_guide.md` — Profile の選び方・切替方法・Case Study・v5.4 で切り替わらない項目の明示

### 変更ファイル

- `sdd-templates/bin/stride` — `stride init --profile <enterprise-erp|saas-integration|prototype>` フラグ追加（default `enterprise-erp` で既存挙動互換）。**init は basic_design.profile（SSoT）と state/state.yaml の top-level profile（キャッシュ）の両方を同時にセットする**。再実行時は既存 state.yaml の `work_items` / `run_index` を保持しつつ profile 行のみ更新する（P1 修正: 以前はキャッシュを作らなかったため後段の state.yaml 生成で PROFILE_MISMATCH ドリフトする穴があった）
- `sdd-templates/tools/stride_lint.py` — `KNOWN_PROFILES` + `check_profile_consistency()` 追加。新規エラーコード: `PROFILE_UNKNOWN` / `PROFILE_MISMATCH` / warning: `PROFILE_MISSING`
- `sdd-templates/tools/pr_readiness_checker.py` — `--summary-line` フラグ追加。project-level 1-line summary を出力（task ID / AC / NFR / scenarios は責務境界外で出力しない）。self-tests 10 → 12
- `sdd-templates/templates/basic_design_template.md` — `basic_design:` ブロック配下に `profile: "enterprise-erp"` 追加（`meta.*` ではなく `basic_design.*` 配下。linter 既存パスを再利用）
- `sdd-templates/templates/state_template.yaml` — top-level `profile: enterprise-erp` 追加（flat schema、`workspace.*` ネスト禁止）
- `agent_docs/sdd_bootstrap.md`
  - §4b Completeness Principle を Profile-aware 閾値 + 判定優先順位（risk_flags 最優先）に改訂
  - §5 Task Completion Checklist に §5.0 Profile-Dependent Reporting Matrix / §5.1 5-step full report / §5.2 1-line summary format + 合成ロジック + 分解テーブル / §5.3 Blocking rule を追加
  - Step 1-5 全実行を全 Profile で必須と明記（`AC + NFR + pr-check` の三要素縮約を明示的に禁止）
- `SDD_MANIFESTO.md` — Completeness Principle を Profile-aware に改訂。risk_flags 新規追加は Profile 不問で最優先「海」トリガー
- `specs/FEAT-ERPSAMPLE/basic_design.md` — `profile: "enterprise-erp"` を先頭に追加（サンプルを v5.4 schema に同期）
- `specs/FEAT-ERPSAMPLE/state/state.yaml` — top-level `profile: enterprise-erp` 追加
- `README.md` / `memory/constitution.md` / `sdd-templates/memory/constitution.md` / `sdd-templates/VERSION` — v5.4.0 反映
- `manual/38_profile_guide.md` — 新章追加

### 不変項目（ガバナンス保守）

- **14 Articles** (I〜XIV) 全て保持
- **Instruction Precedence 10 段ヒエラルキー** 不変
- **AI Action Boundary 3 分類** (MUST DO / MUST ASK / MUST NOT DO) 不変
- **lint 自動修正 loop bound** (最大 5 回 / 3-strike) 不変
- **§4-BPMN MUST-DO** (Camunda 8.8、14+9 Hard Requirements、ID スキーム) 不変
- **APPROVAL.md / WI-*.approval.md 編集禁止** 不変
- **ERP DB 直書き禁止 / 画面スクレイピング禁止** 不変
- **Execution Authority 宣言** (conversational / gated / prohibited) 不変
- **tier_mode_minimum** (critical は最低 confirm) 不変
- **SEC-006 AI Provenance キーワード 6 件** 不変

### Out-of-scope for v5.4（全 Profile で現行正本を維持 — preserve_current + canonical_source 参照）

- **BPMN 必須**: `agent_docs/sdd_bootstrap.md` §4-BPMN の現行ルール
- **Evidence Pack**: `memory/tecnos_org_constraints.md` §6.5 + `sdd-templates/templates/ops_template.md` の現行記述
- **SEC-006 Provenance**: `stride_security_checker` SEC-006 の現行 6 キーワード全記録
- **Epic-Feature Hierarchy**: Constitution Article X の現行ルール
- **Ops Pack**: `ops_pack_registry_template.yaml` + `epic_design_template.md` + `manual/` の現行条件
- **Coverage Tier 宣言**: `basic_design.coverage_tier` の現行ルール

上記を Profile 切替対象とする提案は v5.5 以降で別タスクとして起票する。v5.4 は**本プロンプト内で新規数値・条件を決め打ちしない**（canonical_source 参照で表現）。

### 責務境界（v5.4 重要）

- `stride pr-check --summary-line` は **project-level** のみ（7 base checks + optional mutation）
- Task-level 1-line（`✅ T-XXX-001: AC-* 全充足 / NFR OK / stride-lint PASS / pr-check PR_READY (coverage: <tier>)`）は AI が bootstrap §5 Step 1-5 の結果から合成
- Step 3 (scenarios) / Step 4 (stride-lint) の省略禁止

---

## [5.3.3-tecnos-stride] - 2026-04-17

### Fixed — BPMN Rule Compliance Enforcement

ultrathink 調査で `epic_flow.bpmn` / `process.bpmn` がルール通りに作成されない原因を
7 つ特定し、AI が literal に BPMN を生成できるようテンプレート設計を改善。機能追加なし、
既存 BPMN 作成機能の正常化のみ。

**根本原因（7つ）:**

1. FEAT template (`BPMN-TASK-001`) と EPIC template (`Task_A_Send`) の ID スキーム不統一 —
   AI が「どちらでもよい」と誤解して混ぜる
2. `sdd_bootstrap.md` の BPMN 指示が 1 行（process.bpmn）+ 1 行（epic_flow.bpmn）のみで
   MUST チェックリストなし → Opus 4.7 literal-follow 不十分
3. `bpmn_generator_rules.md` が 1017 行で AI が最初の要件だけ見て §16 Validation /
   §15 Naming 等をスキップ
4. EPIC template に `xmlns:xsi` 未宣言 + `isExecutable` 属性未明示 → Modeler 挙動不安定
5. `epic_validator.validate_epic_bpmn` が participant/collaboration のみチェックし
   内部 process の flow node incoming/outgoing / BPMNShape 完全性を未検証
6. `stride_lint.validate_bpmn` が sequenceFlow の sourceRef/targetRef の参照整合性を未検証
7. 「テンプレートをリテラルにコピー→プレースホルダ置換→増減」の明示がなく、
   AI が毎回ゼロから書こうとする

**v5.3.3 での対策:**

- **`agent_docs/sdd_bootstrap.md` に §4-BPMN セクション新設** — Phase 1 Design の下に
  BPMN Creation MUST-DO (Step 1-6) を追加。copy-template-literally 指示、FEAT/EPIC 決定
  ツリー、ID スキーム表、14+9 項目の Hard Requirements、top 失敗パターン、`stride lint`
  エラーコード早見表を literal-follow 向けに構造化。
- **`sdd-templates/docs/bpmn_quick_reference.md` 新規作成** — 1-page の AI 向け checklist。
  1017 行の `bpmn_generator_rules.md` を補完。決定ツリー / 14 MUST (FEAT) / 9 MUST (EPIC) /
  トップ失敗パターン / 検証フロー / エラーコード早見表。root `docs/` にもコピー。
- **`epic_flow_template.bpmn` 整合性修正:**
  - `xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"` を追加（FEAT と揃える）
  - `<bpmn:process isExecutable="false">` を明示（overview 用であることを明確化）
- **`epic_validator.validate_epic_bpmn` 強化** — FEAT と同等レベルに:
  - 内部 process の全 flow node に `<bpmn:incoming>` / `<bpmn:outgoing>`
  - `<bpmn:sequenceFlow>` の `sourceRef` / `targetRef` が process 内に実在
  - 全 flow node に `<bpmndi:BPMNShape>`、全 sequenceFlow に `<bpmndi:BPMNEdge>`
  - 違反時は `EPIC_BPMN_INVALID` error を発行
- **`stride_lint.validate_bpmn` 強化** — sequenceFlow の `sourceRef` / `targetRef`
  参照整合性チェックを追加（タイポ検出）。
- **`basic_design_template.md` に BPMN ID 一致ルール明記** —
  `bpmn_descriptions.elements[].bpmn_id` は `process.bpmn` 内の実 id と完全一致必須。

### Testing

- `stride_lint.py` — 既存 fixture (`sdd-templates/specs/sample_feature`, `specs/FEAT-ERPSAMPLE`)
  は BPMN 関連エラーなし (APPROVAL_PENDING / RUN_MULTIPLE 等の既存課題は変更なし)
- `epic_validator.py --test` — 全テストパス
- `epic_validator.py validate epics/EPIC-SAMPLE/` — 新 checks 全通過

### Changed files

- `agent_docs/sdd_bootstrap.md` (§4-BPMN 新設、version header 更新)
- `sdd-templates/docs/bpmn_quick_reference.md` (新規)
- `docs/bpmn_quick_reference.md` (新規, sdd-templates/docs/ からのコピー)
- `sdd-templates/templates/epic_flow_template.bpmn` (xsi 宣言 + isExecutable 明示)
- `sdd-templates/tools/epic_validator.py` (内部 process 検証追加)
- `sdd-templates/tools/stride_lint.py` (sourceRef/targetRef 検証追加)
- `sdd-templates/templates/basic_design_template.md` (BPMN ID 一致ルール明記)
- 15-file version bump checklist (VERSION, README, constitution, etc.)

---

## [5.3.2-tecnos-stride] - 2026-04-22

### Fixed — Template Scaffolding Bug Fixes

v5.3.1 テンプレクローン運用（tecnos-note プロジェクト初期化）で検出した 4 つの
bug を修正。機能追加なし、既存機能の正常化のみ。

- **`.claude/settings.json` の clean template 化**
  - 個人開発者の `entire hooks claude-code session-start` / `pre-task` /
    `post-task` / `user-prompt-submit` / `stop` / `post-todo` 等の呼び出しが
    tracked 状態だったため、git archive | tar でテンプレ展開した新規プロジェクト
    にも全て継承されてしまっていた。
  - personal hooks を `.claude/settings.local.json`（gitignored 済）へ退避、
    tracked `.claude/settings.json` は **Phase Gate hook (PreToolUse + PostToolUse)
    のみ** の clean state に。
- **`scripts/stride-new-project.sh` Step 4: Phase Gate hooks 常時 install**
  - 旧動作: `.claude/settings.json` がすでに存在すれば "Skipped" で終了
    → personal hooks が残ったまま Phase Gate hook は install されない。
  - 新動作: `stride hooks --tool claude --force` を常に実行。
    既存の非 Phase-Gate hooks（あれば）は merge で保持され、Phase Gate hook は
    確実に追加される。
- **Step 6 の exit-code-from-last-command bug 修正（GitHub Project + Linear Project 両方）**
  - 旧パターン: `if "$STRIDE_CLI" project create ... 2>&1 | sed 's/^/    /'; then`
  - Bug: shell pipeline の exit code は最後のコマンド (sed) のもの。sed は常に
    0 を返すため、`stride project create` が失敗しても if は true 扱いとなり
    「✓ GitHub Project bound」と**偽陽性表示**していた。
  - 新パターン: `OUT=$("$STRIDE_CLI" project create ... 2>&1); EXIT=$?; echo "$OUT" | sed ...`
    で exit code を捕捉してから判定。失敗時は正しく「failed (exit=N)」を表示。
- **Step 6 GitHub Project: `--org` / `GITHUB_OWNER` 未指定時の early graceful skip**
  - 旧動作: owner を指定せず `gh project create` を呼ぶと
    `owner is required when not running interactively` で必ず失敗していた。
  - 新動作: 事前に ORG_NAME / GITHUB_OWNER を判定し、未指定なら skip + 手動実行
    方法（`stride project create "<title>" --owner <owner>`）を案内。

### Verified

- `stride hooks --tool claude --force` で `.claude/settings.json` が Phase Gate
  hook のみの clean state になる（新規抽出 + 既存設定上書き両方で確認）
- `stride new-project <name> --dry-run` で:
  - `--org` 未指定 → GitHub Project を skip + 手動実行ヒント表示
  - `--org my-org` → `stride project create ... --owner my-org` を計画表示
- `stride new-project <name>` 実行時の Step 6 偽陽性が解消（exit code 正確反映）

### Version Bump Checklist (MEMORY.md)

VERSION / CHANGELOG / memory (6) / README (2) / id_conventions.yaml /
stride_lint_spec.md / bpmn_generator_rules.md / CI_CD + TEST_PATTERNS /
config/testing (8) / CLAUDE.md / CLAUDE_WORKFLOW.md / sdd_bootstrap.md /
CHEATSHEET.md / manual/_coverpage.md

---

## [5.3.1-tecnos-stride] - 2026-04-19

### Added — Per-Project Tracker Isolation

テンプレートをクローンして新プロジェクトを作る毎に、**Linear Project と GitHub
Project V2 を専用作成・binding する**仕組みを追加。v5.3.0 では Linear Issue を
作るたびに team backlog 直入れで、複数 STRIDE プロジェクトが混在していた問題を解消。

- **`stride linear project <create|list|use|status>`** サブコマンド群（linear_bridge.py 拡張）
  - `LinearClient.list_projects` / `find_project_by_name` / `create_project` GraphQL 追加
  - `memory/linear.yaml` 永続化（team_key / project_id / project_name / url）
  - 解決順位: CLI flag > `LINEAR_PROJECT_ID` env > `memory/linear.yaml` > none
- **`stride project <create|list|use|status>`** サブコマンド群（`sdd-templates/tools/github_project_bridge.py` 新設、~340 行）
  - `gh` CLI subprocess 経由（既存 `stride_wi_sync.py` と同パターン）
  - `memory/github_project.yaml` 永続化（owner / project_number / project_id / project_title / url）
  - 解決順位: `GITHUB_PROJECT_NUMBER` env > `memory/github_project.yaml` > none
  - 10 offline self-tests（`--test`）
- **`stride new-project` Step 6/7 拡張** — 新プロジェクト初期化時に両 tracker を自動作成
  - 新フラグ: `--linear-project <name>` / `--github-project <title>` / `--no-linear-project` / `--no-github-project`
  - デフォルト: プロジェクト名から自動導出（`<name>` → Linear Project、`<title> SDD Board` → GH Project）
  - 認証未設定（`LINEAR_API_KEY` 欠落 / `gh auth` 未ログイン）は **graceful skip**、既存フロー不停止
- **`tests/test_github_project_bridge_integration.py`** 新設（8 integration tests）
- **`tests/test_linear_bridge_integration.py`** — 既存のまま + Linear Project サブコマンドは self-tests (linear_bridge --test) でカバー
- **`memory/linear.yaml.example` / `memory/github_project.yaml.example`** — schema ドキュメント
- **`manual/37_linear_integration_guide.md` §11** — Per-Project Linear Project 自動作成 の完全ガイド
- **`agent_docs/commands.md`** — Linear Project 管理セクション + 新規 §13 GitHub Project V2 Integration

### Changed

- `sdd-templates/bin/stride` — `stride project` dispatch 追加、`stride linear --help` に project サブコマンド行、`show_help` に project/linear project 記述
- `sdd-templates/tools/linear_bridge.py` — `cmd_init` 内で `resolve_project_id(repo_root)` を使用、`memory/linear.yaml` から project_id を自動解決
- `scripts/stride-new-project.sh` — Step 数を 6 → 7 に拡張（External tracker bindings を挿入）

### Design Decisions

- **別々の SSoT ファイル**: `memory/linear.yaml` と `memory/github_project.yaml` を独立ファイル化
  （単一責任、binding 有無を個別に管理可能）
- **`gh` CLI subprocess**: 新規 Python 依存を増やさず、既存 `stride_wi_sync.py` と同パターン
- **既存メカニズムとの共存**:
  - `state.yaml` `work_items[].linear_issue_id` は **feature 単位**（per-WI）
  - `memory/*.yaml` は **project 単位**（どの Linear Project / GitHub Project に紐付くか）
  - 併用で階層的な trackability を実現
- **冪等性**: `create` は既存 Project を検索して再利用（同名二重作成を防止）

### Verified

- `linear_bridge --test`: 19/19 PASS（offline、project CRUD を含む）
- `github_project_bridge --test`: 10/10 PASS（offline、mock gh）
- `tests/test_linear_bridge_integration.py`: 10/10 PASS
- `tests/test_github_project_bridge_integration.py`: 8/8 PASS（新規）
- `stride linear project --dry-run create "test"`: 動作確認
- `stride project --dry-run create "test"`: 動作確認
- `stride new-project test --dry-run` Step 6/7 が両 tracker を順に呼出し確認
- Memory SSoT (root ↔ sdd-templates) 完全同期

---

## [5.3.0-tecnos-stride] - 2026-04-19

### Added

- **Linear Integration** — Run 成果物 (findings / walkthrough / test_results / lessons) を Linear Issue に同期する新規ブリッジ
  - `sdd-templates/tools/linear_bridge.py` (~500 lines, urllib-based GraphQL、**外部依存ゼロ**)
    - `LinearClient` — GraphQL POST クライアント（get_team / list_workflow_states / find_issue_by_wi / create_issue / add_comment / transition_issue）
    - Dataclasses: `LinearTeam`, `LinearWorkflowState`, `LinearIssue`, `SyncResult`
    - 7 subcommands: `init` / `findings` / `evidence` / `learn` / `sync` / `close` / `status`
    - Idempotent: `find_issue_by_wi` が `[WI-XXX]` タイトル prefix で既存検索、重複作成を回避
    - state.yaml の `work_items[].linear_issue_id` フィールドを SSoT として管理
    - **19 offline self-tests**（`--test` で mock Linear API、network 不要）
  - `stride linear <subcmd>` CLI 統合（`sdd-templates/bin/stride` に dispatch + help）
  - `tests/test_linear_bridge_integration.py` — **10 integration tests**（subprocess 経由、GH/Linear 未接続環境で hermetic）
- **Planning Bridge Linear Hook** — `STRIDE_LINEAR_AUTO=1` 設定時、`sdd_planning_bridge.py` の `init` / `evidence` が Linear を自動呼出し（非致命的フォールバック、失敗時 SDD フロー不停止）
- **manual/37_linear_integration_guide.md** — エンドユーザー向け完全ガイド（API Key 取得 / CLI リファレンス / 推奨 workflow / GitHub-Linear ハイブリッド運用 / トラブルシュート / FAQ 全 10 章）
- **manual/_sidebar.md** — チャプター 37 追加
- **agent_docs/commands.md §12** — AI 向け Linear CLI SSoT（AI Behavior Rules 4 項目 + MCP fallback 指針）
- **agent_docs/sdd_bootstrap.md §6** — WI フローに `5b` / `10b` / `16b` の optional Linear ステップ追加
- **CLAUDE_WORKFLOW.md §8** — Claude Code 固有の CLI vs MCP 使い分け指針
- **state_template.yaml** — `linear_issue_id` フィールドのコメント例

### Configuration

- 認証: `LINEAR_API_KEY` env（未設定時 graceful skip, exit 0 — 既存フロー完全不変）
- 既定 Team: `LINEAR_TEAM_KEY=TEC` (Tecnos AI)
- 任意: `LINEAR_PROJECT_ID`（Linear Project 紐付け）
- 自動モード: `STRIDE_LINEAR_AUTO=1`

### Design Decisions

- **GitHub Issues ハイブリッド WI 管理と共存**: Linear 置換ではなく併用（GitHub=merge ゲート / Linear=実行証跡ボード）
- **依存追加せず urllib.request ベース**: プロジェクトの zero-deps 方針を維持（PyYAML は既存の optional 依存）
- **dry-run は API key 不要**: `--dry-run` 時は body-building + preview のみ、skip check をバイパス
- **`[WI-XXX]` タイトル prefix 規約**: Linear 側で手動 Issue 作成済でも `state.yaml` に `linear_issue_id` を手書きすれば紐付け可能

### Verified

- Default `pytest -q`: 568 passed / 1 skipped / 3 deselected (回帰なし、Linear integration 10 tests + v5.2.1 558 passed = 568)
- `stride linear --test`: 19/19 self-tests PASS（offline）
- 全ツール self-test PASS 継続
- Memory SSoT (root ↔ sdd-templates) 完全同期

---

## [5.2.1-tecnos-stride] - 2026-04-19

### Added

- **Symphony Agent Reproducibility** — `agent.claude_code` に明示的な実行制御パラメータを追加
  - `model: "claude-opus-4-7"` — Design/Specify/Tasking Phase の使用モデルを固定
  - `effort_level: "low"|"medium"|"high"|"xhigh"|"max"` — Claude Code `--effort` に伝播
  - `max_output_tokens: 65536` — `CLAUDE_CODE_MAX_OUTPUT_TOKENS` env で runner に伝播
  - `symphony/config.py` `ClaudeCodeAgentConfig` に 3 フィールド + `ConfigLoader._validate()` にバリデーション追加（VALID_CLAUDE_CODE_EFFORT_LEVELS ホワイトリスト + 非空文字列 + 正の整数）
  - `symphony/runner.py` `_build_claude_code_command()` / `_build_claude_code_env()` で実装
  - `symphony/tests/test_config.py` + `test_runner.py` に 4 新規テスト
  - SYMPHONY.md + SYMPHONY_template.md + manual/30_symphony_orchestration_guide.md に設定例と解説
- **SEC-006 AI Provenance Keywords 6 件追加** — AI trust boundary の provenance 記録項目を拡充
  - `record_provider_surface` — LLM プロバイダー表面（OpenAI/Anthropic/Gemini 等）
  - `record_model_id` — モデル識別子
  - `record_execution_settings` — temperature / top_p / effort 等の実行設定
  - `record_budget_controls` — token/cost 予算制御
  - `record_tokenizer_notes` — tokenizer 情報（サロゲート文字列・絵文字対応の注記）
  - `record_cyber_safeguards_status` — セーフガード有効状況（PII 検知器 / 出力フィルタ 等）
  - `sdd-templates/tools/stride_security_checker.py` `_PROVENANCE_ONLY_KEYWORDS` に 6 件追加
  - `memory/tecnos_org_constraints.md` + `sdd-templates/memory/tecnos_org_constraints.md` (SSoT sync) の `ai_usage_policy.provenance` セクションを 9 項目に拡充
  - `sdd-templates/templates/evidence_pack_template.md` + `plan_template.md` に provenance テンプレ反映
  - `specs/FEAT-ERPSAMPLE/plan.md` + `implementation-details/evidence_pack.md` にサンプル反映
  - `sdd-templates/specs/sample_feature/plan.md` + `implementation-details/evidence_pack.md` にサンプル反映
- **Post-release housekeeping** — v5.2.0 の仕上げ作業
  - `.entire/` を `.gitignore` に追加（tool session metadata 120MB / tracked 2 files untrack）
  - `specs/*/state/evaluator_latest.json` を `.gitignore` に追加（LLM run ごとに mutate される ephemeral ファイル）
  - `pyproject.toml` testpaths に `sdd-templates/tests` を追加（E2E suite が default discovery に入る）
  - `pyproject.toml` に `addopts = "-m 'not api'"` 追加（default pytest を hermetic に、554→558 passed / 3 deselected）

### Changed

- **Doc updates** — provenance + Symphony 再現性の連動反映
  - `agent_docs/security.md` — provenance セクション更新
  - `manual/07_practitioner_execution_guide.md` / `12_plan_guide.md` / `14_evidence_pack_guide.md` / `34_security_audit_guide.md` — provenance 拡張反映
  - `manual/30_symphony_orchestration_guide.md` — claude_code 詳細設定セクション追加、`stride symphony janitor` CLI サブコマンド、quick-ref 整合
  - `manual/index.md` quick reference に `stride symphony janitor` 2 行追加
  - `manual/33_integration_test_guide.md` — deselect vs skip の意味的区別を明示（`api` は default `-m 'not api'` で deselect、`skip` は runtime 判定）

### Fixed

- **`multi_model_evaluator.extract_canonical_yaml` public alias 復活** — YAML refactor で private にリネームしたため `symphony/tests/test_evaluator_core.py` の 14 tests が ImportError で失敗していたのを、1 行の後方互換 alias で解消
- **README test count drift 同期** — 558 → 562（unstaged テスト追加反映後の実体数）

### Verified

- Default `pytest -q`: **558 passed / 1 skipped / 3 deselected** (17.28s)
- 全ツール self-test PASS: shared_lib 8/8, harness_report 6/6, pr_readiness 10/10, wi_readiness 17/17, evidence_metrics 6/6, stride_health 6/6, amendment 61/61
- Memory SSoT (root ↔ sdd-templates) 完全同期

---

## [5.2.0-tecnos-stride] - 2026-04-17

### Added

- **`sdd-templates/tools/stride_shared_lib.py`** — Canonical YAML 抽出の共通ユーティリティ（8 self-tests）
  - `extract_canonical_yaml(path, *, section, strict)` / `extract_frontmatter_yaml(path)` / `find_all_canonical_blocks(path)` の高水準 API
  - `extract_yaml_blocks` / `extract_yaml_after_marker` / `extract_first_yaml_block` の低水準ヘルパ
  - 5 caller (stride_lint / multi_model_evaluator / sdd_planning_bridge / wi_readiness_checker / post_edit_guard) を書換え、重複実装を解消
- **`stride symphony <subcmd>`** — `bin/stride` から完全ディスパッチ統合
  - `run [--once] [--dry-run]` / `dispatch --issue N` / `status` / `validate` / `janitor [--dry-run]` の 5 subcommand
  - `agent_docs/commands.md §8` を stride CLI 経由に書換え
- **`tests/test_stride_symphony_dispatch.py`** — 5 dispatch テスト（dispatch/unknown-issue は GH_TOKEN 未設定時 skip）
- **`sdd-templates/tests/test_execution_authority_e2e.py`** — v4.6 Schema-Gated AI の E2E 14 テスト
  - Normal path (EA-1..4) / Failure path (EA-F1..5) / Janitor integration (JN-1..5)
  - `tmp_path` fixture で実 specs 汚染を回避
- **`docs/tuneup-2026-04-17/`** — Opus 4.7 literal-follow 対応の tune-up プロンプト集（5 task + README）

### Changed

- **Governance hardening for Opus 4.7 literal-follow precision:**
  - `CLAUDE.md` — Instruction Precedence 10 段階ヒエラルキー + 衝突解決例 4 種（Parallel/Batch/No-root/Test-first）
  - `agent_docs/sdd_bootstrap.md` — version header v5.0.0→v5.1.0-tecnos-stride、自動修正 loop bound（lint 最大 5 / pr-check 最大 3 / 3-Strike 停止）、Completeness Principle 4 条件数値基準、AI Action Boundary 3 分類表、タスク完了チェックリスト固定テンプレート、WI フロー 1-16 連番化
  - `SDD_MANIFESTO.md` — Completeness 4 条件湖判定、Phase 毎の lint loop bound 明記
  - `CLAUDE_WORKFLOW.md` — 全面書換え: bootstrap SSoT へ Phase 詳細を委譲、Claude 固有設定のみに限定
  - `SYMPHONY.md` — janitor=true がプロジェクト override である旨を明示コメント化
  - `sdd-templates/templates/SYMPHONY_template.md` — janitor セクション追加（safe default enabled=false、v5.1 で欠落していた箇所を補填）
  - `agent_docs/harness.md` — トリガー条件を machine-checkable に（score [70,85)、MUTATION_THRESHOLD=80、COVERAGE_DECAY_THRESHOLD_PCT=5.0）
  - `agent_docs/sdd_guidelines.md` — §6/§8 を bootstrap §5/§6 の SSoT ポインタ化
- **Manual consolidation (Option A)**: `manual2/` 全 32 files を `archive/manual2-2026-04-17/` へ退避。`manual/` を単一 SSoT として確定、`manual/_sidebar.md` に退避注記

### Fixed

- **`stride_harness_report.py` Test 6** — 「all controls present → FULL」失敗を修正、6/6 PASS へ
  - `agent_docs/harness.md` Harness Report 行に FULL 判定条件（8 controls 全配置 ∧ tests ∧ workflows の 3 AND）を明記
- **`multi_model_evaluator.extract_canonical_yaml` public alias 復活** — YAML refactor で `_canonical_yaml_text`（private）へ改名したため `symphony/tests/test_evaluator_core.py` が ImportError で 14 テスト失敗。1 行の後方互換エイリアスで解消
- **`pyproject.toml` testpaths に `sdd-templates/tests` を追加** — 新規 E2E スイート `test_execution_authority_e2e.py` がデフォルト pytest 収集対象外になっていた問題（収集数 544 → 558）を修正。`pytest` 単体実行および CI が 14 E2E テストを必ず実行するようになる
- **`pyproject.toml` default `addopts = "-m 'not api'"` を追加** — `symphony/tests/test_evaluator_live.py` の API 依存 3 テストが `.env.local` にキーがあるがプロバイダー到達不能な環境で `PROVIDER_ERROR` により失敗していた問題を修正。default `pytest -q` は hermetic（554 passed / 1 skipped / 3 deselected）に、API テストは明示的に `pytest -m api` で実行可能

### Verified

- Tune-up 影響範囲: **61 passed / 1 skipped**（GH_TOKEN 依存で skip、仕様通り）
- 全ツール self-test PASS: shared_lib 8/8、harness_report 6/6、pr_readiness 10/10、wi_readiness 17/17、evidence_metrics 6/6、stride_health 6/6、amendment 61/61
- `stride-lint specs/FEAT-ERPSAMPLE/` の baseline 不変（3 errors、回帰なし）
- Total pytest collection: **558 tests, 0 errors**（`testpaths` 修正後、default discovery で再現可能）
- Default `pytest -q`: **554 passed / 1 skipped / 3 deselected** — hermetic（API 到達性不要）
- `pytest -m api`: 3 tests collectable（開発者が API キーありで明示実行可能）

---

## [5.1.0-tecnos-stride] - 2026-04-07

### Added - Harness Maturity (Fowler-inspired)

- **Mutation Testing (opt-in)** — `pr_readiness_checker.py`
  - `mutation_check(project_root, threshold)` — cosmic-ray based mutation testing
  - `run_all_checks(..., include_mutation=False)` — extended with opt-in `--mutation` flag
  - `main()` — `--mutation` argument passthrough
  - `format_human_readable()` — dynamic `[idx/{total}]` display (no longer hardcoded to 7)
  - `MUTATION_THRESHOLD` env var (default 80) for project policy

- **Self-Review Loop** — `multi_model_evaluator.py`
  - `self_review_loop(review_packet, max_iters=3)` — re-examines borderline results for missed critical issues
  - `--review` flag — activates loop when primary score is in [70, 85)
  - Critical issues found in review are appended to `primary_result` and force `overall=FAIL`
  - `aggregate_results()` remains pure (no args/review_packet dependency)

- **Runtime Sensors** — `sdd-templates/tools/stride_health.py` (new)
  - `detect_dead_code()` — pylint W0611/W0612/W0613/W0614 on tools/
  - `detect_coverage_decay()` — compares current coverage vs `.coverage_baseline`
  - `COVERAGE_DECAY_THRESHOLD_PCT` env var (default 5.0)
  - `stride health <project_root> [--runtime] [--json]` CLI
  - 6 self-tests

- **Harness Coverage Report** — `sdd-templates/tools/stride_harness_report.py` (new)
  - 8 controls inventory (pr-readiness, stride-lint, spec-drift, security-checker, runtime-sensors, semantic-eval, phase-gate-hook, post-edit-guard)
  - `build_harness_report()` — coverage_pct, controls, gaps
  - `stride harness-report <project_root> [--json]` CLI
  - 6 self-tests

- **Janitor Proposals** — Symphony integration
  - `JanitorConfig` dataclass in `symphony/config.py` (enabled/interval_hours/exclude_recent_pr_days/risk_flags_exclude)
  - `SymphonyConfig.janitor` field with safe defaults (enabled=False)
  - `has_recent_pr(repo, feature_name, days)` in `symphony/tracker.py`
  - `create_janitor_issue(repo, feature_name, drift_report)` in `symphony/tracker.py`
  - `_run_janitor_scan()` in `symphony/cli.py` — interval-gated, autopilot+starter scope, Issue proposal only (no auto-PR)
  - `SYMPHONY.md` front-matter: `janitor:` config block added

- **Feedforward Guide** — `agent_docs/harness.md` (new)
  - Fowler-inspired explanation of feedforward/feedback/runtime sensors/janitor
  - Scale-level operation table (starter/standard/enterprise)
  - Quick reference CLI commands

- **5 new test files** (50 fixtures total, all `@pytest.mark.harness`)
  - `tests/test_harness_mutation.py` — 10 tests
  - `tests/test_self_review.py` — 10 tests
  - `tests/test_stride_health.py` — 10 tests
  - `tests/test_harness_report.py` — 10 tests
  - `symphony/tests/test_janitor.py` — 10 tests

### Changed

- `requirements-dev.txt` — added `cosmic-ray>=8.3`
- `pyproject.toml` — added `harness` pytest marker
- `sdd-templates/bin/stride` — added `health`, `harness-report` subcommands; updated pr-check help with `--mutation`
- `sdd-templates/bin/stride` header comment — added health/harness-report entries

---

## [5.0.0-tecnos-stride] - 2026-04-02

### Added

- **stride-lint CLI UX 改善** — clig.dev + Agent-Human Parity 原則準拠
  - `suggested_action` ヒントを text 出力に `→` 付きで表示
  - `--help` に examples セクションと exit codes ドキュメントを追加
  - `-o ndjson`: 1 feature = 1 行の NDJSON 出力（パイプフレンドリー）
  - `--plain`: TSV 出力（grep/awk/CI 向け）
  - `-o` ショートハンドフラグ（`gh`/`kubectl` と共通慣習）
  - TTY 判定カラー出力（`--no-color` / `NO_COLOR` 環境変数対応）
  - パス typo サジェスト（`difflib.get_close_matches`）
  - Canonical YAML 事前検証（lint 前に exit code 4 で早期検出）
  - JSON/NDJSON 出力にアクター情報追加（`STRIDE_ACTOR` 環境変数 / `meta.invocation_mode`）
  - 次ステップサジェスト（`stride auto-continue` / fix hints）
  - `--plain` vs `-o json/ndjson`、`--verbose` vs 機械可読出力の排他制御（exit code 2）
  - `agent_docs/commands.md` にエージェント向け Quick Reference セクション追加
  - `stride help` の lint セクションに新フラグ表示追加
  - 14 新規統合テスト（合計 475 テスト）

### Fixed

- `GATE_FAILED` の `suggested_action` が存在しない `gate` コマンドを案内していた問題を修正

---

## [4.9.0-tecnos-stride] - 2026-03-31

### Added

- **Completeness Principle** を `SDD_MANIFESTO.md` と `agent_docs/sdd_bootstrap.md` に追記
  - AI が「だいたい動く」で止めず「全ACを満たす」まで実装する思想的基盤
  - Inspired by gstack Boil the Lake principle (garrytan/gstack)

- **`stride security`** コマンド（`stride_security_checker.py`）
  - `--daily`: 軽量セキュリティチェック（confidence >= 8/10）
  - `--audit`: 総合セキュリティ監査（confidence >= 2/10）
  - OpenAPI security / authz_matrix / security requirements / secrets / audit-correlation / LLM trust boundary / SoD / data policy / org constraints / ERP direct write guard を確認
  - `--json` 出力対応、`--test` セルフテスト8件
  - Inspired by gstack /cso two-tier scan (garrytan/gstack)

- **`stride retro`** コマンド（`stride_retro.py`）
  - Feature / Epic レベルの定量ふりかえりレポート
  - Phase duration, WI統計, テスト, lessons, change events, bottleneck analysis
  - Epic は `epic_design.md` の feature 一覧を起点に集計
  - `--json` 出力対応、`--test` セルフテスト6件
  - Inspired by gstack /retro (garrytan/gstack)

- **LLM trust boundary** セクションを `agent_docs/security.md` に追加
  - Input validation, output verification, trust boundary, fallback/human escalation を明文化

- **セキュリティタグ自動注入** を `sdd_planning_bridge.py` の knowledge 検索に追加
  - `risk_flags` に authz / sod / pii / audit_log 等がある場合、セキュリティ知識を追加検索

---

## [4.8.0-tecnos-stride] - 2026-03-23

### Added

- **Database Lifecycle Management** — DB スキーマの設計後ライフサイクル管理を標準化
  - `basic_design.database` に `ssot_model`, `design_ssot`, `deployment_ssot`, `ai_metadata` セクション追加（後方互換、全フィールド optional）
  - `database_schema_gate_check.rules` に `all_tables_have_description`, `all_columns_have_description`, `description_coverage_min`, `migration_forward_only` 追加
  - `stride_lint.py` の `validate_database_schema()` に description 網羅率チェックを追加
    - `DATABASE_SCHEMA_MISSING_DESCRIPTION`（個別欠落: warning）
    - `DATABASE_SCHEMA_LOW_DESCRIPTION_COVERAGE`（網羅率不足: **error** — 品質ゲートとして機能）
  - `migration_tool` 選択肢に `drizzle`, `atlas` を追加（`basic_design_template.md` と `database_schema_template.yaml` の両方）
  - `spec_as_code.artifacts` に `schema_json` 型を追加（spec_template.md, 11_spec_guide.md, FEAT-ERPSAMPLE/spec.md）
  - `manual/31_database_lifecycle_guide.md` 新規作成（SSOTモデル選定、tbls導入、CI再生成、migration運用、AI/RAG向けメタデータ）
  - サンプル feature（FEAT-ERPSAMPLE）に新フィールドのデフォルト値を追加
- **Camunda 8.8 BPMN Refresh** — FEAT/EPIC の BPMN アーティファクトと説明整合ルールを標準化
  - `stride init <feature>` で `process.bpmn` を生成し、FEAT BPMN を executable `process` + `laneSet` の縦レイアウト標準へ更新
  - `stride epic init <EPIC_ID>` で `epic_flow.bpmn` を生成し、EPIC BPMN を `collaboration + participant(pool)` の overview 標準へ追加
  - `stride_lint.py` に BPMN structure / documentation / YAML 連動チェックを追加（`basic_design.md` の `bpmn_descriptions` と整合）
  - `epic_validator.py` に `epic_flow.bpmn` の軽量検証を追加（`epic_design.md` の `epic_flow_descriptions` と整合）
  - BPMN の説明正本方針を整理し、Canonical YAML を第1正本、`bpmn:documentation` を第2正本、`Text Annotation` を補足用途に明確化
  - User Task 標準例を `candidateGroups` 中心から `assignee` 中心へ更新
  - テンプレート、サンプル、ガイド、LLM dictionary を Camunda 8.8 ベースラインへ同期

### Changed

- `manual/_sidebar.md` に「データベースライフサイクル管理」を追加
- README / ガイドの BPMN セクションを FEAT `process.bpmn` と EPIC `epic_flow.bpmn` の役割分担に合わせて更新

---

## [4.7.0-tecnos-stride] - 2026-03-16

### Added

- **Enterprise Hierarchy CLI Integration** — Epic管理をstride CLIに統合
  - `config/enterprise.yaml` — Enterprise On/Off設定（デフォルト: Off、YAML正規パース）
  - `stride epic init <EPIC_ID>` — Epic作成（epic_design, EPIC_APPROVAL, DEPENDENCY_MANIFEST, OPS_PACK_REGISTRY, shared/contracts/ を一括生成）
  - `stride epic validate / gates / features / progress / list` — 既存ツール（epic_validator.py, epic_progress_aggregator.py）をCLIでラップ
  - `stride init <feature> --epic <EPIC_ID> [--team <TEAM_ID>]` — Feature作成時にepic_ref + team_idを自動設定（team_idはepic_design.mdから自動検出）
  - `stride lint --enterprise` — Feature lint時にstride_lint_enterprise.pyを自動呼び出し
  - `stride lint --all --enterprise` — 全Feature + 全Epic（epic_validator.py経由）を一括検証
  - Enterprise Off時は従来通りのフラットFeature構造で完全に動作（後方互換）

---

## [4.6.0-tecnos-stride] - 2026-03-11

### Added

- **Execution Authority（3層権限宣言）** — mode_policy.yaml に `execution_authority` セクション追加
  - conversational: AIが承認なしに自由に実行できる行為（6アクション）
  - gated: スキーマ検証（stride-lint/phase_gate/wi_readiness_checker）通過時のみ実行可能（4アクション）
  - prohibited: AIに実行権限がない行為・人間専用（6アクション）
  - Cook et al. (2026) arXiv:2603.06394「検証スコープスペクトラム」に基づく設計

- **Article XIV: Execution Authority Separation** — constitution.md に14条目を追加
  - AIの会話権限と実行権限を分離し、実行はスキーマ検証済みインターフェースを通じてのみ許可
  - 5ルール + 4判定基準を明文化

- **ed_cf_score** — basic_design_template.md に実行決定性/会話柔軟性スコアを追加
  - `execution_determinism: 4` (1-5), `conversational_flexibility: 3` (1-5)

- **wi_readiness_checker Check 8: Execution Authority** — WI mode と execution_authority 宣言の整合性検証
  - FAIL: WI mode が推奨 mode を下回り mode_override.reason 未指定
  - WARN: mode が推奨を下回るが mode_override.reason 指定あり
  - PASS: mode が推奨以上、または execution_authority 未宣言（レガシー互換）
  - セルフテスト 3件追加（14 → 17）

### Changed

- `SDD_MANIFESTO.md` — Execution Authority Separation セクション追加（3層テーブル + 検証スコープ）
- `manual/17_adaptive_execution_guide.md` — Execution Authority Declaration (v4.6.0) セクション追加
- `memory/constitution.md` — v4.6.0 (Fourteen Articles), amendment_history 更新

---

## [4.5.0-tecnos-stride] - 2026-03-04

### Added

- **BDD形式 `acceptance_criteria`** — tasks_templateに構造化受け入れ条件を追加
  - Given-When-Then形式でタスクの完了条件を機械可読に定義
  - `verification` フィールド: `automated` | `manual` | `hitl` で検証方法を明示
  - `escalation_trigger` フィールド: 認証/DB/外部依存/金銭/セキュリティ変更時に人間レビューを強制
  - 全9タスクにBDD受け入れ条件の記載例を追加

- **`escalation_triggers` セクション** — constitution.mdに新設
  - 5つのエスカレーション条件と理由を明文化
  - Gate 5でHITLレビューを自動要求するトリガー定義

- **BDD Lint ルール AC-001〜AC-005** — stride_lint_spec.mdに追加
  - AC-001: acceptance_criteria存在確認 (WARNING)
  - AC-002: BDD構造の完全性 (ERROR)
  - AC-003: verification値の妥当性 (ERROR)
  - AC-004: escalation_trigger設定の確認 (WARNING)
  - AC-005: automated比率の確認 (WARNING)

### Changed

- tasks_templateヘッダーに `bdd_mode`, `escalation_policy_ref`, `verification_matrix` を追加

### Notes

- `done_when` は後方互換性のため維持（非推奨にはしない）
- `bdd_mode: "required"` でAC-001はWARNING（移行期間中）

---

## [4.4.0-tecnos-stride] - 2026-02-15

### Added - AI Autonomous Execution

- **AI Autonomous Execution Model** — Claude Code が全作業の「実行者」(R) として自律実行
  - 人間は「承認者」(A) として APPROVAL.md 編集のみ
  - Feature ライフサイクル全体を指示なしで連続実行（init → design → specify → tasking → execute → final）
  - APPROVAL_PENDING / WI_APPROVAL_PENDING でのみ停止
  - lint FAIL（APPROVAL_PENDING 以外）は AI が自動修正して再実行
  - 承認依頼の標準形式を定義

### Changed

- `CLAUDE_WORKFLOW.md` — 全面書き換え: Operating Principle + AI Autonomous Execution Rules + 自動 Lint 実行ルール + Auto-Continue
- `SDD_MANIFESTO.md` — Enforced Workflow に `(AI auto)` / `(HITL)` ラベル付与、Execution Model 冒頭注記追加
- `agent_docs/sdd_guidelines.md` — AI Behavior Rules v4.4（自律実行ルール7項目 + 承認依頼形式 + 自動修正範囲）、Blocking Rule Note 追加
- `CLAUDE.md` — Quick Reference に Execution Model (v4.4) セクション追加

---

## [4.3.0-tecnos-stride] - 2026-02-14

### Added - PR Readiness Checker

- **PR Readiness Checker** — `pr_readiness_checker.py` 新規ツール
  - 7つのチェックを統合した PR 作成可否判定
    1. stride-lint: stride_lint import による lint 実行（APPROVAL_PENDING 除外）
    2. spec:drift: spec_drift_detector import によるドリフト検出
    3. tests: evidence_metrics_collector import によるテスト結果確認
    4. coverage: coverage_tier 自動判定（critical→90%, standard→80%, experimental→60%）
    5. walkthrough checklist: `[x]`/`[ ]` パース
    6. evidence_pack: 必須セクション検出
    7. TODO/FIXME: src/ スキャン（`--strict` でブロッキング）
  - `--json` で機械可読出力、`-v` で詳細表示、`--strict` で TODO を FAIL 扱い
  - `--coverage-threshold N` でカバレッジ閾値オーバーライド
  - `--test` で 10 件のセルフテスト
  - Exit codes: 0=PR_READY, 1=NOT_READY, 2=ERROR

- **`stride pr-check`** — stride CLI に PR readiness コマンド追加

### Changed

- `SDD_MANIFESTO.md` — PR Readiness Rule セクション追加
- `agent_docs/commands.md` — PR_READINESS_CHECK コマンド追加
- `agent_docs/sdd_guidelines.md` — Task Completion Checklist に PR readiness ステップ追加
- `README.md` — ツール一覧・バージョン履歴・ディレクトリ構成更新
- `manual/index.md` — 機能表・ツールコマンド追加
- `manual/_coverpage.md` — バージョン更新
- `roadmap.md` — PR Readiness Checker 完了項目追加

---

## [4.2.0-tecnos-stride] - 2026-02-14

### Added - Monorepo Default with Scale Levels + Living Spec Drift + Evidence Metrics

- **Monorepo をデフォルト化** — `stride init` は常に Turborepo 構成を配置（AI開発においてはMonorepo一択）
- **`--scale` フラグ** — スケールレベルで段階的に複雑度を選択
  - `starter` (デフォルト): turbo.json (build+test のみ), tsconfig.base.json, 簡易 CI
  - `standard`: Full Turborepo + vitest.workspace.ts + 差分実行 CI (lint, typecheck, test, test:coverage, test:contract, build)
  - `enterprise`: Standard + リモートキャッシュ + 完全差分実行 CI + Evidence Pack (90日保持)
  - Starter でも turbo.json + workspaces を配置 → standard/enterprise への自然な成長パス

- **sdd-templates/config/monorepo/** — Scale 別テンプレート
  - `turbo.starter.json` — Starter パイプライン (build+test)
  - `turbo.standard.json` — Standard パイプライン (全 SDD タスク)
  - `turbo.enterprise.json` — Enterprise パイプライン (Standard 同等、リモートキャッシュは CI 環境変数)
  - `tsconfig.base.json` — 共有 TypeScript 設定（全 Scale 共通）
  - `vitest.workspace.ts` — Monorepo テストワークスペース (standard/enterprise)
  - `github-actions/ci-starter.yml` — Starter CI (簡易)
  - `github-actions/ci-standard.yml` — Standard CI (差分実行 + ローカルキャッシュ)
  - `github-actions/ci-enterprise.yml` — Enterprise CI (リモートキャッシュ + Evidence Pack 90日)
  - `package.json.snippet` — workspaces 定義参照
  - `package-templates/` — パッケージ雛形 (lib, service)
  - `README.md` — Monorepo 設定ガイド

- **Spec Drift Detector** — `spec_drift_detector.py` 新規ツール
  - contracts/ の OpenAPI YAML と src/ のルート実装を比較
  - 検出種別: endpoint_not_implemented (critical), contract_outdated (high), schema_mismatch (medium), parameter_missing (medium)
  - `--json` で機械可読出力、`--verbose` で詳細表示、`--test` で6件のセルフテスト
  - CI 統合: `spec:drift` Turbo タスクとして standard/enterprise CI に追加

- **Evidence Metrics Collector** — `evidence_metrics_collector.py` 新規ツール
  - coverage-summary.json からカバレッジ率、JUnit XML/JSON からテスト結果を収集
  - Turbo キャッシュヒット率、APPROVAL.md Gate リードタイムを計算
  - `--json` で機械可読出力、`--test` で6件のセルフテスト
  - Enterprise CI に metrics 収集ステップ追加

- **codegen_config.yaml** — OpenAPI → TypeScript 型生成の設定テンプレート

- **metrics_trend** セクション — evidence_pack_template.md に追加
  - coverage_trend, test_time_trend, cache_hit_rate, gate_lead_time_hours, spec_drift_count

- **Turborepo Monorepo マニュアル** — `manual/appendix_turborepo_monorepo.md` 新規
  - Scale Levels / turbo.json / CI テンプレート / Spec Drift / トラブルシューティング

### Changed

- `SDD_MANIFESTO.md` — CI/CD Requirements (Monorepo) セクションを Scale 別に改訂、Living Spec Drift / Evidence Measurement セクション追加
- `sdd-templates/bin/stride` — `--monorepo` → `--scale` に変更、monorepo セットアップを常時実行
- `agent_docs/commands.md` — STRIDE_INIT に `--scale` オプション記載、SPEC_DRIFT_CHECK / EVIDENCE_METRICS コマンド追加
- `turbo.standard.json` / `turbo.enterprise.json` — `spec:drift` タスク追加
- `ci-standard.yml` / `ci-enterprise.yml` — Spec Drift Check ステップ追加
- `ci-enterprise.yml` — Evidence Metrics Collection ステップ追加
- `evidence_pack_template.md` — metrics_trend YAML + Metrics & Drift チェックリスト追加
- `README.md` — バージョン、機能テーブル、ディレクトリ構成、バージョン履歴更新
- `manual/` — coverpage, index, sidebar, evidence_pack_guide を v4.2.0 に更新

---

## [4.1.0-tecnos-stride] - 2026-02-08

### Added - Roadmap Optimization (Phase 6)

- **Auto-Continue Planner** — `auto_continue_runner.py` 新規ツール
  - `stride auto-continue specs/<feature>/` で次フェーズの実行シーケンスを生成
  - HITL チェックポイント（Gate承認）で停止するシーケンスを明示
  - `--json` で機械可読出力

- **Decision Index Manager** — `decision_index.py` 新規ツール
  - `shared/decisions/decision-index.md` を ADR ファイルから再生成
  - `stride decisions init|refresh` で運用可能

- **DDD Optional Scaffolding** — `stride ddd-init`
  - `implementation-details/domain_model.md` と `technical_design.md` を生成
  - 初回 ADR を `shared/decisions/ADR-*.md` に生成
  - Decision Index を自動更新

- **Mandatory Output Rules Command** — `stride output-rules`
  - PASS/FAIL/WARN/SKIP、[n/N]、no ASCII table ルールを表示

- **DDD/ADR Templates**
  - `templates/ddd_domain_model_template.md`
  - `templates/ddd_technical_design_template.md`
  - `templates/adr_template.md`

### Changed

- `sdd-templates/bin/stride` - `auto-continue`, `ddd-init`, `decisions`, `output-rules` コマンド追加
- `sdd-templates/templates/basic_design_template.md` - `delivery_model.type` に `ddd` 追加、`ddd_policy` セクション追加
- `agent_docs/sdd_guidelines.md` - Section 10-13（Auto-Continue, Output Rules, DDD, Decision Index）追加
- `agent_docs/commands.md` - v4.1 コマンド群を追加
- `SDD_MANIFESTO.md` - v4.1 運用ルール（Auto-Continue/Output/DDD/ADR）追記

---

## [4.0.0-tecnos-stride] - 2026-02-08

### Added - Multi-Tool Strategy

- **SDD_MANIFESTO.md** — ツール非依存のSDDコアルール
  - SSoT Hierarchy、Phase Gate Rules、Enforced Workflow、APPROVAL.md Rules、Post-Approval Change Rule
  - Claude Code、Cursor、Copilot、その他のAIツールで共通利用可能

- **CLAUDE_WORKFLOW.md** — Claude Code 固有の設定
  - Agent Docs 読み込み順序、Tooling Setup、Phase Gate Hook Configuration、Planning Rule

- **stride hooks --tool** — マルチツールアダプター
  - `--tool claude` (default): `.claude/settings.json` PreToolUse hook
  - `--tool cursor`: `.cursor/rules/phase-gate.md` ルール生成
  - `--tool copilot`: `.github/copilot/phase-gate.md` 指示ファイル生成
  - `--tool manual`: `docs/phase-gate-checklist.md` 手動チェックリスト

### Changed

- `CLAUDE.md` — SDD_MANIFESTO.md + CLAUDE_WORKFLOW.md の参照に簡素化（ByteRover 部分は維持）
- `sdd-templates/bin/stride` — `hooks --tool` サブコマンド追加、help 更新
- `agent_docs/commands.md` — STRIDE_HOOKS に `--tool` オプション記載

---

## [3.3.0-tecnos-stride] - 2026-02-08

### Added - Brownfield & Auto-Init

- **Brownfield Detector** — `brownfield_detector.py` 新規ツール
  - プロジェクトルートのマニフェスト解析（package.json, pyproject.toml, go.mod, Cargo.toml, pom.xml, build.gradle, composer.json）
  - 検出項目: プロジェクト種別（greenfield/brownfield）、構造（monolith/monorepo）、言語、フレームワーク、テストフレームワーク
  - `--json` で機械可読出力、`--test` で8件のセルフテスト

- **stride init --detect** — 既存プロジェクトスタック自動検出
  - Brownfield Detector をテンプレート初期化時に実行
  - 検出結果を `implementation-details/brownfield_detection.json` に保存
  - `delivery_model` を自動設定（brownfield → requirement_driven, greenfield → fit_to_standard）

### Changed

- `sdd-templates/bin/stride` - `--detect` フラグ追加、help にBrownfield検出例追加
- `agent_docs/commands.md` - BROWNFIELD_DETECT コマンド追加、STRIDE_INIT に `--detect` 記載

---

## [3.2.0-tecnos-stride] - 2026-02-08

### Added - Operational Maturity

- **Walkthrough Review Checklist** — `walkthrough_template.md` に構造化レビューチェックリスト追加
  - Security（秘密情報、入力検証、SQLインジェクション、エラーリーク）
  - AC Coverage（spec_refs全AC検証、scenarios.yaml全expected検証、NFRエッジケース）
  - Code Quality（未使用コード、関数/ファイルサイズ、命名規約）

- **Phase Quick Reference TOC** — `sdd_guidelines.md` 冒頭にフェーズ別目次追加
  - 各Phase（Design/Specify/Tasking/Execute）で参照すべきセクションを一覧表示

- **GitHub Actions Dashboard Template** — `github-actions/epic-progress-report.yml`
  - 平日9時自動実行、HTML/Markdownダッシュボード自動生成・コミット
  - `sdd-templates/templates/github-actions/` に配置

- **Planning Evidence in Evidence Pack** — `evidence_pack_template.md` に Planning 参照追加
  - Canonical YAML に `planning_evidence` セクション追加
  - Required Evidence Checklist に Planning Evidence チェック項目追加

### Changed

- `agent_docs/sdd_guidelines.md` - Phase Quick Reference テーブル追加、Review Checklist ルール追加
- `sdd-templates/templates/walkthrough_template.md` - Review Checklist セクション追加
- `sdd-templates/templates/evidence_pack_template.md` - Planning Evidence 参照追加
- `manual/21_pm_dashboard_guide.md` - GitHub Actions テンプレート参照追加

---

## [3.1.0-tecnos-stride] - 2026-02-07

### Added - Adaptive Execution

- **Autonomy Bias System** — プロジェクトレベルのMode調整メカニズム
  - `shared/policies/mode_policy.yaml` に `autonomy_bias` セクション追加
  - `state_template.yaml` に `autonomy_bias` フィールド追加
  - `basic_design_template.md` に `autonomy_bias` 設定追加
  - autonomous/balanced/controlled の3段階でチェックポイント量を調整
  - tier_mode_minimum による下限保証（critical tier は常に最低 confirm）
  - `wi_readiness_checker.py` がBias考慮のMode判定を実行

- **Run Resume Detection** — 中断Run自動再開検出
  - `run_resume_detector.py` — アーティファクト存在チェックによる再開ポイント検出
  - walkthrough.md/test_results.md/.planning/ の存在で再開フェーズ判定

### Changed

- `agent_docs/sdd_guidelines.md` - Autonomy Bias ルール追加、Resume Detection ルール追加
- `agent_docs/commands.md` - DETECT_RUN_RESUME コマンド追加、Workflow を v3.1 に更新
- `sdd-templates/templates/basic_design_template.md` - autonomy_bias フィールド追加

---

## [3.0.1-tecnos-stride] - 2026-02-07

### Added - Planning Integration for Run Execution

- **Run内Planning証跡** - AI計画・調査・学習の監査証跡をRun内に保存
  - `walkthrough_template.md` に "Planning Evidence" セクション追加
  - `.planning/` (plan.md, findings.md, lessons.md) を各Run内に格納
  - Run開始時に `/planning` 自動実行、完了時に `/planning:archive` でグローバル知識保存

### Changed

- `agent_docs/sdd_guidelines.md` - Section 9 追加 (Run実行時Planning自動統合)
- `agent_docs/sdd_guidelines.md` - Section 7 AI Behavior Rules に Planning ルール追加
- `agent_docs/commands.md` - START_RUN_PLANNING / ARCHIVE_RUN_PLANNING コマンド追加
- `agent_docs/commands.md` - ERP Addon Workflow を Planning統合版に更新

---

## [3.0.0-tecnos-stride] - 2026-02-07

### Added - STRIDE Multi-Team Edition

- **PM進捗ダッシュボード** - Epic横断でチーム進捗を一元管理
  - `epic_progress_report_template.md` - PM週次レポートテンプレート
  - `team_status_report_template.md` - チームリード報告テンプレート
  - `epic_progress_aggregator.py` - Epic進捗集約ツール
    - `--format summary` - ターミナル表示（デフォルト）
    - `--format json` - JSON出力（CI/CD連携用）
    - `--format markdown` - EPIC_DASHBOARD.md自動生成

- **WI実行準備チェッカー** - Run実行前の自動検証
  - `wi_readiness_checker.py` - Gate/Mode/依存/Ops/State検証
    - Gate 5承認、Mode Policy準拠、Pre-run承認、依存充足、Ops Pack確認

- **共有契約レジストリ** - 契約バージョン・消費者を一元追跡
  - `shared_contract_registry_template.yaml` - 契約レジストリテンプレート

- **チーム間依存マニフェスト** - blocking/soft依存を明示追跡
  - `cross_team_dependency_manifest_template.yaml` - 依存マニフェストテンプレート

- **Opsパックレジストリ** - ERP Ops準備状況を一元管理
  - `ops_pack_registry_template.yaml` - Ops準備追跡テンプレート

- **Organization Modeポリシー** - Tier×Mode制約を組織レベルで定義
  - `shared/policies/mode_policy.yaml` - Mode最低要件・エスカレーション

- **Article XIII: PM Progress Visibility** - Constitution新条項
  - PMがEpic横断で進捗・ブロッカー・リスクを把握する権利と義務
  - Epic Progress Gate追加（チーム報告、依存追跡、契約レジストリ）

### Changed

- **Twelve Articles → Thirteen Articles** - STRIDE拡張1条追加
  - Article XIII: PM Progress Visibility
- **Constitution version** - 2.0.0-tecnos-enterprise → 3.0.0-tecnos-stride
- **VERSION** - 2.1.0-tecnos-enterprise → 3.0.0-tecnos-stride
- **commands.md** - Section 6: Multi-Team Progress Managementコマンド群追加
- **sdd_guidelines.md** - Section 8: Multi-Team Progress Management ルール追加

### Documentation

- **manual/20_multi_team_guide.md** - マルチチームコラボレーションガイド
- **manual/21_pm_dashboard_guide.md** - PMダッシュボードガイド

---

## [2.0.0-tecnos-enterprise] - 2026-01-20

### Added - Enterprise Edition

- **Epic/Feature階層** - 大規模要件をEpic → Featureに分解、チーム横断で管理
  - `epic_design_template.md` - Epic設計テンプレート
  - `feature_breakdown_template.md` - Feature分割テンプレート
  - `EPIC_APPROVAL.md` - Epic Gate承認記録
  - `epic_validator.py` - Epic構造検証ツール

- **3段階カバレッジTier** - critical/standard/experimentalで品質要求を階層化
  - `coverage_tiers.yaml` - Tier別カバレッジ定義
  - basic_design.mdに`coverage_tier`フィールド追加

- **委任承認マトリクス** - TierとGate種別に応じた承認者自動ルーティング
  - `approval_matrix_template.yaml` - 承認マトリクス定義
  - `approval_router.py` - 承認ルーティングツール
    - `route` - 必要な承認者とCo-Approverを表示
    - `validate` - can_approve/escalation/co-approverの3層検証
    - `parallel` - Gate並列処理可否判定
    - `--json` - CI/CD連携用JSON出力

- **エスカレーションルール** - 条件に応じた自動エスカレーション
  - `coverage_tier == 'critical'` → ARCH_BOARD
  - `cross_team_dependency == true` → ARCH_BOARD
  - `shared_contract_change == true` → ARCH_BOARD
  - `security_sensitive == true AND coverage_tier == 'critical'` → SECURITY_OFFICER
  - `erp_integration == true` → ARCH_BOARD

- **共有契約レイヤー** - チーム間API/Event契約を一元管理
  - `shared_contract_template.yaml` - 共有契約テンプレート
  - `CONSUMERS.yaml` - 契約利用者一覧
  - `cross_refs_template.yaml` - クロスリファレンス定義

- **依存管理** - チーム間依存のサイクル検出・可視化
  - `dependency_manifest_template.yaml` - 依存宣言テンプレート
  - `dependency_checker.py` - 依存サイクル検出、DOTグラフ生成
  - `dependency_rules.yaml` - 依存関係ルール

- **契約変更提案（CCP）ワークフロー** - 破壊的変更の承認フロー
  - `ccp_template.md` - 契約変更提案テンプレート
  - 影響分析、消費者通知、ARCH_BOARD承認

- **Enterprise Lint** - Epic参照、Tier検証、共有契約検証
  - `stride_lint_enterprise.py` - Enterprise拡張Lint

- **エスカレーションフラグ** - basic_design.mdに追加
  - `security_sensitive` - PII/認証/暗号化処理フラグ
  - `erp_integration` - ERP連携フラグ

### Changed

- **Nine Articles → Twelve Articles** - Enterprise拡張3条追加
  - Article X: Epic-Feature Hierarchy
  - Article XI: Tiered Quality
  - Article XII: Contract-First Coordination

- **ID規約拡張** - Enterprise ID追加
  - `EPIC-[A-Z]{3,}` - Epic ID
  - `TEAM-[A-Z]{1,3}` - Team ID
  - `SC-(API|EVT|FILE)-[A-Z0-9]{3,}` - Shared Contract ID
  - `CCP-[0-9]{3}` - CCP ID

### Documentation

- **manual/15_enterprise_guide.md** - Enterprise Edition完全ガイド
- **README.md** - Enterprise Edition概要、クイックスタート

---

## [1.2.6-tecnos] - 2026-01-19

### Changed

- **Directory renamed** - `templates_v1.2.5-tecnos/` → `sdd-templates/`
  - Version-agnostic directory name eliminates need for path updates on version changes
  - All internal path references updated accordingly

- **Version management overhaul**
  - Added `VERSION` file as single source of truth for template version
  - `stride` now reads version from `VERSION` file dynamically
  - Template files use `{{TEMPLATE_VERSION}}` placeholder, replaced during `stride init`
  - Future version upgrades require only: 1) Edit `VERSION`, 2) Add CHANGELOG entry

- **Removed CBP references** - Removed Composable Business Platform (CBP) terminology from templates
  - `target_state`, `cbp_alignment` fields removed from basic_design template
  - `target_domains` simplified in plan template

### Fixed

- **Phase Gate hook auto-configuration** - Now automatically enabled during `stride init`
  - Robust JSON validation for `.claude/settings.json` merge
  - Handles empty, invalid, non-dict JSON gracefully
  - Validates `hooks.PreToolUse` structure before merge
  - Detects existing `phase_gate_hook.py` to prevent duplicates
  - Clear error messages for canonical config issues
  - Conditional "hooks active/NOT active" messaging based on configuration success
  - Lite Mode gate naming (A/B/C) in post-init messages

---

## [1.2.5-tecnos] - 2026-01-07

### Fixed

- **Python E2E artifact path resolution** - Changed from relative paths (`../reports/e2e`) to `Path(__file__)` based paths
  - `e2e.spec.template.py` and `conftest_e2e.template.py` now use file-relative paths
  - Ensures correct artifact output regardless of CWD when running pytest
  - Uses `Path(__file__).parent.parent / "reports" / "e2e"` for consistent resolution

- **Approval sample format consistency** - Fixed all manual samples to use correct Japanese labels
  - Changed `Approver:` / `Date:` to `承認者:` / `日付:` to match stride-lint validation
  - Affected files: `manual/10_stride_lint.md`, `manual/11_troubleshooting.md`, `manual/appendix_web_edi_tutorial.md`

- **Gate header consistency** - Fixed all gate headers in manual samples to match stride-lint expectations
  - `Gate 2: BPMN` (not "BPMN Flow")
  - `Gate 3: Spec` (not "Spec Review" or "Specification")
  - `Final: Implementation` (not "Final Gate")

- **Lite Mode gate headers** - Fixed to match official template format
  - `Gate A: Design & Flow` (not "Design & BPMN")
  - `Gate C: Implementation & Verification` (not "Tasks & Final")

- **Playwright report path** - Added explicit path to `npx playwright show-report` commands
  - `npx playwright show-report specs/<feature>/tests/reports/e2e/playwright-report`

---

## [1.2.4-tecnos] - 2026-01-06

### Added

- **stride CLI** (`bin/stride`) - New unified command-line tool
  - `stride init <feature>` - Initialize feature with all templates
  - `stride lint <path>` - Run linting (replaces long Python path)
  - `stride phase-status` - Show Phase Gate approval status
  - `stride phase-check <file>` - Check if file creation is allowed
  - `stride hooks` - Setup Phase Gate hooks automatically (replaces setup_hooks.py)
  - `stride help` - Show usage information

- **Lite Mode** - 3-stage approval workflow for small projects/PoC/solo development
  - `APPROVAL_LITE.md` template with Gate A, B, C (replaces 6-stage workflow)
  - `stride init --lite` - Initialize feature with Lite Mode approval template
  - `stride lint --lite-mode` - Lint with Lite Mode gate mapping
  - Auto-detection: If APPROVAL.md contains "Gate A:" or "Lite Mode", treated as lite

- **5-Language Test Tools** - Python, TypeScript, Rust, Go, Java support
  - `config/testing/` directory with language-specific configurations
  - `manual/12_language_test_tools.md` - Comprehensive guide

- **Docsify Manual** - Web-based searchable documentation
  - `manual/index.html` - Docsify entry point
  - `manual/_sidebar.md` - Navigation sidebar
  - All chapters accessible via `npx docsify-cli serve manual/`

- **Python E2E Templates**
  - `templates/tests/e2e.spec.template.py` - pytest-playwright test template
  - `templates/tests/conftest_e2e.template.py` - E2E fixtures

- **Playwright templates** - TypeScript E2E test scaffolding
  - `playwright.config.template.ts` - Playwright configuration with evidence output
  - `e2e.spec.template.ts` - Test file template with AC traceability annotations
  - Automatically copied by `stride init` to `tests/e2e/`

- **ops_template.md** - Operations baseline template for audit/SoD/monitoring requirements

- **openapi_template.yaml** - OpenAPI 3.1 skeleton template for API contracts

- **Post-Approval Change Detection** - `POST_APPROVAL_CHANGE` warning when files are modified after gate approval

- **COUNTS_MISMATCH / COUNTS_SUGGESTION** - Improved count validation with copy-paste ready correct values

- **Default Coverage Summary** - Brief coverage stats shown in every lint run
  - Format: `Coverage: ✓ AC 5/5 (100%)  ○ CT 2/3 (66.7%)`
  - ✓ indicates full coverage, ○ indicates incomplete
  - Full report still available with `--coverage-report` flag

- **E2E_TAG_OVERUSE** warning - Alerts when too many ACs are tagged with `e2e`
  - Triggers when e2e count > 5 or > 20% of total ACs
  - E2E tests are expensive; this encourages limiting to critical user journeys

- **ID conventions config** (`config/id_conventions.yaml`) - Centralized ID pattern definitions
  - All ID patterns documented in YAML format
  - `load_id_conventions()` function for programmatic access
  - Foundation for future ID validation enhancements

- **CI/CD Integration Guide** (`docs/CI_CD_INTEGRATION.md`)
  - GitHub Actions, GitLab CI, Azure DevOps examples
  - Phase gate deployment strategies
  - Evidence pack automation
  - Coverage threshold enforcement

### Changed

- **phase_gate.py** - Added clarifying comments for Phase 4 definition (no logic change)

- **compare_counts()** - Enhanced to show correct values in YAML format for easy copy-paste

- **QUICKSTART.md** - Updated to use `stride init` as the recommended approach

- **CHEATSHEET.md** - Added new error codes documentation

### Fixed

- **macOS sed compatibility** - Added OS-specific sed command examples in QUICKSTART.md

- **Feature ID validation** - Hyphens/underscores removed to comply with constitution regex `^FEAT-[A-Z0-9]{3,}$`

- **Feature ID length validation** - Error on feature IDs shorter than 3 characters

### Deprecated

- Direct execution via `python3 templates_v1.2.x-tecnos/tools/stride_lint.py` - Still works but `stride lint` is preferred

---

## [1.2.3-tecnos] - 2025-12-31

### Added

- HITL Approval System with APPROVAL.md
- Phase Gate enforcement (phase_gate.py)
- Evidence Pack template and validation
- Spec-as-Code artifact validation
- E2E test reporting and triage workflow
- Tagged AC coverage enforcement (integration, e2e)

### Changed

- Enhanced stride-lint with approval checking
- Updated templates for Tecnos enterprise requirements

---

## [1.2.2-tecnos] - 2024-12-15

### Added

- Basic Design Gate with RACI+ and delivery model
- BPMN Camunda 8 (Zeebe 8.8) validation
- Tecnos org constraints integration

---

## [1.2.1-tecnos] - 2024-12-01

### Added

- Initial Tecnos enterprise edition
- stride-lint tool
- SDD workflow templates
- Nine Articles (constitution.md)
