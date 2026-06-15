---
name: layered-context-modelling
description: Tecnos-STRIDE VALUE Upstream Extension の Phase 0 で 4-layer Requirements
  Architecture (System / Business / Condition / Business Use Case) を 5 シートで完成。「Tecnos-STRIDE
  Layered Context Modelling」「4-layer Requirements Architecture」「5-sheet Requirements
  Modeling」「stride-context-model」「VALUE pack Context」「上位コンサル Layered Context」を含む依頼時のみ発火
  (Tecnos-STRIDE 固有語必須)。汎用語の「Context Modelling」「actor」「usecase」「state」単独では発火しない (誤起動回避、WI-VALF01-003)。
argument-hint: <feature_name>
plane: internal
visibility: abstract
return_policy:
  customer: abstract
  platform_admin: abstract
  tecnos_admin: full
---

# Skill: layered-context-modelling

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

このスキルは、4-layer Requirements Architecture (System / Business / Condition / Business Use Case) を 5 シートで完成させ、`specs/<feature>/upstream/phase_0_5_context_modelling/` 配下に成果物を生成します。

## STEP 0: PRE-FLIGHT (MANDATORY — DO THIS FIRST)

> ⛔ **STOP.** auto-fire でこの skill が起動された場合でも、4-layer Requirements Architecture
> の定義 + 5 templates + Article XVI は context に自動 load されない。手動で Read してから着手すること。

### 必須 Read リスト (順番厳守)

1. `${CLAUDE_PLUGIN_ROOT}/reference_files/manual/41_layered_requirements_modeling_guide.md` — 4-layer Requirements Architecture 解説
2. `${CLAUDE_PLUGIN_ROOT}/reference_files/constitution_amendments/XVI_layered_requirement_architecture.md` — Article XVI 仕様
3. `${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/actor_system_template.yaml`
4. `${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/business_usecase_template.yaml`
5. `${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/requirements_architecture_template.yaml`

### 必須実行コマンド (template-copy 強制)

```bash
mkdir -p specs/<feature>/upstream/phase_0_5_context_modelling
for f in actor_system business_usecase information_state condition_variation requirements_architecture; do
  cp ${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/${f}_template.yaml \
     specs/<feature>/upstream/phase_0_5_context_modelling/${f}.yaml
done
# 大型 BUC を分解する場合のみ
# cp ${CLAUDE_PLUGIN_ROOT}/reference_files/templates/upstream/usecase_complex_template.yaml \
#    specs/<feature>/upstream/phase_0_5_context_modelling/usecase_complex.yaml
```

### 🚫 ANTI-PATTERN

| 違反 | 正しい行動 |
|---|---|
| 4 layer を区別せず 1 シートで合成 | System / Business / Condition / BUC を 5 シートに分割 |
| broken_link を残したまま完成宣言 | requirements_architecture.yaml の cross-layer ref を全件解決 |
| Phase 0 Discovery / Elicit 結果を再利用せず重複定義 | stakeholder_map / context_map / elicitation_results を Read してから着手 |

### Output of STEP 0

```
[PRE-FLIGHT REPORT]
  read: 41_layered_requirements_modeling_guide.md (✓)
  read: Article XVI amendment (✓)
  read: 5 yaml templates (✓)
  templates_copied: 5 yaml files (BUC 分解版は scope 次第)
  prerequisites_verified: phase_0_discovery + phase_0_3_elicit complete (✓)
  ready_to_proceed: true
```

---

## Usage

```
/stride:context-model <feature_name>
```

## Workflow

### 1. Understand the Input

- Phase 0 Discovery (`baccm-discovery`) と Elicit (`babok-elicitation`) の成果物を読む (前提)
- 特に `stakeholder_map.yaml` から actor 一覧、`context_map.yaml` から system 一覧を取得

### 2. Reference Files

- `reference_files/manual/41_layered_requirements_modeling_guide.md` (4-layer Requirements Architecture 解説)
- `reference_files/templates/upstream/actor_system_template.yaml`
- `reference_files/templates/upstream/business_usecase_template.yaml`
- `reference_files/templates/upstream/information_state_template.yaml`
- `reference_files/templates/upstream/condition_variation_template.yaml`
- `reference_files/templates/upstream/requirements_architecture_template.yaml`
- `reference_files/templates/upstream/usecase_complex_template.yaml` (大型 BUC を分解する場合)

### 3. Generate Output (5 シート、順序厳守)

#### 3.1 System Layer → `actor_system.yaml`
- actor (人 / 役割) と system (社内 IT / 外部 SaaS) を明示
- stakeholder_map.yaml の actor を引用しつつ、システム視点で整理

#### 3.2 Business Layer → `business_usecase.yaml`
- 業務ユースケース (UC-001, UC-002, ...) を 5+ 件以上
- 各 UC は「actor が system を使って X を実現する」形式
- ID 命名規約は `UC-NNN` (3 桁数字)
- 大型 UC は §3.3 で `usecase_complex_<NNN>.yaml` に分解

#### 3.3 Condition Layer → `condition_variation.yaml`
- 業務イベント (顧客来店 / 月次締め / API 着信 等) と、それぞれの状態変化
- value_chain (O2C / P2P / R2R) 単位で整理

#### 3.4 BUC Layer → `information_state.yaml`
- 情報モデル (entity 一覧)
- 各 entity の state (ライフサイクル: draft → active → archived 等)
- Business Use Case との関連

#### 3.5 Architecture → `requirements_architecture.yaml`
- 上記 4 シートを統合した要件アーキテクチャ図
- BACCM 6 軸との整合性を再確認
- Phase 1 (basic_design.md) への引き渡し前提を整理

### 4. 大型 BUC の分解 (任意、必要時のみ)

`business_usecase.yaml` の 1 UC が複雑すぎる場合 (sub-flow 5+ / 関連 entity 5+ 等):
- `usecase_complex_<NNN>.yaml` に分解 (`<NNN>` は元 UC の 3 桁数字)
- 各 sub-flow を独立した step として記述

### 5. Completion Criteria

- 5 シート全て生成済
- `business_usecase.yaml` に 5+ 件の UC、ID は `UC-NNN` 形式
- `/stride:validate <feature>` で 4-layer Requirements Architecture pass
- 大型 BUC があれば `usecase_complex_<NNN>.yaml` で分解

## Attributions

- **4-layer Requirements Architecture**: System / Business / Condition / Business Use Case の 4 階層 + 5-sheet 構造の概念を採用 (考え方のみ、固有商標名は使用しない)
