# validators/ — BPMN Lint Tool

`bpmn_lint.py` は **stdlib のみ依存** の Python script で、Camunda 8 BPMN ファイル (FEAT process.bpmn / EPIC epic_flow.bpmn) を機械検証する。

---

## 動作要件

- **Python 3.7+** (stdlib のみ)
- 外部依存なし (PyPI install 不要)

`requirements.txt` は依存記録用に空ファイルを置いているが、本当に依存はない。

---

## 使い方

### 基本 — auto-detect モード

```bash
python3 bpmn_lint.py path/to/your-process.bpmn
```

`<bpmn:collaboration>` 内の `<bpmn:participant>` 数で FEAT / EPIC を自動判定:
- 0〜1 participant → FEAT (executable BPMN として検証)
- 2+ participants → EPIC (overview BPMN として検証)

### モード強制

```bash
python3 bpmn_lint.py --feat path/to/process.bpmn       # FEAT 強制 (executable BPMN ルール)
python3 bpmn_lint.py --epic path/to/epic_flow.bpmn     # EPIC 強制 (collaboration + multi-pool ルール)
```

### Placeholder チェックを無効化

テンプレートそのものを検証する際など、`{{...}}` や `BPMN-PROC-XXX` を残したまま PASS させたい場合:

```bash
python3 bpmn_lint.py --no-placeholder-check templates/process_bpmn_template.bpmn
```

### 詳細ヘルプ

```bash
python3 bpmn_lint.py --help
```

---

## 出力例

### PASS 例

```
$ python3 bpmn_lint.py examples/process_bpmn_example.bpmn
BPMN Lint Report (FEAT)
============================================================
PASS: 0 errors, 0 warnings
```

### FAIL 例

```
$ python3 bpmn_lint.py broken.bpmn
BPMN Lint Report (FEAT)
============================================================
  ✗ BPMN_VALIDATION_FAILED: broken.bpmn: serviceTask missing zeebe:taskDefinition
  ✗ BPMN_VALIDATION_FAILED: broken.bpmn: XOR missing condition Flow_3
  ⚠ BPMN_DOCUMENTATION_MISSING: broken.bpmn: process 'Process_X' has no <documentation>

FAIL: 2 errors, 1 warning
```

### Exit codes

- `0` — PASS (errors=0)
- `1` — FAIL (errors≥1)
- `2` — File not found / parse error

---

## 検証項目一覧

### FEAT process.bpmn (14 項目、`--feat` モード)

| # | 検証項目 | エラーコード | 必須/警告 |
|---|---------|------------|---------|
| 1 | namespace (zeebe / modeler / xsi / bpmn / bpmndi) | `BPMN_VALIDATION_FAILED` | error |
| 2 | `executionPlatform="Camunda Cloud"` + `executionPlatformVersion=8.x` | `BPMN_VALIDATION_FAILED` | error (8.8/8.9 推奨) |
| 3 | `<bpmn:process isExecutable="true">` | `BPMN_VALIDATION_FAILED` | error |
| 4 | 全 flow node に `<bpmn:incoming>` / `<bpmn:outgoing>` | `BPMN_VALIDATION_FAILED` | error |
| 5 | `<bpmn:serviceTask>` は `<zeebe:taskDefinition type="...">` | `BPMN_VALIDATION_FAILED` | error |
| 6 | `<bpmn:exclusiveGateway>` (2+ outgoing) は default または全 outgoing に conditionExpression | `BPMN_VALIDATION_FAILED` | error |
| 7 | `<bpmn:conditionExpression>` は `xsi:type="bpmn:tFormalExpression"` + 非空 | `BPMN_VALIDATION_FAILED` | error/warn |
| 8 | `<bpmn:sequenceFlow>` の sourceRef/targetRef が実在 | `BPMN_VALIDATION_FAILED` | error |
| 9 | `<bpmn:boundaryEvent>` は `attachedToRef` を持つ + outgoing (compensation 例外) | `BPMN_VALIDATION_FAILED` | error |
| 10 | `<bpmn:timeDuration>` は ISO-8601 (`PT*`/`P*`) | `BPMN_VALIDATION_FAILED` | error |
| 11 | `<bpmndi:BPMNDiagram>` → `<bpmndi:BPMNPlane>` を持つ + plane が process/collaboration を参照 | `BPMN_VALIDATION_FAILED` | error |
| 12 | 全 flow node に BPMNShape、全 sequenceFlow に BPMNEdge | `BPMN_VALIDATION_FAILED` | error |
| 13 | participant shape は `isHorizontal="false"` (vertical swimlane、Tecnos override) | `BPMN_VALIDATION_FAILED` | error |
| 14 | process / userTask / serviceTask / 条件付き gateway / 条件付き sequenceFlow に `<bpmn:documentation>` (Tecnos override) | `BPMN_DOCUMENTATION_MISSING` | warning |

加えて、message catch (除く start) に `correlationKey` 必須、`bpmn:message` の存在チェックも実施。

### EPIC epic_flow.bpmn (9 項目、`--epic` モード)

| # | 検証項目 | エラーコード | 必須/警告 |
|---|---------|------------|---------|
| 1 | `<bpmn:collaboration>` を必ず持つ | `EPIC_BPMN_INVALID` | error |
| 2 | `<bpmn:participant>` ≥ 2 | `EPIC_BPMN_INVALID` | error |
| 3 | 各 participant の `processRef` が実在 process を参照 | `EPIC_BPMN_INVALID` | error |
| 4 | 各 process 内の flow node に `incoming/outgoing` | `EPIC_BPMN_INVALID` | error |
| 5 | sequenceFlow の sourceRef/targetRef が process 内に実在 | `EPIC_BPMN_INVALID` | error |
| 6 | `<bpmn:messageFlow>` に `<bpmn:documentation>` | `EPIC_BPMN_DOCUMENTATION_MISSING` | warning |
| 7 | BPMNPlane の `bpmnElement` が collaboration を参照 | `EPIC_BPMN_INVALID` | warning |
| 8 | 各 participant shape は `isHorizontal="false"` (vertical swimlane、Tecnos override) | `EPIC_BPMN_INVALID` | error |
| 9 | 全 flow node に BPMNShape、全 sequenceFlow/messageFlow に BPMNEdge | `EPIC_BPMN_INVALID` | error |

### Placeholder チェック (両モード)

| パターン | エラーコード | 種別 |
|---------|------------|------|
| `{{...}}` (テンプレート placeholder) | `BPMN_PLACEHOLDER_PRESENT` / `EPIC_BPMN_PLACEHOLDER` | warning |
| `BPMN-PROC-XXX` (FEAT 未置換) | `BPMN_PLACEHOLDER_PRESENT` | warning |
| `EPIC-XXX` (EPIC 未置換) | `EPIC_BPMN_PLACEHOLDER` | warning |

---

## CI 統合例

### GitHub Actions

```yaml
# .github/workflows/bpmn-lint.yml
name: BPMN Lint
on: [pull_request]
jobs:
  bpmn-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Lint BPMN files
        run: |
          for f in $(find . -name "*.bpmn" -not -path "./bpmn/templates/*" -not -path "./bpmn/examples/*"); do
            echo "=== Linting $f ==="
            python3 bpmn/validators/bpmn_lint.py "$f" || exit 1
          done
```

### Pre-commit hook

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: bpmn-lint
      name: BPMN Lint
      entry: python3 bpmn/validators/bpmn_lint.py
      language: system
      files: \.bpmn$
      exclude: ^bpmn/(templates|examples)/
```

---

## 実装の派生元

`bpmn_lint.py` は Tecnos-STRIDE v5.4.0 の以下から抽出・適応:
- `sdd-templates/tools/stride_lint.py` の `validate_bpmn()` (FEAT、L859-1130)
- `sdd-templates/tools/epic_validator.py` の `validate_epic_bpmn()` (EPIC、L471-728)

stride_lint.py の依存 (`stride_shared_lib`、Phase Gate、profile system 等) を完全に切り離し、stdlib のみで動作する単独 script に再構成した。検証ロジック自体は stride_lint.py / epic_validator.py と同等。

---

> Tecnos-STRIDE BPMN Authoring Pack v1.0.0 — validators/README.md
