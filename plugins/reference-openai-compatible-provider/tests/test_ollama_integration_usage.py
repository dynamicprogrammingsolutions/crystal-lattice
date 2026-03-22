from __future__ import annotations

import os

import pytest
import requests

from agent_core.core import AgentCore
from plugins.request_options_feature import RequestOptionsFeature

from reference_openai_compatible_provider.provider import OpenAICompatibleProvider
from reference_openai_compatible_provider.reasoning_extension import (
    OpenAICompatibleReasoningExtension,
)
from reference_openai_compatible_provider.tools_extension import (
    OpenAICompatibleToolsExtension,
)
from reference_openai_compatible_provider.usage_extension import (
    OpenAICompatibleUsageExtension,
)


def _ollama_available(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/models", timeout=2)
        return bool(r.ok)
    except Exception:
        return False


def _ollama_cfg() -> dict:
    return {
        "base_url": os.environ.get(
            "OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1"
        ),
        "model": os.environ.get("OLLAMA_OPENAI_MODEL", "qwen3:0.6b"),
        "timeout": float(os.environ.get("OLLAMA_OPENAI_TIMEOUT", "60")),
    }


@pytest.mark.integration
@pytest.mark.ollama
def test_usage_metadata_ollama_openai_compat():
    cfg = _ollama_cfg()
    if not _ollama_available(cfg["base_url"]):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    core = AgentCore()
    core.register_feature(RequestOptionsFeature)
    core.register_provider(
        OpenAICompatibleProvider,
        extensions=[
            OpenAICompatibleToolsExtension,
            OpenAICompatibleReasoningExtension,
            OpenAICompatibleUsageExtension,
        ],
    )

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with the single word: pong")
    _session2, finals = core.send_request(session, cfg)

    assert finals and finals[-1]["role"] == "assistant"
    metadata = finals[-1].get("metadata") or {}
    usage = metadata.get("usage")
    if not isinstance(usage, dict):
        pytest.skip("No usage metadata produced by this Ollama model/server")

    assert isinstance(metadata.get("usage_total_tokens"), int)
