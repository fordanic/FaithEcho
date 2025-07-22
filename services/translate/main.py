from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.cloud import translate_v3 as translate
from google.cloud.translate_v3.types import TranslateTextGlossaryConfig
from pydantic import BaseModel

app = FastAPI(title="FaithEcho TRANSLATE Service")

# Initialise Google Translate client and configuration once at startup.
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    TRANSLATE_CLIENT = translate.TranslationServiceClient()
else:
    from google.auth.credentials import AnonymousCredentials

    TRANSLATE_CLIENT = translate.TranslationServiceClient(
        credentials=AnonymousCredentials()
    )
PARENT = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT', 'test')}/locations/{os.getenv('TRANSLATE_LOCATION', 'global')}"
_glossary = os.getenv("TRANSLATE_GLOSSARY")
GLOSSARY_CONFIG = TranslateTextGlossaryConfig(glossary=_glossary) if _glossary else None


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

    loop = asyncio.get_running_loop()

    def do_request(text: str, lang: str) -> str:
        response = TRANSLATE_CLIENT.translate_text(
            parent=PARENT,
            contents=[text],
            source_language_code=source_lang,
            target_language_code=lang,
            mime_type="text/plain",
            glossary_config=GLOSSARY_CONFIG,
        )
        return response.translations[0].translated_text

    async for chunk in chunks:
        # Run translation requests for all target languages concurrently
        tasks = [
            loop.run_in_executor(None, do_request, chunk.text, lang)
            for lang in target_langs
        ]
        results = await asyncio.gather(*tasks)

        for lang, translated_text in zip(target_langs, results):
            yield TranslatedChunk(
                text=translated_text,
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
                    break
                chunk = TextChunk(**data)
                await chunk_q.put(chunk)
        except WebSocketDisconnect:
            pass
        except Exception:
            import logging

            logging.exception("Error in websocket receiver")
        finally:
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
