# バージョン履歴

> **対象**: 全読者
> **所要時間**: 5分
> **前提**: なし
> **In scope**: manual2 で把握しておきたい主要リリースの流れ
> **Out of scope**: すべての内部変更の列挙

---

## v5.1.0 — Harness Maturity（2026-04-08）

- `stride pr-check --mutation`: ミューテーションテスト（cosmic-ray opt-in）を Check [8/8] として追加。閾値は `.env.local` の `MUTATION_THRESHOLD`（デフォルト 80%）
- `stride evaluate --review`: Self-Review Loop — ボーダーライン域（スコア 70〜84）の評価を最大 3 回再評価し、critical issue を自動注入
- `stride health --runtime`: ランタイムセンサー — デッドコード（pylint）とカバレッジ減衰（`.coverage_baseline` 比較）を確認
- `stride harness-report`: 8 制御インベントリ → FULL / gaps レポートを出力
- Symphony Janitor: `SYMPHONY.md` の `janitor:` セクションでスタイル/循環複雑度の改善 Issue を自動提案（autopilot + starter scope）
- テスト: 539 件（symphony/262、integration/274、api/3）、`pytest -m harness` = 59 件

---

## v5.0.0

- CLI UX の強化
- `stride lint` の JSON / NDJSON / TSV 整備
- `suggested_action` と次ステップ案内の改善
- Agent Quick Reference 整備

## v4.9.0

- `stride security`
- `stride retro`
- LLM trust boundary の強化

## v4.8.x

- Database Lifecycle
- BPMN / Camunda まわりの整理

## v4.7.x

- Enterprise Hierarchy CLI 統合
- `stride epic`
- `stride init --epic`
- `stride lint --enterprise`

## v4.5.x 〜 v4.6.x

- Symphony
- BDD 受入条件
- Execution Authority

## v4.4 以前

- AI 自律実行モデルの整備
- PM / 実行者向けガイドの充実

---

## 次に読むべきもの

- まず使い始める: [../01_quickstart.md](../01_quickstart.md)
- CLI 全体を見る: [../reference/13_cli_reference.md](../reference/13_cli_reference.md)
