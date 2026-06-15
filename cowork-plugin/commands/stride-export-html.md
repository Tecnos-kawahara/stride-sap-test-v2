---
description: basic_design.md を顧客レビュー用 HTML に 1 コマンドで変換。Tecnos-STRIDE 本体の scripts/build_basic_design_html.py を呼び出し、specs/<feature>/exports/basic_design_<feature>.html を生成する。
argument-hint: "<feature_name>"
---

# /stride:export-html

Tecnos-STRIDE VALUE Upstream Extension の Phase 1 完成成果物 (`basic_design.md`) を **顧客レビュー用 HTML** に 1 コマンドで変換します。Tecnos-STRIDE 本体の `scripts/build_basic_design_html.py` を呼び出し、自己完結 HTML (CSS 同梱) を生成。

> Phase F-2 中優先 新規 (WI-VALF01-011 / 改善要望-10): basic_design.md が Markdown のままで顧客レビュー時に読みづらい問題を解消。

## Usage

```
/stride:export-html <feature_name>
```

## Workflow

### 1. Validate Input

- `specs/<feature_name>/basic_design.md` が存在 (Phase 1 完了済み)
- **前提**: Tecnos-STRIDE 本体が clone 済み (Plugin 単体では HTML 不可、DR-103: Plugin 配布物最小化)
- **前提**: Python 3.11+ + `markdown` package (未 install の場合は `pip install markdown` を提案)

### 2. ★ Tecnos-STRIDE 本体 helper 実行

```bash
FEATURE="<feature_name>"

# 必須: Tecnos-STRIDE 本体 clone 済み (DR-103 = Plugin 配布物最小化)
if [ ! -f scripts/build_basic_design_html.py ]; then
  echo "⛔ [BLOCKER] Tecnos-STRIDE 本体 helper not found: scripts/build_basic_design_html.py"
  echo "本コマンドは Tecnos-STRIDE 本体 clone を前提とします。"
  echo "未 clone の場合: git clone https://github.com/tecnos-japan-cbp/tecnos-stride.git"
  exit 1
fi

# 依存 module check
if ! python3 -c "import markdown" 2>/dev/null; then
  echo "ℹ markdown module 未 install。次で install してください:"
  echo "    pip install markdown"
  exit 2
fi

# HTML 生成
python3 scripts/build_basic_design_html.py "specs/${FEATURE}/basic_design.md"
```

### 3. Output

- `specs/<feature_name>/exports/basic_design_<feature_name>.html` (顧客レビュー用 HTML)
- HTML は **自己完結** (外部 CSS / JS 不要)、メールや SharePoint / 顧客 web で直接表示可能

### 4. Notes

- **DR-103 (Phase F decision)**: HTML helper は Tecnos-STRIDE 本体の `scripts/` 配下に配置し、Plugin (`cowork-plugin/`) には**同梱しない**。理由: Plugin 配布物の最小化と、HTML 出力ロジックを本体側で集中管理するため
- 顧客実データを basic_design.md に含めない (§Rule 15-B)。HTML 出力は basic_design.md の内容をそのまま反映するため、サニタイズ済の状態で生成される
- CSS は HTML テンプレ内 inline で同梱 (オフライン環境でもレイアウト維持)
- 顧客 PJ の Cowork Project 側で Plugin を使う場合、本コマンドは Tecnos-STRIDE template repo を clone 済みの環境でのみ動作

### 5. Next Step

- 顧客レビューミーティングで HTML を提示
- フィードバック反映時は `basic_design.md` を直接編集後、再度 `/tecnos-stride-value:stride-export-html` 実行で HTML を更新

> Phase F (WI-VALF01-011) で HTML 出力を新規追加。Phase E v0.1.0-poc → v0.2.0-stable。
