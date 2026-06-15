# 05. STRIDE SDD Board — PM向け操作ガイド

> **Tecnos-STRIDE SDD Board を使ったプロジェクト管理の実践ガイド**
> 
> このドキュメントでは、PMの1日の業務フローに沿って、STRIDE SDD Board の6つのビューをどう活用するかをシナリオ形式で解説します。
>
> **関連ガイド**: 実施担当者が Run Report をどう生成し、一次レビューするかは [実施担当者ガイド（§07）](07_practitioner_execution_guide.md) を参照してください。PM のダッシュボード操作と実施担当者の活動の連携については §07 の「3.2.7 Run Report と PM 連携」で詳しく解説しています。

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

- **田中PM** — ERP受注管理プロジェクトの PM
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
│ [EPIC] EPIC-SAMPLE: ERP受注管理アドオン │ In Progress│           │          │
│ [MS] MS-01: 受注登録・承認フロー完了       │ Done       │           │          │
│ [MS] MS-02: 権限管理・監査ログ完了     │ In Progress│           │          │
│ [WI] WI-ERP-SAMPLE-001: 受注登録画面のUI改善      │ Done       │ Final     │ autopilot│
│ [WI] WI-ERP-SAMPLE-002: 承認フロー・権限管理      │ In Progress│ Gate 5    │ confirm  │ ← 🔴
│ [WI] WI-ERP-SAMPLE-003: 監査ログ出力   │ In Progress│ Gate 5    │ validate │ ← 🟡
│ [RISK] ERP-R001: DB排他制御タイムアウト      │ In Progress│           │          │
│ [AMD] AMD-ERP-001: 承認権限マトリクス追加 │ In Progress│           │          │ ← 📜
└──────────────────────────────────────────┴────────────┴───────────┴──────────┘
```

**田中PMの確認ポイント：**
- ✅ WI-ERP-SAMPLE-001 は Done（完了）→ 問題なし
- 🔴 WI-ERP-SAMPLE-002 は Gate 5 で止まっている → 何か問題がありそう
- 🟡 WI-ERP-SAMPLE-003 も Gate 5 → 確認が必要
- 📜 Amendment が1件ある → 後で対応

> 💡 **Tips:** Status カラムでソートすると「In Progress」のアイテムが上に来て、対応が必要なものを素早く見つけられます。

---

### 09:15 — 問題の深掘り

Overview で WI-ERP-SAMPLE-002 が気になった田中PMは、**🔬 Findings** ビューに切り替えます。

#### 🔬 Findings でやること

AIが実装中に発見した問題（Findings）の多さで、**どの Work Item に注意が必要か**を判断します。

```
🔬 Findings ビュー
┌──────────────────────────────────────────┬──────────────┬─────────────┐
│ Title                                    │ Findings     │ Status      │
├──────────────────────────────────────────┼──────────────┼─────────────┤
│ [WI] WI-ERP-SAMPLE-002: 承認フロー・権限管理      │ findings:4+  │ In Progress │ ← ⚠️ 要注意
│ [WI] WI-ERP-001: 受注登録画面のUI改善     │ findings:1-3 │ Done        │
│ [WI] WI-ERP-SAMPLE-001: 受注登録画面のUI改善      │ findings:1-3 │ Done        │
│ [WI] WI-ERP-SAMPLE-003: 監査ログ出力   │ findings:1-3 │ Done        │
└──────────────────────────────────────────┴──────────────┴─────────────┘
```

**ラベルの読み方：**

| ラベル | 意味 | PMのアクション |
|--------|------|--------------|
| `findings:0` | 問題なし | 特になし |
| `findings:1-3` | 軽微な問題あり | Issue コメントで内容を確認 |
| `findings:4+` | 多数の問題あり | **要注意！** 詳細を確認して対処を検討 |

**田中PMの判断：**

> WI-ERP-SAMPLE-002 だけ `findings:4+` か。Issue を開いて Run Report を見てみよう。

Issue #17 を開くと、Claude Code が投稿した **Run Report** が表示されます：

```
🏃 Run Complete: RUN-20260213-0900

📋 Findings (5件)
┌───┬──────────────┬─────────────────────────────────────────────┬────────┐
│ # │ 種別         │ 発見内容                                     │ 影響度 │
├───┼──────────────┼─────────────────────────────────────────────┼────────┤
│F-1│ authorization│ 承認権限マトリクスの定義不足                    │ high   │
│F-2│ authorization│ 多段階承認フローの未考慮                       │ high   │
│F-3│ audit        │ 監査ログの詳細レベル不足                       │ medium │
│F-4│ performance  │ 大量注文時のDB排他制御タイムアウト               │ medium │
│F-5│ data_quality │ 権限名称の表記揺れ                            │ low    │
└───┴──────────────┴─────────────────────────────────────────────┴────────┘
```

> F-1〜F-3 が権限系で影響度 high... これは仕様変更が必要だな。

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
│                     │ │ WI-ERP-SAMPLE-002│ │                     │
│                     │ │ 承認フロー・     │ │                     │
│                     │ │ 権限管理         │ │                     │
│                     │ │ spec-impact:     │ │                     │
│                     │ │ required 🔴     │ │                     │
│                     │ └─────────────────┘ │                     │
│                     │                     │                     │
│                     │ ┌─────────────────┐ │                     │
│                     │ │ WI-ERP-SAMPLE-003│ │                     │
│                     │ │ 監査ログ出力     │ │                     │
│                     │ │                  │ │                     │
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

> WI-ERP-SAMPLE-002 が `required`（必須）で、WI-ERP-SAMPLE-003 が `proposed`（提案中）。
> WI-ERP-SAMPLE-002 は仕様を変更しないと先に進めない。Amendment を確認しよう。

---

### 09:45 — Amendment（仕様改訂）の対応

田中PMは **📜 Amendments** ビューに切り替えます。

#### 📜 Amendments でやること

仕様改訂のライフサイクルを **draft → review → applied** の3段階で管理します。

```
📜 Amendments ビュー（Board形式）
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ draft               │ review              │ applied             │
│ 起案済み             │ レビュー中           │ 反映完了             │
│ (0)                 │ (1)                 │ (0)                 │
│                     │                     │                     │
│                     │ ┌─────────────────┐ │                     │
│                     │ │ AMD-ERP-001      │ │                     │
│                     │ │ 承認権限         │ │                     │
│                     │ │ マトリクス       │ │                     │
│                     │ │ 追加             │ │                     │
│                     │ └─────────────────┘ │                     │
│                     │                     │                     │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

**Amendment のライフサイクル：**

```
AIまたはPMが起案        PMがレビュー・承認       specに反映完了
  ┌──────────┐         ┌──────────┐          ┌──────────┐
  │  draft   │ ──────→ │  review  │ ──────→  │ applied  │
  └──────────┘         └──────────┘          └──────────┘
   起案中                承認待ち               完了
```

**田中PMの操作：**

Issue #21（AMD-ERP-001）を開くと、Amendment の詳細が表示されます：

```markdown
📜 Amendment: 承認権限マトリクス追加

AMD ID: AMD-ERP-001
Feature: FEAT-SAMPLE

### 変更概要
承認権限マトリクスの定義不足を解決するため、ロール別権限定義を追加する。

### 根拠となる Findings
- [ ] WI-ERP-SAMPLE-002 F-1: 承認権限マトリクスの定義不足
- [ ] WI-ERP-SAMPLE-002 F-3: 監査ログ詳細レベル不足

### 変更内容
| ファイル   | セクション | 変更内容                                    |
|-----------|-----------|-------------------------------------------|
| spec.md   | AC-ERP-002 | 承認ロール定義マトリクスを追加                 |
| plan.md   | NFR-003   | 「多段階承認は Phase 2」の明記               |

### 承認
- [ ] PM承認        ← ここにチェックを入れる！
- [ ] Tech Lead承認
```

**田中PMの操作：**

1. 変更内容を確認 → 妥当と判断
2. `- [ ] PM承認` を `- [x] PM承認` に編集
3. Tech Lead の承認も得られたら、Claude Code に `apply` を指示

> 💡 **承認チェックボックスは人間のみが編集できます。** AIが勝手に承認することはありません（SDD の INVIOLABLE ルール）。

---

### 10:00 — 新しい Amendment を起案したい場合

田中PMが「WI-ERP-SAMPLE-003 の監査ログ精度の問題も仕様変更したい」と判断した場合：

#### Claude Code との対話で Amendment を作成

```
田中PM: 「WI-ERP-SAMPLE-003 の監査ログ精度の問題、仕様変更を検討したい」

Claude Code: 影響分析を実行します...

  📊 Amendment Impact Analysis
  
  Feature: FEAT-SAMPLE
  Topic: 監査ログ精度
  
  関連 Findings (1件)
  ┌────────┬───┬─────────────┬──────────────────────────────┬────────┐
  │ WI     │ # │ 種別        │ 内容                          │ 影響度 │
  ├────────┼───┼─────────────┼──────────────────────────────┼────────┤
  │WI-ERP-SAMPLE-003│F-1│audit│ 監査ログ精度の差異（秒vs │ medium │
  │        │   │             │ ミリ秒）                      │        │
  └────────┴───┴─────────────┴──────────────────────────────┴────────┘
  
  💡 AI 推奨:
  監査証跡にタイムスタンプ+操作ハッシュの
  併用を提案します。spec.md AC-ERP-003 にハッシュ比較
  ロジックの追加が必要です。

田中PM: 「ハッシュ併用でOK。ただしハッシュ対象項目は
         設定可能にして」

Claude Code: 了解しました。ドラフトを修正します...
         （ドラフト提示）

田中PM: 「これでOK。Issue 作って」

Claude Code: Amendment Issue を作成しました。
         → Issue #22: [AMD] AMD-ERP-002
         → ラベル: amendment:draft
         → Project に追加済み
```

**ポイント：**
- PMは方向性を示すだけ
- データ収集・分析・ドラフト作成はAIが自動実行
- PMが「これでOK」と言うまで Issue は作成されない

---

### Amendment Fast Track（v4.5.1）

低リスクの Amendment（ドキュメント修正、パラメータ名変更、コメント追加など）は **Fast Track** で承認プロセスを簡略化できます。

```bash
# 通常の Amendment ドラフト（PM + Tech Lead 承認が必要）
amendment_generator.py draft FEAT-SAMPLE AMD-SAMPLE-003

# Fast Track ドラフト（Tech Lead のみで承認可能）
amendment_generator.py draft FEAT-SAMPLE AMD-SAMPLE-003 --fast
```

**Fast Track を使うべきケース：**
- ドキュメント・コメントの修正
- パラメータ名やラベルの変更
- テストケースの追加・補正
- 既存仕様の明確化（意味の変更なし）

**Fast Track を使ってはいけないケース：**
- ビジネスロジックの変更
- API契約（contracts/）の変更
- Acceptance Criteria の追加・削除
- セキュリティ関連の変更

Fast Track で作成された Amendment Issue には `⚡ fast-track` マーカーが付与され、Tech Lead 単独の承認で `apply` に進めます。
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
│ [WI] WI-ERP-SAMPLE-002: 承認フロー・権限管理      │ decisions:4+ │ confirm  │ ← 要確認
└──────────────────────────────────────────┴──────────────┴──────────┘
```

**ラベルの読み方：**

| ラベル | 意味 | PMのアクション |
|--------|------|--------------|
| `decisions:0` | 判断なし（シンプルな実装） | 特になし |
| `decisions:1-3` | 少数の判断 | 必要に応じて確認 |
| `decisions:4+` | 多数の判断 | **要確認！** 判断内容をレビュー |

**田中PMの確認：**

> WI-ERP-SAMPLE-002 は `decisions:4+` で Mode が `confirm`。
> confirm モードは「AIが判断を記録し、人間が確認する」モード。
> Issue の Run Report で Decisions の内容を確認しよう。

Issue #17 の Run Report を確認：

```
📝 Decisions (6件)
┌───┬──────────────────────────────────────────────┬──────────┐
│ # │ 判断内容                                      │ ステータス│
├───┼──────────────────────────────────────────────┼──────────┤
│D-1│ DB直接アクセス→API経由に変更                    │ accepted │
│D-2│ 管理者承認を先行、多段階はPhase 2               │ proposed │ ← spec変更待ち
│D-3│ 承認ステップ数を configurable化（デフォルト2段階）│ accepted │
│D-4│ 権限マトリクスをロール別定義に変更               │ proposed │ ← spec変更待ち
│D-5│ 権限名称正規化テーブルを導入                    │ accepted │
│D-6│ 初期データ投入はバッチ処理に変更                │ accepted │
└───┴──────────────────────────────────────────────┴──────────┘
```

> D-2 と D-4 が `proposed`（spec変更待ち）。これは AMD-ERP-001 で対応中だな。

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
│ [WI] WI-ERP-SAMPLE-001: 受注登録画面のUI改善      │ learning:    │ Approval Flow Manager    │
│                                          │ pattern      │                          │
│ [WI] WI-ERP-SAMPLE-003: 監査ログ出力   │ learning:    │ Audit Log with Full      │
│                                          │ pattern      │ Traceability             │
└──────────────────────────────────────────┴──────────────┴──────────────────────────┘
```

**田中PMの活用：**

> Approval Flow Manager パターンが発見されている。
> これは購買管理や在庫管理の承認フローでも使えるぞ。
> チームに共有して、次のプロジェクトで再利用しよう。

Issue を開くと、Run Report の Lessons セクションに詳細が記載されています：

```
📚 Reusable Patterns

L-1: Approval Flow Manager
  概要: 多段階承認 + 権限チェック + 自動エスカレーションを
       統合した承認フローマネージャー
  再利用先: 他モジュール（購買、在庫等）の承認フロー
  キーファイル: src/approval/flow_manager.ts
```

---

### 17:00 — 1日の振り返り

田中PMは再び **📊 Overview** に戻り、今日の成果を確認します。

**今日やったこと：**

| 時間 | ビュー | アクション |
|------|--------|----------|
| 09:00 | 📊 Overview | 全体進捗を把握。WI-ERP-SAMPLE-002 が気になる |
| 09:15 | 🔬 Findings | WI-ERP-SAMPLE-002 に5件の Finding。権限系が多い |
| 09:30 | 🔄 Spec Impact | WI-ERP-SAMPLE-002 が required、WI-ERP-SAMPLE-003 が proposed |
| 09:45 | 📜 Amendments | AMD-ERP-001 の内容を確認し PM承認 |
| 10:00 | — | 新しい Amendment を Claude Code と対話で起案 |
| 14:00 | 🔍 Decisions | WI-ERP-SAMPLE-002 の6件の判断を確認 |
| 16:00 | 📚 Learnings | 承認フローパターンをチームに共有 |

---

## 🔗 実施担当者との連携ポイント

PM のダッシュボード操作と実施担当者の活動は、以下のポイントで繋がっています。

### Run Report → ラベル → STRIDE Board

```
実施担当者（鈴木さん）                        PM（田中PM）
─────────────────────                      ──────────────
                                            
① Claude Code に実装指示                    
② Walkthrough レビュー（AC照合）              
③ Run Report レビュー（Findings/Decisions）   
   ├── 技術的な問題 → 自分で解消              
   ├── Findings backlog → マーク               
   └── spec-impact:required → ④へ            ④ 🔬 Findings / 🔍 Decisions /
                                               🔄 Spec Impact ビューで確認
⑤ PM にエスカレーション ──────────────────→ ⑥ Amendment 起案・承認
                                            ⑦ Claude Code に spec 更新指示
⑧ Amendment 適用後の影響確認 ←───────────── (spec 更新の通知)
⑨ 影響範囲の実装・テスト修正                  
⑩ 承認（approval.md 編集）                  
```

### PM が実施担当者に依頼するタイミング

| PM のアクション | 実施担当者への依頼内容 | 参照先 |
|---------------|---------------------|-------|
| Findings ビューで `findings:4+` を発見 | 「問題の対処状況を報告してください」 | §07 [Findings の対処手順](07_practitioner_execution_guide.md#findings-の対処手順) |
| Decisions ビューで `decisions:4+` を発見 | 「判断の妥当性を説明してください」 | §07 [Decisions の対処手順](07_practitioner_execution_guide.md#decisions-の対処手順) |
| Amendment を承認・適用した | 「spec が更新されたので影響範囲を確認してください」 | §07 [§2 15:00 Amendment 適用後](07_practitioner_execution_guide.md) |
| validate モードの WI の事前承認 | 「design_diff を確認するので提出してください」 | §07 [§2 13:00 高リスクWI](07_practitioner_execution_guide.md) |

### 実施担当者が PM にエスカレーションするタイミング

| 状況 | 実施担当者のアクション | PM の対応 |
|------|---------------------|---------|
| `spec-impact:required` が出た | PM に Amendment 起案を依頼 | 📜 Amendments で起案・承認 |
| `spec-impact:proposed` でビジネス判断が必要 | PM に判断を仰ぐ | 内容を確認し、Amendment 要否を判断 |
| Decisions の `proposed` でスコープ影響あり | PM に承認を依頼 | ビジネス影響を評価し accept/reject |
| validate モードの事前承認が必要 | PM に design_diff + plan_review を依頼 | 内容を確認し承認 |

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
| | `amendment:applied` | 反映完了 | 🟢 エメラルド |
| **Symphony** | `symphony:ready` | 実行トリガー | 🔵 青 |
| | `symphony:running` | エージェント実行中 | 🟡 黄 |
| | `symphony:done` | Phase完了 | 🟢 緑 |
| | `symphony:blocked` | 承認待ち | 🟠 オレンジ |
| | `symphony:failed` | 失敗（リトライ上限到達） | 🔴 赤 |

### ビュー × アクション対応表

| 状況 | 見るビュー | 次のアクション |
|------|----------|--------------|
| 全体の進捗を知りたい | 📊 Overview | Status / SDD Gate カラムを確認 |
| 問題がありそうなWIを見つけたい | 🔬 Findings | `findings:4+` のIssueを優先確認 |
| AIの判断を確認したい | 🔍 Decisions | `decisions:4+` のRun Reportを確認 |
| 仕様変更が必要か判断したい | 🔄 Spec Impact | required は即対応、proposed は検討 |
| 再利用できるパターンを探したい | 📚 Learnings | lessons.md の詳細を確認 |
| 仕様改訂の状況を確認したい | 📜 Amendments | draft → review → applied の進捗 |

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
│   （✅ 人間のみ）        │  ・spec への反映                 │
│                          │  ・ラベル自動更新                │
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

| Gate | Phase | 説明 |
|------|-------|------|
| Gate 1,2 | Design | Basic Design + BPMN 承認 |
| Gate 3,4 | Specify | Spec + Plan 承認 |
| Gate 5 | Tasking | Tasks 承認 → Execute Phase 開始 |
| Final | Final | 全 WI 完了 + Evidence Pack → リリース可能 |

> **Note**: Gate 5 承認後に Execute Phase が始まり、WI ごとの実装→レビュー→承認サイクルが回ります。
> 実施担当者が WI レベルで何をしているかは [実施担当者ガイド（§07）](07_practitioner_execution_guide.md) を参照してください。

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

**A:** 定期的に 📚 Learnings ビューを確認し、発見されたパターンをチーム内で共有してください。同じ種類の実装（承認フロー、権限管理など）を行う際に、過去の Learnings を参照することでAIの実装品質が向上します。

---

> **📌 このガイドは SDD v4.8.0-tecnos-stride に基づいています。**
> 
> ツールの詳細は以下を参照してください：
> - `sdd-templates/tools/run_report_generator.py` — Run Report 生成
> - `sdd-templates/tools/amendment_generator.py` — Amendment 管理
> - `sdd-templates/tools/setup_project_labels.py` — ラベル設定
> - `agent_docs/github_project_views.md` — ビュー設定ガイド
