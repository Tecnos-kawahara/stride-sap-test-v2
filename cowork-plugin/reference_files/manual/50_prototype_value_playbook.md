# prototype Profile VALUE Upstream Extension Playbook

> Version: v6.0.0-tecnos-stride-value (Phase D, FEAT-VALD01) / Last reviewed: 2026-04-30

社内 PoC・短命ツール・innovation 推進部の試行プロジェクトに、VALUE Upstream Extension (Phase 0 拡張) を **lite-mode** で適用する実践 playbook です。「動かして学ぶ」を優先しつつ、後段で enterprise-erp / saas-integration profile への格上げが可能な状態で立ち上げることを目指します。

## 1. Profile の特徴

`prototype` profile は `shared/policies/profile_policy.yaml` で **最も軽量な閾値** を設定します。`task_completion_report: one_line` (1-line per task) / `completeness_lake_max_lines: 100` / `completeness_lake_max_files: 3` で、ドキュメント生成負荷を最小化します。

主な適用ターゲット:

- **innovation 推進部の社内 PoC** (技術検証・市場検証)
- **3 ヶ月以内で完走する短命ツール**
- **新規アイデアの実現可能性検証 (Feasibility study)**
- **既存業務に影響が限定的な小規模機能**
- **学習目的の社内ハッカソン / ワークショップ成果物**

prototype の核心は「過度なドキュメント化を避けて、実装で確認したフィードバックを優先する」ことです。BACCM 6 軸の必須度は `stakeholder + value` の 2 軸のみとし、他 4 軸 (change / need / solution / context) は **warning レベル** で扱います。Phase 0 で `business_need.yaml` や `value_canvas.yaml` を 30 分〜1 時間で書き、すぐ実装に着手します。

iteration 段階は bootstrap → structure → refinement のうち **bootstrap 1 周** で済ませることが多く、refinement は実機 feedback が出てから判断します。

## 2. VALUE 適用フロー

### Phase 0 (Discovery lite) — 0.5〜1 日

`stride upstream init <feature> --phase discovery --profile prototype` で 7 artifact が scaffold されますが、**最低限**以下の 2 ファイルだけ埋めれば Gate 0 通過扱いとします:

- `stakeholder_map.yaml`: 利用者 + スポンサー + 開発者の 3 役割 (1 名ずつでも可)
- `value_canvas.yaml`: 「PoC で何を検証したいか」「成功 / 失敗の定義」を 1-3 行で

残り 5 artifact (`business_need / context_map / risk_register / change_strategy / goal_tree`) は **空欄 OK**。warning レベルとして lint には残りますが BLOCKER ではありません (`baccm_completeness.yaml` の `prototype` 閾値で許容)。

### Phase 0.3 (Elicit) — optional

`stride upstream init <feature> --phase elicit` は **任意**。PoC 内で関係者へのヒアリングが必要な場合のみ実施し、`elicitation_results` を 1 ファイル書く程度で十分です。

### Phase 0.5 (Context Modelling) — optional

`stride upstream init <feature> --phase context_modelling` も **任意**。short-lived ツールの場合は `business_use_case` のみ書いて、その他 5 Layered Requirements Modeling artifact は省略可。enterprise-erp / saas-integration へ格上げするタイミングで書き足します。

### Phase 0 → 1 接続 + Phase 1 → Final

`stride upstream-bridge <feature> --target phase1 --apply` で `links` populate (Phase 0 が空でも `upstream_dir_ref` は populate される)。Phase 1 (basic_design.md) は最小スキーマ (WHO / WHAT / WHY + 1 traceability_row) で十分です。`stride retro --solution-eval` は PoC 終了時に「PoC 成果と次フェーズ判断」を 1 ファイルにまとめる用途で活用してください。

## 3. Dogfooding 事例 (横断学び、サニタイズ済)

prototype profile での dogfooding は本リリースには未実施 (primary candidate は enterprise-erp での external SCM pilot) ですが、prototype を採る場合の典型的な学びを整理:

- **成功パターン**: 1 日で `stakeholder_map.yaml` + `value_canvas.yaml` のみ書いて Phase 1 へ進み、3 週間 PoC で `stride retro --solution-eval` で「次は saas-integration profile に格上げ」と判断 → スムーズに本格開発へ移行
- **失敗パターン (回避方法)**: prototype のまま 6 ヶ月以上運用してしまい、後付けで enterprise-erp の整合をとるのが困難になる case → **PoC 期間 (3 ヶ月以内) を必ず設定** し、終了時 retro で profile 格上げ判断を必須にする
- **改善要望**: prototype でも最低限の `risk_register` (1-3 リスクのみ) は書かせる方が良い → Phase E でテンプレ更新候補

## 4. チェックリスト (lite-mode、各 Gate 通過時)

### Gate 0 (Discovery lite 完了)

- [ ] `stakeholder_map.yaml` に 3 役割以上
- [ ] `value_canvas.yaml` に成功 / 失敗の定義 1-3 行
- [ ] `stride upstream validate <feature>` で stakeholder + value 軸 pass (他軸は warning OK)

### Gate 0.5 (Context Modelling、任意)

- [ ] `business_use_case.yaml` を書いた場合は 1 件以上のユースケース定義
- [ ] (省略時) basic_design の `links.upstream_dir_ref` だけ populate

### Gate 1 / 2 (Design / BPMN、最小スキーマ)

- [ ] `basic_design.md` に WHO / WHAT / WHY 記載
- [ ] `traceability_rows` 1 件以上
- [ ] `process.bpmn` は最小 (start → 1 task → end)

### Gate 5 / Final (PoC 終了時)

- [ ] PoC 期間内に終了 (3 ヶ月以内)
- [ ] `stride retro <feature> --solution-eval` で次フェーズ判断記録 (廃止 / saas-integration / enterprise-erp 格上げ)
- [ ] (任意) lessons を `memory/lessons_learned/` 共有

## 5. 関連ツール

| コマンド | prototype での扱い |
|---|---|
| `stride upstream init <feature> --phase discovery --profile prototype` | 必須、最低 2 artifact 埋める |
| `stride upstream init <feature> --phase elicit` | 任意 |
| `stride upstream init <feature> --phase context_modelling` | 任意 |
| `stride upstream validate <feature>` | stakeholder + value 軸の pass のみ要 |
| `stride upstream-bridge <feature> --target phase1 --apply` | 任意 (空 Phase 0 でも実行可) |
| `stride lint --upstream <feature>` | warning OK、ERROR のみ修正 |
| `stride retro <feature> --solution-eval` | PoC 終了時に次フェーズ判断記録 |

prototype で動かして良いと判断した後で saas-integration / enterprise-erp に **格上げ** する場合は、`upstream_migration_helper.py` で既存 basic_design.md から Phase 0 yaml seed を逆生成し、人間 refinement で完成させる流れが効率的です (`manual/migration/v54_to_v60.md` 参照)。

## 6. Attributions

- **BABOK v3 (IIBA)**: framework backbone — fair-use, names and section refs only
- **Layered Requirements Modeling ((concept reference, no proprietary brand))**: structural integrity — fair-use, layer/diagram names only
- **value-driven discovery (philosophical foundation)**: philosophical inspiration (value canvas) — fair-use, model names only

> 軽量さを保ちつつ、後で saas-integration / enterprise-erp に格上げできる土台を残すことが prototype profile の本質です。詳細は `manual/48` (enterprise-erp) / `manual/49` (saas-integration) も参照してください。
