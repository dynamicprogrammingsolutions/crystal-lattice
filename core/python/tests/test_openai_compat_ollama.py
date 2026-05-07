"""
Integration test for the OpenAI-Compatible provider against Ollama.

Requirements:
- `ollama` executable available on PATH
- Ollama running locally (default http://localhost:11434)
- Uses OpenAI-compatible endpoint at http://localhost:11434/v1
- Uses a small reasoning-capable model (qwen3) for stability

This test skips gracefully if Ollama is unavailable or the model cannot be pulled.
"""

import os
import shutil
import subprocess
import threading
import time
from typing import Optional

import pytest

from agent_core import AgentCore
from agent_core.types import ProviderRequestCancelled
from plugins.openai_provider import OpenAICompatibleProvider


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")  # reasoning model for stable behavior
pytestmark = pytest.mark.integration


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


@pytest.mark.ollama
def test_openai_compat_non_streaming_with_ollama(ensure_model):
    core = AgentCore()
    # Discover and register provider from plugins directory structure
    core.discover_and_register(["plugins.openai_provider"])

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


@pytest.mark.ollama
def test_request_options_feature_with_ollama(ensure_model):
    from plugins.openai_provider import OpenAICompatibleProvider
    from plugins.request_options_feature import RequestOptionsFeature

    core = AgentCore()
    core.register_provider(OpenAICompatibleProvider)
    core.register_feature(RequestOptionsFeature)

    config = {
        "model": MODEL,
        "base_url": OPENAI_BASE_URL,
        "timeout": 60,
        "request_options": {
            "temperature": 0.1,
            "max_tokens": 32,
        },
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "List three programming languages in a short sentence.",
    )

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert responses
    final_message = responses[-1]
    assert isinstance(final_message, dict)
    assert final_message.get("role") == "assistant"


@pytest.mark.ollama
def test_openai_compat_stream_cancel_soon_after_send_with_ollama(ensure_model):
    provider = OpenAICompatibleProvider()
    config = {
        "model": MODEL,
        "base_url": OPENAI_BASE_URL,
        "timeout": 60,
    }
    state = provider.init(config)
    native_messages = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "Write a long detailed essay about distributed systems.",
            }
        ],
        state,
    )
    native_messages, state = provider.initialize_request(
        native_messages,
        state,
        request_id="openai_compat_cancel_soon",
    )

    outcome: dict[str, object] = {"chunks": []}

    def _consume() -> None:
        try:
            for chunk in provider.stream_api(
                native_messages,
                state,
                request_id="openai_compat_cancel_soon",
            ):
                outcome["chunks"].append(chunk)
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    worker = threading.Thread(target=_consume)
    worker.start()

    deadline = time.time() + 10.0
    while time.time() < deadline:
        if provider.cancel_request("openai_compat_cancel_soon"):
            break
        time.sleep(0.02)
    else:
        raise AssertionError("OpenAI-compatible request was never registered as active")

    worker.join(timeout=20.0)
    assert not worker.is_alive()
    assert not outcome["chunks"]
    assert outcome.get("error") is None or isinstance(
        outcome.get("error"), ProviderRequestCancelled
    )


@pytest.mark.ollama
def test_openai_compat_stream_cancel_after_first_partial_with_ollama(ensure_model):
    provider = OpenAICompatibleProvider()
    config = {
        "model": MODEL,
        "base_url": OPENAI_BASE_URL,
        "timeout": 60,
    }
    state = provider.init(config)
    native_messages = provider.to_native_messages(
        [{"role": "user", "content": "Write a long detailed essay about concurrency."}],
        state,
    )
    native_messages, state = provider.initialize_request(
        native_messages,
        state,
        request_id="openai_compat_cancel_after_partial",
    )

    outcome: dict[str, object] = {"chunks": []}

    def _consume() -> None:
        try:
            for chunk in provider.stream_api(
                native_messages,
                state,
                request_id="openai_compat_cancel_after_partial",
            ):
                outcome["chunks"].append(chunk)
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    worker = threading.Thread(target=_consume)
    worker.start()

    deadline = time.time() + 30.0
    while time.time() < deadline:
        if outcome["chunks"]:
            break
        time.sleep(0.05)
    else:
        raise AssertionError(
            "OpenAI-compatible stream did not emit a partial before cancellation"
        )

    assert provider.cancel_request("openai_compat_cancel_after_partial") is True

    worker.join(timeout=20.0)
    assert not worker.is_alive()
    assert outcome["chunks"]
    assert isinstance(outcome.get("error"), ProviderRequestCancelled)
