"""
Integration test for PROJECT_PLAN Example 1 against local Ollama.
Skips gracefully if Ollama is unavailable or model cannot be pulled.
"""
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")


def _which(cmd: str):
    return shutil.which(cmd)


def _run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


@pytest.fixture(scope="module")
def ensure_model():
    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping project plan example test")
    # Quick ping to the server via ollama ps
    try:
        _run(["ollama", "ps"], timeout=30)
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
def test_project_plan_example1_basic_runs(ensure_model):
    # The example reads OLLAMA_HOST/OLLAMA_MODEL from env
    os.environ.setdefault("OLLAMA_HOST", OLLAMA_HOST)
    os.environ.setdefault("OLLAMA_MODEL", MODEL)

    mod = __import__("examples.project_plan_example1_basic", fromlist=["run_example"])
    assert hasattr(mod, "run_example")
    mod.run_example()
