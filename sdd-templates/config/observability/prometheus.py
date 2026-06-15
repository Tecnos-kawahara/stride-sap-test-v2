# =============================================================================
# Prometheus Metrics for FastAPI
# Application Performance Monitoring (APM)
# =============================================================================

"""
Prometheus metrics integration for FastAPI applications.

Usage:
    from prometheus import setup_metrics, MetricsMiddleware

    app = FastAPI()
    setup_metrics(app)
"""

from __future__ import annotations

import time
from functools import wraps
from typing import TYPE_CHECKING, Callable

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

if TYPE_CHECKING:
    from fastapi import FastAPI, Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware

# -----------------------------------------------------------------------------
# Metric Definitions
# -----------------------------------------------------------------------------

# Application info
APP_INFO = Info(
    "app_info",
    "Application information",
)

# HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"],
)

# Database metrics
DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

DB_CONNECTIONS_ACTIVE = Gauge(
    "db_connections_active",
    "Active database connections",
)

DB_CONNECTIONS_POOL_SIZE = Gauge(
    "db_connections_pool_size",
    "Database connection pool size",
)

# Redis metrics
REDIS_OPERATIONS_TOTAL = Counter(
    "redis_operations_total",
    "Total Redis operations",
    ["operation", "status"],
)

REDIS_OPERATION_DURATION_SECONDS = Histogram(
    "redis_operation_duration_seconds",
    "Redis operation duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1),
)

# Business metrics
ORDERS_CREATED_TOTAL = Counter(
    "orders_created_total",
    "Total orders created",
    ["status"],
)

ORDERS_PROCESSING_DURATION_SECONDS = Histogram(
    "orders_processing_duration_seconds",
    "Order processing duration in seconds",
    ["order_type"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

ACTIVE_USERS = Gauge(
    "active_users",
    "Currently active users",
)

# Error metrics
ERRORS_TOTAL = Counter(
    "errors_total",
    "Total errors",
    ["error_type", "endpoint"],
)


# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------

class MetricsMiddleware:
    """Middleware for collecting HTTP metrics."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Skip metrics endpoint to avoid recursion
        path = scope.get("path", "")
        if path == "/metrics":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "UNKNOWN")
        endpoint = self._normalize_path(path)

        # Track in-progress requests
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

        start_time = time.perf_counter()
        status_code = 500  # Default to error

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - start_time

            # Record metrics
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code),
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

            HTTP_REQUESTS_IN_PROGRESS.labels(
                method=method,
                endpoint=endpoint,
            ).dec()

    def _normalize_path(self, path: str) -> str:
        """Normalize path to prevent high cardinality.

        Replaces dynamic segments like /orders/123 with /orders/{id}
        """
        import re

        # Replace UUIDs
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path,
            flags=re.IGNORECASE,
        )

        # Replace numeric IDs
        path = re.sub(r"/\d+", "/{id}", path)

        return path


# -----------------------------------------------------------------------------
# Decorators
# -----------------------------------------------------------------------------

def track_db_query(operation: str, table: str):
    """Decorator to track database query metrics.

    Example:
        @track_db_query("select", "orders")
        async def get_orders():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                DB_QUERY_DURATION_SECONDS.labels(
                    operation=operation,
                    table=table,
                ).observe(duration)
        return wrapper
    return decorator


def track_redis_operation(operation: str):
    """Decorator to track Redis operation metrics.

    Example:
        @track_redis_operation("get")
        async def get_cached_value(key):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.perf_counter() - start_time
                REDIS_OPERATIONS_TOTAL.labels(
                    operation=operation,
                    status=status,
                ).inc()
                REDIS_OPERATION_DURATION_SECONDS.labels(
                    operation=operation,
                ).observe(duration)
        return wrapper
    return decorator


def track_business_operation(metric_name: str, labels: dict | None = None):
    """Generic decorator for tracking business operations.

    Example:
        @track_business_operation("order_processing", {"order_type": "standard"})
        async def process_order(order):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                if metric_name == "order_processing":
                    order_type = (labels or {}).get("order_type", "unknown")
                    ORDERS_PROCESSING_DURATION_SECONDS.labels(
                        order_type=order_type,
                    ).observe(duration)
        return wrapper
    return decorator


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def record_order_created(status: str = "success"):
    """Record order creation metric."""
    ORDERS_CREATED_TOTAL.labels(status=status).inc()


def record_error(error_type: str, endpoint: str):
    """Record error metric."""
    ERRORS_TOTAL.labels(error_type=error_type, endpoint=endpoint).inc()


def set_active_users(count: int):
    """Set active users gauge."""
    ACTIVE_USERS.set(count)


def set_db_connection_stats(active: int, pool_size: int):
    """Set database connection statistics."""
    DB_CONNECTIONS_ACTIVE.set(active)
    DB_CONNECTIONS_POOL_SIZE.set(pool_size)


# -----------------------------------------------------------------------------
# Setup Functions
# -----------------------------------------------------------------------------

def setup_metrics(
    app: "FastAPI",
    app_name: str = "web-edi",
    app_version: str = "1.0.0",
    environment: str = "development",
):
    """
    Setup Prometheus metrics for FastAPI application.

    Args:
        app: FastAPI application instance
        app_name: Application name
        app_version: Application version
        environment: Deployment environment

    Example:
        from fastapi import FastAPI
        from prometheus import setup_metrics

        app = FastAPI()
        setup_metrics(app, app_name="web-edi", app_version="1.0.0")
    """
    from fastapi import Response

    # Set application info
    APP_INFO.info({
        "app_name": app_name,
        "version": app_version,
        "environment": environment,
    })

    # Add metrics middleware
    app.add_middleware(MetricsMiddleware)

    # Add metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )


# -----------------------------------------------------------------------------
# Database Connection Pool Monitoring
# -----------------------------------------------------------------------------

async def monitor_db_pool(engine):
    """
    Monitor database connection pool statistics.

    Call this periodically (e.g., every 30 seconds) to update pool metrics.

    Example:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            lambda: asyncio.create_task(monitor_db_pool(engine)),
            'interval',
            seconds=30,
        )
        scheduler.start()
    """
    pool = engine.pool
    if pool:
        set_db_connection_stats(
            active=pool.checkedout(),
            pool_size=pool.size(),
        )


# -----------------------------------------------------------------------------
# Grafana Dashboard JSON (for reference)
# -----------------------------------------------------------------------------

GRAFANA_DASHBOARD_JSON = """
{
  "title": "Web-EDI Application Dashboard",
  "panels": [
    {
      "title": "Request Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(http_requests_total[5m])",
          "legendFormat": "{{method}} {{endpoint}}"
        }
      ]
    },
    {
      "title": "Request Duration (p95)",
      "type": "graph",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
          "legendFormat": "{{method}} {{endpoint}}"
        }
      ]
    },
    {
      "title": "Error Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m])",
          "legendFormat": "5xx errors"
        }
      ]
    },
    {
      "title": "Database Query Duration",
      "type": "graph",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))",
          "legendFormat": "{{operation}} {{table}}"
        }
      ]
    },
    {
      "title": "Active Database Connections",
      "type": "gauge",
      "targets": [
        {
          "expr": "db_connections_active"
        }
      ]
    },
    {
      "title": "Orders Created",
      "type": "stat",
      "targets": [
        {
          "expr": "increase(orders_created_total[24h])",
          "legendFormat": "Last 24h"
        }
      ]
    }
  ]
}
"""
