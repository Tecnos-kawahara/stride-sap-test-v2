---
description: VALUE pack (Phase 1) + Spec/Plan (Phase 2) 完成後、SDD Phase 3 (Tasking) を 1 コマンドで進める。tasks.md scaffold + work_items/WI-*.md scaffold を生成し、AI Plan Agent → AI Task Agent の橋渡しを担う。
argument-hint: "<feature_name>"
---

# /stride:tasking

VALUE pack (Phase 1) + Spec/Plan (Phase 2) 完成後の **SDD Phase 3 (Tasking)** を 1 コマンドで進めます。`tasks.md` の scaffold + `work_items/WI-*.md` scaffold を生成し、Phase 4 (Execute) 着手準備を整えます。

> Phase F-1 緊急 新規 (WI-VALF01-016 / 改善要望-15、★ v2 P0-3): VALUE pack → Phase 3 (tasking) を 1 コマンドで連結、Phase 3 を機械化。

## Usage

```
/stride:tasking <feature_name>
```

## Workflow

### 1. Validate Input (前提条件確認)

- `specs/<feature_name>/basic_design.md` が完成 (Phase 1)
- `specs/<feature_name>/spec.md` + `plan.md` が完成 (Phase 2)
- `specs/<feature_name>/contracts/openapi.yaml` (or 該当 contract) が存在
- `specs/<feature_name>/APPROVAL.md` で Gate 1-4 承認済 (人間編集)

### 2. ★ tasks.md scaffold 生成

`plan.md` の `plan.phases[].groups[]` 構造から 1-to-1 で task scaffold を生成。

```bash
FEATURE="<feature_name>"
PLAN="specs/${FEATURE}/plan.md"
TASKS="specs/${FEATURE}/tasks.md"

# 既存 tasks.md は template scaffold (stride init で生成)、ここでは plan.md の groups から
# T-G<NN>-<NNN> または T-WI-<NNN> 形式で実行可能タスクを expand する。
# basic-design-authoring + tasks-authoring skill を起動して Cowork 内で対話的に生成。
```

実装上は `tasks-authoring` skill (Cowork セッション内で対話) または AI Task Agent (Cowork 自動生成) のいずれかを起動する。Phase F では **対話的 generation を default**、自動 generation は Phase G 候補。

### 3. ★ work_items/ scaffold 生成

`plan.md` の groups + `tasks.md` の tasks から、各 WI の scaffold を `specs/<feature>/work_items/WI-<FEATUREID>-<NNN>.md` として生成する。

```bash
WORK_ITEMS_DIR="specs/${FEATURE}/work_items"
mkdir -p "${WORK_ITEMS_DIR}"

# 各 WI 用の scaffold (frontmatter + plan_refs + spec_refs + outputs + done_when)
# 標準テンプレ: sdd-templates/templates/work_item_template.md (or repo の既存形式)
```

各 work_item には:
- `wi_id`: `WI-<FEATUREID>-<NNN>`
- `title`: tasks.md の対応 task title
- `plan_refs`: tasks.md の plan_refs (CT/TS/G/Phase/CMP/LIB)
- `spec_refs`: tasks.md の spec_refs (US/AC)
- `bpmn_refs`: 対応 BPMN element ID
- `outputs`: deliverable file list
- `done_when`: 完了条件
- `status`: `not_started` (初期)

### 4. ★ state.yaml Phase 3 完了マーク

`specs/<feature>/state/state.yaml` を更新し、Phase 3 (tasking) 完了を記録。

```yaml
phase_3:
  status: "completed"
  tasks_count: <N>
  work_items_count: <N>
  completed_at: "<ISO 8601>"
```

(WI-VALF01-010 で state.yaml schema が拡張済の前提)

### 5. Validate Output

- `specs/<feature>/tasks.md` が生成され、stride lint PASS (counts + tasks_gate_check.tasks_ready_for_code: true)
- `specs/<feature>/work_items/WI-*.md` が tasks.md の各 task と 1-to-1 対応
- `specs/<feature>/APPROVAL.md` Gate 5 (Tasks) は **人間編集**を待つ

### 6. Output

- `specs/<feature>/tasks.md` (Phase 3 deliverable)
- `specs/<feature>/work_items/WI-<FEATUREID>-001.md` 〜 `WI-<FEATUREID>-NNN.md` (Phase 4 入力)
- `specs/<feature>/state/state.yaml` Phase 3 完了マーク

### 7. Next Step

- Hitoshi さん **Gate 5 (Tasks) 承認** を APPROVAL.md で実施 (人間編集)
- Gate 5 承認後、Phase 4 (Execute) に進む:
  - 各 WI ごとに `/stride:wi-start <WI-ID>` (Phase G 候補、現状は手動)
  - WI 完了時に `state/state.yaml` を `in_progress` → `done` に更新

### 8. Notes

- Phase 3 (Tasking) は **AI と人間の役割分離** が重要:
  - AI: tasks.md / work_items scaffold 生成 (本 command が担当)
  - 人間: Gate 5 承認 (APPROVAL.md 編集)、業務優先度 / リスク再評価
- `tasks-authoring` skill は対話で task description / done_when を補正、AI 単独ではなく Cowork 共同作業
- WI 順序は `plan.phases[].groups[].depends_on_groups` を尊重 (DAG 順序保持)

> Phase F (WI-VALF01-016) で Phase 3 (tasking) を 1 コマンド化。Phase E v0.1.0-poc → v0.2.0-stable。
