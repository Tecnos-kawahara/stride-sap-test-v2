# examples/ — 動作する BPMN サンプル

このフォルダには、Camunda 8 で実行可能な (or planning に使える) BPMN サンプルが含まれる。すべて `validators/bpmn_lint.py` で PASS する。

---

## ファイル一覧

### `process_bpmn_example.bpmn` — 基本 FEAT サンプル

- **題材**: 受注処理 (Order Fulfillment) ワークフロー
- **使用要素**:
  - Start Event → ServiceTask (Validate Order) → ExclusiveGateway → UserTask (Review Order) + boundary timer (2H) → ServiceTask (Process Order) → EndEvent
  - Error EndEvent (validation 失敗時)
  - Timeout EndEvent (review 期限切れ)
  - TextAnnotation
- **Camunda 8 機能**:
  - `zeebe:taskDefinition` (Service Task)
  - `zeebe:userTask` + `formDefinition` + `assignmentDefinition` + `taskSchedule`
  - `zeebe:executionListener` (audit-logger / metrics-collector)
  - `zeebe:ioMapping`
  - Boundary timer (interrupting, ISO-8601 `PT2H`)
  - `bpmn:errorEventDefinition` (named error)
- **構造**: 単一 process、collaboration なし (FEAT で laneSet も使わないシンプル構造)
- **検証**:
  ```bash
  python3 ../validators/bpmn_lint.py process_bpmn_example.bpmn
  # → PASS: 0 errors, 0 warnings (placeholder なし、documentation 完備)
  ```
- **派生元**: `sdd-templates/examples/process_bpmn_example.bpmn`

### `process_bpmn_advanced_example.bpmn` — Advanced FEAT サンプル

- **題材**: 申請承認の高度なフロー (Advanced Approval Process)
- **使用要素 (advanced)**:
  - Validation ServiceTask + 結果判定 ExclusiveGateway
  - UserTask + 4H Boundary Timer + Escalation ServiceTask
  - 外部 API ServiceTask (with `zeebe:ioMapping` 入出力)
  - **Business Rule Task** (`zeebe:calledDecision` で DMN ディシジョン呼び出し)
  - **Call Activity** (`zeebe:calledElement` で再利用 sub-process 呼び出し)
  - **Error End Event** (validation 不合格時、named error reference)
- **Camunda 8 機能**:
  - すべての §5 系 task type を網羅
  - timer boundary (PT4H) + escalation pattern
  - DMN integration
  - process orchestration (call activity)
- **構造**: 単一 process、collaboration なし
- **検証**:
  ```bash
  python3 ../validators/bpmn_lint.py process_bpmn_advanced_example.bpmn
  ```
- **派生元**: `sdd-templates/examples/process_bpmn_advanced_example.bpmn`

---

## 検証

すべての example は CI / 手動で検証可能:

```bash
cd bpmn/examples
python3 ../validators/bpmn_lint.py process_bpmn_example.bpmn
python3 ../validators/bpmn_lint.py process_bpmn_advanced_example.bpmn
```

両方とも `PASS: 0 errors` が期待結果。

---

## EPIC サンプルがない理由

EPIC (epic_flow.bpmn) のサンプルは現状このパッケージには含まない (Tecnos-STRIDE 本体では `epics/EPIC-SAMPLE/epic_flow.bpmn` がある)。EPIC のテンプレートからの作成方法は `templates/epic_flow_template.bpmn` を参照のこと。EPIC サンプルが必要な場合は、Tecnos-STRIDE 本体の `epics/EPIC-SAMPLE/` を参考にできる。

---

## サンプル拡張の指針

新しい example を追加する場合:

1. `validators/bpmn_lint.py` で PASS することを確認
2. Tecnos override (BPMN-* ID, vertical layout, documentation, etc.) を踏襲
3. 顧客固有名詞 (実在の顧客名・人名・社内システム名) を含めない (この pack は配布前提)
4. `examples/README.md` (このファイル) に追記

---

> Tecnos-STRIDE BPMN Authoring Pack v1.0.0 — examples/README.md
