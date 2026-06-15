# 📊 STRIDE SDD Board — PM向け操作ガイド

> **Tecnos-STRIDE SDD Board を使ったプロジェクト管理の実践ガイド**
> 
> このドキュメントでは、PMの1日の業務フローに沿って、STRIDE SDD Board の6つのビューをどう活用するかをシナリオ形式で解説します。

---

## 🎯 STRIDE SDD Board とは

STRIDE SDD Board は、SDD（Specification-Driven Development）のプロジェクト管理を GitHub Projects V2 上で行うためのダッシュボードです。

AIが自律的にコーディングを進める SDD において、**PMが「今何が起きているか」を素早く把握し、適切なタイミングで意思決定を行う**ための仕組みです。

### 6つのビュー

| ビュー | レイアウト | 用途 |
|--------|----------|------|
| 📊 **Overview** | Table / Board / Roadmap | 全体進捗の一覧。全アイテムを俯瞰 |
| 🔬 **Findings** | Table | AIが発見した問題・課題の一覧 |
| 🔍 **Decisions** | Table | 重要な判断が多い Work Item の一覧 |
| 🔄 **Spec Impact** | Board | 仕様変更が必要な Work Item のトリアージ |
| 📚 **Learnings** | Table | 再利用可能なパターン・知見の一覧 |
| 📜 **Amendments** | Board | 仕様改訂（Amendment）のライフサイクル管理 |

### アクセス方法

```
https://github.com/orgs/tecnos-japan-cbp/projects/2
```

---

## 🌅 PMの1日 — シナリオで学ぶ STRIDE Board

### 登場人物

- **田中PM** — Salesforce連携プロジェクトの PM
- **Claude Code** — SDD に基づいてコーディングを行う AI

---

### 09:00 — 朝の進捗確認

田中PMは出社後、まず **📊 Overview** ビューを開きます。

#### 📊 Overview でやること

全体を俯瞰して「今日対応が必要なもの」を把握します。

```
📊 Overview ビュー
┌──────────────────────────────────────────┬────────────┬───────────┬──────────┐
│ Title                                    │ Status     │ SDD Gate  │ SDD Mode │
├──────────────────────────────────────────┼────────────┼───────────┼──────────┤
│ [EPIC] EPIC-SF: Salesforceリアルタイム連携 │ In Progress│           │          │
│ [MS] SF-01: OAuth認証・基本同期完了       │ Done       │           │          │
│ [MS] SF-02: 双方向リアルタイム同期完了     │ In Progress│           │          │
│ [WI] WI-SF-001: OAuth2認証フロー実装      │ Done       │ Final     │ autopilot│
│ [WI] WI-SF-002: 商談データ双方向同期      │ In Progress│ Gate 5    │ confirm  │ ← 🔴
│ [WI] WI-SF-003: コンフリクト解決ロジック   │ In Progress│ Gate 5    │ validate │ ← 🟡
│ [RISK] SF-R001: APIレートリミット超過      │ In Progress│           │          │
│ [AMD] AMD-SF-001: 通貨コードフィールド追加 │ In Progress│           │          │ ← 📜
└──────────────────────────────────────────┴────────────┴───────────┴──────────┘
```

**田中PMの確認ポイント：**
- ✅ WI-SF-001 は Done（完了）→ 問題なし
- 🔴 WI-SF-002 は Gate 5 で止まっている → 何か問題がありそう
- 🟡 WI-SF-003 も Gate 5 → 確認が必要
- 📜 Amendment が1件ある → 後で対応

> 💡 **Tips:** Status カラムでソートすると「In Progress」のアイテムが上に来て、対応が必要なものを素早く見つけられます。

---

### 09:15 — 問題の深掘り

Overview で WI-SF-002 が気になった田中PMは、**🔬 Findings** ビューに切り替えます。

#### 🔬 Findings でやること

AIが実装中に発見した問題（Findings）の多さで、**どの Work Item に注意が必要か**を判断します。

```
🔬 Findings ビュー
┌──────────────────────────────────────────┬──────────────┬─────────────┐
│ Title                                    │ Findings     │ Status      │
├──────────────────────────────────────────┼──────────────┼─────────────┤
│ [WI] WI-SF-002: 商談データ双方向同期      │ findings:4+  │ In Progress │ ← ⚠️ 要注意
│ [WI] WI-ERP-001: 受注登録画面のUI改善     │ findings:1-3 │ Done        │
│ [WI] WI-SF-001: OAuth2認証フロー実装      │ findings:1-3 │ Done        │
│ [WI] WI-SF-003: コンフリクト解決ロジック   │ findings:1-3 │ Done        │
└──────────────────────────────────────────┴──────────────┴─────────────┘
```

**ラベルの読み方：**

| ラベル | 意味 | PMのアクション |
|--------|------|--------------|
| `findings:0` | 問題なし | 特になし |
| `findings:1-3` | 軽微な問題あり | Issue コメントで内容を確認 |
| `findings:4+` | 多数の問題あり | **要注意！** 詳細を確認して対処を検討 |

**田中PMの判断：**

> WI-SF-002 だけ `findings:4+` か。Issue を開いて Run Report を見てみよう。

Issue #17 を開くと、Claude Code が投稿した **Run Report** が表示されます：

```
🏃 Run Complete: RUN-20260213-0900

📋 Findings (5件)
┌───┬──────────────┬─────────────────────────────────────────────┬────────┐
│ # │ 種別         │ 発見内容                                     │ 影響度 │
├───┼──────────────┼─────────────────────────────────────────────┼────────┤
│F-1│ schema       │ 通貨コード情報の欠落                          │ high   │
│F-2│ schema       │ カスタムフィールドの動的マッピング不可           │ high   │
│F-3│ schema       │ 多通貨対応の未考慮                            │ medium │
│F-4│ performance  │ バルク同期時のメモリ超過                       │ medium │
│F-5│ data_quality │ ステージ名の表記揺れ                          │ low    │
└───┴──────────────┴─────────────────────────────────────────────┴────────┘
```

> F-1〜F-3 が schema 系で影響度 high... これは仕様変更が必要だな。

---

### 09:30 — 仕様変更の影響を確認

田中PMは **🔄 Spec Impact** ビューに切り替えます。

#### 🔄 Spec Impact でやること

**仕様変更が必要な Work Item** を、緊急度別に3カラムで視覚的にトリアージします。

```
🔄 Spec Impact ビュー（Board形式）
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ Todo                │ In Progress         │ Done                │
│ (0)                 │ (2)                 │ (0)                 │
│                     │                     │                     │
│                     │ ┌─────────────────┐ │                     │
│                     │ │ WI-SF-002       │ │                     │
│                     │ │ 商談データ双方向  │ │                     │
│                     │ │ 同期             │ │                     │
│                     │ │ spec-impact:     │ │                     │
│                     │ │ required 🔴     │ │                     │
│                     │ └─────────────────┘ │                     │
│                     │                     │                     │
│                     │ ┌─────────────────┐ │                     │
│                     │ │ WI-SF-003       │ │                     │
│                     │ │ コンフリクト解決  │ │                     │
│                     │ │ ロジック         │ │                     │
│                     │ │ spec-impact:     │ │                     │
│                     │ │ proposed 🟡     │ │                     │
│                     │ └─────────────────┘ │                     │
│                     │                     │                     │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

**ラベルの読み方：**

| ラベル | 意味 | 色 | PMのアクション |
|--------|------|----|--------------|
| `spec-impact:none` | 仕様変更不要 | — | このビューには表示されない |
| `spec-impact:proposed` | 仕様変更を提案中 | 🟡 | 内容を確認し、必要なら Amendment を起案 |
| `spec-impact:required` | 仕様変更が必須 | 🔴 | **ブロッカー！** 早急に Amendment を起案 |

**田中PMの判断：**

> WI-SF-002 が `required`（必須）で、WI-SF-003 が `proposed`（提案中）。
> WI-SF-002 は仕様を変更しないと先に進めない。Amendment を確認しよう。

---

### 09:45 — Amendment（仕様改訂）の対応

田中PMは **📜 Amendments** ビューに切り替えます。

#### 📜 Amendments でやること

仕様改訂のライフサイクルを **draft → review → applying → applied** の4段階で管理します。

```
📜 Amendments ビュー（Board形式）
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ draft        │ review       │ applying     │ applied      │
│ 起案済み      │ レビュー中    │ Spec PR中    │ 反映完了      │
│ (0)          │ (1)          │ (0)          │ (0)          │
│              │              │              │              │
│              │ ┌──────────┐ │              │              │
│              │ │AMD-SF-001│ │              │              │
│              │ │商談同期の │ │              │              │
│              │ │通貨コード │ │              │              │
│              │ │フィールド │ │              │              │
│              │ │追加       │ │              │              │
│              │ └──────────┘ │              │              │
│              │              │              │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**Amendment のライフサイクル：**

```
PM/AIが起案     PMがレビュー      PM承認→Spec反映PR   PRマージ→WI起票
 ┌────────┐    ┌────────┐       ┌────────────┐     ┌────────┐
 │ draft  │ →  │ review │  →   │ applying   │  →  │ applied│
 └────────┘    └────────┘       └────────────┘     └────────┘
  起案中         承認待ち        Spec PR レビュー中    完了
```

**田中PMの操作：**

Issue #21（AMD-SF-001）を開くと、Amendment の詳細が表示されます：

```markdown
📜 Amendment: 商談同期の通貨コードフィールド追加

AMD ID: AMD-SF-001
Feature: FEAT-SF-CONN

### 変更概要
通貨コード情報の欠落を解決するため、通貨コードフィールドを追加する。

### 根拠となる Findings
- [ ] WI-SF-002 F-1: フィールドマッピング不整合（通貨コード欠落）
- [ ] WI-SF-002 F-3: 多通貨対応の未考慮

### 変更内容
| ファイル   | セクション | 変更内容                                    |
|-----------|-----------|-------------------------------------------|
| spec.md   | AC-SF-002 | currency_code フィールド（ISO 4217）を追加    |
| plan.md   | NFR-003   | 「多通貨対応は Phase 2」の明記               |

### 承認
- [ ] PM承認        ← ここにチェックを入れる！
- [ ] Tech Lead承認
```

**田中PMの操作：**

1. 変更内容を確認 → 妥当と判断
2. `- [ ] PM承認` を `- [x] PM承認` に編集
3. Claude Code が自動で Spec 反映 PR を作成（`apply`）
4. PR をレビューし、Amendment マーカーを正式な仕様文言に編集
5. PR をマージ
6. Claude Code が `finalize` で新WI起票 + Amendment close

> **PMが行うのは承認とPRレビューのみ。**
> Spec パッチ・PR作成・WI起票・ラベル管理はすべて自動化されます。

---

### 10:00 — 新しい Amendment を起案したい場合

田中PMが「WI-SF-003 のタイムスタンプ精度の問題も仕様変更したい」と判断した場合：

#### Claude Code との対話で Amendment を作成

```
田中PM: 「WI-SF-003 のタイムスタンプ精度の問題、仕様変更を検討したい」

Claude Code: 影響分析を実行します...

  📊 Amendment Impact Analysis
  
  Feature: FEAT-SF-CONN
  Topic: タイムスタンプ精度
  
  関連 Findings (1件)
  ┌────────┬───┬─────────────┬──────────────────────────────┬────────┐
  │ WI     │ # │ 種別        │ 内容                          │ 影響度 │
  ├────────┼───┼─────────────┼──────────────────────────────┼────────┤
  │WI-SF-003│F-1│compatibility│ タイムスタンプ精度の差異（秒vs │ medium │
  │        │   │             │ ミリ秒）                      │        │
  └────────┴───┴─────────────┴──────────────────────────────┴────────┘
  
  💡 AI 推奨:
  コンフリクト検知にタイムスタンプ+レコードハッシュの
  併用を提案します。spec.md AC-SF-003 にハッシュ比較
  ロジックの追加が必要です。

田中PM: 「ハッシュ併用でOK。ただしハッシュ対象フィールドは
         設定可能にして」

Claude Code: 了解しました。ドラフトを修正します...
         （ドラフト提示）

田中PM: 「これでOK。Issue 作って」

Claude Code: Amendment Issue を作成しました。
         → Issue #22: [AMD] AMD-SF-CONN-002
         → ラベル: amendment:draft
         → Project に追加済み
```

**ポイント：**
- PMは方向性を示すだけ
- データ収集・分析・ドラフト作成はAIが自動実行
- PMが「これでOK」と言うまで Issue は作成されない
- 承認チェックボックスは常に人間が操作

---

### 14:00 — 判断の多い Work Item を確認

午後、田中PMは **🔍 Decisions** ビューを確認します。

#### 🔍 Decisions でやること

AIが実装中に多くの判断（Decisions）を行った Work Item を特定し、**その判断が適切だったか**をレビューします。

```
🔍 Decisions ビュー
┌──────────────────────────────────────────┬──────────────┬──────────┐
│ Title                                    │ Decisions    │ SDD Mode │
├──────────────────────────────────────────┼──────────────┼──────────┤
│ [WI] WI-ERP-001: 受注登録画面のUI改善     │ decisions:4+ │ autopilot│
│ [WI] WI-SF-002: 商談データ双方向同期      │ decisions:4+ │ confirm  │ ← 要確認
└──────────────────────────────────────────┴──────────────┴──────────┘
```

**ラベルの読み方：**

| ラベル | 意味 | PMのアクション |
|--------|------|--------------|
| `decisions:0` | 判断なし（シンプルな実装） | 特になし |
| `decisions:1-3` | 少数の判断 | 必要に応じて確認 |
| `decisions:4+` | 多数の判断 | **要確認！** 判断内容をレビュー |

**田中PMの確認：**

> WI-SF-002 は `decisions:4+` で Mode が `confirm`。
> confirm モードは「AIが判断を記録し、人間が確認する」モード。
> Issue の Run Report で Decisions の内容を確認しよう。

Issue #17 の Run Report を確認：

```
📝 Decisions (6件)
┌───┬──────────────────────────────────────────────┬──────────┐
│ # │ 判断内容                                      │ ステータス│
├───┼──────────────────────────────────────────────┼──────────┤
│D-1│ Streaming API（PushTopic）を採用               │ accepted │
│D-2│ 単一通貨を先行、多通貨は Phase 2               │ proposed │ ← spec変更待ち
│D-3│ バッチサイズを configurable 化（デフォルト1000）│ accepted │
│D-4│ フィールドマッピングをテナント別定義に変更       │ proposed │ ← spec変更待ち
│D-5│ ステージ名正規化テーブルを導入                  │ accepted │
│D-6│ 初期同期はストリーミング処理に変更              │ accepted │
└───┴──────────────────────────────────────────────┴──────────┘
```

> D-2 と D-4 が `proposed`（spec変更待ち）。これは AMD-SF-001 で対応中だな。

---

### 16:00 — ナレッジの蓄積確認

夕方、田中PMは **📚 Learnings** ビューを確認します。

#### 📚 Learnings でやること

AIが実装中に発見した**再利用可能なパターンや知見**を確認し、チーム内でナレッジを共有します。

```
📚 Learnings ビュー
┌──────────────────────────────────────────┬──────────────┬──────────────────────────┐
│ Title                                    │ Learning     │ パターン名               │
├──────────────────────────────────────────┼──────────────┼──────────────────────────┤
│ [WI] WI-ERP-001: 受注登録画面のUI改善     │ learning:    │ Form Validation Pattern  │
│                                          │ pattern      │                          │
│ [WI] WI-SF-001: OAuth2認証フロー実装      │ learning:    │ Secure OAuth2 Token      │
│                                          │ pattern      │ Manager                  │
│ [WI] WI-SF-003: コンフリクト解決ロジック   │ learning:    │ Conflict Resolution with │
│                                          │ pattern      │ Full Audit               │
└──────────────────────────────────────────┴──────────────┴──────────────────────────┘
```

**田中PMの活用：**

> OAuth2 Token Manager パターンが発見されている。
> これは Google Workspace 連携や Microsoft Graph 連携でも使えるぞ。
> チームに共有して、次のプロジェクトで再利用しよう。

Issue を開くと、Run Report の Lessons セクションに詳細が記載されています：

```
📚 Reusable Patterns

L-1: Secure OAuth2 Token Manager
  概要: PKCE + Mutex + 自動リフレッシュ + スコープ検証を
       統合したトークンマネージャー
  再利用先: Google Workspace, Microsoft Graph 等の
           OAuth2 連携コネクタ
  キーファイル: src/auth/token_manager.ts
```

---

### 17:00 — 1日の振り返り

田中PMは再び **📊 Overview** に戻り、今日の成果を確認します。

**今日やったこと：**

| 時間 | ビュー | アクション |
|------|--------|----------|
| 09:00 | 📊 Overview | 全体進捗を把握。WI-SF-002 が気になる |
| 09:15 | 🔬 Findings | WI-SF-002 に5件の Finding。schema 系が多い |
| 09:30 | 🔄 Spec Impact | WI-SF-002 が required、WI-SF-003 が proposed |
| 09:45 | 📜 Amendments | AMD-SF-001 の内容を確認し PM承認 |
| 10:00 | — | 新しい Amendment を Claude Code と対話で起案 |
| 14:00 | 🔍 Decisions | WI-SF-002 の6件の判断を確認 |
| 16:00 | 📚 Learnings | OAuth2 パターンをチームに共有 |

---

## 📋 クイックリファレンス

### ラベル早見表

| カテゴリ | ラベル | 意味 | 色 |
|---------|--------|------|-----|
| **Findings** | `findings:0` | 問題なし | 🟢 緑 |
| | `findings:1-3` | 軽微な問題 | 🟡 黄 |
| | `findings:4+` | 多数の問題 | 🔴 赤 |
| **Decisions** | `decisions:0` | 判断なし | 🟢 緑 |
| | `decisions:1-3` | 少数の判断 | 🟡 黄 |
| | `decisions:4+` | 多数の判断 | 🔴 赤 |
| **Spec Impact** | `spec-impact:none` | 変更不要 | ⚪ 灰 |
| | `spec-impact:proposed` | 変更提案中 | 🟡 黄 |
| | `spec-impact:required` | 変更必須 | 🔴 赤 |
| **Learning** | `learning:pattern` | 再利用パターン発見 | 🟣 紫 |
| **Amendment** | `amendment:draft` | 起案中 | 🟡 薄黄 |
| | `amendment:review` | レビュー中 | 🟠 アンバー |
| | `amendment:applying` | Spec PR中 | 🔵 ブルー |
| | `amendment:applied` | 反映完了 | 🟢 エメラルド |
| | `amendment-derived` | Amendment由来WI | 🟩 ライトグリーン |

### ビュー × アクション対応表

| 状況 | 見るビュー | 次のアクション |
|------|----------|--------------|
| 全体の進捗を知りたい | 📊 Overview | Status / SDD Gate カラムを確認 |
| 問題がありそうなWIを見つけたい | 🔬 Findings | `findings:4+` のIssueを優先確認 |
| AIの判断を確認したい | 🔍 Decisions | `decisions:4+` のRun Reportを確認 |
| 仕様変更が必要か判断したい | 🔄 Spec Impact | required は即対応、proposed は検討 |
| 再利用できるパターンを探したい | 📚 Learnings | lessons.md の詳細を確認 |
| 仕様改訂の状況を確認したい | 📜 Amendments | draft → review → applying → applied の進捗 |

### Amendment の操作フロー

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   PMができる操作          │  AIが自動で行うこと              │
│  ─────────────────       │  ──────────────────              │
│                          │                                  │
│  ・方向性を示す           │  ・Findings / Decisions を収集    │
│  ・スコープを調整         │  ・影響分析・リスク提示           │
│  ・「これでOK」と承認     │  ・ドラフト作成                  │
│  ・承認チェックを入れる    │  ・Issue 作成・ラベル付与         │
│   （人間のみ）           │  ・Spec反映PR作成 (apply)        │
│  ・PRレビュー・マージ     │  ・新WI自動起票 (finalize)       │
│                          │  ・ラベル自動更新・Issue close    │
│                          │                                  │
└─────────────────────────────────────────────────────────────┘
```

### SDD Mode の意味

| Mode | 説明 | PMの関与度 |
|------|------|----------|
| `autopilot` | AIが自律的に実装。最小限の確認 | 低（結果のみ確認） |
| `confirm` | AIが判断を記録し、人間が確認 | 中（Decisions を確認） |
| `validate` | AIが提案し、人間が承認してから実行 | 高（各ステップで承認） |

### SDD Gate の意味

| Gate | 説明 | 状態 |
|------|------|------|
| Gate 1 | Planning 完了 | 計画承認済み |
| Gate 3 | Implementation 開始 | コーディング中 |
| Gate 5 | Walkthrough / Testing | レビュー・テスト中 |
| Final | 全工程完了 | リリース可能 |

---

## ❓ よくある質問

### Q: ラベルは誰が付けるのですか？

**A:** Claude Code が Run 完了時に自動で付与します。`run_report_generator.py` が Findings / Decisions の件数を集計し、適切なラベルを Issue に付けます。PMが手動でラベルを操作する必要はありません。

### Q: Amendment は必ず作る必要がありますか？

**A:** いいえ。`spec-impact:none`（仕様変更不要）の場合は不要です。`spec-impact:required` が出た場合のみ、仕様変更を正式に管理するために Amendment を起案します。

### Q: Amendment を自分で作りたい場合は？

**A:** Claude Code に「〇〇の仕様変更を検討したい」と伝えてください。AIが影響分析を行い、対話しながらドラフトを作成します。最終的に「これでOK」と伝えると Issue が作成されます。

### Q: AIが勝手に仕様を変更することはありますか？

**A:** ありません。Amendment Issue の承認チェックボックスは **人間のみが編集できる** という INVIOLABLE（不可侵）ルールがあります。AIは提案はしますが、承認なしに spec を変更することはできません。

### Q: Learnings はどう活用すればよいですか？

**A:** 定期的に 📚 Learnings ビューを確認し、発見されたパターンをチーム内で共有してください。同じ種類の実装（OAuth連携、データ同期など）を行う際に、過去の Learnings を参照することでAIの実装品質が向上します。

---

> **📌 このガイドは SDD v4.5（Tecnos-STRIDE）に基づいています。**
> 
> ツールの詳細は以下を参照してください：
> - `sdd-templates/tools/run_report_generator.py` — Run Report 生成
> - `sdd-templates/tools/amendment_generator.py` — Amendment 管理
> - `sdd-templates/tools/setup_project_labels.py` — ラベル設定
> - `agent_docs/github_project_views.md` — ビュー設定ガイド
