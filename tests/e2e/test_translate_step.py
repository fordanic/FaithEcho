"""E2E test for the Translation service."""

from __future__ import annotations

import json
import os
from typing import List

import aiohttp
import pytest


@pytest.fixture
def translate_url() -> str:
    """Get Translation service URL from env or use default."""
    return os.getenv("TRANSLATE_URL", "ws://localhost:8102/stream")


@pytest.fixture
def test_chunks() -> List[dict]:
    """Sample text chunks for translation testing."""
    return [
        {
            "text": "Välkommen till vår gudstjänst",
            "is_final": True,
            "timestamp_ms": 1000,
        },
        {
            "text": "Vi ska sjunga en psalm tillsammans",
            "is_final": True,
            "timestamp_ms": 2000,
        },
    ]


@pytest.mark.asyncio
async def test_translate_service(translate_url: str, test_chunks: List[dict]) -> None:
    """Test Translation service can translate text chunks."""
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(translate_url) as ws:
            # Configure translation languages
            await ws.send_json(
                {"source_lang": "sv-SE", "target_langs": ["en-US", "fr-FR"]}
            )

            # Verify language configuration accepted
            resp = await ws.receive_json()
            assert "accepted_langs" in resp
            assert isinstance(resp["accepted_langs"], list)
            assert all(lang in resp["accepted_langs"] for lang in ["en-US", "fr-FR"])

            # Stream text chunks
            for chunk in test_chunks:
                await ws.send_json(chunk)
            await ws.send_json({"stop": True})

            # Track chunks and translations
            translations = []
            chunk_index = 0
            current_chunk_index = -1
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    translations.append(data)
                    chunk_index = len(translations) - 1
                    new_chunk_index = chunk_index // 2

                    if new_chunk_index != current_chunk_index:
                        current_chunk_index = new_chunk_index
                        orig_chunk = test_chunks[current_chunk_index]
                        print(
                            f"\nOriginal ({orig_chunk['timestamp_ms']}ms): {orig_chunk['text']}"
                        )
                    print(f"Translation ({data['lang']}): {data['text']}")

            # Print summary of translations received
            print(f"\nReceived {len(translations)} total translations:")
            current_chunk_index = -1
            for i, trans in enumerate(translations):
                new_chunk_index = i // 2
                if new_chunk_index != current_chunk_index:
                    current_chunk_index = new_chunk_index
                    orig_chunk = test_chunks[current_chunk_index]
                    print(f"\nOriginal: {orig_chunk['text']}")
                print(
                    f"{trans['lang']}: {trans['text']} (timestamp: {trans['timestamp_ms']}ms)"
                )

    # Verify translation results
    assert len(translations) > 0, "No translations received"

    # Each source chunk should have translations for both target languages
    expected_count = len(test_chunks) * 2  # 2 target languages
    assert (
        len(translations) >= expected_count
    ), f"Expected at least {expected_count} translations"

    # Verify translation structure
    for trans in translations:
        assert "text" in trans, "Missing text in translation"
        assert "lang" in trans, "Missing language code"
        assert "is_final" in trans, "Missing is_final flag"
        assert "timestamp_ms" in trans, "Missing timestamp"
        assert trans["lang"] in [
            "en-US",
            "fr-FR",
        ], f"Unexpected language: {trans['lang']}"
        assert isinstance(trans["text"], str), "Text should be string"
        assert isinstance(trans["is_final"], bool), "is_final should be boolean"
        assert isinstance(trans["timestamp_ms"], int), "timestamp should be integer"

    # Verify we got translations in both target languages
    langs_received = {t["lang"] for t in translations}
    assert langs_received == {
        "en-US",
        "fr-FR",
    }, "Missing translations for some target languages"
