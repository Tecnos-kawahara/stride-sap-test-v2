# 07. Tecnos-STRIDE 実施担当者ガイド — AI と共に仕様を「実行」する

> **Version**: v5.4.0-tecnos-stride
> **対象**: 開発者・実施担当者（初めて STRIDE に参加する人を含む）
> **所要時間**: 通読 約60分（リファレンスとして随時参照）

---

## PM向け3分サマリー

このガイドは **実施担当者（開発者）** 向けです。PMの方は [PM向けガイド](05_pm_operations_guide.md) を参照してください。

実施担当者はこのガイドで以下を学びます：
- Claude Code に何を伝え、何を確認し、何を承認するか
- AI が自律実行する作業の全体像と、人間が介入するポイント
- stride-lint エラーの読み方と、AI への修正指示の出し方
- Work Item / Run / State のライフサイクルの理解

---

## 1. このガイドの対象と目的

### 1.1 対象読者

- **SDD/STRIDE プロジェクトに初めて参加する開発者**
- **Claude Code を使って実装作業を進める実施担当者**
- テックリードとして WI のレビュー・承認を行う方

### 1.2 v4.4 における実施担当者の役割

> **v4.4 の核心**: 実施担当者は**自分でコードを書いたりコマンドを叩く必要はない**。
> Claude Code に要件や修正依頼を伝え、成果物を確認し、承認するのが主な仕事。

| 担当 | やること | やらないこと |
|------|---------|-------------|
| **実施担当者** | Claude Code への指示、成果物レビュー、APPROVAL.md / WI-*.approval.md の編集、業務判断 | ファイル作成、コマンド実行、lint、テスト実行 |
| **Claude Code** | 全作業の自律実行（init〜実装〜テスト〜lint〜Evidence作成） | 承認ファイルの編集、業務判断 |

つまり、**実施担当者は Claude Code の「ドライバー」** です。行き先（要件）を伝え、道中の安全確認（レビュー）をし、チェックポイント（Gate）でサインオフする。ハンドル操作（実装）は Claude Code がやります。

### 1.3 前提知識

| 必須 | あると望ましい |
|------|--------------|
| Claude Code の基本操作（起動、対話、ファイル確認） | ERP 業務の基本知識 |
| Git の基本概念（ブランチ、コミット、PR） | BPMN の読み方 |
| Markdown / YAML が読めること | OpenAPI の基礎 |
| 業務要件を言語化する能力 | テスト駆動開発の概念 |

> **Note**: Python や TypeScript のコーディングスキルは**必須ではない**。Claude Code がコードを書き、テストを実行する。ただし、成果物のレビュー時にコードが読めると品質判断がしやすい。

### 1.4 このガイドで学べること

1. Claude Code にどう指示を出すか（Phase ごとの具体的なプロンプト例）
2. Claude Code が自律実行する内容と、人間が介入するポイント
3. stride-lint エラーが出た時の読み方と、AI への修正指示
4. Work Item → Run → Walkthrough → 承認のライフサイクル
5. 成果物のレビュー方法（何を確認すべきか）
6. トラブルシューティング

### 1.5 対象外

- プロジェクト管理・進捗管理 → [PM向けガイド](05_pm_operations_guide.md)
- GitHub Projects のビュー設定 → [GitHub Projects連携ガイド](26_github_projects_guide.md)
- 組織制約（監査/運用ルール）の詳細 → `memory/tecnos_org_constraints.md`

---

## 2. 実施担当者の1日（シナリオ形式）

### 登場人物

- **鈴木さん** — Web-EDI 受注機能の実施担当者（STRIDE 初参加）
- **Claude Code** — AI 実行エージェント（全作業の実行者 R）
- **田中PM** — プロジェクトマネージャー（承認者 A）

---

### 09:00 — 朝の状態確認

鈴木さんはまず、Claude Code を起動して担当 Feature の現在状態を確認します。

```
鈴木: 「web_edi_order の現在の状態を教えてください。
       自分の担当 WI と、次にやるべきことを整理してください。」

Claude Code:
  現在の状態を確認します...

  Feature: FEAT-WEB-EDI-001
  Current Gate: Gate 5（承認済み — Execute Phase）
  
  Work Items:
  ┌─────────────────────┬─────────────┬───────────┐
  │ WI ID               │ Status      │ Mode      │
  ├─────────────────────┼─────────────┼───────────┤
  │ WI-WEB-EDI-001      │ done        │ autopilot │
  │ WI-WEB-EDI-002      │ in_progress │ autopilot │ ← あなたの担当（低リスク）
  │ WI-WEB-EDI-003      │ not_started │ validate  │
  └─────────────────────┴─────────────┴───────────┘
  
  WI-WEB-EDI-002 は autopilot モードです。
  事前承認なしで実装を開始できます。
  実装を開始しますか？
```

**state.yaml の構造（Claude Code が内部で参照）：**

```yaml
feature: FEAT-WEB-EDI-001
current_gate: Gate5
autonomy_bias: balanced

work_items:
  - wi_id: WI-WEB-EDI-001
    status: done
    mode: autopilot
  - wi_id: WI-WEB-EDI-002       # ← 鈴木さんの担当
    status: in_progress
    mode: autopilot              # risk_flags: [ui_only] → autopilot
  - wi_id: WI-WEB-EDI-003
    status: not_started
    mode: validate               # risk_flags: [db_schema, data_migration] → validate

run_index:
  WI-WEB-EDI-001: RUN-001
```

> 💡 **ポイント**: `mode: autopilot` なので、事前承認なしでClaude Codeが実装を開始できる。ただし実装後の walkthrough レビューは必須。

---

### 09:15 — AI が自律実装を開始

```
鈴木: 「はい、WI-WEB-EDI-002 の実装を開始してください。」

Claude Code:
  WI-WEB-EDI-002 の実装を開始します。

  readiness check:
  [1/5] WI file exists .................. PASS
  [2/5] Risk flags valid ................ PASS
  [3/5] Mode matches policy ............. PASS (autopilot)
  [4/5] Dependencies resolved ........... PASS
  [5/5] Pre-run approval ................ N/A (autopilot — 事前承認不要)
  Result: READY

  実装を進めます...
  [1/4] AC-US-FEATWEB-EDI-001-001-01 の実装...
  [2/4] AC-US-FEATWEB-EDI-001-001-02 の実装...
  [3/4] テスト作成・実行（5件 全 PASS）...
  [4/4] stride lint → PASS

  実装が完了しました。walkthrough と Run Report を作成します...
```

> autopilot モードでは、鈴木さんが「開始してください」と言えば、実装→テスト→walkthrough→Run Report まで一気に進みます。

---

### 10:30 — Walkthrough のレビュー

Claude Code が全工程を完了し、成果物の確認を依頼してきます。

```
Claude Code:
  WI-WEB-EDI-002 の全工程が完了しました。

  成果物サマリー:
  - 実装: src/api/orders.py, src/domain/order_validator.py
  - テスト: 5件 全 PASS
  - Coverage: LIB-01 87%/78%, CMP-01 65%/55%
  - stride-lint: PASS
  - Run Report: Findings 1件, Decisions 2件

  walkthrough.md と Run Report を確認してください。
```

鈴木さんの仕事は**成果物のレビュー**です。
Claude Code に AC と Evidence の対照表を一発で出させます。

```
鈴木: 「WI-WEB-EDI-002 の AC の then 条件と、walkthrough の Evidence の
       実際の結果を対照表にして見せてください。一致/不一致も判定してください。」

Claude Code:
  AC ↔ Evidence 対照表:
  ┌──────────────────────────┬───────────────────┬───────────────────────┬────┐
  │ AC ID                    │ then 条件（仕様）  │ Evidence（実際）       │判定│
  ├──────────────────────────┼───────────────────┼───────────────────────┼────┤
  │AC-US-FEATWEB-EDI-001-01 │ 200 OK + order_id │ 200 OK + order_id     │ ✅ │
  │AC-US-FEATWEB-EDI-001-02 │ 409 Conflict      │ 500 Internal Server   │ ❌ │
  │                          │ + 在庫不足メッセージ │ Error                │    │
  └──────────────────────────┴───────────────────┴───────────────────────┴────┘
  
  Coverage: LIB-01 87%/78% ✅, CMP-01 65%/55% ✅
  
  ⚠️ 1件の不一致があります。
  AC-...-02: 仕様は 409 Conflict ですが、実際は 500 が返っています。
  テストは PASS ですが、アサーションがステータスコードを検証していない可能性があります。
```

> 鈴木さんは対照表の ❌ だけ確認すればよい。全項目を自分で照合する必要はありません。

**不一致を発見 → フィードバック**

```
鈴木: 「AC-...-02 の不一致を修正してください。
       テストのアサーションでステータスコードも検証してください。」

Claude Code:
  確認しました...
  
  問題を特定しました。TS-INT-02 のアサーションが
  「レスポンスボディに "在庫不足" が含まれること」のみで、
  ステータスコード 409 を検証していませんでした。
  
  また、実装側でも StockShortageError が catch されておらず、
  500 が返っていました。
  
  修正します...
  
  [1/4] src/api/orders.py: StockShortageError の catch を追加 → 409 返却
  [2/4] TS-INT-02: assert response.status_code == 409 を追加
  [3/4] テスト再実行: TS-INT-02 PASS ✅（409 Conflict を確認）
  [4/4] walkthrough.md の Evidence を更新

  修正完了しました。stride-lint: PASS
  再度ご確認ください。
```

**Step 4: 再確認 → OK**

```
鈴木: 「修正後の Evidence を見せてください。」

Claude Code:
  ## Evidence（修正後）
  - Test: TS-INT-01 PASS — 正常系: 200 OK + order_id 返却 ✅
  - Test: TS-INT-02 PASS — 在庫不足: 409 Conflict + 在庫不足メッセージ ✅
  - Coverage: 87% line / 78% branch
```

AC の then 条件と Evidence が一致 ✅ → 次は Run Report を確認します。

> 💡 **レビューの基本**: 「spec.md の AC → walkthrough の Evidence」を照合する。
> テストが PASS していても、AC の条件と実際の挙動が一致しているかは人間が確認する。
> 詳細は [3.2.4 Walkthrough のレビューとフィードバック](#324-walkthrough-のレビューとフィードバック) を参照。

---

### 11:00 — Run Report のレビュー（Findings / Decisions）

walkthrough の技術面が OK なので、次は Run Report を確認します。
**これが PM のダッシュボード（STRIDE Board）と繋がるポイントです。**

```
鈴木: 「Run Report の Findings と Decisions を見せてください。」

Claude Code:
  📋 Findings (1件)
  ┌───┬──────────────┬────────────────────────────────────────┬────────┐
  │ # │ 種別         │ 発見内容                                │ 影響度 │
  ├───┼──────────────┼────────────────────────────────────────┼────────┤
  │F-1│ performance  │ 大量注文時（1000件超）にバリデーションが遅い │ medium │
  └───┴──────────────┴────────────────────────────────────────┴────────┘

  📝 Decisions (2件)
  ┌───┬─────────────────────────────────────────────┬──────────┐
  │ # │ 判断内容                                     │ ステータス│
  ├───┼─────────────────────────────────────────────┼──────────┤
  │D-1│ バリデーションをドメイン層（LIB-01）に実装    │ accepted │
  │D-2│ 在庫チェックは同期 API で実施                │ accepted │
  └───┴─────────────────────────────────────────────┴──────────┘

  Spec Impact: none
  Lessons: なし
```

**鈴木さんの対処：**

```
鈴木: 「F-1 のパフォーマンス問題は、現行の要件（日次約200件）では
       影響ないのでバックログに回します。
       D-1 は Article I（Library-First）に準拠していて OK。
       D-2 は NFR-PERF-001（500ms以下）を満たしているか確認したい。」

Claude Code:
  D-2 の実測結果: 在庫チェック処理 平均 180ms（NFR-PERF-001: 500ms 以下を充足）

  F-1: backlog としてマークしました。
```

> **このRun Reportが GitHub Issue にラベルとして自動反映されます**：
> - `findings:1-3`（軽微な問題あり）
> - `decisions:1-3`（少数の判断）
> - `spec-impact:none`（仕様変更不要）
>
> 田中PMは STRIDE Board の 🔬 Findings ビューや 🔍 Decisions ビューでこのラベルを見て、
> 「WI-WEB-EDI-002 は問題なさそうだ」と判断します。
> もし `findings:4+` や `spec-impact:required` だったら、PM が介入してきます。
> → [PM側の確認フロー（§05）](05_pm_operations_guide.md)

---

### 11:30 — 承認

Run Report も問題なし → 承認に進みます。

```
鈴木: 「問題ありません。承認します。」
```

**鈴木さんが `WI-WEB-EDI-002.approval.md` を編集**：

```markdown
- [x] Walkthrough reviewed by TL  ← チェックを入れる
- [x] CI passed
- Approver: 鈴木
- Date: 2026-03-10
```

```
Claude Code:
  承認を確認しました。state.yaml を更新します。
  WI-WEB-EDI-002: done
  次の WI-WEB-EDI-003 の準備を開始します...
```

---

### 13:00 — 高リスク WI の事前承認プロセス

午後、次の WI-WEB-EDI-003 に取り掛かります。これは `validate` モード（高リスク）です。

```
鈴木: 「WI-WEB-EDI-003 の実行準備を確認してください。」

Claude Code:
  WI-WEB-EDI-003 の準備状況:
  - Mode: validate（高リスク）
  - risk_flags: [db_schema, data_migration]
  - 依存: WI-WEB-EDI-002 (done) ✅

  readiness check:
  [1/5] WI file exists .................. PASS
  [2/5] Risk flags valid ................ PASS
  [3/5] Mode matches policy ............. PASS (validate)
  [4/5] Dependencies resolved ........... PASS
  [5/5] Pre-run approval (validate) ..... PENDING
        → design_diff: PENDING ← 必要
        → plan_review: PENDING ← 必要

  Result: NOT_READY — 2つの事前承認が必要です。
  
  validate モードでは:
  1. design_diff（設計差分レビュー）→ 田中PMに依頼
  2. plan_review（実装計画レビュー）→ 田中PMに依頼
  の両方が必要です。
```

> 鈴木さんは田中PMに design_diff と plan_review を依頼します。
> **PM 側では**: 田中PMが STRIDE Board の Overview でこの WI を確認し、
> validate の2段階承認を実施 → [PM側のフロー（§05）](05_pm_operations_guide.md)

---

### 15:00 — PM にエスカレーションが必要なケース

WI-WEB-EDI-003 の事前承認を待つ間に、別の例を見てみましょう。
もし Run Report に **spec-impact:required** が出た場合、鈴木さんは PM にエスカレーションします。

```
Claude Code:
  📋 Findings (3件)
  ┌───┬──────────────┬────────────────────────────────────────┬────────┐
  │ # │ 種別         │ 発見内容                                │ 影響度 │
  ├───┼──────────────┼────────────────────────────────────────┼────────┤
  │F-1│ schema       │ 通貨コード情報が API レスポンスに欠落     │ high   │
  │F-2│ performance  │ 大量データ時にバリデーションが遅い          │ medium │
  │F-3│ data_quality │ 商品コードの表記揺れ（全角/半角混在）      │ low    │
  └───┴──────────────┴────────────────────────────────────────┴────────┘

  Spec Impact: required 🔴
  → F-1 の通貨コード情報が spec.md に未定義です。

鈴木: 「F-1 は仕様変更が必要なので、田中PMにエスカレーションします。
       F-2 はバリデーションをバルク処理に最適化してください。
       F-3 はバックログに回します。」
```

**鈴木さんが田中PMに連絡：**

```
鈴木 → 田中PM:
  「WI-WEB-EDI-003 の Run Report で spec-impact:required が出ました。
   通貨コード情報が spec.md に未定義です。
   Amendment の起案をお願いできますか？」
```

> **PM 側では**: 田中PMが STRIDE Board の 🔄 Spec Impact ビューで `required` を確認し、
> 📜 Amendments ビューで Amendment を起案・承認 → Claude Code が spec を更新
> → 更新後、鈴木さんに「spec が更新されたので、影響範囲を確認してください」と連絡
> → [PM側のAmendmentフロー（§05）](05_pm_operations_guide.md)

**Amendment 適用後の鈴木さんの対応：**

```
鈴木: 「Amendment AMD-WEB-EDI-001 が適用されました。
       spec.md の変更が WI-WEB-EDI-003 に影響するか確認してください。
       必要なら実装とテストを修正してください。」

Claude Code:
  spec.md の変更を確認します...
  
  影響分析:
  - AC-US-FEATWEB-EDI-001-001-01: currency_code フィールド追加 → 影響あり
  - AC-US-FEATWEB-EDI-001-001-02: 変更なし → 影響なし
  
  影響がある箇所を修正します...
  [1/3] src/domain/order.py: currency_code フィールド追加
  [2/3] TS-INT-01: currency_code のアサーション追加
  [3/3] テスト再実行: PASS

  修正完了。walkthrough を更新しました。
```

---

### 17:00 — 1日の振り返り

```
鈴木: 「今日の作業サマリーを教えてください。」

Claude Code:
  今日の作業サマリー:
  ┌──────┬─────────────────────────────────────────────────┐
  │ 時間 │ 内容                                             │
  ├──────┼─────────────────────────────────────────────────┤
  │09:00 │ 状態確認 — WI-002(autopilot), WI-003(validate)   │
  │09:15 │ WI-002 実装開始（Claude Code 自律実行）           │
  │10:30 │ WI-002 walkthrough レビュー（AC照合で不備発見→修正）│
  │11:00 │ WI-002 Run Report レビュー（F-1 backlog, D-1/D-2 OK）│
  │11:30 │ WI-002 承認 → done                               │
  │13:00 │ WI-003 readiness check → validate の事前承認待ち  │
  │15:00 │ （例示）spec-impact:required → PM にエスカレーション│
  │17:00 │ 今日の振り返り                                    │
  └──────┴─────────────────────────────────────────────────┘

  明日の予定:
  - WI-003: design_diff + plan_review 承認後に実装開始
```

> 💡 **シナリオの全体像**: 実施担当者の1日は「状態確認 → 実装指示 → Walkthrough レビュー（AC照合）→ Run Report レビュー（Findings/Decisions対処）→ 承認 → 次のWI」のサイクルを回すこと。PM との接点は Run Report のラベル（自動）と、エスカレーション（必要時のみ）。

---

## 3. Phase 別アクション — 新機能を最初から

> **ここからは鈴木さんが「新しい Feature」を Design Phase からスタートする流れを追います。**
> §2 のシナリオが「Execute Phase の途中から」だったのに対し、ここでは**最初の一歩から**。
> 各 Phase で「Claude Code に何を伝えるか → 何を確認するか → 何を承認するか」に集中します。

### 全体マップ

```
Phase 1-3: Design → Specify → Tasking  → Gate 1〜5 承認  ← シニアSE/アーキテクト担当（§06）
Phase 4:   Execute                      → WI 承認        ← 実施担当者の主戦場（本ガイド）
Phase 5:   Final                        → Final 承認     ← PR Ready
```

> **v4.4 ルール**: 各 Phase のファイル作成・lint・自動修正はすべて Claude Code が自律実行。
> 実施担当者は **Execute Phase で「WI を受け取り → レビュー → 承認する」** のが主な仕事。

### Execute Phase で実施担当者がやること / Claude Code がやること

| 作業 | 実施担当者 | Claude Code |
|------|-----------|-------------|
| WI の risk_flags / Mode レビュー | ✅ 妥当性確認 | — |
| WI の実装・テスト・walkthrough | — | ✅ 自律実行 |
| stride-lint の実行と修正 | — | ✅ 自動修正 |
| walkthrough のレビュー（AC 照合） | ✅ 内容確認 | — |
| Run Report の対処（Findings/Decisions） | ✅ 判断を伝える | — |
| PM へのエスカレーション | ✅ 必要時に連絡 | — |
| WI-*.approval.md の編集 | ✅ 承認する | ❌ **編集禁止** |
| APPROVAL.md（Final Gate）の編集 | ✅ 承認する | ❌ **編集禁止** |
| state.yaml の更新 | — | ✅ 自律実行 |

---

### 3.1 上流フェーズの概要（Design → Specify → Tasking）

> **上流フェーズ（Gate 1〜5）はシニアSE・アーキテクト・TL が担当**します。
> 実施担当者（鈴木さん）は Gate 5 承認後の Execute Phase から参加します。
> ここでは「自分に降りてくる前に何が決まっているか」を把握するための概要です。
>
> 📖 **上流フェーズを自分で実行する場合**: → [上流工程ガイド（§06）](06_upstream_phase_guide.md) を参照

#### Design Phase（Gate 1,2）— 何を作るか

シニアSE が Claude Code に機能の要件を伝え、以下が作成されます：

| 成果物 | 内容 |
|--------|------|
| `basic_design.md` | Who/What/Why、連携先、coverage_tier、RACI+ |
| `process.bpmn` | 業務フローの可視化 |

**実施担当者が知っておくべきこと:**
- `coverage_tier`（critical / standard / experimental）が Execute Phase の Mode 制約に影響する
- `integration_flows` に定義された連携先が、後の Contract Test の対象になる

#### Specify Phase（Gate 3,4）— どう作るか

シニアSE が Claude Code と仕様・計画を詰め、以下が作成されます：

| 成果物 | 内容 |
|--------|------|
| `spec.md` | ユースケース、受入条件（AC）、NFR |
| `plan.md` | テスト戦略、Coverage Policy、コンポーネント設計 |
| `contracts/` | OpenAPI 定義等 |

**実施担当者が知っておくべきこと:**
- `spec.md` の **AC（Acceptance Criteria）** が Execute Phase で「何を満たせば完了か」の基準になる
- AC の `tags`（`integration` / `e2e`）が必要なテストの種類を決定する
- `plan.md` の **Coverage Policy** がカバレッジ目標を定義する

#### Tasking Phase（Gate 5）— 何をどの順でやるか

シニアSE が Claude Code とタスクを分解し、以下が作成されます：

| 成果物 | 内容 |
|--------|------|
| `tasks.md` | タスク一覧、依存関係、マイルストーン |

**実施担当者が知っておくべきこと:**
- 各タスクの `plan_refs` が plan.md の stable ID を参照している
- タスクの依存関係（`depends_on`）が WI の実行順を決定する

> **Gate 5 が承認されると、Claude Code が tasks.md をもとに Work Item（WI）を自動分割し、Execute Phase が始まります。** ここからが実施担当者の出番です。

---

### 3.2 Execute Phase — 実施担当者の主戦場

> Gate 5 の承認が完了すると Execute Phase に入ります。ここが実施担当者の本番です。
> §2 のシナリオはこの Phase の中盤からの話でした。ここでは WI 作成から順に解説します。

#### 3.2.1 Work Item の作成

Claude Code が tasks.md をもとに WI を自動分割・作成します。

```
鈴木: 「WI の一覧を見せてください。risk_flags と Mode を確認したいです。」

Claude Code:
  Work Items:
  ┌─────────────────────┬──────────────────┬───────────────┬───────────┐
  │ WI ID               │ risk_flags       │ 推奨 Mode     │ 最終 Mode │
  ├─────────────────────┼──────────────────┼───────────────┼───────────┤
  │ WI-WEB-EDI-001      │ [ui_only]        │ autopilot     │ autopilot │
  │ WI-WEB-EDI-002      │ [new_api]        │ confirm       │ autopilot │ ← override
  │ WI-WEB-EDI-003      │ [db_schema,      │ validate      │ validate  │
  │                     │  data_migration] │               │           │
  └─────────────────────┴──────────────────┴───────────────┴───────────┘

  ⚠️ WI-WEB-EDI-002: policy(confirm) より弱い autopilot に override されています。
     理由: "API は既存パターンの踏襲で影響範囲が限定的"
```

> 鈴木さんは override の理由が妥当かレビューするだけ。risk_flags と Mode の対応表は → [Appendix A.6](#a6-risk_flags-と-mode-の対応) を参照。

> 📖 **WI ファイルの YAML 構造を理解したい場合**: → [Appendix A.5](#a5-wi-ファイル構造) を参照

#### 3.2.2 wi_readiness_checker

Claude Code が WI 実装前に自動で実行します。

```
鈴木: 「WI-WEB-EDI-002 の実行準備を確認してください。」

Claude Code:
  readiness check:
  [1/5] WI file exists .................. PASS
  [2/5] Risk flags valid ................ PASS
  [3/5] Mode matches policy ............. PASS
  [4/5] Dependencies resolved ........... PASS
  [5/5] Pre-run approval ................ N/A (autopilot)
  Result: READY
```

> NOT_READY の場合、Claude Code が何が足りないか報告します。「対処してください」と伝えれば自動修正。

#### 3.2.3 Run の実行フロー

Claude Code がすべて自律実行します。実施担当者は ⛔ マークのポイントでのみ介入します。

```
1. [Claude Code] Run ディレクトリ作成
2. ⛔ [confirm/validate の場合] 事前承認を取得 — 人間が承認
3. [Claude Code] 実装（spec_refs の全 AC の全要素を満たすコード）
4. [Claude Code] テスト作成・実行
5. [Claude Code] Walkthrough 作成
6. [Claude Code] stride-lint 実行 → エラーがあれば自動修正
7. [Claude Code] Run Report 生成
8. ⛔ 承認依頼 → 人間が WI-*.approval.md を編集
9. [Claude Code] state.yaml を done に更新
```

> **重要**: 「動いた」≠「完了」。AC の**全要素**を満たして初めて完了。

#### 3.2.4 Walkthrough のレビューとフィードバック

> **§2 のシナリオ（10:30）で一連の流れを体験しました。** ここでは体系的にまとめます。
> **承認は「内容に問題がない」ことを確認してから行う。** 不備があれば承認せず、修正を指示します。

##### Walkthrough の確認ポイント

まず Claude Code に対照表を出させるのが最も効率的です：

```
「AC の then 条件と Evidence の実際の結果を対照表にして、
 一致/不一致を判定してください。」
```

対照表が出たら、以下の観点で ❌（不一致）の項目と全体の品質を確認します：

| 確認観点 | 確認方法 | 不備の例 |
|---------|---------|---------|
| **AC ↔ Evidence の一致** | 対照表の ❌ を確認 | テスト PASS でもステータスコードが AC と不一致 |
| **What の具体性** | 読んで「何が変わったか」を一言で説明できるか | 「改善した」だけで具体性がない |
| **How to Verify の再現性** | 「自分がこの手順だけで検証できるか？」を想像する | 手順が曖昧、前提条件の記載がない |
| **Coverage の充足** | tier 別目標を満たしているか | LIB が 85%/75% 未満 |

> **レビューの基本動作**: Claude Code に対照表を出させる → ❌ の項目を修正指示 → 全体の品質を確認。

##### 不備を見つけた時のフィードバックフロー

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Code: 「WI-WEB-EDI-002 の承認をお願いします。」       │
├─────────────────────────────────────────────────────────────┤
│ 実施担当者: walkthrough.md をレビュー                        │
│                                                             │
│   問題なし？                                                │
│   ├── Yes → approval.md を [x] に → 「承認しました」        │
│   └── No  → 具体的にフィードバック → Claude Code が修正      │
│             → 再レビュー → 問題なし？ → ...（ループ）        │
└─────────────────────────────────────────────────────────────┘
```

> **重要**: 不備がある状態で承認してはいけません。承認 = 「この成果物は品質基準を満たしている」という判断です。

##### ケース別フィードバックの例

**ケース1: walkthrough の記述が不十分**

**発見方法**: Claude Code にチェックさせる。

```
実施担当者: 「walkthrough の How to Verify を検証してください。
            第三者がこの手順だけで再現できるか確認し、
            不足している情報（URL、リクエスト例、期待値、前提条件）を
            指摘してください。不足があれば補完してください。」

Claude Code:
  How to Verify を検証します...

  ⚠️ 不足を発見:
  - 手順2: 「APIを叩く」だけで、リクエストボディと期待レスポンスがない
  - 手順3: 前提条件（在庫不足のテストデータ設定方法）が未記載

  補完して修正します...（修正完了）
```

**ケース2: 実装が AC を満たしていない**

**発見方法**: Claude Code に対照表を出させ、❌ の項目を確認する。テストが PASS していてもアサーションが甘い場合があるため、対照表の「実際の値」を注視する。

```
実施担当者: 「AC-...-02 が不一致です。修正してください。
            テストのアサーションでステータスコードも検証してください。」

Claude Code:
  確認しました。テストのアサーションがステータスコードを検証していませんでした。
  
  [1/4] src/api/orders.py: StockShortageError の catch を追加 → 409 返却
  [2/4] TS-INT-02: assert response.status_code == 409 を追加
  [3/4] テスト再実行: TS-INT-02 PASS（409 を確認）
  [4/4] walkthrough.md の Evidence を更新
  
  修正完了しました。stride-lint: PASS
  再度ご確認ください。
```

**ケース3: テスト自体が不十分**

**発見方法**: Claude Code に境界値分析をさせる。

```
実施担当者: 「各 AC の given/when/then に対して、テストが境界値や
            異常系をカバーしているか分析してください。
            不足しているテストケースがあれば追加してください。」

Claude Code:
  境界値分析:
  ┌──────────────────┬──────────────────────┬─────────────────┬──────┐
  │ AC ID            │ 条件                  │ テスト状況       │ 判定 │
  ├──────────────────┼──────────────────────┼─────────────────┼──────┤
  │ AC-...-01 given  │ 有効な商品ID+数量      │ 正常系1件のみ    │ ⚠️  │
  │                  │ → 数量0              │ 未テスト         │      │
  │                  │ → 数量上限            │ 未テスト         │      │
  │                  │ → 無効な商品ID         │ 未テスト         │      │
  │ AC-...-02 given  │ 在庫不足の数量         │ テスト済み       │ ✅   │
  └──────────────────┴──────────────────────┴─────────────────┴──────┘

  3件のテストを追加します...（追加完了）
  カバレッジ: LIB-01 87% → 91% に向上
```

**ケース4: 設計判断に疑問がある（Run Report の Decisions）**

**発見方法**: Claude Code に SDD の 9 Articles との整合チェックをさせる。

```
実施担当者: 「Run Report の Decisions を SDD の 9 Articles に照らして
            セルフチェックしてください。違反があれば指摘してください。」

Claude Code:
  Decisions × 9 Articles チェック:
  ┌───┬──────────────────────────────┬────────────────┬──────┐
  │ # │ 判断内容                      │ 関連 Article   │ 判定 │
  ├───┼──────────────────────────────┼────────────────┼──────┤
  │D-1│ バリデーションをAPI層で実施     │ Art.I Library- │ ❌   │
  │   │                              │ First          │      │
  │   │ → ビジネスロジックはLIBに集約  │                │      │
  │D-2│ 在庫チェックは同期APIで実施    │ Art.V Module   │ ✅   │
  └───┴──────────────────────────────┴────────────────┴──────┘

  ⚠️ D-1 が Article I（Library-First）に違反しています。
  バリデーションロジックを LIB-01 に移動しますか？

実施担当者: 「はい、移動してください。」
```

##### レビューの効率化パターン

| やり方 | プロンプト例 |
|--------|------------|
| **AC↔Evidence 照合** | 「ACのthen条件とEvidenceの実際の結果を対照表にして、一致/不一致を判定して」 |
| **How to Verify 検証** | 「第三者がこの手順だけで再現できるか検証して。不足があれば補完して」 |
| **境界値テスト分析** | 「各ACのgiven/whenの境界値・異常系テストが足りているか分析して。不足は追加して」 |
| **Decisions × Articles チェック** | 「DecisionsをSDDの9 Articlesに照らしてセルフチェックして。違反があれば指摘して」 |
| **全体セルフチェック** | 「walkthrough全体を品質チェックして。問題があれば修正して」 |

> **原則**: 自分で目視確認する前に、まず Claude Code にチェックさせる。
> Claude Code が ✅ を返した項目は信頼し、⚠️/❌ の項目だけ人間が判断する。
> 人間の仕事は「チェック作業」ではなく「判断」。

#### 3.2.5 Mode 別チェックポイント

| Mode | Pre-Run（実装前） | Post-Run（実装後） |
|------|-------------------|-------------------|
| **autopilot** | なし | walkthrough + CI + ops review |
| **confirm** | plan_review | walkthrough + CI + ops review |
| **validate** | design_diff + plan_review | walkthrough + CI + ops review |

> 全 Mode で Post-Run の walkthrough_review / ci_pass / ops_review は**必須**。
> Autonomy Bias による Mode シフトの詳細 → [Appendix A.7](#a7-autonomy-bias-テーブル) を参照。

#### 3.2.6 Run Resume（中断からの再開）

```
鈴木: 「WI-WEB-EDI-002 の Run を再開してください。」

Claude Code:
  既存アーティファクトを検出...
  - walkthrough.md: あり
  - test_results.md: なし
  → テスト実行から再開します。よろしいですか？

鈴木: 「はい、お願いします。」
```

> **注意**: 再開はユーザーの確認後のみ実行。自動再開はしません。

#### 3.2.7 Run Report と PM 連携

Claude Code が Run 完了時に自動で生成します。Run Report は GitHub Issue にラベルとして自動反映され、**PM のダッシュボード（STRIDE Board）に連動**します。

##### Run Report の構成

| セクション | 内容 | ラベル例 |
|-----------|------|---------|
| **Findings** | 実装中に見つかった問題点 | `findings:0` / `findings:1-3` / `findings:4+` |
| **Decisions** | AI / 人間が行った技術判断 | `decisions:0` / `decisions:1-3` / `decisions:4+` |
| **Spec Impact** | 仕様変更の要否 | `spec-impact:none` / `proposed` / `required` |
| **Lessons** | 再利用可能なパターン | `learning:pattern` |

##### 実施担当者と PM の役割分担

Run Report のレビューは**実施担当者（TL）と PM で役割が分かれて**います。

```
Claude Code が Run Report 生成 → GitHub Issue にラベル自動付与
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ↓                                           ↓
          実施担当者（一次レビュー）                     PM（二次レビュー）
          ─────────────────────                     ──────────────────
          ✅ Findings の技術的解消                   📊 Findings ビューで
             （修正が必要なら Claude Code               異常 WI を特定
              に指示して解消する）                       （findings:4+ に注目）

          ✅ Decisions の技術面レビュー              📊 Decisions ビューで
             （Article 違反がないか、                   判断が多い WI を特定
              設計原則に沿っているか）                   （decisions:4+ に注目）
                                                    ✅ ビジネス影響のレビュー
                                                       （コスト、スケジュール、
                                                        スコープへの影響）

          ✅ テスト品質の確認                        📊 Spec Impact ビューで
             （AC 照合、カバレッジ）                     仕様変更の要否を判断
                                                    ✅ Amendment の起案・承認
                   │                                           │
                   └──── WI 承認（approval.md）────────────────┘
                                                    └──── Gate 承認（APPROVAL.md）
```

##### Findings の対処手順

Findings は実装中に Claude Code が発見した問題点です。実施担当者が Claude Code と協力して解消します。

**Step 1: Run Report の Findings を確認する**

```
実施担当者: 「WI-WEB-EDI-002 の Run Report を見せてください。
            Findings の一覧を確認したいです。」

Claude Code:
  📋 Findings (3件)
  ┌───┬──────────────┬────────────────────────────────────────┬────────┐
  │ # │ 種別         │ 発見内容                                │ 影響度 │
  ├───┼──────────────┼────────────────────────────────────────┼────────┤
  │F-1│ schema       │ 通貨コード情報が API レスポンスに欠落     │ high   │
  │F-2│ performance  │ 大量データ時にバリデーションが遅い          │ medium │
  │F-3│ data_quality │ 商品コードの表記揺れ（全角/半角混在）      │ low    │
  └───┴──────────────┴────────────────────────────────────────┴────────┘
```

**Step 2: 影響度別に対処を判断する**

| 影響度 | 実施担当者のアクション |
|--------|---------------------|
| **high** | 今の WI 内で対応できるか判断。仕様変更が必要なら PM にエスカレーション |
| **medium** | 今の WI 内で対応するか、次の WI に回すか判断 |
| **low** | 次の WI やバックログに回してよい |

**Step 3: 対応方針を決めて Claude Code に指示する**

```
実施担当者: 「F-1 は通貨コードが spec.md に未定義なので、仕様変更が必要です。
            これは PM にエスカレーションします。
            F-2 はバリデーションをバルク処理に最適化してください。
            F-3 は低優先度なのでバックログに回します。」

Claude Code:
  了解しました。

  F-1: spec-impact:required としてマークしました。
       PM にエスカレーションしてください。

  F-2: バリデーションを最適化します...
       [1/2] バルク処理用のバッチバリデーション関数を追加
       [2/2] テスト再実行: PASS（処理時間 1200ms → 180ms）
       F-2 を resolved としてマークしました。

  F-3: backlog としてマークしました。
```

**Step 4: 仕様変更が必要な場合は PM にエスカレーション**

```
実施担当者: 「田中PMへ — WI-WEB-EDI-002 の F-1 で通貨コード情報の欠落が
            判明しました。spec.md に通貨コードフィールドの追加が必要です。
            Amendment をお願いできますか？」
```

PM は [STRIDE Board の Spec Impact ビュー](05_pm_operations_guide.md) で確認し、Amendment を起案します。

---

##### Decisions の対処手順

Decisions は AI（または人間）が実装中に行った技術判断の記録です。実施担当者が技術面を一次レビューし、ビジネス判断が必要なものは PM に報告します。

**Step 1: Run Report の Decisions を確認する**

```
実施担当者: 「Run Report の Decisions を見せてください。」

Claude Code:
  📝 Decisions (4件)
  ┌───┬─────────────────────────────────────────────┬──────────┐
  │ # │ 判断内容                                     │ ステータス│
  ├───┼─────────────────────────────────────────────┼──────────┤
  │D-1│ バリデーションをドメイン層（LIB-01）に実装    │ accepted │
  │D-2│ 在庫チェックは非同期ではなく同期 API で実施   │ accepted │
  │D-3│ 多通貨対応は Phase 2 に先送り                │ proposed │ ← 要確認
  │D-4│ エラーレスポンスの形式を RFC 7807 に準拠      │ accepted │
  └───┴─────────────────────────────────────────────┴──────────┘
```

**Step 2: Claude Code に自動チェックさせる**

```
実施担当者: 「Decisions を以下の観点でセルフチェックして対照表にしてください。
            1. SDD 9 Articles との整合性
            2. spec.md / plan.md との矛盾
            3. ビジネス影響（スコープ・コスト・スケジュール）
            4. 技術的リスク（パフォーマンス・セキュリティ）」

Claude Code:
  Decisions セルフチェック:
  ┌───┬──────────────────────┬─────────┬──────────┬──────────┬──────┐
  │ # │ 判断内容              │Articles │spec整合 │ビジネス影響│技術Risk│
  ├───┼──────────────────────┼─────────┼──────────┼──────────┼──────┤
  │D-1│ LIB-01にバリデーション│ ✅      │ ✅      │ なし     │ 低   │
  │D-2│ 在庫チェック同期API   │ ✅      │ ✅      │ なし     │ ⚠️   │
  │   │                      │         │          │          │注1   │
  │D-3│ 多通貨→Phase 2先送り │ ✅      │ ⚠️ spec │ ⚠️ スコープ│ —   │
  │   │                      │         │ 未定義   │ 影響あり  │      │
  │D-4│ RFC 7807エラー形式   │ ✅      │ ✅      │ なし     │ 低   │
  └───┴──────────────────────┴─────────┴──────────┴──────────┴──────┘
  注1: 日次2000件超で非同期化が必要。NFRに閾値追記を推奨。

  ⚠️ D-3 はビジネス影響あり（スコープ変更）→ PM判断が必要です。
  ⚠️ D-2 は技術的リスクあり → NFRに閾値を追記しますか？
```

> 実施担当者は ⚠️ だけ確認。D-2 は「追記してください」で解決。D-3 は PM にエスカレーション。

**Step 3: ビジネス判断が必要な Decisions は PM に報告**

ステータスが `proposed`（提案中）で、スコープ・スケジュール・コストに影響する判断は PM の確認が必要です。

```
実施担当者: 「田中PMへ — WI-WEB-EDI-002 の D-3 で、多通貨対応を
            Phase 2 に先送りする判断をしています。
            現在の spec.md は単一通貨のみの定義です。
            多通貨が Phase 1 のスコープに必要かどうか、ご判断をお願いします。」
```

PM が「Phase 2 でよい」と判断すれば D-3 は `accepted` に。
PM が「Phase 1 で対応必要」と判断すれば、Amendment を起案して spec.md を更新します。

---

##### Spec Impact の対処

| ラベル | 実施担当者のアクション |
|--------|---------------------|
| `spec-impact:none` | 対応不要 |
| `spec-impact:proposed` | 内容を確認し、PM にエスカレーションが必要か判断 |
| `spec-impact:required` | **PM に即報告**。PM が Amendment を起案 → 承認後に Claude Code が spec を更新 |

---

##### Lessons の共有

再利用可能なパターンが見つかった場合、チーム内で共有します。

```
実施担当者: 「Run Report の Lessons に 'RFC 7807 エラーレスポンスパターン' が
            記録されています。他の WI でも使えるので共有します。」
```

PM は 📚 Learnings ビューで確認できます。

> **参考**: PM がどのようにこれらのラベルを使ってプロジェクトを管理するかは、[PM向けガイド（§05）](05_pm_operations_guide.md) の「PMの1日」シナリオで詳しく解説されています。

---

### 3.3 Final Phase — PR Ready へ

> **Goal**: 全 WI が done → Claude Code が evidence_pack と pr-check を自動実行 → Final Gate 承認 → PR 作成。

```
鈴木: 「全 WI が完了しました。Final Phase の準備をしてください。」

Claude Code:
  Final Phase を開始します...

  [1/3] evidence_pack.md を生成中...
        CI: PASS (12/12 tests)
        Coverage: AC 100%, CT 100%, Code LIB-01 87%/78%
        SAST/SCA: 0 Critical, 0 High
        AI Provenance: Anthropic/claude-code, claude-opus-4-7, xhigh/adaptive, v5.2.0

  [2/3] Ops Pack を確認中...
        transport_manifest.yaml: ✅
        release_checklist.md: ✅
        rollback_plan.md: ✅
        hypercare_runbook.md: ✅

  [3/3] stride pr-check を実行中...
        ┌───┬──────────────┬────────┐
        │ # │ チェック      │ 結果   │
        ├───┼──────────────┼────────┤
        │ 1 │ stride-lint  │ PASS   │
        │ 2 │ spec:drift   │ PASS   │
        │ 3 │ tests        │ PASS   │
        │ 4 │ coverage     │ PASS   │
        │ 5 │ walkthrough  │ PASS   │
        │ 6 │ evidence_pack│ PASS   │
        │ 7 │ TODO/FIXME   │ PASS   │
        └───┴──────────────┴────────┘

  PR_READY (exit 0) 🎉
  Final Gate の承認をお願いします。
  承認後、PR を作成しますか？

鈴木: （APPROVAL.md で Final Gate を承認）
      「承認しました。PR を作成してください。」

Claude Code:
  PR #42 を作成しました: "feat(web-edi): Web-EDI受注受付機能"
  reviewers: @tanaka
```

> 📖 **Evidence Pack / Ops Pack のテンプレート**: → [Appendix A.8](#a8-evidence-pack-テンプレート), [Appendix A.9](#a9-ops-pack-構成) を参照

---

## 4. Claude Code への効果的な指示の出し方

> §3 で多くのプロンプト例を見てきました。ここでは**パターン**を整理します。

### 4.1 プロンプトの3パターン

| パターン | いつ使う | テンプレート |
|---------|---------|------------|
| **要件伝達** | 新機能を開始する時 | 【機能名】【誰が使う】【何をする】【なぜ必要】【関連システム】【制約】 |
| **修正依頼** | 成果物に問題がある時 | 「○○を修正してください。変更内容:〜 理由:〜 修正後 stride-lint を実行して」|
| **セルフチェック依頼** | レビュー前に品質を確認する時 | 「○○のセルフチェックをしてください。以下の観点で対照表にして：1. ... 2. ...」 |

### 4.2 AI が自動修正するもの vs 人間の判断が必要なもの

| AI が自動修正 | 人間の判断が必要 |
|-------------|----------------|
| 構造エラー（必須セクション欠落） | APPROVAL_PENDING（承認ファイル編集） |
| counts と実際の定義数の不一致 | WI_APPROVAL_PENDING |
| プレースホルダ残留（XXX, NNN, TODO） | blocking questions への回答 |
| テストの軽微な修正と再実行 | アーキテクチャ変更の判断 |
| lint WARN の修正 | セキュリティ方針の決定 |

### 4.3 陥りがちな罠と対策

| 罠 | 対策 |
|-----|------|
| AI の出力を検証せずにコミット | walkthrough で AC 照合。対照表で ❌ を確認 |
| プロンプトが曖昧で不完全な成果物 | 入力例・期待出力・制約を必ず含める |
| Gate 承認前に次 Phase のファイル作成 | stride-lint が Phase Gate 違反を検出。従う |
| 承認済み成果物を AI に変更させる | 再承認プロセスを経る（change_log.md 記録 + 再承認） |

---

## 5. stride-lint エラーガイド

> **基本**: stride-lint エラーが出たら「stride-lint のエラーを修正してください」と Claude Code に伝えるだけで解決します。
> 人間が対応するのは **`APPROVAL_PENDING` / `WI_APPROVAL_PENDING`**（承認ファイルの編集）のみ。

### 5.1 APPROVAL_PENDING の扱い方

```
stride-lint → PASS (structural) → FAIL (APPROVAL_PENDING)
```

これは**正常な動作**です。構造チェックは通過し、承認だけが pending の状態。

- **やること**: APPROVAL.md / WI-*.approval.md のチェックボックスを `[x]` に変更
- **やらないこと**: AI が APPROVAL.md を編集する（**絶対禁止** — INVIOLABLE ルール）

### 5.2 その他のエラー

`APPROVAL_PENDING` 以外のエラーは全て「このエラーを修正してください」で Claude Code が自動修正します。

> 📖 **全エラーコードの一覧が必要な場合**: → [Appendix B](#appendix-b-stride-lint-エラーコード全一覧) を参照

---

## 6. テスト実装ガイド

> テストの実装・実行は Claude Code が自律的に行います。
> このセクションは Claude Code の出力をレビューするためのリファレンスです。

### 6.1 Coverage Policy の3層管理

| Layer | 対象 | 目標 | 検証方法 |
|-------|------|------|---------|
| **Layer 1: AC Coverage** | 全 AC が TS でカバーされるか | **100% 必須** | stride-lint が AC↔TS のマッピングを検証 |
| **Layer 2: CT Coverage** | 全 CT が TS-CON でカバーされるか | **原則 100%** | stride-lint が CT↔TS-CON のマッピングを検証 |
| **Layer 3: Code Coverage** | 行/分岐カバレッジ | tier 別目標（例: LIB 85%/75%） | CI で `coverage xml` を出力し検証 |

### 6.2 Tier 別カバレッジ要件

| Tier | AC | CT | Code (line/branch) | E2E | autopilot |
|------|----|----|---------------------|-----|-----------|
| **critical** | 100% | 100% | 85%/75% | 必須 | **禁止** |
| **standard** | 100% | 80% | 70%/60% | 任意 | 可能 |
| **experimental** | 80% | 60% | 50%/40% | 不要 | 可能 |

### 6.3 テスト結果の確認

```
鈴木: 「テストの実行結果とカバレッジを見せてください。」

Claude Code:
  テスト結果:
  ┌───────────┬───────┬──────────┐
  │ テスト種別 │ 件数  │ 結果     │
  ├───────────┼───────┼──────────┤
  │ TS-UT-*   │ 8     │ 8 PASS   │
  │ TS-CON-*  │ 3     │ 3 PASS   │
  │ TS-INT-*  │ 2     │ 2 PASS   │
  │ TS-E2E-*  │ 1     │ 1 PASS   │
  └───────────┴───────┴──────────┘

  カバレッジ:
  - LIB-01: 87% line / 78% branch (目標: 85%/75%) ✅
  - CMP-01: 65% line / 55% branch (目標: 60%/50%) ✅
```

> **テストは `specs/<feature>/tests/` に配置**（ルートの `tests/` ではない）。

> 📖 **Python / TypeScript のテストコード例が必要な場合**: → [Appendix C](#appendix-c-テストコード例) を参照

---

## 7. ID 規約クイックリファレンス

使用頻度の高い順に並べています。

| 種類 | フォーマット | 正規表現 | 例 |
|------|------------|---------|-----|
| **Feature** | `FEAT-XXX` or `FEAT-ORD-001` | `^FEAT-(?:[A-Z]{2,4}-)?[A-Z0-9]{3,}$` | `FEAT-WEB-EDI-001` |
| **Use Case** | `US-FEATXXX-NNN` | `^US-FEAT[A-Z0-9]{3,}-[0-9]{3}$` | `US-FEATWEB-EDI-001-001` |
| **Acceptance** | `AC-US-FEATXXX-NNN-NN` | `^AC-US-FEAT[A-Z0-9]{3,}-[0-9]{3}-[0-9]{2}$` | `AC-US-FEATWEB-EDI-001-001-01` |
| **Task** | `T-XX-NNN` | `^T-[A-Z0-9]{2,}-[0-9]{3}$` | `T-VAL-001` |
| **Work Item** | `WI-FEAT-XXX-NNN` | — | `WI-WEB-EDI-002` |
| **Contract** | `CT-TYPE-NN` | `^CT-(API\|CLI\|EVT\|FILE\|BATCH\|EDI\|IDOC\|DB)-[0-9]{2}$` | `CT-API-01` |
| **Test** | `TS-TYPE-NN` | `^TS-(CON\|INT\|E2E\|UT)-[0-9]{2}$` | `TS-INT-01` |
| **Requirement** | `RQ-NNN` | `^RQ-[0-9]{3}$` | `RQ-001` |
| **Component** | `CMP-NN` | `^CMP-[0-9]{2}$` | `CMP-01` |
| **Library** | `LIB-NN` | `^LIB-[0-9]{2}$` | `LIB-01` |
| **Phase** | `Phase-N` | `^Phase-[0-9]+$` | `Phase-1` |
| **Group** | `G-NN-name` | `^G-[0-9]{2}-[a-z0-9-]+$` | `G-01-validation` |
| **BPMN Process** | `BPMN-PROC-XXX` | `^BPMN-PROC-[A-Z0-9]{3,}$` | `BPMN-PROC-WEBEDI` |
| **Milestone** | `M-NN` | `^M-[0-9]{2}$` | `M-01` |

### 命名のコツ

- **Feature ID**: プロジェクト内で重複しない略称を使う（`WEB-EDI`, `ORD`, `INV`）
- **Task ID**: 担当領域の略称をプレフィックスに（`VAL`, `ERP`, `E2E`）
- **ゼロ埋め**: 3桁以上で統一（`001`, `010`, `100`）→ ソート順が自然になる

---

## 8. トラブルシューティング

**基本**: 問題が起きたら、まず Claude Code に解決させる。

```
「stride-lint で〇〇エラーが出ました。原因を特定して修正してください。」
「wi_readiness_checker が NOT_READY です。何が足りないか確認して対処してください。」
```

ほとんどの問題は Claude Code が自律解決します。以下は **Claude Code では解決できない、人間の判断が必要な問題** のみをまとめたものです。

### Claude Code に任せれば解決する問題

以下のエラーが出た場合は「このエラーを修正してください」と伝えるだけで解決します：

`COUNTS_SUGGESTION` / `STATE_WI_MISMATCH` / `WALKTHROUGH_MISSING` / `OPS_PACK_MISSING` / `RUN_MULTIPLE` / `WI_SCHEMA_INVALID` / `WARN_SPEC_LINK_NOT_FOUND` / `spec:drift` / テスト失敗 / E2E flaky / conftest 問題 / OpenAPI validation / pytest 競合

### 人間の判断・操作が必要な問題

| # | 症状 | なぜ人間が必要か | 対処 |
|---|------|----------------|------|
| 1 | `PHASE_GATE_BLOCKED` | 承認は人間のみ | APPROVAL.md を確認し、該当 Gate を承認 |
| 2 | `APPROVAL_PENDING` / `WI_APPROVAL_PENDING` | 承認は人間のみ | APPROVAL.md / approval.md を編集 |
| 3 | `APPROVAL.md` を AI が編集してしまった | INVIOLABLE ルール違反 | `git revert` で取り消し、人間が正しく編集 |
| 4 | `AUTOPILOT_FORBIDDEN_BY_TIER` | Mode の変更はリスク判断 | risk_flags と coverage_tier を確認し、mode を `confirm` 以上に変更するか Claude Code に指示 |
| 5 | `MODE_OVERRIDE_REASON_MISSING` | Override の理由は業務判断 | なぜ policy より弱い mode にするのか理由を Claude Code に伝え、記載させる |
| 6 | Gate 承認後に仕様変更が必要 | Amendment は PM の承認が必要 | PM にエスカレーションし、Amendment 起案を依頼 |
| 7 | 依存 WI が完了しない（ブロック状態） | 優先度判断 | PM と相談し、依存の解消方法を決定 |
| 8 | AI がコンテキストを失っている | — | 「CLAUDE.md を読み直してください」と伝える |
| 9 | Git コンフリクト（state.yaml） | マージ判断 | Claude Code に「コンフリクトを解決してください」と伝える（判断が必要な場合は相談される） |

---

## 9. ベストプラクティス集

### 9.1 WI 分割のコツ

- **1 WI = 1〜2 日** で完了できる規模に分割
- **リスクの異なる変更は別 WI** に分ける（ui_only と db_schema を混ぜない）
- **依存関係は最小限** に（循環依存は禁止）
- **Spec Links と DoD を明確に** — 何を満たせば「完了」か誰でもわかるように

### 9.2 Walkthrough の質を上げるコツ

- **What**: ファイル名と具体的な変更内容（「改善した」ではなく「○○関数を追加した」）
- **Why**: 必ず AC / RQ の ID を引用する
- **How to Verify**: 第三者が再現できるステップバイステップ
- **Evidence**: テスト結果は Pass/Fail + カバレッジ数値。スクリーンショットはパスを明記

### 9.3 テスト戦略のコツ

- **テストピラミッド**: Unit（70%）→ Integration（20%）→ E2E（10%）
- **テストデータ**: fixture / factory で管理。ハードコードしない
- **E2E は最小限**: `e2e` タグ付き AC のみ。全フローを E2E にしない
- **CI で必ず実行**: ローカルだけでなく CI パイプラインに組み込む

### 9.4 Mode の選び方フローチャート

```
risk_flags に高リスクがある？
  ├── Yes → validate
  └── No → risk_flags に中リスクがある？
              ├── Yes → confirm
              └── No → autopilot

coverage_tier が critical？
  └── Yes → 最低でも confirm（autopilot 禁止）

autonomy_bias を考慮（balanced なら変更なし）
```

### 9.5 実施担当者としてのセルフチェック

WI 完了前に Claude Code に以下を聞くだけで済みます：

```
「この WI の完了前チェックをしてください。
 AC↔Evidence照合、stride-lint、Coverage、walkthrough品質、
 Run Report の Findings/Decisions 全てまとめて報告してください。」
```

Claude Code が全項目をチェックし、⚠️/❌ がなければ承認に進めます。
人間が判断すべきのは以下のみ：

- [ ] **業務判断**: blocking questions に回答したか？
- [ ] **承認**: APPROVAL.md / WI-*.approval.md を承認したか？
- [ ] **PM連携**: spec-impact:required があれば PM にエスカレーションしたか？
- [ ] **Decisions**: proposed ステータスでビジネス影響のある判断を PM に報告したか？

---

## 10. 用語集

| 用語 | 読み方 | 説明 |
|------|--------|------|
| **SDD** | エスディーディー | Specification-Driven Development — 仕様駆動開発 |
| **STRIDE** | ストライド | State-Tracked Run Intent-Driven Engineering — テクノス独自メソッド |
| **Spec** | スペック | 仕様書（spec.md）— WHAT/WHY を定義 |
| **Plan** | プラン | 実装計画（plan.md）— HOW を定義 |
| **Tasks** | タスクス | タスク分解（tasks.md）— DO を定義 |
| **Gate** | ゲート | 品質チェックポイント。人間の承認が必須 |
| **HITL** | ヒットル | Human-in-the-Loop — Gate での人間承認 |
| **WI** | ダブリューアイ | Work Item — Execute Phase の実行単位 |
| **Run** | ラン | WI の実行証跡（1 WI = 1 Run） |
| **Mode** | モード | 承認儀式の厳格度（autopilot / confirm / validate） |
| **AC** | エーシー | Acceptance Criteria — 受入条件 |
| **US** | ユーエス | Use Case — ユースケース |
| **CT** | シーティー | Contract — システム間の通信ルールの定義（法的契約ではない） |
| **TS** | ティーエス | Test Specification — テスト仕様 |
| **NFR** | エヌエフアール | Non-Functional Requirements — 非機能要件 |
| **SSoT** | エスエスオーティー | Single Source of Truth — 唯一の正本 |
| **Canonical YAML** | カノニカルヤムル | 成果物の正本となる YAML ブロック |
| **Evidence Pack** | エビデンスパック | 品質証跡の集合（CI/テスト/SAST/SCA/AI出自） |
| **Ops Pack** | オプスパック | 運用パック（輸送/リリース/ロールバック/ハイパーケア） |
| **Autonomy Bias** | オートノミーバイアス | プロジェクトの自律性嗜好による Mode 自動調整 |
| **stride-lint** | ストライドリント | SDD 品質ゲートの機械検証ツール |
| **RACI+** | レイシープラス | 責務分担モデル（AI と CI の列を追加） |
| **R (Responsible)** | — | 実行者（v4.4 では Claude Code） |
| **A (Accountable)** | — | 承認者（人間のみ。AI は A になれない） |
| **Phase Gate** | フェイズゲート | Phase 間の進行制御。未承認では次 Phase に進めない |

---

## 11. 関連ドキュメントマップ

```
どのガイドをいつ読むか？

┌─────────────────────────────────────────────────────────────────┐
│ 初めて参加するとき                                              │
│   → 01_getting_started.md（SDD の基本）                         │
│   → 07_practitioner_execution_guide.md（★ 本ガイド）            │
├─────────────────────────────────────────────────────────────────┤
│ Design Phase の作業中                                           │
│   → 09_basic_design_guide.md（basic_design.md の詳細）          │
│   → 10_bpmn_guide.md（BPMN の作成方法）                        │
├─────────────────────────────────────────────────────────────────┤
│ Specify Phase の作業中                                          │
│   → 11_spec_guide.md（spec.md の詳細）                         │
│   → 12_plan_guide.md（plan.md の詳細）                         │
│   → 19_coverage_policy.md（Coverage Policy の詳細）             │
├─────────────────────────────────────────────────────────────────┤
│ Tasking Phase の作業中                                          │
│   → 13_tasks_guide.md（tasks.md の詳細）                       │
├─────────────────────────────────────────────────────────────────┤
│ Execute Phase の作業中                                          │
│   → 27_erp_addon_playbook.md（ERP 向け実行追跡メソッド）        │
│   → 17_adaptive_execution_guide.md（Autonomy Bias / Run Resume）│
│   → 18_execution_governance_guide.md（Auto-Continue / DDD）     │
├─────────────────────────────────────────────────────────────────┤
│ Final Phase・PR 作成時                                          │
│   → 14_evidence_pack_guide.md（Evidence Pack の詳細）           │
│   → 22_pr_readiness_guide.md（PR Readiness の 7 チェック）      │
├─────────────────────────────────────────────────────────────────┤
│ AI 自律実行の詳細を知りたいとき                                  │
│   → 15_ai_autonomous_execution_guide.md（v4.4 AI 自律実行）     │
├─────────────────────────────────────────────────────────────────┤
│ 上流工程（Design → Specify → Tasking）を担当するとき            │
│   → 06_upstream_phase_guide.md（シニアSE・アーキテクト向け）     │
├─────────────────────────────────────────────────────────────────┤
│ PM 視点でプロジェクト管理したいとき                              │
│   → 05_pm_operations_guide.md（PM 向け）                     │
├─────────────────────────────────────────────────────────────────┤
│ ID 規約・lint の詳細                                            │
│   → appendix_a_id_conventions.md（ID 規約の正規表現全文）               │
│   → appendix_b_stride_lint.md（stride-lint の全ルール）                 │
├─────────────────────────────────────────────────────────────────┤
│ 組織制約（監査/運用/ERP）                                       │
│   → memory/constitution.md（憲法）                              │
│   → memory/tecnos_org_constraints.md（テクノス組織制約）         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Appendix A: YAML テンプレート＆リファレンス

> §3 から参照されるテンプレート集。Claude Code が自動生成する成果物の構造を理解したい時に参照してください。
> 通常の運用では読む必要はありません。

### A.1 basic_design.md Canonical YAML

```yaml
artifact: "basic_design"
feature_id: "FEAT-WEB-EDI-001"
version: "0.1.0"
status: "draft"

context:
  who: "取引先の購買担当者（約80社）"
  what: "Web-EDIで発注データを受け付け、ERPに自動登録し、受注番号と納期回答を返す"
  why: "現状はメール/Excelで受注を手入力しており、1件20分・誤入力1%が発生"

delivery_model:
  type: "agile"     # agile | waterfall | ddd
  iteration_length: "2 weeks"

raci_plus:
  pm: { name: "田中PM", role: "A" }
  tech_lead: { name: "鈴木", role: "R" }
  ai_agent: { name: "Claude Code", role: "R" }
  ci: { name: "GitHub Actions", role: "CI" }

ai_policy:
  data_classification: "Internal"
  prohibited_inputs: ["個人情報（匿名化なし）", "秘密鍵"]

traceability:
  - { requirement: "RQ-001", source: "顧客要望", priority: "must" }
  - { requirement: "RQ-002", source: "業務改善", priority: "should" }

integration_flows:
  - { id: "FLOW-001", from: "Web-EDI Portal", to: "SAP S/4HANA", type: "API" }

systems:
  - { name: "SAP S/4HANA", role: "ERP", integration: "OData API" }
  - { name: "Web-EDI Portal", role: "Frontend", integration: "REST API" }

coverage_tier: "standard"   # critical | standard | experimental

basic_design_gate_check:
  traceability_present: true
  integration_flows_identified: true
  exceptions_documented: true
  delivery_model_defined: true
  raci_plus_defined: true
  ai_policy_defined: true
  artifact_registry_defined: true
  ready_for_bpmn: true
  counts:
    traceability_rows: 2
    integration_flows: 1
    blocking_questions: 0
  rules:
    min_traceability_rows: 1
    min_integration_flows: 1
    max_blocking_questions: 0
```

> **Note**: `counts` は Claude Code が自動計算します。

---

### A.2 spec.md Canonical YAML

**ポイント**: spec は「WHAT（何を）/ WHY（なぜ）」だけ。「HOW（どのように）」は plan.md に書く。

```yaml
artifact: "spec"
feature_id: "FEAT-WEB-EDI-001"

overview:
  who: "取引先の購買担当者"
  what: "Web-EDI受注受付"
  why: "手入力ミス削減と処理時間短縮"

use_cases:
  - id: "US-FEATWEB-EDI-001-001"
    title: "正常な受注登録"
    actor: "購買担当者"
    trigger: "発注データ送信"
    main_flow:
      - "購買担当者がWeb-EDIポータルで商品と数量を入力"
      - "システムが形式バリデーションを実行"
      - "システムが在庫引当チェックを実行"
      - "ERPに受注伝票を自動作成"
      - "受注番号と納期回答を返却"

acceptance:
  - id: "AC-US-FEATWEB-EDI-001-001-01"
    us_ref: "US-FEATWEB-EDI-001-001"
    description: "正しい発注データで受注番号が返却される"
    tags: ["integration"]
    given: "有効な商品IDと数量"
    when: "POST /api/orders を送信"
    then: "200 OK + order_id が返却"

  - id: "AC-US-FEATWEB-EDI-001-001-02"
    us_ref: "US-FEATWEB-EDI-001-001"
    description: "在庫不足時にエラーが返却される"
    tags: ["integration"]
    given: "在庫が不足する数量"
    when: "POST /api/orders を送信"
    then: "409 Conflict + 在庫不足メッセージ"

  - id: "AC-US-FEATWEB-EDI-001-001-03"
    us_ref: "US-FEATWEB-EDI-001-001"
    description: "E2E: 受注〜納期回答の一連フロー"
    tags: ["e2e"]
    given: "ブラウザでWeb-EDIポータルを開く"
    when: "商品を選択し発注ボタンを押す"
    then: "受注番号と納期が画面に表示される"

requirements:
  integration:
    - id: "NFR-INT-001"
      description: "SAP S/4HANA OData API 経由で受注伝票を作成"
  security:
    - id: "NFR-SEC-001"
      description: "CSRF トークン必須、RBAC による権限制御"
  data:
    - id: "NFR-DATA-001"
      description: "発注データは Confidential 分類"
  performance:
    - id: "NFR-PERF-001"
      description: "受注処理は 500ms 以下で完了"

spec_as_code:
  - type: "openapi"
    location: "specs/web_edi_order/contracts/order_api.yaml"
  - type: "test_scenarios"
    location: "specs/web_edi_order/tests/scenarios.yaml"
```

---

### A.3 plan.md Canonical YAML

```yaml
artifact: "plan"
feature_id: "FEAT-WEB-EDI-001"

components:
  - { id: "CMP-01", name: "order-validation", responsibility: "入力バリデーション" }
  - { id: "CMP-02", name: "erp-integration", responsibility: "SAP OData 連携" }

libraries:
  - { id: "LIB-01", name: "order-domain", responsibility: "受注ドメインロジック" }

contracts:
  - { id: "CT-API-01", type: "API", description: "POST /api/orders", spec_ref: "order_api.yaml" }
  - { id: "CT-API-02", type: "API", description: "GET /api/orders/{id}", spec_ref: "order_api.yaml" }
  - { id: "CT-EVT-01", type: "EVT", description: "OrderCreated イベント", spec_ref: "events.yaml" }

tests:
  - { id: "TS-CON-01", type: "contract", covers: ["CT-API-01", "CT-API-02"] }
  - { id: "TS-INT-01", type: "integration", covers: ["AC-US-FEATWEB-EDI-001-001-01"] }
  - { id: "TS-INT-02", type: "integration", covers: ["AC-US-FEATWEB-EDI-001-001-02"] }
  - { id: "TS-E2E-01", type: "e2e", covers: ["AC-US-FEATWEB-EDI-001-001-03"] }

coverage_policy:
  acceptance_coverage_target_pct: 100
  contract_coverage_target_pct: 100
  code_coverage_targets:
    - { scope: "LIB-*", line_pct: 85, branch_pct: 75 }
    - { scope: "CMP-*", line_pct: 60, branch_pct: 50 }

evidence_pack:
  required_artifacts:
    - "ci_results"
    - "test_reports"
    - "sast"
    - "sca"
    - "secrets_scan"
    - "ai_provenance"

phases:
  - { id: "Phase-1", name: "基盤構築", groups: ["G-01-validation", "G-02-erp"] }
  - { id: "Phase-2", name: "E2E 統合", groups: ["G-03-e2e"] }

groups:
  - { id: "G-01-validation", components: ["CMP-01"], contracts: ["CT-API-01"] }
  - { id: "G-02-erp", components: ["CMP-02"], contracts: ["CT-EVT-01"] }
  - { id: "G-03-e2e", tests: ["TS-E2E-01"] }
```

---

### A.4 tasks.md Canonical YAML

**ルール**: 全タスクに `plan_refs`（plan.md の stable ID 参照）を必ず設定。

```yaml
artifact: "tasks"
feature_id: "FEAT-WEB-EDI-001"

milestones:
  - { id: "M-01", name: "API 実装完了", target_date: "2026-03-01" }
  - { id: "M-02", name: "E2E テスト完了", target_date: "2026-03-15" }

tasks:
  - id: "T-VAL-001"
    title: "入力バリデーション実装"
    plan_refs: ["CMP-01", "CT-API-01", "TS-CON-01"]
    milestone: "M-01"
    depends_on: []
    done_when: "CT-API-01 の全エンドポイントが契約テスト PASS"
    outputs: ["src/validation/", "specs/web_edi_order/tests/contract/"]

  - id: "T-ERP-001"
    title: "SAP OData 連携実装"
    plan_refs: ["CMP-02", "CT-EVT-01", "TS-INT-01", "TS-INT-02"]
    milestone: "M-01"
    depends_on: ["T-VAL-001"]
    done_when: "統合テスト TS-INT-01, TS-INT-02 が PASS"
    outputs: ["src/erp/", "specs/web_edi_order/tests/integration/"]

  - id: "T-E2E-001"
    title: "E2E テスト実装"
    plan_refs: ["TS-E2E-01", "G-03-e2e"]
    milestone: "M-02"
    depends_on: ["T-ERP-001"]
    done_when: "TS-E2E-01 が PASS"
    outputs: ["specs/web_edi_order/tests/e2e/"]

tasks_gate_check:
  no_dependency_errors: true
  tasks_ready_for_code: true
  counts:
    tasks: 3
    use_cases_referenced: 1
    acceptance_referenced: 3
    tasks_with_plan_refs: 3
  rules:
    min_tasks: 1
    min_use_cases_referenced: 1
    min_acceptance_referenced: 1
```

---

### A.5 WI ファイル構造

**YAML frontmatter + Markdown:**

```yaml
---
wi_id: WI-WEB-EDI-002
title: "受注データバリデーションと在庫チェック"
complexity: medium
mode: confirm
risk_flags: ["new_api", "contract_change"]
spec_refs: ["spec.md"]
contract_refs:
  acceptance_ids:
    - "AC-US-FEATWEB-EDI-001-001-01"
    - "AC-US-FEATWEB-EDI-001-001-02"
owners:
  pm: "@tanaka"
  tech_lead: "@suzuki"
---

## Spec Links (Single source of truth)
- API: specs/web_edi_order/contracts/order_api.yaml
- TEST: specs/web_edi_order/tests/scenarios.yaml

## Definition of Done
- [ ] 全 AC の要素が充足していること
- [ ] 契約テスト（TS-CON-01）PASS
- [ ] 統合テスト（TS-INT-01, TS-INT-02）PASS
- [ ] walkthrough レビュー完了
- [ ] CI 合格
- [ ] stride-lint PASS
```

**ディレクトリ構造（Claude Code が自動生成）:**

```
specs/web_edi_order/
├── work_items/
│   ├── WI-WEB-EDI-001.md
│   ├── WI-WEB-EDI-002.md
│   └── WI-WEB-EDI-003.md
├── runs/
│   ├── WI-WEB-EDI-001/
│   │   └── RUN-001/
│   │       ├── walkthrough.md
│   │       └── test_results.md
│   └── WI-WEB-EDI-002/
│       └── RUN-001/
│           └── walkthrough.md
├── state/
│   └── state.yaml
└── ops/
    ├── transport_manifest.yaml
    ├── release_checklist.md
    ├── rollback_plan.md
    └── hypercare_runbook.md
```

---

### A.6 risk_flags と Mode の対応

```yaml
# High risk → validate（2 checkpoint: design_diff + plan_review）
- authz           # 権限制御
- sod             # 職務分離（Separation of Duties）
- audit_log       # 監査ログ
- pii             # 個人情報
- accounting_calc # 会計計算
- inventory_valuation  # 在庫評価
- db_schema       # DBスキーマ変更
- data_migration  # データ移行
- update_integration   # 更新系連携
- cross_module    # モジュール横断

# Medium risk → confirm（1 checkpoint: plan_review）
- new_api         # 新規API
- contract_change # 契約変更
- performance_sensitive  # 性能影響

# Low risk → autopilot（0 checkpoint、事後 walkthrough 必須）
- ui_only         # UIのみ
- message_only    # メッセージのみ
- test_only       # テストのみ
- logging_only    # ログのみ
```

> **mode_override**: policy より弱い Mode を使う場合は `mode_override.reason` が必須。理由なしは lint エラー。

---

### A.7 Autonomy Bias テーブル

`state.yaml` の `autonomy_bias` 設定により、risk_flags から算出された推奨 Mode がシフトします。

| Policy Mode | autonomous | balanced | controlled |
|-------------|-----------|----------|------------|
| autopilot | autopilot | autopilot | **confirm** |
| confirm | **autopilot** | confirm | **validate** |
| validate | **confirm** | validate | validate |

**安全制約**:
- `coverage_tier: critical` → 最低でも `confirm`（Bias に関わらず）
- `validate` を超える Mode は存在しない
- `mode_override` は Bias 適用後の推奨 Mode に対して行う

---

### A.8 Evidence Pack テンプレート

```markdown
# Evidence Pack: FEAT-WEB-EDI-001

## Gate / Decision
- **判定**: 合格

## CI Results
- GitHub Actions Run #42: PASS (2026-03-15)
- All 12 tests passed, 0 failures

## Test Reports
- TS-CON-01: PASS — 契約テスト（OpenAPI 整合性）
- TS-INT-01: PASS — 統合テスト（正常系受注）
- TS-INT-02: PASS — 統合テスト（在庫不足）
- TS-E2E-01: PASS — E2E テスト（受注フロー）

## Coverage
- AC Coverage: 100% (3/3)
- CT Coverage: 100% (3/3)
- Code Coverage: LIB-01 87%/78%, CMP-01 65%/55%

## SAST / SCA / Secrets
- Snyk: 0 Critical, 0 High
- GitLeaks: 0 findings

## AI Provenance
- Provider / Surface: Anthropic / claude-code
- Model: claude-opus-4-7
- Execution: effort=xhigh, reasoning=adaptive, max_output_tokens=65536
- Prompt version: v5.2.0
- Input hash: sha256:abc123...
- Cyber safeguards / CVP: reviewed / not_required

## Run Index
| WI | Run | Status | Mode |
|----|-----|--------|------|
| WI-WEB-EDI-001 | RUN-001 | done | autopilot |
| WI-WEB-EDI-002 | RUN-001 | done | confirm |
| WI-WEB-EDI-003 | RUN-001 | done | validate |
```

---

### A.9 Ops Pack 構成

ERP Addon では必須。

| ファイル | 内容 |
|---------|------|
| `transport_manifest.yaml` | 輸送対象（プログラム・テーブル・設定）と依存関係 |
| `release_checklist.md` | Pre-Release / Release / Post-Release のチェックリスト |
| `rollback_plan.md` | ロールバック手順（輸送の逆順） |
| `hypercare_runbook.md` | 本番稼働後の監視・対応手順 |

---

## Appendix B: stride-lint エラーコード全一覧

### B.1 ブロッキングエラー（修正必須）

| コード | メッセージ | 原因 | 修正方法 |
|--------|----------|------|---------|
| `APPROVAL_PENDING` | Gate X not approved | APPROVAL.md が未承認 | **人間が** APPROVAL.md のチェックボックスを `[x]` に |
| `WI_APPROVAL_PENDING` | WI approval pending | WI の承認が未完了 | **人間が** WI-*.approval.md を編集 |
| `WI_DIR_MISSING` | work_items/ not found | Gate 5 以降で work_items/ がない | ディレクトリを作成し WI ファイルを配置 |
| `WI_SCHEMA_INVALID` | Missing required field | WI の必須項目（wi_id, title, mode 等）が欠落 | 不足フィールドを YAML frontmatter に追加 |
| `WI_MODE_INVALID` | Invalid mode value | mode が autopilot/confirm/validate 以外 | 正しい値に修正 |
| `WI_RISK_FLAG_INVALID` | Unknown risk flag | risk_flags が taxonomy に存在しない | 正しいフラグ名に修正 |
| `MODE_OVERRIDE_REASON_MISSING` | Override without reason | policy より弱い mode で理由がない | `mode_override.reason` を追加 |
| `STATE_MISSING` | state.yaml not found | state.yaml がない | テンプレートからコピーして配置 |
| `STATE_WI_MISMATCH` | State/WI file mismatch | state と WI ファイルの不整合 | state.yaml の work_items と WI ファイルを同期 |
| `RUN_MISSING` | No run for done WI | WI が done なのに Run がない | Run ディレクトリと walkthrough.md を作成 |
| `RUN_MULTIPLE` | Multiple runs for WI | 1 WI に複数の Run（1 WI = 1 Run 違反） | 不要な Run を削除、または新 WI を作成 |
| `WALKTHROUGH_MISSING` | No walkthrough.md | walkthrough.md がない | Run ディレクトリに walkthrough.md を作成 |
| `OPS_PACK_MISSING` | Ops pack incomplete | ops pack の 4 ファイルが揃っていない | 不足ファイルを作成 |
| `AUTOPILOT_FORBIDDEN_BY_TIER` | Autopilot not allowed | critical tier で autopilot は禁止 | mode を confirm 以上に変更 |
| `PHASE_GATE_BLOCKED` | Phase N+1 file before Phase N approval | 承認前に次 Phase のファイルを作成 | 先に APPROVAL.md で該当 Gate を承認 |

### B.2 警告（非ブロッキング）

| コード | メッセージ | 対応 |
|--------|----------|------|
| `COUNTS_SUGGESTION` | Counts mismatch | 提示された値で counts を更新 |
| `WARN_WI_MODE_POLICY_VIOLATION` | Mode weaker than policy | mode_override.reason が適切か確認 |
| `WARN_SPEC_LINK_NOT_FOUND` | Spec link target missing | 参照先ファイルパスを修正 |
| `WARN_SPEC_REF_NOT_FOUND` | spec_refs target missing | spec_refs のパスを修正 |

---

## Appendix C: テストコード例

### C.1 Python テスト例

```python
# specs/web_edi_order/tests/integration/test_order_creation.py
import pytest
from src.api.orders import create_order

class TestOrderCreation:
    """TS-INT-01: AC-US-FEATWEB-EDI-001-001-01 をカバー"""

    def test_valid_order_returns_order_id(self, valid_order_payload):
        """正しい発注データで受注番号が返却される"""
        response = create_order(valid_order_payload)
        assert response.status_code == 200
        assert "order_id" in response.json()
        assert response.json()["order_id"].startswith("ORD-")

    def test_order_persisted_in_db(self, valid_order_payload, db_session):
        """受注データがDBに永続化される"""
        response = create_order(valid_order_payload)
        order_id = response.json()["order_id"]
        order = db_session.query(Order).filter_by(id=order_id).first()
        assert order is not None
        assert order.status == "created"
```

### C.2 TypeScript (Playwright) E2E テスト例

```typescript
// specs/web_edi_order/tests/e2e/order_flow.spec.ts
import { test, expect } from "@playwright/test";

test.describe("TS-E2E-01: 受注フロー E2E", () => {
  test("AC-US-FEATWEB-EDI-001-001-03: 受注〜納期回答", async ({ page }) => {
    // Given: Web-EDIポータルを開く
    await page.goto("/web-edi/orders/new");

    // When: 商品を選択し発注
    await page.selectOption("#product", "P-123");
    await page.fill("#quantity", "10");
    await page.click("#submit-order");

    // Then: 受注番号と納期が表示される
    await expect(page.locator("#order-id")).toBeVisible();
    await expect(page.locator("#delivery-date")).toBeVisible();
    const orderId = await page.textContent("#order-id");
    expect(orderId).toMatch(/^ORD-/);
  });
});
```

### C.3 テストディレクトリ構造

```
specs/<feature>/tests/
├── conftest.py          # 共有フィクスチャ（Python）
├── scenarios.yaml       # テストシナリオ定義
├── unit/                # TS-UT-*
│   └── test_*.py
├── contract/            # TS-CON-*
│   └── test_*.py
├── integration/         # TS-INT-*
│   └── test_*.py
└── e2e/                 # TS-E2E-*
    └── *.spec.ts
```

> **重要**: テストは `specs/<feature>/tests/` に配置。ルートの `tests/` ではない。

---

> SDD Templates Manual - 07. Tecnos-STRIDE 実施担当者ガイド (v4.7)
