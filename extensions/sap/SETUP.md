# SAP 開発環境 初回セットアップ手順

> **本ドキュメントは AI（Claude Code）が読んで自動実行するための手順書です。**
> 上から順番に各ステップを実行してください。

---

## 前提条件

| ツール | バージョン | 確認コマンド |
|--------|-----------|-------------|
| Node.js | 18 以上 | `node --version` |
| npm | 9 以上 | `npm --version` |
| Python | 3.8 以上 | `python3 --version` |
| Claude Code | 最新 | `claude --version` |
| STRIDE | v6.0.0 以上 | `sdd-templates/bin/stride --version` |

---

## ステップ 1: テンプレートルートの把握

テンプレートルートは、この `SETUP.md` が存在するディレクトリ（`extensions/sap/`）の **2階層上** のディレクトリである。
つまり `CLAUDE.md`、`sdd-templates/`、`extensions/` 等が存在するディレクトリがテンプレートルートとなる。
以降のステップは、すべてテンプレートルートを基準に実行する。

SDD 成果物は `specs/<feature>/` 配下に自動生成される。
ソースコードは `src/` に格納される。
いずれもテンプレートルート直下の固定パスであり、変更はできない
（`stride-lint` やテンプレート内のパス参照がこの構造を前提としているため）。

---

## ステップ 2: .env バリデーション

### 2-1. .env ファイルの存在確認

**テンプレートルート**に `.env` ファイルが存在するか確認する。
（`.env` はテンプレートルート直下に配置する。`extensions/sap/tools/*.js` は `.env` をテンプレートルートから読み取る。）

- **存在する場合** -> ステップ 2-2 へ
- **存在しない場合** -> 以下の内容で `.env` を新規作成する:
  ```
  # SAP接続情報（必須）
  SAP_URL=
  SAP_CLIENT=
  SAP_USERNAME=
  SAP_PASSWORD=

  # E2Eテスト専用クライアント（任意）
  SAP_TEST_CLIENT=
  ```

### 2-2. 必須キーのバリデーション

`.env` ファイルを読み取り、以下の必須キーに値が設定されているか確認する。

| キー | 必須 | 説明 | 例 |
|------|------|------|----|
| `SAP_URL` | 必須 | SAP システムの URL | `https://10.1.1.8:44300` |
| `SAP_CLIENT` | 必須 | SAP クライアント番号 | `240` |
| `SAP_USERNAME` | 必須 | SAP ログインユーザー名 | `DEVELOPER` |
| `SAP_PASSWORD` | 必須 | SAP ログインパスワード | `********` |
| `SAP_TEST_CLIENT` | 任意 | テスト用クライアント番号 | `241` |

### 2-3. 未設定キーへの対応

必須キーのうち値が空または未定義のものがある場合:

1. 未設定のキー名を一覧で**ユーザーに提示**する
2. 各キーの値を**ユーザーに入力を求める**
3. 入力された値を `.env` ファイルに書き込む
4. 再度バリデーションを実行し、全必須キーに値があることを確認する

> **注意:** `.env` は `.gitignore` に登録済みのため、Git にはコミットされません。
> `SAP_TEST_CLIENT` は任意項目のため、未設定でも警告のみ表示し処理を継続します。

---

## ステップ 3: 依存パッケージのインストール

**`extensions/sap/`**（`package.json` が存在するディレクトリ）で以下を実行する。

### 3-1. インストール実行

```bash
# package-lock.json がある場合（再現性重視）
npm ci

# package-lock.json がない場合
npm install
```

### 3-2. インストール結果の確認

以下を確認する:

1. `node_modules/` ディレクトリが作成されていること
2. `abap-adt-api` が存在すること: `node -e "require('abap-adt-api'); console.log('OK')"`
3. `dotenv` が存在すること: `node -e "require('dotenv'); console.log('OK')"`
4. `abaplint` が実行可能なこと: `npx abaplint --version`

> **注意:** `node_modules/` は `.gitignore` に登録済みです。

---

## ステップ 4: MCP サーバーの登録

SAP 開発では以下の MCP サーバーを使用する。

| MCP サーバー | 必須/任意 | 用途 | リポジトリ |
|-------------|-----------|------|-----------|
| `sap-adt` | **任意** | SAP 実機への ADT REST API アクセス（検索・読取・書込・有効化・テスト） | https://github.com/Tecnos-Japan-NGB/s4_environment/tree/main/mcp-server（非公開） |
| `abap-mcp-server` | **任意** | SAP Help Portal / SAP Community のドキュメント検索 | https://github.com/marianfoo/abap-mcp-server（公開） |
| `playwright` | 必須 | ブラウザ操作（Fiori テスト等） | npm パッケージ `@playwright/mcp@latest` |

> **`sap-adt` と `abap-mcp-server` はプロジェクトによって利用可否が異なるため任意です。**
> 導入に失敗した場合は、エラー内容をユーザーに報告し、スキップするか再試行するかの判断を仰いでください。
> スキップした場合でも、SAP ADT スクリプト（`extensions/sap/tools/*.js`）による直接接続は引き続き利用可能です。

### 4-1. 登録状態の確認と判定

```bash
claude mcp list
```

各サーバーについて、以下の判定を行う:

| 状態 | 判定 | アクション |
|------|------|-----------|
| 一覧に名前がない | 未登録 | 新規登録する（4-2 以降） |
| `Connected` + スコープが `Local config` | 正常 | スキップ |
| `Failed to connect` | 異常 | `claude mcp remove <name>` で削除してから再登録 |
| `Connected` だがスコープが `Project config` | 要再登録 | `claude mcp remove <name>` で削除してから再登録 |
| `Connected` だがスコープが `User config` | 要確認 | 別プロジェクトの接続先と競合する可能性あり。削除して再登録を推奨 |

> **重要: ローカルスコープ（デフォルト、フラグなし）で登録すること。**
>
> Claude Code の MCP 登録には3つのスコープがある:
>
> | スコープ | フラグ | 保存先 | 特徴 |
> |---------|--------|--------|------|
> | **local** | なし（デフォルト） | `.claude/settings.local.json` | プロジェクト個別・git非共有 |
> | project | `-s project` | `.mcp.json` | git共有（チーム向け） |
> | user | `-s user` | `~/.claude/settings.json` | 全プロジェクト共通 |
>
> **local を使う理由:**
> - プロジェクトごとに異なる SAP システム（開発機・検証機等）に接続できる
> - 認証情報がプロジェクト内に閉じ、他プロジェクトに影響しない
> - `.claude/` は `.gitignore` に含まれるため git にコミットされない
>
> **project スコープ（`.mcp.json`）を避ける理由:**
> MCP サーバーのリポジトリに同梱される `.mcp.json` は開発者向け設定であり、
> 相対パスやシェル変数参照を使用しているため、利用者環境では正しく動作しない。
>
> **user スコープを避ける理由:**
> 全プロジェクトで同一の接続先が使われるため、接続先が異なる複数プロジェクトを
> 並行して扱う場合に競合する。

スコープの確認方法:
```bash
claude mcp get <サーバー名>
```

### 4-2. sap-adt の登録（任意）

> **このサーバーはプロジェクトによって利用可否が異なります。**
> 導入に失敗した場合は、エラー内容をユーザーに報告し、スキップ/再試行の判断を仰いでください。

まず、ローカルにビルド済みのサーバーがあるか自動検索する:
- `**/s4_environment/mcp-server/dist/index.js`

**見つかった場合:** そのパスを使って登録する。
**ビルド前のリポジトリが見つかった場合:** `npm install && npm run build` を実行してからそのパスを使う。
**見つからない場合:** テンプレートルート直下の `.external/` にクローンしてビルドする:

```bash
mkdir -p <テンプレートルート>/.external
git clone https://github.com/Tecnos-Japan-NGB/s4_environment.git <テンプレートルート>/.external/s4_environment
cd <テンプレートルート>/.external/s4_environment/mcp-server
npm install
npm run build
```

> **注意:** 非公開リポジトリのため、GitHub 認証が必要です。認証エラーが出た場合はユーザーに確認する。
> `.external/` は `.gitignore` に追加すること。

**上記のいずれかのステップで失敗した場合:**
1. エラー内容をユーザーに提示する（例: 「sap-adt の導入に失敗しました: `git clone` で認証エラー」）
2. ユーザーに以下の選択肢を提示する:
   - **スキップ**: sap-adt なしで続行（SAP ADT スクリプトによる直接接続は利用可能）
   - **再試行**: 原因を解消してから再実行
3. ユーザーが「スキップ」を選択した場合 -> **4-3 へ進む**

**導入成功した場合:** `.env` から接続情報を読み取り、登録を実行する。

**環境変数マッピング（.env のキー名と MCP の環境変数名が異なるため注意）:**

| .env のキー | MCP の環境変数 |
|-------------|---------------|
| `SAP_URL` | `SAP_HOST` |
| `SAP_USERNAME` | `SAP_USER` |
| `SAP_CLIENT` | `SAP_CLIENT` |
| `SAP_PASSWORD` | `SAP_PASSWORD` |

```bash
claude mcp add sap-adt \
  --env SAP_HOST=<.envのSAP_URLの値> \
  --env SAP_CLIENT=<.envのSAP_CLIENTの値> \
  --env SAP_USER=<.envのSAP_USERNAMEの値> \
  --env SAP_PASSWORD=<.envのSAP_PASSWORDの値> \
  --env SAP_LANGUAGE=JA \
  --env NODE_TLS_REJECT_UNAUTHORIZED=0 \
  -- node <dist/index.jsの絶対パス>
```

> **絶対パスを使うこと。** 相対パスは Claude Code のプロジェクトルートに依存するため、
> 環境によって解決先が変わり接続に失敗する。
> スコープフラグは不要（デフォルトの local が使われる）。

### 4-3. abap-mcp-server の登録（任意）

> **このサーバーはプロジェクトによって利用可否が異なります。**
> 導入に失敗した場合は、エラー内容をユーザーに報告し、スキップ/再試行の判断を仰いでください。

ローカルにビルド済みのサーバーがあるか自動検索する:
- `**/abap-mcp-server/dist/src/server.js`

**見つからない場合:** テンプレートルート直下の `.external/` にクローンしてビルドする:

```bash
mkdir -p <テンプレートルート>/.external
git clone https://github.com/marianfoo/abap-mcp-server.git <テンプレートルート>/.external/abap-mcp-server
cd <テンプレートルート>/.external/abap-mcp-server
npm ci
npm run build
```

**上記のいずれかのステップで失敗した場合:**
1. エラー内容をユーザーに提示する（例: 「abap-mcp-server の導入に失敗しました: `npm run build` でエラー」）
2. ユーザーに以下の選択肢を提示する:
   - **スキップ**: abap-mcp-server なしで続行（SAP ドキュメント検索は手動で実施）
   - **再試行**: 原因を解消してから再実行
3. ユーザーが「スキップ」を選択した場合 -> **4-4 へ進む**

**導入成功した場合:** 登録を実行する:

```bash
claude mcp add abap-mcp-server \
  -- bash -c "cd <abap-mcp-serverの絶対パス> && node dist/src/server.js"
```

### 4-4. playwright の登録

```bash
claude mcp add playwright -- npx @playwright/mcp@latest
```

### 4-5. 登録完了後の接続確認

MCP サーバーの登録が完了したら、ユーザーに以下を案内する:

> MCP サーバーの登録が完了しました。**Claude Code を再起動してください。**
> 再起動後に MCP サーバーが利用可能になります。

再起動後、**必ず以下の接続確認を実施する**:

```bash
claude mcp list
```

**登録したサーバーが `Connected` であることを確認する。**
- 任意サーバー（`sap-adt`, `abap-mcp-server`）をスキップした場合、一覧に表示されないのは正常。
- 登録したサーバーで `Failed` がある場合は、エラーリカバリーセクションの「MCP 関連」を参照して対処する。

> **Step 5 の SAP 接続テスト（search.js）は Node.js スクリプトによる直接接続であり、
> MCP サーバー経由ではない。** そのため Step 5 が成功しても MCP が正常とは限らない。
> この Step 4-5 の確認を省略しないこと。

確認が完了したら、ステップ 5 へ進む。

---

## ステップ 5: SAP 接続テスト

**テンプレートルート**で SAP への接続が正常に動作するか確認する。

```bash
# テンプレートルートで実行（オブジェクト検索テスト、読み取り専用、安全）
node extensions/sap/tools/search.js object "ZCL_*" --type class
```

- **結果が返る** -> 接続成功。ステップ 6 へ。
- **エラーが出る** -> エラーリカバリーセクションを参照。

---

## ステップ 6: 完了報告

全ステップが正常に完了したら、以下をユーザーに報告する:

1. **環境変数:** `.env` の全必須キーが設定済み
2. **依存パッケージ:** `abap-adt-api`, `dotenv`, `@abaplint/cli` がインストール済み
3. **MCP サーバー:** 登録状況の一覧（各サーバーが「登録済み」「スキップ」のいずれか）
   - スキップしたサーバーがある場合: 「`sap-adt` はスキップされました。MCP 経由の SAP アクセスは利用できませんが、ADT スクリプト（`extensions/sap/tools/*.js`）による直接接続は利用可能です」等
4. **接続テスト:** search.js による SAP 接続確認結果
5. **次のステップ:** 「開発を始めるには、CLAUDE.md の手順に従って `stride intake <feature>` または `stride init <feature> --detect` を実行してください」

---

## エラーリカバリー

### .env 関連

| エラー | 対処 |
|--------|------|
| `.env` の読み取り権限がない | ファイルのパーミッションを確認 |
| ユーザーが値の入力を拒否 | 未設定キーを明示して中断。後で再実行可能 |

### npm 関連

| エラー | 対処 |
|--------|------|
| `npm ci` が失敗 | `node_modules` を削除し `npm install` にフォールバック |
| `npm install` が失敗 | ネットワーク接続・プロキシ設定を確認 |
| Node.js バージョン不足 | LTS 版（18 以上）へアップグレード |

### MCP 関連

| エラー | 対処 |
|--------|------|
| ローカルにビルド済みファイルが見つからない | 公開リポジトリからクローンしてビルドする |
| `git clone` が失敗 | ネットワーク接続を確認。非公開リポの場合は認証情報を確認 |
| MCP サーバーのビルド失敗 | `node_modules` を削除して `npm install` -> `npm run build` を再実行 |
| `claude mcp add` が失敗 | 既存登録を `claude mcp remove <name>` で削除してから再登録 |
| 登録済みだが `Failed` | `claude mcp remove <name>` -> **絶対パス**で再登録 -> Claude Code 再起動 |
| 登録済み・Connected だがツールが見えない | `claude mcp get <name>` でスコープを確認。`Project config` や `User config` の場合は `claude mcp remove <name>` -> フラグなし（local）で再登録 |
| `.mcp.json` が既に存在して競合 | リポジトリ同梱の `.mcp.json` は開発者向け設定。利用者はフラグなし（local スコープ）で別途登録すれば競合しない |
| 別プロジェクトの `sap-adt` が残っている（user スコープ） | `claude mcp remove sap-adt` で削除し、フラグなし（local）で再登録。user スコープは全プロジェクトに影響するため、接続先が異なる場合は必ず local に変更する |

### SAP 接続関連

| エラー | 対処 |
|--------|------|
| `ECONNREFUSED` / タイムアウト | SAP システムが起動しているか確認。VPN 接続が必要な場合あり |
| `401 Unauthorized` | `.env` の `SAP_USERNAME` / `SAP_PASSWORD` を確認 |
| `403 Forbidden` | ユーザーに ADT 権限（`S_ADT_RES`）が付与されているか SAP 管理者に確認 |
| 自己署名証明書エラー | スクリプトは `NODE_TLS_REJECT_UNAUTHORIZED=0` で対応済み。MCP 側は登録時の `--env` で設定済み |
