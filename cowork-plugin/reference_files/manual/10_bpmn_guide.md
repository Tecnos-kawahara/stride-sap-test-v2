# 10. BPMNガイド - 業務フロー（process.bpmn / epic_flow.bpmn）の作成方法

**所要時間**: 約30分

---

## このガイドで学ぶこと

1. BPMNとは何か
2. FEAT BPMN と EPIC BPMN の使い分け
3. Camunda 8 / Zeebe 8.8 の要件
4. BPMN要素の使い方
5. 重要なルール（incoming/outgoing、縦型レイアウト）
6. documentation と textAnnotation の使い分け
7. basic_design.md / epic_design.md との連動
8. サンプルBPMNの解説

---

**FEAT サンプル**: `specs/FEAT-ERPSAMPLE/process.bpmn`（受注管理プロセス）
**EPIC サンプル**: `epics/EPIC-SAMPLE/epic_flow.bpmn`（営業部門 + mcframe基幹の連携概観）
**Advanced サンプル**: `sdd-templates/examples/process_bpmn_advanced_example.bpmn`
**実践ガイド**: `docs/camunda_bpmn_practice_guide.md`
**Tecnos 適用ルール全仕様**: `sdd-templates/policies/bpmn_generator_rules.md`（§24 で OMG/Camunda 推奨と Tecnos override の対比）
**OMG + Camunda 8.9 全要素辞書**: `docs/camunda_bpmn_dictionary_complete.md`（深堀り用、2744 行）

### FEAT と EPIC の使い分け

| 種別 | ファイル | 生成コマンド | 目的 | 検証 |
|------|---------|-------------|------|------|
| **FEAT** | `specs/<feature>/process.bpmn` | `stride init <feature>` | 単一 Feature の executable フロー | `stride_lint.py` |
| **EPIC** | `epics/<EPIC>/epic_flow.bpmn` | `stride epic init <EPIC>` | チーム間連携の overview | `epic_validator.py` |

- **FEAT**: Zeebe 実行拡張（`taskDefinition`, `userTask`, `formDefinition`, `assignmentDefinition` 等）を使う executable BPMN。ルート構造は **2 形式とも許容**:
  - 単一 `process` + `laneSet`（lane で actor 区分する場合の最小形）
  - `collaboration` + 1 `participant` + 1 `process`（pool で actor 区分する場合 — テンプレ `process_bpmn_template.bpmn` および sample `specs/FEAT-ERPSAMPLE/process.bpmn` はこちらの形式を採用）
- **EPIC**: 標準は `collaboration` + 複数 `participant(pool)`。Zeebe 拡張は不要で、`messageFlow` でチーム間・システム間の受け渡しを表現
- **共通**: 業務記述の第1正本は Canonical YAML、第2正本は `bpmn:documentation`。`bpmn:textAnnotation` は補足用途のみ
- **縦レイアウト**: FEAT はレーンまたは pool を上から下に並べる。pool/participant shape には **`isHorizontal="false"`** を設定する（FEAT/EPIC 共通、`stride lint` が機械検証）

## 1. BPMNとは何か

### 定義

**BPMN（Business Process Model and Notation）** は、業務プロセスを視覚的に表現するための標準記法です。

### SDDにおける役割

```text
FEAT: basic_design.md → process.bpmn → spec.md
EPIC: epic_design.md  → epic_flow.bpmn → feature_breakdown.md
```

- **目的**: 業務フローを共通言語で可視化する
- **承認**: 人間が必ずレビューし承認する（HITL）
- **正本**:
  - 業務記述の正本は Canonical YAML
  - BPMN はレビュー・承認対象の図面兼機械可読な第2正本となる

---

## 初心者向け: 最小構成（これだけ作ればOK）

`stride init <feature>` で FEAT 用 `process.bpmn` が自動生成されます。現行標準は laneSet ベースです。

```xml
<bpmn:process id="BPMN-PROC-001" name="Web-EDI受注受付" isExecutable="true">
  <bpmn:documentation>受注受付の最小フロー</bpmn:documentation>
  <bpmn:laneSet id="LaneSet_1">
    <bpmn:lane id="Lane_Business" name="営業部門">
      <bpmn:flowNodeRef>BPMN-EVT-001</bpmn:flowNodeRef>
      <bpmn:flowNodeRef>BPMN-TASK-001</bpmn:flowNodeRef>
    </bpmn:lane>
    <bpmn:lane id="Lane_System" name="基幹システム">
      <bpmn:flowNodeRef>BPMN-EVT-002</bpmn:flowNodeRef>
    </bpmn:lane>
  </bpmn:laneSet>

  <bpmn:startEvent id="BPMN-EVT-001" name="受注受信">
    <bpmn:outgoing>BPMN-FLOW-001</bpmn:outgoing>
  </bpmn:startEvent>

  <bpmn:serviceTask id="BPMN-TASK-001" name="受注登録">
    <bpmn:documentation>目的: 受注データをDBに登録する</bpmn:documentation>
    <bpmn:incoming>BPMN-FLOW-001</bpmn:incoming>
    <bpmn:outgoing>BPMN-FLOW-002</bpmn:outgoing>
    <bpmn:extensionElements>
      <zeebe:taskDefinition type="register-order"/>
    </bpmn:extensionElements>
  </bpmn:serviceTask>

  <bpmn:endEvent id="BPMN-EVT-002" name="受付完了">
    <bpmn:incoming>BPMN-FLOW-002</bpmn:incoming>
  </bpmn:endEvent>
</bpmn:process>
```

**重要**:
- FEAT 標準では `collaboration` / `participant` は必須ではありません
- laneSet を使う場合も BPMNDI 上で各 `lane` / `task` / `flow` に対応する Shape / Edge を持たせます
- cross-team / cross-system の受け渡しを表現したい場合は、FEAT に無理に pool を入れず、EPIC の `epic_flow.bpmn` に切り出します

---

## 2. Camunda 8 / Zeebe 8.8 の要件

### 2.1 名前空間

```xml
<!-- FEAT の例 -->
<bpmn:definitions
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
  xmlns:modeler="http://camunda.org/schema/modeler/1.0"
  modeler:executionPlatform="Camunda Cloud"
  modeler:executionPlatformVersion="8.8.0">
```

> **補足**: `xmlns:zeebe` は FEAT の executable BPMN では必須です。EPIC の `epic_flow.bpmn` は overview 用なので、`zeebe` 名前空間は不要です。

### 2.2 必須属性

| 属性 | 値 | 適用 | 説明 |
|------|-----|------|------|
| `xmlns:zeebe` | `http://camunda.org/schema/zeebe/1.0` | FEAT | Zeebe名前空間 |
| `xmlns:modeler` | `http://camunda.org/schema/modeler/1.0` | FEAT / EPIC | Modeler名前空間 |
| `modeler:executionPlatform` | `Camunda Cloud` | FEAT 必須 / EPIC 推奨 | 実行プラットフォーム |
| `modeler:executionPlatformVersion` | `8.8.*` | FEAT 必須 / EPIC 推奨 | バージョン（8.8で始まる） |

### 2.3 必須の構造

```xml
<!-- FEAT: executable process -->
<bpmn:process id="BPMN-PROC-XXX" name="プロセス名" isExecutable="true">
  <bpmn:documentation>プロセスの業務説明</bpmn:documentation>
  <bpmn:laneSet id="LaneSet_1">
    <bpmn:lane id="Lane_1" name="担当部門"/>
  </bpmn:laneSet>
  <!-- flow elements -->
</bpmn:process>

<!-- EPIC: overview collaboration -->
<bpmn:collaboration id="Collaboration_EPIC-XXX">
  <bpmn:documentation>Epic overview</bpmn:documentation>
  <bpmn:participant id="Participant_A" name="営業部門" processRef="Process_A" />
  <bpmn:participant id="Participant_B" name="基幹システム" processRef="Process_B" />
</bpmn:collaboration>
```

- FEAT では `isExecutable="true"` が必須
- FEAT の標準構造は `process` + `laneSet`
- EPIC では `collaboration` + `participant(pool)` が必須
- `bpmn:documentation` で業務説明を記載する

### 2.4 縦型レイアウト（必須）

DI セクションでは、FEAT はレーンを縦に積み、EPIC は participant の `isHorizontal="false"` を必ず設定して上から下に流します。

```xml
<!-- FEAT: lane shape -->
<bpmndi:BPMNShape id="Lane_Business_di" bpmnElement="Lane_Business">
  <dc:Bounds x="100" y="80" width="700" height="180" />
</bpmndi:BPMNShape>

<!-- EPIC: participant shape -->
<bpmndi:BPMNShape id="Participant_di" bpmnElement="Participant_XXX" isHorizontal="false">
  <dc:Bounds x="80" y="80" width="300" height="780" />
</bpmndi:BPMNShape>
```

> **注意**:
> - EPIC では `isHorizontal="true"` や属性なしの場合、`epic_validator.py` が error を出します
> - FEAT でも participant を使う構成にした場合は、同じく縦向きが必要です
> - FEAT 標準は laneSet なので、participant は必須ではありません

### 2.5 作成手順（初心者向け）

1. `stride init <feature>` で `process.bpmn` を自動生成（推奨）
2. cross-team / cross-system の概観が必要なら `stride epic init <EPIC>` で `epic_flow.bpmn` を生成
3. **Camunda Modeler** で開き、FEAT は laneSet、EPIC は participant(pool) を縦配置する
4. **ID命名規則** に従って `BPMN-*` / `Participant_*` / `MsgFlow_*` を付与
5. 各要素に `bpmn:documentation` で業務説明を記載する
6. FEAT は `basic_design.md` の `bpmn_descriptions`、EPIC は `epic_design.md` の `epic_flow_descriptions` と ID を合わせる
7. FEAT は `stride lint`、EPIC は `stride epic validate` で検証する

---

## 3. BPMN要素の使い方

### 3.1 イベント（Events）

#### 開始イベント（Start Event）

```xml
<bpmn:startEvent id="StartEvent_1" name="発注受信">
  <bpmn:outgoing>Flow_001</bpmn:outgoing>
</bpmn:startEvent>
```

#### 終了イベント（End Event）

```xml
<bpmn:endEvent id="EndEvent_1" name="受注受付完了">
  <bpmn:incoming>Flow_010</bpmn:incoming>
</bpmn:endEvent>
```

#### タイマーイベント（Timer Event）

```xml
<bpmn:intermediateCatchEvent id="Timer_Wait" name="5分待機">
  <bpmn:incoming>Flow_005</bpmn:incoming>
  <bpmn:outgoing>Flow_006</bpmn:outgoing>
  <bpmn:timerEventDefinition id="TimerDef_1">
    <bpmn:timeDuration>PT5M</bpmn:timeDuration>
  </bpmn:timerEventDefinition>
</bpmn:intermediateCatchEvent>
```

### 3.2 タスク（Tasks）

#### サービスタスク（Service Task）- 最重要

```xml
<bpmn:serviceTask id="BPMN-TASK-001" name="受注登録">
  <bpmn:incoming>Flow_001</bpmn:incoming>
  <bpmn:outgoing>Flow_002</bpmn:outgoing>
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="register-order" retries="3"/>
    <zeebe:ioMapping>
      <zeebe:input source="=orderPayload" target="orderPayload"/>
      <zeebe:output source="=orderNumber" target="orderNumber"/>
    </zeebe:ioMapping>
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

**必須要素**:
- `<bpmn:incoming>` - 入力フロー
- `<bpmn:outgoing>` - 出力フロー
- `<zeebe:taskDefinition type="...">` - タスク定義

#### ユーザータスク（User Task）

```xml
<bpmn:userTask id="UserTask_Approval" name="受注内容承認">
  <bpmn:incoming>Flow_003</bpmn:incoming>
  <bpmn:outgoing>Flow_004</bpmn:outgoing>
  <bpmn:extensionElements>
    <zeebe:assignmentDefinition assignee="=approverEmail" />
    <zeebe:formDefinition formId="approval-form"/>
  </bpmn:extensionElements>
</bpmn:userTask>
```

### 3.3 ゲートウェイ（Gateways）

#### 排他ゲートウェイ（Exclusive Gateway / XOR）

```xml
<!-- 分岐 -->
<bpmn:exclusiveGateway id="Gateway_Decision" name="受注承認結果" default="Flow_Rejected">
  <bpmn:incoming>Flow_004</bpmn:incoming>
  <bpmn:outgoing>Flow_Approved</bpmn:outgoing>
  <bpmn:outgoing>Flow_Rejected</bpmn:outgoing>
</bpmn:exclusiveGateway>

<!-- 条件付きフロー -->
<bpmn:sequenceFlow id="Flow_Approved" sourceRef="Gateway_Decision" targetRef="Task_Execute">
  <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=approved = true</bpmn:conditionExpression>
</bpmn:sequenceFlow>

<!-- デフォルトフロー（条件なし） -->
<bpmn:sequenceFlow id="Flow_Rejected" sourceRef="Gateway_Decision" targetRef="EndEvent_Rejected"/>
```

**ポイント**:
- `default` 属性でデフォルトフローを指定
- 条件付きフローには `<bpmn:conditionExpression>` を設定
- FEEL式（`=approved = true`）を使用

#### 並列ゲートウェイ（Parallel Gateway / AND）

```xml
<!-- 分岐（全パス並列実行） -->
<bpmn:parallelGateway id="Gateway_Split">
  <bpmn:incoming>Flow_001</bpmn:incoming>
  <bpmn:outgoing>Flow_A</bpmn:outgoing>
  <bpmn:outgoing>Flow_B</bpmn:outgoing>
</bpmn:parallelGateway>

<!-- 合流（全パス待ち合わせ） -->
<bpmn:parallelGateway id="Gateway_Join">
  <bpmn:incoming>Flow_A_End</bpmn:incoming>
  <bpmn:incoming>Flow_B_End</bpmn:incoming>
  <bpmn:outgoing>Flow_002</bpmn:outgoing>
</bpmn:parallelGateway>
```

#### 包含ゲートウェイ（Inclusive Gateway / OR）

```xml
<bpmn:inclusiveGateway id="Gateway_Options">
  <bpmn:incoming>Flow_001</bpmn:incoming>
  <bpmn:outgoing>Flow_Email</bpmn:outgoing>
  <bpmn:outgoing>Flow_SMS</bpmn:outgoing>
  <bpmn:outgoing>Flow_Push</bpmn:outgoing>
</bpmn:inclusiveGateway>
```

### 3.4 境界イベント（Boundary Events）

```xml
<!-- タスクにアタッチ -->
<bpmn:boundaryEvent id="Timeout_Event" name="タイムアウト" attachedToRef="BPMN-TASK-001">
  <bpmn:outgoing>Flow_Timeout</bpmn:outgoing>
  <bpmn:timerEventDefinition>
    <bpmn:timeDuration>PT30S</bpmn:timeDuration>
  </bpmn:timerEventDefinition>
</bpmn:boundaryEvent>
```

**必須**: `attachedToRef` で親タスクを参照

---

## 4. 重要なルール（incoming/outgoing）

### 最重要ルール

**原則として、全ての FlowNode（Task/Event/Gateway）は `<bpmn:incoming>` と `<bpmn:outgoing>` を持つ必要があります。**

```xml
<!-- ✅ 正しい -->
<bpmn:serviceTask id="Task_1" name="タスク1">
  <bpmn:incoming>Flow_001</bpmn:incoming>  <!-- 必須 -->
  <bpmn:outgoing>Flow_002</bpmn:outgoing>  <!-- 必須 -->
</bpmn:serviceTask>

<!-- ❌ 間違い（Zeebeデプロイエラー） -->
<bpmn:serviceTask id="Task_1" name="タスク1">
  <!-- incoming/outgoing がない -->
</bpmn:serviceTask>
```

### 例外

| 要素 | incoming | outgoing |
|------|----------|----------|
| StartEvent | 不要 | 必須 |
| EndEvent | 必須 | 不要 |
| Event SubProcess（`triggeredByEvent="true"`） | 不要 | 不要 |
| Compensation Handler（`isForCompensation="true"`） | 不要 | 不要 |
| その他 | 必須 | 必須 |

### シーケンスフローとの対応

```xml
<!-- フロー定義 -->
<bpmn:sequenceFlow id="Flow_001" sourceRef="StartEvent_1" targetRef="Task_1"/>
<bpmn:sequenceFlow id="Flow_002" sourceRef="Task_1" targetRef="EndEvent_1"/>

<!-- 要素の参照 -->
<bpmn:startEvent id="StartEvent_1">
  <bpmn:outgoing>Flow_001</bpmn:outgoing>  <!-- Flow_001を参照 -->
</bpmn:startEvent>

<bpmn:serviceTask id="Task_1">
  <bpmn:incoming>Flow_001</bpmn:incoming>  <!-- Flow_001を参照 -->
  <bpmn:outgoing>Flow_002</bpmn:outgoing>  <!-- Flow_002を参照 -->
</bpmn:serviceTask>

<bpmn:endEvent id="EndEvent_1">
  <bpmn:incoming>Flow_002</bpmn:incoming>  <!-- Flow_002を参照 -->
</bpmn:endEvent>
```

---

## 5. BPMN DI（ダイアグラム情報）

### 必須のDI構造

```xml
<!-- FEAT -->
<bpmndi:BPMNDiagram id="BPMNDiagram_1">
  <bpmndi:BPMNPlane id="BPMNPlane_FEAT" bpmnElement="BPMN-PROC-XXX">
    <!-- lane / flow node / sequence flow の位置・サイズ -->
  </bpmndi:BPMNPlane>
</bpmndi:BPMNDiagram>

<!-- EPIC -->
<bpmndi:BPMNDiagram id="BPMNDiagram_2">
  <bpmndi:BPMNPlane id="BPMNPlane_EPIC" bpmnElement="Collaboration_EPIC-XXX">
    <!-- 各要素の位置・サイズ -->
  </bpmndi:BPMNPlane>
</bpmndi:BPMNDiagram>
```

- FEAT の `BPMNPlane` は `process` を参照
- EPIC の `BPMNPlane` は `collaboration` を参照

### 標準サイズ

| 要素 | 幅 x 高さ |
|------|-----------|
| Task | 100 x 80 |
| Gateway | 50 x 50 |
| StartEvent | 36 x 36 |
| EndEvent | 36 x 36 |
| IntermediateEvent | 36 x 36 |
| BoundaryEvent | 36 x 36 |
| SubProcess | 最小 200 x 150 |

### DI記述例

```xml
<bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">
  <dc:Bounds x="152" y="102" width="36" height="36"/>
</bpmndi:BPMNShape>

<bpmndi:BPMNShape id="Task_1_di" bpmnElement="Task_1">
  <dc:Bounds x="250" y="80" width="100" height="80"/>
</bpmndi:BPMNShape>

<bpmndi:BPMNEdge id="Flow_001_di" bpmnElement="Flow_001">
  <di:waypoint x="188" y="120"/>
  <di:waypoint x="250" y="120"/>
</bpmndi:BPMNEdge>
```

---

## 6. Camunda 8 コネクタ

### REST Connector

```xml
<bpmn:serviceTask id="RestCall" name="API呼び出し">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="io.camunda:http-json:1"/>
    <zeebe:ioMapping>
      <zeebe:input source="=&quot;GET&quot;" target="method"/>
      <zeebe:input source="=&quot;https://api.example.com/data&quot;" target="url"/>
      <zeebe:output source="=response.body" target="result"/>
    </zeebe:ioMapping>
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

### Slack Connector

```xml
<zeebe:taskDefinition type="io.camunda:slack:1"/>
```

### Kafka Producer

```xml
<zeebe:taskDefinition type="io.camunda:kafka:1"/>
```

---

## 7. 補償パターン（Saga Pattern）

### 補償イベントの定義

```xml
<!-- 補償境界イベント -->
<bpmn:boundaryEvent id="Compensate_Boundary" attachedToRef="Task_Create">
  <bpmn:compensateEventDefinition/>
</bpmn:boundaryEvent>

<!-- 補償ハンドラ -->
<bpmn:serviceTask id="Compensate_Handler" name="取消処理" isForCompensation="true">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="compensate-create"/>
  </bpmn:extensionElements>
</bpmn:serviceTask>

<!-- 関連付け -->
<bpmn:association id="Assoc_1" sourceRef="Compensate_Boundary" targetRef="Compensate_Handler"/>
```

---

## 8. documentation と textAnnotation の使い分け

### 8.1 正本の優先順位

| 順位 | 方法 | 用途 |
|------|------|------|
| 第1正本 | `basic_design.md` / `epic_design.md` の Canonical YAML | 業務記述の SSoT |
| 第2正本 | `bpmn:documentation` | BPMN 要素に紐づく業務説明 |
| 補足表示 | `bpmn:textAnnotation` | 図上で目立たせたい補足情報 |
| 非正本 | XML コメント | 補助メモ（正本にしない） |

### 8.2 `bpmn:documentation` の標準記載項目

| 要素 | 記載内容 |
|------|---------|
| `process` | 目的、開始条件、完了条件、正本参照 |
| `userTask` / `serviceTask` | 目的、入力、出力、関連AC、関連Contract |
| `exclusiveGateway`（分岐あり） | 判定の業務意味、デフォルトフローの意味 |
| 条件付き `sequenceFlow` | 業務条件、条件式の業務意味 |

### 8.3 `bpmn:textAnnotation` の用途

全要素に付けるのではなく、**図上で目立たせたい補足** に限定します。

**FEAT で使う場面:**
- 金額閾値（例: 承認閾値 100万/500万円）
- タイムアウト時の扱い
- 補償や運用上の注意

**EPIC で使う場面:**
- SLA / latency
- blocking dependency
- 重要な契約ID
- スコープ外の注記

### 8.4 basic_design.md との連動

- `basic_design.md` の `bpmn_descriptions` セクションが BPMN 要素の業務記述正本
- `traceability_rows` は AC / Contract / Test の正本（業務記述とは別管理）
- `process.bpmn` を更新したら `basic_design.md` の `bpmn_descriptions` も同期する
- EPIC の `epic_flow.bpmn` は `epic_design.md` の `epic_flow_descriptions` と同期する

---

## 9. ID命名規則

| 要素 | パターン | 例 |
|------|----------|-----|
| Process | `BPMN-PROC-XXX` | BPMN-PROC-001 |
| Task | `BPMN-TASK-NNN` | BPMN-TASK-001 |
| Gateway | `BPMN-GW-NNN` | BPMN-GW-001 |
| Event | `BPMN-EVT-NNN` | BPMN-EVT-001 |
| Flow | `BPMN-FLOW-NNN` | BPMN-FLOW-001 |

---

## 10. 検証チェックリスト

### stride-lint でのBPMN検証

**FEAT `process.bpmn` の主なチェック:**

1. **ファイル/Parse** — XMLとしてparse可能、ルート要素が `definitions`
2. **名前空間** — `xmlns:zeebe`、`xmlns:modeler` が存在
3. **実行プラットフォーム** — `modeler:executionPlatform="Camunda Cloud"`、`executionPlatformVersion` が `8.x`（8.8推奨）
4. **プロセス** — `isExecutable="true"`
5. **DI** — `BPMNDiagram` / `BPMNPlane` がプロセスを参照
6. **サービスタスク** — `zeebe:taskDefinition/@type` が存在
7. **XORゲートウェイ** — `default` または全フローに `conditionExpression`
8. **タイマー** — `timeDuration` が ISO-8601 形式
9. **FlowNode incoming/outgoing** — 全FlowNodeが `<incoming>/<outgoing>` を持つ（StartEvent は outgoing のみ、EndEvent は incoming のみ）
10. **conditionExpression** — 空値禁止、`xsi:type="bpmn:tFormalExpression"` を推奨
11. **BPMNShape 完全性** — 全 flow node に対応する `BPMNShape` が存在
12. **BPMNEdge 完全性** — 全 sequence flow に対応する `BPMNEdge` が存在
13. **boundaryEvent** — `attachedToRef` が必須、`outgoing` が必須
14. **participant を使う場合** — participant shape は `isHorizontal="false"`
15. **description alignment** — `basic_design.md` の `bpmn_descriptions` / `traceability_rows` と ID が整合

> **補足**: 補償 boundary event は association で補償ハンドラへ接続するため、通常の boundary event と違って `<outgoing>` 必須チェックの例外です。

### `epic_validator.py` による EPIC `epic_flow.bpmn` チェック

1. `epic_flow.bpmn` の存在（未作成は warning）
2. XML parse / `definitions` / `collaboration`
3. participant が 2 件以上
4. 各 participant の `processRef` が既存 process を指す
5. `BPMNPlane` が `collaboration` を参照
6. participant shape の `isHorizontal="false"`
7. messageFlow に `BPMNEdge`
8. collaboration / participant / messageFlow の `documentation`
9. `epic_flow_descriptions` との ID 整合
10. `overview.purpose` と collaboration documentation の presence check

---

## 11. サンプルBPMN

完全なサンプルは `sdd-templates/examples/process_bpmn_example.bpmn` を参照してください。

---

## チェックリスト

- [ ] 名前空間（bpmn, bpmndi, dc, di, xsi, zeebe, modeler）を設定した
- [ ] `modeler:executionPlatform="Camunda Cloud"` / `executionPlatformVersion="8.8.0"` を設定した
- [ ] FEAT では `isExecutable="true"` を設定した
- [ ] 全FlowNodeに `<incoming>/<outgoing>` を設定した（StartEvent は outgoing のみ、EndEvent は incoming のみ）
- [ ] ServiceTask に `zeebe:taskDefinition type="..."` を設定した
- [ ] UserTask に `zeebe:userTask` + `formDefinition` + `assignmentDefinition` を設定した
- [ ] XORゲートウェイに `default` 属性またはすべてのフローに `conditionExpression` を設定した
- [ ] `conditionExpression` に `xsi:type="bpmn:tFormalExpression"` を付けた
- [ ] FEAT の `BPMNPlane` は `process`、EPIC の `BPMNPlane` は `collaboration` を参照した
- [ ] 全 flow node に `BPMNShape`、全 sequence flow に `BPMNEdge` を配置した
- [ ] `boundaryEvent` に `attachedToRef` を設定した（補償 boundary は `<outgoing>` 例外）
- [ ] participant / pool を使う場合は `isHorizontal="false"` にした
- [ ] FEAT は `bpmn_descriptions`、EPIC は `epic_flow_descriptions` と ID を合わせた
- [ ] ID命名規則（BPMN-PROC-*, BPMN-TASK-*, BPMN-GW-*, BPMN-EVT-*, BPMN-FLOW-*）に従った

---

## 12. Advanced パターン

基本的な BPMN 作成を習得した後、以下の拡張パターンを活用できます。

- **タイマー付き承認**: boundary timer + エスカレーション通知
- **外部API連携**: ioMapping による入出力マッピング
- **DMN 呼び出し**: businessRuleTask + calledDecision
- **再利用プロセス**: callActivity + calledElement
- **Agentic / Ad-hoc**: optional advanced（プロジェクト要件に応じて導入）

**詳細**: `docs/camunda_bpmn_practice_guide.md` を参照してください。
**サンプル**: `sdd-templates/examples/process_bpmn_advanced_example.bpmn`

---

## 次のステップ

→ [11. 仕様書ガイド](11_spec_guide.md)

---

> SDD Templates Manual - 10. BPMN Guide
