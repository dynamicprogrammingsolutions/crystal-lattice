"""OpenRouter integration test for KimiWebSearchTool."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from kimi_tools import KimiWebSearchTool


load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

MODEL = os.getenv("OPENROUTER_MODEL_KIMI_TOOLS", "moonshotai/kimi-k2.5")


def _final_text(response: dict) -> str:
    text = (response.get("content") or "").strip()
    if text:
        return text
    return str((response.get("metadata") or {}).get("reasoning") or "").strip()


def _run_tool_loop(core: AgentCore, session, config: dict, max_rounds: int = 6):
    seen_tools: list[str] = []
    tool_results: list[dict] = []
    for _ in range(max_rounds):
        session, responses = core.send_request(session, config)
        tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
        if not tool_calls:
            return session, responses, seen_tools, tool_results

        seen_tools.extend(call.get("function", {}).get("name") for call in tool_calls)
        for tool_msg in core.execute_tool_calls(tool_calls, config):
            tool_results.append(tool_msg)
            session = core.add_message(
                session,
                role=tool_msg["role"],
                content=tool_msg["content"],
                metadata=tool_msg.get("metadata"),
                config=config,
            )
    raise AssertionError("tool loop did not converge")


@pytest.mark.integration
@pytest.mark.openrouter
def test_kimi_web_search_tool_via_openrouter_tavily() -> None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        pytest.skip("TAVILY_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(KimiWebSearchTool)

    config = {
        "model": MODEL,
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "web_search_enabled": True,
        "web_search_provider": "tavily",
        "tavily_api_key": tavily_key,
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        (
            "When the user explicitly asks you to use SearchWeb, call the "
            "SearchWeb tool before answering. After a successful tool result, "
            "reply exactly OK."
        ),
    )
    session = core.add_message(
        session,
        "user",
        (
            "Use SearchWeb to search for current information about the Python "
            "programming language official website. Then reply exactly OK."
        ),
    )

    _session, responses, seen_tools, tool_results = _run_tool_loop(
        core, session, config
    )

    assert "SearchWeb" in seen_tools
    assert tool_results
    assert any("Title: " in (msg.get("content") or "") for msg in tool_results)
    final_text = _final_text(responses[-1])
    assert not final_text or "OK" in final_text.split()