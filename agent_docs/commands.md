# Canonical Project Commands (SSoT) - SDD Template Pack
# Single source of truth for CLI commands in this repo.

## Quick Reference for AI Agents

This section provides a minimal overview for agents that need to use stride-lint.
For full command details, see sections below.

### stride-lint Exit Codes

| Code | Meaning | Agent Action |
|------|---------|--------------|
| 0 | All checks passed | Proceed to next gate |
| 1 | Lint errors found | Read errors[].suggested_action, fix, re-run |
| 2 | Usage error (bad arguments) | Check `stride lint --help` |
| 3 | Feature directory not found | Check path (see stderr for Did-you-mean suggestion) |
| 4 | YAML parse error | Fix YAML syntax in the reported file |

### Output Formats

| Flag | Format | Use Case |
|------|--------|----------|
| (default) | Colored text | Human terminal |
| `--plain` | TSV (tab-separated) | grep / awk / CI log parsing |
| `-o json` | JSON object | Programmatic parsing |
| `-o ndjson` | NDJSON (1 JSON per line) | Pipe-friendly per-feature parsing |

Note: `--plain` and `-o json`/`-o ndjson` are mutually exclusive.
`--verbose` cannot be combined with machine-readable output formats.

### Typical Agent Workflow

```bash
stride lint specs/FEAT-ORDER/ -o json    # Parse result programmatically
stride auto-continue specs/FEAT-ORDER/   # Get next actionable steps
stride phase-status specs/FEAT-ORDER/    # Check gate approval status
```

### Limitations

- `APPROVAL.md` is human-only. Agents must NOT edit it.
- Phase gates are enforced: Phase 2 files require Gate 1+2 approval.
- `stride lint` is read-only: it never modifies your files.
- Enterprise features require `sdd-templates/config/enterprise.yaml` with `enterprise.enabled: true`.

---

## 0) Preconditions
- Working directory: project root (where `sdd-templates/` exists).
- Python 3 with PyYAML is required for `stride-lint`.

### Optional venv setup
- PYTHON_VENV_SETUP: `python3 -m venv sdd-templates/.venv && sdd-templates/.venv/bin/pip install pyyaml`

### Optional: Multi-Model Evaluator
- INSTALL_AI_EVAL: `pip install -r sdd-templates/requirements-ai-eval.txt`
  - Required for: `stride evaluate` command
  - Only needed if multi-model evaluation is enabled (`.env.local` configured)

## 1) Feature scaffolding

### Recommended: Intake-First approach (v1.2.5)
- STRIDE_INTAKE: `sdd-templates/bin/stride intake <feature>`
  - Creates `specs/<feature>/basic_design_intake.md` (simplified questionnaire)
  - User fills in intake (10-15 min)
  - AI generates full `basic_design.md` from intake

### Alternative: stride init (full templates at once)
- STRIDE_INIT: `sdd-templates/bin/stride init <feature>`
  - Creates `specs/<feature>/` with all templates (basic_design, spec, plan, tasks, etc.)
  - Use `--lite` flag for Lite Mode (3-stage approval: Gate A/B/C)
  - Use `--detect` flag to auto-detect existing project stack (v3.3)
    - Analyzes manifests (package.json, pyproject.toml, go.mod, etc.)
    - Saves detection to `implementation-details/brownfield_detection.json`
    - Auto-fills `delivery_model` (brownfield → requirement_driven)
  - Use `--scale` flag to select monorepo complexity level (v4.2)
    - `--scale starter` (default): turbo.json(build+test), tsconfig.base.json, simple CI
    - `--scale standard`: Full Turborepo + vitest.workspace.ts + differential CI
    - `--scale enterprise`: Standard + remote cache + full CI differential + Evidence Pack (90d)
    - Monorepo setup (turbo.json, workspaces, CI) always runs — monorepo is the default
    - Injects `workspaces` + turbo scripts into `package.json` (if present)
    - Skips files that already exist (safe for re-runs)
    - Reference: `sdd-templates/config/monorepo/README.md`

### Brownfield detection (standalone)
- BROWNFIELD_DETECT: `python3 sdd-templates/tools/brownfield_detector.py <project_root>`
  - Detects: project type (greenfield/brownfield), structure (monolith/monorepo), languages, frameworks, test frameworks
  - Use `--json` for machine-readable output
  - Use `--test` to run 8 self-tests

### Traditional: Manual template copy
- CREATE_FEATURE_DIRS: `mkdir -p specs/<feature>/{contracts,tests,implementation-details}`

- COPY_TEMPLATES:
```
cp sdd-templates/templates/basic_design_template.md specs/<feature>/basic_design.md
cp sdd-templates/templates/spec_template.md specs/<feature>/spec.md
cp sdd-templates/templates/plan_template.md specs/<feature>/plan.md
cp sdd-templates/templates/tasks_template.md specs/<feature>/tasks.md
cp sdd-templates/templates/evidence_pack_template.md specs/<feature>/implementation-details/evidence_pack.md
cp sdd-templates/templates/APPROVAL.md specs/<feature>/APPROVAL.md
```

- COPY_SPEC_AS_CODE_ARTIFACTS (spec_as_codeのスケルトン):
```
cp sdd-templates/templates/contracts/openapi_template.yaml specs/<feature>/contracts/openapi.yaml
cp sdd-templates/specs/sample_feature/implementation-details/migration_mapping.yaml specs/<feature>/implementation-details/migration_mapping.yaml
cp sdd-templates/specs/sample_feature/implementation-details/authz_matrix.yaml specs/<feature>/implementation-details/authz_matrix.yaml
cp sdd-templates/templates/tests/scenarios_template.yaml specs/<feature>/tests/scenarios.yaml
```

- COPY_OPS_E2E_TRIAGE (運用/triageの雛形):
```
cp sdd-templates/specs/sample_feature/implementation-details/ops.md specs/<feature>/implementation-details/ops.md
cp sdd-templates/specs/sample_feature/implementation-details/e2e-triage.md specs/<feature>/implementation-details/e2e-triage.md
```

- COPY_DB_SCHEMA (v1.2.5追加・任意):
```
cp sdd-templates/templates/contracts/database_schema_template.yaml specs/<feature>/contracts/database_schema.yaml
```

- COPY_DB_INPUT_CSV (v1.2.5追加・AI生成用):
```
cp sdd-templates/templates/contracts/database_schema_input.csv /tmp/tables.csv
# CSVを編集後、AIに「このCSVから database_schema.yaml を生成」と依頼
```

- COPY_ARTIFACT_REGISTRY: `cp sdd-templates/memory/artifact_registry.md memory/artifact_registry.md`

- REPLACE_PLACEHOLDERS_MAC:
```
sed -i '' 's/FEAT-XXX/FEAT-001/g' specs/<feature>/*.md specs/<feature>/*/*.md specs/<feature>/*/*.yaml
sed -i '' 's/FEATXXX/001/g' specs/<feature>/*.md specs/<feature>/*/*.md specs/<feature>/*/*.yaml
sed -i '' 's/XXX_feature_name/<feature>/g' specs/<feature>/*.md specs/<feature>/*/*.md specs/<feature>/*/*.yaml
sed -i '' 's/{{FEATURE_NAME}}/<feature>/g' specs/<feature>/*.md specs/<feature>/*/*.md specs/<feature>/*/*.yaml
sed -i '' 's/{{FEATURE_ID}}/001/g' specs/<feature>/*.md specs/<feature>/*/*.md specs/<feature>/*/*.yaml
```

- REPLACE_PLACEHOLDERS_LINUX:
```
sed -i 's/FEAT-XXX/FEAT-001/g' specs/<feature>/*.md specs/<feature>/*/*.md specs/<feature>/*/*.yaml
sed -i 's/FEATXXX/001/g' specs/<feature>/*.md specs/<feature>/*/*.md specs/<feature>/*/*.yaml
sed -i 's/XXX_feature_name/<feature>/g' specs/<feature>/*.md specs/<feature>/*/*.md specs/<feature>/*/*.yaml
sed -i 's/{{FEATURE_NAME}}/<feature>/g' specs/<feature>/*.md specs/<feature>/*/*.md specs/<feature>/*/*.yaml
sed -i 's/{{FEATURE_ID}}/001/g' specs/<feature>/*.md specs/<feature>/*/*.md specs/<feature>/*/*.yaml
```

## 2) Quality gates
- STRIDE_LINT: `sdd-templates/bin/stride lint specs/<feature>/`
- STRIDE_LINT_COVERAGE: `sdd-templates/bin/stride lint specs/<feature>/ --coverage-report`
- STRIDE_LINT_WARN: `sdd-templates/bin/stride lint specs/<feature>/ --warn-only`

### Multi-Model Semantic Evaluator
- STRIDE_EVALUATE: `sdd-templates/bin/stride evaluate specs/<feature>/ --phase <design|specify|tasking>`
  - stride lint PASS 後に呼び出す。LLM が意味的な穴（業務リスク・ERP統合盲点・ACテスタビリティ・SoD曖昧さ）を評価する
  - FAIL の場合は差し戻し（exit 1）。Generator が成果物を修正して再実行する
  - 評価レポート JSON: `specs/<feature>/state/evaluator_latest.json`（正本）
  - 評価レポート MD: `specs/<feature>/state/eval_report_<phase>_<timestamp>.md`（履歴）
  - 終了コード: 0=PASS/WARN, 1=FAIL, 2=PROVIDER_ERROR（--allow-provider-degraded 未指定時）
  - API 障害時は --allow-provider-degraded を付けると WARN で続行（exit 0）

### Security Audit
- STRIDE_SECURITY_DAILY: `sdd-templates/bin/stride security specs/<feature>/ --daily`
  - 軽量セキュリティチェック（confidence >= 8/10 のみ）
  - Gate 前の日常チェック
  - OpenAPI security, security AC と authz_matrix, security requirements, secrets, audit/correlation を確認

- STRIDE_SECURITY_AUDIT: `sdd-templates/bin/stride security specs/<feature>/ --audit`
  - 総合セキュリティ監査（confidence >= 2/10 すべて報告）
  - Final 前の包括チェック
  - LLM trust boundary, SoD, data class / retention, org constraints, direct ERP DB write guard を追加確認

- STRIDE_SECURITY_JSON: `sdd-templates/bin/stride security specs/<feature>/ --daily --json`
  - CI/CD 連携用 JSON 出力

## 3) Phase Gate commands
- STRIDE_PHASE_STATUS: `sdd-templates/bin/stride phase-status specs/<feature>/`
- STRIDE_PHASE_CHECK: `sdd-templates/bin/stride phase-check <file_path>`
- STRIDE_HOOKS: `sdd-templates/bin/stride hooks`
  - Sets up Phase Gate hooks in `.claude/settings.json`
  - Use `--force` to overwrite existing configuration
  - Use `--tool <name>` for other AI tools (v4.0):
    - `--tool claude` (default): `.claude/settings.json` PreToolUse hook
    - `--tool cursor`: `.cursor/rules/phase-gate.md` rule generation
    - `--tool copilot`: `.github/copilot/phase-gate.md` instruction file generation
    - `--tool manual`: `docs/phase-gate-checklist.md` manual checklist

### Direct Python commands (alternative)
- PHASE_GATE_STATUS: `python3 sdd-templates/tools/phase_gate.py status specs/<feature>/`
- PHASE_GATE_CHECK: `python3 sdd-templates/tools/phase_gate.py check <file_path>`

### Phase Gate workflow (Full Mode)
```
Phase 1 (Design): basic_design.md, process.bpmn, APPROVAL.md
  → 作成可（bootstrap）
  → 次フェーズ解放: Gate 1, 2

Phase 2 (Specify): spec.md, plan.md, contracts/*, implementation-details/*, tests/scenarios.yaml
  → 作成要件: Gate 1, 2 承認済み
  → 次フェーズ解放: Gate 3, 4

Phase 3 (Tasking): tasks.md, tests/*
  → 作成要件: Gate 3, 4 承認済み
  → 次フェーズ解放: Gate 5

Phase 4 (Execute): src/*
  → 作成要件: Gate 5 承認済み
  → 次フェーズ解放: Final
```

### Lite Mode (Gates A, B, C)
APPROVAL.md に `## Gate A`, `## Gate B`, `## Gate C` セクションがあると自動検出されます。

### APPROVAL.md rules (INVIOLABLE)
- **AI is FORBIDDEN from editing APPROVAL.md**
- Human must check boxes `[x]` and fill approver name
- stride-lint fails with `APPROVAL_PENDING` if gate not approved

## 3.1) Roadmap Optimization Commands (v4.1)

### Auto-Continue

- AUTO_CONTINUE: `sdd-templates/bin/stride auto-continue specs/<feature>/`
  - 現在の承認状態から「次に実行すべきフェーズ内ステップ」を自動生成
  - 次の HITL チェックポイント（Gate 承認）で必ず停止
  - `--json` で機械可読出力

### Mandatory Output Rules

- OUTPUT_RULES: `sdd-templates/bin/stride output-rules`
  - AI 出力フォーマット規則（PASS/FAIL/WARN/SKIP, [n/N], no ASCII tables）を表示

### DDD Integration (Optional)

- DDD_INIT: `sdd-templates/bin/stride ddd-init <feature>`
  - `implementation-details/domain_model.md` を作成
  - `implementation-details/technical_design.md` を作成
  - `shared/decisions/` に初回 ADR を作成（未作成時）
  - `decision-index.md` を自動更新

### Decision Index (ADR)

- DECISIONS_INIT: `sdd-templates/bin/stride decisions init`
  - `shared/decisions/decision-index.md` を初期化
- DECISIONS_REFRESH: `sdd-templates/bin/stride decisions refresh`
  - `ADR-*.md` から `decision-index.md` を再生成

---

## 4) Enterprise Commands (v1.2.6)

> エンタープライズ拡張（3-5チーム規模の大規模開発向け）

### stride epic コマンド（推奨）

> Enterprise mode が有効な場合に使用可能。
> `sdd-templates/config/enterprise.yaml` で `enterprise.enabled: true` に設定。

- STRIDE_EPIC_INIT: `sdd-templates/bin/stride epic init <EPIC_ID>`
- STRIDE_EPIC_VALIDATE: `sdd-templates/bin/stride epic validate <EPIC_ID>`
- STRIDE_EPIC_GATES: `sdd-templates/bin/stride epic gates <EPIC_ID>`
- STRIDE_EPIC_FEATURES: `sdd-templates/bin/stride epic features <EPIC_ID>`
- STRIDE_EPIC_PROGRESS: `sdd-templates/bin/stride epic progress <EPIC_ID>`
- STRIDE_EPIC_LIST: `sdd-templates/bin/stride epic list`

- STRIDE_INIT_WITH_EPIC: `sdd-templates/bin/stride init <feature> --epic <EPIC_ID>`
  - basic_design.md の epic_ref を自動設定

- STRIDE_LINT_ENTERPRISE: `sdd-templates/bin/stride lint specs/<feature>/ --enterprise`
  - 従来の lint に加え、epic_ref/team_id/coverage_tier の整合性を検証

- STRIDE_LINT_ALL_ENTERPRISE: `sdd-templates/bin/stride lint --all --enterprise`
  - 全 Feature + 全 Epic を一括検証

### Epic scaffolding（手動手順）

- CREATE_EPIC_DIRS: `mkdir -p epics/<epic_id>/{features,docs}`

- COPY_EPIC_TEMPLATES:
```
cp sdd-templates/templates/epic_design_template.md epics/<epic_id>/epic_design.md
cp sdd-templates/templates/feature_breakdown_template.md epics/<epic_id>/feature_breakdown.md
cp sdd-templates/templates/EPIC_APPROVAL.md epics/<epic_id>/EPIC_APPROVAL.md
```

- REPLACE_EPIC_PLACEHOLDERS_MAC:
```
sed -i '' 's/{{EPIC_ID}}/<epic_id>/g' epics/<epic_id>/*.md
sed -i '' 's/{{EPIC_NAME}}/<epic_name>/g' epics/<epic_id>/*.md
```

### Shared contract scaffolding

- CREATE_SHARED_CONTRACT_DIRS: `mkdir -p shared/contracts/{api,events} shared/schemas`

- COPY_SHARED_CONTRACT:
```
cp sdd-templates/templates/shared_contract_template.yaml shared/contracts/api/<contract_id>.yaml
```

- COPY_CCP_TEMPLATE:
```
cp sdd-templates/templates/ccp_template.md enterprise/change_proposals/CCP-<number>.md
```

### Enterprise lint

- STRIDE_LINT_ENTERPRISE: `python3 sdd-templates/tools/stride_lint_enterprise.py specs/<feature>/`
  - エンタープライズ拡張フィールド（epic_ref, team_id, coverage_tier）を検証
  - 共有契約参照の整合性チェック
  - 階層カバレッジ要件の検証

- STRIDE_LINT_ENTERPRISE_EPIC: `python3 sdd-templates/tools/stride_lint_enterprise.py epics/<epic_id>/`
  - Epic全体の検証（epic_design, feature_breakdown, EPIC_APPROVAL）

### Dependency checker

- DEP_CHECK: `python3 sdd-templates/tools/dependency_checker.py check specs/<feature>/`
  - Feature単体の依存関係チェック

- DEP_CHECK_ALL: `python3 sdd-templates/tools/dependency_checker.py check --all`
  - 全Featureの依存サイクル検出

- DEP_GRAPH: `python3 sdd-templates/tools/dependency_checker.py graph`
  - 依存グラフを DOT 形式で出力

- DEP_GRAPH_PNG: `python3 sdd-templates/tools/dependency_checker.py graph | dot -Tpng -o deps.png`
  - 依存グラフを PNG で可視化（Graphviz 要）

- DEP_VALIDATE_CONTRACTS: `python3 sdd-templates/tools/dependency_checker.py validate --contracts`
  - 共有契約の消費者整合性チェック

### Epic validator

- EPIC_VALIDATE: `python3 sdd-templates/tools/epic_validator.py validate epics/<epic_id>/`
  - Epic設計の検証（ID規約、必須フィールド、features整合性）

- EPIC_GATES: `python3 sdd-templates/tools/epic_validator.py gates epics/<epic_id>/`
  - Epic Gate状態の表示

- EPIC_FEATURES: `python3 sdd-templates/tools/epic_validator.py features epics/<epic_id>/`
  - Epic配下のFeature一覧と状態

- EPIC_VALIDATE_ALL: `python3 sdd-templates/tools/epic_validator.py validate --all`
  - 全Epicの検証

### Approval router

- APPROVAL_ROUTE: `python3 sdd-templates/tools/approval_router.py route specs/<feature>/ --gate <gate_number>`
  - 指定Gateの承認者を coverage_tier に基づいて決定

- APPROVAL_ROUTE_EPIC: `python3 sdd-templates/tools/approval_router.py route epics/<epic_id>/ --gate E<number>`
  - Epic Gateの承認者を決定

- APPROVAL_VALIDATE: `python3 sdd-templates/tools/approval_router.py validate specs/<feature>/`
  - 承認マトリクスとの整合性チェック

- APPROVAL_PARALLEL: `python3 sdd-templates/tools/approval_router.py parallel specs/<feature>/`
  - 並列承認可能なGateの一覧

### Cross-team coordination

- COPY_DEPENDENCY_MANIFEST:
```
cp sdd-templates/templates/dependency_manifest_template.yaml specs/<feature>/dependencies/dependency_manifest.yaml
```

- COPY_CROSS_REFS:
```
cp sdd-templates/templates/cross_refs_template.yaml specs/<feature>/contracts/cross_refs.yaml
```

- NOTIFY_CONSUMERS: `python3 sdd-templates/tools/dependency_checker.py notify <contract_id> --message "<change_description>"`
  - 契約変更時の消費者チームへの通知

### Coverage tier management

- COVERAGE_TIERS_INFO: `cat shared/policies/coverage_tiers.yaml`
  - 階層カバレッジ定義の確認

- COVERAGE_CHECK: `python3 sdd-templates/tools/stride_lint_enterprise.py specs/<feature>/ --coverage-tier`
  - Feature の coverage_tier に基づくカバレッジ要件チェック

### Enterprise workflow (推奨手順)

```
# 1. Epic 作成
CREATE_EPIC_DIRS (epic_id=EPIC-ORDER)
COPY_EPIC_TEMPLATES
→ epic_design.md を編集
→ EPIC_VALIDATE

# 2. Feature Breakdown
→ feature_breakdown.md を編集
→ EPIC_VALIDATE
→ EPIC_APPROVAL.md の Gate E1, E2 を人間が承認

# 3. 各 Feature の Spec 作成
STRIDE_INIT (各 feature)
→ basic_design.md に epic_ref, team_id, coverage_tier を設定
→ STRIDE_LINT_ENTERPRISE

# 4. 依存関係の宣言
COPY_DEPENDENCY_MANIFEST
→ dependency_manifest.yaml を編集
→ DEP_CHECK_ALL (サイクル検出)

# 5. 共有契約の定義（必要な場合）
COPY_SHARED_CONTRACT
→ shared_contract.yaml を編集
→ DEP_VALIDATE_CONTRACTS

# 6. 契約変更提案（必要な場合）
COPY_CCP_TEMPLATE
→ CCP を編集
→ 消費者チームに NOTIFY_CONSUMERS
→ ARCH_BOARD 承認
```

### EPIC_APPROVAL.md rules (INVIOLABLE)
- **AI is FORBIDDEN from editing EPIC_APPROVAL.md**
- Human must check boxes `[x]` and fill approver name
- Epic Gateは Feature Gate とは独立
- Epic Gate 未承認でも配下 Feature の作業は可能（ただし epic_ref 設定要）

---

## 5) ERP Addon Execution Tracking (v2.1.0)

> ERPアドオン向けマイクロレベル実行追跡（Work Item/Run/State/Mode）

### Activation
ERP Addon は以下の場合のみ有効化：
1. `work_items/` ディレクトリが存在 OR
2. `basic_design.md` YAML に `execution_profile: erp_addon` を設定

AND Gate 5 以降（tasks.md が存在 or Gate 5 承認済み）

### Initialize ERP Addon for existing feature

- ERP_ADDON_INIT:
```
mkdir -p specs/<feature>/{work_items,runs,state,ops}
cp sdd-templates/templates/state_template.yaml specs/<feature>/state/state.yaml
```

### Create Work Item

- CREATE_WORK_ITEM:
```
cp sdd-templates/templates/work_item_template.md specs/<feature>/work_items/WI-ERP-<FEATID>-<NNN>.md
```

### Create Work Item Approval (all modes, post-run approvals)

- CREATE_WI_APPROVAL:
```
cp sdd-templates/templates/work_item_approval_template.md specs/<feature>/work_items/WI-ERP-<FEATID>-<NNN>.approval.md
```

### Create Run Evidence

- CREATE_RUN:
```
mkdir -p specs/<feature>/runs/<WI_ID>/RUN-$(date +%Y%m%d-%H%M)
cp sdd-templates/templates/walkthrough_template.md specs/<feature>/runs/<WI_ID>/RUN-$(date +%Y%m%d-%H%M)/walkthrough.md
```

### Planning Integration (v5.0 — SDD Planning Bridge)

- BRIDGE_INIT: `python3 sdd-templates/tools/sdd_planning_bridge.py init specs/<feature>/ <WI-ID>`
  - RUN ディレクトリ内に .planning/ を作成（SDD 文脈付き）
  - WI 定義の spec_refs, risk_flags, mode を plan.md に自動注入
  - グローバル知識 (~/.claude/knowledge/) を検索・適用
  - RUN ディレクトリが未作成なら自動作成

- BRIDGE_SYNC: `python3 sdd-templates/tools/sdd_planning_bridge.py sync specs/<feature>/`
  - stride-lint を実行し、FAIL を plan.md Errors テーブルに自動反映
  - Use `--wi-id <WI-ID>` to specify which RUN の .planning/ を更新するか

- BRIDGE_EVIDENCE: `python3 sdd-templates/tools/sdd_planning_bridge.py evidence specs/<feature>/ <WI-ID>`
  - .planning/ の内容を walkthrough.md の "Planning Evidence" セクションに自動挿入
  - walkthrough.md が未作成の場合は stdout に出力

- BRIDGE_LEARN: `python3 sdd-templates/tools/sdd_planning_bridge.py learn specs/<feature>/ <WI-ID>`
  - .planning/ から lesson 候補を抽出（Errors retries, Decisions, findings Technical Notes, lint FAILs）
  - 標準出力に候補を表示（自動書き込みしない）
  - Use `--apply` to write candidates directly to lessons.md

- ARCHIVE_RUN_PLANNING:
```
# Run 完了時に実行。lessons.md をグローバル知識に保存
# （Claude Code が /planning:archive を自動実行）
```

### Run Resume Detection (v3.1)

- DETECT_RUN_RESUME: `python3 sdd-templates/tools/run_resume_detector.py specs/<feature>/runs/<WI_ID>/RUN-<TIMESTAMP>/`
  - 中断された Run のアーティファクト存在状況を検出
  - 再開推奨ポイントと次のアクションを提示

- DETECT_RUN_RESUME_VERBOSE: `python3 sdd-templates/tools/run_resume_detector.py specs/<feature>/runs/<WI_ID>/RUN-<TIMESTAMP>/ --verbose`
  - 各アーティファクトの詳細チェック結果を表示

### Create Ops Pack (ERP addon required)

- CREATE_OPS_PACK:
```
mkdir -p specs/<feature>/ops
cp sdd-templates/templates/ops/transport_manifest.yaml specs/<feature>/ops/
cp sdd-templates/templates/ops/release_checklist.md specs/<feature>/ops/
cp sdd-templates/templates/ops/rollback_plan.md specs/<feature>/ops/
cp sdd-templates/templates/ops/hypercare_runbook.md specs/<feature>/ops/
```

### Validate ERP Addon

- ERP_ADDON_VALIDATE: `python3 sdd-templates/tools/erp_addon_exec_tracking.py specs/<feature>/ [coverage_tier]`
  - Work Item 構造検証
  - Mode/risk_flags ポリシー検証
  - Run 証跡検証
  - Ops Pack 検証（ERP addon 必須）

- STRIDE_LINT（通常と同じ）: `sdd-templates/bin/stride lint specs/<feature>/`
  - ERP Addon が有効化されている場合、自動的に追加検証を実行

### Mode Policy

| Mode | Pre-run | Post-run | Use when |
|------|---------|----------|----------|
| autopilot | なし | walkthrough, CI, ops | 低リスク（UI, messages） |
| confirm | plan_review | walkthrough, CI, ops | 中リスク（new API, perf） |
| validate | design_diff, plan_review | walkthrough, CI, ops | 高リスク（auth, accounting） |

### Risk Flags → Mode Mapping

| Risk Flags | Recommended Mode |
|------------|------------------|
| ui_only, message_only, test_only, logging_only | autopilot |
| audit_log | validate |
| new_api, contract_change, performance_sensitive | confirm |
| authz, sod, pii, accounting_calc, inventory_valuation | validate |
| db_schema, data_migration, update_integration, cross_module | validate |

### ERP Addon Workflow (Planning 統合版 v3.1)

```
# 1. Gate 1-5 を通常通り完了

# 2. ERP Addon を有効化
ERP_ADDON_INIT

# 3. Work Item を作成
CREATE_WORK_ITEM
→ wi_id, complexity, mode, risk_flags を設定
→ Spec Links / DoD を記入
→ CREATE_WI_APPROVAL を作成（post-run 承認用）

# 4. state.yaml を更新
→ work_items[] に WI を追加

# 5. Run 実行前チェック
WI_READINESS                   # FAIL があれば Run 開始禁止

# 5b. Run Resume Check (v3.1)
# 既存RUNがある場合は再開ポイントを検出
DETECT_RUN_RESUME              # 中断RUNがあれば再開ポイント検出

# 6. Run 開始（Planning Bridge 統合）
CREATE_RUN                     # RUN ディレクトリ作成
BRIDGE_INIT                    # sdd_planning_bridge.py init で .planning/ 作成（SDD 文脈付き）

# 7. 実装
→ コード変更（2-Action Rule / 3-Strike Protocol に従う）
→ .planning/findings.md を調査ごとに更新
→ stride-lint 後に BRIDGE_SYNC で FAIL を plan.md Errors に自動反映
→ .planning/plan.md のエラーを随時記録

# 8. Run 証跡作成
BRIDGE_EVIDENCE                # walkthrough.md に Planning Evidence 自動挿入
→ test_results.md を追加（standard/critical tier）
ARCHIVE_RUN_PLANNING           # /planning:archive でグローバル知識保存

# 9. 承認 (all modes)
→ WI-*.approval.md のチェックボックスを完了（pre/post-run）

# 10. 完了
→ state.yaml の status を done に更新
→ stride-lint で検証

# 11. Final
→ evidence_pack.md を更新
→ ops pack を作成（ERP addon 必須）
```

### Work Item Approval rules (INVIOLABLE)
- **AI is FORBIDDEN from editing WI-*.approval.md**
- Human must check boxes `[x]` for pre-run/post-run checkpoints (all modes)
- stride-lint fails with `WI_APPROVAL_PENDING` if approval not completed

---

## 6) Multi-Team Progress Management (v3.0.0)

> PMがEpic横断で進捗管理するためのコマンド群

### Epic Progress Dashboard

- EPIC_PROGRESS: `python3 sdd-templates/tools/epic_progress_aggregator.py epics/<epic_id>/`
  - 全Feature × Gate × Team の進捗集約をターミナル表示

- EPIC_PROGRESS_JSON: `python3 sdd-templates/tools/epic_progress_aggregator.py epics/<epic_id>/ --format json`
  - JSON形式で出力（CI/CD連携用）

- EPIC_PROGRESS_DASHBOARD: `python3 sdd-templates/tools/epic_progress_aggregator.py epics/<epic_id>/ --format markdown`
  - EPIC_DASHBOARD.md を自動生成

### WI Readiness Check

- WI_READINESS: `python3 sdd-templates/tools/wi_readiness_checker.py specs/<feature>/ <WI-ID>`
  - Work ItemのRun実行準備状況を検証

- WI_READINESS_VERBOSE: `python3 sdd-templates/tools/wi_readiness_checker.py specs/<feature>/ <WI-ID> --verbose`
  - 詳細チェック結果を表示

### Multi-Team Template Scaffolding

- COPY_EPIC_PROGRESS_REPORT:
```
cp sdd-templates/templates/epic_progress_report_template.md epics/<epic_id>/EPIC_PROGRESS_REPORT.md
```

- COPY_TEAM_STATUS_REPORT:
```
cp sdd-templates/templates/team_status_report_template.md epics/<epic_id>/TEAM_STATUS_<TEAM_ID>.md
```

- COPY_CONTRACT_REGISTRY:
```
cp sdd-templates/templates/shared_contract_registry_template.yaml shared/contracts/CONTRACT_REGISTRY.yaml
```

- COPY_DEPENDENCY_MANIFEST_V3:
```
cp sdd-templates/templates/cross_team_dependency_manifest_template.yaml epics/<epic_id>/DEPENDENCY_MANIFEST.yaml
```

- COPY_OPS_PACK_REGISTRY:
```
cp sdd-templates/templates/ops_pack_registry_template.yaml epics/<epic_id>/OPS_PACK_REGISTRY.yaml
```

---

## 7) Spec Drift & Evidence Metrics (v4.2)

> Living Spec Drift Detection と Evidence Pack Measurement Infrastructure

### Spec Drift Detection

- SPEC_DRIFT_CHECK: `python3 sdd-templates/tools/spec_drift_detector.py <project_root>`
  - contracts/ の OpenAPI 定義と src/ のルート実装を比較
  - 検出: endpoint_not_implemented, contract_outdated, schema_mismatch, parameter_missing
  - Use `--json` for machine-readable output
  - Use `--verbose` for detailed drift information
  - Use `--test` to run 6 self-tests

- SPEC_DRIFT_CHECK_JSON: `python3 sdd-templates/tools/spec_drift_detector.py <project_root> --json`
  - CI/CD 連携用 JSON 出力

### Evidence Metrics Collection

- EVIDENCE_METRICS: `python3 sdd-templates/tools/evidence_metrics_collector.py <project_root>`
  - 収集: coverage %, テスト結果 (pass/fail/skip), Turbo キャッシュ率, Gate リードタイム
  - Use `--json` for machine-readable output
  - Use `--test` to run 6 self-tests

- EVIDENCE_METRICS_JSON: `python3 sdd-templates/tools/evidence_metrics_collector.py <project_root> --json`
  - CI/CD 連携用 JSON 出力

### PR Readiness Check (v4.3)

- PR_READINESS_CHECK: `python3 sdd-templates/tools/pr_readiness_checker.py <project_root>`
  - 7チェック統合 PR 品質ゲート: stride-lint, spec:drift, tests, coverage, walkthrough, evidence_pack, TODO/FIXME
  - Exit codes: 0=PR_READY, 1=NOT_READY, 2=ERROR
  - Use `--json` for machine-readable output
  - Use `-v` for verbose details
  - Use `--strict` to treat TODO/FIXME as blocking FAIL
  - Use `--coverage-threshold N` to override auto-detected threshold
  - Use `--test` to run 10 self-tests

- PR_READINESS_CHECK_JSON: `python3 sdd-templates/tools/pr_readiness_checker.py <project_root> --json`
  - CI/CD 連携用 JSON 出力

- STRIDE_PR_CHECK: `sdd-templates/bin/stride pr-check <project_root>`
  - stride CLI 経由の PR readiness チェック（上記と同等）

### Retrospective Report
- STRIDE_RETRO: `sdd-templates/bin/stride retro specs/<feature>/`
  - Phase duration, WI統計, テスト, lessons, spec変更の定量レポート
  - ボトルネック分析と改善提案を含む

- STRIDE_RETRO_EPIC: `sdd-templates/bin/stride retro epics/<EPIC_ID>/`
  - `epic_design.md` の feature 一覧を辿って Epic 横断で集計

- STRIDE_RETRO_JSON: `sdd-templates/bin/stride retro specs/<feature>/ --json`
  - CI/CD 連携用 JSON 出力

---

### Multi-Team Workflow (v3.0 推奨手順)

```
# 1. Epic作成（v2.0と同じ）
CREATE_EPIC_DIRS → COPY_EPIC_TEMPLATES → epic_design.md編集

# 2. マルチチーム管理成果物の初期化（v3.0 新規）
COPY_EPIC_PROGRESS_REPORT
COPY_CONTRACT_REGISTRY
COPY_DEPENDENCY_MANIFEST_V3
COPY_OPS_PACK_REGISTRY

# 3. 各チームのステータスレポート初期化
COPY_TEAM_STATUS_REPORT（チーム数分）

# 4. Feature作成（各チーム）
STRIDE_INIT → basic_design.mdにepic_ref, team_id, coverage_tier設定

# 5. 進捗追跡（PM日次/週次）
EPIC_PROGRESS                  # ターミナルサマリー
EPIC_PROGRESS_DASHBOARD        # EPIC_DASHBOARD.md 自動生成

# 6. WI実行前チェック（各チーム）
WI_READINESS                   # Run実行準備の検証

# 7. 定例報告
→ TEAM_STATUS_<TEAM_ID>.md を各チームリードが週次更新
→ EPIC_PROGRESS_REPORT.md をPMが集約確認
```

---

## 8) Symphony Orchestration (v5.0 / v5.1)

> GitHub Issues → エージェント自動実行 → PR パイプライン
>
> v5.1: `stride symphony <subcmd>` が `bin/stride` から完全にディスパッチされます
> （内部で `python3 -m symphony …` を呼び出し、REPO_ROOT で実行）。

### ヘルプ
- SYMPHONY_HELP: `sdd-templates/bin/stride symphony --help`

### 実行
- SYMPHONY_RUN: `sdd-templates/bin/stride symphony run`
- SYMPHONY_RUN_ONCE: `sdd-templates/bin/stride symphony run --once`
- SYMPHONY_DISPATCH: `sdd-templates/bin/stride symphony dispatch --issue <number>`

### 管理
- SYMPHONY_STATUS: `sdd-templates/bin/stride symphony status`
- SYMPHONY_VALIDATE: `sdd-templates/bin/stride symphony validate`
- SYMPHONY_DRY_RUN: `sdd-templates/bin/stride symphony run --once --dry-run`

### Janitor 提案 (v5.1)
- SYMPHONY_JANITOR: `sdd-templates/bin/stride symphony janitor`
- SYMPHONY_JANITOR_DRY_RUN: `sdd-templates/bin/stride symphony janitor --dry-run`
  - `SYMPHONY.md` の `janitor.enabled=false` なら "skipped" を出力して即終了。
  - 詳細: `agent_docs/harness.md §2.4`。

### ラベルセットアップ
- SYMPHONY_LABELS: `python3 sdd-templates/tools/setup_project_labels.py --repo <owner/repo> --symphony`

### Phase別エージェント割り当て
| Phase | Engine | 理由 |
|-------|--------|------|
| design | Claude Code | 基本設計・BPMNは判断力が必要 |
| specify | Claude Code | spec_as_code・NFR・契約定義は文脈理解が必要 |
| tasking | Claude Code | Plan IDとの整合性が重要 |
| execute | Codex（並列） | WI 単位で明確、速度×並列を優先 |

---

## 12) Linear Integration (v5.3)

> Run 成果物 (walkthrough / findings / lessons / test_results) を Linear Issue に同期する。
> GitHub Issues ハイブリッド WI 管理とは独立で並行利用可能（GitHub = merge ゲート、Linear = 実行証跡）。

**認証**: `LINEAR_API_KEY` env 必須（未設定 → graceful skip で exit 0、SDD 本体フロー不停止）
**既定 Team**: `LINEAR_TEAM_KEY=TEC`（Tecnos AI）
**自動同期**: `STRIDE_LINEAR_AUTO=1` で `sdd_planning_bridge.py init`/`evidence` 時に自動トリガー

### コマンド

- LINEAR_INIT: `sdd-templates/bin/stride linear init <feature_dir> <wi_id>`
  - Linear Issue 作成または既存検索、`state.yaml` の `work_items[].linear_issue_id` に記録
- LINEAR_FINDINGS: `sdd-templates/bin/stride linear findings <run_dir>`
  - `.planning/findings.md` を要約して Linear Issue にコメント
- LINEAR_EVIDENCE: `sdd-templates/bin/stride linear evidence <run_dir>`
  - `walkthrough.md` + `test_results.md` を要約してコメント
- LINEAR_LEARN: `sdd-templates/bin/stride linear learn <run_dir>`
  - `.planning/lessons.md` をコメント
- LINEAR_SYNC: `sdd-templates/bin/stride linear sync <run_dir>`
  - findings + evidence + learn を**冪等に一括投下**（推奨 — Run 完了時の 1コマンド）
- LINEAR_CLOSE: `sdd-templates/bin/stride linear close <feature_dir> <wi_id> [--state Done|Canceled]`
  - Linear Issue を Done（既定）または指定状態に遷移
- LINEAR_STATUS: `sdd-templates/bin/stride linear status <feature_dir> [<wi_id>]`
  - WI → Linear Issue マッピング一覧表示
- LINEAR_DRY_RUN: 任意のコマンドに `--dry-run` — API 呼出しせずプレビュー（API key 不要）
- LINEAR_TEST: `sdd-templates/bin/stride linear --test` — 19 オフライン self-tests

### Linear Project 管理 (v5.3.1)

- LINEAR_PROJECT_CREATE: `sdd-templates/bin/stride linear project create <name> [--description <desc>]`
  - Linear Project 作成（または既存検索）、`memory/linear.yaml` に永続化
- LINEAR_PROJECT_LIST: `sdd-templates/bin/stride linear project list`
  - team 内の Linear Project 一覧
- LINEAR_PROJECT_USE: `sdd-templates/bin/stride linear project use <project_id>`
  - 既存 Project を `memory/linear.yaml` に紐付け
- LINEAR_PROJECT_STATUS: `sdd-templates/bin/stride linear project status`
  - 現在の Project binding 確認

### AI Behavior Rules (v5.3 / v5.3.1 Linear Integration)

1. **Run 開始時**（`sdd_planning_bridge.py init` 直後）: `stride linear init <feature> <wi>` で Issue 作成/再利用
   - `STRIDE_LINEAR_AUTO=1` 設定時は自動実行
   - `LINEAR_API_KEY` 未設定時は graceful skip
   - Issue は `memory/linear.yaml` の `project_id` に自動紐付け（v5.3.1）
2. **Run 完了時**（`bridge evidence` 直後）: `stride linear sync <run_dir>` で成果物を一括投下
   - 自動モードでは `bridge evidence` が内部で呼ぶ
3. **WI 承認後**（人間が `WI-*.approval.md` を編集した後）: `stride linear close <feature> <wi>` で Done 遷移
   - 承認前に close しない（state.yaml の `status: done` と連動）
4. **新プロジェクト初期化時** (v5.3.1): `stride new-project <name> --linear-project <name>` で
   専用 Linear Project を自動作成 → `memory/linear.yaml` 永続化
5. **Linear MCP fallback**: Claude Code セッションで直接 Issue 操作が必要な場合、
   `mcp__claude_ai_Linear__save_issue` / `save_comment` / `get_issue` 等の MCP ツールも利用可能
   （CLI と MCP の選択ルール: バッチ/自動化=CLI、対話=MCP）

### 詳細
- エンドユーザー向け: `manual/37_linear_integration_guide.md`
- 実装: `sdd-templates/tools/linear_bridge.py`（urllib ベース、19 self-tests + 10 integration tests）

---

## 13) GitHub Project V2 Integration (v5.3.1)

> 各 STRIDE プロジェクトに専用の GitHub Project V2 を作成し、`memory/github_project.yaml`
> で binding を永続化する。`stride_wi_sync` / Projects 逆同期 / GitHub Actions 全体で参照される SSoT。

**認証**: `gh auth status` が OK であること（未認証時は graceful skip, exit 0）

### コマンド

- PROJECT_CREATE: `sdd-templates/bin/stride project create <title> [--owner <owner>]`
  - GitHub Project V2 作成（または既存検索）、`memory/github_project.yaml` に永続化
- PROJECT_LIST: `sdd-templates/bin/stride project list [--owner <owner>]`
  - owner の Project V2 一覧
- PROJECT_USE: `sdd-templates/bin/stride project use <project_number> [--owner <owner>]`
  - 既存 Project を binding
- PROJECT_STATUS: `sdd-templates/bin/stride project status`
  - 現在の binding 確認

### 解決順位（precedence）

1. CLI `--project-number` 引数
2. `GITHUB_PROJECT_NUMBER` env
3. `memory/github_project.yaml` の `project_number`

### AI Behavior Rules (v5.3.1)

1. **新プロジェクト初期化時**: `stride new-project <name> --github-project "<title>"` で
   Project V2 を自動作成、`memory/github_project.yaml` に永続化
2. **既存プロジェクト導入時**: `stride project use <number> --owner <owner>` で既存 Project に binding
3. **gh 未認証時**: 全コマンドが graceful skip（既存フロー不停止）

### 詳細
- 実装: `sdd-templates/tools/github_project_bridge.py`（gh CLI subprocess、10 self-tests + 8 integration tests）
- テスト: `tests/test_github_project_bridge_integration.py`
