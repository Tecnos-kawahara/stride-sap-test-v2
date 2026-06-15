# BPMN PRE-FLIGHT CHECKLIST (FEAT)

> 全項目 [x] になるまで artefact 生成に着手してはならない。
> agent はこのファイルを `Read` した後、メモリ内で各項目を `[ ]` → `[x]` に書き換えながら確認し、
> 最終的に `## 提出フォーマット` の形式でユーザに submit する。

これは **2026-05-08 BPMN vertical flow violation incident** (`docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md`) を契機に新設された structural guard。
SKILL.md auto-trigger ≠ SKILL.md body load の failure mode を防ぐため、
agent は「skill 名と description だけで合成を始める」のではなく、本 checklist の literal 完了を経由して artefact 生成に進むこと。

---

## A. 参照ファイル Read 完了

下記 4 ファイルを `Read` ツールで literal 読み込み:

- [ ] `bpmn/rules/bpmn_quick_reference.md` — FEAT 14 / EPIC 9 MUST-DO 1-page checklist
- [ ] `bpmn/rules/bpmn_generator_rules.md` §24 (Tecnos override) — 3 大 override 仕様
- [ ] `bpmn/templates/process_bpmn_template.bpmn` (FEAT) — canonical XML template
- [ ] `bpmn/spec/camunda_bpmn_dictionary_complete.md` — 該当箇所のみ参照 (深堀り用、2744 行)

## B. Template-copy 完了

- [ ] `cp bpmn/templates/process_bpmn_template.bpmn specs/<feature>/process.bpmn` 実行済
- [ ] target ファイルに `BPMN-PROC-XXX` placeholder が存在することを確認 (= ゼロから書いていない証跡)
- [ ] (EPIC の場合) `cp bpmn/templates/epic_flow_template.bpmn epics/<EPIC>/epic_flow.bpmn` 実行済

## C. ID 命名理解

- [ ] FEAT は `BPMN-{TASK,GW,EVT,FLOW}-NNN` (3 桁ゼロ埋め、ハイフン) と理解
  - 例: `BPMN-TASK-001`, `BPMN-GW-002`, `BPMN-EVT-003`, `BPMN-FLOW-004`
  - ❌ `BPMN_TASK_01_register_source` (アンダースコア + 命名不一致)
  - ❌ `BPMN-TASK-1` (3 桁ゼロ埋めなし)
- [ ] EPIC は `<Process>_<Role>_<Action>` 形式 (FEAT と混在禁止) と理解
  - 例: `Process_A`, `Task_A_Send`, `Flow_A_001`

## D. Tecnos override 3 大原則 (`bpmn/rules/bpmn_generator_rules.md` §24)

- [ ] **MUST-DO #13**: participant shape は `isHorizontal="false"` で書く (縦型 swimlane 強制)
  - ❌ `isHorizontal="true"` を書くと incident #2 の再発 (2026-05-08)
- [ ] sequenceFlow は top-to-bottom (waypoint y 増加) が主流 (左右の cross-lane は許容)
- [ ] Process / userTask / serviceTask / 条件付き gateway / 条件付き sequenceFlow に `<bpmn:documentation>` (第 2 正本)
  - basic_design.bpmn_descriptions と完全一致

## E. Validator 使用方針

- [ ] 自作 Python script を作らない (incident #6: agent が即興で「BPMN MUST-DO 14 を検証する Python」を書いて false PASS を返した)
- [ ] `python3 ${CLAUDE_PLUGIN_ROOT}/bpmn/validators/bpmn_lint.py --feat specs/<feature>/process.bpmn` を実行
- [ ] エラー 0 まで自動修正 (最大 5 回、3-Strike Protocol で停止して人間相談)
- [ ] (オプション) `python3 ${CLAUDE_PLUGIN_ROOT}/bpmn/scripts/render_ascii_preview.py <path>` で縦型 layout を視覚確認

## F. basic_design.md 連動

- [ ] `basic_design.md` の `bpmn_descriptions.elements[].bpmn_id` を process.bpmn の id と完全一致させる
- [ ] `python3 ${CLAUDE_PLUGIN_ROOT}/bpmn/validators/bd_bpmn_sync.py basic_design.md process.bpmn` で sync 確認 (PASS まで)

## G. Validator PASS の意味

- [ ] `bpmn_lint.py PASS` = 機械的 14/9 MUST-DO 通過 (必要条件、十分条件ではない)
- [ ] `bd_bpmn_sync.py PASS` = basic_design ↔ process.bpmn の id 一致
- [ ] `render_ascii_preview.py` 出力 = layout 視覚確認 (縦型 vs 横型を一目で判別可能)
- [ ] **3 段階全 PASS した後にのみ user に「完成」と提示する**

---

## 提出フォーマット例

agent は `bpmn-authoring` skill 起動時、本 checklist 全 7 セクション完了後に下記フォーマットを user に submit:

```
PRE-FLIGHT CHECKLIST: PASS
A: 4/4 (refs Read)
B: 2/2 (template copy + placeholder confirmed) [or 3/3 if EPIC]
C: 2/2 (FEAT/EPIC ID conventions understood)
D: 3/3 (Tecnos override applied: vertical / top-to-bottom / documentation)
E: 3/3 (canonical bpmn_lint.py used、自作禁止遵守、自動修正完了)
F: 2/2 (planned, after generation: bpmn_descriptions sync + bd_bpmn_sync.py PASS)
G: 4/4 (validator PASS の限界理解、3 段階確認済)
```

`*/*` のいずれかが未完了なら artefact 生成不可。
all green でない状態で BPMN を生成 → user submit したら **STRUCTURAL GUARD VIOLATION** として再発予防 incident 起票対象。

---

## References

- `bpmn/rules/bpmn_quick_reference.md` — FEAT 14 / EPIC 9 MUST-DO
- `bpmn/rules/bpmn_generator_rules.md` §24 — Tecnos override 3 大原則
- `bpmn/templates/process_bpmn_template.bpmn` — FEAT canonical
- `bpmn/templates/epic_flow_template.bpmn` — EPIC canonical
- `bpmn/validators/bpmn_lint.py` — canonical lint (自作禁止)
- `bpmn/validators/bd_bpmn_sync.py` — basic_design ↔ process.bpmn sync (TASK 4)
- `bpmn/scripts/render_ascii_preview.py` — ASCII layout viewer (TASK 5)
- `docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md` — 起票元 incident
- `cowork-plugin/skills/bpmn-authoring/SKILL.md` §STEP 0 — 同等内容を skill 側にも mandate
