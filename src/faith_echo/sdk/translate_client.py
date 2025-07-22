from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator, List

import websockets

from .models import LangRequest, LangResponse, TextChunk, TranslatedChunk


class TranslateClient:
    """Async client for the translation microservice."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def stream(
        self,
        chunks: AsyncIterator[TextChunk],
        source_lang: str,
        target_langs: List[str],
    ) -> AsyncIterator[TranslatedChunk]:
        """Translate text chunks and yield translated results."""

        uri = f"{self.base_url}/stream"
        async with websockets.connect(uri) as ws:
            req = LangRequest(source_lang=source_lang, target_langs=target_langs)
            await ws.send(req.model_dump_json())
            LangResponse.model_validate_json(
                await ws.recv()
            )  # LangResponse acknowledgement

            async def sender() -> None:
                async for chunk in chunks:
                    await ws.send(chunk.model_dump_json())
                await ws.send(json.dumps({"stop": True}))

            send_task = asyncio.create_task(sender())
            try:
                async for message in ws:
                    yield TranslatedChunk.model_validate_json(message)
            finally:
                send_task.cancel()
                try:
                    await send_task
                except asyncio.CancelledError:
                    pass  # Task cancellation is expected
