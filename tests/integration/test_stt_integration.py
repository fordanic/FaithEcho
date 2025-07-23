import importlib
from typing import AsyncIterator, List

from starlette.testclient import TestClient  # type: ignore[import-not-found]


import pytest

@pytest.mark.integration
def test_stt_service_receives_audio_and_returns_transcripts(monkeypatch) -> None:
    # Arrange
    module = importlib.import_module("services.stt.main")

    received: List[bytes] = []

    async def fake_transcribe(chunks: AsyncIterator[bytes]):
        async for chunk in chunks:
            received.append(chunk)
        yield module.TextChunk(text="chunk1", is_final=False, timestamp_ms=1)
        yield module.TextChunk(text="chunk2", is_final=True, timestamp_ms=2)

    monkeypatch.setattr(module, "transcribe_stream", fake_transcribe)

    client = TestClient(module.app)
    test_audio = b"testaudio" * 10

    # Act
    with client.websocket_connect("/stream") as ws:
        for i in range(0, len(test_audio), 4):
            ws.send_bytes(test_audio[i : i + 4])
        ws.send_text("stop")
        first_response = ws.receive_json()
        second_response = ws.receive_json()

    # Assert
    assert first_response["text"] == "chunk1"
    assert second_response["text"] == "chunk2"
    assert b"".join(received) == test_audio
