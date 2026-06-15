# 34. Security Audit ガイド

> **対象**: セキュリティチェックを自動化したい開発者・PM
> **所要時間**: 約10分
> **バージョン**: v4.9.0

---

## 5分クイックリファレンス（PM向け）

**v4.9 で何が変わったか**:
- `stride security` コマンドで Feature のセキュリティ状態を **10 チェック** で自動監査
- `--daily`（軽量・Gate 前）と `--audit`（包括・Final 前）の **2 段階スキャン**
- OpenAPI / authz / secrets / LLM trust boundary / SoD / ERP 直接書き込みまでカバー

**PM が確認すべきこと**:
- `SECURE` / `NOT_SECURE` の判定結果
- `FAIL` のチェック ID と severity

---

## 1. 概要

### 1.1 なぜ Security Audit が必要か

SDD では仕様が契約ですが、セキュリティ観点の検証は `stride-lint` のスコープ外でした。
v4.9 の `stride security` は、canonical YAML・OpenAPI 契約・ファイル内容を解析し、
セキュリティ上の漏れを **機械的に検出** します。

### 1.2 gstack からの着想

gstack（garrytan/gstack, MIT License）の `/cso` コマンドが持つ daily/comprehensive 二段階スキャンの考え方を取り込みました。

---

## 2. 使い方

### 2.1 daily モード（Gate 前の日常チェック）

```bash
stride security specs/<feature>/ --daily
```

confidence >= 8/10 の高確度チェックのみ実行（5 チェック）。
Design/Specify/Tasking の各 Gate 承認依頼前に実行することを推奨します。

### 2.2 audit モード（Final 前の包括チェック）

```bash
stride security specs/<feature>/ --audit
```

confidence >= 2/10 の全チェックを実行（10 チェック）。
Final Gate 前、または PR 作成前に実行します。

### 2.3 JSON 出力（CI/CD 連携）

```bash
stride security specs/<feature>/ --daily --json
```

### 2.4 セルフテスト

```bash
stride security --test    # 8 テスト実行
```

---

## 3. チェック項目一覧

### daily モード（confidence >= 8）

| ID | チェック | severity | confidence |
|----|---------|----------|------------|
| SEC-001 | OpenAPI に securitySchemes / security 宣言があるか | HIGH | 9 |
| SEC-002 | security タグ付き AC に authz_matrix 成果物があるか | HIGH | 9 |
| SEC-003 | `requirements.security_privacy` が定義されているか | HIGH | 10 |
| SEC-004 | ファイルにハードコードされたシークレットがないか | CRITICAL | 10 |
| SEC-005 | 監査ログ・Correlation ID・冪等性の言及があるか | MEDIUM | 8 |

### audit モード追加（confidence < 8）

| ID | チェック | severity | confidence |
|----|---------|----------|------------|
| SEC-006 | AI/LLM 統合時に trust boundary 4 観点が定義されているか | HIGH | 7 |
| SEC-007 | authz_matrix に SoD（職務分掌）定義があるか | MEDIUM | 6 |
| SEC-008 | データ分類と保持期間が定義されているか | LOW | 5 |
| SEC-009 | org_constraints_ref の参照があるか | MEDIUM | 4 |
| SEC-010 | 外部 ERP への直接 DB 書き込みがないか | CRITICAL | 3 |

### FAIL / WARN の判定

- `CRITICAL` / `HIGH` → **FAIL**
- `MEDIUM` / `LOW` → **WARN**
- FAIL が 1 件でもあれば `NOT_SECURE`（exit 1）

---

## 4. SEC-006: LLM Trust Boundary の詳細

AI/LLM を機能仕様として統合する Feature では、以下の **4 観点すべて** が仕様に記載されている必要があります：

| 観点 | 説明 | 検索キーワード例 |
|------|------|----------------|
| **boundary** | trusted / untrusted の境界定義 | `trusted`, `untrusted`, `trust boundary` |
| **input_validation** | 入力のサニタイズ・分離 | `input validation`, `input_validation` |
| **output_verification** | LLM 出力の検証 | `output verification`, `output_verification` |
| **fallback** | 人間エスカレーション | `fallback`, `human escalation` |

1 観点でも欠けていれば FAIL になります。

> **注意**: Evidence Pack の provenance 記録（`record_model_id`, `record_execution_settings` 等）だけでは AI 統合とみなしません。
> 実際に LLM / AI agent の出力が業務フローに関与する場合のみ SEC-006 が評価されます。

詳細: `agent_docs/security.md` セクション 6

### 4.1 Anthropic 利用時の運用補足

- セキュリティ調査・脆弱性再現を Anthropic surface で行う場合、cyber safeguards による遮断を前提にする
- Evidence Pack には `cyber_safeguards_reviewed` と `cvp_status` を残す
- provider 経路によって CVP の可否が変わるため、blocked の切り分けでは model だけでなく provider target も確認する

---

## 5. SEC-010: ERP 直接書き込みガード

外部 ERP（mcframe, SAP 等）の system-of-record への直接 DB 書き込みを検出します。

- **検出対象**: `INSERT INTO erp.table`, `UPDATE mcframe.master`, `direct db write to ...`
- **除外対象**: Feature 所有の addon テーブル（`erp_addon_buffer`, `mcframe_ext_log` 等）

addon テーブルかどうかは命名で判定します（`erp_` / `mcframe_` の直後に `_` が続く場合は addon と見なし除外）。

---

## 6. 出力例

```
=== STRIDE Security Check: daily ===
Feature: specs/my_feature/
Checks: 5 | PASS: 3 | FAIL: 1 | WARN: 1

FAIL  SEC-001 [HIGH conf:9/10] OpenAPI に securitySchemes / security 宣言が未定義
WARN  SEC-005 [MED  conf:8/10] 監査・相関ID・冪等性の記述が不足
PASS  SEC-002 security tagged AC に authz_matrix 定義あり
PASS  SEC-003 requirements.security_privacy あり
PASS  SEC-004 ハードコードされたシークレットなし

Result: NOT_SECURE (exit 1)
```

---

## 7. ワークフロー統合

### 推奨タイミング

| タイミング | モード | 理由 |
|-----------|--------|------|
| Gate 1,2 承認前 | `--daily` | Design 段階でセキュリティ要件の漏れを早期検出 |
| Gate 3,4 承認前 | `--daily` | Spec/Plan の OpenAPI 契約にセキュリティ宣言があるか確認 |
| Final Gate 前 | `--audit` | 全 10 チェックで包括的に監査 |
| PR 作成前 | `--audit` | `stride pr-check` と合わせて実行 |

### Exit codes

| コード | 意味 |
|--------|------|
| 0 | `SECURE` — FAIL なし |
| 1 | `NOT_SECURE` — FAIL あり |
| 2 | `ERROR` — 引数不正、YAML パース不可 |

---

## 8. テスト

セルフテスト 8 件 + integration テスト 13 件:

```bash
stride security --test                                          # セルフテスト
python3 -m pytest tests/test_security_checker_integration.py -v # integration テスト
```

---

> **Inspired by**: gstack /cso two-tier scan (garrytan/gstack, MIT License)
