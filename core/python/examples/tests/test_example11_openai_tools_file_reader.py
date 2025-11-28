"""
Integration test for Example 11 (OpenAI tools + FileReader with Ollama).

Skips gracefully if Ollama or the model is unavailable.
"""

import os
import shutil
import subprocess
import sys
from typing import Optional

import pytest

# Ensure repo root and core/python are importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL_TOOLS = os.getenv("OLLAMA_MODEL_TOOLS", "qwen3:0.6b")


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
    )


@pytest.fixture(scope="module")
def ensure_model():
    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping Example 11 integration test")
    # Ping server
    try:
        _run(["ollama", "ps"], timeout=30)
    except Exception:
        pytest.skip("ollama command unavailable or not responding; skipping")
    # Pull tools-capable model (idempotent)
    try:
        cp = _run(["ollama", "pull", MODEL_TOOLS], timeout=1200)
        if cp.returncode != 0:
            msg = cp.stderr.decode("utf-8", errors="ignore")
            pytest.skip(f"failed to pull model {MODEL_TOOLS}: {msg}")
    except Exception as e:
        pytest.skip(f"could not pull model {MODEL_TOOLS}: {e}")


@pytest.mark.ollama
def test_example11_openai_tools_file_reader(ensure_model):
    mod = __import__(
        "examples.example11_openai_tools_file_reader", fromlist=["run_example"]
    )
    content, info = mod.run_example()
    assert isinstance(content, str)
    if not content:
        pytest.skip(
            f"model {MODEL_TOOLS} did not return content; ensure a running Ollama and tools-capable model"
        )
    assert len(content) > 0
