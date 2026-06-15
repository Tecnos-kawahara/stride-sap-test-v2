---
name: epic-decomposition
description: Tecnos-STRIDE SDD で Epic 階層化判定 + epic_design.md + feature_breakdown.md
  を作成。「Tecnos-STRIDE Epic」「Epic 階層化」「stride-epic-init」「VALUE pack Epic」「epic_design.md」「feature_breakdown.md」「shared_contracts」を含む依頼時のみ発火
  (Tecnos-STRIDE 固有語必須)。汎用語の「Epic」「複数チーム」「大規模」単独では発火しない (誤起動回避、WI-VALF01-003)。Phase
  1 設計後に Epic 階層化が必要かをチェックする役割。
argument-hint: <EPIC_ID> [--features <feat1,feat2>]
plane: internal
visibility: abstract
return_policy:
  customer: abstract
  platform_admin: abstract
  tecnos_admin: full
---

# Skill: epic-decomposition

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

このスキルは、Phase 1 完成後に **Epic 階層が必要かを判定** し、必要時のみ `epics/<EPIC_ID>/epic_design.md` + `feature_breakdown.md` を生成します。

## STEP 0: PRE-FLIGHT (MANDATORY — DO THIS FIRST)

> ⛔ **STOP.** auto-fire でこの skill が起動された場合でも、Article X (Epic-Feature Hierarchy) +
> 4 templates は context に自動 load されない。手動で Read してから判定を開始すること。

### 必須 Read リスト (順番厳守)

1. `${CLAUDE_PLUGIN_ROOT}/reference_files/constitution.md` Article X — Epic-Feature Hierarchy 規範
2. `${CLAUDE_PLUGIN_ROOT}/reference_files/templates/epic_design_template.md` — Epic canonical schema
3. `${CLAUDE_PLUGIN_ROOT}/reference_files/templates/feature_breakdown_template.md` — feature 分解 canonical
4. `${CLAUDE_PLUGIN_ROOT}/bpmn/templates/epic_flow_template.bpmn` — Epic レベル BPMN canonical (必要時)
5. `${CLAUDE_PLUGIN_ROOT}/bpmn/PRE_FLIGHT_CHECKLIST.md` — BPMN 連携 (epic_flow.bpmn 作成時)

### 必須実行コマンド (template-copy 強制)

```bash
# Epic 階層が必要と判定された場合のみ
mkdir -p epics/<EPIC_ID>
cp ${CLAUDE_PLUGIN_ROOT}/reference_files/templates/epic_design_template.md \
   epics/<EPIC_ID>/epic_design.md
cp ${CLAUDE_PLUGIN_ROOT}/reference_files/templates/feature_breakdown_template.md \
   epics/<EPIC_ID>/feature_breakdown.md
# epic_flow.bpmn が必要な場合は bpmn-authoring の STEP 0 PRE-FLIGHT を経由すること
```

### 🚫 ANTI-PATTERN

| 違反 | 正しい行動 |
|---|---|
| Epic 階層判定を省いて常に作成 | profile + UC 数 + actor 数で判定、不要なら作らない |
| epic_flow.bpmn を bpmn-authoring の PRE-FLIGHT を経ずに作成 | epic_flow.bpmn は bpmn-authoring skill の STEP 0 を経由 (template copy + lint) |
| feature_breakdown.md に shared_contracts を未列挙 | cross-feature 依存は shared_contracts に明示 (CT-* / SC-*) |

### Output of STEP 0

```
[PRE-FLIGHT REPORT]
  read: constitution.md Article X (✓)
  read: epic_design_template.md (✓)
  read: feature_breakdown_template.md (✓)
  decision: <"hierarchy needed" | "single feature OK">
  templates_copied: <0 | 2 | 3 (with epic_flow.bpmn via bpmn-authoring)>
  ready_to_proceed: true
```

---

## Usage

```
/stride:epic-init <EPIC_ID> [--features <feat1,feat2>]
```

EPIC_ID 命名: `EPIC-<UPPERCASE_DOMAIN>` (例: `EPIC-ORDER`, `EPIC-SCM`)

## Workflow

### 1. Understand the Input

- 対象 feature(s) の `basic_design.md` を読む
- 関連 stakeholder_map.yaml から actor 数、business_usecase.yaml から UC 数を取得
- profile を確認

### 2. Reference Files

- `reference_files/templates/epic_design_template.md` (Epic 設計 canonical)
- `reference_files/templates/feature_breakdown_template.md` (feature 分解 canonical)
- `reference_files/templates/epic_progress_report_template.md` (進捗レポート、必要時)
- `reference_files/templates/epic_flow_template.bpmn` (Epic レベル BPMN、必要時)
- `reference_files/constitution.md` Article X (Epic-Feature Hierarchy)

### 3. 判定基準 (Decision Tree)

#### 3.1 必須 (Epic 化マスト)

以下のいずれか 1 つでも当てはまれば **Epic 階層必須**:

- **複数チーム** (Article X 規定): 2 team 以上が関与
- **shared_contracts ≥ 3**: 複数 feature が共有する API/Event/File contract が 3 件以上

#### 3.2 推奨 (Epic 化しても良い)

- **1 team + 高複雑度**: BUC ≥ 10、stakeholder ≥ 8、データエンティティ ≥ 15
- **shared_contracts ≥ 1**: 複数 feature が同一 contract を参照

#### 3.3 任意 (Epic 化は判断による)

- **1 team + 中複雑度**: BUC 5-9、stakeholder 5-7
- 開発期間が 3 ヶ月以上の場合は Epic 化推奨

#### 3.4 不要 (Epic 階層作らない)

- **prototype profile** (社内 PoC、短命ツール): Epic 階層は冗長
- **1 team + 低複雑度**: BUC ≤ 4、stakeholder ≤ 4
- **単一 feature** (関連 feature がない、shared_contract なし)

### 4. Generate Output (Epic 化判定 = はい の場合のみ)

#### 4.1 `epics/<EPIC_ID>/epic_design.md`

`reference_files/templates/epic_design_template.md` をベースに:

- frontmatter: `epic_id`, `title`, `version`, `owners` (Epic Owner / Tech Lead)
- canonical YAML:
  - `epic` セクション (vision / strategic_goal / KPIs / scope_boundary)
  - `features[]` (各 feature_id + 概要)
  - `shared_contracts[]` (3+ 件、API/Event/File 別)
  - `dependencies` (feature 間 + 外部システム)
  - `team_allocation` (各 feature に team 割当)
  - `epic_gate_check`

#### 4.2 `epics/<EPIC_ID>/feature_breakdown.md`

`reference_files/templates/feature_breakdown_template.md` をベースに:

- 各 feature の概要 (1 段落 / feature)
- feature 間の依存関係マトリクス
- 共通 contract / 共通 library / 共通テスト戦略

#### 4.3 (任意) `epic_flow.bpmn`

複数 feature の業務フローが横断する場合のみ。`reference_files/templates/epic_flow_template.bpmn` をベース。

### 5. Generate Output (Epic 化判定 = いいえ の場合)

- 判定結果を stdout に出力 (理由を明示):
  - 例: `Epic 階層不要: profile=prototype + 1 team + BUC 3 件で軽量、Article X 規定外`
- ファイル生成は行わない
- 後で Epic 化が必要になった場合は再起動可能

### 6. Completion Criteria

- 判定結果 (Yes/No + 理由) が stdout 出力済
- Yes の場合: `epics/<EPIC_ID>/epic_design.md` + `feature_breakdown.md` 生成済
- (任意) `epic_flow.bpmn` 生成済 (該当する場合)

## Attributions

- Tecnos-STRIDE Constitution Article X (Epic-Feature Hierarchy)。Tecnos Japan Inc.
