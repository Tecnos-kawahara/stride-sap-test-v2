# Upstream Dogfooding Lessons — saas-integration profile (Pilot 01)

**Status:** scaffold (検証手順 + lessons 構造を整備、実 dogfooding は Phase F PR merge 後に Hitoshi さん follow-up)
**Phase F WI:** WI-VALF01-006
**Gap reference:** Gap-F-006 (Test-2 saas-integration profile 検証)
**AC:** AC-US-FEATVALF01-006-01

## 1. 検証目的

Cowork Plugin v0.2.0-stable を **saas-integration profile** (`shared/policies/profile_policy.yaml` で定義) に従って 1 PoC 案件で端到端実行し、playbook の有効性 + ハッピーパスの完走 + lessons を sanitized 形式で記録する。

enterprise-erp profile は fc-sd 案件 (Phase F の改善要望源) で dogfood 完了済 (lessons は Hitoshi さん内部メモに保管、本リポジトリには §Rule 15-B サニタイズ後のもののみ転記)。本ファイルは **saas-integration profile** の dogfood lessons の SSoT。

## 2. PoC 案件選定 (Q-102)

`Q-102` (specs/val_f01/spec.md) で確認中。Phase F-2 着手時 (2026-05-15 までに) Tecnos AI チームが
saas-integration profile に適合する PoC 案件を 1 件確保する。候補基準:

- 顧客 PJ の中核が **SaaS-to-SaaS / SaaS-to-ERP の統合** (Salesforce ↔ kintone、Workday ↔ SAP 等)
- データフローが **API-first / Event-driven**
- 上位コンサル + 開発チームが **2-3 週間で Phase 0 → Phase 1 完成可能** な規模

(候補案件の固有名詞は §Rule 15-B 準拠で本ファイルには記録しない、Hitoshi さん内部メモで管理)

## 3. 検証手順 (Hitoshi さん follow-up タスク)

### 3-A. saas-integration profile 起動

```bash
# Plugin v0.2.0-stable 候補 install 済 + dev 依存揃っている前提
claude -p --plugin-dir ./cowork-plugin "/tecnos-stride-value:stride-init <feature_name> --profile saas-integration"
```

### 3-B. 8 commands 順次実行

```
/tecnos-stride-value:stride-discovery <feature_name>
/tecnos-stride-value:stride-elicit <feature_name>
/tecnos-stride-value:stride-context-model <feature_name>
/tecnos-stride-value:stride-validate <feature_name>
/tecnos-stride-value:stride-bridge <feature_name>
/tecnos-stride-value:stride-design <feature_name>
/tecnos-stride-value:stride-epic-init <EPIC_ID>     # 必要時のみ
/tecnos-stride-value:stride-handoff <feature_name>
/tecnos-stride-value:stride-tasking <feature_name>  # Phase F 新規 (WI-VALF01-016)
```

### 3-C. 検証ポイント

- [ ] saas-integration profile 固有の閾値 (line counts +150、Discovery 簡略化) が適用されているか
- [ ] BACCM 6 軸完成度がプロファイル別に判定されているか (`shared/policies/baccm_completeness.yaml` 参照)
- [ ] 上位コンサル単独で 2-3 週間で Phase 0 → Phase 1 完成可能か
- [ ] handoff サニタイズ grep (WI-VALF01-004) が saas-integration profile でも誤検出を出さないか
- [ ] CI workflow (WI-VALF01-002) が PR で trigger され Green になるか

## 4. 期待される Sanitized Lessons (構造、実データは follow-up 後に追記)

```yaml
# Hitoshi さん follow-up 後に本セクションに追記する想定の構造
saas_integration_pilot_01:
  pilot_id: saas-int-01
  profile: saas-integration
  phase_completed: phase_1
  duration_days: <number>           # 2-3 週間想定
  basic_design_status: completed
  bpmn_status: completed
  lessons:
    what_worked_well:
      - "<sanitized lesson>"
    what_did_not_work:
      - "<sanitized lesson>"
    surprises:
      - "<sanitized lesson>"
    recommendations_for_phase_g:
      - "<recommendation>"
  follow_up_actions:
    - "<action item>"
```

## 5. 既知制約

- **AI 単独では実 dogfooding 完了不可**: PoC 案件選定 + 上位コンサル稼働は人間タスク。AI は本ファイルで scaffold + 検証手順 + lessons 構造を提供するに留まる。
- **実 dogfooding は Phase F PR merge 後**: Hitoshi さん follow-up として、本ファイルに実検証結果 (sanitized lessons) を §4 へ追記して closure。
- **§Rule 15-B サニタイズ厳守**: 顧客名 / 案件 ID / 担当者名 / 金額 / 契約番号は本ファイルに記録しない。`memory/projects/<project>/...` などの内部メモで管理。

## 6. Closure 条件

以下 4 件すべて完了で本 lessons file は **completed** ステータスに移行:

- [ ] PoC 案件確保 (Q-102 closure、Hitoshi さん + Tecnos AI チーム)
- [ ] 8 commands 順次実行 + Phase 0 → Phase 1 完成
- [ ] §4 sanitized lessons の追記 (`yaml` ブロック内のプレースホルダを実値で置換)
- [ ] state.yaml `final.evidence_pack_done: true` への更新 (Phase F merge 後の追加 PR にて)

## 7. References

- Phase F prompt §4-3-D (saas-integration / prototype 実機テスト)
- `shared/policies/profile_policy.yaml` (saas-integration profile 閾値定義)
- `shared/policies/baccm_completeness.yaml` (BACCM 完成度判定)
- `cowork-plugin/commands/stride-init.md` (`--profile` フラグ)
- `specs/val_f01/spec.md` US-FEATVALF01-006 + AC-US-FEATVALF01-006-01

> Phase F (WI-VALF01-006) で saas-integration profile dogfood lessons の scaffold を整備。実 dogfooding は Hitoshi さん follow-up。
