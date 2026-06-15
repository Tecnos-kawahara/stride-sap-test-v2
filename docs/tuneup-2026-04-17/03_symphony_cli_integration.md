# Task: `stride symphony <subcmd>` を bin/stride から実呼出しに統合

## 前提コンテキスト

- プロジェクト: `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`（Tecnos-STRIDE v5.1.0）
- 問題: `sdd-templates/bin/stride` の help に `symphony` コマンドが記載され、`agent_docs/commands.md §8` にも `SYMPHONY_RUN`, `SYMPHONY_DISPATCH` 等のコマンド例があるが、**`bin/stride` 本体から実際の dispatch が未実装**。ユーザーは `python3 -m symphony.cli ...` を直接実行する必要があり、UX が割れている。
- 目的: `stride symphony run [--once] [--dry-run]` / `dispatch --issue N` / `status` / `validate` / `janitor [--dry-run]` を `bin/stride` 経由で完全に呼び出せるようにする。

## 作業開始前に読むファイル（順序厳守）

1. `agent_docs/sdd_bootstrap.md` §1-2, §5（実行モデル、報告テンプレート）
2. `SYMPHONY.md`（ルート、janitor セクション含む）
3. `agent_docs/harness.md` §2.4（Janitor 仕様）
4. `sdd-templates/bin/stride` 全体（1834 行）。特に:
   - コマンドディスパッチ機構（argparse or 手書き switch か）
   - 既存の類似サブコマンド実装（`stride epic` がサブコマンドを持つ好例）
   - Python interpreter 解決（`.venv/bin/python` → `python3`）
5. `symphony/cli.py`（Symphony 本体 CLI）
6. `symphony/config.py`（SymphonyConfig, JanitorConfig dataclasses）
7. `symphony/tracker.py`（GitHub Issues 連携、has_recent_pr, create_janitor_issue）
8. `sdd-templates/CHANGELOG.md` の v5.1.0 「Janitor」セクション

## 作業手順

### Phase A: dispatch 機構の理解

1. `bin/stride` でコマンドがどう振り分けられているか読む（switch? argparse? match?）
2. 既存の `stride epic <subcmd>` 実装を精査 — **これと同じ構造**で symphony を追加する
3. Python interpreter 解決ロジックを確認（`.venv` 優先 / `python3` fallback）

### Phase B: CLI 設計

`bin/stride` に以下のサブコマンド追加:

```
stride symphony run [--once] [--dry-run]       # デフォルト: 60s polling
stride symphony dispatch --issue <number>      # 単一 Issue 手動起動
stride symphony status                         # アクティブ/ブロック中のセッション表示
stride symphony validate                       # SYMPHONY.md 設定の検証
stride symphony janitor [--dry-run]            # Janitor 単発実行
```

各サブコマンドは `symphony.cli` の対応関数を呼ぶ（subprocess or import 両選択肢あり。**import の方が好ましい**が、Python path 解決に注意）。

### Phase C: help 更新

- `stride help` で symphony コマンド群が表示される
- `stride symphony --help` でサブコマンド一覧が表示される
- `--help` テキストは `stride epic` と同じフォーマット

### Phase D: テスト

セルフテスト追加先: `sdd-templates/bin/stride` に `--test-symphony` フラグ、または別ファイル `sdd-templates/tests/test_stride_symphony_dispatch.py`:

1. Test 1: `stride symphony --help` が exit 0 を返し、expected 5 subcmds が表示
2. Test 2: `stride symphony validate` が SYMPHONY.md を読み、janitor 設定込みで OK を返す
3. Test 3: `stride symphony run --dry-run --once` が実 GitHub API を叩かず 0 で終了（モック or skip-on-no-token）
4. Test 4: `stride symphony dispatch --issue 99999` が不在 Issue で適切なエラー
5. Test 5: `stride symphony janitor --dry-run` が janitor.enabled を確認し、disabled なら "skipped" を出力

### Phase E: ドキュメント更新

- `agent_docs/commands.md §8` の `SYMPHONY_*` コマンド群を `stride symphony <subcmd>` 経由に書換え
- `agent_docs/harness.md §2.4` の Janitor 呼出し方法を `stride symphony janitor` に統一
- `SYMPHONY.md` の「コマンド参照: agent_docs/commands.md §8」クロスリンクを確認

## 制約

- `symphony.cli` の公開関数シグネチャは**変更しない**（別途テストされているため）
- `SYMPHONY.md` のスキーマは**変更しない**（JanitorConfig フィールドも）
- `stride-lint` / `stride pr-check` の挙動は**変更しない**
- GitHub Issues の実 API を叩くテストは `GH_TOKEN` 未設定環境で **skip** すること
- APPROVAL.md / WI-*.approval.md は絶対に編集しない
- `bin/stride` への追加は **+150 行以内**。超える場合は共通 helper を `symphony/cli_dispatch.py` に切出す

## 完了条件

- [ ] `stride symphony run --once --dry-run` が exit 0 で終了（GH_TOKEN 無し環境）
- [ ] `stride symphony validate` が SYMPHONY.md の janitor 含め PASS を返す
- [ ] `stride symphony --help` が 5 サブコマンド全てを表示
- [ ] 既存コマンド（`stride lint`, `stride pr-check`, `stride epic ...` 等）の挙動が**不変**（回帰なし）
- [ ] `agent_docs/commands.md §8` が stride CLI 経由に書換わっている
- [ ] 既存ツールセルフテスト全 PASS 継続
- [ ] symphony/tests/ の既存テストも全 PASS 継続

## 検証コマンド

```bash
cd /Users/j620h-okzk/ZINOKZ/sdd_template_enterprise

# Phase D テスト
sdd-templates/bin/stride symphony --help
sdd-templates/bin/stride symphony validate
sdd-templates/bin/stride symphony run --once --dry-run
sdd-templates/bin/stride symphony status
sdd-templates/bin/stride symphony janitor --dry-run

# 回帰テスト
sdd-templates/bin/stride --help
sdd-templates/bin/stride lint specs/FEAT-ERPSAMPLE/ | tail -5
sdd-templates/bin/stride pr-check . 2>&1 | tail -3
sdd-templates/bin/stride phase-status specs/FEAT-ERPSAMPLE/

# symphony 側のテスト
cd symphony && python3 -m pytest tests/ -x --tb=short 2>&1 | tail -10
```

## 報告テンプレート

```
## Task Completion Report: stride symphony CLI integration

### Implementation approach
- Dispatch: <argparse / manual switch / other>
- Import strategy: <subprocess / direct import>
- Python resolution: <.venv / python3 fallback>

### New subcommands wired
- stride symphony run [--once] [--dry-run]
- stride symphony dispatch --issue N
- stride symphony status
- stride symphony validate
- stride symphony janitor [--dry-run]

### Lines changed
bin/stride: +<N>
agent_docs/commands.md: <±M>
agent_docs/harness.md: <±K>

### Test results
New symphony dispatch tests: 5/5 PASS
symphony/tests/ existing: <X>/<X> PASS
stride CLI regression: lint ✅ pr-check ✅ epic ✅ phase-status ✅
Other tool self-tests: 全 PASS 継続

### Dependencies
No new packages added.
```
