# Task: Canonical YAML 抽出関数を `stride_shared_lib.py` に集約

## 前提コンテキスト

- プロジェクト: `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`（Tecnos-STRIDE v5.1.0）
- 問題: Canonical YAML ブロック抽出 (`# 0. Canonical ... (YAML)` ヘッダー以降の ` ```yaml ... ``` ` を抽出する) ロジックが **4+ ファイルに重複コピー**されている。regex drift の危険。
- 背景: v5.1 チューンナップ 2026-04-17 の調査で判明した最大の構造負債（別セッション報告書参照）

## 目的

共通ライブラリ `sdd-templates/tools/stride_shared_lib.py` を新設し、YAML 抽出関数を 1 箇所に集約。全 caller を書換えて重複削除。**既存の全セルフテスト・CLI 動作・JSON 出力スキーマに影響を与えない**リファクタ。

## 作業開始前に読むファイル（順序厳守）

1. `agent_docs/sdd_bootstrap.md` §1-2（実行モデル、AI Action Boundary）
2. `agent_docs/sdd_bootstrap.md` §4b（Completeness Principle — 湖/海 数値基準）
3. `agent_docs/sdd_bootstrap.md` §5（Task Completion Checklist）
4. 重複箇所を特定するため以下をすべて読む:
   - `sdd-templates/tools/stride_lint.py` — `extract_yaml_blocks` / `extract_canonical_yaml` / 同等の内部関数
   - `sdd-templates/tools/multi_model_evaluator.py` — `build_compact_packet` 周辺の YAML 抽出
   - `sdd-templates/tools/sdd_planning_bridge.py` — spec/plan 読取部
   - `sdd-templates/tools/wi_readiness_checker.py` — basic_design/tasks 読取部
   - `sdd-templates/tools/amendment_generator.py` — Spec diff 周辺
   - `sdd-templates/hooks/phase_gate_hook.py`
   - `sdd-templates/hooks/post_edit_guard.py`
5. `sdd-templates/docs/stride_lint_spec.md`（lint ルール仕様）

## 作業手順

### Phase A: 調査（read-only, brv query 相当）

1. 重複関数の特定。各ファイルで以下のパターンを grep:
   ```bash
   cd /Users/j620h-okzk/ZINOKZ/sdd_template_enterprise
   grep -n "Canonical.*YAML\|extract.*yaml\|def.*yaml.*block\|# 0\." sdd-templates/tools/*.py sdd-templates/hooks/*.py
   ```
2. 各重複実装の差分を diff で可視化（`colordiff` or `diff -u`）
3. 仕様を統合: 「最も厳しい caller の要件」を満たす単一シグネチャを設計
   - 必須: ファイルパス受取り → dict を返す
   - `# 0. Canonical` ヘッダー名のバリエーション（`Canonical Basic Design` / `Canonical Spec` / `Canonical Plan` / `Canonical Tasks` 等）の正規化
   - フェンス付き / フェンス無し両対応
   - マルチブロック対応（ファイルに複数 canonical block あり得る）
   - エラー時の挙動: malformed YAML は例外 or None（caller の既存挙動を壊さない方を選ぶ）

### Phase B: 新モジュール作成

ファイル: `sdd-templates/tools/stride_shared_lib.py`

必須 API:
```python
def extract_canonical_yaml(
    path: pathlib.Path,
    *,
    section: Optional[str] = None,  # "spec", "plan", "tasks", "basic_design", None=all
    strict: bool = False,            # True=raise on malformed, False=return None
) -> Optional[dict]:
    """Canonical YAML ブロックを抽出。

    Canonical ヘッダー（`# 0. Canonical ... (YAML)` または `# 1. Canonical Tasks (YAML)`）
    の直後のフェンス付き yaml ブロックを読み取り、dict として返す。

    複数 section ある場合 section 指定必須。無指定かつ複数ある場合は TypeError。
    """

def extract_frontmatter_yaml(path: pathlib.Path) -> Optional[dict]:
    """ファイル冒頭の --- yaml --- フロントマターを抽出。"""

def find_all_canonical_blocks(path: pathlib.Path) -> List[tuple[str, dict]]:
    """(section_name, parsed_dict) のリスト。section_name は正規化後（snake_case）。"""
```

### Phase C: セルフテスト追加

`sdd-templates/tools/stride_shared_lib.py` 末尾に `_run_self_tests()` を実装:
- Test 1: 単一 Canonical block（spec.md サンプル）
- Test 2: 複数 Canonical block（basic_design + spec + plan 連結ファイル）
- Test 3: malformed YAML（strict=True で raise, strict=False で None）
- Test 4: フェンス無しバリエーション（旧テンプレ互換）
- Test 5: frontmatter 抽出
- Test 6: 空ファイル / 存在しないパス
- Test 7: section 指定ミスマッチ（section="tasks" 指定だが basic_design しか無い → None）
- Test 8: section 無指定で複数 block あり → TypeError

### Phase D: caller 書換え

上記調査で特定した caller を順に書換え:
1. `stride_lint.py` — 最難関。既存挙動を完全保持。既存の `_run_self_tests()` 相当が全 PASS を維持
2. `multi_model_evaluator.py` — prompt packet 作成の入力形式が変わらないことを確認
3. `sdd_planning_bridge.py` — init/sync/evidence/learn 各コマンドが同じ出力
4. `wi_readiness_checker.py` — 17 tests 全 PASS
5. `amendment_generator.py` — 61 tests 全 PASS
6. `phase_gate_hook.py` / `post_edit_guard.py` — hook として静かに動作（fail-open）

各書換えごとに `stride-lint specs/FEAT-ERPSAMPLE/` を実行し既存エラー数（3: RUN_MULTIPLE / WALKTHROUGH_MISSING / TEST_RESULTS_MISSING）が不変であることを確認。新規エラー発生は回帰。

### Phase E: 重複コード削除

- 各 caller 内の重複関数定義を削除
- `from stride_shared_lib import extract_canonical_yaml` の import を追加
- 内部関数参照が残っていないか `grep` で確認

### Phase F: ドキュメント

- `sdd-templates/docs/stride_lint_spec.md` に「YAML 抽出は stride_shared_lib に集約」と1パラグラフ追記
- `sdd-templates/tools/stride_shared_lib.py` の docstring に全 API 仕様を記載

## 制約（INVIOLABLE）

- **公開 CLI の挙動・exit code・JSON/NDJSON 出力スキーマを変更しない**
- **既存セルフテストを PASS のまま維持**（特に stride_lint.py の 50+ tests）
- 新規依存パッケージ禁止（PyYAML / pathlib / re / dataclasses のみ使用）
- `APPROVAL.md` / `WI-*.approval.md` は絶対に編集しない
- ツール配下のコード変更のみ。`specs/` 内は編集しない（Phase Gate の対象外なので影響しない）
- Completeness 湖判定: 全体で **+400 行以内**（新モジュール本体 + test + caller 合計）。超える場合は Phase 分割を提案して停止

## 完了条件

- [ ] `stride_shared_lib.py` が新設され `--test` で全 8 テスト PASS
- [ ] 重複関数が全 caller から削除されている（grep 確認）
- [ ] 全ツールセルフテスト継続 PASS:
  - pr_readiness_checker: 10/10
  - wi_readiness_checker: 17/17
  - evidence_metrics_collector: 6/6
  - stride_health: 6/6
  - stride_harness_report: 6/6（※ Prompt 1 適用済み前提。未適用なら 5/6 維持）
  - amendment_generator: 61/61
  - stride_shared_lib: 8/8 (new)
- [ ] `stride-lint specs/FEAT-ERPSAMPLE/` の出力がリファクタ前後で**完全一致**（diff 空）
- [ ] stride CLI の `stride lint -o json specs/FEAT-ERPSAMPLE/` の JSON 出力が**完全一致**
- [ ] import grep で旧関数の生き残りがない:
  ```bash
  grep -rn "def extract_canonical_yaml\|def extract_yaml_blocks" sdd-templates/tools/ sdd-templates/hooks/ | wc -l
  # → 期待値: 1（stride_shared_lib.py のみ）
  ```

## 検証コマンド

```bash
# リファクタ前に baseline 取得
sdd-templates/bin/stride lint specs/FEAT-ERPSAMPLE/ -o json > /tmp/lint-before.json
sdd-templates/bin/stride lint specs/FEAT-ERPSAMPLE/ --coverage-report > /tmp/lint-before.txt

# リファクタ後に検証
sdd-templates/bin/stride lint specs/FEAT-ERPSAMPLE/ -o json > /tmp/lint-after.json
sdd-templates/bin/stride lint specs/FEAT-ERPSAMPLE/ --coverage-report > /tmp/lint-after.txt
diff /tmp/lint-before.json /tmp/lint-after.json  # 空であること
diff /tmp/lint-before.txt /tmp/lint-after.txt    # 空であること

# 全セルフテスト
for tool in pr_readiness_checker wi_readiness_checker evidence_metrics_collector stride_health stride_harness_report amendment_generator stride_shared_lib; do
  echo "=== $tool ==="
  python3 sdd-templates/tools/${tool}.py --test 2>&1 | tail -3
done

# 重複削除確認
grep -rn "def extract_canonical_yaml\|def extract_yaml_blocks" sdd-templates/
```

## 報告テンプレート

```
## Task Completion Report: stride_shared_lib.py 新設とリファクタ

### Discovered duplicates
- stride_lint.py:<line-range>
- multi_model_evaluator.py:<line-range>
- sdd_planning_bridge.py:<line-range>
- wi_readiness_checker.py:<line-range>
- amendment_generator.py:<line-range>
- phase_gate_hook.py:<line-range>
- post_edit_guard.py:<line-range>

### New module API
- extract_canonical_yaml(path, section, strict)
- extract_frontmatter_yaml(path)
- find_all_canonical_blocks(path)

### Migration
- <callers> が新 API を使用
- 重複関数 <N> 件削除

### Test results
stride_shared_lib: 8/8 PASS (new)
stride_lint integration: ±0 diff (baseline preserved)
pr_readiness_checker: 10/10 PASS
... (全て列挙)

### Diff size
<M> lines added (stride_shared_lib + tests)
-<N> lines removed (duplicates)
Net: +<M-N> lines (湖判定 ✅)

### Follow-ups
（任意：次の tune-up 候補があれば列挙）
```
