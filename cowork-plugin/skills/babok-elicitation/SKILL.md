---
name: babok-elicitation
description: Tecnos-STRIDE VALUE Upstream Extension の Phase 0 で BABOK KA4 (Elicitation)
  を実施。50 technique から context 別に 5 件推奨し、対話で elicitation_plan.yaml + elicitation_results.yaml
  を完成。「Tecnos-STRIDE Phase 0 Elicit」「BABOK Elicitation」「stride-elicit」「BABOK 50 technique」「VALUE
  pack Elicitation」「上位コンサル Elicit」を含む依頼時のみ発火 (Tecnos-STRIDE 固有語必須)。汎用語の「インタビュー」「ワークショップ」「Brainstorming」単独では発火しない
  (誤起動回避、WI-VALF01-003)。
argument-hint: <feature_name>
plane: internal
visibility: abstract
return_policy:
  customer: abstract
  platform_admin: abstract
  tecnos_admin: full
---

# Skill: babok-elicitation

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

このスキルは、BABOK Knowledge Area 4 (Elicitation) を実施し、`specs/<feature>/upstream/phase_0_3_elicit/` 配下に `elicitation_plan.yaml` + `elicitation_results.yaml` を生成します。

## STEP 0: PRE-FLIGHT (MANDATORY — DO THIS FIRST)

> ⛔ **STOP.** auto-fire でこの skill が起動された場合でも、50 technique のカタログ +
> 2 templates は context に自動 load されない。手動で Read してから対話を開始すること。

### 必須 Read リスト (順番厳守)

1. `${CLAUDE_PLUGIN_ROOT}/reference_files/policies/technique_library.yaml` — BABOK 50 technique カタログ
2. `${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/elicitation_plan_template.yaml`
3. `${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/elicitation_results_template.yaml`
4. `${CLAUDE_PLUGIN_ROOT}/reference_files/manual/42_upstream_phases_walkthrough.md` — Phase 0.3 walkthrough

### 必須実行コマンド (template-copy 強制)

```bash
mkdir -p specs/<feature>/upstream/phase_0_3_elicit
cp ${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/elicitation_plan_template.yaml \
   specs/<feature>/upstream/phase_0_3_elicit/elicitation_plan.yaml
cp ${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/elicitation_results_template.yaml \
   specs/<feature>/upstream/phase_0_3_elicit/elicitation_results.yaml
```

### 🚫 ANTI-PATTERN

| 違反 | 正しい行動 |
|---|---|
| 50 technique を見ずに 1-2 件のみ提案 | technique_library.yaml から context 別に 5 件推奨 |
| Phase 0 Discovery 未参照で Elicit 開始 | stakeholder_map.yaml + context_map.yaml を Read してから対話 |
| 結果 yaml に source / decision_rationale を未記録 | 全 elicitation result に actor / technique / source を明記 |

### Output of STEP 0

```
[PRE-FLIGHT REPORT]
  read: technique_library.yaml (50 techniques) (✓)
  read: elicitation_plan_template.yaml (✓)
  read: elicitation_results_template.yaml (✓)
  templates_copied: 2 yaml files
  prerequisites_verified: stakeholder_map.yaml + context_map.yaml exist (✓)
  ready_to_proceed: true
```

---

## Usage

```
/stride:elicit <feature_name>
```

## Workflow

### 1. Understand the Input

- Phase 0 Discovery (`baccm-discovery` skill) の成果物を読む (前提)
- `specs/<feature>/upstream/phase_0_discovery/stakeholder_map.yaml` から actor 一覧を取得

### 2. Reference Files

- `reference_files/policies/technique_library.yaml` (BABOK 50 technique カタログ)
- `reference_files/templates/upstream/elicitation_plan_template.yaml`
- `reference_files/templates/upstream/elicitation_results_template.yaml`
- `reference_files/manual/42_upstream_phases_walkthrough.md` (Phase 0.3 walkthrough)

### 3. Generate Output

#### 3.1 50 technique から 5 件推奨

`reference_files/policies/technique_library.yaml` から context (案件 profile / 規模 / stakeholder 数) に応じて以下のような組み合わせで推奨:

- **enterprise-erp 大型 PJ (stakeholder 5-7 階層)**:
  - Brainstorming (発散的アイデア出し)
  - Document Analysis (既存仕様書レビュー)
  - Interviews (キーマン個別ヒアリング)
  - Workshops (合意形成)
  - Process Modelling (As-Is/To-Be 整理)
- **saas-integration 中規模 PJ**:
  - Document Analysis (SaaS 公式ドキュメント / API 仕様書)
  - Interviews (SaaS ベンダ TS / 社内利用部門)
  - Prototyping (連携 PoC 実機検証)
  - Survey (関連部署アンケート)
  - Observation (現行運用観察)
- **prototype 小規模 PJ**:
  - Brainstorming
  - Interviews (1-2 名)
  - Prototyping (動かして学ぶ)

コンサルが提示された 5 件から **3-5 件を選択** (重複可、優先度を付与)。

#### 3.2 `elicitation_plan.yaml` 生成

選択した technique ごとに:
- 対象 stakeholder
- 想定スケジュール (week 単位)
- 期待 outcome
- 成功基準

#### 3.3 `elicitation_results.yaml` 生成

実施後に以下を記録 (このスキルでは plan のみ生成、results は実施後に追記):
- 実施 technique 名
- 実施日 / 参加者
- 抽出された要件・課題・前提
- BACCM 6 軸へのフィードバック (どの軸を refinement したか)

### 4. Completion Criteria

- 3-5 technique が elicitation_plan.yaml に記載済
- 各 technique に対象 stakeholder + スケジュール + 期待 outcome 明記
- `/stride:validate <feature>` で elicitation_plan が pass
- (実施後追記) elicitation_results.yaml に少なくとも 1 件の実施記録

## Attributions

- **BABOK v3 (IIBA)**: KA4 Elicitation の 50 technique カタログ。fair-use, technique names only
