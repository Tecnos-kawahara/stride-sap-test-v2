# Docker 設定ガイド

## 概要

このディレクトリにはアプリケーションのコンテナ化に必要なファイルが含まれています。

## ファイル構成

| ファイル | 説明 |
|---------|------|
| `Dockerfile.python` | Python/FastAPI アプリ用 |
| `Dockerfile.node` | Node.js/TypeScript アプリ用 |
| `docker-compose.yml` | マルチサービス構成 |
| `.dockerignore` | ビルド除外ファイル |

## クイックスタート

### 1. 設定ファイルをコピー

```bash
cp sdd-templates/config/docker/Dockerfile.python ./Dockerfile
cp sdd-templates/config/docker/docker-compose.yml ./docker-compose.yml
cp sdd-templates/config/docker/.dockerignore ./.dockerignore
```

### 2. 環境変数を設定

```bash
cp .env.example .env
# SECRET_KEY, DB_PASSWORD を必ず設定
```

### 3. 開発環境で起動

```bash
# ビルドして起動
docker-compose up --build

# バックグラウンドで起動
docker-compose up -d

# ログを確認
docker-compose logs -f app
```

### 4. 本番環境で起動

```bash
# 本番プロファイル (nginx含む)
docker-compose --profile production up -d
```

## Dockerfile ベストプラクティス

### マルチステージビルド

```dockerfile
# Stage 1: 依存関係のインストール
FROM python:3.12-slim as builder
...

# Stage 2: 本番イメージ (最小限)
FROM python:3.12-slim as production
COPY --from=builder ...
```

**メリット**:
- イメージサイズ削減
- ビルドツールが本番に含まれない
- セキュリティ向上

### 非rootユーザー

```dockerfile
# ユーザー作成
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# 所有権変更
COPY --chown=appuser:appgroup src/ ./src/

# ユーザー切り替え
USER appuser
```

**重要**: 本番環境では必ず非rootユーザーで実行

### ヘルスチェック

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

**パラメータ**:
- `interval`: チェック間隔
- `timeout`: タイムアウト
- `start-period`: 起動猶予時間
- `retries`: 失敗許容回数

## docker-compose サービス構成

```
┌─────────────────────────────────────────────────┐
│                    nginx:80/443                 │
│                  (reverse proxy)                │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│                   app:8000                      │
│                  (FastAPI)                      │
└──────┬──────────────────────────────┬───────────┘
       │                              │
┌──────▼──────┐              ┌────────▼────────┐
│   db:5432   │              │   redis:6379    │
│ (PostgreSQL)│              │    (Cache)      │
└─────────────┘              └─────────────────┘
```

## 環境変数

### 必須

| 変数 | 説明 | 例 |
|-----|------|-----|
| `SECRET_KEY` | JWT署名キー | `your-secret-key` |
| `DB_PASSWORD` | DBパスワード | `secure-password` |

### オプション

| 変数 | デフォルト | 説明 |
|-----|-----------|------|
| `APP_ENV` | `production` | 環境名 |
| `APP_PORT` | `8000` | アプリポート |
| `BUILD_TARGET` | `production` | ビルドターゲット |

## コマンドリファレンス

```bash
# ビルド
docker-compose build
docker-compose build --no-cache  # キャッシュなし

# 起動
docker-compose up -d
docker-compose up -d --scale app=3  # スケール

# 停止
docker-compose down
docker-compose down -v  # ボリューム削除

# ログ
docker-compose logs -f app
docker-compose logs --tail=100 app

# シェル接続
docker-compose exec app /bin/bash
docker-compose exec db psql -U webedi

# 状態確認
docker-compose ps
docker-compose top
```

## トラブルシューティング

### ヘルスチェック失敗

```bash
# コンテナ状態確認
docker inspect web-edi-app --format='{{.State.Health}}'

# ヘルスチェックログ
docker inspect web-edi-app --format='{{range .State.Health.Log}}{{.Output}}{{end}}'
```

### 依存サービス起動待ち

```yaml
depends_on:
  db:
    condition: service_healthy  # healthy になるまで待機
```

### ボリュームの権限問題

```bash
# ボリューム所有者を確認
docker-compose exec app ls -la /app/data

# 権限修正 (Dockerfile 内で)
RUN chown -R appuser:appgroup /app/data
```

## セキュリティチェックリスト

- [ ] 非rootユーザーで実行
- [ ] ヘルスチェックを設定
- [ ] 最小限のベースイメージ (slim/alpine)
- [ ] シークレットを環境変数で注入
- [ ] `.dockerignore` で不要ファイルを除外
- [ ] イメージスキャン (Trivy, Snyk) を CI に追加
