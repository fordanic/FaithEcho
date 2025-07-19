import importlib


def test_language_service_messages_exist() -> None:
    pb2 = importlib.import_module("faith_echo.proto.language_service_pb2")
    assert hasattr(pb2, "AudioChunk")
    assert hasattr(pb2, "TextChunk")
    assert hasattr(pb2, "SpeechChunk")
    assert hasattr(pb2, "LangRequest")
    assert hasattr(pb2, "LangResponse")
