"""E2E test for the Text-to-Speech service."""

from __future__ import annotations

import asyncio
import base64
import json
import os
from io import BytesIO
from typing import List

import pyaudio
from pydub import AudioSegment

import aiohttp
import pytest


@pytest.fixture
def tts_url() -> str:
    """Get TTS service URL from env or use default."""
    return os.getenv("TTS_URL", "ws://localhost:8103/stream")


@pytest.fixture
def play_audio() -> bool:
    """Check if audio should be played during test."""
    return os.getenv("PLAY_AUDIO", "").lower() in ("1", "true", "yes")


def play_mp3_bytes(audio_bytes: bytes) -> None:
    """Decode MP3 bytes to PCM with pydub and play via PyAudio."""
    # Decode MP3 to raw PCM using pydub (requires ffmpeg in PATH).
    audio = AudioSegment.from_file(BytesIO(audio_bytes), format="mp3")

    p = pyaudio.PyAudio()
    stream = p.open(
        format=p.get_format_from_width(audio.sample_width),
        channels=audio.channels,
        rate=audio.frame_rate,
        output=True,
    )

    try:
        stream.write(audio.raw_data)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


@pytest.fixture
def test_chunks() -> List[dict]:
    """Sample text chunks for speech synthesis testing."""
    return [
        {
            "text": "Welcome to our church service",
            "is_final": True,
            "timestamp_ms": 1000,
        },
        {
            "text": "We will sing a hymn together",
            "is_final": True,
            "timestamp_ms": 2000,
        },
    ]


@pytest.mark.asyncio
async def test_tts_service(
    tts_url: str, test_chunks: List[dict], play_audio: bool
) -> None:
    """Test TTS service can synthesize speech from text chunks."""
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(tts_url) as ws:
            # Configure voice parameters
            await ws.send_json(
                {
                    "lang": "en-US",
                    "voice": None,  # Use default voice
                    "speaking_rate": 1.0,
                }
            )

            # Verify configuration accepted
            resp = await ws.receive_json()
            assert resp.get("accepted") is True, "Voice configuration was not accepted"

            # Stream text chunks
            for chunk in test_chunks:
                await ws.send_json(chunk)
            await ws.send_json({"stop": True})

            # Collect synthesized audio
            audio_chunks = []
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    audio_chunks.append(data)

    # Verify synthesis results
    assert len(audio_chunks) > 0, "No audio chunks received"
    assert len(audio_chunks) >= len(test_chunks), "Missing audio for some text chunks"

    # Verify audio chunk structure
    for chunk in audio_chunks:
        assert "audio_b64" in chunk, "Missing audio data"
        assert "is_final" in chunk, "Missing is_final flag"
        assert "timestamp_ms" in chunk, "Missing timestamp"

        # Verify audio data is valid base64
        try:
            audio_bytes = base64.b64decode(chunk["audio_b64"])
            assert len(audio_bytes) > 0, "Empty audio data"
            # MP3 files typically start with "ID3" metadata or a 0xFF 0xFB frame‑sync header
            # Validate MP3 header: either an ID3 tag or a generic MPEG frame‑sync word
            valid_mp3_header = (
                audio_bytes.startswith(b"ID3")  # ID3 metadata present
                or (
                    len(audio_bytes) >= 2
                    and audio_bytes[0] == 0xFF
                    and (audio_bytes[1] & 0xE0) == 0xE0  # 111xxxxx – sync word
                )
            )
            assert valid_mp3_header, "Audio bytes are not in MP3 format"
        except Exception as e:
            pytest.fail(f"Invalid base64 audio data: {e}")

        assert isinstance(chunk["is_final"], bool), "is_final should be boolean"
        assert isinstance(chunk["timestamp_ms"], int), "timestamp should be integer"

    # Verify timestamps are monotonically increasing
    timestamps = [chunk["timestamp_ms"] for chunk in audio_chunks]
    assert all(
        t1 <= t2 for t1, t2 in zip(timestamps, timestamps[1:])
    ), "Timestamps not in order"
    # Ensure the synthesis stream ended correctly
    assert audio_chunks[-1]["is_final"] is True, "Last chunk should be marked as final"

    # Play audio if enabled
    if play_audio:
        for chunk in audio_chunks:
            audio_bytes = base64.b64decode(chunk["audio_b64"])
            play_mp3_bytes(audio_bytes)
            # Small pause between chunks
            await asyncio.sleep(0.1)
