"""OpenRouter integration test for KimiShellTool."""

from __future__ import annotations

import os

import pytest

from agent_core import AgentCore

from kimi_tools import KimiShellTool


MODEL = os.getenv("OPENROUTER_MODEL_KIMI_TOOLS", "moonshotai/kimi-k2.5")


@pytest.mark.integration
@pytest.mark.openrouter
def test_kimi_shell_tool_via_openrouter(tmp_path):
    """Test that Kimi uses Shell tool correctly."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    target = tmp_path / "output.txt"

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(KimiShellTool)

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
        "You must use the Shell tool to execute shell commands. Never answer without calling the tool first.",
    )
    session = core.add_message(
        session,
        "user",
        "Execute a shell command to write the text 'Kimi shell test' to a file named output.txt using echo and redirection.",
    )

    session, responses = core.send_request(session, config)
    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected a tool call"

    tool_name = tool_calls[0].get("function", {}).get("name")
    assert tool_name == "Shell"

    for tool_msg in core.execute_tool_calls(tool_calls, config):
        session = core.add_message(
            session,
            role=tool_msg["role"],
            content=tool_msg["content"],
            metadata=tool_msg.get("metadata"),
            config=config,
        )

    # Verify file was created with correct content
    assert target.exists(), "output.txt should have been created"
    assert "Kimi shell test" in target.read_text()