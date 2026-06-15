# 03. mcframe設計書からSDDへの移行ガイド

> **このガイドの目的**: mcframe アドオン機能設計書（画面）で設計してきた開発者が、SDDテンプレートで同じ内容をどう書くかを理解する

---

## 1. 3分で分かる違い

### 1.1 一番大きな違い：「何から始めるか」

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  【mcframe設計書】画面から始める                                 │
│                                                                 │
│    「こんな画面を作る」                                          │
│         ↓                                                       │
│    「この項目が必要」                                            │
│         ↓                                                       │
│    「この処理を実装」                                            │
│         ↓                                                       │
│    「動作確認する」                                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【SDD】要件から始める                                           │
│                                                                 │
│    「ユーザーは○○したい」（要件: RQ）                            │
│         ↓                                                       │
│    「だから○○できる機能が必要」（ユースケース: US）               │
│         ↓                                                       │
│    「○○したら△△になる」（受入条件: AC）← テストと同時に定義    │
│         ↓                                                       │
│    「APIは○○、DBは△△」（契約: CT）                             │
│         ↓                                                       │
│    「タスクAでAC-01を実装」（タスク: T）                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 実際の違いを見てみよう

**同じ「受注一覧画面」を設計する場合：**

#### mcframe設計書での書き方

```markdown
## 機能概要
### 【説明】
取引先からの受注データを一覧表示し、編集・削除を行う画面

### 【目的】
受注状況の確認と管理を効率化する

## 項目仕様
| № | 項目名 | 入力 | 型 | 桁数 |
|---|--------|------|-----|------|
| 1 | 取引先コード | | S | 10 |
| 2 | 受注日From | ● | D | 10 |
| 3 | 受注日To | ● | D | 10 |

## 動作確認
| No. | テスト観点 | 期待される結果 |
|-----|-----------|---------------|
| 1 | 一覧表示 | 該当データ表示 |
| 2 | 編集 | 更新完了メッセージ |
```

#### SDDでの書き方

```yaml
# basic_design.md（なぜ作るか）
basic_design:
  context:
    who: "受注担当者"
    what: "受注データの一覧表示・編集・削除"
    why: "受注状況の確認と管理を効率化"

# spec.md（何ができればOKか）
spec:
  use_cases:
    - id: "US-ORDER-001"
      title: "受注一覧表示"
      acceptance:
        - id: "AC-US-ORDER-001-01"
          statement: "取引先コードと受注日範囲で検索すると、該当する受注が一覧表示される"
          tags: ["integration"]
        - id: "AC-US-ORDER-001-02"
          statement: "一覧から行を選択して更新すると、更新完了メッセージが表示される"

# contracts/database_schema.yaml（DBの仕様）
tables:
  - name: "orders"
    columns:
      - name: "partner_code"
        type: "varchar"
        length: 10
      - name: "order_date"
        type: "date"

# tests/scenarios.yaml（テストシナリオ）
scenarios:
  - id: "SCN-001"
    covers_acs: ["AC-US-ORDER-001-01"]  # ← ACと紐付いている！
    steps:
      - action: "検索条件を入力して検索"
    expected:
      - description: "該当する受注が表示される"
```

**ポイント**:
- mcframe: 「項目仕様」と「動作確認」は別々に作成
- SDD: 「AC（受入条件）」と「テスト」が最初から紐付いている

---

## 2. mcframe開発者のための対応表

### 2.1 「あれはどこに書く？」早見表

| mcframeで書いていたこと | SDDではここに書く |
|------------------------|------------------|
| **機能概要の【説明】【目的】** | `basic_design.md` の `context.what/why` |
| **項目仕様（DB項目）** | `contracts/database_schema.yaml` |
| **電文項目仕様（API）** | `contracts/openapi.yaml` |
| **動作確認** | `spec.md` の `acceptance[]` + `tests/scenarios.yaml` |
| **処理・サービス関連図** | `process.bpmn` |
| **承認票** | `APPROVAL.md` |
| **来歴** | Git履歴 |
| **レビュー記録** | GitHub PR/Issues |

### 2.2 用語の対応表

| mcframe用語 | SDD用語 | 説明 |
|------------|--------|------|
| 機能概要 | **US（ユースケース）** | ユーザーが達成したいこと |
| 動作確認のテスト観点 | **AC（受入条件）** | 「何ができたらOKか」の定義 |
| 電文項目仕様 | **CT（契約）** + OpenAPI | API仕様を機械可読形式で |
| 項目仕様 | database_schema.yaml | DB仕様を機械可読形式で |
| 承認票 | **APPROVAL.md** | 人間の承認記録（AI編集禁止） |
| 来歴シート | **Git履歴** | 変更履歴はGitで自動管理 |

---

## 3. 具体的に何が変わるか

### 3.1 項目仕様の書き方

#### Before（mcframe）

```markdown
| № | 項目名 | 入力 | 型 | 桁数 | 説明 |
|---|--------|------|-----|------|------|
| 1 | 取引先コード | ● | S | 10 | 必須入力 |
| 2 | 受注番号 | | S | 20 | 自動採番 |
| 3 | 受注金額 | | N | 15,2 | 小数点以下2桁 |
```

#### After（SDD）

```yaml
# contracts/database_schema.yaml
tables:
  - id: "TBL-ORDERS"
    name: "orders"
    description: "受注テーブル"
    columns:
      - name: "partner_code"
        type: "varchar"
        length: 10
        nullable: false          # ← 必須
        description: "取引先コード"

      - name: "order_number"
        type: "varchar"
        length: 20
        nullable: false
        description: "受注番号（自動採番）"
        default: "auto-generated"

      - name: "order_amount"
        type: "decimal"
        precision: 15
        scale: 2                 # ← 小数点以下2桁
        description: "受注金額"
```

**何が嬉しいか**:
- YAMLなので**AIが読み書きできる**
- **stride-lint**で整合性を自動チェック
- マイグレーションツールと連携可能

---

### 3.2 電文項目仕様の書き方

#### Before（mcframe）

```markdown
### オペレーション: 受注検索
| 項目№ | 項目名 | 上り | 下り | 説明 |
|------|--------|-----|-----|------|
| 1 | 取引先コード | ● | ● | 検索キー |
| 2 | 受注日From | ● | | 検索条件 |
| 3 | 受注日To | ● | | 検索条件 |
| 4 | 受注番号 | | ● | 結果 |
| 5 | 受注金額 | | ● | 結果 |
```

#### After（SDD）

```yaml
# contracts/openapi.yaml
openapi: "3.1.0"
info:
  title: "受注管理API"
  version: "1.0.0"

paths:
  /api/v1/orders:
    get:
      operationId: "searchOrders"
      summary: "受注検索"
      parameters:
        - name: partner_code
          in: query
          schema:
            type: string
            maxLength: 10
          description: "取引先コード（検索キー）"
        - name: order_date_from
          in: query
          required: true
          schema:
            type: string
            format: date
          description: "受注日From"
        - name: order_date_to
          in: query
          required: true
          schema:
            type: string
            format: date
          description: "受注日To"
      responses:
        "200":
          description: "検索結果"
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Order"

components:
  schemas:
    Order:
      type: object
      properties:
        partner_code:
          type: string
        order_number:
          type: string
        order_amount:
          type: number
```

**何が嬉しいか**:
- **Swagger UI**でドキュメント自動生成
- **契約テスト**で自動検証可能
- **クライアントコード**を自動生成可能

---

### 3.3 動作確認の書き方

#### Before（mcframe）

```markdown
## 動作確認
| No. | テスト観点 | テスト方法 | 期待される結果 | 判定 |
|-----|-----------|-----------|---------------|------|
| 1 | 正常検索 | 検索条件入力→検索 | 該当データ表示 | |
| 2 | 該当なし | 存在しない条件で検索 | 0件メッセージ | |
| 3 | 更新成功 | 行選択→更新 | 更新完了メッセージ | |
```

**問題点**:
- 設計完了後に「後付け」で作成
- 仕様との紐付きが曖昧
- テスト漏れが発生しやすい

#### After（SDD）

**Step 1: spec.mdでACを定義**

```yaml
# spec.md
spec:
  use_cases:
    - id: "US-ORDER-001"
      title: "受注検索"
      acceptance:
        - id: "AC-US-ORDER-001-01"
          statement: "取引先コードと受注日範囲で検索すると、該当する受注が一覧表示される"
          tags: ["integration"]
          priority: "must"

        - id: "AC-US-ORDER-001-02"
          statement: "該当データがない場合、「該当なし」メッセージが表示される"
          tags: ["integration"]
          priority: "must"

        - id: "AC-US-ORDER-001-03"
          statement: "一覧から行を選択して更新すると、更新完了メッセージが表示される"
          tags: ["integration"]
          priority: "must"
```

**Step 2: tests/scenarios.yamlでテストシナリオを定義**

```yaml
# tests/scenarios.yaml
scenarios:
  - id: "SCN-001"
    name: "正常検索フロー"
    priority: "critical"
    covers_acs: ["AC-US-ORDER-001-01"]  # ← ACと紐付け！
    steps:
      - step: 1
        action: "取引先コード「A001」、受注日2025-01-01〜2025-01-31を入力"
      - step: 2
        action: "検索ボタンをクリック"
    expected:
      - id: "EXP-001-01"
        description: "取引先A001の2025年1月の受注が一覧表示される"
        verification_method: "UI確認"
    completion_checklist:
      - "expected が全て満たされているか"
      - "AC-US-ORDER-001-01 の全要素を確認したか"

  - id: "SCN-002"
    name: "該当なしフロー"
    priority: "high"
    covers_acs: ["AC-US-ORDER-001-02"]
    steps:
      - step: 1
        action: "存在しない取引先コード「ZZZZ」で検索"
    expected:
      - id: "EXP-002-01"
        description: "「該当なし」メッセージが表示される"
        verification_method: "UI確認"
```

**何が嬉しいか**:
- **ACとテストが最初から紐付き**、テスト漏れを防止
- **stride-lint**で「全ACがテストでカバーされているか」を自動検証
- **completion_checklist**でタスク完了時の確認漏れを防止

---

### 3.4 承認プロセスの違い

#### Before（mcframe）

```markdown
## 承認票
| Ver. | 作成日 | 変更内容 | 作成者 | 確認者 | 承認者 |
|------|--------|---------|--------|--------|--------|
| v1.00 | 2025-01-15 | 初版作成 | 山田 | 鈴木 | 佐藤 |
| v1.10 | 2025-01-20 | 項目追加 | 山田 | 鈴木 | 佐藤 |
```

**問題点**:
- バージョン単位で「全体承認」
- 小さな変更でも再承認が必要
- 何を承認したか曖昧になりがち

#### After（SDD）

```markdown
# APPROVAL.md

## Gate 1: Basic Design Gate
- [x] context（who/what/why）が明確
- [x] 制約・前提条件が定義されている
- **承認者**: 佐藤  **承認日**: 2025-01-10

## Gate 2: BPMN Gate
- [x] process.bpmn が作成されている
- [x] 開始/終了イベントが定義されている
- **承認者**: 佐藤  **承認日**: 2025-01-12

## Gate 3: Spec Gate
- [x] ユースケース（US-*）が1件以上
- [x] 受入条件（AC-*）が必須項目をカバー
- [x] stride-lint PASS
- **承認者**: 佐藤  **承認日**: 2025-01-15

## Gate 4: Plan Gate
- [x] 契約（CT-*）が定義されている
- [x] テスト計画（TS-*）がACをカバー
- **承認者**: 佐藤  **承認日**: 2025-01-18

## Gate 5: Tasks Gate
- [x] 全タスクがPlan IDと紐付いている
- **承認者**: 佐藤  **承認日**: 2025-01-20
```

**何が嬉しいか**:
- **段階的承認**で、手戻りを最小化
- **stride-lint PASS**が承認条件、機械検証で品質担保
- **AIは編集禁止**、人間の承認が確実に記録される

---

## 4. よくある質問

### Q1: 画面レイアウトはどこに書く？

**A**: SDDでは画面レイアウト自体は**補助資料**扱いです。

```
mcframe: レイアウト → 項目仕様 → 処理詳細
SDD:     AC（期待結果）が正本、レイアウトは implementation-details/ に補助資料として保管
```

重要なのは「ユーザーが何を見るか・何ができるか」をACに書くこと：

```yaml
# 良い例：期待結果をACに
acceptance:
  - id: "AC-001"
    statement: "検索ボタンをクリックすると、受注一覧が表形式で表示される"

# 補助資料として残す場合
# implementation-details/ui_layout.md に画面キャプチャやモックを保管
```

### Q2: 処理詳細（C/S区分）はどこに書く？

**A**: `process.bpmn` + `plan.md` の組み合わせで表現します。

```yaml
# plan.md
plan:
  architecture:
    components:
      - id: "COMP-FE"
        name: "フロントエンド"
        responsibility: "UI表示、入力バリデーション"
      - id: "COMP-API"
        name: "APIサーバー"
        responsibility: "ビジネスロジック、DB操作"

  contracts:
    apis_events:
      - id: "CT-API-01"
        name: "受注検索API"
        protocol: "REST"
        direction: "inbound"  # フロント→API
```

### Q3: メッセージ一覧はどこに書く？

**A**: `implementation-details/messages.yaml` に機械可読形式で：

```yaml
# implementation-details/messages.yaml
messages:
  - id: "MSG-001"
    code: "E0001"
    severity: "error"
    text_ja: "取引先コードが見つかりません"
    text_en: "Partner code not found"

  - id: "MSG-002"
    code: "I0001"
    severity: "info"
    text_ja: "更新が完了しました"
```

エラー時の期待結果は**ACとして定義**：

```yaml
# spec.md
acceptance:
  - id: "AC-ERROR-01"
    statement: "存在しない取引先コードを入力すると、エラーメッセージ「取引先コードが見つかりません」が表示される"
```

### Q4: stride-lint って何？

**A**: SDDの整合性を自動チェックするツールです。

```bash
# 実行方法
python3 sdd-templates/tools/stride_lint.py specs/my_feature/

# チェック内容
✓ 全ACがテストでカバーされているか
✓ IDの命名規則が正しいか
✓ トレーサビリティ（RQ→US→AC→CT→TS）が正しいか
✓ 承認状態が正しいか
```

---

## 5. 移行チェックリスト

mcframe設計書からSDDへ移行する際のステップ：

### Step 1: basic_design.md を作成

- [ ] 【説明】→ `context.what`
- [ ] 【目的】→ `context.why`
- [ ] 前提条件 → `assumptions[]`
- [ ] データアクセスコントロール → `requirements.security_privacy[]`

### Step 2: spec.md を作成

- [ ] 機能概要 → `use_cases[]`
- [ ] 動作確認のテスト観点 → `acceptance[]`
- [ ] 各ACにタグ付け（`integration`/`e2e`等）

### Step 3: 契約ファイルを作成

- [ ] 項目仕様 → `contracts/database_schema.yaml`
- [ ] 電文項目仕様 → `contracts/openapi.yaml`
- [ ] 動作確認 → `tests/scenarios.yaml`

### Step 4: plan.md を作成

- [ ] サービス呼出仕様 → `contracts.apis_events[]`
- [ ] テスト計画 → `test_strategy.tests[]`

### Step 5: process.bpmn を作成

- [ ] Feature の処理・サービス関連図 → `process.bpmn` の BPMNタスク/フロー
- [ ] 画面遷移 → `process.bpmn` の BPMNシーケンスフロー
- [ ] チーム間/システム間の概観が必要なら `epic_flow.bpmn` に切り出す

### Step 6: 検証

- [ ] `stride-lint` を実行
- [ ] エラーを全て解消
- [ ] APPROVAL.md を作成し承認取得

---

## 6. 対応表リファレンス（詳細）

### 6.1 mcframeシート → SDDファイル対応

| mcframeシート | SDDファイル | 備考 |
|--------------|------------|------|
| 表紙 | `basic_design.md` frontmatter | YAML部分 |
| 来歴 | Git履歴 | `git log` |
| 承認票 | `APPROVAL.md` | AI編集禁止 |
| レビュー記録 | GitHub PR/Issues | |
| 機能概要 | `basic_design.md` + `spec.md` | |
| レイアウト | `implementation-details/ui_layout.md` | 補助資料 |
| 項目仕様 | `contracts/database_schema.yaml` | |
| 操作種別・検索モード | `spec.md` use_cases | |
| 処理・サービス関連図 | `process.bpmn` | Feature 実装フローの BPMN 2.0形式 |
| 検索入出力仕様 | `plan.md` + `contracts/openapi.yaml` | |
| 更新入出力仕様 | `plan.md` + `contracts/openapi.yaml` | |
| ファイル入出力仕様 | `contracts/file_spec.yaml` | |
| 画面遷移 | `process.bpmn` | Feature 内フロー |
| メッセージ一覧 | `implementation-details/messages.yaml` | |
| 補助説明書 | `implementation-details/` | |
| 動作確認 | `spec.md` AC + `tests/scenarios.yaml` | |
| 処理詳細 | `plan.md` + `implementation-details/` | |
| サービス呼出仕様 | `contracts/openapi.yaml` | |
| 電文項目仕様 | `contracts/openapi.yaml` | |

### 6.2 mcframe項目属性 → database_schema.yaml対応

| mcframe | database_schema.yaml | 例 |
|---------|---------------------|-----|
| 入力（●/空欄） | `nullable: false/true` | `nullable: false` |
| 型（S） | `type: "varchar"` | 文字列 |
| 型（N） | `type: "integer"` or `"decimal"` | 数値 |
| 型（D） | `type: "date"` | 日付 |
| 桁数 | `length` / `precision` | `length: 10` |
| 説明 | `description` | |
| 初期値 | `default` | |

---

## 7. まとめ

### mcframe設計書とSDDの本質的な違い

| 観点 | mcframe設計書 | SDD |
|-----|--------------|-----|
| **起点** | 画面 | 要件（なぜ作るか） |
| **正本** | Excel/Markdown | YAML（機械可読） |
| **テスト** | 後付け | ACと同時定義 |
| **検証** | 人手レビューのみ | stride-lint + レビュー |
| **承認** | バージョン単位 | Phase Gate単位 |
| **AI対応** | 考慮なし | YAML正本でAI読み書き可 |

### SDDを使う最大のメリット

1. **テスト漏れ防止**: ACとテストが紐付き、stride-lintで自動検証
2. **トレーサビリティ**: 「このコードはどの要件を実現しているか」が追跡可能
3. **早期問題検出**: 設計段階でstride-lintがエラーを検出
4. **AI活用**: YAML正本でAIが直接読み書き可能

---

> SDD Templates Manual - mcframe移行ガイド
