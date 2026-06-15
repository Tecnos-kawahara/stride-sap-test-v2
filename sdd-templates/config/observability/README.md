# OpenTelemetry 計装ガイド

## 概要

分散トレーシング、メトリクス、ログ相関を提供するOpenTelemetry設定テンプレートです。

## クイックスタート

### 1. 依存関係をインストール

```bash
pip install \
  opentelemetry-api \
  opentelemetry-sdk \
  opentelemetry-exporter-otlp \
  opentelemetry-instrumentation-fastapi \
  opentelemetry-instrumentation-sqlalchemy \
  opentelemetry-instrumentation-httpx \
  opentelemetry-instrumentation-redis \
  opentelemetry-instrumentation-logging
```

### 2. 設定ファイルをコピー

```bash
cp sdd-templates/config/observability/opentelemetry.py src/observability.py
```

### 3. FastAPI に統合

```python
from fastapi import FastAPI
from observability import setup_telemetry, shutdown_telemetry
from database import engine

app = FastAPI()

@app.on_event("startup")
async def startup():
    setup_telemetry(
        app,
        service_name="web-edi",
        instrument_db=True,
        db_engine=engine,
    )

@app.on_event("shutdown")
async def shutdown():
    shutdown_telemetry()
```

### 4. 環境変数を設定

```bash
# .env
OTEL_ENABLED=true
OTEL_SERVICE_NAME=web-edi
OTEL_SERVICE_VERSION=1.0.0
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_LOG_LEVEL=INFO
```

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   FastAPI   │  │  SQLAlchemy │  │    HTTPX    │              │
│  │ Instrumented│  │ Instrumented│  │ Instrumented│              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│              ┌───────────▼───────────┐                          │
│              │   OpenTelemetry SDK   │                          │
│              │  - TracerProvider     │                          │
│              │  - MeterProvider      │                          │
│              │  - LoggingInstrumentor│                          │
│              └───────────┬───────────┘                          │
└──────────────────────────┼──────────────────────────────────────┘
                           │ OTLP (gRPC)
                           ▼
              ┌────────────────────────┐
              │   OpenTelemetry        │
              │   Collector            │
              │                        │
              │  - Receivers           │
              │  - Processors          │
              │  - Exporters           │
              └───────────┬────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  Jaeger  │   │Prometheus│   │   Loki   │
    │ (Traces) │   │ (Metrics)│   │  (Logs)  │
    └──────────┘   └──────────┘   └──────────┘
```

## 自動計装

以下が自動的にトレースされます：

### HTTP リクエスト
- リクエストパス、メソッド
- レスポンスステータスコード
- リクエスト/レスポンス時間
- 例外情報

### データベース
- SQL クエリ（パラメータ付き）
- 実行時間
- コネクションプール状態

### 外部 HTTP 呼び出し
- HTTPX クライアントリクエスト
- コンテキスト伝播（Trace Context）

## カスタム計装

### スパン属性の追加

```python
from observability import add_span_attributes

@app.post("/orders")
async def create_order(order: OrderCreate):
    # ビジネスコンテキストを追加
    add_span_attributes({
        "order.id": order.id,
        "order.total": order.total,
        "customer.id": order.customer_id,
    })
    ...
```

### 手動スパン作成

```python
from observability import get_tracer

tracer = get_tracer(__name__)

async def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)

        # 子スパン
        with tracer.start_as_current_span("validate_inventory"):
            await validate_inventory(order_id)

        with tracer.start_as_current_span("charge_payment"):
            await charge_payment(order_id)
```

### 例外の記録

```python
from observability import record_exception

try:
    await process_order(order)
except OrderError as e:
    record_exception(e, {"order.id": order.id})
    raise
```

## Docker Compose 設定

```yaml
# docker-compose.observability.yml
services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel/config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel/config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8889:8889"   # Prometheus metrics

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "14250:14250"  # gRPC

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

## OTel Collector 設定

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

  prometheus:
    endpoint: "0.0.0.0:8889"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

## ベストプラクティス

### 1. 除外パス

ヘルスチェックなどの高頻度エンドポイントは除外：

```python
FastAPIInstrumentor.instrument_app(
    app,
    excluded_urls="health,healthz,ready,metrics",
)
```

### 2. サンプリング

本番環境ではサンプリングを設定：

```bash
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1  # 10% サンプリング
```

### 3. 機密情報の除外

リクエストヘッダーから認証情報を除外：

```python
# カスタムスパンプロセッサで Authorization ヘッダーを削除
```

### 4. リソース属性

サービス識別に十分な情報を設定：

```bash
OTEL_RESOURCE_ATTRIBUTES=service.namespace=production,service.instance.id=pod-123
```

## トラブルシューティング

### トレースが表示されない

1. Collector エンドポイントを確認
2. ネットワーク接続を確認
3. `OTEL_ENABLED=true` を確認

### パフォーマンス影響

- BatchSpanProcessor を使用（デフォルト）
- サンプリングを適切に設定
- 除外パスを設定

## 関連ドキュメント

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger](https://www.jaegertracing.io/docs/)
- [Prometheus](https://prometheus.io/docs/)
