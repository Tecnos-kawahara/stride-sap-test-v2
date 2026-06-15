# Tecnos-STRIDE v5.1 Tune-up — 残存タスク用プロンプト集

**作成日**: 2026-04-17
**対象版数**: Tecnos-STRIDE v5.1.0
**目的**: Opus 4.7 の literal instruction-following 向けチューンナップ後、ガバナンス文書で特定された残存実装タスクを、独立した Claude Code セッションで安全に実施するための self-contained プロンプト集。

## 実施順序（推奨）

| # | プロンプト | 所要 | 並列可 | 前提 |
|---|-----------|------|-------|------|
| 1 | [01_harness_report_test6.md](01_harness_report_test6.md) | 30 分 | ✅ 他と並列可 | なし |
| 2 | [02_yaml_extraction_refactor.md](02_yaml_extraction_refactor.md) | 2-3 時間 | 単独推奨 | 1 完了推奨 |
| 3 | [03_symphony_cli_integration.md](03_symphony_cli_integration.md) | 1-2 時間 | ✅ 1 と並列可 | なし |
| 4 | [04_manual_consolidation.md](04_manual_consolidation.md) | 1 時間 + 対話 | 単独 | ユーザー対話必須 |
| 5 | [05_execution_authority_e2e.md](05_execution_authority_e2e.md) | 2-3 時間 | 単独推奨 | 2 完了推奨 |

**推奨フロー**: 1 + 3 を並列 → 2 → 5 → 4（対話） の順。

## 共通運用ルール

全プロンプトは以下を前提に書かれている:

- 各プロンプトは **self-contained** — 新規セッションにそのまま貼り付けて開始可能
- 各タスクは `agent_docs/sdd_bootstrap.md §5` の固定報告テンプレートで完了報告
- `APPROVAL.md` / `WI-*.approval.md` / `EPIC_APPROVAL.md` は**絶対に編集しない**
- lint 自動修正は**最大 5 回**、`pr-check` は**最大 3 回**（bootstrap §1 の loop bound 準拠）
- Completeness 湖判定（+100 行 / +3 ファイル / 新 AC 無 / 新リスク無）を超える場合は停止してユーザー相談

## ByteRover 注意

2026-04-17 時点で Node.js v25 非互換により `brv` コマンドがクラッシュしている。`nvm use 22` で復旧可能。ByteRover が使えない場合は `~/.claude/projects/*/memory/` 経由の auto-memory を代替。

## 背景（本タスク群の導出経緯）

2026-04-17 のチューンナップセッションで、Opus 4.7 の literal-follow に対する governance ドキュメントの問題を洗出し、8 ファイルを修正済み:

- CLAUDE.md / CLAUDE_WORKFLOW.md
- SDD_MANIFESTO.md / SYMPHONY.md
- agent_docs/sdd_bootstrap.md / sdd_guidelines.md / harness.md
- sdd-templates/templates/SYMPHONY_template.md

その際、ガバナンスではなく**実装側の tune-up 候補** 5 件が残存した。それを本ディレクトリのプロンプト集として実行可能な形で確定したもの。
