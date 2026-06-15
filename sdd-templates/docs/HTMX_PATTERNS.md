# HTMX レスポンスパターン

## 1. 概要

HTMX を使用する場合、同じエンドポイントが JSON と HTML の両方を返す必要があることがあります。
このドキュメントでは、コンテンツネゴシエーションとレスポンス形式の管理方法を説明します。

---

## 2. 問題: JSON vs HTML

### 2.1 問題の発生パターン

```html
<!-- ダッシュボードでHTMXを使用 -->
<div hx-get="/api/v1/orders" hx-trigger="load" hx-swap="innerHTML">
    読み込み中...
</div>
```

```python
# APIエンドポイント（JSONを返す）
@router.get("/orders")
async def list_orders() -> list[OrderResponse]:
    return [...]  # JSON: [{"id": "...", "order_number": "..."}]
```

**結果**: ダッシュボードに生のJSONが表示される

```
[{"id":"abc123","order_number":"ORD-001","status":"pending"...}]
```

### 2.2 解決策

1. **HTML専用エンドポイントを分離** (推奨)
2. Accept ヘッダーでコンテンツネゴシエーション
3. クエリパラメータで形式を指定

---

## 3. パターン1: エンドポイント分離 (推奨)

### 3.1 構造

```
/api/v1/orders      → JSON API (クライアント・他サービス用)
/partials/orders    → HTML パーシャル (HTMX用)
```

### 3.2 実装

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

# JSON API
api_router = APIRouter(prefix="/api/v1")

@api_router.get("/orders", response_model=list[OrderResponse])
async def list_orders_api() -> list[OrderResponse]:
    orders = await order_repo.list_all()
    return [OrderResponse.from_domain(o) for o in orders]

# HTML パーシャル
html_router = APIRouter()

@html_router.get("/partials/orders", response_class=HTMLResponse)
async def list_orders_html(request: Request):
    orders = await order_repo.list_all()
    return templates.TemplateResponse(
        "partials/orders_list.html",
        {"request": request, "orders": orders}
    )
```

### 3.3 テンプレート

```html
<!-- templates/partials/orders_list.html -->
{% if orders %}
<table class="table">
    <thead>
        <tr>
            <th>注文番号</th>
            <th>ステータス</th>
            <th>操作</th>
        </tr>
    </thead>
    <tbody>
        {% for order in orders %}
        <tr>
            <td>{{ order.order_number }}</td>
            <td>
                <span class="badge badge-{{ order.status.value }}">
                    {{ order.status.value }}
                </span>
            </td>
            <td>
                <button hx-get="/partials/orders/{{ order.id }}"
                        hx-target="#order-detail"
                        class="btn btn-sm">
                    詳細
                </button>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<p class="text-muted">注文がありません</p>
{% endif %}
```

### 3.4 ダッシュボードでの使用

```html
<!-- dashboard.html -->
<div id="orders-container"
     hx-get="/partials/orders"
     hx-trigger="load"
     hx-swap="innerHTML">
    <div class="spinner">読み込み中...</div>
</div>
```

---

## 4. パターン2: コンテンツネゴシエーション

### 4.1 Accept ヘッダーによる判定

```python
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

@router.get("/orders")
async def list_orders(request: Request):
    orders = await order_repo.list_all()

    accept = request.headers.get("Accept", "")

    if "text/html" in accept:
        # HTMX リクエスト → HTML
        return templates.TemplateResponse(
            "partials/orders_list.html",
            {"request": request, "orders": orders}
        )
    else:
        # API リクエスト → JSON
        return [OrderResponse.from_domain(o) for o in orders]
```

### 4.2 HX-Request ヘッダーによる判定

```python
def is_htmx_request(request: Request) -> bool:
    """HTMXリクエストかどうかを判定"""
    return request.headers.get("HX-Request") == "true"

@router.get("/orders")
async def list_orders(request: Request):
    orders = await order_repo.list_all()

    if is_htmx_request(request):
        return templates.TemplateResponse(
            "partials/orders_list.html",
            {"request": request, "orders": orders}
        )
    else:
        return [OrderResponse.from_domain(o) for o in orders]
```

---

## 5. HTMX 特有のヘッダー

### 5.1 リクエストヘッダー (HTMX → サーバー)

| ヘッダー | 説明 | 例 |
|---------|------|-----|
| `HX-Request` | HTMXリクエストの識別 | `true` |
| `HX-Target` | ターゲット要素のID | `#orders-container` |
| `HX-Trigger` | トリガー要素のID | `#load-btn` |
| `HX-Current-URL` | 現在のページURL | `/dashboard` |
| `HX-Prompt` | hx-prompt の入力値 | `user input` |

### 5.2 レスポンスヘッダー (サーバー → HTMX)

| ヘッダー | 説明 | 例 |
|---------|------|-----|
| `HX-Redirect` | リダイレクト先 | `/login` |
| `HX-Refresh` | ページ全体をリフレッシュ | `true` |
| `HX-Trigger` | イベントをトリガー | `orderCreated` |
| `HX-Trigger-After-Swap` | swap後にトリガー | `showNotification` |
| `HX-Retarget` | ターゲットを変更 | `#error-container` |
| `HX-Reswap` | swap方法を変更 | `innerHTML` |

### 5.3 レスポンスヘッダーの使用例

```python
from fastapi.responses import HTMLResponse

@router.post("/orders")
async def create_order(request: Request, data: CreateOrderRequest):
    order = await order_service.create(data)

    if is_htmx_request(request):
        html = templates.TemplateResponse(
            "partials/order_row.html",
            {"request": request, "order": order}
        )
        # イベントをトリガーして通知を表示
        html.headers["HX-Trigger"] = "orderCreated"
        return html

    return OrderResponse.from_domain(order)
```

```html
<!-- クライアント側でイベントをリッスン -->
<body hx-on:orderCreated="showNotification('注文が作成されました')">
```

---

## 6. エラーハンドリング

### 6.1 HTMX用エラーレスポンス

```python
from fastapi import HTTPException
from fastapi.responses import HTMLResponse

@router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if is_htmx_request(request):
        return HTMLResponse(
            content=f'''
            <div class="alert alert-error" role="alert">
                <strong>エラー:</strong> {exc.detail}
            </div>
            ''',
            status_code=exc.status_code,
            headers={"HX-Retarget": "#error-container"}
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
```

### 6.2 バリデーションエラー

```python
@router.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if is_htmx_request(request):
        errors = exc.errors()
        error_html = "<ul class='error-list'>"
        for error in errors:
            field = ".".join(str(x) for x in error["loc"])
            error_html += f"<li>{field}: {error['msg']}</li>"
        error_html += "</ul>"

        return HTMLResponse(
            content=f'<div class="alert alert-error">{error_html}</div>',
            status_code=422,
            headers={"HX-Retarget": "#form-errors"}
        )

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
```

---

## 7. フォーム送信パターン

### 7.1 JSON送信 (fetch使用)

```html
<form id="order-form">
    <input type="text" name="item_code" required>
    <input type="number" name="quantity" required>
    <button type="submit">送信</button>
</form>

<script>
document.getElementById('order-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);

    const response = await fetch('/api/v1/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (response.ok) {
        htmx.trigger('#orders-container', 'refresh');
    }
});
</script>
```

### 7.2 HTMX直接送信 (hx-vals使用)

```html
<form hx-post="/api/v1/orders"
      hx-ext="json-enc"
      hx-target="#result">
    <input type="text" name="item_code" required>
    <input type="number" name="quantity" required>
    <button type="submit">送信</button>
</form>

<!-- json-enc 拡張が必要 -->
<script src="https://unpkg.com/htmx.org/dist/ext/json-enc.js"></script>
```

---

## 8. ディレクトリ構成

```
templates/
├── base.html              # 基本レイアウト
├── dashboard.html         # フルページ
├── login.html
└── partials/              # HTMX用パーシャル
    ├── orders_list.html   # 注文一覧
    ├── order_row.html     # 注文行（追加用）
    ├── order_detail.html  # 注文詳細
    └── error.html         # エラー表示
```

---

## 9. チェックリスト

- [ ] JSON API と HTML パーシャルを分離
- [ ] `/partials/` プレフィックスでHTMX用エンドポイントを識別可能に
- [ ] `is_htmx_request()` ヘルパーを使用
- [ ] エラーハンドリングでHTMXレスポンスを考慮
- [ ] `HX-Trigger` でクライアント側イベントを活用
- [ ] フォーム送信は JSON または `json-enc` 拡張を使用
