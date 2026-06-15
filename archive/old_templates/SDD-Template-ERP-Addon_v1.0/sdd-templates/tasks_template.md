---
template: tasks
feature_id: FEAT-ERP-{{DOMAIN}}-{{NNN}}
rule:
  - "tasks are coding-focused; operations artifacts live under ops/"
  - "every test spec must be represented by a task"
work_items:
  - wi_id: WI-ERP-{{FEATURE_ID}}-001
    title: "{{...}}"
    depends_on: []
milestones:
  - name: "Gate5 Approved"
  - name: "All WI Done"
---

# Tasks (coding-focused)
1. Setup scaffold (src/, config)
2. Implement WI-001
3. Add/Update tests (TS-*)
4. Run CI + fix
5. Prepare ops pack (transport/release checklist)
