# Enterprise 拡張

> **対象**: PM / 設計者 / リードエンジニア
> **所要時間**: 15分
> **前提**: [04_ai_execution_model.md](04_ai_execution_model.md) を読んでいること
> **In scope**: Enterprise が必要なケース、Epic/Feature 階層、共有契約、マルチチーム運用の考え方
> **Out of scope**: Enterprise 設定ファイルの全項目、各補助ツールの詳細オプション

---

## Enterprise 拡張は何のためにあるか

標準の feature 単位運用だけでも、多くの案件は進められます。  
ただし、次のような条件が揃うと、feature だけでは管理しにくくなります。

- 複数チームが同時に動く
- 共有 API や共有契約がある
- 依存関係の調整が頻繁に起きる
- PM が横断進捗を見たい
- 承認権限を案件規模に応じて分けたい

こうした場面で使うのが Enterprise 拡張です。

---

## Epic と Feature

Enterprise では、作業を次の 2 層で扱います。

| 単位 | 役割 |
|---|---|
| Epic | 大きな業務テーマや横断施策 |
| Feature | 実装・検証の基本単位 |

たとえば「受注業務刷新」が Epic で、その中に「受注登録 API」「在庫連携」「承認ワークフロー」などの Feature が並ぶイメージです。

この構造により、PM は Epic 単位で全体進捗を見つつ、実装は Feature 単位で管理できます。

---

## Enterprise の主要成果物

Enterprise 案件では、Feature 側の成果物に加えて、Epic 側の成果物も持ちます。

| 成果物 | 主な役割 |
|---|---|
| `epic_design.md` | Epic 全体の目的、体制、マイルストーンを整理する |
| `epic_flow.bpmn` | チーム間・システム間の受け渡しを俯瞰する |
| `feature_breakdown.md` | Epic をどの Feature に分けるか整理する |
| `EPIC_APPROVAL.md` | Epic Gate の承認状態を管理する |

Feature 側の `basic_design.md` や `process.bpmn` が「個別機能の実装に向いた粒度」だとすると、Epic 側は「横断調整に向いた粒度」です。

---

## Enterprise が向いている案件

次のうち 2 つ以上に当てはまるなら、Enterprise を検討する価値があります。

- 3 チーム以上で並行開発する
- Epic をまたいだ契約や依存がある
- ERP や基幹連携など監査性が重い
- 承認権限を PM だけで持てない
- Feature 単位では見えない横断リスクがある

逆に、単独チームで短期間に完結する案件なら、標準運用の方が軽くて扱いやすいことが多いです。

---

## 共有契約と依存関係

Enterprise で難しくなるのは、個別 feature の品質ではなく、**feature 間の関係**です。

代表例は次の通りです。

- 共通 API を複数 feature が使う
- ある feature の完了が別 feature の開始条件になる
- 共有データ定義や IDoc 仕様を複数チームが参照する

このため Enterprise では、共有契約や依存関係を明示的に管理します。  
目的は統制のためだけではなく、「どこが変更の起点になるか」を見えるようにすることです。

---

## `epic_flow.bpmn` とは何か

`epic_flow.bpmn` は、**Epic 全体の連携概観を表す BPMN** です。  
単一 Feature の実装フローを表す `process.bpmn` とは役割が違います。

この章で押さえるべきなのは、**どう描くかの細則ではなく、何のために置くのか**です。

### `process.bpmn` との違い

| 観点 | `process.bpmn` | `epic_flow.bpmn` |
|---|---|---|
| 対象 | 単一 Feature | Epic 全体 |
| 主な目的 | 実装対象の業務フロー整理 | チーム間・システム間の受け渡し整理 |
| 粒度 | 実装に近い | 俯瞰・計画に近い |
| 形 | executable BPMN | overview BPMN |

`process.bpmn` に無理にすべてのチームやシステムを詰め込むと、図が重くなり、実装者にも PM にも読みにくくなります。  
そのため、**チーム横断・システム横断の受け渡しは `epic_flow.bpmn` に切り出す**のが基本です。

### どんなときに必要か

- 複数チームで受け渡しがある
- 外部システムとのやり取りが複数の Feature にまたがる
- Feature 単体の BPMN では全体像が見えない

### 実務での見方

- どの participant がどこで引き継ぐか
- どの message flow が依存関係になっているか
- どの Feature がどの受け渡しを前提にしているか

> **注: participant / message flow**  
> BPMN で、参加者や受け渡しを表す要素です。  
> Epic BPMN では、処理の細部よりも、この受け渡し関係が重要になります。

詳細な記法や作図ルールは、この章では扱いません。  
必要になったら、既存の詳細資料である `manual/10_bpmn_guide.md` や `docs/camunda_bpmn_practice_guide.md` を参照してください。

---

## Epic Gate の考え方

Feature に Gate があるように、Epic にも全体確認の節目があります。  
Epic Gate は、個々の実装品質というより、**横断計画と整合性**を見る場面で役立ちます。

たとえば次の観点を確認します。

- Epic の目的が feature 分解と一致しているか
- チーム分担が現実的か
- 依存サイクルがないか
- 共有契約の変更が統制されているか

---

## TEIM / PMO との相性

Tecnos-STRIDE の Enterprise 拡張は、既存の PMO 管理や TEIM 的なフェーズ管理と相性がよい設計です。  
理由は、成果物と Gate が明示されているため、会議体やレビューの入口を作りやすいからです。

> **注: TEIM**  
> ここでは、テクノスの大規模導入案件で使う実行方法論や PMO 運用の文脈を指しています。  
> 詳細な対照表は、実装時に別資料へリンクする前提です。

---

## 主なコマンド

Enterprise が有効な場合、次のようなコマンドを使います。

```bash
# Epic を作成
sdd-templates/bin/stride epic init EPIC-ORDER

# Epic を検証
sdd-templates/bin/stride epic validate EPIC-ORDER

# Epic の Gate 状態
sdd-templates/bin/stride epic gates EPIC-ORDER

# Epic 配下に Feature を作成
sdd-templates/bin/stride init feat_order_api --epic EPIC-ORDER

# Enterprise 拡張を含めて lint
sdd-templates/bin/stride lint specs/feat_order_api/ --enterprise
```

`stride epic init` を使うと、Epic の土台として `epic_design.md` と `epic_flow.bpmn` が生成されます。

> **補足**  
> Enterprise 機能は `sdd-templates/config/enterprise.yaml` で有効化されている必要があります。

---

## Enterprise で特に大事なこと

### 1. 個別 feature の最適化だけで終わらない

1 つの feature がきれいでも、横断整合が崩れていれば全体は失敗します。

### 2. 共有契約を勝手に変えない

共有 API、共有データ定義、共有イベントは、複数チームへ波及します。  
変更時は影響範囲を見えるようにします。

### 3. PM が「全体の詰まり」を見えるようにする

実装進捗だけでなく、依存、承認待ち、共有契約待ちを追うことが重要です。

---

## 次に読むべきもの

- PM の横断管理: [../guides/06_pm_guide.md](../guides/06_pm_guide.md)
- 品質ゲートと CI: [../guides/11_quality_gates.md](../guides/11_quality_gates.md)
- ERP 実務寄りの注意点: [../appendix/20_erp_addon_playbook.md](../appendix/20_erp_addon_playbook.md)
