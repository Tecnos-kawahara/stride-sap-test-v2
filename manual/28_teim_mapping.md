# 28. TEIM/PMO マッピングガイド

> Tecnos-STRIDE と TEIM（テクノスエンタープライズ導入メソドロジー）の対応関係

---

## 1. 概要

### 1.1 TEIM とは

TEIM（Tecnos ERP Implementation Methodology）は、テクノスジャパンの
ERP 導入プロジェクト管理手法です。Tecnos-STRIDE は TEIM のフレームワーク内で
動作するよう設計されています。

### 1.2 マッピングの目的

| 目的 | 説明 |
|------|------|
| **ゲート整合** | TEIM の品質ゲートと STRIDE の Gate を対応付け |
| **成果物整合** | TEIM 要求成果物と STRIDE 成果物をマッピング |
| **レポーティング** | STRIDE の進捗を TEIM/PMO にレポート可能に |

---

## 2. ゲート対応表

### 2.1 TEIM ゲート → STRIDE Gate

| TEIM フェーズ | TEIM ゲート | STRIDE Gate | 主成果物 |
|--------------|------------|-------------|---------|
| **要件定義** | 要件確定 | Gate 1, 2 | basic_design.md, process.bpmn（必要に応じて epic_flow.bpmn） |
| **設計** | 設計品質 | Gate 3, 4 | spec.md, plan.md, contracts/ |
| **構築** | 構築完了 | Gate 5 + Run | tasks.md, work_items/, runs/ |
| **試験** | 試験完了 | Run + Final | test_results, evidence_pack |
| **移行** | 移行準備 | Final | ops/ (transport, rollback, hypercare) |
| **稼働** | 稼働判定 | Final 完了 | 全成果物完成 |

### 2.2 詳細マッピング

```
┌─────────────────────────────────────────────────────────────────┐
│  TEIM             STRIDE                                        │
├─────────────────────────────────────────────────────────────────┤
│  要件定義         Gate 1: basic_design.md                       │
│                   Gate 2: process.bpmn                          │
├─────────────────────────────────────────────────────────────────┤
│  設計             Gate 3: spec.md (AC/NFR)                      │
│                   Gate 4: plan.md (Contracts/Tests)             │
├─────────────────────────────────────────────────────────────────┤
│  構築/試験        Gate 5: tasks.md + Work Item 初期化           │
│                   Run: 実装 → walkthrough → CI → Done           │
├─────────────────────────────────────────────────────────────────┤
│  移行/稼働        Final: evidence_pack + ops pack               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 成果物マッピング

### 3.1 TEIM 成果物 → STRIDE 成果物

| TEIM 成果物 | STRIDE 成果物 | 説明 |
|------------|--------------|------|
| 要件定義書 | basic_design.md | 目的・範囲・統合点 |
| 業務フロー図 | process.bpmn / epic_flow.bpmn | FEAT 実装フローと EPIC 連携概観 |
| 機能仕様書 | spec.md | AC（受入条件）と NFR |
| 詳細設計書 | plan.md + contracts/ | テスト戦略と契約定義 |
| テスト仕様書 | tests/scenarios.yaml | テストシナリオ |
| テスト結果 | runs/*/test_results.md | テスト実行結果 |
| 移行計画書 | ops/transport_manifest.yaml | 輸送マニフェスト |
| 運用手順書 | ops/hypercare_runbook.md | ハイパーケア手順 |

### 3.2 追加の STRIDE 成果物

TEIM には直接対応がないが、STRIDE で必須の成果物：

| STRIDE 成果物 | 目的 | TEIM での位置づけ |
|--------------|------|------------------|
| work_items/*.md | 変更単位の追跡 | 構築管理台帳に相当 |
| state/state.yaml | 進捗の単一真実源 | WBS 進捗に相当 |
| runs/*/walkthrough.md | 実行証跡 | レビュー記録に相当 |
| APPROVAL.md | Gate 承認記録 | 品質ゲート承認に相当 |

---

## 4. PMO レポーティング

### 4.1 進捗レポート

STRIDE の状態を PMO 向けに変換：

```markdown
## 週次進捗レポート

### Gate 進捗
- Gate 1-4: ✅ 完了
- Gate 5: ✅ 完了
- Final: 🔄 進行中

### Work Item 進捗
| Status | 件数 | 割合 |
|--------|------|------|
| done | 8 | 53% |
| in_progress | 3 | 20% |
| pending_* | 4 | 27% |

### Mode 分布
- autopilot: 6件（低リスク）
- confirm: 5件（中リスク）
- validate: 4件（高リスク）

### リスク・課題
- [高] WI-003: validate モード、Ops レビュー待ち
```

### 4.2 GitHub Projects からのレポート

Projects の Insights を活用：

1. **バーンダウンチャート**: 残 WI 数の推移
2. **Status 分布**: 現在の進捗状況
3. **Mode 分布**: リスク傾向

### 4.3 コマンドラインでのレポート生成

```bash
# ローカルデータからレポート用情報を取得
python scripts/sync_stride_to_projects.py --local-only --all

# 出力例:
# Feature: my_erp_addon
#   - WI-001: done (mode=autopilot)
#   - WI-002: pending_ci (mode=confirm)
#   - WI-003: in_progress (mode=validate)
```

---

## 5. FB/是正管理

### 5.1 TEIM の FB 管理 → STRIDE

| TEIM | STRIDE | 説明 |
|------|--------|------|
| フィードバック | walkthrough.md の Notes | レビュー指摘を記録 |
| 是正対応 | 新規 Work Item | 是正は新しい WI として追跡 |
| 横展開 | ByteRover (brv curate) | 学習内容をナレッジ化 |

### 5.2 FB 記録テンプレート

```markdown
# Walkthrough: WI-ERP-FEAT-001

## Notes (FB/是正)

### レビュー指摘
- [FB-001] 入力チェックが不足 → WI-002 で対応
- [FB-002] エラーメッセージが不親切 → 本 WI 内で修正

### 横展開事項
- 入力チェックパターンを共通化 → brv curate 済み
```

---

## 6. リスク管理

### 6.1 STRIDE risk_flags と TEIM リスク分類

| STRIDE risk_flag | TEIM リスク分類 | 対応モード |
|------------------|----------------|-----------|
| authz, sod | セキュリティリスク | validate |
| accounting_calc | 業務リスク（会計） | validate |
| inventory_valuation | 業務リスク（在庫） | validate |
| data_migration | 移行リスク | validate |
| performance_sensitive | 性能リスク | confirm |
| new_api | 技術リスク | confirm |

### 6.2 リスクレポート

```markdown
## リスク一覧

### 高リスク（validate モード）
| WI ID | risk_flags | Status | 対策 |
|-------|-----------|--------|------|
| WI-003 | authz, audit_log | pending_ops | TL + Ops 合同レビュー |
| WI-007 | accounting_calc | in_progress | 会計チーム確認中 |

### 中リスク（confirm モード）
| WI ID | risk_flags | Status | 対策 |
|-------|-----------|--------|------|
| WI-005 | new_api | done | API 仕様レビュー完了 |
```

---

## 7. 実践例

### 7.1 TEIM マイルストーンと STRIDE の対応

```
TEIM: 要件定義完了 (M1)
  └─ STRIDE: Gate 1, 2 承認完了

TEIM: 設計完了 (M2)
  └─ STRIDE: Gate 3, 4 承認完了

TEIM: 構築完了 (M3)
  └─ STRIDE: Gate 5 承認 + 全 WI が done

TEIM: 試験完了 (M4)
  └─ STRIDE: Final 承認（evidence_pack 完成）

TEIM: 稼働判定 (M5)
  └─ STRIDE: ops pack 完成、ハイパーケア準備完了
```

### 7.2 PMO 報告時のチェックリスト

```markdown
## PMO 報告チェックリスト

### Gate 状況
- [ ] Gate 1-5 の承認状況を確認
- [ ] APPROVAL.md の承認者・日付を確認
- [ ] 未承認 Gate があればエスカレーション

### WI 進捗
- [ ] state.yaml の status を集計
- [ ] pending_* の WI を特定
- [ ] ブロッカーがあれば報告

### リスク
- [ ] validate モードの WI を確認
- [ ] 高リスク WI の対策状況を報告
```

---

## 8. ベストプラクティス

### 8.1 TEIM ゲートレビュー前の準備

1. `stride lint` を実行して全エラーを解消
2. APPROVAL.md の該当 Gate が承認済みか確認
3. 成果物の完全性をチェック

### 8.2 PMO 向けレポートの自動化

1. GitHub Projects の Insights を活用
2. 定期的に `sync_stride_to_projects.py` を実行
3. Projects のビューを PMO 向けにカスタマイズ

### 8.3 横展開の仕組み化

1. Walkthrough に横展開事項を記録
2. `brv curate` でナレッジ化
3. 定期的にナレッジをレビュー

---

## 関連ドキュメント

- [Tecnos-STRIDE メソッド](27_erp_addon_playbook.md)
- [RACI+ (AI時代の責務分担)](16_raci_plus.md)
- [GitHub Projects 連携ガイド](26_github_projects_guide.md)
- [Enterprise ガイド](04_enterprise_guide.md)
