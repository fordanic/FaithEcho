"""Shared test fixtures."""

from __future__ import annotations

import importlib
from collections.abc import Generator

import pytest
from starlette.testclient import TestClient  # type: ignore[import-not-found]

# Configure pytest-asyncio to use asyncio as the default event loop
pytest.register_assert_rewrite("pytest_asyncio")


@pytest.fixture(params=["stt", "translate", "tts"])
def client(request: pytest.FixtureRequest) -> Generator[TestClient, None, None]:
    """Return a TestClient for the requested service."""
    module = importlib.import_module(f"services.{request.param}.main")
    app = getattr(module, "app")
    with TestClient(app) as test_client:
        yield test_client
