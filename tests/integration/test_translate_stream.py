import importlib
from typing import AsyncIterator

from starlette.testclient import TestClient  # type: ignore[import-not-found]


import pytest


@pytest.mark.integration
def test_translate_service_streams_translations_correctly(monkeypatch) -> None:
    # Arrange
    module = importlib.import_module("services.translate.main")

    async def fake_translate_stream(
        chunks: AsyncIterator,
        source_lang: str,
        target_langs: list[str],
    ) -> AsyncIterator:
        async for chunk in chunks:
            for lang in target_langs:
                yield module.TranslatedChunk(
                    text=chunk.text.upper(),
                    is_final=chunk.is_final,
                    timestamp_ms=chunk.timestamp_ms,
                    lang=lang,
                )

    monkeypatch.setattr(module, "translate_stream", fake_translate_stream)

    client = TestClient(module.app)

    # Act
    with client.websocket_connect("/stream") as ws:
        ws.send_json({"source_lang": "sv", "target_langs": ["en"]})
        accepted_langs_response = ws.receive_json()
        ws.send_json({"text": "hej", "is_final": False, "timestamp_ms": 1})
        ws.send_json({"text": "slut", "is_final": True, "timestamp_ms": 2})
        ws.send_json({"stop": True})
        first_translation = ws.receive_json()
        second_translation = ws.receive_json()

    # Assert
    assert accepted_langs_response == {"accepted_langs": ["en"]}
    assert first_translation == {
        "text": "HEJ",
        "is_final": False,
        "timestamp_ms": 1,
        "lang": "en",
    }
    assert second_translation == {
        "text": "SLUT",
        "is_final": True,
        "timestamp_ms": 2,
        "lang": "en",
    }
