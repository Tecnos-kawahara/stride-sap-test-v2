# 35. Retrospective Report ガイド

> **対象**: Feature / Epic の完了後にデータ駆動のふりかえりを行いたい PM・開発者
> **所要時間**: 約10分
> **バージョン**: v4.9.0

---

## 5分クイックリファレンス（PM向け）

**v4.9 で何が変わったか**:
- `stride retro` コマンドで Feature / Epic の定量ふりかえりレポートを自動生成
- Phase 間の所要時間、WI 統計、テスト、教訓数、ボトルネック分析を **1 コマンド** で取得
- Epic 横断で「最長 Phase」「最多 retry WI」を特定し、改善アクションにつなげる

**PM が確認すべきこと**:
- ボトルネック Phase はどこか
- retry が多い WI は何か（validate mode の WI に集中していないか）
- 教訓が十分にキャプチャされているか

---

## 1. 概要

### 1.1 なぜ定量ふりかえりが必要か

SDD の Phase Gate と WI/Run モデルは、開発プロセスの全データを成果物として残します。
`stride retro` はこれらの既存データを集約し、定量的なふりかえりレポートを自動生成します。

「なぜこの Phase が長かったのか」「なぜこの WI は retry が多かったのか」を
データに基づいて議論できるようになります。

### 1.2 gstack からの着想

gstack（garrytan/gstack, MIT License）の `/retro` コマンドが持つ定量レポートの考え方を取り込みました。

---

## 2. 使い方

### 2.1 Feature レベル

```bash
stride retro specs/<feature>/
```

### 2.2 Epic レベル（横断集計）

```bash
stride retro epics/<EPIC_ID>/
```

Epic の場合、`epic_design.md` の `epic.features[].feature_id` を辿って対応する `specs/<FEATURE_ID>/` を集計します。

### 2.3 JSON 出力

```bash
stride retro specs/<feature>/ --json
```

### 2.4 セルフテスト

```bash
stride retro --test    # 6 テスト実行
```

---

## 3. 収集メトリクス

### 3.1 Phase Durations（所要時間）

`APPROVAL.md` の Gate 承認日付から Phase 間の所要時間を算出します。

| 区間 | 計算 |
|------|------|
| Design → Specify | Gate 1 → Gate 3 |
| Specify → Tasking | Gate 3 → Gate 5 |
| Tasking → Execute | Gate 5 → Final |
| Total lead time | 最初の Gate → 最後の Gate |

日付フォーマットは `日付: YYYY-MM-DD`（標準）と `Date: YYYY-MM-DD`（後方互換）の両方をサポートします。

### 3.2 WI Statistics（Work Item 統計）

`state/state.yaml` の `work_items` 配列から集計:

- **合計 WI 数**
- **Mode 別内訳**: autopilot / confirm / validate / other
- **Status 別内訳**: done / pending / in_progress / blocked / other
- **平均 attempts/WI**: `runs/` 配下の RUN ディレクトリ総数 / WI 総数
- **WI 別 attempt 数**: 各 WI の RUN ディレクトリ数（降順ソート）

### 3.3 Test Statistics（テスト統計）

- `tests/scenarios.yaml` のシナリオ数
- `spec.md` の AC 総数に対する `covers_ac` カバレッジ

### 3.4 Lessons（教訓数）

`runs/**/.planning/lessons.md` から以下の 4 カテゴリを自動カウント:

| カテゴリ | セクションヘッダ |
|---------|----------------|
| best_practice | `## Best Practices` |
| trouble | `## Troubles` |
| technical | `## Technical Knowledge` |
| reusable_pattern | `## Reusable Patterns` |

### 3.5 Spec Changes（仕様変更数）

`implementation-details/change_log.md` のエントリ数をカウントします。

---

## 4. Insights（自動分析）

### 4.1 Feature レベル

| Insight | 条件 |
|---------|------|
| **Bottleneck phase** | 3 区間のうち最も長い Phase を特定 |
| **Highest retry WI** | 最多 RUN 数の WI を ID・attempts・mode 付きで報告 |
| **Recommendation** | validate mode の WI が retry 多の場合、事前 design_diff/authz review 強化を提案 |

### 4.2 Epic レベル

Feature 横断で以下を集計:

| Insight | 内容 |
|---------|------|
| **Longest phase** | 全 Feature のうち最長の Phase（Feature 名付き） |
| **Highest retry WI** | 全 Feature のうち最多 retry の WI（Feature 名付き） |

---

## 5. 出力例

### Feature レベル

```
=== STRIDE Retro: specs/order_import/ ===

Phase Durations
  Design  -> Specify:  2d 4h
  Specify -> Tasking:  1d 2h
  Tasking -> Execute:  3d 6h
  Total lead time:     6d 12h

Work Items
  Total: 8 | autopilot: 5 | confirm: 2 | validate: 1
  Done: 7 | Pending: 1 | In Progress: 0 | Blocked: 0
  Avg attempts/WI: 1.3

Tests
  Scenarios: 12 | ACs covered: 5/5 (100%)

Lessons
  Captured: 6 (best_practice: 3, trouble: 2, technical: 1)

Spec Changes
  Change log entries: 2

Insights
  - Bottleneck phase: Tasking -> Execute (3d 6h)
  - Highest retry WI: WI-ERP-ORD-003 (3 attempts, mode: validate)
  - Recommendation: validate mode の WI が retry 多 → 事前 design_diff / authz review 強化を検討
```

### Epic レベル

```
=== STRIDE Retro (Epic): epics/EPIC-ORDER/ ===
Features: 3 (FEAT-ORD-IMPORT, FEAT-ORD-APPROVE, FEAT-ORD-REPORT)

Aggregate
  Total WIs: 12
  Total scenarios: 28
  AC coverage: 15/15 (100.0%)
  Total lessons: 14
  Total change entries: 3

Insights
  - Longest phase: Tasking -> Execute (3d 6h) in FEAT-ORD-IMPORT
  - Highest retry WI: WI-ERP-ORD-003 (3 attempts, mode: validate) in FEAT-ORD-IMPORT

--- Feature: specs/FEAT-ORD-IMPORT/ ---
  (Feature レベルのレポートが続く)
```

---

## 6. ワークフロー統合

### 推奨タイミング

| タイミング | コマンド | 用途 |
|-----------|---------|------|
| Feature 完了後 | `stride retro specs/<feature>/` | 個別ふりかえり |
| Sprint / イテレーション終了時 | `stride retro epics/<EPIC_ID>/` | チーム横断ふりかえり |
| Release 前 | `stride retro epics/<EPIC_ID>/ --json` | メトリクス記録 |

### ふりかえり会議での活用

1. `stride retro` の出力をチームに共有
2. **Bottleneck phase** → なぜ長かったか議論
3. **Highest retry WI** → 何が原因で retry したか分析
4. **Lessons** → 教訓が十分にキャプチャされているか確認
5. アクションアイテムを次のイテレーションに反映

---

## 7. テスト

セルフテスト 6 件 + integration テスト 8 件:

```bash
stride retro --test                                       # セルフテスト
python3 -m pytest tests/test_retro_integration.py -v      # integration テスト
```

---

> **Inspired by**: gstack /retro quantitative retrospective (garrytan/gstack, MIT License)
