from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


def compile_proto(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    proto_rel = "faith_echo/proto/language_service.proto"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            "-Isrc",
            f"--python_out={tmp_path}",
            proto_rel,
        ],
        check=True,
        cwd=root,
    )
    (tmp_path / "faith_echo").mkdir(exist_ok=True)
    (tmp_path / "faith_echo" / "__init__.py").touch()
    (tmp_path / "faith_echo" / "proto").mkdir(exist_ok=True)
    (tmp_path / "faith_echo" / "proto" / "__init__.py").touch()
    sys.path.insert(0, str(tmp_path))
    pkg = importlib.import_module("faith_echo")
    pkg.__path__.insert(0, str(tmp_path / "faith_echo"))
    importlib.invalidate_caches()
    return importlib.import_module("faith_echo.proto.language_service_pb2")


def test_language_service_messages_exist(tmp_path: Path) -> None:
    pb2 = compile_proto(tmp_path)
    for name in [
        "AudioChunk",
        "TextChunk",
        "SpeechChunk",
        "LangRequest",
        "LangResponse",
    ]:
        assert hasattr(pb2, name)
