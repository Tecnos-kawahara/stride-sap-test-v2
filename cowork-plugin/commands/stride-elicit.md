---
description: BABOK KA4 Elicitation を実施。50 technique から context 別に 5 件推奨し、対話で elicitation_plan.yaml を完成。
argument-hint: "<feature_name>"
---

# /stride:elicit

`babok-elicitation` skill を起動し、BABOK KA4 Elicitation を実施します。

## Usage

```
/stride:elicit <feature_name>
```

## Workflow

### 1. Validate Input
- `specs/<feature_name>/upstream/phase_0_discovery/` の 7 yaml が完成していること
- まだなら `/stride:discovery` を先に実行するよう案内

### 2. Trigger Skill

`babok-elicitation` Skill を auto-trigger:

- `stakeholder_map.yaml` から actor 一覧を取得
- BABOK 50 technique から context (profile / 規模 / stakeholder 数) に応じて 5 件推奨
- コンサルが 3-5 件選択
- `elicitation_plan.yaml` 生成 (technique / 対象 stakeholder / スケジュール / 期待 outcome)

### 3. Output

- `specs/<feature>/upstream/phase_0_3_elicit/elicitation_plan.yaml`
- (実施後追記) `specs/<feature>/upstream/phase_0_3_elicit/elicitation_results.yaml`

### 4. Next Step

実施完了後、`/stride:context-model <feature_name>` で Layered Context Modelling (4-layer Requirements Architecture) に進む。
