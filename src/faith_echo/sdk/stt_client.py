from __future__ import annotations

import asyncio
from typing import AsyncIterator

import websockets

from .models import TextChunk


class STTClient:
    """Async client for the STT microservice."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def stream(self, chunks: AsyncIterator[bytes]) -> AsyncIterator[TextChunk]:
        """Send audio chunks and yield transcript results."""

        uri = f"{self.base_url}/stream"

        async with websockets.connect(uri) as ws:

            async def sender() -> None:
                async for chunk in chunks:
                    await ws.send(chunk)
                await ws.send("stop")

            send_task = asyncio.create_task(sender())
            try:
                async for message in ws:
                    yield TextChunk.model_validate_json(message)
            finally:
                await send_task
