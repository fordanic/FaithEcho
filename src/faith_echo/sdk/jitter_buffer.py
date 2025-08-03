"""Per-language jitter buffer for aligning reissued segments."""

from __future__ import annotations

from typing import Dict, Iterable, List

from .models import SpeechChunk


class SegmentJitterBuffer:
    """Hold segments per language until all languages finalize a segment.

    Each language maintains its own buffer keyed by ``segment_id``. When a
    chunk arrives, the latest revision for that language and segment is stored.
    Once every language has a final revision for the same ``segment_id``, the
    segment is flushed and returned. Segments are flushed in ascending
    ``segment_id`` order to preserve playback alignment.
    """

    def __init__(self, languages: Iterable[str]) -> None:
        """Initialise buffers for ``languages``.

        Args:
            languages: Language codes that will supply segments.
        """

        self._buffers: Dict[str, Dict[int, SpeechChunk]] = {
            lang: {} for lang in languages
        }

    def process(self, lang: str, chunk: SpeechChunk) -> List[Dict[str, SpeechChunk]]:
        """Store ``chunk`` and return any segments ready to flush.

        Args:
            lang: Language code associated with ``chunk``.
            chunk: Incoming audio segment.

        Returns:
            List of flushed segments. Each item maps language codes to their
            final ``SpeechChunk`` for the flushed ``segment_id``.
        """

        if lang not in self._buffers:
            raise KeyError(f"Unknown language: {lang}")

        buf = self._buffers[lang]
        current = buf.get(chunk.segment_id)
        if not current or chunk.revision >= current.revision:
            buf[chunk.segment_id] = chunk

        flushed: List[Dict[str, SpeechChunk]] = []
        while True:
            common_ids = set.intersection(
                *(set(b.keys()) for b in self._buffers.values())
            )
            if not common_ids:
                break
            seg_id = min(common_ids)
            if all(
                self._buffers[lang_key][seg_id].is_final for lang_key in self._buffers
            ):
                flushed.append(
                    {
                        lang_key: self._buffers[lang_key].pop(seg_id)
                        for lang_key in self._buffers
                    }
                )
            else:
                break
        return flushed
