import base64

from src.faith_echo.sdk.jitter_buffer import SegmentJitterBuffer  # type: ignore[import-untyped]
from src.faith_echo.sdk.models import SpeechChunk  # type: ignore[import-untyped]


def make_chunk(seg: int, rev: int, final: bool = True) -> SpeechChunk:
    return SpeechChunk(
        audio_b64=base64.b64encode(f"{seg}-{rev}".encode()).decode(),
        is_final=final,
        timestamp_ms=seg * 100,
        segment_id=seg,
        revision=rev,
    )


def test_flushes_when_both_languages_final() -> None:
    # Arrange
    buf = SegmentJitterBuffer(["en", "fr"])

    # Act
    out1 = buf.process("en", make_chunk(1, 0))
    out2 = buf.process("fr", make_chunk(1, 0))

    # Assert
    assert out1 == []
    assert len(out2) == 1
    flushed = out2[0]
    assert flushed["en"].segment_id == flushed["fr"].segment_id == 1


def test_reissued_segments_replace_and_flush() -> None:
    # Arrange
    buf = SegmentJitterBuffer(["en", "fr"])

    # Act
    buf.process("en", make_chunk(1, 0, final=False))
    buf.process("fr", make_chunk(1, 0, final=False))
    buf.process("en", make_chunk(1, 1))
    out = buf.process("fr", make_chunk(1, 1))

    # Assert
    flushed = out[0]
    assert flushed["en"].revision == flushed["fr"].revision == 1
