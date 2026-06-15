---
description: basic_design.md (canonical schema 準拠) + process.bpmn (BPMN MUST-DO 厳守) を完成させる。upstream-bridge の skeleton を Phase 1 完成形に育てる。起動時に必要 Python dev 依存を自動検出し、未 install の場合は pip install を提案する。
argument-hint: "<feature_name>"
---

# /stride:design

`basic-design-authoring` + `bpmn-authoring` の 2 skills を順次起動し、Phase 1 (basic_design.md + process.bpmn) を完成させます。

> Phase F-1 緊急 改修 (WI-VALF01-013 / 改善要望-12): 起動時に必要 Python dev 依存を自動検出し、未 install の場合は pip install を提案する workflow を追加。

## Usage

```
/stride:design <feature_name>
```

## Workflow

### 0. ★ Dev 依存関係自動検出 (WI-013、改善要望-12)

`basic-design-authoring` + `bpmn-authoring` skills が必要とする Python dev 依存を起動時に自動検出。未 install の場合は **pip install を提案** し、コンサル承認後に install を実行する。

```bash
# 0-A. 必要 Python module を import チェック
REQUIRED_MODULES=(
  "yaml"        # PyYAML — basic_design.md canonical YAML 解析
  "jsonschema"  # JSON Schema — process.bpmn / state.yaml 検証 (補助)
  "markdown"    # Markdown レンダリング (HTML 出力 helper / WI-011 で使用)
  "jinja2"      # テンプレレンダリング (HTML 出力 helper)
)

missing_modules=()
for module in "${REQUIRED_MODULES[@]}"; do
  if ! python3 -c "import ${module}" 2>/dev/null; then
    missing_modules+=("${module}")
  fi
done

# 0-B. 未 install 依存があれば提案
if [ ${#missing_modules[@]} -gt 0 ]; then
  pip_packages=()
  for m in "${missing_modules[@]}"; do
    case "$m" in
      yaml) pip_packages+=("pyyaml") ;;
      jsonschema) pip_packages+=("jsonschema") ;;
      markdown) pip_packages+=("markdown") ;;
      jinja2) pip_packages+=("jinja2") ;;
    esac
  done
  echo "ℹ /stride:design は次の Python 依存を要求します:"
  printf '   - %s\n' "${pip_packages[@]}"
  echo ""
  echo "未 install のため、次のコマンドで install してください:"
  echo "   pip install ${pip_packages[*]}"
  echo ""
  echo "(コンサルへ): install を実施した後、再度 /tecnos-stride-value:stride-design ${1:-<feature_name>} を実行してください。"
  exit 2  # 提案のみ。コンサルが手動 install → 再実行する想定
fi

echo "✅ Python dev 依存揃っています (${#REQUIRED_MODULES[@]} modules OK)"
```

> **注**: AI が自動で `pip install` を実行することは権限境界の関係で**しない**。コンサル環境で実行する `pip install` を **提案** するに留める。

### 1. Validate Input
- `upstream-bridge` (`/stride:bridge`) で生成された `basic_design.md` skeleton が存在
- BPMN-TASK 候補リストが Cowork セッションのコンテキストに残っている

### 2. Trigger Skills

#### 2.1 `basic-design-authoring`

`basic_design.md` の canonical YAML 全セクションを埋める:
- frontmatter (feature_id / basic_design_id / title / profile / version)
- basic_design (profile / coverage_tier / autonomy_bias / ed_cf_score / organization / delivery_model / raci_plus / context / business_domain / scope / systems / data_policy / agentops_policy / e2e_policy / integration_flows / traceability_rows / open_questions / assumptions / decisions / exceptions)
- `basic_design_gate_check` の全 booleans 真化 (process_bpmn_approved / ready_for_specify は Gate 2 後)

#### 2.2 `bpmn-authoring` (v0.4.0 で `bpmn/` パッケージ統合)

`process.bpmn` を BPMN MUST-DO (FEAT 14 / EPIC 9) 厳守で作成。**plugin 同梱の `bpmn/` パッケージ** を直接参照:

- **テンプレからコピー** (zero from scratch 禁止)
  - FEAT: `${CLAUDE_PLUGIN_ROOT}/bpmn/templates/process_bpmn_template.bpmn`
  - EPIC: `${CLAUDE_PLUGIN_ROOT}/bpmn/templates/epic_flow_template.bpmn`
- **MUST-DO 14 項目を `bpmn/rules/bpmn_quick_reference.md` で確認**
- **詳細仕様** は `bpmn/rules/bpmn_generator_rules.md` (§24 で Tecnos override = 縦型 / pool-lane / BPMN-* ID 厳守)
- **深堀り** は `bpmn/spec/camunda_bpmn_dictionary_complete.md` (OMG + Camunda 8.9 全要素辞書 2744 行)
- BPMN-PROC-<FEATUREID> 自動置換、全 task / event / gateway に incoming/outgoing、XOR は default + conditionExpression、BPMNShape / BPMNEdge 完全性、participant の `isHorizontal="false"` (vertical swimlane 強制)
- `basic_design.bpmn_descriptions[].bpmn_id` と完全一致
- 完成時: **`/stride:bpmn-validate <feature_name>`** または `python3 ${CLAUDE_PLUGIN_ROOT}/bpmn/validators/bpmn_lint.py specs/<feature>/process.bpmn` で機械検証 → PASS まで修正

### 3. Output

- `specs/<feature>/basic_design.md` (canonical YAML 全セクション populated)
- `specs/<feature>/process.bpmn` (BPMN MUST-DO 14 項目クリア、`bpmn/validators/bpmn_lint.py` で PASS)
- `bpmn_descriptions` セクションが BPMN element と完全一致

### 4. Next Step

- BPMN 単独検証: `/stride:bpmn-validate <feature_name>` (高速、validator のみ)
- 全体検証: `/stride:validate <feature_name>` (BACCM 6 軸 + 4-layer + Phase 1 整合性 + BPMN 検証)
- 必要時: `/stride:epic-init <EPIC_ID>` で Epic 階層判定
- そのまま: `/stride:handoff <feature_name>` で Claude Code 引き渡し

> Phase G+ v0.4.0 で `bpmn/` パッケージ (rules + spec + templates + examples + validators) を plugin に統合。BPMN 作成は `bpmn/` を first-class reference として参照。
> Phase F (WI-VALF01-013) で起動時 dev 依存自動検出。Phase E v0.1.0-poc → v0.2.0-stable → v0.3.x → v0.4.0。
