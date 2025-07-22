import importlib
import asyncio
from typing import AsyncIterator, List

from fastapi import WebSocketDisconnect
import pytest
from starlette.testclient import TestClient
from typing import Any

from src.faith_echo.sdk import (  # type: ignore[import-untyped]
    STTClient,
    TranslateClient,
    TTSClient,
    TextChunk,
    VoiceParams,
)


class FakeWS:
    def __init__(self, session: Any) -> None:  # session is WebSocketTestSession
        self._session = session

    async def send(self, data) -> None:
        if isinstance(data, bytes):
            await asyncio.to_thread(self._session.send_bytes, data)  # type: ignore[attr-defined]
        else:
            await asyncio.to_thread(self._session.send_text, data)  # type: ignore[attr-defined]

    def __aiter__(self) -> "FakeWS":
        return self

    async def __anext__(self) -> str:
        try:
            msg = await asyncio.to_thread(self._session.receive_text)  # type: ignore[attr-defined]
        except WebSocketDisconnect as exc:  # connection closed
            raise StopAsyncIteration from exc
        return msg

    async def recv(self) -> str:
        return await self.__anext__()

    async def close(self) -> None:
        await asyncio.to_thread(self._session.close)  # type: ignore[attr-defined]


def make_connect(client: TestClient):
    def _connect(url: str, *args, **kwargs):
        path = url.split("testserver")[-1]
        ctx = client.websocket_connect(path)

        class _Ctx:
            async def __aenter__(self_inner):
                session = ctx.__enter__()
                self_inner._session = session
                return FakeWS(session)

            async def __aexit__(self_inner, exc_type, exc, tb):
                await asyncio.to_thread(ctx.__exit__, exc_type, exc, tb)

        return _Ctx()

    return _connect


@pytest.mark.asyncio
async def test_stt_client(monkeypatch) -> None:
    module = importlib.import_module("services.stt.main")

    async def fake_transcribe(_: AsyncIterator[bytes]):
        yield module.TextChunk(text="a", is_final=False, timestamp_ms=1)
        yield module.TextChunk(text="b", is_final=True, timestamp_ms=2)

    monkeypatch.setattr(module, "transcribe_stream", fake_transcribe)

    client = TestClient(module.app)
    monkeypatch.setattr(
        "src.faith_echo.sdk.stt_client.websockets.connect", make_connect(client)
    )

    stt = STTClient("ws://testserver")

    async def audio() -> AsyncIterator[bytes]:
        yield b"1"
        yield b"2"

    results = [chunk async for chunk in stt.stream(audio())]
    assert [r.text for r in results] == ["a", "b"]


@pytest.mark.asyncio
async def test_translate_client(monkeypatch) -> None:
    module = importlib.import_module("services.translate.main")

    async def fake_translate(
        chunks: AsyncIterator[TextChunk], source_lang: str, target_langs: List[str]
    ):
        async for chunk in chunks:
            for lang in target_langs:
                yield module.TranslatedChunk(
                    text=chunk.text.upper(),
                    is_final=chunk.is_final,
                    timestamp_ms=chunk.timestamp_ms,
                    lang=lang,
                )

    monkeypatch.setattr(module, "translate_stream", fake_translate)

    client = TestClient(module.app)
    monkeypatch.setattr(
        "src.faith_echo.sdk.translate_client.websockets.connect", make_connect(client)
    )

    tc = TranslateClient("ws://testserver")

    async def chunks() -> AsyncIterator[TextChunk]:
        yield TextChunk(text="hej", is_final=False, timestamp_ms=1)
        yield TextChunk(text="då", is_final=True, timestamp_ms=2)

    results = [r async for r in tc.stream(chunks(), "sv", ["en"])]
    assert [r.text for r in results] == ["HEJ", "DÅ"]


@pytest.mark.asyncio
async def test_tts_client(monkeypatch) -> None:
    module = importlib.import_module("services.tts.main")

    async def fake_tts(chunks: AsyncIterator[TextChunk], params: VoiceParams):
        async for chunk in chunks:
            yield module.SpeechChunk(
                audio_b64="deadbeef",
                is_final=chunk.is_final,
                timestamp_ms=chunk.timestamp_ms,
            )

    monkeypatch.setattr(module, "synthesize_stream", fake_tts)

    client = TestClient(module.app)
    monkeypatch.setattr(
        "src.faith_echo.sdk.tts_client.websockets.connect", make_connect(client)
    )

    tts = TTSClient("ws://testserver")

    async def chunks() -> AsyncIterator[TextChunk]:
        yield TextChunk(text="hi", is_final=True, timestamp_ms=1)

    results = [r async for r in tts.stream(chunks(), VoiceParams(lang="en"))]
    assert results[0].audio_b64 == "deadbeef"
