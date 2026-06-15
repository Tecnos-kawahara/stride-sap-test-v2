# Harness Maturity Guide (v5.1.0)

Tecnos-STRIDE v5.1.0 では、Martin Fowler の **Test Harness** 思想を参考に、  
単なる「テストが通る」を超えた「品質を継続的に維持する仕組み（ハーネス）」を導入します。

---

## 1. Fowler 記事の要点

Fowler は [Test Coverage](https://martinfowler.com/bliki/TestCoverage.html) で以下を強調しています：

- カバレッジ数値は **結果**であって **目標**ではない
- 大事なのは「テストが書かれていないリスク領域」を見つけること
- ハーネスは feedforward（予防）と feedback（事後検出）の両輪で機能する

Tecnos-STRIDE はこれを SDD のフェーズゲートと統合します。

---

## 2. このリポジトリでの対応

### 2.1 Feedforward（事前予防）

| 機能 | コマンド | トリガー条件（machine-checkable） |
|------|---------|----------------------------------|
| **SDD Lint** | `stride lint specs/<feature>/` | Phase 内のファイル作成/編集完了後、自動実行（最大 5 回の自動修正ループまで） |
| **Semantic Gate** | `stride evaluate specs/<feature>/ --phase <phase>` | Gate 承認依頼の直前に 1 回実行 |
| **Self-Review Loop** | `stride evaluate ... --review` | 初回 evaluate の primary score が **[70, 85)** のときのみ自動起動、内部 max_iters=3 |
| **Phase Gate Hook** | `.claude/settings.json` PreToolUse | Write/Edit ツール実行前（harness 設定不要、既定で有効） |
| **Security Audit (daily)** | `stride security specs/<feature>/ --daily` | WI 開始前（mode ≠ autopilot のとき）。confidence ≥ 8/10 のみ報告 |

### 2.2 Feedback（事後検出）

| 機能 | コマンド | トリガー条件（machine-checkable） |
|------|---------|----------------------------------|
| **PR Readiness** | `stride pr-check <project_root>` | Final Gate 承認依頼前に 1 回、NOT_READY なら自動修正（最大 3 回） |
| **Spec Drift** | `stride pr-check` に含む（内部で spec_drift_detector.py 呼出） | critical > 0 で PR_READY=false |
| **Mutation Testing** | `stride pr-check --mutation` | opt-in。`MUTATION_THRESHOLD` env（既定 80）を下回ると FAIL |
| **Retro** | `stride retro specs/<feature>/` | WI 完了後（state.yaml の status=done 直後）に 1 回 |

### 2.3 Runtime Sensors（継続監視）

| センサー | コマンド | 検出内容 / 閾値 |
|---------|---------|---------------|
| **Dead Code** | `stride health <project_root> --runtime` | pylint W0611/W0612/W0613/W0614（未使用 import / 未使用変数 / 未使用 args / wildcard import） |
| **Coverage Decay** | `stride health <project_root> --runtime` | `.coverage_baseline` 比で低下 > `COVERAGE_DECAY_THRESHOLD_PCT`（既定 5.0%）で WARN |
| **Harness Report** | `stride harness-report <project_root> [--json]` | 8 controls の coverage_pct、FULL / gaps 一覧（FULL 条件: 8 controls 全配置（hooks/ vs tools/ の所在区別あり）∧ tests/ 配下に test_*.py ∧ .github/workflows/*.yml 存在、3条件 AND） |

### 2.4 Janitor Proposals（技術的負債の自動提案）

Symphony Orchestrator が `mode:autopilot + tier:starter` の Issue を定期スキャンし、  
リスクフラグのない低影響エリアに対して **GitHub Issue でのクリーンアップ提案** を生成します。

- 自動 PR は発行しない（安全設計）
- 対象: `mode:autopilot`, `tier:starter` かつリスクフラグなし
- 除外: `risk:authz`, `risk:pii`, `risk:external_api`, `risk:sod`
- 直近 PR があれば除外（`exclude_recent_pr_days` = 7日）

設定: `SYMPHONY.md` の `janitor:` セクション参照。

**手動実行 (v5.1 — CLI 統合):**

```bash
stride symphony janitor            # 1回だけスキャンして Issue 提案を生成
stride symphony janitor --dry-run  # 設定とスコープを表示（GitHub API 呼出なし）
```

`janitor.enabled=false` の場合は "skipped" を出力して exit 0 で終了します。
`stride symphony run` のポーリングループは同じ内部スキャンを `interval_hours`
間隔で呼び出すため、CLI 実行と自動実行でロジックは完全に共有されます。

---

## 3. Scale 別の運用差

| 項目 | starter | standard | enterprise |
|------|---------|----------|-----------|
| Semantic Gate | スキップ（コスト最適化）| 全 Phase | 全 Phase |
| Self-Review Loop | 無効 | `--review` opt-in | `--review` opt-in |
| Mutation Testing | 無効 | `--mutation` opt-in | `--mutation` opt-in |
| Runtime Sensors | 手動のみ | CI 統合 推奨 | CI 統合 必須 |
| Janitor Proposals | **対象**（autopilot + starter scope の唯一の対象）| 対象外 | 対象外 |
| Coverage Decay Alert | 任意 | 推奨 | 必須 |

---

## 4. クイックリファレンス

```bash
# Feedforward
stride lint specs/<feature>/
stride evaluate specs/<feature>/ --phase design
stride evaluate specs/<feature>/ --phase design --review  # borderline 時

# Feedback
stride pr-check .                    # 7チェック標準
stride pr-check . --mutation         # + mutation testing (opt-in)

# Runtime Sensors
stride health . --runtime --json     # dead code + coverage decay
stride harness-report . --json       # controls/gaps サマリ

# Security
stride security specs/<feature>/ --daily
```

---

## 5. 関連ドキュメント

- `manual/22_pr_readiness_guide.md` — PR Readiness Checker 詳細
- `manual/32_multi_model_evaluator_guide.md` — Semantic Gate 詳細
- `manual/34_security_audit_guide.md` — Security Audit 詳細
- `manual/35_retro_guide.md` — Retro ガイド
- `manual/36_harness_guide.md` — Harness Maturity マニュアル（エンドユーザー向け）
- `SYMPHONY.md` — Janitor 設定
