"""Smoke tests for basic service endpoints."""

from starlette.testclient import TestClient  # type: ignore[import-not-found]


def test_service_health(client: TestClient) -> None:
    # Arrange & Act
    resp = client.get("/health")

    # Assert
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_service_ready(client: TestClient) -> None:
    # Arrange & Act
    resp = client.get("/ready")

    # Assert
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


def test_service_metrics(client: TestClient) -> None:
    # Arrange & Act
    resp = client.get("/metrics")

    # Assert
    assert resp.status_code == 200
    assert b"http_requests_total" in resp.content
