# cowork-plugin/scripts/ — Plugin 同梱補助スクリプト集

> Phase F WI-VALF01-014 / 改善要望-13 (★ v2 P0-2)
> reference_files = 49 不変 (本ディレクトリは別ディレクトリ計上)

## 配置方針

このディレクトリは Cowork Plugin (`cowork-plugin/`) の **配布物に同梱** される補助 Python スクリプトを格納します。`reference_files/` 49 ファイルとは別ディレクトリとして計上され、reference_files の件数厳守 (= 49) に影響しません。

**Plugin runtime 仕様 (Markdown + JSON only) との関係**: Plugin package 自体は Markdown + JSON のみで実装される (Anthropic 公式仕様)。本 `scripts/` は Plugin package が外部呼び出しできる **補助ツールボックス** として位置付けられ、Plugin runtime の動作を規定するわけではありません (Plugin runtime SSoT は `.claude-plugin/plugin.json` + Skills / Commands / `.mcp.json`)。

詳細: `cowork-plugin/README.md §1.1 Architecture Notes` を参照。

## 配置スクリプト一覧

| スクリプト | 役割 | 起動元 |
|---|---|---|
| `validate_state_yaml.py` | `specs/<feature>/state/state.yaml` の Phase 2-4 schema を機械検証 (WI-VALF01-010 連携) | コンサル手動 / `stride-validate` skill |
| `check_handoff_files.py` | handoff 4 ファイル (basic_design.md / process.bpmn / claude_code_handoff.md / acceptance_criteria.yaml) の存在 + 必須セクションを検証 (WI-VALF01-001 と二重保険) | `stride-handoff` command または手動 |

> 本 README は `cowork-plugin/scripts/` のディレクトリ説明書 (3 ファイル目)。`reference_files/` には含めない。

## 利用例

```bash
# state.yaml schema 検証
python3 cowork-plugin/scripts/validate_state_yaml.py specs/val_f01/state/state.yaml

# handoff 4 ファイル + 必須セクション検証
python3 cowork-plugin/scripts/check_handoff_files.py specs/val_f01/
```

## Plugin install 配布

`claude plugin install tecnos-stride-value@tecnos-stride` で Plugin install 時に
本ディレクトリ + 配下の Python ファイルが配布されます。コンサル環境にて
`pyyaml` (PyYAML) が install 済であれば、追加の依存なしで動作します。
