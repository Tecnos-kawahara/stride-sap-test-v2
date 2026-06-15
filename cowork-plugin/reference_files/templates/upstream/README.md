# Tecnos-STRIDE Upstream Extension — Template Index (Phase A)

> Tecnos-STRIDE v5.4 + VALUE Upstream Extension (codename: VALUE) Phase A
> 15 artifact templates + 4 policy YAML の索引。
> Phase A: スキーマ定義のみ。ツール実装 (`stride upstream init / validate`、evaluator `--discovery`) は Phase B 以降。

## Policies (`shared/policies/`)

| File | 役割 |
|------|------|
| `upstream_policy.yaml` | Phase 0 / 0.3 / 0.5 の成果物・Profile 適用度・Phase A 制約 |
| `baccm_completeness.yaml` | BACCM 6 軸 (Change/Need/Solution/Stakeholder/Value/Context) の完全性ゲート定義 |
| `technique_library.yaml` | BABOK v3 §10 の 50 技法カタログ (id / name / purpose / typical_phase) |
| `upstream_iteration_policy.yaml` | 3-iteration pattern (bootstrap → structure → refinement) と loop bound |

## Templates (`sdd-templates/templates/upstream/`)

### Phase 0 — Discovery (BABOK KA6, Gate 0)

| ファイル | 3-letter | BABOK Source | Layered Requirements Modeling Source | 匠 Source | 責務 |
|---------|---------|-------------|-------------|----------|------|
| `business_need_template.yaml` | BNE | KA6.1 / 6.2 | n/a | 価値分析モデル | 解決すべき問題 / 活用すべき機会の明文化 (BACCM Need 軸) |
| `value_canvas_template.yaml` | VLC | KA6 / Technique 10.8 | n/a | 価値モデル | from_state / to_state / potential_value / anti_value (BACCM Change + Value 軸) |
| `stakeholder_map_template.yaml` | SHM | KA6 / Technique 10.43 | アクター図 | ステークホルダーモデル | 関係者の影響度 / 関心 / 支持度を 3 件以上整理 (BACCM Stakeholder 軸) |
| `context_map_template.yaml` | CTX | KA6 | システムコンテキスト図 | コンテキストモデル | 内外環境・規制・連携対象 (BACCM Context 軸) |
| `risk_register_template.yaml` | RRG | KA6 / Technique 10.38 | n/a | n/a | リスクの識別・評価・対応計画 |
| `change_strategy_template.yaml` | CHS | KA6.4 | n/a | 変革ロードマップ | 中間状態 / 解決手段 / 段階的展開計画 (BACCM Change + Solution 軸) |
| `goal_tree_template.yaml` | GLT | KA6.2 | n/a | 目的階層ツリー | 最上位ゴール → サブゴールの階層分解 (BACCM Solution 軸) |

### Phase 0.3 — Elicitation (BABOK KA4, Gate 0.3)

| ファイル | 3-letter | BABOK Source | Layered Requirements Modeling Source | 匠 Source | 責務 |
|---------|---------|-------------|-------------|----------|------|
| `elicitation_plan_template.yaml` | ELP | KA4.1 | n/a | n/a | 採用技法 / 対象 SH / スケジュール / リソース |
| `elicitation_results_template.yaml` | ELR | KA4.2 / 4.3 | n/a | n/a | findings / 未解決質問 / 矛盾 / 保留トピック |

### Phase 0.5 — Context Modelling (BABOK KA7, Gate 0.5)

| ファイル | 3-letter | BABOK Source | Layered Requirements Modeling Source | 匠 Source | 責務 |
|---------|---------|-------------|-------------|----------|------|
| `actor_system_template.yaml` | ACS | KA7.1 | アクター・外部システム図 | n/a | アクター + 連携システムの体系化 |
| `business_usecase_template.yaml` | BUC | KA7 / Technique 10.47 | ビジネスユースケース図 | n/a | BUC + actor + trigger + outcome |
| `information_state_template.yaml` | INS | KA7 / Technique 10.11 / 10.44 | 情報モデル / 状態モデル | n/a | エンティティ + 状態 + 遷移 |
| `condition_variation_template.yaml` | CVR | KA7 / Technique 10.9 / 10.17 | 条件・バリエーションモデル | n/a | ビジネスルール + 決定表 |
| `usecase_complex_template.yaml` | UCX | KA7.1 | UC 複合図 | n/a | BUC × Actor × Information × Condition の交差点 |
| `requirements_architecture_template.yaml` | RAR | KA7.5 | 要求アーキテクチャ (4-layer) | 価値→目的→業務→システム階層 | Layered Requirements Modeling System / Business / BusinessUseCase / Conditions レイヤー連結 |

## Common Frontmatter

各テンプレートは以下の共通フロントマター + YAML 本体構造を持つ:

```yaml
---
# Template: <artifact_name>
# Phase: <phase_X>
# BABOK Source: <KA-X.Y task or technique name>
# Layered Requirements Modeling Source: <該当ダイアグラム名 or "n/a">
# Inspired by: <value-driven discovery method の該当モデル名 or "n/a">
# Rule-0: 正本は YAML フロントマター + 下記 YAML ブロック
---

artifact: "<artifact_name>"
template_id: "TPL-UP-<3-letter>-001"
feature_id: "FEAT-XXX"
upstream_artifact_id: "<3-letter>-XXX"
title: "<Title> - <Feature Name>"
version: "{{TEMPLATE_VERSION}}"
status: "draft"
phase: "<phase_X>"
profile_applicability: ["enterprise-erp", "saas-integration", "prototype"]
owners: []
reviewers: []
links:
  upstream_policy_ref: "shared/policies/upstream_policy.yaml"
  baccm_completeness_ref: "shared/policies/baccm_completeness.yaml"
  iteration_policy_ref: "shared/policies/upstream_iteration_policy.yaml"
  constitution_ref: "memory/constitution.md"
  amendment_ref: "memory/constitution_amendments/<該当 Article>.md"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"

# 各テンプレ固有のフィールド
```

## Phase B 予定機能

- `stride upstream init <feature>` — 15 templates 一括 scaffold
- `stride upstream validate <feature>` — BACCM 6 軸完全性 + JSON Schema 検証
- `stride evaluate --discovery` — Multi-Model Evaluator の Discovery phase 拡張
- `stride upstream iterate` — 3-iteration pattern の進行管理

## Attributions

- **BABOK v3 (IIBA)** — framework backbone (KA4 / KA6 / KA7 / §10 Techniques) — fair-use, names and section refs only
- **Layered Requirements Modeling ((concept reference, no proprietary brand))** — structural integrity (4-layer architecture, diagram names) — fair-use, layer/diagram names only
- **value-driven discovery (philosophical foundation)** — philosophical inspiration (value design models) — fair-use, model names only

原典テキストの長文転記は行わず、`purpose` / 説明文は Claude による独自要約。各ファイル末尾に `attributions:` を必ず付記する。
