import base64

from faith_echo.sdk.models import SpeechChunk
from faith_echo.sdk.tts_receiver import TTSReceiver


def make_chunk(seg: int, rev: int, ts: int) -> SpeechChunk:
    return SpeechChunk(
        audio_b64=base64.b64encode(f"{seg}-{rev}".encode()).decode(),
        is_final=True,
        timestamp_ms=ts,
        segment_id=seg,
        revision=rev,
    )


def test_new_revision_overwrites_previous() -> None:
    recv = TTSReceiver()
    recv.process(make_chunk(1, 0, 100))
    recv.process(make_chunk(1, 1, 100))

    ordered = recv.ordered_segments()
    assert len(ordered) == 1
    assert ordered[0].revision == 1


def test_segments_returned_in_timestamp_order() -> None:
    recv = TTSReceiver()
    recv.process(make_chunk(2, 0, 200))
    recv.process(make_chunk(1, 0, 100))

    ordered = recv.ordered_segments()
    assert [c.segment_id for c in ordered] == [1, 2]
