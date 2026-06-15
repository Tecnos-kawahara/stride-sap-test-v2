---
description: Phase 0 (Discovery / Elicit / Context Modelling) 完成後の Phase 1 への橋渡し。basic_design.md skeleton 生成 + links populate。
argument-hint: "<feature_name>"
---

# /stride:bridge

`upstream-bridge` skill を起動し、Phase 0 → Phase 1 接続の `basic_design.md` skeleton を生成します。

## Usage

```
/stride:bridge <feature_name>
```

## Workflow

### 1. Validate Input
- Phase 0 全成果物 (Discovery 7 + Elicit 2 + Context Modelling 5+) が完成
- まだなら `/stride:validate <feature>` を案内、不足軸を refinement

### 2. Trigger Skill

`upstream-bridge` Skill を auto-trigger:

- BACCM + 4-layer Requirements Architecture → basic_design.md セクションへの mapping
- `links` populate (upstream_dir_ref / upstream_policy_ref / baccm_completeness_ref / process_bpmn_ref / spec/plan/tasks ref)
- `context.who/what/why` を `business_need.yaml` から自動抽出
- `business_domain` / `scope` / `systems` / `raci_plus.actors` を Phase 0 yaml から自動抽出
- BPMN-TASK 候補リストを stdout に Markdown 出力 (`business_usecase.yaml` 由来)

### 3. Output

- `specs/<feature>/basic_design.md` (skeleton、人間確認待ちフィールドあり)
- stdout の BPMN-TASK 候補リスト (次 `/stride:design` の入力)

### 4. Next Step

`/stride:design <feature_name>` で `basic-design-authoring` + `bpmn-authoring` を順次起動、basic_design + process.bpmn を完成。
