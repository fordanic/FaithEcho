"""Shared data models for SDK clients."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class TextChunk(BaseModel):
    """Transcript chunk."""

    text: str
    is_final: bool
    timestamp_ms: int


class LangRequest(BaseModel):
    """Language selection request."""

    source_lang: str
    target_langs: List[str]


class LangResponse(BaseModel):
    """Confirmation of accepted languages."""

    accepted_langs: List[str]


class TranslatedChunk(TextChunk):
    """Translated text chunk with language code."""

    lang: str


class VoiceParams(BaseModel):
    """Voice parameters for synthesis."""

    lang: str
    voice: str | None = None
    speaking_rate: float | None = None


class SpeechChunk(BaseModel):
    """Encoded speech result."""

    audio_b64: str
    is_final: bool
    timestamp_ms: int
