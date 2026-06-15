---
description: VALUE pack (Phase 0/1) 完成後に Cowork セッション内で機械検証 + サニタイズ自動 grep + GitHub MCP 経由で feature ブランチ push + PR draft 作成。Claude Code 引き渡しの自動化。
argument-hint: "<feature_name> [--repo <github_url>]"
---

# /stride:handoff

VALUE pack (Phase 0/1) 完成後に Cowork セッション内で **機械検証** + **§Rule 15-B サニタイズ自動 grep** + GitHub MCP 経由で feature ブランチ push + PR draft 作成、Claude Code 引き渡しを自動化します。

> Phase F-1 緊急 改修 (WI-VALF01-001 / WI-VALF01-004): Cowork セッション内で 4 ファイル + 必須セクション grep + サニタイズ grep を機械検証。

## Usage

```
/stride:handoff <feature_name> [--repo <github_url>]
```

## Workflow

### 1. Validate Input (前提条件確認)

- `specs/<feature_name>/basic_design.md` + `process.bpmn` + `claude_code_handoff.md` + `acceptance_criteria.yaml` が完成 (前提)
- `/stride:validate <feature_name>` が PASS している
- `.mcp.json` で `github` MCP server 設定済 + `GITHUB_PERSONAL_ACCESS_TOKEN` 環境変数設定済
- `--repo` 省略時は `git remote get-url origin` から自動取得

### 2. ★ Cowork セッション内 機械検証 (WI-001、Gap-F-001)

handoff 直前に Cowork セッション内で以下を bash 1-liner で機械検証する。**1 つでも FAIL なら [BLOCKER] で停止。**

```bash
# 2-A. 4 ファイル存在検証
FEATURE="<feature_name>"
SPEC_DIR="specs/${FEATURE}"
HANDOFF_FILES=(
  "${SPEC_DIR}/basic_design.md"
  "${SPEC_DIR}/process.bpmn"
  "${SPEC_DIR}/upstream/claude_code_handoff.md"
  "${SPEC_DIR}/upstream/acceptance_criteria.yaml"
)
missing=0
for f in "${HANDOFF_FILES[@]}"; do
  if [ ! -f "$f" ]; then echo "⛔ [BLOCKER] missing: $f"; missing=1; fi
done
[ $missing -eq 0 ] || exit 1

# 2-B. basic_design.md 必須セクション grep (#0 Canonical Basic Design + 主要 fields)
REQUIRED_SECTIONS=(
  "# 0. Canonical Basic Design"
  "basic_design:"
  "context:"
  "scope:"
  "bpmn_descriptions:"
  "traceability_rows:"
  "basic_design_gate_check:"
)
for sec in "${REQUIRED_SECTIONS[@]}"; do
  if ! grep -Fq "$sec" "${SPEC_DIR}/basic_design.md"; then
    echo "⛔ [BLOCKER] basic_design.md missing required section: $sec"
    exit 1
  fi
done

# 2-C. process.bpmn 必須要素 grep
BPMN_REQUIRED=(
  "<bpmn:process"
  "<bpmn:startEvent"
  "<bpmn:endEvent"
  "<bpmndi:BPMNDiagram"
)
for el in "${BPMN_REQUIRED[@]}"; do
  if ! grep -Fq "$el" "${SPEC_DIR}/process.bpmn"; then
    echo "⛔ [BLOCKER] process.bpmn missing required element: $el"
    exit 1
  fi
done

echo "✅ Pre-flight machine verification PASS (4 files + required sections + BPMN elements)"
```

### 3. ★ §Rule 15-B サニタイズ自動 grep (WI-004、Gap-F-004)

handoff 前に **顧客実データ流出を機械防止** する。upstream/*.yaml + lessons_learned に対し §Rule 15-B 禁止キーワード集を grep -E で検査。**1 件でもヒットしたら [BLOCKER] で停止し、サニタイズ要請。**

```bash
# 3-A. 禁止キーワード集 (§Rule 15-B、Phase D で確立、Phase F で grep 自動化)
# 注: 実プロジェクト固有名詞 / 担当者名 / 契約番号パターン / 金額表記。
# 汎用業務語 (注文 / 在庫 / 顧客 等) は除外し、誤検出を防ぐ。
SANITIZE_PATTERNS=(
  # 顧客名 (例)
  "JM Costco|JAMESMARTIN|コストコ|jm[_-]costco"
  # プロジェクト ID パターン (案件番号)
  "PRJ-[0-9]{4,}|案件[#番号][[:space:]]*[0-9]{4,}"
  # 金額表記 (実額数値、3 桁区切り or 単位付き)
  "[0-9]{1,3}(,[0-9]{3}){2,}[[:space:]]*(円|JPY|USD|万円|億円)"
  # 個人名候補 (姓 + 様 / さん + 部署語)
  "(山田|佐藤|鈴木|高橋|田中|渡辺|伊藤|加藤)[[:space:]]*(様|さん|部長|課長|主任)"
  # 契約番号パターン
  "契約番号[[:space:]]*[:：][[:space:]]*[A-Z0-9-]{6,}"
)

SANITIZE_TARGETS=(
  "${SPEC_DIR}/upstream"
  "${SPEC_DIR}/upstream/lessons_learned"
  "memory/lessons_learned/upstream_dogfooding"
)

sanitize_hit=0
for pattern in "${SANITIZE_PATTERNS[@]}"; do
  for target in "${SANITIZE_TARGETS[@]}"; do
    if [ -e "$target" ]; then
      hits=$(grep -rEn "$pattern" "$target" --include='*.yaml' --include='*.yml' --include='*.md' 2>/dev/null || true)
      if [ -n "$hits" ]; then
        echo "⛔ [BLOCKER] §Rule 15-B sanitize hit (pattern: $pattern):"
        echo "$hits" | head -5
        sanitize_hit=1
      fi
    fi
  done
done

if [ $sanitize_hit -ne 0 ]; then
  echo "⛔ [BLOCKER] handoff aborted. §Rule 15-B 禁止キーワードを検出。サニタイズ後に再実行してください。"
  exit 1
fi
echo "✅ §Rule 15-B sanitize grep clean (0 hits)"
```

### 4. Pre-flight Check

- baseline 改変禁止リスト (Phase A-E + bugfix v7 成果物) を `git diff` で確認、Phase 範囲外の変更がないことを確認
- Cowork Project 内の関連資料も含めてコミット対象を整理

### 5. Trigger MCP

`github` MCP server (CONNECTORS.md §2 の PAT scope: Contents R/W + PR R/W + Metadata R) を経由して:

1. `feature/FEAT-<FEATUREID>-<feature_name>` ブランチを作成 (origin/main から派生)
2. Phase 0/1 成果物を commit:
   - `specs/<feature>/upstream/` (Phase 0 yaml 12+ 件)
   - `specs/<feature>/basic_design.md`
   - `specs/<feature>/process.bpmn`
   - (任意) `epics/<EPIC_ID>/` (Epic 階層作成済の場合)
3. ブランチを push (`origin/feature/FEAT-<FEATUREID>-<feature_name>`)
4. PR draft 作成:
   - title: `feat(<feature>): Phase 0/1 — <Feature Title> (FEAT-<FEATUREID>)`
   - body:
     - Phase 0 + Phase 1 成果物のサマリ
     - BACCM 6 軸完成度
     - profile (enterprise-erp / saas-integration / prototype)
     - Claude Code 引き渡し依頼 (Phase 2-4 実装担当者へ)
     - HITL レビュー依頼項目
     - **(WI-001) 完全性検証 / (WI-004) サニタイズ検証** が PASS した旨を明記

### 6. Output

- GitHub PR URL (draft 状態) を stdout 出力
- Claude Code 担当者への通知 (任意、`openclaw message send` 等が利用可能なら)

### 7. Notes

- PR は **draft 状態** で作成。Claude Code 担当者がレビュー後に Ready for review に変更
- PAT scope 不足エラーが出た場合は CONNECTORS.md §4 トラブルシューティングを参照
- 顧客実データを含む可能性のある場合は §3 サニタイズ grep が機械検出する。検出時は手動サニタイズ後に再実行
- §3 のサニタイズパターンは Tecnos 内部固有名詞ベースのため、汎用業務語は誤検出されない (false-positive 抑制)

### 8. Next Step

Claude Code 担当者が PR を pull、Phase 2 (Specify) → Phase 3 (Tasking) → Phase 4 (Execute) → Final で実装を進める。

> Phase F (WI-VALF01-001 + WI-VALF01-004) で Cowork セッション内 機械検証 + サニタイズ自動 grep を実装。Phase E v0.1.0-poc → v0.2.0-stable。
