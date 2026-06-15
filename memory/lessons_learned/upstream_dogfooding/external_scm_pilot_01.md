# external_scm_pilot_01: VALUE Upstream Extension Dogfooding Lessons (Phase 1 完了時点 中間スナップショット)

> Version: v6.0.0-tecnos-stride-value (Phase D, FEAT-VALD01) / Last reviewed: 2026-04-30  
> Source: external SCM pilot (フランチャイズ外食 SCM 案件) — § Rule 15-B / 15-C 匿名化済  
> Status: **中間版** (Phase 0 / 0.3 / 0.5 完走、Phase 1 着手中)。Final 後の補完は後続 PR (Option B) で追記予定。

このファイルは Phase D primary dogfooding として実施中の **external SCM pilot** の sanitized 学び記録です。`§Rule 15-B 対応表` で全実データを匿名化し、Hitoshi さん目視レビューで実データ残存ゼロを確認しています。

## 1. プロジェクト概要 (匿名化済)

- **目的**: フランチャイズ外食 SCM 案件における大手小売チェーン向け供給管理システムの上流要件統合 + Phase 1 設計の初動を VALUE Upstream Extension v6.0 で実施
- **スコープ**: 製造委託先 A / B (連番) との連携 SKU カテゴリ X / Y を含む在庫・受発注プロセスの可視化、KPI 在庫金額・売上・欠品率は桁丸め (オーダー感のみ)、〜億円規模の月次在庫を対象とする
- **期間**: 2026-04 着手、現在 Phase 1 実施中
- **チーム規模**: 業務部門リーダー 1 名 + IT 部門 1 名 + 経営層 SH 1 名 + Hitoshi (Tecnos AI / facilitator) + Claude Code (AI Executor)
- **profile**: enterprise-erp (BACCM 100% 必須、iteration 3 段階完走必須、KA8 稼働後評価必須を採用)

## 2. 適用 Phase

| Phase | 完了状況 | 主成果物 |
|---|---|---|
| Phase 0 (Discovery) | ✅ 完走 | 7 artifacts 全 populated (`business_need / value_canvas / stakeholder_map / context_map / risk_register / change_strategy / goal_tree`) |
| Phase 0.3 (Elicit) | ✅ 完走 | `elicitation_plan` + `elicitation_results` (インタビュー 8 件 + ドキュメントレビュー 3 件) |
| Phase 0.5 (Context Modelling) | ✅ 完走 | 6 Layered Requirements Modeling artifacts 全 populated (`system_context / business_context / business_use_case / business_process / business_event / business_state`) |
| Phase 0 → 1 接続 | ✅ 完走 | `stride upstream-bridge --apply` 成功、`basic_design.md` の `links` populate 済 |
| Phase 1 (Design) | 🔄 実施中 | `basic_design.md` 編集中 |
| Phase 2 → Final | 📅 予定 | 後続 PR で追記 (Option B) |

## 3. BACCM スコア推移

各 Gate 通過時点での `stride upstream validate <feature>` 結果のサマリ (匿名化済、桁丸め):

| Gate | change | need | solution | stakeholder | value | context | 総合 |
|---|---|---|---|---|---|---|---|
| Gate 0 (初回) | 80% | 90% | 70% | 60% | 75% | 70% | **fail (stakeholder 60%)** |
| Gate 0 (iter 2) | 90% | 95% | 85% | 95% | 90% | 85% | **fail (solution/context 85%)** |
| Gate 0 (iter 3) | 100% | 100% | 100% | 100% | 100% | 100% | **pass (full BACCM 100%)** |
| Gate 0.5 | 100% | 100% | 100% | 100% | 100% | 100% | pass |
| Gate 1 (Phase 1 着手後) | 100% | 100% | 100% | 100% | 100% | 100% | pass |

**iteration 3 段階を素直に通したことで BACCM 100% を達成**。enterprise-erp profile の閾値 (`threshold_for_gate_0: 100`) を 1 周で満たすのは難しく、3 iteration 必須運用が現実的という肌感が得られました。

## 4. 失敗パターン

### 4.1 stakeholder_map が浅く、初回 Gate 0 で fail

- **現象**: 初回 Discovery では stakeholder_map に「業務部門 / IT 部門」の 2 層しか書かなかった。`baccm_completeness_checker` が stakeholder 軸 60% で fail。
- **原因**: enterprise-erp 案件における「経営層 / 子会社 / 製造委託先 / 業務部門リーダー」の階層を Discovery 時点で意識できていなかった。
- **修正**: `stakeholder_map.yaml` に「業務 / IT / 監査 / 経営 / SI / SaaS / 製造委託先 (連番)」の 7 階層を追加 (役割名のみ)。
- **教訓**: enterprise-erp profile を選んだ時点で stakeholder 5-7 階層は **必須前提**。playbook (`manual/48`) のチェックリストでこれを明示する。

### 4.2 risk_register に SaaS 側 SLA / レート制限を書き忘れ

- **現象**: 別の internal PoC (saas-integration profile) で、SaaS 側 API のレート制限・障害時 SLA・再試行ポリシーを `risk_register.yaml` に書かないまま Phase 0 完走したケース。Phase 4 (Execute) で integration テスト失敗 → 後付けで追記する手戻り発生。
- **原因**: Discovery 時に SaaS ベンダー (CSM / TS) を stakeholder に含めなかった + risk_register の典型項目チェックリストが薄かった。
- **修正**: `manual/49_saas_integration_value_playbook.md` の Discovery チェックリストに「SaaS 側レート制限 + SLA + 再試行 + 監査ログ」を必須項目として明記。
- **教訓**: saas-integration profile では `risk_register` の API 連携固有リスクを Discovery 段階でテンプレート化しておくと手戻りを削減できる。

### 4.3 business_use_case の命名規約が曖昧

- **現象**: Phase 0.5 で `business_use_case.yaml` のユースケース連番命名規約 (UC-01 / UC-NN) が Phase A/B/C テンプレで明示されておらず、ある時は `UC-001`、ある時は `usecase_01` と書き分けてしまった。Phase 1 BPMN-TASK との対応が崩れる原因に。
- **原因**: `sdd-templates/templates/upstream/business_usecase_template.yaml` のコメントが曖昧。
- **修正案 (Phase E 候補)**: テンプレに「`UC-NNN` (3 桁数字、`^UC-[0-9]{3}$`)」を明示し、`stride lint --upstream` で BPMN-TASK との対応をチェック。
- **教訓**: ID 命名規約は Constitution `id_conventions` に拡張するのが本筋。Phase E でスキーマ拡張候補として記録。

## 5. 成功パターン

### 5.1 既存 v5.x プロジェクトの逆遡及で Phase 0 着手工数を短縮

- **現象**: 既存 v5.x プロジェクト (別の internal 案件) を `upstream_migration_helper.py --apply` で逆遡及 → 「自動抽出可能」「要人間確認」ラベル付きの Phase 0 yaml seed が生成 → 業務専門家 1 名のヒアリング 2 時間 + 個人作業 4 時間で 7 軸を埋め切った。
- **効果**: ヒアリング工数を **30% 短縮** (オーダー感、桁丸め)。helper の seed が「現場ヒアリング時の 1 次たたき台」として有効に機能した。
- **教訓**: 逆遡及 helper は完成品ではなく seed (種) と割り切ると効果的。`manual/migration/v54_to_v60.md` の手順 A をデフォルト推奨にする方針が妥当。

### 5.2 stride upstream-bridge で Phase 0 → 1 認識齟齬ゼロ

- **現象**: `stride upstream-bridge <feature> --target phase1 --apply` で `basic_design.md` の `links` populate + BPMN-TASK 候補出力 → Phase 1 着手時に「Phase 0 で何を決めたか」を明示的に Phase 1 設計者へ受け渡せた。
- **効果**: Phase 0 → 1 の **翻訳ロス (認識齟齬・記入漏れ) ゼロ** で着手。手作業時代と比べて Phase 1 開始時点の前提共有時間が大幅短縮。
- **教訓**: bridge コマンドの dry-run → review → --apply のフローは `manual/45_upstream_bridge_guide.md §2` 通りに従うのが安全。

### 5.3 stride upstream validate のエラーメッセージで refinement が方向付け

- **現象**: BACCM 軸 fail のエラーメッセージが「どの軸の何が不足か」を明示するため、refinement のターゲットが具体化された。
- **効果**: iteration 1 → 2 → 3 の refinement で「次にやるべきこと」が常に明確、無駄な探索を回避。
- **教訓**: BACCM の機械検証 (Phase B `baccm_completeness_checker.py`) は単なる pass/fail でなく、軸ごとの**詳細フィードバック**を提供することが現場価値の源泉。

## 6. 改善要望 (Phase E 候補)

dogfooding 中に発見した、Phase E (将来) で扱いたい改善要望:

1. **business_use_case 命名規約の Constitution 拡張** (§4.3 参照): `UC-NNN` を `id_conventions` に追加、`stride lint --upstream` で BPMN-TASK との対応チェック
2. **risk_register テンプレート強化**: profile 別 (enterprise-erp / saas-integration) の典型リスク項目を default で埋める scaffold 拡張
3. **iteration 3 段階の進捗可視化**: 現状 `stride evaluate --phase discovery` の出力が iteration 単位、複数 iteration の推移を見るダッシュボード化候補
4. **upstream_migration_helper の精度向上**: 「自動抽出可能」フィールドの精度を実プロジェクト feedback で改善 (現状は basic_design.md の SSoT YAML 構造に依存、自然言語抽出は弱い)
5. **AsyncAPI / Event 中心ケースの business_event テンプレ拡張** (§ saas-integration playbook 参照)
6. **stakeholder_map の階層数 lint**: enterprise-erp で 5 層未満なら warning、3 層未満なら ERROR、等の profile 別閾値
7. **dogfooding 学び自動集約**: `memory/lessons_learned/upstream_dogfooding/*.md` から横断 failure_patterns / success_patterns を `stride retro --aggregate-lessons` で自動生成する CLI 拡張

これらは将来の `FEAT-VALE01` 等で issue 起票し、Phase E で取り扱います。

## 7. 残作業 (Final まで)

- Phase 1 (Design) 完了 → Gate 1/2 承認
- Phase 2 (Specify) → 3 (Tasking) → 4 (Execute) → Final
- 完走後に `stride retro --solution-eval --kpi-source <path>` で BABOK KA8 稼働後評価 (KPI 実績集計)
- Final 後に本ファイルを後続 PR で**完成版 (sanitized)** へ更新 (Option B フォールバック)

---

## サニタイズ確認チェック (§Rule 15-B 対応表準拠)

このファイルには以下のカテゴリの実データキーワードが**含まれていない**ことを確認済 (具体的な対応表は本リポジトリの `docs/Tecnos-STRIDE Upstream Extension_D.md §Rule 15-B サニタイズ方針詳細表` を参照、本ファイルには引用しない / CI grep 誤検知回避のため):

- 顧客固有名 → 「external PoC」「フランチャイズ外食 SCM 案件」等の汎用表現に置換済
- 顧客顧客 (元請け先) → 「大手小売チェーン」等の業態カテゴリに置換済
- OEM 委託先名 (実名) → 「製造委託先 A / B (連番)」に置換済
- 具体的 SKU 名 → 「SKU カテゴリ X / Y」に抽象化済
- 実 KPI 数値 → 「〜億円規模 / 〜% / 桁丸め」のオーダー感のみ
- 担当者個人名 → 「業務部門リーダー / 経営層 SH / 購買担当者」等の役割名に置換済
- 要件定義書ファイル名・社内文書名 → 言及なし

Hitoshi さん目視レビュー: 2026-04-30 (実データ残存ゼロ)。  
CI grep ガード: 本ファイル全体に対して `docs/Tecnos-STRIDE Upstream Extension_D.md §Rule 15-B` の禁止語パターンを実行し、0 件確認。

> 後続 PR で Final 完了後の補完 (KA8 評価結果 + 残 lessons) を追記する想定。
