# SAP 拡張 ツール開発ガイド (v2)

SAP 拡張パック v2.0.0 (STRIDE v6.0.0) に新しいツールを追加する手順を解説する。
対象読者: テンプレートメンテナー、ツール開発者。

関連ドキュメント:
- [migration_from_v1.md](migration_from_v1.md) -- v1 からの移行情報
- [SAP_TROUBLESHOOTING.md](SAP_TROUBLESHOOTING.md) -- トラブルシューティング

---

## 1. ツールの種類

v2 のツールは `MANIFEST.yaml` の `tools` セクションで 4 層に分類される。

| 層 | 言語 | 配置先 | 用途 | MANIFEST セクション |
|----|------|--------|------|---------------------|
| validators | Python | `extensions/sap/tools/*.py` | YAML 検証、品質チェック、クロスファイル整合性 | `tools.validators` |
| utilities | Python / JS | `extensions/sap/tools/*.py` or `*.js` | 分析・整形・生成の補助ツール | `tools.utilities` |
| mapping_refs | Markdown | `extensions/sap/agent_docs/*.md` | AI が参照する転記マッピング定義 | `tools.mapping_refs` |
| sap_operations | Node.js | `extensions/sap/tools/*.js` | SAP システムとの通信（ADT API 経由） | `tools.sap_operations` |

Python ツールは主に 2 つのインターフェースを持つ:

- **ValidatorContext 方式** (validators): stride_lint から動的にロードされ、`ValidatorContext` を受け取り `ValidationResult` を返す。スタンドアロン実行なし。
- **CLI 方式** (utilities): `argparse` / `sys.argv` でコマンドラインから直接実行。`--step-id` を受け取り、`tool_evidence_writer` でエビデンスを記録する。

---

## 2. Python ツールの開発

### 2.1 Validator 方式（stride_lint 経由）

v2 の新規バリデータは `ValidatorContext` / `ValidationResult` インターフェースに従う。
stride_lint が `MANIFEST.yaml` の `tools.validators` を読み、各バリデータを動的にロードして実行する。

```python
"""
my_validator.py
参照仕様: 03_lint §3-x (ルール番号)
共通インターフェース: 03_lint §2 (ValidatorContext -> ValidationResult)

バリデータの説明。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationError:
    code: str          # エラーコード（例: "MY_RULE_VIOLATION"）
    message: str       # 人間向けメッセージ
    severity: str      # "ERROR" | "WARNING"
    file: str          # 対象ファイルパス
    line: int | None = None
    suggestion: str = ""


@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)


@dataclass
class ValidatorContext:
    feature_dir: Path
    basic_design: dict
    spec: dict | None = None
    plan: dict | None = None
    config: dict = field(default_factory=dict)
    sap_connection: Any = None
    source_yaml: dict | None = None  # parsed yaml spec


def validate_my_rule(context: ValidatorContext) -> ValidationResult:
    """
    メインエントリポイント。
    関数名は validate_<ルール名> とする。
    """
    result = ValidationResult()
    bd = context.basic_design

    if not bd:
        result.errors.append(ValidationError(
            code="MY_RULE_NO_DATA",
            message="basic_design is empty or not parsed",
            severity="ERROR",
            file=str(context.feature_dir / "basic_design.md"),
            suggestion="Ensure basic_design.md has valid #0 YAML canonical section",
        ))
        return result

    # ---- ここにバリデーションロジック ----

    return result
```

**重要:**
- Validator は `if __name__ == "__main__"` ブロックを持たない（stride_lint が呼び出す）
- `ValidationError.code` は一意で検索可能な文字列にする
- `severity` は `"ERROR"` (Gate 通過不可) と `"WARNING"` (情報提供) の 2 値
- `suggestion` に修正案を具体的に書く

### 2.2 CLI 方式（ユーティリティツール）

CLI から直接実行するユーティリティツールの基本パターン:

```python
"""
my_utility.py -- ツールの説明（1行）

詳細な説明。

Usage:
  python3 extensions/sap/tools/my_utility.py specs/<feature>/ --step-id <step-id>

実行タイミング: Step X-Y（ステップの説明）
"""

from __future__ import annotations

import sys
from pathlib import Path

# 共通モジュールのインポート
sys.path.insert(0, str(Path(__file__).parent))
from sap_evidence_common import load_yaml_from_md, load_yaml_file
from tool_evidence_writer import write_evidence


def _safe_print(text: str) -> None:
    """Windows コンソールで UTF-8 を安全に出力する。"""
    try:
        sys.stdout.buffer.write((text + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()
    except (AttributeError, UnicodeEncodeError):
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("ascii", errors="replace").decode("ascii"))


def main() -> None:
    original_argv = sys.argv.copy()

    # --step-id の抽出
    step_id = None
    if "--step-id" in sys.argv:
        idx = sys.argv.index("--step-id")
        if idx + 1 < len(sys.argv):
            step_id = sys.argv[idx + 1]
            sys.argv = sys.argv[:idx] + sys.argv[idx + 2:]

    if step_id is None:
        print(
            "ERROR: --step-id is required.\n"
            "Usage: python3 my_utility.py specs/<feature>/ --step-id <step-id>",
            file=sys.stderr,
        )
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python3 my_utility.py specs/<feature>/ --step-id <step-id>",
              file=sys.stderr)
        sys.exit(1)

    feature_dir = Path(sys.argv[1])
    if not feature_dir.is_dir():
        print(f"Error: {feature_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    # ---- ここにツールのメインロジック ----
    result_summary = do_something(feature_dir)

    # エビデンス記録
    write_evidence(
        feature_dir=str(feature_dir),
        step_id=step_id,
        tool_name="my_utility.py",
        command=" ".join(original_argv),
        options=[],
        result_summary=result_summary,
    )


if __name__ == "__main__":
    main()
```

---

## 3. 共通モジュール

### 3.1 sap_evidence_common.py

YAML パースのユーティリティ。`extensions/sap/tools/sap_evidence_common.py` に配置。

| 関数 | シグネチャ | 用途 |
|------|-----------|------|
| `load_yaml_from_md` | `(path: Path) -> dict[str, Any]` | Markdown 内の YAML を読み込む。3 形式対応 |
| `load_yaml_file` | `(path: Path) -> dict[str, Any]` | 純 YAML ファイルを読み込む |

**`load_yaml_from_md` の対応形式:**

1. `` ```yaml `` コードブロック（plan.md 等の Canonical YAML）
2. フロントマター（`---` で囲まれた YAML）
3. 純粋な YAML ファイル（上記 2 つにマッチしない場合）

**共通仕様:**
- YAML パースエラー時は空 dict `{}` を返す（例外を投げない）
- ファイルが存在しない場合も空 dict `{}` を返す
- PyYAML (`yaml`) が未インストールの場合も空 dict `{}` を返す
- エンコーディングは UTF-8 固定

### 3.2 tool_evidence_writer.py

ツール実行エビデンスの記録。`extensions/sap/tools/tool_evidence_writer.py` に配置。

```python
write_evidence(
    feature_dir: str | Path,   # specs/<feature>/ のパス
    step_id: str,              # ステップ ID（例: "1.5-B2", "2-D1", "4-B4"）
    tool_name: str,            # ツール名（例: "sap_context_metadata.py"）
    command: str,              # 実行コマンド全体
    options: list[str] | None = None,  # CLI オプションリスト
    exit_code: int = 0,        # 終了コード
    result_summary: str = "",  # 結果サマリー
    outputs: list[dict[str, str]] | None = None,  # [{"path": "...", "action": "created|modified"}]
    duration_ms: int | None = None,  # 実行時間（ミリ秒）
) -> Path  # 書き出したエビデンスファイルのパスを返す
```

**出力先:** `specs/<feature>/.tool_evidence/{step_id}__{tool_basename}.evidence.yaml`

**補助関数:**
- `evidence_filename(step_id, tool_name) -> str` -- エビデンスファイル名を生成

**Node.js 版:** `tools/lib/evidence_writer.js` に同等の関数が提供されている。

```javascript
const { writeEvidence, writeEvidenceIfStepId, getStepIdFromArgs } = require('./lib/evidence_writer');
```

| 関数 | 用途 |
|------|------|
| `writeEvidence(opts)` | エビデンスファイルを書き出す |
| `writeEvidenceIfStepId(opts)` | `--step-id` が指定されている場合のみ書き出す |
| `getStepIdFromArgs()` | `process.argv` から `--step-id` の値を取得 |

Node.js 版は追加で `extraData` パラメータを受け取り、任意の構造化データをエビデンスに含められる。

---

## 4. Python エラーハンドリング規約

### Validator 方式

| 状況 | 対処 |
|------|------|
| 検証エラー (Gate ブロック) | `result.errors.append(ValidationError(..., severity="ERROR"))` |
| 検証警告 (情報提供) | `result.warnings.append(ValidationError(..., severity="WARNING"))` |
| データ不在 (basic_design が空) | `result.errors.append(...)` で報告し、早期 return |
| YAML パースエラー | `load_yaml_from_md()` が空 dict を返すため、空チェックで対処 |

### CLI 方式

| 状況 | 対処 |
|------|------|
| 致命的エラー（実行不可） | `print("ERROR: ...", file=sys.stderr)` + `sys.exit(1)` |
| 警告（続行可能） | `print("Warning: ...", file=sys.stderr)` + 処理続行 |
| ファイル未検出 | ツールの性質に応じて `sys.exit(1)` または空結果を返す |
| YAML パースエラー | `load_yaml_from_md()` が空 dict を返すため、呼び出し側で空チェック |

---

## 5. Windows 互換性

SAP 拡張パックは Windows 環境で動作する前提。以下の規約を守ること。

| 項目 | 対処 |
|------|------|
| UTF-8 出力 | `_safe_print()` ヘルパーを使用する（cp932 エンコードエラー回避） |
| パス区切り | `pathlib.Path` を使用し、`/` や `\` をハードコードしない |
| 外部コマンド実行 | `subprocess.run()` で `shell=True` が必要な場合がある（npx 等） |
| ファイル書き込み | `encoding="utf-8"` を明示する |

`_safe_print()` パターン:

```python
def _safe_print(text: str) -> None:
    """Windows コンソールで UTF-8 を安全に出力する。"""
    try:
        sys.stdout.buffer.write((text + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()
    except (AttributeError, UnicodeEncodeError):
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("ascii", errors="replace").decode("ascii"))
```

---

## 6. Node.js ツールの開発

### 6.1 基本構造

```javascript
#!/usr/bin/env node
/**
 * tool_name.js -- ツールの説明
 *
 * Usage:
 *   node extensions/sap/tools/tool_name.js <args> --step-id <step-id> --feature-dir specs/<feature>/
 *
 * Environment (.env):
 *   SAP_URL       -- SAP system URL
 *   SAP_USERNAME  -- SAP user
 *   SAP_PASSWORD  -- SAP password
 *   SAP_CLIENT    -- SAP client number
 */

'use strict';

const { ADTClient } = require('abap-adt-api');
const { writeEvidenceIfStepId, getStepIdFromArgs } = require('./lib/evidence_writer');
require('dotenv').config();
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'; // 自己署名証明書対応

// .env バリデーション
function createClient() {
  const { SAP_URL, SAP_USERNAME, SAP_PASSWORD, SAP_CLIENT } = process.env;
  if (!SAP_URL || !SAP_USERNAME || !SAP_PASSWORD) {
    console.error('Error: SAP_URL, SAP_USERNAME, SAP_PASSWORD must be set in .env');
    process.exit(1);
  }
  return new ADTClient(SAP_URL, SAP_USERNAME, SAP_PASSWORD, SAP_CLIENT, '');
}

function getFeatureDirFromArgs() {
  const idx = process.argv.indexOf('--feature-dir');
  if (idx !== -1 && idx + 1 < process.argv.length) {
    return process.argv[idx + 1];
  }
  return null;
}

async function main() {
  const args = process.argv.slice(2);
  // ... 引数パース ...

  const client = createClient();

  try {
    // ---- ここにツールのメインロジック ----
    const result = await doSomething(client);
    console.log(JSON.stringify(result, null, 2));
  } catch (err) {
    console.error(`Error: ${err.message || err}`);
    if (err.response) {
      console.error(`HTTP ${err.response.status}: ${err.response.statusText || ''}`);
    }
    process.exit(1);
  }

  // エビデンス出力
  const stepId = getStepIdFromArgs();
  if (stepId) {
    const featureDir = getFeatureDirFromArgs();
    if (featureDir) {
      writeEvidenceIfStepId({
        featureDir,
        toolName: 'tool_name.js',
        command: process.argv.join(' '),
        options: [],
        resultSummary: 'result summary text',
      });
    }
  }
}

main();
```

### 6.2 ADT クライアントの使い方

`abap-adt-api` の主要 API:

| メソッド | 用途 |
|---------|------|
| `client.objectStructure(objectUrl)` | オブジェクト構造の取得 |
| `client.getObjectSource(sourceUrl)` | ソースコードの取得 |
| `client.setObjectSource(sourceUrl, source)` | ソースコードの書き込み |
| `client.lock(objectUrl)` | オブジェクトのロック |
| `client.unLock(objectUrl, lockHandle)` | ロック解除 |
| `client.activate(objectName, objectUrl)` | アクティベーション |
| `client.searchObject(query, type)` | オブジェクト検索 |
| `client.nodeContents(type, name)` | パッケージ内容一覧 |

### 6.3 エラーハンドリング規約

| 状況 | 対処 |
|------|------|
| .env 未設定 | `console.error("Error: ...")` + `process.exit(1)` |
| HTTP エラー | ステータスコードとステータステキストを出力 + `process.exit(1)` |
| ロック競合 | エラーメッセージに SM12 参照を含める |
| オブジェクト未検出 | 404 の場合はオブジェクト名の確認を促す |

### 6.4 sap_operations の authority レベル

`MANIFEST.yaml` で `sap_operations` に登録するツールには authority レベルを指定する。

| authority | 説明 | 例 |
|-----------|------|----|
| `conversational` | 読み取り専用。承認不要で実行可能 | `read.js`, `search.js`, `data_preview.js` |
| `gated` | 書き込みや副作用あり。Gate 承認が必要 | `create_object.js`, `activate.js`, `pull.js` |

---

## 7. ツールの登録: MANIFEST.yaml

v2 では、全てのツールを `extensions/sap/MANIFEST.yaml` の `tools` セクションに登録する。
v1 の `tool_evidence_registry.yaml` のみへの登録は不十分であり、`MANIFEST.yaml` への登録が必須。

### 7.1 Validator の登録

```yaml
tools:
  validators:
    - name: "my_new_validator"
      path: "tools/my_new_validator.py"
      trigger: "phase:design,phase:specify"   # 実行フェーズ（カンマ区切り）
      description: "CX: ルール説明"
      severity: "error"                        # "error" | "warning"
```

**trigger に指定可能な値:**
`phase:design`, `phase:specify`, `phase:sap_context`, `phase:execute`, `phase:final`

### 7.2 Utility の登録

```yaml
tools:
  utilities:
    - name: "my_new_utility"
      path: "tools/my_new_utility.py"
      trigger: "manual"                        # "manual" | "phase:<phase>"
      description: "ユーティリティの説明"
```

### 7.3 SAP Operation の登録

```yaml
tools:
  sap_operations:
    - name: "my_sap_tool"
      path: "tools/my_sap_tool.js"
      authority: "gated"                       # "gated" | "conversational"
      description: "SAP 操作の説明"
```

### 7.4 phase_steps への追加

ツールをワークフローステップとして実行させる場合、`phase_steps` にも追加する。

```yaml
phase_steps:
  specify:
    steps:
      - id: "2-D5"
        name: "新規バリデーション"
        tool: "my_new_validator"          # tools セクションの name と一致
        type: "validator"                  # "validator" | "utility" | "workflow"
```

### 7.5 tool_evidence_registry.yaml の更新

`config/tool_evidence_registry.yaml` にも登録して、エビデンス検証 (`sap_tool_evidence_validator.py`) の対象にする。

---

## 8. テスト

### 8.1 Validator のテスト

Validator は stride_lint 経由で実行されるため、テスト用の feature ディレクトリを用意し lint を実行する。

```bash
# stride lint でバリデータを含む全検証を実行
sdd-templates/bin/stride lint specs/test_feature/
```

個別テストには、`ValidatorContext` を手動構築して関数を直接呼び出す方法もある:

```python
from pathlib import Path
from my_new_validator import validate_my_rule, ValidatorContext

context = ValidatorContext(
    feature_dir=Path("specs/test_feature/"),
    basic_design={"front_matter": {"title": "Test"}, ...},
    spec=None,
)
result = validate_my_rule(context)
assert len(result.errors) == 0
```

### 8.2 CLI ユーティリティのテスト

```bash
# Python ユーティリティ
python3 extensions/sap/tools/my_utility.py specs/test_feature/ --step-id 1.5-B2

# Node.js SAP 操作ツール（.env に SAP 接続情報を設定済みであること）
node extensions/sap/tools/my_sap_tool.js <args> --step-id 4-A1 --feature-dir specs/test_feature/
```

### 8.3 エビデンス出力の確認

```bash
# エビデンスファイルが生成されたか確認
ls specs/test_feature/.tool_evidence/
# 例: 1.5-B2__my_utility.evidence.yaml が存在すること

# 内容の確認
cat specs/test_feature/.tool_evidence/1.5-B2__my_utility.evidence.yaml
```

### 8.4 MANIFEST.yaml 整合性の確認

```bash
# MANIFEST.yaml に登録した path が実在するか確認
ls extensions/sap/tools/my_new_validator.py
```

---

## 9. チェックリスト（新規ツール追加時）

### 全ツール共通

- [ ] ツール本体を `extensions/sap/tools/` に配置した
- [ ] `MANIFEST.yaml` の `tools` セクション（validators / utilities / sap_operations）に登録した
- [ ] `MANIFEST.yaml` の `phase_steps` にステップとして追加した（ワークフローに組み込む場合）
- [ ] `config/tool_evidence_registry.yaml` にツールを登録した
- [ ] `CLAUDE_WORKFLOW_SAP.md` の該当 Phase 参照テーブルを更新した
- [ ] 該当 Phase の `agent_docs/phase*.md` にステップを追記した
- [ ] `CLAUDE_SAP.md` のコマンド一覧を更新した（新規操作ツールの場合）
- [ ] Windows 環境での動作確認を行った

### Validator 固有

- [ ] `ValidatorContext` / `ValidationResult` インターフェースに準拠した
- [ ] エントリポイント関数名が `validate_<ルール名>` である
- [ ] `ValidationError.code` が一意で `suggestion` が具体的である
- [ ] `severity` を適切に設定した（Gate ブロックは `"error"`）
- [ ] `trigger` フェーズを正しく設定した

### CLI ユーティリティ固有

- [ ] `--step-id` 引数を受け付けるようにした
- [ ] `tool_evidence_writer.py` でエビデンスを記録するようにした
- [ ] Usage/help テキストに正しいステップ ID を記載した

### Node.js SAP Operation 固有

- [ ] `.env` バリデーション (`SAP_URL`, `SAP_USERNAME`, `SAP_PASSWORD`) を実装した
- [ ] `lib/evidence_writer.js` の `writeEvidenceIfStepId` でエビデンスを記録するようにした
- [ ] `--step-id` と `--feature-dir` を受け付けるようにした
- [ ] `authority` レベルを適切に設定した（読み取り専用 = `conversational`, 書き込み = `gated`）
- [ ] エラー時に HTTP ステータスとボディを出力するようにした
