---
description: process.bpmn / epic_flow.bpmn を bpmn/validators/bpmn_lint.py で直接機械検証 (FEAT 14 + EPIC 9 MUST-DO)。/stride:validate より高速、BPMN だけ検証したい時に使用。
argument-hint: "<feature_name> [--epic|--feat]"
---

# /stride:bpmn-validate

`bpmn/validators/bpmn_lint.py` (stdlib のみ依存の単独 Python validator) を直接呼び出し、BPMN ファイルを機械検証します。`/stride:validate` の BACCM 全体検証は不要、**BPMN だけ検証したい時** に高速に使えます。

> Phase G+ v0.4.0 で新規追加。`bpmn/` パッケージ (plugin 同梱) の validator を活用する直接 lint コマンド。

## Usage

```bash
# auto-detect (collaboration + 2+ participant で EPIC、それ以外 FEAT)
/stride:bpmn-validate <feature_name>

# モード強制
/stride:bpmn-validate <feature_name> --feat
/stride:bpmn-validate <epic_name> --epic
```

## Workflow

### 1. Validate Input
- 引数 `<feature_name>` または `<epic_name>` を受領
- `specs/<feature_name>/process.bpmn` (FEAT) または `epics/<epic_name>/epic_flow.bpmn` (EPIC) の存在確認

### 2. ファイル特定 (auto-detect)

```bash
FEATURE_ARG="${1:?feature name required}"
MODE_ARG="${2:-auto}"  # --feat / --epic / auto

# FEAT 候補
FEAT_PATH="specs/${FEATURE_ARG}/process.bpmn"
# EPIC 候補
EPIC_PATH="epics/${FEATURE_ARG}/epic_flow.bpmn"

if [ -f "$FEAT_PATH" ]; then
  TARGET="$FEAT_PATH"
  DEFAULT_KIND="feat"
elif [ -f "$EPIC_PATH" ]; then
  TARGET="$EPIC_PATH"
  DEFAULT_KIND="epic"
else
  echo "❌ BPMN ファイルが見つかりません: $FEAT_PATH または $EPIC_PATH"
  exit 1
fi
```

### 3. validator 実行

```bash
LINT_SCRIPT="${CLAUDE_PLUGIN_ROOT}/bpmn/validators/bpmn_lint.py"

if [ ! -f "$LINT_SCRIPT" ]; then
  echo "❌ bpmn_lint.py が見つかりません: $LINT_SCRIPT"
  echo "   plugin が正しくインストールされているか確認してください。"
  exit 2
fi

# モード判定
case "$MODE_ARG" in
  --feat) MODE_FLAG="--feat" ;;
  --epic) MODE_FLAG="--epic" ;;
  *) MODE_FLAG="" ;;  # auto-detect
esac

# 検証実行 (Python 3.7+ stdlib のみ)
python3 "$LINT_SCRIPT" $MODE_FLAG "$TARGET"
LINT_EXIT=$?

if [ $LINT_EXIT -eq 0 ]; then
  echo ""
  echo "✅ BPMN lint PASS — Gate 2 (BPMN) 承認に進めます"
  echo "   次は: /stride:validate ${FEATURE_ARG} で BACCM 全体検証"
else
  echo ""
  echo "❌ BPMN lint FAIL — エラーを修正して再実行してください"
  echo "   - ルール参照: ${CLAUDE_PLUGIN_ROOT}/bpmn/rules/bpmn_quick_reference.md"
  echo "   - エラーコード詳細: ${CLAUDE_PLUGIN_ROOT}/bpmn/validators/README.md"
  exit $LINT_EXIT
fi
```

### 4. JSON 出力モード (CI 統合用)

```bash
/stride:bpmn-validate <feature_name> --json
# → JSON 形式 (errors / warnings / passed flag) を stdout に出力
```

機械処理向け:

```bash
RESULT=$(python3 "$LINT_SCRIPT" --json "$TARGET")
PASSED=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['passed'])")
if [ "$PASSED" = "True" ]; then
  echo "PASS"
fi
```

## 検証ルール (要約)

### FEAT (`process.bpmn`) — 14 MUST-DO
詳細は `${CLAUDE_PLUGIN_ROOT}/bpmn/rules/bpmn_quick_reference.md` を参照。主要項目:

1. namespace (zeebe / modeler / xsi / bpmn / bpmndi)
2. `executionPlatform="Camunda Cloud"` + `executionPlatformVersion=8.x` (8.8/8.9 推奨)
3. `<bpmn:process isExecutable="true">`
4. 全 flow node に `<incoming>` / `<outgoing>`
5. `<bpmn:serviceTask>` は `<zeebe:taskDefinition type="...">`
6. XOR は `default` または全 outgoing に conditionExpression
7. conditionExpression は `xsi:type="bpmn:tFormalExpression"` + `=` で開始 (FEEL)
8. sequenceFlow の sourceRef/targetRef が実在
9. boundaryEvent は `attachedToRef` を持つ
10. timeDuration は ISO-8601
11. BPMNDiagram → BPMNPlane を持つ
12. 全 flow node に BPMNShape、全 sequenceFlow に BPMNEdge
13. participant shape は `isHorizontal="false"` (vertical swimlane、Tecnos override)
14. `<bpmn:documentation>` を process / userTask / serviceTask / 条件付き gateway / 条件付き sequenceFlow に記入 (warning)

### EPIC (`epic_flow.bpmn`) — 9 MUST-DO
1. `<bpmn:collaboration>` 必須
2. `<bpmn:participant>` ≥ 2
3. processRef が実在
4. 内部 process flow node の incoming/outgoing
5. sequenceFlow の sourceRef/targetRef
6. messageFlow の構造
7. BPMNPlane が collaboration を参照
8. participant shape は `isHorizontal="false"`
9. 全要素 BPMNShape / Edge

## いつ使うか

| シーン | 推奨コマンド |
|--------|-------------|
| BPMN 作成中、形式チェック繰り返し | **`/stride:bpmn-validate`** (高速、validator のみ) |
| BPMN 完成、Gate 2 承認直前 | **`/stride:bpmn-validate`** で 0 errors 確認 |
| basic_design + BPMN 全体整合性チェック | `/stride:validate` (BACCM + Phase 1 + BPMN) |
| CI/CD パイプライン | `python3 ${CLAUDE_PLUGIN_ROOT}/bpmn/validators/bpmn_lint.py --json ...` |

## Output

```
BPMN Lint Report (FEAT)
============================================================
PASS: 0 errors, 0 warnings

✅ BPMN lint PASS — Gate 2 (BPMN) 承認に進めます
   次は: /stride:validate <feature> で BACCM 全体検証
```

または FAIL の場合:

```
BPMN Lint Report (FEAT)
============================================================
  ✗ BPMN_VALIDATION_FAILED: specs/foo/process.bpmn: serviceTask missing zeebe:taskDefinition
  ⚠ BPMN_DOCUMENTATION_MISSING: specs/foo/process.bpmn: process 'Process_X' has no <documentation>

FAIL: 1 error, 1 warning

❌ BPMN lint FAIL — エラーを修正して再実行してください
```

## 関連 Skills / Commands

- **`bpmn-authoring`** skill — BPMN 作成本体
- **`/stride:design`** — basic-design + bpmn-authoring 連続起動
- **`/stride:validate`** — BACCM 6 軸 + 4-layer + Phase 1 + BPMN の全体検証
- 直接実行: `python3 ${CLAUDE_PLUGIN_ROOT}/bpmn/validators/bpmn_lint.py path/to/file.bpmn`

> v0.4.0 — bpmn/ パッケージ統合に伴い新設。BPMN 作成のフィードバックループを高速化する直接 lint command。
