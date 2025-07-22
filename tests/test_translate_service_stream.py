import importlib
from typing import AsyncIterator

from starlette.testclient import TestClient  # type: ignore[import-not-found]


def test_translate_service_stream(monkeypatch) -> None:
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
    with client.websocket_connect("/stream") as ws:
        ws.send_json({"source_lang": "sv", "target_langs": ["en"]})
        assert ws.receive_json() == {"accepted_langs": ["en"]}
        ws.send_json({"text": "hej", "is_final": False, "timestamp_ms": 1})
        ws.send_json({"text": "slut", "is_final": True, "timestamp_ms": 2})
        ws.send_json({"stop": True})
        assert ws.receive_json() == {
            "text": "HEJ",
            "is_final": False,
            "timestamp_ms": 1,
            "lang": "en",
        }
        assert ws.receive_json() == {
            "text": "SLUT",
            "is_final": True,
            "timestamp_ms": 2,
            "lang": "en",
        }
