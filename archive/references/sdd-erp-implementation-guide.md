# ERP導入におけるSDD（Spec-Driven Development）完全解説書
— specs.md（Simple / FIRE / AI‑DLC）を"ERP実装・PMO・監査"に落とす —

> 目的：ERP導入（標準設定＋周辺連携＋アドオン＋移行＋権限＋運用）を、
> **「仕様で制御し、実行を追跡し、品質を人が担保する」**AIネイティブな運用に再構成し、
> Tecnos Japanの **SI → CBP → AgentOps** への変換を加速する。

---

## Table of Contents

1. Executive Summary（要点・結論）
2. 基本概念：SDDとは何か（ERP文脈で）
   - 2.5 STRIDE: テクノス独自のSDD実践メソッド
3. 3つのフロー：Simple / FIRE / AI‑DLC（"別設計"として理解する）
4. ERP導入における最適解：外形Waterfall × 内側SDD（ハイブリッド）
5. フロー選定：PMOが迷わない判定ルール（決定木・スコア）
6. 各フロー運用マニュアル（完全版）
   - 6.1 Simple（Spec-Plan-Tasks）
   - 6.2 FIRE（Work Item / Run / Walkthrough / State）
   - 6.3 AI‑DLC（Intent / Unit / Story / Bolt / Operations）
7. ERPアドオンの"事故"を潰す（リスクと対策）
8. 成果物設計：Spec diff / 状態管理 / 監査パック
9. PMO実装：Gate（品質ゲート）・RACI・KPI
10. 90日導入ロードマップ（Tecnos向け）
11. テンプレ集（コピペ運用一式）
12. 参考リンク（specs.md）

---

## 1. Executive Summary（要点・結論）

### 1.1 specs.mdは「1フレームワーク3フロー」

specs.md は SDD を **3つの独立したフロー**として提供するフレームワークです。
**Simple（仕様生成中心）／FIRE（適応的実行・brownfield/monorepo強い）／AI‑DLC（AWS由来の正式メソドロジー＋DDD＋フル追跡）**。
重要なのは、これは段階的な"上位互換"ではなく **用途で選ぶ**ことです。

### 1.2 SDDのコアは一貫して「AIが提案し、人が検証する」

AIに分解・設計案・トレードオフ提示をさせ、**人間が明示的な承認ゲート（チェックポイント）**で品質を担保します。
速さと安全性（監査性）を同時に取りに行く思想です。

### 1.3 ERP導入で効く"実装ノウハウ"は3点に集約

1) **粒度設計**（Intent→Work Item/Run、または Intent→Unit→Story→Bolt）
2) **適切な実行モード／Boltタイプ**（速度⇄リスクの最適化）
3) **成果物＝状態**（statelessなエージェント前提。保存された成果物が唯一の真実）

### 1.4 Tecnos Japanの結論（SI→CBP→AgentOpsに直結）

ERP導入は「合意・監査・UAT・Cutover」が重いため、**外形はWaterfall（V字）を維持**しつつ、
内側（基本設計〜実装〜検証）を **SDDで置換**するのが2026最適解です。

- **Simple**：提案・要件定義・引き継ぎの高速化（spec生成→承認→引継ぎ）
- **FIRE（標準レーン）**：既存ERP/周辺のbrownfield改修を **短サイクルで安全に**回す中核（Work Item→Run→walkthrough→state）
- **AI‑DLC（重点レーン）**：複雑ドメイン（SCM/会計/調達・生産）や監査・規制案件で **DDD＋完全トレーサビリティ＋Operations**を担保

---

## 2. 基本概念：SDDとは何か（ERP文脈で）

### 2.1 "仕様＝会話ログ"ではなく"永続成果物（Artifacts）"

SDDは **意図（Intent）→ 構造化成果物 → 承認 → 実行 → ウォークスルー**を軸に、
AIの揺らぎ（幻覚・文脈落ち）を **成果物へ固定**して制御します。

> 重要：**「エージェントが覚える」のではなく「リポジトリが覚える」**。

- Simple：`specs/{feature}/requirements.md|design.md|tasks.md` が状態
- FIRE：`.specs-fire/state.yaml` と intent/work-item/run/walkthrough が状態
- AI‑DLC：`memory-bank/`（intent/unit/story/bolt/standards）が状態

### 2.2 ERPでSDDが効く理由（契約が強いから）

ERPアドオンは「画面項目1つ」で **入出力・電文・メッセージ・権限・DB・移行・テスト**が連鎖します。
ここで重要なのは「コードが書けたか」より **契約（Spec）と検証（テスト）を揃えたか**です。
SDDはこの"契約管理"を、差分と承認で回せる形に変換します。

---

## 2.5 STRIDE: テクノス独自のSDD実践メソッド

### STRIDEとは

**STRIDE = State-Tracked Run Intent-Driven Engineering**

specs.mdのFIREフローとAWSのAI-DLCを基盤に、テクノスジャパンがERP導入の実践知を反映させた独自メソッドです。
「AIと共に前進する（Stride）」というコンセプトを体現し、**品質を担保しながらも迅速に成果を出す**ことを目指します。

### 名称の構成

STRIDEは2つのコンセプトで構成されます：

1. **State-Tracked & Run**（状態追跡と実行）
   - FIREの`state.yaml`と`Run`を継承
   - 「エージェントが覚える」のではなく「成果物が状態を記録する」
   - 全ての変更が追跡可能な監査対応アーキテクチャ

2. **Intent-Driven Engineering**（意図駆動エンジニアリング）
   - AI-DLCの`Intent`を中核に据える
   - 「何を達成したいか」から始まる設計プロセス
   - 仕様→実装→テストの一貫したトレーサビリティ

### STRIDEがERP導入に効く理由

| 従来の課題 | STRIDEのアプローチ |
|------------|-------------------|
| 仕様と実装の乖離 | Intent→Spec→Runの一気通貫追跡 |
| 属人化・暗黙知 | State永続化による知識の外部化 |
| 手戻り・品質劣化 | 適切な粒度とチェックポイント |
| 監査対応の重荷 | 成果物＝証跡の自動蓄積 |

### FIREとAI-DLCの"いいとこ取り"

STRIDEは単なる折衷ではなく、**ERP導入の実務に最適化した統合**です：

- **FIREから継承**: 適応的実行モード（Autopilot/Confirm/Validate）、brownfield対応、軽量な状態管理
- **AI-DLCから継承**: Intent階層、DDD設計（複雑ドメイン用）、Operationsフェーズ
- **テクノス独自**: ERP固有のリスクフラグ、移送/移行を見据えたOpsパック、mcframe/SAP対応

> STRIDEは、Tecnos Japanの **SI → CBP → AgentOps** 変換において、
> 「仕様で制御し、実行を追跡し、品質を人が担保する」を実現する中核メソドロジーです。

---

## 3. 3つのフロー：Simple / FIRE / AI‑DLC（"別設計"として理解する）

### 3.1 早見表（経営・PMO判断に効く差分）

| 観点 | Simple | FIRE | AI‑DLC |
| -------------- | --------------------------- | ----------------------------------- | -------------------------------- |
| 主目的 | 仕様生成（spec generation） | 適応的実行＋追跡 | フルSDLC方法論 |
| 中核成果物 | requirements/design/tasks | state/runs/walkthrough + work items | memory-bank + bolts + operations |
| 承認ゲート | 3フェーズ承認 | 0/1/2（可変） | 多段（固定、10–26/bolt想定） |
| brownfield適性 | Basic | **強い**（前提） | **alpha注意**（明記） |
| DDD | 任意 | 必要な時だけ厚く | **デフォルトで強制** |
| Ops（運用） | tasksはコーディング中心 | 方法論としては限定 | **Operationsフェーズを明示** |

---

## 4. ERP導入の最適解：外形Waterfall × 内側SDD（ハイブリッド）

ERPは顧客合意・監査・UAT・Cutoverが重いため、**外形のV字ゲートを崩すと事故が増えます**。
一方、内側はAIにより「仕様→実装→テスト」の反復が高速化できる。

したがって最適解は以下です。

- **外形（顧客向け）**：Waterfall/V字のゲート（合意・稟議・UAT・Go/No-Go）
- **内側（開発運用）**：SDDで **成果物＝状態**、**承認ゲート＝品質ゲート** を徹底

---

## 5. フロー選定：PMOが迷わない判定ルール

### 5.1 決定木（最小）

```
実行トラッキングが必要か？
  ├─ No → Simple
  └─ Yes → ゲートは可変か固定か？
            ├─ 可変（リスクで0/1/2）→ FIRE
            └─ 固定（監査・DDD・Opsまで）→ AI-DLC
```

### 5.2 Tecnos向け "強制引上げ"ルール（ERP/SCM/CRM共通）

- 権限/SoD/監査ログ/個人情報 → **FIRE: Validate** 以上（監査案件は AI‑DLC も検討）
- DBスキーマ変更/データ移行 → **FIRE: Validate**
- 更新系外部IF（副作用あり）/契約変更 → **Confirm or Validate（原則Validate寄り）**
- 会計・原価・在庫評価など複雑ルール → **AI‑DLC（DDD Bolt）**を局所適用

---

## 6. 各フロー運用マニュアル（完全版）

### 6.1 Simple（Spec-Plan-Tasks：仕様生成中心）

#### 6.1.1 成果物

`specs/{feature}/requirements.md|design.md|tasks.md` の3点セット。

#### 6.1.2 手順（必ず承認ゲート）

1. Requirements（何を作るか）
2. Design（どう作るか）
3. Tasks（実装チェックリスト）

各フェーズで承認し、必要なら前フェーズへ戻る。

#### 6.1.3 受入基準：EARS（ミニチート）

- WHEN … SHALL …
- WHILE … SHALL …
- IF … THEN … SHALL …
- WHERE … SHALL …

#### 6.1.4 Tasksの作法（ERPで事故らない最低条件）

- コーディングタスクのみ
- 2階層まで
- 2〜3タスクごとにテストのチェックポイント
- すべて要件参照（AC/要件ID）

> 注意：ERPは運用（輸送/移行/監視）が致命点になりやすいので、Simpleでも **Ops成果物を別紙で必須化**する（後述）。

---

### 6.2 FIRE（適応的実行：ERPアドオンの標準レーン）

#### 6.2.1 FIREの骨格

- **Intent → Work Item → Run**
- **walkthrough**（変更点・理由・検証手順）
- **state.yaml**（全体進捗の単一真実）

#### 6.2.2 3エージェント（役割）

- Orchestrator：入口
- Planner：Intent作成、Work Item分解、mode推奨
- Builder：Work Item実行、Run生成、walkthrough生成

#### 6.2.3 実行モード（速度×リスクのレバー）

- Autopilot（0 checkpoint）
- Confirm（1 checkpoint）
- Validate（2 checkpoint：設計レビュー＋実行承認）

> PMOの仕事は **modeポリシー**を固定し、Autopilot乱用を防ぐこと。

#### 6.2.4 Run / State の意味（ERPに翻訳）

- Work Item：変更要求の最小単位（DoD、依存、mode）
- Run：その変更を1回で完了させる"監査単位"
- Walkthrough：レビュー・QA・監査に耐える要約＋検証手順
- State：進捗の台帳（会議の真実）

---

### 6.3 AI‑DLC（フル方法論：複雑ドメイン/監査レーン）

#### 6.3.1 位置づけ

AI‑DLCは「アジャイルの空白（設計や品質が未定義で抜ける）」を、
**成果物の永続化（Memory Bank）＋チェックポイント**で埋める正式メソドロジー。

#### 6.3.2 3フェーズ

- Inception：Intent、要求、Unit定義、Bolt計画
- Construction：Boltをステージで実行
- Operations：deploy/verify/monitor、runbook等

#### 6.3.3 階層

**Intent → Unit → Story → Bolt → Stages**

#### 6.3.4 Bolt planning（何を決めるか）

- どのStoryを同じBoltに束ねるか（バッチング）
- Bolt type を DDD / Simple のどちらにするか（設計儀式の選択）

#### 6.3.5 Bolt type（最重要レバー）

- DDD Construction：Model → Design → ADR → Implement → Test
- Simple Construction：Plan → Implement → Test

単純タスクにDDDを当てない／複雑ドメインにSimpleを当てない。

> 注意：AI‑DLCはbrownfieldサポートがalpha注意として明記されているため、
> ERP周辺の既存改修はFIRE主戦場、AI‑DLCは"新規境界/新規ドメイン"から段階適用が安全。

---

## 7. ERPアドオンで起きがちな事故（リスクと対策）

### 事故1：速さを理由に承認ゲートをスキップ

- 仕様と実装が乖離し手戻り増
- 対策：チェックポイントを **品質ゲート**としてPMO標準化（レビュー/テスト/セキュリティ）

### 事故2：粒度が不適切（大きすぎ/小さすぎ）

- 対策：FIREは Work Item complexity と mode をセット設計
  AI‑DLCは Bolt type と timebox を適切に選ぶ。

### 事故3：stateless理解不足（"エージェントが覚えてない"）

- 対策：成果物保存を儀式化（commit/PR、walkthroughレビュー、state更新）

### 事故4：AI‑DLCをbrownfieldに全面適用

- 対策：FIRE主戦場／AI‑DLCは新規境界から段階展開。

---

## 8. 成果物設計：Spec diff / 状態管理 / 監査パック

### 8.1 Spec diff（仕様差分が一次情報）

変更を「どこがどう変わったか」で追跡し、レビュー・影響分析・再テストを差分起点に揃える。
ERPでは UI/IO/API/MSG/TEST が揃って初めて"契約変更"が完結する。

**成立条件（最低5つ）**

1. Specの分割（ui/io/api/messages/test）
2. 一意ID（AC/CT/MSG/TC等）
3. 固定フォーマット（差分ノイズ抑制）
4. Specとテストの紐づき
5. Specを一次情報として運用（Excelは出力扱い）

### 8.2 監査パック（"説明責任"を自動で束ねる）

- Spec差分（何が変わったか）
- Run/walkthrough（なぜ・どう検証したか）
- CI結果（テスト/解析/依存スキャン/Secrets）
- Opsパック（輸送、rollback、runbook）

---

## 9. PMO実装：Gate・RACI・KPI

### 9.1 Gate（承認ゲート＝品質ゲート）最小セット

- Spec承認（Requirements/Design/Tasks または Spec pack）
- 実行承認（FIRE Confirm/Validate、AI‑DLC stage）
- walkthrough承認（Runごと）
- Ops承認（輸送/移行/rollback/監視）

### 9.2 RACI（最小）

| 役割 | Simple | FIRE | AI‑DLC |
| --------- | ---------------- | --------------------------- | -------------------------- |
| 業務PO | requirements承認 | Validate設計レビュー承認 | Inception主要承認 |
| Tech Lead | design/tasks承認 | mode設定・Run承認 | Bolt type・設計/実装ゲート |
| QA | テスト観点 | walkthrough検証手順レビュー | Test/Operationsゲート |
| PMO | 仕様と進捗 | state/runs監査・横展開 | 方法論順守・証跡監査 |

### 9.3 KPI（AgentOpsに直結する指標）

- Lead time（Work Item→Done）
- Review time（walkthroughレビュー時間）
- 手戻り率（Spec差分の再オープン）
- SIT欠陥流出（重大欠陥0を基本）
- 回帰自動化率（契約テストの網羅）
- 監査パック生成コスト（手作業時間）

---

## 10. 90日導入ロードマップ（Tecnos向け）

### Phase 1（0–2週）：型を作る（事故を止める）

- FIREを標準実行レーンに設定（brownfield主戦場）
- modeポリシーをPMO標準化
- walkthroughレビューをDoDに組み込み（Autopilotでも必須）
- Specをmd/yamlに正規化（Excelは合意用出力へ）

### Phase 2（3–6週）：チーム運用（品質×速度の最適化）

- Work Item粒度標準化（complexity→mode推奨）
- state更新・成果物保存を儀式化（stateless対策）
- IDE拡張で可視化（runs/bolts/overview）

### Phase 3（7–12週）：AI‑DLCの局所投入（複雑ドメイン）

- 会計/在庫/需給などを DDD Bolt 対象に指定
- Inception→Construction→Operations をTEIM/品質基準に紐付け
- brownfield alpha注意のため"新規境界から段階適用"

---

## 11. テンプレ集（コピペ運用一式）

> 以下は "specs.md思想に準拠しつつ、ERP導入（監査・移送・運用）まで回る形"に最適化したテンプレです。

### 11.1 Simple：requirements.md（EARS＋用語集）

```md
# Requirements

## Introduction
（2〜3文で「何を実現するか」）

## Glossary
- **System**:
- **Actor**:
- **KeyTerm**:

## Requirements

### Requirement 1
**User Story:** As a <role>, I want <capability>, so that <benefit>.

#### Acceptance Criteria (EARS)
1. WHEN <trigger>, THE <System> SHALL <response>.
2. IF <undesired condition>, THEN THE <System> SHALL <response>.
3. WHILE <state>, THE <System> SHALL <response>.
4. WHERE <option>, THE <System> SHALL <response>.
```

### 11.2 FIRE：modeポリシー（ERP版）

```yaml
# fire-mode-policy.yaml（PMO管理）
mode_policy:
  autopilot:
    use_when:
      - "表示/文言/ログ/テスト追加など可逆で局所"
    avoid_when:
      - "権限/監査/SoD/PII"
      - "DBスキーマ/データ移行"
      - "更新系外部IF"
  confirm:
    use_when:
      - "通常機能追加"
      - "契約変更（影響限定）"
  validate:
    use_when:
      - "権限/SoD/監査/PII"
      - "会計/在庫などコアロジック"
      - "DBスキーマ/移行"
      - "更新系外部IF/横断影響"
```

### 11.3 FIRE：Work Item（ERP版）

```md
# Work Item: WI-ERP-XXX

## Mode
- validate|confirm|autopilot

## Risk Flags (Yes/No)
- 権限/内部統制:
- DBスキーマ:
- データ移行:
- 更新系外部IF:
- 会計/在庫計算:

## Spec Links（唯一の真実）
- UI:
- IO:
- API/電文:
- MSG:
- TEST:

## Definition of Done
- [ ] Spec差分レビュー完了
- [ ] 実装完了（影響箇所列挙）
- [ ] テスト追加/更新（契約＋例外＋メッセージ）
- [ ] walkthrough（変更点・理由・検証手順）レビュー完了
- [ ] CI合格
- [ ] Ops更新（輸送/rollback/監視）
```

### 11.4 AI‑DLC：Bolt type選定（社内基準案）

```yaml
# bolt-type-policy.yaml
bolt_type_policy:
  ddd_construction:
    triggers:
      - "複雑な業務ルール"
      - "誤りの影響が大"
      - "集約/不変条件設計が必要"
    stages: ["domain-model", "technical-design", "adr-analysis", "implement", "test"]
  simple_construction:
    triggers:
      - "UI"
      - "単純CRUD"
      - "外部API連携"
      - "ユーティリティ/スクリプト"
    stages: ["plan", "implement", "test"]
```

### 11.5 Opsパック（Simple/FIREでも必須化する最小）

```md
# Ops Pack (ERP)

## Transport / Release
- DEV->QA:
- QA->PRD:
- リリース窓:
- 影響範囲（モジュール/テーブル/IF/バッチ）:

## Rollback
- ロールバック条件:
- 手順:
- 依存（データ移行がある場合の扱い）:

## Hypercare
- 監視観点:
- 障害一次切り分け:
- 問合せ窓口/体制:
```

---

## 12. 参考リンク（specs.md）

- specs.md ドキュメント: https://specs.md
- Simple Flow: https://specs.md/simple-flow/overview
- FIRE Flow: https://specs.md/fire-flow/overview
- AI-DLC Flow: https://specs.md/aidlc/overview
- GitHub: https://github.com/fabriqaai/specs.md

---

## 付録：追加章として一体化可能なもの

- **案件受付のFlow Decision Record（FDR）**（例外承認・部分適用・監査区分）
- **ERP/SCM/CRM別 Validate 判定表**（権限/データ/統合点の具体チェック）
- **mcframe/SAP設計書 → Spec（md/yaml）変換規約**（ID体系・差分更新ルール）

---

*作成: 2026-02-02 岡崎 仁（Hitoshi Okazaki）*
*テクノスジャパン イノベーション推進本部*
