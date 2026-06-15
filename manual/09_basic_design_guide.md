# 09. 基本設計ガイド - basic_design.md の書き方

**所要時間**: 従来 約30分 → **Intake-First なら 10-15分 + AI生成**

---

## 推奨: Intake-First アプローチ（対話式、v4.4）

**Claude Code との対話で要件を聞き取り、intake を自動記入し、完全な basic_design.md を生成します。**

```
# Claude Code に以下のように依頼するだけ:

Intake-First で SDD 開発を始めてください。
機能名は「my_feature」です。
質問形式で要件を聞き取ってください。
```

Claude Code が自動で行うこと:
1. `stride intake my_feature` を実行（ディレクトリ + intake テンプレート作成）
2. Who/What/Why、Scope、関連システム、業務フロー、未解決の質問を**1つずつ対話で聞き取り**
3. 回答をもとに `basic_design_intake.md` を**自動記入**
4. intake から完全な `basic_design.md` を生成
5. `stride lint` を実行 → エラーがあれば自動修正
6. Gate で停止して承認を依頼

> **Note**: 手動で intake を記入することも可能です（`stride intake my_feature` 後に直接編集）。

**従来アプローチ**（全テンプレートを手動で埋める）を使う場合は、以下のガイドに従ってください。

---

## 修正ワークフロー（既存 basic_design.md の変更）

**basic_design.md** はYAMLが正本です。修正時は以下のワークフローに従ってください。

### ドキュメント構造

| セクション | 種別 | 編集方法 |
|-----------|------|----------|
| `#0 YAML` | **正本（SSoT）** | 直接編集 |
| `#1 Document Intent` | 読み方ガイド | 固定（編集不要） |
| `#2 Traceability` | AI生成ビュー | YAML変更後にAIが再生成 |
| `#3 Part A` | AI生成ビュー | YAML変更後にAIが再生成 |
| `#4 Part B` | AI生成ビュー | YAML変更後にAIが再生成 |
| `#5 Part C` | AI生成ビュー | YAML変更後にAIが再生成 |
| `#6 Decision Log` | AI生成ビュー | YAML変更後にAIが再生成 |
| `#7 Checks` | **ゲート状態** | 手動管理（AIは再生成しない） |

### 修正手順

```bash
# Step 1: #0 YAML セクションを直接編集
# 例: context.who を変更する場合、YAMLのcontext.whoを編集

# Step 2: AIに再生成を依頼
# Claude Code に依頼: 「YAMLを更新したので、ビューを再生成して」
# ⚠️ #7 Checks はゲート状態のため再生成対象外

# Step 3: stride-lint で検証
stride lint specs/my_feature/ --warn-only
```

### なぜこのワークフローか？

**Single Source of Truth (SSoT)** の原則:
- **YAML = 正本**: 機械可読、バリデーション可能
- **Part A/B/C = ビュー**: 人間が読みやすい形式
- **二重管理を回避**: YAMLだけを編集すれば、ビューはAIが同期

**メリット**:
- YAMLのバリデーションで不整合を検出
- 修正漏れがない（YAMLから自動生成）
- レビュー効率向上（YAMLのdiff確認）

---

## このガイドで学ぶこと

1. basic_design.md の目的
2. 構成要素の詳細
3. 書き方のステップ
4. よくある間違いと対処法
5. ゲート通過条件

---

**サンプル参照**: `sdd-templates/specs/sample_feature` に Web-EDI の参考サンプルがあります（未承認/プレースホルダあり）。
**注**: パスは例なので、自分の機能では `specs/<feature>` に置き換えます。

## 1. basic_design.md の目的

### なぜ必要か？

**basic_design.md** は、人間とAIの「認識齟齬を潰すハブ」です。

```
[人間の曖昧な要望]
        ↓
[basic_design.md] ← ここで認識を合わせる
        ↓
[明確な仕様へ]
```

### 何を書くか？

| 書くこと | 書かないこと |
|----------|-------------|
| 誰が使うか（Who） | 実装方法 |
| 何を実現するか（What） | 技術選定 |
| なぜ必要か（Why） | コード |
| どのシステムと連携するか | 詳細設計 |
| 重要な業務フロー | |
| 未解決の質問・前提条件 | |

### 初心者向けの最短ルート（まずはここから）

1. **context（who/what/why）** を具体的に埋める  
2. **scope（in/out）** で期待値を固定する  
3. **systems** で連携相手を列挙する  
4. **traceability_rows** にRQ→US→ACを最低1行入れる  
5. **bpmn_descriptions** に process と主要業務ブロックの説明を入れる  
6. **open_questions** で不明点を洗い出す（blockingは必ず解決）

### このパートの引き渡し（次の成果物との関係）

basic_design は「合意の箱」です。ここで決めた内容が、以降の成果物の前提になります。

```
basic_design
  -> process.bpmn : 業務フローの前提（誰が/何を/どの範囲で）
  -> spec.md      : US/ACの起点（何ができれば合格か）
  -> plan.md      : 統合/監査/運用の前提（どの制約があるか）
  -> tasks.md     : traceabilityの起点（要件からタスクへの根拠）
```

**最低限引き渡すべき項目**:
- context（who/what/why）
- scope（in/out）
- systems（連携システム）
- traceability_rows（RQ/US/ACの起点）
- bpmn_descriptions（BPMN業務記述の正本）
- open_questions / assumptions（未確定事項）

---

## 2. 構成要素の詳細

### 2.1 Front Matter（必須）

```yaml
---
artifact: "basic_design"
template_id: "TPL-BD-TECNOS-001"
feature_id: "FEAT-001"              # ← 機能ID（置換必須）
basic_design_id: "BD-001"           # ← 設計書ID（置換必須）
title: "Basic Design - Web-EDI受注受付"
version: "{{TEMPLATE_VERSION}}"      # stride initで自動設定
status: "draft"                      # draft → in_review → approved
owners:
  - { name: "山田太郎", role: "Product Owner / Business" }
  - { name: "鈴木一郎", role: "Tech Lead / Architect" }
  - { name: "佐藤花子", role: "PMO (TEIM)" }
created_at: "2025-01-15"
updated_at: "2025-01-15"
---
```

**ポイント**:
- `feature_id` と `basic_design_id` は必ず実際のIDに置換する
- `status` はレビュー状況に応じて更新する
- `owners` には実際の担当者を記載する

### 2.2 context（最重要）

```yaml
basic_design:
  context:
    who: "取引先の購買担当者（約80社）が、Web-EDIポータルから発注を送信し、社内受注担当者が内容を確認するために使用する"
    what: "Web-EDIで発注データを受け付け、ERPに自動登録し、受注番号と納期回答を返す"
    why: "現状はメール/Excelで受注を手入力しており、1件20分・誤入力1%が発生。受付〜確認を5分以内に短縮し、誤入力を0.1%以下にしたい"
```

**書き方のコツ**:

| 項目 | 悪い例 | 良い例 |
|------|--------|--------|
| who | ユーザー | 取引先の購買担当者（約80社）が、Web-EDIポータルから |
| what | データ統合 | Web-EDI発注をERPに自動登録し、受注番号と納期回答を返す |
| why | 効率化のため | 受注入力に20分→5分に短縮したい |

### 2.3 scope（スコープ）

```yaml
  scope:
    in:
      - "Web-EDI発注入力/CSVアップロード"
      - "発注内容のバリデーション"
      - "ERPへの受注登録"
      - "受注番号・納期回答の通知"
    out:
      - "請求書発行"
      - "支払処理"
      - "EDI標準(JCA/EDI)との相互接続"
      - "モバイルアプリ対応"
```

**ポイント**:
- `in`: 今回対応する範囲を明確に
- `out`: 対応しない範囲も明示（期待値コントロール）

### 2.4 systems（連携システム）

```yaml
  systems:
    - system: "SAP S/4HANA"
      category: "ERP"
      owner: "経理部"
      integration_modes: ["API(OData V4)", "IDoc"]
    - system: "Web-EDI Portal"
      category: "B2B Portal"
      owner: "営業企画部"
      integration_modes: ["API(REST)"]
```

### 2.5 delivery_model（配布モデル）

```yaml
  delivery_model:
    type: "requirements-driven"   # requirements-driven | ftos | hybrid
    rationale: "取引先ごとの運用差異があるため、要件重視型を採用"
    ftos_exit_criteria:
      enabled: false
      criteria: []
```

**選択肢**:
- `requirements-driven`: 要件重視型（カスタム多い場合）
- `ftos`: Fit to Standard（標準適合型）
- `hybrid`: 混合型

**迷ったら**: まずは `requirements-driven` を選び、FtoSに寄せる場合は理由を明記します。

### 2.6 raci_plus（責任分担）

```yaml
  raci_plus:
    actors:
      - "TJ_Human_PM"           # Tecnos PM
      - "TJ_Human_TechLead"     # Tecnos Tech Lead
      - "TJ_AI_CodingAgent"     # AI Agent
      - "TJ_CI_Gate"            # CI/CD
      - "Customer_BizOwner"     # 顧客業務責任者
      - "Customer_ITOwner"      # 顧客IT責任者
    rules:
      - "AIはAccountableになれない（Aは人間のみ）"
      - "Merge/Release/GoNoGoはHuman A + CI passが前提"
      - "AI生成物はProvenanceを必須記録"
```

### 2.7 traceability_rows（トレーサビリティ）

**最も重要なセクション** - 要件からタスクまでの追跡を可能にします。

```yaml
  traceability_rows:
    - rq:
        id: "RQ-001"
        statement: "Web-EDIで発注後、5分以内に受注番号と納期回答を返却できること"
      us:
        id: "US-FEAT001-001"
        title: "Web-EDI発注送信"
      ac:
        id: "AC-US-FEAT001-001-01"
        statement: "取引先ID「P-1001」で発注CSV(10行)をアップロードすると、60秒以内に受注番号と納期が表示される"
        tags: ["integration", "performance"]
      bpmn:
        id: "BPMN-TASK-001"
        name: "受注登録"
      contract:
        id: "CT-API-01"
      test:
        id: "TS-INT-01"
        type: "integration"
      task:
        id: "T-G01-001"
```

**補足**: basic_design段階では `bpmn / contract / test / task` が未確定でも問題ありません。  
未確定の場合は空文字（`""`）にし、**BPMN承認やGateを通す前**に埋めるのがルールです。

**タグの意味**:

| タグ | 意味 | 必要なテスト |
|------|------|-------------|
| `integration` | 統合テストが必要 | TS-INT-* |
| `e2e` | E2Eテストが必要 | TS-E2E-* |
| `security` | セキュリティ観点 | - |
| `performance` | 性能観点 | - |
| `data` | データ観点 | - |

### 2.8 bpmn_descriptions（BPMN業務記述正本）

`traceability_rows` が **AC / Contract / Test / Task** の正本なのに対し、`bpmn_descriptions` は **BPMN 要素の業務記述** の正本です。

```yaml
  bpmn_descriptions:
    process:
      process_id: "BPMN-PROC-WEBEDI"
      purpose: "取引先の発注受付からERP登録完了までの業務フロー"
      start_condition: "発注データが送信される"
      end_condition: "受注番号と納期回答が返却される"
      business_outcome: "受注処理の迅速化と誤入力削減"
      primary_actors: ["取引先購買担当", "受注担当"]
    elements:
      - bpmn_id: "BPMN-TASK-001"
        name: "受注登録"
        type: "serviceTask"
        purpose: "受信した発注データをERPへ登録する"
        business_role: "受注受付の中核処理"
        trigger: "発注データのバリデーション完了"
        inputs: ["発注ヘッダ", "発注明細"]
        outputs: ["受注番号", "登録結果"]
        business_rules:
          - "取引先コードと品目コードが有効であること"
        exceptions:
          - "マスタ不備時は登録せずエラー返却"
```

**ポイント**:
- `process.process_id` は `process.bpmn` の実 `process id` と一致させる
- `elements[].bpmn_id` は BPMN 上の業務ブロック ID と一致させる
- `related_ac_ids` / `related_contract_ids` は `traceability_rows` が正本なので、ここでは重複保持しない
- FEAT では `process.bpmn` と同期する。EPIC 側の同等概念は `epic_design.md` の `epic_flow_descriptions`

### 2.9 integration_flows（統合フロー）

```yaml
  integration_flows:
    - id: "FLOW-001"
      name: "Web-EDI受注受付フロー"
      summary: "Web-EDIポータルで受注を受付し、ERPへ登録、受注番号/納期回答を返却"
      kpi_slo: "P95 < 60秒、可用性 99.5%"
      e2e_target: true
```

**ポイント**: integration_flows は「重要な連携の骨格」を書く場所で、  
process.bpmn は「業務の全体フロー」を書く場所です。細部はBPMNへ寄せます。

### 2.10 open_questions（未解決質問）

```yaml
  open_questions:
    - id: "Q-001"
      question: "取引先への納期回答は即時（自動）か、受注担当の承認後か？"
      blocking: true
      owner: "Customer_ITOwner"
      due: "2025-01-20"
```

**ポイント**:
- `blocking: true` の質問が残っていると、ゲートを通過できない
- 必ず `owner` と `due`（期限）を設定する

### 2.11 assumptions（前提条件）

```yaml
  assumptions:
    - id: "A-001"
      assumption: "取引先マスタがERPに登録済みである"
      rationale: "未登録の取引先は受注登録できないため"
      risk_if_false: "マスタ整備が先行タスクになり、開始が遅れる"
```

### 2.12 decisions（意思決定ログ）

```yaml
  decisions:
    - id: "DR-001"
      context: "発注データの受領方式"
      options:
        - "Webフォーム入力"
        - "CSVアップロード"
        - "EDI(JCA)連携"
      decision: "Webフォーム入力 + CSVアップロード"
      consequences: "CSV仕様の固定化と入力バリデーションが必要"
```

---

## 3. 書き方のステップ

### Step 1: IDを置換する

テンプレートをコピーしたら、まずIDを置換します。

```bash
# FEATXXX → 001 に置換
sed -i '' 's/FEATXXX/001/g' specs/my_feature/basic_design.md

# XXX_feature_name → my_feature に置換
sed -i '' 's/XXX_feature_name/my_feature/g' specs/my_feature/basic_design.md
```

### Step 2: context を埋める

最も重要なセクションから始めます。

```yaml
context:
  who: "【誰が】【どのような状況で】使うのか"
  what: "【何を】実現するのか（価値）"
  why: "【なぜ】今それが必要か（課題・背景）"
```

### Step 3: scope を明確にする

対応範囲と非対応範囲を明示します。

### Step 4: systems を列挙する

連携するシステムを洗い出します。

### Step 5: traceability_rows を追加する

要件を1行ずつ追加していきます。最低1行は必須です。

### Step 6: open_questions を洗い出す

不明点を全て書き出します。blocking な質問を解決するまでゲートは通過できません。

### Step 7: delivery_model と raci_plus を決める

配布モデルと責任分担を決定します。

### Step 8: counts を更新する

```yaml
derived_fields:
  counts:
    traceability_rows: 2   # ← 実際の行数に更新
    integration_flows: 1   # ← 実際のフロー数に更新
    blocking_questions: 0  # ← blocking質問を解決したら0に
```

---

## 4. よくある間違いと対処法

### 間違い1: プレースホルダが残っている

```yaml
# ❌ 間違い
feature_id: "FEAT-XXX"   # XXXが残っている

# ✅ 正しい
feature_id: "FEAT-001"   # 実際のIDに置換
```

**対処法**: `stride-lint` で `PLACEHOLDER_VALUE_PRESENT` エラーが出たら確認

### 間違い2: who/what/why が曖昧

```yaml
# ❌ 間違い
context:
  who: "ユーザー"
  what: "システム改善"
  why: "効率化"

# ✅ 正しい
context:
  who: "取引先の購買担当者が、Web-EDIポータルから発注する"
  what: "発注データをERPに自動登録し、受注番号と納期回答を返す"
  why: "手入力による時間と誤入力を削減し、受注処理を迅速化する"
```

### 間違い3: traceability_rows が空

```yaml
# ❌ 間違い
traceability_rows: []

# ✅ 正しい（最低1行）
traceability_rows:
  - rq: { id: "RQ-001", statement: "..." }
    us: { id: "US-FEAT001-001", title: "..." }
    ...
```

### 間違い4: blocking質問が未解決

```yaml
# ❌ ゲート通過不可
open_questions:
  - id: "Q-001"
    question: "..."
    blocking: true   # ← blocking質問が残っている
    owner: ""        # ← ownerも未設定

# ✅ ゲート通過可能
open_questions:
  - id: "Q-001"
    question: "..."
    blocking: false  # ← 解決済み or non-blocking
```

---

## 5. ゲート通過条件

### Basic Design Gate の条件

```yaml
basic_design_gate_check:
  # 必須条件
  traceability_present: true              # traceability_rows が1行以上
  integration_flows_identified: true      # integration_flows が1件以上
  exceptions_documented: true             # 例外は明示（空配列でもOK）
  delivery_model_defined: true            # delivery_model が設定済み
  raci_plus_defined: true                 # raci_plus が設定済み
  ai_policy_defined: true                 # AI Policy が設定済み
  artifact_registry_defined: true         # Artifact Registry が設定済み

  # 数値条件
  counts.traceability_rows >= 1
  counts.integration_flows >= 1
  counts.blocking_questions == 0          # blocking質問がゼロ

  # 最終フラグ
  ready_for_bpmn: true                    # BPMNに進む準備完了
```

### 確認方法

```bash
# stride-lint で検証
sdd-templates/tools/stride-lint specs/my_feature/ --warn-only
```

---

## 6. 実践例

### 例: Web-EDI受注受付機能

```yaml
basic_design:
  context:
    who: "取引先の購買担当者（約80社）が、Web-EDIポータルから発注を送信し、社内受注担当者が内容を確認するために使用"
    what: "Web-EDIで発注データを受け付け、ERPに自動登録し、受注番号と納期回答を返す"
    why: "現状はメール/Excelで受注を手入力しており、1件20分・誤入力1%が発生。受付〜確認を5分以内に短縮し、誤入力を0.1%以下にしたい"

  scope:
    in:
      - "Web-EDI発注入力/CSVアップロード"
      - "発注内容のバリデーション"
      - "ERPへの受注登録"
      - "受注番号・納期回答の通知"
    out:
      - "請求書発行"
      - "支払処理"
      - "EDI標準(JCA/EDI)との相互接続"
      - "モバイルアプリ対応（Phase 2で検討）"

  systems:
    - system: "SAP S/4HANA"
      category: "ERP"
      owner: "経理部"
      integration_modes: ["API(OData V4)"]
    - system: "Web-EDI Portal"
      category: "B2B Portal"
      owner: "営業企画部"
      integration_modes: ["API(REST)"]

  traceability_rows:
    - rq:
        id: "RQ-001"
        statement: "Web-EDIで発注後、5分以内に受注番号と納期回答を返却できること"
      us:
        id: "US-FEAT001-001"
        title: "Web-EDI発注送信"
      ac:
        id: "AC-US-FEAT001-001-01"
        statement: "取引先ID「P-1001」で発注CSV(10行)をアップロードすると、60秒以内に受注番号と納期が表示される"
        tags: ["integration", "performance"]
      bpmn:
        id: "BPMN-TASK-001"
        name: "受注登録"
      contract:
        id: "CT-API-01"
      test:
        id: "TS-INT-01"
        type: "integration"
      task:
        id: "T-G01-001"

  integration_flows:
    - id: "FLOW-001"
      name: "Web-EDI受注受付フロー"
      summary: "Web-EDIポータルで受注を受付し、ERPへ登録、受注番号/納期回答を返却"
      kpi_slo: "P95 < 60秒、可用性 99.5%"
      e2e_target: true

  open_questions: []  # 全て解決済み

  assumptions:
    - id: "A-001"
      assumption: "取引先マスタがERPに登録済み"
      rationale: "未登録の取引先は受注登録できない"
      risk_if_false: "マスタ整備が先行タスクになり、開始が遅れる"
```

---

## チェックリスト

- [ ] IDをすべて置換した（FEAT-XXX → FEAT-001 等）
- [ ] who/what/why を具体的に書いた
- [ ] scope の in/out を明確にした
- [ ] systems を列挙した
- [ ] traceability_rows を最低1行追加した
- [ ] integration_flows を最低1件追加した
- [ ] blocking質問を全て解決した（またはnon-blockingに変更）
- [ ] delivery_model を決定した
- [ ] raci_plus を設定した
- [ ] counts を更新した
- [ ] stride-lint が通った

---

## 次のステップ

→ [03. BPMNガイド](10_bpmn_guide.md)

---

> SDD Templates Manual - 02. Basic Design Guide
