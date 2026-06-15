# 06. Tecnos-STRIDE 上流工程ガイド — 設計から実装計画まで

> **Version**: v5.4.0-tecnos-stride
> **対象**: シニアSE・アーキテクト・テックリード（上流フェーズを Claude Code と実行する人）
> **所要時間**: 通読 約40分（リファレンスとして随時参照）

---

## 実施担当者・PM 向けサマリー

このガイドは **上流フェーズ（Design → Specify → Tasking）** を担当するシニアSE・アーキテクト向けです。

- 実施担当者（Execute Phase 担当）は → [実施担当者ガイド（§07）](07_practitioner_execution_guide.md)
- PM（プロジェクト管理）は → [PM向けガイド（§05）](05_pm_operations_guide.md)

上流工程の成果物は、**Execute Phase で実施担当者が受け取る「設計図」** です。
ここで作る spec.md の AC（受入条件）が、実施担当者の「何を満たせば完了か」の基準になります。

---

## 1. このガイドの対象と目的

### 1.1 対象読者

- **シニアSE・アーキテクト** — Feature の設計・仕様策定を主導する
- **テックリード** — 技術方針を決定し、タスク分解を行う
- 上記の立場で **Claude Code を使って上流フェーズを進める** 方

### 1.2 v4.4 における上流担当者の役割

> **v4.4 の核心**: ファイル作成・lint・自動修正はすべて Claude Code が自律実行。
> 上流担当者は **要件・方針を伝え、成果物を判断し、Gate を承認する** のが仕事。

| 担当 | やること | やらないこと |
|------|---------|-------------|
| **上流担当者** | 要件定義、設計判断、AC の品質レビュー、Gate 承認 | YAML の手書き、lint 実行、テンプレート作成 |
| **Claude Code** | basic_design〜tasks の全作成、lint、自動修正 | 承認ファイルの編集、ビジネス判断 |

### 1.3 前提知識

| 必須 | あると望ましい |
|------|--------------|
| 業務要件を構造化する能力 | ERP / SAP の基本知識 |
| システム間連携の設計経験 | BPMN の読み書き |
| 非機能要件（NFR）の設計経験 | OpenAPI の基礎 |
| Claude Code の基本操作 | テスト戦略の設計経験 |

### 1.4 上流工程の全体像

```
Phase 1: Design    → basic_design.md, process.bpmn     → Gate 1,2 承認
Phase 2: Specify   → spec.md, plan.md, contracts/      → Gate 3,4 承認
Phase 3: Tasking   → tasks.md                           → Gate 5 承認
─────────────────────────────────────────────────────────────────────
Gate 5 承認後 → Execute Phase（実施担当者へ引き継ぎ）→ §07 参照
```

> **Phase Gate 強制**: 前の Phase の Gate が未承認の状態で、次の Phase のファイルを作成することはできません。stride-lint が `PHASE_GATE_BLOCKED` エラーで阻止します。

---

## 2. 上流担当者の1日（シナリオ形式）

### 登場人物

- **佐藤さん** — シニアSE / アーキテクト（上流工程担当）
- **Claude Code** — AI 実行エージェント（全作業の実行者 R）
- **田中PM** — プロジェクトマネージャー（承認者 A）
- **鈴木さん** — 実施担当者（Execute Phase を担当。上流完了後に引き継ぐ相手）

---

### 09:00 — 新機能の要件整理

佐藤さんは田中PM から「ERP 受注管理アドオン」の開発を依頼されました。
まず要件を整理して、Claude Code に伝えます。

```
佐藤: 「以下の機能を開発したいです。SDD 開発を開始してください。

【機能名】ERP 受注管理アドオン
【誰が使う】営業部門（約50名）+ 経理部
【何をする】ERP の受注データに対して承認ワークフロー・監査ログ・自動仕訳を追加する
【なぜ必要】現状は受注登録後に手動で承認フローを回している。承認漏れや
           監査証跡の欠如が内部監査で指摘されている
【関連システム】SAP S/4HANA（OData）、社内認証基盤（LDAP）
【制約】
  - ERP 本体 DB への直接書き込み禁止（OData API 経由のみ）
  - 監査ログは7年間保持
  - 承認権限は LDAP グループに基づく」
```

**Claude Code が自律実行する内容：**
1. `stride init order_addon --detect` でスキャフォールド作成
2. 要件をもとに `basic_design.md` の Canonical YAML を構造化
3. `process.bpmn` を作成
4. `stride lint` → エラーがあれば自動修正 → PASS で停止

```
Claude Code:
  Feature FEAT-SAMPLE を初期化しました。

  作成したファイル:
  - specs/order_addon/basic_design.md
  - specs/order_addon/process.bpmn
  - specs/order_addon/APPROVAL.md

  stride-lint: PASS
  Gate 1,2 の承認をお願いします。
```

---

### 09:30 — Design Phase のレビュー

佐藤さんは Claude Code にセルフチェックを依頼し、結果を確認します。

```
佐藤: 「basic_design.md のセルフチェックをしてください。
       1. Who/What/Why が伝えた内容と一致しているか
       2. integration_flows に連携先が網羅されているか
       3. coverage_tier は妥当か（判断の根拠も）
       4. ai_policy の data_classification は適切か
       5. 不足や懸念点」

Claude Code:
  セルフチェック結果:
  ┌───┬──────────────────────┬──────┬──────────────────────────────┐
  │ # │ 観点                  │ 判定 │ 詳細                          │
  ├───┼──────────────────────┼──────┼──────────────────────────────┤
  │ 1 │ Who/What/Why の一致   │ ✅   │ 入力内容と完全一致            │
  │ 2 │ integration_flows     │ ⚠️   │ SF→SAP はあるが SAP→SF       │
  │   │                      │      │ （逆方向同期）が未定義         │
  │ 3 │ coverage_tier         │ ⚠️   │ standard と判定したが、        │
  │   │                      │      │ 個人情報制約あり → critical   │
  │   │                      │      │ を検討すべき                  │
  │ 4 │ ai_policy             │ ✅   │ Confidential, 個人情報禁止    │
  │ 5 │ 懸念点               │ ⚠️   │ API コール数制限に対する       │
  │   │                      │      │ バッチ戦略が未定義            │
  └───┴──────────────────────┴──────┴──────────────────────────────┘
```

佐藤さんは ⚠️ の3項目を判断します：

```
佐藤: 「以下を修正してください。
       - integration_flows に 承認→自動仕訳 の連携フローを追加
       - coverage_tier を critical に変更（監査要件 + 会計データ連携のため）
       - blocking_questions に "承認権限のLDAP連携方式" を追加して、
         田中PM に確認が必要な項目として記録してください」

Claude Code:
  修正しました。

  変更点:
  1. integration_flows: FLOW-002 (承認完了 → 自動仕訳) を追加
  2. coverage_tier: standard → critical
     ⚠️ critical に変更したため、Execute Phase で autopilot モードが禁止されます。
     全 WI が confirm 以上の Mode になります。
  3. blocking_questions に追加:
     - BQ-001: "承認権限のLDAP連携方式（グループ同期 or 都度問い合わせ）を決定してください"

  stride-lint: PASS（APPROVAL_PENDING のみ）
```

> 💡 **coverage_tier の変更は影響が大きい**: critical にすると Execute Phase で autopilot が禁止され、全 WI に事前承認が必要になる。この判断は上流担当者の重要な責務。

---

### 10:00 — blocking questions の解消

佐藤さんは blocking questions を田中PM と相談して解消します。

```
佐藤 → 田中PM:
  「承認権限のLDAP連携方式について相談です。
   LDAPグループを日次バッチで同期してローカルキャッシュする方式と、
   承認時に都度LDAPに問い合わせる方式、どちらがよいですか？」

田中PM:
  「日次同期でOK。ただし、人事異動の即時反映が必要なケースもあるから、
   NFR に "緊急時は手動でキャッシュ更新可能" の要件を入れておいて。」

佐藤: 「Claude Code、blocking question BQ-001 を以下の方針で解消してください。
       - LDAP連携: 日次バッチでグループ同期（ローカルキャッシュ）
       - 緊急時: 管理者による手動キャッシュ更新API
       - NFR に追加: LDAP同期は日次 + 手動更新API提供
       blocking_questions を 0 件にしてください。」

Claude Code:
  BQ-001 を解消しました。
  - NFR-INT-002: "LDAP同期は日次 + 手動更新API提供" を追加
  - blocking_questions: 1 → 0

  stride-lint: PASS
```

> **blocking_questions が 0 にならないと Gate 承認できません。**

---

### 10:30 — Gate 1,2 承認 → Specify Phase へ

```
佐藤: （APPROVAL.md で Gate 1,2 を承認）
      「承認しました。Specify Phase に進んでください。」

Claude Code:
  Gate 1,2 承認を確認しました。Specify Phase を開始します...

  作成中:
  [1/4] spec.md — ユースケース・AC・NFR の構造化...
  [2/4] plan.md — テスト戦略・Coverage Policy の設計...
  [3/4] contracts/ — OpenAPI 定義の作成...
  [4/4] tests/scenarios.yaml — テストシナリオの定義...

  stride-lint: PASS
  Gate 3,4 の承認をお願いします。
```

---

### 11:00 — Specify Phase のレビュー（最重要）

> **Specify Phase は上流工程で最も重要なフェーズです。**
> ここで定義する AC の品質が、Execute Phase の成果物品質を直接決定します。

```
佐藤: 「spec.md と plan.md のセルフチェックをしてください。
       以下の観点で結果を対照表にしてください。
       1. 全 AC が業務要件を正しく反映しているか（basic_design との整合性）
       2. AC の given/when/then が具体的か（曖昧な表現がないか）
       3. Tagged AC（integration/e2e）の付与は適切か
       4. plan.md の全 AC が TS でカバーされているか（AC↔TS マッピング表）
       5. contracts/ が integration_flows の全連携先を網羅しているか
       6. Coverage Policy の目標値は coverage_tier: critical と整合しているか
       7. NFR に漏れがないか（性能、セキュリティ、データ、運用）」

Claude Code:
  セルフチェック結果:
  ┌───┬────────────────────────┬──────┬─────────────────────────────┐
  │ # │ 観点                    │ 判定 │ 詳細                         │
  ├───┼────────────────────────┼──────┼─────────────────────────────┤
  │ 1 │ AC↔業務要件の整合性      │ ✅   │ 5 AC 全て basic_design から  │
  │   │                        │      │ トレース可能                │
  │ 2 │ AC の具体性             │ ⚠️   │ AC-ERP-003 の then が        │
  │   │                        │      │ 「正しく承認される」と曖昧    │
  │ 3 │ Tagged AC の妥当性      │ ✅   │ integration: 3件, e2e: 1件  │
  │ 4 │ AC↔TS マッピング        │ ✅   │ 5/5 AC がカバー済み          │
  │ 5 │ contracts 網羅性        │ ⚠️   │ 承認API エンドポイントが      │
  │   │                        │      │ 未定義                       │
  │ 6 │ Coverage Policy         │ ✅   │ critical tier に準拠         │
  │   │                        │      │ (LIB 85%/75%, CMP 85%/75%) │
  │ 7 │ NFR                    │ ⚠️   │ 運用系 NFR（監視、アラート）  │
  │   │                        │      │ が未定義                    │
  └───┴────────────────────────┴──────┴─────────────────────────────┘
```

佐藤さんは ⚠️ の3項目を修正します：

```
佐藤: 「以下を修正してください。

       1. AC-ERP-003 の then を具体化:
          "正しく承認される" → "承認完了後に自動仕訳が生成され、
          仕訳番号が SAP に OData 経由で登録されること。
          処理時間は30秒以内であること"

       2. contracts/ に 承認API エンドポイント（POST /api/erp/approve）を追加

       3. NFR に運用系を追加:
          - NFR-OPS-001: "承認エラー時に Slack #erp-addon-alerts に通知"
          - NFR-OPS-002: "仕訳登録遅延が5分を超えた場合にアラート通知"」
```

> 💡 **AC の品質が全てを決める**: `then: "正しく同期される"` のような曖昧な AC は、Execute Phase で「何をもって完了か」が判断できない。**具体的な数値・条件・検証方法**を含めること。

---

### 11:30 — AC の品質を深掘りレビュー

佐藤さんは全 AC の品質をさらに確認します。

```
佐藤: 「全 AC の given/when/then を一覧表にして、以下を検証してください。
       - given: テスト時に再現可能な前提条件か？
       - when: 具体的な操作・APIコールが特定できるか？
       - then: 測定可能な期待結果か？（数値・ステータス・エラーコード等）
       曖昧なものに ⚠️ を付けてください。」

Claude Code:
  AC 品質チェック:
  ┌───────────┬──────────────────────┬───────────────────────┬────────────────────────┬────┐
  │ AC ID     │ given                │ when                  │ then                   │判定│
  ├───────────┼──────────────────────┼───────────────────────┼────────────────────────┼────┤
  │AC-ERP-001 │ 有効な LDAP 認証     │ POST /api/erp/        │ 200 OK + 承認済み       │ ✅ │
  │           │ トークン             │ approve               │ ステータス返却          │    │
  │AC-ERP-002 │ 受注が承認完了       │ 自動仕訳トリガー       │ SAP に仕訳番号が        │ ✅ │
  │           │ ステータスに変更     │ 実行                  │ 登録される (30秒以内)   │    │
  │AC-ERP-003 │ 承認者が受注詳細     │ 「承認」ボタン         │ 監査ログに承認者・      │ ✅ │
  │           │ 画面を開く           │ クリック               │ 日時・理由が記録される  │    │
  │AC-ERP-004 │ SAP OData API が     │ 仕訳登録実行           │ 3回リトライ後、         │ ✅ │
  │           │ 503 を返す状態       │                       │ エラー通知 + ログ記録   │    │
  │AC-ERP-005 │ ブラウザで管理       │ 「一括承認」ボタン     │ 対象受注の一括承認が    │ ⚠️ │
  │           │ 画面を開く           │ クリック               │ 実行される              │    │
  │           │                     │                       │ → 件数と所要時間を表示 │    │
  └───────────┴──────────────────────┴───────────────────────┴────────────────────────┴────┘

  ⚠️ AC-ERP-005: then が "対象受注の一括承認が実行される" だけでは検証が難しい。
  成功基準（例: "承認件数と所要時間が画面に表示され、エラー0件"）を追加推奨。

佐藤: 「AC-ERP-005 の then を修正してください。
       "対象受注の一括承認が実行され、承認結果（成功件数・失敗件数・所要時間）が
       画面に表示される。失敗件数が0件であること"」
```

---

### 13:00 — plan.md のレビュー

```
佐藤: 「plan.md のコンポーネント設計とテスト戦略を確認したいです。
       1. コンポーネントの責務分離は適切か（Article I: Library-First）
       2. テストピラミッド（Unit > Integration > E2E）のバランス
       3. coverage_tier: critical の要件（85%/75%）を満たす設計になっているか」

Claude Code:
  plan.md レビュー:
  ┌───┬──────────────────────────┬──────┬──────────────────────────────┐
  │ # │ 観点                      │ 判定 │ 詳細                          │
  ├───┼──────────────────────────┼──────┼──────────────────────────────┤
  │ 1 │ Library-First 準拠        │ ✅   │ LIB-01 (sync-domain) に      │
  │   │                          │      │ ビジネスロジック集約          │
  │ 2 │ テストピラミッド           │ ✅   │ UT:8, CON:3, INT:4, E2E:1   │
  │ 3 │ Coverage 設計             │ ⚠️   │ CMP-03 (webhook-receiver)    │
  │   │                          │      │ の目標が 70%/60%             │
  │   │                          │      │ → critical は 85%/75% 必要   │
  └───┴──────────────────────────┴──────┴──────────────────────────────┘

佐藤: 「CMP-03 の Coverage 目標を 85%/75% に引き上げてください。
       critical tier なので全コンポーネントに適用です。」
```

---

### 14:00 — Gate 3,4 承認 → Tasking Phase へ

```
佐藤: （APPROVAL.md で Gate 3,4 を承認）
      「承認しました。Tasking Phase に進んでください。」
```

---

### 14:30 — Tasking Phase のレビュー

Claude Code が tasks.md を自動生成します。

```
佐藤: 「tasks.md のセルフチェックをしてください。
       1. タスクの粒度（1タスク = 1〜2日が目安）
       2. 全 TS がタスク化されているか（TS↔Task マッピング）
       3. 依存関係に問題がないか（循環依存、クリティカルパス）
       4. plan_refs が全て有効な stable ID を参照しているか
       5. e2e タスクの3点セット（harness, test, triage）が揃っているか」

Claude Code:
  セルフチェック結果:
  ┌───┬────────────────────────┬──────┬─────────────────────────────┐
  │ # │ 観点                    │ 判定 │ 詳細                         │
  ├───┼────────────────────────┼──────┼─────────────────────────────┤
  │ 1 │ タスク粒度              │ ⚠️   │ T-SYNC-002 が3日相当         │
  │   │                        │      │ → 分割を推奨                │
  │ 2 │ TS↔Task マッピング      │ ✅   │ 16/16 TS がカバー済み        │
  │ 3 │ 依存関係                │ ✅   │ 循環なし                    │
  │ 4 │ plan_refs の有効性      │ ✅   │ 全 refs が plan.md に存在    │
  │ 5 │ e2e 3点セット           │ ✅   │ harness + test + triage 完備│
  └───┴────────────────────────┴──────┴─────────────────────────────┘

  依存グラフ:
  T-AUTH-001 → T-SYNC-001 → T-SYNC-002 → T-CONFLICT-001 → T-E2E-001
                                ↑ 3日相当（分割推奨）

佐藤: 「T-SYNC-002 を分割してください。
       SF→SAP 同期と SAP→SF 同期を別タスクにしたい。
       それぞれ依存関係も適切に設定して。」

Claude Code:
  分割しました。

  T-SYNC-002a: "SF→SAP 商談同期"（1.5日）
  T-SYNC-002b: "SAP→SF 商談同期"（1.5日）
  依存: T-SYNC-001 → T-SYNC-002a → T-SYNC-002b → T-CONFLICT-001

  stride-lint: PASS
```

---

### 15:00 — Gate 5 承認 → 実施担当者への引き継ぎ

```
佐藤: （APPROVAL.md で Gate 5 を承認）
      「承認しました。」
```

Gate 5 承認後、Claude Code が WI を自動分割します。

```
Claude Code:
  Gate 5 承認を確認しました。Execute Phase を開始します。
  tasks.md をもとに Work Items を作成しました:

  ┌──────────────────────┬──────────────────────┬──────────────────┬───────────┐
  │ WI ID                │ Title                │ risk_flags       │ Mode      │
  ├──────────────────────┼──────────────────────┼──────────────────┼───────────┤
  │ WI-ERP-SAMPLE-001    │ 受注登録画面UI改善    │ [ui_only]        │ confirm   │
  │ WI-ERP-SAMPLE-002    │ 承認フロー・権限管理  │ [authz, sod]     │ validate  │
  │ WI-ERP-SAMPLE-003    │ 監査ログ出力         │ [audit_log]      │ validate  │
  │ WI-ERP-SAMPLE-004    │ API連携強化          │ [new_api,        │ validate  │
  │                      │                      │  contract_change]│           │
  │ WI-ERP-SAMPLE-005    │ E2E テスト           │ [test_only]      │ confirm   │
  └──────────────────────┴──────────────────────┴──────────────────┴───────────┘

  ⚠️ coverage_tier: critical のため、autopilot は使用できません。
  全 WI が confirm 以上の Mode です。
```

> **注意**: critical tier では **全 WI が confirm 以上**。実施担当者に引き継ぐ際、この制約を必ず伝えてください。

#### 鈴木さん（実施担当者）への引き継ぎ

```
佐藤 → 鈴木:
  「ERP受注管理アドオンの Execute Phase に入りました。
   以下を把握しておいてください。

   ⚠️ 重要事項:
   - coverage_tier: critical → autopilot 禁止、全 WI confirm 以上
   - 権限・監査制約あり → ai_policy で prohibited_inputs 設定済み
   - DB排他制御 → 大量注文時のタイムアウト対策済み（plan.md 参照）

   WI は5件、全て validate か confirm です。
   WI-ERP-SAMPLE-001 の受注登録UIから順番に進めてください。
   困ったことがあれば私か田中PM に相談してください。」
```

> 鈴木さんの Execute Phase の進め方は [実施担当者ガイド（§07）](07_practitioner_execution_guide.md) を参照。

---

## 3. Design Phase — 詳細ガイド

### 3.1 Claude Code への要件伝達

要件伝達のテンプレート：

```
【機能名】○○○
【誰が使う】ユーザーの属性と規模
【何をする】機能の概要（1-2文）
【なぜ必要】現状の課題と期待効果
【関連システム】連携先システムとAPI方式
【制約】技術的・ビジネス的な制約
```

> 💡 **Intake-First モード**: 要件が曖昧な場合は「Intake-First で始めてください」と伝えると、Claude Code が対話形式で 1 つずつ要件を聞き取ります。これは要件が固まっていない段階で特に有効です。

### 3.2 basic_design.md のレビューポイント

Claude Code にセルフチェックを依頼する時の推奨観点：

| # | 観点 | なぜ重要か |
|---|------|----------|
| 1 | Who/What/Why の一致 | 要件の取りこぼしを防ぐ |
| 2 | integration_flows の網羅性 | 連携漏れは Execute Phase で手戻りの原因 |
| 3 | coverage_tier の妥当性 | Execute Phase の Mode 制約を決定する |
| 4 | ai_policy の適切性 | データ分類ミスはセキュリティリスク |
| 5 | blocking_questions が 0 か | 1件でも残っていると Gate 承認不可 |

> 📖 **basic_design.md の YAML 構造**: → [§07 Appendix A.1](07_practitioner_execution_guide.md#a1-basic_designmd-canonical-yaml) を参照

### 3.3 coverage_tier の判断基準

| Tier | 条件 | Execute Phase への影響 |
|------|------|---------------------|
| **critical** | 会計影響、個人情報、外部公開 API、規制対象 | autopilot 禁止、E2E 必須、Coverage 85%/75% |
| **standard** | 社内業務改善、情報参照系 | autopilot 可能、E2E 任意、Coverage 70%/60% |
| **experimental** | PoC、社内ツール、影響範囲が限定的 | autopilot 可能、E2E 不要、Coverage 50%/40% |

> **迷ったら critical を選ぶ**。standard に下げるのは後からでもできるが、critical に上げると Execute Phase の WI が全て confirm 以上に変わるため、手戻りが大きい。

### 3.4 BPMN のレビュー

```
佐藤: 「process.bpmn のセルフチェックをしてください。
       1. 全てのハッピーパスが網羅されているか
       2. エラーハンドリングフロー（例外パス）があるか
       3. integration_flows の全連携がBPMNに反映されているか」
```

> **BPMN の詳細な書き方**: → [BPMN ガイド（§10）](10_bpmn_guide.md) を参照

---

## 4. Specify Phase — 詳細ガイド

### 4.1 AC（受入条件）の品質基準

**良い AC の条件：**

| 要素 | 基準 | ❌ 悪い例 | ✅ 良い例 |
|------|------|---------|---------|
| **given** | テスト時に再現可能 | 「正常な状態で」 | 「有効な OAuth トークンが存在し、SF API が応答する状態で」 |
| **when** | 具体的な操作/API | 「同期を実行すると」 | 「POST /api/sf/sync を実行すると」 |
| **then** | 測定可能な期待結果 | 「正しく同期される」 | 「SAP 商談ステータスが SF と一致し、差分が30秒以内」 |

> **原則**: AC の then を見て「テストコードのアサーションが書けるか？」と自問する。書けないなら曖昧すぎる。

### 4.2 Tagged AC の判断

| タグ | いつ付ける | 例 |
|------|----------|-----|
| `integration` | 外部システムとの通信を含む AC | SF API コール、SAP OData 連携 |
| `e2e` | ユーザーの操作から結果確認まで一気通貫 | 管理画面から強制同期→結果表示 |
| タグなし | 単一モジュール内で完結する処理 | バリデーション、データ変換 |

> **`e2e` は最小限に**: critical journey（ユーザーが最も重要と感じるフロー）だけ。付けすぎるとテストが肥大化し、メンテナンスコストが増大する。

### 4.3 NFR の設計チェックリスト

| カテゴリ | 検討項目 | 見落としがちなポイント |
|---------|---------|---------------------|
| **Performance** | レスポンスタイム、スループット | バルク処理時の性能劣化 |
| **Security** | 認証、認可、データ分類 | CSRF、RBAC の漏れ |
| **Data** | 個人情報分類、保持期間 | ログに個人情報が混入 |
| **Integration** | API 方式、エラーハンドリング | レートリミット、リトライ戦略 |
| **Operations** | 監視、アラート、ログ | 障害時の切り戻し手順 |

### 4.4 Coverage Policy の設計

```
佐藤: 「coverage_policy の設計をレビューしてください。
       coverage_tier: critical の全要件を満たしているか確認して。」

Claude Code:
  Coverage Policy チェック:
  ┌──────────────────┬───────────┬─────────┬──────┐
  │ 対象              │ 目標      │ 要件    │ 判定 │
  ├──────────────────┼───────────┼─────────┼──────┤
  │ AC Coverage      │ 100%      │ 100%    │ ✅   │
  │ CT Coverage      │ 100%      │ 100%    │ ✅   │
  │ LIB-* line/branch│ 85%/75%  │ 85%/75% │ ✅   │
  │ CMP-* line/branch│ 85%/75%  │ 85%/75% │ ✅   │
  │ E2E             │ あり      │ 必須    │ ✅   │
  └──────────────────┴───────────┴─────────┴──────┘
```

> 📖 **spec.md / plan.md の YAML 構造**: → [§07 Appendix A.2](07_practitioner_execution_guide.md#a2-specmd-canonical-yaml), [A.3](07_practitioner_execution_guide.md#a3-planmd-canonical-yaml) を参照

---

## 5. Tasking Phase — 詳細ガイド

### 5.1 タスク分割の判断基準

| 基準 | 推奨 | 理由 |
|------|------|------|
| **粒度** | 1 WI = 1〜2日 | 3日以上のタスクはレビューが重く、問題発見が遅れる |
| **リスク分離** | リスクの異なる変更は別タスク | ui_only と db_schema を混ぜると Mode が validate に引き上げられる |
| **依存関係** | 最小限に。循環依存は禁止 | 並列実行の余地を残す |
| **テスタビリティ** | 1タスクの成果物だけでテスト可能 | 他のタスクに依存しないとテストできない設計は分割失敗 |

### 5.2 依存関係の設計

```
佐藤: 「依存グラフを可視化して、クリティカルパスを教えてください。」

Claude Code:
  依存グラフ:
  T-AUTH-001 ──→ T-SYNC-002a ──→ T-CONFLICT-001 ──→ T-E2E-001
       │              │                                    ↑
       └──→ T-SYNC-001 ──→ T-SYNC-002b ──────────────────┘

  クリティカルパス: T-AUTH-001 → T-SYNC-002a → T-CONFLICT-001 → T-E2E-001
  所要時間: 1 + 1.5 + 2 + 1 = 5.5日

  並列実行可能: T-SYNC-001 と T-SYNC-002a は並列可能
```

### 5.3 e2e タスクの3点セット

spec.md に `tags: ["e2e"]` 付きの AC がある場合、以下の3タスクが必須：

| タスク | 内容 | 依存 |
|--------|------|------|
| **E2E harness** | テスト基盤（Playwright setup、テストデータ、fixture） | 全実装タスク完了後 |
| **E2E test** | E2E テストの実装と実行 | harness 完了後 |
| **E2E triage** | 失敗時のトリアージ手順定義、flaky test 対策 | test 完了後 |

> 📖 **tasks.md の YAML 構造**: → [§07 Appendix A.4](07_practitioner_execution_guide.md#a4-tasksmd-canonical-yaml) を参照

---

## 6. Gate 承認のチェックリスト

### Gate 1,2（Design）

- [ ] Who/What/Why が要件と一致している
- [ ] integration_flows に全連携先が定義されている
- [ ] coverage_tier が適切に設定されている
- [ ] ai_policy が正しく設定されている
- [ ] blocking_questions が 0 件
- [ ] process.bpmn がハッピーパスと例外パスを網羅している
- [ ] stride-lint: PASS

### Gate 3,4（Specify）

- [ ] 全 AC の given/when/then が具体的・測定可能
- [ ] Tagged AC（integration/e2e）が適切に付与されている
- [ ] 全 AC が TS でカバーされている（AC↔TS マッピング 100%）
- [ ] contracts/ が全連携先を網羅している
- [ ] Coverage Policy が coverage_tier の要件を満たしている
- [ ] NFR に漏れがない（性能・セキュリティ・データ・連携・運用）
- [ ] stride-lint: PASS

### Gate 5（Tasking）

- [ ] 全タスクの粒度が 1〜2日以内
- [ ] 全 TS がタスク化されている
- [ ] 依存関係に循環がない
- [ ] e2e タスクの3点セット（harness, test, triage）が揃っている
- [ ] 全タスクの plan_refs が有効
- [ ] stride-lint: PASS

---

## 7. 実施担当者への引き継ぎ

Gate 5 承認後、実施担当者に以下を伝えてください：

### 必ず伝えること

| 項目 | 内容 | 影響 |
|------|------|------|
| **coverage_tier** | critical / standard / experimental | Execute Phase の Mode 制約 |
| **特殊な制約** | 個人情報制約、API 制限、外部連携の注意点 | 実装時の判断に影響 |
| **blocking_questions の解消内容** | 設計判断の経緯 | 判断の背景を知ることで適切な実装が可能 |
| **WI の mode 分布** | validate が多い場合は特に | 事前承認の工数見積もり |

### 伝え方のテンプレート

```
「[Feature名] の Execute Phase に入りました。以下を把握しておいてください。

⚠️ 重要事項:
- coverage_tier: [tier] → [影響の説明]
- [特殊な制約があれば記載]

WI は [N] 件です。
- validate: [N] 件 — 事前承認（design_diff + plan_review）が必要
- confirm: [N] 件 — 事前承認（plan_review）が必要
- autopilot: [N] 件 — 事前承認なしで実行可能

[最初のWI ID] から順番に進めてください。
困ったことがあれば私か [PM名] に相談してください。」
```

---

## 8. ベストプラクティス

### 上流工程でよくある失敗と対策

| 失敗パターン | 結果 | 対策 |
|-------------|------|------|
| AC の then が曖昧 | Execute Phase で「何をもって完了か」が不明 | then にアサーション可能な条件を書く |
| coverage_tier を安易に standard に | 会計影響があるのに autopilot で実行 | 迷ったら critical。下げるのは後でもできる |
| integration_flows の漏れ | Execute Phase で「連携先が未定義」の手戻り | basic_design レビュー時に全システム間フローを洗い出す |
| タスク粒度が大きすぎる | レビューが重い、問題発見が遅い | 3日超のタスクは必ず分割 |
| NFR の運用系が欠落 | リリース後に監視・アラートがない | NFR チェックリスト（§4.3）を毎回確認 |
| e2e タスクの triage 漏れ | flaky test が放置される | e2e 3点セット（harness, test, triage）を確認 |

### Claude Code との効果的な協働

- **セルフチェックは毎回依頼する**: 自分で YAML を読む前に Claude Code にチェックさせ、⚠️/❌ だけ確認
- **判断の理由を伝える**: 「standard にしてください」ではなく「会計影響がないので standard に変更してください」
- **blocking questions は即解消**: 放置すると Gate が通らず全体が止まる
- **Intake-First を活用する**: 要件が曖昧な段階では、Claude Code に聞き取らせた方が漏れが少ない

---

## 9. 関連ドキュメントマップ

```
┌─────────────────────────────────────────────────────────────────┐
│ 本ガイドの各 Phase の詳細                                       │
│   → 09_basic_design_guide.md（basic_design.md の詳細）          │
│   → 10_bpmn_guide.md（BPMN の作成方法）                        │
│   → 11_spec_guide.md（spec.md の詳細）                         │
│   → 12_plan_guide.md（plan.md の詳細）                         │
│   → 13_tasks_guide.md（tasks.md の詳細）                       │
│   → 19_coverage_policy.md（Coverage Policy の詳細）             │
├─────────────────────────────────────────────────────────────────┤
│ Gate 5 承認後                                                   │
│   → 07_practitioner_execution_guide.md（実施担当者ガイド）       │
├─────────────────────────────────────────────────────────────────┤
│ PM 視点                                                         │
│   → 05_pm_operations_guide.md（PM 向け）                     │
├─────────────────────────────────────────────────────────────────┤
│ YAML テンプレート                                               │
│   → 07_practitioner_execution_guide.md Appendix A               │
├─────────────────────────────────────────────────────────────────┤
│ ID 規約・lint の詳細                                            │
│   → appendix_a_id_conventions.md（ID 規約の正規表現全文）               │
│   → appendix_b_stride_lint.md（stride-lint の全ルール）                 │
└─────────────────────────────────────────────────────────────────┘
```

---

> SDD Templates Manual - 06. Tecnos-STRIDE 上流工程ガイド (v4.7)
