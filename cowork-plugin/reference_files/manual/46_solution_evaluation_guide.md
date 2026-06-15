# Solution Evaluation ガイド — BABOK KA8 稼働後評価

> Version: v6.0.0-tecnos-stride-value (Phase C, FEAT-VALC01) / Last reviewed: 2026-04-29

## 1. なぜ稼働後評価が必要か

BABOK v3 の Knowledge Area 8 (KA8 — Solution Evaluation) は、リリース後のソリューションが
**目標 KPI に対してどう機能しているか** を測定し、**次 iteration への学び** に還流するプロ
セスを義務化しています。Tecnos-STRIDE は、Phase A〜B までで Discovery / Design / Implement
の機械検証ループを構築しました。Phase C で導入された `stride retro --solution-eval` によ
り、リリース後のフィードバックループも CLI 1 コマンドでカバーできるようになり、Constitution
Article XVII (Solution Evaluation Feedback Loop) を実運用化します。

## 2. 入力アーティファクト

### 2.1 目標 KPI (必須、Phase 0 で記述済み)

`specs/<feature>/upstream/phase_0_discovery/business_need.yaml` の `success_criteria`
セクションが目標 KPI の正本です:

```yaml
success_criteria:
  kpi_lead_time:
    target: 30
    unit: days
    description: "受注登録リードタイム"
  kpi_cost_reduction:
    target: 100000
    unit: yen
    description: "月次コスト削減"
```

### 2.2 実績 KPI (任意)

リリース後に実測した値を YAML で渡します (`--kpi-source <path>`):

```yaml
kpi_actuals:
  kpi_lead_time:
    actual: 25
    measured_at: "2026-06-01"
  kpi_cost_reduction:
    actual: 120000
    measured_at: "2026-06-01"
```

未指定の場合は **graceful skip + warning** で、KPI 評価をスキップします (exit 0)。

### 2.3 Adoption Survey (任意)

ユーザ採用率と満足度を YAML で渡します (`--adoption-survey <path>`):

```yaml
adoption:
  rate: 0.78
  satisfaction: 4.2
  surveyed_at: "2026-06-15"
  n: 120
```

### 2.4 Issues 集計 (自動)

`specs/<feature>/runs/*/lessons.md` を再帰スキャンし、`- Issue` または
`Issue:` で始まる行を Issue 件数として自動集計します。Run 証跡の標準フォーマットに従って
記録していれば、追加作業なしで集計対象になります。

## 3. 使い方

### 3.1 最小実行

```bash
stride retro <feature> --solution-eval
```

`business_need.yaml.success_criteria` を目標 KPI として読み、Issues のみ集計したレポート
を出力します。kpi/adoption は graceful skip。

### 3.2 完全実行

```bash
stride retro <feature> --solution-eval \
  --kpi-source specs/<feature>/state/kpi_actuals_2026q2.yaml \
  --adoption-survey specs/<feature>/state/adoption_2026q2.yaml
```

KPI / Adoption / Issues すべてを集計し、Markdown レポートを stdout + ファイルに出力します。

### 3.3 出力先

- **stdout**: Markdown レポート (CI/PR コメント等で利用しやすい形)
- **`specs/<feature>/state/solution_eval_<timestamp>.md`**: 同内容の永続記録 (UTC タイム
  スタンプでファイル名を一意化)

## 4. レポート構造

```markdown
# Solution Evaluation Report — FEAT-XXX

- Timestamp (UTC): 2026-06-30T120000Z
- Policy version: 0.1.0-phase-a
- Overall: **PASS**

## KPI Targets vs Actuals

| KPI | Target | Actual | Status |
|---|---|---|---|
| kpi_lead_time | 30 | 25 | met |
| kpi_cost_reduction | 100000 | 120000 | met |

## Adoption

- rate: 0.78
- satisfaction: 4.2

## Issues count: 2 (from runs/*/lessons.md)

## Recommendations

- KPI / Adoption / Issues とも問題なし。次 iteration へ進行可

## Attribution
- BABOK v3 (IIBA), KA8 — Solution Evaluation, fair-use names only
```

## 5. PASS / FAIL 判定ロジック

`overall_pass` は以下の AND で判定:

1. KPI が定義されている場合: 未達の KPI 件数が全体の **50% 未満**
2. Issues 件数が **10 件未満**

PASS なら exit 0、FAIL なら exit 1、入力 YAML の parse 失敗等の ERROR なら exit 2。

## 6. 推奨運用フロー

1. **リリース 1 ヶ月後**: 初回評価 (`stride retro <feature> --solution-eval`、Issues のみ)
2. **リリース 3 ヶ月後**: 完全評価 (KPI 実測 + adoption survey 実施後)
3. **PR コメント連携**: stdout の Markdown を Linear / GitHub Discussion に投稿
4. **次 iteration へ還流**: `recommendations` に基づいて新 feature の Phase 0 で課題化

## 7. 関連 Constitution Article

- **Article XVII (Solution Evaluation Feedback Loop / BABOK KA8)**: 本コマンドの根拠条文。
  稼働後評価の義務化と `solution_eval_*.md` の記録を要求します。
- **Article XV (BACCM Completeness Gate)**: `success_criteria` を Phase 0 で必須項目化する
  ことで、本コマンドの目標 KPI が常に存在することを保証します。

## 8. CLI リファレンス

```
stride retro <feature> --solution-eval [--kpi-source <path>] [--adoption-survey <path>]

Exit code:
  0 = PASS (overall_pass=True or KPI graceful skip)
  1 = FAIL (overall_pass=False, KPI 著しい未達 or Issues 10 件以上)
  2 = ERROR (入力 YAML パース失敗等)
```

## 9. Attribution

- BABOK v3 (IIBA), KA8 — Solution Evaluation framework backbone, fair-use, names and
  section refs only
- value-driven discovery (philosophical foundation), philosophical inspiration on outcome / value evaluation,
  fair-use, model names only
