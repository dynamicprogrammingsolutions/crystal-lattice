from __future__ import annotations

# ruff: noqa: E402

import json
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[3]
CORE_PY = ROOT / "core/python"
PLUGIN_SRC = ROOT / "plugins/claude-tools/src"
SHARED_SRC = ROOT / "plugins/tool-compat-shared/src"
FETCH_SRC = ROOT / "plugins/web-fetch-shared/src"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
if str(PLUGIN_SRC) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SRC))
if str(SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(SHARED_SRC))
if str(FETCH_SRC) not in sys.path:
    sys.path.insert(0, str(FETCH_SRC))

from agent_core import AgentCore
from claude_tools import ClaudeWebSearchTool


load_dotenv(ROOT / ".env")


def _execute_messages(tmp_path: Path, config: dict, calls: list[dict]) -> list[dict]:
    core = AgentCore()
    core.register_tool(ClaudeWebSearchTool)
    return list(
        core.iter_tool_messages(
            calls,
            {"working_directory": str(tmp_path), **config},
        )
    )


@pytest.mark.integration
def test_real_gemini_backend_formats_claude_web_search(tmp_path: Path) -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set; skipping Gemini-backed Claude web search test")

    messages = _execute_messages(
        tmp_path,
        {
            "web_search_enabled": True,
            "web_search_provider": "gemini_api",
            "gemini_api_key": api_key,
        },
        [
            {
                "id": "call_web_search_1",
                "type": "function",
                "function": {
                    "name": "WebSearch",
                    "arguments": json.dumps({"query": "example domain"}),
                },
            }
        ],
    )

    assert messages
    content = messages[0]["content"]
    assert 'Web search results for query: "example domain"' in content
    assert "Links: [" in content
    assert "REMINDER: You MUST include the sources above" in content


@pytest.mark.integration
def test_real_tavily_backend_formats_claude_web_search(tmp_path: Path) -> None:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        pytest.skip("TAVILY_API_KEY not set; skipping Tavily-backed Claude web search test")

    messages = _execute_messages(
        tmp_path,
        {
            "web_search_enabled": True,
            "web_search_provider": "tavily",
            "tavily_api_key": api_key,
        },
        [
            {
                "id": "call_web_search_1",
                "type": "function",
                "function": {
                    "name": "WebSearch",
                    "arguments": json.dumps({"query": "example domain"}),
                },
            }
        ],
    )

    assert messages
    content = messages[0]["content"]
    assert 'Web search results for query: "example domain"' in content
    assert "Links: [" in content
    assert "REMINDER: You MUST include the sources above" in content