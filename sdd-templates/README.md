# SDD Template Pack — Tecnos-STRIDE Edition

> **Version**: 5.4.0-tecnos-stride | **Methodology**: STRIDE (State-Tracked Run Intent-Driven Engineering)

Specification-Driven Development (SDD) を **Tecnos Japan の実務**（全社横断PJ / ERP・SCM・CRM / AgentOps / バイブコーディング）に適用するためのテンプレート一式です。

- **仕様（Spec）が一次成果物** — Plan/Tasks/Code は仕様からの生成物
- **Two-Layer Governance** — Macro Gate (1-Final) + Micro Run (WI/Run)
- **Multi-Tool Strategy** — Claude Code, Cursor, Copilot 等で共通利用可能

---

## Architecture Overview

```
SDD_MANIFESTO.md (ツール非依存コアルール)
    |
    +-- CLAUDE_WORKFLOW.md (Claude Code 固有)
    +-- .cursor/rules/ (Cursor 固有)
    +-- .github/copilot/ (Copilot 固有)

sdd-templates/
    |-- templates/     SDD テンプレート (basic_design, spec, plan, tasks, ...)
    |-- tools/         CLI ツール群 (stride-lint, pr_readiness_checker, ...)
    |-- memory/        Constitution, Artifact Registry, Org Constraints
    |-- policies/      BPMN Generator Rules
    |-- config/        Monorepo, Testing, Docker, K8s, Terraform, ...
    |-- docs/          実装パターン (DateTime, SQLAlchemy, HTMX, CI/CD, Test)
    |-- hooks/         Phase Gate hooks
    |-- agent_docs/    AI エージェント用操作ガイド
    |-- bin/           stride CLI エントリポイント
```

---

## Getting Started

| Document | Purpose | Time |
|----------|---------|------|
| [QUICKSTART.md](./QUICKSTART.md) | 新規参画者向け最短ルート | 30 min |
| [CHEATSHEET.md](./CHEATSHEET.md) | ID 規約・タグ・エラー一覧 | Reference |
| [MIGRATION.md](./MIGRATION.md) | 旧バージョンからの移行手順 | 20 min |

### Quick Start

```bash
# 1. Feature 初期化（Monorepo + Scale Level 選択）
sdd-templates/bin/stride init <feature-name>              # starter (default)
sdd-templates/bin/stride init <feature-name> --scale standard
sdd-templates/bin/stride init <feature-name> --scale enterprise

# 2. 既存プロジェクト（Brownfield）検出
sdd-templates/bin/stride init <feature-name> --detect

# 3. Lite Mode（小規模 PJ / PoC）
sdd-templates/bin/stride init <feature-name> --lite

# 4. Phase Gate hooks 有効化
sdd-templates/bin/stride hooks
sdd-templates/bin/stride hooks --tool cursor    # Cursor 用
sdd-templates/bin/stride hooks --tool copilot   # Copilot 用

# 5. Lint 実行
sdd-templates/bin/stride lint specs/<feature>/

# 6. PR 作成前品質チェック
sdd-templates/bin/stride pr-check specs/<feature>/
```

### Optional: Enterprise Hierarchy (v4.7)

`--scale enterprise` は **Monorepo / CI の規模設定**です。Epic/Feature 階層を有効化するには、別途 `sdd-templates/config/enterprise.yaml` を使います。

```bash
cat > sdd-templates/config/enterprise.yaml <<'YAML'
enterprise:
  enabled: true
YAML

sdd-templates/bin/stride epic init EPIC-ORDER
sdd-templates/bin/stride init order_import --epic EPIC-ORDER --team TEAM-A
sdd-templates/bin/stride lint specs/order_import/ --enterprise
```

---

## Phase Gate Workflow

### Full Mode (Gates 1-5 + Final)

| Phase | Artifacts | Approval |
|-------|-----------|----------|
| 1: Design | basic_design.md, process.bpmn, APPROVAL.md | Gate 1, 2 |
| 2: Specify | spec.md, plan.md, contracts/\*, tests/scenarios.yaml | Gate 3, 4 |
| 3: Tasking | tasks.md, tests/\* | Gate 5 |
| 4: Execute | src/\* | Final |

### Lite Mode (Gates A, B, C) — small PJ / PoC

| Phase | Artifacts | Approval |
|-------|-----------|----------|
| 1: Design & Flow | basic_design.md, process.bpmn, APPROVAL.md | Gate A |
| 2: Spec & Plan | spec.md, plan.md, contracts/\*, tests/\* | Gate B |
| 3: Implementation | tasks.md, src/\* | Gate C |

> **APPROVAL.md** は人間のみが編集可能。AI は `APPROVAL_PENDING` が出たら停止し承認を待つ。

---

## Tools

### stride CLI (`bin/stride`)

| Command | Description |
|---------|-------------|
| `stride init <feature>` | Feature テンプレート初期化 |
| `stride init --scale <level>` | Scale Level 選択 (starter/standard/enterprise) |
| `stride init --detect` | Brownfield スタック自動検出 |
| `stride init --lite` | Lite Mode 初期化 |
| `stride intake <feature>` | Intake-First 対話モード (v4.4) |
| `stride lint <path>` | stride-lint 実行 |
| `stride pr-check <path>` | PR Readiness 7 チェック統合判定（v5.1: `--mutation` opt-in） |
| `stride evaluate <path>` | Multi-Model LLM 意味的評価（v5.1: `--review` Self-Review Loop） |
| `stride security <path>` | Security Audit (v4.9, `--daily`/`--audit` 2段階) |
| `stride retro <path>` | 定量ふりかえりレポート (v4.9) |
| `stride health <path>` | Runtime Sensors (v5.1, `--runtime` dead code + coverage decay) |
| `stride harness-report <path>` | Harness Report (v5.1, 8 controls 可視化) |
| `stride hooks [--tool <name>]` | Phase Gate hooks セットアップ |
| `stride phase-status` | Gate 承認状態表示 |
| `stride phase-check <file>` | ファイル作成可否チェック |
| `stride auto-continue <path>` | 次フェーズ実行シーケンス生成 |
| `stride ddd-init` | DDD スキャフォールディング |
| `stride decisions init\|refresh` | Decision Index 管理 |
| `stride output-rules` | 出力ルール表示 |
| `stride new-project <name>` | テンプレートから新規プロジェクト初期化 |
| `stride epic init <EPIC_ID>` | Epic 初期化 (v4.7) |
| `stride epic validate <EPIC_ID>` | Epic 検証 (v4.7) |
| `stride epic gates <EPIC_ID>` | Epic Gate 状態表示 (v4.7) |
| `stride epic features <EPIC_ID>` | Epic 配下 Feature 一覧 (v4.7) |
| `stride epic progress <EPIC_ID>` | Epic 進捗サマリ表示 (v4.7) |
| `stride epic list` | Epic 一覧 (v4.7) |
| `stride init <feature> --epic <EPIC_ID> [--team <TEAM_ID>]` | Epic 配下に Feature 作成 (v4.7) |
| `stride lint --enterprise` | Enterprise 拡張検証 (v4.7) |
| `stride lint --all --enterprise` | 全 Feature + 全 Epic を一括検証 (v4.7) |
| `stride symphony run \| dispatch \| status \| validate \| janitor` | Symphony オーケストレーション (v5.2 で bin/stride 統合) |

### Python Tools

| Tool | Tests | Description |
|------|-------|-------------|
| `stride_lint.py` | — | Gate/Lint 検査（AC Coverage, Contract Coverage, Test Tasking, Phase Gate） |
| `stride_lint_enterprise.py` | — | Enterprise 拡張（Epic 参照, Tier 検証, 共有契約検証） |
| `pr_readiness_checker.py` | 10 | **v4.3** PR 作成可否 7 チェック統合ゲート（v5.1 で `--mutation` opt-in 追加） |
| `stride_shared_lib.py` | 8 | **v5.2** Canonical YAML 抽出共通ライブラリ（5 caller 集約） |
| `stride_health.py` | 6 | **v5.1** Runtime Sensors（dead code + coverage decay） |
| `stride_harness_report.py` | 6 | **v5.1** Harness Report（8 controls 可視化） |
| `wi_readiness_checker.py` | 17 | WI 実行準備チェック（Gate/Mode/依存/Ops/State + Execution Authority Check 8） |
| `epic_progress_aggregator.py` | 19 | Epic 横断進捗集約（summary/json/markdown/weekly） |
| `run_resume_detector.py` | 6 | 中断 Run 自動再開検出 |
| `brownfield_detector.py` | 8 | 既存プロジェクトスタック検出 |
| `spec_drift_detector.py` | 6 | **v4.2** OpenAPI ↔ src 仕様ドリフト検出 |
| `evidence_metrics_collector.py` | 6 | **v4.2** カバレッジ/テスト/キャッシュ/リードタイム収集 |
| `epic_validator.py` | — | Epic 構造検証 |
| `approval_router.py` | — | 委任承認ルーティング（route/validate/parallel） |
| `dependency_checker.py` | — | 依存サイクル検出・DOT グラフ生成 |
| `auto_continue_runner.py` | — | Auto-Continue Planner |
| `decision_index.py` | — | ADR Decision Index 管理 |
| `erp_addon_exec_tracking.py` | — | ERP Addon 実行トラッキング |
| `phase_gate.py` | — | Phase Gate チェック |
| `setup_hooks.py` | — | Hook 自動セットアップ |

---

## Templates

### Core SDD Templates

| Template | Purpose |
|----------|---------|
| `basic_design_template.md` | HITL ハブ（Canonical YAML + Gate + Autonomy Bias） |
| `spec_template.md` | WHAT/WHY（Canonical YAML + e2e タグ + Spec-as-Code） |
| `plan_template.md` | HOW（coverage_policy + tooling + reporting） |
| `tasks_template.md` | 実行可能タスク（E2E 基盤 + triage タスク） |
| `walkthrough_template.md` | Run 完了ウォークスルー（Review Checklist + Planning Evidence） |
| `evidence_pack_template.md` | ゲート証跡（Evidence Pack + Metrics Trend） |
| `work_item_template.md` | Work Item テンプレート |
| `work_item_approval_template.md` | WI Pre-Run 承認テンプレート |
| `state_template.yaml` | STRIDE State YAML |
| `APPROVAL.md` | Full Mode 承認記録（人間のみ編集可） |
| `APPROVAL_LITE.md` | Lite Mode 承認記録 |

### Enterprise Templates

| Template | Purpose |
|----------|---------|
| `epic_design_template.md` | Epic 設計 |
| `feature_breakdown_template.md` | Feature 分割 |
| `EPIC_APPROVAL.md` | Epic Gate 承認記録 |
| `approval_matrix_template.yaml` | 委任承認マトリクス |
| `shared_contract_template.yaml` | 共有契約（API/Event/File） |
| `shared_contract_registry_template.yaml` | 契約レジストリ |
| `cross_team_dependency_manifest_template.yaml` | チーム間依存マニフェスト |
| `cross_refs_template.yaml` | クロスリファレンス |
| `ccp_template.md` | 契約変更提案（CCP） |
| `dependency_manifest_template.yaml` | 依存宣言 |
| `ops_pack_registry_template.yaml` | Ops 準備追跡 |
| `epic_progress_report_template.md` | PM 週次レポート |
| `team_status_report_template.md` | チームリード報告 |

### DDD / ADR Templates (v4.1)

| Template | Purpose |
|----------|---------|
| `ddd_domain_model_template.md` | DDD ドメインモデル |
| `ddd_technical_design_template.md` | DDD 技術設計 |
| `adr_template.md` | Architecture Decision Record |

### Contract Templates

| Template | Purpose |
|----------|---------|
| `contracts/openapi_template.yaml` | OpenAPI 3.1 スケルトン |
| `contracts/database_schema_template.yaml` | DB スキーマ定義 |
| `contracts/database_schema_input.csv` | AI 生成用 CSV 入力 |

### Ops / BPMN Templates

| Template | Purpose |
|----------|---------|
| `ops_template.md` | Operations ベースライン |
| `ops/` | Ops runbook / release / rollback / transport manifest |
| `process_bpmn_template.bpmn` | Camunda 8 (Zeebe 8.8) BPMN スケルトン |

### Samples

| サンプル | パス | 説明 |
|---------|------|------|
| フラット Feature | `sdd-templates/specs/sample_feature/` | Enterprise なしのシンプルな Feature |
| Enterprise Epic | `epics/EPIC-SAMPLE/` | Epic 設計・承認・進捗管理のサンプル |
| Enterprise Feature | `specs/FEAT-ERPSAMPLE/` | Epic 配下 Feature（`epic_ref` / `team_id` 設定済み） |

> `stride new-project` 実行時にサンプルは自動削除されます（`--keep-samples` で保持）。

### Testing Templates

| Template | Purpose |
|----------|---------|
| `tests/e2e.spec.template.py` | Python E2E (pytest-playwright) |
| `tests/conftest_e2e.template.py` | Python E2E fixtures |
| `tests/e2e.spec.template.ts` | TypeScript E2E |
| `tests/playwright.config.template.ts` | Playwright 設定 |

### GitHub Actions / Projects Templates

| Template | Purpose |
|----------|---------|
| `github-actions/epic-progress-report.yml` | Epic 進捗ダッシュボード自動生成 |
| `github-projects/` | GitHub Projects V2 テンプレート |

---

## Configuration

### Monorepo (v4.2 — Always-On)

`stride init` は常に Turborepo 構成を配置。`--scale` で段階選択:

| Scale | Contents | Use Case |
|-------|----------|----------|
| **starter** (default) | turbo.json (build+test), tsconfig.base.json, 簡易 CI | PoC, 小規模 |
| **standard** | Full Turborepo + vitest.workspace + 差分実行 CI | 中規模チーム |
| **enterprise** | Standard + リモートキャッシュ + Evidence Pack (90 日保持) | 大規模・監査要件 |

Files: `config/monorepo/turbo.*.json`, `config/monorepo/github-actions/ci-*.yml`, `config/monorepo/vitest.workspace.ts`, `config/monorepo/package-templates/`

### Enterprise Hierarchy (v4.7 — Optional)

`config/enterprise.yaml` は Epic/Feature 階層と Enterprise 拡張 lint の On/Off を制御します。

| File | Purpose |
|------|---------|
| `config/enterprise.yaml` | Enterprise Hierarchy の有効化フラグ (`enterprise.enabled`) |

有効化すると以下が使えます。

- `stride epic init|validate|gates|features|progress|list`
- `stride init <feature> --epic <EPIC_ID> [--team <TEAM_ID>]`
- `stride lint --enterprise`

### Testing (5-Language Support)

`config/testing/` — Python, TypeScript, Rust, Go, Java

### Infrastructure

| Directory | Contents |
|-----------|----------|
| `config/docker/` | Dockerfile (Python/Node), docker-compose, .dockerignore |
| `config/kubernetes/` | Deployment, Service, Ingress, HPA, ConfigMap, Kustomize |
| `config/terraform/` | AWS VPC/EKS/RDS/ElastiCache IaC |
| `config/security/` | CORS, CSP, セキュリティヘッダー |
| `config/env/` | .env.example, 環境変数管理 |
| `config/typescript/` | tsconfig.json, ESLint (any 禁止) |
| `config/observability/` | OpenTelemetry, Prometheus |

---

## Memory & Policies

| File | Purpose |
|------|---------|
| `memory/constitution.md` | Fourteen Articles + ID 規約 + Gates |
| `memory/tecnos_org_constraints.md` | Tecnos 組織制約 (AI Policy / RACI+ / Evidence Pack) |
| `memory/artifact_registry.md` | 成果物マスター (ID / 版 / 保管先) |
| `policies/bpmn_generator_rules.md` | Camunda 8 BPMN 生成ルール |
| `config/id_conventions.yaml` | ID パターン定義 (Reference Copy) |

---

## Implementation Patterns

| Document | Topic |
|----------|-------|
| `docs/DATETIME_PATTERNS.md` | UTC-first 設計 (datetime.utcnow() 禁止) |
| `docs/SQLALCHEMY_PATTERNS.md` | 非同期 ORM, N+1 対策, マイグレーション |
| `docs/HTMX_PATTERNS.md` | JSON/HTML 両立 (/api/ vs /partials/) |
| `docs/TEST_PATTERNS.md` | 検証済みテストパターン集 |
| `docs/CI_CD_INTEGRATION.md` | CI/CD パイプライン設定ガイド |

---

## Agent Docs

AI エージェント向け操作ガイド（repo root 配置。Claude Code / Cursor / Copilot 共通参照可能）:

| File | Purpose |
|------|---------|
| `../agent_docs/sdd_bootstrap.md` | 全必須ルール統合（AI が最初に読む 1 ファイル） |
| `../agent_docs/sdd_guidelines.md` | SDD ワークフロー完全ガイド |
| `../agent_docs/commands.md` | CLI コマンドリファレンス (SSoT) |
| `../agent_docs/testing.md` | テスト実行ガイド (5 言語対応) |
| `../agent_docs/conventions.md` | コーディング規約 |
| `../agent_docs/security.md` | セキュリティガイドライン |
| `../agent_docs/project_map.md` | プロジェクト構造マップ |

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| **5.4.0** | 2026-04-24 | Reporting Lightening (Profile-Aware) — `basic_design.profile` SSoT + state.yaml top-level cache で 3 Profile (enterprise-erp / saas-integration / prototype)。`shared/policies/profile_policy.yaml` 新設。`stride init --profile` / `stride pr-check --summary-line` / stride-lint PROFILE_* / bootstrap §5 Profile-Dependent Reporting / Completeness Profile-aware 閾値 (200/150/100 行 × 5/4/3 ファイル) / 20 新規テスト / manual/38_profile_guide.md。**BPMN / Evidence / SEC-006 / Ops Pack / Epic-Feature / Coverage Tier は全 Profile で現行正本のまま不変**（canonical_source 参照） |
| **5.3.3** | 2026-04-17 | BPMN Rule Compliance Enforcement — sdd_bootstrap §4-BPMN 新設（Step 1-6 MUST-DO + FEAT/EPIC 決定ツリー + 14+9 Hard Requirements）/ docs/bpmn_quick_reference.md 新規作成 / epic_flow_template に xsi + isExecutable 明示 / epic_validator 内部 process 検証強化 / stride_lint に sourceRef/targetRef 参照整合性チェック / basic_design_template に BPMN ID 一致ルール明記 |
| **5.3.2** | 2026-04-22 | Template Scaffolding Bug Fixes — `.claude/settings.json` cleanup + stride-new-project.sh Step 4 force + Step 6 exit code fix + --org-missing graceful skip |
| **5.3.1** | 2026-04-19 | Per-Project Tracker Isolation — stride linear project + stride project (GitHub V2) subcommand groups / memory/linear.yaml + memory/github_project.yaml SSoT / stride new-project auto-creates tracker bindings / graceful skip when credentials missing |
| **5.3.0** | 2026-04-19 | Linear Integration — linear_bridge.py (urllib GraphQL, zero deps) + stride linear CLI (7 subcmds) + STRIDE_LINEAR_AUTO auto-sync from planning_bridge + 19 self-tests + 10 integration tests + manual ch.37 |
| **5.2.1** | 2026-04-19 | Symphony Agent Reproducibility (claude_code.model / effort_level / max_output_tokens) + SEC-006 Provenance Expansion (6 new keywords) + .entire/ gitignore + manual P2 fixes |
| **5.2.0** | 2026-04-17 | Opus 4.7 Literal-Follow Tuneup + Hermeticity (Governance hardening / Instruction Precedence / `stride_shared_lib.py` / `stride symphony` CLI 統合 / Execution Authority E2E / hermetic pytest) |
| **5.1.0** | 2026-04-07 | Harness Maturity (Mutation Testing / Self-Review Loop / Runtime Sensors / Harness Report / Janitor Proposals) |
| **5.0.0** | 2026-04-02 | CLI UX Maturity (clig.dev準拠 — カラー/NDJSON/TSV/パスtypo/YAML事前検証/アクター追跡) + Docsify GitHub Pages |
| **4.9.0** | 2026-03-31 | Completeness Principle / `stride security` / `stride retro` |
| **4.8.0** | 2026-03-23 | Database Lifecycle / Camunda 8.8 BPMN Refresh |
| **4.7.0** | 2026-03-16 | Enterprise Hierarchy CLI Integration (`enterprise.yaml`, `stride epic`, `stride init --epic`, `stride lint --enterprise`) |
| **4.6.0** | 2026-03-11 | Schema-Gated AI Authority (Execution Authority 3層権限宣言 + Article XIV + Check 8) |
| **4.5.1** | 2026-03-10 | Tier Mismatch WARN + Amendment Fast Track + PM Quick Start |
| **4.5.0** | 2026-03-04 | BDD Acceptance Criteria + Symphony Orchestration |
| **4.4.0** | 2026-02-15 | AI Autonomous Execution (AI 全作業自律実行 + Intake 対話 + Bootstrap Onboarding) |
| **4.3.0** | 2026-02-14 | PR Readiness Checker (7 チェック統合品質ゲート) |
| **4.2.0** | 2026-02-14 | Monorepo Default + Scale Levels + Spec Drift + Evidence Metrics |
| **4.1.0** | 2026-02-08 | Auto-Continue, DDD Scaffolding, Decision Index, Output Rules |
| **4.0.0** | 2026-02-08 | Multi-Tool Strategy (SDD_MANIFESTO.md split, stride hooks --tool) |
| **3.3.0** | 2026-02-08 | Brownfield Detection + Auto-Init (stride init --detect) |
| **3.2.0** | 2026-02-08 | Operational Maturity (Review Checklist, TOC, GH Actions, Planning Evidence) |
| **3.1.0** | 2026-02-07 | Autonomy Bias + Run Resume Detection |
| **3.0.1** | 2026-02-07 | Planning Integration for Run Execution |
| **3.0.0** | 2026-02-07 | STRIDE Multi-Team Edition (PM Dashboard, WI Checker, Mode Policy) |
| **2.0.0** | 2026-01-20 | Enterprise Edition (Epic/Feature, Coverage Tiers, CCP Workflow) |
| **1.2.6** | 2026-01-19 | VERSION file SSoT, directory rename |
| **1.2.5** | 2026-01-07 | Bug fixes, gate header consistency |
| **1.2.4** | 2026-01-06 | stride CLI, Lite Mode, Docsify Manual, 5-Language Testing |
| **1.2.3** | 2025-12-31 | HITL Approval, Phase Gate, Evidence Pack |

See [CHANGELOG.md](./CHANGELOG.md) for full details.

---

## Notes (Tecnos Operations)

- **Exceptions**: Constitution Article に紐付け `{article, reason, mitigation}` の 3 点セットで記録
- **ERP/SCM/CRM**: 「契約・監査・運用・SoD」を必須論点。`memory/tecnos_org_constraints.md` を参照
- **AI Agent**: CI ゲートは決定論的に維持。MCP は生成・triage・再現に限定
- **Evidence Pack**: CI/テスト/SAST/SCA/Secrets/AI プロヴェナンスをゲート証跡として保存
- **Autonomy Bias**: autonomous/balanced/controlled の 3 段階。critical tier は常に最低 confirm

---

*SDD Template Pack v5.4.0-tecnos-stride — Tecnos Japan*
