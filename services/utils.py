"""Shared utilities for language services."""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    Counter,
    generate_latest,
)


def add_monitoring(app: FastAPI) -> None:
    """Attach Prometheus metrics to ``app``."""
    registry = CollectorRegistry()
    request_count = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint"],
        registry=registry,
    )

    @app.middleware("http")
    async def _count_requests(request: Request, call_next):
        response = await call_next(request)
        request_count.labels(request.method, request.url.path).inc()
        return response

    @app.get("/metrics")
    async def metrics() -> Response:
        """Expose Prometheus metrics."""
        data = generate_latest(registry)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    app.state.registry = registry
