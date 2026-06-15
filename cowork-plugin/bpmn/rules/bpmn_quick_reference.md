---
artifact: "reference"
doc_id: "REF-BPMN-QR-001"
title: "BPMN Quick Reference — AI literal-follow checklist"
version: "5.4.0-tecnos-stride"
status: "active"
last_updated: "2026-05-07"
audience: ["AI (Claude Code / Opus 4.7)", "Developer"]
scope: "FEAT process.bpmn + EPIC epic_flow.bpmn 作成時の 1-page checklist"
references:
  # In standalone bpmn/ package (this file is at bpmn/rules/):
  - "./bpmn_generator_rules.md (Tecnos 適用ルール全仕様、§24 Tecnos override 含む)"
  - "../spec/camunda_bpmn_dictionary_complete.md (OMG BPMN 2.0 + Camunda 8.9 全要素辞書、深堀り用)"
  - "./camunda_bpmn_practice_guide.md (Standard / Advanced / Deferred 実装ガイド)"
  - "../validators/bpmn_lint.py (機械検証 CLI、stdlib のみ)"
  # In Tecnos-STRIDE host repo (when integrated, optional):
  - "agent_docs/sdd_bootstrap.md §4-BPMN (Tecnos-STRIDE Phase Gate 規範)"
---

# BPMN Quick Reference

**目的:** Opus 4.7 が BPMN ファイルを literal に（確実に）ルール通り作成できるよう、1-page に圧縮したチェックリスト。
**全仕様が必要な場合のみ** `sdd-templates/policies/bpmn_generator_rules.md` を参照すること。

---

## 🚦 決定ツリー

```
BPMN ファイルを作るか？
├── FEAT の仕様実行フロー → process.bpmn
│     → sdd-templates/templates/process_bpmn_template.bpmn をコピー
│     → ID スキーム: BPMN-TASK-001, BPMN-FLOW-001, BPMN-GW-001, BPMN-EVT-001
│     → isExecutable="true" (必須)
│     → Zeebe 拡張フル使用 (serviceTask は taskDefinition 必須)
│
└── EPIC の overview フロー → epic_flow.bpmn
      → sdd-templates/templates/epic_flow_template.bpmn をコピー
      → ID スキーム: Process_A, Task_A_Send, Flow_A_001, Start_A
      → collaboration + participant 2+ 必須
      → isExecutable は任意 (overview/planning 用)
      → Zeebe 拡張は最小限 (実行用ではない)
```

**❌ 混ぜ禁止:** FEAT で `Task_A_Send` を使う、EPIC で `BPMN-TASK-001` を使う — これは "AI の怠惰" で起きる典型エラー。

---

## ✅ FEAT process.bpmn MUST-DO (14項目)

| # | 項目 | lint エラーコード（違反時） |
|---|------|---------------------------|
| 1 | `xmlns:zeebe`, `xmlns:modeler`, `xmlns:xsi`, `xmlns:bpmn`, `xmlns:bpmndi` を宣言 | `BPMN_VALIDATION_FAILED` |
| 2 | `modeler:executionPlatform="Camunda Cloud"` + `executionPlatformVersion="8.8.x"` | `BPMN_VALIDATION_FAILED` |
| 3 | `<bpmn:process id="..." isExecutable="true">` | `BPMN_VALIDATION_FAILED` |
| 4 | 全 flow node に `<bpmn:incoming>` / `<bpmn:outgoing>` (StartEvent は outgoing のみ、EndEvent は incoming のみ) | `BPMN_VALIDATION_FAILED` |
| 5 | `<bpmn:serviceTask>` は `<zeebe:taskDefinition type="...">` を持つ | `BPMN_VALIDATION_FAILED` |
| 6 | `<bpmn:exclusiveGateway>` (2+ outgoing) は `default="<flow-id>"` または全 outgoing flow に `<bpmn:conditionExpression>` | `BPMN_VALIDATION_FAILED` |
| 7 | `<bpmn:conditionExpression>` は `xsi:type="bpmn:tFormalExpression"` 付き、`=` で開始する FEEL、空禁止 | `BPMN_VALIDATION_FAILED` |
| 8 | `<bpmn:sequenceFlow sourceRef="..." targetRef="...">` の参照先 ID が実在する | `BPMN_VALIDATION_FAILED` |
| 9 | `<bpmn:boundaryEvent attachedToRef="...">` は必須、非 compensation は outgoing も必須 | `BPMN_VALIDATION_FAILED` |
| 10 | `<bpmn:timeDuration>` は ISO-8601 (`PT1H` / `P1D` / `P1DT2H`) | `BPMN_VALIDATION_FAILED` |
| 11 | `<bpmndi:BPMNDiagram>` → `<bpmndi:BPMNPlane>` を持つ | `BPMN_VALIDATION_FAILED` |
| 12 | 全 flow node に `<bpmndi:BPMNShape>`、全 sequenceFlow に `<bpmndi:BPMNEdge>` | `BPMN_VALIDATION_FAILED` |
| 13 | participant shape は `isHorizontal="false"` (vertical swimlane 強制) | `BPMN_VALIDATION_FAILED` |
| 14 | process / userTask / serviceTask / 条件付き gateway / 条件付き sequenceFlow に `<bpmn:documentation>` | `BPMN_DOCUMENTATION_MISSING` (warning) |

---

## ✅ EPIC epic_flow.bpmn MUST-DO (9項目)

| # | 項目 | lint エラーコード（違反時） |
|---|------|---------------------------|
| 1 | `<bpmn:collaboration>` を必ず持つ | `EPIC_BPMN_INVALID` |
| 2 | `<bpmn:participant>` が 2+ | `EPIC_BPMN_INVALID` |
| 3 | 各 participant に `processRef="<process-id>"`、対応する `<bpmn:process>` が存在 | `EPIC_BPMN_INVALID` |
| 4 | 各 `<bpmn:process>` 内の flow node に `<bpmn:incoming>` / `<bpmn:outgoing>` | `EPIC_BPMN_INVALID` |
| 5 | 各 `<bpmn:sequenceFlow>` の sourceRef/targetRef が process 内に実在 | `EPIC_BPMN_INVALID` |
| 6 | `<bpmn:messageFlow>` の sourceRef/targetRef は participant 間の task を指す | — |
| 7 | BPMNPlane `bpmnElement` は collaboration id を指す | `EPIC_BPMN_INVALID` (warning) |
| 8 | 各 participant shape は `isHorizontal="false"` (vertical swimlane) | `EPIC_BPMN_INVALID` |
| 9 | 全 flow node に BPMNShape、全 sequenceFlow/messageFlow に BPMNEdge | `EPIC_BPMN_INVALID` |

**documentation 推奨:** collaboration, participant, messageFlow に `<bpmn:documentation>` (warning: `EPIC_BPMN_DOCUMENTATION_MISSING`)。

---

## ✅ プレースホルダ置換 (stride init 後、手動確認)

| プレースホルダ | 置換先 | 対象ファイル |
|--------------|--------|-------------|
| `BPMN-PROC-XXX` | `BPMN-PROC-<FEATID>` | process.bpmn |
| `EPIC-XXX` | `EPIC-<ID>` | epic_flow.bpmn |
| `XXX_feature_name` | `<feature>` (targetNamespace) | process.bpmn |
| `{{プロセス名}}`, `{{分岐条件名}}`, `{{条件式}}` 等 | 業務内容で置換 | 全 BPMN |

未置換は `BPMN_PLACEHOLDER_PRESENT` warning。

---

## ✅ basic_design.md ↔ process.bpmn 連動

`basic_design.md` の `bpmn_descriptions` セクションと `process.bpmn` 内の実 ID は**完全一致**させる:

```yaml
# basic_design.md
bpmn_descriptions:
  process:
    process_id: "BPMN-PROC-FEAT001"   # ← process.bpmn の <bpmn:process id="..."> と一致
  elements:
    - bpmn_id: "BPMN-TASK-001"        # ← process.bpmn の <bpmn:userTask id="..."> と一致
      name: "注文受付"
      type: "userTask"
      ...
```

EPIC の場合は `epic_design.md` の `epic_flow_descriptions.message_flows[].flow_id` と `epic_flow.bpmn` の `<bpmn:messageFlow id="..."/>` を一致させる。

---

## 🔁 トップ失敗パターン（AI が迷いやすい箇所）

1. **conditionExpression の xsi:type 忘れ**
   ❌ `<bpmn:conditionExpression>=amount > 100</bpmn:conditionExpression>`
   ✅ `<bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=amount > 100</bpmn:conditionExpression>`

2. **XOR で default も conditionExpression も書かない**
   ❌ 2つ以上の outgoing に両方なし
   ✅ `<bpmn:exclusiveGateway ... default="Flow_Invalid">` + 他 outgoing flow に conditionExpression

3. **BPMNShape / BPMNEdge の省略**
   ❌ `<bpmndi:BPMNPlane>` が空 or flow node 一部のみ
   ✅ 全 flow node に BPMNShape（`<dc:Bounds>` 付き）、全 sequenceFlow に BPMNEdge（`<di:waypoint>` 2個以上）

4. **sourceRef / targetRef のタイポ**
   ❌ `<bpmn:sequenceFlow sourceRef="Task1" targetRef="Task2" />` （実 ID は `Task_1`）
   ✅ 実 ID を正確に記述

5. **participant shape の isHorizontal="true" or 未指定**
   ❌ `<bpmndi:BPMNShape id="..." bpmnElement="Participant_A">`
   ✅ `<bpmndi:BPMNShape id="..." bpmnElement="Participant_A" isHorizontal="false">`

6. **FEAT で isExecutable 忘れ**
   ❌ `<bpmn:process id="...">`
   ✅ `<bpmn:process id="..." isExecutable="true">`

7. **FEAT と EPIC の ID スキーム混在**
   ❌ process.bpmn に `Task_A_Send` を書く、epic_flow.bpmn に `BPMN-TASK-001` を書く
   ✅ FEAT = `BPMN-*`, EPIC = `<Name>_<Role>` を厳守

---

## 🛠️ 検証フロー

### Standalone bpmn/ package (推奨、stdlib のみ依存)

```bash
# 1. bpmn_lint.py で auto-detect 検証 (FEAT/EPIC 自動判定)
python3 ../validators/bpmn_lint.py path/to/your-file.bpmn

# 2. モード強制
python3 ../validators/bpmn_lint.py --feat path/to/process.bpmn
python3 ../validators/bpmn_lint.py --epic path/to/epic_flow.bpmn

# 3. JSON 出力 (CI 統合用)
python3 ../validators/bpmn_lint.py --json path/to/your-file.bpmn

# 4. エラー 0 になるまで修正
```

### Tecnos-STRIDE 統合環境 (フル SDD ガバナンス)

```bash
# Tecnos-STRIDE 本体に統合する場合は stride lint が同等以上の検証を行う
sdd-templates/bin/stride lint specs/<feature>/
python3 sdd-templates/tools/epic_validator.py epics/<EPIC>/
# Phase Gate 承認フローと結合 (Gate 2: BPMN 承認等)
```

### lint エラーコード早見表

| コード | 対象 | 意味 |
|-------|------|------|
| `BPMN_VALIDATION_FAILED` | FEAT | process.bpmn が上記 14 MUST のいずれかに違反 |
| `BPMN_PLACEHOLDER_PRESENT` | FEAT | `{{...}}` or `BPMN-PROC-XXX` が未置換 (warning) |
| `BPMN_DOCUMENTATION_MISSING` | FEAT | `<bpmn:documentation>` 未記入 (warning) |
| `BPMN_VERSION_NOTICE` | FEAT | `executionPlatformVersion` が 8.8/8.9 推奨と異なる (warning) |
| `EPIC_BPMN_INVALID` | EPIC | epic_flow.bpmn が上記 9 MUST のいずれかに違反 |
| `EPIC_BPMN_PLACEHOLDER` | EPIC | `EPIC-XXX` 未置換 (warning) |
| `EPIC_BPMN_DOCUMENTATION_MISSING` | EPIC | `<bpmn:documentation>` 未記入 (warning) |

---

## 📚 深堀り参照（必要時のみ）

> Paths assume the **standalone `bpmn/` package** layout (this file lives at `bpmn/rules/`). For the Tecnos-STRIDE host repo, equivalents live at `sdd-templates/policies/`, `docs/`, `manual/` etc. — see [`../PORTABILITY.md`](../PORTABILITY.md).

| トピック | 参照先 (standalone bpmn/ package) |
|---------|------------------------------------|
| 全 BPMN 要素の XML スニペット (24 セクション、Tecnos override 含む) | `./bpmn_generator_rules.md` |
| OMG BPMN 2.0 + Camunda 8.9 全要素辞書 (深堀り、2744 行) | `../spec/camunda_bpmn_dictionary_complete.md` |
| OMG 実行セマンティクス (token / lifecycle / gateway 動作) | `./bpmn_generator_rules.md §21` |
| Connection Rules (要素間接続の正式ルール) | `./bpmn_generator_rules.md §22` |
| BPMN Coverage (Camunda 8 サポート要素一覧) | `./bpmn_generator_rules.md §23` |
| Modeling Best Practices + Tecnos override | `./bpmn_generator_rules.md §24` |
| Agentic orchestration / AI Agent connector | `./bpmn_generator_rules.md §19` |
| Camunda 8.8/8.9 実践パターン (Standard / Advanced / Deferred) | `./camunda_bpmn_practice_guide.md` |
| 機械検証 CLI (FEAT 14 / EPIC 9 MUST-DO) | `../validators/bpmn_lint.py` |
| FEAT/EPIC 開始テンプレート | `../templates/process_bpmn_template.bpmn` / `../templates/epic_flow_template.bpmn` |
| 動作する BPMN サンプル | `../examples/process_bpmn_example.bpmn` / `../examples/process_bpmn_advanced_example.bpmn` |
| 移植判断ガイド (Tecnos override 詳細) | `../PORTABILITY.md` |

---

> **Remember:** BPMN は「ゼロから書く」ものではない。**template をコピー → placeholder 置換 → ノード増減** の順で作る。
> Opus 4.7 は literal-follow が最も得意 — この 1-page を毎回参照すれば失敗しない。
