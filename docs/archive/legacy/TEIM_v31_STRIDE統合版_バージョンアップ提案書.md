# TEIM v31.0 × Tecnos-STRIDE 統合バージョンアップ提案書

> **Version**: 2.0.0-draft
> **Date**: 2026-03-17
> **Author**: Tecnos Architecture Board / PMO
> **Status**: Draft for Review

---

## 1. エグゼクティブサマリー

### 1.1 背景

テクノスジャパンのERP導入方法論「TEIM v30.1」は、6フェーズ・約200タスク・12テスト工程・8役割定義・5段階稼働判定を網羅する成熟したウォーターフォール型方法論である。しかし、全プロセスが人間の手作業に依存しており、AI活用による生産性向上の余地が大きい。

一方、Tecnos-STRIDE（SDD v4.7.0）は「仕様が契約、コードは生成物」を原則とし、AI自律実行＋人間承認（RACI+）モデルで高速かつ高品質な開発を実現するフレームワークである。

### 1.2 提案の核心

**TEIM v30.1 → v31.0 へのパラダイムシフト**

| 軸 | TEIM v30.1（現行） | TEIM v31.0（提案） |
|---|---|---|
| 実行主体 | 人間が全タスクを実行 | **AI が実行（R）、人間が承認（A）** |
| 仕様の位置づけ | ドキュメント（参照物） | **Contract（機械可読な契約）** |
| 品質管理 | フェーズゲート（人間判断） | **Phase Gate + stride-lint（自動検証）** |
| 進捗管理 | Excel / 手動報告 | **GitHub Issues + Dashboard 自動集約** |
| テスト | 手動テスト主体 | **Coverage Tier × 自動テスト + Evidence Pack** |
| 変更管理 | 変更依頼書 → 承認 → 修正 | **Spec変更 → lint → Gate再承認 → 自動反映** |

### 1.3 期待効果

- 設計〜テスト工程の工数 **30-50% 削減**（AI自律実行による）
- 仕様とコードの乖離 **ゼロ化**（SSoT + stride-lint 自動検証）
- 品質ゲートの客観化（Evidence Pack による監査可能な証跡）
- PM報告業務の **70% 自動化**（ダッシュボード + 自動集約）

---

## 2. 構造比較：TEIM v30.1 ↔ Tecnos-STRIDE

### 2.1 フェーズマッピング

```
TEIM v30.1 (プロジェクト単位)          Tecnos-STRIDE (Feature単位)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━
①見積り                               (プロジェクト初期化)
②PJ計画 ─────────────────────────────→ Epic Design + Feature Breakdown
③要件定義 ────────────────────────────→ Design Phase (basic_design + BPMN)
④ビジネス設計 ────────────────────────→ Specify Phase (spec + plan + contracts)
⑤実現化【前半】アドオン設計/開発 ─────→ Tasking Phase + Execute Phase
⑤実現化【後半】テスト ────────────────→ Execute Phase (テスト自動化)
⑥本稼働準備 ──────────────────────────→ Final Gate + Evidence Pack
```

### 2.2 パラダイムの違い

| 観点 | TEIM v30.1 | Tecnos-STRIDE |
|---|---|---|
| 粒度 | フェーズ単位で順次進行 | Feature単位で並列進行可能 |
| 成果物形式 | Word/Excel（人間可読のみ） | YAML/Markdown/OpenAPI（機械可読） |
| 品質保証 | レビュー会議 | stride-lint + CI + Evidence Pack |
| 承認 | 紙 or メール | APPROVAL.md（Git管理 + 監査証跡） |
| テスト計画 | テスト計画書（Excel） | Coverage Policy（3層: AC/CT/Code） |
| 進捗把握 | 週次報告書（人手） | GitHub Dashboard（リアルタイム） |

---

## 3. 3層アーキテクチャ：TEIM ライフサイクル × STRIDE Feature サイクル

### 3.1 概念図

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: TEIM Project Lifecycle（プロジェクト全体）             │
│  ①見積り → ②PJ計画 → ③要件定義 → ④ビジネス設計 → ⑤実現化 → ⑥本稼働│
│    ↕ Coverage Tier: critical / standard / experimental          │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: STRIDE Feature Cycle（Feature単位）                   │
│  [Epic] ──→ [Feature A] Design→Specify→Task→Execute→Final      │
│         ├─→ [Feature B] Design→Specify→Task→Execute→Final      │
│         └─→ [Feature C] Design→Specify→Task→Execute→Final      │
│    ↕ Phase Gate: Gate 1-5 + Final（人間承認）                   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Symphony Orchestration（自動実行パイプライン）         │
│  GitHub Issues → Agent Loop → stride-lint → CI → Evidence Pack  │
│    ↕ RACI+: AI=R / Human=A / CI=Gate                           │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 層間の接続ルール

- Layer 1 のフェーズ境界 = Layer 2 の Feature群が全て Final Gate 通過していること
- Layer 2 の各 Gate = stride-lint PASS + 人間 APPROVAL.md 編集
- Layer 3 は Layer 2 の実行エンジン（人間は APPROVAL のみ関与）

---

## 4. フェーズ別統合提案

### 4.1 ①見積りフェーズ × STRIDE初期化

**現行 TEIM**: 手動で見積り、提案書作成
**提案 v31.0**:

```yaml
estimation_stride_integration:
  inputs:
    - "RFP / 顧客要件ヒアリング結果"
    - "過去PJ実績データ（SAP原価データ）"
  ai_automation:
    - "要件分類 → Coverage Tier 自動判定"
    - "類似PJ検索 → 工数概算"
    - "TEIM中日程テンプレート → 初期WBS自動生成"
  outputs:
    - "enterprise.yaml（Epic/Feature構成案）"
    - "初期見積書（Coverage Tier別工数）"
  human_approval: "見積り精度確認 + 提案書最終承認"
```

### 4.2 ②PJ計画フェーズ × Epic Design

**現行 TEIM**: 25タスク（体制構築、方針策定、計画策定等）
**提案 v31.0**:

TEIMのPJ計画タスク（1.02〜1.25）を STRIDE の Epic Design + Feature Breakdown にマッピング。

```yaml
pj_planning_mapping:
  teim_tasks:
    "1.02 PJ進め方説明":       "enterprise.yaml 初期化"
    "1.03 顧客体制構築":        "RACI+ 定義（Human/AI/CI）"
    "1.04 SteCo設置":          "approval_matrix.yaml 設定"
    "1.05 PJ方針":             "basic_design.md (Epic Level)"
    "1.06 インフラ方針":        "infra basic_design.md"
    "1.07 中日程作成":          "Epic Milestone + Feature Breakdown"
    "1.08-1.10 管理計画":       "memory/tecnos_org_constraints.md 反映"
    "1.11-1.15 テスト計画":     "Coverage Policy 定義"
    "1.16 変更管理":            "change_request workflow（BPMN）"
    "1.17-1.25 その他":         "project-level specs/ 配下に配置"
```

### 4.3 ③要件定義フェーズ × Design Phase

**現行 TEIM**: 要件定義6点セット（業務フロー、業務要件、帳票、IF、権限、ジョブ）
**提案 v31.0**: STRIDE Spec-as-Code にマッピング

```yaml
requirements_6set_mapping:
  "業務フロー定義":
    stride_artifact: "process.bpmn"
    format: "Camunda 8 (Zeebe 8.8) BPMN"
    machine_readable: true

  "業務要件定義":
    stride_artifact: "basic_design.md + spec.md"
    format: "YAML-embedded Markdown"
    machine_readable: true

  "帳票要件":
    stride_artifact: "specs/<feature>/contracts/report-*.yaml"
    format: "OpenAPI / カスタムスキーマ"
    machine_readable: true

  "IF要件":
    stride_artifact: "specs/<feature>/contracts/CT-API-*.yaml"
    format: "OpenAPI 3.x / AsyncAPI"
    machine_readable: true

  "権限要件":
    stride_artifact: "specs/<feature>/implementation-details/authz_matrix.yaml"
    format: "RBAC Matrix YAML"
    machine_readable: true

  "ジョブ要件":
    stride_artifact: "specs/<feature>/contracts/CT-BATCH-*.yaml"
    format: "Job Schedule YAML"
    machine_readable: true
```

#### 4.3.1 FtoS型 × fit_to_standard_analysis

FtoS型要件定義（42タスク）は STRIDE の適合性分析 Spec-as-Code として構造化：

```yaml
fit_to_standard_analysis:
  feature_id: "FEAT-XXX-001"
  erp_module: "SAP MM"
  analysis_date: "2026-XX-XX"

  standard_functions:
    - function_id: "SF-001"
      name: "購買依頼登録"
      fit_level: "full_fit"          # full_fit / partial_fit / gap
      gap_description: null

    - function_id: "SF-002"
      name: "発注処理"
      fit_level: "partial_fit"
      gap_description: "承認ワークフローのカスタマイズが必要"
      addon_required: true
      addon_type: "enhancement"      # enhancement / new_development / workflow
      estimated_effort_md: 15

  gap_summary:
    total_functions: 50
    full_fit: 35
    partial_fit: 10
    gap: 5
    fit_rate_pct: 70
    addon_count: 15
```

### 4.4 ④ビジネス設計フェーズ × Specify Phase

**現行 TEIM**: 25タスク（適合性分析、実現方式設計、システム仕様設計等）
**提案 v31.0**:

```yaml
business_design_mapping:
  teim_tasks:
    "3.02 適合性分析/実現方式設計":  "spec.md（AC/NFR定義）"
    "3.03 適合性評価":              "fit_to_standard_analysis.yaml 更新"
    "3.04 ライセンス取り纏め":       "infra spec.md"
    "3.05 システム仕様設計":         "plan.md + contracts/"
    "3.06 インフラジョブ設計":       "CT-BATCH-*.yaml"
    "3.07-3.10 各種設計":           "Feature別 spec.md + plan.md"

  stride_gates:
    - "Gate 3: spec.md 承認（AC完全性、NFR妥当性）"
    - "Gate 4: plan.md 承認（アーキテクチャ、テスト戦略）"

  auto_validation:
    - "stride-lint: AC ↔ TS 整合チェック"
    - "OpenAPI schema validation"
    - "Coverage Policy compliance check"
```

### 4.5 ⑤実現化フェーズ × Tasking + Execute Phase

**現行 TEIM**: 60タスク（設計・開発・テスト）
**提案 v31.0**: STRIDE の Tasking + Execute + Evidence Pack

#### 4.5.1 タスク分解

```yaml
realization_mapping:
  design_tasks:     # → STRIDE Tasking Phase
    "4.03 アドオン基本設計":   "tasks.md（Work Item定義）"
    "4.05 アドオン詳細設計":   "WI-*.md 個別タスク"

  development_tasks: # → STRIDE Execute Phase
    "4.06 アドオン開発":       "WI実装 + stride-lint + CI"
    "4.07 単体テスト":         "TS-UT-* 自動実行"

  test_tasks:        # → STRIDE Execute Phase (Coverage Tier別)
    "4.08-4.20 各種テスト":    "Coverage Tier × テスト種別マトリクス"
```

#### 4.5.2 TEIM 12テスト工程 × STRIDE Coverage Tier マトリクス

```
                        │ critical │ standard │ experimental │
━━━━━━━━━━━━━━━━━━━━━━│══════════│══════════│══════════════│
単体テスト              │ 必須     │ 必須     │ 必須         │
機能連携テスト          │ 必須     │ 必須     │ 任意         │
機能単体性能テスト      │ 必須     │ 条件付   │ 任意         │
機能単位障害テスト      │ 必須     │ 条件付   │ 任意         │
権限テスト              │ 必須     │ 必須     │ 条件付       │
JOBテスト               │ 必須     │ 必須     │ 条件付       │
IFテスト                │ 必須     │ 必須     │ 条件付       │
結合テスト              │ 必須     │ 必須     │ 任意         │
移行結合テスト          │ 必須     │ 必須     │ N/A          │
総合テスト              │ 必須     │ 必須     │ 簡易版       │
システム運用テスト      │ 必須     │ 条件付   │ 任意         │
業務運用テスト          │ 必須     │ 必須     │ 簡易版       │
━━━━━━━━━━━━━━━━━━━━━━│══════════│══════════│══════════════│
Evidence Pack           │ 全項目   │ 全項目   │ 簡易版       │
```

### 4.6 ⑥本稼働準備フェーズ × Final Gate + Evidence Pack

**現行 TEIM**: 25タスク + 5段階稼働判定
**提案 v31.0**:

```yaml
go_live_readiness:
  teim_5stage_decision:
    stage_1_application:
      timing: "総合テスト終了時"
      stride_equivalent: "全Feature Final Gate PASS"
      evidence: "Evidence Pack（全Feature集約）"

    stage_2_migration:
      timing: "移行リハ2終了時"
      stride_equivalent: "Migration Feature Final Gate"
      evidence: "移行テスト結果 + データ整合性レポート"

    stage_3_training:
      timing: "現場トレーニング終了時"
      stride_equivalent: "Training Completion Checklist"
      evidence: "トレーニング実施記録 + 理解度テスト結果"

    stage_4_operations:
      timing: "システム運用テスト終了時"
      stride_equivalent: "Ops Pack Registry 完成"
      evidence: "非機能テスト結果 + SLO定義 + 監視設定"

    stage_5_final:
      timing: "業務運用テスト終了時"
      stride_equivalent: "Epic Final Gate"
      evidence: "全Evidence Pack + 残課題ゼロ確認"
```

---

## 5. 役割再定義：TEIM 8役割 → STRIDE RACI+ モデル

### 5.1 マッピング

```
TEIM v30.1 役割              → STRIDE RACI+ Actor           → 責任変更
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
要件定義者                   → TJ_Human_PM / BizAnalyst      → A（承認者）に昇格
ERPコンサル                  → TJ_Human_TechLead             → A（技術承認者）
インフラベーシス             → TJ_Human_InfraLead            → A（インフラ承認者）
実現方式設計者               → TJ_AI_CodingAgent             → R（AI自律実行）
システム仕様設計者           → TJ_AI_CodingAgent             → R（AI自律実行）
基本設計者                   → TJ_AI_CodingAgent             → R（AI自律実行）
詳細設計者                   → TJ_AI_CodingAgent             → R（AI自律実行）
プログラマ                   → TJ_AI_CodingAgent + TJ_CI_Gate → R（AI実装+CI検証）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
（新設）顧客ビジネスオーナー → Customer_BizOwner             → A（業務承認）
（新設）顧客IT責任者         → Customer_ITOwner              → A（技術承認）
（新設）PMO                  → TJ_PMO                        → I/C（監視・助言）
```

### 5.2 RACI+ マトリクス（主要活動）

```
活動                    │PM(A)│TL(A)│AI(R) │CI   │顧客Biz│顧客IT│PMO
━━━━━━━━━━━━━━━━━━━━━━│═════│═════│══════│═════│═══════│══════│════
basic_design 作成       │  C  │  C  │  R   │  -  │   I   │   I  │  I
process.bpmn 作成       │  C  │  A  │  R   │  -  │   A   │   I  │  I
spec.md 作成            │  A  │  C  │  R   │  -  │   I   │   I  │  I
plan.md 作成            │  C  │  A  │  R   │  -  │   -   │   I  │  I
contracts/ 作成         │  -  │  A  │  R   │  V  │   -   │   I  │  -
tasks.md 作成           │  A  │  C  │  R   │  -  │   -   │   -  │  I
コード実装              │  -  │  C  │  R   │  V  │   -   │   -  │  -
テスト実行              │  -  │  C  │  R   │  V  │   -   │   -  │  I
Evidence Pack 生成      │  I  │  I  │  R   │  V  │   -   │   -  │  I
Phase Gate 承認         │  A  │  A  │  -   │  V  │   A*  │  A*  │  C
稼働判定                │  A  │  C  │  R†  │  V  │   A   │   A  │  A
```
*A* = critical tier のみ、R† = Evidence集約のみ

---

## 6. 成果物マッピング：TEIM成果物 → STRIDE Artifact

```yaml
deliverable_mapping:
  # 要件定義6点セット
  "業務フロー定義書":      "process.bpmn"
  "業務要件定義書":         "basic_design.md + spec.md"
  "帳票要件定義書":         "contracts/report-*.yaml"
  "IF要件定義書":           "contracts/CT-API-*.yaml + CT-EVT-*.yaml"
  "権限要件定義書":         "implementation-details/authz_matrix.yaml"
  "ジョブ要件定義書":       "contracts/CT-BATCH-*.yaml"

  # 設計成果物
  "適合性分析書":           "fit_to_standard_analysis.yaml"
  "実現方式設計書":         "plan.md (architecture section)"
  "システム仕様設計書":     "spec.md + plan.md"
  "基本設計書":             "plan.md (component design)"
  "詳細設計書":             "tasks.md (WI detailed specs)"

  # テスト成果物
  "全体テスト計画書":       "Coverage Policy (enterprise.yaml)"
  "各テスト仕様書":         "tests/scenarios.yaml"
  "テスト結果報告書":       "evidence_pack.md"

  # 管理成果物
  "PJ計画書":               "enterprise.yaml + RACI+"
  "進捗報告書":             "Dashboard (自動生成)"
```

---

## 7. プロジェクト管理統合

### 7.1 大中小日程 × STRIDE

```yaml
schedule_integration:
  大日程（Master Schedule）:
    source: "enterprise.yaml → Epic Milestones"
    granularity: "フェーズ/主要マイルストーン"
    update: "Epic Lead が手動更新 + AI提案"
    visibility: "customer_shared"

  中日程（Middle Schedule）:
    source: "Feature Milestones + Gate 状況"
    granularity: "Feature/Gate単位"
    update: "stride-lint 結果から自動集約"
    visibility: "customer_shared（概要）/ internal_only（詳細）"

  小日程（Detail Schedule）:
    source: "tasks.md → Work Items → GitHub Issues"
    granularity: "WI / Task単位"
    update: "GitHub Issues 自動同期"
    visibility: "internal_only"
```

### 7.2 変更管理ハイブリッド

```yaml
change_management:
  teim_4_58:  # Build期間
    trigger: "仕様変更要求"
    flow: |
      1. 変更要求 → GitHub Issue（change-request ラベル）
      2. AI: 影響分析（spec/plan/tasks への影響範囲特定）
      3. 人間: 承認（approval_matrix.yaml に基づく）
      4. AI: spec/plan/tasks 更新 → stride-lint → Gate再承認
    visibility: "internal_only（影響分析）→ customer_shared（承認結果）"

  teim_5_22:  # Release期間
    trigger: "本番リリース前の変更凍結"
    flow: |
      1. 変更凍結宣言（ARCH_BOARD承認）
      2. 緊急変更のみ受付（ESC-001〜005 エスカレーション）
      3. stride pr-check 全項目 PASS 必須
    visibility: "customer_shared"
```

---

## 8. 段階的ロールアウト計画

### Phase 1: 基盤整備（Month 1-2）

- Tecnos-STRIDE リポジトリの標準化
- TEIM タスクテンプレート → STRIDE テンプレートへの変換ツール作成
- パイロットプロジェクト選定（1〜2 Feature）
- チーム教育（SDD概念、stride CLI、APPROVAL フロー）

### Phase 2: パイロット実施（Month 2-4）

- パイロット Feature で Design → Final の全工程を STRIDE で実施
- TEIM既存プロセスとの並走（Dual Track）
- KPI測定：工数削減率、品質指標、チーム適応度

### Phase 3: 横展開（Month 4-6）

- パイロット結果に基づくテンプレート改善
- 全新規プロジェクトで STRIDE 適用開始
- Symphony Orchestration 導入（自動化パイプライン）

### Phase 4: 最適化（Month 6+）

- 実績データに基づく Coverage Tier 基準の最適化
- AI自律度の段階的向上（validate → confirm → autopilot）
- 全社KPI統合ダッシュボード運用開始

---

## 9. 期待効果とリスク

### 9.1 定量効果（想定）

| 指標 | 現行 | 目標 | 改善率 |
|---|---|---|---|
| 設計工数（人日/Feature） | 20-30 | 8-15 | 50-60% |
| テスト工数（人日/Feature） | 15-25 | 5-10 | 60-70% |
| 仕様⇔コード乖離件数 | 10-20/PJ | 0-2/PJ | 90%+ |
| Gate承認リードタイム | 5-10営業日 | 1-3営業日 | 60-80% |
| 報告書作成工数 | 2-3人日/週 | 0.5人日/週 | 75-85% |

### 9.2 リスクと対策

| リスク | 影響度 | 対策 |
|---|---|---|
| AI出力品質のばらつき | 中 | Coverage Policy + stride-lint による自動検証 |
| チーム学習コスト | 高 | 段階的ロールアウト + Dual Track 並走期間 |
| 顧客の理解・受容 | 中 | 顧客向け説明資料 + 可視性制御（3層モデル） |
| 既存PJとの互換性 | 低 | TEIM既存成果物 → STRIDE変換ツール |

---

## 10. マネジメントシステム設計

### 10.1 概念データモデル

TEIM v31.0 のマネジメントシステムは以下の階層で情報を管理する。

```
Project
  ├── Phase（TEIMフェーズ: ①〜⑥）
  │     ├── Feature（STRIDE Feature）
  │     │     ├── Work Item（実装単位）
  │     │     │     └── Run（実行記録）
  │     │     ├── Gate（Phase Gate 承認記録）
  │     │     └── Evidence Pack
  │     └── Milestone（フェーズマイルストーン）
  ├── Meeting（定例会議・SteCo・PMO会議）
  │     ├── Decision（意思決定記録）
  │     └── Action Item
  ├── Issue（課題管理）
  │     ├── IssueEscalation（エスカレーション履歴）
  │     └── IssueResolution
  ├── CostRecord（原価情報）← SAP連携
  ├── Schedule（大中小日程）
  └── ChangeRequest（変更管理）
```

### 10.2 3層可視性モデル

全データに可視性レベル（Visibility Tier）を付与し、報告先に応じた情報制御を行う。

```yaml
visibility_tiers:
  customer_shared:
    description: "顧客PMと共有する情報"
    includes:
      - "大日程（Master Schedule）進捗"
      - "フェーズゲート承認状況"
      - "重要課題（顧客エスカレーション対象）"
      - "成果物納品状況"
      - "稼働判定結果"
      - "変更管理（承認済み）"
    excludes:
      - "コスト構造（原価・利益率）"
      - "社内評価・人事情報"
      - "内部課題（軽微なもの）"

  internal_only:
    description: "テクノス社内（プロジェクトチーム）で共有する情報"
    includes:
      - "customer_shared の全情報"
      - "小日程（WI/Task単位）進捗"
      - "内部品質指標（Coverage、lint結果）"
      - "全課題（軽微なものを含む）"
      - "チーム別進捗・稼働状況"
      - "AI実行ログ・Evidence Pack詳細"
    excludes:
      - "コスト構造（原価・利益率）"
      - "PMO評価・経営判断情報"

  management_only:
    description: "テクノス経営層・PMO のみアクセスする情報"
    includes:
      - "internal_only の全情報"
      - "コスト構造（SAP原価データ）"
      - "利益率・予実差異分析"
      - "PM評価情報"
      - "リソース配置最適化データ"
      - "経営リスク評価"
```

### 10.3 ER図（論理モデル）

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Project  │1───*│  Phase   │1───*│ Feature  │1───*│WorkItem  │
│          │     │          │     │          │     │          │
│ proj_id  │     │ phase_id │     │ feat_id  │     │ wi_id    │
│ name     │     │ teim_no  │     │ name     │     │ title    │
│ customer │     │ name     │     │ cov_tier │     │ status   │
│ status   │     │ status   │     │ status   │     │ assignee │
└──────────┘     └──────────┘     │ gate_*   │     │ est_hours│
      │                           └──────────┘     │ act_hours│
      │                                 │          └──────────┘
      │          ┌──────────┐           │                │
      │1────────*│ Meeting  │           │          ┌──────────┐
      │          │          │           │1────────*│   Run    │
      │          │ mtg_id   │           │          │          │
      │          │ type     │           │          │ run_id   │
      │          │ date     │           │          │ status   │
      │          │ level    │           │          │ started  │
      │          └──────────┘           │          │ finished │
      │                │                │          └──────────┘
      │          ┌──────────┐           │
      │          │ Decision │     ┌──────────┐
      │          │          │     │EvidPack  │
      │          │ dec_id   │     │          │
      │          │ content  │     │ ep_id    │
      │          │ approver │     │ ci_pass  │
      │          └──────────┘     │ lint_pass│
      │                           │ tests    │
      │1────────*┌──────────┐     └──────────┘
      │          │  Issue   │
      │          │          │          ┌──────────┐
      │          │ issue_id │1────────*│CostRecord│
      │          │ title    │          │          │
      │          │ severity │          │ cost_id  │
      │          │ source   │←─Jira    │ sap_ref  │
      │          │ vis_tier │          │ amount   │
      │          │ status   │          │ category │
      │          └──────────┘          │ vis_tier │
      │                                │ ="mgmt"  │
      │1────────*┌──────────┐          └──────────┘
                 │ Schedule │
                 │          │
                 │ sched_id │
                 │ level    │ ← 大/中/小
                 │ baseline │
                 │ actual   │
                 │ vis_tier │
                 └──────────┘
```

### 10.4 役割別アクセスマトリクス

```
データ種別              │顧客PM│顧客IT│TJ_PM│TJ_TL│PMO │経営層│
━━━━━━━━━━━━━━━━━━━━━━│══════│══════│═════│═════│════│═════│
大日程進捗              │  R   │  R   │ RW  │  R  │ R  │  R  │
中日程進捗              │  R*  │  R   │ RW  │ RW  │ R  │  R  │
小日程（WI）            │  -   │  -   │ RW  │ RW  │ R  │  -  │
Gate承認状況            │  R   │  R   │ RW  │ RW  │ R  │  R  │
Evidence Pack           │  R*  │  R   │ RW  │ RW  │ R  │  -  │
課題（重要）            │  R   │  R   │ RW  │ RW  │ R  │  R  │
課題（軽微）            │  -   │  -   │ RW  │ RW  │ R  │  -  │
コスト構造              │  -   │  -   │  -  │  -  │ R  │  R  │
利益率・予実            │  -   │  -   │  -  │  -  │ R  │  R  │
AI実行ログ              │  -   │  -   │  R  │ RW  │ R  │  -  │
変更管理（承認済み）    │  R   │  R   │ RW  │ RW  │ R  │  R  │
変更管理（検討中）      │  -   │  -   │ RW  │ RW  │ R  │  -  │
PM評価                  │  -   │  -   │  -  │  -  │ RW │  R  │
稼働判定結果            │  R   │  R   │ RW  │  R  │ R  │  R  │
リソース配置            │  -   │  -   │  R  │  -  │ RW │  R  │
```
R* = サマリーのみ、RW = 読み書き

---

## 11. 外部システム連携設計

### 11.1 SAP連携（コストデータ）

プロジェクト原価データはSAPから取得し、**management_only** 層でのみ参照可能とする。

```yaml
sap_cost_integration:
  purpose: "プロジェクト原価管理（社内限定）"
  visibility: "management_only"  # 顧客PMには絶対に公開しない

  data_flow:
    source: "SAP CO/PS モジュール"
    extraction:
      method: "API (OData) or RFC"
      frequency: "daily_batch"  # 日次バッチで取得
      target_table: "CostRecord"

    data_items:
      - item: "labor_cost"
        description: "人件費（工数×単価）"
        sap_source: "CO-内部指図 or PS-WBS要素"

      - item: "external_cost"
        description: "外注費・購買費"
        sap_source: "MM-購買実績 → CO転記"

      - item: "travel_expense"
        description: "旅費・経費"
        sap_source: "FI-経費精算 → CO転記"

      - item: "license_cost"
        description: "ライセンス費用"
        sap_source: "CO-コスト要素"

      - item: "budget_baseline"
        description: "予算基準額"
        sap_source: "PS-WBS計画値"

  aggregation:
    by_phase: true       # TEIMフェーズ別集計
    by_feature: true     # STRIDE Feature別集計
    by_team: true        # チーム別集計
    by_cost_element: true # コスト要素別集計

  reporting:
    pmo_meeting:
      content: "予実差異分析（予算消化率、残予算、EAC）"
      format: "Dashboard（自動更新）"
      access: ["PMO", "経営層"]

    internal_review:
      content: "Feature別コスト配分、チーム別稼働率"
      format: "週次レポート（自動生成）"
      access: ["PMO"]

    # ⚠️ 以下は明示的に禁止
    customer_report:
      content: null
      note: "コスト構造は顧客には一切共有しない"
```

### 11.2 Jira連携（課題管理）

課題管理はJiraをソースとし、重要度に応じてフィルタリングして報告する。

```yaml
jira_issue_integration:
  purpose: "課題管理の一元化と報告粒度制御"

  data_flow:
    source: "Jira (REST API)"
    sync:
      method: "Webhook + Polling (15min)"
      target_table: "Issue"
      bidirectional: true  # STRIDE → Jira も同期

    field_mapping:
      jira_key:        "issue_id"
      summary:         "title"
      priority:        "severity"  # P1-P4 → critical/high/medium/low
      status:          "status"
      assignee:        "assignee"
      labels:          "tags"
      custom_field_project: "proj_id"
      custom_field_feature: "feat_id"

  # 報告フィルタリングルール
  visibility_rules:
    customer_shared:
      filter: |
        severity IN ('critical', 'high')
        AND status != 'resolved'
        AND labels CONTAINS 'customer-visible'
      description: "顧客に報告する重要課題のみ"

    internal_only:
      filter: |
        severity IN ('critical', 'high', 'medium')
        OR labels CONTAINS 'internal-escalation'
      description: "社内プロジェクト会議で扱う課題"

    management_only:
      filter: "ALL"  # PMOは全課題を閲覧可能
      additional: "コスト影響・スケジュール影響の分析を付与"

  # エスカレーションフロー
  escalation:
    auto_escalate:
      - condition: "severity == 'critical' AND age_days > 3"
        action: "PMO自動通知 + SteCo議題登録"
      - condition: "severity == 'high' AND age_days > 7"
        action: "PM上長報告 + 対策計画要求"

    reporting_cadence:
      daily_standup: "新規critical/high課題のサマリー"
      weekly_report: "全課題ステータス（フィルタ済み）"
      pmo_meeting:   "重要課題の傾向分析 + 対策状況"
      steco:         "顧客エスカレーション対象のみ"
```

### 11.3 GitHub連携（開発進捗）

```yaml
github_integration:
  purpose: "開発進捗のリアルタイム可視化"

  data_sources:
    issues:
      label_filter: "work-item"
      sync: "stride wi sync → WI-*.md 生成"

    pull_requests:
      check: "stride pr-check（7項目品質ゲート）"

    actions:
      dashboard: "GitHub Actions → Dashboard自動更新"
      evidence:  "CI結果 → Evidence Pack自動生成"

  aggregation:
    feature_progress:
      formula: "完了WI数 / 全WI数 × 100"
      auto_update: true

    phase_progress:
      formula: "完了Feature数 / 全Feature数 × 100"
      auto_update: true

    quality_score:
      components:
        - "stride-lint PASS率"
        - "テストカバレッジ"
        - "Evidence Pack完成度"
```

### 11.4 統合アーキテクチャ

```
                    ┌─────────────────────────────────────────────┐
                    │           Reporting Layer                    │
                    │  ┌─────────┐ ┌──────────┐ ┌──────────────┐ │
                    │  │顧客Portal│ │社内Portal │ │PMO Dashboard │ │
                    │  │(shared)  │ │(internal)│ │(management)  │ │
                    │  └────┬─────┘ └────┬─────┘ └──────┬───────┘ │
                    └───────┼────────────┼──────────────┼─────────┘
                            │            │              │
                    ┌───────┴────────────┴──────────────┴─────────┐
                    │           API Gateway (Visibility Filter)    │
                    │   customer_shared │ internal_only │ mgmt_only│
                    └───────┬────────────┬──────────────┬─────────┘
                            │            │              │
          ┌─────────────────┼────────────┼──────────────┼──────┐
          │                 │    Data Integration Layer  │      │
          │  ┌──────────┐   │   ┌──────────┐   ┌──────────┐   │
          │  │ GitHub    │───┼──→│ STRIDE   │←──│  SAP     │   │
          │  │ (Issues/  │   │   │ Data     │   │ (CO/PS)  │   │
          │  │  PR/CI)   │   │   │ Store    │   │ mgmt_only│   │
          │  └──────────┘   │   │(PostgreSQL)│  └──────────┘   │
          │  ┌──────────┐   │   │          │   ┌──────────┐   │
          │  │  Jira     │───┼──→│          │←──│ その他   │   │
          │  │ (Issues)  │   │   │          │   │ (将来)   │   │
          │  └──────────┘   │   └──────────┘   └──────────┘   │
          └─────────────────┴──────────────────────────────────┘
```

---

## 12. PM情報提示ガイド

### 12.1 目的

PMが各種会議・報告の場で「何の情報を、どの粒度で、誰に提示すべきか」を定義する。
これにより、報告漏れ・過剰報告を防ぎ、会議の生産性を最大化する。

### 12.2 会議レベル別 情報提示マトリクス

#### Level 1: デイリースタンダップ（チーム内）

```yaml
daily_standup:
  audience: "プロジェクトチーム（TJ_PM, TJ_TL, 開発メンバー）"
  frequency: "毎日 15分"
  visibility: "internal_only"

  pm_presents:
    必須:
      - "本日のブロッカー / 新規critical課題"
      - "Gate承認待ち状態のFeature"
      - "顧客からの新規要求・質問"
    自動提供（Dashboard）:
      - "WI進捗（完了/進行中/未着手）"
      - "直近のstride-lint結果"
      - "CI/CDパイプライン状態"
    提示しない:
      - "コスト情報"
      - "PMO評価関連"
      - "他チームの詳細進捗"
```

#### Level 2: 週次プロジェクト会議（社内）

```yaml
weekly_project_meeting:
  audience: "TJ_PM, TJ_TL, PM上長"
  frequency: "週1回 60分"
  visibility: "internal_only"

  pm_presents:
    進捗報告:
      - "中日程ベースの進捗率（Feature単位）"
      - "Gate通過状況（計画 vs 実績）"
      - "今週の完了Feature / 来週の予定Feature"
      source: "GitHub Dashboard 自動集約"

    品質報告:
      - "stride-lint PASS率の推移"
      - "テストカバレッジ（Coverage Tier別）"
      - "Evidence Pack完成度"
      source: "CI自動集約"

    課題報告:
      - "新規課題一覧（severity: critical/high/medium）"
      - "未解決課題のエイジング分析"
      - "エスカレーション候補"
      source: "Jira → internal_only フィルタ"

    リスク報告:
      - "スケジュールリスク（遅延Feature一覧）"
      - "品質リスク（lint FAIL率が高いFeature）"
      - "リソースリスク（稼働率異常）"

    提示しない:
      - "コスト構造・利益率"
      - "PM個人評価"
```

#### Level 3: PMO会議（経営報告）

```yaml
pmo_meeting:
  audience: "PMO, 経営層, PM上長"
  frequency: "月1-2回 90分"
  visibility: "management_only"

  pm_presents:
    プロジェクト概況:
      - "大日程ベースの進捗（フェーズ完了率）"
      - "全体リスクサマリー（Red/Amber/Green）"
      - "主要マイルストーン達成状況"

    コスト報告:      # ← SAP連携データ
      - "予算消化率（計画 vs 実績）"
      - "EAC（完了時見積り）"
      - "予実差異の要因分析"
      - "チーム別コスト配分"
      source: "SAP CO/PS → 自動集約"
      note: "⚠️ この情報は顧客には一切共有しない"

    課題報告:        # ← Jira連携データ
      - "重要課題の傾向分析（件数推移、平均解決日数）"
      - "顧客エスカレーション対象の進捗"
      - "リスク課題の対策状況"
      source: "Jira → management_only フィルタ"

    AI活用レポート:
      - "AI自律実行率（autopilot/confirm/validate比率）"
      - "AI実行による工数削減効果"
      - "AI品質指標（lint自動修正率、テスト自動生成率）"

    判断要求:
      - "リソース追加・配置変更の要否"
      - "スコープ調整の要否"
      - "フェーズ移行判定の可否"
```

#### Level 4: SteCo（ステアリングコミッティ / 顧客報告）

```yaml
steco_meeting:
  audience: "顧客BizOwner, 顧客ITOwner, TJ_PM, TJ_TL"
  frequency: "月1回 or 隔週"
  visibility: "customer_shared"

  pm_presents:
    進捗報告:
      - "大日程ベースのフェーズ進捗"
      - "主要マイルストーン達成状況"
      - "成果物納品状況"
      note: "Feature粒度は必要に応じてサマリーで提示"

    課題報告:
      - "顧客エスカレーション対象課題のみ"
      - "顧客側アクション待ちの事項"
      - "意思決定が必要な事項"
      source: "Jira → customer_shared フィルタ"
      note: "内部課題（軽微）は含めない"

    変更管理:
      - "承認済み変更要求の実施状況"
      - "新規変更要求の影響分析結果"

    次回までの予定:
      - "次フェーズの主要タスクと期待成果"
      - "顧客側タスク・準備事項"

    絶対に提示しない:
      - "コスト構造（原価・利益率・予算消化率）"
      - "社内評価情報"
      - "内部リソース配置"
      - "AI実行ログ詳細"
```

### 12.3 情報提示フロー図

```
  情報源                フィルタリング              報告先
  ━━━━━━              ━━━━━━━━━━━━              ━━━━━━

  GitHub ──→ Feature進捗 ──┬─→ [customer_shared] ──→ SteCo
  (Issues/   Gate状態      │     大日程サマリー
   CI/PR)    品質指標      ├─→ [internal_only] ────→ 週次PJ会議
                           │     Feature粒度詳細        デイリー
                           └─→ [management_only] ──→ PMO会議
                                 AI活用レポート

  Jira ────→ 全課題 ──────┬─→ [customer_shared] ──→ SteCo
  (課題管理)  severity     │     critical+high          (重要のみ)
              age分析      ├─→ [internal_only] ────→ 週次PJ会議
                           │     medium以上              デイリー
                           └─→ [management_only] ──→ PMO会議
                                 傾向分析+全課題

  SAP ─────→ 原価データ ──→ [management_only] ────→ PMO会議のみ
  (CO/PS)    予実差異                                  ⚠️顧客には
             EAC                                       絶対に出さない
```

### 12.4 PM提示情報チェックリスト

PMが各会議前に確認すべきチェックリスト（自動生成対応）。

```yaml
pm_checklist:
  before_steco:
    - check: "大日程の計画 vs 実績が最新か"
      auto: true  # Dashboard から自動取得
    - check: "顧客向け課題一覧が customer_shared フィルタ済みか"
      auto: true  # Jira → フィルタ自動適用
    - check: "コスト情報が資料に含まれていないか"
      auto: true  # visibility チェック自動実行
      critical: true  # ⚠️ 絶対に確認
    - check: "変更要求の承認状況が最新か"
      auto: true
    - check: "顧客アクション待ち事項が明確か"
      auto: false  # PM手動確認

  before_pmo:
    - check: "SAP原価データが最新取得済みか"
      auto: true  # 日次バッチ確認
    - check: "EAC（完了時見積り）を算出したか"
      auto: true  # 自動算出
    - check: "AI活用KPIを集計したか"
      auto: true  # Dashboard から自動
    - check: "リソース配置変更の要否を判断したか"
      auto: false  # PM判断
    - check: "フェーズ移行可否の根拠を準備したか"
      auto: false  # PM判断 + Evidence Pack参照

  before_weekly:
    - check: "Feature別進捗が最新か"
      auto: true  # GitHub自動集約
    - check: "stride-lint結果を確認したか"
      auto: true
    - check: "新規課題のトリアージが完了しているか"
      auto: false  # TLと共同判断
```

---

## 13. ビジネスフロー：RFP → 提案 → マスタスケジュール

### 13.1 全体フロー

```
RFP受領                 提案書作成             受注・PJ開始
━━━━━━                 ━━━━━━━━             ━━━━━━━━━━
  │                       │                     │
  ▼                       ▼                     ▼
┌─────────┐  AI分析  ┌─────────┐  受注   ┌─────────────┐
│ RFP解析 │────────→│ 提案書  │───────→│ enterprise  │
│         │         │ 作成    │        │ .yaml初期化 │
│・要件抽出│         │・概算見積│        │             │
│・リスク  │         │・体制案 │        │・Epic定義   │
│ 分析    │         │・スケ概要│        │・Feature    │
│・類似PJ │         │・Coverage│        │ Breakdown  │
│ 検索    │         │ Tier判定│        │・Coverage   │
└─────────┘         └─────────┘        │ Tier確定   │
                                        └──────┬──────┘
                                               │
                    ┌──────────────────────────┘
                    ▼
            ┌─────────────┐
            │ マスタスケ   │
            │ ジュール作成 │
            │             │
            │・大日程定義  │→ TEIMフェーズ×期間
            │・Epic MS    │→ Epic Milestone
            │・Feature MS │→ Feature Milestone
            │・稼働判定日 │→ 5段階判定スケジュール
            │・Gate計画   │→ Phase Gate予定日
            └──────┬──────┘
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ 大日程   │ │ 中日程   │ │ 小日程   │
│ customer │ │ internal │ │ internal │
│ _shared  │ │ _only    │ │ _only    │
│          │ │          │ │          │
│ Phase単位│ │Feature/  │ │WI/Task  │
│ 月単位   │ │Gate単位  │ │日単位    │
│          │ │週単位    │ │          │
└──────────┘ └──────────┘ └──────────┘
```

### 13.2 RFP解析フェーズ（AI支援）

```yaml
rfp_analysis:
  ai_tasks:
    - task: "RFP文書の構造化解析"
      input: "RFP文書（PDF/Word）"
      output: "要件リスト（YAML）"

    - task: "Coverage Tier 初期判定"
      logic: |
        - ERP標準機能で対応可能 → standard
        - カスタマイズ必要 → standard or critical
        - 新規開発必要 → critical
        - PoC/検証目的 → experimental
      output: "Feature別Coverage Tier案"

    - task: "類似PJ検索"
      input: "要件リスト + 業種 + ERPモジュール"
      source: "過去PJ実績DB"
      output: "類似PJ一覧 + 実績工数 + 教訓"

    - task: "リスク初期評価"
      input: "要件リスト + 類似PJ教訓"
      output: "リスクレジスタ（初版）"

  human_review:
    - "Coverage Tier判定の妥当性確認"
    - "概算見積りの精度確認"
    - "提案戦略の決定"
```

### 13.3 提案書作成フェーズ

```yaml
proposal_creation:
  inputs:
    - "RFP解析結果"
    - "Coverage Tier判定"
    - "類似PJ実績"
    - "SAP原価データ（過去PJ）" # management_only

  ai_generates:
    - artifact: "提案書ドラフト"
      sections:
        - "プロジェクト概要・目的"
        - "TEIM×STRIDEアプローチ説明"
        - "スコープ定義（Epic/Feature構成案）"
        - "体制図（RACI+ベース）"
        - "概算スケジュール（大日程レベル）"
        - "概算見積り（Coverage Tier別）"

    - artifact: "enterprise.yaml（ドラフト）"
      content: "Epic/Feature構成 + Coverage Tier + 依存関係"

  human_decisions:
    - "提案価格の最終決定"  # management_only
    - "体制の最終確定"
    - "スコープの最終確定"
    - "顧客への提案戦略"
```

### 13.4 マスタスケジュール投入

受注確定後、enterprise.yaml をベースにマスタスケジュールを生成する。

```yaml
master_schedule_generation:
  trigger: "受注確定"

  step_1_epic_planning:
    input: "enterprise.yaml（確定版）"
    ai_tasks:
      - "TEIMフェーズ × Epic Milestone のマッピング"
      - "Feature間依存関係の解析"
      - "クリティカルパス算出"
    output: "Epic Milestone Plan"

  step_2_feature_scheduling:
    input: "Epic Milestone Plan + Coverage Tier"
    ai_tasks:
      - "Feature別の Design→Final 期間見積り"
      - "Coverage Tier別の並列度計算"
      - "Gate承認期間の見込み（approval_matrix.yaml参照）"
    output: "Feature Schedule（中日程ベース）"

  step_3_schedule_hierarchy:
    generates:
      大日程:
        granularity: "フェーズ/月単位"
        content:
          - "TEIMフェーズ開始・終了日"
          - "主要マイルストーン"
          - "稼働判定日程（5段階）"
        visibility: "customer_shared"
        format: "Gantt chart（自動生成）"

      中日程:
        granularity: "Feature/Gate/週単位"
        content:
          - "Feature別 Design→Final スケジュール"
          - "Gate承認予定日"
          - "チーム別作業計画"
        visibility: "internal_only（詳細）/ customer_shared（サマリー）"
        format: "GitHub Project Board + Gantt"

      小日程:
        granularity: "WI/Task/日単位"
        content:
          - "WI別作業スケジュール"
          - "日次タスク割り当て"
        visibility: "internal_only"
        format: "GitHub Issues + sprint board"

  step_4_baseline:
    action: "全スケジュールのベースライン保存"
    tracking: "計画 vs 実績の差異を自動追跡"
```

### 13.5 スケジュール vs 納品ステータス

進捗管理では「スケジュール進捗」と「納品（成果物完成）ステータス」を区別する。

```yaml
progress_tracking:
  schedule_progress:
    definition: "時間軸に対する進捗（計画日程 vs 実績日程）"
    metrics:
      - "SPI（Schedule Performance Index）= EV / PV"
      - "遅延日数（Feature単位、Phase単位）"
      - "クリティカルパス上のバッファ消化率"
    source: "GitHub Milestones + Gate承認日"

  delivery_status:
    definition: "成果物の完成度（品質を含む）"
    metrics:
      - "Gate通過率 = 通過Feature数 / 計画Feature数"
      - "Evidence Pack完成度"
      - "stride-lint PASS率"
      - "テストカバレッジ達成率"
    source: "stride-lint + CI + Evidence Pack"

  combined_view:
    description: "スケジュールと納品を統合したビュー"
    matrix: |
      ┌──────────┬─────────────┬─────────────┐
      │          │ 納品OK      │ 納品NG      │
      ├──────────┼─────────────┼─────────────┤
      │ 予定通り │ ✅ Green     │ ⚠️ Amber    │
      │          │ 順調        │ 品質リスク   │
      ├──────────┼─────────────┼─────────────┤
      │ 遅延     │ ⚠️ Amber    │ 🔴 Red      │
      │          │ 日程リスク   │ 要対策      │
      └──────────┴─────────────┴─────────────┘

    auto_classification: true  # Dashboard自動判定
```

---

## 14. 業務モデル・データモデル粒度設計

### 14.1 フェーズ別の意思決定粒度

各TEIMフェーズで「どのレベルまで決める必要があるか」を定義する。

```yaml
decision_granularity:
  "②PJ計画":
    business_model:
      level: "業務領域レベル"
      decides: "対象業務領域、主要業務フロー概要、ERP適用範囲"
      defers: "詳細業務ルール、例外処理"
      artifact: "enterprise.yaml + Epic basic_design.md"

    data_model:
      level: "エンティティレベル"
      decides: "主要マスタ/トランザクション一覧、SoR（正本）定義"
      defers: "属性定義、関連定義"
      artifact: "data_model_overview.yaml"

    schedule:
      level: "フェーズ/月単位"
      decides: "フェーズ期間、主要マイルストーン"
      artifact: "大日程"

  "③要件定義":
    business_model:
      level: "業務プロセスレベル"
      decides: "業務フロー詳細、入出力、権限、ジョブ、IF"
      defers: "ERP設定パラメータ、アドオン詳細仕様"
      artifact: "process.bpmn + basic_design.md + 6点セットSpec"

    data_model:
      level: "属性レベル（主要）"
      decides: "主要属性、型、必須/任意、参照関係"
      defers: "インデックス、パーティション、物理設計"
      artifact: "specs/<feature>/contracts/ + DB-FEAT-*.yaml"

    schedule:
      level: "Feature/Gate単位"
      decides: "Feature別スケジュール、Gate予定日"
      artifact: "中日程"

  "④ビジネス設計":
    business_model:
      level: "実現方式レベル"
      decides: |
        - ERP標準機能 vs アドオンの確定
        - アドオン機能仕様
        - システム間連携仕様
      artifact: "spec.md + plan.md + contracts/"

    data_model:
      level: "物理設計レベル"
      decides: "テーブル定義、インデックス、移行マッピング"
      artifact: "implementation-details/migration_mapping.yaml"

    schedule:
      level: "WI/週単位"
      decides: "実装順序、テスト計画詳細"
      artifact: "中日程（詳細）+ 小日程"

  "⑤実現化":
    business_model:
      level: "実装レベル"
      decides: "コード実装、設定値、テスト条件"
      artifact: "tasks.md + WI-*.md + evidence_pack.md"

    data_model:
      level: "実装レベル"
      decides: "DDL確定、移行スクリプト、テストデータ"
      artifact: "contracts/ + tests/scenarios.yaml"

    schedule:
      level: "Task/日単位"
      decides: "日次タスク割り当て"
      artifact: "小日程（GitHub Issues）"
```

### 14.2 Feature要件 → 要件設計 のトレーサビリティ

```yaml
traceability_chain:
  flow: |
    顧客要求(RFP)
      → 業務要件(RQ-*)
        → ユースケース(US-*)
          → 受入条件(AC-*)
            → テストシナリオ(TS-*)
              → Evidence Pack

  stride_implementation:
    "RQ-* (要件)":
      location: "basic_design.md → requirements[]"
      format: "YAML"

    "US-* (ユースケース)":
      location: "spec.md → use_cases[]"
      format: "YAML"
      links_to: "RQ-* via requirement_refs"

    "AC-* (受入条件)":
      location: "spec.md → use_cases[].acceptance_criteria[]"
      format: "YAML"
      links_to: "US-* (親ユースケース)"
      tagged: "integration, e2e, security 等"

    "TS-* (テストシナリオ)":
      location: "tests/scenarios.yaml"
      format: "YAML"
      links_to: "AC-* via ac_ref"
      coverage: "AC Coverage = 100% 必須"

    "Evidence":
      location: "evidence_pack.md"
      links_to: "TS-* の実行結果"

  validation:
    - "stride-lint: AC → TS カバレッジ 100% チェック"
    - "stride-lint: RQ → US → AC チェーン完全性チェック"
    - "stride pr-check: Evidence Pack 存在チェック"
```

---

## 15. フェーズ別・課題別 デュアルトラッキング

### 15.1 概念

プロジェクト管理では「フェーズベースの進捗」と「課題ベースの対応状況」を並行追跡する。

```yaml
dual_tracking:
  phase_based:
    description: "TEIMフェーズの計画 vs 実績を追跡"
    axes:
      - "フェーズ進捗率"
      - "Gate通過状況"
      - "成果物完成度"
    dashboard: "Phase Progress View"
    update: "自動（GitHub + stride-lint）"

  issue_based:
    description: "課題の発生・対応・解決を追跡"
    axes:
      - "課題件数推移（新規/解決/残存）"
      - "severity別分布"
      - "エイジング（未解決期間）"
      - "Feature紐付き（どのFeatureの課題か）"
    dashboard: "Issue Tracking View"
    update: "自動（Jira同期）"

  cross_reference:
    description: "フェーズ進捗と課題を関連付けて分析"
    examples:
      - "③要件定義フェーズで critical課題が急増 → フェーズ延長リスク"
      - "特定Featureに課題が集中 → Coverage Tier 格上げ検討"
      - "課題解決速度が低下 → リソース追加検討"
```

### 15.2 ダッシュボード構成

```
┌─────────────────────────────────────────────────────────────┐
│  TEIM v31.0 Project Dashboard                               │
├─────────────────────────┬───────────────────────────────────┤
│  Phase Progress         │  Issue Tracking                   │
│  ┌───┬───┬───┬───┬───┐ │  ┌─────────────────────────────┐  │
│  │②  │③  │④  │⑤  │⑥  │ │  │ Open: 15 (▲3)             │  │
│  │100│ 75│ 30│  0│  0│ │  │ Critical: 2  High: 5       │  │
│  │ % │ % │ % │ % │ % │ │  │ Medium: 8                  │  │
│  └───┴───┴───┴───┴───┘ │  │ Avg Age: 4.2 days          │  │
│                         │  └─────────────────────────────┘  │
│  Feature Gate Status    │  Issue Trend (4 weeks)            │
│  ┌─────────┬────┬────┐  │  ┌─────────────────────────────┐  │
│  │Feature  │Gate│Done│  │  │  ■ New  ■ Resolved ■ Open  │  │
│  │FEAT-001 │ 5/5│ ✅ │  │  │  W1: 8/5/15  W2: 6/7/14   │  │
│  │FEAT-002 │ 3/5│ 🔄 │  │  │  W3: 5/8/11  W4: 7/3/15   │  │
│  │FEAT-003 │ 1/5│ 🔄 │  │  └─────────────────────────────┘  │
│  └─────────┴────┴────┘  │                                   │
├─────────────────────────┴───────────────────────────────────┤
│  Schedule vs Delivery Matrix                                │
│  ┌──────────┬──────────┬──────────┐                         │
│  │ FEAT-001 │ ✅ Green  │ on-time + quality OK │            │
│  │ FEAT-002 │ ⚠️ Amber │ on-time but lint FAIL│            │
│  │ FEAT-003 │ 🔴 Red   │ delayed + quality NG │            │
│  └──────────┴──────────┴──────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 16. 次のアクション

### 16.1 即時アクション（Week 1-2）

1. 本提案書のレビュー（Architecture Board + PMO）
2. パイロットプロジェクトの選定
3. enterprise.yaml テンプレートの TEIM 対応拡張
4. SAP連携 API 仕様の確認
5. Jira連携 設定・フィールドマッピング定義

### 16.2 短期アクション（Month 1）

1. TEIM タスク → STRIDE テンプレート変換ツールの開発
2. PM向けダッシュボードのプロトタイプ作成
3. 3層可視性モデルのアクセス制御実装
4. チーム教育プログラムの策定・実施

### 16.3 中期アクション（Month 2-6）

1. パイロットプロジェクトでの実証
2. KPI収集と効果測定
3. テンプレート・ツールの改善
4. 全社展開計画の策定

---

> **End of TEIM v31.0 × Tecnos-STRIDE 統合バージョンアップ提案書 v2.0.0**
