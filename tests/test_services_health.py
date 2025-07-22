from __future__ import annotations

import importlib

from starlette.testclient import TestClient  # type: ignore[import-not-found]
import pytest


@pytest.mark.parametrize("service", ["stt", "translate", "tts"])
def test_service_health(service: str) -> None:
    module = importlib.import_module(f"services.{service}.main")
    app = getattr(module, "app")
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
