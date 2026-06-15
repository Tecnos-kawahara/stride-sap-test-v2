---
description: BACCM 6 軸 (change/need/solution/stakeholder/value/context) で Phase 0 Discovery を完成させる対話を起動。
argument-hint: "<feature_name>"
---

# /stride:discovery

`baccm-discovery` skill を起動し、BABOK BACCM 6 軸で Phase 0 Discovery を対話完成させます。

## Usage

```
/stride:discovery <feature_name>
```

## Workflow

### 1. Validate Input
- `specs/<feature_name>/` が存在すること (なければ `/stride:init` を案内)
- profile を `state.yaml` から読む

### 2. Trigger Skill

このコマンドは `baccm-discovery` Skill を auto-trigger します。Skill が以下を実行:

- 顧客要件メモ + Cowork Project 内資料を読む
- BACCM 6 軸を `change → need → solution → stakeholder → value → context` の順序で対話
- 各軸ごとに最低 3 項目を埋める (enterprise-erp は 100% 必須)
- iteration (bootstrap → structure → refinement) 3 段階を進行

### 3. Output

- `specs/<feature>/upstream/phase_0_discovery/` 配下に 7 yaml 生成:
  - `business_need.yaml` (need 軸)
  - `value_canvas.yaml` (value 軸)
  - `stakeholder_map.yaml` (stakeholder 軸)
  - `context_map.yaml` (context 軸)
  - `risk_register.yaml` (横断、必須リスク)
  - `change_strategy.yaml` (change 軸)
  - `goal_tree.yaml` (solution 軸)

### 4. Next Step

完了後、`/stride:elicit <feature_name>` で BABOK Elicitation に進む。
