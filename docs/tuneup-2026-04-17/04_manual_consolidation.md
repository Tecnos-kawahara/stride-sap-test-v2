# Task: manual/ と manual2/ の関係を整理、single source of documentation 化

## 前提コンテキスト

- プロジェクト: `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`（Tecnos-STRIDE v5.1.0）
- 問題: エンドユーザー向けマニュアルが `manual/`（51 docs, v5.1 最新）と `manual2/`（~21 docs, バージョン不明、2026-04-08 更新）の2系統ある。dual maintenance burden、読者の混乱、検索 SEO 分断。
- 背景: v5.1 チューンナップで判明した governance 外の整理候補。選択肢 A/B/C あり、**ユーザー判断必須**なため、このタスクは「調査 → 選択肢提示 → ユーザー承認 → 実施」の対話形式。

## 作業開始前に読むファイル（順序厳守）

1. `agent_docs/sdd_bootstrap.md` §1（実行モデル、HITL モード）
2. `README.md`（マニュアルへの参照があるか）
3. `manual/index.html`（Docsify 設定）
4. `manual/_sidebar.md`（manual/ の目次）
5. `manual/_coverpage.md`（version badge）
6. `manual2/` のトップレベル構造 (`ls` で確認)
7. `manual2/` のトップ index / _sidebar (存在すれば)
8. 両ディレクトリの git log（履歴と意図推測）:
   ```bash
   git log --follow --oneline manual/ | head -20
   git log --follow --oneline manual2/ | head -20
   ```

## 作業手順

### Phase A: 事実確認（read-only、ユーザーに選択肢提示まで編集しない）

1. **目次・版数・最終更新を対比**:
   ```bash
   echo "=== manual/ ==="
   ls manual/ | sort
   cat manual/_coverpage.md 2>/dev/null | head -5
   echo "=== manual2/ ==="
   ls manual2/ | sort
   head -5 manual2/*.md 2>/dev/null | head -30
   ```

2. **内容の重複度を採点**:
   - manual2/ の各ドキュメントが manual/ のどのファイルに対応するか一覧表化
   - 重複度: **完全重複** / **部分重複** / **manual2 独自** / **manual/ 独自** の4分類
   - タイトルだけでなく冒頭 30 行程度を読み比べる

3. **意図の推測**:
   - manual2/ は manual/ の restructure 試行か、それとも別対象読者向けか
   - git log で「manual2 導入」コミットを発見し、commit message を読む
   - 不明なら「推測 + リスク」として提示する

### Phase B: 選択肢提示

**必ずユーザーに選択肢を提示し、対話で 1 つ選択してもらってから Phase C に進む**（AI は独断で削除しない）。

選択肢:
- **A - manual/ を SSoT とし、manual2/ を archive/ へ移動 (recommended)**:
  - 理由: manual/ が v5.1 反映済み、51 docs で網羅的
  - manual2/ 独自コンテンツ（Phase A で特定）があれば manual/ に取込んでから archive
  - `archive/manual2-YYYY-MM-DD/` に移動、`.gitignore` 対象外として履歴を保持
- **B - manual2/ を SSoT として promote、manual/ を archive**:
  - 理由: 構造が新しい読者向けに整理されている等の積極的理由がある場合のみ
  - manual/ の v5.1 固有内容（harness, v5.1.0 guide 等）を manual2/ に移植してから archive
  - リスク: 大規模な移植作業
- **C - 両方を維持、役割を明確化（異なる対象読者向け等）**:
  - 理由: 明示的な読者分離がある場合（例: manual/ = 開発者、manual2/ = ステークホルダー）
  - 各 README 冒頭に「この manual は <対象> 向け」と明記
  - CI で相互参照の整合性チェック追加

### Phase C: 選択後の実施

**A を選択した場合**:
1. manual2/ 独自コンテンツを manual/ の適切な章に取込み
2. `git mv manual2/ archive/manual2-2026-04-17/`
3. `manual/_sidebar.md` に「v5.1 時点で manual2 を archive 化」と1行注記（読者向け）
4. README.md のマニュアルリンクを manual/ に統一
5. `.symphony/` / `.github/` 内の `manual2` 参照を grep で発見し manual/ に書換え

**B を選択した場合**:
1. manual/ 固有内容を manual2/ の該当章に移植
2. `git mv manual/ archive/manual-legacy-2026-04-17/`
3. `manual2/` を `manual/` にリネーム（単一名のみ残す）
4. Docsify 設定を更新

**C を選択した場合**:
1. 両 README 冒頭に役割宣言を追記
2. cross-link セクションを各 README に作成
3. `.github/workflows/` に「manual と manual2 の version field 整合チェック」ワークフロー追加

### Phase D: 検証

- Docsify が動作するか: `npx docsify-cli serve manual/` で index 表示
- broken link なし: `markdown-link-check manual/**/*.md`
- README/CLAUDE.md/sdd_bootstrap.md からマニュアルへのリンクが生きている
- CI が PASS

## 制約

- **ユーザー承認を得るまで `git mv` / `rm` / コンテンツ削除は絶対禁止**
- 選択肢 A/B/C の判断基準は、読者体験と maintenance cost の 2 軸のみで評価（好みで決めない）
- APPROVAL.md / WI-*.approval.md は絶対に編集しない
- `specs/` 配下には触れない（SDD Phase Gate 対象外の作業）
- 破壊的操作（削除、rename）は必ず `archive/` 配下に git mv で実施。rm 禁止

## 完了条件

- [ ] Phase A の対比表を提示した
- [ ] Phase B でユーザーが A/B/C の1つを明示的に承認した
- [ ] 承認後の作業が Phase C に従って完了
- [ ] Docsify が起動し、選択後の SSoT マニュアルで index が表示される
- [ ] broken link 0 件
- [ ] README.md / CLAUDE.md / agent_docs/* のマニュアル参照が整合
- [ ] `git status` で未追跡ファイルなし、archive/ 配下は履歴保持済み

## 検証コマンド

```bash
# Phase A
ls manual/ manual2/ | head -40
git log --oneline manual/ | head -5
git log --oneline manual2/ | head -5

# Phase D
npx docsify-cli serve manual/ &  # バックグラウンド起動、Ctrl+C で停止
# ブラウザで http://localhost:3000 を確認（可能なら scr）

# broken link
find manual/ -name "*.md" -exec grep -Hn "\[.*\](.*\.md)" {} \; | head -30

# 参照整合
grep -rn "manual/" CLAUDE.md README.md agent_docs/ SDD_MANIFESTO.md
grep -rn "manual2/" CLAUDE.md README.md agent_docs/ SDD_MANIFESTO.md
# 両方とも選択後の SSoT のみに統一されていること
```

## 報告テンプレート

```
## Task Completion Report: manual/ vs manual2/ 整理

### Phase A findings
- manual/: 51 docs, v5.1.0 反映済み, 最終更新 <date>
- manual2/: <N> docs, バージョン記載 <あり/なし>, 最終更新 <date>
- 重複度: 完全重複 <X>件, 部分重複 <Y>件, manual2独自 <Z>件, manual独自 <W>件

### Phase B: user decision
- 提示した選択肢: A/B/C
- ユーザー選択: <A/B/C>
- 選択理由: <ユーザーの述べた理由>

### Phase C: actions taken
- <具体的操作を列挙>
- archive 先: <path>
- 取込み内容: <内訳>

### Phase D: verification
- Docsify: OK
- broken links: 0
- 参照整合: CLAUDE.md ✅ README.md ✅ agent_docs/ ✅

### Diff summary
- moved: <N> files
- rewritten: <M> files
- added archive note: <K> files
```
