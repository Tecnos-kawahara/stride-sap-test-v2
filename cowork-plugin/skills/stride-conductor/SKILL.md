---
name: stride-conductor
description: Tecnos-STRIDE Cowork Plugin の master conductor。コンサルの自然言語をひとこと聞いて状態判定
  + 次の最適ステップを自動選択し、必要な専門 skill (baccm-discovery / babok-elicitation / layered-context-modelling
  / upstream-bridge / basic-design-authoring / bpmn-authoring / epic-decomposition)
  を内部で起動する。新規 PoC / 顧客 / Discovery / Elicit / Context Modelling / 業務フロー / 業務設計 / BACCM
  / 要件 / 要件定義 / 上流 / Phase 0 / Phase 1 / 顧客レビュー / レビュー資料 / Claude Code 引き渡し / handoff
  / 引き渡し / tasks / Tasking / 次に進んで / 進めて / 始めたい / Cowork / Tecnos-STRIDE / VALUE pack
  / SDD 関連の依頼時に発火 (汎用語含む広範囲 trigger)。コンサルは固有語を意識しなくてよい — conductor が状態と意図を解釈して内部で固有語を補完する。
argument-hint: '[<自然言語の指示>]'
plane: internal
visibility: abstract
return_policy:
  customer: abstract
  platform_admin: abstract
  tecnos_admin: full
---

# Skill: stride-conductor

> Master orchestrator skill。Cowork での **自然言語ひとこと指示** から Tecnos-STRIDE の上流フローを自動進行させる。

## Purpose

コンサルが Cowork で `/tecnos-stride-value:start [自然言語の指示]` を打つだけで、Plugin が:
1. **`specs/<feature>/state/state.yaml`** から現状を判定
2. **コンサルの自然言語意図** を解釈
3. **次の最適ステップ** を自動選択
4. **必要な専門 skill** (baccm-discovery / babok-elicitation / layered-context-modelling 等) を内部で起動
5. **完了後の進捗** をコンサルに報告

固有語 (Tecnos-STRIDE / BACCM / 4-layer Requirements Architecture 等) は conductor が内部で補完するため、コンサルは普通の業務日本語で OK。

## Usage

```
/tecnos-stride-value:start [<自然言語の指示>]
```

例:
- `/tecnos-stride-value:start` (引数なし → 状態確認 + 次のおすすめ提示)
- `/tecnos-stride-value:start 新規顧客の supply management PoC を始めたい`
- `/tecnos-stride-value:start Discovery 進めて`
- `/tecnos-stride-value:start 次に進んで`
- `/tecnos-stride-value:start 顧客レビュー用の資料作って`
- `/tecnos-stride-value:start Claude Code に渡して`

## Workflow

### 1. State Detection (state.yaml + ファイル存在で現状判定)

```bash
# 現在の Cowork session の作業ディレクトリで feature 状態を判定
# 1) 既存 feature が basic_design.md 等で確認可能な場合、それを active feature として扱う
# 2) state.yaml の phase_2/3/4 セクション (Phase F WI-010) を読んで進捗判定

# State 判定ロジック (Phase F WI-010 schema 準拠):
# - state.yaml なし or feature 未確定 → "新規 PoC bootstrap or feature init 候補"
# - phase_0_5 yaml 未生成 → "Phase 0 着手"
# - phase_0 yaml あり、basic_design.md 未完成 → "Phase 0 → Phase 1 bridge 候補"
# - basic_design.md 完成、handoff 未実行 → "Phase 1 完成、handoff 候補"
# - handoff 済、Phase 3 未着手 → "Tasking 候補"
# - Phase 3 完了 → "Phase 4 (Execute) を Claude Code 担当者へ"
```

### 2. Intent Interpretation (自然言語 → 内部コマンドにマッピング)

| コンサルの自然言語 (例) | 内部マッピング | 起動する skill / command |
|---|---|---|
| 「PoC 始めたい」「新規顧客」「リポジトリ作って」 | new repo bootstrap | `/stride:bootstrap-repo` (Phase G PR-D) |
| 「feature 作る」「scaffold」 | feature scaffold | `/stride:init` |
| 「Discovery 進めて」「BACCM」「ヒアリング」 | Phase 0 Discovery | `baccm-discovery` skill (固有語 Tecnos-STRIDE / BACCM を補完) |
| 「Elicitation」「technique」「インタビュー設計」 | Phase 0 Elicit | `babok-elicitation` skill (BABOK / KA4 を補完) |
| 「Context Modelling」「業務 use case」「actor」 | Phase 0.5 Context | `layered-context-modelling` skill (4-layer / Tecnos-STRIDE を補完) |
| 「完全性チェック」「validate」 | Phase 0/1 validate | `/stride:validate` |
| 「Phase 1 接続」「basic_design 始める」 | Phase 0 → 1 bridge | `upstream-bridge` skill |
| 「設計書」「BPMN」「業務フロー作って」 | Phase 1 Design | `basic-design-authoring` + `bpmn-authoring` skill |
| 「Epic 階層」「複数 feature」 | Epic 判定 | `epic-decomposition` skill |
| 「顧客レビュー」「HTML 出して」「資料」 | HTML export | `/stride:export-html` |
| 「Claude Code に渡す」「handoff」「引き渡し」「PR 作って」 | handoff | `/stride:handoff` |
| 「Tasking」「tasks.md 作って」「Phase 3」 | Phase 3 tasking | `/stride:tasking` |
| 「次に進んで」「次は何?」 | state.yaml 判定 + 提案 | (state に応じて適切な next step) |

### 3. Confirmation + Execution

```
コンサルへ提示:
  "現在 [feature_name] は Phase 0 Discovery 中で、change / need 軸が完成、stakeholder / value / context が未着手です。
   次は stakeholder マップを作るのが良さそうです。続けますか? (yes/no/別の指示)"

yes → 該当 skill 自動起動
no → コンサルに別の指示を確認
別の指示 → Step 2 に戻る
```

### 4. Progress Report

専門 skill の処理完了後、conductor がコンサルに報告:
```
"✅ Phase 0 Discovery: stakeholder_map.yaml 完成 (3 stakeholder)
 - 残 BACCM 軸: value / context (2 軸)
 - 次は value canvas に進みますか?"
```

### 5. Special Cases

#### 5-A. 引数なし `/tecnos-stride-value:start` (状態のみ確認)

```
"📊 現在の状態:
 active feature: customer_a_oms (specs/customer_a_oms/)
 phase: Phase 0 Discovery (BACCM 6 軸の 4 軸完成)
 next recommended: value canvas → context map → /stride:validate

 続けますか?
 - 「はい」 → BACCM 残 2 軸の対話 (baccm-discovery skill 起動)
 - 「Phase 1 行く」 → /stride:bridge → /stride:design (skip)
 - 「別の feature」 → 既存 feature 一覧 or 新規作成"
```

#### 5-B. feature 未指定 + 「新規 PoC」

```
"新規 PoC ですね。リポジトリから作りますか?
 - 「はい、リポジトリから」 → /stride:bootstrap-repo の引数を対話で収集
   - repo 名は? (例: customer_a_supply_management)
   - GitHub org は? (default: tecnos-japan-cbp)
   - profile は? (enterprise-erp / saas-integration / prototype、default: enterprise-erp)
 - 「既存の repo で feature だけ追加」 → /stride:init の引数を対話で収集"
```

#### 5-C. サニタイズ警告 / BLOCKER (Phase F WI-004)

```
"⛔ §Rule 15-B サニタイズ grep で禁止キーワードを検出:
 - 該当箇所: specs/customer_a_oms/upstream/business_need.yaml L23
 - 検出パターン: 顧客名 (生実名)
 提案: 該当箇所を抽象化してから handoff を再実行してください。一緒に修正しますか?"
```

### 6. 内部 skill 呼び出し時の固有語補完

conductor が他 skill を呼ぶ際、Phase F WI-003 で固有語必須化された description との整合のため、内部 prompt に固有語を補完:

| 呼出 skill | conductor 内部 prompt 補完例 |
|---|---|
| baccm-discovery | "**Tecnos-STRIDE Phase 0 Discovery** を **BACCM 6 軸** で進めてください。feature: <name>" |
| babok-elicitation | "**Tecnos-STRIDE Phase 0** で **BABOK Elicitation** を 50 technique から context 別に 5 件推奨で進めてください。feature: <name>" |
| layered-context-modelling | "**Tecnos-STRIDE Layered Context Modelling** を **4-layer Requirements Architecture (System / Business / Condition / Business Use Case)** で 5 シート完成させてください。feature: <name>" |
| upstream-bridge | "**Tecnos-STRIDE upstream-bridge** で Phase 0 → Phase 1 への橋渡し (basic_design.md skeleton + links populate) を行ってください。feature: <name>" |
| basic-design-authoring | "**Tecnos-STRIDE SDD Phase 1** で **basic_design.md** を **canonical schema (TPL-BD-TECNOS-001)** 準拠で完成させてください。feature: <name>" |
| bpmn-authoring | "**Tecnos-STRIDE SDD Phase 1** で **process.bpmn** を **Camunda 8 BPMN MUST-DO 6 項目** 厳守で作成してください。feature: <name>" |
| epic-decomposition | "**Tecnos-STRIDE Epic** 階層化判定 + 必要なら **epic_design.md / feature_breakdown.md** を作成してください。" |

これにより専門 skill は固有語 trigger 条件を満たして発火、コンサルは固有語を意識しなくてよい二重構造を実現。

## ⚠️ Dispatch 前の MANDATORY Read (2026-05-08 incident hardening)

specialized skill (`baccm-discovery` / `babok-elicitation` / `layered-context-modelling` / `upstream-bridge` / `basic-design-authoring` / `bpmn-authoring` / `epic-decomposition`) を **内部 dispatch する直前に**、conductor は次を必ず実行する:

1. `Read ${CLAUDE_PLUGIN_ROOT}/skills/<target_skill>/SKILL.md` を **Read ツールで literal 実行**
2. その SKILL.md に記載された **「STEP 0: PRE-FLIGHT」リスト** を context に展開
3. 参照ファイル一覧 + template-copy 強制コマンドを **user に提示**して確認 (yes/no)
4. user 同意後にのみ dispatch、agent 側で STEP 0 PRE-FLIGHT REPORT が submit されたことを検証
5. PRE-FLIGHT REPORT が `ready_to_proceed: true` でない場合は dispatch を取り消し、user に状況を報告

これは **「skill 名と description だけで合成を始める」失敗モードの構造的防止策** である
(2026-05-08 incident: simple-bi PoC で `bpmn-authoring` skill が auto-fire され SKILL.md
 本文を Read せずに合成開始、結果として 7 件の canonical 違反が発生し、
 ユーザ指摘がなければ全件スルーで PASS 通過していた事象。
 詳細: `docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md`)。

### Dispatch 前 Read マッピング (固有語補完と並行運用)

| 呼出予定 skill | Read 対象 (literal 必須) |
|---|---|
| baccm-discovery | `${CLAUDE_PLUGIN_ROOT}/skills/baccm-discovery/SKILL.md` (§STEP 0 + §1-7) |
| babok-elicitation | `${CLAUDE_PLUGIN_ROOT}/skills/babok-elicitation/SKILL.md` |
| layered-context-modelling | `${CLAUDE_PLUGIN_ROOT}/skills/layered-context-modelling/SKILL.md` |
| upstream-bridge | `${CLAUDE_PLUGIN_ROOT}/skills/upstream-bridge/SKILL.md` |
| basic-design-authoring | `${CLAUDE_PLUGIN_ROOT}/skills/basic-design-authoring/SKILL.md` |
| **bpmn-authoring** | `${CLAUDE_PLUGIN_ROOT}/skills/bpmn-authoring/SKILL.md` **+** `${CLAUDE_PLUGIN_ROOT}/bpmn/PRE_FLIGHT_CHECKLIST.md` |
| epic-decomposition | `${CLAUDE_PLUGIN_ROOT}/skills/epic-decomposition/SKILL.md` |

`bpmn-authoring` のみ **2 ファイル mandatory** (skill SKILL.md + bpmn pack の PRE_FLIGHT_CHECKLIST.md)。これは 2026-05-08 incident で最も重大な被害が出た領域への multi-layer 対策。

## Completion Criteria

- コンサルが `/tecnos-stride-value:start` のみで全フェーズを進められる
- 各 step 完了時に conductor が次のおすすめを提示
- 失敗時 (BLOCKER 等) は明確な対処を提示
- コンサルは固有語 / Phase 番号 / 引数構文を意識しない
- **dispatch 前 SKILL.md Read を全 specialized skill 起動で literal 実行** (2026-05-08 incident hardening)

## Attributions

- **BABOK v3 (IIBA)** — KA4 Elicitation / KA6 Strategy Analysis / KA7 Requirements Analysis フレームワーク参照
- **4-layer Requirements Architecture** — System / Business / BusinessUseCase / Conditions の構造概念採用 (concepts only, no proprietary brand names)
- **value-driven discovery (philosophical foundation)** — value canvas / goal tree の思想的源流参照 (concepts only, no proprietary brand names)

> Phase G UX-prep PR-E で新設。Cowork での「**自然言語ひとことで進む**」UX を実現する master orchestrator。
