# 18. Execution Governance ガイド

> **対象**: Auto-Continue / Mandatory Output Rules / DDD / ADR Index を運用する開発者・PM
> **所要時間**: 約10分

> **v4.4 Note**: v4.4 の **AI Autonomous Execution** により、Auto-Continue は
> Claude Code が**デフォルトで自動実行**するようになりました。
> 人間が `stride auto-continue` を手動実行する必要はありません。
> Claude Code は Phase 内のステップを連続実行し、Gate でのみ停止して承認を依頼します。
> 詳細: [AI自律実行ガイド (v4.4)](15_ai_autonomous_execution_guide.md)

---

## 5分クイックリファレンス（PM向け）

**v4.1 で何が変わったか**:
- Phase 内の小ステップが自動連続実行され、承認が必要なポイント（Gate）でのみ停止
- AI 出力フォーマットが標準化され、ツールやターミナル環境に依存しなくなった
- 高複雑度の WI で DDD（Domain-Driven Design）をオプション採用可能に
- 設計判断を ADR（Architecture Decision Record）として横断管理

**v4.4 での追加変更**:
- Auto-Continue は Claude Code が**自動実行**（人間が手動で呼ぶ必要なし）
- lint エラーは Claude Code が**自動修正**（APPROVAL_PENDING 以外）
- Feature ライフサイクル全体を AI が自律的に駆動

**PM が確認すべきこと**:
1. Gate で Claude Code が正しく停止しているか
2. `validate` mode の WI で DDD ステージが実施されているか（該当する場合）
3. ADR が `shared/decisions/` に蓄積されているか

---

## 23.1 Auto-Continue

### 概要

`stride auto-continue` は、現在の Gate 承認状態を読み取り、次に実行すべきステップのシーケンスを生成します。
シーケンスは必ず次の **HITL checkpoint**（人間承認ポイント = Gate）で停止します。

```
[従来] Step 1 → ユーザー確認 → Step 2 → ユーザー確認 → Step 3
[v4.1] Step 1 → Step 2 → Step 3 → Gate（ここで停止）
```

### 適用対象

| Phase | 自動連続範囲 | 停止点 |
|-------|-------------|--------|
| Design | basic_design → BPMN → lint | Gate 1, 2 |
| Specify | spec → plan → contracts → lint | Gate 3, 4 |
| Tasking | tasks → lint | Gate 5 |

### 使い方

```bash
# 次のシーケンスを表示
stride auto-continue specs/<feature>/

# JSON出力
stride auto-continue specs/<feature>/ --json
```

### 出力例

```
=== Auto-Continue Sequence ===
Current gate: Gate 2 (approved)
Next sequence:
  1. Create spec.md
  2. Create plan.md
  3. Generate contracts/
  4. Run stride-lint
  → STOP: Gate 3, 4 approval required
```

### セルフテスト

```bash
python3 sdd-templates/tools/auto_continue_runner.py --test
# 4 tests pass
```

---

## 23.2 Mandatory Output Rules

### 概要

AI 出力のフォーマットを標準化するルールです。ターミナル幅やツールに依存しない、一貫した出力を保証します。

### 4つのルール

| # | ルール | 理由 |
|---|--------|------|
| 1 | ASCII テーブルを使わない | ターミナル幅で崩れる |
| 2 | 選択肢は `N - **Option**: Description` 形式 | パース可能で読みやすい |
| 3 | ステータスは `PASS / FAIL / WARN / SKIP` | ツール間で統一された語彙 |
| 4 | 進捗は `[n/N]` 形式 | 自動化可能な進捗追跡 |

### 出力例（良い例）

```
[1/4] stride-lint: PASS (0 errors, 2 warnings)
[2/4] spec:drift: PASS (0 drifts)
[3/4] tests: PASS (47/47 passed)
[4/4] coverage: PASS (87.3% >= 80%)
```

### 確認コマンド

```bash
# 出力ルールの全文を表示
stride output-rules

# 基準文書
docs/mandatory-output-rules.md
```

---

## 23.3 DDD Integration（オプション）

### いつ使うか

DDD は **オプション機能** です。以下の条件に該当する場合に採用を検討します：

- `validate` mode の高リスク WI
- 複雑なドメインロジック（集約・エンティティ・値オブジェクトの設計が必要）
- `basic_design.md` の `delivery_model.ddd_policy` で `when_validate` が設定されている場合

### 有効化

`basic_design.md` の `delivery_model` セクションで設定します：

```yaml
delivery_model:
  type: feature_driven    # or ddd
  ddd_policy: when_validate  # never / when_validate / always
```

### DDD ステージ

DDD を採用した場合、Run 内に以下のステージが追加されます：

```
1. Domain Model（aggregate, entity, value object 定義）
2. Technical Design（アーキテクチャパターン選定）
3. ADR（Architecture Decision Record）
4. Implementation
5. Test
```

### 初期化コマンド

```bash
stride ddd-init <feature>
```

生成される成果物：

| ファイル | 内容 |
|----------|------|
| `specs/<feature>/implementation-details/domain_model.md` | ドメインモデル定義 |
| `specs/<feature>/implementation-details/technical_design.md` | 技術設計 |
| `shared/decisions/ADR-NNN-*.md` | 設計判断記録（初回） |
| `shared/decisions/decision-index.md` | ADR 一覧（自動更新） |

### テンプレート構成

- **Domain Model Template** (`ddd_domain_model_template.md`): Aggregate Root、Entity、Value Object、Domain Event を構造化
- **Technical Design Template** (`ddd_technical_design_template.md`): レイヤー構成、パターン選定、NFR 対応を記述
- **ADR Template** (`adr_template.md`): Status, Context, Decision, Consequences, Alternatives の5セクション

---

## 23.4 Decision Index（ADR）

### 概要

Architecture Decision Records をプロジェクト横断で管理します。ADR は `shared/decisions/` に蓄積され、Index から一覧できます。

```
shared/decisions/
├── ADR-001-database-selection.md
├── ADR-002-auth-strategy.md
└── decision-index.md    ← 全ADRの一覧と状態
```

### コマンド

```bash
# Decision Index を初期化
stride decisions init

# 既存ADRからIndexを再生成
stride decisions refresh
```

### ADR テンプレート構造

```markdown
# ADR-NNN: [Title]

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
[判断が必要になった背景]

## Decision
[選択した方針]

## Consequences
[採用による影響]

## Alternatives
[検討した他の選択肢とその理由]
```

### decision-index.md の出力例

```markdown
| ADR | Status | Date | Title | File |
|-----|--------|------|-------|------|
| ADR-001 | Accepted | 2026-02-10 | Database Selection | ADR-001-database-selection.md |
| ADR-002 | Proposed | 2026-02-12 | Auth Strategy | ADR-002-auth-strategy.md |
```

### セルフテスト

```bash
python3 sdd-templates/tools/decision_index.py --test
# 3 tests pass
```

---

## 23.5 ツールリファレンス

| ツール | コマンド | テスト数 |
|--------|---------|---------|
| auto_continue_runner.py | `stride auto-continue` | 4 |
| decision_index.py | `stride decisions init/refresh` | 3 |

---

## 関連ドキュメント

- [Adaptive Execution ガイド](17_adaptive_execution_guide.md) — Autonomy Bias, Run Resume
- [stride-lint ガイド](appendix_b_stride_lint.md) — Phase Gate lint
- [Evidence Pack ガイド](14_evidence_pack_guide.md) — 品質証跡
- [Spec Drift & Evidence Metrics ガイド](21_spec_drift_metrics_guide.md) — v4.2 機能
