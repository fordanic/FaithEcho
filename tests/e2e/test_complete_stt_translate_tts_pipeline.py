"""E2E test for the complete FaithEcho audio pipeline.

This test simulates a full streaming pipeline:
Audio -> STT -> Translate -> TTS
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import sys
import textwrap
import wave
from io import BytesIO
from pathlib import Path
from typing import AsyncIterator, Dict, List

import aiohttp
import pyaudio
import pytest
from pydub import AudioSegment
from src.faith_echo.segment_manager import SegmentManager
from src.faith_echo.sdk import (
    SpeechChunk,
    TTSReceiver,
    TextChunk,
    TranslatedChunk,
)  # type: ignore[import-untyped]


@pytest.fixture
def audio_file() -> Path:
    """Path to test audio file."""
    return Path(__file__).parent.parent / "data" / "sample001.wav"


@pytest.fixture
def services() -> dict[str, str]:
    """Get service URLs from env or use defaults."""
    return {
        "stt": os.getenv("STT_URL", "ws://localhost:8101/stream"),
        "translate": os.getenv("TRANSLATE_URL", "ws://localhost:8102/stream"),
        "tts": os.getenv("TTS_URL", "ws://localhost:8103/stream"),
    }


@pytest.fixture
def play_audio() -> bool:
    """Check if audio should be played during test."""
    return os.getenv("PLAY_AUDIO", "").lower() in ("1", "true", "yes")


def play_mp3_bytes(audio_bytes: bytes, lang: str) -> None:
    """Decode MP3 bytes to PCM with pydub and play via PyAudio."""
    try:
        audio = AudioSegment.from_file(BytesIO(audio_bytes), format="mp3")
        p = pyaudio.PyAudio()
        stream = p.open(
            format=p.get_format_from_width(audio.sample_width),
            channels=audio.channels,
            rate=audio.frame_rate,
            output=True,
        )
        stream.write(audio.raw_data)
        stream.stop_stream()
        stream.close()
        p.terminate()
    except Exception as e:
        pytest.fail(f"Failed to play audio for lang {lang}: {e}")


async def stream_audio(file: Path) -> AsyncIterator[bytes]:
    """Stream audio file content in chunks."""
    CHUNK_SIZE = 1024 * 4  # 4KB chunks
    with wave.open(str(file), "rb") as wav:
        while True:
            data = wav.readframes(CHUNK_SIZE)
            if not data:
                break
            await asyncio.sleep(0.1)  # Simulate real-time streaming
            yield data


async def printer_task(queue: asyncio.Queue):
    """Manages the console output to create updating "text boxes"."""
    # ANSI escape codes
    CLEAR_SCREEN = "\033[2J"
    MOVE_HOME = "\033[H"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"

    # Box dimensions and positions
    WIDTH = 100
    HEIGHT = 7  # 1 title line + 6 content lines
    STT_Y = 1
    EN_Y = STT_Y + HEIGHT + 1
    FR_Y = EN_Y + HEIGHT + 1
    TOTAL_HEIGHT = FR_Y + HEIGHT

    stt_text = ""
    en_text = ""
    fr_text = ""

    def draw_box(y_pos, title):
        """Draws a box with a title."""
        border = f"+{'=' * (WIDTH - 2)}+"
        print(f"\033[{y_pos};1H{border}", end="")
        print(f"\033[{y_pos};3H {title} ", end="")
        for i in range(1, HEIGHT):
            print(f"\033[{y_pos + i};1H|{' ' * (WIDTH - 2)}|", end="")
        print(f"\033[{y_pos + HEIGHT};1H{border}", end="")

    def update_text_in_box(y_pos, text):
        """Clears the box content and prints new wrapped text."""
        for i in range(1, HEIGHT):
            print(f"\033[{y_pos + i};2H{' ' * (WIDTH - 2)}", end="")

        wrapped_text = textwrap.wrap(text, width=WIDTH - 4)
        for i, line in enumerate(wrapped_text[: HEIGHT - 1]):
            print(f"\033[{y_pos + i + 1};3H{line}", end="")

    # --- Initial Setup ---
    print(f"{CLEAR_SCREEN}{MOVE_HOME}{HIDE_CURSOR}", end="")
    draw_box(STT_Y, "STT Transcription")
    draw_box(EN_Y, "English Translation")
    draw_box(FR_Y, "French Translation")
    sys.stdout.flush()

    try:
        while True:
            item = await queue.get()
            if item is None:
                break

            if item["type"] == "stt":
                stt_text = item["text"]
                if item.get("is_final"):
                    stt_text += " [FINAL]"
                update_text_in_box(STT_Y, stt_text)
            elif item["type"] == "translate":
                if item["lang"] == "en-US":
                    en_text = item["text"]
                    update_text_in_box(EN_Y, en_text)
                elif item["lang"] == "fr-FR":
                    fr_text = item["text"]
                    update_text_in_box(FR_Y, fr_text)

            print(f"\033[{TOTAL_HEIGHT + 2};1H", end="")
            sys.stdout.flush()
    finally:
        print(f"\033[{TOTAL_HEIGHT + 2};1H{SHOW_CURSOR}", end="")
        sys.stdout.flush()


@pytest.mark.asyncio
async def test_complete_stt_translate_tts_pipeline(
    audio_file: Path, services: dict[str, str], play_audio: bool
) -> None:
    """Test complete pipeline: Audio → STT → Translate → TTS."""
    stt_output: List[Dict] = []
    translations: Dict[str, List[Dict]] = {"en-US": [], "fr-FR": []}
    tts_output: Dict[str, List[Dict]] = {"en-US": [], "fr-FR": []}
    audio_to_play: List[Dict] = []

    manager = SegmentManager(["en-US", "fr-FR"])
    print_q: asyncio.Queue = asyncio.Queue()

    async def stt_task(ws: aiohttp.ClientWebSocketResponse):
        """Handles STT: sends audio, receives transcriptions, and queues them."""
        sender_task = asyncio.create_task(stt_sender(ws))
        receiver_task = asyncio.create_task(stt_receiver(ws))
        await asyncio.gather(sender_task, receiver_task)

    async def stt_sender(ws: aiohttp.ClientWebSocketResponse):
        audio_stream = stream_audio(audio_file)
        async for chunk in audio_stream:
            await ws.send_bytes(chunk)
        await ws.send_json({"text": "stop"})

    async def stt_receiver(ws: aiohttp.ClientWebSocketResponse):
        segment_id = 1
        revision = 0
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                revision += 1
                data["segment_id"] = segment_id
                data["revision"] = revision
                stt_output.append(data)
                await print_q.put(data | {"type": "stt"})
                await manager.put_stt_chunk(TextChunk(**data))
                if data.get("is_final"):
                    segment_id += 1
                    revision = 0
        await manager.put_stt_chunk(None)

    async def translate_task(ws: aiohttp.ClientWebSocketResponse):
        """Handles translation: sends transcriptions, receives translations."""
        await ws.send_json({"source_lang": "sv-SE", "target_langs": ["en-US", "fr-FR"]})
        resp = await ws.receive_json()
        assert "accepted_langs" in resp

        sender_task = asyncio.create_task(translate_sender(ws))
        receiver_task = asyncio.create_task(translate_receiver(ws))
        await asyncio.gather(sender_task, receiver_task)

    async def translate_sender(ws: aiohttp.ClientWebSocketResponse):
        while True:
            chunk = await manager.get_stt_chunk()
            if chunk is None:
                break
            await ws.send_json(chunk.model_dump())
        await ws.send_json({"stop": True})

    async def translate_receiver(ws: aiohttp.ClientWebSocketResponse):
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                lang = data["lang"]
                if lang in translations:
                    translations[lang].append(data)
                    await print_q.put(data | {"type": "translate"})
                    await manager.put_translation_chunk(TranslatedChunk(**data))

        await manager.put_translation_chunk(None)

    async def tts_task(ws: aiohttp.ClientWebSocketResponse, lang: str):
        """Handles TTS: sends text, receives audio."""
        await ws.send_json({"lang": lang, "speaking_rate": 1.0})
        resp = await ws.receive_json()
        assert resp.get("accepted") is True

        receiver_state = TTSReceiver()
        sender_task = asyncio.create_task(tts_sender(ws, lang))
        receiver_task = asyncio.create_task(tts_receiver(ws, lang, receiver_state))
        await asyncio.gather(sender_task, receiver_task)

    async def tts_sender(ws: aiohttp.ClientWebSocketResponse, lang: str):
        while True:
            chunk = await manager.get_translation_chunk(lang)
            if chunk is None:
                break
            if not chunk.is_final:
                continue
            await ws.send_json(chunk.model_dump())
        await ws.send_json({"stop": True})

    async def tts_receiver(
        ws: aiohttp.ClientWebSocketResponse, lang: str, state: TTSReceiver
    ):
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                chunk = SpeechChunk(**data)
                state.process(chunk)
                manager.record_tts_chunk(chunk, lang)
                tts_output[lang] = [c.model_dump() for c in state.ordered_segments()]
                if play_audio:
                    audio_bytes = base64.b64decode(data["audio_b64"])
                    audio_to_play.append(
                        {
                            "lang": lang,
                            "bytes": audio_bytes,
                            "timestamp_ms": data.get("timestamp_ms", 0),
                        }
                    )

    # --- Main execution ---
    main_printer = asyncio.create_task(printer_task(print_q))

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(services["stt"]) as stt_ws:
            async with session.ws_connect(services["translate"]) as trans_ws:
                async with session.ws_connect(services["tts"]) as tts_ws_en:
                    async with session.ws_connect(services["tts"]) as tts_ws_fr:
                        await asyncio.gather(
                            stt_task(stt_ws),
                            translate_task(trans_ws),
                            tts_task(tts_ws_en, "en-US"),
                            tts_task(tts_ws_fr, "fr-FR"),
                        )

    await print_q.put(None)
    await main_printer

    if play_audio and audio_to_play:
        print("\nPlaying synthesized audio...")
        audio_to_play.sort(key=lambda x: x.get("timestamp_ms", 0))
        for audio in audio_to_play:
            print(f"Playing audio for language: {audio['lang']}")
            play_mp3_bytes(audio["bytes"], audio["lang"])

    # Final assertions
    assert len(stt_output) > 0, "No transcription received"
    assert any(t.get("is_final") for t in stt_output), "No final transcription"
    assert len(translations["en-US"]) > 0, "No English translations"
    assert len(translations["fr-FR"]) > 0, "No French translations"
    assert len(tts_output["en-US"]) > 0, "No English audio received"
    assert len(tts_output["fr-FR"]) > 0, "No French audio received"
    assert all("audio_b64" in chunk for chunk in tts_output["en-US"])
    assert all("audio_b64" in chunk for chunk in tts_output["fr-FR"])

    print("\n--- Pipeline Test Summary ---")
    print(f"Total STT chunks: {len(stt_output)}")
    print(f"Total English translations: {len(translations['en-US'])}")
    print(f"Total French translations: {len(translations['fr-FR'])}")
    print(f"Total English TTS audio chunks: {len(tts_output['en-US'])}")
    print(f"Total French TTS audio chunks: {len(tts_output['fr-FR'])}")
    print("\nPipeline test completed successfully.")
