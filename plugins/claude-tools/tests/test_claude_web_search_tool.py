# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

# ruff: noqa: E402

import json
import sys
from pathlib import Path

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

from agent_core.tool_interop import (
    DEFAULT_TOOL_INTEROP_REGISTRY,
    compose_tool_interop_registry,
)
from agent_core.tool_result_payloads import FORMAT_ANTHROPIC_MESSAGES
from claude_tools import ClaudeWebSearchTool
from claude_tools.claude_web_search_tool import _filter_results
from tool_compat_shared import SearchResult


def _wrapper(tmp_path: Path, config: dict | None = None):
    tool = ClaudeWebSearchTool()
    state = tool.init({"working_directory": str(tmp_path), **(config or {})})
    return tool, state


def _fixture(name: str) -> dict:
    path = (
        Path(__file__).resolve().parents[1]
        / "investigation"
        / "fixtures"
        / "web-search"
        / f"{name}.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_matches_observed_fixture(tmp_path: Path) -> None:
    tool, state = _wrapper(
        tmp_path,
        {"web_search_enabled": True, "gemini_api_key": "gemini-test"},
    )
    assert tool.get_tool_schemas(state)[0] == _fixture("success-basic")["tool_schema"]


def test_ui_exposes_disabled_or_enabled_rich_toggle(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    tool = ClaudeWebSearchTool()

    disabled = tool.get_ui_elements({})[0]
    enabled = tool.get_ui_elements({"gemini_api_key": "gemini-test"})[0]

    assert disabled["disabled"] is True
    assert enabled["disabled"] is False
    assert enabled["icon"] == "globe"
    assert enabled["rich_ui"]["kind"] == "toggle"
    assert "icon" not in enabled["rich_ui"]
    assert enabled["rich_ui"]["options"][1]["tone"] == "success"


def test_anthropic_schema_converts_to_openai_chat_schema(tmp_path: Path) -> None:
    tool, state = _wrapper(
        tmp_path,
        {"web_search_enabled": True, "gemini_api_key": "gemini-test"},
    )
    schema = tool.get_tool_schemas(state)[0]
    registry = compose_tool_interop_registry(
        contributed=[tool.get_tool_interop_contribution(state)],
        defaults=DEFAULT_TOOL_INTEROP_REGISTRY,
    )
    converted = registry.convert_schemas(
        [schema],
        target_formats=["openai.chat_completions.function.tool_schema"],
    )[0]

    assert converted["type"] == "function"
    assert converted["function"]["name"] == "WebSearch"
    assert converted["function"]["parameters"] == schema["input_schema"]


def test_validation_error_matches_fixture(tmp_path: Path) -> None:
    tool, state = _wrapper(
        tmp_path,
        {"web_search_enabled": True, "gemini_api_key": "gemini-test"},
    )
    result = tool.execute_tool(
        "WebSearch",
        {"query": "x"},
        state,
        tool_call={"id": "call_web_search_1"},
    )

    expected = _fixture("error-query-too-short")["tool_result_message"]["content"][0]
    assert result["text"] == expected["content"]
    assert result["anthropic_content"][0]["is_error"] is True


def test_formats_claude_shaped_success_result(tmp_path: Path) -> None:
    tool, state = _wrapper(
        tmp_path,
        {"web_search_enabled": True, "gemini_api_key": "gemini-test"},
    )
    content = tool._format_content(
        query="example domain",
        summary="Example domains are reserved by IANA for documentation purposes.",
        results=[
            SearchResult(
                title="Example.com",
                url="https://en.wikipedia.org/wiki/Example_domain",
            ),
            SearchResult(
                title="RFC 2606: Reserved Top Level DNS Names",
                url="https://www.iankduncan.com/projects/rfc-browser/2606",
            ),
        ],
    )
    assert content.startswith(
        'Web search results for query: "example domain"\n\nLinks: ['
    )
    assert '"title":"Example.com"' in content
    assert "Example domains are reserved by IANA for documentation purposes." in content
    assert (
        "REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks."
        in content
    )
    result = tool._result(tool_use_id="call_web_search_1", text=content, success=True)
    formatted = tool.format_tool_result(result, state)
    assert formatted["format"] == FORMAT_ANTHROPIC_MESSAGES


def test_allowed_domains_are_enforced_in_formatted_links(tmp_path: Path) -> None:
    filtered = _filter_results(
        [
            SearchResult(
                title="Wikipedia",
                url="https://en.wikipedia.org/wiki/Example_domain",
            ),
            SearchResult(
                title="Other",
                url="https://example.org/info",
            ),
        ],
        allowed_domains=["wikipedia.org"],
        blocked_domains=[],
    )

    assert [item.url for item in filtered] == [
        "https://en.wikipedia.org/wiki/Example_domain"
    ]


def test_tavily_provider_can_be_selected(tmp_path: Path) -> None:
    tool, state = _wrapper(
        tmp_path,
        {
            "web_search_enabled": True,
            "web_search_provider": "tavily",
            "tavily_api_key": "tvly-test",
        },
    )

    provider = tool._provider(state)
    assert provider is not None
    assert provider.name == "Tavily"
