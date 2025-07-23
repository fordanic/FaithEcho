import importlib
from typing import AsyncIterator

from starlette.testclient import TestClient  # type: ignore[import-not-found]


import pytest

@pytest.mark.integration
def test_tts_service_streams_speech_correctly(monkeypatch) -> None:
    module = importlib.import_module("services.tts.main")

    async def fake_synthesize_stream(
        chunks: AsyncIterator,
        params,
    ) -> AsyncIterator:
        async for chunk in chunks:
            yield module.SpeechChunk(
                audio_b64="deadbeef",
                is_final=chunk.is_final,
                timestamp_ms=chunk.timestamp_ms,
            )

    monkeypatch.setattr(module, "synthesize_stream", fake_synthesize_stream)

    client = TestClient(module.app)
    with client.websocket_connect("/stream") as ws:
        ws.send_json({"lang": "en"})
        assert ws.receive_json() == {"accepted": True}
        ws.send_json({"text": "hello", "is_final": True, "timestamp_ms": 1})
        ws.send_json({"stop": True})
        assert ws.receive_json() == {
            "audio_b64": "deadbeef",
            "is_final": True,
            "timestamp_ms": 1,
        }
