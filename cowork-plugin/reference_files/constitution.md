---
artifact: "constitution"
constitution_id: "CONST-TECNOS-001"
title: "SDD Development Constitution (Tecnos Edition)"
version: "6.0.0-tecnos-stride-value"
status: "active" # draft | in_review | active | superseded
owners:
  - { name: "Tecnos Architecture Board", role: "Owner" }
  - { name: "Tecnos PMO / Business Promotion", role: "Co-maintainer" }
last_reviewed_at: "2026-04-29"
amendment_history:
  - { date: "2025-12-17", version: "1.2.0-tecnos", note: "Tecnos org constraints + Camunda 8 + Basic Design hub + stable IDs" }
  - { date: "2025-12-30", version: "1.2.1-tecnos", note: "Coverage Policy (AC/CT/Code) + Tagged AC enforcement + E2E Playwright + AgentOps triage flow" }
  - { date: "2025-12-30", version: "1.2.2-tecnos", note: "Schema/ID/path/coverage_policy alignment across docs/templates" }
  - { date: "2025-12-31", version: "1.2.3-tecnos", note: "TEIM improvements: RACI+ (Human/AI/CI), Spec-as-Code, Evidence Pack, Artifact Registry, FtoS exit criteria" }
  - { date: "2026-01-06", version: "1.2.5-tecnos", note: "Lite Mode support, Phase Gate security fixes, Python E2E templates, infrastructure templates" }
  - { date: "2026-01-19", version: "1.2.6-tecnos", note: "Version management overhaul: VERSION file as SSoT, directory renamed to sdd-templates, auto Phase Gate hook configuration with robust JSON handling" }
  - { date: "2026-01-20", version: "2.0.0-tecnos-enterprise", note: "Enterprise Edition: Epic/Feature階層、3段階カバレッジTier、委任承認マトリクス、共有契約レイヤー、依存管理、CCPワークフロー、Articles X-XII追加" }
  - { date: "2026-02-07", version: "3.0.0-tecnos-stride", note: "STRIDE Edition: PM進捗ダッシュボード、チームステータスレポート、共有契約レジストリ、チーム間依存マニフェスト、Opsパックレジストリ、進捗集約ツール、WI実行準備チェッカー、Article XIII追加" }
  - { date: "2026-02-07", version: "3.1.0-tecnos-stride", note: "Adaptive Execution: Autonomy Bias System（Mode調整メカニズム）、Run Resume Detection（中断Run自動再開）" }
  - { date: "2026-02-08", version: "3.2.0-tecnos-stride", note: "Operational Maturity: Walkthrough Review Checklist、Phase Quick Reference TOC、GitHub Actions Dashboard自動化、Planning Evidence統合、Evidence Pack Planning参照追加" }
  - { date: "2026-02-08", version: "3.3.0-tecnos-stride", note: "Brownfield & Auto-Init: brownfield_detector.py（マニフェスト解析）、stride init --detect（既存スタック自動検出）、delivery_model自動設定" }
  - { date: "2026-02-08", version: "4.0.0-tecnos-stride", note: "Multi-Tool Strategy: SDD_MANIFESTO.md分離（ツール非依存コアルール）、CLAUDE_WORKFLOW.md（Claude固有設定）、stride hooks --tool（Cursor/Copilot/Manual対応）" }
  - { date: "2026-02-08", version: "4.1.0-tecnos-stride", note: "Roadmap Optimization: Auto-Continue（phase内連続実行）、Mandatory Output Rules、DDD optional scaffolding、Decision Index (ADR) 追加" }
  - { date: "2026-02-14", version: "4.2.0-tecnos-stride", note: "Monorepo Default + Scale Levels: Monorepoをデフォルト化、--scale starter/standard/enterprise、Scale別turbo.json/CI テンプレート、SDD_MANIFESTO CI/CD Requirements更新" }
  - { date: "2026-02-14", version: "4.3.0-tecnos-stride", note: "PR Readiness Checker: 7チェック統合PR品質ゲート（stride-lint, spec:drift, tests, coverage, walkthrough, evidence_pack, TODO/FIXME）、stride pr-check コマンド追加" }
  - { date: "2026-02-15", version: "4.4.0-tecnos-stride", note: "AI Autonomous Execution: Claude Code=実行者(R)/人間=承認者(A)モデル、CLAUDE_WORKFLOW全面書き換え、SDD_MANIFESTO/sdd_guidelines (AI auto)/(HITL)ラベル追加" }
  - { date: "2026-03-11", version: "4.6.0-tecnos-stride", note: "Schema-Gated AI Authority: execution_authority宣言（mode_policy.yaml）、Article XIV追加、ED/CFスコア、学術引用（Cook et al. 2026 arXiv:2603.06394）" }
  - { date: "2026-03-16", version: "4.7.0-tecnos-stride", note: "Enterprise Hierarchy CLI Integration: enterprise.yaml, stride epic, stride init --epic, stride lint --enterprise を正式統合" }
  - { date: "2026-04-02", version: "5.0.0-tecnos-stride", note: "CLI UX Maturity: clig.dev準拠CLI改善（カラー出力/NDJSON/TSV/パスtypo/YAML事前検証/アクター追跡/suggested_action表示）、Agent Quick Reference、475テスト" }
  - { date: "2026-04-07", version: "5.1.0-tecnos-stride", note: "Harness Maturity: Mutation Testing（opt-in）、Self-Review Loop、Runtime Sensors（dead code/coverage decay）、Harness Report、Symphony Janitor、agent_docs/harness.md、50新規テスト" }
  - { date: "2026-04-17", version: "5.2.0-tecnos-stride", note: "Opus 4.7 Literal-Follow Tune-up: Governance hardening（Instruction Precedence 10段ヒエラルキー / lint loop bounds max 5 / AI Action Boundary 3分類 / Completeness 4条件数値基準 / Task Completion 固定テンプレート / WI flow 1-16連番化）、stride_shared_lib.py（Canonical YAML抽出共通化、8 self-tests）、stride symphony CLI統合（5 subcmds: run/dispatch/status/validate/janitor）、stride_harness_report Test 6 修正、execution_authority E2E 14 tests、manual2 archive（Option A）、hermetic pytest（pyproject.toml addopts `-m 'not api'` + testpaths 追加）" }
  - { date: "2026-04-19", version: "5.2.1-tecnos-stride", note: "Symphony Agent Reproducibility + SEC-006 Provenance Expansion: (1) SYMPHONY.md の `agent.claude_code` に `model` / `effort_level` / `max_output_tokens` を追加し、ConfigLoader で検証（effort は low/medium/high/xhigh/max のみ）、runner が `--model` / `--effort` / `CLAUDE_CODE_MAX_OUTPUT_TOKENS` env に伝播、4 新規テスト（符号化再現性の明示化）。(2) SEC-006 provenance キーワードを 6 件追加（record_provider_surface / record_model_id / record_execution_settings / record_budget_controls / record_tokenizer_notes / record_cyber_safeguards_status）、stride_security_checker + tecnos_org_constraints + evidence_pack / plan テンプレに反映。(3) `.entire/` gitignore、`evaluator_latest.json` gitignore、manual P2 修正、README test count 同期（562 total / 558 passed default）" }
  - { date: "2026-04-19", version: "5.3.0-tecnos-stride", note: "Linear Integration: linear_bridge.py 新設 — urllib ベース GraphQL クライアント / LinearClient / LinearIssue 等の dataclass / 7 subcommands (init/findings/evidence/learn/sync/close/status) / LINEAR_API_KEY 未設定時 graceful skip / 19 self-tests + 10 integration tests / STRIDE_LINEAR_AUTO=1 で sdd_planning_bridge から自動同期 / state.yaml work_items[].linear_issue_id フィールド追加 / stride linear CLI 統合（bin/stride dispatch）/ manual 37 章新設 / agent_docs/commands.md §12 / CLAUDE_WORKFLOW §8。LINEAR_API_KEY 未設定なら既存フロー完全不変（純粋 opt-in）" }
  - { date: "2026-04-19", version: "5.3.1-tecnos-stride", note: "Per-Project Tracker Isolation: テンプレクローン毎に Linear Project + GitHub Project V2 を専用作成・binding する仕組み。(1) linear_bridge に project create/list/use/status サブコマンド追加（LinearClient.list_projects/find_project_by_name/create_project）、memory/linear.yaml 新設（team_key/project_id/project_name）、解決順位 env > file > none。(2) github_project_bridge.py 新設（gh CLI subprocess、10 self-tests）、stride project create/list/use/status、memory/github_project.yaml 新設。(3) stride-new-project.sh に Step 6/7 として --linear-project/--github-project/--no-* フラグ + 自動作成（認証未設定は graceful skip）。(4) memory/*.yaml.example 2 件 / manual/37 §11 / agent_docs/commands.md §12.Linear Project + §13.GitHub Project V2。未認証環境は完全 graceful skip で既存フロー不変" }
  - { date: "2026-04-22", version: "5.3.2-tecnos-stride", note: "Template Scaffolding Bug Fixes: v5.3.1 テンプレクローン運用で発見した 4 つの bug を修正。(1) `.claude/settings.json` から個人開発者の `entire hooks` 呼び出しを除去し、Phase Gate hook のみの clean state を tracked template に。personal hooks は `.claude/settings.local.json`（gitignored）に退避。(2) stride-new-project.sh Step 4 を `stride hooks --tool claude --force` で常に実行（以前は「既存 settings.json あり」で skip し Phase Gate hook が未 install のまま tracked personal hooks が残るケースを放置していた）。(3) Step 6 GitHub/Linear Project create の `if cmd | sed ; then` pattern を exit code 捕捉に修正（pipe 末尾の sed は常に 0 を返すため stride 失敗時も「bound」と偽陽性表示していた）。(4) Step 6 GitHub Project を `--org` / `GITHUB_OWNER` 未指定時に early skip + 手動 fallback 案内（以前は必ず `owner is required` エラーを出して止まっていた）。version bump のみの小規模 patch で既存機能は不変" }
  - { date: "2026-04-17", version: "5.3.3-tecnos-stride", note: "BPMN Rule Compliance Enforcement: epic_flow.bpmn / process.bpmn がルール通りに作成されない 7 つの根本原因を ultrathink 調査で特定し、AI literal-follow を確実にする構造改善。(1) `agent_docs/sdd_bootstrap.md` に §4-BPMN 新設（Step 1-6 MUST-DO、FEAT/EPIC 決定ツリー、ID スキーム表、14+9 Hard Requirements、top 失敗パターン、lint エラーコード早見表）。(2) `sdd-templates/docs/bpmn_quick_reference.md` 新規作成（1-page、1017行の bpmn_generator_rules.md を補完）、root docs/ にもコピー。(3) `epic_flow_template.bpmn` に `xmlns:xsi` 宣言 + `<bpmn:process isExecutable=\"false\">` 明示。(4) `epic_validator.validate_epic_bpmn` を FEAT と同等レベルに強化（内部 process の incoming/outgoing、sourceRef/targetRef 整合性、BPMNShape/BPMNEdge 完全性）。(5) `stride_lint.validate_bpmn` に sequenceFlow の sourceRef/targetRef 参照整合性チェック追加。(6) `basic_design_template.md` の bpmn_descriptions に ID 完全一致ルール明記。既存機能は不変、BPMN 作成精度のみ向上" }
  - { date: "2026-04-24", version: "5.4.0-tecnos-stride", note: "Reporting Lightening (Profile-Aware): (1) Profile 軸新設 — enterprise-erp (default) / saas-integration / prototype の 3 分類を `basic_design.profile` （canonical schema、`basic_design.*` 配下）と state.yaml top-level profile（flat schema）で宣言。SSoT は basic_design.md 側、state.yaml は同期キャッシュ。`shared/policies/profile_policy.yaml` 新設。(2) Profile-dependent task completion reporting — enterprise-erp=5-step full / saas-integration=critical-only / prototype=1-line。機械検証（stride-lint + pr-check）は全 Profile で同一、Step 1-5 全実行が必須。sdd_bootstrap.md §5 に §5.0 Matrix / §5.1 5-step / §5.2 1-line composition / §5.3 Blocking rule を追加。(3) `stride pr-check --summary-line` — project-level の 1 行サマリ（7 base checks + optional mutation）。task ID / AC / NFR / scenarios は責務境界外。pr_readiness_checker self-tests 10 → 12。(4) Completeness Principle の Profile-aware 閾値 — 200/150/100 行 × 5/4/3 ファイル（AND）。risk_flags 新規追加を Profile 不問の最優先「海」トリガーとして明示。(5) stride_lint に `KNOWN_PROFILES` + `check_profile_consistency()` 追加、新規コード PROFILE_UNKNOWN / PROFILE_MISMATCH / PROFILE_MISSING。(6) `stride init --profile` CLI フラグ追加（default enterprise-erp で既存挙動互換）。init は basic_design.profile（SSoT）と state/state.yaml の top-level profile（キャッシュ）の両方を同時にセット。再実行時は既存 work_items/run_index を保持して profile 行のみ更新。(7) 20 新規テスト `tests/test_profile_policy.py`（policy 構造 / テンプレート schema / CLI --profile 経由で basic_design + state.yaml 両方の伝搬 / 再実行 work_items 保持 / pre-v5.4 state.yaml upgrade / stride-lint PROFILE_* 検出）、manual/38_profile_guide.md。**BPMN / Evidence / SEC-006 / Ops Pack / Epic-Feature Hierarchy / Coverage Tier declaration は全 Profile で現行正本のまま不変**（canonical_source 参照方式）。v5.2 Opus 4.7 hardening、v5.2.1 SEC-006 provenance 拡張、§4-BPMN MUST-DO は 100% 保守" }
  - { date: "2026-04-29", version: "6.0.0-tecnos-stride-value", note: "VALUE Upstream Extension: BACCM Completeness Gate (Article XV) 追加。BABOK v3 BACCM 6 軸の完全性義務化。amendment_ref: memory/constitution_amendments/XV_baccm_completeness.md。" }
  - { date: "2026-04-29", version: "6.0.0-tecnos-stride-value", note: "VALUE Upstream Extension: Layered Requirement Architecture (Article XVI) 追加。4-layer Requirements Architecture (System / Business / BusinessUseCase / Conditions) 構造義務化。amendment_ref: memory/constitution_amendments/XVI_layered_requirement_architecture.md。" }
  - { date: "2026-04-29", version: "6.0.0-tecnos-stride-value", note: "VALUE Upstream Extension: Solution Evaluation Feedback Loop (Article XVII) 追加。BABOK KA8 稼働後評価ループ義務化。amendment_ref: memory/constitution_amendments/XVII_solution_evaluation_loop.md。" }
  - { date: "2026-05-01", version: "6.0.0-tecnos-stride-value", note: "Phase G UX-prep terminology rephrasing: Article XVI の文言を brand-neutral 形式に rephrase (RDRA 3.0 → 4-layer Requirements Architecture、レイヤー名と概念は完全に維持)。Article structure / rules / criteria は不変、固有商標名のみを除去 (concepts only, no proprietary brand names)。BABOK は標準用語のため維持。Tests / behavior 不変。" }
---

# 1. Purpose
- Tecnos Japan における **Specification-Driven Development (SDD)** を実務で破綻させないための「不変原則（Constitution）」を定義する。
- 仕様（Spec）が一次成果物であり、計画（Plan）・タスク（Tasks）・コードは仕様からの生成物である。
- Gate（機械可読）により、生成・実装の進行/停止を**客観基準**で判断できるようにする。
- 例外は例外として**明示**し、憲法（Article）に紐付けて記録する。
- **Coverage Policy**（AC/CT/Code）により、テストの網羅性を3層で管理する。

# 2. Definitions
- **basic_design**: 人間⇄AIの認識齟齬を潰すハブ（HITLで修正可能）
- **process.bpmn**: Camunda 8 (Zeebe 8.8) 前提の業務フロー正本（HITLで承認）
- **Spec**: WHAT/WHY（実装詳細や技術選定は含めない）
- **Plan**: HOW（技術判断・分解・順序。ただしコードは禁止）
- **Tasks**: 実行可能な作業単位（並列性・依存・DoDを明示）
- **Spec-as-Code**: 仕様の機械可読化（OpenAPI/AsyncAPI/権限/移行/テストシナリオ等）
- **Evidence Pack**: ゲート判定の証跡セット（CI/テスト/SAST/SCA/Secrets/AIプロヴェナンス）
- **Artifact Registry**: 成果物の唯一正本リスト（ID/版/必須章/保管先）
- **RACI+**: 人間・AI・CIを含む責任境界の定義（AIはA不可）
- **AI Policy**: 入力データ分類/禁止事項/漏洩対策/ライセンス/監査のルール
- **Tecnos Org Constraints**: Tecnos固有の運用制約（ERP/SCM/CRM統合、監査・運用、AgentOpsガードレール）
  - 参照: `memory/tecnos_org_constraints.md`
  - 本書は不変原則ではないが、Tecnosプロジェクトでは必須参照とする。
- **Coverage Policy**: テストカバレッジの3層管理方針（Plan `coverage_policy` で定義）
  - Layer-1: **Spec Coverage（AC Coverage）** = 全ACがTSでカバーされる（100%必須）
  - Layer-2: **Contract Coverage（CT Coverage）** = 全CTがTS-CONでカバーされる（原則100%）
  - Layer-3: **Code Coverage** = 行/分岐カバレッジ（目標値＋例外管理）

# 3. ID Conventions（唯一の正）
この章の `id_conventions` が唯一の正である。テンプレや他ドキュメントに同様の正規表現が存在しても参照情報であり、規約本体は常に本書から読む。

```yaml
id_conventions:
  # v1.2.6: Extended to support team-prefixed IDs like FEAT-ORD-001
  feature_id: "^FEAT-(?:[A-Z]{2,4}-)?[A-Z0-9]{3,}$"

  requirement_id: "^RQ-[0-9]{3}$"
  decision_id: "^DR-[0-9]{3}$"
  flow_id: "^FLOW-[0-9]{3}$"

  use_case_id: "^US-FEAT[A-Z0-9]{3,}-[0-9]{3}$"
  acceptance_id: "^AC-US-FEAT[A-Z0-9]{3,}-[0-9]{3}-[0-9]{2}$"
  question_id: "^Q-[0-9]{3}$"
  assumption_id: "^A-[0-9]{3}$"

  phase_id: "^Phase-[0-9]+$"
  group_id: "^G-[0-9]{2}-[a-z0-9-]+$"

  component_id: "^CMP-[0-9]{2}$"
  library_id: "^LIB-[0-9]{2}$"

  # Tecnos: ERP/SCM/CRM統合では File/Batch/EDI/IDoc が現実に必要になるため拡張する
  contract_id: "^CT-(API|CLI|EVT|FILE|BATCH|EDI|IDOC|DB)-[0-9]{2}$"
  test_id: "^TS-(CON|INT|E2E|UT)-[0-9]{2}$"

  # v1.2.5: Database schema IDs
  database_schema_id: "^DB-FEAT-[A-Z0-9]{3,}$"

  task_id: "^T-[A-Z0-9]{2,}-[0-9]{3}$"
  milestone_id: "^M-[0-9]{2}$"
  risk_id: "^R-[0-9]{3}$"

  # Camunda 8 (Zeebe) BPMN element IDs（推奨：安定IDでトレーサブルにする）
  bpmn_process_id: "^BPMN-PROC-[A-Z0-9]{3,}$"
  bpmn_element_id: "^BPMN-(TASK|GW|EVT|FLOW)-[0-9]{3}$"

  # Enterprise Extension IDs (v1.2.6: multi-team support)
  epic_id: "^EPIC-[A-Z]{3,}$"
  team_id: "^TEAM-[A-Z]{1,3}$"
  epic_milestone_id: "^EM-[0-9]{2}$"
  integration_point_id: "^IP-[0-9]{3}$"
  dependency_id: "^DEP-[0-9]{3}$"
  shared_contract_id: "^SC-(API|EVT|FILE)-[A-Z0-9]{3,}$"
  feature_breakdown_id: "^FBD-[A-Z0-9]{3,}$"
  ccp_id: "^CCP-[0-9]{3}$"
```

# 4. Fourteen Articles（Principles & Evaluation Criteria）
> 各 Article は「Rules（守ること）」と「Criteria（評価基準）」で構成する。
> 例示は理解補助であり規範ではない。

```yaml
articles:
  - id: "I"
    name: "Library-First"
    summary: "すべての機能はライブラリ境界から始める"
    rules:
      - "ビジネスロジックはライブラリ境界に集約する"
      - "UI/アプリ層はオーケストレーションに留める"
    criteria:
      - "主要概念が library/component と対応している"
      - "責務境界がPlanで明示されている"

  - id: "II"
    name: "Contract/CLI-First"
    summary: "契約（API/CLI/EVT/FILE/BATCH/EDI/IDOC）を実装より先に定義する"
    rules:
      - "契約は contracts/ に置く"
      - "CLI は text-in/text-out を基本とし JSON をサポートする"
      - "FILE/BATCH/EDI/IDOC も契約として入出力・再実行性・監査観点を明文化する"
      - "全CTはTS-CON（契約テスト）でカバーされる（Coverage Policy Layer-2）"
    criteria:
      - "CT-* がPlanに列挙され、Tasksに落ちている"
      - "契約テスト（TS-CON-*）が存在し、全CTをカバーしている"

  - id: "III"
    name: "Test-First"
    summary: "テストを仕様の一部として先に定義する"
    rules:
      - "契約テスト → 統合テスト → E2E → ユニットの順に優先する"
      - "Acceptance Criteria はテストへトレースされる（Coverage Policy Layer-1）"
      - "integrationタグ付きACはTS-INTでカバーされる"
      - "e2eタグ付きACはTS-E2Eでカバーされる"
    criteria:
      - "AC-* が TS-* でカバーされている（100%）"
      - "integration タグ付きACが統合テストで優先されている"
      - "e2e タグ付きACがE2Eテストでカバーされている"

  - id: "IV"
    name: "Documentation-First"
    summary: "仕様・計画・タスクの更新が実装変更に先行する"
    rules:
      - "コードは一次成果物ではない（仕様が先）"
    criteria:
      - "Spec/Plan/Tasks の Gate が通っている"

  - id: "V"
    name: "Modularity"
    summary: "境界を明確にし、変更影響を局所化する（ERP境界を破らない）"
    rules:
      - "境界を越えるのは契約のみ"
      - "ERP本体DB直結などの境界破りは原則禁止（例外は記録）"
    criteria:
      - "責務境界・契約・依存がPlanに明示されている"

  - id: "VI"
    name: "Automation"
    summary: "生成・検証・反復を自動化する"
    rules:
      - "counts はCIが算出し、差分があれば失敗させる"
      - "lintにより形骸化を防ぐ"
      - "Coverage Policyに基づくテスト網羅性をCIで検証する"
      - "Evidence Pack（CI/テスト/SAST/SCA/Secrets/AIプロヴェナンス）を残す"
    criteria:
      - "stride-lint が通る"
      - "derived_fields.counts_are_computed が true"
      - "Tagged AC Coverage / Contract Coverage が pass"
      - "Evidence Pack の証跡が揃っている"

  - id: "VII"
    name: "Simplicity"
    summary: "最小構成から始め、必要性が証明されるまで増やさない"
    rules:
      - "初期は ≤3 project を原則（例外は記録）"
      - "future-proofing を禁止"
      - "E2Eは重要ユーザージャーニー（e2eタグ付きAC）に限定する"
    criteria:
      - "例外が DR/Exceptions に記録されている"

  - id: "VIII"
    name: "Anti-Abstraction"
    summary: "フレームワークを信頼し、不要な抽象化を作らない"
    rules:
      - "薄いラッパーや重複モデルを禁止"
    criteria:
      - "単一表現（Single Source of Model）が守られている"

  - id: "IX"
    name: "Integration-First"
    summary: "実環境に近い統合テストを優先する（ERP/外部連携前提）"
    rules:
      - "契約を先に固め、統合テストで回帰を担保する"
      - "E2Eは「統合クリティカルフロー／Mustのユーザージャーニー」に限定したスモーク＋回帰として運用する"
    criteria:
      - "integration タグACが統合テストでカバーされている"
      - "e2e タグACがE2Eテストでカバーされている"

  # Enterprise Extension Articles (v2.0.0)
  - id: "X"
    name: "Epic-Feature Hierarchy"
    summary: "大規模機能はEpic/Feature階層で分解し、チーム間依存を明示化する"
    rules:
      - "2チーム以上にまたがる機能はEpicを定義する"
      - "各FeatureはただひとつのチームにOwnershipがある"
      - "チーム間依存は明示的にマッピングし、循環依存を禁止する"
      - "Epicレベルの共有契約は shared/ に定義する"
    criteria:
      - "Epic-Featureのトレーサビリティが完備している"
      - "dependency_map に循環がない"
      - "全FeatureにTeam IDが割り当てられている"

  - id: "XI"
    name: "Shared Contract Governance"
    summary: "共有契約は明確なオーナーシップと消費者合意を持つ"
    rules:
      - "共有契約には唯一のオーナーチームがある"
      - "Breaking Changeには消費者への通知と承認が必要（CCP）"
      - "契約テストはProvider側が責任を持つ"
      - "消費者は明示的に登録し、変更通知を受け取る"
    criteria:
      - "全共有契約に消費者リストがある"
      - "クリティカル契約にはCDCテストがある"
      - "Breaking ChangeにはCCPが作成されている"

  - id: "XII"
    name: "Tiered Coverage"
    summary: "カバレッジ要件はFeatureの重要度に応じて階層化する"
    rules:
      - "Critical: AC 100%, CT 100%, Code 85%/75%, E2E必須"
      - "Standard: AC 100%, CT 80%, Code 70%/60%, E2E任意"
      - "Experimental: AC 80%, CT 60%, Code 50%/40%, E2E不要"
      - "Tierはbasic_designで宣言し、planのcoverage_policyで検証する"
    criteria:
      - "coverage_tierがbasic_designで定義されている"
      - "coverage_policyがtier要件を満たしている"
      - "承認者がtierに応じて適切に割り当てられている"

  # STRIDE Multi-Team Articles (v3.0.0)
  - id: "XIII"
    name: "PM Progress Visibility"
    summary: "PMはEpic横断でチーム進捗・ブロッカー・リスクを一元的に把握できなければならない"
    rules:
      - "Epic配下の全FeatureのGate進捗はEPIC_PROGRESS_REPORTで集約する"
      - "チーム間依存はCROSS_TEAM_DEPENDENCY_MANIFESTで明示し、statusを追跡する"
      - "ブロッカーは24h以内にBLOCKER_REGISTRYに登録し、PM/Epic Leadに可視化する"
      - "Ops Packの準備状況はOPS_PACK_REGISTRYで一元管理する"
      - "共有契約はSHARED_CONTRACT_REGISTRYで消費者・バージョン・ステータスを追跡する"
      - "各チームは週次でTEAM_STATUS_REPORTを更新する"
    criteria:
      - "PMが週次でEpic全体の健全性を確認できる"
      - "クリティカルブロッカーが24h以内に可視化される"
      - "チーム間依存のステータスが最新である"
      - "Ops Packの準備率がダッシュボードで確認できる"
      - "共有契約の消費者採用状況が追跡されている"

  # Schema-Gated AI Authority (v4.6.0)
  # Reference: Cook et al. (2026) arXiv:2603.06394
  - id: "XIV"
    name: "Execution Authority Separation"
    summary: "AIの会話権限と実行権限を分離し、実行はスキーマ検証済みインターフェースを通じてのみ許可する"
    rules:
      - "AIの権限スコープは shared/policies/mode_policy.yaml の execution_authority で宣言する"
      - "conversational 行為（解釈・提案・lint修正）は承認不要で自律実行可能"
      - "gated 行為（成果物作成・WI着手・PR作成）はスキーマ検証（stride-lint/phase_gate/wi_readiness_checker）通過が前提"
      - "prohibited 行為（APPROVAL.md編集・Gate skip・ERP直接操作）はAIに実行権限がない"
      - "autopilot/confirm/validate の3モードは検証スコープの段階（ツールレベル→ワークフローレベル→ドメインレベル）に対応する"
    criteria:
      - "mode_policy.yaml に execution_authority セクションが定義されている"
      - "全ての gated 行為が対応するスキーマ検証ツールを持つ"
      - "wi_readiness_checker の Check 8 が execution_authority 宣言時に検証スコープの整合性を検出する"
      - "prohibited 行為の防止は既存の仕組み（APPROVAL.md編集禁止=stride-lint、Phase Gate skip=phase_gate.py、ERP直接操作=tecnos_org_constraints.md）で担保されている"

  # VALUE Upstream Extension Articles (v6.0.0-tecnos-stride-value, Phase C, FEAT-VALC01)
  # Reference: BABOK v3 (IIBA) — fair-use names only.
  # 4-layer Requirements Architecture (System / Business / BusinessUseCase / Conditions) 構造概念を採用 (concepts only, no proprietary brand names).
  # Phase G UX-prep (2026-05-01) で固有商標名を除去、レイヤー名と階層概念は完全に維持。
  - id: "XV"
    name: "BACCM Completeness Gate"
    summary: "Phase 0 Discovery 完了時に BACCM 6 軸 (change/need/solution/stakeholder/value/context) の完全性を機械検証する"
    rules:
      - "BACCM 6 軸ごとに source_artifact の required_keys が充足していること"
      - "Gate 0 通過には全 6 軸が PASS であること (partial_credit_allowed: false)"
      - "stakeholder_map.yaml の stakeholders は最小 3 件"
    criteria:
      - "shared/policies/baccm_completeness.yaml の 6 軸全て pass"
      - "stride upstream validate (stride lint --upstream) がエラーなし"
      - "completeness_scoring.threshold_for_gate_0 = 100 を満たす"

  - id: "XVI"
    name: "Layered Requirement Architecture (4-layer aligned)"
    summary: "Phase 0.5 Context Modelling は 4-layer Requirements Architecture (System / Business / BusinessUseCase / Conditions) で組み立て、レイヤー間参照リンクの整合を保つ"
    rules:
      - "actor_system / business_usecase / information_state / condition_variation / usecase_complex / requirements_architecture を生成する"
      - "requirements_architecture.yaml のレイヤー間リンクが broken でない"
      - "iteration 3 (refinement) までで context modelling を確定する"
    criteria:
      - "BROKEN_LAYER_LINK エラー (4-layer requirements architecture cross_layer_links 整合性検証) が stride lint --upstream で検出されない"
      - "shared/policies/upstream_iteration_policy.yaml の max_iterations=3 を満たす"

  - id: "XVII"
    name: "Solution Evaluation Feedback Loop (BABOK KA8)"
    summary: "稼働後ソリューション評価で目標 KPI 実績差分を測定し、次 iteration への学びを記録する"
    rules:
      - "business_need.yaml の success_criteria を KPI として宣言する"
      - "稼働後 stride retro --solution-eval で KPI 実績 / Adoption / Issues を集計する"
      - "評価結果は specs/<feature>/state/solution_eval_<ts>.md として記録する"
    criteria:
      - "stride retro --solution-eval が PASS / FAIL / ERROR の exit code を返す"
      - "solution_eval_*.md に kpi_targets / kpi_actuals / kpi_gaps が記録されている"
      - "Issues 件数が specs/<feature>/runs/*/lessons.md から集計されている"
```

# 4.1 escalation_triggers

以下に該当するタスクは `acceptance_criteria[].escalation_trigger: true` を設定し、
実装完了後に人間レビューを必須とする。

| # | 条件 | 理由 |
|---|------|------|
| 1 | 認証・認可ロジックの変更 | セキュリティ侵害リスク |
| 2 | DBスキーマのマイグレーション（既存データに影響） | データ消失・整合性破損リスク |
| 3 | 新規外部依存の追加（npm/pypi/Docker） | サプライチェーン攻撃リスク |
| 4 | 支払・金銭処理に関わるロジック | 金銭的損失リスク |
| 5 | セキュリティ設定の変更 | 攻撃面拡大リスク |

`escalation_trigger: true` のタスクはSDD Gate 5（Tasks Gate）で自動的にHITLレビューを要求する。

# 5. Gates（Enforcement）
> Gateは「counts/rules/boolean」を持つ。
> booleanのみでの通過を禁止し、最低限の客観条件基準を rules で定義する。

```yaml
gates:
  - name: "Basic Design Gate"
    artifact: "basic_design"
    requires:
      - "basic_design_gate_check.traceability_present == true"
      - "basic_design_gate_check.integration_flows_identified == true"
      - "basic_design_gate_check.exceptions_documented == true"
      - "basic_design_gate_check.counts.traceability_rows >= basic_design_gate_check.rules.min_traceability_rows"
      - "basic_design_gate_check.counts.integration_flows >= basic_design_gate_check.rules.min_integration_flows"
      - "basic_design_gate_check.counts.blocking_questions <= basic_design_gate_check.rules.max_blocking_questions"
      - "basic_design_gate_check.delivery_model_defined == true"
      - "basic_design_gate_check.raci_plus_defined == true"
      - "basic_design_gate_check.ai_policy_defined == true"
      - "basic_design_gate_check.artifact_registry_defined == true"
      - "basic_design_gate_check.ready_for_bpmn == true"

  # Tecnos: BPMN承認を「下流生成の前提」として客観化（HITL承認が前提）
  - name: "BPMN Approval Gate"
    artifact: "basic_design"
    requires:
      - "basic_design_gate_check.process_bpmn_linked == true"
      - "basic_design_gate_check.process_bpmn_approved == true"
      - "basic_design_gate_check.ready_for_specify == true"

  - name: "Spec Gate"
    artifact: "spec"
    requires:
      - "spec_gate_check.no_blocking_open_questions == true"
      - "spec_gate_check.counts.use_cases >= spec_gate_check.rules.min_use_cases"
      - "spec_gate_check.counts.acceptance_criteria >= spec_gate_check.rules.min_total_acceptance_criteria"
      - "spec_gate_check.counts.integration_tagged_ac >= spec_gate_check.rules.min_integration_acceptance_criteria"
      - "spec_gate_check.counts.blocking_questions <= spec_gate_check.rules.max_blocking_questions"
      - "spec_gate_check.counts.nfr_items >= spec_gate_check.rules.min_nfr_items"
      - "spec_gate_check.counts.security_items >= spec_gate_check.rules.min_security_items"
      - "spec_gate_check.counts.integration_items >= spec_gate_check.rules.min_integration_items"
      - "spec_gate_check.counts.data_items >= spec_gate_check.rules.min_data_items"
      - "spec_gate_check.counts.spec_as_code_artifacts >= spec_gate_check.rules.min_spec_as_code_artifacts"
      - "spec_gate_check.spec_as_code_defined == true"
      - "spec_gate_check.ai_plan_ready == true"

  - name: "Plan Gate"
    artifact: "plan"
    requires:
      - "plan_gate_check.contracts_defined == true"
      - "plan_gate_check.tests_prioritized == true"
      - "plan_gate_check.integration_first_gate_passed == true"
      - "plan_gate_check.counts.in_use_cases >= plan_gate_check.rules.min_in_use_cases"
      - "plan_gate_check.counts.libraries >= plan_gate_check.rules.min_libraries"
      - "plan_gate_check.counts.contracts >= plan_gate_check.rules.min_contracts"
      - "plan_gate_check.counts.tests >= plan_gate_check.rules.min_tests"
      - "plan_gate_check.counts.integration_tests >= plan_gate_check.rules.min_integration_tests"
      - "plan_gate_check.counts.groups >= plan_gate_check.rules.min_groups"
      - "plan_gate_check.evidence_pack_defined == true"
      - "plan_gate_check.ai_tasks_ready == true"

  - name: "Tasks Gate"
    artifact: "tasks"
    requires:
      - "tasks_gate_check.no_dependency_errors == true"
      - "tasks_gate_check.counts.tasks >= tasks_gate_check.rules.min_tasks"
      - "tasks_gate_check.counts.use_cases_referenced >= tasks_gate_check.rules.min_use_cases_referenced"
      - "tasks_gate_check.counts.acceptance_referenced >= tasks_gate_check.rules.min_acceptance_referenced"
      - "tasks_gate_check.counts.tasks_with_plan_refs == tasks_gate_check.counts.tasks"
      - "tasks_gate_check.tasks_ready_for_code == true"

  # Enterprise Extension Gates (v1.2.6)
  - name: "Epic Design Gate"
    artifact: "epic_design"
    requires:
      - "epic_gate_check.all_features_have_team == true"
      - "epic_gate_check.all_dependencies_mapped == true"
      - "epic_gate_check.shared_contracts_defined == true"
      - "epic_gate_check.no_dependency_cycles == true"
      - "epic_gate_check.counts.total_features >= epic_gate_check.rules.min_features"
      - "epic_gate_check.ready_for_feature_specs == true"

  - name: "Feature Breakdown Gate"
    artifact: "feature_breakdown"
    requires:
      - "breakdown_gate_check.no_dependency_cycles == true"
      - "breakdown_gate_check.all_integration_points_defined == true"
      - "breakdown_gate_check.coverage_tiers_assigned == true"
      - "breakdown_gate_check.ready_for_feature_specs == true"

  - name: "Shared Contract Gate"
    artifact: "shared_contract"
    requires:
      - "shared_contract_gate_check.owner_defined == true"
      - "shared_contract_gate_check.consumers_notified == true"
      - "shared_contract_gate_check.contract_tests_defined == true"

  # STRIDE Multi-Team Gates (v3.0.0)
  - name: "Epic Progress Gate"
    artifact: "epic_progress_report"
    requires:
      - "progress_gate_check.all_features_have_team_status == true"
      - "progress_gate_check.dependency_manifest_current == true"
      - "progress_gate_check.no_critical_blockers_unresolved == true"
      - "progress_gate_check.shared_contract_registry_defined == true"
      - "progress_gate_check.ops_pack_registry_defined == true"
      - "progress_gate_check.counts.teams_reporting >= progress_gate_check.rules.min_teams_reporting"
```

# 6. Implementation Notes（テンプレ依存：変動しやすいので隔離）
- 推奨フロー：
  1) 人間の任意テキスト → `basic_design.md`（HITLで修正/承認）
  2) `Basic Design Gate` pass → `process.bpmn` を作成・HITL承認（Camunda 8 / DI必須）
  3) `BPMN Approval Gate` pass → `spec/plan/tasks` を生成
  4) `Spec-as-Code` と `Evidence Pack` を埋め、AI/HITLの証跡を固定する
  4) `stride-lint` で Gate を機械評価し、差し戻し/進行を決める

- 推奨：Spec/Plan/Tasks は Canonical YAML を AI の正本とする（人間向け文章は補助）。
- 推奨：Planの主要要素（component/library/contract/test/phase/group）は stable id を付与し、Tasks は stable id 参照のみを使う。
- 推奨：例外は必ず `{article, reason, mitigation}` の3点セットで記録する（例外が無いなら空配列）。
- 必須：Tecnosの統合・監査・運用要件は `memory/tecnos_org_constraints.md` を参照し、basic_design/spec/plan/tasks に反映する。
- 必須：Coverage Policy（AC/CT/Code）を Plan に定義し、stride-lint で検証する。

# 7. Amendment Process
- 変更理由・影響範囲・Owners承認・SemVer更新・last_reviewed_at 記録を必須とする。
- 改訂は小さく、テンプレ参照の密結合を避ける。

> End of constitution.md
