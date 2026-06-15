"""
Security Headers Middleware for FastAPI

Usage:
    from security_headers import add_security_headers
    app = FastAPI()
    add_security_headers(app)
"""

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティヘッダーを追加するミドルウェア"""

    def __init__(
        self,
        app,
        content_security_policy: str | None = None,
        hsts_max_age: int = 31536000,
        enable_hsts: bool = True,
        frame_options: str = "DENY",
        content_type_options: bool = True,
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str | None = None,
    ):
        super().__init__(app)
        self.csp = content_security_policy
        self.hsts_max_age = hsts_max_age
        self.enable_hsts = enable_hsts
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Content-Security-Policy
        if self.csp:
            response.headers["Content-Security-Policy"] = self.csp

        # Strict-Transport-Security (HTTPS only)
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains; preload"
            )

        # X-Frame-Options (クリックジャッキング防止)
        response.headers["X-Frame-Options"] = self.frame_options

        # X-Content-Type-Options (MIMEスニッフィング防止)
        if self.content_type_options:
            response.headers["X-Content-Type-Options"] = "nosniff"

        # Referrer-Policy
        response.headers["Referrer-Policy"] = self.referrer_policy

        # Permissions-Policy (旧 Feature-Policy)
        if self.permissions_policy:
            response.headers["Permissions-Policy"] = self.permissions_policy

        # X-XSS-Protection (レガシーブラウザ用)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response


# デフォルトCSPポリシー
DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://unpkg.com; "  # HTMX用
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "form-action 'self'; "
    "base-uri 'self'; "
    "upgrade-insecure-requests"
)

# デフォルトPermissions-Policy
DEFAULT_PERMISSIONS_POLICY = (
    "accelerometer=(), "
    "camera=(), "
    "geolocation=(), "
    "gyroscope=(), "
    "magnetometer=(), "
    "microphone=(), "
    "payment=(), "
    "usb=()"
)


def add_security_headers(
    app: FastAPI,
    csp: str | None = DEFAULT_CSP,
    hsts: bool = True,
    hsts_max_age: int = 31536000,
) -> None:
    """FastAPIアプリにセキュリティヘッダーミドルウェアを追加

    Args:
        app: FastAPIアプリケーション
        csp: Content-Security-Policyヘッダー値 (None で無効化)
        hsts: HSTSを有効化するか
        hsts_max_age: HSTS max-age (秒)
    """
    app.add_middleware(
        SecurityHeadersMiddleware,
        content_security_policy=csp,
        enable_hsts=hsts,
        hsts_max_age=hsts_max_age,
        permissions_policy=DEFAULT_PERMISSIONS_POLICY,
    )


# CORS設定 (別途追加)
def add_cors(
    app: FastAPI,
    origins: list[str] | None = None,
    allow_credentials: bool = True,
    allow_methods: list[str] | None = None,
    allow_headers: list[str] | None = None,
) -> None:
    """CORS設定を追加

    Args:
        app: FastAPIアプリケーション
        origins: 許可するオリジン (None で環境変数から取得)
        allow_credentials: 認証情報を許可するか
        allow_methods: 許可するHTTPメソッド
        allow_headers: 許可するヘッダー
    """
    from fastapi.middleware.cors import CORSMiddleware
    import os

    if origins is None:
        origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        origins = [o.strip() for o in origins_str.split(",")]

    if allow_methods is None:
        allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

    if allow_headers is None:
        allow_headers = [
            "Authorization",
            "Content-Type",
            "X-Correlation-ID",
            "X-Request-ID",
            "HX-Request",
            "HX-Target",
            "HX-Current-URL",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        expose_headers=["X-Correlation-ID", "HX-Trigger", "HX-Redirect"],
    )


# 使用例
if __name__ == "__main__":
    from fastapi import FastAPI

    app = FastAPI()

    # セキュリティヘッダーを追加
    add_security_headers(app)

    # CORSを追加
    add_cors(app, origins=["http://localhost:3000", "https://example.com"])

    @app.get("/")
    async def root():
        return {"message": "Secure API"}
