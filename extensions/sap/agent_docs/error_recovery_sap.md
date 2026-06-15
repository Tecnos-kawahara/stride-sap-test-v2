# SAP 拡張エラー回復ガイド（AI 向け）

> Execute Phase（Phase 4）で発生するエラーの回復パターン。
> 人間向けトラブルシューティング: `extensions/sap/docs/SAP_TROUBLESHOOTING.md`

## エラー回復の基本原則

1. **エラーメッセージを必ず読む** — ツールの stderr/stdout 出力が回復手順の手がかり
2. **ツール手順を厳守する** — stdout 出力を経由せず独自ロジックで代替しない（Rule S1）
3. **Phase Gate で止まる** — Gate 未承認のままツールを実行しない
4. **TDD ループを維持する** — エラー修正後も AC 単位の Red-Green サイクルに戻る

---

## 1. SAP 接続エラー

### パターン: .env 未設定 / 接続不可

```
Error: SAP_URL, SAP_USERNAME, SAP_PASSWORD must be set in .env
Error: connect ETIMEDOUT
```

**回復手順:**
1. `.env` ファイルの存在と内容を確認（Read ツールで読む）
2. 変数が未設定 → 人間にエスカレーション（AI は .env を編集しない）
3. 接続タイムアウト → 人間にエスカレーション（VPN/ネットワークの問題）
4. **自動回復不可** — 人間の介入を待つ

---

## 2. オブジェクトロック競合

### パターン: activate.js でロックエラー

```
Error: Failed to lock object. The object may be locked by another user.
```

**回復手順:**
1. `unlock.js` を実行: `node extensions/sap/tools/unlock.js --type <type> --name <name>`
2. 自分のロック → 即座に解除される → `activate.js` を再実行
3. 他ユーザーのロック → 人間にエスカレーション（SM12 での解除が必要）
4. 解除後、S1-D1（activate）からリトライ

---

## 3. アクティベーションエラー

### パターン: 構文エラー / 依存関係エラー

```
Activation failed with messages:
  [error] Line 42: ...
```

**回復手順:**
1. エラーメッセージの行番号と内容を確認
2. ABAP ソース（`src/*.abap`）を修正
3. S1-C1（quality check: clean_abap → abaplint → lint → score）を再実行
4. S1-C1 パス後、S1-D1（activate）を再実行
5. **戻り先: S1-B1（ソース修正）→ S1-C1 → S1-D1**

### パターン: Include の親プログラム選択が必要

```
Multiple parent programs found:
  - ZREP_PROGRAM_A (PROG/P)
  - ZREP_PROGRAM_B (PROG/P)
Error: Multiple parent programs found for this include.
```

**回復手順:**
1. activate.js が出力した親プログラム候補一覧を確認
2. **候補一覧をユーザに提示**し、どの親プログラムで有効化するか選択を求める
3. ユーザの回答を受け取り、`--main-program <選択されたプログラム名>` を付けて activate.js を再実行
4. **自動判断しない** — 親プログラムの選択はユーザの業務判断

### パターン: 移送リクエスト未指定

```
Error: Transport number is required for non-$TMP objects.
```

**回復手順:**
1. S1-A1 で記録した TR 番号を確認
2. `--transport <TR番号>` を付けて `activate.js` を再実行
3. TR 番号が不明 → 人間にエスカレーション

---

## 4. テスト失敗

### パターン: ABAP Unit テスト FAIL

```
FAIL: test_method_name
  Expected: 'E'  Actual: 'S'
```

**回復手順:**
1. 失敗したテストメソッドと期待値を確認
2. spec.md の AC → plan.md の test_scenario → expected_result を参照
3. **原因判定:**
   - 実装バグ → S1-B1 でソース修正 → S1-C1 → S1-D1 → S1-D2
   - テスト期待値の誤り → plan.md の expected_result を修正 → S1-B1 でテストコード修正 → S1-C1 → S1-D1 → S1-D2
   - テストデータ不足 → S1-D3 で data_preview 確認 → 人間にデータ投入依頼
4. **戻り先: S1-B1 → S1-C1 → S1-D1 → S1-D2**

### パターン: テストメソッド未検出

```
Error: No unit test method found on ADTClient
```

**回復手順:**
1. テストクラスの存在を確認:
   - プログラム: `.prog.abap` 内に `CLASS ... FOR TESTING` が含まれるか
   - グローバルクラス: `.clas.testclasses.abap` ファイルが存在するか
2. `FOR TESTING` 句が付与されているか確認
3. `activate.js` でテストクラスがアップロードされているか確認（activate.js はテストクラスを自動検出・アップロードする）
4. **戻り先: S1-B1（テストクラス修正）→ S1-C1 → S1-D1 → S1-D2**

---

## 5. 品質チェックエラー

### パターン: sap_stage1_quality.py のパイプライン中断

```
[ABORT] clean_abap.js failed. Stopping.
[ABORT] abaplint failed. Stopping.
```

**回復手順:**
- `clean_abap.js` 失敗: ABAP 構文の重大エラー。ソースを修正して S1-C1 を再実行
- `abaplint` 失敗: 静的解析エラー。エラーの内容（行番号、ルール名）を確認し修正
- **パイプラインは先頭から再実行する**（clean_abap → abaplint → lint → score）
- **戻り先: S1-B1（ソース修正）→ S1-C1**

### パターン: common_class_lint 違反

```
[CC-FILE-01] Forbidden pattern: 'OPEN DATASET' at line 55
[CC-CHECK-01] Missing method call: ZCL_CMA_COMMON_CHECK=>CHECK_COMPANY_CODE
```

**回復手順:**
- 禁止パターン検出（negative check）: 直接 API 呼び出しを共通クラスのメソッドに置換
- 宣言メソッド未使用（positive check）: `common_class_applicability` で宣言されたメソッドを実装に追加
- 対象クラス・メソッドは `common_class_rules.yaml` と spec.md の `common_class_applicability` を参照
- **戻り先: S1-B1 → S1-C1**

### パターン: quality_score 不足

```
Quality score: 72 / 100 (threshold: 85)
```

**回復手順:**
1. 減点項目を確認（スコアの内訳が stdout に出力される）
2. 主な減点要因:
   - abaplint violations（構文エラー/警告）
   - missing @STEP annotations（source_marker 不足）
   - common_class_lint violations（共通クラス未使用）
   - unused methods / dead code
3. 各減点項目を修正
4. **戻り先: S1-B1 → S1-C1**

---

## 6. （v2 で廃止 — processing_steps は process_definitions[].body に統合済み）

---

## 7. Stage 2（受入テスト）エラー

### パターン: S2-A1 alignment check 失敗

```
[overimpl] @STEP STEP_YYY has no matching AC
[spec-gap] AC-03 has no covering test scenario
```

**回復手順:**
- `overimpl`（過剰実装）:
  1. S1-B1 に戻り、余分な実装を削除
  2. Stage 1 を再実行（S1-C1 → S1-D1 → S1-D2 → S1-E1）
- `spec-gap`（仕様漏れ）:
  1. spec.md に AC / processing_step の追加を提案
  2. 人間にレビュー・承認を依頼
  3. 承認後、plan.md の test_scenario を更新 → S1-B1 で実装

### パターン: evidence_capture.js シナリオ失敗

```
FAIL: SC-01 - Expected message E001 but got S001
```

**回復手順:**
1. 失敗原因を分類:
   - **バグ**: ソースの実装誤り → S1-B1 に戻り修正 → Stage 1 再テスト
   - **テストデータ不足**: データが存在しない → 人間にデータ投入依頼 → リトライ
   - **テスト不可**: 環境制約で実行不可 → HTML に NOT_TESTABLE バッジを付与（S2-B2）
2. バグの場合: S1-B1 → S1-C1 → S1-D1 → S1-D2 → S1-E1 → S2-A1 → S2-B1
3. **Stage 1 に戻った場合、Stage 1 のゲートチェック（S1-E1）から再通過が必要**

---

## 8. エビデンス取得（Stage 3）エラー

### パターン: S-Evidence 取得失敗

```
Error: Screenshot capture failed for scenario SC-01
```

**回復手順:**
1. Playwright MCP サーバーの起動確認
2. SAP セッションの有効性確認
3. 該当シナリオを個別に再実行:
   ```bash
   node extensions/sap/tools/evidence_capture.js --scenario SC-01 --screenshot --step-id S3-A1 --feature-dir specs/<feature>/
   ```
4. 全シナリオ完了後、`evidence_merge_report.js` で統合レポートを再生成

---

## 9. エラー回復フローチャート

```
エラー発生
  │
  ├─ 環境エラー（.env / 接続）→ 人間にエスカレーション → 待機
  │
  ├─ ロックエラー → unlock.js → activate リトライ
  │
  ├─ 構文 / lint エラー → S1-B1（修正）→ S1-C1（quality）→ S1-D1（activate）
  │
  ├─ テスト失敗 → S1-B1（修正）→ S1-C1 → S1-D1 → S1-D2（tests）
  │
  ├─ alignment エラー
  │   ├─ 過剰実装 → S1-B1（削除）→ Stage 1 再テスト
  │   └─ 仕様漏れ → 人間に提案 → 承認後 S1-B1
  │
  └─ エビデンス失敗 → 個別シナリオ再実行 → merge_report 再生成
```

## 10. 重要な注意事項

- **S1-C1 のツール実行順序は固定**: clean_abap → abaplint → common_class_lint → quality_score。途中からの再実行は不可、必ず先頭から。
- **S2-A1 は branch_analyzer を実行**: spec-coverage / impl-coverage の結果は S2-A2 で AI が判断。
- **Stage 1 に戻った場合**: S1-E1（post check）から再通過が必要。S2 以降のエビデンスは無効化される。
- **人間承認が必要なケース**: spec.md の変更、新規 AC の追加、テストデータの投入、ロック競合の解除（他ユーザー）。
