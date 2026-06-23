# 04. Enterprise Edition ガイド

**3-5チーム規模の大規模開発向け拡張**

---

## このガイドで学ぶこと

1. Enterprise Edition の概要と標準版との違い
2. Epic/Feature 階層による要件分解
3. 階層化カバレッジ Tier（critical/standard/experimental）
4. 委任承認マトリクス
5. 共有契約レイヤーとチーム間調整
6. 依存管理とサイクル検出
7. 契約変更提案（CCP）ワークフロー
8. Enterprise ツールの使い方
9. クイックスタート

---

## 0. 5分クイックリファレンス（PM向け）

### Enterprise Edition とは

「**複数チームが1つの大きな機能を分担して開発する**」ための拡張です。

### 見るべき3つのポイント

| ポイント | 確認場所 | 判断基準 |
|---------|---------|---------|
| **Epic Gate 状態** | `EPIC_APPROVAL.md` | E1-E5 + Final が順次通過しているか |
| **Coverage Tier** | `basic_design.md` | critical/standard/experimental が適切か |
| **依存サイクル** | `dependency_checker` 出力 | サイクルがないか |

### PMが決めること

1. **Epic の承認**: E1-E5 + Final Gate の通過判定
2. **Tier の妥当性**: Feature の重要度に応じた Tier 設定の承認
3. **共有契約の変更**: CCP（契約変更提案）の最終承認

---

## 1. Enterprise Edition の概要

### 標準版との違い

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  【標準版】単一チーム・単一Feature                                          │
│  ─────────────────────────────────────────────────────────────────────      │
│                                                                             │
│   要件 → basic_design → spec → plan → tasks → 実装                         │
│                                                                             │
│   ・1つの Feature を1つのチームが担当                                       │
│   ・承認者は固定（PM または TECH_LEAD）                                     │
│   ・カバレッジポリシーは単一                                                │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  【Enterprise Edition】複数チーム・Epic/Feature階層                         │
│  ─────────────────────────────────────────────────────────────────────      │
│                                                                             │
│   大規模要件                                                                │
│        │                                                                    │
│        ▼                                                                    │
│   ┌─────────┐                                                               │
│   │  Epic   │  ← チーム横断の大きな単位                                     │
│   └────┬────┘                                                               │
│        │                                                                    │
│   ┌────┴────┬─────────┬─────────┐                                           │
│   ▼         ▼         ▼         ▼                                          │
│ Feature   Feature   Feature   Feature  ← 各チームが担当                    │
│ (TEAM-A)  (TEAM-A)  (TEAM-B)  (TEAM-C)                                      │
│                                                                             │
│   ・複数チームが Epic を分担                                                │
│   ・Tier に応じて承認者が変わる                                             │
│   ・チーム間の共有契約を一元管理                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### いつ Enterprise Edition を使うか

| 条件 | 標準版 | Enterprise Edition |
|------|--------|-------------------|
| チーム数 | 1チーム | 3-5チーム |
| Feature 数 | 1-3 | 4以上 |
| チーム間依存 | なし | あり |
| 共有契約 | なし | あり |

### 後方互換性

Enterprise Edition は標準版と完全に互換性があります：

- 既存の `specs/<feature>/` は変更なしで動作
- `epic_ref` がない Feature は Epic 検証をスキップ
- `coverage_tier` 未指定時は `standard` がデフォルト
- `--enterprise` フラグなしでは従来動作

### 有効化方法

Enterprise Hierarchy の CLI は `sdd-templates/config/enterprise.yaml` で明示的に有効化します。

```yaml
enterprise:
  enabled: true
```

この設定が有効なとき、`stride epic ...`、`stride init <feature> --epic ... [--team ...]`、`stride lint specs/<feature>/ --enterprise` / `stride lint --all --enterprise` が利用可能になります。

---

## 2. Epic/Feature 階層

### 階層構造

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                        Epic: EPIC-ORDER                                     │
│                     「受注管理システム」                                     │
│                             │                                               │
│         ┌───────────────────┼───────────────────┐                           │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│   ┌───────────┐       ┌───────────┐       ┌───────────┐                     │
│   │ Feature   │       │ Feature   │       │ Feature   │                     │
│   │FEAT-ORD-001│       │FEAT-ORD-002│       │FEAT-INV-001│                     │
│   │「受注登録」│       │「受注照会」│       │「在庫引当」│                     │
│   │ TEAM-ORD  │       │ TEAM-ORD  │       │ TEAM-INV  │                     │
│   │ critical  │       │ standard  │       │ critical  │                     │
│   └───────────┘       └───────────┘       └───────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### ディレクトリ構造

```
epics/
└── EPIC-ORDER/
    ├── epic_design.md           # Epic 設計（WHO/WHAT/WHY）
    ├── epic_flow.bpmn           # Epic overview（collaboration + participant）
    ├── feature_breakdown.md     # Feature 分割
    ├── EPIC_APPROVAL.md         # Epic Gate 承認記録
    ├── EPIC_PROGRESS_REPORT.md  # Epic 進捗サマリ
    ├── DEPENDENCY_MANIFEST.yaml # Feature 間依存
    └── OPS_PACK_REGISTRY.yaml   # Ops 準備状況

specs/
├── FEAT-ORD-001/                # 受注登録（TEAM-ORD）
│   ├── basic_design.md          # epic_ref: EPIC-ORDER
│   ├── process.bpmn             # laneSet ベース Feature BPMN
│   ├── spec.md                  #   team_id: TEAM-ORD
│   └── ...                      #   coverage_tier: critical
├── FEAT-ORD-002/                # 受注照会（TEAM-ORD）
└── FEAT-INV-001/                # 在庫引当（TEAM-INV）

shared/
└── contracts/
    └── CONTRACT_REGISTRY.yaml   # 共有契約レジストリ
```

### Git ブランチモデル（3 階層）

Enterprise Edition では、Epic/Feature の階層構造に対応した 3 階層ブランチモデルを採用します。

```
main                                                      ← 全体管理者がマージ
 └── epic/<EPIC-ID>                                       ← Epic リードがマージ
      ├── feature/<EPIC-ID>/<feature_name>                ← Feature 担当チームがマージ
      │    ├── symphony/<feature_name>-12  (Phase 1)
      │    ├── symphony/<feature_name>-13  (Phase 2)
      │    ├── symphony/<feature_name>-14  (Phase 3)
      │    └── symphony/<feature_name>-20  (WI-001)       ← Phase 4 は WI 単位
      └── feature/<EPIC-ID>/<other_feature>
```

| レベル | 命名規則 | 分岐元 | マージ先 | 管理者 |
|--------|---------|--------|---------|--------|
| Epic | `epic/<EPIC-ID>` | main | main | Epic リード |
| Feature | `feature/<EPIC-ID>/<name>` | epic ブランチ | epic ブランチ | Feature 担当 |
| Symphony (Phase 1-3) | `symphony/<name>-<issue>` | feature ブランチ | feature ブランチ | Symphony 自動 |
| Symphony (WI/Phase 4) | `symphony/<name>-<issue>` | feature ブランチ | feature ブランチ | Symphony 自動 |

Symphony を使用する場合、GitHub Issue テンプレートの **Base Branch** フィールドに Feature ブランチ名を指定します。
これにより、Symphony が作成する worktree ブランチは Feature ブランチから分岐し、PR も Feature ブランチに向けて作成されます。

### Epic 設計（epic_design.md）

```yaml
epic:
  meta:
    epic_id: "EPIC-ORDER"
    title: "受注管理システム"
    epic_lead: "山田花子"
    created: "2026-01-20"

  # WHO: 誰のため
  stakeholders:
    primary:
      - role: "営業担当者"
        need: "受注入力の効率化"
    secondary:
      - role: "物流担当者"
        need: "在庫引当の自動化"

  # WHAT: 何を実現
  objectives:
    - "Web-EDI からの受注を自動登録"
    - "在庫状況に応じた納期回答"
    - "ERP との即座連携"

  # WHY: なぜ必要
  business_value:
    - "受注処理時間を 50% 削減"
    - "入力ミスによる出荷遅延を 80% 削減"

  # チーム構成
  teams:
    - team_id: "TEAM-ORD"
      name: "受注チーム"
      features: ["FEAT-ORD-001", "FEAT-ORD-002"]
    - team_id: "TEAM-INV"
      name: "在庫チーム"
      features: ["FEAT-INV-001"]

  # マイルストーン
  milestones:
    - id: "EM-01"
      name: "設計完了"
      target_date: "2026-02-28"
    - id: "EM-02"
      name: "結合テスト開始"
      target_date: "2026-03-31"
```

### Feature Breakdown（feature_breakdown.md）

> **必須**: `feature_breakdown.md` は Epic 運用で**必須**のファイルです。
> - Gate E2 (Feature Breakdown Approval) で完成が確認されます
> - `epic_validator.py` は存在時のみ検証しますが、E2 承認には必須です
> - 依存サイクル検出（`dependency_checker.py`）もこのファイルを参照します

```yaml
feature_breakdown:
  epic_ref: "EPIC-ORDER"

  features:
    - feature_id: "FEAT-ORD-001"
      title: "Web-EDI 受注登録"
      team_id: "TEAM-ORD"
      coverage_tier: "critical"         # 決済に関わるため critical
      priority: 1
      dependencies:
        - depends_on: "FEAT-INV-001"
          type: "data"
          description: "在庫引当結果を参照"

    - feature_id: "FEAT-ORD-002"
      title: "受注照会画面"
      team_id: "TEAM-ORD"
      coverage_tier: "standard"         # 参照系のため standard
      priority: 2
      dependencies: []

    - feature_id: "FEAT-INV-001"
      title: "在庫引当エンジン"
      team_id: "TEAM-INV"
      coverage_tier: "critical"         # 在庫に影響するため critical
      priority: 1
      dependencies: []
```

---

## 3. 階層化カバレッジ Tier

### 3つの Tier

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  【critical】決済・認証・監査対象・ERP連携                                  │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  ・AC Coverage: 100%（全受入条件をテスト）                                  │
│  ・CT Coverage: 100%（全契約をテスト）                                      │
│  ・Code Coverage: LIB 85%/75%, CMP 70%/60%                                  │
│  ・E2E テスト: 必須                                                         │
│  ・承認者: ARCH_BOARD（アーキテクチャボード）                               │
│                                                                             │
│  例: 決済処理、認証、監査ログ、ERP 連携、個人情報処理                       │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  【standard】通常のビジネス機能                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  ・AC Coverage: 100%                                                        │
│  ・CT Coverage: 80%                                                         │
│  ・Code Coverage: LIB 70%/60%, CMP 60%/50%                                  │
│  ・E2E テスト: 任意                                                         │
│  ・承認者: PM + TECH_LEAD（Final Gate は共同承認）                          │
│                                                                             │
│  例: 一般的な CRUD 操作、レポート出力、検索機能                             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  【experimental】PoC・内部ツール・プロトタイプ                              │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  ・AC Coverage: 80%                                                         │
│  ・CT Coverage: 60%                                                         │
│  ・Code Coverage: LIB 50%/40%, CMP 40%/30%                                  │
│  ・E2E テスト: 不要                                                         │
│  ・承認者: TECH_LEAD                                                        │
│                                                                             │
│  例: PoC、内部ツール、プロトタイプ、実験的機能                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tier 選択のフローチャート

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  この機能は...                                                              │
│                                                                             │
│  決済・認証・監査対象・ERP連携・個人情報処理 に関わる？                      │
│       │                                                                     │
│       ├─ Yes → 【critical】                                                 │
│       │                                                                     │
│       └─ No                                                                 │
│            │                                                                │
│            ├─ 本番環境で使う一般的なビジネス機能？                           │
│            │       │                                                        │
│            │       ├─ Yes → 【standard】                                    │
│            │       │                                                        │
│            │       └─ No → 【experimental】                                 │
│            │                                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### basic_design.md での Tier 指定

```yaml
# specs/FEAT-ORD-001/basic_design.md
basic_design:
  meta:
    feature_id: "FEAT-ORD-001"
  epic_ref: "EPIC-ORDER"           # ← Epic への参照
  team_id: "TEAM-ORD"              # ← 担当チーム
  coverage_tier: "critical"        # ← カバレッジ Tier

  # エスカレーションフラグ（v1.2.6）
  # これらのフラグは approval_matrix.yaml のエスカレーションルールを発動します：
  # - security_sensitive + critical tier → SECURITY_OFFICER
  # - erp_integration (any tier) → ARCH_BOARD
  security_sensitive: false        # PII/認証/暗号化を扱う場合 true
  erp_integration: false           # ERP DB/API 直接連携の場合 true
```

### カバレッジポリシーの自動適用

`coverage_tier` を指定すると、`plan.md` のカバレッジポリシーが自動で適用されます：

```yaml
# plan.md（critical tier の場合）
test_strategy:
  coverage_policy:
    acceptance_coverage_target_pct: 100
    contract_coverage_target_pct: 100
    e2e_required: true
    code_coverage_targets:
      - scope: "LIB-*"
        line_pct: 85
        branch_pct: 75
      - scope: "CMP-*"
        line_pct: 70
        branch_pct: 60
```

---

## 4. 委任承認マトリクス

### 承認者の決定ルール

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                    委任承認マトリクス                                        │
│                                                                             │
│  ┌───────────────┬────────────┬────────────┬──────────────┐                 │
│  │ Gate          │ critical   │ standard   │ experimental │                 │
│  ├───────────────┼────────────┼────────────┼──────────────┤                 │
│  │ Basic Design  │ ARCH_BOARD │ TECH_LEAD  │ TECH_LEAD    │                 │
│  │ BPMN          │ ARCH_BOARD │ TECH_LEAD  │ TECH_LEAD    │                 │
│  │ Spec          │ ARCH_BOARD │ PM         │ TECH_LEAD    │                 │
│  │ Plan          │ ARCH_BOARD │ PM         │ TECH_LEAD    │                 │
│  │ Tasks         │ ARCH_BOARD │ PM         │ TECH_LEAD    │                 │
│  │ Final         │ ARCH_BOARD │ PM+TL 共同 │ TECH_LEAD    │                 │
│  └───────────────┴────────────┴────────────┴──────────────┘                 │
│                                                                             │
│  凡例:                                                                      │
│  ・ARCH_BOARD: アーキテクチャボード（組織レベル）                           │
│  ・PM: プロジェクトマネージャー（チームレベル）                             │
│  ・TECH_LEAD: テックリード（チームレベル）                                  │
│  ・PM+TL 共同: PM と TECH_LEAD の両方が承認必要                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### エスカレーションルール

特定の条件で自動的に上位承認者にエスカレーションされます：

| 条件 | エスカレーション先 |
|------|-------------------|
| `coverage_tier == 'critical'` | ARCH_BOARD |
| `cross_team_dependency == true` | ARCH_BOARD |
| `shared_contract_change == true` | ARCH_BOARD |
| `security_sensitive == true AND coverage_tier == 'critical'` | SECURITY_OFFICER |
| `erp_integration == true` | ARCH_BOARD |

### 承認ルーティングツール

```bash
# 必要な承認者を確認
python3 sdd-templates/tools/approval_router.py route specs/FEAT-ORD-001/ spec

# 出力例:
# Approval Routing for: FEAT-ORD-001
# ==================================================
# Coverage Tier: critical
# Gate Type: spec
# Required Approvers: ARCH_BOARD
# Co-Approvers: (none)

# 承認者の権限を検証（can_approve、escalation、co-approver の3つを検証）
python3 sdd-templates/tools/approval_router.py validate specs/FEAT-ORD-001/ spec PM

# 出力例:
# ❌ PM is not authorized for spec at critical tier. Required: ['ARCH_BOARD']

# 並列処理の可否を確認
python3 sdd-templates/tools/approval_router.py parallel specs/FEAT-ORD-001/ spec

# 出力例（standard/experimental tier の場合）:
# ✅ spec can be processed in parallel with: plan

# JSON 出力（CI/CD 連携用）
python3 sdd-templates/tools/approval_router.py route specs/FEAT-ORD-001/ spec --json
```

---

## 5. Epic Gate ワークフロー

### Epic Gate (E1-E5 + Final)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  E1: Epic Design Approval                                                   │
│  ════════════════════════════════════════════════════════════════════       │
│  目的: Epic 設計の確認（WHO/WHAT/WHY）                                      │
│  確認項目:                                                                  │
│  - [ ] epic_design.md の WHO/WHAT/WHY が明確                               │
│  - [ ] チーム構成と Feature 割り当てが適切                                  │
│  - [ ] 戦略的整合性が確認済み                                               │
│  - [ ] Epic Lead が任命済み                                                 │
│  承認者: EPIC_LEAD                                                          │
│                          │                                                  │
│                          ▼                                                  │
│  E2: Feature Breakdown Approval                                             │
│  ════════════════════════════════════════════════════════════════════       │
│  目的: Feature 分割の妥当性確認                                             │
│  確認項目:                                                                  │
│  - [ ] feature_breakdown.md が完成                                          │
│  - [ ] 各 Feature のスコープが明確                                          │
│  - [ ] Coverage Tier が適切に設定                                           │
│  - [ ] 依存グラフにサイクルがない                                           │
│  承認者: EPIC_LEAD                                                          │
│                          │                                                  │
│                          ▼                                                  │
│  E3: Shared Contract Approval                                               │
│  ════════════════════════════════════════════════════════════════════       │
│  目的: 共有契約の合意（チーム間調整）                                       │
│  確認項目:                                                                  │
│  - [ ] 全共有契約が定義済み                                                 │
│  - [ ] 契約オーナーチームが明確                                             │
│  - [ ] 消費者チームがレビュー・合意済み                                     │
│  - [ ] SLA が定義済み                                                       │
│  承認者: ARCH_BOARD + 各チーム確認                                          │
│                          │                                                  │
│                          ▼                                                  │
│  E4: Integration Plan Approval                                              │
│  ════════════════════════════════════════════════════════════════════       │
│  目的: クロスチーム統合計画の確認                                           │
│  確認項目:                                                                  │
│  - [ ] クロスチーム統合テストが定義済み                                     │
│  - [ ] テスト環境が準備済み（または計画あり）                               │
│  - [ ] 各チームのテスト責任が明確                                           │
│  承認者: EPIC_LEAD + 各チーム確認                                           │
│                          │                                                  │
│                          ▼                                                  │
│  E5: Feature Specs Ready                                                    │
│  ════════════════════════════════════════════════════════════════════       │
│  目的: 全 Feature の Spec 作成可能状態の確認                                │
│  確認項目:                                                                  │
│  - [ ] 全 Feature 依存が解決可能                                            │
│  - [ ] 共有契約が安定                                                       │
│  - [ ] 各チームが Spec 作成開始可能                                         │
│  承認者: EPIC_LEAD                                                          │
│                          │                                                  │
│                          ▼                                                  │
│  Final: Epic Integration Complete                                           │
│  ════════════════════════════════════════════════════════════════════       │
│  目的: Epic 全体の統合完了                                                  │
│  確認項目:                                                                  │
│  - [ ] 全 Feature が Final Gate 通過                                        │
│  - [ ] 全クロスチーム統合テストが成功                                       │
│  - [ ] 共有契約が本番デプロイ済み                                           │
│  - [ ] 全 Evidence Pack が収集済み                                          │
│  承認者: EPIC_LEAD + ARCH_BOARD                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Epic 検証ツール

```bash
# Epic 全体を検証
sdd-templates/bin/stride epic validate EPIC-ORDER

# 出力例:
# Epic Validation Results: EPIC-ORDER
# ==================================================
# Valid: ✅ Yes
#
# Counts:
#   total_features: 3
#   critical_features: 2
#   standard_features: 1
#   cross_team_dependencies: 2
#   shared_contracts: 2
#
# Gate Checks:
#   ⬜ E1_Epic_Design
#   ⬜ E2_Feature_Breakdown
#   ✅ all_features_have_team
#   ✅ no_dependency_cycles

# Gate 状態のみ確認
sdd-templates/bin/stride epic gates EPIC-ORDER

# Feature 一覧を確認
sdd-templates/bin/stride epic features EPIC-ORDER

# 進捗サマリを表示
sdd-templates/bin/stride epic progress EPIC-ORDER

# Markdown レポートとして保存
sdd-templates/bin/stride epic progress EPIC-ORDER --format markdown --output epics/EPIC-ORDER/EPIC_PROGRESS_REPORT.md
```

---

## 6. 共有契約レイヤー

### 共有契約とは

チーム間で使用する API やイベントの契約を一元管理する仕組みです。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  shared/contracts/                                                          │
│  ├── api/                                                                   │
│  │   └── SC-API-ORDER.yaml       # 受注 API 契約                           │
│  └── events/                                                                │
│      └── SC-EVT-INVENTORY.yaml   # 在庫イベント契約                        │
│                                                                             │
│  ┌─────────────┐                ┌─────────────┐                             │
│  │  TEAM-ORD   │  ──使用──→    │ SC-API-ORDER │  ←──提供──  │  TEAM-ORD   │ │
│  │ (消費者)    │                │   共有契約   │             │ (オーナー)  │ │
│  └─────────────┘                └─────────────┘             └─────────────┘ │
│                                        │                                    │
│                                        │                                    │
│  ┌─────────────┐                       │                                    │
│  │  TEAM-INV   │  ──使用──────────────┘                                    │
│  │ (消費者)    │                                                            │
│  └─────────────┘                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 共有契約の構造

```yaml
# shared/contracts/api/SC-API-ORDER.yaml
shared_contract:
  meta:
    contract_id: "SC-API-ORDER"
    type: "API"
    version: "1.0.0"
    status: "stable"
    owner_team: "TEAM-ORD"
    epic_ref: "EPIC-ORDER"

  description: |
    受注登録 API 契約。Web-EDI からの受注データを受け付ける。

  consumers:
    - team_id: "TEAM-INV"
      usage: "在庫引当時に受注情報を参照"
      contact: "inventory-team@example.com"

  sla:
    availability: "99.9%"
    response_time_p95_ms: 500
    rate_limit_per_minute: 1000

  spec_ref: "shared/contracts/api/openapi/order-api.yaml"

  change_policy:
    breaking_change_notice_days: 30
    deprecation_period_days: 90
    ccp_required: true
```

### 消費者一覧（CONSUMERS.yaml）

```yaml
# specs/FEAT-ORD-001/contracts/CONSUMERS.yaml
consumers:
  contract_id: "SC-API-ORDER"
  owner_team: "TEAM-ORD"

  consumer_teams:
    - team_id: "TEAM-INV"
      confirmed: true
      confirmed_by: "田中一郎"
      confirmed_date: "2026-01-20"
      usage_description: "在庫引当時に受注情報を参照"
```

---

## 7. 依存管理

### 依存グラフ

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FEAT-ORD-001 ──(data)──→ FEAT-INV-001                                      │
│       │                        │                                            │
│       │                        │                                            │
│       └──(api)──→ FEAT-ORD-002 ←──(api)──┘                                  │
│                                                                             │
│  依存タイプ:                                                                │
│  ・data: データ参照（在庫引当結果を参照）                                   │
│  ・api: API 呼び出し（受注 API を利用）                                     │
│  ・event: イベント購読（在庫変更イベントを購読）                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 依存サイクル検出

```bash
# 依存サイクルを検出
python3 sdd-templates/tools/dependency_checker.py check epics/EPIC-ORDER/

# 出力例（サイクルなし）:
# Dependency Check Results: EPIC-ORDER
# ==================================================
# Cycles: None
# Max Depth: 2
# Topological Order: ['FEAT-INV-001', 'FEAT-ORD-002', 'FEAT-ORD-001']

# 出力例（サイクルあり）:
# ❌ Cycle Detected: ['FEAT-A', 'FEAT-B', 'FEAT-C', 'FEAT-A']

# DOT グラフを生成
python3 sdd-templates/tools/dependency_checker.py graph epics/EPIC-ORDER/ --format dot

# 依存の深さを分析
python3 sdd-templates/tools/dependency_checker.py analyze epics/EPIC-ORDER/
```

### 依存マニフェスト

```yaml
# specs/FEAT-ORD-001/dependencies/dependency_manifest.yaml
dependency_manifest:
  feature_id: "FEAT-ORD-001"
  epic_ref: "EPIC-ORDER"

  depends_on:
    - dependency_id: "DEP-001"
      target_feature: "FEAT-INV-001"
      type: "data"
      description: "在庫引当結果を参照"
      critical: true
      interface:
        contract_ref: "SC-API-INVENTORY"

  provides_to:
    - dependency_id: "DEP-002"
      consumer_feature: "FEAT-ORD-002"
      type: "api"
      description: "受注データを提供"
      interface:
        contract_ref: "SC-API-ORDER"
```

---

## 8. 契約変更提案（CCP）ワークフロー

### CCP が必要なケース

| 変更タイプ | CCP 必要 | 理由 |
|-----------|---------|------|
| 破壊的変更（Breaking Change） | 必須 | 消費者への影響が大きい |
| 新規エンドポイント追加 | 不要 | 後方互換性あり |
| 必須パラメータ追加 | 必須 | 既存呼び出しが失敗する |
| オプションパラメータ追加 | 不要 | 後方互換性あり |
| レスポンス形式変更 | 必須 | 消費者のパースが失敗する |

### CCP ワークフロー

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  1. 契約オーナーが CCP 作成                                                 │
│     enterprise/change_proposals/CCP-001.md                                  │
│                          │                                                  │
│                          ▼                                                  │
│  2. lint / dependency ツールで影響範囲を確認                                │
│     ・stride lint specs/<feature>/ --enterprise                             │
│     ・dependency_checker.py analyze / check                                 │
│                          │                                                  │
│                          ▼                                                  │
│  3. 消費者チームに通知                                                      │
│     enterprise/notifications/CCP-001-notify.md                              │
│                          │                                                  │
│                          ▼                                                  │
│  4. 消費者チームが確認・承認                                                │
│     ・影響範囲の確認                                                        │
│     ・移行計画の合意                                                        │
│                          │                                                  │
│                          ▼                                                  │
│  5. ARCH_BOARD 最終承認                                                     │
│     ・全消費者の合意確認                                                    │
│     ・移行スケジュール確認                                                  │
│                          │                                                  │
│                          ▼                                                  │
│  6. 新バージョン実装                                                        │
│     ・v2 エンドポイント追加                                                 │
│     ・契約テスト更新                                                        │
│                          │                                                  │
│                          ▼                                                  │
│  7. 消費者移行                                                              │
│     ・各消費者チームが新バージョンに移行                                    │
│     ・移行完了を報告                                                        │
│                          │                                                  │
│                          ▼                                                  │
│  8. 旧バージョン廃止                                                        │
│     ・deprecation_period 経過後                                             │
│     ・v1 エンドポイント削除                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CCP テンプレート

```yaml
# enterprise/change_proposals/CCP-001.md
ccp:
  meta:
    ccp_id: "CCP-001"
    title: "受注 API v2 への移行"
    status: "proposed"  # proposed → under_review → approved → implemented → closed
    created: "2026-01-20"
    owner_team: "TEAM-ORD"

  contract_ref: "SC-API-ORDER"
  change_type: "breaking"

  description: |
    受注 API のレスポンス形式を変更し、納期情報を追加する。

  breaking_changes:
    - field: "response.delivery_date"
      change: "新規追加（必須フィールド）"
      impact: "消費者のパースロジック変更が必要"

  affected_consumers:
    - team_id: "TEAM-INV"
      impact_level: "high"
      migration_effort: "2日"

  migration_plan:
    v2_release_date: "2026-02-01"
    v1_deprecation_date: "2026-03-01"
    v1_removal_date: "2026-04-01"

  approvals:
    consumer_teams:
      - team_id: "TEAM-INV"
        approved: false
        approved_by: ""
        approved_date: ""
    arch_board:
      approved: false
      approved_by: ""
      approved_date: ""
```

---

## 9. Enterprise ツール一覧

### ツールサマリー

| ツール | 目的 | コマンド例 |
|--------|------|-----------|
| `stride epic validate` | Epic 検証 | `sdd-templates/bin/stride epic validate EPIC-ORDER` |
| `stride epic gates` | Epic Gate 状態表示 | `sdd-templates/bin/stride epic gates EPIC-ORDER` |
| `stride epic features` | Epic 配下 Feature 一覧 | `sdd-templates/bin/stride epic features EPIC-ORDER` |
| `stride epic progress` | Epic 進捗サマリ | `sdd-templates/bin/stride epic progress EPIC-ORDER` |
| `stride lint <path> --enterprise` | Feature の Enterprise 拡張検証 | `sdd-templates/bin/stride lint specs/FEAT-001/ --enterprise` |
| `dependency_checker.py` | 依存サイクル検出 | `dependency_checker.py check epics/EPIC-ORDER/` |
| `approval_router.py` | 承認ルーティング・権限検証・並列判定 | `approval_router.py route specs/FEAT-001/ spec` |
| `stride_lint_enterprise.py` | Enterprise lint 実装本体 | `python3 sdd-templates/tools/stride_lint_enterprise.py --test` |

#### approval_router.py サブコマンド

| サブコマンド | 説明 |
|-------------|------|
| `route` | 必要な承認者とCo-Approverを表示 |
| `validate` | 承認者の権限を検証（can_approve / escalation / co-approver） |
| `parallel` | Gate の並列処理可否を判定 |

オプション: `--json` で JSON 出力（CI/CD 連携用）

### セルフテスト

```bash
# 全ツールのセルフテスト
PY=sdd-templates/.venv/bin/python
[ -x "$PY" ] || PY=python3

"$PY" sdd-templates/tools/epic_validator.py --test
"$PY" sdd-templates/tools/approval_router.py --test
"$PY" sdd-templates/tools/dependency_checker.py --test
"$PY" sdd-templates/tools/stride_lint_enterprise.py --test
```

---

## 10. Enterprise ID 規約

### 新規 ID（Enterprise 拡張）

| カテゴリ | 形式 | 正規表現 | 例 |
|----------|------|---------|-----|
| Epic | `EPIC-[A-Z]{3,}` | `^EPIC-[A-Z]{3,}$` | EPIC-ORDER |
| Team | `TEAM-[A-Z]{1,3}` | `^TEAM-[A-Z]{1,3}$` | TEAM-ORD |
| Feature (Team prefix) | `FEAT-[A-Z]{2,4}-[A-Z0-9]{3,}` | `^FEAT-(?:[A-Z]{2,4}-)?[A-Z0-9]{3,}$` | FEAT-ORD-001 |
| Shared Contract | `SC-(API\|EVT\|FILE)-[A-Z0-9]{3,}` | `^SC-(API\|EVT\|FILE)-[A-Z0-9]{3,}$` | SC-API-ORDER |
| CCP | `CCP-[0-9]{3}` | `^CCP-[0-9]{3}$` | CCP-001 |
| Integration Point | `IP-[0-9]{3}` | `^IP-[0-9]{3}$` | IP-001 |
| Dependency | `DEP-[0-9]{3}` | `^DEP-[0-9]{3}$` | DEP-001 |
| Epic Milestone | `EM-[0-9]{2}` | `^EM-[0-9]{2}$` | EM-01 |

---

## 11. クイックスタート

### Step 1: Epic を作成

```bash
# Enterprise Hierarchy を有効化
cat > sdd-templates/config/enterprise.yaml <<'YAML'
enterprise:
  enabled: true
YAML

# Epic 一式を初期化
sdd-templates/bin/stride epic init EPIC-ORDER
```

### Step 2: Epic 設計を記入

```bash
# epic_design.md を編集
# - WHO/WHAT/WHY を記入
# - epic_flow.bpmn を編集（participant / messageFlow / documentation）
# - チーム構成を設定
# - マイルストーンを設定
```

### Step 3: Feature Breakdown を記入

```bash
# feature_breakdown.md を編集
# - Feature 一覧を定義
# - 各 Feature の team_id, coverage_tier を設定
# - 依存関係を定義
```

### Step 4: Epic を検証

```bash
# Epic 検証
sdd-templates/bin/stride epic validate EPIC-ORDER

# Gate 状態確認
sdd-templates/bin/stride epic gates EPIC-ORDER

# 依存サイクル検出
python3 sdd-templates/tools/dependency_checker.py check epics/EPIC-ORDER/
```

### Step 5: Feature を作成

```bash
# Feature を初期化（複数 team の Epic では --team 必須）
sdd-templates/bin/stride init FEAT-ORD-001 --epic EPIC-ORDER --team TEAM-ORD

# basic_design.md には以下が自動設定される
# - epic_ref: EPIC-ORDER
# - team_id: TEAM-ORD
#
# 追加で確認・設定する
# - coverage_tier: critical
# - security_sensitive: true/false（PII/認証/暗号化を扱う場合 true）
# - erp_integration: true/false（ERP 連携の場合 true）
```

### Step 6: Enterprise Lint を実行

```bash
# Enterprise Lint（単一 Feature）
sdd-templates/bin/stride lint specs/FEAT-ORD-001/ --enterprise

# Epic も含めて全体検証する場合
sdd-templates/bin/stride lint --all --enterprise

# 承認ルーティング確認
python3 sdd-templates/tools/approval_router.py route specs/FEAT-ORD-001/ basic_design

# 承認者の権限検証（オプション）
python3 sdd-templates/tools/approval_router.py validate specs/FEAT-ORD-001/ basic_design TECH_LEAD
```

---

## 12. よくあるエラーと対処

### Enterprise 固有エラー

| エラー | 原因 | 対処 |
|--------|------|------|
| `EPIC_REF_INVALID` | epic_ref が無効な形式 | `EPIC-XXX` 形式で指定 |
| `TEAM_ID_INVALID` | team_id が無効な形式 | `TEAM-X` 形式（1-3文字）で指定 |
| `COVERAGE_TIER_MISSING` | coverage_tier が未指定 | critical/standard/experimental のいずれかを指定 |
| `COVERAGE_TIER_INVALID` | coverage_tier が無効な値 | critical/standard/experimental のいずれかを指定 |
| `SHARED_CONTRACT_NOT_FOUND` | 参照した共有契約が存在しない | `shared/contracts/` を確認 |
| `DEPENDENCY_CYCLE_DETECTED` | 依存サイクルが検出された | `dependency_checker` で詳細確認 |
| `CROSS_TEAM_APPROVAL_REQUIRED` | クロスチーム変更に ARCH_BOARD 承認が必要 | ARCH_BOARD に承認依頼 |
| `EPIC_GATE_NOT_PASSED` | 必要な Epic Gate が未通過 | EPIC_APPROVAL.md で承認を取得 |

---

## 13. PM向けチェックリスト

### Epic 立ち上げ時

- [ ] Epic Lead が任命されている
- [ ] チーム構成と Feature 割り当てが明確
- [ ] 各 Feature の Coverage Tier が適切
- [ ] 依存グラフにサイクルがない
- [ ] マイルストーンが設定されている

### Gate 判定時

- [ ] E1: Epic 設計の WHO/WHAT/WHY が明確か
- [ ] E2: Feature 分割が適切か
- [ ] E3: 共有契約に全チームが合意しているか
- [ ] E4: 統合テスト計画が明確か
- [ ] E5: 全 Feature が Spec 作成可能か
- [ ] Final: 全 Feature が完了し、統合テストが成功しているか

### CCP 承認時

- [ ] 影響を受ける全チームが確認済み
- [ ] 移行計画が明確
- [ ] 廃止スケジュールが適切

---

## 次のステップ

→ [08. ID規約リファレンス](appendix_a_id_conventions.md) - Enterprise ID を含む全 ID 規約
→ [09. カバレッジポリシーガイド](19_coverage_policy.md) - Tier 別カバレッジの詳細
→ [10. stride-lint使用ガイド](appendix_b_stride_lint.md) - Enterprise Lint の詳細

---

> SDD Templates Manual - 15. Enterprise Edition Guide
