# Article XVII (ratified) — Solution Evaluation Feedback Loop

> **Status:** **ratified** (2026-04-29, Phase C, FEAT-VALC01)
> **Phase:** C (ratified)
> **Reviewer:** Tecnos Architecture Board
> **Target merge:** Phase B (with `meta.version` bump and `amendment_history` entry)

## 1. Purpose

Tecnos-STRIDE は Phase 4 (Execute) → Final Gate → PR で「ひと回り」を完結させる構造を持つが、**稼働後** (post-deployment) の価値検証 → 上流仕様への還流ルートが Constitution レベルで明文化されていなかった。
本 Article は、**BABOK v3 KA8 Solution Evaluation** の概念を踏襲し、稼働後の価値計測と仕様改訂提案を **明示的なフィードバックループ** として宣言する。

## 2. Article (proposed YAML)

```yaml
articles_proposed:
  - id: "XVII"
    name: "Solution Evaluation Feedback Loop (post-deployment Discovery refresh)"
    summary: "稼働後の価値計測 (BABOK KA8) を Discovery (Phase 0) への還流として制度化する"
    rules:
      - "Final Gate 通過後の運用フェーズで、value_canvas.value_metrics (Phase 0 起点) を実測し、評価レポートを保管する"
      - "計測結果が threshold を下回ったとき、Discovery (Phase 0) を再起動する Issue (`spec-impact:required` ラベル) を起票する"
      - "Phase 0 再起動時は、原則として既存の business_need / value_canvas / goal_tree を改訂し、change_strategy に新しい transition_state を追加する形で行う (新規 feature 起票より優先)"
      - "spec-impact 蓄積が同一 feature で 2 件以上になった時点で amendment_generator が自動 draft 化する (既存 v5.x 機能と接続)"
    criteria:
      - "稼働後 90 日以内に value_metrics の実測レポートが implementation-details/post_evaluation_report.md (Phase B で命名確定) に格納されている"
      - "実測値と Phase 0 設定値の乖離が thresholds で管理され、超過時に Issue が自動起票される"
      - "再起動された Discovery は upstream_iteration_policy.yaml の 3-iteration pattern を再度適用する"
```

## 3. Rationale

- **既存問題:** STRIDE の Final Gate は「PR がマージされたら完了」だが、実運用上は「稼働してみて期待した KPI が出ているか」が真の完了判定となる。Constitution に明示しないとこの観点が運用属人化しやすい。
- **BABOK の貢献:** BABOK v3 KA8 (Solution Evaluation) は、稼働中ソリューションの価値計測 / 限界分析 / 推奨改訂を体系化している。STRIDE では既存の Multi-Model Evaluator (`stride evaluate`) と連動させることで、定性 / 定量の両面を扱える。
- **既存機能との接続:** v5.x で導入された `amendment_generator.py` (`spec-impact:required` ラベル蓄積トリガー) と本 Article は自然に統合できる。本 Article はその上流側の起動条件を制度化する。

## 4. Phase A における取り扱い

- 本 Article は **proposed** 段階に留まる。Constitution 本体 (`memory/constitution.md`) は無変更。
- Phase A では Article の宣言と value_canvas / goal_tree テンプレートの value_metrics フィールドの存在のみを同梱する。
- 稼働後評価ツール (`stride evaluate --post-deployment`、`spec-impact` 自動起票連動) の実装は Phase B 以降。

## 5. Dependencies

- **Article XV (BACCM Completeness Gate)** と循環: Article XV (上流の入口) → Phase 1-4 → Article XVII (出口の評価) → Article XV (Discovery 再起動) というループを構成する。
- **既存 Article XIII (PM Progress Visibility)** と整合: PM ダッシュボードに稼働後評価メトリクスを統合するための受け皿として機能。
- **既存 Article VI (Automation)** と整合: Evidence Pack の post-deployment 拡張として、価値計測も自動証跡化する方向性。

## 6. Acceptance Criteria for Future Merge (Phase B)

- `stride evaluate --post-deployment <feature>` ツールが value_metrics の実測 / threshold 判定 / Issue 起票を行えること
- 稼働後評価レポートのテンプレート (`post_evaluation_report_template.md`) が `sdd-templates/templates/` に追加されていること
- 既存 `amendment_generator.py` との連動 (`spec-impact:required` ラベル自動付与) が動くこと
- 本 Article 採択時に `meta.version` と `amendment_history` を bump する PR が独立に提出されること

---

## Attribution

- **BABOK v3 (IIBA)** — KA8 Solution Evaluation (§8.1 Measure Solution Performance / §8.2 Analyze Performance Measures / §8.3 Assess Solution Limitations / §8.4 Assess Enterprise Limitations / §8.5 Recommend Actions to Increase Solution Value) — fair-use, names and section refs only.
- 本ドキュメントの記述はすべて Claude (Opus 4.7) による独自要約であり、原典テキストの逐語的引用は含まない。
