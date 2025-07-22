from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.cloud import translate_v3 as translate
from google.cloud.translate_v3.types import TranslateTextGlossaryConfig
from pydantic import BaseModel

app = FastAPI(title="FaithEcho TRANSLATE Service")


class TextChunk(BaseModel):
    """Transcript chunk used by the translation service."""

    text: str
    is_final: bool
    timestamp_ms: int


class LangRequest(BaseModel):
    source_lang: str
    target_langs: List[str]


class LangResponse(BaseModel):
    accepted_langs: List[str]


class TranslatedChunk(TextChunk):
    lang: str


async def translate_stream(
    chunks: AsyncIterator[TextChunk],
    source_lang: str,
    target_langs: List[str],
) -> AsyncIterator[TranslatedChunk]:
    """Translate text chunks using Google Cloud Translate."""

    client = translate.TranslationServiceClient()
    parent = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT', 'test')}/locations/{os.getenv('TRANSLATE_LOCATION', 'global')}"
    glossary = os.getenv("TRANSLATE_GLOSSARY")
    glossary_config = (
        TranslateTextGlossaryConfig(glossary=glossary) if glossary else None
    )

    loop = asyncio.get_event_loop()
    async for chunk in chunks:
        for lang in target_langs:

            def do_request() -> str:
                response = client.translate_text(
                    parent=parent,
                    contents=[chunk.text],
                    source_language_code=source_lang,
                    target_language_code=lang,
                    mime_type="text/plain",
                    glossary_config=glossary_config,
                )
                return response.translations[0].translated_text

            translated = await loop.run_in_executor(None, do_request)
            yield TranslatedChunk(
                text=translated,
                is_final=chunk.is_final,
                timestamp_ms=chunk.timestamp_ms,
                lang=lang,
            )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/stream")
async def stream(websocket: WebSocket) -> None:
    """Stream `TextChunk` JSON and return translated results."""

    await websocket.accept()

    first = await websocket.receive_json()
    req = LangRequest(**first)
    await websocket.send_json(
        LangResponse(accepted_langs=req.target_langs).model_dump()
    )

    chunk_q: asyncio.Queue[TextChunk | None] = asyncio.Queue()

    async def receiver() -> None:
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("stop"):
                    await chunk_q.put(None)
                    break
                chunk = TextChunk(**data)
                await chunk_q.put(chunk)
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
        async for out in translate_stream(
            chunk_iter(), req.source_lang, req.target_langs
        ):
            await websocket.send_json(out.model_dump())
    finally:
        await recv_task
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
