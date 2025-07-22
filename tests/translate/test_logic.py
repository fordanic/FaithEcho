from typing import AsyncIterator
from unittest.mock import MagicMock

import pytest

from services.translate import main


@pytest.mark.asyncio
async def test_translate_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_translate_text(**kwargs):
        return MagicMock(
            translations=[MagicMock(translated_text=kwargs["contents"][0].upper())]
        )

    monkeypatch.setattr(main.TRANSLATE_CLIENT, "translate_text", fake_translate_text)

    async def chunks() -> AsyncIterator[main.TextChunk]:
        yield main.TextChunk(text="hej", is_final=True, timestamp_ms=1)

    out = [c async for c in main.translate_stream(chunks(), "sv", ["en", "fr"])]
    assert [c.lang for c in out] == ["en", "fr"]
    assert all(c.text == "HEJ" for c in out)
