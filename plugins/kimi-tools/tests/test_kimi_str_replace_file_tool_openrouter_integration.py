"""OpenRouter integration test for KimiStrReplaceFileTool."""

from __future__ import annotations

import os

import pytest

from agent_core import AgentCore

from kimi_tools import KimiStrReplaceFileTool


MODEL = os.getenv("OPENROUTER_MODEL_KIMI_TOOLS", "moonshotai/kimi-k2.5")


@pytest.mark.integration
@pytest.mark.openrouter
def test_kimi_str_replace_file_tool_via_openrouter(tmp_path):
    """Test that Kimi uses StrReplaceFile tool correctly."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    # Pre-create the file as suggested - simpler test
    target = tmp_path / "note.txt"
    target.write_text("alpha\n", encoding="utf-8")

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(KimiStrReplaceFileTool)

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
        "Use the StrReplaceFile tool when a file must be edited.",
    )
    session = core.add_message(
        session,
        "user",
        "Use StrReplaceFile to change 'alpha' to 'beta' in note.txt.",
    )

    session, responses = core.send_request(session, config)
    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected a tool call"

    tool_name = tool_calls[0].get("function", {}).get("name")
    assert tool_name == "StrReplaceFile"

    for tool_msg in core.execute_tool_calls(tool_calls, config):
        session = core.add_message(
            session,
            role=tool_msg["role"],
            content=tool_msg["content"],
            metadata=tool_msg.get("metadata"),
            config=config,
        )

    # Verify file was edited correctly
    assert target.read_text().strip() == "beta"