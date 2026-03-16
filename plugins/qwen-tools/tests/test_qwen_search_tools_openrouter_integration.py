from __future__ import annotations

import os

import pytest

from agent_core import AgentCore

from qwen_tools import QwenGlobTool, QwenGrepSearchTool, QwenListDirectoryTool


MODEL = os.getenv("OPENROUTER_MODEL_QWEN_TOOLS", "qwen/qwen3.5-flash-02-23")


def _run_tool_loop(core: AgentCore, session, config: dict, max_rounds: int = 8):
    seen_tools: list[str] = []
    for _ in range(max_rounds):
        session, responses = core.send_request(session, config)
        tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
        if not tool_calls:
            return session, responses, seen_tools
        seen_tools.extend(call.get("function", {}).get("name") for call in tool_calls)
        for tool_msg in core.execute_tool_calls(tool_calls, config):
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
def test_qwen_search_tools_via_openrouter(tmp_path):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    src = tmp_path / "src"
    src.mkdir()
    (src / "alpha.txt").write_text("NEEDLE_42\n", encoding="utf-8")
    (src / "beta.py").write_text("print('hi')\n", encoding="utf-8")

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(QwenListDirectoryTool)
    core.register_tool(QwenGlobTool)
    core.register_tool(QwenGrepSearchTool)

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
        "When the user explicitly names required tools, call each named tool before answering. Use only the provided tools and reply with exactly OK after all required tools have been called.",
    )
    session = core.add_message(
        session,
        "user",
        f"Use list_directory on absolute path {src}, then use glob with pattern '*.txt' in src, then use grep_search for pattern 'NEEDLE_42' in src. Reply with exactly OK after all three tools have been used.",
    )

    _session, responses, seen_tools = _run_tool_loop(core, session, config)
    assert {"list_directory", "glob", "grep_search"}.issubset(set(seen_tools))
    assert (responses[-1].get("content") or "").strip() == "OK"
