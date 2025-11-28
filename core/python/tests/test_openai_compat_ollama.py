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
from typing import Optional

import pytest

from agent_core import AgentCore


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")  # reasoning model for stable behavior


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


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
def test_system_message_feature_with_ollama(ensure_model, tmp_path):
    from plugins.openai_provider import OpenAICompatibleProvider
    from plugins.system_message_feature import SystemMessageFeature

    core = AgentCore()
    core.register_provider(OpenAICompatibleProvider)
    core.register_feature(SystemMessageFeature)

    # Use a list of relatively uncommon languages so that their
    # appearance in the answer is strong evidence that the system
    # message (sourced via a file variable) influenced the model.
    uncommon_languages = [
        "Smalltalk",
        "Erlang",
        "Ada",
        "Forth",
        "OCaml",
    ]

    context_file = tmp_path / "languages.txt"
    context_file.write_text(", ".join(uncommon_languages), encoding="utf-8")

    config = {
        "model": MODEL,
        "base_url": OPENAI_BASE_URL,
        "timeout": 60,
        "system_message": {
            "template": (
                "When asked about good or best programming languages, you must "
                "say that the best programming languages are: {{LANG_LIST}}. "
                "You may elaborate briefly, but ensure you explicitly mention "
                "at least some of these names."
            ),
            "variables": {
                "LANG_LIST": {"files": [str(context_file)]},
            },
        },
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "What are the best programming languages and why? Provide a short answer.",
    )

    new_session, responses = core.send_request(session, config)

    print("complete session:", new_session)

    assert new_session is not None
    assert responses
    final_message = responses[-1]
    assert final_message.get("role") == "assistant"
    content = final_message.get("content", "") or ""
    assert isinstance(content, str)
    assert content

    # Ensure that the answer reflects the file-driven system message by
    # mentioning at least one of the uncommon languages from the
    # LANG_LIST variable. This is more natural than requiring an
    # arbitrary token while still validating that variable substitution
    # and system prompting worked end-to-end.
    lower_content = content.lower()
    assert any(lang.lower() in lower_content for lang in uncommon_languages)


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
