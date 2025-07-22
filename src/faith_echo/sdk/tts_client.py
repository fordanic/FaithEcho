from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

import websockets

from .models import SpeechChunk, TextChunk, VoiceParams


class TTSClient:
    """Async client for the TTS microservice."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def stream(
        self, chunks: AsyncIterator[TextChunk], params: VoiceParams
    ) -> AsyncIterator[SpeechChunk]:
        """Synthesize text chunks into speech."""

        uri = f"{self.base_url}/stream"
        async with websockets.connect(uri) as ws:
            await ws.send(params.model_dump_json())
            ack_raw = await ws.recv()
            if not json.loads(ack_raw).get("accepted"):
                raise RuntimeError("TTS server did not accept voice parameters")

            async def sender() -> None:
                async for chunk in chunks:
                    await ws.send(chunk.model_dump_json())
                await ws.send(json.dumps({"stop": True}))

            send_task = asyncio.create_task(sender())
            try:
                async for message in ws:
                    yield SpeechChunk.model_validate_json(message)
            finally:
                await send_task
