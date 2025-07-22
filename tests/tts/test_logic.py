import base64
from typing import AsyncIterator
from unittest.mock import MagicMock

import pytest

from services.tts import main


@pytest.mark.asyncio
async def test_synthesize_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main.TTS_CLIENT,
        "synthesize_speech",
        lambda **_: MagicMock(audio_content=b"aud"),
    )

    async def chunks() -> AsyncIterator[main.TextChunk]:
        yield main.TextChunk(text="hi", is_final=True, timestamp_ms=1)

    params = main.VoiceParams(lang="en")
    out = [c async for c in main.synthesize_stream(chunks(), params)]
    expected = base64.b64encode(b"aud").decode()
    assert out[0].audio_b64 == expected
