# Conventions (Tecnos SDD)
# Keep short. Canonical rules live in templates and memory docs.

## 1) Source of truth
- ID conventions: `memory/constitution.md#id_conventions`.
- Org constraints and gates: `memory/tecnos_org_constraints.md`.
- Artifact registry: `memory/artifact_registry.md`.

## 2) File naming
- Use snake_case for spec files: `basic_design.md`, `spec.md`, `plan.md`, `tasks.md`.
- Avoid hyphens in spec file names; lint expects snake_case.

## 3) Canonical YAML blocks
- Do not delete or rename canonical YAML sections; `stride-lint` extracts these blocks.
- Edit data first, then update counts to match lint suggestions (COUNTS_SUGGESTION).

## 4) IDs and references
- Use stable IDs for components, libraries, contracts, tests, phases, and groups.
- `tasks.plan_refs` must reference stable IDs only.
- `spec_refs` must reference valid US-* and AC-* IDs.

## 5) Placeholders
- Replace template placeholders (FEAT-XXX, FEATXXX, XXX_feature_name) before gating.

## 6) Test File Location (CRITICAL)
- **正しい場所**: `specs/<feature>/tests/`
- **間違い**: プロジェクトルートの `tests/` や `test/`
- テストファイルは必ず機能ディレクトリ内に格納する
- これにより以下が実現される：
  - 機能単位でのポータビリティ（`specs/<feature>/` をコピーするだけで移行可能）
  - stride-lintのトレーサビリティチェックが正確に動作
  - Evidence Packのパス参照が整合
- `pyproject.toml` の `testpaths` は `["specs/<feature>/tests"]` に設定する

## 7) AI Test Tool Auto-Install (MANDATORY)
- **テスト実行前に依存関係を確認し、不足ツールは自動インストールする**
- ユーザーに確認を求めずに進める（テストツールのインストールは安全な操作）
- 仮想環境（`.venv`）が存在する場合は必ず使用する
- インストール失敗時はエラーを報告し、代替案を提示する
- 詳細: `sdd-templates/agent_docs/testing.md` の「AI Agent Pre-Flight Checklist」

### クイックリファレンス
```bash
# Python: pytest確認＆インストール
python -c "import pytest" 2>/dev/null || pip install pytest pytest-cov httpx

# TypeScript: vitest確認＆インストール
npm list vitest 2>/dev/null || npm install -D vitest @vitest/coverage-v8

# Playwright: E2E用ブラウザ
npx playwright --version 2>/dev/null || { npm install -D @playwright/test && npx playwright install chromium; }
```
