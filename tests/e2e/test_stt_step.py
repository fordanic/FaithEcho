"""E2E test for the Speech-to-Text service."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import AsyncIterator

import aiohttp
import pytest


@pytest.fixture
def audio_file() -> Path:
    """Path to test audio file."""
    return Path(__file__).parent.parent / "data" / "sample001.wav"


@pytest.fixture
def stt_url() -> str:
    """Get STT service URL from env or use default."""
    return os.getenv("STT_URL", "ws://localhost:8101/stream")


async def stream_audio(file: Path) -> AsyncIterator[bytes]:
    """Stream audio file content in chunks."""
    CHUNK_SIZE = 1024 * 4  # 4KB chunks

    with wave.open(str(file), "rb") as wav:
        while True:
            data = wav.readframes(CHUNK_SIZE)
            if not data:
                break
            # Add a small delay to simulate real-time streaming
            await asyncio.sleep(0.1)
            yield data


@pytest.mark.asyncio
async def test_stt_service(audio_file: Path, stt_url: str) -> None:
    """Test STT service can transcribe streaming audio."""
    transcriptions = []

    async def receive_transcriptions(ws: aiohttp.ClientWebSocketResponse) -> None:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                transcriptions.append(data)
                # Print transcription result immediately with flush
                print(
                    f"Transcription: {data['text']} {'[FINAL]' if data.get('is_final') else '[interim]'}",
                    flush=True,
                )
                if data.get("is_final"):
                    break

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(stt_url) as ws:
            # Start receiving transcriptions concurrently
            receive_task = asyncio.create_task(receive_transcriptions(ws))

            # Stream audio chunks
            audio_stream = stream_audio(audio_file)
            async for chunk in audio_stream:
                await ws.send_bytes(chunk)
            await ws.send_json({"text": "stop"})

            # Wait for final transcription
            await receive_task

    # Verify transcription results
    assert len(transcriptions) > 0, "No transcription received"
    assert any(t.get("is_final", False) for t in transcriptions), (
        "No final transcription received"
    )

    # Verify transcription structure
    for trans in transcriptions:
        assert "text" in trans, "Missing text in transcription"
        assert "is_final" in trans, "Missing is_final flag"
        assert "timestamp_ms" in trans, "Missing timestamp"
        assert isinstance(trans["text"], str), "Text should be string"
        assert isinstance(trans["is_final"], bool), "is_final should be boolean"
        assert isinstance(trans["timestamp_ms"], int), "timestamp should be integer"
