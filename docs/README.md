# `docs/` Directory Index

> v6.0.0-tecnos-stride-value (2026-04-29) で整理。
> 利用者向けは [Manual (Docsify)](../manual/) を参照、本ディレクトリは **設計補助・実例・プロンプト** を保管。

## 1. アクティブ参照ファイル (root)

`docs/` 直下に置かれるのは README から直接参照されている or 頻繁に使われるドキュメントのみ。

| ファイル | 用途 |
|---|---|
| [`TEMPLATE_USAGE_GUIDE.md`](TEMPLATE_USAGE_GUIDE.md) | テンプレートクローン後の利用ガイド (README からリンク) |
| [`bpmn_quick_reference.md`](bpmn_quick_reference.md) | Camunda 8 BPMN の 1-page チェックリスト (sdd_bootstrap.md §4-BPMN から強参照) |
| [`camunda_bpmn_practice_guide.md`](camunda_bpmn_practice_guide.md) | BPMN 実装ガイド (詳細版) |
| [`mandatory-output-rules.md`](mandatory-output-rules.md) | `stride output-rules` の出力本体 |
| [`stride_github_projects_setup.md`](stride_github_projects_setup.md) | GitHub Projects V2 セットアップガイド |

## 2. 実例 — `examples/`

新規 feature を起こす際の参考実装。

- [`examples/sap-s4hana/`](examples/sap-s4hana/) — SAP SD / S4HANA FI の Epic / Feature 実例 (basic_design.md / process.bpmn / epic_flow.bpmn / 統合テストケース等の 9 ファイル)
- [`examples/bpmn-samples/`](examples/bpmn-samples/) — Camunda 8 BPMN の汎用サンプル (collaboration pool / vertical lane)

## 3. アーカイブ — `archive/`

過去バージョン履歴の保存。現行運用では参照不要だが、ロールバックや履歴確認のために保持。

- [`archive/prompts-history/`](archive/prompts-history/) — v3.x〜v4.x 系の機能強化プロンプト 13 件 (Camunda BPMN 段階別、ECC 採用、統合テスト、Multi-Model Evaluator、Process Metrics 等)
- [`archive/legacy/`](archive/legacy/) — v3.1 時代の TEIM 提案書、VERSION_UPDATE_CHECKLIST、stride-board PM ガイド (現行は manual/00 + manual/22 が後継)

## 4. v5.2 tuneup — `tuneup-2026-04-17/`

v5.2 (Opus 4.7 hardening) リリース時の細分化タスクプロンプト 7 件。リリース完了後は履歴扱い。

## 5. 個人作業領域 — `Rin-Works/` (chmod 700)

開発者個人のプロンプト下書き領域。ディレクトリパーミッション 700 で他者から保護。

## 関連ドキュメント

- [`../README.md`](../README.md) — プロジェクト全体の入口
- [`../manual/`](../manual/) — 利用者向けマニュアル 48 章 (Docsify)
- [`../agent_docs/`](../agent_docs/) — AI agent 向け運用ドキュメント
- [`../memory/`](../memory/) — Constitution / Org constraints / Artifact registry
