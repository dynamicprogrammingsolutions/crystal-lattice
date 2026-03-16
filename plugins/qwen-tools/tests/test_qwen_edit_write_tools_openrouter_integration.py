from __future__ import annotations

import os

import pytest

from agent_core import AgentCore

from qwen_tools import QwenEditTool, QwenWriteFileTool


MODEL = os.getenv("OPENROUTER_MODEL_QWEN_TOOLS", "qwen/qwen3.5-flash-02-23")


def _run_tool_loop(core: AgentCore, session, config: dict, max_rounds: int = 6):
    for _ in range(max_rounds):
        session, responses = core.send_request(session, config)
        tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
        if not tool_calls:
            return session, responses
        for tool_msg in core.execute_tool_calls(tool_calls, config):
            session = core.add_message(
                session,
                role=tool_msg["role"],
                content=tool_msg["content"],
                metadata=tool_msg.get("metadata"),
                config=config,
            )
    raise AssertionError("tool loop did not converge")


def _final_ok_text(response: dict) -> str:
    text = (response.get("content") or "").strip()
    if text:
        return text
    metadata = response.get("metadata") or {}
    reasoning = metadata.get("reasoning")
    return str(reasoning or "").strip()


@pytest.mark.integration
@pytest.mark.openrouter
def test_qwen_edit_write_tools_via_openrouter(tmp_path):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    target = tmp_path / "note.txt"
    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(QwenWriteFileTool)
    core.register_tool(QwenEditTool)

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
    session = core.add_message(session, "system", "Use write_file and edit tools when instructed. Reply with OK only after the file is correct.")
    session = core.add_message(
        session,
        "user",
        f"Use write_file to create the file at absolute path {target} with the exact content 'alpha\n'. Then use edit to change alpha to beta. Reply with OK only.",
    )

    _session, responses = _run_tool_loop(core, session, config)
    assert target.read_text(encoding="utf-8") == "beta\n"
    assert "OK" in _final_ok_text(responses[-1]).split()