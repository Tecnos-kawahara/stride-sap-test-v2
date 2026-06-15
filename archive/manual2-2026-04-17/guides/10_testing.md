# テスト戦略

> **対象**: 実装者 / 設計者 / QA
> **所要時間**: 18分
> **前提**: [09_execute_phase.md](09_execute_phase.md) を読んでいること
> **In scope**: テスト種別の考え方、Tier とテストの関係、testreport、integration test の位置づけ
> **Out of scope**: 各言語フレームワークの細かな API、CI ベンダー別設定、security audit の詳細

---

## テスト戦略の基本

Tecnos-STRIDE のテストは、「とにかく件数を増やす」ためのものではありません。  
**受入条件と契約を、必要な粒度で確かめるための仕組み**として設計します。

まずは、次の 4 種類を区別して考えると整理しやすくなります。

| 種別 | 何を確認するか |
|---|---|
| Unit Test | 個々の関数やクラスのロジック |
| Integration Test | モジュール間・外部連携との接続 |
| Contract Test | 契約どおりに入出力やスキーマが守られているか |
| E2E Test | 利用者視点で一連の流れが成立するか |

---

## Coverage Tier とテストの重さ

Coverage Tier が上がるほど、求められるテストの厚みも増えます。

| Tier | 期待される考え方 |
|---|---|
| `starter` | 最小限の確認で早く回す |
| `standard` | Unit / Integration / Contract の基本セットを揃える |
| `critical` | 契約、権限、業務シナリオ、証跡まで厳密に揃える |

> **注: Tier は「量」だけではありません**  
> 重要なのは、案件の失敗コストに見合う検証を選ぶことです。  
> critical なのに軽いスモークテストだけ、という状態は避けます。

---

## 受入条件からテストへ落とす

よいテスト戦略は、`spec.md` の受入条件とつながっています。

たとえば次のように考えます。

- 正常系の AC は Unit / Integration / E2E のどこで担保するか
- 異常系の AC はどの層で確認するか
- 外部連携の約束事は Contract Test でどう確認するか

「何となく必要そうなテスト」を増やすより、**どの AC をどこで担保するか**を意識してください。

---

## Contract Test の重要性

Tecnos-STRIDE では、契約を先に定めるため、Contract Test の役割が大きくなります。

確認したい観点の例:

- OpenAPI どおりのレスポンスになっているか
- イベントやファイルのスキーマが崩れていないか
- `database_schema.yaml` と実装の前提がずれていないか

契約が曖昧だと、連携先と「想定していた形式が違う」という事故が起きやすくなります。

---

## E2E テストは代表シナリオに絞る

E2E は強力ですが、保守コストも高いです。  
そのため、すべてを E2E に寄せるのではなく、**利用者視点で重要な流れ**に絞るのが基本です。

よくある候補:

- ログインから主要登録処理までの一連操作
- 承認や状態遷移を含む代表フロー
- 外部連携を伴う重要シナリオ

一方で、細かな境界条件や枝分かれは Unit / Integration に寄せた方が扱いやすいことが多いです。

---

## testreport 連携

プロジェクトによっては、外部の testreport 基盤と連携して、CI の結果を整理することがあります。  
この場合も発想は同じで、**テスト結果を Evidence Pack とつなげる**ことが目的です。

testreport を導入している場合は、次を意識してください。

- テストケースと feature の対応が見える
- Evidence Pack へ結果を取り込める
- レポートが CI 上だけで孤立しない

---

## integration test の位置づけ

integration test は、実装と契約のあいだを埋める重要な層です。  
Tecnos-STRIDE のリポジトリでも、統合テストは CLI や feature 検証の回帰確認に活用されています。

integration test が有効な場面:

- CLI の出力や終了コードの回帰確認
- feature ディレクトリを組み立てた状態での検証
- 複数ファイル間の整合性確認

---

## Harness Maturity（v5.1.0）

v5.1.0 から、テストハーネス全体の成熟度を計測・管理する仕組みが追加されました。

### `pytest -m harness`

ハーネス成熟度テスト（59 件）を単独で実行できます。

```bash
pytest -m harness
```

### ミューテーションテスト

テストが「意味のある検証をしているか」を計測します。コードを意図的に書き換えたとき（ミューテーション）にテストが失敗するかどうかで品質を評価します。

```bash
# PR 前の mutation check（cosmic-ray が必要）
stride pr-check . --mutation
```

閾値は `.env.local` の `MUTATION_THRESHOLD`（デフォルト 80%）で設定します。

### ランタイムセンサー

実装後もカバレッジが維持されているか、デッドコードが増えていないかを定期的に確認できます。

```bash
stride health specs/<feature>/ --runtime
```

詳細は [11_quality_gates.md](11_quality_gates.md) の `stride health` セクションを参照してください。

---

## 言語別に押さえる観点

| 言語 / 実行環境 | よく使う組み合わせ |
|---|---|
| TypeScript | Vitest / Playwright |
| Python | pytest / pytest-playwright |
| Java | JUnit / REST Assured |

詳細なコマンドやパターンは、必要に応じて `agent_docs/testing.md` や `sdd-templates/docs/TEST_PATTERNS.md` を参照してください。

---

## 実務でのコツ

### 1. テストを最後に押し込まない

`tasks.md` の段階でテストを明示し、実装と同時に進める方が安定します。

### 2. E2E を万能視しない

E2E は少数精鋭、その他は下位レイヤで支える方が保守しやすいです。

### 3. エビデンスまで含めて考える

「通った」だけでなく、「何が通ったか」を後で説明できる状態が重要です。

---

## 次に読むべきもの

- 品質ゲート全体: [11_quality_gates.md](11_quality_gates.md)
- 成果物の辞書: [../reference/14_artifact_reference.md](../reference/14_artifact_reference.md)
- 詳細なテストガイド: `agent_docs/testing.md`
