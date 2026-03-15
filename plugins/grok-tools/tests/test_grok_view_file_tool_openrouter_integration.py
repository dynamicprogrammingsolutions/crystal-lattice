from __future__ import annotations

import os

import pytest

from agent_core import AgentCore

from grok_tools import GrokViewFileTool


MODEL = os.getenv("OPENROUTER_MODEL_GROK_TOOLS", "x-ai/grok-4.1-fast")


@pytest.mark.integration
@pytest.mark.openrouter
def test_grok_view_file_tool_via_openrouter(tmp_path):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    target = tmp_path / "brief.txt"
    target.write_text("Grok integration line\nSecond line\n", encoding="utf-8")

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(GrokViewFileTool)

    config = {
        "model": MODEL,
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "project_temp_dir": str(tmp_path / ".temp"),
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "Use the view_file tool when a file must be read. Do not answer from memory.",
    )
    session = core.add_message(
        session,
        "user",
        "Use view_file on brief.txt and reply with exactly the first line.",
    )

    session, responses = core.send_request(session, config)
    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected a tool call"

    for tool_msg in core.execute_tool_calls(tool_calls, config):
        session = core.add_message(
            session,
            role=tool_msg["role"],
            content=tool_msg["content"],
            metadata=tool_msg.get("metadata"),
            config=config,
        )

    _session, follow_up = core.send_request(session, config)
    final_text = (follow_up[-1].get("content") or "").strip()
    assert "Grok integration line" in final_text