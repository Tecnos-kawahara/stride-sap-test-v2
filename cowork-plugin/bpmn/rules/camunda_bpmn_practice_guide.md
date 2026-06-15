# Camunda 8.8 BPMN 実践ガイド

> SDD テンプレートにおける Camunda 8.8 活用の実践ガイドです。
> 基本的な BPMN 作成は `manual/10_bpmn_guide.md` を参照してください。

---

## 1. 採用レベルの区別

| レベル | 対象 | 位置づけ |
|--------|------|----------|
| **Standard（デフォルト）** | Start/End, ServiceTask, Managed User Task, XOR Gateway | `stride init` で生成される基本形 |
| **Advanced（任意導入）** | Timer Boundary, BusinessRuleTask, CallActivity, ioMapping, Play/test scenario files, Ad-hoc SubProcess | 別サンプル・別ガイドで段階導入 |
| **Research / Deferred** | `candidateGroups` 中心の承認キュー設計, `fromAi()`, MCP Client connector, Vector DB / AI Agent connector | 現時点では標準化しない |

`stride init` はデフォルトで Standard テンプレートを生成します。Advanced パターンが必要な場合は、`sdd-templates/examples/process_bpmn_advanced_example.bpmn` を参考にしてください。

---

## 2. 標準パターン集

### 2.1 Managed User Task 承認パターン

Camunda 8.8 の Managed User Task を使う標準パターンです。Tecnos-STRIDE では、まず `assignee` ベースまたは明示的な運用設計を前提にしてください。

```xml
<bpmn:userTask id="BPMN-TASK-010" name="承認レビュー">
  <bpmn:incoming>FLOW-IN</bpmn:incoming>
  <bpmn:outgoing>FLOW-OUT</bpmn:outgoing>
  <bpmn:extensionElements>
    <zeebe:userTask />
    <zeebe:formDefinition formId="approval-form" />
    <zeebe:assignmentDefinition assignee="=approverEmail" />
    <zeebe:taskSchedule dueDate="=now() + duration(&quot;PT4H&quot;)" />
    <zeebe:priorityDefinition priority="50" />
  </bpmn:extensionElements>
</bpmn:userTask>
```

**要素の説明:**

| 要素 | 目的 | 必須 |
|------|------|------|
| `zeebe:userTask` | Managed User Task を有効化 | 必須 |
| `zeebe:formDefinition` | フォーム ID を指定（Camunda Forms） | 推奨 |
| `zeebe:assignmentDefinition` | 担当者や割当方針を指定 | 推奨 |
| `zeebe:taskSchedule` | 期限設定（FEEL式） | 任意 |
| `zeebe:priorityDefinition` | 優先度設定 | 任意 |

**運用上の注意:**
- `candidateUsers` / `candidateGroups` は XML 上は表現できますが、Tasklist V2 の標準運用では「これだけで承認キューが成立する」とはみなさないでください。
- グループベースの可視性や割当を採用する場合は、authorization 設計、Tasklist の利用形態、運用フローを別途定義してください。
- Standard テンプレートや標準ガイドでは、`candidateGroups` を中心に据えた承認パターンは採用しません。

### 2.2 タイマー付き承認パターン

承認期限を設け、タイムアウト時にエスカレーション処理を行うパターンです。

```xml
<bpmn:userTask id="BPMN-TASK-020" name="部長承認">
  <bpmn:incoming>FLOW-IN</bpmn:incoming>
  <bpmn:outgoing>FLOW-OUT</bpmn:outgoing>
  <bpmn:extensionElements>
    <zeebe:userTask />
    <zeebe:formDefinition formId="approval-form" />
    <zeebe:assignmentDefinition assignee="=managerEmail" />
    <zeebe:taskSchedule dueDate="=now() + duration(&quot;PT2H&quot;)" />
  </bpmn:extensionElements>
</bpmn:userTask>

<bpmn:boundaryEvent id="BPMN-EVT-020" name="承認期限(2H)"
    attachedToRef="BPMN-TASK-020" cancelActivity="true">
  <bpmn:outgoing>FLOW-TIMEOUT</bpmn:outgoing>
  <bpmn:timerEventDefinition>
    <bpmn:timeDuration>PT2H</bpmn:timeDuration>
  </bpmn:timerEventDefinition>
</bpmn:boundaryEvent>
```

**設計指針:**
- `cancelActivity="true"`: タイムアウトで承認タスクを中断し、エスカレーションへ進める
- `cancelActivity="false"`: リマインダー送信など、タスクを継続したまま通知する
- overdue / reminder は `taskSchedule.dueDate` と boundary timer を組み合わせて設計する

### 2.3 外部 API 呼び出しパターン

`zeebe:ioMapping` で入出力を明示する標準パターンです。

```xml
<bpmn:serviceTask id="BPMN-TASK-030" name="ERP在庫照会">
  <bpmn:incoming>FLOW-IN</bpmn:incoming>
  <bpmn:outgoing>FLOW-OUT</bpmn:outgoing>
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="erp-stock-query" retries="3" />
    <zeebe:ioMapping>
      <zeebe:input source="=productCode" target="itemCode" />
      <zeebe:input source="=requestQuantity" target="quantity" />
      <zeebe:output source="=stockResult.available" target="availableStock" />
      <zeebe:output source="=stockResult.warehouse" target="warehouseId" />
    </zeebe:ioMapping>
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

**REST Connector** を使う場合:

```xml
<zeebe:taskDefinition type="io.camunda:http-json:1" retries="3" />
```

### 2.4 Call Activity（再利用プロセス）

```xml
<bpmn:callActivity id="BPMN-TASK-040" name="通知プロセス">
  <bpmn:incoming>FLOW-IN</bpmn:incoming>
  <bpmn:outgoing>FLOW-OUT</bpmn:outgoing>
  <bpmn:extensionElements>
    <zeebe:calledElement processId="notification-process"
        propagateAllChildVariables="false" />
  </bpmn:extensionElements>
</bpmn:callActivity>
```

### 2.5 Business Rule Task（DMN 呼び出し）

```xml
<bpmn:businessRuleTask id="BPMN-TASK-050" name="承認ルーティング判定">
  <bpmn:incoming>FLOW-IN</bpmn:incoming>
  <bpmn:outgoing>FLOW-OUT</bpmn:outgoing>
  <bpmn:extensionElements>
    <zeebe:calledDecision decisionId="approval-routing"
        resultVariable="routingResult" />
  </bpmn:extensionElements>
</bpmn:businessRuleTask>
```

---

## 3. Web Modeler の使い分け

### 3.1 Task Testing / Play / FEEL Playground

| 機能 | 主用途 | 位置づけ |
|------|--------|----------|
| **Task Testing** | 個別タスクの入力・出力・mapping の確認 | 実装中の局所検証 |
| **Play** | プロセス全体または一部フローの検証 | 高度な動作確認 |
| **FEEL Playground** | 条件式や FEEL 式の確認 | 式の事前検証 |

**推奨順序:**
1. FEEL Playground で条件式を確認する
2. Task Testing で個別タスクの mapping を確認する
3. 必要な場合だけ Play でフロー全体を確認する

### 3.2 Play / Test Scenario Files の扱い

Web Modeler の Play は、BPMN の `processId` に紐づく **JSON 形式の test scenario files** を使います。これは Tecnos-STRIDE の `tests/scenarios.yaml` とは別資産です。

| 資産 | 形式 | 役割 |
|------|------|------|
| Web Modeler test scenario files | JSON | Play 用の低コード検証シナリオ |
| `tests/scenarios.yaml` | YAML | Tecnos-STRIDE の完了確認・E2E検証チェックリスト |

**重要:**
- 現在のリポジトリには、Web Modeler の test scenario files と `tests/scenarios.yaml` を同期・変換する仕組みはありません。
- したがって、`tests/scenarios.yaml` をそのまま Play に流用できる前提では設計しないでください。
- 両方を使う場合は、`tests/scenarios.yaml` を STRIDE 側の検証チェックリスト、Play の scenario files を Web Modeler 側の補助検証資産として分けて扱ってください。

### 3.3 FEEL Playground

条件式は FEEL Playground で事前検証してから BPMN に埋め込むことを推奨します。

```feel
=orderAmount >= 1000000 and orderAmount < 5000000
```

---

## 4. Element Templates

### 4.1 利用方針

Element Templates は、繰り返し使うタスク構成を標準化するための仕組みです。Tecnos-STRIDE では **文書化と利用方針の整理まで** を対象にし、生成機構そのものはまだ実装しません。

**SDD での方針:**
- 承認タスク、ERP 連携タスク、監査ログ記録などを再利用可能なテンプレート候補として整理する
- Template JSON の自動生成はしない
- Web Modeler / Desktop Modeler の実運用導入は別タスクで扱う

### 4.2 推奨テンプレート候補

| テンプレート名 | 用途 | 主要プロパティ |
|---------------|------|---------------|
| SDD承認タスク | Gate 承認 | `formId`, `assignee`, `dueDate`, `priority` |
| ERP在庫引当 | mcframe連携 | `taskDefinition.type`, `ioMapping` |
| 監査ログ記録 | コンプライアンス | `taskDefinition.type`, `retries` |
| REST API呼び出し | 外部連携 | connector type, method, mapping |

**補足:**
- `candidateGroups` ベースのテンプレートは、Tasklist V2 と authorization 設計を明確化するまでは標準候補にしません。
- Web Modeler では 1 ファイル 1 テンプレート前提の運用を基本にしてください。

---

## 5. API / SDK の位置づけ

### 5.1 TypeScript SDK / Orchestration Cluster API

これらは **BPMN 作成後のアプリ統合レイヤ** で使うものです。

| ツール | 用途 | BPMN作成時に必要か |
|--------|------|-------------------|
| Camunda TypeScript SDK | Worker 実装、API 呼び出し | いいえ |
| Orchestration Cluster API | プロセスデプロイ、インスタンス管理 | いいえ |
| Zeebe gRPC API | Worker 登録、ジョブ完了 | いいえ |

### 5.2 非推奨 API

| API | ステータス | 方針 |
|-----|------------|------|
| Tasklist REST API (V1) | Deprecated | 新規依存しない |
| Operate REST API (V1) | Deprecated | 新規依存しない |
| 旧 REST API (V1) | Deprecated | 新規依存しない |

新規プロジェクトでは **Camunda 8 API V2** を前提にしてください。

---

## 6. Conditional Advanced

> この章は optional advanced です。デフォルト雛形や標準 lint 基準には含めません。

### 6.1 Ad-hoc SubProcess の基本例

Camunda 8.8 の ad-hoc sub-process は有効ですが、通常の業務フローより理解コストが高いため、標準テンプレートには入れません。必要な案件だけで採用してください。

```xml
<bpmn:adHocSubProcess id="AdHoc_Review" name="レビュー活動">
  <bpmn:incoming>FLOW-IN</bpmn:incoming>
  <bpmn:outgoing>FLOW-OUT</bpmn:outgoing>
  <bpmn:extensionElements>
    <zeebe:adHoc activeElementsCollection="=activeElements" />
  </bpmn:extensionElements>

  <bpmn:serviceTask id="Task_TechReview" name="技術レビュー">
    <bpmn:extensionElements>
      <zeebe:taskDefinition type="technical-review" />
    </bpmn:extensionElements>
  </bpmn:serviceTask>

  <bpmn:serviceTask id="Task_BizReview" name="業務レビュー">
    <bpmn:extensionElements>
      <zeebe:taskDefinition type="business-review" />
    </bpmn:extensionElements>
  </bpmn:serviceTask>

  <bpmn:completionCondition xsi:type="bpmn:tFormalExpression">=reviewComplete</bpmn:completionCondition>
</bpmn:adHocSubProcess>
```

**注意:**
- ad-hoc 内には通常の start / end event を置かない
- `completionCondition` を書く場合は FEEL formal expression で記述する
- inner activity の制御や active element の扱いを理解してから導入する

### 6.2 Research / Deferred 扱いにするもの

次の機能は、Camunda 8.8 で存在していても、Tecnos-STRIDE の標準ガイドにはまだ取り込みません。

- job-worker-controlled ad-hoc sub-process の標準化
  - 実装する場合は、公式 docs と `sdd-templates/policies/bpmn_generator_rules.md` の `zeebe:taskDefinition` ベース例に従う
- `fromAi()`
  - experimental 機能として扱い、標準サンプルには入れない
- MCP Client connector
  - early-access かつ custom connector runtime 前提のため、標準導入対象にしない
- Vector DB / AI Agent connector
  - 現時点では研究枠とし、標準ガイドには入れない

**導入方針:**
- これらを採用する場合は、別タスクで PoC、運用条件、対応ランタイム、SaaS / Self-Managed の差分を明示した上で検討してください。
- `optional advanced` と `今すぐ推奨` を混同しないでください。

---

## 7. Advanced Example

**Standalone bpmn/ package**: `../examples/process_bpmn_advanced_example.bpmn`
**Tecnos-STRIDE host repo**: `sdd-templates/examples/process_bpmn_advanced_example.bpmn`

次の advanced 例が含まれます:

- 承認 User Task
- Timer Boundary Event
- `ioMapping` を使った ServiceTask
- Business Rule Task
- Call Activity
- Error End Event

このサンプルは **default テンプレートではなく、任意導入の参考例** として扱ってください。`python3 ../validators/bpmn_lint.py ../examples/process_bpmn_advanced_example.bpmn` で動作検証できます (期待結果: PASS 0 errors / 0 warnings)。

---

## 8. EPIC BPMN vs FEAT BPMN の使い分け

Tecnos-STRIDE では、BPMN を 2 種類に分けて使います (Tecnos override — 詳細は `../PORTABILITY.md`)。

| 種別 | 標準配置 (Tecnos-STRIDE 統合) | 目的 | 検証 (standalone bpmn/) |
|------|----------------------------|------|------------------------|
| **FEAT BPMN** | `specs/<feature>/process.bpmn` | 単一 feature の実装フロー (executable) | `python3 ../validators/bpmn_lint.py --feat path/to/file.bpmn` |
| **EPIC BPMN** | `epics/<EPIC>/epic_flow.bpmn` | チーム間・システム間の連携 overview | `python3 ../validators/bpmn_lint.py --epic path/to/file.bpmn` |

**EPIC BPMN の特徴:**
- `bpmn:collaboration` + `bpmn:participant`（pool）を使い、複数チーム/システムの関係を表現
- 実行用 BPMN ではなく planning / architecture 用
- `zeebe:taskDefinition` 等の Zeebe 実行拡張は不要
- 内部タスクは generic task / sendTask / receiveTask で overview に適した表現を使う
- pool は縦型表示（`isHorizontal="false"`）を推奨
- participant 間は `messageFlow` で連携を表現

**生成方法:**
```bash
# Standalone bpmn/ package: テンプレートをコピー
cp ../templates/epic_flow_template.bpmn /path/to/your-project/epic_flow.bpmn
# placeholder ({{Participant A Name}} 等) を置換し、participant を実態に合わせて拡張

# Tecnos-STRIDE host repo: stride epic コマンド (統合運用時のみ)
stride epic init EPIC-ORDER  # → epics/EPIC-ORDER/epic_flow.bpmn が生成
```

**検証:**
```bash
# Standalone bpmn/ package
python3 ../validators/bpmn_lint.py --epic path/to/your-project/epic_flow.bpmn
# auto-detect でも判定可能 (collaboration + 2+ participant で EPIC 判定)

# Tecnos-STRIDE host repo
python3 sdd-templates/tools/epic_validator.py validate epics/EPIC-ORDER/
```

**サンプル:**
- Standalone bpmn/ package: `../templates/epic_flow_template.bpmn` を雛形として参照 (placeholder 残)
- Tecnos-STRIDE host repo: `epics/EPIC-SAMPLE/epic_flow.bpmn` (実際の埋まったサンプル)

---

> Camunda 8.8/8.9 BPMN Practice Guide for SDD Templates / Standalone bpmn/ package
> 詳細な要素仕様は `../spec/camunda_bpmn_dictionary_complete.md` (OMG + Camunda 8.9 全要素辞書) 参照
