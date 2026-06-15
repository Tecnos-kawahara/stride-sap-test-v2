---
description: Tecnos-STRIDE feature scaffold を作成する (specs/<feature>/ 配下)。Phase 0 着手の最初に実行。
argument-hint: "<feature_name> [--profile enterprise-erp|saas-integration|prototype]"
---

# /stride:init

新規 feature のための SDD scaffold を作成します。

## Usage

```
/stride:init <feature_name> [--profile <P>]
```

## Workflow

### 1. Validate Input
- `<feature_name>` は snake_case + alphanum (例: `customer_master_v2`)
- `--profile` 省略時は `enterprise-erp` (default)

### 2. Run Scaffold

`sdd-templates/bin/stride init <feature_name> --profile <P>` 相当の処理を内部で実行:

- `specs/<feature>/basic_design.md` (canonical schema scaffold)
- `specs/<feature>/process.bpmn` (BPMN-PROC-<FEATUREID> 自動置換)
- `specs/<feature>/spec.md` / `plan.md` / `tasks.md` (Phase 2/3 territory)
- `specs/<feature>/contracts/openapi.yaml`
- `specs/<feature>/state/state.yaml` (`profile` 同期)
- `specs/<feature>/APPROVAL.md` (Hitoshi さん編集対象、AI 編集禁止)
- `specs/<feature>/tests/scenarios.yaml`
- `specs/<feature>/implementation-details/{evidence_pack,ops,e2e-triage}.md`

### 3. Output

scaffold 完了後、以下を表示:
- 作成ファイル一覧
- 次の推奨ステップ: `/stride:discovery <feature_name>` で BACCM 6 軸対話開始

### 4. Notes

- `APPROVAL.md` は scaffold 後も AI 編集禁止 (人間のみ編集)
- 既存 `specs/<feature_name>` がある場合は警告 + 上書き確認
- profile は basic_design.md の SSoT、state.yaml は同期キャッシュ
