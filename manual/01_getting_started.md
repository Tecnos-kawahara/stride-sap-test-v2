# 01. はじめに - SDDの基本を理解する

**所要時間**: 約15分

---

## PM向け3分サマリー

**SDDとは**: 「先に仕様とテストを決めてから、実装する」手法です。  
**メリット**: 手戻りが減り、品質が「証拠（Evidence）」として残ります。

1. **基本設計 (Basic Design)**: Why/Whatを決める
2. **仕様 (Spec)**: Acceptance Criteria（受入条件）を決める
3. **計画 (Plan)**: テスト計画と契約 (Contract) を決める
4. **実装 (Tasks)**: タスクを消化し、証拠を集める (Evidence Pack)

→ PMは「各工程のGate」で承認を行うだけで、品質が担保される仕組みです。

---

## このガイドで学ぶこと

1. SDDとは何か
2. なぜSDDが必要なのか
3. なぜこの構造なのか（WHY/WHAT/HOW/DOの分離）
4. 各パートの役割と関係
5. ワークフローの全体像
6. 最初の一歩

---

## 初心者が最初に押さえる3点

1. **仕様が正本**: 迷ったら「spec.md」に合わせる（コードはあとで合わせる）
2. **ACが合否基準**: 受入条件は「テストできる文章」で書く
3. **Gateで進む**: 各パートのゲートが通ってから次へ進む

---

## 1. SDDとは何か

### 定義

**SDD（Specification-Driven Development）** = **仕様駆動開発**

「仕様」を開発の中心に据え、コードはその仕様から派生するものとして扱う開発手法です。

### 従来開発との比較

| 観点 | 従来の開発 | SDD |
|------|-----------|-----|
| 主役 | コード | 仕様（Spec） |
| ドキュメント | 後から書く | 先に書く |
| 正本 | コード | 仕様 |
| 品質保証 | 人の目視 | 機械検証（Gate） |
| 変更時 | コード修正→ドキュメント修正 | 仕様修正→コード修正 |

### SDDの公式

```
仕様（Spec） ＞ コード

仕様とコードに矛盾があれば、仕様が正しい
```

---

## 2. なぜSDDが必要なのか

### 問題1: ドキュメントの形骸化

**従来の問題**
- ドキュメントは書いたが、実装と乖離している
- 誰もドキュメントを信用しない
- メンテナンスされない

**SDDの解決策**
- 仕様が正本なので、仕様を見れば正確な情報がわかる
- stride-lintで仕様とテストの整合性を機械検証
- 形骸化を自動検出

### 問題2: 認識のずれ

**従来の問題**
- 要件の解釈が人によって違う
- 実装してから「違う」と言われる
- 手戻りが多い

**SDDの解決策**
- basic_design で認識を合わせてから進む
- 受入条件（AC）を明確に定義
- ゲートで品質をチェックしてから次へ

### 問題3: AIの暴走

**従来の問題**
- AIが勝手にコードを生成
- 意図しない変更が入る
- 品質が保証されない

**SDDの解決策（v4.4 AI自律実行モデル）**
- AIは全作業の実行者(R)だが、「Accountable（承認者）」には絶対になれない
- APPROVAL.md は人間のみが編集できる安全装置
- Gate で必ず停止し、人間の承認なしに次 Phase に進めない
- AIの生成物は証跡（Provenance）を残す

---

## 3. なぜこの構造なのか（WHY/WHAT/HOW/DOを分ける理由）

SDDの構造は「意思決定の階層」を分けるためにあります。目的や合意は上流で固定し、実装の細部は後で決める。こうすることで、手戻りが起きやすい判断を先に片付け、品質と説明責任を通しやすくします。

### 3.1 この構造が解決すること

- **合意の前倒し**: 目的・範囲を最初に固めるので、後で仕様がぶれにくい
- **品質の自動化**: 各パートにゲートがあるため、抜け漏れを機械検証できる
- **説明責任**: 「何を決めたか」「なぜそうしたか」が段階ごとに残る

### 3.2 各パートが答える問い（役割の整理）

| パート | 答える問い | 役割（ひと言） |
|---|---|---|
| basic_design.md | なぜ/誰が/何を | 目的の合意書 |
| process.bpmn | どの順で業務が進むか | Feature 業務フローの共通言語 |
| epic_flow.bpmn | どのチーム/システムが受け渡すか | Epic 連携概観の共通言語 |
| spec.md | 何ができれば合格か | 仕様の契約書（ACが主役） |
| plan.md | どう実現し、どう検証するか | 実装と品質の設計図 |
| tasks.md | 誰が何をいつするか | 実行の作業指示書 |
| evidence_pack.md | それが守られたか | 監査・品質の証拠箱 |

### 3.3 パート同士の関係（入力 → 出力）

```
basic_design → process.bpmn / spec
process.bpmn → spec / plan
spec → plan
plan → tasks
tasks → 実装/テスト → evidence_pack
```

**ポイント**: 上流は下流の前提、下流は上流の証明です。

> Enterprise / Multi-Team では、この Feature 系の流れとは別に `epic_design.md → epic_flow.bpmn → feature_breakdown.md` を管理します。

### 3.4 トレーサビリティ（関係をつなぐ糸）

```
RQ → US → AC → CT/TS → Tasks → Evidence
```

- **RQ/US/AC** は「何を満たすか」の根拠
- **CT/TS** は「どう検証するか」の設計
- **Tasks** は「誰が実行するか」の作業化
- **Evidence** は「本当に満たしたか」の証跡

### 3.5 変更が起きた時の波及先

| 変更したパート | 更新が必要なパート | 理由 |
|---|---|---|
| basic_design | process / spec / plan | 目的や範囲が変わると全体がずれる |
| epic_flow.bpmn | feature_breakdown / basic_design / process | チーム間・システム間の受け渡し前提が変わる |
| process.bpmn | spec / plan / tasks | 業務フロー参照が変わる |
| spec（AC） | plan / tasks | ACはテストとタスクの起点 |
| plan（CT/TS） | tasks / evidence_pack | テストと成果物が変わる |
| tasks | evidence_pack | 実行証跡の内容が変わる |

---

## 4. SDDの基本概念

### 4.1 成果物の階層

```
basic_design.md   ← 認識合わせ（WHAT/WHY）
      ↓
process.bpmn      ← 業務フロー（視覚化）
      ↓
spec.md           ← 仕様（WHAT/WHY詳細）
      ↓
plan.md           ← 計画（HOW）
      ↓
tasks.md          ← タスク（DO）
      ↓
実装/テスト        ← 実行（派生物）
      ↓
evidence_pack.md  ← 証跡（Gate判定の根拠）
```

> Enterprise / Multi-Team では、これに加えて `epic_design.md → epic_flow.bpmn → feature_breakdown.md` の上位レイヤを持ちます。

### 4.2 各成果物の役割

| 成果物 | 役割 | 書く内容 | 書かない内容 |
|--------|------|----------|-------------|
| basic_design.md | 認識合わせ | 誰が、何を、なぜ | 実装方法 |
| process.bpmn | Feature 業務フロー | 作業の流れ | コード |
| epic_flow.bpmn | Epic 連携概観 | チーム間・システム間の受け渡し | 実装詳細 |
| spec.md | 仕様 | ユースケース、受入条件 | 技術選定 |
| plan.md | 計画 | 契約、テスト戦略 | 実装コード |
| tasks.md | タスク | 作業単位、依存関係 | ビジネスロジック |
| evidence_pack.md | 証跡 | CI/テスト/監査/AI出自の結果 | 仕様や設計の判断 |

### 4.2.1 よくある誤解（初心者向け）

| 誤解 | 正しい理解 |
|------|-----------|
| spec = 詳細設計 | specは「合否の基準」。実装方法はplanへ |
| plan = スケジュール | planは「実行と検証の設計図」。日程は別管理でもOK |
| tasks = チケット一覧 | tasksは「テストや契約を確実に実行するための作業分解」 |

### 4.3 ゲートシステム

各成果物には「ゲート」があり、クリアしないと次に進めません。

```
┌────────────────────┐
│   Basic Design     │
│       Gate         │◀── traceability、integration flows が定義されているか？
└─────────┬──────────┘
          ↓
┌────────────────────┐
│   BPMN Approval    │
│       Gate         │◀── 人間がBPMNを承認したか？
└─────────┬──────────┘
          ↓
┌────────────────────┐
│     Spec Gate      │◀── ユースケース、ACが定義されているか？
└─────────┬──────────┘
          ↓
┌────────────────────┐
│     Plan Gate      │◀── 契約、テストが定義されているか？
└─────────┬──────────┘
          ↓
┌────────────────────┐
│    Tasks Gate      │◀── 全テストがタスク化されているか？
└────────────────────┘
```

### 4.4 AI自律実行とHITL（v4.4）

**AIと人間の役割分担（v4.4 更新）**

| 役割 | AI | 人間 |
|------|-----|------|
| **全作業の実行 (R)** | ○ | — |
| init / 設計 / 仕様 / 実装 / テスト | ○（自律実行） | — |
| lint エラーの自動修正 | ○（自律実行） | — |
| **承認（Approve / A）** | × | ○ |
| **APPROVAL.md 編集** | × | ○ |
| **業務判断** | × | ○ |

**重要**: AIはAccountable（最終責任者）になれません。v4.4 で AI が全作業の実行者 (R) になっても、承認 (A) は人間のみです。詳細: [AI自律実行ガイド (v4.4)](15_ai_autonomous_execution_guide.md)

### 4.5 RACI+

SDDでは、従来のRACIに「AI」と「CI」の列を追加した**RACI+**を使います。

| 略語 | 意味 | 説明 |
|------|------|------|
| R | Responsible | 実行者 |
| A | Accountable | 承認者（人間のみ） |
| C | Consulted | 相談先 |
| I | Informed | 報告先 |
| AI | AI役割 | **全作業の実行者 (R)**（v4.4）。承認 (A) は不可 |
| CI | CI役割 | Verify/Check/Enforce |

---

## 5. ワークフローの全体像

### Phase 1: 認識合わせ

```
[人間の要望] → [basic_design.md作成] → [レビュー] → [Basic Design Gate]
```

**やること**:
1. 誰が（Who）使うのか
2. 何を（What）実現するのか
3. なぜ（Why）必要なのか
4. トレーサビリティ行を定義

### Phase 2: 業務フロー定義

```
[Basic Design Gate通過] → [process.bpmn作成] → [人間が承認] → [BPMN Approval Gate]
```

**やること**:
1. Camunda 8形式でBPMNを作成
2. 人間がフローをレビュー・承認
3. BPMNと要件の紐付けを確認

### Phase 3: 仕様定義

```
[BPMN承認] → [spec.md作成] → [Spec Gate]
```

**やること**:
1. ユースケース（US）を定義
2. 受入条件（AC）を定義（タグ付き）
3. 非機能要件（NFR）を定義
4. Spec-as-Codeを準備

### Phase 4: 計画策定

```
[Spec Gate通過] → [plan.md作成] → [Plan Gate]
```

**やること**:
1. 契約（CT）を定義
2. テスト戦略を定義
3. Coverage Policyを設定
4. Evidence Packを定義

### Phase 5: タスク分解

```
[Plan Gate通過] → [tasks.md作成] → [Tasks Gate]
```

**やること**:
1. 各テストをタスク化
2. 依存関係を定義
3. マイルストーンを設定

### Phase 6: 実装

```
[Tasks Gate通過] → [実装] → [テスト] → [Evidence Pack収集]
```

---

## 6. 最初の一歩

### 開発アプローチの選択

| アプローチ | 所要時間 | 推奨ケース |
|-----------|---------|-----------|
| **Claude Code に全自動で任せる**（最推奨、v4.4） | 5分 + Gate 承認のみ | AI自律実行。人間は承認だけ |
| Intake → AI生成 | 10-15分 + AI生成 | 多少のターミナル操作ができる場合 |
| Full Template | 30-60分 | 従来開発、詳細を自分で埋めたい場合 |

---

## 🤖 最推奨: Claude Code に全て任せる（v4.4 AI自律実行）

> **v4.4 更新**: Claude Code が全作業の「実行者 (R)」として自律的に全フェーズを駆動します。
> 人間は「承認者 (A)」として APPROVAL.md の編集と業務判断のみ行います。
> 詳細: [AI自律実行ガイド (v4.4)](15_ai_autonomous_execution_guide.md)

**ターミナルコマンドを一切打たずに**、Claude Code との対話だけでSDD開発を始められます。

### 準備: テンプレートをプロジェクトに配置

```bash
# 方法1: Git でクローン
git clone https://github.com/Tecnos-Japan-NGB/tecnos-sdd-templates.git my_project
cd my_project

# 方法2: 既存プロジェクトにコピー
cp -r /path/to/tecnos-sdd-templates/sdd-templates ./
cp -r /path/to/tecnos-sdd-templates/agent_docs ./
cp -r /path/to/tecnos-sdd-templates/memory ./
cp /path/to/tecnos-sdd-templates/CLAUDE.md ./
```

### Step 1: Claude Code を起動して理解させる

プロジェクトフォルダで Claude Code を起動し、以下のように伝えます:

```
これはSDD（Specification-Driven Development）開発のテンプレートです。
これから要件を伝えてSDD開発を開始してもらいますので、
まずはこのテンプレートをultrathinkで読み込んで完全に理解してください。

特に以下のファイルを読み込んでください：
- CLAUDE.md（運用ルール）
- agent_docs/sdd_guidelines.md（SDDガイドライン）
- agent_docs/commands.md（コマンドSSoT）
- sdd-templates/templates/basic_design_template.md（基本設計テンプレート）
```

Claude Code が読み込み完了を報告したら、開発を開始できます。

### Step 2: 要件を伝える

自然言語で要件を伝えるだけで、Claude Code がSDD開発を進めます:

```
以下の機能を開発したいです:

【機能名】Web-EDI受注受付
【誰が使う】取引先の購買担当者（約80社）
【何をする】Web-EDIで発注データを受け付け、ERPに自動登録し、受注番号と納期回答を返す
【なぜ必要】現状はメール/Excelで受注を手入力しており、1件20分・誤入力1%が発生している
【関連システム】SAP S/4HANA, Web-EDIポータル

SDD開発を開始してください。
```

### Step 3: Claude Code が自律実行すること（v4.4）

Claude Code は以下を**指示なしで連続実行**します:

1. `stride init <feature> --detect` でディレクトリ構造を自動作成
2. 要件をもとに **basic_design.md** を作成
3. **process.bpmn** を作成（単一Featureの laneSet ベース業務フローを可視化）
4. **stride lint** で検証 → エラーがあれば**自動修正**
5. lint PASS → Gate で停止して人間に承認を依頼
6. 承認後、次のフェーズ（spec → plan → tasks → 実装）へ**自動的に**進行
7. 最終的に evidence_pack, PR readiness check まで自律実行

### Step 4: 対話で進める

Claude Code は各ゲートで確認を求めてきます:

```
[Claude Code] Basic Design Gate の検証が完了しました。
以下の点を確認してください:

✓ Who/What/Why が明確
✓ トレーサビリティが1行以上定義
✓ integration flows が定義
⚠ blocking質問が1件あります:
  "Q-001: 納期回答は即時か、承認後か？"

この質問に回答いただけますか？
```

回答すると、Claude Code が続きを進めます。

### Step 5: 承認を行う

Claude Code は **APPROVAL.md を編集できません**（ルールで禁止）。
ゲート承認が必要な時、Claude Code は以下のように報告します:

```
[Claude Code] Gate 1 の検証が完了しました。
人間による承認が必要です。

以下の手順で承認してください:
1. specs/my_feature/APPROVAL.md を開く
2. Gate 1 のチェックボックスを [x] に変更
3. 承認者名と日付を記入
4. 「承認しました」と伝えてください
```

### よく使うプロンプト集

| シーン | プロンプト例 |
|--------|-------------|
| 開発開始 | 「この要件でSDD開発を開始してください」 |
| 状況確認 | 「現在のゲート状況を教えてください」 |
| lint実行 | 「stride lint を実行してエラーを確認してください」 |
| 修正依頼 | 「basic_design.md の context.who を修正してください」 |
| 次フェーズ | 「次のフェーズに進んでください」 |
| BPMN作成 | 「process.bpmn を作成してください」 |
| テスト作成 | 「AC-001 のテストを作成してください」 |

### Claude Code が従うルール（v4.4 AI自律実行）

Claude Code は CLAUDE.md / SDD_MANIFESTO.md に記載された以下のルールを遵守します:

| ルール | 内容 |
|--------|------|
| **AI = 実行者 (R)** | init〜実装〜テスト〜Evidence まで全作業を自律実行 |
| **APPROVAL.md 編集禁止** | 承認ファイルはAIが編集不可（人間のみ） |
| **Phase Gate 遵守** | 前のゲートが通るまで次のファイルを作成しない |
| **lint 自動実行・自動修正** | 成果物作成後に自動実行。APPROVAL_PENDING 以外は自動修正 |
| **Gate でのみ停止** | Phase 内は連続実行。APPROVAL_PENDING で停止して承認を依頼 |
| **YAML が正本** | basic_design.md は YAML セクションが正本 |

### トラブルシューティング

| 問題 | 解決策 |
|------|--------|
| Claude Code がルールを理解していない | 「CLAUDE.md を読み直してください」と伝える |
| lint エラーが解消しない | 「stride lint のエラーを詳しく分析してください」 |
| 次のフェーズに進めない | 「Phase Gate 状況を確認してください」 |
| 間違った修正をした | 「git diff で変更を確認し、問題があれば戻してください」 |

---

### 代替: Intake-First アプローチ（対話式、v4.4）

**Claude Code との対話で要件を聞き取り → intake を自動記入 → basic_design.md を生成** という流れで始めます。
最推奨アプローチとの違いは、intake テンプレートを中間成果物として残す点です。

#### Step 1: Claude Code に Intake 対話を依頼

```
Intake-First で SDD 開発を始めてください。
機能名は「my_first_feature」です。
質問形式で要件を聞き取ってください。
```

Claude Code は以下を自動で行います:
1. `stride intake my_first_feature` を実行してディレクトリと intake テンプレートを作成
2. テンプレートの各セクション（Who/What/Why、Scope、関連システム等）について**1つずつ質問**
3. 回答をもとに `basic_design_intake.md` を**自動記入**

#### Step 2: 対話に回答する（5-10分）

Claude Code が順番に質問してきます:

```
[Claude Code] Intake を開始します。まず基本情報から伺います。

1. この機能は誰が使いますか？（Who）
2. 何を実現しますか？（What）
3. なぜ必要ですか？（Why）
```

自然言語で回答するだけです:

```
1. 取引先の購買担当者（約80社）
2. Web-EDIで発注データを受け付け、ERPに自動登録する
3. 現状はメール/Excelで手入力しており、1件20分かかっている
```

Claude Code はスコープ、関連システム、業務フロー、未解決の質問も順に聞き取ります。

#### Step 3: AI が自動で残りを実行

対話完了後、Claude Code は以下を**指示なしで連続実行**します:
1. `basic_design_intake.md` に回答を記入
2. intake をもとに完全な `basic_design.md` を生成
3. `stride lint` を実行 → エラーがあれば自動修正
4. Gate で停止して承認を依頼

以降の流れは最推奨アプローチと同じです。

---

### 従来アプローチ: Full Template

詳細を自分で埋めたい場合:

```bash
# 全テンプレートを一括作成
stride init my_first_feature

# Lite Mode（小規模プロジェクト/PoC向け）
stride init --lite my_first_feature
```

### Step 5: 次のガイドへ

[基本設計ガイド](09_basic_design_guide.md) に進んで、basic_design.md の詳しい書き方を学びましょう。

---

## 7. テスト環境のセットアップ（v1.2.4）

テスト実行に必要な設定とツールのセットアップ方法です。

### テストディレクトリ構造

```
specs/<feature>/tests/
├── unit/              # 単体テスト
├── integration/       # 統合テスト
├── contract/          # 契約テスト
├── e2e/               # E2Eテスト
└── conftest.py        # 共有フィクスチャ（Python）
```

> **重要**: テストは `specs/<feature>/tests/` に配置（ルートの `tests/` は使わない）

### Python テストセットアップ

```bash
# 1. conftest.py テンプレートをコピー
cp sdd-templates/config/testing/python/conftest.py.template \
   specs/my_feature/tests/conftest.py

# 2. pyproject.toml に設定を追加（pytest-asyncio 競合回避）
# sdd-templates/config/testing/pyproject.toml.snippet を参照
```

**pyproject.toml 必須設定**:

```toml
[tool.pytest.ini_options]
testpaths = ["specs/my_feature/tests"]
addopts = ["-v", "--strict-markers", "-p", "no:asyncio"]  # -p no:asyncio が重要
```

### AI テストツール自動インストール

AIエージェントは、テスト実行前に依存関係を確認し、不足していれば自動インストールします:

```bash
# Python
python -c "import pytest" 2>/dev/null || pip install pytest pytest-cov httpx

# TypeScript
npm list vitest 2>/dev/null || npm install -D vitest @vitest/coverage-v8
```

詳細: `sdd-templates/agent_docs/testing.md` の「AI Agent Pre-Flight Checklist」

### 関連ドキュメント

- [言語別テストツールガイド](20_language_test_tools.md) - Python/TS/Rust/Go/Java のベストプラクティス
- [テスト実行ガイド](../sdd-templates/agent_docs/testing.md) - 5言語対応
- [テストパターン集](../sdd-templates/docs/TEST_PATTERNS.md) - 7カテゴリの検証済みパターン

---

## 用語集

| 用語 | 読み方 | 意味 |
|------|--------|------|
| SDD | エスディーディー | Specification-Driven Development（仕様駆動開発） |
| Spec | スペック | 仕様書 |
| Plan | プラン | 実装計画 |
| Tasks | タスクス | タスク分解 |
| Gate | ゲート | 品質チェックポイント |
| HITL | ヒットル | Human-in-the-Loop（人間参加型） |
| AC | エーシー | Acceptance Criteria（受入条件） |
| US | ユーエス | Use Case（ユースケース） |
| RQ | アールキュー | Requirement（要求） |
| CT | シーティー | Contract（契約）※下記参照 |
| TS | ティーエス | Test Specification（テスト仕様） |
| BPMN | ビーピーエムエヌ | Business Process Model and Notation |
| NFR | エヌエフアール | Non-Functional Requirements（非機能要件） |
| Evidence Pack | エビデンスパック | ゲート判定の証跡集 |

> **💡 「契約（CT）」について**
>
> SDDの「契約」は法的な契約書ではなく、**システム間の通信ルールを文書化したもの**です。
> 例：「POST /orders を呼ぶと受注番号がJSONで返る」というAPIの仕様。
> 詳しくは [index.md の「契約とは何か」](index.md#-契約contractとは何か) を参照。

---

## チェックリスト

- [ ] SDDとは何か理解した
- [ ] 従来開発との違いを理解した
- [ ] なぜ構造を分けるのか理解した
- [ ] 各パートの役割と関係を理解した
- [ ] トレーサビリティの流れを理解した
- [ ] 成果物の階層を理解した
- [ ] ゲートシステムを理解した
- [ ] HITLの概念を理解した
- [ ] ワークフローの全体像を把握した

---

## 次のステップ

→ [02. 基本設計ガイド](09_basic_design_guide.md)

---

> SDD Templates Manual - 01. Getting Started
