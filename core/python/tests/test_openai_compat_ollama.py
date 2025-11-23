"""
Integration test for the OpenAI-Compatible provider against Ollama.

Requirements:
- `ollama` executable available on PATH
- Ollama running locally (default http://localhost:11434)
- Uses OpenAI-compatible endpoint at http://localhost:11434/v1
- Uses a very small, non-reasoning model to keep it fast

This test skips gracefully if Ollama is unavailable or the model cannot be pulled.
"""

import os
import shutil
import subprocess
import sys
import time
from typing import Optional

import pytest

from agent_core import AgentCore

# Ensure repo root is importable to load plugins/* modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")  # tiny non-reasoning model


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
    )


@pytest.fixture(scope="module")
def ensure_model():
    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping Ollama integration test")
    # Try a quick ping to the server
    try:
        cp = _run(["ollama", "ps"], timeout=30)
    except Exception:
        pytest.skip("ollama command unavailable or not responding; skipping")

    # Pull model if needed (idempotent)
    try:
        cp = _run(["ollama", "pull", MODEL], timeout=600)
        if cp.returncode != 0:
            msg = cp.stderr.decode("utf-8", errors="ignore")
            pytest.skip(f"failed to pull model {MODEL}: {msg}")
    except Exception as e:
        pytest.skip(f"could not pull model {MODEL}: {e}")


@pytest.mark.integration
def test_openai_compat_non_streaming_with_ollama(ensure_model):
    core = AgentCore()
    # Discover and register provider from plugins directory structure
    core.discover_and_register(["plugins.providers.openai.python.openai_provider"])

    config = {
        "model": MODEL,
        "base_url": OPENAI_BASE_URL,
        "timeout": 60,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Write a short poem")

    partial_count = 0
    final = None
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "partial":
            text = chunk["message"].get("content", "")
            print(text, end="")
            if text:
                partial_count += 1
        elif chunk["type"] == "final":
            final = chunk["messages"][-1]
            print(f"\n\nfinal: {final}")

    assert partial_count > 0, "expected some streaming partials"
    assert final is not None
    assert isinstance(final.get("content"), str) and len(final.get("content", "")) > 0
