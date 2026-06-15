# 24. マルチチームコラボレーションガイド

> **Version**: v5.4.0-tecnos-stride
> **対象**: 3-5チーム規模の共同開発プロジェクト

---

## 20.1 いつマルチチームモードを使うか

| 条件 | モード |
|------|--------|
| 1チーム、1-3 Feature | Standard（Epic不要） |
| 2チーム以上、または4+ Feature | **Multi-Team（Epic必須）** |
| ERP/基幹系連携あり | Multi-Team + STRIDE |

---

## 20.2 Epic → Feature → WI 階層

```
Epic (EPIC-ORDER)
├── epic_design.md / epic_flow.bpmn / feature_breakdown.md
│   └── Epic overview / team-system handoff
│
├── Feature (FEAT-ORD-001) ─── TEAM-A
│   ├── basic_design.md → process.bpmn → spec.md → plan.md → tasks.md
│   ├── work_items/
│   │   ├── WI-ERP-ORD001-001 (mode: confirm)
│   │   └── WI-ERP-ORD001-002 (mode: autopilot)
│   └── state/state.yaml
│
├── Feature (FEAT-ORD-002) ─── TEAM-B
│   ├── basic_design.md → process.bpmn → spec.md → plan.md → tasks.md
│   └── work_items/ ...
│
└── Shared Artifacts
    ├── EPIC_PROGRESS_REPORT.md      ← PM Dashboard
    ├── DEPENDENCY_MANIFEST.yaml     ← チーム間依存
    ├── OPS_PACK_REGISTRY.yaml       ← Ops準備状況
    └── shared/contracts/
        └── CONTRACT_REGISTRY.yaml   ← 共有契約
```

---

## 20.3 初期セットアップ手順

### Step 1: Epic作成

```bash
# Enterprise Hierarchy を有効化
cat > sdd-templates/config/enterprise.yaml <<'YAML'
enterprise:
  enabled: true
YAML

# Epic 一式を初期化
sdd-templates/bin/stride epic init EPIC-ORDER
```

### Step 2: 追加成果物の初期化（必要に応じて）

```bash
# `stride epic init` は以下を自動生成します:
# - epics/EPIC-ORDER/epic_flow.bpmn
# - epics/EPIC-ORDER/EPIC_PROGRESS_REPORT.md
# - epics/EPIC-ORDER/DEPENDENCY_MANIFEST.yaml
# - epics/EPIC-ORDER/OPS_PACK_REGISTRY.yaml
# - shared/contracts/CONTRACT_REGISTRY.yaml（未作成時のみ）
#
# チームステータスレポートは必要に応じて追加
cp sdd-templates/templates/team_status_report_template.md epics/EPIC-ORDER/TEAM_STATUS_TEAM-A.md
cp sdd-templates/templates/team_status_report_template.md epics/EPIC-ORDER/TEAM_STATUS_TEAM-B.md
```

> `epic_flow.bpmn` は `collaboration + participant(pool)` の overview 用 BPMN です。各 Feature の `process.bpmn` は laneSet ベースの executable BPMN として分離します。

### Step 3: 各チームのFeature作成

```bash
# TEAM-A
sdd-templates/bin/stride init order_master --epic EPIC-ORDER --team TEAM-A

# TEAM-B
sdd-templates/bin/stride init order_approval --epic EPIC-ORDER --team TEAM-B
```

---

## 20.4 チーム間依存管理

### 依存マニフェスト（DEPENDENCY_MANIFEST.yaml）

```yaml
dependencies:
  - dependency_id: "DEP-001"
    from_feature: "FEAT-ORD-002"
    from_team: "TEAM-B"
    to_feature: "FEAT-ORD-001"
    to_team: "TEAM-A"
    type: "blocking"
    criticality: "high"
    interface:
      contract_ref: "SC-API-ORDER"
    status: "pending"
```

### ステータス遷移

```
pending → in_progress → stable
                      → at_risk → blocked → stable
```

### エスカレーションルール

- `at_risk` の blocking 依存 → PM/Epic Leadに48h以内通知
- `blocked` の依存 → ARCH_BOARDエスカレーション
- 循環依存の検出 → `dependency_checker.py --all`

---

## 20.5 共有契約ガバナンス

### CONTRACT_REGISTRY.yaml

全チームが利用する契約の一元管理:

```yaml
contracts:
  - contract_id: "SC-API-ORDER"
    name: "Order Service API"
    type: "api"
    owner_team: "TEAM-A"
    current_version: "1.0.0"
    consumers:
      - team_id: "TEAM-B"
        adoption_status: "in_development"
```

### 契約変更フロー

1. オーナーチームがCCP（Contract Change Proposal）を作成
2. `dependency_checker.py notify SC-API-ORDER --message "v2.0 breaking change"`
3. 消費者チームがCCPを確認
4. ARCH_BOARD承認（breaking changeの場合）
5. 移行期間を設けて実装

---

## 20.6 Ops Pack管理

### OPS_PACK_REGISTRY.yaml

ERP連携がある全WIのOps準備状況を追跡:

| WI | Feature | Team | Transport | Rollback | Hypercare | Review |
|----|---------|------|-----------|----------|-----------|--------|
| WI-001 | FEAT-ORD-001 | TEAM-A | Ready | Ready | Ready | Approved |
| WI-002 | FEAT-ORD-002 | TEAM-B | Draft | Pending | Pending | Pending |

### Go-Live チェック

Go-Live前に `epic_progress_aggregator.py` で Ops準備率100%を確認。

---

## 20.7 ツールリファレンス

### epic_progress_aggregator.py

```bash
# ターミナルサマリー
python3 sdd-templates/tools/epic_progress_aggregator.py epics/EPIC-ORDER/

# JSON出力（CI連携）
python3 sdd-templates/tools/epic_progress_aggregator.py epics/EPIC-ORDER/ --format json

# ダッシュボード自動生成
python3 sdd-templates/tools/epic_progress_aggregator.py epics/EPIC-ORDER/ --format markdown
```

### wi_readiness_checker.py

```bash
# WI実行準備チェック（Autonomy Bias 対応 — v3.1）
python3 sdd-templates/tools/wi_readiness_checker.py specs/order_master/ WI-ERP-ORD001-001

# 詳細出力
python3 sdd-templates/tools/wi_readiness_checker.py specs/order_master/ WI-ERP-ORD001-001 --verbose
```

> **v3.1**: Autonomy Bias が `state.yaml` に設定されている場合、recommended_mode が自動的にシフトされます。
> 詳細は [22. Adaptive Execution ガイド](17_adaptive_execution_guide.md) を参照。

### run_resume_detector.py (v3.1 新規)

```bash
# Run中断再開ポイントを検出
python3 sdd-templates/tools/run_resume_detector.py specs/order_master/runs/WI-ERP-ORD001-001/RUN-001/
```

> 既存アーティファクトの存在をチェックし、次に作成すべき成果物を提示します。

---

## 20.8 FAQ

**Q: Feature間でコードを共有したい場合は？**
A: `shared/` ディレクトリに共有契約（SC-*）として定義し、CONTRACT_REGISTRY.yamlに登録する。直接のコード参照は禁止（Article V: Modularity）。

**Q: チームリードがステータスレポートを忘れた場合は？**
A: `epic_progress_aggregator.py` がレポート未更新を検知し警告する。2週間未更新はPMがフォローアップ。

**Q: 途中でFeatureを別チームに移管したい場合は？**
A: `epic_design.md` のteam_id変更 → EPIC_APPROVAL.mdで再承認 → DEPENDENCY_MANIFEST.yaml更新。

**Q: experimentalなFeatureもEpic管理が必要？**
A: Epic配下であれば必須。ただしcoverage要件が緩和される（AC 80%, E2E不要）。
