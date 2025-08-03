from __future__ import annotations

import asyncio
import copy
from dataclasses import dataclass, field
from typing import Dict, Optional

from .sdk import SpeechChunk, TextChunk, TranslatedChunk


@dataclass
class StageState:
    """Revision and timing information for a pipeline stage."""

    revision: int = 0
    timestamp_ms: int = 0
    is_final: bool = False


@dataclass
class SegmentState:
    """State for a single segment across all stages."""

    stt: StageState = field(default_factory=StageState)
    translations: Dict[str, StageState] = field(default_factory=dict)
    tts: Dict[str, StageState] = field(default_factory=dict)


class SegmentManager:
    """Lightweight manager storing segment status and timestamps."""

    def __init__(self, translate_langs: Optional[list[str]] = None) -> None:
        self._segments: Dict[int, SegmentState] = {}
        self._stt_queue: asyncio.Queue[TextChunk | None] = asyncio.Queue()
        self._translate_queues: Dict[str, asyncio.Queue[TranslatedChunk | None]] = {
            lang: asyncio.Queue() for lang in (translate_langs or [])
        }

    def update_revision(
        self,
        stage: str,
        segment_id: int,
        revision: int,
        timestamp_ms: int,
        *,
        lang: str | None = None,
        is_final: bool = False,
    ) -> None:
        """Record the latest revision info for a stage."""

        seg = self._segments.setdefault(segment_id, SegmentState())
        if stage == "stt":
            seg.stt = StageState(revision, timestamp_ms, is_final)
        elif stage == "translate":
        elif stage == "translate":
            if lang is None:
                raise ValueError("'lang' is required for 'translate' stage")
            seg.translations[lang] = StageState(revision, timestamp_ms, is_final)
        elif stage == "tts":
            if lang is None:
                raise ValueError("'lang' is required for 'tts' stage")
            seg.tts[lang] = StageState(revision, timestamp_ms, is_final)
        else:  # pragma: no cover - defensive
            raise ValueError(f"Unknown stage {stage}")

    async def put_stt_chunk(self, chunk: TextChunk | None) -> None:
        """Queue an STT chunk for translation and update status."""

        await self._stt_queue.put(chunk)
        if chunk:
            self.update_revision(
                "stt",
                chunk.segment_id,
                chunk.revision,
                chunk.timestamp_ms,
                is_final=chunk.is_final,
            )

    async def get_stt_chunk(self) -> TextChunk | None:
        """Retrieve the next STT chunk for translation."""

        return await self._stt_queue.get()

    async def put_translation_chunk(self, chunk: TranslatedChunk | None) -> None:
        """Queue a translated chunk for TTS and update status."""

        if chunk is None:
            for q in self._translate_queues.values():
                await q.put(None)
            return

        queue = self._translate_queues.setdefault(chunk.lang, asyncio.Queue())
        await queue.put(chunk)
        self.update_revision(
            "translate",
            chunk.segment_id,
            chunk.revision,
            chunk.timestamp_ms,
            lang=chunk.lang,
            is_final=chunk.is_final,
        )

    async def get_translation_chunk(self, lang: str) -> TranslatedChunk | None:
        """Retrieve next translated chunk for a language."""

        queue = self._translate_queues.setdefault(lang, asyncio.Queue())
        return await queue.get()

    def record_tts_chunk(self, chunk: SpeechChunk, lang: str) -> None:
        """Update status for a TTS output chunk."""

        self.update_revision(
            "tts",
            chunk.segment_id,
            chunk.revision,
            chunk.timestamp_ms,
            lang=lang,
            is_final=chunk.is_final,
        )

    def get_sync_status(self) -> Dict[int, SegmentState]:
        """Return a snapshot of all segment states."""

        return copy.deepcopy(self._segments)
