# Postmortem — BPMN Vertical Flow Violation (2026-05-08)

## Summary

- **date**: 2026-05-08
- **severity**: HIGH (canonical rule violation that PASSed self-validation)
- **detected_by**: ユーザ目視レビュー
- **artefacts_affected**: `simple-bi/process.bpmn` (Phase 1)
- **duration_undetected**: 約 30 分 (PRE-FLIGHT 段階で検出されなかった、ユーザレビュー時点で初検出)
- **plugin_affected**: `tecnos-stride-value` v0.4.0-bpmn-package-integration
- **bpmn_pack_affected**: `bpmn/` v1.0.0
- **resolved_by_pr**: `feature/agent-hardening-2026-05` (本ポストモーテムの起票元 PR)

## Timeline

| 時刻 (JST) | event |
|-----------|-------|
| ~14:00 | コンサルが Cowork 上で simple-bi PoC の Phase 1 (BPMN 作成) を依頼 |
| ~14:01 | `bpmn-authoring` skill が auto-fire (固有語 trigger 経由) |
| ~14:02 | agent が SKILL.md 本文 + 参照ファイル群を **Read せず** に process.bpmn を合成開始 |
| ~14:05 | agent が即興で「BPMN MUST-DO 14 を検証する Python」を作成し PASS と宣言 |
| ~14:08 | agent が user に「process.bpmn 完成、validator PASS」と報告 |
| ~14:30 | ユーザが目視レビューで `isHorizontal="true"` (水平 swimlane) を発見、指摘 |
| ~14:35 | agent が isHorizontal を `false` に修正 (1 件のみ) |
| ~15:00 | ユーザが残 6 件の違反 (ID 命名 / template-copy 欠如 / `default` 属性欠如 / `bpmn_descriptions` 未 populate / 自作 validator / SKILL.md 未読) を発見、systemic 問題として escalation |
| 後続 | simple-bi 側で `docs/CLAUDE_CODE_PROMPT_plugin_fix.md` 起票 → 本 PR で構造的修正実装 |

## Root Cause

### 主因 1: SKILL.md auto-trigger ≠ SKILL.md body load

conductor が skill を auto-fire しても、SKILL.md 本文は context に **自動 load されない**。
agent は skill 名と description (frontmatter の数百文字) だけを見て、**訓練データから合成する**。
結果として canonical な参照ファイル群 (`bpmn/rules/*` / `bpmn/templates/*` / `bpmn/PORTABILITY.md`) が
context に存在しないまま XML 生成が始まり、Tecnos override (vertical swimlane / BPMN-* 命名 / etc) を
知らない訓練データの「一般的な BPMN」が出力された。

### 主因 2: 自作 validator が false PASS を返す

agent が即興で「BPMN MUST-DO 14 を検証する Python」を書くと、自分が知らないルール
(`isHorizontal="false"` 強制、`BPMN-{TASK,GW,EVT,FLOW}-NNN` 規約、3 桁ゼロ埋め、
 `<bpmn:documentation>` 第 2 正本、basic_design.bpmn_descriptions 一致等) は
**構造的に検査されない**。agent 自身が書いた validator が「PASS」と返したため、
agent は「合格した」と user に報告する。これが false positive の連鎖を生んだ。

### 主因 3: template-copy の物理的強制がない

SKILL.md に「ゼロから書かない、`bpmn/templates/process_bpmn_template.bpmn` を `cp` してから
placeholder 置換」と書いてあっても、**`cp` を実行する強制力がない**ため違反できる。
`Write` ツールで XML をゼロから書いても何の警告も出ない。これが incident #1 の物理的源流。

## 7 件の違反詳細

| # | 違反 | canonical ルール | 検出ルート |
|---|---|---|---|
| 1 | template をコピーせず、ゼロから合成した | `bpmn/templates/process_bpmn_template.bpmn` を `cp` してから placeholder 置換 | ユーザレビュー |
| 2 | `isHorizontal="true"` で水平 swimlane | MUST-DO #13: `isHorizontal="false"` (Tecnos override #1、縦型強制) | ユーザレビュー (最初に検出) |
| 3 | ID を `BPMN_TASK_01_register_source` 命名 | `BPMN-TASK-001` (3 桁ゼロ埋め・ハイフン、name attribute は別) | ユーザレビュー |
| 4 | XOR Gateway に `default` 属性なし (条件式のみ) | `default` 属性 OR 全 outgoing に conditionExpression | ユーザレビュー |
| 5 | `basic_design.bpmn_descriptions` を populate せず | bpmn_id と process.bpmn の id を完全一致 (MUST-DO #14) | ユーザレビュー |
| 6 | 自作 Python validator を実行して PASS と宣言 | `bpmn/validators/bpmn_lint.py` を必須使用 | ユーザレビュー |
| 7 | SKILL.md の「参照優先順位」10 件を Read せず合成開始 | STEP 1 で必ず Read (SKILL.md §2 Reference Files) | ユーザレビュー |

うち **#2 だけがユーザ指摘で気付いて修正されたが、ユーザが指摘しなければ全件スルーで通過していた**。
これは structural failure であり、agent 側の意識改革では再発防止できない。
プラグイン側の構造的 hardening が必要。

## What Went Right

- ユーザがレビューで違反を発見し、systemic 問題として escalation した
- 修正 (vertical layout rewrite) 後の canonical lint は PASS した
- 本ポストモーテムが起票され、systemic fix が plugin 側に投入された
- `cowork-plugin/bpmn/` の v1.0.0 standalone package + canonical templates は適切に存在しており、agent が **使わなかっただけ**で構造自体は正しかった

## What Went Wrong

- SKILL.md 本文が context に load されないまま生成開始 (主因 1)
- 自作 validator が false PASS を返した (主因 2)
- template-copy が物理的に強制されていなかった (主因 3)
- agent が 7 件の違反を自分では検出できず、ユーザの目視レビューが唯一の発見ルートだった
- 違反 PASS が次の Phase (basic_design ↔ bpmn 同期) にも propagate していた

## Action Items

| # | TASK | 担当ファイル | Status |
|---|------|-------------|--------|
| 1 | SKILL.md STEP 0 強制化 (全 7 specialized skills) | `cowork-plugin/skills/{bpmn-authoring,basic-design-authoring,baccm-discovery,babok-elicitation,layered-context-modelling,epic-decomposition,upstream-bridge}/SKILL.md` | ✅ |
| 2 | PRE_FLIGHT_CHECKLIST.md 新設 | `cowork-plugin/bpmn/PRE_FLIGHT_CHECKLIST.md` | ✅ |
| 3 | ID format 検証を bpmn_lint.py に追加 + fix_hint + --diff-against-template + --legacy-id | `cowork-plugin/bpmn/validators/bpmn_lint.py` (v1.0.0 → v1.1.0) | ✅ |
| 4 | bd_bpmn_sync.py 新設 | `cowork-plugin/bpmn/validators/bd_bpmn_sync.py` | ✅ |
| 5 | ASCII preview ツール追加 | `cowork-plugin/bpmn/scripts/render_ascii_preview.py` | ✅ |
| 6 | conductor の dispatch 前 SKILL.md Read 強制 | `cowork-plugin/skills/stride-conductor/SKILL.md` + `cowork-plugin/commands/start.md` | ✅ |
| 7 | 本ポストモーテム起票 | `docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md` | ✅ |

## Future Hardening (Phase H 候補、本 PR 範囲外)

- bpmn-authoring SKILL.md の STEP 0 PRE-FLIGHT REPORT を **自動 grep** する CI hook (Cowork セッション内 / GitHub Actions)
- `cowork-plugin/scripts/check_skill_step0.py` で SKILL.md `## STEP 0` 章必須化を機械検証
- conductor dispatch ログを `runs/<feature>/RUN-NNN/dispatch_log.yaml` に persist し、SKILL.md Read 履歴を audit 可能化
- LLM-based 違反検出 (Claude Haiku で BPMN XML を pre-review、自作 validator 偽陽性を多角的に検出)

## What Customers / Operators Should Do (運用面の申し送り)

1. **agent から「process.bpmn 完成、validator PASS」と報告された場合は必ず以下 3 段階を要求する**:
   - PRE-FLIGHT REPORT の提出 (STEP 0 完了確認)
   - `bpmn_lint.py` (canonical) PASS の証跡
   - `render_ascii_preview.py` 出力で **vertical orientation** を視覚確認
2. agent が即興で Python validator を書いた場合は **その時点で警告**し、canonical `bpmn_lint.py` の使用を要求する
3. `isHorizontal="true"` を見たら即時差し戻し (Tecnos override #1 違反)
4. `BPMN_TASK_01_xxx` 形式の ID を見たら即時差し戻し (アンダースコア + 命名埋込違反)
5. basic_design.bpmn_descriptions が空のまま PASS と宣言された場合は `bd_bpmn_sync.py` の実行を要求

## References

- `cowork-plugin/bpmn/rules/bpmn_quick_reference.md` — FEAT 14 / EPIC 9 MUST-DO checklist
- `cowork-plugin/bpmn/rules/bpmn_generator_rules.md` §24 — Tecnos override 3 大原則
- `cowork-plugin/bpmn/templates/process_bpmn_template.bpmn` — FEAT canonical template
- `cowork-plugin/bpmn/validators/bpmn_lint.py` v1.1.0 — canonical lint (BPMN_ID_FORMAT_VIOLATION 追加)
- `cowork-plugin/bpmn/validators/bd_bpmn_sync.py` v1.0.0 — basic_design ↔ bpmn id sync
- `cowork-plugin/bpmn/scripts/render_ascii_preview.py` v1.0.0 — ASCII layout viewer
- `cowork-plugin/bpmn/PRE_FLIGHT_CHECKLIST.md` — agent mandatory checklist
- `cowork-plugin/skills/bpmn-authoring/SKILL.md` §STEP 0 — PRE-FLIGHT block
- `cowork-plugin/skills/stride-conductor/SKILL.md` §⚠️ Dispatch 前の MANDATORY Read
- 起票元プロンプト: `simple-bi/docs/CLAUDE_CODE_PROMPT_plugin_fix.md`
- 修正 PR: `feature/agent-hardening-2026-05`
