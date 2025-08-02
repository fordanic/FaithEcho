from typing import AsyncIterator
from unittest.mock import MagicMock

import pytest

from services.stt import main


@pytest.mark.asyncio
async def test_transcribe_stream_returns_correct_transcripts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    mock_result = MagicMock()
    mock_result.alternatives = [MagicMock(transcript="foo")]
    mock_result.is_final = True
    mock_result.result_end_time.total_seconds.return_value = 0.1

    mock_resp = MagicMock()
    mock_resp.results = [mock_result]

    mock_client = MagicMock()
    mock_client.streaming_recognize.return_value = [mock_resp, mock_resp]
    monkeypatch.setattr(main.speech, "SpeechClient", lambda: mock_client)

    async def audio_chunks() -> AsyncIterator[bytes]:
        yield b"a"
        yield b"b"

    # Act
    out = [c async for c in main.transcribe_stream(audio_chunks())]

    # Assert
    assert [c.text for c in out] == ["foo", "foo"]
