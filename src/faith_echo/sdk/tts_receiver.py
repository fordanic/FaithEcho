"""Utilities for handling streamed TTS audio with revisions."""

from __future__ import annotations

from typing import Dict, List

from .models import SpeechChunk


class TTSReceiver:
    """Manage incoming ``SpeechChunk`` items with revision tracking.

    Older revisions for the same ``segment_id`` are discarded. Timestamps are
    retained to allow deterministic ordering when reconstructing the stream.
    """

    def __init__(self) -> None:
        self._segments: Dict[int, SpeechChunk] = {}

    def process(self, chunk: SpeechChunk) -> None:
        """Store ``chunk`` if it is the latest revision for its segment."""

        current = self._segments.get(chunk.segment_id)
        if not current or chunk.revision > current.revision:
            self._segments[chunk.segment_id] = chunk

    def ordered_segments(self) -> List[SpeechChunk]:
        """Return stored segments sorted by ``timestamp_ms``."""

        return sorted(self._segments.values(), key=lambda c: c.timestamp_ms)
