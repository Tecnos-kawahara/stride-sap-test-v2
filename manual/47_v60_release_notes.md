# Tecnos-STRIDE v6.0.0-tecnos-stride-value Release Notes

> Released: 2026-04-29 (Phase C 完了、FEAT-VALC01)
> Last reviewed: 2026-04-29

## 🎉 VALUE Upstream Extension 完成

Tecnos-STRIDE v6.0 は、Phase A → Phase B → Phase C の **3 段階** にわたり積み上げた
**VALUE Upstream Extension** の完成リリースです。Discovery → Design → Implementation →
Operation という SDD のフルサイクルを、BABOK v3 + Layered Requirements Modeling + value-driven discovery method (philosophical
inspiration) の三脚で機械検証可能な形に統合しました。

## 🛣 Phase A → C のロードマップ要約

| Phase | Feature ID | リリース日 | 主成果 |
|---|---|---|---|
| A | FEAT-VALA01 | 2026-04-29 | Schema 基盤: 4 policies + 16 templates + 3 amendments (proposed) + 4 manuals + 5 tests |
| B | FEAT-VALB01 | 2026-04-29 | CLI scaffold: 5 Python tools + 7 tests + 15 JSON schemas + 2 manuals + 4 stride_lint error codes + bin/stride upstream subcommand |
| C | FEAT-VALC01 | 2026-04-29 | 統合: upstream-bridge + retro --solution-eval + Constitution Article XV-XVII ratification + VERSION 6.0.0 MAJOR bump |

## ✨ Phase C 新機能

### `stride upstream-bridge`

Phase 0 / 0.3 / 0.5 で作成した Discovery / Elicit / Context Modelling の YAML 成果物を、
Phase 1 (Design) `basic_design.md` の `links` に **自動 populate** + BPMN Task 候補を
**stdout Markdown 出力** する CLI です。`--apply` は Phase 1 immutability check 付き
(Gate 1/2 未承認 feature にのみ許可)。詳細は [manual/45](45_upstream_bridge_guide.md)。

### `stride retro --solution-eval` (BABOK KA8)

稼働後ソリューション評価。`business_need.yaml.success_criteria` を目標 KPI として、KPI
実績 / Adoption / Issues を集計し、`specs/<feature>/state/solution_eval_<ts>.md` に Markdown
レポートを出力します。詳細は [manual/46](46_solution_evaluation_guide.md)。

### Constitution Article XV / XVI / XVII (ratified)

- **Article XV — BACCM Completeness Gate**: Phase 0 完了時に BACCM 6 軸 (change/need/
  solution/stakeholder/value/context) の機械検証を義務化
- **Article XVI — Layered Requirement Architecture (4-layer aligned)**: Phase 0.5 の
  4-layer Requirements Architecture構造を義務化
- **Article XVII — Solution Evaluation Feedback Loop (BABOK KA8)**: 稼働後評価ループの
  義務化と `solution_eval_*.md` の記録要求

これらは Phase A で `memory/constitution_amendments/` に proposed として置かれていたもので、
Phase C で正式に `memory/constitution.md` の `articles[]` 配列にマージされ、status が
`ratified` に遷移しました。amendments の文言修正は今後、新 amendment 起票で対応します
(既存 ratified の直接書き換えは禁止)。

## ⚠ Breaking Changes

v6.0.0 への昇格は **SemVer MAJOR** です。以下の変更が下流プロジェクトに影響します:

1. **Constitution articles[] が 14 → 17 に拡張**: 既存プロジェクトで Article 数を参照する
   バリデータ・ダッシュボードがある場合は更新が必要
2. **トップレベル `version` が `6.0.0-tecnos-stride-value` に bump**: 旧プロジェクトで
   `version: "5.x"` 前提のスキーマチェックがあれば 6.0 系を許容するように更新
3. **新サブコマンド 2 件**: `stride upstream-bridge` / `stride retro --solution-eval` が
   追加され、bin/stride dispatcher が拡張されています。既存サブコマンドの挙動は不変
4. **basic_design_template.md の links** に `upstream_dir_ref` / `upstream_policy_ref` /
   `baccm_completeness_ref` が追加されました。新規 feature 作成時の scaffold に反映され
   ますが、既存プロジェクトの basic_design.md は **手動更新が必要**

## 🛡 Phase A・B 成果物の保護

Phase C は **既存 Phase A・B 成果物 57 ファイル** (4 policies + 16 templates + 4 manuals +
4 tests + 5 tools + 7 tests + 15 JSON + 2 manuals) の hash を baseline 比較で固定しました。
1 件でも改変があれば BLOCKER として停止する設計です。これにより Phase A・B の意図
(schema 基盤 + CLI scaffold) は破壊されません。

ただし `tests/test_constitution_amendments.py` のみ Phase A 不変条件 (proposed-only +
本体不変) が Phase C 完了状態と論理矛盾するため、Phase C 状態用に改修されました
(ratified 検証 + 本体マージ後検証 へ進化、Hitoshi さん明示承認済み §Rule 1-A 例外)。新旧
の意図は git history と新規 `tests/test_constitution_xv_xvi_xvii_ratified.py` で並存保存
されています。

## 📦 ファイル変更サマリ

| カテゴリ | 新規 | 追記 | 改修 |
|---|---|---|---|
| Python tools | 2 (upstream_bridge.py / solution_evaluator.py) | stride_retro.py / bin/stride | - |
| Tests | 3 (test_upstream_bridge / test_solution_evaluator / test_constitution_xv_xvi_xvii_ratified) + 1 (test_stride_cli_phase_c) | - | 1 (test_constitution_amendments) |
| Constitution | - | constitution.md (articles +3, version, last_reviewed_at, amendment_history +3) + amendments XV/XVI/XVII (status ratified) | - |
| Templates | - | basic_design_template.md (links 拡張) | - |
| Manuals | 3 (45/46/47) | _sidebar.md / project_map.md | - |
| Project meta | - | README.md / VERSION | - |

新規 9 ファイル + 既存追記 11 ファイル + 改修 1 ファイル = 21 ファイル変更。

## 🔍 検証

- baseline pytest (Phase B 完了時): 717 passed
- after Phase C: 740+ passed (回帰 0)
- stride lint specs/val_c01/: PASS (Coverage AC 3/3, CT 2/2)
- stride pr-check . --strict: PR_READY
- shasum -c /tmp/baseline_protected_hashes_c.txt: 全 57 ファイル OK

## 🚀 次のステップ (Phase D)

VALUE Upstream Extension の完成形は v6.0 で達成しましたが、以下は Phase D に持ち越しています:

- **実プロジェクトでの dogfooding**: 実案件での upstream 反復運用と feedback
- **Profile 別 playbook (manual/48-50)**: enterprise-erp / saas-integration / prototype の
  運用ガイド
- **Migration Guide (manual/migration/v54_to_v60.md)**: 既存 v5.x プロジェクトを v6.0 へ
  移行する手順
- **`upstream_migration_helper.py`**: 既存 v5.x プロジェクトを v6.0 仕様に逆遡及適用する
  ツール

## 🙏 Acknowledgments

VALUE Upstream Extension 3 段階の設計と実装を主導した Tecnos Architecture Board と
Hitoshi Okazaki さんに感謝します。BABOK v3 (IIBA) / Layered Requirements Modeling ((concept reference, no proprietary brand)) /
value-driven discovery (philosophical foundation) の各原典が Tecnos-STRIDE の知的基盤を形作っています
(fair-use, names and section refs only)。

## 📝 Attribution

- BABOK v3 (IIBA), framework backbone (KA7 / KA8), license: fair-use, names and section refs only
- Layered Requirements Modeling ((concept reference, no proprietary brand)), structural integrity (4-layer), license: fair-use, layer/diagram names only
- value-driven discovery (philosophical foundation), philosophical inspiration, license: fair-use, model names only
