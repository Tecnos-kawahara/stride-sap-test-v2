# 43. Upstream CLI ガイド (Phase B)

> Tecnos-STRIDE v5.5 + VALUE Upstream Extension Phase B
> Phase A で導入した schema 基盤 (BACCM 6軸 / 15 templates / 50 BABOK techniques) を `stride upstream init/validate` / `stride lint --upstream` / `stride evaluate --phase discovery` として実コマンドで利用するための運用ガイド。

## 43.1 概要

Phase B では Phase A の上流フェーズ (Phase 0 / 0.3 / 0.5) を **実コマンド化** する 4 つの拡張を提供する。

| コマンド | 役割 | 実装ロジック |
|---------|------|-------------|
| `stride upstream init <feature> --phase <phase>` | Phase 0/0.3/0.5 scaffold 生成 | `sdd-templates/tools/upstream_scaffolder.py` |
| `stride upstream validate <feature>` | BACCM 6 軸完全性 + 構造 lint | `baccm_completeness_checker.py` + `upstream_lint.py` |
| `stride lint --upstream <feature_path>` | upstream/ に焦点を絞った lint (alias) | `stride_lint.py` の `--upstream` フラグ |
| `stride evaluate <feature_path> --phase discovery` | LLM による Discovery 完成度評価 | `multi_model_evaluator.py` の `--phase discovery` 拡張 |

## 43.2 stride upstream init — Phase 0/0.3/0.5 scaffold

### 43.2.1 基本書式

```bash
stride upstream init <feature> --phase <phase> [--profile <profile>]
```

- `feature`: snake_case の feature_name (例: `val_b01`、`order_import`)
- `phase`: `discovery` | `elicit` | `context_modelling` (kebab-case `context-modelling` も受付、内部正規化)
- `profile`: `enterprise-erp` (default) | `saas-integration` | `prototype`

### 43.2.2 各 Phase の生成物

| Phase | 生成数 | artifacts |
|-------|--------|-----------|
| `discovery` (BABOK KA6) | 7 (enterprise/saas) / 2 (prototype lite) | business_need.yaml, value_canvas.yaml, stakeholder_map.yaml, context_map.yaml, risk_register.yaml, change_strategy.yaml, goal_tree.yaml |
| `elicit` (BABOK KA4) | 2 | elicitation_plan.yaml, elicitation_results.yaml |
| `context_modelling` (BABOK KA7 / Layered Requirements Modeling) | 6 | actor_system.yaml, business_usecase.yaml, information_state.yaml, condition_variation.yaml, usecase_complex.yaml, requirements_architecture.yaml |

### 43.2.3 配置先

```
specs/<feature>/upstream/
  ├── phase_0_discovery/
  │   ├── business_need.yaml
  │   ├── value_canvas.yaml
  │   └── ... (7 ファイル / prototype は 2)
  ├── phase_0_3_elicit/
  │   ├── elicitation_plan.yaml
  │   └── elicitation_results.yaml
  └── phase_0_5_context_modelling/
      ├── actor_system.yaml
      └── ... (6 ファイル)
```

### 43.2.4 Profile 別の挙動 (lite mode)

`prototype` profile の `discovery` phase では **stakeholder_map + value_canvas の 2 ファイルのみ** に絞り込まれる (Profile-aware 振る舞い、`shared/policies/upstream_policy.yaml` の `profile_applicability` で定義)。

### 43.2.5 既存 artifact の上書き

既存ファイルが存在する場合、`stride upstream init` は **上書きせずに skip** する。スキップしたファイルは出力に列挙される。再生成したい場合は事前に削除が必要。

## 43.3 stride upstream validate — BACCM 完全性 + 構造 lint

### 43.3.1 基本書式

```bash
stride upstream validate <feature> [--phase <phase>]
```

- 引数 `<feature>` のみ必須。`--phase` は省略可 (省略時は全 Phase 0/0.3/0.5 を統合検証)。

### 43.3.2 検証内容

| 観点 | 検証手段 | 失敗時の lint コード |
|------|---------|--------------------|
| BACCM 6 軸完全性 | `baccm_completeness.yaml` の `source_artifacts.required_keys` / `required_min_count` 充足判定 | `BACCM_INCOMPLETE` |
| Layered Requirements Modeling cross_layer_links 整合性 | `requirements_architecture.yaml` の link 切れ検出 | `Layered Requirements Modeling_BROKEN_LINK` |
| template_id 整合 | upstream artifact の frontmatter `template_id` が `^TPL-UP-[A-Z]{3,4}-[0-9]{3}$` に一致 + 登録テンプレと整合 | `UPSTREAM_TEMPLATE_DRIFT` |
| BABOK technique 参照 | `elicitation_plan.yaml` の `techniques` が 50-technique library 内の id を参照 | `BABOK_TECHNIQUE_UNKNOWN` |

### 43.3.3 終了コード

- `0`: 全検証 PASS
- `1`: 1 件以上の lint 違反検出
- `2`: 内部エラー (policy ファイル不在、YAML parse 失敗等)

## 43.4 stride lint --upstream — alias

```bash
stride lint --upstream specs/<feature>/
```

`stride upstream validate <feature>` とほぼ同等で、内部的に `lint_upstream(feature_dir, config, result)` を呼び出す。違いは下記のみ:

| 項目 | `stride upstream validate` | `stride lint --upstream` |
|------|---------------------------|-------------------------|
| 引数 | `<feature>` (snake_case name) | `<feature_path>` (`specs/<feature>/`) |
| 出力フォーマット | BACCM 結果中心 | stride lint 標準 (text/json/ndjson) |
| 既存 lint 統合 | upstream のみ | feature 全体 lint の一部として upstream を含む |

## 43.5 stride evaluate --phase discovery — LLM 評価

```bash
stride evaluate specs/<feature>/ --phase discovery
```

`multi_model_evaluator.py` の v5.5 Phase B 拡張で、Discovery phase の LLM 評価を提供する。

### 43.5.1 評価軸 (DISCOVERY_RUBRIC)

- **D1. BACCM Completeness (50%)**: 6 軸 (Change/Need/Solution/Stakeholder/Value/Context) の意味的充足
- **D2. Iteration Progress (30%)**: bootstrap → structure → refinement の 3 反復進度
- **D3. Phase 1 Readiness (20%)**: blocking_questions 解消 + Phase 0 → Phase 1 ハンドオフ可能性

### 43.5.2 出力

`specs/<feature>/state/eval_report_discovery_<timestamp>.md` に評価レポートが書き出される。`PASS / WARN / FAIL` の判定に加え、各軸の詳細フィードバックを含む。

### 43.5.3 既存 phase との互換性

`design` / `specify` / `tasking` の挙動は完全に変更されていない。`discovery` は新規追加された 4 つ目の choices。

## 43.6 4 新エラーコード詳細

### `BACCM_INCOMPLETE`

- **発火条件**: BACCM 6 軸のいずれかで `source_artifacts.required_keys` が空欄、または `required_min_count` (例: stakeholders ≥ 3) 未充足
- **解消方法**: `stride upstream init <feature> --phase discovery` で scaffold 再生成 + 該当 YAML の必須キーを記入
- **参照**: `manual/40_baccm_guide.md` (BACCM 6 軸詳細)

### `Layered Requirements Modeling_BROKEN_LINK`

- **発火条件**: `requirements_architecture.yaml` の `cross_layer_links` で参照されている `from_id` / `to_id` が、対応するレイヤーの `items` に存在しない
- **解消方法**: layer items にエントリを追加するか、cross_layer_links から削除
- **参照**: `manual/41_layered_requirements_modeling_guide.md` (4 レイヤー連結)

### `UPSTREAM_TEMPLATE_DRIFT`

- **発火条件**: upstream artifact の `template_id` が `^TPL-UP-[A-Z]{3,4}-[0-9]{3}$` に一致しない、または登録済みテンプレに存在しない
- **解消方法**: `sdd-templates/templates/upstream/<template>.yaml` の frontmatter `template_id` に揃える

### `BABOK_TECHNIQUE_UNKNOWN`

- **発火条件**: `elicitation_plan.yaml` の `techniques` 配下に、50 件の `technique_library.yaml` に存在しない id がある
- **解消方法**: `stride upstream technique-list` (Phase C 予定) で 50 件一覧を確認し、id を訂正

## 43.7 典型的なワークフロー

### 43.7.1 新規 feature 着手 → Phase 1 Design 着手前

```bash
# 1. feature scaffold
stride init order_import --profile enterprise-erp

# 2. Phase 0 Discovery scaffold
stride upstream init order_import --phase discovery

# 3. specs/order_import/upstream/phase_0_discovery/*.yaml を編集
# (BABOK 50 technique ライブラリ参照: python3 sdd-templates/tools/technique_library_query.py --phase phase_0_discovery)

# 4. BACCM 完全性確認
stride upstream validate order_import

# 5. LLM 評価 (任意)
stride evaluate specs/order_import/ --phase discovery

# 6. Phase 0.3 Elicitation
stride upstream init order_import --phase elicit

# 7. Phase 0.5 Context Modelling
stride upstream init order_import --phase context_modelling

# 8. 全 Phase の統合検証
stride upstream validate order_import

# 9. Phase 1 Design 着手 → basic_design.md 編集
```

### 43.7.2 既存 feature の途中 Phase からの再開

```bash
# 既存の Phase 0 完成度を評価
stride upstream validate order_import --phase discovery
stride evaluate specs/order_import/ --phase discovery

# 不足分を補強 (既存 artifact は skip される)
stride upstream init order_import --phase discovery
```

## 43.8 Phase C 申し送り

Phase B では実装されない機能 (Phase C 以降):

- `stride upstream-bridge <feature>`: Phase 0 → Phase 1 (basic_design.md) の半自動 populate
- `stride upstream technique-list --phase X`: 50 BABOK technique の Phase 別フィルタ表示
- `stride upstream iterate <feature> --iter <N>`: 3 反復パターン進行管理
- Constitution 本体への Article XV / XVI / XVII 正式マージ
- 稼働後評価 (Article XVII の `stride evaluate --post-deployment`)

## 43.9 関連章 / 参考

- 39 章 — VALUE Upstream Extension 概要
- 40 章 — BACCM 完全性ゲート (Phase 0 詳細)
- 41 章 — Layered Requirements Architecture (Phase 0.5)
- 42 章 — Phase 0 → 0.3 → 0.5 → Phase 1 ウォークスルー
- 44 章 — Upstream Iteration Workflow (3 反復パターン詳細)
- `shared/policies/upstream_policy.yaml` — Phase / artifact / Profile 適用度
- `shared/policies/baccm_completeness.yaml` — BACCM 6 軸 + required_keys

## 43.10 Attribution

- **BABOK v3 (IIBA)** — KA4 / KA6 / KA7 / §10 Techniques refs — fair-use, names and section refs only
- **Layered Requirements Modeling ((concept reference, no proprietary brand))** — 4-layer architecture concept refs — fair-use, layer/diagram names only
- 本章の説明文はすべて Claude (Opus 4.7) による独自要約。原典テキストの逐語的引用は含まない。
