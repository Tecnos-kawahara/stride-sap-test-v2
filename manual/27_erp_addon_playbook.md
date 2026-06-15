# 27. Tecnos-STRIDE: ERPアドオン向け実行追跡メソッド

> **S**tate-Tracked **R**un **I**ntent-**D**riven **E**ngineering
>
> 「AI と共に前進する（Stride）」- 品質を担保しながら迅速に成果を出す

---

## 1. 概要

### 1.1 Tecnos-STRIDE とは

**Tecnos-STRIDE** は、テクノスジャパンがERP導入の実践知を反映させた独自メソッドです。
既存の SDD（Spec-Driven Development）に「マイクロレベル実行追跡」を追加し、
ERPアドオン開発を安全かつ高速に実行できるようにします。

```
┌─────────────────────────────────────────────────────────────────┐
│  従来の SDD                                                     │
│  ・Spec（仕様）が正本                                           │
│  ・Gate 1-Final でマクロ品質を保証                              │
│  ・しかし「実行中の追跡」が弱い                                 │
├─────────────────────────────────────────────────────────────────┤
│  Tecnos-STRIDE（追加）                                          │
│  ・Work Item 単位で変更を追跡                                   │
│  ・Mode（autopilot/confirm/validate）で儀式量を可変化           │
│  ・State.yaml で進捗を一元管理                                  │
│  ・Ops Pack で本番変更を安全に                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 二層統制モデル

| レイヤー | 統制単位 | 目的 | 成果物 |
|----------|----------|------|--------|
| **Macro** | Gate 1〜Final | 仕様パック・監査パックの品質保証 | basic_design, spec, plan, tasks, evidence |
| **Micro** | Work Item / Run | 変更単位の実行追跡・可変儀式 | WI-*.md, walkthrough, state.yaml |

```
┌─────────────────────────────────────────────────────────────────┐
│  Macro: Gate 1 → Gate 2 → Gate 3 → Gate 4 → Gate 5 → Final     │
│         (Design)  (BPMN)   (Spec)   (Plan)  (Tasks)  (Evidence) │
├─────────────────────────────────────────────────────────────────┤
│  Micro: WI-001 ──► RUN-001 ──► Done                             │
│         WI-002 ──► RUN-001 ──► Done                             │
│         WI-003 ──► RUN-001 ──► (in_progress)                    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 基本原則

| 原則 | 説明 |
|------|------|
| **Spec is canonical** | 仕様（Spec）が契約。実装と食い違う場合は「どちらを直すか」を明示的に決定 |
| **Artifacts = State** | 会話ではなく成果物（Spec/Run/State）が唯一の状態 |
| **AI executes, Human approves (v4.4)** | AI が全作業を自律実行、承認 (A) は必ず人間（APPROVAL.md 編集のみ） |
| **1 WI = 1 Run** | 1つの Work Item は1つの Run で完了（監査単位として追跡可能） |

---

## 2. Work Item（変更単位）

### 2.1 Work Item とは

Work Item（WI）は、Gate 5 以降の「実行単位」です。
Spec の変更を小さく分解し、リスクに応じた承認フローを適用します。

```yaml
# WI-ERP-FEAT-001.md (YAML frontmatter)
wi_id: WI-ERP-FEAT-001
title: "受注登録画面のUI改善"
complexity: low          # low / medium / high
mode: autopilot          # autopilot / confirm / validate
risk_flags: ["ui_only"]  # リスクフラグ
```

### 2.2 Work Item の構成要素

| 要素 | 説明 | 例 |
|------|------|-----|
| **wi_id** | 一意識別子 | `WI-ERP-FEAT-001` |
| **title** | 変更の短い要約 | "受注登録画面のUI改善" |
| **complexity** | 作業規模（記録用） | `low`, `medium`, `high` |
| **mode** | 承認儀式の厳格度 | `autopilot`, `confirm`, `validate` |
| **risk_flags** | リスク分類タグ | `["ui_only"]`, `["authz", "audit_log"]` |
| **spec_refs** | 参照する Spec ファイル | `["basic_design.md", "spec.md"]` |
| **contract_refs** | 紐づく AC/CT | `{acceptance_ids: ["AC-001"]}` |
| **owners** | 責任者 | `{pm: "@tanaka", tech_lead: "@suzuki"}` |

### 2.3 Spec Links と Definition of Done

Work Item 本文には以下を記載します：

```markdown
## Spec Links (Single source of truth)
- UI: specs/feature/ui/order_entry.md
- API: specs/feature/contracts/order_api.yaml
- TEST: specs/feature/tests/scenarios.yaml

## Definition of Done
- [ ] Spec差分レビュー完了
- [ ] 実装完了（影響箇所列挙）
- [ ] テスト追加/更新
- [ ] walkthrough レビュー完了
- [ ] CI合格
- [ ] Ops更新
```

---

## 3. Mode（可変チェックポイント）

### 3.1 3つの Mode

リスクに応じて承認儀式の量を変えます。

| Mode | Pre-Run | Post-Run | 適用条件 |
|------|---------|----------|----------|
| **autopilot** | なし | walkthrough, CI, ops review | 低リスク変更 |
| **confirm** | plan_review | walkthrough, CI, ops review | 中リスク変更 |
| **validate** | design_diff, plan_review | walkthrough, CI, ops review | 高リスク変更 |

> **重要**: 全モードで Post-Run 承認（walkthrough_review, ci_pass, ops_review）が必須です。

### 3.2 Risk Flags と Mode の対応

```yaml
# High risk → validate
- authz           # 権限制御
- sod             # 職務分離
- audit_log       # 監査ログ
- pii             # 個人情報
- accounting_calc # 会計計算
- inventory_valuation  # 在庫評価
- db_schema       # DBスキーマ変更
- data_migration  # データ移行
- update_integration   # 更新系連携
- cross_module    # モジュール横断

# Medium risk → confirm
- new_api         # 新規API
- contract_change # 契約変更
- performance_sensitive  # 性能影響

# Low risk → autopilot
- ui_only         # UI のみ
- message_only    # メッセージのみ
- test_only       # テストのみ
- logging_only    # ログのみ
```

### 3.3 Mode Override

policy より弱い Mode を使う場合は理由を記載します：

```yaml
mode: confirm  # policy では validate だが confirm に
mode_override:
  reason: "既存の権限チェック関数を呼び出すのみで、ロジック変更なし"
```

> `mode_override.reason` がない場合、stride-lint はエラーを出力します。

---

## 4. Run（実行証跡）

### 4.1 Run とは

Run は Work Item の実行証跡です。
**1 WI = 1 Run** のルールに従い、やり直しが必要な場合は新しい WI を作成します。

### 4.2 ディレクトリ構造

```
specs/<feature>/runs/
└── WI-ERP-FEAT-001/
    └── RUN-001/
        ├── walkthrough.md     # 必須: What/Why/How/Evidence
        ├── test_results.md    # standard/critical tier で必須
        └── decision_log.md    # validate mode で推奨
```

### 4.3 Walkthrough の書き方

```markdown
# Walkthrough: WI-ERP-FEAT-001

## What Changed
- 受注登録画面のボタン配置を変更
- 「登録」ボタンを右下に移動
- 確認ダイアログを追加

## Why
- ユーザーからのフィードバックにより、誤操作を防止するため

## How to Verify
1. 受注登録画面を開く
2. 「登録」ボタンが右下にあることを確認
3. 「登録」クリック時に確認ダイアログが表示されることを確認

## Evidence
- Screenshot: [order_entry_new.png]
- Test: TS-UI-001 PASS

## Approval
- [ ] Walkthrough reviewed by TL
- [ ] CI passed
- [ ] Ops reviewed
```

---

## 5. State（単一真実源）

### 5.1 state.yaml

Feature 内の全 WI の進捗を一元管理します。

```yaml
# specs/<feature>/state/state.yaml
# 正統スキーマ (v3.1.0-tecnos-stride)

feature: FEAT-ERP-ORDER-001
current_gate: Gate5
autonomy_bias: balanced    # v3.1: autonomous / balanced / controlled

# work_items: 配列形式（正統）
# 各要素は wi_id, status, mode を持つ dict
work_items:
  - wi_id: WI-ERP-ORDER-001
    status: done
    mode: autopilot
  - wi_id: WI-ERP-ORDER-002
    status: done
    mode: confirm
  - wi_id: WI-ERP-ORDER-003
    status: in_progress
    mode: validate

run_index:
  WI-ERP-ORDER-001: RUN-001
  WI-ERP-ORDER-002: RUN-001
```

> **注意**: `work_items_status` (dict 形式) は非推奨です。
> lint と GitHub Projects 同期は `work_items` 配列形式を使用します。

### 5.2 State の整合性

stride-lint は以下をチェックします：

| チェック | エラーコード |
|----------|-------------|
| WI ファイルが存在するのに state に記載がない | `STATE_WI_MISMATCH` |
| state に記載があるのに WI ファイルがない | `STATE_WI_MISMATCH` |
| WI が done なのに Run がない | `RUN_MISSING` |
| WI に複数の Run がある | `RUN_MULTIPLE` |

---

## 6. Ops Pack（運用パック）

### 6.1 ERP Addon では必須

ERP は本番環境への影響が大きいため、**全ての ERP Addon で Ops Pack が必須**です。

```
specs/<feature>/ops/
├── transport_manifest.yaml   # 輸送マニフェスト
├── release_checklist.md      # リリースチェックリスト
├── rollback_plan.md          # ロールバック計画
└── hypercare_runbook.md      # ハイパーケアランブック
```

### 6.2 各ファイルの内容

#### transport_manifest.yaml
```yaml
transport_id: TR-2026-0001
description: "受注登録機能の改善"
components:
  - type: program
    path: /src/order_entry.py
    action: update
  - type: table
    name: T_ORDER_CONFIG
    action: alter
dependencies:
  - TR-2025-0999  # 前提輸送
rollback_order:
  - revert: T_ORDER_CONFIG
  - redeploy: /src/order_entry.py (previous version)
```

#### release_checklist.md
```markdown
## Pre-Release
- [ ] 全 WI が done
- [ ] CI 全パス
- [ ] Ops レビュー完了
- [ ] 輸送マニフェスト承認

## Release
- [ ] バックアップ取得
- [ ] 輸送実行
- [ ] 動作確認

## Post-Release
- [ ] ハイパーケア開始
- [ ] 監視ダッシュボード確認
```

---

## 7. 典型的なワークフロー

### 7.1 全体フロー

```
1. Gate 1-5 を通過（Macro レベル）
   - basic_design.md, process.bpmn, spec.md, plan.md, tasks.md
   - 各 Gate で人間が APPROVAL.md を承認

2. Work Item 作成（Gate 5 後）
   - tasks.md の各タスクを WI に分解
   - risk_flags を評価し Mode を決定
   - state.yaml を初期化

3. Run 実行（Micro レベル）
   - confirm/validate なら事前承認を取得
   - 実装を実行
   - walkthrough.md を作成
   - Post-run 承認を取得（全モード必須）
   - state.yaml を更新

4. Final Gate
   - 全 WI が done
   - evidence_pack を作成
   - Ops Pack を確認
```

### 7.2 コマンド例

```bash
# 1. Feature 初期化
stride init my_erp_addon
echo "execution_profile: erp_addon" >> specs/my_erp_addon/basic_design.md

# 2. Gate 1-5 を通過
stride lint specs/my_erp_addon/
# → 各 Gate で APPROVAL.md に人間が承認

# 3. Work Item 作成
mkdir -p specs/my_erp_addon/work_items
cp sdd-templates/templates/work_item_template.md \
   specs/my_erp_addon/work_items/WI-ERP-MYADDON-001.md

# 4. State 初期化
mkdir -p specs/my_erp_addon/state
cp sdd-templates/templates/state_template.yaml \
   specs/my_erp_addon/state/state.yaml

# 5. Ops Pack 準備
mkdir -p specs/my_erp_addon/ops
cp sdd-templates/templates/ops/* specs/my_erp_addon/ops/

# 6. Run 作成
mkdir -p specs/my_erp_addon/runs/WI-ERP-MYADDON-001/RUN-001
cp sdd-templates/templates/walkthrough_template.md \
   specs/my_erp_addon/runs/WI-ERP-MYADDON-001/RUN-001/walkthrough.md

# 7. 検証
stride lint specs/my_erp_addon/
# または
python3 sdd-templates/tools/erp_addon_exec_tracking.py specs/my_erp_addon/
```

---

## 8. エラーコード一覧

### 8.1 エラー（ブロッキング）

| Code | Meaning |
|------|---------|
| `WI_DIR_MISSING` | Gate5以降で work_items/ がない |
| `WI_SCHEMA_INVALID` | WI必須項目欠落（wi_id, title, mode, risk_flags, complexity, Spec Links, DoD） |
| `WI_MODE_INVALID` | mode が不正（autopilot/confirm/validate 以外） |
| `WI_RISK_FLAG_INVALID` | risk_flags が taxonomy に存在しない |
| `MODE_OVERRIDE_REASON_MISSING` | policy 推奨より弱い mode を使用し、理由がない |
| `STATE_MISSING` | state.yaml がない |
| `STATE_WI_MISMATCH` | state と WI ファイルが不整合 |
| `RUN_MISSING` | WI done なのに Run がない |
| `RUN_MULTIPLE` | Work Item に複数の Run がある（1 WI = 1 Run 違反） |
| `WALKTHROUGH_MISSING` | walkthrough.md がない |
| `TEST_RESULTS_MISSING` | tier標準以上で test_results がない |
| `WI_APPROVAL_PENDING` | 承認未完（pre-run または post-run） |
| `OPS_PACK_MISSING` | ops pack 不足（4ファイル必須） |
| `AUTOPILOT_FORBIDDEN_BY_TIER` | critical tier で autopilot 不可 |

### 8.2 警告（非ブロッキング）

| Code | Meaning |
|------|---------|
| `WARN_WI_MODE_POLICY_VIOLATION` | policy推奨より弱いmode（理由あり） |
| `WARN_SPEC_LINK_NOT_FOUND` | Spec Links 参照先ファイルが見つからない |
| `WARN_SPEC_REF_NOT_FOUND` | spec_refs 参照先ファイルが見つからない |

---

## 9. Coverage Tier と STRIDE

| Tier | AC Coverage | CT Coverage | Ops Pack | E2E | autopilot |
|------|-------------|-------------|----------|-----|-----------|
| **critical** | 100% | 100% | 必須 | 必須 | 禁止 |
| **standard** | 100% | 80% | 必須 | 任意 | 可能 |
| **experimental** | 80% | 60% | 必須 | 不要 | 可能 |

> **ERP Addon では Tier に関係なく Ops Pack は必須**

---

## 10. ベストプラクティス

### 10.1 WI の分割

- **1つの WI は 1-2 日で完了できる規模**に分割
- **リスクの異なる変更は別の WI**に分ける
- **依存関係がある場合は `dependencies` に明記**

### 10.2 Mode の選択

```
risk_flags に高リスクがある → validate
risk_flags に中リスクがある → confirm
risk_flags が低リスクのみ → autopilot
```

### 10.3 Walkthrough の品質

- **What**: 何を変更したか（ファイル名、行数）
- **Why**: なぜ変更したか（Spec 参照）
- **How to Verify**: どう検証するか（手順）
- **Evidence**: 証跡（スクリーンショット、テスト結果）

---

## 11. Autonomy Bias（適応的 Mode 判定）— v3.1

### 11.1 概要

**Autonomy Bias** は、プロジェクトの自律性嗜好に応じて Mode 判定の閾値を自動的にシフトする仕組みです。
risk_flags から決定された推奨 Mode を、プロジェクトの `autonomy_bias` 設定に基づいて調整します。

### 11.2 3つの Bias レベル

| Bias | 効果 | 適用例 |
|------|------|--------|
| **autonomous** | Mode を1段階緩和（validate→confirm, confirm→autopilot） | PoC・実験的開発、高経験チーム |
| **balanced** | シフトなし（デフォルト） | 通常のプロジェクト |
| **controlled** | Mode を1段階厳格化（autopilot→confirm, confirm→validate） | 本番ERP・監査対象・critical tier |

### 11.3 安全制約

- **上限**: `validate` を超える Mode は存在しない（controlled で validate のまま）
- **下限**: `autopilot` より弱い Mode は存在しない（autonomous で autopilot のまま）
- **Critical Tier 強制**: `coverage_tier: critical` の場合、Bias に関わらず最低 `confirm` が適用
- **mode_override は Bias 後**: Bias 適用後の推奨 Mode をさらにオーバーライドする場合、理由が必要

### 11.4 state.yaml への設定

```yaml
# specs/<feature>/state/state.yaml
feature: FEAT-ERP-ORDER-001
current_gate: Gate5
autonomy_bias: balanced    # ← v3.1 追加: autonomous / balanced / controlled

work_items:
  - wi_id: WI-ERP-ORDER-001
    status: in_progress
    mode: confirm
```

### 11.5 wi_readiness_checker での動作

```bash
python3 sdd-templates/tools/wi_readiness_checker.py specs/my_feature/ WI-ERP-FEAT-001

# 出力例（autonomous bias の場合）:
# recommended_mode: autopilot  (policy: confirm → autonomous bias: autopilot)
# autonomy_bias: autonomous
```

> **注意**: `coverage_tier` は `basic_design.md` の Canonical YAML から読み取られます。
> frontmatter ではなく、`# 0. Canonical Basic Design (YAML)` の ```yaml ブロックに記載してください。

---

## 12. Run Resume Detection（中断再開検出）— v3.1

### 12.1 概要

**Run Resume Detection** は、中断された Run のアーティファクトを検査し、
次に作成すべき成果物を特定する仕組みです。

### 12.2 アーティファクト検査順序

| 順番 | アーティファクト | 存在しない場合の再開ポイント |
|------|-----------------|----------------------------|
| 1 | `walkthrough.md` | 実装完了後、walkthrough を作成 |
| 2 | `test_results.md` | テスト実行から再開 |
| 3 | `decision_log.md` | validate mode の場合、判断記録から再開 |

### 12.3 使い方

```bash
# Run ディレクトリを指定
python3 sdd-templates/tools/run_resume_detector.py specs/my_feature/runs/WI-ERP-FEAT-001/RUN-001/

# 出力例（中断検出時）:
# resume_point: test_results
# existing_artifacts: ["walkthrough.md"]
# missing_artifacts: ["test_results.md"]
# recommendation: "テスト実行から再開してください"
```

### 12.4 よくあるケース

| ケース | 状況 | 推奨アクション |
|--------|------|---------------|
| 全アーティファクトなし | Run 開始直後に中断 | 実装から再開 |
| walkthrough のみ | テスト前に中断 | テスト実行 → test_results 作成 |
| walkthrough + test_results | Post-run 承認前に中断 | 承認依頼から再開 |

---

## 関連ドキュメント

- [Adaptive Execution ガイド](17_adaptive_execution_guide.md) — Autonomy Bias と Run Resume の詳細
- [RACI+ (AI時代の責務分担)](16_raci_plus.md)
- [TEIM/PMO マッピング](28_teim_mapping.md)
- [GitHub Projects 連携ガイド](26_github_projects_guide.md)
- [Enterprise ガイド](04_enterprise_guide.md)
