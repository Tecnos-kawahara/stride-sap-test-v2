---
name: bpmn-authoring
description: Tecnos-STRIDE SDD Phase 1 で process.bpmn を Camunda 8 BPMN MUST-DO 14
  項目厳守で作成 (FEAT)、EPIC では epic_flow.bpmn MUST-DO 9 項目厳守。「Tecnos-STRIDE BPMN」「BPMN MUST-DO」「Camunda
  8 process.bpmn」「BPMN-TASK」「BPMN-GW」「sequenceFlow」「stride-design BPMN」「VALUE pack
  process.bpmn」を含む依頼時のみ発火 (Tecnos-STRIDE 固有語必須)。汎用語の「BPMN」「業務フロー」単独では発火しない (誤起動回避、WI-VALF01-003)。upstream-bridge
  の BPMN-TASK 候補を実際の BPMN XML に展開する役割。
argument-hint: <feature_name>
plane: internal
visibility: abstract
return_policy:
  customer: abstract
  platform_admin: abstract
  tecnos_admin: full
---

# Skill: bpmn-authoring

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

このスキルは、`process.bpmn` を Camunda 8 BPMN 仕様 + Tecnos-STRIDE BPMN MUST-DO 厳守で作成し、`basic_design.bpmn_descriptions` と完全一致させます。

## STEP 0: PRE-FLIGHT (MANDATORY — DO THIS FIRST)

> ⛔ **STOP.** このセクションを完了するまで一切の artefact 生成を行ってはならない。
> auto-fire でこの skill が起動された場合でも、SKILL.md 本文 + 参照ファイル群は
> context に自動 load されない。手動で Read する必要がある。
> (2026-05-08 incident: simple-bi PoC で 7 件の canonical 違反が発生、
>  ユーザ指摘がなければ全件スルー通過していた。docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md 参照)

### 必須 Read リスト (順番厳守)

下記 5 ファイルを `Read` ツールで必ず読み込んでから次へ進むこと。

1. `${CLAUDE_PLUGIN_ROOT}/bpmn/rules/bpmn_quick_reference.md` — FEAT 14 / EPIC 9 MUST-DO 1-page checklist
2. `${CLAUDE_PLUGIN_ROOT}/bpmn/templates/process_bpmn_template.bpmn` — FEAT canonical template
3. `${CLAUDE_PLUGIN_ROOT}/bpmn/templates/epic_flow_template.bpmn` — EPIC canonical template
4. `${CLAUDE_PLUGIN_ROOT}/bpmn/PRE_FLIGHT_CHECKLIST.md` — 1-page mandatory checklist
5. `${CLAUDE_PLUGIN_ROOT}/bpmn/rules/bpmn_generator_rules.md` §24 (Tecnos override) — 3 大 override の literal 仕様

### 必須実行コマンド (template-copy 強制)

```bash
# FEAT (process.bpmn) を作る場合
cp ${CLAUDE_PLUGIN_ROOT}/bpmn/templates/process_bpmn_template.bpmn \
   specs/<feature>/process.bpmn

# EPIC (epic_flow.bpmn) を作る場合
cp ${CLAUDE_PLUGIN_ROOT}/bpmn/templates/epic_flow_template.bpmn \
   epics/<EPIC>/epic_flow.bpmn
```

⚠️ **`cp` を実行せずに `Write` ツールで BPMN を新規作成することを禁止する。**
⚠️ **自作 validator (Python script を即興で書く等) は禁止。常に `bpmn/validators/bpmn_lint.py` を使う。**

### 🚫 ANTI-PATTERN (実際に発生した違反、再発禁止)

| 違反 | 正しい行動 |
|---|---|
| ゼロから XML を Write した | template を `cp` してから placeholder 置換 |
| `isHorizontal="true"` を書いた | template の `isHorizontal="false"` を保持 (Tecnos override #13) |
| `BPMN_TASK_01_register_source` 命名 | `BPMN-TASK-001` (3 桁ゼロ埋め・ハイフン) |
| XOR Gateway に `default` 属性なし | `default` 属性 OR 全 outgoing に conditionExpression |
| `basic_design.bpmn_descriptions` を populate せず | bpmn_id と process.bpmn の id を完全一致 |
| 「BPMN MUST-DO 14 を検証する Python」を agent が書いた | `python3 ${CLAUDE_PLUGIN_ROOT}/bpmn/validators/bpmn_lint.py --feat <path>` を呼ぶ |
| validator PASS を「合格」と宣言 | canonical lint + render_ascii_preview + ユーザ視覚確認の 3 段階で初めて完成 |

### Output of STEP 0 (artefact 生成前に必ず提出)

agent は次のような output を返してから artefact 生成に着手すること:

```
[PRE-FLIGHT REPORT]
  read: bpmn_quick_reference.md (✓)
  read: process_bpmn_template.bpmn (✓)
  read: epic_flow_template.bpmn (✓)
  read: PRE_FLIGHT_CHECKLIST.md (✓)
  read: bpmn_generator_rules.md §24 (✓)
  template_copied: specs/<feature>/process.bpmn (from process_bpmn_template.bpmn)
  understood_must_do_count: 14
  validator_to_use: ${CLAUDE_PLUGIN_ROOT}/bpmn/validators/bpmn_lint.py
  ready_to_proceed: true
```

このリポートを user に提示しない、または `ready_to_proceed: false` で止まった場合は **artefact 生成を一切してはならない**。

---

## Usage

```
/stride:design <feature_name>
```

(`/stride:design` は内部で `basic-design-authoring` + `bpmn-authoring` を順次起動)

## Workflow

### 1. Understand the Input

- `basic-design-authoring` で完成済の `basic_design.md`
- `upstream-bridge` で stdout に出力された **BPMN-TASK 候補リスト** (`business_usecase.yaml` 由来)

### 2. Reference Files

> **v0.4.0 で BPMN ルール体系を `bpmn/` 単独パッケージに統合。** 1〜7 と 10 は plugin 内 `bpmn/` 配下、8 は `reference_files/` 残存、9 (validator) は `bpmn/validators/bpmn_lint.py`。

参照優先順位 (上から):
1. `bpmn/rules/bpmn_quick_reference.md` — 1-page checklist、FEAT 14 / EPIC 9 MUST-DO (毎回最初に参照)
2. `reference_files/sdd-templates/sdd_bootstrap.md` §4-BPMN — Tecnos-STRIDE Phase Gate 規範 (6 step フロー)
3. `bpmn/templates/process_bpmn_template.bpmn` — FEAT テンプレ (ゼロから書かない、コピー → placeholder 置換)
4. `bpmn/templates/epic_flow_template.bpmn` — EPIC テンプレ (同上)
5. `bpmn/rules/bpmn_generator_rules.md` — Tecnos 適用ルール全仕様 (§21 OMG セマンティクス + §22 Connection Rules + §23 BPMN Coverage + §24 Tecnos override 含む)
6. `bpmn/rules/camunda_bpmn_practice_guide.md` — Standard / Advanced / Deferred 区分の実装ガイド
7. `bpmn/spec/camunda_bpmn_dictionary_complete.md` — OMG BPMN 2.0 + Camunda 8.9 全要素辞書 (深堀り用、2744 行)
8. `reference_files/manual/10_bpmn_guide.md` — エンドユーザーガイド (顧客レビュー説明用)
9. `bpmn/validators/bpmn_lint.py` — stdlib のみ単独 lint CLI (FEAT 14 + EPIC 9 MUST-DO 機械検証、`/stride:bpmn-validate` で起動可)
10. `bpmn/PORTABILITY.md` — Tecnos override の内訳 + 移植ガイド (顧客 PoC repo に bpmn/ をコピー配布する際の判断材料)

### 3. BPMN MUST-DO (絶対厳守 — 主要 8 項目要約、完全 14 項目は `bpmn_quick_reference.md` 参照)

| 必須事項 | 内容 |
|---|---|
| **テンプレからのコピー** | `process.bpmn` はゼロから書かない、`stride init` が自動コピー (template) |
| **Process ID** | `BPMN-PROC-<FEATUREID>` (例: BPMN-PROC-VALE01)、stride init で自動置換 |
| **Element ID スキーム (FEAT)** | `BPMN-TASK-NNN`, `BPMN-GW-NNN`, `BPMN-EVT-NNN`, `BPMN-FLOW-NNN` (3 桁数字、ゼロパディング)。EPIC は `Process_A` / `Task_A_Send` / `Flow_A_001` — 混在禁止 |
| **incoming/outgoing 必須** | 全 task / event / gateway に明示 (start event は incoming なし、end event は outgoing なし) |
| **XOR ゲート** | `<bpmn:exclusiveGateway>` には必ず **`default` 属性 または 全 outgoing flow に conditionExpression** (`xsi:type="bpmn:tFormalExpression"` 必須、`=` で開始する FEEL 式) |
| **isExecutable + executionPlatform** | `<bpmn:process isExecutable="true">`、`modeler:executionPlatform="Camunda Cloud"` + `executionPlatformVersion="8.8.x"` (8.9.x も可) |
| **DI 完全性 + 縦型 swimlane** | `BPMNShape` (全 element) + `BPMNEdge` (全 sequenceFlow) を `bpmndi:BPMNDiagram` 配下に配置、participant shape は **`isHorizontal="false"` (vertical swimlane 強制、Tecnos override)** |
| **bpmn_descriptions 一致 + documentation** | `basic_design.bpmn_descriptions[].bpmn_id` と `process.bpmn` の id が **完全一致**、process / userTask / serviceTask / 条件付き gateway / 条件付き sequenceFlow に `<bpmn:documentation>` (第2正本) |

### 4. Generate Output

#### 4.1 BPMN XML 生成

`reference_files/templates/process_bpmn_template.bpmn` をベースに、以下を順次追加:

1. **collaboration / participant** (process_id 置換、name にプロセス名)
2. **process** (id, name, isExecutable=true, documentation)
3. **start event** (`BPMN-EVT-001`、name + outgoing)
4. **userTask / serviceTask** (BPMN-TASK-NNN、name + documentation + incoming + outgoing + extensionElements で `<zeebe:userTask>` または `<zeebe:taskDefinition type="...">`)
5. **exclusiveGateway** (BPMN-GW-NNN、必ず `default` 属性 + conditionExpression、documentation)
6. **end event** (BPMN-EVT-NNN、name + incoming)
7. **sequenceFlow** (BPMN-FLOW-NNN、sourceRef + targetRef、conditionExpression は XOR の場合)
8. **bpmndi:BPMNDiagram** (Participant_di + 全 Shape + 全 Edge)

#### 4.2 basic_design.bpmn_descriptions 同期

`basic_design.md` の `bpmn_descriptions` セクションに以下を populate:

```yaml
bpmn_descriptions:
  process:
    process_id: "BPMN-PROC-<FEATUREID>"
    purpose: "..."
    start_condition: "..."
    end_condition: "..."
    business_outcome: "..."
    primary_actors: [...]
  elements:
    - bpmn_id: "BPMN-EVT-001"
      name: "..."
      type: "startEvent"
      purpose: "..."
      ...
    - bpmn_id: "BPMN-TASK-001"
      name: "..."
      type: "userTask"  # or serviceTask
      purpose: "..."
      business_role: "..."
      trigger: "..."
      inputs: [...]
      outputs: [...]
      business_rules: [...]
      exceptions: [...]
    # ... gateways, end events
```

**bpmn_id は process.bpmn の id と 1:1 完全一致**。

### 5. 検証チェックリスト (必須)

- [ ] `<bpmn:process isExecutable="true">`
- [ ] 全 task/event/gateway に `<bpmn:incoming>` `<bpmn:outgoing>` (start/end は片方のみ)
- [ ] 全 XOR Gateway に `default` 属性 + conditionExpression
- [ ] 全 sequenceFlow に valid `sourceRef` + `targetRef`
- [ ] `BPMNDiagram` 配下に **全 element の Shape** + **全 sequenceFlow の Edge**
- [ ] `basic_design.bpmn_descriptions` の bpmn_id と process.bpmn の id が **完全一致**

### 6. Completion Criteria

- `process.bpmn` 完成 (上記検証チェックリスト全 OK)
- `basic_design.bpmn_descriptions` と `process.bpmn` が完全一致
- **`/stride:bpmn-validate <feature>`** で `bpmn/validators/bpmn_lint.py` 直接 lint → PASS 0 errors (warnings は許容)
- `/stride:validate <feature>` で BACCM/Phase 1 整合性 + BPMN 検証 pass
- (任意) Camunda Modeler で開いて視覚確認

### 7. 上流工程での bpmn/ パッケージ活用 (v0.4.0)

本 plugin は **`bpmn/` を first-class component として同梱**。AI agent が BPMN を作成する際:

1. **必ず最初に** `bpmn/rules/bpmn_quick_reference.md` の 14 MUST-DO を確認
2. **テンプレートをコピー** (`bpmn/templates/process_bpmn_template.bpmn` または `epic_flow_template.bpmn`)
3. **placeholder を置換** (`{{プロセス名}}`、`BPMN-PROC-XXX` 等を業務内容に)
4. **examples で構造確認** (`bpmn/examples/process_bpmn_example.bpmn` で基本パターン、`process_bpmn_advanced_example.bpmn` で advanced パターン参照)
5. **検証** (`python3 ${CLAUDE_PLUGIN_ROOT}/bpmn/validators/bpmn_lint.py path/to/file.bpmn` で 14/9 MUST-DO 機械検証、PASS まで自動修正最大 5 回)

顧客 PoC repo に bpmn ルール一式を配布したい場合は `cp -r ${CLAUDE_PLUGIN_ROOT}/bpmn /path/to/customer-repo/` で完結。`bpmn/PORTABILITY.md` で Tecnos override (縦型 / pool-lane / BPMN-* ID) の採用判断ガイドが付属。

## Attributions

- **Camunda 8 / Camunda Modeler 5.x**: BPMN 2.0 + Zeebe 拡張仕様。fair-use, spec refs only
- **Tecnos-STRIDE BPMN MUST-DO**: §4-BPMN (sdd_bootstrap.md)
