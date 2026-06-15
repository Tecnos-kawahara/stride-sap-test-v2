# =============================================================================
# OpenTelemetry Instrumentation for FastAPI
# Distributed tracing, metrics, and logging
# =============================================================================

"""
OpenTelemetry setup for FastAPI applications.

Usage:
    from observability import setup_telemetry

    app = FastAPI()
    setup_telemetry(app, service_name="web-edi")
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

@lru_cache
def get_otel_config() -> dict:
    """Get OpenTelemetry configuration from environment."""
    import os

    return {
        "service_name": os.getenv("OTEL_SERVICE_NAME", "app"),
        "service_version": os.getenv("OTEL_SERVICE_VERSION", "0.1.0"),
        "environment": os.getenv("APP_ENV", "development"),
        "otlp_endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        "otlp_insecure": os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true",
        "log_level": os.getenv("OTEL_LOG_LEVEL", "INFO"),
        "enabled": os.getenv("OTEL_ENABLED", "true").lower() == "true",
    }


# -----------------------------------------------------------------------------
# Tracer Setup
# -----------------------------------------------------------------------------

def setup_tracing(service_name: str, otlp_endpoint: str, insecure: bool = True):
    """
    Configure OpenTelemetry tracing with OTLP exporter.

    Args:
        service_name: Name of the service for trace identification
        otlp_endpoint: OTLP collector endpoint (e.g., http://localhost:4317)
        insecure: Whether to use insecure connection (no TLS)
    """
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    config = get_otel_config()

    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: config["service_version"],
        "deployment.environment": config["environment"],
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=insecure,
    )

    # Add batch processor for efficient export
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    return provider


# -----------------------------------------------------------------------------
# Metrics Setup
# -----------------------------------------------------------------------------

def setup_metrics(service_name: str, otlp_endpoint: str, insecure: bool = True):
    """
    Configure OpenTelemetry metrics with OTLP exporter.

    Args:
        service_name: Name of the service
        otlp_endpoint: OTLP collector endpoint
        insecure: Whether to use insecure connection
    """
    from opentelemetry import metrics
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME

    config = get_otel_config()

    resource = Resource.create({
        SERVICE_NAME: service_name,
        "deployment.environment": config["environment"],
    })

    # Configure metric exporter
    metric_exporter = OTLPMetricExporter(
        endpoint=otlp_endpoint,
        insecure=insecure,
    )

    # Create periodic reader (exports every 60 seconds by default)
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=60000,
    )

    # Create meter provider
    provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )

    # Set as global meter provider
    metrics.set_meter_provider(provider)

    return provider


# -----------------------------------------------------------------------------
# FastAPI Instrumentation
# -----------------------------------------------------------------------------

def instrument_fastapi(app: "FastAPI"):
    """
    Instrument FastAPI application with OpenTelemetry.

    Automatically traces:
    - HTTP requests/responses
    - Request headers (sanitized)
    - Response status codes
    - Exception handling
    """
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="health,healthz,ready,metrics",
    )


def instrument_sqlalchemy(engine):
    """
    Instrument SQLAlchemy engine with OpenTelemetry.

    Traces:
    - SQL queries
    - Connection pool usage
    - Transaction boundaries
    """
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    SQLAlchemyInstrumentor().instrument(
        engine=engine,
        enable_commenter=True,
    )


def instrument_httpx():
    """
    Instrument HTTPX client with OpenTelemetry.

    Traces outgoing HTTP requests with context propagation.
    """
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    HTTPXClientInstrumentor().instrument()


def instrument_redis(redis_client):
    """
    Instrument Redis client with OpenTelemetry.

    Traces Redis commands.
    """
    from opentelemetry.instrumentation.redis import RedisInstrumentor

    RedisInstrumentor().instrument()


# -----------------------------------------------------------------------------
# Logging Integration
# -----------------------------------------------------------------------------

def setup_logging_integration():
    """
    Integrate Python logging with OpenTelemetry.

    Automatically adds trace_id and span_id to log records.
    """
    from opentelemetry.instrumentation.logging import LoggingInstrumentor

    LoggingInstrumentor().instrument(
        set_logging_format=True,
        log_level=logging.INFO,
    )


# -----------------------------------------------------------------------------
# Custom Span Helpers
# -----------------------------------------------------------------------------

def get_tracer(name: str = __name__):
    """Get a tracer instance for manual instrumentation."""
    from opentelemetry import trace
    return trace.get_tracer(name)


def add_span_attributes(attributes: dict):
    """
    Add custom attributes to the current span.

    Example:
        add_span_attributes({
            "user.id": user_id,
            "order.id": order_id,
            "order.total": total_amount,
        })
    """
    from opentelemetry import trace

    span = trace.get_current_span()
    if span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def record_exception(exception: Exception, attributes: dict | None = None):
    """
    Record an exception in the current span.

    Example:
        try:
            process_order(order)
        except OrderError as e:
            record_exception(e, {"order.id": order.id})
            raise
    """
    from opentelemetry import trace

    span = trace.get_current_span()
    if span.is_recording():
        span.record_exception(exception)
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)


# -----------------------------------------------------------------------------
# Main Setup Function
# -----------------------------------------------------------------------------

def setup_telemetry(
    app: "FastAPI",
    service_name: str | None = None,
    enable_tracing: bool = True,
    enable_metrics: bool = True,
    enable_logging: bool = True,
    instrument_db: bool = True,
    db_engine = None,
):
    """
    Complete OpenTelemetry setup for FastAPI application.

    Args:
        app: FastAPI application instance
        service_name: Service name (defaults to OTEL_SERVICE_NAME env var)
        enable_tracing: Enable distributed tracing
        enable_metrics: Enable metrics collection
        enable_logging: Enable log correlation
        instrument_db: Instrument database (requires db_engine)
        db_engine: SQLAlchemy engine instance

    Example:
        from fastapi import FastAPI
        from observability import setup_telemetry
        from database import engine

        app = FastAPI()
        setup_telemetry(
            app,
            service_name="web-edi",
            instrument_db=True,
            db_engine=engine,
        )
    """
    config = get_otel_config()

    if not config["enabled"]:
        logging.info("OpenTelemetry is disabled")
        return

    service = service_name or config["service_name"]
    endpoint = config["otlp_endpoint"]
    insecure = config["otlp_insecure"]

    logging.info(f"Setting up OpenTelemetry for {service}")

    # Setup tracing
    if enable_tracing:
        setup_tracing(service, endpoint, insecure)
        instrument_fastapi(app)
        instrument_httpx()
        logging.info("Tracing enabled")

    # Setup metrics
    if enable_metrics:
        setup_metrics(service, endpoint, insecure)
        logging.info("Metrics enabled")

    # Setup logging integration
    if enable_logging:
        setup_logging_integration()
        logging.info("Logging integration enabled")

    # Instrument database
    if instrument_db and db_engine:
        instrument_sqlalchemy(db_engine)
        logging.info("Database instrumentation enabled")


# -----------------------------------------------------------------------------
# Shutdown Handler
# -----------------------------------------------------------------------------

def shutdown_telemetry():
    """
    Gracefully shutdown OpenTelemetry providers.

    Call this during application shutdown to flush pending data.
    """
    from opentelemetry import trace, metrics

    # Shutdown tracer provider
    tracer_provider = trace.get_tracer_provider()
    if hasattr(tracer_provider, "shutdown"):
        tracer_provider.shutdown()

    # Shutdown meter provider
    meter_provider = metrics.get_meter_provider()
    if hasattr(meter_provider, "shutdown"):
        meter_provider.shutdown()
