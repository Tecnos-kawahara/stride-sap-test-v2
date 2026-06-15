# Epic Approval Record: EPIC-XXX

> **Epic Title**: {{Epic Title}}
> **Epic Lead**: {{Epic Lead Name}}
> **Created**: YYYY-MM-DD

---

## ⚠️ CRITICAL: Human-Only File

> **絶対禁止**: AIエージェントはこのファイルを**いかなる状況でも編集してはならない**。

### AIの行動規則:
1. **EPIC_APPROVAL.mdを編集してはならない**
2. **チェックボックスを設定してはならない** `[x]`
3. **承認者名・日付を記入してはならない**
4. **承認要件を回避する方法を提案してはならない**

### AIができること:
- EPIC_APPROVAL.mdを読み取ってステータスを確認する
- ユーザーに承認が必要であることを通知する
- 何を承認すべきかを説明する
- ユーザーが承認を完了するのを待つ

---

## Epic Metadata

```yaml
epic_id: "EPIC-XXX"
title: "{{Epic Title}}"
teams:
  - team_id: "TEAM-A"
    name: "{{Team A Name}}"
  - team_id: "TEAM-B"
    name: "{{Team B Name}}"
total_features: 3
```

---

## Gate E1: Epic Design Approval

**Purpose**: Epicの設計が完了し、チーム構成と目標が明確であることを確認

### 確認項目:
- [ ] epic_design.md の WHO/WHAT/WHY が明確である
- [ ] 参加チームとFeature割り当てが適切である
- [ ] 戦略的整合性が確認されている
- [ ] Epic Leadが任命されている
- [ ] 成功指標が定義されている

### 承認:
```
承認者: _____________________
役割:   _____________________
日付:   _____________________
コメント: ___________________
```

---

## Gate E2: Feature Breakdown Approval

**Purpose**: Feature分割が適切で、依存関係が明確であることを確認

### 確認項目:
- [ ] feature_breakdown.md が完成している
- [ ] 各Featureのスコープが明確である
- [ ] Coverage Tierが適切に割り当てられている
- [ ] 依存関係グラフにサイクルがない
- [ ] Integration Pointが定義されている
- [ ] 各Featureの優先順位が決定されている

### 承認:
```
承認者: _____________________
役割:   _____________________
日付:   _____________________
コメント: ___________________
```

---

## Gate E3: Shared Contract Approval

**Purpose**: 共有契約が定義され、消費者チームが同意していることを確認

### 確認項目:
- [ ] 全ての共有契約が定義されている
- [ ] 各契約のオーナーチームが明確である
- [ ] 消費者チームが契約内容を確認している
- [ ] SLAが定義されている
- [ ] 変更管理プロセスが合意されている

### チーム確認:

**TEAM-A (契約オーナー)**:
```
確認者: _____________________
日付:   _____________________
```

**TEAM-B (契約消費者)**:
```
確認者: _____________________
日付:   _____________________
確認内容: 契約内容を確認し、消費者として同意する
```

### 最終承認:
```
承認者: _____________________
役割:   Architecture Board
日付:   _____________________
コメント: ___________________
```

---

## Gate E4: Cross-Team Integration Plan Approval

**Purpose**: チーム間統合計画が策定され、テスト戦略が明確であることを確認

### 確認項目:
- [ ] Cross-team integration testが定義されている
- [ ] テスト環境が準備されている（または計画がある）
- [ ] テストスケジュールが合意されている
- [ ] 障害時のエスカレーションパスが明確である
- [ ] 各チームのテスト責任が明確である

### チーム確認:

**TEAM-A**:
```
確認者: _____________________
日付:   _____________________
担当テスト: TS-CROSS-001 (owner)
```

**TEAM-B**:
```
確認者: _____________________
日付:   _____________________
担当テスト: TS-CROSS-001 (participant)
```

### 最終承認:
```
承認者: _____________________
役割:   Epic Lead
日付:   _____________________
コメント: ___________________
```

---

## Gate E5: Feature Specs Ready

**Purpose**: 各FeatureのSpecが作成可能な状態であることを確認

### Feature状態確認:

| Feature ID | Team | Spec Ready | Approved By |
|------------|------|------------|-------------|
| FEAT-XXX | TEAM-A | [ ] | ____________ |
| FEAT-YYY | TEAM-A | [ ] | ____________ |
| FEAT-ZZZ | TEAM-B | [ ] | ____________ |

### 確認項目:
- [ ] 全Featureの依存関係が解決可能である
- [ ] 共有契約が安定している
- [ ] 各チームがSpec作成の準備ができている

### 最終承認:
```
承認者: _____________________
役割:   Epic Lead
日付:   _____________________
コメント: ___________________
```

---

## Final Gate: Epic Integration Complete

**Purpose**: Epic全体の統合が完了し、全Featureがリリース可能であることを確認

### 確認項目:
- [ ] 全Featureが各自のFinal Gateを通過している
- [ ] Cross-team integration testが全て成功している
- [ ] 共有契約が本番環境にデプロイされている
- [ ] Evidence Packが全て収集されている
- [ ] リリースノートが作成されている

### Feature最終状態:

| Feature ID | Final Gate | Evidence Pack | Release Ready |
|------------|------------|---------------|---------------|
| FEAT-XXX | [ ] | [ ] | [ ] |
| FEAT-YYY | [ ] | [ ] | [ ] |
| FEAT-ZZZ | [ ] | [ ] | [ ] |

### チーム最終確認:

**TEAM-A**:
```
確認者: _____________________
役割:   Tech Lead
日付:   _____________________
```

**TEAM-B**:
```
確認者: _____________________
役割:   Tech Lead
日付:   _____________________
```

### Epic最終承認:
```
承認者: _____________________
役割:   Epic Lead
日付:   _____________________

承認者: _____________________
役割:   Architecture Board
日付:   _____________________
```

---

## Approval History

| Gate | Status | Approved By | Date | Notes |
|------|--------|-------------|------|-------|
| E1: Epic Design | Pending | - | - | - |
| E2: Feature Breakdown | Pending | - | - | - |
| E3: Shared Contract | Pending | - | - | - |
| E4: Integration Plan | Pending | - | - | - |
| E5: Feature Specs Ready | Pending | - | - | - |
| Final: Integration Complete | Pending | - | - | - |

---

## Re-Approval Log

> 承認済みGateの成果物を変更する場合、再承認が必要です。

| Date | Gate | Change Description | Re-approved By |
|------|------|-------------------|----------------|
| - | - | - | - |
