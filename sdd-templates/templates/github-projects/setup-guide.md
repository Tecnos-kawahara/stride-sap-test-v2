# GitHub Projects セットアップガイド

## 概要

SDD (Spec-Driven Development) のワークフローを GitHub Projects V2 で管理するための設定ガイドです。
`specs/<feature>/state/state.yaml` の `github_projects` セクションと連携します。

---

## Quick Start（5分セットアップ）

```bash
# 1a. Labels 一括登録（GitHub Projects ラベル — labels.json から 43件）
cat sdd-templates/templates/github-projects/labels.json | jq -c '.[]' | while read label; do
  name=$(echo "$label" | jq -r '.name')
  color=$(echo "$label" | jq -r '.color')
  desc=$(echo "$label" | jq -r '.description')
  gh label create "$name" --color "$color" --description "$desc" --force
done

# 1b. STRIDE Learning Loop ラベル（findings/decisions/amendment/sentry 等 — 20件）
python3 sdd-templates/tools/setup_project_labels.py --repo OWNER/REPO

# 2. Milestones 作成
for gate in "Gate 1: Design Review" "Gate 2: BPMN Review" "Gate 3: Spec Review" \
            "Gate 4: Plan Review" "Gate 5: Tasking Review" "Final: Evidence Review"; do
  gh api repos/{owner}/{repo}/milestones -f title="$gate"
done

# 3. Issue Templates コピー
cp sdd-templates/templates/github-projects/ISSUE_TEMPLATE/*.md .github/ISSUE_TEMPLATE/
```

---

## 1. Labels

### Label Taxonomy（43ラベル）

`labels.json` から登録されるラベル。

| Category | Labels | Purpose |
|----------|--------|---------|
| **Issue Type** | `epic`, `milestone`, `work-item`, `risk`, `blocker`, `dependency` | 課題種別 |
| **Mode** | `mode:autopilot`, `mode:confirm`, `mode:validate` | AI実行モード |
| **Scale Tier** | `tier:starter`, `tier:standard`, `tier:enterprise` | プロジェクト規模 |
| **Risk Flag** | `risk:authz`, `risk:audit_log`, `risk:data_migration`, `risk:external_api`, `risk:ui_only` | リスクフラグ |
| **Status** | `status:done`, `status:in-progress`, `status:pending`, `status:blocked` | 状態 |
| **Priority** | `priority:high`, `priority:medium`, `priority:low` | 優先度 |
| **Gate** | `gate:1-design` ~ `gate:final` | Gate段階 |
| **Ops** | `ops-ready`, `ops-not-ready` | 運用準備状態 |
| **Quality** | `sdd-reference-miss` | 品質計測 |
| **Symphony** | `symphony:ready`, `symphony:running`, `symphony:blocked`, `symphony:done`, `symphony:failed`, `symphony:janitor` | Symphony Orchestration |
| **Phase** | `phase:design`, `phase:specify`, `phase:tasking`, `phase:execute` | SDD Phase 可視化 |

---

## 2. Milestones

SDD の Gate + Epic マイルストーンに対応する GitHub Milestones:

### Gate Milestones（全Epic共通）

```bash
gh api repos/{owner}/{repo}/milestones -f title="Gate 1: Design Review"
gh api repos/{owner}/{repo}/milestones -f title="Gate 2: BPMN Review"
gh api repos/{owner}/{repo}/milestones -f title="Gate 3: Spec Review"
gh api repos/{owner}/{repo}/milestones -f title="Gate 4: Plan Review"
gh api repos/{owner}/{repo}/milestones -f title="Gate 5: Tasking Review"
gh api repos/{owner}/{repo}/milestones -f title="Final: Evidence Review"
```

### Epic Milestones（EPIC-SAMPLE例）

```bash
gh api repos/{owner}/{repo}/milestones -f title="EM-01: 受注登録基盤完了" -f due_on="2026-02-10T00:00:00Z"
gh api repos/{owner}/{repo}/milestones -f title="EM-02: 権限・承認・監査完了" -f due_on="2026-03-01T00:00:00Z"
gh api repos/{owner}/{repo}/milestones -f title="EM-03: Epic統合完了・リリース" -f due_on="2026-03-15T00:00:00Z"
```

---

## 3. Issue Templates

4種類のIssue Template:

| Template | File | Usage |
|----------|------|-------|
| Epic | `ISSUE_TEMPLATE/epic.md` | Epic全体の進捗追跡 |
| Milestone | `ISSUE_TEMPLATE/milestone.md` | マイルストーン追跡 |
| Work Item | `ISSUE_TEMPLATE/work-item.md` | WI単位の実行追跡 |
| Risk/Blocker | `ISSUE_TEMPLATE/risk.md` | リスク・ブロッカー管理 |

---

## 4. GitHub Projects V2 Custom Fields

Projects V2 で以下のカスタムフィールドを追加:

### Required Fields

| Field Name | Type | Options / Format |
|------------|------|------------------|
| WI ID | Text | WI-XXX-NNN |
| Feature ID | Text | FEAT-XXX |
| Epic ID | Text | EPIC-XXX |
| SDD Mode | Single Select | autopilot, confirm, validate |
| Coverage Tier | Single Select | starter, standard, enterprise |
| SDD Gate | Single Select | Gate 1, Gate 2, Gate 3, Gate 4, Gate 5, Final |
| Complexity | Single Select | low, medium, high |
| Risk Flags | Text | comma-separated |
| Ops Ready | Single Select | Yes, No, N/A |

### Recommended Fields

| Field Name | Type | Options / Format |
|------------|------|------------------|
| Priority | Single Select | high, medium, low |
| Target Date | Date | YYYY-MM-DD |
| Run ID | Text | RUN-NNN |
| Walkthrough | Single Select | Yes, No |
| Milestone | Single Select | EM-01, EM-02, EM-03 |

---

## 5. PM Dashboard Views

GitHub Projects V2 で以下のViewを作成:

### View 1: Epic Overview（テーブル）

PM が全体を俯瞰するためのメインビュー。

| Column | Source | Group By | Sort |
|--------|--------|----------|------|
| Title | Issue title | — | — |
| Status | Status field | — | Priority |
| Feature ID | Custom field | Feature ID | — |
| SDD Mode | Custom field | — | — |
| Coverage Tier | Custom field | — | — |
| Assignee | Issue assignee | — | — |
| Milestone | Custom field | — | — |

**Filter**: `label:epic,work-item`

### View 2: Kanban Board（ボード）

WI の進捗をカンバンで管理。

| Column | Items |
|--------|-------|
| **Backlog** | status:pending |
| **Design Review** | gate:1-design ~ gate:5-tasking |
| **In Progress** | status:in-progress |
| **Pending Review** | walkthrough待ち |
| **Done** | status:done |

**Filter**: `label:work-item`

### View 3: Risk Heatmap（テーブル）

リスクとブロッカーを一覧。

| Column | Source |
|--------|--------|
| Title | Issue title |
| Probability | Label (risk level) |
| Impact | Label (impact level) |
| Status | Status field |
| Owner | Assignee |

**Filter**: `label:risk,blocker`
**Sort**: Impact DESC, Probability DESC

### View 4: Milestone Timeline（ロードマップ）

マイルストーンの時系列表示。

| Column | Source |
|--------|--------|
| Title | Milestone name |
| Target Date | Date field |
| Completion | Progress indicator |
| Features | Linked issues |

**Filter**: `label:milestone`
**Layout**: Roadmap

### View 5: Ops Readiness（テーブル）

リリース準備状況。

| Column | Source |
|--------|--------|
| WI ID | Custom field |
| Title | Issue title |
| Ops Ready | Custom field |
| Transport | Label (verified/not) |
| Rollback | Label (tested/not) |
| Hypercare | Label |

**Filter**: `label:work-item`

---

## 6. state.yaml との対応

```yaml
# specs/<feature>/state/state.yaml
github_projects:
  project_id: "PVT_kwDOBxxxxxx"   # Projects V2 の ID
  project_number: 2
  project_title: "Tecnos-STRIDE SDD Board"

  # Label Mapping
  labels:
    - { sdd_concept: "coverage_tier", github_label: "tier:standard" }
    - { sdd_concept: "mode:autopilot", github_label: "mode:autopilot" }
    - { sdd_concept: "mode:validate", github_label: "mode:validate" }
    - { sdd_concept: "risk:authz",     github_label: "risk:authz" }

  # Milestone Mapping
  milestones:
    - { sdd_gate: "Gate1", github_milestone: "Gate 1: Design Review" }
    - { sdd_gate: "Final", github_milestone: "Final: Evidence Review" }

  # Epic Milestone Mapping
  epic_milestones:
    - { epic_milestone: "EM-01", github_milestone: "EM-01: 受注登録基盤完了" }
    - { epic_milestone: "EM-02", github_milestone: "EM-02: 権限・承認・監査完了" }
    - { epic_milestone: "EM-03", github_milestone: "EM-03: Epic統合完了・リリース" }

  # Views (Projects V2 preset views)
  views:
    - name: "Epic Overview"
      type: "table"
      filter: "label:epic,work-item"
    - name: "Kanban Board"
      type: "board"
      filter: "label:work-item"
    - name: "Risk Heatmap"
      type: "table"
      filter: "label:risk,blocker"
    - name: "Milestone Timeline"
      type: "roadmap"
      filter: "label:milestone"
    - name: "Ops Readiness"
      type: "table"
      filter: "label:work-item"
```

---

## 7. Sample: EPIC-SAMPLE 完全セットアップ

### Step 1: Epic Issue

```bash
gh issue create \
  --title "[EPIC] EPIC-SAMPLE: mcframe受注管理アドオン" \
  --label "epic,tier:standard,status:in-progress" \
  --body "$(cat epics/EPIC-SAMPLE/PM_DASHBOARD.md)"
```

### Step 2: Milestone Issues

```bash
gh issue create \
  --title "[MS] EM-01: 受注登録基盤完了" \
  --label "milestone,status:done" \
  --milestone "EM-01: 受注登録基盤完了" \
  --body "$(cat <<'EOF'
## Milestone: EM-01

| Field | Value |
|-------|-------|
| Target Date | 2026-02-10 |
| Status | :white_check_mark: completed |
| Completion | 100% |

## Exit Criteria
- [x] 受注登録API（CT-API-01）実装・テスト完了
- [x] 確認ダイアログUI実装（AC-US-FEATERPOMS-001-02）
- [x] mcframe在庫引当連携（CT-API-03）動作確認
EOF
)"

gh issue create \
  --title "[MS] EM-02: 権限・承認・監査完了" \
  --label "milestone,status:pending" \
  --milestone "EM-02: 権限・承認・監査完了" \
  --body "$(cat <<'EOF'
## Milestone: EM-02

| Field | Value |
|-------|-------|
| Target Date | 2026-03-01 |
| Status | :hourglass: on_track |
| Completion | 0% |

## Exit Criteria
- [ ] 金額別3段階承認フロー実装（AC-US-FEATERPOMS-002-01）
- [ ] SoD検証ロジック実装・テスト完了
- [ ] 全操作の監査ログ出力（AC-US-FEATERPOMS-002-02）
EOF
)"

gh issue create \
  --title "[MS] EM-03: Epic統合完了・リリース" \
  --label "milestone,status:pending" \
  --milestone "EM-03: Epic統合完了・リリース" \
  --body "$(cat <<'EOF'
## Milestone: EM-03

| Field | Value |
|-------|-------|
| Target Date | 2026-03-15 |
| Status | :hourglass: pending |
| Completion | 0% |

## Exit Criteria
- [ ] 全50テストPASS、カバレッジ≥80%
- [ ] Ops Pack完成（transport/rollback/hypercare）
- [ ] Final Gate承認
EOF
)"
```

### Step 3: WI Issues

```bash
gh issue create \
  --title "[WI] WI-ERP-SAMPLE-001: 受注登録画面のUI改善" \
  --label "work-item,mode:autopilot,risk:ui_only,tier:standard,status:done,ops-ready" \
  --milestone "Gate 5: Tasking Review" \
  --assignee yamada \
  --body "$(cat <<'EOF'
## Work Item

| Field | Value |
|-------|-------|
| WI ID | WI-ERP-SAMPLE-001 |
| Feature | FEAT-ERP-OMS |
| Mode | autopilot |
| Complexity | low |
| Risk Flags | ui_only |

## Intent
受注登録画面の登録ボタン配置改善と確認ダイアログの追加

## Acceptance Criteria
- [x] AC-US-FEATERPOMS-001-02: 確認ダイアログが表示される

## Run Results
- Run: RUN-001 :white_check_mark:
- Tests: 50/50 PASS
- Coverage: 83.6%
- Walkthrough: completed

## Status: DONE :white_check_mark:
EOF
)"

gh issue create \
  --title "[WI] WI-ERP-SAMPLE-002: 権限チェックロジック追加" \
  --label "work-item,mode:validate,risk:authz,risk:audit_log,tier:standard,status:pending,ops-not-ready,priority:high" \
  --milestone "Gate 5: Tasking Review" \
  --assignee yamada \
  --body "$(cat <<'EOF'
## Work Item

| Field | Value |
|-------|-------|
| WI ID | WI-ERP-SAMPLE-002 |
| Feature | FEAT-ERP-OMS |
| Mode | validate |
| Complexity | high |
| Risk Flags | authz, audit_log |

## Intent
RBAC権限マトリクス・金額別承認フロー・SoD検証・監査ログの実装

## Acceptance Criteria
- [ ] AC-US-FEATERPOMS-002-01: 金額別3段階承認フロー
- [ ] AC-US-FEATERPOMS-002-02: 全操作の監査ログ出力

## Blockers
- 設計レビュー待ち（Pre-Run承認が必要）

## Status: PENDING :hourglass:
EOF
)"
```

### Step 4: Risk Issues

```bash
gh issue create \
  --title "[RISK] ER-001: mcframe API月次締め応答遅延" \
  --label "risk,priority:medium,status:in-progress" \
  --body "$(cat <<'EOF'
## Risk: ER-001

| Dimension | Level |
|-----------|-------|
| Probability | :red_circle: High |
| Impact | :orange_circle: Medium |
| Status | mitigating |

## Description
mcframe API月次締め期間（25日-末日）の応答遅延

## Mitigation
- リトライ間隔延長（3s→10s）
- アラート閾値緩和
- PENDING_STOCK状態でのフォールバック実装済み

## Owner
TEAM-SALES (@suzuki)
EOF
)"

gh issue create \
  --title "[RISK] ER-002: 権限チェック実装→セキュリティリスク" \
  --label "risk,priority:high,status:pending" \
  --body "$(cat <<'EOF'
## Risk: ER-002

| Dimension | Level |
|-----------|-------|
| Probability | :orange_circle: Medium |
| Impact | :red_circle: High |
| Status | open |

## Description
権限チェック実装の複雑さによるセキュリティリスク

## Mitigation
- authz_matrix.yamlでの宣言的権限定義
- validate modeでの設計レビュー必須化

## Owner
TEAM-SALES (@suzuki)
EOF
)"

gh issue create \
  --title "[RISK] ER-003: 監査ログ欠落→コンプライアンス違反" \
  --label "risk,priority:high,status:pending" \
  --body "$(cat <<'EOF'
## Risk: ER-003

| Dimension | Level |
|-----------|-------|
| Probability | :green_circle: Low |
| Impact | :red_circle: High |
| Status | open |

## Description
監査ログの欠落によるコンプライアンス違反

## Mitigation
- ミドルウェアでの自動ログ出力
- TS-INT-04での全操作パターン検証

## Owner
TEAM-SALES (@suzuki)
EOF
)"
```

### Step 5: Sync to Projects

```bash
python scripts/sync_stride_to_projects.py --all
```

---

## 8. ワークフロー図

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          GitHub Projects V2                             │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │ Epic        │  │ Kanban      │  │ Risk        │  │ Milestone    │  │
│  │ Overview    │  │ Board       │  │ Heatmap     │  │ Timeline     │  │
│  │ (Table)     │  │ (Board)     │  │ (Table)     │  │ (Roadmap)    │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘  │
│         │                │                │                │           │
│         └────────────────┴────────────────┴────────────────┘           │
│                                   │                                     │
│                                   ▼                                     │
│                         GitHub Issues                                   │
│                    [EPIC] [WI] [MS] [RISK]                              │
│                    Labels + Milestones + Fields                         │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                  ┌─────────┴─────────┐
                  │  stride-sync.yml  │  (GitHub Actions)
                  │  Forward Sync     │
                  │  ─────────────    │
                  │  Reverse Sync     │
                  │  stride-reverse   │
                  └─────────┬─────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────────────┐
│                        SDD File System (SSoT)                           │
│                                                                         │
│  epics/EPIC-SAMPLE/              specs/sample_erp_addon/                │
│  ├── PM_DASHBOARD.md             ├── state/state.yaml                   │
│  ├── epic_design.md              ├── work_items/WI-*.md                 │
│  ├── feature_breakdown.md        ├── contracts/api.yaml                 │
│  ├── EPIC_PROGRESS_REPORT.md     ├── tests/scenarios.yaml              │
│  ├── DEPENDENCY_MANIFEST.yaml    ├── runs/WI-*/RUN-*/                  │
│  ├── OPS_PACK_REGISTRY.yaml      └── ops/                              │
│  └── EPIC_APPROVAL.md                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. PM チェックリスト

PMが日常的に確認すべき項目:

### Daily

- [ ] Kanban Board で WI の進捗確認
- [ ] ブロッカー Issue の確認
- [ ] `python sdd-templates/tools/epic_progress_aggregator.py epics/EPIC-SAMPLE/`

### Weekly

- [ ] EPIC_PROGRESS_REPORT.md の更新
- [ ] PM_DASHBOARD.md のステータス確認
- [ ] Risk Issue の棚卸し
- [ ] Dependency Status の確認
- [ ] 次週のAction Items確認

### Milestone

- [ ] Exit Criteria の充足確認
- [ ] Gate 承認状態の確認
- [ ] Ops Readiness の確認
- [ ] ステアリング会議報告準備

### Go-Live

- [ ] Go-Live Checklist 全項目確認
- [ ] Ops Pack Registry 100%確認
- [ ] Final Integration Test 完了
- [ ] Go/No-Go Decision

---

## 10. Automation

### stride-sync.yml（Forward Sync）

`state.yaml` の変更を GitHub Projects に自動反映:

```yaml
# .github/workflows/stride-sync.yml
on:
  push:
    paths: ['specs/**/state/state.yaml']
```

### stride-reverse-sync.yml（Reverse Sync）

GitHub Projects の変更をファイルに反映（手動 or スケジュール）:

```yaml
# .github/workflows/stride-reverse-sync.yml
on:
  workflow_dispatch:
    inputs:
      feature: { required: true }
      prefer: { type: choice, options: [auto, file, projects] }
```

### stride-lint.yml

PR作成時に SDD 準拠チェック:

```yaml
# .github/workflows/stride-lint.yml
on:
  pull_request:
    paths: ['specs/**']
```
