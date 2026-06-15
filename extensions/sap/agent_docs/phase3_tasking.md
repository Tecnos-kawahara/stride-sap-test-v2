# Phase 3: Tasking（SAP 拡張）

> **Compaction re-read**: コンテキスト圧縮後、このファイルを再読み込みすること。
> Phase 3 の SAP 固有タスク構成ルールが記載されている。

---

## 1. SAP 開発順序（MANDATORY）

tasks.md のタスク順序は以下の SAP オブジェクト依存関係に従う:

```
DDIC → CDS → BDEF → CLAS → DCLS → SRVD → SRVB → DDLX
```

| 順序 | オブジェクト種別 | 説明 | 依存先 |
|------|----------------|------|--------|
| 1 | DDIC | データディクショナリ（テーブル/ドメイン/データ要素） | なし |
| 2 | CDS | Core Data Services ビュー定義 | DDIC |
| 3 | BDEF | Behavior Definition | CDS |
| 4 | CLAS | ABAP クラス（Behavior Implementation 含む） | CDS, BDEF |
| 5 | DCLS | Access Control（権限制御） | CDS |
| 6 | SRVD | Service Definition | CDS, BDEF |
| 7 | SRVB | Service Binding | SRVD |
| 8 | DDLX | Metadata Extension（UI アノテーション） | CDS |

**違反禁止**: 依存先が未完了のタスクに先行着手してはならない。

---

## 2. Mode 自動判定（Rule S7）

各タスクの risk_flags から実行 mode を自動判定する:

| risk_flags | Mode | 事前承認 |
|------------|------|---------|
| `ui_only`, `message_only`, `test_only`, `logging_only` | **autopilot** | なし |
| `new_api`, `contract_change`, `performance_sensitive` | **confirm** | plan_review |
| `accounting_calc`, `db_schema`, `authz`, `sod`, `pii`, `data_migration` | **validate** | design_diff + plan_review |

### SAP 固有 risk_flags の判定基準

- `accounting_calc`: basic_design の CALC カタログに金額計算が存在
- `db_schema`: data_references に新規テーブル（gate: empty）が存在
- `authz`: screens[].access_control にロール別制御が存在

validate mode のタスクは **設計差分レビュー + 計画レビュー** を人間に求めてから着手する。

---

## 3. sap_objects メタデータ（per task）

各タスクに `sap_objects` を記録する。データソースは `basic_design.sap_context.dev_objects`:

```yaml
tasks:
  - id: "T-FEAT001-001"
    title: "DDIC テーブル作成"
    sap_objects:
      - type: "TABL"
        name: "ZTABLE_NAME"
      - type: "DTEL"
        name: "ZDATA_ELEMENT"
    risk_flags: ["db_schema"]
    mode: "validate"  # risk_flags から自動判定
    plan_refs: ["PL-FEAT001-001"]
```

### sap_objects 必須ルール

1. **type**: SAP オブジェクトタイプ（TABL, DTEL, DOMA, DDLS, BDEF, CLAS, DCLS, SRVD, SRVB, DDLX, PROG, FUGR, INTF 等）
2. **name**: SAP オブジェクト名（Z/Y プレフィックス）
3. **ソース**: `basic_design.sap_context.dev_objects` から取得。手動追加禁止
4. **空配列禁止**: sap_objects が空のタスクは Phase 4 に進めない（Rule S4）

---

## 4. tasks.md Canonical YAML（SAP 拡張フィールド）

標準の tasks.md YAML に以下の SAP 固有フィールドを追加:

```yaml
tasks_gate_check:
  tasks_ready_for_code: true
  sap_dev_order_validated: true  # SAP 開発順序検証済み
  bdd_mode: "required"           # BDD モード必須
```

### 検証

```bash
sdd-templates/bin/stride lint specs/<feature>/
```

stride-lint が以下を検証する:
- SAP 開発順序の整合性（依存先タスクが先行していること）
- sap_objects の存在と basic_design.sap_context.dev_objects との一致
- risk_flags → mode マッピングの正当性
- bdd_mode = required の設定

---

## 5. Task → Work Item 構成ルール（MANDATORY）

### Task と WI の関係

- **Task** (tasks.md): 作業の分解単位。type（impl / test / ops / contract 等）で分類する
- **Work Item** (work_items/): Phase 4 の実行単位。1 WI = 1 Run で実行する

複数の Task を 1 つの WI にまとめる。
WI の分割基準は **標準 SDD フレームワーク（sdd_bootstrap.md §6）に従う**。
SAP 拡張が独自の分割基準を定義することはない。

### WI の分割基準（標準準拠）

以下は標準の分割基準であり、SAP 開発でもそのまま適用する:

1. **risk_flags → mode に基づくグルーピング**: 同じリスクプロファイルの作業を同一 WI にまとめる
2. **Intent/Scope の統一性**: 1 WI = 1 つの明確な目的
3. **spec の AC との対応**: WI が担当する AC に対して、scenarios.yaml の該当シナリオをその WI 単独で実行・検証できること
4. **complexity に応じた粒度**: 複雑度が高い場合は分割を検討

### SAP 開発での適用

SAP 開発では複数の SAP オブジェクト（MSAG, PROG, CLAS 等）を実装する場合がある。
これらのオブジェクトを WI に構成する際は、上記の標準分割基準に従う。

- **前提オブジェクト（MSAG 等）と本体オブジェクト（PROG 等）が同じ AC を共同で充足する場合**: 同一 WI にまとめる。SAP 開発順序（create/activate の順序）は WI 内の Step 6 で管理する
- **独立した AC を持つオブジェクト群**: 別 WI に分割できる（標準の分割基準に照らして判断）

### テスト Task の組み込み

テスト Task（type: test）は、テスト対象の実装 Task と同じ WI に含める。
WI の 16-step フローは実装とテストの両方を 1 Run 内で実行する構造のため、
テスト専用の WI を別に作成する必要はない。

### risk_flags の集約

WI に複数の Task をまとめる場合、WI の risk_flags は **含まれる全 Task の risk_flags の和集合** とする。
mode は集約後の risk_flags から §2 のルールで判定する。

```yaml
# 例: MSAG 作成 (message_only) + PROG 実装 (authz, accounting_calc) + 単体テスト (test_only) → 1 WI
wi_id: "WI-FEAT001-001"
risk_flags: ["authz", "accounting_calc"]  # 最も厳しいフラグが mode を決定
mode: "validate"                           # authz → validate
```

### WI 内の SAP オブジェクト開発順序

1 WI に複数の SAP オブジェクトが含まれる場合、Step 6 で以下の順序に従って create → activate を実行する:

```
DDIC → CDS → BDEF → CLAS → DCLS → SRVD → SRVB → DDLX
```

同種のオブジェクト内では、tasks.md の `activation_order` に従う。

### 構成例（レポートプログラム開発）

tasks.md に MSAG 作成 + PROG 実装 + 各種テスト Task がある場合の WI 構成:

| WI | 含まれる Task | risk_flags | mode |
|----|-------------|-----------|------|
| WI-001 | MSAG 作成 + PROG 実装 + 契約テスト + 単体テスト + 統合テスト + E2E テスト | authz, accounting_calc | validate |

- MSAG と PROG は同じ AC を共同で充足するため、1 WI にまとめる
- Step 6 内で MSAG → PROG の順序で create/activate を実行する
- テスト Task は実装 Task と同じ WI に含める
- Ops Pack（transport/release/rollback/hypercare）は WI の post-run で作成する
- エビデンス取得（Stage 3）は WI 内で実行する
- evidence_pack.md 集約・Ops Pack 検証・移送準備は Final Phase で実施する

---

## 承認済み成果物の変更ルール

本 Phase の作業中に、先行 Gate で承認済みの成果物（basic_design.md, process.bpmn, spec.md, plan.md, contracts/, scenarios.yaml 等）を修正する必要が生じた場合:
1. `implementation-details/change_log.md` に変更内容・理由・影響範囲を記録する
2. 意味的変更（要件追加・削除等）の場合は人間に再承認を相談する
3. フォーマット修正のみ（lint 準拠等）の場合は change_log 記録のみで続行可

**change_log を記録せずに承認済み成果物を変更してはならない。**

---

## プログラム種別別 タスク構成リファレンス

本セクションは、プログラム種別ごとのタスク構成を決定する際の参照情報である。
basic_design.sap_context.program_type に基づき、適切な sap_objects・done_when・エビデンス対象を設定する。

### 種別一覧表

| 種別 | 主な sap_objects | 契約 Phase 固有 done_when | エビデンス Tx | 受入テスト観点 |
|------|-----------------|--------------------------|--------------|---------------|
| **report** | PROG | -- | SE38, SE16 | SAP GUI データ検証 |
| **fugr** | FUGR, FUNC | FUGR インターフェース仕様（IMPORTING/EXPORTING/CHANGING/TABLES/EXCEPTIONS）が定義されている | SE37, SE16 | 汎用モジュール呼び出し・パラメータ検証・例外処理 |
| **enhancement** | CLAS, ENHS | 拡張ポイント仕様（BAdI 定義・Enhancement Spot・標準プロセス影響分析）が定義されている | SE18, SE19, SE16 | 標準プロセス経由での BAdI 呼び出し・拡張ロジック検証 |
| **interface** | PROG | インターフェース仕様（入力ファイルフォーマット、RFC/IDoc、エラーハンドリング）が定義されている | SE38, SE16 | ファイル入出力・RFC/IDoc 連携 |
| **rap_bo** | TABL, DDLS, BDEF, CLAS, DCLS, SRVD, SRVB | DDIC テーブル定義・CDS ビュー階層・BDEF 契約が定義されている | ADT, OData V4, SE16 | OData CRUD・バリデーション・権限チェック |

### 種別別 詳細ノート

#### report（レポートプログラム）

- **sap_objects**: `PROG`（TYPE 1 レポートプログラム）
- **実装タスク概要**: レポートプログラム本体 + ABAP Unit テストクラス（local include）
- **done_when（実装固有）**: レポートプログラムが構文チェック通過・アクティベーション成功
- **エビデンス取得**: SE38 実行画面 + SE16 事前/事後データ確認スクリーンショット
- **特記事項**: 最もシンプルな構成。MSAG（メッセージクラス）が必要な場合は同一 WI にまとめる

#### fugr（汎用モジュールグループ）

- **sap_objects**: `FUGR`（汎用モジュールグループ）+ `FUNC`（汎用モジュール）
- **実装タスク概要**: 汎用モジュールグループ + 汎用モジュール + ABAP Unit テストクラス
- **done_when（実装固有）**: 汎用モジュールグループ・全汎用モジュールが構文チェック通過・アクティベーション成功。IMPORTING/EXPORTING/CHANGING/TABLES パラメータ処理が実装されている
- **done_when（契約固有）**: FUGR インターフェース仕様（IMPORTING/EXPORTING/CHANGING/TABLES/EXCEPTIONS パラメータ定義）が契約に含まれている
- **エビデンス取得**: SE37 汎用モジュール実行画面 + SE16 事前/事後データ確認スクリーンショット
- **特記事項**: 汎用モジュール単位でパラメータの入出力契約を定義する。EXCEPTIONS の定義が契約 Phase で必須

#### enhancement（拡張実装 / BAdI）

- **sap_objects**: `CLAS`（BAdI 実装クラス）+ `ENHS`（Enhancement Spot）
- **実装タスク概要**: BAdI 実装クラス + Enhancement Spot 登録 + ABAP Unit テストクラス
- **done_when（実装固有）**: BAdI 実装クラスが構文チェック通過・アクティベーション成功。Enhancement Spot への登録が完了。標準プロセスへの影響が設計通り
- **done_when（契約固有）**: 拡張ポイント仕様（BAdI 定義・Enhancement Spot・標準プロセスへの影響分析）が契約に含まれている
- **エビデンス取得**: SE18（BAdI 定義確認）+ SE19（BAdI 実装確認）+ SE16 事前/事後データ確認スクリーンショット
- **特記事項**: 標準の制御メカニズムの範囲内で拡張すること（SAP 拡張原則）。標準プロセスへの影響分析が契約 Phase で必須。受入テストは標準トランザクション経由で BAdI が正しく呼び出されることを検証する

#### interface（インターフェースプログラム）

- **sap_objects**: `PROG`（TYPE 1/2 インターフェースプログラム）
- **実装タスク概要**: インターフェースプログラム本体 + ABAP Unit テストクラス
- **done_when（実装固有）**: インターフェースプログラムが構文チェック通過・アクティベーション成功。ファイル入出力処理・RFC/IDoc 呼び出し・エラーハンドリングが実装されている
- **done_when（契約固有）**: インターフェース仕様（入力ファイルフォーマット、RFC/IDoc 連携、エラーハンドリング方針）が契約に含まれている
- **エビデンス取得**: SE38 実行画面 + SE16 事前/事後データ確認スクリーンショット
- **特記事項**: ファイル連携・RFC/IDoc 通信の外部依存を持つ。テストではモック/スタブによる外部接続代替が必要になる場合がある

#### rap_bo（RAP Business Object）

- **sap_objects**: `TABL`（DBテーブル）+ `DDLS`（CDS ビュー）+ `BDEF`（Behavior Definition）+ `CLAS`（Behavior Implementation）+ `DCLS`（Access Control）+ `SRVD`（Service Definition）+ `SRVB`（Service Binding）
- **実装タスク概要**: 全 RAP スタックオブジェクトの一括実装 + ABAP Unit テストクラス
- **done_when（実装固有）**: 全 DDIC テーブル・CDS ビュー・BDEF + Behavior Implementation・DCLS・SRVD/SRVB が構文チェック通過・アクティベーション成功
- **done_when（契約固有）**: DDIC テーブル定義・CDS ビュー階層・BDEF 契約（Standard Operations, Validations, Determinations, Actions）が契約に含まれている
- **エビデンス取得**: ADT 画面（各オブジェクトのアクティベーション確認）+ OData V4 エンドポイントテスト + SE16 データ確認スクリーンショット
- **特記事項**: SAP 開発順序（DDIC -> CDS -> BDEF -> CLAS -> DCLS -> SRVD -> SRVB）に厳密に従う。オブジェクト数が最も多く、WI 構成時の SAP 開発順序遵守が特に重要。DDLX（Metadata Extension）が必要な場合は SRVB の後に追加する

### 全種別共通の done_when（実装 Phase）

以下は種別に関係なく全てのタスクで必須となる:

- 全処理ステップ（PS-xxx）が @STEP アノテーション付きで実装されている
- 全 AC に対応するテストメソッドが @TS アノテーション付きで作成されている
- sap_ts_coverage_lint.py PASS（各 TS-ID に対応する @TS 付きテストメソッドが個別に存在）
- run_tests.js で全テストメソッドが GREEN
- ステートメントカバレッジ 100%（ABAP フレームワーク制約による除外は理由を文書化）
- sap_common_class_lint.py PASS

---

## 参照

- `CLAUDE_SAP.md` Rule S4（WI メタデータ必須）
- `CLAUDE_SAP.md` Rule S7（SAP 固有 risk_flags）
- `agent_docs/sdd_bootstrap.md` Phase 3 セクション
