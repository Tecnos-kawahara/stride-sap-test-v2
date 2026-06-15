---
artifact: "artifact_registry"
registry_id: "REG-TECNOS-001"
title: "Artifact Registry (Tecnos)"
version: "5.4.0-tecnos-stride"
status: "active" # draft | active | deprecated
owners:
  - { name: "Tecnos PMO", role: "Owner" }
  - { name: "Tecnos Architecture Board", role: "Co-owner" }
last_reviewed_at: "2026-04-24"
---

# 1. Purpose
- 成果物を **ID/版/保管先** で一意同定し、ゲート判定の証跡を固定する。
- 版の乱立を防ぎ、参照元の唯一正本を維持する。

# 2. Canonical Artifact Registry (YAML)
```yaml
artifact_registry:
  - artifact_id: "APP-TP-REQ-001"
    name: "全体テスト計画【要件定義版】"
    phase: "②要件定義"
    domains: ["アプリ", "マネジメント"]
    owner_role: "テクノス_PM/QA"
    approver_role: "顧客_PM/情シス責任者"
    required_sections:
      - "テスト工程定義（Txx）"
      - "対象範囲（機能/IF/帳票/権限/ジョブ）"
      - "合格基準（重大欠陥/証跡/非機能）"
      - "主体遷移（工程別R&R）"
      - "環境/データ準備方針"
    evidence_for_gates:
      - gate: "②要件定義ゲート"
        usage: "計画妥当性・責任分担の合意根拠"
    version_rule:
      scheme: "verXX"
      mandatory_fields: ["改訂日", "改訂者", "改訂概要"]
    storage:
      canonical_path: "/TEIM/Projects/<PJID>/Artifacts/APP/"
      single_source_of_truth: true
```

# 3. Rules
- **唯一正本**のパスを `storage.canonical_path` に必ず記載する。
- Gateで参照する成果物は **artifact_id** で固定する。

> End of artifact_registry.md
