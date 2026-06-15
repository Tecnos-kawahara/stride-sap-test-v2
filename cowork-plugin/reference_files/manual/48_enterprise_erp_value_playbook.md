# enterprise-erp Profile VALUE Upstream Extension Playbook

> Version: v6.0.0-tecnos-stride-value (Phase D, FEAT-VALD01) / Last reviewed: 2026-04-30

ERP / SAP / mcframe / SCM / CRM 統合プロジェクト向けに、VALUE Upstream Extension (Phase 0 拡張) を **最も厳格に適用する** ための実践 playbook です。社内・顧客 ERP 案件で要件定義の漏れを最小化し、Tecnos-STRIDE v6.0 の SDD パイプラインを完走させることを目的とします。

## 1. Profile の特徴

`enterprise-erp` profile は `shared/policies/profile_policy.yaml` で **最も厳格な閾値** を設定する profile です。`task_completion_report: full_5_step` / `completeness_lake_max_lines: 200` / `completeness_lake_max_files: 5` で、Phase 0 → Final まで **報告粒度を最高水準** に維持します。

主な適用ターゲット:

- **SAP S/4HANA / mcframe / Oracle ERP** などの基幹システム導入・更新
- **SCM (Supply Chain Management)** の在庫・受発注統合
- **CRM (Salesforce 等)** との Customer Master 統合 / Lead-to-Order
- **監査対象 (J-SOX、ISMS、ISO/IEC 42001)** プロジェクト
- **複数子会社・海外拠点を跨ぐ業務統合**

これら案件では「Phase 0 で BACCM 6 軸 (change/need/solution/stakeholder/value/context) のいずれか **1 軸でも欠ければ、Phase 1 設計が必ず歪む**」ため、`shared/policies/baccm_completeness.yaml` の `threshold_for_gate_0: 100` (100% 必須) を **そのまま** 採用します。saas-integration / prototype のように軸の必須度を緩めることはしません。

加えて、`shared/policies/upstream_iteration_policy.yaml` で定義される iteration 3 段階 (bootstrap → structure → refinement) を **3 周完走** すること、KA8 (BABOK Solution Evaluation) 稼働後評価を **必須** とすることが、enterprise-erp profile を選ぶプロジェクトの暗黙合意になります。

## 2. VALUE 適用フロー

各 Phase の判断ポイントを整理します。詳細コマンドは §5 を参照。

### Phase 0 (Discovery) — 着手 1〜2 週間

`stride upstream init <feature> --phase discovery --profile enterprise-erp` で 7 つの artifact (`business_need / value_canvas / stakeholder_map / context_map / risk_register / change_strategy / goal_tree`) を scaffold します。**ここで全 7 ファイルを埋め切る**ことが enterprise-erp の出発点です。Discovery では、ERP 導入前提の業務プロセス (例: P2P / O2C / R2R) を value_chain として明示し、関係者を「業務部門 / IT 部門 / 監査 / 経営層 / SI ベンダ / SaaS ベンダ」の **5-7 階層**で stakeholder_map に層別化します。

### Phase 0.3 (Elicit) — 並行〜2 週間

`stride upstream init <feature> --phase elicit` で `elicitation_plan` / `elicitation_results` を scaffold。enterprise-erp では **インタビュー (15-30 件) + ワークショップ (3-5 回) + ドキュメントレビュー** の 3 ルートを最低限とし、各ルートで stakeholder_map の各層を 1 名以上カバーします。ERP 案件特有の「現場プロセスと標準業務プロセスの乖離」を抽出するのが本 Phase の核心です。

### Phase 0.5 (Context Modelling) — 並行〜2 週間

`stride upstream init <feature> --phase context_modelling` で 6 つの Layered Requirements Modeling artifact (`system_context / business_context / business_use_case / business_process / business_event / business_state`) を scaffold。enterprise-erp では **既存システム (SAP / mcframe / Salesforce 等) との境界** を `business_context.systems` に明記し、`business_use_case` に「Customer Master 取込」「受注登録」「月次締め」等を主要ユースケースとして記述します。

### Phase 0 → Phase 1 接続

`stride upstream-bridge <feature> --target phase1 --apply` で `basic_design.md` の `links` に `upstream_dir_ref / upstream_policy_ref / baccm_completeness_ref` を populate。BPMN-TASK 候補を `business_use_case` から自動生成して stdout に出力します (Phase C bridge 機能、`manual/45` 参照)。

### Phase 1 → 4 + Final

通常の Tecnos-STRIDE フロー (Design → Specify → Tasking → Execute → Final)。enterprise-erp profile では各 Gate で `task_completion_report: full_5_step` を厳守し、Final で `stride retro <feature> --solution-eval --kpi-source <path>` を実行して BABOK KA8 稼働後評価を記録します (Phase C retro 機能、`manual/46`)。

## 3. Dogfooding 事例 (中間スナップショット、サニタイズ済)

primary dogfooding として実施中の **external SCM pilot (フランチャイズ外食 SCM 案件)** の中間学び (Phase 0 → 0.3 → 0.5 完走時点) を抜粋:

- **失敗パターン**: 初回 Discovery で stakeholder_map が「業務部門 / IT 部門」の 2 層しか出ず、`baccm_completeness_checker` で stakeholder 軸が 60% で fail。**経営層 / 子会社 / 製造委託先 (連番) / 業務部門リーダー (役割名)** を追加して 100% 達成までに 2 iteration 必要だった。
- **成功パターン**: 既存 v5.x プロジェクトを `upstream_migration_helper.py` で逆遡及 (`--apply`) して Phase 0 yaml seed を生成 → 「自動抽出可能」「要人間確認」ラベル付きの seed が、現場ヒアリング時の 1 次たたき台として機能、ヒアリング工数を 30% 短縮 (オーダー感、桁丸め)。
- **改善要望**: Phase 0.5 の `business_use_case.yaml` に「ユースケース連番命名規約 (UC-01..UC-NN)」のガイドラインが薄い。Phase E でのスキーマ拡張候補として `memory/lessons_learned/upstream_dogfooding/external_scm_pilot_01.md` に転記済。

実運用では §Rule 15-B 対応表に従って必ず匿名化し、`Hitoshi さん目視レビュー必須` の HITL ガード後に Tecnos-STRIDE 本体へ転記してください。

## 4. チェックリスト (各 Gate 通過時)

### Gate 0 (Discovery 完了)

- [ ] 7 artifact (`business_need / value_canvas / stakeholder_map / context_map / risk_register / change_strategy / goal_tree`) 全てが populated
- [ ] `stride upstream validate <feature>` (= `baccm_completeness_checker`) で **全軸 100%**
- [ ] stakeholder_map に「業務 / IT / 監査 / 経営 / SI / SaaS」の 5 層以上
- [ ] `stride evaluate <feature_path> --phase discovery` で iteration 3 段階の bootstrap が PASS

### Gate 0.5 (Context Modelling 完了)

- [ ] 6 Layered Requirements Modeling artifact 全 populated
- [ ] `business_context.systems` に既存基幹システム (SAP / mcframe / Salesforce 等) を明記
- [ ] `business_use_case` ≥ 5 件、いずれも「業務」が主語 (システムが主語の use case は spec 寄り)

### Gate 1 / 2 (Design / BPMN 完了、`stride upstream-bridge` 適用後)

- [ ] `basic_design.md` の `links.upstream_dir_ref / upstream_policy_ref / baccm_completeness_ref` 全 populated
- [ ] `process.bpmn` に business_use_case 由来の BPMN-TASK が反映
- [ ] `stride lint --upstream` PASS

### Gate 5 / Final

- [ ] `stride retro <feature> --solution-eval --kpi-source <path>` で BABOK KA8 評価記録
- [ ] iteration 3 段階 (bootstrap / structure / refinement) 全完走
- [ ] `task_completion_report: full_5_step` で全 WI 報告

## 5. 関連ツール

| コマンド | 用途 | 詳細 |
|---|---|---|
| `stride upstream init <feature> --phase <p> --profile enterprise-erp` | Phase 0/0.3/0.5 scaffold | manual/43 |
| `stride upstream validate <feature>` | BACCM 完成度チェック (=baccm_completeness_checker) | manual/43 |
| `stride upstream-bridge <feature> --target phase1 [--apply]` | Phase 0 → 1 接続 | manual/45 |
| `stride lint --upstream <feature>` | upstream 構造整合 lint | manual/43 |
| `stride evaluate <feature_path> --phase discovery` | iteration 評価 | manual/44 |
| `stride retro <feature> --solution-eval --kpi-source <path>` | BABOK KA8 稼働後評価 | manual/46 |
| `python3 sdd-templates/tools/upstream_migration_helper.py <feature_dir> [--apply]` | v5.x → v6.0 Phase 0 seed 逆生成 | manual/migration/v54_to_v60.md |

## 6. Attributions

`shared/policies/upstream_policy.yaml` / `baccm_completeness.yaml` / `technique_library.yaml` 各成果物末尾の attributions を参照。

- **BABOK v3 (IIBA)**: framework backbone (KA4 Elicitation / KA6 Strategy Analysis / KA7 Requirements Analysis / KA8 Solution Evaluation) — fair-use, names and section refs only
- **Layered Requirements Modeling ((concept reference, no proprietary brand))**: structural integrity (4-layer system_context / business_context / business_use_case / business_process / business_event / business_state) — fair-use, layer/diagram names only
- **value-driven discovery (philosophical foundation)**: philosophical inspiration (value canvas / goal tree) — fair-use, model names only

> 詳細は `agent_docs/sdd_bootstrap.md` および各 Phase のマニュアル (`manual/43-47`) を参照してください。
