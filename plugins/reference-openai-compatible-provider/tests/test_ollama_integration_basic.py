from __future__ import annotations

import os

import pytest
import requests

from agent_core.core import AgentCore

from reference_openai_compatible_provider.provider import OpenAICompatibleProvider
from reference_openai_compatible_provider.reasoning_extension import OpenAICompatibleReasoningExtension
from reference_openai_compatible_provider.tools_extension import OpenAICompatibleToolsExtension


def _ollama_available(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/models", timeout=2)
        return bool(r.ok)
    except Exception:
        return False


def _ollama_cfg() -> dict:
    return {
        "base_url": os.environ.get("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1"),
        "model": os.environ.get("OLLAMA_OPENAI_MODEL", "qwen3:0.6b"),
        "timeout": float(os.environ.get("OLLAMA_OPENAI_TIMEOUT", "60")),
    }


@pytest.mark.integration
@pytest.mark.ollama
def test_basic_non_streaming_ollama_openai_compat():
    cfg = _ollama_cfg()
    if not _ollama_available(cfg["base_url"]):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    core = AgentCore()
    core.register_provider(
        OpenAICompatibleProvider,
        extensions=[OpenAICompatibleToolsExtension, OpenAICompatibleReasoningExtension],
    )

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with the single word: pong")
    _session2, finals = core.send_request(session, cfg)
    assert finals and finals[-1]["role"] == "assistant"
    assert isinstance(finals[-1].get("content"), str)
    assert finals[-1]["content"].strip() != ""


@pytest.mark.integration
@pytest.mark.ollama
def test_basic_streaming_ollama_openai_compat():
    cfg = _ollama_cfg()
    if not _ollama_available(cfg["base_url"]):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    core = AgentCore()
    core.register_provider(
        OpenAICompatibleProvider,
        extensions=[OpenAICompatibleToolsExtension, OpenAICompatibleReasoningExtension],
    )

    session = core.create_session()
    session = core.add_message(session, "user", "Count to 3, separated by spaces.")

    saw_partial = False
    final_event = None
    for e in core.send_request_stream(session, cfg):
        if e.get("type") == "partial":
            saw_partial = True
        if e.get("type") == "final":
            final_event = e

    assert saw_partial
    assert final_event is not None
    assert final_event["messages"][-1]["role"] == "assistant"
    assert final_event["messages"][-1].get("content")


@pytest.mark.integration
@pytest.mark.ollama
def test_models_ui_schema_lists_available_models():
    cfg = _ollama_cfg()
    if not _ollama_available(cfg["base_url"]):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    core = AgentCore()
    core.register_provider(OpenAICompatibleProvider)

    schema = core.get_ui_schema(cfg)
    model_el = next((el for el in schema if isinstance(el, dict) and el.get("key") == "model"), None)
    assert model_el is not None
    options = model_el.get("options")
    if model_el.get("type") != "select" or not isinstance(options, list) or not options:
        pytest.skip("No model options returned by /models")
