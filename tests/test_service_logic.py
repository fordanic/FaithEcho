import importlib
import base64
from typing import AsyncIterator

import pytest


@pytest.mark.asyncio
async def test_transcribe_stream(monkeypatch) -> None:
    module = importlib.import_module("services.stt.main")  # type: ignore

    class FakeSpeechClient:
        def streaming_recognize(self, request_iter):
            # skip config
            next(request_iter)
            for req in request_iter:
                assert hasattr(req, "audio_content")
                result = type(
                    "Resp",
                    (),
                    {
                        "results": [
                            type(
                                "Result",
                                (),
                                {
                                    "alternatives": [
                                        type(
                                            "Alt", (), {"transcript": b"foo".decode()}
                                        )()
                                    ],
                                    "is_final": True,
                                    "result_end_time": type(
                                        "Dur", (), {"total_seconds": lambda self: 0.1}
                                    )(),
                                },
                            )()
                        ]
                    },
                )
                yield result

    monkeypatch.setattr(module.speech, "SpeechClient", lambda: FakeSpeechClient())

    async def chunks() -> AsyncIterator[bytes]:
        yield b"a"
        yield b"b"

    out = [chunk async for chunk in module.transcribe_stream(chunks())]
    assert [c.text for c in out] == ["foo", "foo"]


@pytest.mark.asyncio
async def test_translate_stream(monkeypatch) -> None:
    module = importlib.import_module("services.translate.main")  # type: ignore

    def fake_translate_text(**kwargs):
        return type(
            "Resp",
            (),
            {
                "translations": [
                    type("Tr", (), {"translated_text": kwargs["contents"][0].upper()})()
                ]
            },
        )

    monkeypatch.setattr(module.TRANSLATE_CLIENT, "translate_text", fake_translate_text)

    async def chunks() -> AsyncIterator[module.TextChunk]:  # type: ignore[name-defined]
        yield module.TextChunk(text="hej", is_final=True, timestamp_ms=1)

    out = [c async for c in module.translate_stream(chunks(), "sv", ["en", "fr"])]
    assert [c.lang for c in out] == ["en", "fr"]
    assert all(c.text == "HEJ" for c in out)


@pytest.mark.asyncio
async def test_synthesize_stream(monkeypatch) -> None:
    module = importlib.import_module("services.tts.main")  # type: ignore

    def fake_synthesize_speech(**kwargs):
        return type("Resp", (), {"audio_content": b"aud"})()

    monkeypatch.setattr(module.TTS_CLIENT, "synthesize_speech", fake_synthesize_speech)

    async def chunks() -> AsyncIterator[module.TextChunk]:  # type: ignore[name-defined]
        yield module.TextChunk(text="hi", is_final=True, timestamp_ms=1)

    params = module.VoiceParams(lang="en")
    out = [c async for c in module.synthesize_stream(chunks(), params)]
    expected = base64.b64encode(b"aud").decode()
    assert out[0].audio_b64 == expected
