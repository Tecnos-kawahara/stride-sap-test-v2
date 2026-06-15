---
description: Tecnos-STRIDE Cowork Plugin の 1 コマンド入口。コンサルの自然言語ひとこと指示から、状態判定 + 次の最適ステップ自動選択
  + 適切な専門 skill 自動起動 まで一気通貫で進める。固有語 / Phase 番号 / 引数構文を覚える必要なし。
argument-hint: '[<自然言語の指示>]'
plane: internal
visibility: id_only
return_policy:
  customer: blocked
  platform_admin: id_only
  tecnos_admin: full
---

# /stride:start

**Tecnos-STRIDE Cowork Plugin の唯一の入口**。コンサルが Cowork で打つのはこれだけ。あとは Plugin が状態を判定して進めてくれます。

> Phase G UX-prep PR-E で新設。「**自然言語ひとことで進む**」UX を実現する master command。

## Usage

```
/tecnos-stride-value:start [<自然言語の指示>]
```

### 引数なし

```
/tecnos-stride-value:start
```
→ 現在の状態を判定し、次のおすすめステップを提示

### 自然言語ひとこと

```
/tecnos-stride-value:start 新規顧客の supply management PoC を始めたい
/tecnos-stride-value:start Discovery 進めて
/tecnos-stride-value:start 顧客レビュー資料作って
/tecnos-stride-value:start Claude Code に渡して
/tecnos-stride-value:start 次に進んで
/tecnos-stride-value:start 完全性チェックして
```

## Workflow

### 1. Trigger Conductor Skill

`stride-conductor` skill を auto-trigger:

- 引数あり → コンサルの自然言語意図として渡す
- 引数なし → 「現状を確認して次のおすすめを提示」と解釈

### 2. State Detection (state.yaml + ファイル存在で判定)

conductor 内部で `specs/<feature>/state/state.yaml` (Phase F WI-010 の `phase_2/3/4/final` schema) + 各 yaml ファイル存在を読んで進捗判定:

| 状態 | conductor の応答例 |
|---|---|
| 何もない | "新規 PoC ですね。リポジトリから作りますか? それとも既存 repo で feature 追加?" |
| Phase 0 着手中 (BACCM 軸途中) | "Phase 0 Discovery 中。残 [X] 軸 (例: stakeholder/value/context) を進めますか?" |
| Phase 0 完了、Phase 0.5 未着手 | "Phase 0 完了 ✅。次は Layered Context Modelling です。進めますか?" |
| Phase 0.5 完了、Phase 1 未着手 | "Phase 0 全完了 ✅。Phase 1 (設計書 + BPMN) に進みますか?" |
| basic_design.md 完成、handoff 未 | "Phase 1 完成 ✅。顧客レビュー (HTML 出力) する? それとも Claude Code に handoff?" |
| handoff 済、Phase 3 未 | "handoff 完了 ✅。SDD Phase 3 (Tasking) に進みますか?" |
| Phase 3 完了 | "Tasking 完了 ✅。Claude Code 担当者へ引き渡し済。Cowork の役割は完了です。" |

### 3. Intent Interpretation + Skill Auto-launch

conductor が自然言語意図を解釈し、適切な内部 skill / command を起動:

| 自然言語 (例) | 内部 action |
|---|---|
| 「PoC 始めたい」「新規顧客」 | `/stride:bootstrap-repo` 引数を対話収集 + 起動 |
| 「Discovery 進めて」「BACCM」「ヒアリング」 | `baccm-discovery` skill 起動 (固有語補完) |
| 「Elicit」「インタビュー設計」 | `babok-elicitation` skill 起動 |
| 「Context Modelling」「actor」「business use case」 | `layered-context-modelling` skill 起動 |
| 「完全性チェック」「validate」 | `/stride:validate` |
| 「Phase 1 行く」「設計始める」 | `upstream-bridge` → `basic-design-authoring` → `bpmn-authoring` を順次 |
| 「設計書」「basic_design」「BPMN」 | `basic-design-authoring` + `bpmn-authoring` skill |
| 「Epic」「複数 feature」 | `epic-decomposition` skill |
| 「顧客レビュー」「HTML」「資料」 | `/stride:export-html` |
| 「Claude Code に渡す」「handoff」 | `/stride:handoff` |
| 「Tasking」「tasks.md」 | `/stride:tasking` |
| 「次に進んで」「次は?」 | state 判定 + 自動選択 |

### 4. Confirmation + Execution

conductor は自動実行ではなく **コンサルに確認** してから実行:

```
[conductor]:
"customer_a_oms の Phase 0 Discovery で stakeholder マップを作成します。
ヒアリング情報 (主要 stakeholder 3 名以上) をお持ちですか?

  yes → baccm-discovery skill で対話開始
  no  → ヒアリングが必要です。顧客側担当者へ依頼しますか?
  別の指示 → どうぞ"
```

### 5. Progress Report (各 step 完了時)

```
[conductor]:
"✅ stakeholder_map.yaml 完成 (主要 3 名: <sanitized>)
 残 BACCM 軸: value / context (2 軸)
 次は value canvas に進みますか?"
```

### 6. BLOCKER 時の対処案内

サニタイズ grep / 完全性 fail / hash 検証 fail 等が発生した場合:

```
[conductor]:
"⛔ §Rule 15-B サニタイズで顧客固有名詞を検出 (specs/customer_a_oms/upstream/business_need.yaml L23)
 提案: 該当箇所を抽象化してから handoff を再実行してください
 一緒に該当箇所を見ますか? (yes/no)"
```

## Why /stride:start?

### Before (Phase F まで): 12 commands を覚える

```
/tecnos-stride-value:stride-bootstrap-repo <repo> --org <org> --profile <P>
/tecnos-stride-value:stride-init <feature> --profile <P>
/tecnos-stride-value:stride-discovery <feature>
/tecnos-stride-value:stride-elicit <feature>
/tecnos-stride-value:stride-context-model <feature>
/tecnos-stride-value:stride-validate <feature>
/tecnos-stride-value:stride-bridge <feature>
/tecnos-stride-value:stride-design <feature>
/tecnos-stride-value:stride-epic-init <EPIC_ID>
/tecnos-stride-value:stride-handoff <feature>
/tecnos-stride-value:stride-export-html <feature>
/tecnos-stride-value:stride-tasking <feature>
```

12 個の中から「次は何打つんだ?」と毎回判断 + 引数構文を覚える + 固有語前置詞 (Tecnos-STRIDE / BACCM 等) を毎回打つ。

### After (Phase G UX-prep PR-E): 1 コマンドだけ

```
/tecnos-stride-value:start [自然言語の指示]
```

これだけ。conductor が状態と意図を解釈して内部で全部やる。コンサルは普通の業務日本語で OK。

## Notes

- 既存 12 commands は **internal reference として残す** (詳細制御したいケース、auto-trigger 不発時の fallback)
- conductor 内部から呼ばれる時は固有語が補完されるため、専門 skill (baccm-discovery 等) の Phase F WI-003 固有語必須は維持される (誤起動回避継続)
- コンサルが慣れてきたら直接 12 commands を打つこともできる (互換性維持)
- **(2026-05-08 incident hardening)** conductor が specialized skill (bpmn-authoring 等) を内部 dispatch する直前に、対象 skill の SKILL.md を **literal Read** + STEP 0 PRE-FLIGHT リストを user に提示する義務がある。これは「skill 名と description だけで合成を始める」failure mode の構造的防止策。詳細は `cowork-plugin/skills/stride-conductor/SKILL.md` §⚠️ Dispatch 前の MANDATORY Read 参照

## References

- conductor skill: `cowork-plugin/skills/stride-conductor/SKILL.md`
- state.yaml schema (Phase F WI-010): `cowork-plugin/scripts/validate_state_yaml.py`
- 12 internal commands: `cowork-plugin/commands/stride-{bootstrap-repo,init,discovery,elicit,context-model,validate,bridge,design,epic-init,handoff,export-html,tasking}.md`
- Plugin runtime SSoT: `cowork-plugin/.claude-plugin/plugin.json` (v0.3.0-simple-ux)

> Phase G UX-prep PR-E で新設。Cowork での「**自然言語ひとことで進む**」UX を実現する 1 コマンド入口。
