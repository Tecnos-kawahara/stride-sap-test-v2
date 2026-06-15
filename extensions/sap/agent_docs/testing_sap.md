# SAP テスト拡張ガイド

> SAP 拡張パックのテスト関連ドキュメント。標準の `agent_docs/testing.md` と併用すること。

## テストカテゴリマッピング（SAP → 標準）

> **SAP プロジェクト**: SAP 固有のテストカテゴリ（ABAP Unit, CDS Test, Behavior Test, Authorization Test, OData Test, GUI Test）は
> `evidence_pack_category_mapping.yaml` により標準カテゴリにマッピングされる。
> 詳細は `extensions/sap/templates/evidence_pack_category_mapping.yaml` および
> `extensions/sap/templates/contracts/abap_test_scenarios.yaml` を参照。

## SAP GUI テスト（画面テスト — Step S1-D4）

> **対象**: 選択画面・ALV一覧等の画面を持つ SAP ABAP プログラム（TYPE 1 レポート等）
> **位置づけ**: ABAP Unit テスト（Step S1-D2）ではカバーできない画面操作・表示の検証
> **詳細仕様**: `extensions/sap/docs/SAP_GUI_TEST.md`

### テストタイプマッピング

| AC Tag | Test Type | Test ID Pattern | ツール |
|--------|-----------|-----------------|--------|
| `gui` | GUI Screen | TS-GUI-* | gui_test.js + WSF |

GUI テストは plan.md の test_strategy に AC 単位で定義する（SAP 拡張: 1 AC = 1 TS）:
```yaml
test_strategy:
  tests:
    - id: "TS-GUI-01"
      type: "gui"
      scope: "RQ-001 選択画面表示 / SCREEN_LAYOUT / success"
      covers_acceptance_ids: ["AC-US-FEATXXX-001-01"]  # AC 1 つのみ
    - id: "TS-GUI-02"
      type: "gui"
      scope: "RQ-001 ALV一覧表示 / SCREEN_LAYOUT / success"
      covers_acceptance_ids: ["AC-US-FEATXXX-001-02"]  # AC 1 つのみ
```

### テスト作成手順

**Step S1-D4-1a: テンプレートから WSF を作成する**
- **入力**: `extensions/sap/templates/tests/gui_test_template.wsf`（移行済みテンプレート）
- **アクション**: テンプレートをコピーして WSF ファイルを作成する:
```bash
cp extensions/sap/templates/tests/gui_test_template.wsf \
   specs/<feature>/tests/e2e/gui_test_<program>.wsf
```
- **出力**: `specs/<feature>/tests/e2e/gui_test_<program>.wsf`（テンプレート状態）

**Step S1-D4-1b: CONFIG — program / selectionFields 設定**
- **入力**: spec.md の selection_screen 定義、basic_design.md の program_id、**Step 6-3 のテストデータ対応表**
- **アクション**: WSF の CONFIG セクションに以下を設定する:
  - `program` → プログラム名（basic_design.md / spec.md から取得）
  - `selectionFields` → 選択画面のフィールド定義（spec.md の selection_screen から取得）
  - `mandatoryDefaults` → OBLIGATORY フィールドのデフォルト値（**Step 6-3 で特定した実機確認済みの値を使用**）
- **出力**: WSF の program / selectionFields / mandatoryDefaults が設定済み

**Step S1-D4-1c: CONFIG — expectedColumns 設定**
- **入力**: spec.md の出力項目定義（ALV カラム等）
- **アクション**: WSF の CONFIG セクションに `expectedColumns` を設定する
- **出力**: WSF の expectedColumns が設定済み
- **⚠️ ALV を持たないプログラムの場合はスキップ可**

**Step S1-D4-1d: CONFIG — filterTests / contentChecks / regressionTest 設定**
- **入力**: spec.md の AC（フィルタ・表示内容に関するもの）、plan.md のテストシナリオ
- **アクション**: WSF の CONFIG セクションに以下を設定する:
  - `filterTests[].acId` → spec.md の AC-ID（トレーサビリティ確保）
  - `contentChecks[].acId` → spec.md の AC-ID
  - `regressionFilterField` / `regressionData` → 回帰テスト用（必要な場合）
- **出力**: WSF の filterTests / contentChecks が設定済み

**Step S1-D4-1e: カスタムテスト追加（必要な場合のみ）**
- **入力**: spec.md の AC で標準パターン（T0〜T11）ではカバーできない要件
- **アクション**: `[CUSTOM TESTS]` セクションにプロジェクト固有のテストを追加する
- **出力**: WSF 完成（全 CONFIG 設定 + カスタムテスト追加済み）

### 実行

```bash
# フル自動（SAP GUI 起動→テスト→終了、GREEN確認のみ）
node extensions/sap/tools/gui_test.js \
  specs/<feature>/tests/e2e/gui_test_<program>.wsf \
  --auto
```

> **注意**: S1-D4 はテスト GREEN の確認のみが目的。`--output` は不要。
> 正式エビデンス（画面スクショ）は全テスト GREEN 後に S3-A1 で取得する。

### 標準テストパターン（テンプレート内蔵）

テンプレートは CONFIG 設定だけで以下の標準テストを自動実行する:

| パターン | 確認内容 | 不要時 |
|---------|---------|--------|
| プログラム起動 | SA38 → 選択画面遷移 | `enableT0_Launch: false` |
| フィールド存在 | 選択画面の全フィールド確認 | `enableT1_FieldCheck: false` |
| ALV 表示 | フィルタなし実行で ALV 表示 | `enableT2_ALVDisplay: false` |
| カラム検証 | 期待カラム全件存在 | `enableT3_ColumnCheck: false` |
| データ内容 | 先頭行の主要項目が非空 | `enableT4_DataCheck: false` |
| F3 ナビゲーション | ALV → 選択画面に復帰 | `enableT5_BackNav: false` |
| 該当なし | エラー時に異常終了しない | `enableT6_NoData: false` |
| 選択フィルタ | 条件指定で正しく絞込 | `enableT7_Filters: false` |
| カラム内容 | 名称・テキスト列の有効率 | `enableT8_ContentChecks: false` |
| 回帰テスト | 特定レコードの値一致 | `enableT9_Regression: false` |
| ALV ソート | ソート操作の正常動作 | `enableT10_Sort: false` |
| ALV エクスポート | エクスポート機能の存在 | `enableT11_Export: false` |

### テスト FAIL 時の対応

**FAIL した場合は `agent_docs/gui_test_fail_analysis.md` を参照すること。**
GUI テストの原則、原因分析手順、禁止事項、修正フローが記載されている。

## S3-A1: 正式エビデンス一括取得

> **正式エビデンスは S3-A1 で取得する画面スクショのみ。Stage 1 の出力は開発者参考用。**

### Step S3-A1 前提条件チェック

- **入力**: Stage 2 の結果
- **アクション**: 以下の前提条件を全て満たしていることを確認する:
  1. 全 ABAP Unit テスト GREEN（S1-D2 完了）
  2. 全 GUI テスト PASS（S1-D4 完了、画面ありプログラムの場合）
  3. 仕様ベース分岐カバレッジ 100%（S1-E1 完了）
  4. 仕様 = 実装 一致（S2-A1 完了）
  5. 全テストシナリオ PASS（S2-B1 完了）
  6. stride-lint PASS（S2-B3 完了）
- **出力**: 前提条件チェック OK → エビデンス取得実行に進む
- **⚠️ 前提条件を1つでも満たさない場合、S3-A1 に進んではならない。該当ステップに戻って解決すること。**

### Step S3-A1: エビデンス取得実行

- **入力**: 前提条件チェック OK、plan.md の test_scenarios
- **アクション**: 各シナリオを1つずつ実行する:
```bash
node extensions/sap/tools/evidence_capture.js specs/<feature>/ --scenario SC-XX --step-id S3-A1
```
- **出力**: `screenshots/` 配下にスクリーンショット PNG、`evidence_data/` 配下に pre/post JSON

### 取得内容

plan.md の `test_strategy.evidence_capture` セクションの定義に基づく:

| プログラムtype | SE16 事前 | SE38 実行 | SE16 事後 |
|---------------|-----------|-----------|-----------|
| `reference` | pre（前提データ確認） | 全画面遷移スクショ | - |
| `update` | テーブルデータスクショ | 全画面遷移スクショ | テーブルデータスクショ |
| `reference` | テーブルデータスクショ | 全画面遷移スクショ | - |

### Step S3-A3: 統合レポート生成

- **入力**: 全シナリオの個別 HTML（`evidence_SC-*.html`）
- **アクション**: 全シナリオ完了後に実行する:
```bash
node extensions/sap/tools/evidence_merge_report.js specs/<feature>/
```
- **出力**: `tests/reports/evidence_report.html`（サイドメニュー付き統合 HTML）

### AC 別検証結果の表示

個別シナリオ HTML には、`covers_ts` の `expected_checks` フィールドに基づいて AC 別検証結果テーブルが自動生成される:

| 列 | 内容 | データソース |
|---|---|---|
| AC ID | 受入条件 ID | covers_ts[].ac_id |
| 受入条件 | AC の statement テキスト | spec.md の use_cases.acceptance |
| 検証方法 | 自動検証 / 間接確認 / AI マルチモーダル判定 | covers_ts[].verification_method |
| 期待結果 | この AC の判定に使うチェック内容 | covers_ts[].expected_checks[].description |
| 実結果 | 対応するチェック項目の実際の結果 | evidence_capture.js の検証結果 |
| 判定 | PASS / FAIL | シナリオ全体の判定 |

`expected_checks` は `sap_scenario_generator.py` が `test_perspective_master.yaml` の `perspective_expected_checks` セクションから自動生成する。

### エビデンス出力

| ファイル | 内容 | 生成元 |
|---------|------|--------|
| `evidence_SC-XX.html` | 個別シナリオ HTML | evidence_capture.js |
| `evidence_report.html` | 統合レポート HTML（サイドメニュー付き） | evidence_merge_report.js |
| `screenshots/*.png` | 画面キャプチャ（SAP GUI HardCopy） | evidence_capture.js |

出力先: `specs/<feature>/tests/reports/`

## S3 Evidence Rework（エビデンス再取得・修正モード）

`evidence_capture.js` には、初回エビデンス取得後に部分的な再取得・修正を行うメンテナンスモードがある。
エビデンスレビューで差し戻しがあった場合や、スクリーンショットの更新が必要な場合に使用する。

| モード | フラグ | 用途 | コマンド例 |
|--------|--------|------|-----------|
| **EC-M1** | `--recapture` | シナリオ再実行 + SLG1 ログ再取得 | `node evidence_capture.js --scenario SC-01 --recapture` |
| **EC-M2** | `--replace-screenshot` | 既存 HTML 内のスクリーンショットを差し替え（base64 Data URI） | `node evidence_capture.js --scenario SC-01 --replace-screenshot path/to/new.png` |
| **EC-M3** | `--update-data` | HTML のデータセクションを JSON から再生成（レイアウト維持） | `node evidence_capture.js --scenario SC-01 --update-data path/to/updated.json` |

### 使い分け

- **テストデータが変わった**: EC-M1（再実行）
- **スクリーンショットだけ撮り直し**: EC-M2（差し替え）
- **エビデンス HTML の数値・テキストのみ更新**: EC-M3（データ更新）

> EC-M1 は SAP GUI セッションが必要。EC-M2/M3 はオフラインで実行可能。

## Related Documents

- `extensions/sap/docs/SAP_GUI_TEST.md` - SAP GUI テストフレームワーク仕様
- `extensions/sap/templates/abap/PATTERNS.md` - ABAPパターン索引
- `extensions/sap/templates/abap/TEST_EVIDENCE_GUIDE.md` - テストエビデンスガイド
