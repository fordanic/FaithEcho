from __future__ import annotations

import asyncio
import base64
from typing import AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.cloud import texttospeech_v1 as tts
from pydantic import BaseModel

app = FastAPI(title="FaithEcho TTS Service")


class TextChunk(BaseModel):
    """Chunk of text to synthesise."""

    text: str
    is_final: bool
    timestamp_ms: int


class VoiceParams(BaseModel):
    """Voice configuration for synthesis."""

    lang: str
    voice: str | None = None
    speaking_rate: float | None = None


class SpeechChunk(BaseModel):
    """Encoded speech result."""

    audio_b64: str
    is_final: bool
    timestamp_ms: int


async def synthesize_stream(
    chunks: AsyncIterator[TextChunk], params: VoiceParams
) -> AsyncIterator[SpeechChunk]:
    """Send chunks to Google TTS and yield encoded audio."""

    client = tts.TextToSpeechClient()
    voice = tts.VoiceSelectionParams(
        language_code=params.lang,
        name=params.voice,
    )
    audio_config = tts.AudioConfig(
        audio_encoding=tts.AudioEncoding.MP3,
        speaking_rate=params.speaking_rate or 1.0,
    )
    loop = asyncio.get_running_loop()

    async for chunk in chunks:

        def do_request() -> bytes:
            response = client.synthesize_speech(
                input=tts.SynthesisInput(text=chunk.text),
                voice=voice,
                audio_config=audio_config,
            )
            return response.audio_content

        audio = await loop.run_in_executor(None, do_request)
        yield SpeechChunk(
            audio_b64=base64.b64encode(audio).decode(),
            is_final=chunk.is_final,
            timestamp_ms=chunk.timestamp_ms,
        )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/stream")
async def stream(websocket: WebSocket) -> None:
    """Accept text chunks and stream back synthesized audio."""

    await websocket.accept()

    first = await websocket.receive_json()
    params = VoiceParams(**first)
    await websocket.send_json({"accepted": True})

    chunk_q: asyncio.Queue[TextChunk | None] = asyncio.Queue()

    async def receiver() -> None:
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("stop"):
                    await chunk_q.put(None)
                    break
                chunk_q.put_nowait(TextChunk(**data))
        except WebSocketDisconnect:
            await chunk_q.put(None)

    async def chunk_iter() -> AsyncIterator[TextChunk]:
        while True:
            item = await chunk_q.get()
            if item is None:
                break
            yield item

    recv_task = asyncio.create_task(receiver())
    try:
        async for out in synthesize_stream(chunk_iter(), params):
            await websocket.send_json(out.model_dump())
    finally:
        await recv_task
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
