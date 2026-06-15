# ERPアドオン向け lint 追加仕様（v1.0, Patch Proposal）

## 0. 目的
既存の **Gate 1〜Final（APPROVAL.md / phase_gate.py / speckit-lint）** を温存したまま、
ERPアドオン版で追加した **Run/State/Mode（FIRE相当）** と **coverage tier** を “機械検証” する。

狙い：
- Gate5以降は「tasksがある」だけでなく **Work Item（変更単位）** が定義されている
- 変更ごとに **Mode（autopilot/confirm/validate）** が付与され、リスクに応じた儀式量になる
- 実行の証跡（Run/Walkthrough/CI結果）が残り、statelessなAIでも継続実行できる
- coverage tier（critical/standard/experimental）に応じて、必要な証跡と承認を強制する

---

## 1. 対象範囲（いつlintが発動するか）
推奨の発動条件（段階導入を壊さない）：
- `specs/<feature>/work_items/` が存在する（= ERPアドオン実行追跡を採用）
  もしくは `basic_design.md` YAMLに `execution_profile: erp_addon`
- かつ Gate5以降（`APPROVAL.md`でGate5が進行/承認済み、または tasks.md が存在）

---

## 2. 追加する成果物（最低限）
### 2.1 Work Item（変更単位）
- `specs/<feature>/work_items/WI-*.md`（YAML front matter必須）
- `specs/<feature>/work_items/WI-*.approval.md`（confirm/validateで必須）

### 2.2 Run（実行ログ）
- `specs/<feature>/runs/<wi_id>/RUN-*/walkthrough.md`
- `specs/<feature>/runs/<wi_id>/RUN-*/test_results.md`（tier=critical/standardで必須）
- `specs/<feature>/runs/<wi_id>/RUN-*/decision_log.md`（validate推奨）

### 2.3 State（単一真実）
- `specs/<feature>/state/state.yaml`（WI status / mode / dependencies / run_index）

### 2.4 Policy（Modeとリスク分類）
- `memory/erp_addon_mode_policy.yaml`
- `memory/erp_addon_risk_taxonomy.yaml`

---

## 3. 追加エラーコード（現行体系に合わせる）
| Error Code | 意味 | Fix（最短） |
|---|---|---|
| WI_DIR_MISSING | Gate5以降なのに work_items/ が無い | work_items/ を作り WI を定義 |
| WI_SCHEMA_INVALID | WI必須項目欠落 | YAMLを補完 |
| WI_MODE_INVALID | modeが不正 | autopilot/confirm/validateに修正 |
| WI_RISK_FLAG_INVALID | risk_flagsが不正 | taxonomyに合わせて修正 |
| WI_MODE_POLICY_VIOLATION | policy上必要なmodeより弱い | mode引上げ or override理由＋承認 |
| MODE_OVERRIDE_REASON_MISSING | overrideしたが理由が無い | mode_override.reason を追加 |
| WI_DEPENDENCY_CYCLE | WI依存が循環 | cycle解消 |
| STATE_MISSING | state.yaml が無い | state/state.yaml 作成 |
| STATE_WI_MISMATCH | stateとWI実体が不整合 | state更新 |
| RUN_MISSING | WIがdoneなのにRunが無い | RUN作成しwalkthrough残す |
| WALKTHROUGH_MISSING | walkthrough.mdが無い | walkthrough作成 |
| TEST_RESULTS_MISSING | tier標準以上でtest_results.mdが無い | CI要点を記載 |
| WI_APPROVAL_PENDING | confirm/validate承認が未完 | WI approvalのチェック完了 |
| OPS_PACK_MISSING | validate/criticalでops成果物不足 | ops/を補完 |
| AUTOPILOT_FORBIDDEN_BY_TIER | criticalでautopilot許容外 | mode変更 |

---

## 4. 追加lintルール（要件）
### 4.1 Gate5で落とす
- tasks.md YAMLの `work_items:` と WIファイルが一致
- WIの mode/risk_flags が policy/taxonomyに整合
- state.yaml が存在し、WI一覧・依存が揃っている

### 4.2 Runで落とす
- state.yaml 上で `status: done` のWIは、少なくとも1つのRUNがある
- RUNには walkthrough がある
- tier=critical/standard は test_results が必須
- validate or tier=critical は ops pack を必須

### 4.3 承認票で落とす
- confirm/validate のWIは `WI-*.approval.md` が存在
- confirm: plan_review 完了
- validate: design_diff_review + plan_review 完了

### 4.4 coverage tier 連動
- critical: autopilotは低リスクに限定、ops pack必須
- standard: validate時のみops pack必須
- experimental: ops pack任意（ただしRun/Stateは維持）

---

## 5. 実装ポイント（speckit-lint）
- `validate_erp_addon_execution_tracking(feature_path, approval_status, coverage_tier)` を追加
- `validate_feature()` の末尾（Gate5以降判定後）で呼び出す
- 既存 `parse_approval_md()` を流用して WI approval を解析（checkbox形式）

---

## 6. 最小テスト
- Gate4まで：従来通過
- Gate5＋WIあり：schema/mode/stateで検出
- done＋RUNなし：RUN_MISSING
- critical＋autopilot違反：AUTOPILOT_FORBIDDEN_BY_TIER
- validate＋ops不足：OPS_PACK_MISSING
