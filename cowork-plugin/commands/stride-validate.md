---
description: BACCM 6 軸 + 4-layer Requirements Architecture + Phase 1 整合性を機械検証。Phase 0/1 各 milestone で fail 軸を発見。
argument-hint: "<feature_name>"
---

# /stride:validate

Phase 0 (Discovery + Elicit + Context Modelling) と Phase 1 (basic_design + process.bpmn) の完全性を機械検証します。

## Usage

```
/stride:validate <feature_name>
```

## Workflow

### 1. Validate Input
- `specs/<feature_name>/` が存在
- profile を `state.yaml` から読む

### 2. 機械検証 (内部 logic)

`reference_files/policies/baccm_completeness.yaml` の閾値を読み、以下を順次チェック:

#### 2.1 BACCM 6 軸完全性
各軸ごとに対応 yaml の populated 状況を確認:
- `change` → `change_strategy.yaml`
- `need` → `business_need.yaml`
- `solution` → `goal_tree.yaml`
- `stakeholder` → `stakeholder_map.yaml`
- `value` → `value_canvas.yaml`
- `context` → `context_map.yaml`

profile 別閾値:
- **enterprise-erp**: 全軸 100% 必須 (`threshold_for_gate_0: 100`)
- **saas-integration**: 全軸 pass 必須 (空項目あれば fail)
- **prototype**: stakeholder + value のみ必須、他は warning

#### 2.2 4-layer Requirements Architecture完全性 (Phase 0.5 完成時)
- 5 シート全て populated か
- `business_usecase.yaml` の UC が 5+ 件、ID 命名 `UC-NNN` 形式

#### 2.3 Phase 1 整合性 (basic_design.md 完成時)
- `basic_design.bpmn_descriptions[].bpmn_id` と `process.bpmn` の id が完全一致
- `traceability_rows` 1+ 件
- `basic_design_gate_check` の rules を満たす counts

#### 2.4 BPMN 機械検証 (v0.4.0 — `bpmn/` パッケージ統合)
- **`process.bpmn`** に対し `python3 ${CLAUDE_PLUGIN_ROOT}/bpmn/validators/bpmn_lint.py specs/<feature>/process.bpmn` を実行
  - FEAT 14 MUST-DO の機械検証 (errors=0 で PASS)
- **`epic_flow.bpmn`** がある場合 (`epics/<EPIC>/epic_flow.bpmn`) は `--epic` 強制で検証
  - EPIC 9 MUST-DO の機械検証
- BPMN_PLACEHOLDER_PRESENT (`{{...}}` 等の未置換) は warning レベル、修正必須
- 詳細は `${CLAUDE_PLUGIN_ROOT}/bpmn/validators/README.md` (CI 統合例同梱)
- 単独 BPMN 検証だけしたい場合は **`/stride:bpmn-validate <feature_name>`** が高速

### 3. Output

stdout に以下を Markdown で出力:

```markdown
# Validate Result for <feature_name> (profile: <P>)

## BACCM 6 軸 (target: <N>%)
- change:      ✅ 100% (3/3 fields)
- need:        ✅ 100%
- solution:    ⚠️  85% (1 軸不足: tree_hierarchy が空)
- stakeholder: ✅ 100%
- value:       ✅ 100%
- context:     ✅ 100%

→ profile=enterprise-erp で 100% 必須、`solution` 軸 fail。

## 4-layer Requirements Architecture (該当する場合)
- ✅ actor_system / business_usecase / information_state / condition_variation / requirements_architecture 全 populated

## Phase 1 整合性 (該当する場合)
- ✅ basic_design.bpmn_descriptions と process.bpmn の id 完全一致

## 推奨アクション
- `goal_tree.yaml` の `tree_hierarchy` を埋めて `/stride:discovery <feature>` を再実行
```

### 4. Next Step

- 全 pass なら `/stride:bridge` で Phase 1 接続
- fail 軸あれば対応 skill (例: solution 軸 fail なら `/stride:discovery`) で再対話
