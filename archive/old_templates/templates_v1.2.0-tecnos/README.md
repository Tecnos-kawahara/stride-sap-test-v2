# SDD Template Pack (Tecnos v1.2.0-tecnos)

本パックは、Specification-Driven Development (SDD) を **Tecnos Japan の実務**（全社横断PJ／ERP・SCM・CRM／CBP／AgentOps）に適用するためのテンプレート一式です。

- **仕様（Spec）が一次成果物**であり、Plan/Tasks/Code は仕様からの生成物です。
- **basic_design.md** は、人間の任意テキストを受けて AI が SDD（BPMN → Spec/Plan/Tasks）へ落とす前に、認識齟齬を潰す **HITLハブ**です。
- **process.bpmn** は **Camunda 8 (Zeebe 8.8) 仕様**の BPMN 2.0 XML であり、HITL承認済みのフロー正本として扱います。

## Contents
- `templates/basic_design_template.md` : HITLハブ（Human-editable Canonical YAML + Gate）
- `templates/spec_template.md` : WHAT/WHY（Canonical YAML + Spec Gate）
- `templates/plan_template.md` : HOW（Canonical YAML + Plan Gate、BPMN mapping を含む）
- `templates/tasks_template.md` : 実行可能タスク（Canonical YAML + Tasks Gate）
- `policies/bpmn_generator_rules.md` : Camunda 8 (Zeebe 8.8) BPMN 2.0 生成ルール（executionPlatform 強制）
- `examples/process_bpmn_template.bpmn` : DI付きの最小 Camunda 8 BPMN スケルトン
- `memory/constitution.md` : Nine Articles + ID規約 + Gates（Tecnos拡張）
- `memory/tecnos_org_constraints.md` : Tecnos 組織制約（ERP/SCM/CRM統合、監査、運用、AgentOpsガードレール）
- `tools/speckit_lint_spec.md` : speckit-lint 仕様（Basic Design + Camunda platform checks + Tecnos拡張）

## Recommended Workflow（最短導線）
1. `basic_design.md` を作成（テンプレ適用）し、#0 Canonical YAML を埋める  
   - `traceability_rows` を最低1行  
   - `integration_flows` を最低1件  
   - ブロッキング質問（blocking=true）を 0 件に  
   - `basic_design_gate_check.ready_for_bpmn = true` を立てる
2. `process.bpmn` を Camunda 8 形式で作成（または生成）し、HITL承認  
   - `process_bpmn_linked = true` / `process_bpmn_approved = true`  
   - 承認後に `ready_for_specify = true`
3. `spec.md` を作成し、blocking open questions を 0 にして `spec_gate_check.ai_plan_ready = true`
4. `plan.md` を作成し、contracts/tests/phases/groups を stable id で確定して `plan_gate_check.ai_tasks_ready = true`
5. `tasks.md` を作成し、全タスクが plan_refs（stable id）を持つ状態にして `tasks_gate_check.tasks_ready_for_code = true`
6. `speckit-lint` を回し、Gate fail を差し戻し条件として運用

## Notes（Tecnos運用の前提）
- 例外（Exceptions）は必ず Constitution の Article に紐付け、`{article, reason, mitigation}` の3点セットで記録します。
- ERP/SCM/CRM 統合は「契約（Contract）・監査（Audit）・運用（Ops）・SoD（職務分掌）」を必須論点とし、`memory/tecnos_org_constraints.md` を参照します。
