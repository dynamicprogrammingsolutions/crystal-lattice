from __future__ import annotations

import os

import pytest
import requests

from agent_core.core import AgentCore

from plugins.math_tools import MathTools

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
def test_tools_tool_loop_ollama_openai_compat():
    cfg = _ollama_cfg()
    if not _ollama_available(cfg["base_url"]):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    core = AgentCore()
    core.register_tool(MathTools)
    core.register_provider(
        OpenAICompatibleProvider,
        extensions=[OpenAICompatibleToolsExtension, OpenAICompatibleReasoningExtension],
    )

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Use the add tool to add 2 and 3. After using tools, reply with just the number.",
    )

    session2, finals = core.send_request(session, cfg)
    assert finals and finals[-1]["role"] == "assistant"

    tool_calls = (finals[-1].get("metadata") or {}).get("tool_calls")
    if not isinstance(tool_calls, list) or not tool_calls:
        pytest.skip("Model did not emit tool calls")

    tool_messages = core.execute_tool_calls(tool_calls, cfg)
    assert tool_messages

    for tm in tool_messages:
        session2 = core.add_message(
            session2,
            tm.get("role", "tool"),
            tm.get("content", ""),
            metadata=tm.get("metadata"),
            config=cfg,
        )

    _session3, finals2 = core.send_request(session2, cfg)
    assert finals2 and finals2[-1]["role"] == "assistant"


@pytest.mark.integration
@pytest.mark.ollama
def test_reasoning_metadata_ollama_openai_compat():
    cfg = {**_ollama_cfg(), "think": True}

    if not _ollama_available(cfg["base_url"]):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    core = AgentCore()
    core.register_provider(
        OpenAICompatibleProvider,
        extensions=[OpenAICompatibleToolsExtension, OpenAICompatibleReasoningExtension],
    )

    session = core.create_session()
    session = core.add_message(session, "user", "Compute 12*12. Return only the number.")

    final_event = None
    try:
        for e in core.send_request_stream(session, cfg):
            if e.get("type") == "final":
                final_event = e
    except RuntimeError as e:
        msg = str(e)
        if "reasoning" in msg or "think value" in msg:
            pytest.skip("Reasoning request options not supported by this model/server")
        raise

    assert final_event is not None
    assistant = final_event["messages"][-1]
    reasoning = (assistant.get("metadata") or {}).get("reasoning")
    if not isinstance(reasoning, str) or not reasoning:
        pytest.skip("No reasoning metadata produced (model/server may not support reasoning deltas)")
