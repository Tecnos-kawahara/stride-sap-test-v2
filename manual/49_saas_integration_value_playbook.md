# saas-integration Profile VALUE Upstream Extension Playbook

> Version: v6.0.0-tecnos-stride-value (Phase D, FEAT-VALD01) / Last reviewed: 2026-04-30

SaaS API 連携・公開 API・規制対象 Event 基盤 (CBP v3 等) の統合プロジェクト向けに、VALUE Upstream Extension (Phase 0 拡張) を **API 契約整合を強調しつつ適用する** 実践 playbook です。BACCM 6 軸はすべて pass を維持しつつ、Phase 0 / 0.5 を「API/Event 契約 SSoT を確立する」観点で運用します。

## 1. Profile の特徴

`saas-integration` profile は `shared/policies/profile_policy.yaml` で **連携業務 SaaS / API / Event 中心の統合案件** に特化した閾値を設定します。`task_completion_report: critical_only` (critical tier のみ 5-step、他は 1-line) / `completeness_lake_max_lines: 150` / `completeness_lake_max_files: 4` で、報告粒度は enterprise-erp より軽量、prototype より厳格です。

主な適用ターゲット:

- **Salesforce / HubSpot / Marketo** などの SaaS API 連携 (Lead / Opportunity / Contact 同期)
- **公開 API (Open API / OAuth / OIDC)** を提供するサービス
- **Event 基盤 (Kafka / EventBridge / Pub-Sub)** の規制対象トピック
- **Webhook / Callback** 中心の連携統合
- **Connected Business Process (CBP v3)** 等の標準業務 SaaS 適用案件

これら案件では「契約 (OpenAPI / AsyncAPI / EDI / IDoc) が SSoT として最初に定まり、その後ろで業務プロセスが整流化される」性質があります。Phase 0 では BACCM 6 軸の change/need/solution/stakeholder/value/context すべてを **必須 pass** とし、特に `solution` 軸で API/Event の SLA・冪等性・監査ログを早期に明文化します。

iteration 段階は bootstrap → structure → refinement の 3 段階を **2 周以上** 完走することを推奨。enterprise-erp の 3 周必須に対し、API 連携は仕様確定後の手戻りが軽いため、2 周で十分なケースもあります (Hitoshi さんの判断で 3 周まで延長可)。

## 2. VALUE 適用フロー

### Phase 0 (Discovery) — 1〜2 週間

`stride upstream init <feature> --phase discovery --profile saas-integration` で 7 artifact を scaffold。saas-integration の特徴は以下:

- **`stakeholder_map`**: SaaS ベンダ (CSM / TS) を必ず stakeholder に含める。社内側は API 利用者と運用監視者を分けて記述
- **`value_canvas`**: 「API 経由で連携することで何が変わるか」を業務 KPI と連結
- **`risk_register`**: SaaS 側の API 互換性破壊・レート制限・障害時 SLA 違反を必ず記載

### Phase 0.3 (Elicit) — 並行〜1 週間

`stride upstream init <feature> --phase elicit`。saas-integration では **SaaS 公式ドキュメントレビュー (OpenAPI / AsyncAPI 仕様) と SaaS ベンダーへの照会** を `elicitation_plan.routes` に必ず含めます。インタビュー中心の enterprise-erp とは異なり、**ドキュメント中心 + 補助インタビュー** が現実的です。

### Phase 0.5 (Context Modelling) — 並行〜1 週間

`stride upstream init <feature> --phase context_modelling`。saas-integration では:

- **`system_context`**: 自社 + SaaS + 関連サービス (認証基盤 / API Gateway / DLQ) を境界として記述
- **`business_context.systems`**: SaaS の正式名 + version + 接続プロトコル (REST / GraphQL / Event)
- **`business_event`**: 規制対象イベント (請求 / 決済 / KYC / GDPR) を必ず明記
- **`business_use_case`**: 「API 経由 X を取得 / 更新する」を主述語にする (enterprise-erp の業務主述語と対比)

### Phase 0 → 1 接続 + Phase 1 → Final

`stride upstream-bridge <feature> --target phase1 --apply` で `links` populate。saas-integration では `basic_design.md` の `contracts/openapi.yaml` (または `asyncapi.yaml`) との整合が `stride lint --upstream` で検証されます (`spec_as_code.artifacts` 参照)。Phase 4 (Execute) では契約テスト (TS-CON-*) を最優先で実装し、integration テスト (TS-INT-*) で SaaS sandbox 接続を確認します。

## 3. Dogfooding 事例 (中間スナップショット、サニタイズ済)

primary dogfooding (external SCM pilot) は enterprise-erp profile での実施ですが、saas-integration 観点での横断学びとして以下を抜粋:

- **成功パターン**: SaaS の OpenAPI 仕様を `Phase 0.5 system_context` に最初に貼り付けて、`business_context.systems` の境界定義を OpenAPI servers と一致させたところ、Phase 1 の `contracts/openapi.yaml` 作成時の認識齟齬が発生しなかった
- **失敗パターン**: SaaS 側のレート制限と再試行ポリシーを `risk_register` に書かずに進めた case (内部 PoC) で、Phase 4 で integration テスト失敗。`risk_register` に「SLA 違反時の DLQ / 再試行 / 監査ログ要件」を明示すると Phase 1 の `data_governance` セクションへ自然に伝搬する
- **改善要望**: AsyncAPI を扱う case の例示が `business_event.yaml` テンプレートに薄い。Phase E で「Event 中心」テンプレ拡張候補として記録

## 4. チェックリスト (各 Gate 通過時)

### Gate 0 (Discovery 完了)

- [ ] 7 artifact 全 populated
- [ ] BACCM 6 軸全 pass (`stride upstream validate <feature>`)
- [ ] stakeholder_map に SaaS ベンダ (CSM / TS) を含む
- [ ] risk_register に SaaS 側 API 互換性 + レート制限 + 障害 SLA 記載

### Gate 0.5 (Context Modelling 完了)

- [ ] 6 Layered Requirements Modeling artifact 全 populated
- [ ] system_context に自社 + SaaS + 関連サービス境界
- [ ] business_event に規制対象イベント明記 (該当する場合)
- [ ] business_use_case は API 経由を主述語

### Gate 1 / 2 (Design / BPMN)

- [ ] `links.upstream_*_ref` 全 populated
- [ ] `contracts/openapi.yaml` または `asyncapi.yaml` が存在
- [ ] `stride lint --upstream` PASS

### Gate 5 / Final

- [ ] 契約テスト (TS-CON-*) 100% カバー
- [ ] SaaS sandbox での integration テスト (TS-INT-*) 確認
- [ ] iteration 段階 2 周以上完走
- [ ] (推奨) `stride retro --solution-eval` で SaaS 連携の稼働後評価

## 5. 関連ツール

| コマンド | 用途 | manual/49 視点での補足 |
|---|---|---|
| `stride upstream init <feature> --phase <p> --profile saas-integration` | Phase 0/0.3/0.5 scaffold | profile を必ず明示 |
| `stride upstream validate <feature>` | BACCM 完成度チェック | 6 軸 pass 必須 |
| `stride upstream-bridge <feature> --target phase1 --apply` | Phase 0 → 1 接続 | OpenAPI/AsyncAPI 連携を意識 |
| `stride lint --upstream <feature>` | upstream lint | spec_as_code との整合確認 |
| `stride evaluate <feature_path> --phase discovery` | iteration 評価 | 2 周以上を推奨 |
| `stride retro <feature> --solution-eval --kpi-source <path>` | KA8 稼働後評価 | SaaS 連携の SLA / 障害発生数を記録 |

API 仕様検証ツールの統合例 (任意): `schemathesis run contracts/openapi.yaml --base-url <sandbox>` を Phase 4 の integration テストに組み込むと、契約-実装の乖離を早期に検出できます。

## 6. Attributions

- **BABOK v3 (IIBA)**: framework backbone (KA4 Elicitation / KA6 Strategy Analysis / KA7 Requirements Analysis / KA8 Solution Evaluation) — fair-use, names and section refs only
- **Layered Requirements Modeling ((concept reference, no proprietary brand))**: structural integrity — fair-use, layer/diagram names only
- **value-driven discovery (philosophical foundation)**: philosophical inspiration — fair-use, model names only
- **OpenAPI Initiative (Linux Foundation)** / **AsyncAPI Initiative**: 仕様の参照のみ、再配布なし

> Phase 別の詳細手順は `manual/43-47` を参照。enterprise-erp との対比は `manual/48` を、社内 PoC で軽量に運用する場合は `manual/50_prototype_value_playbook.md` を参照してください。
