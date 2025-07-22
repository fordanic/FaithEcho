from __future__ import annotations

import importlib

from starlette.testclient import TestClient  # type: ignore[import-not-found]
import pytest


@pytest.fixture(params=["stt", "translate", "tts"])
def client(request: pytest.FixtureRequest) -> TestClient:
    """Return a TestClient for the requested service."""
    module = importlib.import_module(f"services.{request.param}.main")
    app = getattr(module, "app")
    return TestClient(app)


def test_service_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_service_ready(client: TestClient) -> None:
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


def test_service_metrics(client: TestClient) -> None:
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert b"http_requests_total" in resp.content
