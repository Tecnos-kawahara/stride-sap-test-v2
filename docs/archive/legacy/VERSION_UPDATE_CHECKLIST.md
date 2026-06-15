# SDD Templates バージョン更新ガイド

v1.2.6-tecnos から、バージョン管理は **VERSION ファイルを Single Source of Truth (SSoT)** とする方式に変更されました。

---

## 新方式（v1.2.6〜）

### バージョン更新手順

```bash
# 1. VERSION ファイルを更新（これが唯一の正）
echo "1.2.7-tecnos" > sdd-templates/VERSION

# 2. CHANGELOG.md に変更内容を追記
# sdd-templates/CHANGELOG.md の先頭に新バージョンセクションを追加

# 3. コミット＆プッシュ
git add -A
git commit -m "chore: Bump version to v1.2.7-tecnos"
git push origin main
```

### VERSION ファイルの仕組み

| ファイル | 役割 |
|----------|------|
| `sdd-templates/VERSION` | **唯一のバージョン正本**（1行テキスト） |

- `stride init` 実行時に VERSION ファイルを読み込み、テンプレート内の `{{TEMPLATE_VERSION}}` を自動置換
- 生成されたファイルには実際のバージョン番号が埋め込まれる

### プレースホルダ一覧

| プレースホルダ | 置換内容 | 対象ファイル |
|---------------|----------|-------------|
| `{{TEMPLATE_VERSION}}` | VERSION ファイルの値 | .md, .yaml, .yml, .ts, .py, .csv |
| `{{FEATURE_NAME}}` | 機能名 | 同上 |
| `{{FEATURE_ID}}` | 機能ID（XXX部分） | 同上 |
| `FEAT-XXX` | FEAT-{ID} | 同上 |

---

## 更新が必要なファイル（手動）

VERSION ファイル更新後、以下は手動更新が必要です。

| ファイル | 更新内容 |
|----------|----------|
| `sdd-templates/CHANGELOG.md` | 新バージョンの変更内容を先頭に追加 |
| `README.md`（ルート） | バージョン履歴テーブルに追加 |

### 更新不要なファイル

以下はバージョン固定表記を削除済みのため、更新不要です。

- `sdd-templates/CHEATSHEET.md` - バージョン番号なし
- `sdd-templates/agent_docs/testing.md` - VERSION参照に変更
- `manual/index.md` - バージョン番号なし
- `manual/index.html` - バージョン番号なし
- 全テンプレートファイル - `{{TEMPLATE_VERSION}}` プレースホルダ使用

---

## 検証コマンド

```bash
# 現在のバージョン確認
cat sdd-templates/VERSION

# テンプレート内にハードコードされたバージョンがないか確認
# ※ archive/ は履歴的ファイルのため除外
# ※ v有無両方を検知 (v1.2.x-tecnos と 1.2.x-tecnos)
grep -r 'v\?1\.2\.[0-9]-tecnos' sdd-templates/templates/ --include="*.md" --include="*.yaml" --include="*.yml" --include="*.ts" --include="*.py" --include="*.csv" | grep -v "archive/"

# プレースホルダが正しく設定されているか確認
grep -r '{{TEMPLATE_VERSION}}' sdd-templates/templates/
```

### 除外対象（チェック不要）

| パス | 理由 |
|------|------|
| `sdd-templates/templates/archive/` | 非推奨の履歴的ファイル（意図的に旧バージョン固定） |
| `sdd-templates/CHANGELOG.md` | 変更履歴（履歴的参照） |
| `manual/*.md` の履歴記載 | 機能追加時のバージョン記録 |

---

## 旧方式との違い

| 項目 | 旧方式（〜v1.2.5） | 新方式（v1.2.6〜） |
|------|-------------------|-------------------|
| 正本 | なし（各ファイルに直書き） | `sdd-templates/VERSION` |
| ディレクトリ名 | `templates_v1.2.x-tecnos/` | `sdd-templates/`（固定） |
| テンプレート内 | 固定値 `v1.2.5-tecnos` | `{{TEMPLATE_VERSION}}` |
| 更新作業 | 20+ファイルを手動置換 | VERSION + CHANGELOG のみ |

---

## 公開URL

- **マニュアル**: https://sdd-templates-manual.pages.dev#/
- **IP制限**: Tecnos社内ネットワークからのみアクセス可能
