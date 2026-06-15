# Upstream Dogfooding Lessons — prototype profile (Pilot 01)

**Status:** scaffold (検証手順 + lessons 構造を整備、実 dogfooding は Phase F PR merge 後に Hitoshi さん follow-up)
**Phase F WI:** WI-VALF01-007
**Gap reference:** Gap-F-007 (Test-3 prototype profile 検証)
**AC:** AC-US-FEATVALF01-007-01

## 1. 検証目的

Cowork Plugin v0.2.0-stable を **prototype profile** (`shared/policies/profile_policy.yaml` で定義、軽量化 path) に従って 1 PoC 案件で端到端実行し、軽量 path の有効性 + ハッピーパスの完走 + lessons を sanitized 形式で記録する。

prototype profile は enterprise-erp / saas-integration よりも閾値を **緩和** し (line counts +100、files +3)、Discovery lite モード + Epic 不要判定 + 過度なドキュメント化なしで rapid prototyping 案件に適合させる軽量プロファイル。

## 2. PoC 案件選定 (Q-102)

`Q-102` (specs/val_f01/spec.md) で確認中。候補基準:

- 顧客 PJ が **検証フェーズ / 提案前 PoC / 内製 prototype** であり、本格運用ドキュメントは Phase G 以降想定
- スコープが **1 機能 / 1 ユースケース** (Epic 階層化不要)
- 上位コンサル単独で **1 週間以内に Phase 0 → Phase 1 完成可能** な規模

## 3. 検証手順 (Hitoshi さん follow-up タスク)

### 3-A. prototype profile 起動

```bash
claude -p --plugin-dir ./cowork-plugin "/tecnos-stride-value:stride-init <feature_name> --profile prototype"
```

### 3-B. 軽量 path commands 実行

```
/tecnos-stride-value:stride-discovery <feature_name>      # lite モード (BACCM 6 軸の 4 軸のみ)
/tecnos-stride-value:stride-context-model <feature_name>  # Layered Requirements Modeling 簡略 (BUC のみ)
/tecnos-stride-value:stride-validate <feature_name>
/tecnos-stride-value:stride-bridge <feature_name>
/tecnos-stride-value:stride-design <feature_name>         # basic_design.md 軽量版
                                                          # /stride:epic-init は不要 (prototype profile では Epic 階層化なし)
/tecnos-stride-value:stride-handoff <feature_name>
/tecnos-stride-value:stride-tasking <feature_name>        # Phase F 新規 (WI-VALF01-016)
```

### 3-C. 検証ポイント

- [ ] prototype profile の閾値 (line counts +100、files +3) が適用されているか
- [ ] BACCM 6 軸の 4 軸のみで Discovery 完了判定が出るか (lite モード)
- [ ] Epic 階層化が不要と判定されるか (epic-decomposition skill が "不要" を返すか)
- [ ] 過度なドキュメント化が抑制されているか (basic_design.md の sections が必要最小限か)
- [ ] handoff workflow + サニタイズ grep が prototype 案件でも動作するか

## 4. 期待される Sanitized Lessons (構造、実データは follow-up 後に追記)

```yaml
# Hitoshi さん follow-up 後に本セクションに追記する想定の構造
prototype_pilot_01:
  pilot_id: proto-01
  profile: prototype
  phase_completed: phase_1
  duration_days: <number>           # 1 週間以内想定
  basic_design_status: completed_lite
  bpmn_status: minimal              # prototype profile は BPMN MUST-DO の最小集合のみ
  epic_decomposed: false            # prototype は Epic 階層化なし
  lessons:
    what_worked_well:
      - "<sanitized lesson>"
    what_did_not_work:
      - "<sanitized lesson>"
    overhead_observations:           # prototype profile の軽量性が機能したか
      - "<observation>"
    recommendations_for_phase_g:
      - "<recommendation>"
  follow_up_actions:
    - "<action item>"
```

## 5. 既知制約

- **AI 単独では実 dogfooding 完了不可**: PoC 案件選定 + 上位コンサル稼働は人間タスク。
- **実 dogfooding は Phase F PR merge 後**: Hitoshi さん follow-up として、本ファイルに実検証結果を §4 へ追記して closure。
- **§Rule 15-B サニタイズ厳守**: 顧客固有データは本ファイルに記録しない。

## 6. Closure 条件

以下 4 件すべて完了で本 lessons file は **completed** ステータスに移行:

- [ ] PoC 案件確保 (Q-102 closure、Hitoshi さん + Tecnos AI チーム)
- [ ] 軽量 path commands 順次実行 + Phase 0 → Phase 1 完成 (1 週間以内)
- [ ] §4 sanitized lessons の追記
- [ ] state.yaml `final.evidence_pack_done: true` への更新 (Phase F merge 後の追加 PR にて)

## 7. References

- Phase F prompt §4-3-D (saas-integration / prototype 実機テスト)
- `shared/policies/profile_policy.yaml` (prototype profile 閾値定義 = ERP の 50% 閾値)
- `cowork-plugin/skills/epic-decomposition/SKILL.md` (Epic 不要判定基準)
- `specs/val_f01/spec.md` US-FEATVALF01-007 + AC-US-FEATVALF01-007-01

> Phase F (WI-VALF01-007) で prototype profile dogfood lessons の scaffold を整備。実 dogfooding は Hitoshi さん follow-up。
