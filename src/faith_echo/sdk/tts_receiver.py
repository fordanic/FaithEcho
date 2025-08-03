"""Utilities for handling streamed TTS audio with revisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .models import SpeechChunk


@dataclass
class SegmentAudio:
    """Stored audio for a single segment revision."""

    chunk: SpeechChunk
    faded_out: bool = False


class TTSReceiver:
    """Manage incoming ``SpeechChunk`` items with revision tracking.

    Older revisions for the same ``segment_id`` are discarded. When a higher
    revision arrives, the previous audio is marked as ``faded_out`` so callers
    can gracefully stop playback if desired. Timestamps are retained to allow
    deterministic ordering when reconstructing the stream.
    """

    def __init__(self) -> None:
        self._segments: Dict[int, SegmentAudio] = {}

    def process(self, chunk: SpeechChunk) -> None:
        """Store ``chunk`` if it is the latest revision for its segment."""

        current = self._segments.get(chunk.segment_id)
        if current and chunk.revision <= current.chunk.revision:
            return  # Ignore stale revision
        if current:
            current.faded_out = True
        self._segments[chunk.segment_id] = SegmentAudio(chunk=chunk)

    def ordered_segments(self) -> List[SpeechChunk]:
        """Return stored segments sorted by ``timestamp_ms``."""

        return [
            s.chunk
            for s in sorted(self._segments.values(), key=lambda s: s.chunk.timestamp_ms)
        ]
