---
description: 4-layer Requirements Architecture / 5 シート (actor / business_usecase / information_state / condition_variation / requirements_architecture) で Context Modelling を完成。
argument-hint: "<feature_name>"
---

# /stride:context-model

`layered-context-modelling` skill を起動し、4-layer Requirements Architecture (System / Business / Condition / Business Use Case) を 5 シートで Context Modelling を完成させます。

## Usage

```
/stride:context-model <feature_name>
```

## Workflow

### 1. Validate Input
- Phase 0 Discovery + Elicit 完成 (前提)

### 2. Trigger Skill

`layered-context-modelling` Skill を auto-trigger:

1. **System Layer** → `actor_system.yaml` (actor + system)
2. **Business Layer** → `business_usecase.yaml` (UC-NNN 形式、5+ 件)
3. **Condition Layer** → `condition_variation.yaml` (業務イベント + 状態変化)
4. **BUC Layer** → `information_state.yaml` (entity + state ライフサイクル)
5. **Architecture** → `requirements_architecture.yaml` (4 レイヤー統合)

大型 BUC は `usecase_complex_<NNN>.yaml` に分解 (sub-flow 5+ 等)。

### 3. Output

`specs/<feature>/upstream/phase_0_5_context_modelling/` 配下に 5+ yaml。

### 4. Next Step

完了後、`/stride:validate <feature_name>` で Phase 0 完全性チェック → `/stride:bridge` で Phase 1 接続。
