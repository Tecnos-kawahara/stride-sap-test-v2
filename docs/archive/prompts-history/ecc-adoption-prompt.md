# ECC ティップス採用 — 実装プロンプト

作業ディレクトリ: /Users/j620h-okzk/ZINOKZ/sdd_template_enterprise

## 背景

Everything Claude Code (ECC) リポジトリのアイデアから、Tecnos-STRIDE に以下の4点を採用する。
優先順序で実装すること。

- **Priority 1:** `lessons.md` スキーマ統一 + repo内 `learn` サブコマンド導入
- **Priority 2:** 軽量 `PostToolUse` quality gate hook 導入
- **Priority 3:** Search-First を Design/Specify の prompt/checklist に移植
- **Priority 4:** Phase handoff summary（必要に応じて）

---

## Priority 1: lessons.md スキーマ統一 + `learn` サブコマンド

### 問題の所在

`sdd_planning_bridge.py` の `cmd_init`（L313-341）が生成する `lessons.md` と、
`epic_progress_aggregator.py` の `_parse_lesson_items`（L1243-1256）が読み取る `lessons.md` のスキーマが不一致。

**書き出し側（sdd_planning_bridge.py L313-341）の見出し:**
```
## Inherited Knowledge Effectiveness
## Best Practices Discovered
## Troubles Resolved
## Technical Knowledge
## Archive Summary
```

**読み取り側（epic_progress_aggregator.py L1243-1256）が探す見出し:**
```
## Reusable Patterns
```

→ `_parse_lesson_items` は `## Reusable Patterns` セクションのみをパースするため、
`Best Practices Discovered` / `Troubles Resolved` / `Technical Knowledge` に書かれた教訓は全て無視される。

### Step 1: スキーマ統一

**方針:** 書き出し側（sdd_planning_bridge.py）のスキーマを正とし、読み取り側を合わせる。
既存のRunに書かれた `lessons.md` との後方互換も維持する。

1. **`sdd_planning_bridge.py` L313-341 を確認**
   - 現行の見出し構造をそのまま維持する（変更しない）
   - ただし `## Archive Summary` テーブルの `Type` 列の値域を明確化する（列の追加はしない）:

   ```
   ## Archive Summary
   | ID | Type | Title | Reusability | Archive? |
   |----|------|-------|-------------|----------|
   ```
   
   `Type` の値: `best_practice` / `trouble` / `technical` / `reusable_pattern`
   （現行の5列構造を維持。列数は変更しない）

2. **`epic_progress_aggregator.py` の `_parse_lesson_items`（L1243-1256）を修正**
   - `## Reusable Patterns` だけでなく、以下の全セクションからアイテムを抽出するように変更:
     - `## Best Practices Discovered`
     - `## Troubles Resolved`
     - `## Technical Knowledge`
     - `## Reusable Patterns`（後方互換）
   - **戻り値は `List[str]` のまま変更しない**（`WeeklyRunData.lessons: List[str]` および
     `format_weekly_summary` L1360付近の Markdown テーブル出力がそのまま文字列前提のため）
   - 各アイテムの先頭に `[BP]` / `[TR]` / `[TK]` / `[RP]` のカテゴリプレフィックスを付与する:
     - `## Best Practices Discovered` の行 → `"[BP] original text"`
     - `## Troubles Resolved` の行 → `"[TR] original text"`
     - `## Technical Knowledge` の行 → `"[TK] original text"`
     - `## Reusable Patterns` の行 → `"[RP] original text"`（後方互換）
   - これにより `WeeklyRunData.lessons`、`len()`、Markdown テーブル出力は一切壊れない
   - 必要な場合、消費側でプレフィックスをパースしてカテゴリ分類できる

### Step 2: `learn` サブコマンド追加

**`sdd_planning_bridge.py` に `cmd_learn` 関数を追加する。**

入力: `python3 sdd-templates/tools/sdd_planning_bridge.py learn <feature_dir> <wi_id> [<run_dir>]`

処理:
1. `.planning/` から以下のファイルを読む:
   - `findings.md` — 調査メモ
   - `plan.md` — Errors テーブル（stride-lint FAIL履歴）、Decisions テーブル
   - stride-lint の最新出力（`cmd_sync` と同様に実行して取得）

   **注意:** `walkthrough.md`（RUN直下）は読まない。walkthrough は evidence 生成のソースであり、
   lesson 抽出のソースは上記3ファイルに限定する。

2. 以下のルールで `lessons.md` の各セクションに追記候補を**標準出力に提示**する（自動書き込みしない）:

   | 情報ソース | 抽出ルール | 分類先 |
   |-----------|-----------|--------|
   | `plan.md` Errors テーブル | `attempt` が 2以上（リトライした）のエラー | `## Troubles Resolved` |
   | `plan.md` Decisions テーブル | 全件 | `## Best Practices Discovered`（判断の記録） |
   | `findings.md` | `## Technical Notes` 配下の非空行 | `## Technical Knowledge` |
   | stride-lint 結果 | 今回のRunで発生した FAIL パターン（APPROVAL除外） | `## Troubles Resolved` |

3. 出力フォーマット:
   ```
   === Lesson Candidates for WI-XXX ===
   
   ## Best Practices Discovered (from Decisions)
   - D1: [decision content] — Rationale: [rationale]
   
   ## Troubles Resolved (from Errors with retries)
   - E3: [error] → Fix: [resolution] (attempts: 2)
   
   ## Technical Knowledge (from findings.md)
   - [technical note]
   
   ## Archive Summary (suggested rows)
   | BP-001 | best_practice | [title] | cross-feature | Yes |
   | TR-001 | trouble | [title] | feature-specific | Maybe |
   
   To apply: review above and manually add to .planning/lessons.md
   Then run: /planning:archive (Claude Code built-in command) to save to global knowledge
   ```

4. **`--apply` フラグ**を付けた場合のみ、lessons.md に直接追記する

5. `main()` のsubparser登録を追加（L607付近）:
   ```python
   learn_parser = subparsers.add_parser("learn", help="Extract lesson candidates from Run artifacts")
   learn_parser.add_argument("feature_dir", type=Path)
   learn_parser.add_argument("wi_id")
   learn_parser.add_argument("run_dir", type=Path, nargs="?", default=None)
   learn_parser.add_argument("--apply", action="store_true", help="Write candidates directly to lessons.md")
   ```

### Step 3: ドキュメント更新

1. `agent_docs/commands.md` に `learn` サブコマンドを追加
2. `agent_docs/sdd_bootstrap.md` セクション6の WI フロー（L109-120付近）に、ステップ6c（evidence の後）として追記:
   ```
   6c. `sdd_planning_bridge.py learn` → lesson候補を確認、必要なら `--apply`
   ```

### テスト

1. `sdd_planning_bridge.py` の既存テストがあるか確認: `find . -name "test_*planning*" -o -name "*planning*test*"`
2. `cmd_learn` のユニットテストを作成:
   - Errors テーブルに `attempt >= 2` の行がある plan.md → `Troubles Resolved` に候補が出ること
   - Decisions テーブルに行がある plan.md → `Best Practices Discovered` に候補が出ること
   - findings.md の `## Technical Notes` に内容がある → `Technical Knowledge` に候補が出ること
   - `--apply` フラグで lessons.md に追記されること
3. `_parse_lesson_items` の修正テスト:
   - 旧形式（`## Reusable Patterns` のみ）の lessons.md でも正しくパースできること（後方互換）
   - 新形式（4セクション全て）の lessons.md で全アイテムが抽出されること

### 検証

```bash
# 型チェック
python3 -c "import ast; ast.parse(open('sdd-templates/tools/sdd_planning_bridge.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('sdd-templates/tools/epic_progress_aggregator.py').read()); print('OK')"

# 既存テスト
python3 -m pytest sdd-templates/tools/ -x -q 2>/dev/null || echo "No pytest tests found"

# 新規テスト
python3 -m pytest <新規テストファイル> -x -q
```

---

## Priority 2: 軽量 PostToolUse quality gate hook

### 問題の所在

現在の hook は `sdd-templates/hooks/settings.json` + `phase_gate_hook.py` の **PreToolUse（Write/Edit ブロック）** のみ。
編集後の品質チェックがない。

`spec_drift_detector.py` は `contracts/` と `src/` を広く走査するため、毎 Edit 後に回すには重すぎる。
ECC の `quality-gate.js` も実際は「編集したファイル単位の軽量チェック」。

### 設計方針

- `PostToolUse` に新規の **軽量 guard**（`post_edit_guard.py`）を追加
- **touched file 単位** で小さく検査する（プロジェクト全体走査はしない）
- `spec_drift_detector.py` は `after_run` / 明示コマンドに残す

### Step 1: `post_edit_guard.py` を新規作成

場所: `sdd-templates/hooks/post_edit_guard.py`

**Claude Code PostToolUse Hook Protocol:**
- stdin に JSON: `{"tool_name": "Edit", "tool_input": {"file_path": "..."}, "tool_result": {...}}`
- stdout に JSON: `{"decision": "allow"}` のみ（PostToolUse では block/notification は使わない）
- **警告の伝達方法:** 問題を検出した場合は **stderr にメッセージを出力** する
  - stderr 出力は Claude Code のコンテキストに渡り、エージェントが認識できる
  - stdout の JSON は常に `{"decision": "allow"}` を返す（fail-open 原則）
  - この repo 内の既存 hook（`phase_gate_hook.py`）は PreToolUse の block/allow のみ使用しており、
    PostToolUse の `notification` フィールドは未検証のため、stderr 方式が安全

**検査ロジック（touched file のパスに応じて分岐）:**

| 変更ファイルのパターン | 検査内容 | 重さ |
|----------------------|---------|------|
| `specs/*/contracts/*.yaml` | YAML 構文チェック（`yaml.safe_load` のみ） | 極軽量 |
| `specs/*/spec.md` | Canonical YAML ブロックのパース可否チェック | 極軽量 |
| `specs/*/plan.md` | `coverage_policy` の存在チェック | 極軽量 |
| `specs/*/tasks.md` | 全 task に `plan_refs` があるか（正規表現） | 軽量 |
| `specs/*/basic_design.md` | Canonical YAML を軽くパースし `basic_design.traceability_rows` と `basic_design.delivery_model` の存在チェック | 極軽量 |
| 上記以外 | 検査なし（即 allow） | なし |

**実装の注意点:**
- `yaml` モジュールが import できない場合は graceful に skip（`yaml = None` パターン、既存コードと同じ）
- エラー時は `{"decision": "allow"}` を返す（fail-open。hookの障害で開発を止めない）
- 処理全体を 2秒以内に収める
- `phase_gate_hook.py` と同じ `_configure_console_encoding()` を冒頭に入れる（Windows対応）

**出力例（警告時）:**

stdout:
```json
{"decision": "allow"}
```

stderr:
```
⚠ post_edit_guard: specs/my-feature/contracts/openapi.yaml — YAML parse error at line 42: mapping values are not allowed here
```

### Step 2: `settings.json` に PostToolUse hook を追加

`sdd-templates/hooks/settings.json` を更新:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/sdd-templates/hooks/phase_gate_hook.py\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/sdd-templates/hooks/post_edit_guard.py\""
          }
        ]
      }
    ]
  }
}
```

### Step 3: ドキュメント更新

1. `agent_docs/sdd_bootstrap.md` セクション7（品質ゲートコマンド）に PostToolUse hook の存在を追記
2. `CLAUDE_WORKFLOW.md` の Tooling Setup セクションに追記

### テスト

`post_edit_guard.py` のユニットテスト（stdout は常に `{"decision": "allow"}`、警告は stderr で判定）:
1. `contracts/*.yaml` の正常YAML → stderr 空
2. `contracts/*.yaml` の壊れたYAML → stderr に parse error メッセージ
3. `spec.md` に Canonical YAML がある → stderr 空
4. `spec.md` に Canonical YAML がない/壊れている → stderr に警告
5. `tasks.md` の全 task に `plan_refs` がある → stderr 空
6. `tasks.md` に `plan_refs` のない task がある → stderr に警告
7. `specs/` 外のファイル → 即 allow、stderr 空
8. stdin が不正JSON → fail-open（allow、stderr 空）

### 検証

```bash
# 構文チェック
python3 -c "import ast; ast.parse(open('sdd-templates/hooks/post_edit_guard.py').read()); print('OK')"

# JSON整合性
python3 -c "import json; json.load(open('sdd-templates/hooks/settings.json')); print('OK')"

# 手動テスト（正常ケース）
echo '{"tool_name":"Edit","tool_input":{"file_path":"specs/test/spec.md"},"tool_result":{}}' | python3 sdd-templates/hooks/post_edit_guard.py

# 新規テスト
python3 -m pytest <新規テストファイル> -x -q
```

---

## Priority 3: Search-First を Design/Specify prompt に移植

### 設計方針

Execute Phase ではなく **Design/Specify Phase** のプロンプトとチェックリストに「探索ラダー」を入れる。
Tasking 以降で外部探索を強めると spec/task 固定後に設計が揺れるリスクがあるため。

### Step 1: SYMPHONY.md の Design/Specify プロンプトに追記

`SYMPHONY.md` L105 以降の `{% if phase == "design" %}` ブロックに、Step 1.5 として追加:

```
1.5. **探索ラダー**（既存解の確認、新規実装の前に必ず実施）
   - [ ] **プロジェクト内:** `rg` / `grep` で既存の類似実装を検索
   - [ ] **過去の教訓:** `~/.claude/knowledge/index.json` と直近 Runs の `lessons.md` を確認
   - [ ] **パッケージ/ライブラリ:** npm / PyPI / crates.io で既存の解がないか
   - [ ] **契約との整合:** 既存の `shared/contracts/` や他 feature の `contracts/` に類似定義がないか
   → 結果を `basic_design.md` の `## B.2 契約（Contract/CLI-First）` セクションに反映
```

同様に `{% elif phase == "specify" %}` ブロックに、Step 0.5 として追加:

```
0.5. **探索ラダー**（spec.md 作成前に実施）
   - [ ] 他 feature の `spec.md` で類似の AC/NFR パターンがないか確認
   - [ ] `shared/contracts/` の共通コントラクトとの整合を事前確認
   - [ ] 既存の `tests/scenarios.yaml` で再利用可能なシナリオがないか
   → 発見した再利用可能要素を `spec.md` の `## 1.4 Spec-as-Code` セクション内に記録
```

### Step 2: `.planning/findings.md` テンプレートに探索ラダー欄を追加

`sdd_planning_bridge.py` の `cmd_init`（L295-311）が生成する `findings.md` テンプレートに、
「探索ラダー」セクションを追加:

```markdown
## Exploration Ladder (Search-First)
- [ ] Project-internal: similar implementations found?
- [ ] Past lessons: relevant knowledge items?
- [ ] External packages: existing solutions?
- [ ] Contract alignment: existing shared contracts?

## Spec Refs
...（既存のまま）
```

### テスト

1. `cmd_init` が生成する `findings.md` に `## Exploration Ladder` が含まれること
2. 既存のテストが壊れていないこと

### 検証

```bash
python3 -c "import ast; ast.parse(open('sdd-templates/tools/sdd_planning_bridge.py').read()); print('OK')"
python3 -m pytest sdd-templates/tools/ -x -q 2>/dev/null || echo "No pytest tests found"
```

---

## Priority 4: Phase handoff summary（低優先）

### 判断基準

Priority 1-3 の実装が完了し、実運用で「Phase間の設計意図ロスト」が実際に問題になった場合のみ着手。
Symphony は phase ごとに別 run なので、コンパクション問題自体は本質的には存在しない。
必要になった場合は、`SYMPHONY.md` の `hooks.after_run` に
`specs/<feature>/state/phase_N_summary.md` 自動生成を追加する。

---

## 完了基準

- [ ] `_parse_lesson_items` が 4 セクションを読めること + 旧形式後方互換テスト PASS
- [ ] `cmd_learn` が lesson 候補を正しく抽出すること + テスト PASS
- [ ] `post_edit_guard.py` が touched file 単位で軽量検査すること + テスト PASS
- [ ] `settings.json` に PostToolUse hook が追加されていること
- [ ] SYMPHONY.md の Design/Specify プロンプトに探索ラダーが追加されていること
- [ ] `findings.md` テンプレートに Exploration Ladder が含まれること
- [ ] `agent_docs/sdd_bootstrap.md` と `agent_docs/commands.md` が更新されていること
- [ ] 全ファイルの構文チェック（ast.parse / json.load / yaml.safe_load）PASS
- [ ] 既存テスト全 PASS

完了したら:
```bash
openclaw system event --text "Done: ECC adoption — lessons schema + learn cmd + PostToolUse guard + search-first prompts" --mode now
```
