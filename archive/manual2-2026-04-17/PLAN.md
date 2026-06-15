# manual2 構成計画 — Tecnos-STRIDE マニュアル完全リニューアル

> 作成日: 2026-04-02
> ステータス: 構成案（アウトライン確定後に執筆開始）

---

## 設計原則

1. **読者別の入口** — PM / 設計者 / 実行者(AI+人間) の3ペルソナを意識
2. **4類型分離（Diataxis）** — Tutorial / Explanation / How-to / Reference を混ぜない
3. **1ファイル1責務** — 各ファイルに `In scope / Out of scope` を明示し、複数ペルソナの混在を防ぐ
4. **ファイル数半減** — 旧44本 → 新21本（Docsify設定ファイルは除く）
5. **ツールリファレンスは集約** — 散在していた CLI / quality gate / 補助ツール情報をリファレンスに統合
6. **正本を明確化** — `manual2/` は人間向け説明、`agent_docs/commands.md` はコマンド正本、`sdd-templates/docs/` は深掘り技術資料

---

## ディレクトリ構成

```
manual2/
├── index.md                           # トップページ
├── 01_quickstart.md                   # クイックスタート（全読者共通）
│
├── concepts/                          # 【概念編】なぜ・何を
│   ├── 02_sdd_fundamentals.md         #   SDD の基本思想
│   ├── 03_phase_gates.md              #   Phase Gate モデル
│   ├── 04_ai_execution_model.md       #   AI 自律実行モデル
│   └── 05_enterprise_scale.md         #   Enterprise 拡張
│
├── guides/                            # 【実践ガイド】どうやる
│   ├── 06_pm_guide.md                 #   PM 操作ガイド
│   ├── 07_design_phase.md             #   Phase 1: 設計
│   ├── 08_specify_phase.md            #   Phase 2: 仕様策定
│   ├── 09_execute_phase.md            #   Phase 3-5: 実行
│   ├── 10_testing.md                  #   テスト設計・テスト成果物
│   ├── 11_quality_gates.md            #   quality gate / CI / evaluator / security
│   └── 12_migration.md                #   既存フォーマットからの移行
│
├── reference/                         # 【リファレンス】調べる
│   ├── 13_cli_reference.md            #   stride CLI 全コマンド
│   ├── 14_artifact_reference.md       #   成果物テンプレート
│   ├── 15_id_conventions.md           #   ID 規約
│   └── 16_fourteen_articles.md        #   14原則
│
├── appendix/                          # 【付録】
│   ├── 17_troubleshooting.md          #   トラブルシューティング
│   ├── 18_changelog.md                #   バージョン履歴
│   ├── 19_tutorial_web_edi.md         #   Web-EDI チュートリアル
│   └── 20_erp_addon_playbook.md       #   ERP Addon 実務プレイブック
│
├── _sidebar.md
├── _coverpage.md
├── _navbar.md
├── index.html
└── 404.html
```

---

## 旧マニュアルからの対応表

| 新ファイル | 旧ファイル（統合元） | 統合の考え方 |
|-----------|---------------------|-------------|
| `index.md` | 旧index.md（ナビ部分のみ） | 1ページ概要 + 読者別ナビ。旧1,503行→200行以下 |
| `01_quickstart.md` | 00_pm_quickstart | PMだけでなく全読者の入口に拡張 |
| `02_sdd_fundamentals.md` | 01_getting_started + index.md（概念部分） | SDD思想・トレーサビリティ・契約の概念を1本に |
| `03_phase_gates.md` | index.md（Gate部分）+ 19_coverage_policy | 6ゲート + Lite 3ゲート + カバレッジTier |
| `04_ai_execution_model.md` | 15 + 16 + 17 + 18 | AI自律実行・RACI+・Adaptive・Governance統合 |
| `05_enterprise_scale.md` | 04 + 24 + 28 | Epic/Feature + マルチチーム + TEIM統合 |
| `06_pm_guide.md` | 05 + 25 + 26 | PM操作 + ダッシュボード + GitHub Projects |
| `07_design_phase.md` | 09 + 10 | basic_design + BPMN（Phase 1の全成果物） |
| `08_specify_phase.md` | 11 + 12 | spec + plan + contracts（Phase 2の全成果物） |
| `09_execute_phase.md` | 13 + 14 + 07（実行部分） | tasks + WI/Run + evidence_pack（Phase 3-5） |
| `10_testing.md` | 20 + 29 + 33 | テスト設計・testreport・integration test を統合 |
| `11_quality_gates.md` | 21 + 22 + 34 + 35 | drift / evaluator / security / retro / CI quality gate を統合 |
| `12_migration.md` | 02 + 03 | テクノス/mcframe移行を統合 |
| `13_cli_reference.md` | appendix_b + 18 + 23 + 30 + 31 + 32 | stride CLI + 補助ツールを集約 |
| `14_artifact_reference.md` | index.md（成果物部分）+ 各ガイドのフィールド表 | 辞書的に引ける全フィールド解説 |
| `15_id_conventions.md` | appendix_a | そのまま移行 |
| `16_fourteen_articles.md` | appendix_c | そのまま移行 |
| `17_troubleshooting.md` | appendix_d | そのまま移行 + 各ガイドのFAQ統合 |
| `18_changelog.md` | index.md（バージョン表） | バージョン履歴を独立ファイル化 |
| `19_tutorial_web_edi.md` | 08 | 学習用チュートリアルとして再構成 |
| `20_erp_addon_playbook.md` | 27 | ERP Addon 実務運用ガイドを独立保持 |

### 廃止する旧ファイル（内容は他に吸収済み）

| 旧ファイル | 吸収先 |
|-----------|--------|
| 06_upstream_phase_guide.md | 07, 08, 09 に分散吸収 |
| 23_turborepo_monorepo.md | 13_cli_reference（`stride init --scale`） |
| index.md（1,503行） | 分解して各ファイルに配置 |

---

## manual外ドキュメントの扱い（SSoTルール）

| パス | 役割 | 新方針 |
|------|------|--------|
| `agent_docs/commands.md` | コマンド構文の正本 | **維持**。`manual2/reference/13_cli_reference.md` は人間向け要約とし、構文差異が出た場合はこちらを優先 |
| `sdd-templates/docs/CI_CD_INTEGRATION.md` | CI/CD 深掘り技術資料 | **維持**。`manual2/guides/11_quality_gates.md` からリンクし、ベンダー別YAMLは重複掲載しない |
| `sdd-templates/docs/wi-management-guide.md` | WI/Run 運用の補助資料 | **維持**。`manual2/guides/09_execute_phase.md` には基本概念だけ載せ、詳細はリンク |
| `docs/camunda_bpmn_practice_guide.md` | BPMN 高度実践 | **維持**。`manual2/guides/07_design_phase.md` からリンク |
| `manual/` 既存各ファイル | 移行元 | **凍結**。`manual2/` 完成までは参照元として保持し、切替後に archive または stub 化 |

### 正本ルール

- `manual2/` は **人間向けの入口・説明・運用導線** を担う
- `agent_docs/commands.md` は **CLI コマンドと実行例の正本** を担う
- `sdd-templates/docs/` は **実装者向けの深掘り技術資料** として残す
- 同じ情報を2か所に詳細重複させない。`manual2/` は概要と判断基準、外部 docs は詳細手順に寄せる

---

## 責務境界（In scope / Out of scope の基準）

| ファイル | In scope | Out of scope |
|---------|----------|--------------|
| `01_quickstart.md` | 10分で全体像を掴む入口、最短導線 | 全フィールド解説、全CLI網羅、詳細運用ルール |
| `07_design_phase.md` | basic_design / BPMN / Gate 1-2 の実務 | BPMN仕様の深掘り、Camunda高度テクニック |
| `08_specify_phase.md` | spec / plan / contracts の作り方 | 各契約形式の詳細仕様書、CI連携の実装詳細 |
| `09_execute_phase.md` | tasks / WI / Run / evidence の運用 | PR品質ゲートの詳細仕様、CIベンダー別設定 |
| `10_testing.md` | テスト戦略、testreport、integration test の設計 | security audit、retro、drift、evaluator の詳細 |
| `11_quality_gates.md` | stride evaluate / security / retro / PR Readiness / CI quality gate | 各テスト技法の詳細、全CLIオプション辞書 |
| `13_cli_reference.md` | コマンドの一覧、用途、主要オプション、実行例 | 長い背景説明、各成果物の書き方 |
| `14_artifact_reference.md` | 各成果物の辞書的参照 | フェーズ別の手順、導入ストーリー |
| `19_tutorial_web_edi.md` | 学習用の一気通貫チュートリアル | ERP運用ルールの総覧、社内標準手順書 |
| `20_erp_addon_playbook.md` | ERP Addon 実務の注意点と運用標準 | 初学者向けの導入チュートリアル |

### 運用ルール

- 各ファイル冒頭に `対象 / 所要時間 / 前提 / In scope / Out of scope` を書く
- `Out of scope` に入る内容は、該当する別ファイルか外部 deep-dive docs へリンクする
- 1ファイルが 800 行を超えそうなら、統合ではなく再分割を優先する

---

## 各ファイルの詳細アウトライン

---

### index.md — トップページ（目標: 200行以下）

```
# Tecnos-STRIDE マニュアル
  ## このマニュアルについて
    - 一文サマリー: 「仕様が契約。AIが実行。人間が承認。」
    - 対象読者（PM / 設計者 / 実行者）
  ## 読者別ガイド
    - PM → 01_quickstart → 06_pm_guide
    - 設計者 → 01_quickstart → 07/08/09
    - 開発者/AI → 01_quickstart → 13_cli_reference
  ## マニュアル構成図（視覚的なマップ）
  ## バージョン
    - 現在のバージョン + 18_changelog へのリンク
```

---

### 01_quickstart.md — クイックスタート（目標: 300行）

```
# クイックスタート（10分）
  ## 30秒で理解する Tecnos-STRIDE
    - 「要件を伝える → AI実行 → 承認 → 完成」の図
  ## 全体フロー（6ステップ図）
    - Phase 1〜Final の一気通貫図 + 各Gateの承認ポイント
  ## Step 1: プロジェクトを作る
    - `stride new-project` のコマンド例
  ## Step 2: 最初の機能を作る
    - 自然言語で要件を伝える → AI自律実行の流れ
  ## Step 3: 承認する
    - APPROVAL.md のチェックボックス操作
    - 工程別の確認ポイント表（基本設計/仕様/計画/タスク/最終）
  ## Step 4: PRを作成する
    - `stride pr-check` → PR作成
  ## 次に読むべきもの
    - PM → 06_pm_guide
    - 設計の詳細 → 07_design_phase
    - CLIコマンド → 13_cli_reference
```

---

### concepts/02_sdd_fundamentals.md — SDDの基本思想（目標: 600行）

```
# SDD の基本思想
  ## なぜ仕様駆動なのか
    - 従来の問題（認識ズレ・手戻り・証跡不足）
    - SDD の答え: 仕様が唯一の正本（SSoT）
  ## 5つの成果物と役割
    - basic_design / spec / plan / tasks / evidence_pack の一文説明
    - トレーサビリティの流れ図（要望→仕様→設計→コード→テスト→証跡）
  ## 「契約（Contract）」とは何か
    - SDDにおける契約の意味（法的契約との比較）
    - 契約の種類一覧（API/CLI/EVT/FILE/BATCH/EDI/IDoc）
    - Contract-First のメリット（認識ズレ防止）
  ## テンプレート連携の全体像
    - 5つのテンプレートがIDで紐付く構造図
    - 各成果物のインプット/アウトプット関係
  ## 用語集
    - 主要20語の一文定義
```

---

### concepts/03_phase_gates.md — Phase Gateモデル（目標: 500行）

```
# Phase Gate モデル
  ## Gate とは何か
    - 「次へ進んでよいか」の判定ポイント
    - 人間のみが承認する理由
  ## Full Mode（6ゲート）
    - Gate 1: Basic Design → Gate 2: BPMN → ... → Final
    - 各ゲートの確認項目と承認者
    - APPROVAL.md の構造
  ## Lite Mode（3ゲート）
    - Gate A/B/C の対応関係
    - いつ Lite Mode を使うか（PoC・小規模・単独開発者）
  ## カバレッジ Tier
    - critical / standard / starter の3段階
    - Tier別の必須テスト・証跡・承認要件
    - Tier Mismatch WARN の仕組み
  ## Post-Approval Change 制御
    - 承認済みファイルの変更検知
    - Amendment Fast Track（低リスク変更の承認簡略化）
  ## Phase Gate × AI
    - Phase Gate hooks（Claude Code / Cursor / Copilot / manual）
    - stride phase-check による自動ブロック
```

---

### concepts/04_ai_execution_model.md — AI自律実行モデル（目標: 500行）

```
# AI 自律実行モデル
  ## 基本原則: AI=実行者、人間=承認者
    - RACI+ での役割定義（R=AI, A=人間, C/I）
    - APPROVAL.md は人間のみ編集
  ## RACI+ 責務分担
    - 役割一覧表（PM/Tech Lead/AI/QA）
    - 責務マトリクス（Phase × 役割）
  ## Adaptive Execution（適応的実行）
    - Mode: autopilot / confirm / validate
    - Autonomy Bias: プロジェクトの自律性嗜好
    - risk_flags に応じた Mode 自動判定
  ## Execution Authority（3層権限）
    - conversational / gated / prohibited
    - mode_policy.yaml の構造
  ## Execution Governance
    - Auto-Continue の仕組み
    - Mandatory Output Rules
    - DDD（任意）/ ADR Index
  ## Completeness Principle
    - 「だいたい動く」で止めない思想（Boil the Lake）
```

---

### concepts/05_enterprise_scale.md — Enterprise拡張（目標: 600行）

```
# Enterprise 拡張
  ## いつ Enterprise が必要か
    - 3チーム以上 / Epic跨ぎ / 共有契約あり → Enterprise
  ## Epic / Feature 階層
    - Epic = 大規模要件、Feature = 実装単位
    - epic_design.md / feature_breakdown.md / EPIC_APPROVAL.md
    - Epic Gate ワークフロー（E1/E2/E3/E4）
  ## マルチチーム運用
    - チーム間依存管理（DEPENDENCY_MANIFEST.yaml）
    - 共有契約レイヤー（CONTRACT_REGISTRY.yaml）
    - 契約変更提案（CCP）ワークフロー
  ## 委任承認マトリクス
    - Tier × Gate種別 → 承認者の自動ルーティング
  ## TEIM/PMO マッピング
    - Tecnos Enterprise Implementation Methodology との対応
    - Phase Gate → TEIM フェーズ対照表
  ## Enterprise CLI
    - `stride epic init/validate/gates/features/progress/list`
    - `stride init <feature> --epic <id> --team <id>`
    - `stride lint --all --enterprise`
```

---

### guides/06_pm_guide.md — PM操作ガイド（目標: 600行）

```
# PM 操作ガイド
  ## PMの役割サマリー
    - 「承認・監視・意思決定」の3つ
  ## PMの1日（シナリオ形式）
    - 朝: ダッシュボード確認
    - 日中: Gate承認・リスク対応
    - 夕: 進捗レビュー
  ## 承認操作
    - APPROVAL.md の編集手順
    - 確認すべきポイント（Gate別チェックリスト）
    - Epic 承認（EPIC_APPROVAL.md）
  ## ダッシュボード
    - PM_DASHBOARD.md の読み方
    - Gate Completion Matrix / Team Status / Milestone Tracking
    - HTMLビジュアルダッシュボード（6パネル）
    - プロセスメトリクス（Gate別滞留時間分析）
  ## GitHub Projects 連携
    - セットアップ手順
    - Forward Sync（ファイル→Projects）/ Reverse Sync
    - Projects の活用パターン
  ## 実施担当者との連携ポイント
    - 承認依頼の標準形式
    - エスカレーション基準
  ## PM向けチェックリスト
    - 導入時 / 日常 / Gate判定時
```

---

### guides/07_design_phase.md — Phase 1: 設計（目標: 700行）

```
# Phase 1: 設計
  ## このフェーズで作るもの
    - basic_design.md + process.bpmn + APPROVAL.md
  ## Intake-First アプローチ（推奨）
    - `stride intake <feature>` → 質問形式で要件整理 → AI生成
    - 所要時間: 10-15分
  ## basic_design.md の書き方
    - Canonical YAML の構造
    - 主要フィールド解説（feature/scope/requirements/constraints/integration_flows）
    - delivery_model の選び方（fit_to_standard / requirement_driven）
    - Brownfield Detection（`--detect`）
  ## BPMN の作成
    - Feature BPMN（process.bpmn）— 単一Feature実装フロー
      - Camunda 8.8 形式 / laneSet / executable process
      - bpmn_descriptions との連動
    - Epic BPMN（epic_flow.bpmn）— チーム間概観
      - collaboration + participant(pool) 形式
    - YAML ↔ BPMN 双方向 ID 照合
  ## Gate 1, 2 の承認
    - 確認ポイント
    - stride lint で事前チェック
  ## よくあるエラーと対処
    - MISSING_FILE / BPMN_VALIDATION_FAILED / PLACEHOLDER_VALUE_PRESENT
```

---

### guides/08_specify_phase.md — Phase 2: 仕様策定（目標: 700行）

```
# Phase 2: 仕様策定
  ## このフェーズで作るもの
    - spec.md + plan.md + contracts/*
  ## spec.md の書き方
    - Canonical YAML 構造
    - ユースケース（US-*）の定義
    - 受入条件（AC-*）の書き方（Given-When-Then）
    - セキュリティ要件（security_sensitive / sod_relevant）
    - spec_as_code（OpenAPI / JSON Schema / DB Schema）
  ## plan.md の書き方
    - テスト戦略（test_strategy）
    - テストエントリとカバレッジ（covers_acceptance_ids / covers_contract_ids）
    - リスク管理（risks / mitigations）
    - 依存関係（dependencies）
  ## 契約（Contracts）の定義
    - contracts/ ディレクトリの構造
    - OpenAPI / AsyncAPI / JSON Schema テンプレート
    - Database Schema（database_schema.yaml）
    - Contract-First ワークフロー
  ## Gate 3, 4 の承認
  ## よくあるエラーと対処
    - AC_NOT_COVERED / CONTRACT_COVERAGE_INCOMPLETE / REF_NOT_FOUND
```

---

### guides/09_execute_phase.md — Phase 3-5: 実行（目標: 800行）

```
# Phase 3-5: 実行
  ## このフェーズで作るもの
    - tasks.md + 実装コード + テスト + evidence_pack.md
  ## tasks.md の書き方
    - Work Item（WI-*）の構造
    - risk_flags と Mode 判定（autopilot/confirm/validate）
    - BDD 受入条件（Given-When-Then + escalation_trigger）
    - タスク分解のベストプラクティス
  ## Work Item / Run の実行追跡
    - Run ディレクトリ構造（RUN-YYYYMMDD-HHMM/）
    - walkthrough.md / test_results.md / lessons.md
    - Run Resume Detection（中断再開）
  ## Evidence Pack の管理
    - evidence_pack.md の構造
    - 自動収集されるメトリクス
    - 手動追加が必要な証跡
    - CI Results / Test Reports / SAST・SCA
  ## Gate 5 / Final の承認
  ## PR Readiness
    - `stride pr-check` の7チェック
    - PR作成前チェックリスト
  ## よくあるエラーと対処
    - APPROVAL_PENDING / TEST_NOT_TASKED / RUN_MULTIPLE
```

---

### guides/10_testing.md — テスト戦略（目標: 600行）

```
# テスト戦略
  ## テストの全体像
    - テスト種別一覧（UT/INT/CON/E2E）と使い分け
    - カバレッジポリシー（Tier別の必須テスト）
  ## 言語別テストツールガイド
    - TypeScript（Vitest / Playwright）
    - Python（pytest / pytest-playwright）
    - Java（JUnit / REST Assured）
    - テスト共通ベストプラクティス
  ## 契約テスト（TS-CON-*）
    - Contract-First でのテスト設計
    - OpenAPI / AsyncAPI のテスト手法
  ## E2E テスト
    - テストシナリオ設計（scenarios.yaml）
    - E2E Triage（e2e-triage.md）
    - E2Eレポーティング設定
  ## testreport 連携
    - CI テスト結果の evidence_pack 統合
  ## integration test の考え方
    - `tests/test_*_integration.py` の役割
    - CLI smoke / import API / fixture 設計
```

---

### guides/11_quality_gates.md — 品質ゲート（目標: 600行）

```
# 品質ゲート
  ## Quality Gate の全体像
    - stride lint / evaluate / pr-check / security / retro の位置付け
    - 「テスト」と「ゲート」を分けて理解する
  ## Living Spec Drift Detection
    - contracts/ と src/ の乖離自動検出
    - `spec_drift_detector.py` の使い方
  ## Multi-Model Evaluator
    - `stride evaluate` — LLMベースの意味的品質ゲート
    - 評価 Rubric / FAIL 条件
  ## Security Audit
    - `stride security --daily` / `--audit`
    - 10チェック項目一覧
    - LLM Trust Boundary
  ## PR Readiness
    - `stride pr-check` の7チェック
    - PR作成前チェックリスト
  ## Retrospective
    - `stride retro`
    - Feature / Epic の振り返りの読み方
  ## CI/CD 連携
    - 典型パイプライン
    - deep-dive は `sdd-templates/docs/CI_CD_INTEGRATION.md` へリンク
```

---

### guides/12_migration.md — 既存フォーマットからの移行（目標: 500行）

```
# 既存フォーマットからの移行
  ## SDD 導入の判断基準
    - どの案件から適用するか（新規 vs 既存）
    - 段階的導入のステップ
  ## テクノス既存フォーマット（SAPアドオン）からの移行
    - アドオン設計書 → SDD テンプレート対応表
    - 基本設計書 → basic_design.md
    - 詳細設計書 → spec.md + plan.md
    - テスト仕様書 → plan.md test_strategy + evidence_pack
  ## mcframe 設計書からの移行
    - 画面設計書 → basic_design.md + spec.md
    - 機能設計書 → spec.md + plan.md
    - 移行時の注意点（ID体系の違い等）
  ## 移行チェックリスト
    - 事前準備 / 変換作業 / 検証
```

---

### reference/13_cli_reference.md — stride CLI全コマンド（目標: 800行）

```
# stride CLI 全コマンドリファレンス
  ## インストールと PATH 設定
  ## stride lint
    - 概要 / オプション一覧 / 出力フォーマット（text/json/ndjson/plain）
    - Exit codes（0/1/2/3/4）
    - エラーコード一覧（全コード + suggested_action）
    - カラー出力 / NO_COLOR / --no-color
    - アクター追跡（STRIDE_ACTOR）
    - Lite Mode / Enterprise Mode
  ## stride init
    - オプション（--lite / --detect / --scale / --epic / --team）
    - Monorepo セットアップ（starter/standard/enterprise）
  ## stride intake
  ## stride phase-status / phase-check
  ## stride hooks（--tool claude/cursor/copilot/manual）
  ## stride auto-continue
  ## stride evaluate
  ## stride pr-check
  ## stride security
  ## stride retro
  ## stride ddd-init / decisions
  ## stride new-project
  ## stride symphony（run/dispatch/status/validate）
  ## stride epic（init/validate/gates/features/progress/list）
  ## 補助ツール
    - wi_readiness_checker.py
    - run_resume_detector.py
    - sdd_planning_bridge.py（init/sync/evidence/learn）
    - spec_drift_detector.py
    - evidence_metrics_collector.py
    - epic_progress_aggregator.py（HTML ダッシュボード含む）
    - stride_process_metrics.py
    - Database Lifecycle（stride db）
  ## 正本リンク
    - 構文の正本は `agent_docs/commands.md`
    - CI 詳細は `sdd-templates/docs/CI_CD_INTEGRATION.md`
```

---

### reference/14_artifact_reference.md — 成果物テンプレート（目標: 600行）

```
# 成果物テンプレートリファレンス
  ## 成果物一覧表
    - ファイル名 / 作成Phase / 必須/任意 / 概要
  ## basic_design.md
    - Canonical YAML 全フィールド解説
    - basic_design_gate_check
  ## spec.md
    - Canonical YAML 全フィールド解説
    - ユースケース / AC / spec_as_code
  ## plan.md
    - Canonical YAML 全フィールド解説
    - test_strategy / risks / dependencies
  ## tasks.md
    - Canonical YAML 全フィールド解説
    - Work Item / BDD AC / risk_flags
  ## APPROVAL.md
    - Gate 構造 / チェックボックス / 承認者フィールド
  ## evidence_pack.md
    - セクション構造 / 自動・手動収集フィールド
  ## process.bpmn / epic_flow.bpmn
    - 必須要素 / ID規約 / bpmn_descriptions
  ## contracts/*
    - openapi.yaml / database_schema.yaml / イベントスキーマ
  ## 補助成果物
    - constitution.md / artifact_registry.md
    - walkthrough.md / test_results.md / lessons.md
    - scenarios.yaml / e2e-triage.md / ops.md
```

---

### reference/15_id_conventions.md — ID規約（目標: 400行）

```
# ID 規約リファレンス
  （旧 appendix_a をそのまま移行。内容は変更なし）
  ## ID 体系一覧
  ## Feature ID（FEAT-*）
  ## ユースケース ID（US-*）
  ## 受入条件 ID（AC-*）
  ## 契約 ID（CT-*）
  ## テスト ID（TS-*）
  ## BPMN ID（BPMN-*）
  ## Work Item ID（WI-*）
  ## Epic ID（EPIC-*）
  ## config/id_conventions.yaml の構造
```

---

### reference/16_fourteen_articles.md — 14原則（目標: 200行）

```
# Fourteen Articles（十四条）
  （旧 appendix_c をそのまま移行。内容は変更なし）
  ## 基本4原則（I〜IV）
  ## 運用品質ルール（V〜IX）
  ## 拡張原則（X〜XIV）
```

---

### appendix/17_troubleshooting.md — トラブルシューティング（目標: 600行）

```
# トラブルシューティング
  （旧 appendix_d + 各ガイドのFAQを統合）
  ## stride-lint エラー
    - エラーコード別の対処法
  ## Phase Gate 関連
    - hooks が効かない / 承認が認識されない
  ## BPMN 関連
    - バリデーションエラー / Camunda 形式
  ## Enterprise 関連
    - Epic/Feature 紐付けエラー
  ## CI/CD 連携
    - PR Readiness / Symphony / テストレポート
  ## よくある質問（FAQ）
    - 各旧ガイドの FAQ を統合
```

---

### appendix/18_changelog.md — バージョン履歴（目標: 300行）

```
# バージョン履歴
  ## v5.0.0（現在）
    - stride-lint CLI UX 改善（clig.dev + Agent-Human Parity）
  ## v4.9.0
    - Security Audit / Retrospective Report / LLM Trust Boundary
  ## v4.8.0
    - Database Lifecycle / BPMN Camunda 8.8
  ## v4.7.x
    - Lesson Schema / learn サブコマンド / PostToolUse Guard
  ## v4.5.x〜v4.6.x
    - Symphony / BDD AC / Execution Authority
  ## v4.0〜v4.4
    - AI Autonomous Execution / Turborepo / PR Readiness
  ## v3.x
    - Tecnos-STRIDE (WI/Run/Mode/Autonomy Bias)
  ## v2.x
    - Enterprise Edition (Epic/Feature/Multi-team)
  ## v1.x
    - 基本SDD + stride-lint
```

---

### appendix/19_tutorial_web_edi.md — Web-EDIチュートリアル（目標: 1,000行）

```
# Web-EDI 実践チュートリアル
  （旧 08 を再構成。学習用の一本道チュートリアル）
  ## チュートリアルの概要
    - 何を作るか（Web-EDI受注受付）
    - 前提条件
  ## Step 1: 機能を初期化する
  ## Step 2: 基本設計を書く（basic_design.md）
  ## Step 3: BPMNを作成する
  ## Step 4: Gate 1,2 を承認する
  ## Step 5: 仕様を策定する（spec.md + plan.md）
  ## Step 6: Gate 3,4 を承認する
  ## Step 7: タスクを分解する（tasks.md）
  ## Step 8: Gate 5 を承認する
  ## Step 9: 実装する（WI/Run）
  ## Step 10: Final 承認 → PR
```

---

### appendix/20_erp_addon_playbook.md — ERP Addonプレイブック（目標: 700行）

```
# ERP Addon 実務プレイブック
  （旧 27 を再構成。実務運用・社内標準寄り）
  ## どの案件で使うか
    - SAP / ERP 連携案件の判断基準
  ## ERP固有の設計観点
    - IDoc / BAPI / FILE / Batch 契約
    - direct write 禁止、SoD、監査証跡
  ## ERP固有の実行追跡
    - WI / Run / walkthrough / test_results
  ## ERP固有のテスト戦略
    - critical tier 前提
    - 業務シナリオ / 回帰 / 移送 / 権限
  ## 運用上の注意
    - PM / Tech Lead / QA の確認観点
    - 典型エラーと対処
```

---

## サイドバー（_sidebar.md）

```markdown
- [🏠 Tecnos-STRIDE マニュアル](index.md)
- [⚡ クイックスタート（10分）](01_quickstart.md)

- **概念を理解する**
  - [SDD の基本思想](concepts/02_sdd_fundamentals.md)
  - [Phase Gate モデル](concepts/03_phase_gates.md)
  - [AI 自律実行モデル](concepts/04_ai_execution_model.md)
  - [Enterprise 拡張](concepts/05_enterprise_scale.md)

- **実践ガイド** 🚀
  - [PM 操作ガイド](guides/06_pm_guide.md)
  - [Phase 1: 設計](guides/07_design_phase.md)
  - [Phase 2: 仕様策定](guides/08_specify_phase.md)
  - [Phase 3-5: 実行](guides/09_execute_phase.md)
  - [テスト戦略](guides/10_testing.md)
  - [品質ゲート](guides/11_quality_gates.md)
  - [既存フォーマットからの移行](guides/12_migration.md)

- **リファレンス** 📖
  - [stride CLI 全コマンド](reference/13_cli_reference.md)
  - [成果物テンプレート](reference/14_artifact_reference.md)
  - [ID 規約](reference/15_id_conventions.md)
  - [14原則](reference/16_fourteen_articles.md)

- **付録** 📎
  - [トラブルシューティング](appendix/17_troubleshooting.md)
  - [バージョン履歴](appendix/18_changelog.md)
  - [Web-EDI チュートリアル](appendix/19_tutorial_web_edi.md)
  - [ERP Addon プレイブック](appendix/20_erp_addon_playbook.md)
```

---

## 執筆方針

### 文体
- **です・ます調**（PMにも読みやすい）
- 技術用語は初出時に一文説明を添える
- コマンド例は実行可能な形で記載

### 各ファイルの構造テンプレート
```markdown
# タイトル

> **対象**: PM / 設計者 / 実行者
> **所要時間**: X分
> **前提**: 01_quickstart を読んでいること
> **In scope**: このページで扱う範囲
> **Out of scope**: 扱わない内容とリンク先

---

## 本文

---

## 次に読むべきもの
- [関連ガイドへのリンク]
```

### 図表の方針
- ASCII図は最小限に（旧マニュアルの巨大ASCII図は読みにくかった）
- 表（Markdown table）を積極活用
- Mermaid 図を導入検討（Docsify で対応可能）

---

## 執筆順序（推奨）

1. **index.md** + **01_quickstart.md** — 入口を先に確定
2. **concepts/** 4本 — 概念の土台を固める
3. **guides/** 7本 — 実践ガイドを執筆（最もボリューム大）
4. **reference/** 4本 — リファレンスを整理（既存内容の再構成中心）
5. **appendix/** 4本 — 付録（既存の移行 + 統合）
6. **_sidebar.md** + **index.html** — Docsify 設定

---

*このファイルは manual2 完成後に削除またはアーカイブする。*
