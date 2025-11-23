"""Streaming integration test for Ollama thinking extension with qwen3.

Requires:
- `ollama` on PATH
- Ollama server running (default http://localhost:11434)
- A qwen3 model that supports `think` and `reasoning` fields

Skips gracefully if prerequisites are not met.
"""

import os
import shutil
import subprocess
import sys
from typing import Optional

import pytest

from agent_core import AgentCore

# Ensure repo root is importable to load plugins/* modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL_QWEN3 = os.getenv("OLLAMA_MODEL_QWEN3", "qwen3:0.6b")


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
    )


@pytest.fixture(scope="module")
def ensure_model():
    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping Ollama qwen3 thinking streaming test")
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


@pytest.mark.integration
def test_ollama_thinking_streaming_with_qwen3(ensure_model):
    core = AgentCore()
    core.discover_and_register(
        [
            "plugins.providers.openai.python.openai_provider",
            "plugins.providers.openai.python.ollama_thinking_extension",
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
        "Calculate a color code from the given words. "
        "WORDS: Mountain Sky River Forest Cloud.",
    )

    partial_reasoning_seen = False
    final_reasoning: Optional[str] = None

    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "partial":
            msg = chunk["message"]
            metadata = msg.get("metadata") or {}
            reasoning = metadata.get("reasoning")
            if isinstance(reasoning, str) and reasoning:
                partial_reasoning_seen = True
        elif chunk["type"] == "final":
            final_msg = chunk["messages"][-1]
            metadata = final_msg.get("metadata") or {}
            final_reasoning = metadata.get("reasoning")

    assert partial_reasoning_seen, "expected at least one partial reasoning update"
    assert isinstance(final_reasoning, str)
