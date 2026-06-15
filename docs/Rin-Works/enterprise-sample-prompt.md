# Claude Code 指示プロンプト: Enterprise サンプル追加

## 作業ディレクトリ
`/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

## 概要
v4.7.0 の Enterprise Hierarchy 機能の動作を新規利用者が即座に理解できるよう、
テンプレートリポジトリの **ルートレベル** に動作するサンプル Epic + Feature を配置する。

## 配置の大原則

**サンプルは実際の CLI/ツール探索パスと一致する場所に置く。**

| ツール | 探索パス | サンプル配置先 |
|--------|---------|--------------|
| `stride epic list/validate/gates` | `epics/EPIC-*/` | `epics/EPIC-SAMPLE/` |
| `stride init --epic` | `epics/<EPIC_ID>/` | 同上 |
| `stride lint --enterprise` (Epic) | `epics/` | 同上 |
| `epic_validator.py` (Feature検索) | `specs/<feature_id>/` | `specs/FEAT-ERPSAMPLE/` |
| `stride lint` (Feature) | `specs/<feature>/` | 同上 |
| `stride_lint_enterprise.py` (epic_ref) | `epics/<epic_ref>/` | 同上 |
| `discover_features()` | `specs/` + `sdd-templates/specs/` | 両方を走査 |

したがって配置は：
- **Epic**: `epics/EPIC-SAMPLE/`（ルート）
- **Feature**: `specs/FEAT-ERPSAMPLE/`（ルート）
- **テンプレートサンプル**（フラット版）: `sdd-templates/specs/sample_feature/`（既存のまま）

## 前提: 変更前に必ず確認すべきファイル

| ファイル | 用途 |
|---------|------|
| `archive/sample-specs/EPIC-SAMPLE/` | 既存 Epic サンプル（コピー元、7ファイル） |
| `archive/sample-specs/FEAT-ERP-OMS/` | 既存 Feature サンプル（コピー元、27ファイル） |
| `scripts/stride-new-project.sh` line 250-268 | `stride new-project` のサンプル削除対象 |
| `sdd-templates/tools/epic_validator.py` line 415 | Feature探索: `self.base_dir / "specs" / fid` |
| `sdd-templates/tools/stride_lint_enterprise.py` line 423 | Epic探索: `self.root / "epics" / epic_ref` |
| `sdd-templates/bin/stride` line 1579 | `epic list`: `epics/EPIC-*/` を走査 |

**archive 内の旧パス参照の実態**（約200箇所）：
- `specs/sample_erp_addon/...` — basic_design.md, spec.md, plan.md, tasks.md, contracts/, epic_design.md 等に多数
- `FEAT-ERP-OMS` — feature_id としてEpic側・Feature側の両方に

## Step 1: archive から ルートにサンプルをコピー

```bash
# Epic サンプル → ルートの epics/ (stride epic コマンドが探索する場所)
cp -R archive/sample-specs/EPIC-SAMPLE epics/EPIC-SAMPLE

# Feature サンプル → ルートの specs/FEAT-ERPSAMPLE/ (epic_validator が feature_id で探す場所)
cp -R archive/sample-specs/FEAT-ERP-OMS specs/FEAT-ERPSAMPLE
```

**⚠️ なぜ `specs/FEAT-ERPSAMPLE/` か：**
`epic_validator.py` line 415-425 は `self.base_dir / "specs" / fid` で Feature を探す。
`fid` は `epic_design.md` の `features[].feature_id` の値。
ディレクトリ名を `feature_id` と一致させることで、ツールが Feature を正しく発見できる。

## Step 2: Feature ID の統一

archive の Feature ID は `FEAT-ERP-OMS`。これを `FEAT-ERPSAMPLE` に統一する。
**Epic 側と Feature 側の両方で置換する。**

```bash
# macOS — *.md, *.yaml, *.bpmn すべてを対象にする
# (process.bpmn 内にも FEAT-ERP-OMS / sample_erp_addon が含まれているため *.bpmn 必須)
find specs/FEAT-ERPSAMPLE -type f \( -name "*.md" -o -name "*.yaml" -o -name "*.bpmn" \) \
  -exec sed -i '' 's/FEAT-ERP-OMS/FEAT-ERPSAMPLE/g' {} +

find epics/EPIC-SAMPLE -type f \( -name "*.md" -o -name "*.yaml" -o -name "*.bpmn" \) \
  -exec sed -i '' 's/FEAT-ERP-OMS/FEAT-ERPSAMPLE/g' {} +
```

## Step 3: パス参照の統一

archive 内のファイルは `specs/sample_erp_addon/...` を参照している（約200箇所）。
これを `specs/FEAT-ERPSAMPLE/...` に置換する。**`*.bpmn` も対象に含める。**

```bash
# macOS — *.md, *.yaml, *.bpmn すべてを対象
find specs/FEAT-ERPSAMPLE -type f \( -name "*.md" -o -name "*.yaml" -o -name "*.bpmn" \) \
  -exec sed -i '' 's|specs/sample_erp_addon/|specs/FEAT-ERPSAMPLE/|g' {} +

find epics/EPIC-SAMPLE -type f \( -name "*.md" -o -name "*.yaml" -o -name "*.bpmn" \) \
  -exec sed -i '' 's|specs/sample_erp_addon/|specs/FEAT-ERPSAMPLE/|g' {} +
```

## Step 4: `stride-new-project.sh` の削除対象を確認

`scripts/stride-new-project.sh` line 250-264 を確認する。
既存の削除対象に以下が **既に含まれているか** 確認：

```bash
grep "FEAT-ERPSAMPLE\|EPIC-SAMPLE" scripts/stride-new-project.sh
```

既存コード（line 257-258）で `epics/EPIC-SAMPLE` は削除対象に含まれているはず。
`specs/FEAT-ERPSAMPLE` が含まれていなければ追加する：

```bash
    # Remove sample enterprise feature
    for dir in specs/FEAT-ERPSAMPLE; do
        if [ -d "$dir" ]; then
            log "  Removing $dir/"
            run "rm -rf $dir/"
        fi
    done
```

**⚠️ 既存の削除対象リスト（`specs/sample_erp_addon` 等）は変更しない。追加のみ。**

## Step 5: 検証（厳密）

```bash
# 検証開始前に enterprise.yaml をバックアップし、成功・失敗を問わず必ず復元する
cp sdd-templates/config/enterprise.yaml sdd-templates/config/enterprise.yaml.bak
trap 'mv sdd-templates/config/enterprise.yaml.bak sdd-templates/config/enterprise.yaml' EXIT

echo -e "enterprise:\n  enabled: true" > sdd-templates/config/enterprise.yaml

# 1. Epic validate（stride CLI 経由 — _resolve_python() で venv 整合）
sdd-templates/bin/stride epic validate EPIC-SAMPLE
# 確認: "FEATURE_SPEC_MISSING" が出ないこと（specs/FEAT-ERPSAMPLE/ が見つかること）

# 2. Feature lint + enterprise（--warn-only なし = ERROR があれば非0終了で失敗）
sdd-templates/tools/stride-lint specs/FEAT-ERPSAMPLE/ --enterprise
# 確認: exit code 0 であること。EPIC_NOT_FOUND が出ないこと。
# WARNING（PLACEHOLDER_VALUE_PRESENT 等）は許容するが ERROR は許容しない。

# 3. stride epic list でサンプルが見えること
sdd-templates/bin/stride epic list
# 期待出力に EPIC-SAMPLE/ が含まれること

# 4. stride epic features でサンプル Feature が見えること
sdd-templates/bin/stride epic features EPIC-SAMPLE
# 期待出力に FEAT-ERPSAMPLE が含まれること

# 5. Feature 内の旧パス参照が残っていないこと（*.bpmn 含む）
grep -rn "sample_erp_addon" specs/FEAT-ERPSAMPLE/ epics/EPIC-SAMPLE/ | head -5
# ヒット 0 件であること

# 6. Feature 内の旧 Feature ID が残っていないこと（*.bpmn 含む）
grep -rn "FEAT-ERP-OMS" specs/FEAT-ERPSAMPLE/ epics/EPIC-SAMPLE/ | head -5
# ヒット 0 件であること

# 7. 既存フラット版サンプルが壊れていないこと
sdd-templates/tools/stride-lint sdd-templates/specs/sample_feature/ --warn-only

# 8. enterprise.yaml は trap EXIT で自動復元される
```

**検証 1 で `FEATURE_SPEC_MISSING` が出た場合：**
Epic の `features[].feature_id` と `specs/` 配下のディレクトリ名が一致していない。
Step 2 の置換が不完全なので修正すること。

**検証 2 で exit code が非0の場合：**
`Errors:` セクションの内容を確認し、サンプルデータを修正すること。
`EPIC_NOT_FOUND` なら `epic_ref` の値と `epics/` のディレクトリ名が不一致。

## Step 6: ドキュメント更新

### 6a. `sdd-templates/README.md`

適切な場所に追記：

```markdown
### サンプル

| サンプル | パス | 説明 |
|---------|------|------|
| フラット Feature | `sdd-templates/specs/sample_feature/` | Enterprise なしのシンプルな Feature |
| Enterprise Epic | `epics/EPIC-SAMPLE/` | Epic 設計・承認・進捗管理のサンプル |
| Enterprise Feature | `specs/FEAT-ERPSAMPLE/` | Epic 配下 Feature（`epic_ref` / `team_id` 設定済み） |

> `stride new-project` 実行時にサンプルは自動削除されます（`--keep-samples` で保持）。
```

### 6b. `sdd-templates/QUICKSTART.md`

Enterprise 利用の手順にサンプル参照を追加：

```markdown
> 💡 Enterprise 機能のサンプルは `epics/EPIC-SAMPLE/` と `specs/FEAT-ERPSAMPLE/` を参照してください。
> `stride epic features EPIC-SAMPLE` で Epic 配下の Feature 一覧を確認できます。
```

## チェックリスト

```
□ epics/EPIC-SAMPLE/ にサンプル Epic がコピーされたか？
□ specs/FEAT-ERPSAMPLE/ にサンプル Feature がコピーされたか？
□ ディレクトリ名が specs/FEAT-ERPSAMPLE/ である（feature_id と一致）か？
□ Epic の features[].feature_id が "FEAT-ERPSAMPLE" に統一されたか？
□ Feature の frontmatter feature_id が "FEAT-ERPSAMPLE" か？
□ Feature の epic_ref が "EPIC-SAMPLE" を指しているか？
□ Feature の team_id が Epic の teams に存在するか？
□ "specs/sample_erp_addon/" パス参照が 0 件か？（grep で確認）
□ "FEAT-ERP-OMS" 参照が 0 件か？（grep で確認）
□ stride epic validate EPIC-SAMPLE で FEATURE_SPEC_MISSING が出ないか？（bare python3 ではなく stride CLI 経由）
□ stride lint specs/FEAT-ERPSAMPLE/ --enterprise（--warn-only なし）が exit 0 か？
□ stride epic list で EPIC-SAMPLE が見えるか？
□ stride epic features EPIC-SAMPLE で FEAT-ERPSAMPLE が見えるか？
□ sdd-templates/specs/sample_feature/ の lint が壊れていないか？
□ stride-new-project.sh の削除対象に specs/FEAT-ERPSAMPLE を追加したか？
□ archive の元ファイルは削除していないか？
□ README.md / QUICKSTART.md にサンプル一覧を追記したか？
```

## ⚠️ やってはいけないこと

1. **`sdd-templates/specs/sample_feature/` を変更しない** — フラット版は独立
2. **archive の元ファイルを削除しない** — 履歴として保持
3. **サンプルを `sdd-templates/epics/` や `sdd-templates/specs/` に置かない** — ツール探索パスと不一致になる
4. **ディレクトリ名と feature_id を不一致にしない** — `epic_validator.py` が `specs/<feature_id>/` で探す

---

完了したら:
```
openclaw system event --text "Done: Enterprise サンプル追加 (epics/EPIC-SAMPLE + specs/FEAT-ERPSAMPLE)" --mode now
```
