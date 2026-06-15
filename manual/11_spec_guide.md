# 11. 仕様書ガイド - spec.md の書き方

**所要時間**: 約30分

---

## このガイドで学ぶこと

1. spec.md の目的
2. ユースケース（US）の書き方
3. 受入条件（AC）の書き方とタグ付け
4. 非機能要件（NFR）の書き方
5. Spec-as-Code
6. **scenarios.yaml の構造（v1.2.5更新）** - タスク完了検証のチェックリスト

---

**サンプル参照**: `sdd-templates/specs/sample_feature` に Web-EDI の参考サンプルがあります（未承認/プレースホルダあり）。  
**注**: パスは例なので、自分の機能では `specs/<feature>` に置き換えます。

## 1. spec.md の目的

### 何を書くか

**spec.md** は「WHAT（何を）」「WHY（なぜ）」を定義する仕様書です。

| 書くこと | 書かないこと |
|----------|-------------|
| ユースケース（US） | 実装方法 |
| 受入条件（AC） | 技術選定 |
| 非機能要件（NFR） | API設計詳細 |
| 業務用語の定義 | コード |

### 重要な原則

```
「HOW（どのように）」は書かない → plan.md へ
```

### 初心者向けの書き方の順序

1. **overview（who/what/why）** を書く  
2. **use_cases** を1件作る（主語・トリガー・主フロー）  
3. **acceptance（AC）** を3件書く（テスト可能な文章）  
4. **requirements（NFR）** を6カテゴリで埋める  
5. **spec_as_code** の最小セットを定義する

### このパートの引き渡し（次の成果物との関係）

spec は「合否の基準」です。ここで決めたACが、PlanとTasksの起点になります。

```
spec
  -> plan.md      : 契約(CT)とテスト(TS)の設計起点
  -> tasks.md     : ACを実行可能な作業へ分解
  -> evidence_pack: 実施したテストの証跡を集める対象
```

**最低限引き渡すべき項目**:
- use_cases / acceptance（US/AC）
- requirements（NFR）
- spec_as_code.artifacts（機械可読仕様のパス）

---

## 2. 構成要素の詳細

### 2.1 Front Matter

```yaml
---
artifact: "spec"
template_id: "TPL-SPEC-TECNOS-001"
feature_id: "FEAT-001"
spec_id: "SPEC-001"
version: "{{TEMPLATE_VERSION}}"      # stride initで自動設定
title: "Web-EDI受注受付 Specification"
status: "draft"
owners:
  - { name: "山田太郎", role: "Product Owner / Business" }
  - { name: "鈴木一郎", role: "Tech Lead" }
links:
  basic_design_ref: "specs/<feature>/basic_design.md"
  process_bpmn_ref: "specs/<feature>/process.bpmn"
created_at: "2025-01-15"
updated_at: "2025-01-15"
---
```

### 2.2 overview

```yaml
spec:
  overview:
    who: "取引先の購買担当者が、Web-EDIポータルから発注する"
    what: "発注データを送信し、受注番号と納期回答を受け取る"
    why: "手入力と確認作業を減らし、受注処理のスピードと正確性を高める"
```

### 2.3 business_value

```yaml
  business_value:
    kpis:
      - "受注登録時間: 20分 → 5分（75%削減）"
      - "誤入力率: 1.0% → 0.1%"
      - "問い合わせ件数: 月200件 → 月80件"
    financial_hypotheses:
      revenue_uplift: "納期回答の早期化による取りこぼし削減（売上+2%を期待）"
      cost_reduction: "受注入力工数削減（年間600時間）"
      risk_reduction: "誤入力による出荷トラブルの低減"
```

### 2.4 goals / non_goals

```yaml
  goals:
    - "Web-EDI発注受付"
    - "受注番号と納期回答の即時返却"
    - "発注データの自動登録"

  non_goals:
    - "請求書発行・入金処理"
    - "EDI標準(JCA/EDI)との相互接続"
    - "モバイルアプリ対応"
    - "出荷通知の自動連携（Phase 2）"
```

### 2.5 domain_terms

```yaml
  domain_terms:
    - term: "Web-EDI"
      definition: "取引先がブラウザから発注を入力・送信できる仕組み"
    - term: "受注番号"
      definition: "ERPで発番される受注の識別子"
    - term: "取引先コード"
      definition: "ERP上で取引先を識別するID"
    - term: "SoR"
      definition: "System of Record - データの正本を保持するシステム"
```

---

## 3. ユースケース（US）の書き方

### 3.1 構造

```yaml
  use_cases:
    - id: "US-FEAT001-001"
      title: "Web-EDI発注送信"
      primary_actor: "取引先購買担当者"
      trigger: "Web-EDIで発注を送信"
      preconditions:
        - "取引先が有効な取引先コードでログイン済み"
        - "商品マスタがERPに登録済み"
      main_flow:
        - "取引先が発注データを入力またはCSVアップロードする"
        - "システムが必須項目と商品コードを検証する"
        - "システムがERPに受注を登録する"
        - "システムが受注番号と納期回答を表示する"
      alternate_flows:
        - "商品コードが無効な場合、エラーメッセージを表示する"
      postconditions:
        - "受注番号と納期回答が画面に表示されている"
      acceptance:
        # ← 次のセクションで詳細説明
```

### 3.2 ID命名規則

```
US-FEAT<機能ID>-<連番>

例: US-FEAT001-001, US-FEAT001-002
```

---

## 4. 受入条件（AC）の書き方とタグ付け

### 4.1 ACの書き方

**良いACの条件**:
1. テスト可能である
2. 曖昧な言葉がない
3. 前提条件・操作・期待結果が明確

**書き方の型（初心者向け）**:
- **Given**（前提）: 「取引先IDが有効」など
- **When**（操作）: 「CSVを送信する」など
- **Then**（結果）: 「60秒以内に受注番号が表示される」など

```yaml
      acceptance:
        - id: "AC-US-FEAT001-001-01"
          statement: "取引先ID「P-1001」で発注CSV(10行)をアップロードすると、60秒以内に受注番号「SO-2025-000123」が表示される"
          tags: ["integration", "performance"]
          priority: "must"

        - id: "AC-US-FEAT001-001-02"
          statement: "発注数量が在庫不足の場合、納期回答日（YYYY-MM-DD）が表示される"
          tags: ["integration", "e2e"]
          priority: "must"

        - id: "AC-US-FEAT001-001-03"
          statement: "未登録商品コードを含む発注は、「商品コードが無効です」エラーが表示され、受注は登録されない"
          tags: ["integration"]
          priority: "must"
```

### 4.2 ACの悪い例と良い例

| 悪い例 | 問題点 | 良い例 |
|--------|--------|--------|
| 「速く表示される」 | 曖昧 | 「3秒以内に表示される」 |
| 「正しく動作する」 | テスト不能 | 「受注番号が表示される」 |
| 「使いやすい」 | 主観的 | 「3クリック以内で目的の画面に到達できる」 |

### 4.3 タグの意味と使い分け

| タグ | 意味 | 必要なテスト | 使用場面 |
|------|------|-------------|----------|
| `integration` | 統合テストが必要 | TS-INT-* | 外部システム連携、API呼び出し |
| `e2e` | E2Eテストが必要 | TS-E2E-* | 重要ユーザージャーニー |
| `security` | セキュリティ観点 | - | 認証、認可、データ保護 |
| `performance` | 性能観点 | - | 応答時間、スループット |
| `data` | データ観点 | - | データ整合性、移行 |
| `ops` | 運用観点 | - | 監視、ログ、復旧 |

### 4.4 タグの重要なルール

```
integration タグ → TS-INT-* でカバー必須
e2e タグ → TS-E2E-* でカバー必須
```

**注意**: e2eタグは「重要ユーザージャーニー」に限定する（Simplicity原則）

### 4.5 priority

| 値 | 意味 |
|-----|------|
| `must` | 必須（MoSCoW の M） |
| `should` | 重要（MoSCoW の S） |
| `could` | あれば良い（MoSCoW の C） |

---

## 5. 非機能要件（NFR）の書き方

### 5.1 必須の6カテゴリ

**最低各1件** 定義する必要があります。

```yaml
  requirements:
    # 1. 統合要件
    integration:
      - "ERP受注登録APIは最大3回リトライする"
      - "Correlation IDを全ログに出力し、追跡可能にする"
      - "ERP接続タイムアウトは30秒とする"

    # 2. データガバナンス
    data_governance:
      - "受注データのSoRはERPとする"
      - "取引先マスタのSoRはERPとする"
      - "受注データは7年間保管する"

    # 3. 性能
    performance:
      - "発注受付のP95応答時間は60秒以内"
      - "同時接続200社をサポートする"

    # 4. 可用性・信頼性
    availability_reliability:
      - "システム可用性99.5%（月間ダウンタイム3.6時間以内）"
      - "障害時は自動フェイルオーバーする"

    # 5. セキュリティ・プライバシー
    security_privacy:
      - "認証はSSOを使用する"
      - "APIアクセスはJWTトークンで認可する"
      - "監査ログは180日間保持する"

    # 6. 運用
    operations:
      - "エラー発生時はSlack #ops-alerts に通知する"
      - "メトリクス（応答時間、エラー率）を監視ツールに送信する"
```

**迷ったら**: 数値や方針が未確定の場合は `open_questions` に記録し、  
**blocking: true** を付けて合意が取れるまでGateを通さないようにします。

---

## 6. Spec-as-Code

### 6.1 目的

仕様を**機械可読**な形式で保持し、AI/HITLで検証可能にする。

### 6.2 必須の成果物

```yaml
  spec_as_code:
    artifacts:
      - type: "openapi"
        path: "specs/<feature>/contracts/openapi.yaml"
        schema_version: "3.1.0"
        status: "draft"

      - type: "database_schema"    # v1.2.5追加（任意）
        path: "specs/<feature>/contracts/database_schema.yaml"
        schema_version: "1.0"
        status: "draft"

      - type: "schema_json"        # v4.8.0追加（AI/RAG向け、任意）
        path: "docs/schema/<feature>/schema.json"
        schema_version: "1.0"
        status: "not_applicable"  # ai_metadata有効化後に "generated" へ変更

      - type: "migration_mapping"
        path: "specs/<feature>/implementation-details/migration_mapping.yaml"
        schema_version: "1.0"
        status: "draft"

      - type: "authz_matrix"
        path: "specs/<feature>/implementation-details/authz_matrix.yaml"
        schema_version: "1.0"
        status: "draft"

      - type: "test_scenarios"
        path: "specs/<feature>/tests/scenarios.yaml"
        schema_version: "1.0"
        status: "draft"

    validation:
      schema_validation: true
      lint_required: true
```

**最小構成（初心者向け）**:
- まずは `openapi` と `test_scenarios` を用意
- データ移行や権限が重要な案件では `migration_mapping` / `authz_matrix` を追加
- **データベースを使用する案件**では `database_schema` を追加

### 6.3 各成果物の説明

| 種類 | 説明 | 配置場所 | 必須 |
|------|------|----------|------|
| openapi | REST API定義 | `contracts/openapi.yaml` | ✅ |
| database_schema | DBスキーマ定義（v1.2.5） | `contracts/database_schema.yaml` | DB使用時 |
| schema_json | AI/RAG向けスキーマJSON（v4.8.0） | `docs/schema/<feature>/schema.json` | ai_metadata有効時 |
| migration_mapping | データ移行マッピング | `implementation-details/migration_mapping.yaml` | 移行時 |
| authz_matrix | 権限マトリクス | `implementation-details/authz_matrix.yaml` | 権限管理時 |
| test_scenarios | テストシナリオ | `tests/scenarios.yaml` | ✅ |

### 6.4 test_scenarios（scenarios.yaml）の構造（v1.2.5更新）

`tests/scenarios.yaml` は、E2E検証シナリオを定義し、**タスク完了検証のチェックリスト**として機能します。

#### v1.2.5 で追加されたフィールド

| フィールド | 説明 | 用途 |
|-----------|------|------|
| `feature_id` | 機能ID | トレーサビリティ |
| `priority` | 優先度（critical/high/medium/low） | テスト優先順位 |
| `covers_acs` | カバーするACのリスト | ACとの紐付け |
| `steps[].step` / `steps[].action` | 手順番号とアクション | 構造化された手順 |
| `completion_checklist` | 完了検証チェックリスト | タスク完了時の確認項目 |

#### 構造例

```yaml
test_scenarios:
  version: "{{TEMPLATE_VERSION}}"    # stride initで自動設定
  feature_id: "FEAT-001"

  usage_guide:
    purpose: "タスク完了検証のチェックリストとして使用"
    when_to_use: "タスク完了報告の前に必ず確認"

  scenarios:
    - id: "SCN-001"
      name: "基本フロー（正常系）"
      description: "最も基本的なユーザージャーニーの検証"
      priority: "critical"

      # ACとの紐付け（重要）
      covers_acs:
        - "AC-US-FEAT001-001-01"
        - "AC-US-FEAT001-001-02"

      preconditions:
        - "前提条件1"

      # 構造化された手順
      steps:
        - step: 1
          action: "操作1を記載"
        - step: 2
          action: "操作2を記載"

      expected:
        - id: "EXP-001-01"
          description: "期待結果1"
          verification_method: "UI確認"

      # タスク完了時のチェックリスト
      completion_checklist:
        - "全 expected が満たされているか"
        - "covers_acs の全ACに記載された要素を満たしているか"

  verification_instructions:
    before_completion:
      - "covers_acs に含まれる全ACを spec.md で再読する"
      - "各 expected を一つずつ検証する"
```

#### タスク完了検証での使い方

1. タスク完了報告前に `tests/scenarios.yaml` を開く
2. 該当タスクに関連するシナリオを `covers_acs` で特定
3. シナリオの全 `expected` を一つずつ検証
4. `completion_checklist` の全項目を確認
5. [06. タスクガイド](13_tasks_guide.md#11-task-completion-checklistv125-必須) のフォーマットで報告

---

### 6.5 database_schema の使い方（v1.2.5新規）

データベースを使用する機能では、`database_schema` を定義することで以下のメリットがあります：

1. **トレーサビリティ**: テーブル ↔ ユースケース ↔ 契約の紐付け
2. **データガバナンス**: PII、監査、暗号化ポリシーの明文化
3. **マイグレーション計画**: スキーマ変更の追跡
4. **stride-lint連携**: スキーマ整合性の自動検証

#### セットアップ

```bash
# テンプレートをコピー
cp sdd-templates/templates/contracts/database_schema_template.yaml \
   specs/<feature>/contracts/database_schema.yaml

# プレースホルダーを置換
sed -i '' 's/FEAT-XXX/FEAT-001/g' specs/<feature>/contracts/database_schema.yaml
sed -i '' 's/XXX_feature_name/<feature>/g' specs/<feature>/contracts/database_schema.yaml
```

#### 最小構成例

```yaml
database_schema:
  meta:
    schema_id: "DB-FEAT-001"
    feature_id: "FEAT-001"
    dialect: "postgresql"
    status: "draft"

  traceability:
    spec_ref: "specs/my_feature/spec.md"
    related_contracts: ["CT-API-01"]
    related_use_cases: ["US-FEAT001-001"]

  data_governance:
    data_classification: "Internal"
    contains_pii: false
    audit_log_required: true
    retention_policy: "7 years"

  tables:
    - name: "orders"
      description: "受注データ"
      domain_object: "Order"
      columns:
        - name: "id"
          type: "uuid"
          primary_key: true
        - name: "order_number"
          type: "varchar(50)"
          nullable: false
        - name: "created_at"
          type: "timestamp with time zone"
          default: "CURRENT_TIMESTAMP"
```

#### spec.md への登録

```yaml
# spec.md
spec_as_code:
  artifacts:
    - type: "database_schema"
      path: "specs/my_feature/contracts/database_schema.yaml"
      schema_version: "1.0"
      status: "draft"
```

> **注**: データベースを使わない機能（フロントエンドのみ、外部API呼び出しのみ等）では、`database_schema` は不要です。

### 6.6 database_schema の AI 生成ワークフロー（v1.2.5新規）

CSVファイルや自然言語のテキスト情報から、AIを使って `database_schema.yaml` を生成する場合の品質担保ワークフローです。

#### 概要：4フェーズワークフロー

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI生成 品質担保ワークフロー                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Phase 1: 入力準備              Phase 2: AI生成                      │
│  ┌──────────────────┐          ┌──────────────────┐                 │
│  │ CSV / NL / DDL   │ ──────▶ │ 段階的生成       │                 │
│  │ ↓                │          │ (meta→table→rel) │                 │
│  │ 標準化・レビュー  │          │ ↓                │                 │
│  │ [Gate 1: 入力確認]│          │ [Gate 2: 各段階] │                 │
│  └──────────────────┘          └──────────────────┘                 │
│           │                             │                            │
│           ▼                             ▼                            │
│  Phase 3: 検証                 Phase 4: 承認                        │
│  ┌──────────────────┐          ┌──────────────────┐                 │
│  │ stride-lint     │          │ human review     │                 │
│  │ SQL構文チェック   │          │ PII最終確認      │                 │
│  │ ↓                │          │ ↓                │                 │
│  │ [Gate 3: Lint]   │          │ [Gate 4: 承認]   │                 │
│  └──────────────────┘          └──────────────────┘                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

#### Phase 1: 入力準備と標準化

##### 推奨入力形式（優先順）

| 形式 | 品質 | 用途 | 備考 |
|------|------|------|------|
| **CSV（推奨）** | ◎ | 新規設計 | 構造化済み、レビュー容易 |
| **既存DDL** | ○ | マイグレーション | 型変換が必要 |
| **自然言語** | △ | 初期検討 | AI解釈誤りのリスク高 |

##### CSV入力テンプレート

以下のCSV形式を使用すると、AIの解釈誤りを最小化できます：

```bash
cp sdd-templates/templates/contracts/database_schema_input.csv \
   specs/<feature>/contracts/database_schema_input.csv
```

```csv
table_name,column_name,type,nullable,pk,uk,fk_table,fk_column,default,description,pii_flag,audit_flag
orders,id,uuid,false,true,false,,,gen_random_uuid(),主キー,false,false
orders,customer_id,uuid,false,false,false,customers,id,,顧客参照,false,false
orders,order_number,varchar(50),false,false,true,,,,"受注番号（業務キー）",false,true
orders,customer_name,varchar(100),false,false,false,,,,顧客名,true,false
orders,email,varchar(255),true,false,false,,,,連絡先メール,true,false
orders,total_amount,"decimal(12,2)",false,false,false,,,0,合計金額,false,false
orders,status,varchar(20),false,false,false,,,"'pending'",ステータス（pending/confirmed/completed/cancelled）,false,true
order_items,id,uuid,false,true,false,,,gen_random_uuid(),主キー,false,false
order_items,order_id,uuid,false,false,false,orders,id,,受注参照,false,false
order_items,product_id,uuid,false,false,false,products,id,,商品参照,false,false
order_items,quantity,integer,false,false,false,,,1,数量,false,false
order_items,unit_price,"decimal(10,2)",false,false,false,,,0,単価,false,false
order_items,line_total,"decimal(12,2)",false,false,false,,,0,明細金額,false,false
```

**補足**: 監査カラム（created_at, updated_at, created_by, updated_by）は最終YAMLで必須です。CSVでは省略し、AI生成時に追加してください。

**CSV列の説明**:

| 列名 | 説明 | 必須 |
|------|------|------|
| `table_name` | テーブル名 | ✅ |
| `column_name` | カラム名 | ✅ |
| `type` | データ型（Dialect準拠） | ✅ |
| `nullable` | NULL許可（true/false） | ✅ |
| `pk` | 主キー（true/false） | ✅ |
| `uk` | ユニーク制約（true/false） | |
| `fk_table` | 外部キー参照先テーブル | |
| `fk_column` | 外部キー参照先カラム | |
| `default` | デフォルト値 | |
| `description` | 説明 | ✅ |
| `pii_flag` | PII該当（true/false） | ✅ |
| `audit_flag` | 監査対象（true/false） | |

##### pii_flag と audit_flag の判断基準

**pii_flag（個人情報フラグ）**

`true` に設定すべきデータ：

| カテゴリ | 例 |
|---------|-----|
| **識別情報** | 氏名、住所、電話番号、メールアドレス、生年月日 |
| **ID情報** | マイナンバー、パスポート番号、運転免許証番号、社員番号 |
| **金融情報** | 銀行口座番号、クレジットカード番号、年収 |
| **医療情報** | 病歴、処方薬、健康診断結果 |
| **認証情報** | パスワードハッシュ、セキュリティ質問の回答 |
| **位置情報** | GPS座標、IPアドレス（個人特定可能な場合） |

`pii_flag=true` の効果：
- `data_governance.encryption.columns` に自動追加（暗号化対象）
- データアクセスログの詳細化
- データエクスポート時の匿名化/マスキング対象

**audit_flag（監査フラグ）**

`true` に設定すべきデータ：

| カテゴリ | 例 |
|---------|-----|
| **業務キー** | 受注番号、請求書番号、取引ID |
| **ステータス** | 承認状態、処理状態、フロー進捗 |
| **金額** | 取引金額、割引額、税額 |
| **日時** | 処理日時、承認日時、有効期限 |
| **担当者** | 承認者、処理者、変更者 |

`audit_flag=true` の効果：
- 変更履歴テーブル（`*_history`）への記録対象
- 監査ログへの出力対象
- 会計監査・内部統制の証跡対象

**判断フローチャート**:

```
カラムを追加
    │
    ├─ 個人を特定できる情報か？
    │      │
    │      ├─ Yes → pii_flag=true
    │      └─ No  → pii_flag=false
    │
    └─ 変更履歴を残す必要があるか？
           │
           ├─ 業務上の重要データ → audit_flag=true
           ├─ 法的要件あり      → audit_flag=true
           └─ 参照用データのみ  → audit_flag=false
```

##### 自然言語入力の場合

自然言語から生成する場合は、以下の情報を明示的に記述してください：

```markdown
# データベース要件（自然言語）

## 対象機能
- Feature ID: FEAT-001
- 機能名: 受注管理

## テーブル構成
1. orders（受注）テーブル
   - 主キー: UUID
   - 業務キー: 受注番号（50文字、ユニーク）
   - 顧客参照: customers テーブルの id を参照
   - 金額: 小数点2桁、最大10桁
   - ステータス: pending / confirmed / completed / cancelled

2. order_items（受注明細）テーブル
   - 主キー: UUID
   - 親参照: orders テーブルの id を参照（CASCADE削除）
   - 商品参照: products テーブルの id を参照
   - 数量: 整数、1以上

## データガバナンス
- 顧客名、メールアドレスは PII
- 全テーブルに監査カラム必須（created_at, updated_at, created_by, updated_by）
- データ保持期間: 7年
```

##### Gate 1: 入力確認チェックリスト

AI生成を開始する前に、以下を確認：

- [ ] 全テーブルに主キーが定義されている
- [ ] 外部キーの参照先テーブルが存在する
- [ ] PII列が明示的にマークされている
- [ ] データ型がターゲットDialectに適合している

---

#### Phase 2: AI生成（段階的アプローチ）

> **重要**: 一括生成ではなく、セクションごとに生成・確認することで品質を担保します。

##### 生成順序

```
Step 1: meta セクション
    ↓ [確認]
Step 2: data_governance セクション
    ↓ [確認: 特にPII]
Step 3: tables セクション（カラム定義）
    ↓ [確認]
Step 4: indexes / constraints セクション
    ↓ [確認]
Step 5: relationships セクション
    ↓ [確認]
Step 6: traceability セクション
    ↓ [最終確認]
```

##### AIプロンプトテンプレート（推奨）

```markdown
# database_schema.yaml 生成依頼

## 基本情報
- Feature ID: FEAT-001
- Dialect: postgresql
- データ分類: Internal
- 監査要件: 全テーブルに監査カラム必須

## 入力データ
[CSV または 自然言語テキストをここに貼り付け]

## 生成ルール（厳守）
1. schema_id は "DB-FEAT-001" 形式
2. 全テーブルに以下の監査カラムを追加:
   - created_at (timestamp with time zone, default CURRENT_TIMESTAMP)
   - updated_at (timestamp with time zone, default CURRENT_TIMESTAMP)
   - created_by (varchar(100), nullable)
   - updated_by (varchar(100), nullable)
3. 全外部キーにインデックスを追加
4. PII列は data_governance.encryption.columns に追加
5. 型は PostgreSQL 構文に統一

## 不明点の報告
以下の場合は [UNCERTAIN] タグで明示:
- 型推論に自信がない場合
- リレーションシップが不明確な場合
- PII判定に迷う場合

## 出力形式
sdd-templates/templates/contracts/database_schema_template.yaml
の形式に準拠した YAML を出力してください。
```

##### Gate 2: 各段階の確認ポイント

| Step | 確認項目 |
|------|---------|
| meta | schema_id, feature_id, dialect が正しいか |
| data_governance | contains_pii, encryption.columns が入力と一致するか |
| tables | 全カラムの型、制約が入力と一致するか |
| indexes | 全FKにインデックスがあるか |
| relationships | FK定義と一致するか |
| traceability | spec_ref, plan_ref のパスが存在するか |

---

#### Phase 3: 検証

##### 自動検証

```bash
# 1. stride-lint で形式検証
sdd-templates/tools/stride-lint specs/<feature>/

# 2. YAML構文検証（オプション）
python3 -c "import yaml; yaml.safe_load(open('specs/<feature>/contracts/database_schema.yaml'))"

# 3. SQL生成テスト（オプション：DDL生成可能か確認）
# 独自スクリプトまたはORMツールで検証
```

##### Gate 3: Lint検証チェックリスト

stride-lint の以下のエラーが出ないことを確認：

| エラーコード | 説明 |
|-------------|------|
| `DATABASE_SCHEMA_UNDEFINED` | spec.md に database_schema が未登録 |
| `ID_REGEX_MISMATCH` | schema_id が規約に違反 |
| `MISSING_TRACEABILITY` | traceability リンク切れ |

---

#### Phase 4: 人間レビューと承認

##### 最終レビューチェックリスト

**データガバナンス（必須レビュー）**:
- [ ] PII列が全て `encryption.columns` に含まれている
- [ ] `data_classification` が適切（Public/Internal/Confidential/Regulated）
- [ ] `retention_policy` が組織ポリシーに準拠
- [ ] 監査カラムが全テーブルに存在

**整合性（必須レビュー）**:
- [ ] 全テーブルに主キーが存在
- [ ] 外部キーの参照先が存在
- [ ] インデックスが性能要件を満たす

**トレーサビリティ（必須レビュー）**:
- [ ] `spec_ref`, `plan_ref` のファイルが存在
- [ ] `related_use_cases` が spec.md の US-* と一致
- [ ] `related_contracts` が plan.md の CT-* と一致

##### AIが [UNCERTAIN] タグを付けた箇所

AIが不確実とマークした箇所は、必ず人間が判断してください：

```yaml
# 例: AIが不確実とした箇所
columns:
  - name: "customer_code"
    type: "varchar(20)"  # [UNCERTAIN] 桁数が不明、要確認
    description: "顧客コード"
    # [UNCERTAIN] PIIかどうか判断できない - 業務要件を確認
```

##### Gate 4: 承認

全チェックリストを確認後、`database_schema_gate_check` を更新：

```yaml
database_schema_gate_check:
  tables_defined: true
  relationships_documented: true
  data_governance_defined: true
  traceability_linked: true
  ready_for_migration: true  # ← 承認完了
```

---

#### アンチパターン（避けるべき方法）

| パターン | 問題点 | 対策 |
|---------|--------|------|
| 一括生成 | エラーが連鎖、修正困難 | 段階的生成を使用 |
| PII自動判定のみ | 見落とし・誤検知のリスク | 必ず人間レビュー |
| Lint後回し | エラー蓄積 | 各段階でLint実行 |
| traceability後回し | リンク切れ発生 | 最初にパス確認 |
| 型の曖昧指定 | DDL生成失敗 | Dialect固有の型を明示 |

---

#### クイックスタート: AI生成コマンド例

```bash
# 1. CSVテンプレートをコピー
cp sdd-templates/templates/contracts/database_schema_input.csv /tmp/tables.csv

# 2. CSVを編集してテーブル定義を記入
vi /tmp/tables.csv

# 3. テンプレートをコピー
cp sdd-templates/templates/contracts/database_schema_template.yaml \
   specs/<feature>/contracts/database_schema.yaml

# 4. AIに生成依頼（Claude Code等）
# プロンプト: "以下のCSVから database_schema.yaml を生成してください。
#             Feature ID: FEAT-001, Dialect: postgresql"
# [CSVを貼り付け]

# 5. 生成されたYAMLで上書き
# specs/<feature>/contracts/database_schema.yaml

# 6. Lint検証
sdd-templates/tools/stride-lint specs/<feature>/

# 7. 人間レビュー（PIIとtraceability必須）

# 8. spec.md に登録
# spec_as_code.artifacts に database_schema を追加
```

---

## 7. counts の更新

```yaml
derived_fields:
  counts_are_computed: true
  counts:
    use_cases: 2                    # USの件数
    acceptance_criteria: 6          # ACの合計件数
    integration_tagged_ac: 4        # integrationタグ付きAC
    e2e_tagged_ac: 2               # e2eタグ付きAC
    blocking_questions: 0           # blocking質問数
    nfr_items: 12                   # NFR合計件数
    security_items: 3               # security_privacy件数
    integration_items: 3            # integration件数
    data_items: 3                   # data_governance件数
    spec_as_code_artifacts: 5       # Spec-as-Code成果物数（v4.8.0: +schema_json）
```

**重要**: ACやNFRを追加したら、countsも更新する

---

## 8. ゲート通過条件

### Spec Gate の条件

```yaml
spec_gate_check:
  rules:
    min_use_cases: 1                           # US最低1件
    min_total_acceptance_criteria: 3           # AC合計最低3件
    min_integration_acceptance_criteria: 1     # integrationタグ付きAC最低1件
    max_blocking_questions: 0                  # blocking質問は0
    min_nfr_items: 6                          # NFR合計最低6件
    min_security_items: 1                      # security最低1件
    min_integration_items: 1                   # integration最低1件
    min_data_items: 1                          # data最低1件
    min_spec_as_code_artifacts: 1              # Spec-as-Code最低1件

  # 必須フラグ
  no_blocking_open_questions: true
  spec_as_code_defined: true
  ai_plan_ready: true
```

---

## 9. よくある間違いと対処法

### 間違い1: HOWを書いてしまう

```yaml
# ❌ 間違い（HOWを書いている）
statement: "React.jsでテーブルコンポーネントを使用して発注一覧を表示する"

# ✅ 正しい（WHATだけ）
statement: "発注一覧が日付降順でテーブル表示される"
```

### 間違い2: 曖昧なAC

```yaml
# ❌ 間違い
statement: "発注が正しく登録される"

# ✅ 正しい
statement: "取引先ID「P-1001」で発注CSV(10行)を送信すると、60秒以内に受注番号が表示される"
```

### 間違い3: integrationタグの付け忘れ

```yaml
# ❌ 間違い（外部連携なのにタグなし）
- id: "AC-..."
  statement: "ERPへ受注登録して結果を返却する"
  tags: []  # ← integrationタグがない

# ✅ 正しい
- id: "AC-..."
  statement: "ERPへ受注登録して結果を返却する"
  tags: ["integration"]  # ← 外部連携なのでintegrationタグ
```

### 間違い4: NFRの記載漏れ

```yaml
# ❌ 間違い（カテゴリが空）
requirements:
  integration: []      # ← 空
  data_governance: [] # ← 空

# ✅ 正しい（各カテゴリ最低1件）
requirements:
  integration:
    - "ERP受注登録APIは3回リトライする"
  data_governance:
    - "受注データのSoRはERPとする"
```

---

## 10. 実践例

### 完成したspec.md の例（抜粋）

```yaml
spec:
  overview:
    who: "取引先の購買担当者が、Web-EDIポータルから発注する"
    what: "発注データを送信し、受注番号と納期回答を受け取る"
    why: "手入力と確認作業を減らし、受注処理を迅速化する"

  use_cases:
    - id: "US-FEAT001-001"
      title: "Web-EDI発注送信"
      primary_actor: "取引先購買担当者"
      trigger: "Web-EDIで発注を送信"
      preconditions:
        - "取引先が有効な取引先コードでログイン済み"
      main_flow:
        - "発注データを入力またはCSVアップロードする"
        - "システムがバリデーションを行う"
        - "システムがERPに受注を登録する"
        - "受注番号と納期回答が表示される"
      acceptance:
        - id: "AC-US-FEAT001-001-01"
          statement: "発注CSV(10行)を送信すると、60秒以内に受注番号が表示される"
          tags: ["integration", "performance"]
          priority: "must"

        - id: "AC-US-FEAT001-001-02"
          statement: "在庫不足の場合、納期回答日が表示される"
          tags: ["integration", "e2e"]
          priority: "must"

  requirements:
    integration:
      - "Correlation IDを全ログに出力"
      - "ERP接続タイムアウト30秒"
    data_governance:
      - "受注データのSoRはERPとする"
    security_privacy:
      - "取引先コード単位でアクセス制御"
    performance:
      - "P95 < 60秒"
    availability_reliability:
      - "可用性99.5%"
    operations:
      - "エラー時Slack通知"

  spec_as_code:
    artifacts:
      - type: "openapi"
        path: "sdd-templates/specs/sample_feature/contracts/openapi.yaml"
```

---

## チェックリスト

- [ ] IDをすべて置換した
- [ ] overview の who/what/why を書いた
- [ ] use_cases を最低1件定義した
- [ ] acceptance を合計3件以上定義した
- [ ] integrationタグ付きACを最低1件含めた
- [ ] e2eタグは重要フローのみに限定した
- [ ] NFRを6カテゴリ各1件以上定義した
- [ ] spec_as_code.artifacts を定義した
- [ ] counts を更新した
- [ ] blocking質問を全て解決した

---

## 次のステップ

→ [05. 実装計画ガイド](12_plan_guide.md)

---

> SDD Templates Manual - 04. Spec Guide
