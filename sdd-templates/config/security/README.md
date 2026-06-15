# セキュリティ設定ガイド

## 概要

このディレクトリにはWebアプリケーションのセキュリティ設定テンプレートが含まれています。

## セキュリティヘッダー

### 使用方法

```python
from fastapi import FastAPI
from security_headers import add_security_headers, add_cors

app = FastAPI()

# セキュリティヘッダーを追加
add_security_headers(app)

# CORSを追加 (必要な場合)
add_cors(app, origins=["https://example.com"])
```

### 追加されるヘッダー

| ヘッダー | 値 | 目的 |
|---------|-----|------|
| `Content-Security-Policy` | 設定可能 | XSS/インジェクション防止 |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | HTTPS強制 |
| `X-Frame-Options` | `DENY` | クリックジャッキング防止 |
| `X-Content-Type-Options` | `nosniff` | MIMEスニッフィング防止 |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | リファラー漏洩防止 |
| `Permissions-Policy` | 各種機能無効化 | 不要な機能の制限 |
| `X-XSS-Protection` | `1; mode=block` | レガシーXSS防止 |

## Content-Security-Policy (CSP)

### デフォルト設定

```
default-src 'self';
script-src 'self' 'unsafe-inline' https://unpkg.com;
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self';
connect-src 'self';
frame-ancestors 'none';
form-action 'self';
base-uri 'self';
upgrade-insecure-requests
```

### カスタマイズ

```python
custom_csp = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.example.com; "
    "style-src 'self' https://fonts.googleapis.com; "
    "img-src 'self' https://images.example.com; "
)

add_security_headers(app, csp=custom_csp)
```

### CSP無効化（非推奨）

```python
add_security_headers(app, csp=None)
```

## CORS設定

### 開発環境

```python
add_cors(
    app,
    origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
)
```

### 本番環境

```python
add_cors(
    app,
    origins=["https://app.example.com"],
    allow_credentials=True,
)
```

### 環境変数から設定

```env
CORS_ORIGINS=https://app.example.com,https://admin.example.com
```

```python
add_cors(app)  # CORS_ORIGINS 環境変数を自動で読み込み
```

## セキュリティチェックリスト

### 必須

- [ ] セキュリティヘッダーミドルウェアを追加
- [ ] CORSオリジンを適切に制限
- [ ] HTTPS を本番環境で強制 (HSTS)
- [ ] CSP を設定 ('unsafe-inline' は可能な限り避ける)

### 推奨

- [ ] rate limiting を実装
- [ ] 認証エンドポイントにブルートフォース対策
- [ ] ログにセンシティブ情報を出力しない
- [ ] エラーメッセージにスタックトレースを含めない (本番)

## Nginx での設定

アプリケーション前段にNginxがある場合は、Nginx側でヘッダーを設定することも可能です：

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self';" always;

    location / {
        proxy_pass http://app:8000;
    }
}
```

## 関連ドキュメント

- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [MDN HTTP Headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers)
- [Content-Security-Policy Reference](https://content-security-policy.com/)
