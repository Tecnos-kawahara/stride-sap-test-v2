# BPMN 2.0 & Camunda 完全辞書データ (OMG仕様 + Camunda拡張) (AIエージェント向け)

このドキュメントは、CamundaのBPMN 2.0フロー作成に関する包括的な辞書データです。Claude CodeやCodexなどのAIエージェントがCamunda BPMNモデルを理解し、生成・検証するためのリファレンスとして設計されています。

## 目次
1. [BPMNの基本概念とCamundaアーキテクチャ](#1-bpmnの基本概念とcamundaアーキテクチャ)
2. [BPMN要素リファレンス](#2-bpmn要素リファレンス)
3. [Camunda固有の拡張要素 (zeebe:*)](#3-camunda固有の拡張要素-zeebe)
4. [変数とデータフロー](#4-変数とデータフロー)
5. [モデリングのベストプラクティスと命名規則](#5-モデリングのベストプラクティスと命名規則)
6. [エラーハンドリングと例外処理パターン](#6-エラーハンドリングと例外処理パターン)

---

## 1. BPMNの基本概念とCamundaアーキテクチャ

Business Process Model and Notation (BPMN) はプロセスモデリングのグローバルスタンダードです。Camundaのワークフローエンジン（Zeebe）は、BPMNで定義されたプロセスを実行し、API、マイクロサービス、人間の作業などをオーケストレーションします。

---

## 2. BPMN要素リファレンス



### BPMN in Modeler

#### 1. ページタイトルと概要説明
**ページタイトル:** BPMN in Modeler
**概要説明:**
Business Process Model and Notation (BPMN) は、複雑なプロセスを表現するためのグラフィカルな表記法として開発されました。非営利団体であるThe Object Management Group (OMG) によって維持されており、世界中の多くの組織で採用されています。BPMNの視覚的な性質により、特にModeler内において、異なるチーム間のコラボレーションが促進されます。

#### 2. BPMN要素の定義と用途
WebおよびDesktop Modelerは、同様のコアBPMN 2.0モデリングエクスペリエンスを提供します。
- ページの左側にあるパレットからBPMN要素をドラッグし、ダイアグラムキャンバスにドロップして追加します。
- 要素をクリックしてコンテキストメニューを表示し、要素のタイプをその場で変更できます。例えば、「Change element」メニューアイコンを選択して、要素のタイプをサービスタスクやユーザータスクに変更します。

#### 3. XMLプロパティ・属性の詳細
右側のプロパティパネルで、選択した要素に適用される属性を表示および編集できます。
（※このページには具体的なXMLプロパティや属性の詳細なリストは含まれていません。詳細は各要素のドキュメントを参照する必要があります。）

#### 4. 実装に必要な設定項目
- Camunda 8内のサービスタスクでは、タスクタイプを設定し、プロセス内の特定のタスクを実行するためのジョブワーカー（job workers）を実装する必要があります。

#### 5. コード例やXML例
（※このページには具体的なコード例やXML例は含まれていません。）

#### 6. 制約事項や注意点
**注意点 (NOTE):**
- BPMNダイアグラムは、デプロイされる予定のプロセスエンジン用に作成する必要があります。現時点では、Camunda 7用にモデリングされたBPMNダイアグラムをCamunda 8で実行したり、その逆を行ったりすることはできません。

#### 7. 他の要素との関連性
- ModelerでBPMNを使用すると、タスクタイプやイベント定義など、より多くのBPMN 2.0要素を作成できます。
- モデリングツールでサポートされているBPMN要素の完全なリストについては、BPMN 2.0カバレッジドキュメントを確認してください。
- BPMNを使用したモデリングの一般的なガイドラインについては、読みやすいプロセスモデルの作成（creating readable process models）を参照してください。


---


### Send Tasks

#### 1. ページタイトルと概要説明
- **ページタイトル**: Send tasks
- **概要説明**: Send taskは、外部システム（例：Kafkaトピックやメールサーバー）へのメッセージの公開をモデル化するために使用されます。

#### 2. BPMN要素の定義と用途
- **定義**: Send taskは、外部システムへのメッセージ送信を表すBPMN要素です。
- **用途**: Kafkaトピックへのメッセージ公開やメール送信など、外部システムとの通信に使用されます。
- **動作**: Send taskはService taskと全く同じように動作します。どちらのタスクタイプもジョブとジョブワーカーに基づいています。違いは視覚的な表現（タスクマーカー）とモデルのセマンティクスのみです。プロセスインスタンスがSend taskに入ると、対応するジョブが作成され、その完了を待ちます。ジョブワーカーはこのジョブタイプのジョブを要求して処理する必要があります。ジョブが完了すると、プロセスインスタンスは続行されます。

#### 3. XMLプロパティ・属性の詳細
- **`id`**: タスクの一意の識別子（例: `publish-message`）。
- **`name`**: タスクの表示名（例: `Publish message`）。
- **`zeebe:taskDefinition`**:
  - **`type`**: ジョブワーカーがサブスクライブするジョブのタイプを指定します（例: `kafka`、`mail`）。必須。
- **`zeebe:taskHeaders`**:
  - **`zeebe:header`**: ジョブワーカーに渡す静的パラメータ。
    - **`key`**: ヘッダーのキー（例: `kafka-topic`）。
    - **`value`**: ヘッダーの値（例: `payment`）。

#### 4. 実装に必要な設定項目
- **ジョブタイプ (Job type)**: Service taskと同様に、Send taskはジョブタイプを定義する必要があります。これはワーカーがサブスクライブすべきジョブのタイプ（例：`kafka`や`mail`）を指定します。
- **タスクヘッダー (Task headers)**: ジョブワーカーに静的パラメータ（例：メッセージを公開するトピックの名前）を渡すために使用します。
- **変数マッピング (Variable mappings)**: Service taskと同様に、ジョブワーカーに渡される変数を変換したり、ジョブの変数がどのようにマージされるかをカスタマイズするために定義します。
- **ジョブワーカー (Job worker)**: Send taskのジョブはZeebe自体では処理されません。処理するためには、ジョブワーカーを提供する必要があります。

#### 5. コード例やXML例
カスタムヘッダーを持つSend taskのXML例：
```xml
<bpmn:sendTask id="publish-message" name="Publish message">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="kafka" />
    <zeebe:taskHeaders>
      <zeebe:header key="kafka-topic" value="payment" />
    </zeebe:taskHeaders>
  </bpmn:extensionElements>
</bpmn:sendTask>
```

#### 6. 制約事項や注意点
- **注意点**: Send taskのジョブはZeebe自体では処理されません。処理するためには、ジョブワーカーを提供する必要があります。

#### 7. 他の要素との関連性
- **Service tasks**: Send taskはService taskと全く同じように動作します。違いは視覚的な表現とモデルのセマンティクスのみです。
- **Job workers**: Send taskの処理にはジョブワーカーが必要です。
- **Community Extension**: Kafka Connect Zeebeというコミュニティ拡張機能があり、Kafkaトピックにメッセージを公開するジョブワーカーを提供しています。これを実行するか、独自のジョブワーカーのブループリントとして使用できます。


---


### Manual Tasks

#### 1. ページタイトルと概要説明
- **ページタイトル**: Manual tasks
- **概要説明**: マニュアルタスク（Manual task）は、人間の対話を必要とするが、外部ツールやUIインターフェースを必要としないタスクを定義します。例えば、ユーザーがドキュメントをレビューしたり、物理的なタスクを完了したりする場合です。

#### 2. BPMN要素の定義と用途
- **定義**: マニュアルタスクは、プロセスエンジン外で実行されるタスクに関する洞察を提供し、プロセスのモデリングを支援します。
- **用途**: リンクされた自動化プロセスは利用されませんが、人間の作業をプロセスモデルに明示的に含めるために使用されます。ヒューマンタスクオーケストレーション（human task orchestration）の一部ですが、ワークフローエンジンやソフトウェアアプリケーションによって支援される実行可能なタスクを定義するユーザータスク（user tasks）とは異なります。

#### 3. XMLプロパティ・属性の詳細
- `id`: (必須) タスクの一意の識別子。例: `manual-task`
- `name`: (任意) タスクの表示名。例: `Manual task`

#### 4. 実装に必要な設定項目
エンジンおよびBPMNモデル内では、マニュアルタスクはパススルー（pass-through）アクティビティとして処理され、プロセスインスタンスが到着した瞬間に自動的にプロセスが継続されます。特別な設定項目は必要ありません。

#### 5. コード例やXML例
**XML表現**:
```xml
<bpmn:manualTask id="manual-task" name="Manual task" />
```

#### 6. 制約事項や注意点
- マニュアルタスクはパススルーアクティビティとして扱われるため、プロセスエンジンはタスクの完了を待ちません。プロセスインスタンスが到達するとすぐに次のステップに進みます。
- 外部ツールやUIインターフェースとの連携はありません。

#### 7. 他の要素との関連性
- **ユーザータスク（User tasks）との違い**: ユーザータスクはワークフローエンジンやソフトウェアアプリケーションによって支援される実行可能なタスクですが、マニュアルタスクは外部ツールやUIを持たない純粋な人間の作業を表します。
- **ヒューマンタスクオーケストレーション（Human task orchestration）**: マニュアルタスクはこのオーケストレーションの一部として位置づけられます。


---


### Undefined Tasks

#### 1. ページタイトルと概要説明
- **ページタイトル**: Undefined tasks
- **概要説明**: Undefined task（抽象タスクとも呼ばれる）は、作業の種類が指定されていないタスクを定義します。これは、エンジンが認識する必要のない人物によって行われる作業や、既知のシステムやUIインターフェースが存在しない作業をモデル化するために使用されます。また、自動化されていないプロセスや、プロセス自動化の開発中にプロセスをモデル化する際にも使用されます。

#### 2. BPMN要素の定義と用途
- **定義**: 作業の種類が指定されていないタスク。
- **用途**: 
  - エンジンが認識する必要のない人物による作業のモデル化。
  - 既知のシステムやUIインターフェースが存在しない作業のモデル化。
  - 自動化されていないプロセスのモデル化。
  - プロセス自動化の開発中のモデル化。
  - プロセスエンジンの外部で実行されるタスクに関する洞察を提供するため。

#### 3. XMLプロパティ・属性の詳細
- `id`: タスクの一意の識別子（例: `undefined-task`）。
- `name`: タスクの表示名（例: `Undefined task`）。

#### 4. 実装に必要な設定項目
- Web ModelerおよびDesktop Modelerでは、プロセスにタスクを追加する際のデフォルトがUndefined taskになっています。
- タスクをクリックし、**Change element**メニューアイコンを選択することで、タスクタイプを変更できます。

#### 5. コード例やXML例
```xml
<bpmn:task id="undefined-task" name="Undefined task" />
```

#### 6. 制約事項や注意点
- エンジンにとって、Undefined taskはパススルーアクティビティとして扱われ、プロセスインスタンスが到着した瞬間に自動的にプロセスが続行されます。
- プロセスの自動化において実質的な利点はありません。

#### 7. 他の要素との関連性
- デフォルトのタスクタイプとして機能し、後からService taskやUser taskなどの他の特定のタスクタイプに変更することが想定されています。


---


### Gateways Overview

Gateways are elements that route tokens in more complex patterns than plain sequence flow.

BPMN's **exclusive gateway** chooses one sequence flow out of many based on data, whereas BPMN's **parallel gateway** generates new tokens by activating multiple sequence flows in parallel, for example.

Currently supported elements:
* Exclusive gateways
* Parallel gateways
* Event-based gateways
* Inclusive gateways

### Exclusive gateway

An exclusive gateway (or XOR-gateway) allows you to make a decision based on data (i.e. on process variables).

If an exclusive gateway has multiple outgoing sequence flows, all sequence flows except one must have a `conditionExpression` to define when the flow is taken. The gateway can have one sequence flow without `conditionExpression`, which must be defined as the default flow.

When entering an exclusive gateway, the system evaluates the `conditionExpression` of each outgoing sequence flow in the order they are defined in the BPMN XML and selects the first flow whose condition is fulfilled.

If no condition is fulfilled, it takes the **default flow** of the gateway. If the gateway has no default flow, an incident is created.

An exclusive gateway can also be used to join multiple incoming flows together and improve the readability of the BPMN. A joining gateway has a pass-through semantic and doesn't merge the incoming concurrent flows like a parallel gateway.

#### Conditions

A `conditionExpression` defines when a flow is taken. It is a boolean expression that can access the process variables and compare them with literals or other variables. The condition is fulfilled when the expression returns `true`.

Multiple boolean values or comparisons can be combined as disjunction (`or`) or conjunction (`and`).

For example:
```
= totalPrice > 100
= order.customer = "Paul"
= orderCount > 15 or totalPrice > 50
= valid and orderCount > 0
```

#### XML representation

An exclusive gateway with two outgoing sequence flows:

```xml
<bpmn:exclusiveGateway id="exclusiveGateway" default="else" />
<bpmn:sequenceFlow id="priceGreaterThan100" name="totalPrice &#62; 100"  sourceRef="exclusiveGateway" targetRef="shipParcelWithInsurance">
  <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">
    = totalPrice &gt; 100
  </bpmn:conditionExpression>
</bpmn:sequenceFlow>
<bpmn:sequenceFlow id="else" name="else"  sourceRef="exclusiveGateway" targetRef="shipParcel" />
```

### Parallel gateway

A parallel gateway (or AND-gateway) allows you to split the flow into concurrent paths.

When a parallel gateway with multiple outgoing sequence flows is entered, all flows are taken. The paths are executed concurrently and independently.

The concurrent paths can be joined using a parallel gateway with multiple incoming sequence flows. The process instance waits at the parallel gateway until each incoming sequence is taken.

**Note:** The outgoing paths of the parallel gateway are executed concurrently and not parallel in the sense of parallel threads. All records of a process instance are written to the same partition (single stream processor).

#### XML representation

A parallel gateway with two outgoing sequence flows:

```xml
<bpmn:parallelGateway id="split" />
<bpmn:sequenceFlow id="to-ship-parcel" sourceRef="split"  targetRef="shipParcel" />
<bpmn:sequenceFlow id="to-process-payment" sourceRef="split"  targetRef="processPayment" />
```

### Event-based gateway

An event-based gateway allows you to make a decision based on events.

An event-based gateway must have at least **two** outgoing sequence flows. Each sequence flow must be connected to an intermediate catch event of type timer, message or signal.

When an event-based gateway is entered, the process instance waits at the gateway until one of the events is triggered. When the first event is triggered, the outgoing sequence flow of this event is taken. No other events of the gateway can be triggered afterward.

#### XML representation

An event-based gateway with two outgoing sequence flows:

```xml
<bpmn:eventBasedGateway id="gateway" />
<bpmn:sequenceFlow id="s1" sourceRef="gateway" targetRef="payment-details-updated" />
<bpmn:intermediateCatchEvent id="payment-details-updated"  name="Payment Details Updated">
  <bpmn:messageEventDefinition messageRef="message-payment-details-updated" />
</bpmn:intermediateCatchEvent>
<bpmn:sequenceFlow id="s2" sourceRef="gateway" targetRef="wait-one-hour" />
<bpmn:intermediateCatchEvent id="wait-one-hour" name="1 hour">
  <bpmn:timerEventDefinition>
    <bpmn:timeDuration>PT1H</bpmn:timeDuration>
  </bpmn:timerEventDefinition>
</bpmn:intermediateCatchEvent>
<bpmn:intermediateCatchEvent id="payment-canceled" name="Payment canceled">
  <bpmn:signalEventDefinition signalRef="signal-payment-canceled" />
</bpmn:intermediateCatchEvent>
```

### Inclusive gateway

The inclusive gateway (or OR-gateway) allows for making multiple decisions based on data or process variables. Inclusive gateways can be diverging (a sequence flow is split into multiple paths) or converging (split paths are merged before continuing).

If an inclusive gateway has multiple outgoing sequence flows, all sequence flows must have a condition to define when the flow is taken. If the inclusive gateway only has one outgoing sequence flow, then it does not need to have a condition.

Optionally, one of the sequence flows can be marked as the default flow. This sequence flow should not have a condition, because its behavior depends on the other conditions.

When an inclusive gateway is entered, the conditions are evaluated. The process instance takes all sequence flows where the condition is fulfilled.

If no condition is fulfilled, it takes the **default flow** of the gateway. Note that the default flow is not expected to have a condition, and is therefore not evaluated. If no condition is fulfilled and the gateway has no default flow, an incident is created.

A converging inclusive gateway (also known as a merging or joining inclusive gateway) merges incoming paths before the sequence flow continues. A converging gateway is completed and merges incoming sequence flows if one of the following conditions is met:
* All incoming sequence flows have been taken at least once.
* No path exists from any active flow node to the inclusive gateway (excluding incoming paths to the inclusive gateway that have already been taken).

#### Conditions

A `conditionExpression` defines when a flow is taken. It is a boolean expression that can access the process variables and compare them with literals or other variables. The condition is fulfilled when the expression returns `true`.

Multiple boolean values or comparisons can be combined as disjunction (`and`) or conjunction (`or`).

For example:
```
= totalPrice > 100
= order.customer = "Paul"
= orderCount > 15 or totalPrice > 50
= valid and orderCount > 0
= list contains(courses, "salad")
```

#### XML representation

An inclusive gateway with three outgoing sequence flows and the default sequence flow is `Salad`:

```xml
<bpmn:inclusiveGateway id="Gateway_1dj8ts6" name="Courses selected?" default="Flow_05d0jjq">
      <bpmn:incoming>Flow_0mfam08</bpmn:incoming>
      <bpmn:outgoing>Flow_0d3xogt</bpmn:outgoing>
      <bpmn:outgoing>Flow_1le3l31</bpmn:outgoing>
      <bpmn:outgoing>Flow_05d0jjq</bpmn:outgoing>
</bpmn:inclusiveGateway>
<bpmn:sequenceFlow id="Flow_0d3xogt" name="Pasta"
    sourceRef="Gateway_1dj8ts6" targetRef="Activity_1orhxob">
    <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">
       = list contains(courses, "pasta")
    </bpmn:conditionExpression>
</bpmn:sequenceFlow>
<bpmn:sequenceFlow id="Flow_1le3l31" name="Steak"
    sourceRef="Gateway_1dj8ts6" targetRef="Activity_0rygy6z">
    <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">
      = list contains(courses, "steak")
    </bpmn:conditionExpression>
</bpmn:sequenceFlow>
<bpmn:sequenceFlow id="Flow_05d0jjq" name="Salad"
    sourceRef="Gateway_1dj8ts6" targetRef="Activity_06yrt1e" />
```


---


### Exclusive gateway

#### 概要
Exclusive gateway（またはXOR-gateway）は、データ（プロセス変数）に基づいて決定を下すことを可能にします。

#### BPMN要素の定義と用途
Exclusive gatewayは、複数の出力シーケンスフローを持つ場合、1つを除くすべてのシーケンスフローに、そのフローが選択される条件を定義する `conditionExpression` を持たせる必要があります。ゲートウェイは `conditionExpression` を持たないシーケンスフローを1つ持つことができ、これはデフォルトフローとして定義されなければなりません。

Exclusive gatewayに入ると、システムはBPMN XMLで定義された順序で各出力シーケンスフローの `conditionExpression` を評価し、条件が満たされた最初のフローを選択します。

どの条件も満たされない場合、ゲートウェイの**デフォルトフロー**が選択されます。ゲートウェイにデフォルトフローがない場合、インシデント（incident）が作成されます。

Exclusive gatewayは、複数の入力フローを結合し、BPMNの可読性を向上させるためにも使用できます。結合ゲートウェイはパススルーセマンティクスを持ち、パラレルゲートウェイのように入力される並行フローをマージしません。

#### 実装に必要な設定項目・条件 (Conditions)
`conditionExpression` は、フローが選択される条件を定義します。これはプロセス変数にアクセスし、リテラルや他の変数と比較できるブール式（boolean expression）です。式が `true` を返したときに条件が満たされます。

複数のブール値や比較は、論理和（`or`）または論理積（`and`）として組み合わせることができます。

例:
```
= totalPrice > 100
= order.customer = "Paul"
= orderCount > 15 or totalPrice > 50
= valid and orderCount > 0
```

#### コード例やXML例 (XML representation)
2つの出力シーケンスフローを持つExclusive gatewayの例:

```xml
<bpmn:exclusiveGateway id="exclusiveGateway" default="else" />
<bpmn:sequenceFlow id="priceGreaterThan100" name="totalPrice &#62; 100"  sourceRef="exclusiveGateway" targetRef="shipParcelWithInsurance">
  <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">
    = totalPrice &gt; 100
  </bpmn:conditionExpression>
</bpmn:sequenceFlow>
<bpmn:sequenceFlow id="else" name="else"  sourceRef="exclusiveGateway" targetRef="shipParcel" />
```

#### 制約事項や注意点
- 複数の出力フローがある場合、1つを除いてすべてに `conditionExpression` が必要。
- 条件が1つも満たされず、デフォルトフローも設定されていない場合はインシデントが発生する。
- 結合ゲートウェイとして使用する場合、並行フローのマージは行われない（パススルーとして機能する）。

#### 他の要素との関連性
- **プロセス変数**: 条件式で評価される。
- **インシデント (Incidents)**: 条件が満たされずデフォルトフローもない場合に発生。
- **式 (Expressions)**: `conditionExpression` の記述に使用される。
- **パラレルゲートウェイ**: 結合時の動作が異なる（パラレルはマージするが、エクスクルーシブはマージしない）。


---


### Parallel gateway

#### 概要説明
A parallel gateway (or AND-gateway) allows you to split the flow into concurrent paths.

#### BPMN要素の定義と用途
When a parallel gateway with multiple outgoing sequence flows is entered, all flows are taken. The paths are executed concurrently and independently.

The concurrent paths can be joined using a parallel gateway with multiple incoming sequence flows. The process instance waits at the parallel gateway until each incoming sequence is taken.

#### 制約事項や注意点
**NOTE**
The outgoing paths of the parallel gateway are executed concurrently and not parallel in the sense of parallel threads. All records of a process instance are written to the same partition (single stream processor).

#### コード例やXML例
A parallel gateway with two outgoing sequence flows:

```xml
<bpmn:parallelGateway id="split" />
<bpmn:sequenceFlow id="to-ship-parcel" sourceRef="split"  targetRef="shipParcel" />
<bpmn:sequenceFlow id="to-process-payment" sourceRef="split"  targetRef="processPayment" />
```

#### XMLプロパティ・属性の詳細
(Not explicitly detailed in the provided text, but the example shows `id` for `bpmn:parallelGateway` and `id`, `sourceRef`, `targetRef` for `bpmn:sequenceFlow`.)

#### 実装に必要な設定項目
(Not explicitly detailed in the provided text.)

#### 他の要素との関連性
Used with sequence flows to split or join concurrent paths.


---


### Inclusive gateway

#### 1. ページタイトルと概要説明
- **ページタイトル**: Inclusive gateway
- **概要説明**: Inclusive gateway（またはOR-gateway）は、データやプロセス変数に基づいて複数の決定を行うためのゲートウェイです。Inclusive gatewayは、分岐（シーケンスフローが複数のパスに分割される）または合流（分割されたパスが継続する前にマージされる）のいずれかになります。

#### 2. BPMN要素の定義と用途
- **分岐 (Diverging)**: Inclusive gatewayに複数の出力シーケンスフローがある場合、すべてのシーケンスフローには、そのフローがいつ実行されるかを定義する条件が必要です。出力シーケンスフローが1つしかない場合は、条件は不要です。
- **デフォルトフロー**: オプションで、シーケンスフローの1つをデフォルトフローとしてマークできます。このシーケンスフローには条件を設定しないでください。その動作は他の条件に依存するためです。
- **合流 (Converging)**: 合流するInclusive gateway（マージまたはジョインInclusive gatewayとも呼ばれます）は、シーケンスフローが継続する前に、入力パスをマージします。以下のいずれかの条件が満たされると、合流ゲートウェイは完了し、入力シーケンスフローをマージします。
  - すべての入力シーケンスフローが少なくとも1回実行された。
  - アクティブなフローノードからInclusive gatewayへのパスが存在しない（すでに実行されたInclusive gatewayへの入力パスを除く）。

#### 3. XMLプロパティ・属性の詳細
- `id`: ゲートウェイやシーケンスフローの一意の識別子（例: `Gateway_1dj8ts6`）。
- `name`: ゲートウェイやシーケンスフローの表示名（例: `Courses selected?`）。
- `default`: デフォルトフローとして使用されるシーケンスフローのID（例: `Flow_05d0jjq`）。
- `sourceRef`: シーケンスフローの開始元要素のID。
- `targetRef`: シーケンスフローのターゲット要素のID。
- `bpmn:incoming`: 入力シーケンスフローのID。
- `bpmn:outgoing`: 出力シーケンスフローのID。
- `bpmn:conditionExpression`: フローが実行される条件を定義する式。`xsi:type="bpmn:tFormalExpression"`を指定します。

#### 4. 実装に必要な設定項目
- **条件式 (conditionExpression)**: フローが実行されるタイミングを定義します。プロセス変数にアクセスし、リテラルや他の変数と比較できるブール式です。式が `true` を返すと条件が満たされます。
- 複数のブール値や比較は、論理和 (`or`) または論理積 (`and`) として組み合わせることができます。

#### 5. コード例やXML例
### 条件式の例
```feel
= totalPrice > 100
= order.customer = "Paul"
= orderCount > 15 or totalPrice > 50
= valid and orderCount > 0
= list contains(courses, "salad")
```

### XML表現の例
3つの出力シーケンスフローとデフォルトシーケンスフロー（`Salad`）を持つInclusive gatewayの例：
```xml
<bpmn:inclusiveGateway id="Gateway_1dj8ts6" name="Courses selected?" default="Flow_05d0jjq">
  <bpmn:incoming>Flow_0mfam08</bpmn:incoming>
  <bpmn:outgoing>Flow_0d3xogt</bpmn:outgoing>
  <bpmn:outgoing>Flow_1le3l31</bpmn:outgoing>
  <bpmn:outgoing>Flow_05d0jjq</bpmn:outgoing>
</bpmn:inclusiveGateway>
<bpmn:sequenceFlow id="Flow_0d3xogt" name="Pasta" sourceRef="Gateway_1dj8ts6" targetRef="Activity_1orhxob">
  <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">
    = list contains(courses, "pasta")
  </bpmn:conditionExpression>
</bpmn:sequenceFlow>
<bpmn:sequenceFlow id="Flow_1le3l31" name="Steak" sourceRef="Gateway_1dj8ts6" targetRef="Activity_0rygy6z">
  <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">
    = list contains(courses, "steak")
  </bpmn:conditionExpression>
</bpmn:sequenceFlow>
<bpmn:sequenceFlow id="Flow_05d0jjq" name="Salad" sourceRef="Gateway_1dj8ts6" targetRef="Activity_06yrt1e" />
```

#### 6. 制約事項や注意点
- Inclusive gatewayに入ると、条件が評価されます。プロセスインスタンスは、条件が満たされたすべてのシーケンスフローを実行します。
- どの条件も満たされない場合、ゲートウェイの**デフォルトフロー**が実行されます。デフォルトフローには条件がないことが想定されているため、評価されません。
- どの条件も満たされず、ゲートウェイにデフォルトフローがない場合、**インシデント (incident)** が作成されます。

#### 7. 他の要素との関連性
- **Conditions**: 条件式を使用して、どのパスを進むかを決定します。
- **Incidents**: 条件が満たされず、デフォルトフローもない場合に発生します。


---


### Event-based gateway

#### 概要説明
An event-based gateway allows you to make a decision based on events.

#### BPMN要素の定義と用途
An event-based gateway must have at least **two** outgoing sequence flows. Each sequence flow must be connected to an intermediate catch event of type timer, message or signal.

When an event-based gateway is entered, the process instance waits at the gateway until one of the events is triggered. When the first event is triggered, the outgoing sequence flow of this event is taken. No other events of the gateway can be triggered afterward.

#### XMLプロパティ・属性の詳細
- `id`: (String) The unique identifier of the gateway.
- `name`: (String, Optional) The name of the gateway.

#### 実装に必要な設定項目
- At least two outgoing sequence flows.
- Each sequence flow must connect to an intermediate catch event (timer, message, or signal).

#### コード例やXML例
```xml
<bpmn:eventBasedGateway id="gateway" />
<bpmn:sequenceFlow id="s1" sourceRef="gateway" targetRef="payment-details-updated" />
<bpmn:intermediateCatchEvent id="payment-details-updated"  name="Payment Details Updated">
  <bpmn:messageEventDefinition messageRef="message-payment-details-updated" />
</bpmn:intermediateCatchEvent>
<bpmn:sequenceFlow id="s2" sourceRef="gateway" targetRef="wait-one-hour" />
<bpmn:intermediateCatchEvent id="wait-one-hour" name="1 hour">
  <bpmn:timerEventDefinition>
    <bpmn:timeDuration>PT1H</bpmn:timeDuration>
  </bpmn:timerEventDefinition>
</bpmn:intermediateCatchEvent>
<bpmn:intermediateCatchEvent id="payment-canceled" name="Payment canceled">
  <bpmn:signalEventDefinition signalRef="signal-payment-canceled" />
</bpmn:intermediateCatchEvent>
```

#### 制約事項や注意点
- Must have at least two outgoing sequence flows.
- Outgoing sequence flows must connect to intermediate catch events (timer, message, or signal).
- No other events of the gateway can be triggered after the first event is triggered.

#### 他の要素との関連性
- Timer events
- Message events
- Signal events


---


### Overview | Camunda 8 Docs

**Events** in BPMN represent things that _happen_. A process can react to events (_catching_ event) as well as emit events (_throwing_ event). For example, a catching message event makes the token continue as soon as a message is received. The XML representation of the process contains the criteria for which kind of message triggers continuation.

Events can be added to the process in various ways. Not only can they be used to make a token wait at a certain point, but also for interrupting a token's progress.

Currently supported events:

*   None events
*   Message events
*   Timer events
*   Error events
*   Escalation events
*   Terminate events
*   Link events
*   Signal events
*   Compensation events

note

Not all the events are supported yet. For a complete overview of supported events, refer to the BPMN coverage.

Events in BPMN can be **thrown** (i.e. sent), or **caught** (i.e. received), respectively referred to as **throw** or **catch** events (e.g. `message throw event`, `timer catch event`).

Additionally, a distinction is made between start, intermediate, and end events:

*   **Start events** (catch events, as they can only react to something) are used to denote the beginning of a process or subprocess.
*   **End events** (throw events, as they indicate something has happened) are used to denote the end of a particular sequence flow.
*   **Intermediate events** can be used to indicate that something has happened (i.e. intermediate throw events), or to wait and react to certain events (i.e. intermediate catch events).

Intermediate catch events can be inserted into your process in two different contexts: normal flow, or attached to an activity, and are called boundary events.

...Send message A(intermediate throw event)Wait for msg. B(intermediate catch event)...

In a typical flow, an intermediate throw event executes its event (e.g. send a message) once the token has reached it. Once complete, the token continues to all outgoing sequence flows (1).

An intermediate catch event, however, stops the token and waits until the event it is waiting for occurs, at which point execution resumes and the token moves on (2).

Boundary events provide a way to model what should happen if an event occurs while an activity is active. For example, if a process is waiting on a user task to happen which is taking too long, an intermediate timer catch event can be attached to the task, with an outgoing sequence flow to notification task, allowing the modeler to automate and sending a reminder email to the user.

...Do something.........Do something elseEscalate task(in parallel)7 days(interrupting boundary event)every day(non interrupting boundary event)

A boundary event must be an intermediate catch event, and can be either interrupting (1)or non-interrupting (2). Interrupting means that once triggered, before taking any outgoing sequence flow the activity the event is attached to is terminated. This allows modeling timeouts where we can prune certain execution paths if something happens (e.g. the process takes too long).


---


### None events | Camunda 8 Docs

#### 1. ページタイトルと概要説明
**ページタイトル**: None events

None events（Noneイベント）は、指定されていないイベントであり、「blank（空白）」イベントとも呼ばれます。

#### 2. BPMN要素の定義と用途
Noneイベントには主に3つのタイプがあり、それぞれ異なる用途と定義を持っています。

**None start events (None開始イベント)**は、プロセスインスタンスまたはサブプロセスがアクティブ化されたときに開始される場所です。プロセスは最大で1つのNone開始イベントを持つことができます（他のタイプの開始イベントを除く）。また、フォームを介してプロセスをトリガーする場合に必要となります。

**None end events (None終了イベント)**は、プロセスまたはサブプロセス内に複数存在することができます。None終了イベントに入ると、現在の実行パスが終了します。プロセスインスタンスまたはサブプロセスにアクティブな実行パスが残っていない場合、完了となります。アクティビティに外向きのシーケンスフローがない場合、None終了イベントに接続されているのと同じように動作し、アクティビティが完了すると現在の実行パスが終了します。

**Intermediate none events (中間Noneイベント - throwing)**は、プロセス内で達成された特定の状態を示すために使用されます。マイルストーンや重要業績評価指標（KPI）など、プロセスの進行状況を監視・理解するのに特に役立ちます。エンジン自体はこのイベントで何も行わず、単に通過するだけです。

#### 3. XMLプロパティ・属性の詳細
NoneイベントのXML要素には、以下のプロパティが使用されます。

| プロパティ名 | 型 | 必須/任意 | デフォルト値 | 説明 |
| --- | --- | --- | --- | --- |
| id | string | 必須 | なし | 要素の一意の識別子 |
| name | string | 任意 | なし | 要素の表示名 |

#### 4. 実装に必要な設定項目
すべてのNoneイベントは変数の出力マッピング（variable output mappings）を持つことができます。開始イベントの場合、これはプロセス変数の初期化によく使用されます。

#### 5. コード例やXML例
以下は、各NoneイベントのXML表現の例です。

**None start event**:
```xml
<bpmn:startEvent id="order-placed" name="Order Placed" />
```

**None end event**:
```xml
<bpmn:endEvent id="order-delivered" name="Order Delivered" />
```

**Intermediate none event**:
```xml
<bpmn:intermediateThrowEvent id="money-collected" name="Money Collected" />
```

#### 6. 制約事項や注意点
プロセスは最大で**1つ**のNone開始イベントしか持つことができません。また、エンジンは中間Noneイベントで何のアクションも実行せず、単に通過します。アクティビティに外向きのシーケンスフローがない場合、暗黙的にNone終了イベントとして扱われる点にも注意が必要です。

#### 7. 他の要素との関連性
フォームを介してプロセスをトリガーするには、None開始イベントが必要です。また、変数の出力マッピングを使用して、プロセス変数を初期化したり更新したりすることができます。


---


BPMN, DMN, and FEEL

BPMN

BPMN primer

Version: 8.9

On this page

BPMN primer

Business Process Model and Notation 2.0 (BPMN) is an industry standard for process modeling and execution. A BPMN process is an XML document that has a visual representation. For example, here is a BPMN process:

The corresponding XML

```xml
<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn" exporter="Camunda Modeler" exporterVersion="0.1.0">  <bpmn:process id="Process_1" isExecutable="true">    <bpmn:startEvent id="StartEvent_1" name="Order Placed">      <bpmn:outgoing>SequenceFlow_1bq1azi</bpmn:outgoing>    </bpmn:startEvent>    <bpmn:sequenceFlow id="SequenceFlow_1bq1azi" sourceRef="StartEvent_1" targetRef="Task_1f47b9v" />    <bpmn:sequenceFlow id="SequenceFlow_09hqjpg" sourceRef="Task_1f47b9v" targetRef="Task_1109y9g" />    <bpmn:sequenceFlow id="SequenceFlow_1ea1mpb" sourceRef="Task_1109y9g" targetRef="Task_00moy91" />    <bpmn:endEvent id="EndEvent_0a27csw" name="Order Delivered">      <bpmn:incoming>SequenceFlow_0ojoaqz</bpmn:incoming>    </bpmn:endEvent>    <bpmn:sequenceFlow id="SequenceFlow_0ojoaqz" sourceRef="Task_00moy91" targetRef="EndEvent_0a27csw" />    <bpmn:serviceTask id="Task_1f47b9v" name="Collect Money">      <bpmn:extensionElements>        <zeebe:taskDefinition type="collect-money" retries="3" />      </bpmn:extensionElements>      <bpmn:incoming>SequenceFlow_1bq1azi</bpmn:incoming>      <bpmn:outgoing>SequenceFlow_09hqjpg</bpmn:outgoing>    </bpmn:serviceTask>    <bpmn:serviceTask id="Task_1109y9g" name="Fetch Items">      <bpmn:extensionElements>        <zeebe:taskDefinition type="fetch-items" retries="3" />      </bpmn:extensionElements>      <bpmn:incoming>SequenceFlow_09hqjpg</bpmn:incoming>      <bpmn:outgoing>SequenceFlow_1ea1mpb</bpmn:outgoing>    </bpmn:serviceTask>    <bpmn:serviceTask id="Task_00moy91" name="Ship Parcel">      <bpmn:extensionElements>        <zeebe:taskDefinition type="ship-parcel" retries="3" />      </bpmn:extensionElements>      <bpmn:incoming>SequenceFlow_1ea1mpb</bpmn:incoming>      <bpmn:outgoing>SequenceFlow_0ojoaqz</bpmn:outgoing>    </bpmn:serviceTask>  </bpmn:process>  <bpmndi:BPMNDiagram id="BPMNDiagram_1">    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">      <bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_1">        <dc:Bounds x="191" y="102" width="36" height="36" />        <bpmndi:BPMNLabel>          <dc:Bounds x="175" y="138" width="68" height="12" />        </bpmndi:BPMNLabel>      </bpmndi:BPMNShape>      <bpmndi:BPMNEdge id="SequenceFlow_1bq1azi_di" bpmnElement="SequenceFlow_1bq1azi">        <di:waypoint xsi:type="dc:Point" x="227" y="120" />        <di:waypoint xsi:type="dc:Point" x="280" y="120" />        <bpmndi:BPMNLabel>          <dc:Bounds x="253.5" y="99" width="0" height="12" />        </bpmndi:BPMNLabel>      </bpmndi:BPMNEdge>      <bpmndi:BPMNEdge id="SequenceFlow_09hqjpg_di" bpmnElement="SequenceFlow_09hqjpg">        <di:waypoint xsi:type="dc:Point" x="380" y="120" />        <di:waypoint xsi:type="dc:Point" x="440" y="120" />        <bpmndi:BPMNLabel>          <dc:Bounds x="410" y="99" width="0" height="12" />        </bpmndi:BPMNLabel>      </bpmndi:BPMNEdge>      <bpmndi:BPMNEdge id="SequenceFlow_1ea1mpb_di" bpmnElement="SequenceFlow_1ea1mpb">        <di:waypoint xsi:type="dc:Point" x="540" y="120" />        <di:waypoint xsi:type="dc:Point" x="596" y="120" />        <bpmndi:BPMNLabel>          <dc:Bounds x="568" y="99" width="0" height="12" />        </bpmndi:BPMNLabel>      </bpmndi:BPMNEdge>      <bpmndi:BPMNShape id="EndEvent_0a27csw_di" bpmnElement="EndEvent_0a27csw">        <dc:Bounds x="756" y="102" width="36" height="36" />        <bpmndi:BPMNLabel>          <dc:Bounds x="734" y="142" width="81" height="12" />        </bpmndi:BPMNLabel>      </bpmndi:BPMNShape>      <bpmndi:BPMNEdge id="SequenceFlow_0ojoaqz_di" bpmnElement="SequenceFlow_0ojoaqz">        <di:waypoint xsi:type="dc:Point" x="696" y="120" />        <di:waypoint xsi:type="dc:Point" x="756" y="120" />        <bpmndi:BPMNLabel>          <dc:Bounds x="726" y="99" width="0" height="12" />        </bpmndi:BPMNLabel>      </bpmndi:BPMNEdge>      <bpmndi:BPMNShape id="ServiceTask_0lao700_di" bpmnElement="Task_1f47b9v">        <dc:Bounds x="280" y="80" width="100" height="80" />      </bpmndi:BPMNShape>      <bpmndi:BPMNShape id="ServiceTask_0eetpqx_di" bpmnElement="Task_1109y9g">        <dc:Bounds x="440" y="80" width="100" height="80" />      </bpmndi:BPMNShape>      <bpmndi:BPMNShape id="ServiceTask_09won99_di" bpmnElement="Task_00moy91">        <dc:Bounds x="596" y="80" width="100" height="80" />      </bpmndi:BPMNShape>    </bpmndi:BPMNPlane>  </bpmndi:BPMNDiagram></bpmn:definitions>
```

This duality makes BPMN very powerful. The XML document contains all the necessary information to be interpreted by workflow engines and modeling tools like Zeebe. At the same time, the visual representation contains just enough information to be quickly understood by humans, even when they are non-technical people. The BPMN model is source code and documentation in one artifact.

The following is an introduction to BPMN 2.0, its elements, and their execution semantics. It tries to briefly provide an intuitive understanding of BPMN's power, but does not cover the entire feature set. For more exhaustive BPMN resources, refer to the

reference links

at the end of this section.

Modeling BPMN diagrams

​

The best tool for modeling BPMN diagrams for Zeebe is

Modeler

. Learn more by

modeling your first diagram

.

Download page

Source code repository

BPMN elements

​

Sequence flow: Controlling the flow of execution

​

A core concept of BPMN is a

sequence flow

that defines the order in which steps in the process happen. In BPMN's visual representation, a sequence flow is an arrow connecting two elements. The direction of the arrow indicates their order of execution.

You can think of process execution as tokens running through the process model. When a process is started, a token is created at the beginning of the model and advances with every completed step. When the token reaches the end of the process, it is consumed and the process instance ends. Zeebe's task is to drive the token and to make sure the job workers are invoked whenever necessary.

Tasks: Units of work

​

The basic elements of BPMN processes are tasks; these are atomic units of work composed to create a meaningful result. Whenever a token reaches a task, the token stops and Zeebe creates a job and notifies a registered worker to perform work. When that handler signals completion, the token continues on the outgoing sequence flow.

Choosing the granularity of a task is up to the person modeling the process. For example, the activity of processing an order can be modeled as a single

Process Order

task, or as three individual tasks

Collect Money

,

Fetch Items

,

Ship Parcel

. If you use Zeebe to orchestrate microservices, one task can represent one microservice invocation.

Refer to the

tasks

section on which types of tasks are currently supported and how to use them.

Gateways: Steering flow

​

Gateways are elements that route tokens in more complex patterns than plain sequence flow.

BPMN's

exclusive gateway

chooses one sequence flow out of many based on data:

BPMN's

parallel gateway

generates new tokens by activating multiple sequence flows in parallel:

Refer to the

gateways

section on which types of gateways are currently supported and how to use them.

Events: Waiting for something to happen

​

Events

in BPMN represent things that

happen

. A process can react to events (

catching

event) as well as emit events (

throwing

event). For example:

The circle with the envelope symbol is a catching message event. It makes the token continue as soon as a message is received. The XML representation of the process contains the criteria for which kind of message triggers continuation.

Events can be added to the process in various ways. Not only can they be used to make a token wait at a certain point, but also for interrupting a token's progress.

Refer to the

events

section on which types of events are currently supported and how to use them.

Subprocesses: Grouping elements

​

Subprocesses

are element containers that allow defining common functionality. For example, you can attach an event to a subprocess's border.

When the event is triggered, the subprocess is interrupted, regardless which of its elements is currently active.

Refer to the

subprocesses

section on which types of subprocesses are currently supported and how to use them.

Additional resources

​

BPMN specification

BPMN tutorial

Full BPMN reference

BPMN book

---


### Message events

#### 1. ページタイトルと概要説明
- **ページタイトル**: Message events
- **概要説明**: メッセージイベントは、メッセージを参照するイベントであり、適切なメッセージが受信されるまで待機するために使用されます。単一のプロセスインスタンスが、セカンダリプロセスまたは外部システムからのメッセージを待機する必要がある場合に使用されます。これは単一の送信者から単一の受信者への関係（1:1）であり、メッセージは複数の受信者を持つことはできません。

#### 2. BPMN要素の定義と用途
- **Message start events (メッセージ開始イベント)**: プロセスは1つ以上のメッセージ開始イベントを持つことができます。各メッセージイベントは一意のメッセージ名を持つ必要があります。プロセスがデプロイされると、各メッセージ開始イベントに対してメッセージサブスクリプションが作成されます。メッセージ名が一致する場合、メッセージは開始イベントに相関され、新しいプロセスインスタンスが作成されます。
- **Intermediate message catch events (中間メッセージキャッチイベント)**: 中間メッセージキャッチイベントに入ると、対応するメッセージサブスクリプションが作成されます。プロセスインスタンスはこの時点で停止し、メッセージが相関されるまで待機します。メッセージが相関されると、キャッチイベントが完了し、プロセスインスタンスが続行されます。
- **Message boundary events (メッセージ境界イベント)**: アクティビティは1つ以上のメッセージ境界イベントを持つことができます。各メッセージイベントは一意のメッセージ名を持つ必要があります。アクティビティに入ると、各境界メッセージイベントに対応するメッセージサブスクリプションが作成されます。中断しない境界イベントがトリガーされた場合、アクティビティは終了せず、複数のメッセージを相関させることができます。
- **Message throw events / Message end events (メッセージスローイベント / メッセージ終了イベント)**: 外部システム（例：Kafkaトピック）へのメッセージの公開をモデル化するために使用されます。これらはサービスタスクや送信タスクとまったく同じように動作し、同じジョブ関連のプロパティ（ジョブタイプ、カスタムヘッダーなど）を持ちます。

#### 3. XMLプロパティ・属性の詳細
- **messageRef**: メッセージ定義を参照するための属性。
- **name**: メッセージの名前。通常は静的な値（例：`order canceled`）として定義されますが、式（例：`= "order " + awaitingAction`）として定義することもできます。式は文字列を返す必要があります。
- **correlationKey**: メッセージの相関キー。通常はメッセージの相関キーを保持するプロセスインスタンスの変数にアクセスする式です。式は文字列または数値を返す必要があります。メッセージ開始イベントのみによって参照される場合、`correlationKey`は必須ではありません。

#### 4. 実装に必要な設定項目
- メッセージ開始イベントの場合、BPMNモデルで`correlationKey`を指定しません。アプリケーションがメッセージを送信する際に`correlationKey`を指定できます。
- メッセージスローイベントはZeebe自体によって処理されません。代わりに、定義されたジョブタイプでジョブを作成します。これらを処理するには、ジョブワーカーを提供する必要があります。

#### 5. コード例やXML例
**メッセージ定義を持つメッセージ開始イベント:**
```xml
<bpmn:message id="Message_0z0aft4" name="order-placed" />
<bpmn:startEvent id="order-placed" name="Order placed">
  <bpmn:messageEventDefinition messageRef="Message_0z0aft4" />
</bpmn:startEvent>
```

**メッセージ定義を持つ中間メッセージキャッチイベント:**
```xml
<bpmn:message id="Message_1iz5qtq" name="money-collected">
  <bpmn:extensionElements>
    <zeebe:subscription correlationKey="= orderId" />
  </bpmn:extensionElements>
</bpmn:message>
<bpmn:intermediateCatchEvent id="money-collected" name="Money collected" >
  <bpmn:messageEventDefinition messageRef="Message_1iz5qtq" />
</bpmn:intermediateCatchEvent>
```

**境界メッセージイベント:**
```xml
<bpmn:boundaryEvent id="order-canceled" name="Order Canceled" attachedToRef="collect-money">
  <bpmn:messageEventDefinition messageRef="Message_1iz5qtq" />
</bpmn:boundaryEvent>
```

#### 6. 制約事項や注意点
- メッセージは、プロセスがデプロイされる前に公開された場合、または適切な開始イベントなしでプロセスの新しいバージョンがデプロイされた場合は相関されません。
- `correlationKey`を使用してプロセスインスタンスの作成を制御できます。
  - このプロセスのインスタンスがアクティブであり、同じ`correlationKey`を持つメッセージによってトリガーされた場合、メッセージは相関されず、新しいインスタンスは作成されません。メッセージのTTL > 0の場合、バッファリングされます。
  - アクティブなプロセスインスタンスが完了または終了し、同じ`correlationKey`と一致するメッセージ名を持つメッセージがバッファリングされている場合、このメッセージが相関され、プロセスの最新バージョンの新しいインスタンスが作成されます。
- メッセージの`correlationKey`が空の場合、新しいプロセスインスタンスが作成され、インスタンスがすでにアクティブかどうかは確認されません。
- メッセージ開始イベントによってキャッチされたメッセージに`correlationKey`値が含まれている場合、`correlationKey`はキーごとに1つのプロセスインスタンスのみがアクティブであることを保証するために使用されます（冪等性）。`correlationKey`はプロセスインスタンスのタグとして保存されず、`tags`フィールドは空のままです。

#### 7. 他の要素との関連性
- **シグナルイベントとの違い**: シグナルイベントは複数のリスナーと通信する場合（1:N）に使用されますが、メッセージイベントは単一の送信者から単一の受信者への関係（1:1）です。
- **受信タスク (Receive task)**: 中間メッセージキャッチイベントの代替として使用でき、同じように動作しますが、境界イベントと一緒に使用できます。
- **サービスタスク / 送信タスク**: メッセージスローイベントおよびメッセージ終了イベントは、これらとまったく同じように動作し、同じジョブ関連のプロパティを持ちます。違いは、視覚的表現とモデルのセマンティクスです。
- **変数マッピング**: デフォルトでは、すべてのメッセージ変数はプロセスインスタンスにマージされます。この動作は、メッセージキャッチイベントで出力マッピングを定義することでカスタマイズできます。


---


### Timer events

#### 1. ページタイトルと概要説明
- **ページタイトル**: Timer events
- **概要説明**: Timer events（タイマーイベント）は、定義されたタイマーによってトリガーされるイベントです。

#### 2. BPMN要素の定義と用途
- **Timer start events (タイマー開始イベント)**:
  - プロセスは1つ以上のタイマー開始イベントを持つことができます。
  - 各タイマーイベントは、`time date`（日時）または`time cycle`（サイクル）の定義を持つ必要があります。
  - プロセスがデプロイされると、各タイマー開始イベントに対してタイマーがスケジュールされます。以前のバージョンのプロセス（BPMNプロセスIDに基づく）のスケジュールされたタイマーはキャンセルされます。
  - タイマーがトリガーされると、新しいプロセスインスタンスが作成され、対応するタイマー開始イベントがアクティブになります。
- **Intermediate timer catch events (中間タイマーキャッチイベント)**:
  - `time duration`（期間）または`time date`（日時）のいずれかを持つことができます。
  - 中間タイマーキャッチイベントに入ると、対応するタイマーがスケジュールされます。プロセスインスタンスはこの時点で停止し、タイマーがトリガーされるまで待機します。タイマーがトリガーされると、キャッチイベントが完了し、プロセスインスタンスが続行されます。
- **Timer boundary events (タイマー境界イベント)**:
  - **Interrupting (中断型)**: `time duration`または`time date`の定義を持つ必要があります。対応するタイマーがトリガーされると、アクティビティは終了します。タイムアウトのモデリング（例：5分後に処理をキャンセルして別のことを行う）によく使用されます。
  - **Non-interrupting (非中断型)**: `time duration`、`time cycle`、または`time date`の定義を持つ必要があります。アクティビティに入ると、対応するタイマーがスケジュールされます。タイマーがトリガーされ、0より大きい繰り返し回数を持つ`time cycle`として定義されている場合、定義された繰り返し回数に達するまでタイマーが再度スケジュールされます。`time duration`で定義された非中断型タイマー境界イベントは、指定された日時に達したときに1回だけトリガーされることに注意してください。通知のモデリング（例：処理に1時間以上かかる場合にサポートに連絡する）によく使用されます。

#### 3. XMLプロパティ・属性の詳細
タイマーは、日付（date）、期間（duration）、またはサイクル（cycle）のいずれかを提供して定義する必要があります。
タイマーは、静的値（例：`P3D`）または式（expression）として定義できます。
式を使用する2つの一般的な方法：
- 変数へのアクセス（例：`= remainingTime`）
- 時間値の使用（例：`= date and time(expirationDate) - date and time(creationDate)`）

### Time date (日時)
- ISO 8601の結合された日付と時間の表現として定義された特定の時点。
- タイムゾーン情報（UTCの場合は`Z`、またはゾーンオフセット）を含める必要があります。オプションでゾーンIDを含めることができます。
- 例：
  - `2019-10-01T12:00:00Z` - UTC時間
  - `2019-10-02T08:09:40+02:00` - UTCプラス2時間のゾーンオフセット
  - `2019-10-02T08:09:40+02:00[Europe/Berlin]` - ベルリンでのUTCプラス2時間のゾーンオフセット
- デプロイ時に日付が過去である場合、タイマーはすぐに発火します。

### Time duration (期間)
- ISO 8601の期間フォーマットとして定義され、時間間隔内の介在する時間の量を定義します。フォーマットは`P(n)Y(n)M(n)DT(n)H(n)M(n)S`です。
- 例：
  - `PT15S` - 15秒
  - `PT1H30M` - 1時間30分
  - `P14D` - 14日
  - `P14DT1H30M` - 14日1時間30分
  - `P3Y6M4DT12H30M5S` - 3年6ヶ月4日12時間30分5秒
- 期間がゼロまたは負の場合、タイマーはすぐに発火します。

### Time cycle (サイクル)
- ISO 8601の繰り返し間隔フォーマットとして定義され、期間と繰り返し回数を含みます。繰り返しが定義されていない場合、タイマーはキャンセルされるまで無限に繰り返されます。
- 例：
  - `R5/PT10S`: 10秒ごとに最大5回
  - `R/P1D`: 毎日、無限に
- 開始時間を定義することが可能です。これにより、タイマーは指定された開始時間に初めてトリガーされ、その後は通常通り間隔に従います。
  - `R3/2022-04-27T17:20:00Z/P1D`: 2022年4月27日午後5時20分(UTC)から開始して、毎日最大3回
  - `R/2022-01-01T10:00:00+02:00[Europe/Berlin]/P1D`: 2022年1月1日午前10時(UTC+2)から開始して、毎日無限に
- デプロイ時に開始時間が過去である場合、タイマーはデプロイ時にすぐに発火し、その後はその時点から通常の間隔で継続します。
- cron式を使用してタイムサイクルを指定することもできます。
  - `0 0 9-17 * * MON-FRI`: 月曜日から金曜日の午前9時から午後5時(UTC)までの毎時0分

#### 4. 実装に必要な設定項目
- タイマーイベントには、`<bpmn:timerEventDefinition>`要素を含める必要があります。
- その中に、`<bpmn:timeDate>`、`<bpmn:timeDuration>`、または`<bpmn:timeCycle>`のいずれかを含める必要があります。
- 式を使用する場合、プロセスのタイマー開始イベントに属する式はプロセスのデプロイ時に評価されます。それ以外の場合は、タイマーキャッチイベントのアクティブ化時に評価されます。評価結果は、静的値と同じISO 8601フォーマットを持つ`string`、または同等の時間値（日時、期間、またはサイクル）である必要があります。

#### 5. コード例やXML例

**Timer start event with time date:**
```xml
<bpmn:startEvent id="release-date">
  <bpmn:timerEventDefinition>
    <bpmn:timeDate>2019-10-01T12:00:00Z</bpmn:timeDate>
  </bpmn:timerEventDefinition>
</bpmn:startEvent>
```

**Intermediate timer catch event with time duration:**
```xml
<bpmn:intermediateCatchEvent id="coffee-break">
  <bpmn:timerEventDefinition>
    <bpmn:timeDuration>PT10M</bpmn:timeDuration>
  </bpmn:timerEventDefinition>
</bpmn:intermediateCatchEvent>
```

**Non-interrupting boundary timer event with time cycle:**
```xml
<bpmn:boundaryEvent id="reminder" cancelActivity="false" attachedToRef="process-order">
  <bpmn:timerEventDefinition>
    <bpmn:timeCycle>R3/PT1H</bpmn:timeCycle>
  </bpmn:timerEventDefinition>
</bpmn:boundaryEvent>
```

#### 6. 制約事項や注意点
- **非同期システム**: Zeebeは非同期システムです。その結果、タイマーが設定された時間に正確にトリガーされるという保証はありません。システムにかかっている負荷に応じて、タイマーは期日より遅くトリガーされる可能性があります。ただし、タイマーが期日より早くトリガーされることは決してありません。
- 過去の日付/期間がゼロまたは負の場合、タイマーはすぐに発火します。

#### 7. 他の要素との関連性
- **変数**: 式を使用して変数にアクセスし、タイマーの値を動的に設定できます。
- **アクティビティ**: 境界イベントとしてアクティビティにアタッチされ、タイムアウト（中断型）や通知（非中断型）をモデリングするために使用されます。


---


### Error events

#### 1. ページタイトルと概要説明
- **ページタイトル**: Error events
- **概要説明**: プロセス自動化において、デフォルトのシナリオから逸脱した場合に対処する方法の1つとしてBPMNエラーイベントを使用します。これにより、プロセスのモデルはタスク内で発生したエラーに反応することができます。

#### 2. BPMN要素の定義と用途
- **エラー (Errors)**: 発生する可能性のあるエラーを定義します。
- **エラーイベント (Error events)**: プロセス内の要素であり、定義されたエラーを参照します。1つのエラーは1つ以上のエラーイベントから参照される可能性があります。

#### 3. XMLプロパティ・属性の詳細
- **errorCode**: エラーは `errorCode` を定義する必要があります。この値は、スローされたエラーをどのキャッチイベントがキャッチできるかを決定するために使用されます。
  - **エラースローイベント (Error throw events)**: `errorCode` を式 (expression) または静的な値 (static value) として定義できます。式が設定されている場合、イベントに到達した時点で評価され、エラーのスローに使用されます。
  - **エラーキャッチイベント (Error catch events)**: `errorCode` は静的な値 (static value) でなければなりません。または、エラー参照を完全に省略することもでき、その場合はスローされた**すべて**のエラーをキャッチします。

#### 4. 実装に必要な設定項目
- **エラーのスロー**:
  - プロセス内でエラー**終了イベント (end event)** を使用してエラーをスローできます。
  - または、**クライアントコマンド (client command)** を使用してビジネスエラーが発生したことをZeebeに通知できます。このコマンドはジョブの処理中にのみ使用できます。エラーをスローすると同時に、ジョブは無効化され、他のジョブワーカーによってアクティブ化または完了されるのを防ぎます (gRPCコマンドおよびRESTリクエストを参照)。
- **エラーのキャッチ**:
  - スローされたエラーは、エラー**境界イベント (boundary event)** またはエラー**イベントサブプロセス (event subprocess)** を使用してキャッチできます。
  - エラーがスローされたスコープから開始し、エラーコードはそのレベルにアタッチされたエラー境界イベントおよびエラーイベントサブプロセスと照合されます。エラーは、エラーコードに一致するスコープ階層内の最初のイベントによってキャッチされます。各スコープで、エラーはキャッチされるか、親スコープに伝播されます。
  - コールアクティビティを介してプロセスインスタンスが作成された場合、呼び出し元の親プロセスインスタンスでエラーをキャッチすることもできます。
  - 単一のスコープ内で同じ `errorCode` を持つ複数のエラーキャッチイベントを定義することはできません。また、単一のスコープ内に複数のエラーキャッチオールイベント (すべてをキャッチするイベント) を配置することも許可されていません。ただし、特定の `errorCode` を持つエラーキャッチイベントと、エラーキャッチオールイベントの両方を同じスコープ内に定義することは可能です。この場合、`errorCode` に一致するエラーキャッチイベントが優先されます。
  - エラー境界イベントとエラーイベントサブプロセスは**中断 (interrupting)** でなければなりません。つまり、プロセスインスタンスは通常のパスに沿って続行せず、エラーをキャッチしたイベントから出るパスに従います。
  - ジョブに対してエラーがスローされた場合、関連するタスクが最初に終了します。実行を続行するには、エラーをキャッチしたエラー境界イベントまたはエラーイベントサブプロセスがアクティブ化されます。

#### 5. コード例やXML例
- **境界エラーイベント (A boundary error event)**:
```xml
<bpmn:error id="invalid-credit-card-error" errorCode="Invalid Credit Card" />
<bpmn:boundaryEvent id="invalid-credit-card-1" name="Invalid Credit Card" attachedToRef="collect-money">
  <bpmn:errorEventDefinition errorRef="invalid-credit-card-error" />
</bpmn:boundaryEvent>
```

- **エラー境界キャッチオールイベント (A error boundary catch-all event)**:
```xml
<bpmn:boundaryEvent id="invalid-credit-card-2" name="Unknown Error" attachedToRef="collect-money">
  <bpmn:errorEventDefinition id="catch-all-errors" />
</bpmn:boundaryEvent>
```

#### 6. 制約事項や注意点
- **未処理のエラー (Unhandled errors)**: エラーがスローされてキャッチされなかった場合、失敗を示す**インシデント (incident)** (例: `Unhandled error event`) が発生します。インシデントは、エラーがスローされた対応する要素 (処理されたジョブのタスクまたはエラー終了イベント) にアタッチされます。
  - タスクにアタッチされたインシデントを解決すると、エラーは無視され、ジョブが再び有効になり、ジョブワーカーによって再びアクティブ化および完了できるようになります。
  - エラー終了イベントにアタッチされたインシデントは、失敗がプロセス自体にあるため、ユーザーが解決することはできません。このプロセスインスタンスに対してエラーをキャッチするようにプロセスを変更することはできません。
- **ビジネスエラー vs. 技術的エラー**:
  - 技術的な問題 (例: サービスの一時的な利用不可) をエラーイベントで処理することは推奨されません。代わりに、再試行 (retries) またはインシデントへのフォールバックを使用します。
  - エラーの発生源よりも、エラーに対する**反応 (reaction)** に注目することが重要です。技術的な問題であっても、ビジネス上の反応 (例: スコアリングサービスが利用できない場合にプロセスを続行し、顧客に良い評価を与える) が適格となる場合があります。
  - プロセスでモデル化される**ビジネス上の反応**と、再試行やインシデントを使用して汎用的に処理される**技術的な反応**について話し合うことをお勧めします。

#### 7. 他の要素との関連性
- **変数マッピング (Variable mappings)**: クライアントコマンドからエラーがスローされた場合、ペイロードとともに変数をエラーキャッチイベントに渡すことができます。これらの変数は、エラーキャッチイベントで出力マッピング (output mapping) を定義することで、プロセスインスタンスにマージできます。
- **インシデント (Incidents)**: 未処理のエラーはインシデントを発生させます。


---


### Signal events

#### 1. ページタイトルと概要説明
- **ページタイトル**: Signal events
- **概要説明**: シグナルイベントは、シグナルを参照するイベントです。シグナルをブロードキャストすると、ブロードキャストされたシグナルの名前と一致するすべてのシグナルイベントがトリガーされます。複数のリスナーと通信したい場合に一般的に使用されます。

#### 2. BPMN要素の定義と用途
- **用途**: 複数のリスナーとの通信。中間イベントの場合、シグナルは対応するキャッチイベントでトークンが待機しているすべてのプロセスインスタンスを（異なるプロセス間であっても）トリガーします。開始イベントの場合、対応するシグナル開始を持つプロセスごとに1つのインスタンスを開始します。つまり、シグナルは「1対多（単一の送信者から複数の受信者）」の関係を形成します。
- **メッセージイベントとの違い**: メッセージイベントは、単一のプロセスインスタンスが二次プロセスや外部システムからのメッセージを待つ必要がある場合に使用され、「1対1（単一の送信者から単一の受信者）」の関係になります。

### Signal start events (シグナル開始イベント)
- プロセスインスタンスの開始に使用されます。
- シグナル開始イベントを持つ複数のプロセスをデプロイすると、1回のブロードキャストで複数のプロセスインスタンスを作成できます。
- シグナルサブスクリプションは、プロセス定義の最新バージョンに対してのみ存在します。同じプロセスの新しいバージョンをデプロイすると、古いサブスクリプションは削除され、新しいサブスクリプションが開かれます。

### Signal intermediate catch events (シグナル中間キャッチイベント)
- アクティビティに入ると、シグナルサブスクリプションが作成されます。プロセスインスタンスはこの時点で停止し、同じ名前のブロードキャストされたシグナルによってトリガーされるまで待機します。
- トリガーされると、対応するシグナルキャッチイベントが完了し、プロセスインスタンスが続行されます。

### Signal boundary events (シグナル境界イベント)
- アクティビティは1つ以上のシグナル境界イベントを持つことができます。各シグナルイベントは一意のシグナル名を持つ必要があります。
- 中断しない（non-interrupting）境界イベントがトリガーされた場合、アクティビティは終了せず、複数のブロードキャストされたシグナルが境界イベントをトリガーできます。

### Signal throw events (シグナルスローイベント)
- プロセスには、シグナルのブロードキャストをモデル化するためのシグナル中間スローイベントまたはシグナル終了イベントを含めることができます。
- シグナルスローイベントに入ると、シグナルサブスクリプションをトリガーできるシグナルをブロードキャストします。

#### 3. XMLプロパティ・属性の詳細
- **`signal`**: BPMNでは、シグナルイベントは `signal` を参照します。シグナルは1つ以上のシグナルイベントから参照できます。
- **`name`**: シグナルは `name` を定義する必要があります。この値は以下を決定するために使用されます：
  - シグナルスローイベントでブロードキャストするシグナルの名前。
  - シグナルキャッチイベントでサブスクライブするシグナルの名前。
  - 通常、静的な値（例：`order canceled`）として定義されますが、式（例：`= "order " + awaitingAction`）として定義することもできます。式は `string` の結果になる必要があります。

#### 4. 実装に必要な設定項目
- **変数のマッピング (Variable mappings)**:
  - シグナルをブロードキャストする際、変数を渡すことができます。
  - デフォルトでは、すべてのシグナル変数はプロセスインスタンスにマージされます。この動作は、シグナルキャッチイベントで出力マッピング（output mapping）を定義することでカスタマイズできます。
  - シグナルスローイベントがシグナルをブロードキャストする際、すべてのローカル変数が渡されます。入力マッピング（input mappings）を使用してこれらのローカル変数を定義できます。

#### 5. コード例やXML例

**Signal start event:**
```xml
<bpmn:startEvent id="startEventId" name="Order placed">
  <bpmn:signalEventDefinition id="signalEventDefinitionId" signalRef="signalId" />
</bpmn:startEvent>
<bpmn:signal id="signalId" name="order placed" />
```

**Signal boundary event:**
```xml
<bpmn:boundaryEvent id="order-canceled" name="Order canceled" attachedToRef="ActivityId">
  <bpmn:signalEventDefinition id="signalId" />
</bpmn:boundaryEvent>
<bpmn:signal id="signalId" name="order canceled" />
```

**Signal intermediate catch event:**
```xml
<bpmn:intermediateThrowEvent id="money-collected" name="Money collected">
  <bpmn:signalEventDefinition id="signalEventDefinitionId" signalRef="signalId" />
</bpmn:intermediateThrowEvent>
<bpmn:signal id="signalId" name="money collected" />
```

**Signal end event:**
```xml
<bpmn:endEvent id="parcel_shipped" name="Parcel shipped">
  <bpmn:signalEventDefinition id="signalEventDefinitionId" signalRef="signalId" />
</bpmn:endEvent>
<bpmn:signal id="signalId" name="parcel shipped" />
```

#### 6. 制約事項や注意点
- シグナル開始イベントのサブスクリプションは、プロセス定義の最新バージョンに対してのみ存在します。
- シグナル境界イベントを使用する場合、各シグナルイベントは一意のシグナル名を持つ必要があります。
- シグナル名に式を使用する場合、シグナル開始イベントに属する式はプロセスのデプロイ時に評価されます。それ以外の場合は、シグナルイベントのアクティブ化時に評価されます。

#### 7. 他の要素との関連性
- **メッセージイベントとの違い**: メッセージイベントは1対1の通信に使用されますが、シグナルイベントは1対多の通信に使用されます。
- **変数スコープ**: シグナルを介して変数を渡す場合、変数スコープの概念が適用されます。


---


### Escalation Events

#### Overview
Escalation events are events which reference a named escalation, and are used to communicate to a higher flow scope. Unlike an error, an escalation event is non-critical and execution continues at the location of throwing.

#### Execution Flow
1. The process reaches the `Throw` event.
2. This throws an escalation to a higher flow scope.
3. The escalation is caught by the `Catch` event.
4. As escalation events are non-critical, the outgoing sequence flows of `Throw` and `Catch` are both taken.

#### Defining an Escalation
In BPMN, an `escalation event` references an `escalation`. Escalations can be referenced by one or more escalation events.

An escalation must define an `escalationCode`. The value of this `escalationCode` is used to determine which catch event can catch the thrown escalation.

#### Throwing the Escalation
For escalation throw events, it is possible to define the `escalationCode` as an `expression` or a static value. If an `escalationCode` expression is configured then it will be evaluated once the event is reached, and used to throw the escalation.

An escalation can be thrown by an escalation end event, or by an intermediate escalation throw event. Escalation events are non-critical. This means that if the throwing event has any outgoing sequence flows, they will be taken.

#### Catching the Escalation
For escalation catch events `escalationCode` must be a static value. Alternatively an escalation catch event may omit the escalation reference all together. In this case it catches **all** thrown escalations.

An escalation can be caught using a boundary event, or using an event subprocess. It is caught by one catch event at most, and this will be the catch event in the nearest parent flow scope.

It is not possible to define multiple escalation catch events with the same `escalationCode` in a single scope. It is also not permitted to have multiple escalation catch-all events in a single scope. However, it is possible to define both an escalation catch event referencing an escalation with a particular `escalationCode` and an escalation catch-all event within the same scope. When this happens, the escalation catch event that matches the `escalationCode` is prioritized.

If there are no escalation catch events that match the `escalationCode`, the escalation will not be caught. Unlike with error events, no incident is raised. The process will continue without escalating.

Even though escalations are non-critical, it is still possible make escalation catch events interrupting. This will behave the same as other interrupting events. The catch event will terminate the scope it is attached to. In this case, the outgoing sequence flows of the throwing escalation event are not taken.

#### XML Representation

An intermediate escalation throw event with expression:
```xml
<bpmn:intermediateThrowEvent id="StartEvent_1">
  <bpmn:escalationEventDefinition id="EscalationEventDefinition_0sdm9od" escalationRef="Escalation_2alpsjo" />
</bpmn:intermediateThrowEvent>
<bpmn:escalation id="Escalation_2alpsjo" name="Escalation_2alpsjo" escalationCode="=escalationCode" />
```

An escalation boundary catch event:
```xml
<bpmn:boundaryEvent id="Event_1wpcmdz" cancelActivity="false" attachedToRef="Activity_1q7i1lv">
  <bpmn:escalationEventDefinition id="EscalationEventDefinition_1fpge5i" escalationRef="Escalation_2alpsjo" />
</bpmn:boundaryEvent>
<bpmn:escalation id="Escalation_2alpsjo" name="Escalation_2alpsjo" escalationCode="escalationCode" />
```

A escalation boundary catch-all event:
```xml
<bpmn:boundaryEvent id="Event_1wpcmdz" cancelActivity="false" attachedToRef="Activity_1q7i1lv">
  <bpmn:escalationEventDefinition id="EscalationEventDefinition_1fpge5i" />
</bpmn:boundaryEvent>
```


---


### Terminate events

#### 1. ページタイトルと概要説明
- **ページタイトル**: Terminate events
- **概要説明**: Terminate end events（終了イベント（停止））は、唯一の種類の終了イベント（停止）です。プロセスインスタンスが終了イベント（停止）に到達すると、その終了イベントと同じフロースコープ内にあるすべての要素インスタンスを終了させます。

#### 2. BPMN要素の定義と用途
- **定義**: 同じフロースコープ内のすべての要素インスタンスを終了させる終了イベント。
- **用途**: 不要になった並行フローを終了させるためによく使用されます。

#### 3. XMLプロパティ・属性の詳細
- `bpmn:endEvent`: 終了イベントの基本要素。
  - `id`: (文字列, 必須) イベントの一意の識別子。
- `bpmn:terminateEventDefinition`: 終了イベント（停止）を定義する要素。
  - `id`: (文字列, 必須) 定義の一意の識別子。

#### 4. 実装に必要な設定項目
特に追加の設定項目はドキュメントに記載されていません。BPMN XMLにおいて `<bpmn:terminateEventDefinition />` を含めることで実装されます。

#### 5. コード例やXML例
```xml
<bpmn:endEvent id="terminate-end-event">
  <bpmn:incoming>Flow_0zv9prm</bpmn:incoming>
  <bpmn:terminateEventDefinition id="TerminateEventDefinition_1" />
</bpmn:endEvent>
```

#### 6. 制約事項や注意点
- **プロセススコープでの動作**: サブプロセスに埋め込まれていないプロセススコープの終了イベント（停止）は、プロセスインスタンスのすべての要素インスタンスを終了させます。終了後、プロセスインスタンスは完了します。
- **コールアクティビティからの呼び出し**: プロセスインスタンスが親プロセスのコールアクティビティによって作成された場合、コールアクティビティは完了し、親プロセスインスタンスは外向きのシーケンスフローに進みます。
- **サブプロセス内での動作**: 埋め込みサブプロセスまたはイベントサブプロセス内の終了イベント（停止）は、そのサブプロセスのすべての要素インスタンスを終了させます。終了後、サブプロセスは完了し、プロセスインスタンスは外向きのシーケンスフローに進みます。
- **スコープの制限**: 終了イベント（停止）はそのサブプロセスに限定されます。サブプロセス外の要素インスタンスは終了させません。
- **マルチインスタンスサブプロセス**: サブプロセスがマルチインスタンスの場合、終了イベント（停止）は現在のイテレーションの要素インスタンスのみを終了させます。他のマルチインスタンスイテレーションの要素インスタンスは終了させません。

#### 7. 他の要素との関連性
- **並行タスク**: 並行して実行されているタスク（例：タスクBとタスクC）がある場合、一方が終了イベント（停止）に到達すると、もう一方のタスクはキャンセルされます。
- **コールアクティビティ**: 親プロセスから呼び出された場合、終了イベント（停止）に到達すると親プロセスに制御が戻ります。
- **サブプロセス**: サブプロセス内で使用された場合、そのサブプロセスのみを終了させ、親プロセスは継続します。


---


### Link events

#### 概要説明
Link events are intermediate events that connect two sections of a process. They have no significance related to content, but facilitate the diagram-creation process.

#### BPMN要素の定義と用途
You can use link events to create loops, to skip sections of a process, or to simplify the sequence flow lines in the diagram.
Link events have a throwing link event as the "exit point", and a catching link event as the "re-entrance point". They are linked together by their link name. Multiple throwing link events can link to the same catching link event. A throwing link event cannot link to multiple catching link events.
In practice, two paired link events function the same as two intermediate none events connected via a sequence flow.
Link events can be very useful if you draw comprehensive process diagrams with many sequence flows. Links help avoid what otherwise might look like a “spaghetti” diagram. In the example below, a retry loop is created using the link events pair `A`.

#### 制約事項や注意点
Link events are limited to a single scope. Link events can only be used to link sections of a process within the same scope. I.e., they can only exist together on the root process level or within the same subprocess.
Similarly, a sequence flow cannot be drawn between flow nodes at different scopes. For example, a task in the root process level cannot connect to another task in a subprocess using a sequence flow. Link events have the same limitation.

#### コード例やXML例
```xml
<bpmn:intermediateThrowEvent id="Throw_Link_Event_A" name="A">
  <bpmn:linkEventDefinition id="ThrowLinkEventDefinition" name="A" />
</bpmn:intermediateThrowEvent>
<bpmn:intermediateCatchEvent id="Catch_Link_Event_A" name="A">
  <bpmn:linkEventDefinition id="CatchLinkEventDefinition" name="A" />
</bpmn:intermediateCatchEvent>
```

#### 他の要素との関連性
- Intermediate none events


---


### Compensation events

#### Overview
Compensation events assist with undoing steps that were already successfully completed in the case that their results are no longer desired and need to be reversed.

To revert the effects of an activity, a compensation boundary event is attached to the activity. This activity is called **compensation activity**. The compensation boundary event is associated with the compensation handler, an activity with a compensation marker that is in charge of reverting the effects of the compensation activity.

#### Execution of Compensation Events
1. After the service task `A` is completed, the process reaches the compensation intermediate throw event.
2. This invokes the compensation handler `Undo A` associated with the compensation boundary event.
3. Once the compensation handler `Undo A` is completed, the process completes the compensation intermediate throw event and takes the outgoing sequence flow.

#### Triggering Compensation
When a process instance enters a compensation intermediate throw or end event, it triggers the compensation within its scope and invokes all compensation handlers of completed activities. The compensation handlers of active or terminated activities are not invoked. The compensation throw event remains active until all invoked compensation handlers are completed.

**Note:** The process instance invokes all compensation handlers at once without any specific order. If the order is important, the compensation can be triggered for a specific activity.

#### Compensating Embedded Subprocesses
If a process instance enters a compensation throw event and there are completed embedded subprocesses in the same scope, it invokes the compensation handlers within these subprocesses and nested subprocesses. The compensation handlers are not invoked if the subprocess is active or terminated.

If the compensation throw event is inside an embedded subprocess, the process instance invokes only the compensation handlers within the subprocess. It doesn't invoke any compensation handler outside the subprocess.

**Info:** Compensation handlers of child processes are not invoked. The triggering of the compensation stops at the call activity. To revert the effects of a child process, attach a compensation boundary event on the call activity.

#### Compensating Multi-instance Activities
The compensation handler of a multi-instance activity is invoked only once, rather than for each item in the input collection. The compensation handler is responsible for reverting the effects of all instances of the multi-instance activity.

To revert the effects of each instance separately, the compensation handler could be marked as multi-instance as well.

**Note:** The process instance invokes the compensation handler only if all instances of the multi-instance activity are completed.

#### Triggering Compensation for a Specific Activity
By default, a compensation throw event invokes all compensation handlers in its scope. However, it is also possible to trigger the compensation for a specific activity. This can be used to enforce that compensation handlers are invoked synchronously in a given order.

On a compensation intermediate throw or end event, it is possible to specify the activity to compensate by using the property `activityRef`. The referenced activity must have a compensation boundary event and must be in the same scope of the compensation throw event.

#### Triggering Compensation from an Event Subprocess
An interrupting or non-interrupting event subprocess can contain compensation intermediate throw events or a compensation end event. These compensation events can specify an activity or broadcast the compensation within the outer scope of the event subprocess.

A common pattern is to use this in combination with an error event subprocess to revert the effects of compensation activities if a failure occurs that can't be recovered from.

#### XML Representation
An intermediate compensation throw event with a referenced activity:

```xml
<intermediateThrowEvent id="CompensationThrowEvent">
  <incoming>Flow_0b2blc2</incoming>
  <outgoing>Flow_1goayj7</outgoing>
  <compensateEventDefinition id="CompensateEventDefinition_1afu1vn" activityRef="Task_A" />
</intermediateThrowEvent>
```

### XML Properties
- `activityRef`: (Optional) Specifies the activity to compensate. The referenced activity must have a compensation boundary event and must be in the same scope of the compensation throw event.


---


### Embedded subprocess

#### 1. ページタイトルと概要説明
- **ページタイトル**: Embedded subprocess
- **概要説明**: Embedded subprocess（埋め込みサブプロセス）は、プロセスの要素をグループ化するためのBPMN要素です。

#### 2. BPMN要素の定義と用途
- **定義**: プロセス内の複数の要素を1つのサブプロセスとしてグループ化します。
- **用途**: プロセス図のビューを簡素化し、複雑さを隠蔽するために使用されます。また、境界イベント（boundary events）と組み合わせて使用されることが多く、割り込み境界イベントがトリガーされると、サブプロセス全体（すべてのアクティブな要素を含む）が終了します。

#### 3. XMLプロパティ・属性の詳細
- `id`: (必須) サブプロセスの一意の識別子。
- `name`: (任意) サブプロセスの名前。

#### 4. 実装に必要な設定項目
- 埋め込みサブプロセスは、正確に**1つ**の「none start event（空の開始イベント）」を持たなければなりません。他の開始イベントは許可されていません。
- 埋め込みサブプロセスに入ると、開始イベントがアクティブになります。サブプロセスは、含まれる要素のいずれかがアクティブである限り、アクティブなままです。最後の要素が完了すると、サブプロセスが完了し、外向きのシーケンスフローが実行されます。
- 入力マッピング（Input mappings）を使用して、サブプロセスのスコープ内に新しいローカル変数を作成できます。これらの変数はサブプロセス内でのみ表示されます。
- デフォルトでは、サブプロセスのローカル変数は伝播されません（つまり、スコープとともに削除されます）。この動作は、サブプロセスで出力マッピング（Output mappings）を定義することでカスタマイズできます。出力マッピングはサブプロセスの完了時に適用されます。

#### 5. コード例やXML例
開始イベントを持つ埋め込みサブプロセスのXML例：
```xml
<bpmn:subProcess id="process-order" name="Process Order">
  <bpmn:startEvent id="order-placed" />
  ... more contained elements ...
</bpmn:subProcess>
```

#### 6. 制約事項や注意点
- **開始イベントの制限**: 埋め込みサブプロセスは、正確に1つの「none start event」を持たなければなりません。
- **折りたたまれたサブプロセス（Collapsed subprocesses）**:
  - モデルに埋め込みサブプロセスを追加する際、折りたたまれた状態または展開された状態のいずれかで追加できます。モデル内の既存の展開されたサブプロセスを折りたたむことはできません。
  - Optimizeでは、折りたたまれたサブプロセスは現在部分的にしかサポートされていません。折りたたまれたサブプロセスを含む図をインポートすることはできますが、サブプロセスをドリルダウンすることはできません。他のすべてのCamundaコンポーネントは、折りたたまれたサブプロセスを完全にサポートしています。
  - 折りたたまれたサブプロセスは純粋に表示目的で機能します。再利用可能なプロセスを作成する場合は、コールアクティビティ（call activities）を使用することが推奨されます。
  - Modelerで折りたたまれたサブプロセスを追加すると、ドリルダウン用のリンクが表示されます。このリンクは、同じ図内の埋め込みサブプロセスのみを開きます。そのリンクから別のプロセスをターゲットにしたり再利用したりすることはできません。すでに作成した別のプロセスを参照するには、代わりにコールアクティビティを使用してください。

#### 7. 他の要素との関連性
- **境界イベント（Boundary events）**: 埋め込みサブプロセスは境界イベントと一緒に使用されることがよくあります。1つ以上の境界イベントをサブプロセスにアタッチできます。
- **コールアクティビティ（Call activities）**: 再利用可能なプロセスを作成する場合や、別のプロセスを参照する場合は、埋め込みサブプロセスではなくコールアクティビティを使用することが推奨されます。


---


### Call activities

#### 1. ページタイトルと概要説明
- **ページタイトル**: Call activities
- **概要説明**: コールアクティビティ（または再利用可能なサブプロセス）は、現在のプロセスの一部として別のプロセスを呼び出して実行することを可能にします。埋め込みサブプロセス（embedded subprocess）に似ていますが、プロセスが外部化（別のBPMNとして保存）されており、異なるプロセスから呼び出すことができます。

#### 2. BPMN要素の定義と用途
- コールアクティビティに入ると、参照されたプロセスの新しいプロセスインスタンスが作成されます。
- 新しいプロセスインスタンスは**none start event**（開始イベント）でアクティブになります。他のタイプの開始イベントを持つこともできますが、それらは無視されます。
- 作成されたプロセスインスタンスが完了すると、コールアクティビティを終了し、出力シーケンスフローが実行されます。

#### 3. XMLプロパティ・属性の詳細
- `processId` (必須): 呼び出されるプロセスのBPMNプロセスIDを定義します。静的な値（例: `shipping-process`）または式（例: `= "shipping-" + tenantId`）として定義できます。式はコールアクティビティのアクティブ化時に評価され、文字列を返す必要があります。
- `bindingType` (任意): 呼び出されるプロセスのどのバージョンをインスタンス化するかを決定します。
  - `latest` (デフォルト): コールアクティビティがアクティブになった時点での最新のデプロイ済みバージョン。
  - `deployment`: 呼び出し元プロセスの現在実行中のバージョンと一緒にデプロイされたバージョン。
  - `versionTag`: `versionTag`属性で指定されたバージョンタグが付与された最新のデプロイ済みバージョン。
- `versionTag` (任意): `bindingType`が`versionTag`の場合に指定するバージョンタグ。
- `propagateAllChildVariables` (任意): デフォルトは`true`。作成されたプロセスインスタンスのすべての変数をコールアクティビティに伝播するかどうかを設定します。
- `propagateAllParentVariables` (任意): デフォルトは`true`。コールアクティビティスコープのすべての変数を子プロセスインスタンスにコピーするかどうかを設定します。

#### 4. 実装に必要な設定項目
- 呼び出されるプロセスの`processId`の定義。
- 必要に応じた`bindingType`の選択。
- 境界イベント（中断/非中断）の設定。
- 変数のスコープとマッピング（入力マッピング、出力マッピング）の設定。

#### 5. コード例やXML例

静的プロセスID、すべての子変数の伝播がオン、明示的なバインディングタイプなし（暗黙的に`latest`が使用される）のコールアクティビティ:
```xml
<bpmn:callActivity id="Call_Activity" name="Call Process A">
  <bpmn:extensionElements>
    <zeebe:calledElement processId="child-process-a" propagateAllChildVariables="true" />
  </bpmn:extensionElements>
</bpmn:callActivity>
```

`deployment`バインディングタイプを持つコールアクティビティ:
```xml
<bpmn:callActivity id="Call_Activity" name="Call Process A">
  <bpmn:extensionElements>
    <zeebe:calledElement processId="child-process-a" bindingType="deployment" />
  </bpmn:extensionElements>
</bpmn:callActivity>
```

`versionTag`バインディングタイプを持つコールアクティビティ:
```xml
<bpmn:callActivity id="Call_Activity" name="Call Process A">
  <bpmn:extensionElements>
    <zeebe:calledElement processId="child-process-a"
                         bindingType="versionTag" versionTag="v1.0" />
  </bpmn:extensionElements>
</bpmn:callActivity>
```

すべての子プロセスへの変数のコピーがオフになっているコールアクティビティ:
```xml
<bpmn:callActivity id="Call_Activity" name="Call Process A">
  <bpmn:extensionElements>
    <zeebe:calledElement processId="child-process-id" propagateAllParentVariables="false" />
    <zeebe:ioMapping>
      <zeebe:input source="=variableValue" target="variableName" />
    </zeebe:ioMapping>
  </bpmn:extensionElements>
</bpmn:callActivity>
```

#### 6. 制約事項や注意点
- **境界イベント**:
  - 中断境界イベントがトリガーされると、コールアクティビティと作成されたプロセスインスタンスは終了します。作成されたプロセスインスタンスの変数はコールアクティビティに伝播されません。
  - 非中断境界イベントがトリガーされた場合、作成されたプロセスインスタンスは影響を受けません。出力パスのアクティビティは、別のプロセスインスタンスにバインドされているため、作成されたプロセスインスタンスの変数にアクセスできません。
- **変数の伝播**:
  - コールアクティビティが並列フロー（例: 並列マルチインスタンスとしてマークされている場合）にある場合は、`propagateAllChildVariables`属性を無効にするか、出力マッピングを定義することが推奨されます。そうしないと、並列フローで変数が変更されたときに誤って上書きされる可能性があります。
  - `propagateAllParentVariables`を`false`に設定することで、上位スコープに存在する変数がコピーされなくなります。

#### 7. 他の要素との関連性
- **Embedded subprocess (埋め込みサブプロセス)**: 似ていますが、コールアクティビティは外部化されており、異なるプロセスから呼び出すことができます。
- **Expressions (式)**: `processId`の動的な定義に使用されます。
- **Variable scopes (変数スコープ)** と **Variable mappings (変数マッピング)**: コールアクティビティと呼び出されるプロセス間のデータの受け渡しに密接に関連しています。


---


### BPMN coverage

The following BPMN elements are supported by Camunda modeling tools. Elements highlighted in green (marked as "implemented" in the source) are supported for execution by Camunda 8.

#### Participants
- Pool (Implemented)
- Lane (Implemented)

#### Subprocesses
- Embedded Subprocess (Implemented)
- Call Activity (Implemented)
- Event Subprocess (Implemented)
- Transactional Subprocess
- Ad-Hoc Subprocess (Implemented)

#### Tasks
- Service Task (Implemented)
- User Task (Implemented)
- Receive Task (Implemented)
- Send Task (Implemented)
- Business Rule Task (Implemented)
- Script Task (Implemented)
- Manual Task (Implemented)
- Receive Task Instantiated
- Undefined Task (Implemented)

#### Gateways
- Exclusive Gateway (Implemented)
- Parallel Gateway (Implemented)
- Event-Based Gateway (Implemented)
- Inclusive Gateway (Implemented)
- Complex Gateway

#### Markers
- Multi-Instance Parallel (Implemented)
- Multi-Instance Sequential (Implemented)
- Loop
- Compensation (Implemented)
- Ad-Hoc (Implemented)

#### Data
> `DataObject` and `DataStore`, like other BPMN standard IO mappings, are supported by Camunda for modeling purposes only.

- Data Object (Implemented)
- Data Store (Implemented)

#### Artifacts
- Annotation (Implemented)
- Group (Implemented)

#### Events

| Type | Start | Intermediate Event Subprocess | Intermediate Event Subprocess non-interrupting | Intermediate Catch | Intermediate Boundary | Intermediate Boundary non-interrupting | Intermediate Throw | End |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **None** | Implemented | | | | | | Implemented | Implemented |
| **Message** | Implemented | Implemented | Implemented | Implemented | Implemented | Implemented | Implemented | Implemented |
| **Timer** | Implemented | Implemented | Implemented | Implemented | Implemented | Implemented | | |
| **Error** | | Implemented | | | Implemented | | | Implemented |
| **Signal** | Implemented | Implemented | Implemented | Implemented | Implemented | Implemented | Implemented | Implemented |
| **Conditional** | Implemented | Implemented | Implemented | Implemented | Implemented | Implemented | | |
| **Escalation** | | Implemented | Implemented | | Implemented | Implemented | Implemented | Implemented |
| **Compensation** | | Not Implemented | | | Implemented | | Implemented | Implemented |
| **Cancel** | | | | | Not Implemented | | | Not Implemented |
| **Terminate** | | | | | | | | Implemented |
| **Link** | | | | Implemented | | | Implemented | |
| **Multiple** | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented |
| **Multiple Parallel** | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | | |

*Note: "Implemented" means supported for execution by Camunda 8.*


---


### Event subprocess

#### 1. ページタイトルと概要説明
- **ページタイトル**: Event subprocess
- **概要説明**: イベントサブプロセスは、イベントによってトリガーされるサブプロセスです。これはプロセス全体にグローバルに追加することも、埋め込みサブプロセス内にローカルに追加することもできます。

#### 2. BPMN要素の定義と用途
- イベントサブプロセスは、以下のいずれかのタイプの開始イベントを正確に**1つ**持つ必要があります：
  - Timer (タイマー)
  - Message (メッセージ)
  - Error (エラー)
  - Signal (シグナル)
  - Escalation (エスカレーション)
- イベントサブプロセスは境界イベント（boundary event）のように振る舞いますが、スコープにアタッチされるのではなく、スコープの内部に存在します。
- 境界イベントと同様に、イベントサブプロセスは中断型（interrupting）または非中断型（non-interrupting）にすることができます（BPMNでは開始イベントの境界線が実線か破線かで示されます）。
- イベントサブプロセスの開始イベントは、それを含むスコープがアクティブになったときにトリガーされる可能性があります。

#### 3. XMLプロパティ・属性の詳細
- `triggeredByEvent`: イベントサブプロセスであることを示す属性。値は `"true"`。
- `isInterrupting`: 開始イベントが中断型かどうかを示す属性。値は `"true"` または `"false"`。

#### 4. 実装に必要な設定項目
- **Variables (変数)**:
  - イベントサブプロセスはスコープ内にあるため、それを含むスコープのすべてのローカル変数にアクセスし、変更することができます（境界イベントでは不可能です）。
  - **Input mappings (入力マッピング)**: イベントサブプロセスのスコープ内に新しいローカル変数を作成するために使用できます。これらの変数はイベントサブプロセス内でのみ表示されます。入力マッピングが定義されていない場合、イベントとともに変数にデフォルトの動作が適用されます。
  - **Output mappings (出力マッピング)**: デフォルトでは、イベントサブプロセスのローカル変数は伝播されません（つまり、スコープとともに削除されます）。この動作は、イベントサブプロセスで出力マッピングを定義することでカスタマイズできます。出力マッピングは、イベントサブプロセスの完了時に適用されます。

#### 5. コード例やXML例
中断型タイマー開始イベントを持つイベントサブプロセスのXML表現：

```xml
<bpmn:subProcess id="compensate-subprocess" triggeredByEvent="true">
  <bpmn:startEvent id="cancel-order" isInterrupting="true">
    <bpmn:timerEventDefinition>
      <bpmn:timeDuration>PT5M</bpmn:timeDuration>
    </bpmn:timerEventDefinition>
  ... other elements
</bpmn:subProcess>
```

#### 6. 制約事項や注意点
- 非中断型のイベントサブプロセスは複数回トリガーされる可能性があります。
- 中断型のイベントサブプロセスは1回だけトリガーされます。
- 中断型のイベントサブプロセスがトリガーされると、他の非中断型イベントサブプロセスのインスタンスを含む、それを含むスコープのすべてのアクティブなインスタンスが終了します。
- イベントサブプロセスがトリガーされた場合、トリガーされたインスタンスが完了するまで、それを含むスコープは完了しません。

#### 7. 他の要素との関連性
- **境界イベント (Boundary event)**: イベントサブプロセスは境界イベントに似ていますが、スコープの外部ではなく内部に存在するため、スコープのローカル変数にアクセスして変更できる点が異なります。
- **埋め込みサブプロセス (Embedded subprocess)**: イベントサブプロセスは埋め込みサブプロセス内にローカルに追加することができます。
- **変数スコープ (Variable scopes)**: イベントサブプロセスは独自の変数スコープを持ち、入力/出力マッピングを使用して変数を管理できます。


---


### Multi-instance

#### 1. ページタイトルと概要説明
- **ページタイトル**: Multi-instance
- **概要説明**: Multi-instanceアクティビティは、指定されたコレクションの各要素に対して1回ずつ、複数回実行されるアクティビティです（プログラミング言語の `foreach` ループに似ています）。

#### 2. BPMN要素の定義と用途
- **定義**: 実行レベルでは、Multi-instanceアクティビティは「Multi-instance body」と「inner activity」の2つの部分で構成されます。Multi-instance bodyは、inner activityのすべてのインスタンスのコンテナです。
- **用途**: Service tasks、Receive tasks、Embedded subprocesses、Call activitiesなど、サポートされているすべてのアクティビティに対してMulti-instanceマーカーをサポートしています。
- **動作**: アクティビティに入ると、Multi-instance bodyがアクティブになり、`inputCollection` の各要素に対して1つのインスタンスが作成されます（順次または並列）。すべてのインスタンスが完了すると、bodyが完了し、アクティビティから抜けます。

#### 3. XMLプロパティ・属性の詳細
- `isSequential`: (boolean) 順次実行するかどうか。`true` の場合は順次、`false`（デフォルト）の場合は並列。
- `inputCollection`: (expression) 反復処理するコレクションを定義する式（例: `= items`）。任意の型の配列を返す必要があります。
- `inputElement`: (string) インスタンス内で `inputCollection` の現在の要素にアクセスするための変数名（例: `item`）。
- `outputCollection`: (string) 収集された出力を保存する変数名（例: `results`）。
- `outputElement`: (expression) インスタンスの出力を定義する式（例: `= result`）。
- `completionCondition`: (boolean expression) 条件が満たされたときにMulti-instance bodyを即座に完了できるかどうかを定義します。

#### 4. 実装に必要な設定項目
- **Sequential vs. parallel**: 順次（Sequential）の場合は1つずつ実行され、並列（Parallel）の場合はすべてのインスタンスが同時に作成され、並行して独立して実行されます。
- **Defining the collection to iterate over**: `inputCollection` 式を定義する必要があります。プロセスインスタンスの変数にアクセスすることが一般的です。
- **Collecting the output**: `outputCollection` と `outputElement` 式を定義することで、インスタンスから出力を収集できます。
- **Variable mappings**: 入力および出力の変数マッピングを定義して、インスタンスのスコープ内で新しいローカル変数を作成したり、出力変数を更新したりできます。

#### 5. コード例やXML例
```xml
<bpmn:serviceTask id="task-A" name="A">
  <bpmn:multiInstanceLoopCharacteristics isSequential="true">
    <bpmn:extensionElements>
      <zeebe:loopCharacteristics
          inputCollection="= items" inputElement="item"
          outputCollection="results" outputElement="= result" />
    </bpmn:extensionElements>
    <bpmn:completionCondition xsi:type="bpmn:tFormalExpression">
        = result.isSuccessful
    </bpmn:completionCondition>
  </bpmn:multiInstanceLoopCharacteristics>
</bpmn:serviceTask>
```

#### 6. 制約事項や注意点
- `JobWorker` 実装を持つイベント（Intermediate throw eventsなど）は、このマーカーをサポートしていません。
- `inputCollection` の値が空の場合、Multi-instance bodyは即座に完了し、インスタンスは作成されません。アクティビティがスキップされたように動作します。
- 並列Multi-instanceアクティビティの場合、複数のインスタンスによって変数が変更され、競合状態（race conditions）が発生する可能性があります。変数をローカル変数として定義することで、親やプロセスインスタンスのスコープに伝播されず、インスタンス外から変更できなくなります。

#### 7. 他の要素との関連性
- **Boundary events**: InterruptingおよびNon-interruptingの境界イベントをMulti-instanceアクティビティにアタッチできます。Interruptingイベントがトリガーされると、Multi-instance bodyとすべてのアクティブなインスタンスが終了します。
- **Special multi-instance variables**: 各インスタンスには `loopCounter` というローカル変数があり、`inputCollection` 内のインデックス（1から開始）を保持します。
- **Completion condition properties**: `numberOfInstances`, `numberOfActiveInstances`, `numberOfCompletedInstances`, `numberOfTerminatedInstances` などのプロパティが `completionCondition` 式で使用可能です。


---


### Ad-hoc sub-processes

#### 1. ページタイトルと概要説明
**ページタイトル**: Ad-hoc sub-processes
**概要説明**: 
Ad-hoc sub-processes（アドホックサブプロセス）は、**アドホックマーカー**（**~** チルダ文字で表される）を持つ特別な種類の埋め込みサブプロセス（embedded subprocesses）です。通常のサブプロセスと比較して、内部要素の実行においてより高い柔軟性を提供します。
内部要素は開始イベントや終了イベントに接続されていません。各要素は複数回実行したり、任意の順序で実行したり、スキップしたりすることができます。
要素間に依存関係がある場合は、シーケンスフローで接続して、アドホックサブプロセス内に構造化されたシーケンスを構築することができます。
アドホックサブプロセスは、Zeebeによって内部的に処理されるか、ジョブワーカー（job worker）を使用して処理されます。

#### 2. BPMN要素の定義と用途
アドホックサブプロセスは、実行順序が厳密に定義されていない、または実行時に動的に決定される一連のアクティビティをモデル化するために使用されます。

#### 3. XMLプロパティ・属性の詳細
*   `cancelRemainingInstances`: 完了条件が満たされたときのアドホックサブプロセスの動作に影響を与えるブール属性。
    *   `true`（デフォルト値）に設定されている場合、内部要素の残りのすべてのアクティブなインスタンスが終了し、アドホックサブプロセスが直接完了します。
    *   `false`に設定されている場合、アドホックサブプロセスは完了する前にすべてのアクティブなインスタンスの完了を待ちます。

#### 4. 実装に必要な設定項目
*   **Zeebeによる内部処理（デフォルト）**:
    *   `activeElementsCollection`: 文字列のリストを返す式を定義できます。リスト内の各文字列は、アドホックサブプロセスの内部要素のIDと一致する必要があります。通常、この式は以前に作成され、要素IDのリストを保持するプロセス変数にアクセスします。プロセスインスタンスがアドホックサブプロセスに到達すると、この式を評価し、リストにIDが含まれるすべての要素をアクティブにします。リストが空または式が定義されていない場合、要素はアクティブにならず、アドホックサブプロセスはアクティブなままになります。
    *   `completionCondition`: 内部要素が完了するたびに評価されるオプションのブール式。内部要素の完了後に式が`true`と評価された場合、アドホックサブプロセスは完了し、プロセスインスタンスは出力シーケンスフローに進みます。定義されていない場合、すべてのアクティブ化された要素が完了した後にアドホックサブプロセスが完了します。
*   **ジョブワーカーによる処理**:
    *   タスク定義を持つサブプロセスとして定義します。ジョブワーカーは、内部要素をアクティブにし、いつ完了するかを決定することで、サブプロセスを制御できます。
*   **出力の収集**:
    *   `outputCollection`: 収集された出力を保存する変数名（例：`results`）を定義します。この変数はアドホックサブプロセスのローカル変数として作成され、内部フローが完了するたびに更新されます。アドホックサブプロセスが完了すると、親スコープに伝播されます。
    *   `outputElement`: 内部フローの出力（例：`= result`）を定義します。通常、出力値を保持する内部フローの変数にアクセスします。
*   **変数マッピング**:
    *   **入力変数マッピング**: アドホックサブプロセスのアクティブ化時、および`activeElementsCollection`式の評価前に適用されます。ローカル変数を作成するために使用できます。
    *   **出力変数マッピング**: アドホックサブプロセスの完了時に適用されます。ローカル変数をプロセスインスタンスに伝播するために使用できます。デフォルトでは、ローカル変数は伝播されません。

#### 5. コード例やXML例
```xml
<bpmn:adHocSubProcess id="ad-hoc-subprocess" name="Ad-hoc sub-process" cancelRemainingInstances="false">
  <bpmn:extensionElements>
    <zeebe:adHoc activeElementsCollection="=activeElements" />
  </bpmn:extensionElements>
  ... more contained elements ...
  <bpmn:completionCondition xsi:type="bpmn:tFormalExpression">=myCondition</bpmn:completionCondition>
</bpmn:adHocSubProcess>
```

#### 6. 制約事項や注意点
*   少なくとも1つのアクティビティを持つ必要があります。
*   開始イベントまたは終了イベントを持つことはできません。
*   現在、アドホックサブプロセスがアクティブになった後に要素を動的にアクティブにすることはできず、サブプロセスに入るときにのみ可能です。
*   `activeElementsCollection`の評価結果が文字列のリストでない場合、またはリストに内部要素ID以外の値が含まれている場合、プロセスインスタンスはインシデントを作成します。
*   ジョブワーカーを使用する場合、ワーカーは一度に複数の要素をアクティブにでき、Zeebeは要素が完了するたびにジョブを作成するため、実行中にアドホックサブプロセスのジョブが再作成される可能性があります。一度にアクティブなジョブは1つだけです。ジョブワーカーは以下を想定する必要があります：
    *   処理中にジョブが再作成される可能性があります。
    *   ジョブの完了により`NOT_FOUND`の拒否が発生する可能性があります。
*   `adHocSubProcessElements`変数を更新しないでください。値を変更すると、予期しない動作が発生する可能性があります。

#### 7. 他の要素との関連性
*   **イベントサブプロセス**: イベントサブプロセスはジョブワーカーではなくイベントによってトリガーされるため、ジョブワーカーの直接の制御外で実行できます。イベントサブプロセスが終了すると、ジョブワーカーが再びトリガーされ、制御が戻されるため、新しい要素をアクティブにしたり（オプションで他の要素をキャンセルしたり）、アドホックサブプロセスを完了したりできます。
    *   **中断イベントサブプロセス**: 特別なケースであり、すべてのアクティブな要素をキャンセルし、ジョブワーカーの決定を待たずにアドホックサブプロセスを完了します。
*   **特別なアドホックサブプロセス変数**: アドホックサブプロセスがアクティブになると、そのスコープ内に`adHocSubProcessElements`変数が作成されます。この変数は、サブプロセスとその内部要素に関するメタデータを提供します。ジョブワーカーはこれを使用して、どの要素をアクティブにするかを決定できます。この変数には、アクティブ化可能な要素のリストが含まれており、各要素には`elementId`、`elementName`、`documentation`、`properties`、および`fromAi` FEEL関数を使用して定義された`parameters`が含まれます。


---


### Creating readable process models

* * [Best Practices](/docs/components/best-practices/best-practices-overview/)* Modeling* Creating readable process models
Version: 8.9

On this page

### Creating readable process models

We create visual process models to better understand, discuss, and remember processes. Hence, it is crucial that models are easy to read and understand. The single most important thing is to use well-chosen labels.

#### Essential practices[​](#essential-practices "Direct link to Essential practices")

### Labeling BPMN elements[​](#labeling-bpmn-elements "Direct link to Labeling BPMN elements")

Use [conventions for naming BPMN elements](/docs/components/best-practices/modeling/naming-bpmn-elements/); this will consistently inform the reader of the business semantics. The clarity and meaning of a process is often only as good as its labels.

1

*Start event* labels informs the reader of how the process is *triggered*.

2

An *activity* - labeled as "activity" - informs the reader of the piece of *work* to be *carried out*.

3

*Gateway* labels clarifies based on which condition(s) and along *which sequence flow* the process proceeds.

4

Labeled *boundary events* clearly express in which cases a process execustion might follow an *exceptional path*.

5

Labeled *end events* characterize end *results* of the process from a business perspective.

#### Recommended practices[​](#recommended-practices "Direct link to Recommended practices")

### Modeling symmetrically[​](#modeling-symmetrically "Direct link to Modeling symmetrically")

Try to model symmetrically. Identify related splitting and joining gateways and form easily recognizable *visual*, eventually *nested*, *blocks* with those gateways.

1

The inclusive gateway splits the process flow into two paths which are ...

2

... joined again with an inclusive gateway. Inside that block ...

3

another exclusive gateway splits the process flow into two more paths which are ...

4

... joined again with an exclusive gateway.

By explicitly showing *pairs of gateways* "opening" and "closing" parts of the process diagram, and by positioning such gateway pairs *as symmetrically as possible*, the readability of process model is improved. The reader can easily recognize logical parts of the diagram and quickly jump to those parts the reader is momentarily interested in.

### Modeling from left to right[​](#modeling-from-left-to-right "Direct link to Modeling from left to right")

Model process diagrams *from left to right*. By carefully positioning symbols from left to right, according to the typical point in time at which they occur, one can improve the readability of process models significantly:

Modeling from left to right supports the reading direction (for western audience) and supports the human field of vision - which prefers wide screens.

### Creating readable sequence flows[​](#creating-readable-sequence-flows "Direct link to Creating readable sequence flows")

Consciously decide whether *overlapping sequence flows* make your model more or less readable. On one hand, avoid overlapping sequence flows where the reader will not be able to follow the flow directions anymore. Use overlapping sequence flows where it is less confusing for the reader to observe just one line representing several sequence flows leading to the same target.

Avoid sequence flows *violating the reading direction*, meaning no outgoing flows on the left or incoming flows on the right of a symbol.

1

The author could have made the five (!) sequence flows leading into the end event visible by separating them. However, by consciously choosing to partly overlap those flows, this model becomes less cluttered, therefore less confusing and easier to read.

2

The author could have attached the sequence flow, leaving this task on its left. However, this would have decreased readability, because the flow connection violates the reading direction. The same applies to incoming flows on the right of a symbol.

*Avoid flows crossing each other* and *flows crossing many pools or lanes*, wherever possible. Rearrange the order of lanes and paths to make your sequence flows more readable. Oftentimes, removing lanes can improve readability! Rearrange the order of pools in a collaboration diagram to avoid message flows crossing pools as much as possible. Often, you will find a "natural" order of pools reflecting the order of first involvement of parties in the end-to-end process. This order will often also lead to a minimum of crossing lines.

*Avoid very long (multi page) sequence flows*, especially when flowing against the reading direction. The reader will lose any sense of what such lines actually mean. Instead, use link events to connect points which are not on the same page or screen anymore.

1

You observe a throwing link event here, which...

2

...directly links to a catching link event just as if the sequence flow would have been connected.

Avoid excessive use of link events. The example above serves to show the possible usage, but at the same time, it is too small to satisfy the usage of link events in real-world scenario!

### Modeling explicitly[​](#modeling-explicitly "Direct link to Modeling explicitly")

Make your models easier to understand by modeling *explicitly*, which most often means to either completely avoid certain more "implicit" BPMN constructs, or at least to use them cautiously. Always consider the central *goal of increased readability* and understandability of the model when deciding whether to model explicitly or implicitly. When in doubt, it's best to favor an explicit style.

#### Using gateways instead of conditional flows[​](#using-gateways-instead-of-conditional-flows "Direct link to Using gateways instead of conditional flows")

Model splitting the process flow by always using *gateway symbols* such as ![Inclusive gateway](/img/bpmn-elements/inclusive-gateway.svg) instead of conditional flows ![Conditional flow](/img/bpmn-elements/conditional-flow.svg).

1

For example, you could've left out this inclusive gateway by drawing two outgoing sequence flows directly out of the preceding task **Choose menu** and attaching conditions to those sequence flows (becoming conditional sequence flows ![Conditional flow](/img/bpmn-elements/conditional-flow.svg)). However, experience shows that readers understand the flow semantics of gateways better, which is why we do not make use of this possibility.

#### Modeling start and end events[​](#modeling-start-and-end-events "Direct link to Modeling start and end events")

Model the trigger and the end status of processes by always explicitly showing the *start* and *end event symbols*.

caution

Process models without start and end event cannot be executed on the Camunda workflow engine

1

According to the BPMN standard, you could have left out the start event...

2

...as long as you also leave out the end events of a process. However, you would have lost important information in your model, which is why we do not make use of this syntactical possibility.

Be specific about the *state* you reached with your event from a *business perspective*. Quite typically, you will reach "success" and "failure" like events from a business perspective:

1

'Invoice paid' better qualifies the "successful" business state than e.g. 'Invoice processed' would...

2

...because in principle, you can call the failed state 'Invoice processed', too, but the reader of the diagram is much better informed by calling it 'Invoice rejected'.

#### Separating splitting and joining gateways[​](#separating-splitting-and-joining-gateways "Direct link to Separating splitting and joining gateways")

In general, avoid mixing up the split and join semantics of gateways by explicitly showing *two separate symbols*:

1

You could have modeled this join implicitly by leaving out the explicitly joining XOR gateway and directly connecting two incoming sequence flows to...

2

...the subsequent splitting XOR gateway. Of course, BPMN would allow this for other gateway types, too. However, experience shows that readers will often overlook the join semantics of such gateways serving two purposes at the same time.

The fact that readers will often overlook the join semantics of gateways serving to join as well as split the process flow at the same time, combined with the preference for [modeling symmetrically](#modeling-symmetrically), leads us to prefer *splitting and joining gateways modeled with separate symbols*.

However, there are cases in which the readability of models can be improved with *implicit modeling*. Consider the following example:

1

The two incoming sequence flows to the task "Review tweet" could be merged with an XOR gateway, following explicit modeling. We argue that a merging XOR gateway directly behind the start event decreases the readability. A merging XOR gateway is a passive element and the reader expects the process to continue with an active element after the start event.

#### Using XOR gateway markers[​](#using-xor-gateway-markers "Direct link to Using XOR gateway markers")

Model the XOR gateway by explicitly showing the **X** symbol, even if some tools allow to draw a blank gateway.

1

You could have shown the splitting gateway...

2

...as well as the joining gateway without the **X** symbol indicating that it is an exclusive gateway.

The **X** marker makes a clearer difference to the other gateway types (inclusive, parallel, event-based, complex) which leads us to prefer *explicit XOR gateway markers* in general.

#### Splitting sequence flows with parallel gateways[​](#splitting-sequence-flows-with-parallel-gateways "Direct link to Splitting sequence flows with parallel gateways")

Always model splitting the process flow by explicitly showing the *gateway symbol*:

1

You could have modeled this parallel split implicitly by leaving out the gateway and drawing two outgoing sequence flows out of the preceding task **Choose menu**. However, the reader needs deeper BPMN knowledge in order to understand this model. Additionally, for joining the parallel flows...

2

...you will always need the explicit symbol.

The fact that readers of models using parallelization will likely need to understand the semantics of a parallel join combined with the preference for modeling symmetrically leads us to prefer *explicit parallel gateways*, too.

#### Joining sequence flows with XOR gateways[​](#joining-sequence-flows-with-xor-gateways "Direct link to Joining sequence flows with XOR gateways")

Model joining the process flow by explicitly showing the *XOR gateway symbol* so the reader does not have to know BPMN details to understand how two incoming or outgoing sequence flows in a task behave. Additionally, this often supports the [symmetry of the model](#modeling-symmetrically) by explicitly showing a "relationship" of the splitting and joining *gateways forming a visual "block"*.

1

You could have modeled this join implicitly by leaving out the gateway and directly connecting the two incoming sequence flows to the subsequent task **Have lunch**. However, explicitly modeling the join better visualizes a block, the joining gateway semantically "belongs" to...

2

...the earlier split. In case the reader is not interested in the details of dinner preparation but just in having dinner, it's easy to "jump" to the gateway, "closing" that logical part of the model.

This is particularly helpful for models bigger than that example with many such (eventually nested) blocks. Consider the following model, showing two *nested blocks* of gateways:

1

Now, you couldn't have modeled this join implicitly, because it's directly followed by an inclusive gateway with very different join semantics. *Consistency* of joining techniques is another reason why we prefer explicitly joining sequence flows in general.

There are always exceptions to the rule! There are cases in which the readability of models can be *improved* with *implicit modeling*. So don't be dogmatic about explicit modeling; always aim for the most readable model. The following example shows a case of a model in which splitting and joining points do not form natural "blocks" anyway. In such cases, it can be preferable to make use of *implicit joining* to improve the overall readability!

### Avoiding lanes[​](#avoiding-lanes "Direct link to Avoiding lanes")

Consider *avoiding lanes* for most of your models all together. They tend to conflict with several of the best practices presented here, like [Modeling *Symmetrically*](#modeling-symmetrically), [Emphasizing the *Happy Path*](#emphasizing-the-happy-path) and [Creating Readable *Sequence Flows*](#creating-readable-sequence-flows). Apart from readability concerns, our experience also shows that lanes make it more difficult to change the resulting process models and therefore cause considerably *more effort in maintenance*.

When modeling on an *operational level*, where showing the responsibility of roles matters most, we recommend to [use *collaboration diagrams*](#using-collaboration-diagrams) with several *separate pools* for the process participants instead of lanes.

However, the usage of lanes might be meaningful for:

* *Strategic* level models (refer to [BPMN Tutorial](https://camunda.com/bpmn/) and [Real-Life BPMN](https://www.amazon.com/Real-Life-BPMN-4th-introduction-DMN/dp/1086302095/) on details for modeling levels) - especially when they have a focus on *responsibilities and their borders*.
* *Technical/executable* models with a focus on *human work-flow* and its ongoing "ping pong" between several participants.

For these cases, also consider alternative methods to maintain and show roles:

* As a *visible part* of the *task name*, e.g. in between squared brackets []: *"Review tweet [Boss]"*.

Camunda 7 Only

During execution you can remove this part of the task name if you like by using simple mechanisms like shown in the [Task Name Beautifier](https://github.com/camunda/camunda-consulting/tree/master/snippets/task-name-beautifier) so it does not clutter your tasklist.

* As a *text annotation* or a *custom artifact*

note

Roles are part of your executable BPMN process model as *technical attributes* anyway - even if hidden in the BPMN diagram. For example, they can be used during execution for assignment at runtime.

#### Helpful practices[​](#helpful-practices "Direct link to Helpful practices")

### Emphasizing the happy path[​](#emphasizing-the-happy-path "Direct link to Emphasizing the happy path")

You may want to emphasize the *"happy path"* leading to the delivery of a successful process result by placing the tasks, events, and gateways belonging to the happy path on a straight sequence flow in the center of your diagram - at least as often as possible.

The *five* BPMN symbols belonging to the happy path are put on a straight sequence flow in the center of the diagram.

### Avoid modeling retry behavior[​](#avoid-modeling-retry-behavior "Direct link to Avoid modeling retry behavior")

A common idea is to model retry behavior into your process models. This *should be avoided* in general. The following process model shows a typical example of this anti pattern:

All operations use cases put into the model can be handled via Camunda tooling, e.g. by [retrying](/docs/components/concepts/job-workers/#completing-or-failing-jobs) or [Camunda Operate](/docs/components/operate/operate-introduction/).

### Using collaboration diagrams[​](#using-collaboration-diagrams "Direct link to Using collaboration diagrams")

If you model on an operational level (refer to [BPMN Tutorial](https://camunda.com/bpmn/) and [Real-Life BPMN](https://www.amazon.com/Real-Life-BPMN-4th-introduction-DMN/dp/1086302095/) on details for modeling levels) use *collaboration diagrams* with several *separate pools* for the process participants [instead of lanes](#avoiding-lanes) as operational models using lanes make it very hard for the individual process participant to identify the details of their process involvement.

Furthermore, model just *one coherent process per pool* (apart from event subprocesses, of course), even though BPMN in principle allows several processes per pool. This improves readability by constituting a clear visual border around every process and by providing a natural space for labeling that part of the end-to-end process in the pool's header.

1

The Team Assistance is responsible for initial "Invoice Collection" as well as "Invoice Clarification" - if applicable. Those two processes are modeled by using two separate pools for the team assistance, just as...

2

...the approver can observe the "Invoice Approval" process in a separate pool and...

3

...the managing director can observe the "Invoice Payment" process in a separate pool while the collaboration diagram as a whole shows the business analyst that the overall end-to-end process works.

Using *collaboration diagrams* with *separate pools* for the process participants allows to explicitly show interaction and communication between them by means of message flow and further improves readability by transparently showing the participants their own involvement in the end-to-end-process. As a consequence, they do not need to fully read and understand the end-to-end process in order to read, understand, and agree to their own involvement by looking at their own pools.

### Showing interaction with systems[​](#showing-interaction-with-systems "Direct link to Showing interaction with systems")

Consciously decide how you want to model systems the process participants are interacting with. Use *data stores* to show systems which primarily serve as a means to store and retrieve data. Use - depending on your needs *collapsed* or *expanded* - *pools* for systems which are carrying out crucial activities in the process going way beyond storing and retrieving data.

1

A *collapsed pool* is used to represent a system which supports the process and/or carries out process tasks on its own. The pool could be expanded later to model the internal system details, maybe even with the goal to execute a technical process flow directly with a BPMN capable process engine.

2

A *data store* is used to represent a technical container meant to archive PDFs and store them for later retrieval.

3

Another *data store* is used to represent a container which could be a physical storage place for paper invoices to be paid at the moment but could become a representation for business objects in a database with the object state "to be paid" in the future.

When *choosing* between those *two options* for modeling systems (data stores, collapsed pools) keep in mind that only pools represent processes and therefore have the capability to be expanded and modeled in all their internal details later on.

### Avoiding excessive usage of data objects[​](#avoiding-excessive-usage-of-data-objects "Direct link to Avoiding excessive usage of data objects")

Avoid excessive use of *data objects*, but use them cautiously to show the *most important data related aspects* of your process.

Experience shows that many data objects and especially many data associations quickly clutter your process model and that visual noise reduces readability - especially for less experienced readers.

You might find three practices helpful to find your own "right" amount of data visualization:

1

Cautiously use data objects and associations to show the *most important data related aspects* of your process. We could have modeled that all the tasks in the "Payments Creation" process either read, update, or delete the "new payment", however we decided that we just want to point out that the process works on a new payment object.

2

Use data stores for *coupling processes via data*. We could have modeled a lot of other tasks in the process that either read or update the "payments", however, we decided to just point out the most important aspect for the process diagram, which is that the "Payments Creation" process of delivery service is loosely coupled with the "Payments Processing" via commonly shared data.

3

Here we decided that it's helpful to know that this message does not only inform an adjustment possibility was checked, but that it also delivers all the necessary details of the adjustment.

### Avoiding changes to symbol size and color[​](#avoiding-changes-to-symbol-size-and-color "Direct link to Avoiding changes to symbol size and color")

Leave the *size of symbols as it is* by default. For example, different sizes of tasks or events suggest that the bigger symbol is more important than the smaller one - an often unwarranted assumption. Instead of writing long labels, use short and consistent labels in line with your [naming conventions](/docs/components/best-practices/modeling/naming-bpmn-elements/) and move all additional information into BPMN annotations associated to your specific BPMN element.

Furthermore, avoid *excessive use of colors*. Experience shows that colors are visually very strong instruments and psychologically very suggestive, but will typically suggest different things to different readers. Additionally, a colorful model often looks less professional.

However, there are valid exceptions. For example, you could mark the *happy path* through a process with a visually weak coloring:

Another case for useful coloring might be to make a visual difference between *human* and *technical flows* within a bigger collaboration diagram by coloring the header bar on the left side of the pools.

**Was this helpful?**

**Tags:**

* [BPMN](/docs/tags/bpmn/)

[Edit this page](https://github.com/camunda/camunda-docs/edit/main/versioned_docs/version-8.9/components/best-practices/modeling/creating-readable-process-models.md)

[Previous

Local development with element templates and Camunda 8 Run](/docs/components/best-practices/development/local-development-with-element-templates/)[Next

Naming BPMN elements](/docs/components/best-practices/modeling/naming-bpmn-elements/)

* [Essential practices](#essential-practices)
  + [Labeling BPMN elements](#labeling-bpmn-elements)* [Recommended practices](#recommended-practices)
    + [Modeling symmetrically](#modeling-symmetrically)+ [Modeling from left to right](#modeling-from-left-to-right)+ [Creating readable sequence flows](#creating-readable-sequence-flows)+ [Modeling explicitly](#modeling-explicitly)+ [Avoiding lanes](#avoiding-lanes)* [Helpful practices](#helpful-practices)
      + [Emphasizing the happy path](#emphasizing-the-happy-path)+ [Avoid modeling retry behavior](#avoid-modeling-retry-behavior)+ [Using collaboration diagrams](#using-collaboration-diagrams)+ [Showing interaction with systems](#showing-interaction-with-systems)+ [Avoiding excessive usage of data objects](#avoiding-excessive-usage-of-data-objects)+ [Avoiding changes to symbol size and color](#avoiding-changes-to-symbol-size-and-color)

---


### Design a process using BPMN

#### 概要説明
Business Process Model and Notation (BPMN) はプロセスモデリングのグローバルスタンダードです。導入しやすい視覚的なモデリング言語であるBPMNとCamundaを組み合わせることで、ビジネスプロセスを自動化できます。

プロセスは、独立したタスクに基づいて組織がどのように機能するかを決定するアルゴリズムです。成功するビジネスは、実証済みの効果的なプロセスから成長します。したがって、Camundaのワークフローエンジンは、BPMNで定義されたプロセスを実行し、これらのプロセスがダイアグラム内で迅速にオーケストレーションされることを保証します。

BPMNは、経験豊富なエンジニアとビジネス関係者の両方が理解できる方法で、重要なビジネスプロセスに対する制御と可視性を提供します。ワークフローエンジンは、API、マイクロサービス、ビジネス上の意思決定とルール、人間の作業、IoTデバイス、RPAボットなど、さまざまな要素にまたがるプロセスをオーケストレーションします。

#### BPMN要素の定義と用途
BPMNダイアグラムは、以下のようないくつかの要素を使用して構築できます：

*   **Events (イベント)**: 発生する事象。例えば、プロセスを開始および終了する開始イベント(Start events)と終了イベント(End events)。
*   **Tasks (タスク)**: 例えば、特定のユーザーが完了するためのユーザータスク(User tasks)や、さまざまなWebサービスを呼び出すためのサービスタスク(Service tasks)。
*   **Gateways (ゲートウェイ)**: 例えば、同時に2つのタスク間でプロセスを進める並列ゲートウェイ(Parallel gateways)。
    *   プロセスインスタンスのデータを反映するために**変数(variables)**を利用します。
    *   変数にアクセスし、その値を計算するために**式(expressions)**を活用します。
*   **Subprocesses (サブプロセス)**: 例えば、複数のアクティビティを1つのトランザクションにグループ化するために使用できるトランザクションサブプロセス(Transaction subprocess)。

#### 実装に必要な設定項目 / BPMN in action
BPMNダイアグラムを構築する手順の例（ケーキを焼くプロセス）：

1.  ダイアグラム上に、円の形をした開始イベントが配置されています。要素をクリックし、**Change element** メニューアイコンを選択します。ここでは開始イベントのままにします。円をダブルクリックしてテキストを追加します。
2.  矢印を最初のタスク（長方形の図形）にドラッグ＆ドロップするか、開始イベントをクリックしてからタスク要素をクリックして自動的に接続します。
3.  要素をクリックし、**Change element** メニューアイコンを選択して、タイプをユーザータスクに変更し、「Purchase Ingredients（材料の購入）」という名前を付けます。追加された各要素には調整可能な属性があることに注意してください。ページの右側にあるプロパティパネルを使用して、これらの属性を調整します。
4.  ユーザータスクをクリックして、ゲートウェイを接続します。要素をクリックし、**Change element** メニューアイコンを選択して並列ゲートウェイとして宣言することで、同時に発生する可能性のある2つのタスク（材料を混ぜる、オーブンを予熱する）に接続できます。
5.  これら2つのタスクが完了したら、次のゲートウェイを接続して先に進みます。
6.  ケーキを焼くユーザータスクを追加し、最後にケーキにアイシングをするユーザータスクを追加します。
7.  太い円で表される終了イベントを追加します。
8.  保存する必要はありません。Web Modelerは加えたすべての変更を自動保存します。

#### 制約事項や注意点
*   Web Modelerを使用してBPMNダイアグラムをインポートすることもできます。
*   ダイアグラムを変更して自動保存されても、クラスターには影響しません。ダイアグラムをデプロイすると、選択したクラスターで利用可能になり、新しいインスタンスを開始できるようになります。
*   変数はプロセスインスタンスの一部であり、インスタンスのデータを表します。

#### 他の要素との関連性
*   **Operate**: 完了したプロセスダイアグラムをデプロイして実行した後、Operateでインスタンスを監視できます。
*   **Tasklist**: BPMNダイアグラムで必要なユーザータスクの進行中のリストを確認できます。

*(注: このページは入門的な概要ページであるため、XMLプロパティ・属性の詳細やコード例・XML例は含まれていません。)*


---


### Data flow

#### 概要説明
すべてのBPMNプロセスインスタンスは、1つ以上の変数を持つことができます。
変数はキーと値のペアであり、ジョブワーカーが作業を行うため、またはどのシーケンスフローを選択するかを決定するために必要なプロセスインスタンスのコンテキストデータを保持します。変数は、プロセスインスタンスの作成時、ジョブの完了時、およびメッセージの相関時に提供できます。

#### ジョブワーカー (Job workers)
デフォルトでは、ジョブワーカーはプロセスインスタンスのすべての変数を取得します。必要な変数のリストを **fetchVariables** として提供することで、データを制限できます。
ワーカーは変数を使用して作業を行います。作業が完了すると、ジョブを完了します。作業の結果が後続のタスクで必要な場合、ワーカーはジョブを完了する際に変数を設定します。これらの変数はプロセスインスタンスにマージされます。

入力マッピングと出力マッピング：
ジョブワーカーが異なる形式や異なる名前で変数を期待する場合、プロセスで **入力マッピング (input mappings)** を定義することで変数を変換できます。**出力マッピング (output mappings)** は、ジョブ変数をプロセスインスタンスにマージする前に変換するために使用できます。

#### 変数スコープとトークンベースのデータ (Variable scopes vs. token-based data)
プロセスは並行パスを持つことができます（例：並列ゲートウェイを使用する場合）。実行が並列ゲートウェイに到達すると、新しいトークンが作成され、後続のパスが並行して実行されます。
変数はトークンではなくプロセスインスタンスの一部であるため、どのトークンからでもグローバルに読み取ることができます。あるトークンが変数を追加したり、変数の値を変更したりした場合、その変更は並行するトークンからも見えます。
変数の可視性は、プロセスの **変数スコープ (variable scopes)** によって定義されます。

#### 並行処理に関する考慮事項 (Concurrency considerations)
プロセスインスタンス内に複数のアクティブなアクティビティが存在する場合（つまり、並列ゲートウェイの使用、複数の送信シーケンスフロー、または並列マルチインスタンスマーカーのような並行実行の形式がある場合）、変数の扱いに特別な注意を払う必要があるかもしれません。あるアクティビティによって変数が変更されると、同時に別のアクティビティによってアクセスされ、変更される可能性があります。このようなプロセスでは競合状態 (Race conditions) が発生する可能性があります。

並列フローで変数を書き込む際には注意することをお勧めします。変数マッピングを使用して変数が正しい変数スコープに書き込まれることを確認し、ジョブの完了やメッセージの公開は必要最小限の変数のみで行うようにしてください。

これらの種類の問題は、以下の方法で回避できます：
* 更新された変数のみを渡す
* 出力変数マッピングを使用して変数の伝播をカスタマイズする
* 埋め込みサブプロセスと入力変数マッピングを使用して、変数の可視性と伝播を制限する

#### 関連要素
* Job handling
* Variables
* Input/output variable mappings
* Variable scopes


---


* * [BPMN, DMN, and FEEL](/docs/components/concepts/bpmn-dmn-feel/)* BPMN* Tasks* Overview
Version: 8.9

### Overview

The basic elements of BPMN processes are tasks; these are atomic units of work composed to create a meaningful result. Whenever a token reaches a task, the token stops and Zeebe creates a job and notifies a registered worker to perform work. When that handler signals completion, the token continues on the outgoing sequence flow.

Choosing the granularity of a task is up to the person modeling the process. For example, the activity of processing an order can be modeled as a single *Process Order* task, or as three individual tasks *Collect Money*, *Fetch Items*, *Ship Parcel*. If you use Zeebe to orchestrate microservices, one task can represent one microservice invocation.

Currently supported elements:

* [Service tasks](/docs/components/modeler/bpmn/service-tasks/)
* [User tasks](/docs/components/modeler/bpmn/user-tasks/)
* [Receive tasks](/docs/components/modeler/bpmn/receive-tasks/)
* [Business rule tasks](/docs/components/modeler/bpmn/business-rule-tasks/)
* [Script tasks](/docs/components/modeler/bpmn/script-tasks/)
* [Send tasks](/docs/components/modeler/bpmn/send-tasks/)
* [Manual tasks](/docs/components/modeler/bpmn/manual-tasks/)
* [Undefined tasks](/docs/components/modeler/bpmn/undefined-tasks/)

**Was this helpful?**

[Edit this page](https://github.com/camunda/camunda-docs/edit/main/versioned_docs/version-8.9/components/modeler/bpmn/tasks.md)

---



---


### Service Tasks

#### 1. ページタイトルと概要説明
- **ページタイトル**: Service tasks | Camunda 8 Docs
- **概要説明**: Service taskは、特定のタイプを持つプロセス内の作業項目（work item）を表します。Service taskに入ると、対応するジョブが作成されます。プロセスインスタンスはここで停止し、ジョブが完了するまで待機します。ジョブワーカー（job worker）はジョブタイプをサブスクライブし、ジョブを処理して、Zeebeクライアントのいずれかを使用して完了させることができます。ジョブが完了すると、Service taskが完了し、プロセスインスタンスが続行されます。

#### 2. BPMN要素の定義と用途
- **定義**: プロセス内の特定のタイプの作業項目を表すBPMN要素。
- **用途**: 外部システムとの連携や、カスタムロジックの実行など、ジョブワーカーによって処理されるタスクを定義するために使用されます。

#### 3. XMLプロパティ・属性の詳細
Service taskは `taskDefinition` を持つ必要があります。これは、どのジョブワーカーがService taskの作業を処理するかを指定するために使用されます。

`taskDefinition` は以下のプロパティを指定します：
- **`type`** (必須):
  - **型**: String
  - **用途**: どのジョブワーカーがそれぞれのService taskジョブを要求するかを指定するための参照として使用されます（例: `order-items`）。
  - **設定方法**: 任意の静的値（例: `myType`）として指定するか、`=` をプレフィックスとするFEEL式（任意のFEEL文字列に評価されるもの）として指定できます（例: `= "order-" + priorityGroup`）。
- **`retries`** (任意):
  - **型**: Number
  - **用途**: ワーカーが失敗をシグナルしたときにジョブが再試行される回数を指定します。
  - **デフォルト値**: 3

※ 式はService taskのアクティブ化時に評価され、ジョブタイプの場合は `string`、再試行回数の場合は `number` になる必要があります。

#### 4. 実装に必要な設定項目
- **Task headers**: Service taskは任意の数の `taskHeaders` を定義できます。これらはジョブとともにワーカーに渡される静的なメタデータです。ヘッダーはワーカーの設定パラメータとして使用できます。
- **Variable mappings**: デフォルトでは、すべてのジョブ変数はプロセスインスタンスにマージされます。この動作は、Service taskで出力マッピング（output mapping）を定義することでカスタマイズできます。入力マッピング（input mapping）は、変数をジョブワーカーが受け入れる形式に変換するために使用できます。

#### 5. コード例やXML例
カスタムヘッダーを持つService taskのXML表現の例：

```xml
<bpmn:serviceTask id="collect-money" name="Collect Money">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="payment-service" retries="5" />
    <zeebe:taskHeaders>
      <zeebe:header key="method" value="VISA" />
    </zeebe:taskHeaders>
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

#### 6. 制約事項や注意点
- Service taskは必ず `taskDefinition` を持つ必要があります。
- `type` プロパティは必須です。
- `type` や `retries` にFEEL式を使用する場合、評価結果はそれぞれ `string` と `number` になる必要があります。

#### 7. 他の要素との関連性
- **Job workers**: Service taskの実際の処理はジョブワーカーによって行われます。
- **Variable mappings**: 入出力変数のマッピングを使用して、プロセスインスタンスとジョブワーカー間でデータをやり取りします。
- **Incidents**: ジョブの処理中にエラーが発生し、再試行回数が尽きた場合などにインシデントが発生する可能性があります。


---


### User tasks

#### 1. ページタイトルと概要説明
- **ページタイトル**: User tasks | Camunda 8 Docs
- **概要説明**: ユーザータスクは、人間の作業が必要で、ワークフローエンジンやソフトウェアアプリケーションによって支援される作業をモデル化するために使用されます。これは、外部ツールの支援を受けないマニュアルタスクとは異なります。プロセスインスタンスがユーザータスクに到達すると、Zeebeで新しいユーザータスクインスタンスが作成され、プロセスインスタンスは停止してユーザータスクインスタンスが完了するまで待機します。完了すると、プロセスインスタンスは続行されます。

#### 2. BPMN要素の定義と用途
- **Camunda user task**: デフォルトのユーザータスク実装タイプで、`zeebe:userTask`拡張要素を使用します。Camunda 8.6で導入された推奨される実装タイプです。アサインメント、スケジューリング、タスクの更新、変数マッピング、およびフォームをサポートします。
- **Job worker implementation**: `zeebe:userTask`拡張要素を削除することで、ジョブワーカーを使用してユーザータスクを実装することもできます。ただし、この方法は非推奨（deprecated）であり、APIの互換性やライフサイクル管理の面で制限があります。

#### 3. XMLプロパティ・属性の詳細
- **zeebe:AssignmentDefinition**: タスクを割り当てるユーザーを定義します。
  - `assignee`: タスクに割り当てられるユーザーを指定します。Tasklistはこのユーザーのためにタスクを要求します。
  - `candidateUsers`: タスクを割り当てることができるユーザーを指定します。
  - `candidateGroups`: タスクを割り当てることができるユーザーのグループを指定します。
- **zeebe:taskSchedule**: ユーザーがタスクと対話するタイミングを定義します。
  - `dueDate`: ユーザータスクの期限を指定します。
  - `followUpDate`: ユーザータスクのフォローアップ日を指定します。
- **zeebe:priorityDefinition**: ユーザータスクの優先度を指定します。
  - `priority`: 0から100までの整数。デフォルト値は50。値が大きいほど重要度が高いことを示します。
- **zeebe:formDefinition**: フォーム参照を定義します。
  - `formId`: Camunda FormのIDを指定します。
  - `bindingType`: リンクされたフォームのどのバージョンを使用するかを決定します（`latest`, `deployment`, `versionTag`）。デフォルトは`latest`。
  - `versionTag`: `bindingType`が`versionTag`の場合に指定します。
  - `externalReference`: カスタムフォーム参照の場合に使用します。
  - `formKey`: ジョブワーカー実装の場合に、`externalReference`の代わりに使用します。
- **zeebe:taskListeners**: ユーザータスクのライフサイクルイベントに反応するためのリスナーを定義します。
  - `eventType` (必須): リスナーをトリガーするイベント（`creating`, `assigning`, `updating`, `completing`, `canceling`）。
  - `type` (必須): リスナーのタイプ。
  - `retries` (任意): ユーザータスクリスナージョブの再試行回数（デフォルトは3）。

#### 4. 実装に必要な設定項目
- **アサインメント**: `assignee`, `candidateUsers`, `candidateGroups`は静的な値または式（例: `= book.author`）として定義できます。Tasklistでタスクを要求するには、`assignee`の値がユーザーの一意の識別子（メールアドレスやユーザー名など）である必要があります。
- **スケジューリング**: `dueDate`と`followUpDate`は静的な値（ISO 8601形式）または式として定義できます。
- **優先度**: 静的な整数値または式として設定できます。
- **変数マッピング**: デフォルトではすべての変数がプロセスインスタンスにマージされますが、出力マッピングを定義することでカスタマイズできます。入力マッピングを使用して変数を別の形式に変換することもできます。
- **フォーム**: Camunda Formsを使用するか、カスタムフォームを使用できます。Camunda FormsはTasklistで表示するか、カスタムアプリケーションで処理できます。

#### 5. コード例やXML例
**Camunda Formをリンクしたユーザータスク（デフォルト）:**
```xml
<bpmn:userTask id="configure" name="Configure">
  <bpmn:extensionElements>
    <zeebe:formDefinition formId="configure-control-process" />
    <zeebe:assignmentDefinition assignee="= default_controller"
                                candidateGroups="controllers, auditors" />
    <zeebe:taskSchedule dueDate="= task_finished_deadline"
                        followUpDate="= now() + duration(&#34;P12D&#34;)" />
    <zeebe:userTask />
  </bpmn:extensionElements>
</bpmn:userTask>
```

**カスタムフォーム参照を持つユーザータスク:**
```xml
<bpmn:userTask id="configure" name="Configure">
  <bpmn:extensionElements>
    <zeebe:formDefinition externalReference="custom-key" />
    <zeebe:userTask />
  </bpmn:extensionElements>
</bpmn:userTask>
```

**ユーザータスクリスナーを設定したユーザータスク:**
```xml
<bpmn:userTask id="configure" name="Configure">
  <bpmn:extensionElements>
    <zeebe:taskListeners>
      <zeebe:taskListener eventType="assigning" type="assigning-user-task-listener" retries="5" />
      <zeebe:taskListener eventType="completing" type="completing-user-task-listener" />
    </zeebe:taskListeners>
    <zeebe:userTask/>
  </bpmn:extensionElements>
</bpmn:userTask>
```

#### 6. 制約事項や注意点
- **大文字小文字の区別**: Orchestration Clusterのユーザー名とグループIDはケースセンシティブです。
- **Tasklist V2の制限**: Tasklist V2では、`candidateUsers`と`candidateGroups`はタスクの可視性や割り当てのために評価されません。プロセス定義レベルの認可ベースのアクセス制御に依存します。
- **ジョブワーカー実装の制限**: ジョブワーカーを使用したユーザータスクの実装は非推奨です。Orchestration Cluster REST APIを使用して管理できず、ライフサイクル管理やメトリクス・レポート機能が制限されます。

#### 7. 他の要素との関連性
- **マニュアルタスク**: 外部ツールの支援を受けない点でユーザータスクと異なります。
- **サービスタスク**: ジョブワーカー実装のユーザータスクはサービスタスクと同様に動作しますが、視覚的なマーカーとプロセスモデルにおける意味合いが異なります。
- **Camunda Forms**: ユーザータスクはCamunda Formsと連携して、ユーザーに作業指示を提供し、構造化された情報を取得できます。


---


### Receive Tasks

#### 概要説明
Receive tasks reference a message; these are used to wait until a proper message is received.
When a receive task is entered, a corresponding message subscription is created. The process instance stops at this point and waits until the message is correlated.
A message can be published using one of the Zeebe clients. When the message is correlated, the receive task is completed and the process instance continues.

#### BPMN要素の定義と用途
Receive tasks are used to wait for a message. They reference a message definition.

#### XMLプロパティ・属性の詳細
- `messageRef`: 参照するメッセージのIDを指定します。
- `name` (Message): メッセージの名前。静的な値（例: `order canceled`）または式（例: `= "order " + awaitingAction`）として定義できます。式は文字列を返す必要があります。
- `correlationKey` (Message Subscription): メッセージの相関キーを保持するプロセスインスタンスの変数にアクセスする式。文字列または数値を返す必要があります。

#### 実装に必要な設定項目
- メッセージの名前（Name）
- 相関キー（Correlation Key）

#### コード例やXML例
```xml
<bpmn:message id="Message_1iz5qtq" name="Money collected">
  <bpmn:extensionElements>
    <zeebe:subscription correlationKey="=orderId" />
  </bpmn:extensionElements>
</bpmn:message>
<bpmn:receiveTask id="money-collected" name="Money collected" messageRef="Message_1iz5qtq">
</bpmn:receiveTask>
```

#### 制約事項や注意点
- An alternative to receive tasks is a message intermediate catch event, which behaves the same way but can be used together with event-based gateways.
- The `correlationKey` expression is evaluated on activating the receive task and must result either in a `string` or `number`.
- The message name expression is evaluated on activating the receive task and must result in a `string`.

#### 他の要素との関連性
- Message correlation
- Expressions
- Variable mappings
- Incidents
- Message intermediate catch event (alternative)


---


### Business rule tasks

#### 概要説明
ビジネスルールタスク（Business rule task）は、ビジネスルールの評価をモデル化するために使用されます。例えば、Decision Model and Notation (DMN) でモデル化されたディシジョンの評価などです。

#### BPMN要素の定義と用途
プロセスインスタンスがビジネスルールタスクに到達すると、内部のDMNディシジョンエンジンを使用してディシジョンが評価されます。ディシジョンが下されると、プロセスインスタンスは続行されます。
ディシジョンの評価が失敗した場合、ビジネスルールタスクでインシデント（incident）が発生します。インシデントが解決されると、ディシジョンは再度評価されます。

Camunda 8では、ビジネスルールタスクの代替タスク実装（ジョブワーカー実装）もサポートされています。DMNディシジョンを評価するだけでなく、ジョブワーカーを使用してビジネスルールタスクを実装することも可能です。

#### 実装に必要な設定項目とXMLプロパティ・属性の詳細

### Called Decision (DMNディシジョンの呼び出し)
呼び出されるディシジョン（called decision）は、ビジネスルールタスクをDMNディシジョン（ディシジョンテーブルまたはディシジョンリテラル式）にリンクします。これは `zeebe:calledDecision` 拡張要素を使用して定義されます。

*   **decisionId** (必須): 呼び出されるディシジョンのDMNディシジョンID。通常は静的な値（例: `shipping_box_size`）として定義されますが、式（例: `= "shipping_box_size_" + countryCode`）として定義することもできます。式は、入力マッピングが適用された後、ビジネスルールタスクがアクティブ化されたとき（またはインシデントが解決されたとき）に評価されます。式の結果は `string` である必要があります。
*   **bindingType** (任意): 評価される呼び出し先ディシジョンのバージョンを決定します。指定されていない場合、デフォルトで `latest` が使用されます。
    *   `latest`: ビジネスルールタスクがアクティブ化された時点での最新のデプロイ済みバージョン。
    *   `deployment`: プロセスの現在実行中のバージョンと一緒にデプロイされたバージョン。
    *   `versionTag`: `versionTag` 属性で指定されたバージョンタグが注釈された最新のデプロイ済みバージョン。
*   **versionTag** (条件付き必須): `bindingType` が `versionTag` の場合に指定します。
*   **resultVariable** (必須): ディシジョン結果のプロセス変数名。ディシジョンの結果はこの変数に保存されます。静的な値として定義されます。デフォルトでは、この変数はプロセスインスタンスにマージされます。この動作は、出力マッピングを定義することでカスタマイズできます。

### Job Worker Implementation (ジョブワーカー実装)
ビジネスルールタスクは、DMNでモデル化されたディシジョンを評価する代わりに、ジョブワーカーを使用して実装することもできます。これは `zeebe:taskDefinition` 拡張要素を使用して定義されます。
ジョブワーカー実装を持つビジネスルールタスクは、サービスタスクとまったく同じように動作します。違いは、視覚的な表現（タスクマーカー）とモデルのセマンティクスです。

*   **type** (必須): ジョブタイプ。サービスタスクと同様に定義します。静的な値（`myType`）またはFEEL式（例: `= "order-" + priorityGroup`）として指定できます。
*   **zeebe:taskHeaders** (任意): ジョブワーカーに静的パラメータ（例: 評価するディシジョンのキー）を渡すために使用します。

#### 変数マッピング (Variable Mappings)
ビジネスルールタスクのスコープ内にあるすべての変数は、ディシジョンが評価されるときにディシジョンエンジンで利用可能です。入力マッピングを使用して、変数をディシジョンが受け入れる形式に変換できます。
入力マッピングは、ディシジョン評価の前に、ビジネスルールタスクをアクティブ化するとき（またはインシデントが解決されたとき）に適用されます。

ジョブワーカー実装の場合も、サービスタスクと同じように変数マッピングを定義して、ジョブワーカーに渡される変数を変換したり、ジョブの変数がどのようにマージされるかをカスタマイズしたりできます。

#### コード例やXML例

**バインディングタイプを指定しない（暗黙的に `latest` が使用される）場合:**
```xml
<bpmn:businessRuleTask id="determine-box-size" name="Determine shipping box size">
  <bpmn:extensionElements>
    <zeebe:calledDecision decisionId="shipping_box_size" resultVariable="boxSize" />
  </bpmn:extensionElements>
</bpmn:businessRuleTask>
```

**`deployment` バインディングタイプを使用する場合:**
```xml
<bpmn:businessRuleTask id="determine-box-size" name="Determine shipping box size">
  <bpmn:extensionElements>
    <zeebe:calledDecision decisionId="shipping_box_size" bindingType="deployment"
                          resultVariable="boxSize" />
  </bpmn:extensionElements>
</bpmn:businessRuleTask>
```

**`versionTag` バインディングタイプを使用する場合:**
```xml
<bpmn:businessRuleTask id="determine-box-size" name="Determine shipping box size">
  <bpmn:extensionElements>
    <zeebe:calledDecision decisionId="shipping_box_size"
                          bindingType="versionTag" versionTag="v1.0"
                          resultVariable="boxSize" />
  </bpmn:extensionElements>
</bpmn:businessRuleTask>
```

**ジョブワーカー実装とカスタムヘッダーを使用する場合:**
```xml
<bpmn:businessRuleTask id="calculate-risk" name="Calculate risk">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="calculate_risk" />
    <zeebe:taskHeaders>
      <zeebe:header key="decisionRef" value="risk" />
    </zeebe:taskHeaders>
  </bpmn:extensionElements>
</bpmn:businessRuleTask>
```

#### 制約事項や注意点
*   DMNディシジョンのみを評価したい場合は、`EvaluateDecision` APIを使用できます。
*   インシデントが解決されたとき、入力マッピングはディシジョン評価の前に再度適用されます。これはディシジョンの結果に影響を与える可能性があります。
*   `decisionId` を式で定義する場合、その結果は `string` である必要があります。

#### 他の要素との関連性
*   **DMN (Decision Model and Notation)**: ビジネスルールタスクは、DMNでモデル化されたディシジョン（ディシジョンテーブルやディシジョンリテラル式）を評価するために頻繁に使用されます。
*   **Service Tasks (サービスタスク)**: ジョブワーカー実装を使用する場合、ビジネスルールタスクは技術的にはサービスタスクとまったく同じように動作します。違いはセマンティクスと視覚的表現のみです。
*   **Job Workers (ジョブワーカー)**: 代替実装として、外部のジョブワーカーにタスクの処理を委譲できます。


---


### Script Tasks

#### 1. ページタイトルと概要説明
- **ページタイトル**: Script tasks
- **概要説明**: スクリプトタスクは、Groovy、JavaScript、Pythonなどで記述されたスクリプトの評価をモデル化するために使用されます。Camunda 8では、スクリプトタスクの代替実装をサポートしており、独自のジョブワーカー実装を使用するか、組み込みのFEEL式実装を使用することができます。

#### 2. BPMN要素の定義と用途
- **定義**: スクリプトの評価を実行するためのタスク。
- **用途**: プロセス内でスクリプト（Groovy、JavaScript、Pythonなど）やFEEL式を評価し、その結果をプロセス変数として保存するために使用されます。

#### 3. XMLプロパティ・属性の詳細
### FEEL式を使用する場合 (`zeebe:script` 拡張要素)
- **`expression`**:
  - **型**: 文字列 (FEEL式)
  - **必須/任意**: 必須
  - **デフォルト値**: なし
  - **説明**: 評価するFEEL式を定義します。
- **`resultVariable`**:
  - **型**: 文字列
  - **必須/任意**: 必須
  - **デフォルト値**: なし
  - **説明**: FEEL式の評価結果を格納するプロセス変数の名前を定義します。デフォルトでは、この変数はプロセスインスタンスにマージされます。

### ジョブワーカー実装を使用する場合 (`zeebe:taskDefinition` 拡張要素)
- **`type`**:
  - **型**: 文字列
  - **必須/任意**: 必須
  - **デフォルト値**: なし
  - **説明**: ジョブワーカーがサブスクライブするジョブのタイプ（例: `script`）を指定します。

#### 4. 実装に必要な設定項目
### FEEL式実装
- `zeebe:script` 拡張要素を使用して、`expression` と `resultVariable` を設定します。
- スクリプトタスクのスコープ内のすべての変数は、FEELエンジンが式を評価する際に利用可能です。
- 入力マッピングを使用して、変数をFEEL式が受け入れる形式に変換できます。

### ジョブワーカー実装
- サービスタスクと同様に、ジョブタイプを定義する必要があります。
- ジョブワーカーに静的パラメータ（評価するスクリプトなど）を渡すために、タスクヘッダー（`zeebe:taskHeaders`）を使用します。
- コミュニティ拡張の「Zeebe Script Worker」を使用する場合、タスクヘッダーに特定の属性（`language` や `script` など）を設定する必要があります。
- 変数マッピングを定義して、ジョブワーカーに渡される変数を変換したり、ジョブの変数がどのようにマージされるかをカスタマイズしたりできます。

#### 5. コード例やXML例

### インラインFEEL式を持つスクリプトタスクの例
```xml
<bpmn:scriptTask id="calculate-sum" name="Calculate sum">
  <bpmn:extensionElements>
    <zeebe:script expression="=a + b" resultVariable="sum" />
  </bpmn:extensionElements>
</bpmn:scriptTask>
```

### カスタムヘッダーを持つスクリプトタスク（ジョブワーカー実装）の例
```xml
<bpmn:scriptTask id="calculate-sum" name="Calculate sum">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="script" />
    <zeebe:taskHeaders>
      <zeebe:header key="language" value="javascript" />
      <zeebe:header key="script" value="a + b" />
    </zeebe:taskHeaders>
  </bpmn:extensionElements>
</bpmn:scriptTask>
```

#### 6. 制約事項や注意点
- **FEEL式のエラー処理**: FEEL式の評価が失敗した場合、スクリプトタスクでインシデントが発生します。インシデントが解決されると、スクリプトタスクは再度評価されます。
- **入力マッピングのタイミング**: 入力マッピングは、スクリプトタスクがアクティブ化されたとき（またはインシデントが解決されたとき）、FEEL式の評価前に適用されます。インシデント解決時に再適用されるため、FEEL式の評価結果に影響を与える可能性があります。
- **ジョブ処理の主体**: スクリプトタスクのジョブはZeebe自体では処理されません。処理するには、ジョブワーカーを提供する必要があります。

#### 7. 他の要素との関連性
- **サービスタスク (Service tasks)**: ジョブワーカー実装を使用する場合、スクリプトタスクはサービスタスクとまったく同じように動作します。どちらもジョブとジョブワーカーに基づいています。違いは視覚的表現（タスクマーカー）とモデルのセマンティクスのみです。
- **入力/出力変数マッピング (Input and output variable mappings)**: 変数の変換や結果のカスタマイズに使用されます。
- **インシデント (Incidents)**: 評価失敗時に発生し、解決後に再評価されます。


---
## 5. モデリングのベストプラクティスと命名規則

### 命名規則
- **Tasks**: オブジェクトと動詞の原形を使用（例: `Check invoice`, `Review draft`）
- **Events**: オブジェクトと状態を表す動詞を使用（例: `Invoice checked`, `Draft reviewed`）
- **Gateways**: 質問形式でラベル付けし、出力フローに条件を記述（例: `Invoice correct?` -> `Yes` / `No`）
- **Processes/Pools**: オブジェクトと名詞化された動詞を使用（例: `Dinner preparation`）
- **一般的な規則**: センテンスケース（文の先頭のみ大文字）を使用し、技術用語や略語を避ける。

### 読みやすいプロセスモデルの作成
- **左から右へ**: プロセスは左から右へ流れるようにモデリングする。
- **対称性**: 分岐（Split）と結合（Join）のゲートウェイを対にして配置する。
- **明示的なモデリング**: 暗黙的な分岐や結合を避け、ゲートウェイを明示的に使用する。
- **Happy Pathの強調**: 正常系のフローを中央に直線的に配置する。

---

## 6. エラーハンドリングと例外処理パターン

Happy Path（正常系）を最初にモデリングし、その後で例外やエラーを段階的に追加します。

- **特定のポイントでの分岐**: Exclusive Gateway（データに基づく分岐）やEvent-based Gateway（イベントに基づく分岐）を使用。
- **アクティビティ中のエラー**: Boundary Events（境界イベント）を使用。中断型（Interrupting）と非中断型（Non-interrupting）を使い分ける。
- **プロセス全体での例外**: Event Subprocesses（イベントサブプロセス）を使用し、プロセスのどこにいても対応できるようにする。
- **タイムアウト処理**: Timer Boundary EventやEvent-based GatewayとTimer Eventを組み合わせて、応答がない場合の処理を実装する。


---


## 8. OMG BPMN 2.0 実行セマンティクスと接続ルール

このセクションでは、OMG公式のBPMN 2.0仕様書に基づく厳密な実行セマンティクスと要素間の接続ルールを定義します。

### 8.1 実行セマンティクス (Execution Semantics)

#### 8.1.1 トークンの概念
BPMNの実行セマンティクスは「トークン（Token）」の概念に基づいています。トークンはプロセス内を移動し、各要素の振る舞いを定義します。
- **開始**: Start Eventがトリガーされると、新しいプロセスインスタンスが生成され、各出力Sequence Flowにトークンが生成されます。
- **移動**: トークンはSequence Flowに沿って移動します。
- **消費**: End Eventは到達したトークンを消費します。プロセス内のすべてのトークンが消費されると、プロセスインスタンスは完了状態になります。

#### 8.1.2 ゲートウェイの厳密なセマンティクス
- **Exclusive Gateway (XOR)**:
  - **分岐 (Split)**: 到着したトークンは、条件が`true`と評価された**最初**のSequence Flowにのみルーティングされます。すべての条件が`false`の場合、デフォルトフローが選択されます。デフォルトフローもなく、すべての条件が`false`の場合、例外がスローされます。
  - **合流 (Merge)**: パススルーセマンティクスを持ちます。到着した各トークンはそのまま通過します（同期は行われません）。
- **Parallel Gateway (AND)**:
  - **分岐 (Split)**: 到着した1つのトークンを消費し、**すべて**の出力Sequence Flowに1つずつトークンを生成します。
  - **合流 (Merge)**: **すべて**の入力Sequence Flowに少なくとも1つのトークンが存在する場合にのみアクティブになります。各入力から1つずつトークンを消費し、出力に1つのトークンを生成します（同期）。
- **Inclusive Gateway (OR)**:
  - **分岐 (Split)**: 条件が`true`と評価された**すべて**のSequence Flowにトークンを生成します。
  - **合流 (Merge)**: アクティブな（トークンが到達する可能性のある）すべての入力パスからトークンが到着するのを待って同期します。
- **Event-Based Gateway**:
  - パススルーの合流セマンティクスを持ちます。分岐においては、接続された複数のCatch Eventのうち、**最初**にトリガーされたイベントのパスのみが選択され、他のパスは無効化（Withdrawn）されます。

#### 8.1.3 アクティビティのライフサイクル
アクティビティ（Task, Sub-Process）は以下の状態遷移を持ちます：
1. **Ready**: 必要なトークンが利用可能になった状態。
2. **Active**: データの入力が完了し、実行中の状態。
3. **Completing**: 実行が終了し、事後処理（出力データのマッピングなど）を行っている状態。
4. **Completed**: 正常に完了し、出力Sequence Flowにトークンを生成した状態。
5. **Failed**: 実行中にエラーが発生した状態。
6. **Terminated**: 外部からの割り込み（Error Eventなど）により強制終了された状態。
7. **Withdrawn**: Event-Based Gatewayなどで他のパスが選択され、実行前にキャンセルされた状態。

### 8.2 要素間の接続ルール (Connection Rules)

BPMN 2.0仕様に基づく、要素間のSequence Flow接続の厳密なルールです。

#### 8.2.1 Sequence Flowの有効なソースとターゲット
- **Start Event**:
  - 入力 (Incoming): **不可**（0本）※例外：Event Sub-ProcessのStart Eventも入力不可
  - 出力 (Outgoing): **必須**（1本以上）※例外：Compensation Event Sub-ProcessのStart Eventは出力不可の場合あり
- **End Event**:
  - 入力 (Incoming): **必須**（1本以上）
  - 出力 (Outgoing): **不可**（0本）
- **Intermediate Event (Catch/Throw)**:
  - 入力 (Incoming): **必須**（1本以上）※例外：Boundary Eventは入力不可
  - 出力 (Outgoing): **必須**（1本以上）※例外：Link Catch Eventは入力不可
- **Task / Sub-Process**:
  - 入力 (Incoming): **必須**（1本以上）※例外：Compensation Taskは入力不可
  - 出力 (Outgoing): **必須**（1本以上）
- **Gateway**:
  - 入力 (Incoming): **必須**（1本以上）
  - 出力 (Outgoing): **必須**（1本以上）
  - ※Gatewayは「複数の入力」または「複数の出力」のいずれか（または両方）を持たなければなりません。

#### 8.2.2 境界イベント (Boundary Events) のルール
- Boundary EventはActivity（TaskまたはSub-Process）の境界にのみ配置できます。
- Boundary Eventは**Catch Event**のみ許可されます（Throw Eventは不可）。
- Boundary Eventは入力Sequence Flowを持つことはできません。
- Boundary Eventは必ず1本以上の出力Sequence Flowを持たなければなりません。
- **Interrupting (中断)**: トリガーされると、アタッチされているActivityの実行を即座にキャンセルします（実線で描画）。
- **Non-Interrupting (非中断)**: トリガーされても、アタッチされているActivityの実行は継続します（破線で描画）。ErrorとCancelは常にInterruptingです。

### 8.3 BPMN DI (Diagram Interchange) の厳密な仕様

BPMN 2.0 XMLにおいて、視覚的表現を定義する`bpmndi:BPMNDiagram`セクションのOMG公式仕様です。

#### 8.3.1 BPMNPlane
- `bpmndi:BPMNDiagram`は必ず1つの`bpmndi:BPMNPlane`を含まなければなりません。
- `BPMNPlane`の`bpmnElement`属性は、描画対象のプロセス（`bpmn:Process`のID）を参照しなければなりません。

#### 8.3.2 BPMNShape
- すべてのフローノード（Event, Task, Gateway, Sub-Process）は対応する`bpmndi:BPMNShape`を持たなければなりません。
- `bpmnElement`属性で対象ノードのIDを参照します。
- 必須の子要素として`dc:Bounds`（x, y, width, height）を持ちます。
- **Sub-Process固有の属性**:
  - `isExpanded`: 展開表示の場合は`true`、折りたたみ表示の場合は`false`。Camundaでは通常`true`を使用します。

#### 8.3.3 BPMNEdge
- すべてのSequence Flowは対応する`bpmndi:BPMNEdge`を持たなければなりません。
- `bpmnElement`属性で対象フローのIDを参照します。
- 必須の子要素として2つ以上の`di:waypoint`（x, y）を持ちます。
- ウェイポイントは、ソース要素の境界から始まり、ターゲット要素の境界で終わらなければなりません。

### 8.4 OMG仕様とCamunda仕様のバッティング解決ルール

OMGのBPMN 2.0仕様とCamundaの実装仕様が競合する場合、本辞書では**Camundaの仕様を優先**します。主な違いは以下の通りです：

1. **サポートされる要素の制限**:
   - OMG仕様では多数の要素（Complex Gateway, Choreographyなど）が定義されていますが、Camunda（Zeebe）エンジンで実行可能な要素のみを使用してください（セクション2を参照）。
2. **データフローの表現**:
   - OMG仕様では`DataObject`や`DataInputAssociation`を用いた視覚的なデータマッピングが定義されていますが、Camundaでは実行セマンティクスとして`zeebe:ioMapping`（入力/出力変数マッピング）を使用します。
3. **スクリプトの実行**:
   - OMG仕様の`ScriptTask`はスクリプト言語を直接記述できますが、Camunda 8では通常`ServiceTask`として実装し、Job Workerで処理するか、FEEL式を用いて変数を評価します。
4. **メッセージの相関 (Message Correlation)**:
   - OMG仕様では複雑なCorrelation Key定義がありますが、Camundaでは`zeebe:subscription`要素を用いて明確に相関キー（`correlationKey`）を定義します。

## 9. BPMNDiagram（ダイアグラムレイアウト情報）- 必須セクション

> **重要**: Camunda Modelerで表示するためには、`<bpmndi:BPMNDiagram>`セクションが**必須**です。このセクションがないと「no diagram to display」エラーが発生します。

### 7.1. 構造

```xml
<bpmndi:BPMNDiagram id="BPMNDiagram_1">
  <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="プロセスID">
    <!-- 各ノード要素のShape -->
    <bpmndi:BPMNShape id="要素ID_di" bpmnElement="要素ID">
      <dc:Bounds x="X座標" y="Y座標" width="幅" height="高さ" />
    </bpmndi:BPMNShape>
    <!-- 各シーケンスフローのEdge -->
    <bpmndi:BPMNEdge id="フローID_di" bpmnElement="フローID">
      <di:waypoint x="始点X" y="始点Y" />
      <di:waypoint x="終点X" y="終点Y" />
    </bpmndi:BPMNEdge>
  </bpmndi:BPMNPlane>
</bpmndi:BPMNDiagram>
```

### 7.2. 要素サイズの標準値

| 要素タイプ | 幅 (width) | 高さ (height) |
|---|---|---|
| startEvent | 36 | 36 |
| endEvent | 36 | 36 |
| intermediateCatchEvent | 36 | 36 |
| boundaryEvent | 36 | 36 |
| exclusiveGateway | 50 | 50 |
| parallelGateway | 50 | 50 |
| eventBasedGateway | 50 | 50 |
| userTask | 100 | 80 |
| serviceTask | 100 | 80 |
| sendTask | 100 | 80 |
| callActivity | 100 | 80 |
| subProcess (展開時) | 350+ | 200+ |

### 7.3. 必須ルール

1. **全てのノード要素**（startEvent, endEvent, task, gateway, subprocess, intermediateCatchEvent, boundaryEvent）に対して`BPMNShape`が必要。
2. **全てのシーケンスフロー**に対して`BPMNEdge`が必要。
3. `BPMNEdge`には最低2つの`di:waypoint`が必要。
4. `BPMNPlane`の`bpmnElement`属性はプロセスIDを参照する必要がある。
5. サブプロセスの`BPMNShape`には`isExpanded="true"`を設定する。
6. `BPMNShape`と`BPMNEdge`のIDは通常「元のID + _di」の形式。
7. 境界イベントの座標は、親要素の境界上（通常は下端）に配置する。

### 7.4. 必須名前空間

```xml
xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
```


### 7.5. レイアウトのベストプラクティス（上から下へのフロー）

> **重要**: AIエージェントがBPMNを生成する際、デフォルトのレイアウト方向は**「上から下（Top-to-Bottom）」**とします。これにより、複雑なプロセスでも視覚的に整理され、人間が読みやすいモデルになります。

1. **メインフローの配置**:
   - メインの正常系フロー（Happy Path）は中央の列（例: `X = 400`）に配置し、Y座標を段階的に増加（例: `Y = 100, 220, 340...`）させます。
2. **分岐の配置**:
   - エラー処理や拒否ルートは左側の列（例: `X = 200`）に配置します。
   - 並列処理や代替ルートは右側の列（例: `X = 600`）に配置します。
3. **サブプロセスとイベントサブプロセスの配置**:
   - サブプロセス内の要素も**完全に上から下へ**流れるように配置します（横方向のフローは避けます）。
   - サブプロセス自体は縦長に配置し、内部の要素のY座標を段階的に増加させます。
   - イベントサブプロセスはメインフローから離れた右側の領域（例: `X = 950`）に配置し、メインフローと重ならないようにします。
4. **シーケンスフローのルーティング**:
   - **全てのフローは「下」から出て「上」に入る**ことを基本とします。
   - 分岐や合流でX座標が変わる場合は、直角に曲がるようにウェイポイント（`di:waypoint`）を設定します。
   - ウェイポイントは「始点（下端） → 中間点（少し下へ移動） → 中間点（X軸移動） → 終点（上端）」のように、直角ルーティングを意識して計算します。
