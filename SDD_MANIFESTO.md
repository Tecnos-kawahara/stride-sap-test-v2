# SDD Manifesto - Spec-Driven Development Core Rules
# Tool-Agnostic | Tecnos-STRIDE Enterprise Edition
#
# This file defines the INVIOLABLE rules for SDD projects.
# It is consumed by all AI tools (Claude Code, Cursor, Copilot, etc.).
# Tool-specific configuration lives in separate files.

## Principle

The Spec IS the Code. The Code is just a compile artifact.

## Completeness Principle — 湖を沸かせ (Boil the Lake, Profile-Aware v5.4)

> Inspired by gstack (garrytan/gstack, MIT License)

AIが実行する場合、追加の完成度コストはほぼゼロに近い。
「だいたい動く」実装ではなく「全ACを満たす」実装を常に選べ。

| 作業種別 | 人間チーム | AI + STRIDE | 圧縮率 |
|----------|-----------|-------------|--------|
| ボイラープレート | 2日 | 15分 | ~100x |
| テスト追加 | 1日 | 15分 | ~50x |
| WI 実装 | 1週間 | 30分 | ~30x |
| バグ修正 | 4時間 | 15分 | ~20x |

### 湖 (lake) 判定閾値 — Profile 別（AND logic：両方満たして「湖」、いずれか超過は「海」）

| Profile | 行数上限 | ファイル数上限 |
|---------|---------|---------------|
| `enterprise-erp` | +200 行 | +5 ファイル |
| `saas-integration` | +150 行 | +4 ファイル |
| `prototype` | +100 行 | +3 ファイル |

Profile の解決順位：`basic_design.profile` → `state.yaml` top-level `profile` → fallback `enterprise-erp`。
詳細: `shared/policies/profile_policy.yaml`

### 全 Profile 共通の「海」トリガー（いずれか該当で Phase 分割提案）

1. **risk_flags の新規追加**（`authz/sod/pii/accounting_calc/db_schema/data_migration`）→ Profile に関わらず最優先の「海」トリガー
2. **承認済み成果物の変更**（basic_design / spec / plan / tasks の改変）
3. **新規 AC / 新規契約 / 新規 NFR の創出**
4. 上表の Profile 別上限の超過

### 判定の優先順位（literal-follow 用 — 上から順に評価して最初に該当した時点で確定）

1. `risk_flags` 新規追加 → 即「海」（他の判定より優先、Profile 不問）
2. 承認済み成果物の変更 → 即「海」
3. 新規 AC/契約/NFR の創出 → 即「海」
4. 行数・ファイル数の Profile 閾値チェック（両方満たせば「湖」、いずれか超過で「海」）
5. 上記すべて通過 → 「湖」として即実装

手を抜くことは、後から人間が直すことを意味する。
AIにとっての限界費用がゼロなら、完全にやらない理由はない。
ただし「湖」を超える「海」を沸かそうとすれば承認体系を壊す。**上記の優先順位を literal に判定すること**。

## Project Context
- Goal: Defined in `basic_design.md` (who/what/why) and `spec.md` (overview).
- Artifacts: `specs/<feature>/` (basic_design, process.bpmn, spec, plan, tasks, evidence)
- Constraints: `memory/tecnos_org_constraints.md` (Audit, ERP, Security - INVIOLABLE)

## Single Source of Truth (SSoT) Hierarchy
1) Intent & Flow: `basic_design.md` (Why), `process.bpmn` (Flow)
2) Specs: `spec.md` (Requirements), `plan.md` (Architecture), `tasks.md` (WBS)
3) Contracts: `contracts/` (OpenAPI, etc.)
4) Code: Implementation
*Rule: Never change #4 without updating #1-#3. Code that deviates from Spec is a bug in the Code.*

## Enforced Workflow

> **Execution Model (v4.4)**: AI（Claude Code等）が全作業の「実行者」(R)。
> 人間は「承認者」(A) として APPROVAL.md の編集のみ行う。
> Lint, init, テスト, Evidence作成等はすべて AI が自律実行する。

0) **Orientation (AI auto)**
   - Use only the Tecnos templates (no ad-hoc markdown).
   - Do not edit derived `counts` blindly; update them to match `COUNTS_SUGGESTION` after lint.
   - Do not rename or remove canonical YAML headings; `stride-lint` extracts those blocks.
1) **Design (AI auto → HITL at Gate 1,2)**
   - AI: `stride init <feature> --detect` でスキャフォールド（未作成時）
   - AI: `memory/artifact_registry.md` の存在確認・作成
   - AI: プレースホルダ置換
   - AI: `basic_design.md` & `process.bpmn` 作成。`delivery_model` & `RACI+` 設定。
   - AI: `stride-lint` 実行 → PASS するまで自動修正（**最大 5 回、以降停止して報告**）
   - AI: gate flags を lint 結果に基づいて設定
   - AI: BPMN 承認後、`process_bpmn_linked`, `process_bpmn_approved`, `ready_for_specify` を設定
   - **HITL**: Gate 1,2 → 人間が APPROVAL.md を編集
2) **Specify (AI auto → HITL at Gate 3,4)**
   - AI: `spec.md` 作成（AC, NFR, `spec_as_code`, blocking questions 解決）
   - AI: `plan.md` 作成（3-layer coverage, tests, `evidence_pack`）
   - AI: contracts/ 作成
   - AI: gate flags を設定
   - AI: `stride-lint specs/<feature>/` → MUST PASS（FAILなら自動修正、**最大 5 回**）
   - AI: `e2e` タグは critical user journeys のみに適用
   - **HITL**: Gate 3,4 → 人間が APPROVAL.md を編集
3) **Tasking (AI auto → HITL at Gate 5)**
   - AI: `tasks.md` 作成。全 Task に `plan_refs` を設定。
   - AI: `e2e`タグAC存在時は E2E harness, test, triage tasks を含める
   - AI: `stride-lint` 実行 → PASS するまで自動修正（**最大 5 回、同一エラーコード 3 連続で停止**）
   - AI: `tasks_gate_check.tasks_ready_for_code = true` 設定
   - **HITL**: Gate 5 → 人間が APPROVAL.md を編集
4) **Execute & Verify (AI auto → HITL at WI approval & Final)**
   - AI: タスクを1つずつ実装
   - AI: **完了報告前の必須確認**（Task Completion Checklist）を自律実行:
     1. 該当タスクの `spec_refs` の全ACを再読
     2. 各ACの全要素充足を確認
     3. `tests/scenarios.yaml` の該当シナリオの全 `expected` を検証
     4. 「動いた」≠「完了」。ACの全要素を満たして初めて完了。
   - AI: **Outer Loop** 自動実行: `stride-lint` + Tests + Evidence 生成
   - AI: `evidence_pack.md` を CI proofs で更新
   - AI: specs/plans 変更時は即座に `stride-lint` を再実行
   - AI: `stride pr-check .` → PR_READY 確認
   - **HITL**: WI-*.approval.md → 人間が編集
   - **HITL**: Final Gate → 人間が APPROVAL.md を編集

## Quality Gates (Canonical Commands)
- **Lint Specs**: `sdd-templates/bin/stride lint specs/<feature>/` (CRITICAL)
- **Tests**: Use the Plan's test strategy.
- **Verification**: Ensure `evidence_pack` is populated before closing tasks.

## Interaction Norms
- **AI Role**: You are "Responsible" (R), Human is "Accountable" (A).
- **Stop Condition**: If `memory/tecnos_org_constraints.md` is violated (e.g., direct DB write), STOP and ask.

## CRITICAL: APPROVAL.md - Human-Only File

> **ABSOLUTE PROHIBITION**: AI agents are **FORBIDDEN** from editing `APPROVAL.md` under any circumstances.

### What is APPROVAL.md?
- Located at `specs/<feature>/APPROVAL.md`
- Records human approval for each gate (1-5 and Final)
- Contains checkboxes and approver signature fields

### Rules for AI:
1. **NEVER edit APPROVAL.md** - This file is exclusively for human editing
2. **NEVER set checkboxes** `[x]` in APPROVAL.md
3. **NEVER fill in approver names** or dates in APPROVAL.md
4. **DO NOT suggest workarounds** to bypass approval requirements

### What AI CAN do:
- Read APPROVAL.md to check status
- Inform the user when approval is pending
- Explain what needs to be approved
- Wait for human to complete approval before proceeding

### Enforcement:
- `stride-lint` checks APPROVAL.md for valid human approvals
- Gate progression is blocked until human approves in APPROVAL.md
- Violations will cause lint to fail with `APPROVAL_PENDING` error

### Example Workflow:
```
1. AI completes work for Gate 3
2. AI runs stride-lint -> PASSES structural checks
3. AI runs stride-lint -> FAILS with APPROVAL_PENDING (Gate 3 not approved)
4. AI informs user: "Gate 3 requires your approval in APPROVAL.md"
5. Human edits APPROVAL.md: checks boxes, adds name/date
6. AI runs stride-lint -> PASSES (including approval check)
7. AI proceeds to Gate 4
```

## Execution Authority Separation (v4.6.0)

> **Reference:** Cook, S. et al. (2026). "Talk Freely, Execute Strictly: Schema-Gated Agentic AI
> for Flexible and Reproducible Scientific Workflows." arXiv:2603.06394.

AI agentの権限は3層に分離される。詳細は `shared/policies/mode_policy.yaml` の `execution_authority` セクションを参照。

| 権限層 | 説明 | ゲート機構 |
|--------|------|-----------|
| **Conversational** | 解釈・提案・lint修正 | なし（自律実行） |
| **Gated** | 成果物作成・WI着手・PR作成 | stride-lint + phase_gate.py + wi_readiness_checker.py |
| **Prohibited** | APPROVAL.md編集・Gate skip | 絶対禁止（既存ルールで担保済み） |

### 3モードと検証スコープの対応

| Mode | 検証スコープ | 対応する権限層 |
|------|-------------|---------------|
| autopilot | ツールレベル（stride-lint PASS） | conversational + gated（最小検証） |
| confirm | ワークフローレベル（+ plan_review） | conversational + gated（中程度検証） |
| validate | ドメインレベル（+ design_diff_review） | conversational + gated（最大検証） |

## CRITICAL: Phase Gate Enforcement (INVIOLABLE)

> **この規則は絶対に破ってはならない。違反はセキュリティ違反と同等に扱う。**

### Phase Gate の仕組み

SDDでは、ファイル作成は **Phase順序** に従う必要がある：

| Phase | 作成可能なファイル | 次のPhaseを解放する承認 |
|-------|-------------------|------------------------|
| 1: Design | basic_design.md, process.bpmn, APPROVAL.md | Gate 1, 2 |
| 2: Specify | spec.md, plan.md, contracts/*, implementation-details/*, tests/scenarios.yaml | Gate 3, 4 |
| 3: Tasking | tasks.md, tests/* | Gate 5 |
| 4: Execute | src/* | Final |

> **重要**: テストファイルは `specs/<feature>/tests/` に格納する（ルートの `tests/` ではない）。
> `pyproject.toml` の `testpaths` は `["specs/<feature>/tests"]` に設定すること。

### 必須プロセス（各Phase完了時）

```
1. ファイルを作成する
2. stride-lint を実行する
3. APPROVAL_PENDING が表示されたら:
   ┌─────────────────────────────────────────────────┐
   │ ⛔ ここで完全に停止する                          │
   │                                                 │
   │ 次のファイルを作成してはならない                 │
   │ 次のPhaseに進んではならない                     │
   │ ユーザーに承認を依頼する                        │
   │ ユーザーが APPROVAL.md を編集するのを待つ       │
   └─────────────────────────────────────────────────┘
4. ユーザーが承認を完了したと報告したら続行
```

### AI の行動規則

1. **Phase 1 ファイル作成前**: チェック不要（最初のPhase）
2. **Phase 2 ファイル作成前**: `phase_gate.py check` を実行
3. **BLOCKED が返されたら**: ファイルを作成しない、ユーザーに報告
4. **stride-lint 実行後 APPROVAL_PENDING**: 完全停止、次に進まない

## CRITICAL: Post-Approval Change Rule (INVIOLABLE)

> **承認済み成果物の変更禁止ルール - この規則は絶対に破ってはならない**

### 原則

Gate を通過した成果物は、その Gate の承認が有効である限り変更してはならない。

| Gate 通過後 | 変更禁止ファイル |
|-------------|-----------------|
| Gate 1, 2 | basic_design.md, process.bpmn |
| Gate 3, 4 | spec.md, plan.md, contracts/ |
| Gate 5 | tasks.md |

### 変更が必要な場合の手順

```
1. 変更理由を implementation-details/change_log.md に記録する
2. 該当 Gate の再承認をユーザーに依頼する
3. ユーザーが APPROVAL.md を更新するのを待つ
4. 再承認完了後、変更を適用する
```

### AI の行動規則

1. **承認済みファイルを Edit/Write する前に、必ず再承認の必要性を報告する**
2. **ユーザーが再承認を完了するまで変更しない**
3. **緊急の場合も、変更理由を明記し再承認を経る**

### 違反時の対処

1. 変更内容を change_log.md に記録する
2. 該当 Gate の再承認を依頼する
3. 再承認が完了するまで次の Phase に進まない

### Pre-Approval Lint Rule

承認依頼の**前**に stride-lint を実行し、APPROVAL_PENDING 以外のエラーを全て解消すること。
これにより、承認後の成果物変更を未然に防ぐ。

```
[正しいフロー]
1. ファイル作成・編集
2. stride-lint 実行
3. エラー解消（APPROVAL_PENDING 以外）
4. 承認依頼 ← ここで初めて依頼
5. 承認完了
6. 次の Phase へ

[誤ったフロー]
1. ファイル作成・編集
2. 承認依頼 ← lint 前に依頼してしまう
3. 承認完了
4. stride-lint 実行 → エラー発見
5. ファイル修正 ← 承認後の変更（違反）
```

## Auto-Continue Rule (Phase Execution)

- Execute phase-internal steps continuously without intermediate confirmation.
- Stop only at HITL checkpoints (Gate approvals in `APPROVAL.md`).
- Use `sdd-templates/bin/stride auto-continue specs/<feature>/` to generate the next sequence.

## Mandatory Output Rules

- Do not use fixed-width ASCII tables in AI terminal output.
- For choices, use `N - **Option**: Description`.
- Status labels must be one of: `PASS`, `FAIL`, `WARN`, `SKIP`.
- Multi-step progress must use `[n/N]` format.

## Optional DDD Path (validate mode)

- For high-risk work (`mode: validate`), `delivery_model.type: ddd` can be selected in `basic_design.md`.
- When DDD is enabled, maintain:
  - `implementation-details/domain_model.md`
  - `implementation-details/technical_design.md`
  - `shared/decisions/decision-index.md` + ADR files (`ADR-*.md`)
- Bootstrap artifacts via `sdd-templates/bin/stride ddd-init <feature>`.

## Decision Index (ADR)

- Architectural decisions must be tracked as ADR files under `shared/decisions/`.
- Keep `shared/decisions/decision-index.md` updated using:
  - `sdd-templates/bin/stride decisions init`
  - `sdd-templates/bin/stride decisions refresh`

## PR Readiness Rule (v4.3)

WI 完了後、PR を作成する前に `stride pr-check` を実行し、7つの品質チェックに合格すること。

- **実行**: `sdd-templates/bin/stride pr-check <project_root>` (または `python3 sdd-templates/tools/pr_readiness_checker.py <project_root>`)
- **判定**: 全チェック PASS → PR_READY (exit 0)、FAIL あり → NOT_READY (exit 1)
- **チェック項目**:
  1. stride-lint (APPROVAL_PENDING 除外)
  2. spec:drift (critical > 0 → FAIL)
  3. tests (failed > 0 → FAIL)
  4. coverage (tier 閾値未満 → FAIL)
  5. walkthrough checklist (未チェック項目あり → FAIL)
  6. evidence_pack (存在しない → FAIL)
  7. TODO/FIXME scan (`--strict` 時のみ FAIL)

## CI/CD Requirements (Monorepo) (v4.2)

Monorepo は SDD プロジェクトのデフォルト構成。`stride init` は常に Turborepo 設定を配置する。
スケールレベル（`--scale`）により複雑度を段階的に選択可能：

| Scale | 対象 | 構成 |
|-------|------|------|
| **starter** (default) | 小規模・初回 SDD | turbo.json (build+test), tsconfig.base.json, 簡易 CI |
| **standard** | 複数サービス | Full Turborepo + vitest.workspace.ts + 差分実行 CI |
| **enterprise** | CBP クラス | Standard + リモートキャッシュ + 完全差分実行 + Evidence Pack (90日保持) |

### 共通ルール

- **キャッシュ**: タスクの inputs/outputs を明示し、不要な再実行を防止
- **SDD Lint**: `stride lint --all --warn-only` は Turborepo パイプライン外で実行（全 Feature 横断検証）

### Standard / Enterprise 追加

- **差分実行**: `turbo run test --filter=...[HEAD~1]` で PR 影響範囲のみテスト
- **契約テスト**: `test:contract` タスクで Spec 変更時に契約テストを自動実行
- **Evidence Pack**: `turbo run test:coverage` の結果を CI 成果物として保存

### スケール選択

```bash
stride init <feature>                     # → Starter（デフォルト）
stride init <feature> --scale standard    # → Standard
stride init <feature> --scale enterprise  # → Enterprise
```

Starter でも turbo.json と workspaces は配置される。成長に応じて standard/enterprise へ自然に移行可能。

### Living Spec Drift Detection (v4.2)

contracts/ と src/ の乖離を自動検出し、SSoT 原則（Intent → Specs → Contracts → Code）を維持する。

- **`spec_drift_detector.py`** — OpenAPI YAML を解析し、src/ のルート定義と比較
- **検出ドリフト種別**:
  - `endpoint_not_implemented` (critical): 契約にあるが src/ にない
  - `contract_outdated` (high): src/ にあるが契約にない
  - `schema_mismatch` (medium): レスポンスフィールドが TypeScript 型と不一致
  - `parameter_missing` (medium): 必須パラメータがハンドラで未使用
- **CI 統合**: `spec:drift` タスクが standard/enterprise CI で自動実行
- **codegen_config.yaml**: OpenAPI → TypeScript 型生成の設定テンプレート

### Evidence Pack Measurement (v4.2)

CI メトリクスを収集し、Evidence Pack にトレンドデータを蓄積する。

- **`evidence_metrics_collector.py`** — coverage, テスト結果, キャッシュ率, Gate リードタイムを収集
- **`metrics_trend`** セクション: evidence_pack_template.md にトレンド追跡フィールド追加
- **Enterprise CI**: メトリクス収集ステップが evidence-pack アーティファクトに自動含有
