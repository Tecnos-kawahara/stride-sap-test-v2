#!/usr/bin/env bash
# scripts/sync_cowork_plugin_reference.sh
# Tecnos-STRIDE 本体の更新を cowork-plugin/reference_files/ に同期 (46 ファイル厳守)
#
# 冪等性: 上書きコピーなので何度実行しても同じ結果。
# 件数チェック: 46 ファイル以外なら exit 1 (BLOCKER)。
#
# v0.4.0 履歴 (2026-05-07): BPMN package integration で BPMN 4 ファイル
#   (bpmn_quick_reference / camunda_bpmn_practice_guide / camunda_bpmn_dictionary_complete /
#    bpmn_generator_rules) を reference_files/docs/ から bpmn/ に移動し drift 防止。
#   reference_files 49 → 46 に正規化。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/cowork-plugin/reference_files"

echo "Syncing reference_files from Tecnos-STRIDE main..."

# manual/ (13 ファイル: 10 + 39-50)
# 10_bpmn_guide.md = エンドユーザーガイド (顧客レビュー説明用、bpmn-authoring SKILL.md §2 から参照)
mkdir -p "$DEST/manual"
cp "$ROOT/manual/10_bpmn_guide.md" "$DEST/manual/"
cp "$ROOT/manual/"{39,40,41,42,43,44,45,46,47,48,49,50}_*.md "$DEST/manual/"

# manual/migration/ (1 ファイル)
mkdir -p "$DEST/migration"
cp "$ROOT/manual/migration/v54_to_v60.md" "$DEST/migration/"

# constitution
cp "$ROOT/memory/constitution.md" "$DEST/"

# amendments (XV/XVI/XVII)
mkdir -p "$DEST/constitution_amendments"
cp "$ROOT/memory/constitution_amendments/X"{V,VI,VII}_*.md "$DEST/constitution_amendments/"

# policies (5)
mkdir -p "$DEST/policies"
cp "$ROOT/shared/policies/"{upstream_policy,baccm_completeness,technique_library,upstream_iteration_policy,profile_policy}.yaml "$DEST/policies/"

# templates/upstream/ (16: 15 yaml + README)
mkdir -p "$DEST/templates/upstream"
cp -r "$ROOT/sdd-templates/templates/upstream/"* "$DEST/templates/upstream/"

# templates/ (4: basic_design + epic_design + feature_breakdown + epic_progress_report)
# v0.4.0 BPMN package integration で process_bpmn / epic_flow templates も bpmn/templates/ に移動 (drift 防止)。
mkdir -p "$DEST/templates"
cp "$ROOT/sdd-templates/templates/"{basic_design,epic_design,feature_breakdown,epic_progress_report}_template.md "$DEST/templates/"

# SDD 中核 (3)
mkdir -p "$DEST/sdd-templates"
cp "$ROOT/AGENTS.md" "$DEST/sdd-templates/"
cp "$ROOT/SDD_MANIFESTO.md" "$DEST/sdd-templates/"
cp "$ROOT/agent_docs/sdd_bootstrap.md" "$DEST/sdd-templates/"

# BPMN ガイドは v0.4.0 で cowork-plugin/bpmn/ に統合移動 (drift 防止)。
# reference_files/docs/ への copy は廃止。$DEST/docs/ は不要 (ディレクトリ自体作成しない)。

echo "✅ Sync complete. Files in $DEST:"
FOUND=$(find "$DEST" -type f | wc -l | tr -d ' ')
echo "  Found: $FOUND files"

# 46 ファイル厳守チェック (v0.4.0 で 49 → 46、BPMN 4 ファイルが bpmn/ に移動)
if [ "$FOUND" -ne 46 ]; then
    echo "⛔ [BLOCKER] reference_files 数が想定と一致しません: 期待 46 / 実際 $FOUND"
    echo "内訳:"
    echo "  manual/                  : $(find "$DEST/manual" -type f 2>/dev/null | wc -l | tr -d ' ') (期待 13)"
    echo "  constitution.md          : $(find "$DEST" -maxdepth 1 -name 'constitution.md' | wc -l | tr -d ' ') (期待 1)"
    echo "  constitution_amendments/ : $(find "$DEST/constitution_amendments" -type f 2>/dev/null | wc -l | tr -d ' ') (期待 3)"
    echo "  policies/                : $(find "$DEST/policies" -type f 2>/dev/null | wc -l | tr -d ' ') (期待 5)"
    echo "  templates/upstream/      : $(find "$DEST/templates/upstream" -type f 2>/dev/null | wc -l | tr -d ' ') (期待 16)"
    echo "  templates/ (top)         : $(find "$DEST/templates" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ') (期待 4)"
    echo "  sdd-templates/           : $(find "$DEST/sdd-templates" -type f 2>/dev/null | wc -l | tr -d ' ') (期待 3)"
    echo "  migration/               : $(find "$DEST/migration" -type f 2>/dev/null | wc -l | tr -d ' ') (期待 1)"
    echo "  (BPMN 関連は cowork-plugin/bpmn/ に統合済、reference_files から除外)"
    exit 1
fi
echo "✅ 46 reference files confirmed (BPMN 4 ファイルは bpmn/ に統合済、v0.4.0)"
