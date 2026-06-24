# SAP Extension Pack v2 — evidence_pack overlay

<!-- overlay_type: merge -->
<!-- base: sdd-templates/templates/evidence_pack_template.md -->
<!-- 参照仕様: 05_テンプレート設計.md §B-5 -->

## overlay: SAP 追加セクション

### activation_log

オブジェクト有効化ログ。Phase 4 Step 6-6（activate.js 実行後）に記入。

```yaml
activation_log:
  timestamp: ""
  objects:
    - name: ""
      status: ""                # active / inactive / error
      warnings: []
```

### unit_test_results

ABAP Unit テスト結果。Phase 4 Step 6-7（run_tests.js 実行後）に記入。

```yaml
unit_test_results:
  total: 0
  passed: 0
  failed: 0
  coverage: ""
```

### code_inspector_results

Code Inspector / ATC 結果。Phase 4 Step 6-5（品質チェック完了後）に記入。

```yaml
code_inspector_results:
  variant: ""
  errors: 0
  warnings: 0
  info: 0
```

### sap_gui_screenshots

SAP GUI スクリーンショット。Phase 4 Step 6-9（gui_test.js 実行後。画面系の場合のみ）に記入。

```yaml
sap_gui_screenshots:
  - screen: ""
    file: ""
    description: ""
```

### authorization_test

権限テストエビデンス。Phase 4 Stage 2（受入テスト時。authz risk_flag がある場合）に記入。

```yaml
authorization_test:
  scenarios:
    - role: ""
      expected: ""              # full_access / restricted_access / no_access
      result: ""                # pass / fail
```

### transport_evidence

移送エビデンス。Phase 4 Stage 3（移送実行後）に記入。

```yaml
transport_evidence:
  transport_number: ""
  source_system: ""
  target_system: ""
  transport_log: ""
  objects_transported:
    - type: ""
      name: ""
      status: ""                # success / error
```

### test_results（拡充）

テスト結果にシナリオ ID（scenarios.yaml）との紐付けを追加。Phase_final で最終版を記録。

```yaml
# v6.0.0 標準の test_results を拡充:
# - scenario_ref: scenarios.yaml の id への参照を追加
```

### test_green_confirmation（デュアルテストゲート）

Unit テスト（run_tests.js）と GUI テスト（gui_test.js / evidence_capture.js）の
両方が pass（または not_applicable）でなければ WI 承認不可。
sap_s_evidence_validator で SE_TEST_GREEN_NOT_CONFIRMED として検証される。
Phase 4 Step 14（5-step Step 3 で all_passed=true を確認）に記入。

```yaml
test_green_confirmation:
  unit_test:
    all_passed: true            # run_tests.js の全テスト GREEN
    count: <テスト数>
  gui_test:
    all_passed: true            # gui_test.js / evidence_capture.js 全 PASS
    count: <テスト数>            # 画面なしプログラムは 0 で all_passed: true
  all_passed: true              # unit_test.all_passed AND gui_test.all_passed の導出値
  note: ""                      # FAIL 時の説明（FAIL 分類: bug / not_testable / data-issue）
```

## overlay: 変更なしセクション

その他全セクションは v6.0.0 標準の evidence_pack_template.md のまま。
