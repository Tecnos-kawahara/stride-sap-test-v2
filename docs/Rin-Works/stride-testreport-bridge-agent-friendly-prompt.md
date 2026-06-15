# stride-testreport-bridge Agent-Friendly CLI 改善タスク

作業ディレクトリ: `/path/to/sdd_template_enterprise/`  
（ローカルでは `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise/`）

## 背景

`stride_testreport_bridge.py` は山嵜さんが実装し、`feat: v4.5 BDD acceptance_criteria + escalation_triggers + testreport bridge` で統合されたCLIツール。

昨日のコミット（`feat: agent-friendly CLI design for stride_lint.py and stride-new-project.sh`）で `stride_lint.py` と `stride-new-project.sh` にAgent-Friendly CLI Design 8原則を適用した。同じ原則を `stride_testreport_bridge.py` にも適用する。

---

## 改善①: 終了コードの細分化

**ファイル:** `sdd-templates/tools/stride_testreport_bridge.py`

### 現状

`main()` 内の終了コードが以下の2値のみ：
- `0` — cases.jsonなし（testreport未設定）or 正常完了
- `1` — ディレクトリが存在しない

### 問題

`exit 0` でも「cases.jsonなし」と「正常完了」が区別できない。AIエージェントが結果を判定できない。

### 要件

以下の終了コード体系に拡張する。**既存のデフォルト動作（引数なし時のargparseエラー）は維持すること。**

| コード | 意味 | 発生条件 |
|--------|------|---------|
| 0 | 正常完了 | cases.jsonが存在し、分析が完了した |
| 1 | 分析エラー | 予期しない例外 |
| 2 | 引数エラー | feature_dir未指定（argparseのデフォルト動作を維持） |
| 3 | ディレクトリ非存在 | 指定したfeature_dirが存在しない（現在はexit 1） |
| 4 | testreport未設定 | feature_dirは存在するがcases.jsonが見つからない（現在はexit 0） |

実装方針：
- `main()` のディレクトリ存在チェック部分を `sys.exit(3)` に変更
- `result is None` の場合（cases.jsonなし）を `sys.exit(4)` に変更
- `sys.exit(4)` 時のメッセージに `suggested_action` を含める（下記③参照）
- 変更箇所に `# Agent-friendly: <理由>` コメントを付ける

---

## 改善②: ヘルプに具体例を追加

**ファイル:** `sdd-templates/tools/stride_testreport_bridge.py`

### 現状

`argparse` の `description` が1行のみ。`--json` や `--mapping-file` の使用例がない。

### 要件

`ArgumentParser` に `epilog` を追加して具体例を記載する：

```python
parser = argparse.ArgumentParser(
    description="stride-testreport-bridge: Bridge between testreport and STRIDE",
    epilog=textwrap.dedent("""\
        Examples:
          # テキスト出力（デフォルト）
          %(prog)s specs/FEAT-001/

          # JSON出力（AIエージェント・CI向け）
          %(prog)s specs/FEAT-001/ --json

          # カスタムマッピングファイルを指定
          %(prog)s specs/FEAT-001/ --mapping-file path/to/stride_mapping.yaml

          # セルフテスト実行
          %(prog)s --test

        Exit codes:
          0  正常完了（cases.jsonあり、分析完了）
          1  分析エラー（予期しない例外）
          2  引数エラー
          3  feature_dirが存在しない
          4  cases.jsonが見つからない（testreport未設定）
    """),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
```

`import textwrap` を追加すること。

---

## 改善③: cases.jsonなし時のメッセージに suggested_action を追加

**ファイル:** `sdd-templates/tools/stride_testreport_bridge.py`

### 現状

```python
print("No cases.json found — testreport not configured for this feature.")
sys.exit(0)
```

### 要件

STDOUTの通常メッセージ（テキストモード時）と `--json` 出力の両方を改善する：

**テキストモード時（STDOUTに出力）：**
```
No cases.json found — testreport not configured for this feature.
Suggested action: mkdir testreport/ && echo '[]' > testreport/cases.json && testreport generate
```

**`--json` 指定時（STDOUTにJSON出力）：**
```json
{
  "ok": false,
  "reason": "cases_not_found",
  "message": "No cases.json found — testreport not configured for this feature.",
  "suggested_action": "mkdir testreport/ && echo '[]' > testreport/cases.json && testreport generate",
  "exit_code": 4
}
```

実装方針：
- `args.json` が True の場合はJSON形式で出力
- いずれも `sys.exit(4)` で終了

---

## 改善④: `check_testreport_integration()` の返り値に `suggested_action` を追加

**ファイル:** `sdd-templates/tools/stride_testreport_bridge.py`

### 背景

昨日のコミットで `stride_lint.py` の `add_warning()` / `add_error()` に `suggested_action` が追加された。  
しかし `stride_lint.py` が `check_testreport_integration()` を呼ぶ際、返り値に `suggested_action` がないため `SUGGESTED_ACTIONS` テーブルのフォールバックに頼りきりになっている。

また `stride_lint.py` の `SUGGESTED_ACTIONS` に `TESTREPORT_*` 系のキーが存在しない（現在3種類のwarningが `suggested_action=None` のまま）。

### 要件

**`check_testreport_integration()` の返り値に `suggested_actions` を追加：**

```python
return {
    "report_missing": not result["report_exists"],
    "validate_failed": result["validate_status"] == "fail" and result["validate_available"],
    "validate_message": result["validate_message"],
    "unmapped_cases": result["unmapped_cases"],
    # Agent-friendly: actionable hints for stride-lint integration
    "suggested_actions": {
        "report_missing": "testreport generate を実行してreport.htmlを生成してください",
        "validate_failed": "testreport validate <dir> を手動実行してエラー内容を確認してください",
        "unmapped_cases": "testreport/stride_mapping.yaml に未マッピングのcase_idを追記してください",
    },
}
```

**`stride_lint.py` の呼び出し側を更新：**

ファイル: `sdd-templates/tools/stride_lint.py`

```python
# 変更前（3箇所）
result.add_warning("TESTREPORT_REPORT_MISSING",
    "testreport cases.json found but report.html is missing (run: testreport generate)")
result.add_warning("TESTREPORT_VALIDATE_FAILED",
    f"testreport validate failed: {tr_result.get('validate_message', '')}")
result.add_warning("TESTREPORT_UNMAPPED_CASES",
    f"testreport cases not mapped to STRIDE ACs: {unmapped}")

# 変更後（suggested_actionを明示）
sa = tr_result.get("suggested_actions", {})
result.add_warning(
    "TESTREPORT_REPORT_MISSING",
    "testreport cases.json found but report.html is missing (run: testreport generate)",
    suggested_action=sa.get("report_missing"),
)
result.add_warning(
    "TESTREPORT_VALIDATE_FAILED",
    f"testreport validate failed: {tr_result.get('validate_message', '')}",
    suggested_action=sa.get("validate_failed"),
)
result.add_warning(
    "TESTREPORT_UNMAPPED_CASES",
    f"testreport cases not mapped to STRIDE ACs: {unmapped}",
    suggested_action=sa.get("unmapped_cases"),
)
```

また `stride_lint.py` の `SUGGESTED_ACTIONS` に `TESTREPORT_*` 系のエントリを追加：

```python
"TESTREPORT_REPORT_MISSING": "testreport generate を実行してreport.htmlを生成してください",
"TESTREPORT_VALIDATE_FAILED": "testreport validate <testreport_dir> を手動実行してエラー内容を確認してください",
"TESTREPORT_UNMAPPED_CASES": "testreport/stride_mapping.yaml に未マッピングのcase_idを追記してください",
```

---

## 共通制約

- **後方互換を維持**: デフォルト動作（引数なし時のhelpなど）は変えない
- **既存の14件のセルフテストを壊さない**
- **新規テストを追加**: 以下の3ケースを `_run_self_tests()` に追加
  - exit code 4（cases.jsonなし）のケース
  - exit code 3（ディレクトリ非存在）のケース
  - `--json` でcases.jsonなしの場合にJSON形式で出力されることの確認
- **変更箇所に `# Agent-friendly: <理由>` コメントを付ける**
- **完了後の報告**: 変更ファイル一覧と変更行数をまとめて報告すること

---

## PRの要件

- **ブランチ名**: `feat/testreport-bridge-agent-friendly`
- **PRタイトル**: `feat(stride-testreport-bridge): Agent-Friendly CLI Design 8原則の適用`
- **PRボディ**:

```markdown
## 概要

stride_testreport_bridge.py に Agent-Friendly CLI Design 8原則を適用。

昨日の `feat: agent-friendly CLI design for stride_lint.py and stride-new-project.sh` に続く改善。

## 変更内容

- **終了コードの細分化** (0/1/2/3/4)
  - 4: cases.jsonなし（testreport未設定）を正常完了(0)と区別
  - 3: ディレクトリ非存在を明示
- **ヘルプに具体例を追加** (`--json`, `--mapping-file`, exit codes)
- **cases.jsonなし時のメッセージ改善** (`suggested_action` を含むJSON出力対応)
- **`check_testreport_integration()` に `suggested_actions` フィールドを追加**
- **`stride_lint.py` の `SUGGESTED_ACTIONS` に `TESTREPORT_*` 系を追加**

## テスト

- 既存セルフテスト 14件: 全pass維持
- 新規テスト 3件追加（exit 3/4, --json出力）

## 確認コマンド

`​`​`bash
# ① exit 4（cases.jsonなし）
python3 sdd-templates/tools/stride_testreport_bridge.py /tmp; echo "exit: $?"
# → exit: 4

# ② exit 3（ディレクトリ非存在）
python3 sdd-templates/tools/stride_testreport_bridge.py /nonexistent; echo "exit: $?"
# → exit: 3

# ③ --json でcases.jsonなし
python3 sdd-templates/tools/stride_testreport_bridge.py /tmp --json | python3 -m json.tool
# → {"ok": false, "reason": "cases_not_found", ...}

# ④ セルフテスト全件
python3 sdd-templates/tools/stride_testreport_bridge.py --test
# → 17/17 tests passed

# ⑤ stride_lintのTESTREPORT系suggested_action確認
python3 sdd-templates/tools/stride_lint.py --all --format json 2>/dev/null \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
for r in d.get('results', []):
    for w in r.get('warnings', []):
        if 'TESTREPORT' in w.get('code', ''):
            print(w.get('code'), '->', w.get('suggested_action'))
"
`​`​`
```

- **ベースブランチ**: `main`
- **リポジトリ**: `tecnos-japan-cbp/tecnos-sdd-template-enterprise`

---

## 完了確認コマンド（実装後に必ず実行）

```bash
cd /path/to/sdd_template_enterprise

# ① exit 4（cases.jsonなし）
python3 sdd-templates/tools/stride_testreport_bridge.py /tmp; echo "exit: $?"

# ② exit 3（ディレクトリ非存在）
python3 sdd-templates/tools/stride_testreport_bridge.py /nonexistent; echo "exit: $?"

# ③ --json でcases.jsonなし
python3 sdd-templates/tools/stride_testreport_bridge.py /tmp --json | python3 -m json.tool

# ④ セルフテスト全件
python3 sdd-templates/tools/stride_testreport_bridge.py --test

# ⑤ stride_lintのTESTREPORT系suggested_action確認
python3 sdd-templates/tools/stride_lint.py --all --format json 2>/dev/null \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
for r in d.get('results', []):
    for w in r.get('warnings', []):
        if 'TESTREPORT' in w.get('code', ''):
            print(w.get('code'), '->', w.get('suggested_action'))
"
```
