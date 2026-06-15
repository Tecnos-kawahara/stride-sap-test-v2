# Phase 4 〜 Final Phase の全体構造（SAP 拡張）

> この文書は Phase 4 と Final Phase の役割分担を理解するための参照資料です。
> 作業手順は `agent_docs/phase4_execute.md` および `agent_docs/phase_final.md` を参照してください。

---

## 全体フロー

```
Phase 4: Execute（WI 単位で繰り返し）
  ├── WI-A → 16-step フロー → WI 承認
  ├── WI-B → 16-step フロー → WI 承認
  └── ...全 WI 完了
        │
        ▼
Final Phase（Feature 単位で 1 回）
  ├── F-1: evidence_pack.md 集約
  ├── F-2: Ops Pack 検証
  ├── F-3: stride pr-check 7/7
  └── F-4: Final Gate 承認
```

---

## WI の構成基準

WI の分割基準は **標準 SDD フレームワーク（sdd_bootstrap.md §6）に従う**。
risk_flags、Intent/Scope の統一性、AC との対応（該当シナリオを独立検証可能か）に基づいて構成する。
同じ AC を共同で充足する複数の SAP オブジェクトは 1 WI にまとめ、開発順序は WI 内の Step 6 で管理する。
（Task → WI の構成ルールは `agent_docs/phase3_tasking.md` §5 を参照）

---

## 1 WI 内のフロー（SAP 統合版）

標準の 16-step WI フロー（sdd_bootstrap.md §6）に SAP 固有ステップを統合した全体像。
SAP 固有ステップ（★）は ABAP 開発を伴う WI でのみ実行する。

```
[準備]
  Step 1:  WI 定義作成 ★ sap_transport / sap_objects / sap_owner を設定
  Step 2:  wi_readiness_checker → PASS
  Step 3:  Mode 判定 → confirm/validate なら事前承認 ★ SAP 固有 risk_flags 対応
  Step 4:  RUN ディレクトリ作成
  Step 5:  sdd_planning_bridge.py init

[実装 + テスト] ★ ABAP 開発を伴う WI のみ
  Step 6:  SAP 実装サイクル（6-1〜6-4）
           6-1  create_object.js
           6-2  TDD サイクル（AC 単位で繰り返し）
                ├─ テスト記述 → 品質チェック → activate → run_tests（RED）
                └─ 実装記述   → 品質チェック → activate → run_tests（GREEN）
                品質チェック = clean_abap → abaplint → sap_common_class_lint → sap_quality_score
           6-3  data_preview.js
           6-4  gui_test.js              ※ FAIL → 6-2 に戻る

[受入テスト] ★ ABAP 開発を伴う WI のみ
  Stage 2: 受入テスト
           S2-A1 alignment check（spec-coverage / impl-coverage）
           S2-A2 AI 判定（過剰実装 / 仕様漏れ検出）
           S2-B1 テストシナリオ全実行（ABAP Unit + GUI テスト）
           S2-B2 NOT_TESTABLE 判定
           S2-B3 stride-lint PASS
           Dual Test Gate: 全 ABAP Unit GREEN + 全 GUI テスト PASS → 次へ

[エビデンス取得] ★ ABAP 開発を伴う WI のみ
  Stage 3: エビデンス取得
           S3-A1 前提条件チェック（Stage 2 完了確認）
           S3-A2 evidence_capture.js でシナリオ別取得  (gated)
           S3-A3 evidence_merge_report.js で統合レポート生成
           S3-A4 AC 別検証結果テーブル確認
           S3-A5 エビデンス自己チェック（5 項目）

[記録 + 完了]（全ステップ必須 — SAP 固有の追加なし、標準フロー通り実行）
  Step 7:  stride-lint 実行
  Step 8:  sdd_planning_bridge.py sync
  Step 9:  walkthrough.md 作成
  Step 10: sdd_planning_bridge.py evidence
  Step 11: test_results.md 作成（coverage_tier が standard/critical なら必須）
  Step 12: sdd_planning_bridge.py learn（全 WI で実行。空でも実行する）
  Step 13: /planning:archive 実行（全 WI で実行。空でも実行する）
  Step 14: stride-lint 最終実行 + 完了チェック ★ SAP 拡張チェック S-1/S-2/S-3 追加
  Step 15: WI 承認依頼（⛔ 停止）
  Step 16: state.yaml 更新
```

---

## Phase 4 と Final Phase の責務分担

| 責務 | Phase 4（WI 内） | Final Phase（Feature 単位） |
|------|-----------------|--------------------------|
| ABAP ソース実装 | Step 6 (6-1〜6-9) | — |
| 単体テスト / GUI テスト | Step 6 (6-4, 6-7, 6-9) | — |
| 受入テスト（alignment + シナリオ） | Stage 2 | — |
| テストエビデンス取得 | Stage 3 | — |
| walkthrough / test_results | Step 9, 11 | — |
| WI 承認 | Step 15 | — |
| evidence_pack.md 集約 | — | F-1 |
| ai_provenance 記録 | — | F-1 |
| Ops Pack 検証 | — | F-2 |
| stride pr-check 7/7 | — | F-3 |
| Final Gate 承認 | — | F-4 |

---

## SAP 固有ステップの適用条件

Step 6（6-1〜6-9）、Stage 2、Stage 3 は **ABAP 開発（ソース実装）を伴う WI でのみ実行する**。
ABAP 開発を伴わない WI は、標準 16-step フローをそのまま実行する。

なお、標準の WI 分割基準に従い、前提オブジェクト（MSAG 等）と本体オブジェクト（PROG 等）が
同じ AC を共同で充足する場合は 1 WI にまとめるため、MSAG のみの WI が発生するケースは限定的。

---

## 参照

- `agent_docs/phase4_execute.md` — Phase 4 作業手順
- `agent_docs/phase_final.md` — Final Phase 作業手順
- `agent_docs/phase3_tasking.md` §5 — Task → WI 構成ルール
- `agent_docs/sdd_bootstrap.md` §6 — 標準 16-step WI フロー
