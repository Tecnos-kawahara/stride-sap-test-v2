---
name: baccm-discovery
description: Tecnos-STRIDE VALUE Upstream Extension の Phase 0 (Discovery) を BABOK
  BACCM 6 軸 (change/need/solution/stakeholder/value/context) で完成させる。「Tecnos-STRIDE
  Phase 0」「BACCM Discovery」「BACCM 6 軸」「BACCM」「VALUE pack Phase 0」「上位コンサル」「stride-discovery」を含む依頼時のみ発火
  (Tecnos-STRIDE 固有語必須)。汎用語の「Discovery」「需要」「価値」「ステークホルダー」単独では発火しない (誤起動回避、WI-VALF01-003)。
argument-hint: <feature_name>
plane: internal
visibility: abstract
return_policy:
  customer: abstract
  platform_admin: abstract
  tecnos_admin: full
---

# Skill: baccm-discovery

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

このスキルは、Phase 0 (Discovery) を BABOK の Business Analysis Core Concept Model (BACCM) 6 軸で完成させ、`specs/<feature>/upstream/phase_0_discovery/` 配下に 7 yaml 成果物を生成します。

## STEP 0: PRE-FLIGHT (MANDATORY — DO THIS FIRST)

> ⛔ **STOP.** auto-fire でこの skill が起動された場合でも、BACCM 6 軸の定義 +
> 7 templates は context に自動 load されない。手動で Read してから対話を開始すること。

### 必須 Read リスト (順番厳守)

1. `${CLAUDE_PLUGIN_ROOT}/reference_files/manual/40_baccm_guide.md` — BACCM 6 軸の正本ガイド
2. `${CLAUDE_PLUGIN_ROOT}/reference_files/policies/baccm_completeness.yaml` — Profile 別の完成度閾値
3. `${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/business_need_template.yaml` — 7 templates の代表として 1 件
4. `${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/value_canvas_template.yaml`
5. `${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/stakeholder_map_template.yaml`

### 必須実行コマンド (template-copy 強制)

```bash
# 7 templates を一括 copy (ゼロから書かない)
mkdir -p specs/<feature>/upstream/phase_0_discovery
for f in business_need value_canvas stakeholder_map context_map risk_register change_strategy goal_tree; do
  cp ${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/${f}_template.yaml \
     specs/<feature>/upstream/phase_0_discovery/${f}.yaml
done
```

### 🚫 ANTI-PATTERN

| 違反 | 正しい行動 |
|---|---|
| 7 yaml をゼロから合成 | template を `cp` してから placeholder 置換 |
| BACCM 6 軸のうち 3-4 軸しか埋めず PASS と宣言 | enterprise-erp profile では 6 軸 100% 必須 |
| stakeholder を 1-2 名のみ列挙 | Article XV 違反、最低 3 名以上 |
| `success_criteria` (KPI) を未定義のまま | KA8 後評価の基準なので必ず定量化 |

### Output of STEP 0

```
[PRE-FLIGHT REPORT]
  read: 40_baccm_guide.md (✓)
  read: baccm_completeness.yaml (✓)
  read: 5 yaml templates (✓)
  templates_copied: 7 yaml files to specs/<feature>/upstream/phase_0_discovery/
  profile: <enterprise-erp | saas-integration | prototype>
  baccm_completeness_target: <100% | 70% | 50%>
  ready_to_proceed: true
```

---

## Usage

```
/stride:discovery <feature_name>
```

## Workflow

### 1. Understand the Input

- 顧客から共有された **要件メモ / インタビューメモ / 問題提起資料** を収集
- profile (`enterprise-erp` / `saas-integration` / `prototype`) を確認 (basic_design.md またはコンサル指定)
- 既存の Cowork Project 内の関連資料を `${WORKSPACE}` 配下から検索

### 2. Reference Files

- `reference_files/manual/40_baccm_guide.md` (BACCM 6 軸の説明)
- `reference_files/policies/baccm_completeness.yaml` (Profile 別の完成度閾値、enterprise-erp は 100% 必須)
- `reference_files/templates/upstream/business_need_template.yaml`
- `reference_files/templates/upstream/value_canvas_template.yaml`
- `reference_files/templates/upstream/stakeholder_map_template.yaml`
- `reference_files/templates/upstream/context_map_template.yaml`
- `reference_files/templates/upstream/risk_register_template.yaml`
- `reference_files/templates/upstream/change_strategy_template.yaml`
- `reference_files/templates/upstream/goal_tree_template.yaml`

### 3. Generate Output

BACCM 6 軸を以下の順序で対話的に埋める。**各軸ごとに最低 3 項目** を埋め、profile が enterprise-erp なら **6 軸全て 100% 必須**。

#### 3.1 change 軸 → `change_strategy.yaml`
- 現状 (As-Is) と目標 (To-Be) を対比
- 移行計画 (transition_plan)、教育・周知計画 (training_plan) を含む

#### 3.2 need 軸 → `business_need.yaml`
- WHAT (何を実現するか) と WHY (なぜ今必要か)
- capability (調達 DX / 生産 DX 等)

#### 3.3 solution 軸 → `goal_tree.yaml`
- in_scope / out_scope を明示
- root → sub-goal → tasks の階層構造

#### 3.4 stakeholder 軸 → `stakeholder_map.yaml`
- enterprise-erp なら **5-7 階層** (業務 / IT / 監査 / 経営 / SI / SaaS / 製造委託先 等)
- 各 actor の role + concern + influence を記述
- saas-integration なら SaaS ベンダ (CSM / TS) を必ず stakeholder に含める

#### 3.5 value 軸 → `value_canvas.yaml`
- current_state → target_state の差分
- proposition (顧客への提供価値)
- 業務 KPI と連結

#### 3.6 context 軸 → `context_map.yaml`
- 関連システム (SAP / mcframe / Salesforce 等) を境界として明示
- value_chain (O2C / P2P / R2R 等)

### 4. Iteration

`reference_files/policies/upstream_iteration_policy.yaml` に従い、**bootstrap → structure → refinement** の 3 段階で iterate。各 iteration ごとに:

1. すべての yaml を **対話で埋める**
2. `/stride:validate <feature>` で BACCM 完全性チェック
3. fail 軸を refinement、再 validate

enterprise-erp は 3 iteration 必須、saas-integration は 2 iteration 以上推奨、prototype は bootstrap 1 iteration で OK。

### 5. Completion Criteria

- 7 yaml 全て生成済 (空欄なし、または warning レベル容認 prototype のみ)
- `/stride:validate <feature>` が全軸 pass (enterprise-erp なら 100%、他は profile 別閾値)
- `risk_register.yaml` に最低 3 リスクを記載 (saas-integration なら SaaS 側 SLA / レート制限を必須)

## Attributions

- **BABOK v3 (IIBA)**: BACCM 6 軸の framework。fair-use, names and section refs only
- **value-driven discovery (philosophical foundation)**: value_canvas / goal_tree の思想的源流として参照 (考え方のみ、固有商標名は使用しない)
