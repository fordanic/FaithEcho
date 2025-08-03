import pytest

from src.faith_echo.segment_manager import SegmentManager
from src.faith_echo.sdk import SpeechChunk, TextChunk, TranslatedChunk


@pytest.mark.asyncio
async def test_segment_manager_tracks_status() -> None:
    """Segments record revisions for each stage."""
    # Arrange
    manager = SegmentManager(translate_langs=["en-US"])
    stt = TextChunk(text="hej", is_final=True, timestamp_ms=1, segment_id=1, revision=1)
    translation = TranslatedChunk(
        text="hi", is_final=True, timestamp_ms=2, segment_id=1, revision=1, lang="en-US"
    )
    speech = SpeechChunk(
        audio_b64="deadbeef", is_final=True, timestamp_ms=3, segment_id=1, revision=1
    )

    # Act
    await manager.put_stt_chunk(stt)
    await manager.put_translation_chunk(translation)
    manager.record_tts_chunk(speech, "en-US")

    # Assert
    status = manager.get_sync_status()
    seg = status[1]
    assert seg.stt.revision == 1
    assert seg.translations["en-US"].timestamp_ms == 2
    assert seg.tts["en-US"].revision == 1
