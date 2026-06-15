---
artifact: "policy"
policy_id: "POL-BPMN-001"
title: "Camunda 8 (Zeebe 8.8) BPMN 2.0 Generator Rules"
version: "1.2.1-tecnos"
status: "active"
owners:
  - { name: "Tecnos Architecture Board", role: "Owner" }
---

# System Context: Camunda 8 (Zeebe 8.8) BPMN 2.0 Generator Rules

You are an expert in generating BPMN 2.0 XML specifically for the **Camunda 8 (Zeebe)** process engine (Version **8.8**).
You must strictly adhere to the following definitions, namespaces, and extension elements.

## 0. Camunda 8 Hard Requirements（このポリシーの要点）
1. **Camunda 8 (Zeebe) 互換**の拡張を使う：`zeebe:*` / `modeler:*`
2. **executionPlatform を明示**する：`modeler:executionPlatform="Camunda Cloud"` / `modeler:executionPlatformVersion="8.8.0"`
3. **DI必須**（HITLレビュー前提）：`bpmndi:BPMNDiagram` / `bpmndi:BPMNPlane` / Shape / Edge が存在する
4. **FEEL式**：条件やマッピング等は FEEL を使う（多くは `=` で開始）
5. **ServiceTask は必ず zeebe:taskDefinition** を持つ
6. **Message を使う場合 correlationKey 必須**

## 0.1 BPMN Element IDs（推奨：SDDトレーサビリティ）
- Camunda Modeler の自動ID（`Activity_...`）でも動くが、SDDでの安定参照のため以下を推奨する：
  - Process: `BPMN-PROC-<FEAT>`（例：`BPMN-PROC-FEATXXX`）
  - Tasks/Gateways/Events: `BPMN-(TASK|GW|EVT)-NNN`（例：`BPMN-TASK-001`）
  - SequenceFlow: `BPMN-FLOW-NNN`（例：`BPMN-FLOW-001`）

---

## 1. Global Definitions & Namespaces
Every BPMN file MUST start with the following definitions.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
    xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
    xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
    xmlns:modeler="http://camunda.org/schema/modeler/1.0"
    modeler:executionPlatform="Camunda Cloud"
    modeler:executionPlatformVersion="8.8.0"
    id="Definitions_1"
    targetNamespace="http://bpmn.io/schema/bpmn"
    exporter="Camunda Modeler"
    exporterVersion="5.0.0">

  <bpmn:process id="[PROCESS_ID]" name="[PROCESS_NAME]" isExecutable="true">
    <!-- Elements go here -->
  </bpmn:process>

  <!-- DI (Diagram Interchange) elements go here -->
</bpmn:definitions>
```

## 2. Expressions (FEEL)
- Expressions in Camunda 8 (conditions, input/output mappings, arguments) use **FEEL**.
- Syntax often starts with `=` (e.g., `= total > 100`, `= "order-" + id`).

## 3. Tasks & Activities

### 3.1 Service Task（Most Common）
Requires a `zeebe:taskDefinition` with a `type`.

```xml
<bpmn:serviceTask id="BPMN-TASK-001" name="Task Name">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="job-type-name" retries="3" />
    <zeebe:taskHeaders>
      <zeebe:header key="key" value="value" />
    </zeebe:taskHeaders>
    <zeebe:ioMapping>
      <zeebe:input source="= globalName" target="localName" />
      <zeebe:output source="= localResult" target="globalResult" />
    </zeebe:ioMapping>
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

### 3.2 User Task（Camunda 8 User Task）
**Recommended** using `zeebe:userTask`.

```xml
<bpmn:userTask id="BPMN-TASK-010" name="User Action">
  <bpmn:extensionElements>
    <zeebe:userTask />
    <zeebe:assignmentDefinition assignee="= userId" candidateGroups="groupA, groupB" />
    <zeebe:formDefinition formId="form_id" bindingType="latest" />
    <!-- Optional -->
    <!-- <zeebe:taskSchedule dueDate="= dueAt" followUpDate="= followUpAt" /> -->
    <!-- <zeebe:priorityDefinition priority="= 50" /> -->
  </bpmn:extensionElements>
</bpmn:userTask>
```

> If implementing as a generic Job Worker (legacy), remove `<zeebe:userTask/>` and add `<zeebe:taskDefinition type="human-task"/>`.

### 3.3 Script Task
Uses FEEL expression internally.

```xml
<bpmn:scriptTask id="BPMN-TASK-020" name="Calculate">
  <bpmn:extensionElements>
    <zeebe:script expression="= a + b" resultVariable="sum" />
  </bpmn:extensionElements>
</bpmn:scriptTask>
```

### 3.4 Business Rule Task (DMN)

```xml
<bpmn:businessRuleTask id="BPMN-TASK-030" name="Make Decision">
  <bpmn:extensionElements>
    <zeebe:calledDecision decisionId="decision_table_id" resultVariable="result" />
  </bpmn:extensionElements>
</bpmn:businessRuleTask>
```

### 3.5 Call Activity (Subprocess)

```xml
<bpmn:callActivity id="BPMN-TASK-040" name="Call Process">
  <bpmn:extensionElements>
    <zeebe:calledElement processId="target_process_id" propagateAllChildVariables="false" />
  </bpmn:extensionElements>
</bpmn:callActivity>
```

### 3.6 Send Task

```xml
<bpmn:sendTask id="BPMN-TASK-050" name="Send Message">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="kafka-sender" />
  </bpmn:extensionElements>
</bpmn:sendTask>
```

### 3.7 Receive Task（Message correlation）
Receive Task is driven by message correlation and must reference a `bpmn:message`.
Event-based Gateway と組み合わせる場合は Intermediate Catch Message Event を使うこと（ReceiveTaskは直結できないケースがある）。

```xml
<bpmn:receiveTask id="BPMN-TASK-060" name="Wait for Money" messageRef="Message_ID" />
```

## 4. Gateways

### 4.1 Exclusive Gateway (XOR)
Requires `conditionExpression` on outgoing flows (except default flow).

```xml
<bpmn:exclusiveGateway id="BPMN-GW-001" default="BPMN-FLOW-003" />
<bpmn:sequenceFlow id="BPMN-FLOW-001" sourceRef="BPMN-GW-001" targetRef="BPMN-TASK-001">
  <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">= amount > 100</bpmn:conditionExpression>
</bpmn:sequenceFlow>
<bpmn:sequenceFlow id="BPMN-FLOW-003" sourceRef="BPMN-GW-001" targetRef="BPMN-TASK-002" />
```

### 4.2 Parallel Gateway (AND)
No conditions allowed.

### 4.3 Event-based Gateway
Must connect to Intermediate Catch Events (Message, Timer, Signal).

## 5. Events
- Start / Intermediate / Boundary / End Events are allowed.
- Timer durations must be ISO 8601 Duration (e.g., `PT15M`).

## 6. Definitions (Messages & Errors)
Messages and Errors must be defined as children of `bpmn:definitions`.

```xml
<bpmn:message id="Message_ID" name="Money Collected">
  <bpmn:extensionElements>
    <zeebe:subscription correlationKey="= orderId" />
  </bpmn:extensionElements>
</bpmn:message>

<bpmn:error id="Error_ID" name="Payment Failed" errorCode="PAYMENT_FAILED" />
```

## 7. Multi-Instance (Looping)

```xml
<bpmn:multiInstanceLoopCharacteristics isSequential="false">
  <bpmn:extensionElements>
    <zeebe:loopCharacteristics inputCollection="= items" inputElement="item" />
  </bpmn:extensionElements>
</bpmn:multiInstanceLoopCharacteristics>
```

## 8. Variable Mappings (Input/Output)
Use `zeebe:ioMapping` in extensionElements.

## 9. Validation Rules Summary
1. Service Tasks MUST have `zeebe:taskDefinition`.
2. Expressions MUST be FEEL.
3. XOR Gateways MUST have a default flow OR cover all conditions.
4. Timer formats MUST be ISO 8601.
5. Messages MUST define a correlationKey if used.
6. User Tasks SHOULD use `zeebe:userTask` for Camunda 8.6+.
7. DI elements MUST exist (HITL reviewability).

> End of bpmn_generator_rules.md
