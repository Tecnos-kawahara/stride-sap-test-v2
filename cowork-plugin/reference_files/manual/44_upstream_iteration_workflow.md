# 44. Upstream Iteration Workflow — 3 反復パターン (Phase B 実装ガイド)

> 本章は Phase B で実装された `stride evaluate --phase discovery` + `upstream_iteration_evaluator.py` を活用した、**bootstrap → structure → refinement** の 3 反復パターンの実践ガイドである。
> Layered Requirements Modeling の段階的精緻化思想を踏襲しつつ、STRIDE 流に loop_bound max=3 で確定運用する。

## 44.1 3 反復パターンの目的

Phase 0 / 0.3 / 0.5 を **1 回で完成形に到達させる** のは現実的でない。多くの案件で観察される「初回は粗く、回を重ねて深まる」性質を **3 反復** として明示的にモデル化する。

| Iteration | 目的 | 評価軸 |
|-----------|------|--------|
| **1: bootstrap** | 網羅性優先・精度無視 | 漏れより重複を許容 |
| **2: structure** | 依存関係で組立て・整合性付与 | 各要素の関連と境界明示 |
| **3: refinement** | 条件・バリエーション・状態で詳細化 | テスタブルな粒度まで落とす |

3 反復で発散・構造化・詳細化が一巡する経験則。Opus 4.7 literal-follow の loop bound (max 5) より厳格に **max 3** に確定 (`shared/policies/upstream_iteration_policy.yaml`)。

## 44.2 各 Iteration の典型 BABOK Technique

### 44.2.1 Iteration 1 — bootstrap (網羅性優先)

`technique_library_query.py --phase phase_0_discovery` で抽出される技法から、**発散系**を選ぶ:

| Technique ID | 和名 | 適用例 |
|--------------|------|--------|
| `brainstorming` | ブレインストーミング | 関係者全員でステークホルダー候補・課題候補を 30 分で発散 |
| `mind_mapping` | マインドマッピング | 中心概念から放射状に課題・価値・関係者を網羅 |
| `stakeholder_list_map_or_personas` | ステークホルダーリスト・マップ・ペルソナ | 影響度マトリクスを粗く描画 |

**Output:** `stakeholder_map.yaml` (3 件以上) + `value_canvas.yaml` (from/to + potential_value/anti_value)

**Iteration 1 完了判定:**
```bash
python3 sdd-templates/tools/upstream_iteration_evaluator.py specs/<feature>/
# iteration_complete: 1 (stakeholder_map + value_canvas が存在)
```

### 44.2.2 Iteration 2 — structure (依存関係付与)

| Technique ID | 和名 | 適用例 |
|--------------|------|--------|
| `functional_decomposition` | 機能分解 | Iteration 1 で出した課題を上位機能 → 下位機能に分解 |
| `process_modelling` | プロセスモデリング | 業務フローを BPMN で可視化 (Phase 1 BPMN への布石) |
| `scope_modelling` | スコープモデリング | In/Out 境界を線引き |

**Output:** `goal_tree.yaml` (root_goal + subgoals 階層) + `change_strategy.yaml` (transition_states + solution_scope)

**Iteration 2 完了判定:**
```bash
python3 sdd-templates/tools/upstream_iteration_evaluator.py specs/<feature>/
# iteration_complete: 2 (goal_tree + change_strategy が存在)
```

### 44.2.3 Iteration 3 — refinement (詳細化)

| Technique ID | 和名 | 適用例 |
|--------------|------|--------|
| `business_rules_analysis` | ビジネスルール分析 | 業務判断を 'IF-THEN' 形式で抽出 |
| `decision_modelling` | 意思決定モデリング | DMN 形式の決定表で表現 |
| `state_modelling` | 状態モデリング | エンティティの取りうる状態と遷移条件を厳密化 |

**Output:** `condition_variation.yaml` (conditions + variations) + `information_state.yaml` (information_items + states + transitions)

**Iteration 3 完了判定:**
```bash
python3 sdd-templates/tools/upstream_iteration_evaluator.py specs/<feature>/
# iteration_complete: 3 (condition_variation + information_state が存在)
```

## 44.3 stride evaluate --phase discovery との連動

各 Iteration 終了時に LLM 評価を回すことで、機械検証では捕まえられない **意味的な発散・収束ギャップ** を検出できる:

```bash
# Iteration 1 完了時
stride evaluate specs/<feature>/ --phase discovery
# → DISCOVERY_RUBRIC の D1 (BACCM Completeness) と D2 (Iteration Progress) を中心に評価
# → "Iteration 1 終わったが Need 軸の opportunity_statement が空欄" などを検出

# Iteration 2 完了時
stride evaluate specs/<feature>/ --phase discovery
# → D1 が 50% → 80% に改善、D2 が 1/3 → 2/3 に進む

# Iteration 3 完了時
stride evaluate specs/<feature>/ --phase discovery
# → D1 100% / D2 3/3 / D3 (Phase 1 Readiness) で blocking_questions 解消確認
```

## 44.4 Profile 別の最小反復数

`shared/policies/upstream_iteration_policy.yaml` の `profile_minimum_iterations`:

| Profile | 最小反復数 | 推奨運用 |
|---------|-----------|---------|
| `enterprise-erp` | 3 | 全 3 反復を完走 (default) |
| `saas-integration` | 2 | bootstrap + structure で十分。refinement は Phase 0.5 内で吸収可 |
| `prototype` | 1 | bootstrap のみで Phase 1 着手可 (PoC 性質) |

## 44.5 アンチパターン

### 44.5.1 反復をスキップして単発実装

❌ Iteration 1 で全 7 ファイルを完璧に書こうとする → 時間切れ・品質ブレ
✅ Iteration 1 では **2 ファイル** (stakeholder + value_canvas) 必達、残りは粗いラフでも可。Iteration 2-3 で構造化 + 詳細化

### 44.5.2 Iteration 4 への突入

❌ Iteration 3 で完成度が足りないと感じて 4 回目を回す
✅ `loop_bound.max_iterations: 3` の規約。3 回で粒度を確定し、不足は Phase 1 Design で補強する

### 44.5.3 Technique 不使用

❌ artifact の中身を直感だけで埋める
✅ 各 Iteration で `technique_library_query.py --phase phase_0_discovery` 等を実行し、適切な BABOK 技法を **明示的に選択** する。`elicitation_plan.yaml` の `techniques` 配列にも記録

## 44.6 LLM 評価レポートの読み方

`specs/<feature>/state/eval_report_discovery_<ts>.md` の典型的な構造:

```markdown
# Discovery Phase Evaluation Report

## Verdict: PASS / WARN / FAIL
- weighted_score: 78 / 100

## D1. BACCM Completeness (50% weight)
- score: 90
- findings:
  - ✓ Change axis: from_state/to_state clearly described
  - ✓ Need axis: problem + opportunity statements distinguishable
  - ⚠ Solution axis: goal_tree.root_goal partially aligned with change_strategy.solution_scope
  - ✓ Stakeholder axis: 5 stakeholders with influence/interest analysis
  - ✓ Value axis: anti_value acknowledged
  - ✓ Context axis: internal + external both addressed

## D2. Iteration Progress (30% weight)
- score: 67
- iteration_complete: 2 / 3
- findings:
  - ✓ Iteration 1: bootstrap indicators present
  - ✓ Iteration 2: structure indicators present
  - ✗ Iteration 3: condition_variation.yaml missing → blocks refinement

## D3. Phase 1 Readiness (20% weight)
- score: 70
- findings:
  - ⚠ blocking_questions: 1 (Q-001 にデフォルト値で埋まっている)
```

このレポートを見て、不足項目を補強 → 再度 evaluate を回すのが基本ループ。

## 44.7 関連章 / 参考

- 39 章 — VALUE Upstream Extension 概要
- 40 章 — BACCM 完全性ゲート
- 41 章 — Layered Requirements Architecture
- 42 章 — Phase 0 → 0.3 → 0.5 → Phase 1 ウォークスルー
- 43 章 — Upstream CLI ガイド (stride upstream init/validate, stride evaluate --phase discovery)
- `shared/policies/upstream_iteration_policy.yaml` — 3 反復 + loop_bound 定義
- `sdd-templates/tools/upstream_iteration_evaluator.py` — 反復進度判定ロジック

## 44.8 Attribution

- **BABOK v3 (IIBA)** — §10 Techniques (50 techniques refs) — fair-use, names + section refs only
- **Layered Requirements Modeling ((concept reference, no proprietary brand))** — phase iteration concept (network → relationship → detail) — fair-use, structural concept only
- 本章の説明文・例文 (LLM 評価レポート例含む) はすべて Claude (Opus 4.7) による独自要約・架空例。原典テキストの逐語的引用は含まない。
