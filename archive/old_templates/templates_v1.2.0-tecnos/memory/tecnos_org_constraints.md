---
artifact: "org_constraints"
org_id: "ORG-TECNOS-001"
title: "Tecnos Japan Organization Constraints (SDD Addendum)"
version: "1.2.0-tecnos"
status: "active" # draft | active | deprecated
owners:
  - { name: "Tecnos Architecture Board", role: "Owner" }
  - { name: "PMO / Business Promotion", role: "Co-owner" }
last_reviewed_at: "YYYY-MM-DD"
---

# 1. Purpose
本書は、SDDテンプレートが **Tecnos Japan の実務制約**（ERP/SCM/CRM統合、監査・運用、AI/AgentOpsガードレール）を自動的に取り込めるようにするための組織アドオンです。

- 本書は **Constitution（不変原則）ではない**が、Tecnosのプロジェクトでは **必須参照**とする。

# 2. Standard Enterprise Systems（代表例）
> プロジェクト固有の対象は basic_design の `systems[]` に記載すること。

- SAP（ERP）
- mcframe（生産/原価・周辺）
- Salesforce（CRM）
- Integration/ESB/iPaaS（社内標準がある場合は明記）
- IAM（SSO/ID管理）
- DWH/BI（分析基盤）

# 3. Integration Policy（統合の基本）
## 3.1 Allowed Patterns（許可）
- API（REST/OData/SOAP 等）による疎結合連携
- Event（メッセージング）による非同期連携
- File/Batch（SFTP/共有ストレージ等）※契約化・監査可能であること
- EDI / IDoc 等の標準インターフェース（採用時は契約として明文化）

## 3.2 Forbidden Patterns（原則禁止：例外はArticleに紐付けて記録）
- ERP本体DBへの直接書き込み（境界違反）
- 画面スクレイピングによる業務連携（監査・保守性リスク）
- 認証情報の平文保管、共有アカウント乱用

## 3.3 Integration Quality Baseline（最低要件）
- Correlation ID（トレースID）を統一し、ログ/監査で追跡可能にする
- Idempotency（冪等性）を、少なくとも外部入力の再送に対して担保する
- リトライ/タイムアウト/デッドレター等、失敗時の振る舞いを契約に落とす
- データ所有者（SoR: System of Record）を決める（マスタ/トランザクション単位）

# 4. Data / Security / Audit（最低要件）
## 4.1 Data Classification（分類）
- Public / Internal / Confidential / Regulated(PII・契約・財務等) を基本分類とする
- 個人情報・機微情報を扱う場合は、収集目的・保管期間・アクセス権を明記する

## 4.2 Auditability（監査可能性）
- 重要操作は監査ログ（誰が・いつ・何を・なぜ）を残す
- 職務分掌（SoD）を考慮し、権限・承認フローを設計に含める

## 4.3 Access Control（アクセス制御）
- RBAC（役割ベース）を原則とし、最小権限で設計する
- 管理者権限の濫用を防ぐ（監査・承認・緊急時手順）

# 5. Ops Baseline（運用の最低要件）
- 監視：メトリクス/ログ/トレース（いずれか欠ける場合は理由を記録）
- 障害：インシデント→ポストモーテム→Spec/Planへの還流（SDDのフィードバック）
- SLO：可用性、レイテンシ、バッチ完了時間など、対象に応じて定義する
- 変更：リリース手順・ロールバック手順をPlan/Tasksに落とす

# 6. AI / AgentOps Guardrails
- 人間の承認なしに「本番データを不可逆に変更」する自動実行は禁止（例外は記録）
- Kill switch（停止条件）を basic_design に明記する
- 生成物（Spec/Plan/Tasks/BPMN）自体が監査対象になり得るため、改訂履歴を残す

# 7. PMO / Quality（TEIM観点の最小）
- 品質観点は少なくとも「要求・契約・テスト・運用」をカバーする
- 全社横展開が前提の成果物は、再利用可能なライブラリ/契約単位で整備する

> End of tecnos_org_constraints.md
