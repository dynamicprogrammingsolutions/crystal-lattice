"""Integration test for Ollama thinking extension with qwen3.

Requires:
- `ollama` on PATH
- Ollama server running (default http://localhost:11434)
- A qwen3 model that supports `think` and `reasoning` fields

Skips gracefully if prerequisites are not met.
"""

import os
import shutil
import subprocess
from typing import Optional

import pytest

from agent_core import AgentCore


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL_QWEN3 = os.getenv("OLLAMA_MODEL_QWEN3", "qwen3:0.6b")


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


@pytest.fixture(scope="module")
def ensure_model():
    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping Ollama qwen3 thinking test")
    # Try a quick ping to the server
    try:
        cp = _run(["ollama", "ps"], timeout=30)
    except Exception:
        pytest.skip("ollama command unavailable or not responding; skipping")

    # Pull model if needed (idempotent)
    try:
        cp = _run(["ollama", "pull", MODEL_QWEN3], timeout=600)
        if cp.returncode != 0:
            msg = cp.stderr.decode("utf-8", errors="ignore")
            pytest.skip(f"failed to pull model {MODEL_QWEN3}: {msg}")
    except Exception as e:
        pytest.skip(f"could not pull model {MODEL_QWEN3}: {e}")


@pytest.mark.ollama
def test_ollama_thinking_non_streaming_with_qwen3(ensure_model):
    core = AgentCore()
    core.discover_and_register(
        [
            "plugins.openai_provider",
            "plugins.ollama_thinking_extension",
        ]
    )

    config = {
        "model": MODEL_QWEN3,
        "base_url": OPENAI_BASE_URL,
        "timeout": 60,
        "think": True,
    }

    session = core.create_session()
    session = core.add_message(session, "system", "You are a helpful assistant.")
    session = core.add_message(
        session,
        "user",
        "Calculate a color code from the given words. " "WORDS: Mountain Sky River Forest Cloud.",
    )

    new_session, responses = core.send_request(session, config)
    assert new_session is not None
    assert responses, "expected at least one assistant response"

    assistant = responses[-1]
    assert assistant.get("role") == "assistant"
    metadata = assistant.get("metadata") or {}
    # Do not require non-empty reasoning, only that the field is present
    assert "reasoning" in metadata
    assert isinstance(metadata["reasoning"], str)
