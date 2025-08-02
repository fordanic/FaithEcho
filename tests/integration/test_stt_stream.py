import importlib
from typing import AsyncIterator

from starlette.testclient import TestClient  # type: ignore[import-not-found]


import pytest


@pytest.mark.integration
def test_stt_service_streams_transcripts_correctly(monkeypatch) -> None:
    # Arrange
    module = importlib.import_module("services.stt.main")

    async def fake_transcribe(_: AsyncIterator[bytes]):
        yield module.TextChunk(text="hello", is_final=False, timestamp_ms=1)
        yield module.TextChunk(text="hello world", is_final=True, timestamp_ms=2)

    monkeypatch.setattr(module, "transcribe_stream", fake_transcribe)

    app = module.app
    client = TestClient(app)

    # Act
    with client.websocket_connect("/stream") as ws:
        ws.send_bytes(b"\x00\x00")
        ws.send_text("stop")
        data = ws.receive_json()
        final = ws.receive_json()

    # Assert
    assert data == {"text": "hello", "is_final": False, "timestamp_ms": 1}
    assert final == {
        "text": "hello world",
        "is_final": True,
        "timestamp_ms": 2,
    }
