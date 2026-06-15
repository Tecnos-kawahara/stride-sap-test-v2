# Test Results: WI-ERP-SAMPLE-001 / RUN-001

Run date: 2026-02-10 09:30 JST
Environment: CI (GitHub Actions ubuntu-latest)

## Summary
| Metric | Value |
|--------|-------|
| Total tests | 50 |
| Passed | 50 |
| Failed | 0 |
| Skipped | 0 |
| Duration | 32s |
| Coverage | 83.6% |

## Test Suite Results

### TS-E2E-01: 受注登録E2Eスモーク (NEW)
| # | Test | Result | Duration |
|---|------|--------|----------|
| 1 | 確認ダイアログが表示される | PASS | 2.1s |
| 2 | OK で受注が保存される | PASS | 3.4s |
| 3 | キャンセルで入力画面に戻る | PASS | 1.8s |

### TS-CON-01: 受注登録API契約 (既存)
All 8 tests PASS

### TS-CON-02: mcframe在庫引当契約 (既存)
All 5 tests PASS

### TS-INT-01: 受注登録統合 (既存)
All 12 tests PASS

### TS-INT-02: mcframe連携統合 (既存)
All 6 tests PASS

### TS-INT-03: 承認フロー (既存)
All 9 tests PASS

### TS-INT-04: 監査ログ (既存)
All 7 tests PASS

## Coverage Detail
```
Name                          Stmts   Miss  Cover
--------------------------------------------------
src/domain/order.py              87      8   91%
src/domain/approval.py           63      7   89%
src/api/routes/orders.py        124     26   79%
src/api/routes/auth.py           45      5   89%
src/infra/mcframe_client.py      56      7   88%
src/infra/audit_logger.py        34      4   88%
--------------------------------------------------
TOTAL                           409     57   86%
```
