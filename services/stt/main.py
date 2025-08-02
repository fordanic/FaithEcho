from __future__ import annotations

import asyncio
import logging
import queue
import threading
from typing import AsyncIterator, Iterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.cloud import speech_v1 as speech
from google.cloud.speech_v1.types import (
    RecognitionConfig,
    StreamingRecognitionConfig,
    StreamingRecognizeRequest,
)
from pydantic import BaseModel

from services.utils import add_monitoring

app = FastAPI(title="FaithEcho STT Service")

# attach Prometheus metrics middleware and endpoint
add_monitoring(app)


class TextChunk(BaseModel):
    """Transcript chunk returned by the STT service."""

    text: str
    is_final: bool
    timestamp_ms: int


async def transcribe_stream(chunks: AsyncIterator[bytes]) -> AsyncIterator[TextChunk]:
    """Stream audio to Google Cloud STT and yield transcript chunks."""

    audio_q: queue.Queue[bytes | None] = queue.Queue()
    out_q: queue.Queue[TextChunk | None] = queue.Queue()

    def request_gen() -> Iterator[StreamingRecognizeRequest]:
        while True:
            data = audio_q.get()
            if data is None:
                break
            yield StreamingRecognizeRequest(audio_content=data)

    def run_recognize() -> None:
        try:
            client = speech.SpeechClient()
            config = StreamingRecognitionConfig(
                config=RecognitionConfig(
                    encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="sv-SE",
                ),
                interim_results=True,
            )
            try:
                for resp in client.streaming_recognize(  # type: ignore
                    config=config, requests=request_gen()
                ):
                    for result in resp.results:
                        out_q.put(
                            TextChunk(
                                text=result.alternatives[0].transcript,
                                is_final=result.is_final,
                                timestamp_ms=int(
                                    result.result_end_time.total_seconds() * 1000  # type: ignore
                                ),
                            )
                        )
            except Exception as e:
                # Handle stream timeout and other errors gracefully
                if "Audio Timeout Error" in str(e) or "OUT_OF_RANGE" in str(e):
                    # Normal stream end - client disconnected or finished
                    pass
                else:
                    # Log unexpected errors but don't crash
                    logging.exception("Error in speech recognition: %s", e)
        finally:
            out_q.put(None)

    thread = threading.Thread(target=run_recognize, daemon=True)
    thread.start()

    async def feed() -> None:
        async for c in chunks:
            audio_q.put(c)
        audio_q.put(None)

    feed_task = asyncio.create_task(feed())
    loop = asyncio.get_running_loop()
    try:
        while True:
            item = await loop.run_in_executor(None, out_q.get)
            if item is None:
                break
            yield item
    finally:
        await feed_task
        thread.join()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Readiness probe."""
    return {"status": "ready"}


@app.websocket("/stream")
async def stream(websocket: WebSocket) -> None:
    """Accept PCM audio and stream back STT transcripts."""

    await websocket.accept()

    audio_q: asyncio.Queue[bytes | None] = asyncio.Queue()

    async def ws_receiver() -> None:
        try:
            while True:
                message = await websocket.receive()
                if "bytes" in message:
                    await audio_q.put(message["bytes"])
                elif message.get("text") == "stop":
                    await audio_q.put(None)
                    break
        except WebSocketDisconnect:
            await audio_q.put(None)

    async def audio_iter() -> AsyncIterator[bytes]:
        while True:
            chunk = await audio_q.get()
            if chunk is None:
                break
            yield chunk

    recv_task = asyncio.create_task(ws_receiver())
    try:
        async for chunk in transcribe_stream(audio_iter()):
            await websocket.send_json(chunk.model_dump())
    finally:
        await recv_task
        await websocket.close()


if __name__ == "__main__":  # pragma: no cover - manual run helper
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
