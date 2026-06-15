# CHANGELOG — BPMN 2.0 Authoring Pack

このフォルダのバージョン履歴。`bpmn/` 配下のすべてのファイルが対象。

---

## v1.1.0 — 2026-05-08

### Added (2026-05-08 BPMN vertical-flow violation incident hardening)

- **`validators/bpmn_lint.py` v1.0.0 → v1.1.0** — 4 件の機能追加:
  - `BPMN_ID_FORMAT_VIOLATION` エラーコード新設 — `^BPMN-(TASK|GW|EVT|FLOW)-\d{3}$` regex で element id を検証 (memory/constitution.md §id_conventions 準拠)。
  - `BPMN_ID_NON_TECNOS_SCHEME` 警告コード新設 — Camunda Modeler default ID (e.g., `Activity_xxx`) には warning のみ (backward compat)。
  - `--legacy-id` フラグ — `BPMN_TASK_01_xxx` 形式の旧 id を `BPMN_ID_FORMAT_LEGACY` warning に格下げ (transition flag、次 major で削除予定)。
  - `--diff-against-template <PATH>` フラグ — ターゲットファイルと canonical template の unified diff を出力 (template-copy 省略検出)。
  - 全エラーに `fix_hint` + `refs` フィールド追加 (構造化 JSON 出力でも参照可)。
- **`validators/bd_bpmn_sync.py` v1.0.0** 新規 — `basic_design.md.bpmn_descriptions.elements[].bpmn_id` ↔ `process.bpmn` 内 id の双方向 sync 検証。stdlib のみ、PyYAML 不要 (regex で bpmn_id 抽出)。`--include-flows` フラグで sequenceFlow id まで sync 確認可。
- **`scripts/render_ascii_preview.py` v1.0.0** 新規 — BPMNDI 座標から ASCII グリッド (lanes + elements) を render、vertical/horizontal orientation を視覚確認可能。Camunda Modeler 不要。`--width` / `--json` フラグ。
- **`PRE_FLIGHT_CHECKLIST.md`** 新規 — agent が BPMN 生成前に literal 確認する 7 セクション 1-page checklist (A 参照ファイル / B template-copy / C ID 命名 / D Tecnos override / E validator / F basic_design 連動 / G validator PASS の意味)。

### Changed

- `validators/bpmn_lint.py` の `LintResult.add_error` / `add_warning` に `fix_hint` + `refs` parameter を追加 (既存呼出は引き続き動作、後方互換維持)。

### Incident Reference

- **2026-05-08 BPMN vertical-flow violation** (`docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md`)。
  simple-bi PoC で `bpmn-authoring` skill が auto-fire され SKILL.md 本文を Read せず合成開始、
  結果として 7 件の canonical 違反が発生 (template-copy 欠如 / `isHorizontal=true` / `BPMN_TASK_01_xxx` 命名 /
  XOR Gateway `default` 欠如 / basic_design.bpmn_descriptions 未 populate / 自作 validator 偽陽性 /
  SKILL.md 未読)。本 v1.1.0 はこれら 7 件のうち BPMN Pack 側で検出可能なものに structural guard を提供。

### Backward Compatibility

- 既存 canonical template (`process_bpmn_template.bpmn` / `epic_flow_template.bpmn`) は v1.1.0 でも PASS (0 errors)。
- 既存 canonical example (`process_bpmn_example.bpmn` Camunda Modeler default ID 使用) は **`BPMN_ID_NON_TECNOS_SCHEME` warning** に格下げで PASS (errors=0)。新規ファイルは canonical 規約 (`BPMN-FLOW-001` 形式) の利用を推奨。

---

## v1.0.0 — 2026-05-07

### Added
- 初回リリース。Tecnos-STRIDE v5.4.0 から派生した独立パッケージ。
- `rules/bpmn_generator_rules.md` (Camunda 8 適用ルール全仕様、24 セクション、§21 OMG 実行セマンティクス + §22 Connection Rules + §23 BPMN Coverage + §24 Tecnos override 含む)
- `rules/bpmn_quick_reference.md` (FEAT 14 / EPIC 9 MUST-DO の 1-page checklist)
- `rules/camunda_bpmn_practice_guide.md` (Standard / Advanced / Deferred 区分の実装パターン)
- `spec/camunda_bpmn_dictionary_complete.md` (OMG BPMN 2.0 + Camunda 8.9 全要素辞書、2744 行)
- `templates/process_bpmn_template.bpmn` (FEAT 用、BPMN-* ID 命名 / vertical layout / pool 構造)
- `templates/epic_flow_template.bpmn` (EPIC 用、collaboration + 2 participant + messageFlow 雛形)
- `examples/process_bpmn_example.bpmn` (basic FEAT サンプル: 受注処理、validation + user task + boundary timer + DMN)
- `examples/process_bpmn_advanced_example.bpmn` (advanced FEAT サンプル: error end + call activity + business rule task)
- `validators/bpmn_lint.py` (stdlib のみ、FEAT 14 + EPIC 9 MUST-DO 検証 CLI、auto-detect FEAT vs EPIC)
- `README.md` / `PORTABILITY.md` (採用判断と移植ガイド) / `CHANGELOG.md` / `VERSION`

### Spec baseline
- Camunda 8 (Zeebe 8.8 runtime / 8.9 spec aligned)
- BPMN 2.0 (OMG 公式仕様、2011-01)

### Tecnos override 同梱内容
- 縦型 (top-to-bottom) layout
- Pool/Lane 強制 (`isHorizontal="false"`)
- BPMN-PROC-XXX / BPMN-TASK-NNN / BPMN-GW-NNN / BPMN-EVT-NNN / BPMN-FLOW-NNN ID スキーム (FEAT)
- Process_A / Task_A_Send / Flow_A_001 / MsgFlow_AtoB ID スキーム (EPIC)
- `bpmn:documentation` 第2正本ルール
- 14 MUST-DO (FEAT) + 9 MUST-DO (EPIC) 機械検証

→ 詳細は [PORTABILITY.md](PORTABILITY.md) 参照。

### Origin
派生元: Tecnos-STRIDE v5.4.0
- `sdd-templates/policies/bpmn_generator_rules.md` (v5.4.0)
- `sdd-templates/tools/stride_lint.py` (validate_bpmn 関数を抽出)
- `sdd-templates/tools/epic_validator.py` (validate_epic_bpmn 関数を抽出)
- `docs/camunda_bpmn_dictionary_complete.md` / `bpmn_quick_reference.md` / `camunda_bpmn_practice_guide.md`

---
