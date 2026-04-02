"""OpenRouter integration test for QwenShellTool."""

from __future__ import annotations

import os

import pytest

from agent_core import AgentCore

from qwen_tools import QwenShellTool


MODEL = os.getenv("OPENROUTER_MODEL_QWEN_TOOLS", "qwen/qwen3.5-flash-02-23")


@pytest.mark.integration
@pytest.mark.openrouter
def test_qwen_shell_tool_via_openrouter(tmp_path):
    """Test that Qwen uses bash tool correctly."""
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
    core.register_tool(QwenShellTool)

    config = {
        "model": MODEL,
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "working_directory": str(tmp_path),
        "workspace_dirs": [str(tmp_path)],
        "project_temp_dir": str(tmp_path / ".temp"),
        "global_temp_dir": str(tmp_path / ".temp-global"),
        "user_skills_dir": str(tmp_path / ".skills"),
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "Use the bash tool when a shell command is needed. Do not answer from memory.",
    )
    session = core.add_message(
        session,
        "user",
        "Use bash to write 'Qwen shell test' to output.txt, then reply with exactly OK.",
    )

    session, responses = core.send_request(session, config)
    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected a tool call"

    tool_name = tool_calls[0].get("function", {}).get("name")
    assert tool_name == "bash"

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

    assert target.exists(), "output.txt should have been created"
    assert "Qwen shell test" in target.read_text()
    assert "OK" in final_text