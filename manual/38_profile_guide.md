# 38. Profile ガイド（報告粒度 + Completeness 閾値の切替）

> **Version:** v5.4.0-tecnos-stride / 最終更新: 2026-04-24
>
> Profile は「Constitution Articles を守りながら、**報告の冗長さと Completeness 閾値**を現場に応じて切り替える」軸です。
>
> **v5.4 で切り替わるのは「報告粒度」と「湖/海判定閾値」の 2 点のみ**。
> BPMN / Evidence / SEC-006 / Ops Pack / Epic-Feature Hierarchy / Coverage Tier 宣言は
> **全 Profile で現行正本のまま** — v5.5 以降で phase/gate 定義の改定として別途起票します。

---

## 38.1 TL;DR — Profile とは何か

同じ STRIDE Constitution を、用途別に「報告の冗長さ」と「Completeness 閾値」だけ変えて適用する軸です。

| 軸 | 対象 | 例 |
|----|------|-----|
| **Mode** (v3+) | WI 単位のチェックポイント量 | autopilot / confirm / validate |
| **Coverage Tier** (v2+) | テスト / Ops Pack / 承認者の重さ | critical / standard / experimental |
| **Profile** (v5.4 新規) | **報告フォーマットと湖/海判定閾値のみ** | enterprise-erp / saas-integration / prototype |

Mode と Coverage Tier はガバナンスの一部を直接動かしますが、Profile は**ガバナンスの定義自体は一切触らず**、報告の冗長さと閾値だけを切り替えます。機械検証（stride-lint + pr-check）は全 Profile で同一です。

---

## 38.2 3 つの Profile — 選び方の判断フロー

```
Q1: この機能は ERP (SAP / mcframe / Salesforce / S4HANA) の本番業務に触れる？
  └ yes → enterprise-erp (default)
  └ no  → Q2 へ

Q2: 連携業務 SaaS / 外部顧客向け API / 規制対象 Event 基盤？
  └ yes → saas-integration
  └ no  → Q3 へ

Q3: 社内 PoC / innovation 推進部 / 使い捨てスクリプト / 短命ツール？
  └ yes → prototype
  └ no  → enterprise-erp (迷ったら default)
```

判断に迷ったら `enterprise-erp` を選ぶのが安全です（最も厚い報告、最大の閾値）。後から Profile を下げることは容易ですが、上げるとそれまでの 1-line レポートを 5-step に書き戻す手間が発生します。

---

## 38.3 Profile ごとの挙動

### enterprise-erp (default)

- **想定**: SAP / mcframe / Salesforce / S4HANA 等 ERP 導入、監査対象案件、既存顧客向け
- **Task Completion Report**: 5-step full report（`sdd_bootstrap.md §5.1`）
- **Completeness 湖判定**: +200 行以内 かつ +5 ファイル以内（AND）
- **判断**: 監査対象のため、AC / NFR / scenarios / lint / pr-check の全 Step を明示的に記載した 5-step report で人間がトレースできるようにする

### saas-integration

- **想定**: 連携業務 SaaS（CBP v3 等）、API / Event 中心、外部連携
- **Task Completion Report**:
  - `basic_design.coverage_tier == "critical"` の WI → 5-step full report
  - それ以外 → 1-line summary
- **Completeness 湖判定**: +150 行以内 かつ +4 ファイル以内（AND）
- **判断**: critical な契約変更は 5-step で厳密に監査し、それ以外の API/Event 変更は 1-line で回転速度を落とさない

### prototype

- **想定**: 社内 PoC、innovation 推進部の小規模ツール、試作コード
- **Task Completion Report**: 1-line summary（`sdd_bootstrap.md §5.2`）
- **Completeness 湖判定**: +100 行以内 かつ +3 ファイル以内（AND）
- **判断**: 実験の回転速度を最大化。ただし機械検証（lint + pr-check）は**省略できない**。「1-line だから省略可」という解釈は禁止

---

## 38.4 切替方法

### CLI で指定（新規 feature）

```bash
stride init my_feature                              # default: enterprise-erp
stride init my_feature --profile saas-integration
stride init my_feature --profile prototype
```

`--profile` を省略すると `enterprise-erp` になります（既存挙動との互換性）。

### `basic_design.md` で宣言（既存 feature）

canonical YAML の `basic_design:` ブロック内に追加：

```yaml
basic_design:
  # Profile (v5.4) — SSoT。state.yaml の profile はキャッシュ
  profile: "saas-integration"   # enterprise-erp | saas-integration | prototype

  # ... 既存の coverage_tier / autonomy_bias / ed_cf_score 等 ...
```

**schema 規約（厳守）:**
- `basic_design.profile` に格納する（`meta.profile` や `workspace.profile` は作らない）
- `state.yaml` の `profile` は flat schema の top-level（`workspace.profile` へのネスト禁止）
- SSoT は `basic_design.md`、`state.yaml` は同期キャッシュ

### 不整合時

`basic_design.md` と `state.yaml` の profile が食い違うと `stride lint` が `PROFILE_MISMATCH` を出します。SSoT は `basic_design.md` 側なので、`state.yaml` の `profile` フィールドを basic_design に合わせて更新してください。

---

## 38.5 切替で変わらないもの（v5.4 重要）

Profile は**下記のいずれも切り替えません**。全 Profile で現行正本のままです。

| 項目 | 正本（canonical_source） |
|------|-----------------------|
| BPMN 必須（process.bpmn / epic_flow.bpmn） | `agent_docs/sdd_bootstrap.md` §4-BPMN |
| Evidence Pack（保持期間・対象ログ） | `memory/tecnos_org_constraints.md` §6.5 + `sdd-templates/templates/ops_template.md` |
| SEC-006 AI Provenance（6 キーワード全記録） | `sdd-templates/tools/stride_security_checker.py` SEC-006 + `memory/tecnos_org_constraints.md` |
| Epic-Feature Hierarchy（Article X） | `memory/constitution.md` |
| Ops Pack（ERP addon 等の required 条件） | `sdd-templates/templates/ops_pack_registry_template.yaml` + `epic_design_template.md` + `manual/` |
| Coverage Tier 宣言 | `sdd-templates/templates/basic_design_template.md`（`basic_design.coverage_tier`） |

これらを Profile で切り替えたい要望が出た場合、phase/gate 定義の改定が必要になるため、v5.5 以降で別タスクとして起票します。

Profile 単体では**ガバナンスの境界**には触れません — あくまで「人間向けレポートの冗長さと、湖/海判定の閾値」のスイッチです。

---

## 38.6 Case Study

### Case A: SAP 導入（O2C 受注フロー）

- Profile: `enterprise-erp`
- Coverage Tier: `critical`
- Mode: `validate`（authz / pii / accounting_calc）
- 報告: 5-step full report、全 AC / NFR / scenarios を明示
- 湖判定: +200 行 / +5 ファイル以内

→ 既存 ERP 案件の運用そのまま。v5.4 以前から挙動は変わらない。

### Case B: CBP v3（連携業務 SaaS）

- Profile: `saas-integration`
- Coverage Tier: `standard`（critical な契約変更のみ `critical`）
- Mode: `confirm`（new_api / contract_change）
- 報告: critical tier の WI のみ 5-step、その他は 1-line
- 湖判定: +150 行 / +4 ファイル以内

→ API/Event の回転を落とさず、契約 Breaking Change だけ厳密に監査。

### Case C: 社内 PoC（innovation 推進部の試作）

- Profile: `prototype`
- Coverage Tier: `experimental`
- Mode: `autopilot`（ui_only / test_only）
- 報告: 全 WI 1-line summary
- 湖判定: +100 行 / +3 ファイル以内

→ 回転速度最大化。**機械検証（lint + pr-check）は省略できない** — report の冗長さだけを削る。

---

## 38.7 よくある誤解

### 誤解 1: 「prototype だから scenarios.yaml の検証をスキップできる」

❌ **禁止**。1-line report は「AC-* 全充足」という 1 行で 5 Step 全ての結果を畳み込んでいるだけです。Step 3（scenarios.yaml の `expected[i]` 検証）と Step 4（`stride lint`）は**全 Profile で必須**。

詳細: `sdd_bootstrap.md §5.3 Blocking rule`

### 誤解 2: 「saas-integration に切り替えたから BPMN は不要」

❌ **禁止**。BPMN 要否は Profile の対象外です。全 Profile で `agent_docs/sdd_bootstrap.md §4-BPMN` の現行ルールに従ってください。

### 誤解 3: 「Profile を切り替えて湖閾値を動かした → それ以外の挙動も変わる」

❌ **違います**。Profile が動かすのは 2 点のみ:
1. Task Completion Report のフォーマット（5-step / 1-line）
2. Completeness 湖判定の行数・ファイル数閾値

Mode / Coverage Tier / BPMN / Evidence / SEC-006 / Ops Pack / Epic-Feature Hierarchy / tier_mode_minimum は**一切動きません**。

### 誤解 4: 「Profile を 1-line に変えたから `stride pr-check --summary-line` の出力に task ID が入る」

❌ **違います**。`--summary-line` は project-level の 1 行サマリ（7 base checks + optional mutation）だけを出します。task ID / AC / NFR / scenarios は**責務境界外**で、AI が `bootstrap §5 Step 1-5` の結果から合成します。

詳細: `sdd_bootstrap.md §5.2` の分解テーブル

---

## 38.7-bis VALUE Upstream Extension Profile 適用ガイド (v6.0 Phase D 追加)

VALUE Upstream Extension v6.0 (BABOK v3 + Layered Requirements Modeling + value-driven discovery method 統合の Phase 0 拡張) を 3 profile それぞれに適用する実践 playbook が `manual/48-50` に揃いました (Phase D, FEAT-VALD01)。

- `manual/48_enterprise_erp_value_playbook.md`: ERP/SAP/SCM/CRM 案件向け、BACCM 6 軸 100% 必須・iteration 3 段階完走・KA8 稼働後評価必須
- `manual/49_saas_integration_value_playbook.md`: SaaS API 連携・公開 API・規制対象 Event 基盤向け、API 契約整合を強調
- `manual/50_prototype_value_playbook.md`: 社内 PoC・短命ツール向け、Discovery lite + Elicit/Context Modelling optional

既存 v5.x プロジェクトを v6.0 仕様にアップグレードする手順は `manual/migration/v54_to_v60.md` を参照。`upstream_migration_helper.py` (Phase D で導入) で basic_design.md から Phase 0 yaml seed を半自動生成できます。

詳細は各 playbook 章末の Attributions も参照してください (BABOK / Layered Requirements Modeling / value-driven discovery method)。

---

## 38.8 v5.5+ でのさらなる切替候補（informational only）

v5.4 では触らなかった以下の項目を、v5.5+ で Profile 切替対象とする提案が出ています（要件未確定、実装未着手）:

- BPMN の必要性（prototype での緩和案）
- Evidence Pack の保持期間（prototype での短縮案）
- SEC-006 Provenance の記録キーワード数（prototype での簡略化案）
- Ops Pack の required 条件（saas-integration / prototype での任意化案）

いずれも phase/gate 定義の改定を伴うため、個別タスクとして切り出して設計・承認を経てから導入します。**v5.4 では現行正本のまま**です。

---

## 38.9 参照

- `shared/policies/profile_policy.yaml` — Profile 定義と invariants_across_profiles の SSoT
- `agent_docs/sdd_bootstrap.md` §4b / §5 — Completeness Principle と Task Completion Report
- `SDD_MANIFESTO.md` — Profile-aware Completeness Principle
- `sdd-templates/templates/basic_design_template.md` — `basic_design.profile` の canonical 位置
- `sdd-templates/templates/state_template.yaml` — top-level `profile` フィールド
- `sdd-templates/tools/stride_lint.py` — `PROFILE_UNKNOWN` / `PROFILE_MISMATCH` / `PROFILE_MISSING`
- `sdd-templates/tools/pr_readiness_checker.py` — `--summary-line` 実装
- `tests/test_profile_policy.py` — 20 tests（policy / schema / CLI `--profile` が basic_design.profile と state.yaml top-level profile の両方を同期することの検証 / 再実行時の work_items 保持 / pre-v5.4 state.yaml upgrade / stride-lint PROFILE_* 検出）
