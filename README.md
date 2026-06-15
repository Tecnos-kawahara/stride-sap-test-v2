# Stride Sap Test V2 — SDD Project

**S**tate-Tracked **R**un **I**ntent-**D**riven **E**ngineering

[![Manual](https://img.shields.io/badge/Manual-Docsify-blue)](./manual/)
[![Version](https://img.shields.io/badge/Version-6.0.0--tecnos--stride--value-brightgreen)]()
[![Plugin](https://img.shields.io/badge/Cowork%20Plugin-0.5.0--agent--hardening-blue)](./cowork-plugin/)
[![BPMN Pack](https://img.shields.io/badge/BPMN%20Pack-1.1.0-orange)](./bpmn/)

> **仕様（Spec）が契約。コードは生成物。変更は Work Item 単位で追跡。**
> **AI が全作業を自律実行し、人間は承認のみ。**

> 🚀 **v6.0.0-tecnos-stride-value (2026-04-29)**: VALUE Upstream Extension 完成。
> Phase A (schema 基盤) + Phase B (CLI scaffold) + Phase C (upstream-bridge / retro --solution-eval / Constitution Article XV-XVII ratification) の三段階で、
> Discovery → Design → Implementation → Operation のフルサイクルを BABOK v3 + Layered Requirements Modeling + value-driven discovery (philosophical foundation) の三脚で機械検証可能化。
> 詳細は [manual/47](manual/47_v60_release_notes.md) (v6.0 Release Notes)。
>
> 🚢 **v6.0.x Phase D 普及準備 (2026-04-30、FEAT-VALD01)**: 3 profile 別 playbook (`manual/48-50`) + v5.x → v6.0 Migration Guide (`manual/migration/v54_to_v60.md`) + `upstream_migration_helper.py` (basic_design.md → Phase 0 yaml seed 半自動逆生成) + dogfooding sanitized 学び (`memory/lessons_learned/upstream_dogfooding/external_scm_pilot_01.md`) で「使える状態」から「使われる状態」へ。VERSION 6.0.0 維持 (普及準備のため bump なし、テスト 769 → 778 passed)。
>
> 🔌 **v6.0.x Phase E Cowork Plugin (2026-04-30、FEAT-VALE01、Plugin 0.1.0-poc)**: 上位コンサル (非技術者) が Claude Cowork で Phase 0 (BACCM Discovery + BABOK Elicit + Layered Context Modelling) → Phase 1 (basic_design + process.bpmn) → 必要時 Epic 階層 → Claude Code 引き渡し (GitHub PR draft) を一気通貫で実行できる Anthropic 公式 `knowledge-work-plugins` 仕様準拠プラグイン (`cowork-plugin/`、Skills 7 + Commands 9 + reference_files 49 + MCP filesystem/github)。Tecnos-STRIDE 本体 VERSION 6.0.0 維持 (Plugin は独立 SemVer)、テスト 778 → 788 passed → 789 passed (PR #11 post-review fix 後)。
>
> 🛠 **v6.0.x Phase F Cowork Plugin v0.2.0-stable (2026-05-01、FEAT-VALF01、PR #14 merged 528ca72)**: fc-sd 実機運用で発見された 16 件改善要望を 17 WI で反映、Plugin v0.1.0-poc → **v0.2.0-stable** に運用品質引き上げ。CI 統合 (`.github/workflows/cowork-plugin-validate.yml`) + Cowork セッション内 機械検証 + サニタイズ自動 grep + state.yaml Phase 2-4 schema (+3 tests) + HTML 出力 (`/stride:export-html`) + Phase 3 連結 (`/stride:tasking`) + 7 Skill description 固有語必須化 (誤起動回避) + `cowork-plugin/scripts/` 同梱 + `.claude-template/settings.json` 推奨値配布。commands 9 → 11、reference_files 49 維持、テスト 789 → 792 passed (回帰 0)。WI-006/007 (saas-integration / prototype profile dogfooding) と WI-012 (GitHub MCP 実 API 検証) は scaffold 完成、実機検証は [Issue #15](https://github.com/tecnos-japan-cbp/tecnos-stride/issues/15) で Phase G 入口の follow-up tracking。詳細: [`manual/52`](manual/52_phase_f_lessons_learned.md)。
>
> 🎨 **v6.0.x Phase G Brand-Neutral + Simple UX (2026-05-07、Plugin v0.2.0-stable → v0.3.2 → v0.4.0-bpmn-package-integration)**: 7 連続 PR (PR #18 → #25 + 直接 commit 2 件) で Plugin を「上位コンサルが Cowork で日本語ひとことで指示する」体験に磨き上げ。**(PR-A #18)** Plugin 内部の RDRA / 匠Method 等の固有名称を考え方ベースの brand-neutral 用語に置換。**(PR-B #19)** 本体 docs + reference_files の同様 RDRA / 匠Method 全件除去。**(PR-C #20)** Constitution Article XVI 文言の brand-neutral rephrasing + code-level error code rename。**(PR-D #21)** `stride-bootstrap-repo` command 新設 — Cowork → Claude Code 継ぎ目のない接続を 1 コマンドで bootstrap。**(marketplace #22)** marketplace.json 0.1.0-poc → 0.2.0-stable bump。**(PR-E #23 v0.3.0-simple-ux)** **`/start` コマンド新規** — 日本語ひとこと指示で Plugin が状態を理解して進める conductor 設計、複雑だった UX を Anthropic 公式パターンに整合。**(PR-F #24 v0.3.1)** stride-start.md → start.md rename hotfix (`/tecnos-stride-value:start` 起動可能化)。**(PR-G #25 v0.3.2)** Plugin docs example の顧客固有名詞 (例) を汎用 placeholder に置換 (sanitize hotfix)。
>
> 📐 **v6.0.x BPMN Standalone Package + Plugin v0.4.0 (2026-05-07、bpmn/ v1.0.0)**: 直接 commit 2 件で BPMN 作成基盤を独立パッケージ化 + Plugin first-class component に統合。**(b8aec09)** BPMN 作成 24 章 ruleset + Camunda 8.9 spec 完全辞書 (2744 行) + FEAT/EPIC templates + bpmn_lint.py validator + examples を `bpmn/` 配下にスタンドアロン化、`bpmn/VERSION 1.0.0` で独立 SemVer 管理開始。**(6acd3fe)** Cowork Plugin v0.4.0-bpmn-package-integration — `cowork-plugin/bpmn/` に first-class component として配置 (Skills / Commands / reference_files と並列)、Plugin install で BPMN 作成基盤一式を自動同梱、`/stride:bpmn-validate` 新規 command (FEAT 14 / EPIC 9 MUST-DO 自動検証)、reference_files から BPMN 重複削除 (drift 防止、git rename detection で 4 件移動)。
>
> 🛡 **v6.0.x Cowork Plugin v0.5.0-agent-hardening + BPMN Pack v1.1.0 (2026-05-08、PR #29 merged f5212b9)**: simple-bi PoC で発生した 2026-05-08 BPMN vertical-flow violation incident (7 件の canonical 違反、ユーザ目視レビューが唯一の発見ルート) への構造的 hardening。**SKILL.md auto-trigger ≠ SKILL.md body load** の failure mode を防止する 7-task structural guard を投入: (1) 全 7 specialized SKILL.md に **STEP 0 PRE-FLIGHT (MANDATORY)** ブロック挿入 — 必須 Read リスト + template-copy 強制 cp コマンド + ANTI-PATTERN 表 + Output of STEP 0 (PRE-FLIGHT REPORT) フォーマット。(2) `bpmn/PRE_FLIGHT_CHECKLIST.md` 1-page checklist 新設。(3) `bpmn_lint.py` v1.0→v1.1 強化 — `BPMN_ID_FORMAT_VIOLATION` (^BPMN-(TASK|GW|EVT|FLOW)-\d{3}$) + `BPMN_ID_NON_TECNOS_SCHEME` warning (backward compat) + `--legacy-id` (transition flag、warn-only) + `--diff-against-template` flag + 全 error に fix_hint+refs。(4) `bd_bpmn_sync.py` 新設 (basic_design.md ↔ process.bpmn id 双方向 sync 検証、stdlib のみ)。(5) `render_ascii_preview.py` 新設 (BPMNDI 座標 → ASCII grid、vertical/horizontal orientation 視覚判別)。(6) stride-conductor SKILL.md に dispatch 前 SKILL.md Read 強制 5-step protocol (bpmn-authoring のみ 2 ファイル mandatory で multi-layer 防御)。(7) `docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md` 起票。**Plugin v0.4.0-bpmn-package-integration → v0.5.0-agent-hardening、BPMN Pack v1.0.0 → v1.1.0** (本体 6.0.0 維持)。詳細: [`docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md`](docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md)。
>
> 📦 **v6.0.x Method Store Publishing (Feature ②、2026-05-08、PR #26 merged 684c948)**: `FEAT-METHODSTOREPUBLISHING` SDD Feature を Phase 1-Final 全 Gate 承認下で実装、Method content の OCI artifact 化 + cosign keyless signing + ghcr.io 配信パイプラインを 1-cmd で起動可能に。**5 stride method subcommands** (preview / validate / diff / publish / rollback、+ 1 implicit drift) + **9-step CI pipeline** (`.github/workflows/method-store-publish.yml`、validate → snapshot_build → cosign sign → ghcr.io push → channel branch → smoke or auto PR → live → notify、permissions 最小化 + workflow injection 防御) + **3 contracts** (CT-CLI-02 5-subcommand schema / CT-FILE-02 RELEASE_NOTES + 3-person METHOD_APPROVAL template / CT-FILE-03 sdd_tenant_policy schema、cross-repo SSoT) + 3 channel (edge / staging / stable) + Method Board 3 person 多人数署名 + 5 min MTTR rollback + tenant policy auto_upgrade。**Tecnos-STRIDE 本体 VERSION 6.0.0 維持** (Phase F と同様、機能追加のみ)、22/22 unit test PASS、Evidence Pack 8 artifacts (CI/SAST/SCA/Secrets/AI provenance + cosign + Rekor)。**(PR #27 bbfe46b)** F3 (`sdd_method_gateway_poc` on cbp-core 別 repo) 着手用の planning doc v1.2.1 を完成 (`.planning/claude_code_instruction_sdd_method_gateway.md` 1499 行、F1+F2 確定情報 + ID convention regex + Phase Gate 実機仕様 + F2 follow-up 7 issue を反映、independent reviewer による Critical 3 + Important 5 件の整合性問題を全件解消後 merge)。F3 は別 session で cbp-core 側で実装予定。
>
> ### 🚀 Plugin Quick Install (実機検証済、本リポジトリ clone 後すぐ動く)
>
> ```bash
> # 1. Tecnos-STRIDE 全体を local marketplace として登録 (.claude-plugin/marketplace.json を利用)
> claude plugin marketplace add "$(pwd)"
>
> # 2. Plugin を user scope に install
> claude plugin install tecnos-stride-value@tecnos-stride
>
> # 3. 動作確認
> claude plugin list | grep tecnos-stride-value   # ✔ enabled
> claude -p --dangerously-skip-permissions \
>   "/tecnos-stride-value:stride-init demo --profile prototype"
> ```
>
> 詳細手順 (3 つの起動方法 / 典型 workflow / Anthropic Cowork web 連携 / トラブルシューティング) は [`manual/51_cowork_plugin_install_guide.md`](manual/51_cowork_plugin_install_guide.md) を参照。

---

## 🚀 始め方

> 📖 **PM の方へ**: [PM クイックスタート（5分）](manual/00_pm_quickstart.md) を読めば、AI 自律開発の全体像と承認操作を5分で理解できます。

### Step 1: テンプレートからプロジェクトを作成

GitHub で **"Use this template"** → 新リポ作成 → clone、または：

```bash
gh repo create my-org/my-project \
  --template tecnos-japan-cbp/tecnos-sdd-template-enterprise --private --clone
cd my-project
```

### Step 2: プロジェクトを初期化

```bash
sdd-templates/bin/stride new-project <project_name> \
  [--org <org>] [--scale starter|standard|enterprise] \
  [--first-feature <feature_name>]
```

サンプル削除・名前置換・CI 設定・Phase Gate hooks がすべて自動で行われます。

### Step 3: Claude Code で開発開始

```
あなた: 「order_import 機能を作って」
Claude: CLAUDE.md → sdd_bootstrap.md を読み、全ルールを把握 → 自律実行開始
```

**これだけです。** あとは Claude Code が SDD のフロー全体を自律的に進めます。

👉 **テンプレート利用の詳細:** [docs/TEMPLATE_USAGE_GUIDE.md](docs/TEMPLATE_USAGE_GUIDE.md)

---

## Claude Code による開発フロー

Tecnos-STRIDE では **Claude Code が実行者 (R)、人間が承認者 (A)** です。
人間がやることは APPROVAL.md の編集と業務判断だけ。それ以外は全て Claude Code が自律実行します。

```
あなた: 「order_import 機能を作って」

Claude Code:
  ┌─ Phase 1: Design ─────────────────────────────────────────┐
  │  basic_design.md + process.bpmn 作成 → lint 自動修正       │
  │  → ⛔「Gate 1,2 の承認をお願いします」                      │
  └────────────────────────────────────────────────────────────┘
  あなた: APPROVAL.md を編集 ✅

  ┌─ Phase 2: Specify ─────────────────────────────────────────┐
  │  spec.md + plan.md + contracts/ 作成 → lint 自動修正        │
  │  → ⛔「Gate 3,4 の承認をお願いします」                      │
  └────────────────────────────────────────────────────────────┘
  あなた: APPROVAL.md を編集 ✅

  ┌─ Phase 3: Tasking ─────────────────────────────────────────┐
  │  tasks.md 作成 → lint 自動修正                              │
  │  → ⛔「Gate 5 の承認をお願いします」                        │
  └────────────────────────────────────────────────────────────┘
  あなた: APPROVAL.md を編集 ✅

  ┌─ Phase 4: Execute ─────────────────────────────────────────┐
  │  WI-001: 定義 → 実装 → テスト → walkthrough → lint          │
  │  → ⛔「WI-001 の承認をお願いします」                        │
  │  WI-002: ...                                                │
  └────────────────────────────────────────────────────────────┘
  あなた: WI-*.approval.md を編集 ✅

  ┌─ Final ────────────────────────────────────────────────────┐
  │  Evidence Pack + Ops Pack + PR Readiness Check              │
  │  → ⛔「Final Gate の承認をお願いします」                    │
  └────────────────────────────────────────────────────────────┘
  あなた: APPROVAL.md を編集 ✅ → PR 作成
```

### Intake-First モード（対話式）

より丁寧に始めたい場合：

```
あなた: 「Intake-First で order_import の要件を聞き取って」

Claude Code:
  1. 「この機能の目的は？誰が使いますか？」
  2. 「対象システムと連携先は？」
  3. 「業務フローを教えてください」
  4.  ... (1つずつ対話で聞き取り)
  → basic_design.md を自動生成 → Design Phase に合流
```

---

## 概要

**Tecnos-STRIDE** は、テクノスジャパンがERP導入の実践知を反映させた SDD（Spec-Driven Development）メソッドです。
「**AI と共に前進する（Stride）**」をコンセプトに、品質を担保しながら迅速に成果を出します。

### 二層統制モデル (Macro Gate + Micro Run)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  v6.0 (任意): Phase 0 ──► Phase 0.3 ──► Phase 0.5 ──► (`stride upstream-bridge`)│
│   Discovery (BABOK KA6)  Elicit (KA4)   Context Modelling (KA7 + 4-layer Requirements Architecture)│
├─────────────────────────────────────────────────────────────────────────────┤
│  Macro: Gate 1 → Gate 2 → Gate 3 → Gate 4 → Gate 5 → Final → Solution Eval │
│         (Design)  (BPMN)   (Spec)   (Plan)  (Tasks)  (Evidence) (KA8、v6.0)  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Micro: WI-001 ──► RUN-001 ──► Done                                         │
│         WI-002 ──► RUN-001 ──► Done                                         │
│         WI-003 ──► RUN-001 ──► (in_progress)                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

**v6.0 — VALUE Upstream Extension** (任意、有効化時のみ): 既存 Phase 1-Final の前段に Phase 0 (Discovery) / 0.3 (Elicit) / 0.5 (Context Modelling) を加え、`stride upstream-bridge` で Phase 1 へ自動接続。`stride retro --solution-eval` で Final 後の稼働後評価ループを実施 (BABOK KA8)。Constitution **Article XV-XVII** で機械検証義務化 (詳細 §「VALUE Upstream Extension v6.0」)。

### 核心原則

| 原則 | 内容 |
|------|------|
| **Spec が正本** | 仕様が契約。実装と食い違えば Spec か Code のどちらを直すか明示的に判断 |
| **AI executes, Human approves** | AI が全作業を自律実行、人間は APPROVAL.md 編集のみ (v4.4) |
| **Work Item 単位追跡** | 変更を WI に分解し、リスクベースで Mode（autopilot/confirm/validate）を付与 |
| **1 WI = 1 Run** | 監査単位として1つの WI は1つの Run で完了 |
| **Ops Pack 必須** | ERP 本番変更には輸送/リリース/ロールバック/ハイパーケアを常に用意 |

### 主な機能

| カテゴリ | 機能 |
|---------|------|
| **統制** | 可変チェックポイント（3 Mode）/ Autonomy Bias / Coverage Tier（3段階）/ Execution Authority（3層権限宣言）/ **Instruction Precedence 10段ヒエラルキー (v5.2)** |
| **自動化** | Intake 対話 / Auto-Continue / Run Resume / Brownfield Detection |
| **品質** | PR Readiness（7チェック統合 + optional Mutation Testing）/ Security Audit（2段階10チェック）/ Multi-Model Evaluator（LLM意味的評価 + Self-Review Loop）/ Living Spec Drift / Evidence Metrics / BDD AC / PostToolUse Guard / CLI UX（カラー出力・NDJSON・TSV・パス候補・YAML事前検証） |
| **Harness Maturity** | Runtime Sensors（dead code / coverage decay）/ Harness Report（8 controls）/ Symphony Janitor（技術的負債の Issue 提案） |
| **Opus 4.7 対策 (v5.2)** | Governance hardening（bootstrap loop bounds / AI Action Boundary 3分類 / Completeness 4条件数値基準 / Task Completion 固定テンプレート）/ stride_shared_lib（YAML抽出集約）/ Execution Authority E2E（14 tests）/ hermetic pytest（addopts `-m 'not api'`） |
| **Reporting Lightening (v5.4)** | Profile 軸（enterprise-erp / saas-integration / prototype）/ Profile-Dependent Task Completion Report（5-step full / critical-only / 1-line）/ Completeness Profile-aware 閾値（200/150/100 行 × 5/4/3 ファイル AND）/ `stride pr-check --summary-line`（project-level 1-line）/ stride-lint PROFILE_MISMATCH / PROFILE_UNKNOWN / PROFILE_MISSING。**BPMN / Evidence / SEC-006 / Ops Pack / Epic-Feature Hierarchy / Coverage Tier は全 Profile で現行正本のまま不変** |
| **VALUE Upstream Extension (v6.0)** | **Phase A** schema 基盤（4 policies + 16 templates + 3 amendments + 4 manuals + 5 tests）/ **Phase B** CLI scaffold（5 Python tools + 7 tests + 15 JSON Schema Draft 2020-12 + `stride upstream init/validate` + `stride lint --upstream` + `stride evaluate --phase discovery` + 4 新エラーコード BACCM_INCOMPLETE/Layered Requirements Modeling_BROKEN_LINK/UPSTREAM_TEMPLATE_DRIFT/BABOK_TECHNIQUE_UNKNOWN + 2 manuals）/ **Phase C** 統合（`stride upstream-bridge` で Phase 0/0.3/0.5 → Phase 1 自動 populate + Gate 1/2 immutability check / `stride retro --solution-eval` で BABOK KA8 稼働後評価 / Constitution Article XV/XVI/XVII を articles[] に正式マージ + amendments status proposed → ratified + 3 manuals）。Discovery → Design → Implementation → Operation のフルサイクルを **BABOK v3 + Layered Requirements Modeling + value-driven discovery (philosophical foundation)** の三脚で機械検証可能化 |
| **学習** | Lesson Schema（4セクション統一）/ `learn` コマンド（教訓自動抽出）/ Retro（定量ふりかえり）/ Search-First 探索ラダー |
| **拡張** | Multi-Tool（Claude/Cursor/Copilot）/ DDD / ADR / Monorepo（3 Scale） |
| **運用** | マルチチーム Epic 管理 / PM ダッシュボード / GitHub Projects 連携 |
| **オーケストレーション** | Symphony — GitHub Issues → Agent 自動実行パイプライン（並列WI対応、v5.2 で `stride symphony` CLI 統合済） |

---

## Mode（可変チェックポイント）

| Mode | Pre-Run | Post-Run | 適用条件 |
|------|---------|----------|----------|
| **autopilot** | なし | walkthrough, CI, ops | ui_only, message_only, test_only |
| **confirm** | plan_review | walkthrough, CI, ops | new_api, contract_change |
| **validate** | design_diff, plan_review | walkthrough, CI, ops | authz, pii, db_schema, data_migration |

### Autonomy Bias

| Bias | low → | medium → | high → |
|------|-------|----------|--------|
| **autonomous** | autopilot | autopilot | confirm |
| **balanced** (default) | autopilot | confirm | validate |
| **controlled** | confirm | validate | validate |

> `tier_mode_minimum` により、autonomous でも critical tier は最低 confirm が保証。

### Profile（報告粒度 + Completeness 閾値の切替、v5.4）

Profile は「Constitution Articles を守りながら、**報告の冗長さと Completeness 閾値**を現場に応じて切替」する軸。
Mode（autopilot/confirm/validate）が「WI 単位のチェックポイント量」を決めるのに対し、
Profile は「Task Completion Report のフォーマット」と「湖/海判定の閾値」だけを切り替える。

**Profile で切り替わるもの（v5.4）:**
- Task Completion Report: `full_5_step` / `critical_only` / `one_line`
- Completeness 閾値: 200/150/100 行 × 5/4/3 ファイル（AND）

**Profile で切り替わらないもの（全 Profile 共通、v5.4 では現行正本のまま維持）:**
- BPMN 必須（`agent_docs/sdd_bootstrap.md` §4-BPMN の現行ルール）
- Evidence Pack（`memory/tecnos_org_constraints.md` §6.5 + `ops_template.md` の現行記述）
- SEC-006 Provenance（`stride_security_checker` SEC-006 の現行 6 キーワード）
- Epic-Feature Hierarchy（Constitution Article X の現行ルール）
- Ops Pack（現行テンプレ・ガイドの条件）
- Coverage Tier 宣言（`basic_design.coverage_tier` の現行ルール）

| Profile | 想定ユースケース | 報告形式 | 湖/海閾値 |
|---------|-----------------|---------|----------|
| `enterprise-erp` (default) | SAP/mcframe/Salesforce 導入、監査対象 | 5-step full | +200 行 / +5 ファイル |
| `saas-integration` | 連携業務 SaaS、API/Event 中心 (例: CBP v3) | critical のみ 5-step、他は 1-line | +150 行 / +4 ファイル |
| `prototype` | 社内 PoC、innovation 推進部 | 1-line summary | +100 行 / +3 ファイル |

機械検証は Profile を跨いで**同一**（`stride-lint` PASS + `stride pr-check` PR_READY）。Profile は人間向けレポートの冗長さのみを切り替える。

```bash
# CLI で選択
stride init <feature> --profile enterprise-erp    # default
stride init <feature> --profile saas-integration
stride init <feature> --profile prototype

# または basic_design.md の basic_design.profile で直接宣言
# SSoT: basic_design.profile、state.yaml top-level profile はキャッシュ
# 不整合時は stride lint が PROFILE_MISMATCH を出す
```

詳細: `shared/policies/profile_policy.yaml`、`manual/38_profile_guide.md`

### Coverage Tier

| Tier | AC | CT | E2E | Ops Pack |
|------|----|----|-----|----------|
| **critical** | 100% | 100% | 必須 | 必須 |
| **standard** | 100% | 80% | 任意 | 必須 |
| **experimental** | 80% | 60% | 不要 | 必須 |

---

## ディレクトリ構成

```
project-root/
├── CLAUDE.md                 # AI エントリーポイント（→ sdd_bootstrap.md）
├── CLAUDE_WORKFLOW.md        # Claude Code 固有設定
├── SDD_MANIFESTO.md          # ツール非依存 SDD コアルール
├── SYMPHONY.md               # Symphony オーケストレーション設定 + プロンプト
├── agent_docs/               # AI Agent ガイド（bootstrap, commands, conventions, testing）
├── specs/                    # Feature 仕様（開発成果物が入る場所）
├── epics/                    # Epic 設計・進捗管理
├── memory/                   # Constitution・組織制約・承認マトリクス
├── shared/                   # ADR・共有ポリシー
├── sdd-templates/            # テンプレートキット
│   ├── bin/stride            #   CLI（19 サブコマンド、symphony/epic/linear/project のサブ含めず）
│   ├── templates/            #   40+ テンプレート
│   ├── tools/                #   31 検証ツール（v5.2 stride_shared_lib / v5.3 linear_bridge / v5.3.1 github_project_bridge を追加、v5.4 は既存ツール拡張のみ）
│   ├── config/               #   Monorepo / Docker / K8s / Terraform / TypeScript
│   ├── hooks/                #   Phase Gate hook + PostToolUse Guard
│   └── policies/             #   BPMN ルール + Camunda 8.8 LLM Dictionary
├── symphony/                 # Symphony オーケストレーションエンジン
├── manual/                   # Docsify マニュアル（38章 + 付録4章）
├── scripts/                  # 運用スクリプト
└── docs/                     # 運用ガイド + BPMN/統合テストサンプル
```

### Feature 仕様の構造

```
specs/<feature>/
├── basic_design.md          # WHAT/WHY + bpmn_descriptions（Phase 1）
├── process.bpmn             # 業務プロセス — Camunda 8.8 executable + laneSet（Phase 1）
├── APPROVAL.md              # Gate 承認 — Human-only ⛔
├── spec.md                  # AC / NFR（Phase 2）
├── plan.md                  # 実装方針（Phase 2）
├── contracts/               # OpenAPI 等（Phase 2）
├── tasks.md                 # タスク定義（Phase 3）
├── work_items/              # WI 定義・承認（Phase 4）
├── runs/                    # Run 証跡（Phase 4）
├── state/state.yaml         # WI 進捗の単一真実源
├── ops/                     # Ops Pack（輸送/リリース/ロールバック/ハイパーケア）
├── tests/                   # テスト資産
└── implementation-details/  # Evidence Pack 等
```

### Epic の構造

```
epics/<EPIC>/
├── epic_design.md           # Epic 設計 + epic_flow_descriptions
├── epic_flow.bpmn           # Epic 概観 — collaboration + participant(pool)（overview）
├── feature_breakdown.md     # Feature 分割
├── EPIC_APPROVAL.md         # Epic 承認 — Human-only ⛔
├── EPIC_PROGRESS_REPORT.md  # 進捗レポート
├── DEPENDENCY_MANIFEST.yaml # チーム間依存
└── OPS_PACK_REGISTRY.yaml   # Ops Pack 管理
```

### BPMN の使い分け

| 種別 | ファイル | 目的 | レイアウト | 検証 |
|------|---------|------|-----------|------|
| **FEAT** | `process.bpmn` | 単一 Feature の実装フロー | 単一 `process` + `laneSet`（縦レイアウト） | `stride_lint.py` |
| **EPIC** | `epic_flow.bpmn` | チーム間・システム間の連携概観 | `collaboration` + `participant(pool)`（縦レイアウト） | `epic_validator.py` |

- `stride init <feature>` は `basic_design.md` と `process.bpmn` を生成し、FEAT BPMN は Camunda 8.8 executable として `basic_design.md` の `bpmn_descriptions` と双方向連動
- `stride epic init <EPIC_ID>` は `epic_design.md` と `epic_flow.bpmn` を生成し、EPIC BPMN は overview/planning 用として `epic_design.md` の `epic_flow_descriptions` と双方向連動
- 説明の正本は Canonical YAML、BPMN 側は `bpmn:documentation` を機械可読な第2正本として保持。`Text Annotation` は補足用途のみ
- 詳細: `docs/camunda_bpmn_practice_guide.md`、`manual/10_bpmn_guide.md`、`docs/archive/prompts-history/camunda_bpmn_description_alignment_prompt.md`
- 実例: `docs/examples/sap-s4hana/sap_sd_order_to_cash_epic_flow.bpmn`、`docs/examples/sap-s4hana/sap_sd_delivery_request_process.bpmn`、`docs/examples/sap-s4hana/s4hana_fi_scratch_core_integration_epic_flow.bpmn`

---

## VALUE Upstream Extension v6.0 (Phase A → G 完成形 + Method Store Publishing 拡張)

v6.0 (`6.0.0-tecnos-stride-value`, 2026-04-29 起点) で **VALUE Upstream Extension** を Phase A → B → C → bugfix v7 → D → E → F → **G + BPMN Package + Method Store Publishing + Agent Hardening** の **七段階 + 1 bugfix + 3 拡張** で完成。Discovery / Elicit / Context Modelling の上流フェーズを **BABOK v3 + Layered Requirements Modeling + value-driven discovery (philosophical foundation)** の三脚で機械検証可能にし、Phase 1 (Design) との接続 + 稼働後評価 (BABOK KA8) + 普及準備 (3 profile playbook + Migration Guide) + Cowork Plugin 化 (上位コンサル単独で Phase 0/1 完成可能、v0.5.0-agent-hardening) + brand-neutral 用語清拭 + Simple UX (`/start` 1 コマンド) + BPMN 標準パッケージ独立化 + Method Store OCI 配信 (cosign keyless + 3 channel) + agent failure mode 構造的 hardening (SKILL.md STEP 0 PRE-FLIGHT + bpmn_lint v1.1 + bd_bpmn_sync + render_ascii_preview) まで一気通貫で自動化する。Tecnos-STRIDE 本体 VERSION は **6.0.0-tecnos-stride-value 維持** (Phase D 以降は本体不変、機能追加のみ)、Cowork Plugin は **独立 SemVer (0.1.0-poc → 0.2.0-stable → 0.3.0-simple-ux → 0.3.1 → 0.3.2 → 0.4.0-bpmn-package-integration → 0.5.0-agent-hardening)**、BPMN Pack も **独立 SemVer (1.0.0 → 1.1.0)**。

### 7 段階 + 1 bugfix + 2 拡張 ロードマップ

| Phase | Feature ID | リリース | PR | 主成果 |
|-------|-----------|---------|----|---------|
| **A** | FEAT-VALA01 | v5.4 系 (2026-04) | [#1](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/1) | **Schema 基盤**: 4 policies (`upstream_policy.yaml` / `baccm_completeness.yaml` / `technique_library.yaml` 50 BABOK techniques / `upstream_iteration_policy.yaml`) + 16 artifact YAML templates (`sdd-templates/templates/upstream/`) + 3 proposed amendments + 4 manuals (39-42) + 5 tests |
| **B** | FEAT-VALB01 | v5.5 (2026-04-29) | [#3](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/3) | **CLI scaffold + lint/eval extension**: 5 Python tools (`upstream_scaffolder` / `baccm_completeness_checker` / `upstream_iteration_evaluator` / `technique_library_query` / `upstream_lint`) + `stride upstream init/validate` 新サブコマンド + `stride lint --upstream` + `stride evaluate --phase discovery` + 4 stride_lint 新エラーコード (BACCM_INCOMPLETE / Layered Requirements Modeling_BROKEN_LINK / UPSTREAM_TEMPLATE_DRIFT / BABOK_TECHNIQUE_UNKNOWN) + 15 JSON Schema (Draft 2020-12) + 2 manuals (43, 44) + 7 tests |
| **C** | FEAT-VALC01 | **v6.0 (2026-04-29)** | [#4](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/4) | **統合 + Constitution body merge**: `stride upstream-bridge` (Phase 0/0.3/0.5 → Phase 1 自動 populate, Gate 1/2 immutability check) / `stride retro --solution-eval` (BABOK KA8 稼働後評価) / Constitution `articles[]` に Article XV-XVII を本体マージ + amendments status proposed → ratified + version 5.4.0 → 6.0.0-tecnos-stride-value **MAJOR bump** + 3 manuals (45-47) + 41 tests (758 total) |
| **bugfix v7** | (post-Phase C) | v6.0 (2026-04-30) | [#8](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/8) | **YAML frontmatter compatibility**: `yaml.safe_load` vs frontmatter 競合の修正 — `stride_shared_lib.py` helper + 6 tools 改修 + 1 test (`test_yaml_frontmatter_compatibility.py`) |
| **D** | FEAT-VALD01 | v6.0 (2026-04-30) | [#9](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/9) | **普及準備**: 3 profile 別 playbook (`manual/48-50_*_value_playbook.md`、各 3000-5000 字 6 章) + v5.x → v6.0 Migration Guide (`manual/migration/v54_to_v60.md`) + `upstream_migration_helper.py` (basic_design.md → Phase 0 yaml seed 半自動逆生成 CLI、BACCM 6 軸ごとに自動抽出 vs 要人間確認をラベル付与) + dogfooding sanitized 学び (`memory/lessons_learned/upstream_dogfooding/external_scm_pilot_01.md`) + 9 tests (baseline 769 → 778 passed)。「使える状態」から「使われる状態」へ |
| **E** | FEAT-VALE01 | v6.0 (2026-04-30) | [#10](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/10)/[#11](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/11)/[#12](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/12)/[#13](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/13) | **Cowork Plugin v0.1.0-poc**: `cowork-plugin/` ディレクトリで Anthropic 公式 `knowledge-work-plugins` 仕様準拠プラグイン。Skills 7 (baccm-discovery / babok-elicitation / layered-context-modelling / upstream-bridge / basic-design-authoring / bpmn-authoring / epic-decomposition) + Slash Commands 9 (stride-{init,discovery,elicit,context-model,validate,bridge,design,epic-init,handoff}) + reference_files 49 + MCP filesystem/github + manual/51 (11 章) + 8 tests (baseline 778 → 788 → 789 passed、PR #11 で `repository` field string 修正、PR #12 で marketplace.json 追加、PR #13 で manual/51 + README を実機検証 install フローに整合)。**上位コンサル (非技術者) が Cowork で Phase 0 → Phase 1 を直接執筆できる、上下流完全分業の起点** |
| **F** | FEAT-VALF01 | v6.0 (2026-05-01) | [#14](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/14) | **Cowork Plugin v0.2.0-stable**: fc-sd 実機運用で発見された 16 件改善要望を 17 WI で反映、Plugin **v0.1.0-poc → v0.2.0-stable** (本体 6.0.0 不変)。CI 統合 (`.github/workflows/cowork-plugin-validate.yml` で PR の Plugin 関連変更を path filter 自動検証) + Cowork セッション内 4 ファイル機械検証 (handoff workflow) + §Rule 15-B サニタイズ自動 grep + state.yaml `phase_2/3/4/final` schema 拡張 (+3 tests) + HTML 出力 (`scripts/build_basic_design_html.py` + `/stride:export-html`) + Phase 3 連結 (`/stride:tasking`) + 7 SKILL description 固有語必須化 (誤起動回避) + `cowork-plugin/scripts/` 補助スクリプト同梱 + `.claude-template/settings.json` 推奨値配布。commands **9 → 11**、reference_files **49 維持** (新規ディレクトリは別計上)、テスト 789 → **792 passed** (回帰 0)。WI-006/007 (saas-integration/prototype dogfooding) + WI-012 (GitHub MCP 実 API 検証) は scaffold 完成 + [Issue #15](https://github.com/tecnos-japan-cbp/tecnos-stride/issues/15) で Phase G 入口 follow-up tracking |
| **G** | (Phase G) | v6.0 (2026-05-07) | [#18](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/18) / [#19](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/19) / [#20](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/20) / [#21](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/21) / [#22](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/22) / [#23](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/23) / [#24](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/24) / [#25](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/25) | **Brand-Neutral + Simple UX**: 7 連続 PR で Plugin 体験を磨き上げ、**Plugin v0.2.0-stable → v0.3.0-simple-ux → v0.3.1 → v0.3.2** (本体 6.0.0 不変)。**(PR-A #18)** Plugin 内部の RDRA / 匠Method 等の固有名称を考え方ベース brand-neutral 用語に置換。**(PR-B #19)** 本体 docs + reference_files の同様除去。**(PR-C #20)** Constitution Article XVI 文言 brand-neutral rephrasing + code-level error code rename。**(PR-D #21)** `stride-bootstrap-repo` command 新設 (Cowork → Claude Code 継ぎ目のない 1 コマンド bootstrap)。**(marketplace #22)** marketplace.json 0.1.0-poc → 0.2.0-stable bump。**(PR-E #23)** **`/start` コマンド新規** — 日本語ひとこと指示で Plugin が状態を理解して進める conductor 設計、`stride-conductor` skill 追加 (skills 7 → 8)、複雑だった UX を Anthropic 公式パターンに整合。**(PR-F #24)** stride-start.md → start.md rename hotfix。**(PR-G #25)** Plugin docs example の顧客固有名詞 placeholder 化 sanitize hotfix |
| **BPMN Pack 拡張** | (extension) | v6.0 (2026-05-07、bpmn/ v1.0.0) | b8aec09 + 6acd3fe (直接 commit) | **BPMN Standalone Package + Plugin v0.4.0**: **(b8aec09)** BPMN 作成基盤を `bpmn/` 配下に独立パッケージ化 — 24 章 ruleset (`rules/bpmn_generator_rules.md` Camunda 8 適用ルール全仕様 + `rules/bpmn_quick_reference.md` 1-page checklist + `rules/camunda_bpmn_practice_guide.md` Standard/Advanced/Deferred 区分) + Camunda 8.9 spec 完全辞書 (`spec/camunda_bpmn_dictionary_complete.md` 2744 行、OMG BPMN 2.0 + Camunda 8.9 全要素) + FEAT/EPIC templates (BPMN-* ID 命名 / vertical layout / pool 構造) + examples (basic + advanced) + `validators/bpmn_lint.py` (stdlib のみ、FEAT 14 + EPIC 9 MUST-DO 検証 CLI、auto-detect FEAT vs EPIC) + README + PORTABILITY.md + CHANGELOG + VERSION 1.0.0。**(6acd3fe)** Cowork Plugin **v0.3.2 → v0.4.0-bpmn-package-integration** — `cowork-plugin/bpmn/` に first-class component として配置 (Skills / Commands / reference_files と並列の自己完結 component)、Plugin install で BPMN 作成基盤一式が自動同梱、`/stride:bpmn-validate` 新規 command (FEAT 14 / EPIC 9 MUST-DO 自動検証)、reference_files から BPMN 重複削除 (drift 防止、git rename detection で 4 件移動)、commands **11 → 14** (start + stride-bootstrap-repo + stride-bpmn-validate)、skills **7 → 8** (stride-conductor)、reference_files **49 → 45** (BPMN 4 件 → bpmn/ へ移動) |
| **Agent Hardening 拡張** | (incident response) | v6.0 (2026-05-08) | [#29](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/29) | **2026-05-08 BPMN vertical-flow violation incident への構造的 hardening**: simple-bi PoC で発生した 7 件の canonical 違反 (ユーザ目視レビューが唯一の発見ルート) への 7-task structural guard。SKILL.md auto-trigger ≠ SKILL.md body load の failure mode を防止。**(1)** 全 7 specialized SKILL.md に STEP 0 PRE-FLIGHT (MANDATORY) ブロック挿入 (必須 Read リスト + template-copy 強制 cp + ANTI-PATTERN 表 + PRE-FLIGHT REPORT フォーマット)。**(2)** `bpmn/PRE_FLIGHT_CHECKLIST.md` 1-page checklist 新設 (7 セクション、agent submit format 確定)。**(3)** `bpmn_lint.py` v1.0→v1.1 強化: `BPMN_ID_FORMAT_VIOLATION` (^BPMN-(TASK\|GW\|EVT\|FLOW)-\\d{3}$) + `BPMN_ID_NON_TECNOS_SCHEME` warning (backward compat) + `--legacy-id` (transition flag) + `--diff-against-template` flag + 全 error に fix_hint+refs。**(4)** `bd_bpmn_sync.py` v1.0 新設 (basic_design.md ↔ process.bpmn id 双方向 sync 検証、stdlib のみ)。**(5)** `render_ascii_preview.py` v1.0 新設 (BPMNDI 座標 → ASCII grid、vertical/horizontal orientation 視覚判別)。**(6)** stride-conductor SKILL.md + commands/start.md に dispatch 前 SKILL.md Read 強制 5-step protocol (bpmn-authoring のみ 2 ファイル mandatory)。**(7)** `docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md` 起票 (7 違反 / 主因 3 件 / Action Items / 運用面の申し送り)。**Plugin v0.4.0 → v0.5.0-agent-hardening、BPMN Pack v1.0.0 → v1.1.0** (本体 6.0.0 維持)。CI 連動 fix: `cowork-plugin-validate.yml` の skill/command/ref_files threshold 更新 + plugin tests count update + `sync_cowork_plugin_reference.sh` を v0.4.0 BPMN integration に追従 |
| **Method Store Publishing 拡張** | FEAT-METHODSTOREPUBLISHING | v6.0 (2026-05-08) | [#26](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/26) + [#27](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/27) | **OCI artifact 配信パイプライン**: SDD Phase 1-Final 全 Gate 承認下で実装した最初の **本体機能拡張型 SDD Feature**。Method content の OCI artifact 化 + cosign keyless signing (Sigstore Fulcio + Rekor + GitHub Actions OIDC) + ghcr.io 配信を 1-cmd で起動。**(PR #26 commit 684c948)** **5 stride method subcommands** (preview / validate / diff / publish / rollback、+ 1 implicit drift) を `sdd-templates/bin/stride` に追加 + `sdd-templates/tools/method_publish/` Python package (12 modules: snapshot_builder, cosign_signer, oci_publisher, publish, release_notes_generator, rollback, drift_detector, tenant_policy_validator, preview, validate, diff, __init__) + `sdd-templates/tools/ci_helpers/` (gitops_pr_creator + slack_notifier) + `.github/workflows/method-store-publish.yml` 9-step CI pipeline (validate → snapshot_build → cosign sign → ghcr.io push → channel branch → smoke or auto PR → live → notify、permissions 最小化 + workflow injection 防御済) + **3 contracts** (CT-CLI-02 5-subcommand schema / CT-FILE-02 RELEASE_NOTES + 3-person METHOD_APPROVAL template / CT-FILE-03 `shared/policies/sdd_tenant_policy_schema.yaml` cross-repo SSoT、JSON Schema Draft 2020-12) + 3 channel (edge {sha7} / staging v{semver}-rc.N / stable v{semver}) + Method Board 3 person 多人数署名 + 5 min MTTR rollback + tenant policy auto_upgrade (none/patch/minor)。22/22 unit test PASS、Evidence Pack 8 artifacts (CI/SAST/SCA/Secrets/AI provenance + cosign + Rekor transparency log) + walkthrough.md。**(PR #27 commit bbfe46b)** F3 (`sdd_method_gateway_poc` on cbp-core 別 repo) 着手用の **planning doc v1.2.1 完成** (`.planning/claude_code_instruction_sdd_method_gateway.md` 1499 行、F1+F2 確定情報 + ID convention 20 種 regex + Phase Gate 実機仕様 + F2 follow-up 7 issue を反映、independent reviewer による Critical 3 + Important 5 件の整合性問題を全件解消後 merge)。F3 = CBP-on-EKS 上の MCP services (sdd-method-service / sdd-output-guard / sdd-stride-engine) 実装は別 session で cbp-core 側で実行予定 |

### Constitution 17 Articles 体制 (v6.0 で 14 → 17)

```
I-XIV   ─ 既存原則 (SSoT / Spec-First / Trace / Phase Gate / Mode / RACI+ / ED-CF / Schema-Gated AI Authority 等)
XV      ─ ★ NEW (v6.0) BACCM Completeness Gate            (BABOK v3)
XVI     ─ ★ NEW (v6.0) Layered Requirement Architecture   (Layered Requirements Modeling 4-layer aligned)
XVII    ─ ★ NEW (v6.0) Solution Evaluation Feedback Loop  (BABOK KA8)
```

詳細仕様は `memory/constitution.md`、各条文の根拠と歴史は `memory/constitution_amendments/{XV,XVI,XVII}_*.md` (Status: ratified, 2026-04-29, Phase C, FEAT-VALC01)。

### Upstream Phase 構造 (任意、有効化時のみ)

```
specs/<feature>/upstream/
├── phase_0_discovery/                # Phase 0 (BABOK KA6 — Strategy Analysis)
│   ├── business_need.yaml            # 目標 KPI (success_criteria) — KA8 評価の基準
│   ├── value_canvas.yaml
│   ├── stakeholder_map.yaml          # 最小 3 stakeholders (Article XV)
│   ├── goal_tree.yaml
│   ├── change_strategy.yaml
│   ├── context_map.yaml
│   └── risk_register.yaml
├── phase_0_3_elicit/                 # Phase 0.3 (BABOK KA4 — Elicitation)
│   ├── elicitation_plan.yaml
│   └── elicitation_results.yaml
└── phase_0_5_context_modelling/      # Phase 0.5 (BABOK KA7 + 4-layer Requirements Architecture)
    ├── actor_system.yaml
    ├── business_usecase.yaml
    ├── information_state.yaml
    ├── condition_variation.yaml
    ├── usecase_complex.yaml
    └── requirements_architecture.yaml
```

`stride upstream-bridge <feature>` が完了時に dry-run で populate 計画 + BPMN-TASK-NNN 候補リストを stdout Markdown で出力、`--apply` で Phase 1 `basic_design.md` の `links` フィールドにのみ実書込 (process.bpmn / implementation-details/* は不変、Gate 1/2 未承認 feature にのみ許可)。

### 既存 v5.x プロジェクトへの影響

- **新規 feature**: `stride init <feature>` の scaffold が自動的に v6.0 仕様を継承 (basic_design_template.md links に upstream 3 参照含む)
- **既存 feature**: Phase 0 を使わなければ完全互換 (任意機能、有効化時のみ Article XV-XVII の機械検証が走る)
- **Migration**: Phase D (PR #9) で `sdd-templates/tools/upstream_migration_helper.py` を **完成済**。既存 v5.x プロジェクトの `basic_design.md` を逆解析して Phase 0 yaml seed を半自動生成、BACCM 6 軸ごとに「自動抽出可能」「要人間確認」のラベル付き。詳細: [`manual/migration/v54_to_v60.md`](manual/migration/v54_to_v60.md)
- **Cowork Plugin (Phase E/F)**: 上位コンサル単独で Phase 0/1 を実行する場合は、Tecnos-STRIDE clone 後に `claude plugin marketplace add "$(pwd)" && claude plugin install tecnos-stride-value@tecnos-stride` で Plugin install (詳細: [`manual/51`](manual/51_cowork_plugin_install_guide.md) + [`manual/52`](manual/52_phase_f_lessons_learned.md))

詳細ガイド:
- 上流概念: [`manual/39_value_upstream_overview.md`](manual/39_value_upstream_overview.md)
- BACCM 完全性: [`manual/40_baccm_guide.md`](manual/40_baccm_guide.md) / [`manual/41_layered_requirements_modeling_guide.md`](manual/41_layered_requirements_modeling_guide.md)
- ウォークスルー: [`manual/42_upstream_phases_walkthrough.md`](manual/42_upstream_phases_walkthrough.md)
- CLI: [`manual/43_upstream_cli_guide.md`](manual/43_upstream_cli_guide.md) / [`manual/44_upstream_iteration_workflow.md`](manual/44_upstream_iteration_workflow.md)
- Bridge / KA8 / Release: [`manual/45_upstream_bridge_guide.md`](manual/45_upstream_bridge_guide.md) / [`manual/46_solution_evaluation_guide.md`](manual/46_solution_evaluation_guide.md) / [`manual/47_v60_release_notes.md`](manual/47_v60_release_notes.md)
- Profile playbook (Phase D): [`manual/48_enterprise_erp_value_playbook.md`](manual/48_enterprise_erp_value_playbook.md) / [`49_saas_integration_value_playbook.md`](manual/49_saas_integration_value_playbook.md) / [`50_prototype_value_playbook.md`](manual/50_prototype_value_playbook.md)
- Cowork Plugin (Phase E/F): [`manual/51_cowork_plugin_install_guide.md`](manual/51_cowork_plugin_install_guide.md) / [`manual/52_phase_f_lessons_learned.md`](manual/52_phase_f_lessons_learned.md)

---

## stride CLI

```bash
# プロジェクト管理
stride new-project <name> [--org <org>] [--scale <level>]
stride intake <feature>                  # 対話式ヒアリング（推奨）
stride init <feature> [--detect] [--scale <level>] [--profile <name>]  # Feature 作成（basic_design.md + process.bpmn + state/state.yaml + tests/scenarios.yaml、v5.4 で --profile を追加）
stride hooks --tool <claude|cursor|copilot|manual>

# 開発フロー
stride lint specs/<feature>/ [-o json|ndjson] [--plain] [--no-color] [--coverage-report] [--warn-only]
stride lint --all [--enterprise] [-o json|ndjson] [--plain]
stride lint --changed <git-range> [-o json|ndjson]
stride evaluate specs/<feature>/ --phase <design|specify|tasking>  # LLM 意味的評価
stride phase-status [<feature>]
stride auto-continue specs/<feature>/
stride pr-check . [--json] [--summary-line] [--strict]   # v5.4 で --summary-line 追加（project-level 1-line、7 base checks + optional mutation）
stride security specs/<feature>/ --daily      # 軽量セキュリティチェック（confidence >= 8）
stride security specs/<feature>/ --audit      # 総合セキュリティ監査（全10チェック）
stride retro specs/<feature>/                 # 定量ふりかえりレポート
stride retro epics/<EPIC_ID>/                 # Epic 横断ふりかえり

# VALUE Upstream Extension (v6.0, Phase A/B/C — BABOK v3 + Layered Requirements Modeling align)
stride upstream init <feature> --phase <discovery|elicit|context_modelling> [--profile <name>]   # Phase 0/0.3/0.5 成果物 scaffold (v5.5 Phase B)
stride upstream validate <feature> [--phase <name>]                                              # BACCM 6 軸 + 4-layer Requirements Architectureの完全性検証 (v5.5 Phase B)
stride upstream-bridge <feature> [--target phase1] [--apply]                                     # Phase 0/0.3/0.5 → Phase 1 自動 populate (v6.0 Phase C、Gate 1/2 immutability check)
stride lint specs/<feature>/ --upstream                                                          # upstream/ も含めた拡張 lint (v5.5 Phase B、4 新エラーコード: BACCM_INCOMPLETE / Layered Requirements Modeling_BROKEN_LINK / UPSTREAM_TEMPLATE_DRIFT / BABOK_TECHNIQUE_UNKNOWN)
stride evaluate specs/<feature>/ --phase discovery                                               # LLM 意味的評価を Discovery 範囲で (v5.5 Phase B)
stride retro <feature> --solution-eval [--kpi-source <path>] [--adoption-survey <path>]         # BABOK KA8 稼働後評価 (v6.0 Phase C、KPI/Adoption/Issues 集計)

# 拡張
stride ddd-init <feature>
stride decisions init|refresh
stride output-rules

# Enterprise Hierarchy (enterprise.enabled: true)
stride epic init <EPIC_ID>             # Epic 作成（epic_design.md + epic_flow.bpmn）
stride epic validate <EPIC_ID>         # Epic 検証
stride epic gates <EPIC_ID>            # Epic Gate 状態
stride epic features <EPIC_ID>         # Feature 一覧
stride epic progress <EPIC_ID>         # 進捗サマリ表示 (--format markdown --output <path> でファイル生成)
stride epic list                       # Epic 一覧
stride init <feature> --epic <EPIC_ID> # Epic 配下に Feature 作成
stride lint specs/<feature>/ --enterprise   # Feature の Enterprise 拡張検証も実行
stride lint --all --enterprise              # 全 Feature + Epic を一括検証

# Symphony Orchestration（v5.2 で bin/stride から完全 dispatch）
stride symphony run [--once] [--dry-run]       # polling ループ起動
stride symphony dispatch --issue <number>      # 単一 Issue 手動起動
stride symphony status                         # Issue 状態表示
stride symphony validate                       # SYMPHONY.md 設定検証
stride symphony janitor [--dry-run]            # Janitor 単発スキャン（v5.1）

# Linear Integration（v5.3、LINEAR_API_KEY 設定時のみ／未設定時 graceful skip）
stride linear init <feature> <wi>              # Linear Issue 作成/検索 → state.yaml 同期
stride linear sync <run_dir>                   # findings + evidence + lessons を一括 comment
stride linear findings|evidence|learn <run>    # 個別に Linear コメント投下
stride linear close <feature> <wi>             # Linear Issue を Done 遷移
stride linear status <feature> [<wi>]          # WI → Linear Issue マッピング
stride linear project create <name>            # Linear Project 作成 → memory/linear.yaml (v5.3.1)
stride linear project list|use|status          # Linear Project binding 管理

# GitHub Project V2 Binding（v5.3.1、`gh auth` 認証時のみ）
stride project create <title> [--owner <o>]    # Project V2 作成 → memory/github_project.yaml
stride project list|use|status                 # GitHub Project V2 binding 管理

# New project bootstrap — per-project tracker も同時作成（v5.3.1）
stride new-project my_erp --org my-org \
  --linear-project "my_erp" \
  --github-project "my_erp SDD Board"
```

### ツール一覧（41 Python ファイル、v6.0 で +7 — VALUE Upstream Extension。test ツール 2 件含む）

| ツール | 用途 | self-test |
|--------|------|-----------|
| `multi_model_evaluator.py` | LLM 意味的評価（ERP blind spots, SoD, AC testability）+ Self-Review Loop + `--phase discovery` (v5.5) | ✓ (API) |
| `stride_lint.py` | SDD lint（カラー/TSV/JSON/NDJSON出力、パスtypoサジェスト、YAML事前検証、アクター追跡）| — |
| `stride_shared_lib.py` **(v5.2)** | Canonical YAML 抽出共通ライブラリ（5 caller を集約） | 8 tests |
| `linear_bridge.py` **(v5.3 新規)** | Linear Issue 同期 (init/findings/evidence/learn/sync/close/status) + Project 管理 (v5.3.1) | 19 tests |
| `github_project_bridge.py` **(v5.3.1 新規)** | GitHub Project V2 binding (create/list/use/status) via gh CLI | 10 tests |
| `epic_validator.py` | Epic 設計 + epic_flow.bpmn 軽量検証 | — |
| `phase_gate.py` | Phase Gate 必須成果物・承認状態検証 | — |
| `pr_readiness_checker.py` | PR 品質ゲート（7チェック + opt-in mutation testing） | 10 tests |
| `stride_health.py` | Runtime Sensors（dead code + coverage decay）| 6 tests |
| `stride_harness_report.py` | Harness Report（8 controls 可視化） | 6 tests |
| `spec_drift_detector.py` | contracts/ vs src/ 乖離検出 | 6 tests |
| `evidence_metrics_collector.py` | カバレッジ・テスト推移計測 | 6 tests |
| `stride_security_checker.py` | セキュリティ監査（daily/audit 2段階, 10チェック）| 8 tests |
| `stride_retro.py` | 定量ふりかえりレポート（Feature/Epic）| 6 tests |
| `wi_readiness_checker.py` | WI 実行準備チェック（Check 8 = Execution Authority） | 17 tests |
| `run_resume_detector.py` | 中断 Run 再開検出 | 6 tests |
| `brownfield_detector.py` | 既存スタック検出 | 8 tests |
| `epic_progress_aggregator.py` | PM ダッシュボード生成 | 20 tests |
| `sdd_planning_bridge.py` | Planning Bridge（init/sync/evidence/learn） | 6 tests |
| `post_edit_guard.py` | PostToolUse 軽量品質ガード | 8 tests |
| `stride_process_metrics.py` | プロセスメトリクス | 51 tests |
| `auto_continue_runner.py` | Auto-Continue シーケンス | 4 tests |
| `decision_index.py` | ADR インデックス管理 | 3 tests |
| `erp_addon_exec_tracking.py` | ERP Addon WI/Run 検証 | ✓ |
| `stride_wi_sync.py` | GitHub Issues ↔ WI 同期 | — |
| `amendment_generator.py` | Spec Amendment 生成 | 61 tests |
| `run_report_generator.py` | Run Report 生成 | 54 tests |
| `setup_project_labels.py` | GitHub ラベル一括登録 | 41 tests |
| `upstream_scaffolder.py` **(v5.5 Phase B)** | Phase 0/0.3/0.5 YAML 成果物 scaffold | 7 tests |
| `baccm_completeness_checker.py` **(v5.5 Phase B)** | BACCM 6 軸完全性検証 | 9 tests |
| `upstream_iteration_evaluator.py` **(v5.5 Phase B)** | Upstream 3 反復パターン評価 | 5 tests |
| `technique_library_query.py` **(v5.5 Phase B)** | BABOK 50 techniques 検索 | 6 tests |
| `upstream_lint.py` **(v5.5 Phase B)** | upstream/ 配下の拡張 lint (Layered Requirements Modeling broken link 等) | 11 tests |
| `upstream_bridge.py` **(v6.0 Phase C)** | Phase 0/0.3/0.5 → Phase 1 自動 populate (Gate immutability check 内蔵) | 13 tests |
| `solution_evaluator.py` **(v6.0 Phase C)** | BABOK KA8 稼働後評価 (KPI/Adoption/Issues 集計) | 9 tests |
| その他 5 ツール | 承認ルーティング, Enterprise lint, 依存チェック, etc. | — |

---

## Multi-Tool 対応

Claude Code 以外の AI ツールでも利用可能です：

```bash
stride hooks --tool cursor   # .cursor/rules/ に Phase Gate ルール生成
stride hooks --tool copilot  # .github/copilot/ に指示ファイル生成
stride hooks --tool manual   # チェックリスト形式で出力
```

SDD のコアルールは `SDD_MANIFESTO.md`（ツール非依存）に記載。
Claude Code 固有設定は `CLAUDE_WORKFLOW.md` に分離されています。

---

## Multi-Model Evaluator（LLM 意味的評価）

`stride evaluate` は `stride lint` の補完として、**LLM が「lint では検出できない意味的な穴」を評価**するゲートです。

```bash
stride evaluate specs/<feature>/ --phase design    # Design Phase 評価
stride evaluate specs/<feature>/ --phase specify   # Specify Phase 評価
stride evaluate specs/<feature>/ --phase tasking   # Tasking Phase 評価
```

### 評価対象（lint が見ないもの）

| Phase | 評価軸 |
|-------|--------|
| **Design** | ERP blind spots / AC testability / Integration architecture / Scope defensibility |
| **Specify** | Cross-artifact consistency / NFR feasibility / Test scenario quality / Audit gaps |
| **Tasking** | Implementation risk / Coverage completeness / Estimation realism |

### アーキテクチャ

```
Compact Packet（Canonical YAML のみ）
  ↓
Primary Model（OpenAI）──→ JSON score + critical_issues
  ↓                           ↓
  ├── Clear FAIL ────────→ FAIL（exit 1）
  ├── Clear PASS ────────→ PASS（exit 0）
  └── Borderline ────────→ Secondary Model（Gemini）で Tie-break
                              ├── Secondary FAIL → FAIL
                              └── Secondary PASS → WARN（exit 0）
```

### FAIL 条件（3つの OR）

1. `weighted_score < 70`
2. いずれかの `critical_issues` に `severity: "critical"` がある
3. いずれかの criterion score が `< 50`（hard floor — 弱い軸が平均に隠れない）

### 設定

`.env.local` に API キーとモデル名を設定（`.gitignore` 対象）:

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.4
OPENAI_REASONING_EFFORT=xhigh

GEMINI_MODEL=gemini-3.1-pro-preview    # 空なら secondary 無効
GEMINI_API_KEY=AIza...                 # 空なら Vertex AI (ADC)
GEMINI_THINKING_BUDGET=-1              # -1 = dynamic
```

```bash
pip install -r sdd-templates/requirements-ai-eval.txt  # openai, google-genai
```

### ワークフロー統合

`auto_continue_runner.py` の各フェーズに evaluator ステップが組み込み済み:

```
lint PASS → evaluate PASS → HITL Gate 承認待ち
```

`coverage_tier=starter` の feature は自動スキップ（コスト最適化）。`--force` で強制実行可。

📖 **詳細**: [manual/32_multi_model_evaluator_guide.md](manual/32_multi_model_evaluator_guide.md)

---

## 統合テスト

792 テストの pytest スイートで全ツールチェーンの回帰を保護（v5.2 で hermetic 設計確立、v5.3 系で Linear / GitHub Project 連携テスト追加、v5.4 で Profile Policy 20 tests 追加、v5.5 Phase B で +38 / v6.0 Phase C で +41 / Phase D で +9 / Phase E で +8 / Phase F で +3 = baseline 558 → 792 passed）:

```bash
# default — API テストは自動 deselect（pyproject.toml addopts で制御）
python3 -m pytest -q                             # 792 passed / 1 skipped / 3 deselected (hermetic)
python3 -m pytest -m "harness" -q                # Harness Maturity（64 tests）
python3 -m pytest sdd-templates/tests/ -q        # Execution Authority E2E（14 tests）
python3 -m pytest -m "e2e" -q                    # E2E — CLI + Enterprise
python3 -m pytest -m "api" -q                    # Live API（3 tests, 要 .env.local + provider 到達）
python3 -m pytest --override-ini="addopts=" -q   # 全 792+ tests（api 含む）実行
```

| カテゴリ | テスト数 | 対象 |
|---------|---------|------|
| **Unit** (symphony/tests/) | 266 | stride_bridge, evaluator core, symphony engine, janitor (18), runner/config 拡張 |
| **Integration** (tests/) | 317 | 全ツール + CLI E2E + CLI UX + harness + stride symphony dispatch + Linear (10) + GitHub Project V2 (8) + Profile Policy (20, v5.4) |
| **Execution Authority E2E** (sdd-templates/tests/) | 14 | Normal / Failure / Janitor paths (v5.2 新規) |
| **Live API** | 3 | OpenAI + Gemini 実呼び出し（default deselect） |

テスト基盤: `tests/project_builder.py` — `tmp_path` に isolated project root を動的生成。
repo root を汚さず、ネットワーク非依存、deterministic。
v5.2 から `pyproject.toml` の `addopts = "-m 'not api'"` と `testpaths = [symphony/tests, tests, sdd-templates/tests]` により default `pytest` が完全 hermetic に。

---

## GitHub Projects 連携

SDD のワークフローを GitHub Projects V2 で管理するための構造が組み込まれています。

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Projects V2                          │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────┐ │
│  │ Epic Overview │ │ Kanban Board │ │ Risk Heatmap │ │Timeline│ │
│  │   (Table)     │ │   (Board)    │ │   (Table)    │ │(Road-  │ │
│  │               │ │              │ │              │ │  map)  │ │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └───┬────┘ │
│         └────────────────┴────────────────┴──────────────┘      │
│                               │                                  │
│                    GitHub Issues + Labels + Fields                │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                  ┌─────────────┴─────────────┐
                  │     GitHub Actions          │
                  │  stride-sync (Forward)      │
                  │  stride-reverse-sync        │
                  │  auto-add-to-project        │
                  │  stride-lint                │
                  └─────────────┬─────────────┘
                                │
┌───────────────────────────────┴──────────────────────────────────┐
│                  SDD File System (SSoT)                           │
│  specs/*/state/state.yaml ←→ work_items/ ←→ runs/                │
└──────────────────────────────────────────────────────────────────┘
```

### Issue Templates（4種類）

`.github/ISSUE_TEMPLATE/` に4つのテンプレートを提供:

| Template | ファイル | 用途 |
|----------|---------|------|
| **Epic** | `epic.md` | Epic 全体の進捗追跡（Feature一覧・Milestone・依存・リスク） |
| **Milestone** | `milestone.md` | マイルストーン追跡（Exit Criteria・WI リスト） |
| **Work Item** | `work-item.yml` | WI 単位の実行追跡（フォーム形式: Mode / Risk Flags / AC） |
| **Risk/Blocker** | `risk.md` | リスク・ブロッカー管理（確率・影響・対策・エスカレーション） |

Work Item テンプレートは YAML フォーム形式（`work-item.yml`）で、以下のフィールドを構造化入力:

- WI ID / Feature ID / Complexity / Execution Mode / Priority
- Risk Flags（チェックボックス: authz, audit_log, db_schema 等 10 項目）
- Spec References / Contract References / Intent / Scope / Plan / AC

### Labels（GitHub Projects 43 + STRIDE Learning Loop 20 = 全ラベル）

2ステップで登録します（詳細は下記のコマンドブロック参照）:

| カテゴリ | ラベル | 色 |
|---------|--------|-----|
| **Issue 種別** | `epic`, `milestone`, `work-item`, `risk`, `blocker`, `dependency` | 紫/青/赤/黄 |
| **実行 Mode** | `mode:autopilot` (緑), `mode:confirm` (黄), `mode:validate` (赤) | リスク対応色 |
| **Scale Tier** | `tier:starter` (水色), `tier:standard` (青), `tier:enterprise` (紫) | 規模別 |
| **Risk Flag** | `risk:authz`, `risk:audit_log`, `risk:data_migration`, `risk:external_api`, `risk:ui_only` | 赤系/緑 |
| **Status** | `status:done` (緑), `status:in-progress` (青), `status:pending` (灰), `status:blocked` (赤) | 状態色 |
| **Priority** | `priority:high` (赤), `priority:medium` (黄), `priority:low` (緑) | 優先度色 |
| **Gate** | `gate:1-design` ~ `gate:5-tasking` (灰), `gate:final` (ティール) | Phase 段階 |
| **Ops** | `ops-ready` (緑), `ops-not-ready` (ピンク) | 運用準備 |
| **品質** | `sdd-reference-miss` (赤) | 参照漏れ計測 |
| **Symphony** | `symphony:ready` (青), `symphony:running` (黄), `symphony:done` (緑), `symphony:blocked` (橙), `symphony:failed` (赤), `symphony:janitor` (薄緑) | ライフサイクル |
| **Phase** | `phase:design` (黄), `phase:specify` (桃), `phase:tasking` (水色), `phase:execute` (薄緑) | SDD Phase 可視化 |

```bash
# Step 1: GitHub Projects ラベル（mode/tier/risk/gate/epic/ops/symphony/phase 等 — labels.json から）
cat sdd-templates/templates/github-projects/labels.json | jq -c '.[]' | while read label; do
  gh label create "$(echo $label | jq -r .name)" \
    --color "$(echo $label | jq -r .color)" \
    --description "$(echo $label | jq -r .description)" --force
done

# Step 2: STRIDE Learning Loop ラベル（findings/decisions/amendment/sentry 等 — setup_project_labels.py から）
python3 sdd-templates/tools/setup_project_labels.py --repo OWNER/REPO
```

> **ラベルの SSoT**:
> - `mode:*`, `tier:*`, `epic`, `work-item`, `gate:*`, `ops-*`, `symphony:*`, `phase:*` → **`labels.json`** (step 1)
> - `findings:*`, `decisions:*`, `amendment:*`, `sentry:*`, `spec-impact:*` → **`setup_project_labels.py`** (step 2)
>
> 各ファイルが担う領域は重複していません。両 Step を実行することで全ラベルが揃います。

### Milestones

SDD Gate に対応する GitHub Milestones:

| Milestone | 対応 Gate |
|-----------|----------|
| Gate 1: Design Review | 基本設計レビュー |
| Gate 2: BPMN Review | 業務フロー承認 |
| Gate 3: Spec Review | 仕様レビュー |
| Gate 4: Plan Review | 設計計画レビュー |
| Gate 5: Tasking Review | タスク分解レビュー |
| Final: Evidence Review | Evidence Pack 最終確認 |
| EM-01 ~ EM-NN | Epic マイルストーン（日付付き） |

### Projects V2 カスタムフィールド

#### 基本フィールド

| フィールド | タイプ | 値 |
|-----------|--------|-----|
| WI ID | Text | `WI-XXX-NNN` |
| Feature ID | Text | `FEAT-XXX` |
| Epic ID | Text | `EPIC-XXX` |
| SDD Mode | Single Select | autopilot / confirm / validate |
| Coverage Tier | Single Select | starter / standard / enterprise |
| SDD Gate | Single Select | Gate 1 ~ Final |
| Complexity | Single Select | low / medium / high |
| Risk Flags | Text | カンマ区切り |
| Ops Ready | Single Select | Yes / No / N/A |

#### Process Metrics フィールド

`stride_process_metrics.py` が自動更新するプロセス計測フィールド:

| フィールド | タイプ | 値 | 用途 |
|-----------|--------|-----|------|
| Gate | Single Select | g1 / g2 / g3 / g4 / g5 / evidence | 現在の Gate |
| Gate Age (days) | Number | — | 現在 Gate での滞留日数 |
| Delay Risk | Single Select | on_track / at_risk / overdue | 遅延リスク判定 |
| Lead Time (days) | Number | — | WI 開始〜完了の日数 |
| Inject Rate | Single Select | 0% / 1-20% / 21-50% / 50%+ | 差し込み率 |

遅延リスク判定の閾値:

| Complexity | at_risk | overdue |
|------------|---------|---------|
| low | 2日超 | 3日超 |
| medium | 3日超 | 5日超 |
| high | 4日超 | 7日超 |

```bash
# フィールド作成
gh project field-create <N> --owner <OWNER> --name "Gate" \
  --data-type "SINGLE_SELECT" --single-select-options "g1,g2,g3,g4,g5,evidence"
gh project field-create <N> --owner <OWNER> --name "Gate Age (days)" \
  --data-type "NUMBER"
gh project field-create <N> --owner <OWNER> --name "Delay Risk" \
  --data-type "SINGLE_SELECT" --single-select-options "on_track,at_risk,overdue"
gh project field-create <N> --owner <OWNER> --name "Lead Time (days)" \
  --data-type "NUMBER"
gh project field-create <N> --owner <OWNER> --name "Inject Rate" \
  --data-type "SINGLE_SELECT" --single-select-options "0%,1-20%,21-50%,50%+"
```

### 推奨 Views（6ビュー）

| View | タイプ | フィルタ | 用途 |
|------|--------|---------|------|
| **Epic Overview** | Table | `label:epic,work-item` | PM の全体俯瞰 |
| **Kanban Board** | Board | `label:work-item` | WI 進捗管理（Backlog → Done） |
| **Risk Heatmap** | Table | `label:risk,blocker` | リスク・ブロッカー一覧 |
| **Milestone Timeline** | Roadmap | `label:milestone` | マイルストーン時系列 |
| **Ops Readiness** | Table | `label:work-item` | リリース準備状況 |
| **Process Metrics** | Table | `label:work-item` | Gate 滞留・遅延リスク分析 |

#### View 6: Process Metrics（詳細）

Gate 別滞留時間と遅延リスクを可視化する PM 向け分析ビュー。

| カラム | ソース | 説明 |
|--------|--------|------|
| Title | Issue title | WI / Epic 名 |
| Status | Status field | 現在の状態 |
| WI ID | Custom field | Work Item ID |
| Gate | Custom field | 現在の Gate（g1〜evidence） |
| Gate Age (days) | Custom field | 現在 Gate での滞留日数 |
| Delay Risk | Custom field | on_track / at_risk / overdue |
| Complexity | Custom field | low / medium / high |
| Lead Time (days) | Custom field | WI 開始〜完了の所要日数 |
| Inject Rate | Custom field | 差し込み率 |

**フィルタ**: `label:work-item`
**ソート**: Delay Risk DESC → Gate Age DESC
**推奨フィルタ（アラート用）**: `Delay Risk is at_risk OR Delay Risk is overdue`

対応する PM_DASHBOARD.md の Process Metrics セクション例:

```markdown
### Gate別滞留時間（プロセスタイム分析）

| Gate | 開始 | 完了 | 滞留日数 | 状態 |
|------|------|------|---------|------|
| Gate 1: Design Review | 2026-02-01 | 2026-02-01 | 0日 | completed |
| Gate 2: BPMN Review   | 2026-02-01 | 2026-02-01 | 0日 | completed |
| Gate 3: Spec Review   | 2026-02-01 | 2026-02-03 | 2日 | completed |
| Evidence Review       | 2026-02-05 | -(進行中)  | 14日 | at_risk |

### WI別遅延リスクサマリ

| WI ID | Complexity | 現在Gate | 滞留日数 | リスク |
|-------|-----------|---------|---------|-------|
| WI-ERP-SAMPLE-001 | medium | evidence | 14日 | at_risk |
| WI-ERP-SAMPLE-002 | high   | gate3    | 2日  | on_track |
```

プロセスメトリクス指標:

| 指標 | STRIDE データソース |
|------|-------------------|
| プロセスタイム（工程別） | Gate 承認日時の差分 |
| 待機時間 | Gate 承認待ち経過日数 |
| 差し込み率 | WI 追加タスク数 / 当初タスク数 |
| 変更リードタイム | WI 開始〜merge 完了の日数 |
| 遅延アラート | 現在 Gate + 残日数 vs Complexity 閾値 |

### GitHub Actions ワークフロー

| ワークフロー | トリガー | 機能 |
|-------------|---------|------|
| `auto-add-to-project.yml` | Issue の作成/ラベル付与 | SDD ラベル付き Issue を Projects V2 に自動追加 + カスタムフィールド設定 |
| `stride-sync.yml` | `state.yaml` 変更 / 手動 | SDD ファイル → GitHub Projects の順方向同期 + Process Metrics 更新 |
| `stride-reverse-sync.yml` | 手動 / スケジュール | GitHub Projects → SDD ファイルの逆方向同期 |
| `stride-lint.yml` | PR / Push / 手動 | `specs/**` 変更時に SDD 準拠チェック |

### state.yaml との連携

`specs/<feature>/state/state.yaml` の `github_projects` セクションで Label/Milestone/View のマッピングを定義:

```yaml
github_projects:
  project_id: "PVT_kwDOBxxxxxx"
  project_number: 2
  labels:
    - { sdd_concept: "mode:autopilot", github_label: "mode:autopilot" }
  milestones:
    - { sdd_gate: "Gate1", github_milestone: "Gate 1: Design Review" }
  views:
    - { name: "Kanban Board", type: "board", filter: "label:work-item" }
```

### セットアップ

```bash
# 1. Labels 一括登録（2 step — 上の「ラベル一覧」セクション参照）
cat sdd-templates/templates/github-projects/labels.json | jq -c '.[]' | while read label; do
  gh label create "$(echo $label | jq -r .name)" \
    --color "$(echo $label | jq -r .color)" \
    --description "$(echo $label | jq -r .description)" --force
done
python3 sdd-templates/tools/setup_project_labels.py --repo OWNER/REPO

# 2. Gate Milestones 作成
for gate in "Gate 1: Design Review" "Gate 2: BPMN Review" "Gate 3: Spec Review" \
            "Gate 4: Plan Review" "Gate 5: Tasking Review" "Final: Evidence Review"; do
  gh api repos/{owner}/{repo}/milestones -f title="$gate"
done

# 3. Issue Templates コピー（テンプレートリポから初期化済み）
cp sdd-templates/templates/github-projects/ISSUE_TEMPLATE/*.md .github/ISSUE_TEMPLATE/
```

詳細: [`sdd-templates/templates/github-projects/setup-guide.md`](sdd-templates/templates/github-projects/setup-guide.md)

---

## マニュアル

```bash
npx docsify-cli serve manual/  # → http://localhost:3000
```

53章 (00 PM クイックスタート + 01-52) ＋付録4章の完全ガイド。主要な章：

| # | 内容 |
|---|------|
| **00** | **⚡ PM クイックスタート（5分）** — 承認操作だけで開発を進める方法 |
| 01 | Getting Started |
| 07 | **実施担当者ガイド** — AI と共に仕様を実行 |
| 08 | Web-EDI 実践チュートリアル |
| 09-14 | 各 Phase ガイド（basic_design / BPMN / spec / plan / tasks / evidence） |
| 15 | **AI 自律実行ガイド** |
| 17 | Autonomy Bias / Run Resume |
| 22 | **PR Readiness** — 7チェック統合品質ゲート（v5.4 `--summary-line` で project-level 1-line 出力も対応） |
| 24 | マルチチームコラボレーション |
| 27 | ERP Addon Playbook |
| 30 | **Symphony Orchestration** — GitHub Issues → Agent 自動実行 |
| 32 | **Multi-Model Evaluator** — LLM 意味的評価ゲート |
| 33 | **統合テストフレームワーク** — **792 テスト**の回帰保護（v5.2 で hermetic 化、v5.3 系で Linear + GitHub Project 系 18 テスト追加、v5.4 で Profile Policy 20 tests 追加、v5.5 Phase B で 38 tests 追加、v6.0 Phase C で 41 tests 追加、Phase D で +9 / Phase E で +8 / Phase F で +3 = 758 → 792 passed） |
| 37 | **Linear Integration** — Run 成果物を Linear Issue に一元可視化 (v5.3) |
| 38 | **Profile ガイド (v5.4)** — 報告粒度 + Completeness 閾値の切替（enterprise-erp / saas-integration / prototype） |
| **39** | **VALUE Upstream Extension 概要 (v5.4 Phase A)** — Discovery / Elicit / Context Modelling の上流フェーズ概念 |
| 40 | **BACCM 完全性ゲートガイド (Phase A)** — BABOK v3 BACCM 6 軸 (change/need/solution/stakeholder/value/context) |
| 41 | **Layered Requirements Architecture (Phase A)** — Layered Requirements Modeling の 4 レイヤー構造 (System/Business/BusinessUseCase/Conditions) |
| 42 | **Upstream Phase 0 → 0.3 → 0.5 → Phase 1 ウォークスルー (Phase A)** |
| 43 | **Upstream CLI ガイド (v5.5 Phase B)** — `stride upstream init/validate` / `stride lint --upstream` / `stride evaluate --phase discovery` |
| 44 | **Upstream Iteration Workflow (v5.5 Phase B)** — 3 反復パターン (initial/refinement/finalization、max_iterations=3) |
| **45** | **Upstream Bridge ガイド (v6.0 Phase C)** — `stride upstream-bridge` による Phase 0 → Phase 1 自動接続、Gate 1/2 immutability check |
| **46** | **Solution Evaluation ガイド (v6.0 Phase C)** — `stride retro --solution-eval` による BABOK KA8 稼働後評価 |
| **47** | **🚀 v6.0 リリースノート** — Phase A/B/C 統合サマリ + Breaking Changes (Constitution Article XV-XVII ratification) + Phase D 申し送り |
| **48** | **enterprise-erp Profile VALUE Playbook (Phase D)** — 大型 ERP 統合 (SAP/mcframe) 案件で VALUE Upstream Extension をどう運用するかの 6 章ガイド (3000-5000 字) |
| **49** | **saas-integration Profile VALUE Playbook (Phase D)** — SaaS-to-SaaS / SaaS-to-ERP 統合案件 (Salesforce/kintone/Workday 等) 向け 6 章ガイド |
| **50** | **prototype Profile VALUE Playbook (Phase D)** — 軽量 path で rapid prototyping 案件向け 6 章ガイド |
| **51** | **🔌 Cowork Plugin Install Guide (Phase E)** — Anthropic 公式 `knowledge-work-plugins` 仕様準拠 Plugin の install + 使い方 (11 章 3000-5000 字、3 つの起動方法 + 典型 workflow + Anthropic Cowork web 連携 + トラブルシューティング) |
| **52** | **🛠 Phase F Lessons Learned + Cowork Plugin v0.2.0-stable 運用ガイド (Phase F)** — fc-sd 実機運用で発見された 16 件改善要望 × 17 WI 対応総括 + 実機 lessons + §9 fc-sd 相当の Plugin 導入手順 (DR-104: 外部 fc-sd repo 触らず本体 manual で集中管理) (11 章) |

---

## 前提条件

```bash
pip install -r sdd-templates/requirements.txt
```

| ツール | バージョン | 必須/任意 |
|--------|-----------|----------|
| Python 3.8+ | `python3 --version` | 必須 |
| Node.js 18+ | `node --version` | 任意（Docsify / Turborepo） |

---

## バージョン履歴

| バージョン | 日付 | 主な変更 |
|-----------|------|----------|
| **v6.0.x — Agent Hardening + F1 retroactive merge** | **2026-05-08** | **[PR #29](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/29) (merge f5212b9) + [PR #30](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/30) — 🛡 2026-05-08 BPMN vertical-flow violation incident への構造的 hardening + F1 後追い merge** — simple-bi PoC で発生した **7 件の canonical 違反** (template-copy 欠如 / `isHorizontal=true` / `BPMN_TASK_01_xxx` 命名 / XOR Gateway `default` 欠如 / `basic_design.bpmn_descriptions` 未 populate / 自作 validator 偽陽性 / SKILL.md 未読、ユーザ目視レビューが唯一の発見ルート) への構造的 hardening。**SKILL.md auto-trigger ≠ SKILL.md body load** の failure mode を防止する 7-task structural guard。**Plugin v0.4.0-bpmn-package-integration → v0.5.0-agent-hardening、BPMN Pack v1.0.0 → v1.1.0** (本体 6.0.0 維持)。**(PR #29 — Agent Hardening)** (1) 全 7 specialized SKILL.md (bpmn-authoring / basic-design-authoring / baccm-discovery / babok-elicitation / layered-context-modelling / epic-decomposition / upstream-bridge) に **STEP 0 PRE-FLIGHT (MANDATORY)** ブロック挿入 — 必須 Read リスト + template-copy 強制 cp コマンド + ANTI-PATTERN 表 + Output of STEP 0 (PRE-FLIGHT REPORT) フォーマット。(2) `cowork-plugin/bpmn/PRE_FLIGHT_CHECKLIST.md` 1-page checklist 新設 (7 セクション A-G、agent submit format 確定)。(3) `bpmn_lint.py` v1.0→v1.1 強化 — `BPMN_ID_FORMAT_VIOLATION` (^BPMN-(TASK\|GW\|EVT\|FLOW)-\\d{3}$ regex) + `BPMN_ID_NON_TECNOS_SCHEME` warning (Camunda Modeler default ID は backward compat) + `--legacy-id` flag (transition、`BPMN_TASK_01_xxx` を warn-only 格下げ) + `--diff-against-template` flag (template-copy 省略の検出) + 全 error に `fix_hint` + `refs` フィールド追加。(4) `bd_bpmn_sync.py` v1.0 新設 — `basic_design.md.bpmn_descriptions.elements[].bpmn_id` ↔ `process.bpmn` 内 id の双方向 sync 検証 (FEAT MUST-DO #14)、stdlib のみ、PyYAML 不要 (regex で bpmn_id 抽出)、`BD_BPMN_SYNC_BD_ORPHAN` / `BD_BPMN_SYNC_BPMN_ORPHAN` エラーコード。(5) `render_ascii_preview.py` v1.0 新設 — BPMNDI 座標から ASCII グリッド (lanes + elements) を render、Camunda Modeler 不要で vertical/horizontal orientation 視覚判別可能、horizontal 検出時警告自動表示。(6) `stride-conductor` SKILL.md + `commands/start.md` に **「⚠️ Dispatch 前の MANDATORY Read」** 5-step protocol 追加 — specialized skill 内部 dispatch 直前に対象 SKILL.md を literal Read + STEP 0 リストを user に提示 + ready_to_proceed:true を検証。`bpmn-authoring` のみ 2 ファイル mandatory (skill SKILL.md + bpmn pack の PRE_FLIGHT_CHECKLIST.md) で multi-layer 防御。(7) `docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md` 起票 (Summary / Timeline / Root Cause 主因 3 件 / 7 違反詳細 / Action Items / Future Hardening Phase H 候補 4 件 / 運用面の申し送り)。**CI 連動 fix**: validate-plugin workflow の skill/command/ref_files threshold 更新 (7→8 / 9→14 / 49→46) + plugin tests count update + `sync_cowork_plugin_reference.sh` の v0.4.0 BPMN integration 追従 (BPMN templates copy 削除、idempotency 復元)。**(PR #30 — F1 retroactive merge)** F1 (`method_ssot_externalization`) を retroactive に main に merge — F2 (PR #26) と同セッション作業時の selective `git add` で F2 のみ origin/main に push されていた状況を是正、51 ファイル (specs/method_ssot_externalization/ 38 + sdd-templates/tools/method_labeling/ 4 + method_audit/method_labels_checker/bulk_apply_labels 3 + plane_classification_ruleset 1 + その他) を main へ追加。F2 PR #26 で referenced されていた CT-FILE-01 (`method-store-schema.json`) + F3 planning doc §6.6 / §18.2 + README + ByteRover memory の F1 完遂前提を全件解決 |
| **v6.0.x — Method Store Publishing (Feature ②)** | **2026-05-08** | **[PR #26](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/26) (merge 684c948) + [PR #27](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/27) (merge bbfe46b) — 📦 FEAT-METHODSTOREPUBLISHING SDD Feature 完遂 + F3 planning doc v1.2.1** — Tecnos-STRIDE が **自身の SDD methodology を使って自身の本体機能を拡張した最初の Feature**。SDD Phase 1-Final 全 Gate 承認下で実装、Method content の OCI artifact 化 + cosign keyless signing + ghcr.io 配信パイプラインを **1-cmd で起動可能** に。**Tecnos-STRIDE 本体 VERSION 6.0.0 維持** (機能追加のみ)。**(PR #26 — F2 merge)** (1) **5 stride method subcommands** (preview / validate / diff / publish / rollback、+ 1 implicit drift) を `sdd-templates/bin/stride` に追加。(2) `sdd-templates/tools/method_publish/` Python package (12 modules: __init__, preview, validate, diff, snapshot_builder, cosign_signer, oci_publisher, publish, release_notes_generator, rollback, drift_detector, tenant_policy_validator) + `sdd-templates/tools/ci_helpers/` (gitops_pr_creator + slack_notifier)。(3) **9-step CI pipeline** (`.github/workflows/method-store-publish.yml`) — validate → snapshot_build → cosign sign (Sigstore Fulcio + Rekor + GitHub Actions OIDC) → ghcr.io push (oras CLI delegate) → channel branch → smoke or auto PR (release_notes_generator + gitops_pr_creator) → Method Board 3 person review → go_live → Slack notify、permissions 最小化 + R-PLAN-004 workflow injection 防御 (env: で untrusted input escape)。(4) **3 contracts**: CT-CLI-02 (`specs/method_store_publishing/contracts/cli_method_publish_schema.yaml` 5-subcommand schema) / CT-FILE-02 (`release_notes_schema.yaml` RELEASE_NOTES.md 8 sections + METHOD_APPROVAL.md 3-person template) / CT-FILE-03 (`shared/policies/sdd_tenant_policy_schema.yaml` cross-repo SSoT、JSON Schema Draft 2020-12、F3 cbp-core master-admin DB が consume)。(5) **3 channel + tenant policy** — edge `edge-{sha7}` (30d retention、社員 dogfooding) / staging `v{semver}-rc.N` (90d、CBP staging) / stable `v{semver}` (indefinite、全顧客テナント)、auto_upgrade (none/patch/minor) + pin (semver constraint with x/* support) + upgrade_window (cron + timezone) + notifications (slack_webhook/email/notify_on)。(6) **5 min MTTR rollback** — `stride method rollback --to=<tag> --reason=<text> --yes` で OCI tag 巻き戻し + GitOps revert PR auto-create + Slack 緊急通知、--reason mandatory (audit 用)、Rekor + ghcr.io tag history + Slack archive で 3 重記録。(7) **22/22 pytest PASS** (TS-CON-01 + TS-INT-01..04 + TS-UT-01) + Evidence Pack 8 artifacts (CI/SAST/SCA/Secrets/AI provenance + cosign signature audit + Rekor transparency log) + walkthrough.md。(8) **Symphony 適用ガイド** for F3 Phase 4 並列化 (Codex 並列実装 + Claude Code judgment-heavy)。Reviewer post-merge fix (4dda7a7) で `bash sdd-templates/bin/stride method <subcmd>` の PYTHONPATH 設定漏れを修正 (CI workflow は env で解決済だったが local CLI 用の hot fix)。**(PR #27 — F3 planning doc)** F3 (`sdd_method_gateway_poc` on cbp-core 別 repo、CBP-on-EKS 上の MCP services 実装) 着手用の **single source of truth doc** v1.2 → v1.2.1 を完成 (`.planning/claude_code_instruction_sdd_method_gateway.md` 1422 → 1499 行)。independent reviewer (pr-review-toolkit:code-reviewer agent) による fact-check で検出された **Critical 3 + Important 5 件**を全件修正 — C1 (INTERNAL_* マーカー数 1 → 3 種正確化、F1 spec/lock.json 整合) + C2 (F1 deliverables の actual filename correction、`method_audit.py` + `method_labels_checker.py` + `bulk_apply_labels.py` + `method_labeling/` package に統合済を反映) + C3 (lock.json schema を 7-value type enum + 4-value return_policy + 6-field ip_boundary_audit + root feature_id="all" sentinel に同期) + I1 (issue count 6→7) + I2 (WI naming WI-MGW-* → WI-SDDMETHODGW-*) + I3 (ID convention regex 6 種 → 20 種に拡張、constitution.md line 224-269 を SSoT として明示) + I5 (upstream/* nested phase folders 構造を反映)。F3 の 13 WI は本書 §13 に記載、Phase 4 で Symphony 並列実装可。詳細: `.planning/claude_code_instruction_sdd_method_gateway.md` v1.2.1 |
| **v6.0.x — BPMN Pack v1.0.0 + Plugin v0.4.0-bpmn-package-integration** | 2026-05-07 | **直接 commit 2 件 (b8aec09 + 6acd3fe) — 📐 BPMN 作成基盤の独立パッケージ化 + Plugin first-class component 統合** — BPMN 作成基盤を `bpmn/` 配下に独立パッケージ化、Cowork Plugin に first-class component として統合。**Tecnos-STRIDE 本体 VERSION 6.0.0 不変、Plugin SemVer 0.3.2 → 0.4.0-bpmn-package-integration、BPMN Pack 独立 SemVer 1.0.0**。**(b8aec09)** `bpmn/` パッケージ新設 — 24 章 ruleset (`rules/bpmn_generator_rules.md` Camunda 8 適用ルール全仕様、§21 OMG 実行セマンティクス + §22 Connection Rules + §23 BPMN Coverage + §24 Tecnos override 含む) + `rules/bpmn_quick_reference.md` (FEAT 14 / EPIC 9 MUST-DO 1-page checklist) + `rules/camunda_bpmn_practice_guide.md` (Standard / Advanced / Deferred 区分) + `spec/camunda_bpmn_dictionary_complete.md` (OMG BPMN 2.0 + **Camunda 8.9** 全要素辞書、2744 行) + `templates/process_bpmn_template.bpmn` (FEAT 用、BPMN-* ID / vertical layout / pool 構造) + `templates/epic_flow_template.bpmn` (EPIC 用、collaboration + 2 participant + messageFlow 雛形) + `examples/process_bpmn_example.bpmn` (basic FEAT サンプル) + `examples/process_bpmn_advanced_example.bpmn` (advanced FEAT、error end + call activity + business rule task) + `validators/bpmn_lint.py` (stdlib のみ、FEAT 14 + EPIC 9 MUST-DO 検証 CLI、auto-detect FEAT vs EPIC) + `README.md` + `PORTABILITY.md` (採用判断と移植ガイド) + `CHANGELOG.md` + `VERSION 1.0.0`。**(6acd3fe)** Cowork Plugin **v0.3.2 → v0.4.0-bpmn-package-integration** — `cowork-plugin/bpmn/` に bpmn pack を first-class component として配置 (Skills / Commands / reference_files と並列の自己完結 component に格上げ)、Plugin install で BPMN 作成基盤一式が自動同梱、`/stride:bpmn-validate` 新規 command (FEAT 14 / EPIC 9 MUST-DO 自動検証)、reference_files から BPMN 重複削除 (drift 防止、git rename detection で 4 件移動: bpmn_quick_reference.md / camunda_bpmn_practice_guide.md / camunda_bpmn_dictionary_complete.md / bpmn_generator_rules.md)、commands 11 → **14** (start + stride-bootstrap-repo + stride-bpmn-validate)、skills 7 → **8** (stride-conductor)、reference_files **49 → 45** (BPMN 4 件 → bpmn/ へ移動)。**Camunda 8.8 → 8.9 spec 最新化**で BPMN 作成精度向上 |
| **v6.0.x — Phase G Brand-Neutral + Simple UX (Plugin v0.3.x)** | 2026-05-07 | **[PR #18-#25](https://github.com/tecnos-japan-cbp/tecnos-stride/pulls?q=is%3Apr+is%3Amerged+%23PR-) — 🎨 Phase G 7 連続 PR で Plugin 体験を磨き上げ** — 上位コンサルが Cowork で日本語ひとことで指示する体験への昇華。**Plugin v0.2.0-stable → v0.3.0-simple-ux → v0.3.1 → v0.3.2** (本体 6.0.0 不変)。**(PR-A #18 commit 7d9c728)** Plugin 内部の RDRA / 匠Method 等の固有名称 (考え方は inspired by 採用、ブランド名は除去) を考え方ベース brand-neutral 用語に置換 — Skills / Commands / reference_files / SKILL.md description を全件 sweep。**(PR-B #19 commit 245a894)** 本体 docs + reference_files の同様 RDRA / 匠Method 全件除去 — 本体 manual + sdd-templates 配下の同等清拭、Plugin と本体の用語整合確保。**(PR-C #20 commit 3b8e7ca)** Constitution **Article XVI** (Layered Requirement Architecture) 文言を brand-neutral rephrasing + code-level error code rename — `BACCM_INCOMPLETE` 等の error code は維持、人間向け文言のみ調整。**(PR-D #21 commit c854dd8)** **`stride-bootstrap-repo` command 新規** — Cowork → Claude Code 継ぎ目のない接続を 1 コマンド bootstrap で実現 (Cowork から GitHub PR draft 生成までの工数削減)。**(marketplace #22 commit d8ba559)** marketplace.json の version を 0.1.0-poc → 0.2.0-stable bump (Plugin 自体の Phase F bump と整合)。**(PR-E #23 commit 9fceb49 v0.3.0-simple-ux)** Hitoshi さん指示「複雑すぎます。pluginを改良してもっとシンプルに Cowork で指示を出して進められるようにしてください」を実現。**`/start` コマンド新規** — 日本語ひとこと指示で Plugin が状態を理解して進める conductor 設計。`stride-conductor` skill 追加 (skills 7 → 8)、複雑だった UX を Anthropic 公式 conductor pattern に整合、ultrathink で UX 診断 → 「コンサルが Cowork に普通の日本語ひとことで指示するだけで Plugin が状態を理解して進める」を真の要請と判断。**(PR-F #24 commit 23456cc v0.3.1)** stride-start.md → start.md rename hotfix (`/tecnos-stride-value:start` 起動可能化、Plugin namespace 整合)。**(PR-G #25 commit fad51cb v0.3.2)** Plugin docs example の顧客固有名詞 (例: コストコ / JM_Costco) を汎用 placeholder に置換 (sanitize hotfix、§Rule 15-B 顧客機密保護) |
| **v6.0.x — Cowork Plugin v0.2.0-stable (Phase F)** | **2026-05-01** | **[PR #14](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/14) (merge 528ca72) — 🛠 VALUE Cowork Plugin v0.2.0-stable (FEAT-VALF01) — fc-sd 実機運用 16 件改善要望反映、運用品質引き上げ** — Phase E v0.1.0-poc を本物の運用環境で安全に使えるレベルに引き上げる 17 Work Items を 4 週間スプリントで実装。**Tecnos-STRIDE 本体 VERSION 6.0.0 不変、Plugin 独立 SemVer 0.1.0-poc → 0.2.0-stable**。(1) **Phase F-1 緊急 6 件 (Week 1)**: stride-handoff workflow に Cowork セッション内 4 ファイル + 必須セクション grep (WI-001 / Gap-F-001) / `.github/workflows/cowork-plugin-validate.yml` 新規 (WI-002 / Gap-F-002、PR の Plugin 関連 path 変更を path filter で自動 trigger、ubuntu-latest + Python 3.11 + claude CLI で `claude plugin validate` + pytest 実行) / state.yaml に `phase_2/3/4/final` schema 拡張 (WI-010 / 改善要望-09) + `tests/test_cowork_plugin_state_yaml_phases.py` +3 tests / GitHub MCP 検証 evidence scaffold (WI-012 / 改善要望-11、`docs/evidence/phase_f/wi_012_mcp_validation.md`) / stride-design に dev 依存自動検出 + pip install 提案 (WI-013 / 改善要望-12) / **stride-tasking command 新規** (WI-016 / 改善要望-15、★ v2 P0-3 必須化、VALUE pack → Phase 3 連結)。(2) **Phase F-1 高優先 3 件 (Week 2)**: 7 SKILL.md description を Tecnos-STRIDE 固有語必須前置詞化 (WI-003 / Gap-F-003、誤起動回避) / stride-handoff workflow に §Rule 15-B サニタイズ自動 grep (WI-004 / Gap-F-004、`grep -E` で禁止キーワード集を `upstream/*.yaml` + `lessons_learned` に対し検査、ヒット時 `[BLOCKER]` 停止) / cowork-plugin/README.md に OpenAPI vs Plugin runtime 関係明示 (WI-005 / Gap-F-005、Architecture Notes §1.1 で 3 階層の役割分担を表で明示)。(3) **Phase F-2 中優先 4 件 (Week 3)**: HTML 出力 (WI-011 / 改善要望-10、`scripts/build_basic_design_html.py` Tecnos-STRIDE 本体 helper + `cowork-plugin/commands/stride-export-html.md`、**DR-103: Plugin 同梱せず本体 scripts/ 配下**で配布物最小化) / `cowork-plugin/scripts/` 新規ディレクトリ + 補助 Python scripts (WI-014 / 改善要望-13、`validate_state_yaml.py` + `check_handoff_files.py` + README、★ v2 P0-2: reference_files=49 不変) / saas-integration / prototype profile dogfooding lessons scaffold (WI-006/007 / Gap-F-006/007、実 dogfooding は Phase F PR merge 後に Hitoshi さん follow-up)。(4) **Phase F-3 仕上げ 3 件 (Week 4)**: `cowork-plugin/.claude-template/settings.json` 新規 (WI-015 / 改善要望-14、Plugin 配布時の推奨 `.claude/settings.json` template、reference_files=49 不変) / `manual/52_phase_f_lessons_learned.md` 11 章 (WI-008 / Gap-F-008、§9 に fc-sd 相当の Plugin 導入手順を **DR-104: 外部 fc-sd repo 触らず本体 manual で集中管理**、WI-017 / 改善要望-16) / `cowork-plugin/.claude-plugin/plugin.json` の version `0.1.0-poc → 0.2.0-stable` (WI-009)。**検証結果**: baseline 789 → **792 passed** (+3 state.yaml schema、回帰 0)、claude plugin validate ✔、改変禁止 hash 13 FAILED 全件 Phase F 許可リスト内 (Rule 1-bis Phase E v3.1 と同じ FAILED 抽出 + 許可リスト判定方式)、commands 9 → **11** (stride-export-html + stride-tasking 新規)、reference_files **49 維持** (cowork-plugin/scripts/ + .claude-template/ は別ディレクトリ計上)、skills 7 (description のみ更新)。**CI 自己検証 Highlight**: WI-002 (`.github/workflows/cowork-plugin-validate.yml`) は **本 PR (#14) で自身を初回 trigger し 3 GitHub Actions checks (quality / validate-plugin / stride-lint) すべて SUCCESS**。**Architecture decisions**: DR-101 (VERSION 戦略) / DR-102 (CI path filter) / DR-103 (HTML helper 本体配置) / DR-104 (manual/52 §9 で外部 fc-sd repo 不変) / DR-105 (Phase F-1緊急 → F-1高優先 → F-2中優先 → F-3仕上げ の 4 週間スプリント)。**Follow-up tracking ([Issue #15](https://github.com/tecnos-japan-cbp/tecnos-stride/issues/15))**: WI-006/007 実 dogfooding (Q-102 closure 2026-05-15) + WI-012 GitHub MCP 実 API 検証 + Q-101 marketplace 登録プロセス確定 + CI workflow 内 claude CLI 正規 install path (現状 Python json check fallback)。詳細: [`manual/52`](manual/52_phase_f_lessons_learned.md) |
| **v6.0.x — Cowork Plugin v0.1.0-poc (Phase E)** | 2026-04-30 | **[PR #10](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/10) + post-merge [#11](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/11) / [#12](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/12) / [#13](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/13) — 🔌 VALUE Cowork Plugin v0.1.0-poc (FEAT-VALE01) — 上下流完全分業の起点** — 上位コンサル (非技術者) が Claude Cowork で Phase 0 → Phase 1 を直接執筆できる Anthropic 公式 `knowledge-work-plugins` 仕様準拠プラグインを `cowork-plugin/` ディレクトリに新規作成。**Tecnos-STRIDE 本体 VERSION 6.0.0 維持、Plugin 独立 SemVer 0.1.0-poc**。(1) **Plugin manifest** 4 files (`.claude-plugin/plugin.json` + `README.md` + `CONNECTORS.md` + `.mcp.json`)。(2) **Skills 7**: `baccm-discovery` / `babok-elicitation` / `layered-context-modelling` (Phase 0 系 3) + `upstream-bridge` / `basic-design-authoring` / `bpmn-authoring` / `epic-decomposition` (Phase 1 + Epic 系 4)、各 SKILL.md は frontmatter (name + description + argument-hint) + Markdown body、description で auto-trigger 条件を明示。(3) **Slash Commands 9**: `stride-{init, discovery, elicit, context-model, validate, bridge, design, epic-init, handoff}.md`、Plugin namespace `/stride:<command>` で全 Skills + scaffold + 完全性チェックを起動可能。(4) **reference_files 49**: Tecnos-STRIDE 本体から sync (manual 12 + constitution 1 + amendments 3 + policies 5 + templates upstream 16 + templates 6 + migration 1 + sdd-templates 3 + docs 2)、`scripts/sync_cowork_plugin_reference.sh` で 49 件厳守チェック内蔵。(5) **MCP Connectors**: filesystem + github (PAT scope = repo r/w + pr r/w + metadata r、必要最小限)。(6) **Tests +8**: `tests/test_cowork_plugin_structure.py` (3 件) + `tests/test_cowork_plugin_skills_commands.py` (5 件) で plugin.json valid + 必須 keys / Skills 7 個 / Commands 9 個 / reference_files 49 件 / SKILL.md frontmatter / commands frontmatter / 参照ファイル実在 / Skill 名 description 整合性 / plugin.json と Skill cross-reference を機械検証 (baseline 778 → **788** → 789 passed、PR #11 post-review fix 後)。(7) **Manual 51**: `manual/51_cowork_plugin_install_guide.md` (11 章 3000-5000 字) で 3 つの起動方法 (ローカル開発 / marketplace 公開後 / Cowork web) + 典型 workflow + トラブルシューティング 5 項目。**post-merge 修正 PR**: PR #11 で `repository` field を Anthropic Plugin spec 準拠の string に修正 (object → string)、PR #12 で `.claude-plugin/marketplace.json` 追加 (Tecnos-STRIDE 全体を local marketplace として登録 → Plugin install 再現性向上)、PR #13 で manual/51 + README を実機検証 install フロー + 実 runtime namespace `/tecnos-stride-value:stride-*` (元の `/stride:*` ではなく Plugin name 経由) に整合 |
| **v6.0.x — 普及準備 (Phase D)** | 2026-04-30 | **[PR #9](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/9) — 🚢 VALUE Upstream Extension Phase D (FEAT-VALD01) — 「使える状態」から「使われる状態」へ** — Phase A/B/C で完成した VALUE Upstream Extension v6.0 を実プロジェクトで利用可能にする普及準備パッケージ。**Tecnos-STRIDE 本体 VERSION 6.0.0 維持** (普及準備のため bump なし)。(1) **3 profile 別 playbook** (各 3000-5000 字 6 章): `manual/48_enterprise_erp_value_playbook.md` (大型 ERP 統合 SAP/mcframe 案件) / `49_saas_integration_value_playbook.md` (SaaS-to-SaaS/ERP 統合) / `50_prototype_value_playbook.md` (rapid prototyping 軽量 path)。(2) **v5.x → v6.0 Migration Guide** (`manual/migration/v54_to_v60.md`) + `sdd-templates/tools/upstream_migration_helper.py` 新規 (basic_design.md → Phase 0 yaml seed 半自動逆生成 CLI、BACCM 6 軸ごとに「自動抽出可能」「要人間確認」のラベル付与)。(3) **Dogfooding sanitized 学び**: `memory/lessons_learned/upstream_dogfooding/external_scm_pilot_01.md` (実 SCM 案件で得た学びを §Rule 15-B サニタイズ済 lessons として記録、外部固有名詞除外)。(4) **Tests +9** (baseline 769 → **778 passed**、回帰 0): `tests/test_upstream_migration_helper.py`。Phase E (Cowork Plugin) への申し送り: 上位コンサル単独で Phase 0/1 を完成可能にする Plugin 化 |
| **v6.0.x — bugfix v7 (post-Phase C)** | 2026-04-30 | **[PR #8](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/8) — 🐛 YAML frontmatter compatibility (post-Phase C bugfix)** — Phase C 完成後の `yaml.safe_load` vs frontmatter 競合の修正。`upstream_*.yaml` の解析時に YAML frontmatter (Markdown 上部の `---...---` ブロック) と本体 YAML が混在するケースで safe_load が失敗していた問題を、`sdd-templates/tools/stride_shared_lib.py` の helper で frontmatter を切り分けて safe_load する設計に変更。`upstream_scaffolder` / `baccm_completeness_checker` / `upstream_iteration_evaluator` / `upstream_lint` / `upstream_bridge` / `solution_evaluator` の 6 tools が新 helper を経由するよう改修、`tests/test_yaml_frontmatter_compatibility.py` (+1 test) で回帰防止。Tecnos-STRIDE 本体 VERSION 6.0.0 不変 |
| **v6.0.0-tecnos-stride-value** | 2026-04-29 | **[PR #4](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/4) — 🚀 VALUE Upstream Extension Phase C (FEAT-VALC01) — VALUE 完成形 + Constitution Article XV-XVII ratification (SemVer MAJOR bump)** — Phase A (schema 基盤) + Phase B (CLI scaffold) を v6.0 完成形へ昇華する総仕上げ。(1) `sdd-templates/tools/upstream_bridge.py` 新設 — Phase 0/0.3/0.5 → Phase 1 自動 populate (`stride upstream-bridge <feature> [--apply]`)、APPROVAL.md パーサで Gate 1/2 immutability check 内蔵（承認済 feature の `--apply` を fail-closed で拒否、`process.bpmn` / `implementation-details/*` には書き込まない）。(2) `sdd-templates/tools/solution_evaluator.py` 新設 — BABOK KA8 稼働後評価 (`stride retro --solution-eval --kpi-source <path> --adoption-survey <path>`)、`business_need.yaml.success_criteria` を目標 KPI として `kpi_actuals.yaml` / `adoption_survey.yaml` / `runs/*/lessons.md` から実績集計、`specs/<feature>/state/solution_eval_<ts>.md` Markdown レポート出力 + overall_pass 判定 (KPI 半数以上未達 or Issues 10 件以上で FAIL)。(3) Constitution 本体マージ — `memory/constitution.md` の `articles[]` 配列に **Article XV (BACCM Completeness Gate)** / **XVI (Layered Requirement Architecture / 4-layer aligned)** / **XVII (Solution Evaluation Feedback Loop / BABOK KA8)** の 3 Article を末尾追加 (14 → 17)、トップレベル `version` を 5.4.0-tecnos-stride → 6.0.0-tecnos-stride-value MAJOR bump、`last_reviewed_at` を 2026-04-29 に更新、`amendment_history` に 3 エントリ追加 (v6.0.0-tecnos-stride-value)、`memory/constitution_amendments/{XV,XVI,XVII}_*.md` の Status を **proposed → ratified** (2026-04-29, Phase C, FEAT-VALC01) に遷移。(4) `sdd-templates/templates/basic_design_template.md` の `links` に `upstream_dir_ref` / `upstream_policy_ref` / `baccm_completeness_ref` の 3 参照を追加。(5) `manual/45_upstream_bridge_guide.md` / `46_solution_evaluation_guide.md` / `47_v60_release_notes.md` 新規 (各 5000-7000 字) + sidebar / project_map / README 追記。(6) Tests +41 (test_upstream_bridge 13 + test_solution_evaluator 9 + test_constitution_xv_xvi_xvii_ratified 9 + test_stride_cli_phase_c 9 + Phase A test 改修 + Phase B test 改修 = baseline 717 → **758 passed**、回帰 0)。(7) Post-review cleanup commit (`0f7d383`) — yaml import dedup + APPROVAL parser hardening (`set(approver) <= {"_"}` で全 underscore 偽装を確実に弾く) + 直接 boundary tests +4。(8) VERSION single-commit invariant 厳格遵守 (`git diff --name-only HEAD~1..HEAD == sdd-templates/VERSION` 機械検証 PASS)。**Breaking Changes (SemVer MAJOR)**: Constitution articles[] 14 → 17 / トップレベル version 6.0 系 / basic_design_template.md links 3 keys 追加 (既存プロジェクトは手動更新必要)。Phase D 申し送り: 実プロジェクト dogfooding / Profile 別 playbook (manual/48-50) / Migration Guide (v54_to_v60.md) / `upstream_migration_helper.py` |
| **v5.5.0-tecnos-stride** | 2026-04-29 | **[PR #3](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/3) — VALUE Upstream Extension Phase B (FEAT-VALB01) — CLI scaffold + lint/eval extension** — Phase A の schema 基盤を実コマンド化。(1) Python tools 5 件新設: `upstream_scaffolder.py` (Phase 0/0.3/0.5 YAML 成果物 scaffold) / `baccm_completeness_checker.py` (BABOK BACCM 6 軸完全性検証) / `upstream_iteration_evaluator.py` (3 反復パターン評価) / `technique_library_query.py` (BABOK 50 techniques 検索) / `upstream_lint.py` (Layered Requirements Modeling broken link / template drift / technique unknown 検出)。(2) `bin/stride` に `upstream init/validate` 新サブコマンド + `lint --upstream` フラグ + `evaluate --phase discovery` 拡張。(3) `stride_lint.py` に 4 新エラーコード追加: **BACCM_INCOMPLETE** / **Layered Requirements Modeling_BROKEN_LINK** / **UPSTREAM_TEMPLATE_DRIFT** / **BABOK_TECHNIQUE_UNKNOWN**。(4) Static JSON Schema 15 件 (Draft 2020-12) を `sdd-templates/static/upstream_schemas/` に配置。(5) `manual/43_upstream_cli_guide.md` / `44_upstream_iteration_workflow.md` 新規。(6) Tests +38 (baseline 649 → 717 passed、回帰 0)。VERSION 5.4.0-tecnos-stride → 5.5.0-tecnos-stride。Phase A schema は完全保持、Constitution Article XV-XVII は依然 proposed 状態のまま (Phase C で本体マージ)。 |
| **v5.4.0** | 2026-04-24 | **Reporting Lightening (Profile-Aware)** — 報告粒度 + Completeness 閾値のみの軽量化。ガバナンスは不変。(1) `basic_design.profile` SSoT + state.yaml top-level cache で 3 Profile（enterprise-erp / saas-integration / prototype）を宣言。`shared/policies/profile_policy.yaml` 新設。(2) `sdd_bootstrap.md §5` に Profile-Dependent Reporting Matrix（5-step full / critical-only / one-line）+ 1-line 合成ロジック（Step 1-5 全実行前提）追加。(3) `stride pr-check --summary-line` で project-level 1-line 出力（7 base checks + optional mutation、task-level は責務境界外）。(4) Completeness Principle を Profile-aware 閾値（200/150/100 行 × 5/4/3 ファイル AND）+ risk_flags 最優先「海」判定に改訂。(5) stride-lint に PROFILE_UNKNOWN / PROFILE_MISMATCH / PROFILE_MISSING 追加。(6) stride init --profile フラグ（basic_design.profile SSoT と state/state.yaml top-level profile キャッシュの両方を同期）。20 新規テスト。**BPMN / Evidence / SEC-006 / Ops Pack / Epic-Feature Hierarchy / Coverage Tier は全 Profile で現行正本のまま不変**（canonical_source 参照）。**v5.4 系で VALUE Upstream Extension Phase A (FEAT-VALA01、[PR #1](https://github.com/tecnos-japan-cbp/tecnos-stride/pull/1)) の schema 基盤も並行投入** — 4 policies + 16 templates + 3 proposed amendments (Constitution 本体不変) + manual 39-42 + 5 tests。**Article XV-XVII の本体マージは Phase C (v6.0)** で実施 |
| **v5.3.3** | 2026-04-17 | **BPMN Rule Compliance Enforcement** — `epic_flow.bpmn` / `process.bpmn` がルール通りに作成されない 7 根本原因を ultrathink 調査で特定。(1) `sdd_bootstrap.md` に §4-BPMN 新設（Step 1-6 MUST-DO、FEAT/EPIC 決定ツリー、ID スキーム表、14+9 Hard Requirements、top 失敗パターン、lint エラーコード早見表）(2) `docs/bpmn_quick_reference.md` 新規作成（1-page AI 向け checklist）(3) `epic_flow_template.bpmn` に `xmlns:xsi` 宣言 + `isExecutable="false"` 明示（4) `epic_validator.validate_epic_bpmn` を FEAT と同等レベルに強化（内部 process の incoming/outgoing、sourceRef/targetRef、BPMNShape/Edge 完全性）(5) `stride_lint.validate_bpmn` に sequenceFlow sourceRef/targetRef 参照整合性チェック追加（6) `basic_design_template.md` に BPMN ID 一致ルール明記。BPMN 作成精度向上の小規模 patch |
| **v5.3.2** | 2026-04-22 | **Template Scaffolding Bug Fixes** — テンプレクローン運用で発見した 4 つの bug 修正。(1) `.claude/settings.json` から個人開発者の `entire hooks` を除去（personal hooks は `.claude/settings.local.json` へ退避）(2) stride-new-project.sh Step 4 を `stride hooks --tool claude --force` で常時実行（以前は既存 settings.json で skip し Phase Gate hook 未 install）(3) Step 6 GitHub/Linear の `if cmd \| sed ; then` exit-code-from-last-command bug を exit code 捕捉に修正（以前は sed 常時 0 で失敗を「bound」と偽陽性表示）(4) Step 6 GitHub を `--org` 未指定時に early skip + 手動 fallback 案内。機能不変の小規模 patch |
| **v5.3.1** | 2026-04-19 | **Per-Project Tracker Isolation** — テンプレをクローンして新プロジェクトを作る毎に、Linear Project + GitHub Project V2 を専用作成・binding する仕組み / `stride linear project <create\|list\|use\|status>` + `stride project <create\|list\|use\|status>` CLI 追加 / `memory/linear.yaml` + `memory/github_project.yaml` 新設（SSoT 永続化）/ `stride new-project` に `--linear-project` / `--github-project` / `--no-linear-project` / `--no-github-project` フラグ（Step 6/7 で認証済なら自動作成、未認証は graceful skip）/ 18 new tests（8 GitHub + 10 Linear integration 拡張）/ manual 37 §11 + agent_docs §13 |
| **v5.3.0** | 2026-04-19 | **Linear Integration** — Run 成果物を Linear Issue に一元可視化する `linear_bridge.py`（urllib-based GraphQL、外部依存ゼロ）新設 / `stride linear <init\|findings\|evidence\|learn\|sync\|close\|status>` CLI / `STRIDE_LINEAR_AUTO=1` で `sdd_planning_bridge` から自動同期 / `state.yaml` に `work_items[].linear_issue_id` / 19 self-tests + 10 integration tests / `manual/37_linear_integration_guide.md` / `LINEAR_API_KEY` 未設定時は全コマンド graceful skip（既存フロー完全不変の純粋 opt-in） |
| **v5.2.1** | 2026-04-19 | **Symphony Agent Reproducibility + SEC-006 Provenance Expansion** — Symphony `agent.claude_code` に `model` / `effort_level` (low/medium/high/xhigh/max) / `max_output_tokens` を追加（`ConfigLoader` で検証、runner で `--model`/`--effort`/`CLAUDE_CODE_MAX_OUTPUT_TOKENS` 伝播、4 新規テスト）/ SEC-006 AI provenance キーワード 6 件追加（provider_surface / model_id / execution_settings / budget_controls / tokenizer_notes / cyber_safeguards_status）、`stride_security_checker` + `tecnos_org_constraints` + evidence_pack/plan テンプレ反映 / `.entire/` + `evaluator_latest.json` gitignore / manual P2 修正 / 562 tests (default 558 passed / 1 skipped / 3 deselected) |
| **v5.2.0** | 2026-04-17 | **Opus 4.7 Literal-Follow Tuneup + Hermeticity** — Governance hardening（Instruction Precedence 10段ヒエラルキー / AI Action Boundary 3分類 / lint loop bounds max 5 / Completeness 4条件数値基準 / Task Completion 固定テンプレート / WI flow 1-16連番）/ `stride_shared_lib.py`（Canonical YAML抽出を 5 caller で集約、8 self-tests）/ `stride symphony` CLI 統合（run/dispatch/status/validate/janitor 5 subcmds）/ Execution Authority E2E（14 tests, Normal/Failure/Janitor）/ stride_harness_report Test 6 修正 / manual2 archive（single SSoT 化）/ hermetic pytest（`addopts -m 'not api'` + `testpaths` sdd-templates/tests 追加、default 554 passed / 1 skipped / 3 deselected） |
| **v5.1.0** | 2026-04-08 | **Harness Maturity** — `stride pr-check --mutation`（Check [8/8]）/ `stride evaluate --review`（Self-Review Loop, borderline [70,85)）/ `stride health --runtime`（デッドコード・カバレッジ減衰）/ `stride harness-report`（8制御インベントリ）/ Symphony Janitor |
| **v5.0.0** | 2026-04-02 | **CLI UX Maturity** — clig.dev準拠（カラー出力・`-o ndjson`・`--plain` TSV・パスtypoサジェスト・YAML事前検証・アクター追跡・`suggested_action`表示・次ステップ提案）/ Agent Quick Reference / Docsify GitHub Pages |
| **v4.9.0** | 2026-03-31 | Completeness Principle / `stride security`（daily/audit 2段階10チェック）/ `stride retro`（Feature/Epic定量ふりかえり）/ LLM trust boundary / Security knowledge tags |
| **v4.8.0** | 2026-03-23 | Database Lifecycle Management / Camunda 8.8 BPMN Refresh（FEAT `process.bpmn` + EPIC `epic_flow.bpmn` + YAML/BPMN description alignment） / description coverage gate / `manual/31_database_lifecycle_guide.md` |
| **v4.7.0** | 2026-03-16 | Enterprise Hierarchy CLI Integration / `enterprise.yaml` / `stride epic` / `stride init --epic` / `stride lint <path> --enterprise` / `stride lint --all --enterprise` |
| **v4.6.0** | 2026-03-11 | Schema-Gated AI Authority — Execution Authority 3層宣言 / Article XIV / ED/CF Score / wi_readiness Check 8 |
| v4.5.1 | 2026-03-10 | Tier Mismatch WARN / Amendment Fast Track / PM クイックスタート / Symphony バグ修正 |
| v4.5.0 | 2026-03-10 | BDD Acceptance Criteria / Symphony Orchestration（GitHub Issues → Agent 自動実行） |
| v4.4.0 | 2026-02-15 | AI Autonomous Execution — AI が実行者(R)、人間は承認者(A)のみ |
| v4.3.0 | 2026-02-14 | PR Readiness Checker — 7チェック統合 PR 品質ゲート |
| v4.2.0 | 2026-02-14 | Monorepo Default + Scale Levels / Living Spec Drift / Evidence Metrics |
| v4.1.0 | 2026-02-08 | Execution Governance — Auto-Continue / DDD / ADR |
| **v4.0.0** | 2026-02-08 | Multi-Tool Strategy — SDD_MANIFESTO.md 分離、Cursor/Copilot 対応 |
| v3.x | 2026-02-07〜08 | Adaptive Execution / Multi-Team / Brownfield Detection |
| v2.x | 2026-01〜02 | Enterprise Edition / Tecnos-STRIDE 導入 |
| v1.x | 2025-12〜2026-01 | SDD Template 初期リリース(2025/12/12) → Tecnos Edition（Lint CLI / Phase Gate / Lite Mode / 5言語テスト / Docsify / Evidence Pack） |

---

**Tecnos-STRIDE v6.0.0-tecnos-stride-value** + **Cowork Plugin v0.5.0-agent-hardening** + **BPMN Pack v1.1.0** — AI と共に前進する、仕様駆動開発 (BABOK v3 + Layered Requirements Modeling + value-driven discovery method 三脚 / 17 Constitution Articles 体制 / Discovery → Design → Implementation → Operation フルサイクル機械検証 / Phase A〜G 完成 + BPMN Pack 拡張 + Method Store Publishing 拡張 / 上位コンサル単独で Phase 0/1 を実行可能な Cowork Plugin (commands 14 + skills 8 + reference_files 45 + bpmn pack 同梱) + Simple UX `/start` 1 コマンド conductor 設計 / 3 profile (enterprise-erp / saas-integration / prototype) の playbook + GitHub Actions CI 統合 + サニタイズ自動 grep + state.yaml Phase 2-4 進捗追跡 + Method Store OCI 配信 (cosign keyless + 3 channel + 5 min MTTR rollback))。
