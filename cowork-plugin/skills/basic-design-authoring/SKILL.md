---
name: basic-design-authoring
description: Tecnos-STRIDE SDD Phase 1 で basic_design.md を canonical schema (template_id
  TPL-BD-TECNOS-001) 準拠で完成させる。「Tecnos-STRIDE basic_design」「TPL-BD-TECNOS-001」「basic_design_gate_check」「stride-design」「VALUE
  pack basic_design.md」「canonical Basic Design」を含む依頼時のみ発火 (Tecnos-STRIDE 固有語必須)。汎用語の「設計書」「basic_design.md
  作成」単独では発火しない (誤起動回避、WI-VALF01-003)。upstream-bridge の skeleton を完成させる役割。
argument-hint: <feature_name>
plane: internal
visibility: abstract
return_policy:
  customer: abstract
  platform_admin: abstract
  tecnos_admin: full
---

# Skill: basic-design-authoring

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

このスキルは、`upstream-bridge` で生成された basic_design.md skeleton を完成させ、`basic_design_gate_check` の全 booleans を真化します。

## STEP 0: PRE-FLIGHT (MANDATORY — DO THIS FIRST)

> ⛔ **STOP.** auto-fire でこの skill が起動された場合でも、SKILL.md 本文 + canonical
> template は context に自動 load されない。手動で Read してから着手すること。

### 必須 Read リスト (順番厳守)

1. `${CLAUDE_PLUGIN_ROOT}/reference_files/templates/basic_design_template.md` — canonical schema (TPL-BD-TECNOS-001、608+ 行)
2. `${CLAUDE_PLUGIN_ROOT}/reference_files/policies/profile_policy.yaml` — Profile 別の閾値 (enterprise-erp / saas-integration / prototype)
3. `${CLAUDE_PLUGIN_ROOT}/reference_files/sdd-templates/sdd_bootstrap.md` §1-3 — Phase Gate 規範
4. `${CLAUDE_PLUGIN_ROOT}/bpmn/PRE_FLIGHT_CHECKLIST.md` (BPMN セクション populate 時に bpmn-authoring と連携)

### 🚫 ANTI-PATTERN

| 違反 | 正しい行動 |
|---|---|
| canonical schema を読まずに自由形式で書いた | template を `cp` してから placeholder 置換 |
| `bpmn_descriptions` を populate せず BPMN だけ作成した | basic_design ↔ process.bpmn の id を完全一致 |
| `basic_design_gate_check` の booleans を埋めなかった | `traceability_present` 等の booleans を全 true 化 |
| profile 別 thresholds を無視した完全性 | profile_policy.yaml の数値要件 (enterprise-erp 100%) を遵守 |

### Output of STEP 0

```
[PRE-FLIGHT REPORT]
  read: basic_design_template.md (✓)
  read: profile_policy.yaml (✓)
  read: sdd_bootstrap.md §1-3 (✓)
  template_copied: specs/<feature>/basic_design.md (from skeleton or template)
  profile: <enterprise-erp | saas-integration | prototype>
  ready_to_proceed: true
```

---

## Usage

```
/stride:design <feature_name>
```

(`/stride:design` は内部で `basic-design-authoring` + `bpmn-authoring` を順次起動)

## Workflow

### 1. Understand the Input

- `upstream-bridge` で生成済の skeleton (`specs/<feature>/basic_design.md`)
- Phase 0 全成果物 (BACCM + 4-layer Requirements Architecture + Elicit)
- profile (`enterprise-erp` / `saas-integration` / `prototype`)

### 2. Reference Files

- `reference_files/templates/basic_design_template.md` (canonical schema、608+ 行)
- `reference_files/policies/profile_policy.yaml` (Profile 別の閾値)
- `reference_files/sdd-templates/sdd_bootstrap.md` (Phase Gate 規範)

### 3. Generate Output (canonical YAML 全セクション埋め)

#### 3.1 frontmatter
- `feature_id` / `basic_design_id` / `title` / `profile` / `version` / `created_at` / `updated_at`
- `owners` (3 人以上: Business / Tech Lead / PMO)
- `reviewers` (Quality / Security / 関連 Lead)

#### 3.2 basic_design YAML

| セクション | 担当 |
|---|---|
| `profile` | Phase 0 で決定した profile |
| `coverage_tier` | enterprise-erp なら `critical` 推奨、saas-integration `standard`、prototype `experimental` |
| `autonomy_bias` | 顧客指示で決定 |
| `ed_cf_score` | coverage_tier の推奨値 |
| `security_sensitive` / `erp_integration` | 案件特性で true/false |
| `organization` | Tecnos Japan / 中期計画 / portfolio_items |
| `delivery_model` | requirements-driven / ftos / hybrid / ddd |
| `raci_plus` | stakeholder_map.yaml から actor を転記 |
| `context.who/what/why` | business_need.yaml + value_canvas.yaml から (要人間確認) |
| `business_domain` | value_chain (O2C/P2P/etc) + capability + domain_objects |
| `scope.in/out` | goal_tree.yaml から |
| `systems` | context_map.yaml から (SAP / mcframe / Salesforce 等) |
| `database` | DB 利用なしなら enabled: false |
| `data_policy` | personal_data 有無、retention policy |
| `agentops_policy` | enabled: true、allowed_action_categories |
| `e2e_policy` | scope: critical-user-journeys / smoke-only / none |
| `bpmn_descriptions` | **`bpmn-authoring` skill が次 step で同期** |
| `flow_reference` | process.bpmn パス |
| `integration_flows` | 重要フロー (KPI 紐付け) |
| `traceability_rows` | RQ→US→AC→BPMN→Test→Task のマッピング |
| `open_questions` / `assumptions` / `decisions` | 各 1+ 項目 |
| `exceptions` | Constitution Article 違反なら必ず記述 (Phase E では空) |

#### 3.3 basic_design_gate_check (全 booleans 真化)

- `traceability_present: true` (traceability_rows 1+ 件)
- `integration_flows_identified: true` (integration_flows 1+ 件)
- `delivery_model_defined: true`
- `raci_plus_defined: true`
- `ai_policy_defined: true`
- `artifact_registry_defined: true`
- `ready_for_bpmn: true`
- `process_bpmn_linked: true`
- `process_bpmn_approved: false` (Gate 2 承認後に Hitoshi さんが手動更新)
- `ready_for_specify: false` (Gate 1+2 後に true)

### 4. Profile 別差分

- **enterprise-erp**: 全セクション full、coverage_tier critical、security_sensitive 高確率
- **saas-integration**: API 中心、systems に SaaS、e2e_policy critical-user-journeys
- **prototype**: 軽量、coverage_tier experimental、open_questions / assumptions 簡略可

### 5. Completion Criteria

- canonical YAML 全セクション埋め
- `traceability_rows` 3+ 件 (RQ→US→AC→BPMN→Test→Task)
- `basic_design_gate_check.ready_for_bpmn: true`
- `/stride:validate <feature>` で basic_design 整合性 pass

## Attributions

- Tecnos-STRIDE canonical schema (TPL-BD-TECNOS-001)。Tecnos Japan Inc.
