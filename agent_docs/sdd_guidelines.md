# SDD Guidelines (Tecnos)
# Purpose: govern workflow and minimum quality bar.

## Phase Quick Reference

> 現在のPhaseに応じて、該当セクションを優先的に参照すること。§1-§2 は全Phase共通。

| Phase | Sections | Key Flow |
|-------|----------|----------|
| Design | §1, §2, §3, §4 | basic_design → BPMN → lint → Gate 1,2 承認待ち |
| Specify | §1, §2, §5 | spec → plan → contracts → lint → Gate 3,4 承認待ち |
| Tasking | §1, §2, §6 | tasks → lint → Gate 5 承認待ち |
| Execute | §1, §2, §7, §8, §9 | WI → Run → test → walkthrough → approval → state.yaml |

## 1) High-impact review criteria (review required)
- Changes to `process.bpmn` or integration flows.
- New or modified contracts (CT-*) or public interfaces.
- AI policy, RACI+, or Evidence Pack changes.
- Exceptions to `memory/constitution.md` or `memory/tecnos_org_constraints.md`.
- E2E scope changes (e2e-tagged ACs).

## 2) Quality bars (minimum)

### basic_design.md must have:
- At least 1 traceability row and 1 integration flow.
- `delivery_model` and RACI+ defined.
- AI policy and artifact registry linked.
- Blocking questions resolved before `ready_for_bpmn = true`.

### spec.md must have:
- >= 1 use case, >= 3 AC, >= 1 integration-tagged AC.
- NFRs include integration, data, and security (>= 1 each).
- `spec_as_code` artifacts listed with valid paths.
- No blocking open questions before `ai_plan_ready = true`.

### plan.md must have:
- `coverage_policy` defined and enforced.
- Tests cover all ACs and contracts (when required).
- Evidence Pack defined (`required_artifacts` + `storage.path`).
- Groups and phases use stable IDs for tasking.

### tasks.md must have:
- All tasks include `plan_refs` to stable IDs only.
- All TS-* items are represented by tasks when `tests_must_be_tasked = true`.
- E2E tasks exist when e2e-tagged ACs exist.

## 3) Deviation rule
If execution deviates from spec or plan:
- Stop, update specs, then continue.

## 4) Phase Gate Enforcement (INVIOLABLE)

### APPROVAL.md Rules
- **AI is ABSOLUTELY FORBIDDEN from editing APPROVAL.md**
- APPROVAL.md is located at `specs/<feature>/APPROVAL.md`
- Human must manually check boxes `[x]` and fill in approver name/date
- stride-lint will fail with `APPROVAL_PENDING` error if gate not approved

### Phase Gate Workflow
| Phase | Files | Gates to unlock next phase |
|-------|-------|----------------------------|
| 1: Design | basic_design.md, process.bpmn, APPROVAL.md | Gate 1, 2 |
| 2: Specify | spec.md, plan.md, contracts/*, implementation-details/*, tests/scenarios.yaml | Gate 3, 4 |
| 3: Tasking | tasks.md, tests/* | Gate 5 |
| 4: Execute | src/* | Final |

> **BPMN の使い分け**: FEAT は `specs/<feature>/process.bpmn`（executable、stride_lint 対象）。EPIC は `epics/<EPIC>/epic_flow.bpmn`（overview/planning、epic_validator 対象）。

### AI Behavior Rules (v4.4 — AI Autonomous Execution)

AI（Claude Code等）は以下のルールに従い、**人間の指示なしで自律的に作業を進める**。
人間が行うのは APPROVAL.md の編集と業務判断のみ。

#### 自律実行ルール
1. Feature 作成指示を受けたら `stride init <feature> --detect` から開始する
   - 「Intake-First」「質問形式で聞き取って」等の指示があれば `stride intake` を使い、各セクション（Who/What/Why → Scope → Systems → Flow → Questions → Constraints）を1つずつ対話で聞き取り、`basic_design_intake.md` を自動記入してから `basic_design.md` を生成する
2. 各 Phase の成果物を連続で作成する（Phase 内で都度確認を求めない）
3. 成果物作成完了のたびに `stride lint specs/<feature>/` を自動実行する
4. lint FAIL（APPROVAL_PENDING 以外）→ **自分で修正して再実行**
5. lint FAIL（APPROVAL_PENDING）→ **停止し、人間に承認を依頼**
6. 人間が APPROVAL.md を編集したことを確認後、次の Phase に進む
7. **NEVER create Phase N+1 files before Phase N is approved**

#### 承認依頼の形式
Gate 承認が必要な場合、以下の形式で人間に通知する:
```
Gate X の承認をお願いします。
APPROVAL.md の「Gate X: <Gate Name>」セクションで:
  1. チェックボックスを [x] に変更
  2. 承認者名と日付を記入
してください。
```

#### 自動修正の範囲
- lint エラー（構造エラー、カウント不一致、プレースホルダ残留等）→ AI が自動修正
- APPROVAL_PENDING → AI は修正しない（人間が APPROVAL.md を編集）
- WI_APPROVAL_PENDING → AI は修正しない（人間が WI-*.approval.md を編集）
- 業務判断が必要なエラー（要件不明、設計方針未決定等）→ 人間に確認

### Phase Gate Check Commands
```bash
# Check current phase status
python3 sdd-templates/tools/phase_gate.py status specs/<feature>/

# Check if file creation is allowed
python3 sdd-templates/tools/phase_gate.py check <file_path>
```

## 5) Progress reporting
When reporting progress, include:
- Current task state.
- Changes made.
- Verification commands and outcomes.
- Next task.

## 6) Task Completion Checklist (MANDATORY)

> **SSoT**: このセクションの完了報告ルールの正本は `agent_docs/sdd_bootstrap.md §5`。
> Opus 4.7 は literal に実行する報告テンプレートが必要。必ず bootstrap §5 の固定テンプレートに従うこと。
> このセクションは補足情報（Anti-Pattern / Blocking Rule）のみを記載する。

### Pre-Completion Verification（完了報告前の必須確認）

#### Step 1: spec.md 全量確認
```
1. 該当タスクの spec_refs に含まれる全ACを読み直す
2. 各ACの全要素を確認（部分的な実装ではないか）:
   - ACに記載された全てのキーワード・条件を見落としていないか
   - 例: ACに「多言語対応」があれば i18n を確認
   - 例: ACに「監査ログ」があれば who/when/what/before/after を確認
   - 例: ACに「エラー時は〜」があればエラー処理を確認
3. ACに書かれていない要素は確認不要（過剰な確認は避ける）
```

#### Step 2: plan.md NFR確認
```
1. 該当タスクに関連するNFRを読み直す
2. 非機能要件の充足を確認:
   - パフォーマンス要件
   - セキュリティ要件
   - 可用性要件
```

#### Step 3: scenarios.yaml E2E検証
```
1. tests/scenarios.yaml を読み、該当シナリオを特定
2. 各シナリオの expected を一つずつ検証:
   - 「expected に書かれている全ての条件を満たしているか」
   - 部分的な動作確認ではなく、シナリオ全体の検証
3. 未検証項目がある場合は「完了」と報告しない
```

### Anti-Pattern: 確認バイアスの回避

❌ **やってはいけないこと**:
- 「実装した機能が動いた」→「完了」と報告
- ACの一部だけ読んで「完了」と判断
- scenarios.yaml を確認せずに「完了」と報告

✅ **やるべきこと**:
- 「仕様に書かれた全ての要素を満たしているか」を確認
- ACを最後まで読み、全てのキーワードをチェック
- scenarios.yaml の expected を全項目検証

### Completion Report Format（完了報告の形式）

タスク完了報告時は以下を含めること：

```markdown
## タスク完了報告: T-XXX-XXX

### 確認したAC
- AC-XXX-001: ✅ 全要素充足
  - (ACに記載された要素を列挙し、各々の充足状況を記載)
- AC-XXX-002: ✅ 全要素充足

### 確認したシナリオ (scenarios.yaml)
- SCN-001: ✅ 全expected項目検証済み
  - expected[0]: ✅
  - expected[1]: ✅

### 未実装・部分実装（ある場合）
- なし（または具体的に記載）

### 検証コマンド実行結果
- stride-lint: PASS
- テスト: X passed, 0 failed
```

### Blocking Rule（ブロッキングルール）

以下の場合、「完了」と報告してはならない：

1. spec_refs のACを全て読み直していない
2. scenarios.yaml の該当シナリオを検証していない
3. ACに記載された要素の一部が未実装
4. stride-lint が PASS していない（自動修正を試みた上で）
5. `stride pr-check .` が NOT_READY を返している（自動修正を試みた上で）

> **Note (v4.4)**: 項目 4, 5 は AI が自律的に実行・修正する。
> 人間に報告する前に、AI は lint/pr-check を実行し、
> 自動修正可能なエラーはすべて修正済みであること。

## 7) Amendment Rules (v4.5)

> Run の Findings/Decisions から蓄積された spec-impact を、仕様改訂（Amendment）として正式に管理する。

19. **PM が仕様変更を検討したい場合、まず `analyze` で影響分析を提示する**
20. **AI は提案するが、スコープの最終判断は PM が行う**
21. **Amendment Issue の承認チェックボックスは人間のみが編集する**（INVIOLABLE）
22. **Amendment 適用後、関連 WI の spec-impact ラベルを自動解消する**
23. **auto-check の閾値はデフォルト 2（同一 Feature への required が 2件以上）**

### Amendment ライフサイクル

```
spec-impact 蓄積 → auto-check → analyze → draft → create → PM承認 → apply
```

### コマンド

| サブコマンド | 目的 |
|-------------|------|
| `analyze --feature --topic` | 影響分析（Findings/Decisions 収集） |
| `draft --feature --title` | ドラフト生成（stdout） |
| `create --feature --draft` | Amendment Issue 作成 |
| `apply --issue` | 承認後の反映（ラベル変更 + spec-impact 解消） |
| `auto-check --feature` | 蓄積チェック（閾値超えでドラフト出力） |

## 8) ERP Addon Execution Tracking (v2.1.0)

> ERPアドオン向けマイクロレベル実行追跡。Gate 1-Final（マクロ統制）の上に、Work Item/Run/State/Mode（マイクロ統制）を追加。
>
> **SSoT 分担**:
> - Mode 判定表 / Autonomy Bias は `agent_docs/sdd_bootstrap.md §6` が正本
> - WI フロー 16 ステップも `sdd_bootstrap.md §6` が正本
> - 本セクションは **詳細 (Directory Structure / AI Behavior Rules 1-18 / Error Codes) のみ** を記載

### Activation Conditions

ERP Addon は以下の場合のみ有効化：
1. `specs/<feature>/work_items/` ディレクトリが存在 OR
2. `basic_design.md` YAML に `execution_profile: erp_addon` を設定

AND Gate 5 以降（tasks.md が存在 or Gate 5 承認済み）

### Directory Structure (Post-Gate 5)

```
specs/<feature>/
  [existing files...]

  work_items/
    WI-ERP-FEAT001-001.md           # Work Item 定義
    WI-ERP-FEAT001-001.approval.md  # post-run承認票（全モード）

  runs/
    WI-ERP-FEAT001-001/
      RUN-20260202-1430/
        walkthrough.md              # 必須: What/Why/How/Evidence/Planning Evidence
        test_results.md             # standard/critical tier で必須
        decision_log.md             # validate で推奨
        .planning/                  # 【v3.0.1】Planning 証跡（自動生成）
          plan.md                   #   計画・フェーズ・判断記録
          findings.md               #   調査発見事項
          lessons.md                #   学習・再利用可能パターン

  state/
    state.yaml                      # WI 状態の単一真実源

  ops/                              # ERP addon で必須
    transport_manifest.yaml
    release_checklist.md
    rollback_plan.md
    hypercare_runbook.md
```

### Mode（リスクに応じた儀式量）

| Mode | Pre-run | Post-run | 適用場面 |
|------|---------|----------|----------|
| **autopilot** | なし | walkthrough, CI, ops | 低リスク（UI, messages） |
| **confirm** | plan_review | walkthrough, CI, ops | 中リスク（new API, perf） |
| **validate** | design_diff, plan_review | walkthrough, CI, ops | 高リスク（auth, accounting） |

### Risk Flags と Mode の対応

```yaml
# High risk → validate
- authz, sod, audit_log, pii, accounting_calc, inventory_valuation
- db_schema, data_migration, update_integration, cross_module

# Medium risk → confirm
- new_api, contract_change, performance_sensitive

# Low risk → autopilot
- ui_only, message_only, test_only, logging_only
```

### Autonomy Bias（プロジェクトレベルのモード調整 v3.1）

Autonomy Bias は `state.yaml` の `autonomy_bias` フィールドで設定される。
risk_flags から推奨される Mode を、プロジェクトの信頼度に応じてシフトする。

| 推奨Mode | autonomous | balanced | controlled |
|----------|------------|----------|------------|
| autopilot | autopilot | autopilot | confirm |
| confirm | autopilot | confirm | validate |
| validate | confirm | validate | validate |

**制約**: `tier_mode_minimum` を下回ることはできない。
例: critical tier は最低 confirm のため、autonomous bias でも autopilot にはならない。

### Run Evidence Requirements by Coverage Tier

| Coverage Tier | walkthrough | test_results | ops pack |
|---------------|-------------|--------------|----------|
| **critical** | Required | Required | Required |
| **standard** | Required | Required | Required |
| **experimental** | Required | Optional | Required |

### AI Behavior Rules (ERP Addon)

1. Gate 5 承認後に `work_items/` を作成
2. Work Item ごとに risk_flags を評価し、適切な mode を設定
3. policy より弱い mode を使う場合は `mode_override.reason` を記載
4. Work Item に complexity と Spec Links / DoD を記入
5. Work Item は **1 Run で完了**（RUN-* は1つ）
6. **Run 開始時に `/planning` を自動実行し、計画ファイルを `.planning/` に作成する**（Section 9 参照）
7. Run 実行後は必ず `walkthrough.md` を作成し、walkthrough/CI/ops の承認を完了
8. **walkthrough.md の "Planning Evidence" セクションに `.planning/` の要約を記載する**
9. Ops pack（transport/release/rollback/hypercare）を必ず用意
10. WI を done にする前に、適切な Run 証跡があることを確認
11. **Run 完了時に `/planning:archive` でグローバル知識に保存する**
12. **walkthrough.md の "Review Checklist" セクションで全項目をチェック済みにする**（該当しない項目は N/A + 理由）
13. **WI-*.approval.md は AI が編集してはならない**

### Run Resume Detection (v3.1)

14. **Run 開始時に既存アーティファクトをチェックし、中断された Run の再開ポイントを自動検出する**
15. **再開ポイントが検出された場合、ユーザーに確認してから再開する**（自動再開は禁止）

### Run Report Generation (v4.3)

16. **Run 完了時に `run_report_generator.py` を実行し、Findings/Decisions/Spec Impact を構造化レポートとして Issue コメントに記録する**
17. **`--labels` オプションで STRIDE ラベル（findings:N, decisions:N, spec-impact:X）を自動適用する**
18. **Epic の週次サマリは `epic_progress_aggregator.py --weekly-summary` で定期生成し、`--post --epic <N>` で Issue に投稿する**

### Work Item Approval Rules (INVIOLABLE)

- **AI is ABSOLUTELY FORBIDDEN from editing WI-*.approval.md**
- Human must check boxes `[x]` for pre-run/post-run checkpoints (all modes)
- stride-lint fails with `WI_APPROVAL_PENDING` if approval not completed

### New Error Codes (ERP Addon)

| Code | Meaning |
|------|---------|
| WI_DIR_MISSING | Gate5以降で work_items/ がない |
| WI_SCHEMA_INVALID | WI必須項目欠落 |
| WI_MODE_INVALID | mode が不正 |
| WI_RISK_FLAG_INVALID | risk_flags が不正 |
| WI_MODE_POLICY_VIOLATION | policy推奨より弱いmode |
| MODE_OVERRIDE_REASON_MISSING | override理由なし |
| STATE_MISSING | state.yaml がない |
| STATE_WI_MISMATCH | stateとWI実体が不整合 |
| RUN_MISSING | WI done なのに Run がない |
| RUN_MULTIPLE | Work Item に複数の Run がある |
| WALKTHROUGH_MISSING | walkthrough.md がない |
| TEST_RESULTS_MISSING | tier標準以上で test_results がない |
| WI_APPROVAL_PENDING | 承認未完 |
| OPS_PACK_MISSING | ERP addon で ops 不足 |
| AUTOPILOT_FORBIDDEN_BY_TIER | critical で autopilot 不可 |

### Warning Codes (ERP Addon)

| Code | Meaning |
|------|---------|
| WARN_WI_MODE_POLICY_VIOLATION | policy推奨より弱いmode（理由あり） |
| WARN_SPEC_LINK_NOT_FOUND | Spec Links 参照先ファイルが見つからない |
| WARN_SPEC_REF_NOT_FOUND | spec_refs 参照先ファイルが見つからない |

## 9) Multi-Team Progress Management (v3.0.0)

> 複数チームが1システムを共同開発する際の進捗管理ルール。Article XIII（PM Progress Visibility）に基づく。

### PM Dashboard ルール

1. **EPIC_PROGRESS_REPORT.md** を週次で更新する
   - `epic_progress_aggregator.py --format markdown` で自動生成可能
   - Team Status Table / Gate Completion Matrix / Blocker List が必須セクション
2. PM は週次ステアリングで EPIC_PROGRESS_REPORT.md をレビューする
3. at-risk または blocked のFeatureがある場合、48h以内にアクションを決定する

### チーム間依存ルール

1. **DEPENDENCY_MANIFEST.yaml** はEpic作成時に初期化し、Feature追加時に更新する
2. 依存の `status` は以下の値をとる:
   - `pending` → 依存先が未着手
   - `in_progress` → 依存先が作業中
   - `stable` → 依存先が完了し安定
   - `at_risk` → 依存先が遅延の恐れ
   - `blocked` → 依存先がブロックされている
3. `blocking` タイプの依存が `at_risk` になった場合、PM/Epic Leadに即時エスカレーション
4. `dependency_checker.py --all` で循環依存を定期チェック

### チームステータスレポートルール

1. 各チームリードは **TEAM_STATUS_<TEAM_ID>.md** を週次更新する
2. 必須記入項目:
   - Feature Gate進捗（Gate 1-5, Final）
   - WI完了率（pending/in_progress/done）
   - ブロッカー（自チーム → 他チームへの依頼事項）
3. ステータスレポートが2週間未更新の場合、PM/Epic Leadがフォローアップ

### Ops Pack管理ルール

1. **OPS_PACK_REGISTRY.yaml** はEpic内の全WIのOps準備状況を追跡する
2. ERP連携（`erp_integration: true`）のWIはOps Pack必須
3. Go-Live前にOps Pack準備率100%を確認する

### WI実行前ルール

1. Run実行前に `wi_readiness_checker.py` を実行する
2. FAIL項目がある場合、Runを開始してはならない
3. WARN項目がある場合、判断を記録した上で実行可能

### Mode Policy ルール

1. `shared/policies/mode_policy.yaml` がOrganizationレベルのMode方針
2. critical tierのFeatureでは autopilot モード禁止
3. Mode override（推奨より弱いモード使用）には理由記載と承認が必要

## 10) Run 実行時の Planning 自動統合 (v5.0)

> Claude Code を使用した Run 実行時に Planning v5.0 スキルと SDD Planning Bridge を統合し、計画・調査・学習の証跡を Run 内に保存する。

### アーキテクチャ

```
Layer 1: Planning v5.0 (~/.claude/commands/planning/)
  → 汎用の計画・知識蓄積エンジン。SDD以外のプロジェクトでもそのまま使える。

Layer 2: SDD Planning Bridge (sdd-templates/tools/sdd_planning_bridge.py)
  → §10 の自動化ツール。SDD の WI/Run 文脈を Planning に注入する。
```

### 概要

```
1 Work Item = 1 Run = 1 Planning
```

各 Run の `.planning/` ディレクトリに計画ログを格納することで、「AIがどう計画し、何を調査し、何を学んだか」が監査証跡として残る。

### Planning ファイルの格納先

```
specs/<feature>/runs/<WI-ID>/RUN-YYYYMMDD-HHMM/
├── walkthrough.md          # 変更証跡（Planning Evidence セクション含む）
├── test_results.md         # テスト結果
└── .planning/              # 【Planning 証跡】
    ├── plan.md             #   計画・フェーズ・判断記録（SDD Context セクション付き）
    ├── findings.md         #   調査発見事項（spec_refs 付き）
    └── lessons.md          #   学習・再利用可能なパターン
```

### SDD Planning Bridge コマンド

| コマンド | タイミング | 動作 |
|---------|-----------|------|
| `bridge init <feature_dir> <WI-ID>` | Run 開始時 | WI 定義読取 → .planning/ 作成（SDD 文脈付き、Exploration Ladder 付き） + knowledge 検索 |
| `bridge sync <feature_dir>` | stride-lint 実行後 | lint FAIL → plan.md Errors テーブルに自動反映 |
| `bridge evidence <feature_dir> <WI-ID>` | walkthrough 作成時 | .planning/ → walkthrough.md Planning Evidence セクション生成 |
| `bridge learn <feature_dir> <WI-ID>` | evidence 後 | Errors retries・Decisions・findings・lint FAIL → lesson 候補抽出（stdout 表示） |
| `bridge learn <feature_dir> <WI-ID> --apply` | 候補確認後 | lesson 候補を lessons.md に直接反映（冪等） + Archive Summary 行追加 |

```bash
# 使い方
python3 sdd-templates/tools/sdd_planning_bridge.py init specs/<feature>/ <WI-ID>
python3 sdd-templates/tools/sdd_planning_bridge.py sync specs/<feature>/
python3 sdd-templates/tools/sdd_planning_bridge.py evidence specs/<feature>/ <WI-ID>
python3 sdd-templates/tools/sdd_planning_bridge.py learn specs/<feature>/ <WI-ID>          # 候補表示のみ
python3 sdd-templates/tools/sdd_planning_bridge.py learn specs/<feature>/ <WI-ID> --apply  # lessons.md に反映
```

### Run 実行フロー（Planning Bridge 統合版）

```
┌─ Pre-Run ─────────────────────────────────────────────────┐
│ 1. wi_readiness_checker.py で準備チェック                   │
│ 2. confirm/validate なら事前承認を取得                      │
├─ Run Start ───────────────────────────────────────────────┤
│ 3. RUN ディレクトリ作成                                     │
│ 4. sdd_planning_bridge.py init <feature> <WI-ID>           │
│    → .planning/ を RUN ディレクトリ内に作成                  │
│    → WI 定義から SDD Context を plan.md に自動注入           │
│    → グローバル知識 (~/.claude/knowledge/) を検索・適用       │
│    → spec_refs を findings.md に自動記載                     │
├─ Implementation ──────────────────────────────────────────┤
│ 5. 実装作業                                                │
│    → 調査2回ごとに findings.md を更新（2-Action Rule）       │
│    → エラー発生時は plan.md の Errors に記録                  │
│    → 3-Strike Protocol: 同じ失敗は繰り返さない               │
│ 5b. stride-lint 実行後:                                     │
│    → sdd_planning_bridge.py sync <feature>                  │
│    → lint FAIL を plan.md Errors に自動反映                  │
├─ Run Complete ────────────────────────────────────────────┤
│ 6. walkthrough.md 作成                                      │
│    → sdd_planning_bridge.py evidence <feature> <WI-ID>      │
│    → Planning Evidence セクションを自動生成・挿入            │
│ 6b. test_results.md 作成（standard/critical tier）          │
│ 6c. sdd_planning_bridge.py learn <feature> <WI-ID>          │
│    → lesson 候補確認、必要なら --apply で lessons.md に反映   │
│ 7. /planning:archive 実行                                   │
│    → lessons.md → ~/.claude/knowledge/ にグローバル保存       │
├─ Post-Run ────────────────────────────────────────────────┤
│ 9. WI-*.approval.md の承認を取得（Human-only）              │
│ 10. state.yaml を done に更新                               │
└───────────────────────────────────────────────────────────┘
```

### AI Behavior Rules (Planning Bridge 統合)

1. **Run 開始時**: RUN ディレクトリ作成直後に `sdd_planning_bridge.py init` を実行する
   - `.planning/` は RUN ディレクトリ内（プロジェクトルートではない）に作成される
   - WI 定義の spec_refs, risk_flags, mode が plan.md の SDD Context に自動注入される
   - 過去のグローバル知識を検索し、SDD/ERP/STRIDE タグで関連するものを適用
2. **実装中**: Planning ファイルを随時更新する
   - **2-Action Rule**: 検索/ブラウズ操作を2回行ったら findings.md を更新
   - **3-Strike Protocol**: 同じエラー3回で根本再考、超過でユーザーに相談
   - stride-lint 実行後は `sdd_planning_bridge.py sync` で FAIL を plan.md Errors に自動反映
3. **walkthrough.md 作成時**: `sdd_planning_bridge.py evidence` を実行する
   - plan.md の Goal, Decisions, Errors を自動要約
   - findings.md の件数、lessons.md の学習項目を集計
   - 既存の walkthrough.md に Planning Evidence セクションを挿入（または更新）
4. **教訓抽出**: `sdd_planning_bridge.py learn` を実行する
   - Errors (attempt≥2), Decisions, findings Technical Notes, lint FAIL から候補を stdout に表示
   - 確認後 `--apply` で lessons.md に冪等反映（Archive Summary 行も自動追加）
5. **Run 完了時**: `/planning:archive` を実行してグローバル知識に保存
6. **Design/Specify Phase 開始時**: findings.md の Exploration Ladder チェックリストを実施する
   - プロジェクト内の類似実装、過去教訓、外部パッケージ、契約整合を確認してから作業開始
7. **複数 WI を連続実行する場合**: 各 WI の Run ごとに独立した `.planning/` を作成する

### Planning 自動起動の判定基準

Run 実行中の全てのタスクで Planning Bridge を自動起動する。これは以下の理由による:
- Run は常に3ステップ以上の作業を伴う（WI定義確認 → 実装 → 証跡作成）
- Run の計画・調査・学習記録は監査証跡として価値がある
- SDD Context の自動注入により、蓄積される知識が SDD 文脈と紐付く
- グローバル知識の蓄積により、同種のWIの実行効率が向上する

### 注意事項

- `.planning/` 内のファイルは AI が管理する（Human-only ではない）
- `.planning/` は walkthrough.md の補足証跡であり、承認対象ではない
- グローバル知識ストア (`~/.claude/knowledge/`) はプロジェクト横断で共有される
- Bridge は Planning v5.0 に依存するが、Planning 側は Bridge を知らない（一方向依存）

## 11) Auto-Continue Rule (v4.1)

> Phase内の小ステップは連続実行し、HITLチェックポイント（Gate承認）でのみ停止する。

### 実行ルール

1. `stride auto-continue specs/<feature>/` で次フェーズの実行シーケンスを取得する
2. シーケンス内の `PASS` ステップは連続で実行する
3. `WARN` で示される HITL checkpoint に到達したら必ず停止する
4. ユーザーが `APPROVAL.md` を更新するまで次のフェーズには進まない

## 12) Mandatory Output Rules (v4.1)

1. AI出力で固定幅 ASCII テーブルを使わない
2. 選択肢の提示は `N - **Option**: Description` を使用する
3. ステータス表記は `PASS / FAIL / WARN / SKIP` のみ使用する
4. 複数ステップの進捗は `[n/N]` 形式で示す

## 13) DDD Integration (Optional, v4.1)

> `mode: validate` かつ高複雑度のWIでのみ推奨。全WIへの強制適用は禁止。

1. `basic_design.md` の `delivery_model.type` を `ddd` に設定した場合のみ有効化する
2. `stride ddd-init <feature>` で以下を初期化する:
   - `implementation-details/domain_model.md`
   - `implementation-details/technical_design.md`
   - `shared/decisions/ADR-*.md`（初回）
3. DDD採用時は、主要な設計判断を ADR として記録する

## 14) Decision Index (ADR, v4.1)

1. ADR は `shared/decisions/ADR-*.md` で管理する
2. `stride decisions refresh` を実行して `decision-index.md` を更新する
3. `status` は `proposed | accepted | superseded | rejected` のいずれかを使用する
