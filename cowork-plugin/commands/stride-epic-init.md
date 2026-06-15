---
description: Epic 階層が必要かを判定し、必要なら epic_design.md + feature_breakdown.md を作成。判定基準で不要と判定された場合はファイル生成しない。
argument-hint: "<EPIC_ID> [--features <feat1,feat2>]"
---

# /stride:epic-init

`epic-decomposition` skill を起動し、Epic 階層の必要性を判定 + 必要時のみ生成。

## Usage

```
/stride:epic-init <EPIC_ID> [--features <feat1,feat2>]
```

EPIC_ID 命名: `EPIC-<UPPERCASE_DOMAIN>` (例: `EPIC-ORDER`, `EPIC-SCM`)

## Workflow

### 1. Validate Input
- `--features` 指定なら対象 feature(s) の `basic_design.md` が完成している
- EPIC_ID が `^EPIC-[A-Z0-9]{2,}$` 形式

### 2. Trigger Skill

`epic-decomposition` Skill を auto-trigger:

#### 2.1 判定基準 (Decision Tree)

| 条件 | Epic 化 |
|---|---|
| 2+ team または shared_contracts ≥ 3 | **必須** |
| 1 team + 高複雑度 (BUC ≥ 10 / stakeholder ≥ 8) | 推奨 |
| 1 team + shared_contract 1-2 件 | 推奨 |
| 1 team + 中複雑度 (BUC 5-9) | 任意 |
| prototype profile / 1 team + 低複雑度 | **不要** |

#### 2.2 必須/推奨と判定された場合

- `epics/<EPIC_ID>/epic_design.md` 生成 (canonical Epic schema)
- `epics/<EPIC_ID>/feature_breakdown.md` 生成 (feature 分解)
- (任意) `epics/<EPIC_ID>/epic_flow.bpmn` (横断業務フローがある場合)

#### 2.3 不要と判定された場合

- 判定結果と理由を stdout に出力
- ファイル生成は行わない
- 後で再判定可能

### 3. Output

- 判定結果 (Yes/No + 理由) が stdout 出力
- Yes の場合: `epics/<EPIC_ID>/` 配下のファイル生成

### 4. Next Step

- Epic 階層 = 不要 → `/stride:handoff <feature_name>` で Claude Code 引き渡し
- Epic 階層 = 作成済 → `epics/<EPIC_ID>/EPIC_APPROVAL.md` を Hitoshi さんが承認後、各 feature を Phase 4 で実装
