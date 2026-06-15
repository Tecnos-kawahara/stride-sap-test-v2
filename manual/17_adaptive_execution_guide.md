# 17. Adaptive Execution ガイド

> **Version**: v5.4.0-tecnos-stride
> **対象**: Autonomy Bias と Run Resume Detection を活用する開発者・PM

> **v4.4 Note**: v4.4 で導入された **AI Autonomous Execution**（AI自律実行モデル）により、
> Claude Code が全作業を自律実行し、人間は承認のみ行うモデルに移行しました。
> Autonomy Bias は引き続き有効ですが、v4.4 では AI が Phase 内を連続実行するため、
> Mode 判定の主な影響は WI 実行時の承認粒度（Pre-run / Post-run）に集中します。
> 詳細: [AI自律実行ガイド (v4.4)](15_ai_autonomous_execution_guide.md)

---

## 22.1 概要

v3.1 で導入された **Adaptive Execution**（適応的実行）は、以下の2つの仕組みで構成されます：

| 機能 | 目的 | 効果 |
|------|------|------|
| **Autonomy Bias** | プロジェクトの自律性嗜好に応じて Mode 判定を自動調整 | チーム特性に合った承認儀式量の最適化 |
| **Run Resume Detection** | 中断された Run の再開ポイントを自動検出 | コンテキスト復旧の高速化、作業の無駄排除 |

### Profile (v5.4) — 姉妹概念として

v5.4 で追加された **Profile**（`enterprise-erp` / `saas-integration` / `prototype`）は、
Mode / Autonomy Bias と**相補的な切替軸**です。3 軸の関係:

| 軸 | 動かすもの | 例 |
|----|------------|-----|
| **Mode** (autopilot/confirm/validate) | WI 単位の**チェックポイント量**（Pre-run / Post-run） | validate = design_diff + plan_review 追加 |
| **Autonomy Bias** (autonomous/balanced/controlled) | Mode を risk_flags から自動シフトする方向 | autonomous = 1段階緩和 |
| **Profile** (enterprise-erp/saas-integration/prototype) | **報告粒度** + **Completeness 湖/海判定閾値** のみ | prototype = 1-line report、100行/3ファイル |

**重要:** Profile は Mode も Autonomy Bias も**一切動かしません**。Profile が切り替えるのは人間向けレポートの冗長さと湖/海閾値だけ。Mode のチェックポイント量や Bias 補正は従来どおり。

詳細: [38. Profile ガイド](38_profile_guide.md)

---

## 22.2 Autonomy Bias System

### Bias の仕組み

risk_flags から決定された推奨 Mode を、プロジェクトの `autonomy_bias` 設定に基づいてシフトします。

```
risk_flags → Policy Mode → Autonomy Bias 適用 → 最終推奨 Mode
                              ↓
                    state.yaml の autonomy_bias を参照
```

### 3つの Bias レベル

| Bias | シフト方向 | 例（policy=confirm） |
|------|-----------|---------------------|
| **autonomous** | 1段階緩和 | confirm → **autopilot** |
| **balanced** | シフトなし | confirm → **confirm** |
| **controlled** | 1段階厳格化 | confirm → **validate** |

### Mode シフト表

| Policy Mode | autonomous | balanced | controlled |
|-------------|-----------|----------|------------|
| autopilot | autopilot | autopilot | **confirm** |
| confirm | **autopilot** | confirm | **validate** |
| validate | **confirm** | validate | validate |

### 安全制約

1. **Mode 上限/下限**: validate を超えない、autopilot を下回らない
2. **Critical Tier 最低保証**: `coverage_tier: critical` の場合、Bias に関わらず最低 `confirm`
3. **mode_override は Bias 後に適用**: オーバーライドする場合は理由が必須

### 設定方法

`state.yaml` に `autonomy_bias` フィールドを追加します：

```yaml
# specs/<feature>/state/state.yaml
feature: FEAT-ERP-ORDER-001
current_gate: Gate5
autonomy_bias: balanced    # autonomous / balanced / controlled

work_items:
  - wi_id: WI-ERP-ORDER-001
    status: in_progress
    mode: confirm
```

### coverage_tier の読み取り

`coverage_tier` は `basic_design.md` の **Canonical YAML**（`# 0. Canonical Basic Design (YAML)` の ```yaml ブロック）から読み取られます。

```yaml
# basic_design.md 内の Canonical YAML
basic_design:
  feature_id: "FEAT-ERP-ORDER-001"
  coverage_tier: critical    # ← ここから読み取り
```

> frontmatter (`---` ブロック) ではなく Canonical YAML が優先されます。

---

## 22.3 Run Resume Detection

### 仕組み

Run ディレクトリ内のアーティファクトの存在を検査し、中断ポイントと次のアクションを特定します。

### アーティファクト検査順序

| 順番 | アーティファクト | 役割 |
|------|-----------------|------|
| 1 | `walkthrough.md` | 変更の What/Why/How/Evidence |
| 2 | `test_results.md` | テスト実行結果（standard/critical tier で必須） |
| 3 | `decision_log.md` | 判断記録（validate mode で推奨） |

### 再開ポイント判定ロジック

```
Run ディレクトリを検査:
├── アーティファクトなし → 「実装から開始」
├── walkthrough.md のみ → 「テスト実行から再開」
├── walkthrough.md + test_results.md → 「Post-run 承認から再開」
└── 全アーティファクトあり → 「Run 完了済み」
```

### 使い方

```bash
# Run ディレクトリを指定して検出
python3 sdd-templates/tools/run_resume_detector.py \
  specs/my_feature/runs/WI-ERP-FEAT-001/RUN-001/
```

### 出力例

```
=== Run Resume Detection ===
Run directory: specs/my_feature/runs/WI-ERP-FEAT-001/RUN-001/
Existing artifacts: walkthrough.md
Missing artifacts: test_results.md, decision_log.md
Resume point: test_results
Recommendation: テスト実行から再開してください
```

---

## 22.4 ツールリファレンス

### wi_readiness_checker.py

```bash
# 基本
python3 sdd-templates/tools/wi_readiness_checker.py specs/<feature>/ <WI-ID>

# 詳細出力
python3 sdd-templates/tools/wi_readiness_checker.py specs/<feature>/ <WI-ID> --verbose

# セルフテスト（17テスト）
python3 sdd-templates/tools/wi_readiness_checker.py --test
```

**v3.1 での変更点**:
- `state.yaml` の `autonomy_bias` を読み取り、推奨 Mode をシフト
- `basic_design.md` の Canonical YAML から `coverage_tier` を読み取り
- `coverage_tier: critical` の場合、最低 `confirm` を強制
- coverage_tier の大文字/小文字・空白を正規化

### run_resume_detector.py

```bash
# 基本
python3 sdd-templates/tools/run_resume_detector.py specs/<feature>/runs/<WI-ID>/RUN-NNN/

# セルフテスト（6テスト）
python3 sdd-templates/tools/run_resume_detector.py --test
```

### erp_addon_exec_tracking.py

```bash
# 基本
python3 sdd-templates/tools/erp_addon_exec_tracking.py specs/<feature>/

# セルフテスト
python3 sdd-templates/tools/erp_addon_exec_tracking.py --test
```

---

## 22.5 Policy 設定

Autonomy Bias のシフトルールは `shared/policies/mode_policy.yaml` の `autonomy_bias` セクションで定義されています。

```yaml
# shared/policies/mode_policy.yaml (抜粋)
autonomy_bias:
  description: "Project-level autonomy preference that shifts Mode thresholds"
  levels:
    autonomous:
      shift: -1
      description: "Reduce ceremony — 1 step less strict"
    balanced:
      shift: 0
      description: "No shift — follow policy as-is"
    controlled:
      shift: +1
      description: "Increase ceremony — 1 step more strict"
  tier_mode_minimum:
    critical: confirm
    standard: autopilot
    experimental: autopilot
```

---

## 22.6 よくある質問

**Q: autonomous bias を設定しても critical tier で autopilot にならないのは？**
A: `tier_mode_minimum` により、critical tier では最低 `confirm` が強制されます。これは安全制約であり、Bias では緩和できません。

**Q: coverage_tier の "Critical"（大文字）と "critical"（小文字）は同じ？**
A: はい。v3.1 で大文字/小文字の正規化が追加されました。未知の値は `standard` にフォールバックします。

**Q: balanced は設定しなくてもよい？**
A: `autonomy_bias` フィールドが未設定の場合、`balanced`（シフトなし）がデフォルトです。

**Q: Run Resume は validate mode でのみ使う？**
A: いいえ。全 Mode で使用できます。ただし `decision_log.md` は validate mode でのみ推奨されるため、他の Mode では検出対象外になることがあります。

---

## Execution Authority Declaration (v4.6.0)

mode_policy.yaml の `execution_authority` セクションで、AIの権限スコープが3層（conversational / gated / prohibited）に宣言されています。

- autopilot/confirm/validate の3モードは、**検証スコープ**（ツール→ワークフロー→ドメイン）の段階に対応します
- これは Cook et al. (2026) の「検証スコープスペクトラム」に基づく設計です
- 詳細: `shared/policies/mode_policy.yaml` の `execution_authority` セクション
- 原則: `memory/constitution.md` Article XIV「Execution Authority Separation」

### wi_readiness_checker の Check 8

v4.6.0 で追加された Check 8（Execution Authority）は、`execution_authority` が宣言されているポリシーに対して、WI の mode が検証スコープを満たしているかを検証します:

- **判定ロジック:** Check 3 と同じ `_get_recommended_mode()` + `_apply_autonomy_bias()` を使用し、`risk_flag_mapping` と `tier_mode_minimum` からポリシー駆動で推奨 mode を算出
- **FAIL条件:** WI の mode が推奨 mode を下回り、かつ `mode_override.reason` が未指定の場合
- **WARN条件:** mode が推奨を下回るが、`mode_override.reason` が指定されている場合
- **PASS条件:** mode が推奨以上、または `execution_authority` が未宣言（レガシーポリシー）
- Check 3 との違い: Check 3 は純粋なポリシー準拠、Check 8 は execution_authority 宣言の文脈で検証スコープの整合性を報告する

---

## 関連ドキュメント

- [Tecnos-STRIDE Playbook](27_erp_addon_playbook.md) — STRIDE の全体概要
- [マルチチームガイド](24_multi_team_guide.md) — ツールリファレンス
- [Coverage Policy](19_coverage_policy.md) — Tier による品質要求の違い
