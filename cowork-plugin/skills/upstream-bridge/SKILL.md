---
name: upstream-bridge
description: Tecnos-STRIDE VALUE Upstream Extension の Phase 0 (Discovery / Elicit
  / Context Modelling) 完成後、Phase 1 への橋渡し。basic_design.md skeleton 生成 + links populate
  を行う。「Tecnos-STRIDE upstream-bridge」「stride-bridge」「Phase 0 → Phase 1 橋渡し」「VALUE
  pack basic_design 生成」「BACCM Phase 0 → 1」を含む依頼時のみ発火 (Tecnos-STRIDE 固有語必須)。汎用語の「basic_design
  生成」「Phase 1 設計」「橋渡し」単独では発火しない (誤起動回避、WI-VALF01-003)。
argument-hint: <feature_name>
plane: internal
visibility: abstract
return_policy:
  customer: abstract
  platform_admin: abstract
  tecnos_admin: full
---

# Skill: upstream-bridge

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

このスキルは、Phase 0 完成成果物 (BACCM + 4-layer Requirements Architecture) を Phase 1 (`basic_design.md`) に橋渡しする骨格を生成します。

## STEP 0: PRE-FLIGHT (MANDATORY — DO THIS FIRST)

> ⛔ **STOP.** auto-fire でこの skill が起動された場合でも、bridge guide + canonical
> schema + Phase 0 成果物は context に自動 load されない。手動で Read してから着手すること。
> upstream-bridge は **Gate 1/2 immutability check** が内蔵されており、承認済 feature の
> `--apply` は fail-closed で reject される。

### 必須 Read リスト (順番厳守)

1. `${CLAUDE_PLUGIN_ROOT}/reference_files/manual/45_upstream_bridge_guide.md` — Bridge 機能の正本ガイド
2. `${CLAUDE_PLUGIN_ROOT}/reference_files/templates/basic_design_template.md` — canonical schema (TPL-BD-TECNOS-001)
3. `${CLAUDE_PLUGIN_ROOT}/reference_files/policies/upstream_policy.yaml` — links 必須項目
4. Phase 0 成果物全件 (`specs/<feature>/upstream/phase_0_*/*.yaml`) を Read

### 必須実行コマンド (Bridge tool delegation)

```bash
# bridge は専用 Python tool を delegate する (自作禁止、stride upstream-bridge 経由)
sdd-templates/bin/stride upstream-bridge <feature> --target phase1
# dry-run で populate 計画 + BPMN-TASK 候補を確認後、--apply で実書込
```

### 🚫 ANTI-PATTERN

| 違反 | 正しい行動 |
|---|---|
| Phase 0 完成 (BACCM 6 軸 100%) を未確認のまま bridge 実行 | `stride upstream validate <feature>` で BACCM_INCOMPLETE / Layered Requirements Modeling_BROKEN_LINK 全 0 を確認 |
| Gate 1/2 承認済 feature に `--apply` を実行 | immutability check が拒否、change_log.md 経由の正規ルートに切替 |
| `process.bpmn` を bridge で書き込む | bridge は `basic_design.md links` のみ書込、`process.bpmn` は bpmn-authoring 担当 |
| BPMN-TASK 候補を無視して bpmn-authoring へ渡さず | bridge stdout の BPMN-TASK 候補は bpmn-authoring の primary input |

### Output of STEP 0

```
[PRE-FLIGHT REPORT]
  read: 45_upstream_bridge_guide.md (✓)
  read: basic_design_template.md (✓)
  read: upstream_policy.yaml (✓)
  read: phase_0_discovery/*.yaml (7 files) + phase_0_3_elicit/*.yaml (2 files) + phase_0_5_context_modelling/*.yaml (5+ files)
  upstream_validate_status: <PASS | FAIL>  (FAIL なら bridge 実行不可)
  gate_1_2_status: <unapproved | approved>  (approved なら --apply 不可)
  ready_to_proceed: true
```

---

## Usage

```
/stride:bridge <feature_name>
```

## Workflow

### 1. Understand the Input

- Phase 0 完成成果物を確認: `specs/<feature>/upstream/phase_0_discovery/*.yaml` (7 件) + `phase_0_3_elicit/*.yaml` (2 件) + `phase_0_5_context_modelling/*.yaml` (5+ 件)
- profile (`enterprise-erp` / `saas-integration` / `prototype`) を確認

### 2. Reference Files

- `reference_files/manual/45_upstream_bridge_guide.md` (Bridge 機能の正本ガイド、Phase C で導入)
- `reference_files/templates/basic_design_template.md` (canonical schema、Phase A で確定)
- `reference_files/policies/upstream_policy.yaml` (links 必須項目)

### 3. Generate Output

#### 3.1 basic_design.md skeleton 生成

`reference_files/templates/basic_design_template.md` をベースに、以下を populate:

- **frontmatter**: feature_id (FEAT-<FEATUREID>)、basic_design_id (BD-<FEATUREID>)、title、profile、version、created_at、owners、reviewers
- **`links` セクション**:
  - `upstream_dir_ref`: `specs/<feature>/upstream/`
  - `upstream_policy_ref`: `shared/policies/upstream_policy.yaml`
  - `baccm_completeness_ref`: `shared/policies/baccm_completeness.yaml`
  - `process_bpmn_ref`: `specs/<feature>/process.bpmn`
  - その他 spec/plan/tasks ref
- **`context.who/what/why`**: Phase 0 の `business_need.yaml` から自動抽出 (要人間確認)
- **`business_domain`**: `value_canvas.yaml` + `context_map.yaml` から自動抽出
- **`scope.in/out`**: `goal_tree.yaml` から自動抽出
- **`systems`**: `context_map.yaml` の systems を転記
- **`raci_plus.actors`**: `stakeholder_map.yaml` から自動抽出

#### 3.2 BPMN Task 候補リスト生成

`business_usecase.yaml` の各 UC を BPMN-TASK-NNN 候補として stdout に Markdown で提示:
- `UC-001` → `BPMN-TASK-001` 候補 (3 桁数字対応)
- 各 UC の actor / outcome / inputs / outputs を BPMN documentation 用にサマリ

コンサルがレビューしてから次の `/stride:design` で `bpmn-authoring` skill が実装する。

### 4. Phase 1 Immutability の警告

Gate 1 / Gate 2 がすでに承認されている場合 (APPROVAL.md の `[x]` チェック)、`basic_design.md` の **意味的変更** は禁止。bridge skill は基本的に新規 feature への適用前提だが、既存 feature で再起動された場合は warning を出す。

### 5. Completion Criteria

- `specs/<feature>/basic_design.md` の skeleton が生成済 (links populate 済、context/scope/systems/raci_plus は人間確認待ち)
- BPMN-TASK 候補リストが stdout に出力済 (次 `/stride:design` の入力)
- `/stride:validate <feature>` で Phase 0 整合性 pass

## Attributions

- **BABOK v3 (IIBA)**: KA7 Requirements Analysis の Phase 0 → 1 transition pattern。fair-use
- **4-layer Requirements Architecture**: structural integrity を Phase 1 に引き継ぐ概念 (考え方のみ、固有商標名は使用しない)
- **value-driven discovery method**: value canvas → goal tree の transition (考え方のみ、固有商標名は使用しない)
