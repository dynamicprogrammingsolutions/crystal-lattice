"""Tests for KimiWebSearchTool."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from aiohttp import web
from dotenv import load_dotenv

from agent_core.plugin import ToolWrapper
from kimi_tools import KimiWebSearchTool
from tool_compat_shared import (
    GeminiApiProvider,
    SearchResponse,
    SearchResult,
    TavilyProvider,
)


load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")


def _make_wrapper(
    config: Dict[str, Any] | None = None,
) -> tuple[ToolWrapper, Dict[str, Any]]:
    wrapper = ToolWrapper(KimiWebSearchTool)
    state = wrapper.init(config or {})
    return wrapper, state


class TestSchema:
    def test_tool_name_is_search_web(self) -> None:
        wrapper, state = _make_wrapper(
            {"web_search_enabled": True, "gemini_api_key": "gemini-test"}
        )
        schemas = wrapper.get_tool_schemas(state)
        assert schemas[0]["function"]["name"] == "SearchWeb"

    def test_schema_matches_kimi_cli_parameters(self) -> None:
        wrapper, state = _make_wrapper(
            {"web_search_enabled": True, "gemini_api_key": "gemini-test"}
        )
        params = wrapper.get_tool_schemas(state)[0]["function"]["parameters"]
        props = params["properties"]

        assert params["required"] == ["query"]
        assert list(props.keys()) == ["query", "limit", "include_content"]
        assert props["query"]["type"] == "string"
        assert props["limit"]["default"] == 5
        assert props["limit"]["minimum"] == 1
        assert props["limit"]["maximum"] == 20
        assert props["include_content"]["default"] is False
        assert props["include_content"]["type"] == "boolean"

    def test_description_matches_kimi_cli(self) -> None:
        wrapper, state = _make_wrapper(
            {"web_search_enabled": True, "gemini_api_key": "gemini-test"}
        )
        desc = wrapper.get_tool_schemas(state)[0]["function"]["description"]
        assert desc == (
            "WebSearch tool allows you to search on the internet to get latest "
            "information, including news, documents, release notes, blog posts, "
            "papers, etc."
        )

    def test_schema_has_no_provider_parameter(self) -> None:
        wrapper, state = _make_wrapper(
            {"web_search_enabled": True, "gemini_api_key": "gemini-test"}
        )
        props = wrapper.get_tool_schemas(state)[0]["function"]["parameters"][
            "properties"
        ]
        assert "provider" not in props


class TestConfigAndVisibility:
    def test_config_schema_defaults_disabled(self) -> None:
        tool = KimiWebSearchTool()
        schema = tool.get_config_schema()
        assert schema["web_search_enabled"]["default"] is False
        assert schema["web_search_provider"]["default"] == "moonshot"
        assert "tavily_api_key" in schema
        assert "gemini_api_key" in schema

    def test_plugin_visible_when_disabled(self) -> None:
        wrapper = ToolWrapper(KimiWebSearchTool)
        config = {"tavily_api_key": "tvly-test"}
        assert wrapper.is_enabled(config, [], [], {}) is None

    def test_plugin_visible_when_no_provider_so_ui_can_explain(self) -> None:
        wrapper = ToolWrapper(KimiWebSearchTool)
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("TAVILY_API_KEY", raising=False)
            mp.delenv("GEMINI_API_KEY", raising=False)
            assert wrapper.is_enabled({"web_search_enabled": True}, [], [], {}) is None

    def test_is_enabled_visible_when_enabled_with_provider(self) -> None:
        wrapper = ToolWrapper(KimiWebSearchTool)
        config = {"web_search_enabled": True, "tavily_api_key": "tvly-test"}
        assert wrapper.is_enabled(config, [], [], {}) is None

    def test_ui_explains_missing_provider(self) -> None:
        tool = KimiWebSearchTool()
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("TAVILY_API_KEY", raising=False)
            mp.delenv("GEMINI_API_KEY", raising=False)
            elements = tool.get_ui_elements({})
        assert elements[0]["key"] == "web_search_enabled"
        assert elements[0]["disabled"] is True
        assert elements[0]["icon"] == "globe"
        assert "GEMINI_API_KEY" in elements[0]["description"]
        assert elements[0]["rich_ui"]["kind"] == "toggle"
        assert "icon" not in elements[0]["rich_ui"]
        assert elements[0]["rich_ui"]["options"][0]["tone"] == "primary"

    def test_ui_shows_provider_select_when_multiple_providers_configured(self) -> None:
        tool = KimiWebSearchTool()
        elements = tool.get_ui_elements(
            {
                "gemini_api_key": "gemini-test",
                "tavily_api_key": "tvly-test",
            }
        )

        provider = next(el for el in elements if el.get("key") == "web_search_provider")
        option_values = [option["value"] for option in provider["options"]]
        assert option_values == ["tavily", "gemini_api"]

    def test_schema_empty_when_disabled(self) -> None:
        wrapper, state = _make_wrapper({"tavily_api_key": "tvly-test"})
        assert wrapper.get_tool_schemas(state) == []

    def test_schema_empty_when_enabled_without_provider(self) -> None:
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("TAVILY_API_KEY", raising=False)
            mp.delenv("GEMINI_API_KEY", raising=False)
            wrapper, state = _make_wrapper({"web_search_enabled": True})
        assert wrapper.get_tool_schemas(state) == []

    def test_schema_present_when_enabled_with_provider(self) -> None:
        wrapper, state = _make_wrapper(
            {"web_search_enabled": True, "gemini_api_key": "gemini-test"}
        )
        assert wrapper.get_tool_schemas(state)[0]["function"]["name"] == "SearchWeb"

    def test_execute_when_disabled(self) -> None:
        wrapper, state = _make_wrapper({"tavily_api_key": "tvly-test"})
        result = wrapper.execute_tool("SearchWeb", {"query": "test"}, state)
        assert result["success"] is False
        assert "disabled" in result["error"].lower()

    def test_execute_enabled_without_provider(self) -> None:
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("TAVILY_API_KEY", raising=False)
            mp.delenv("GEMINI_API_KEY", raising=False)
            wrapper, state = _make_wrapper({"web_search_enabled": True})

        result = wrapper.execute_tool("SearchWeb", {"query": "test"}, state)
        assert result["success"] is False
        assert "Search service is not configured" in result["error"]


class TestProviderSelection:
    def test_default_selects_moonshot_when_configured(self) -> None:
        config = {
            "web_search_enabled": True,
            "services": {
                "moonshot_search": {
                    "base_url": "https://search.example",
                    "api_key": "test-key",
                }
            },
        }
        _wrapper, state = _make_wrapper(config)
        assert state["provider_name"] == "moonshot"
        assert "moonshot" in state["providers"]

    def test_default_falls_back_to_tavily(self) -> None:
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("GEMINI_API_KEY", raising=False)
            _wrapper, state = _make_wrapper(
                {"web_search_enabled": True, "tavily_api_key": "tvly-test"}
            )
        assert state["provider_name"] == "tavily"
        assert isinstance(state["providers"]["tavily"], TavilyProvider)

    def test_explicit_gemini_provider(self) -> None:
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("TAVILY_API_KEY", raising=False)
            _wrapper, state = _make_wrapper(
                {
                    "web_search_enabled": True,
                    "web_search_provider": "gemini_api",
                    "gemini_api_key": "gemini-test",
                }
            )
        assert state["provider_name"] == "gemini_api"
        assert isinstance(state["providers"]["gemini_api"], GeminiApiProvider)

    def test_unavailable_explicit_provider_errors(self) -> None:
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("TAVILY_API_KEY", raising=False)
            mp.delenv("GEMINI_API_KEY", raising=False)
            wrapper, state = _make_wrapper(
                {
                    "web_search_enabled": True,
                    "web_search_provider": "tavily",
                    "services": {
                        "moonshot_search": {
                            "base_url": "https://search.example",
                            "api_key": "test-key",
                        }
                    },
                }
            )
        result = wrapper.execute_tool("SearchWeb", {"query": "test"}, state)
        assert result["success"] is False
        assert "not configured" in result["error"]


class TestValidation:
    def test_unknown_tool_name(self) -> None:
        wrapper, state = _make_wrapper(
            {"web_search_enabled": True, "tavily_api_key": "tvly-test"}
        )
        result = wrapper.execute_tool("WrongTool", {"query": "test"}, state)
        assert result["success"] is False
        assert "Unknown tool" in result["error"]

    def test_empty_query(self) -> None:
        wrapper, state = _make_wrapper(
            {"web_search_enabled": True, "tavily_api_key": "tvly-test"}
        )
        result = wrapper.execute_tool("SearchWeb", {"query": "   "}, state)
        assert result["success"] is False
        assert "cannot be empty" in result["error"]

    def test_invalid_limit(self) -> None:
        wrapper, state = _make_wrapper(
            {"web_search_enabled": True, "tavily_api_key": "tvly-test"}
        )
        result = wrapper.execute_tool(
            "SearchWeb", {"query": "test", "limit": 21}, state
        )
        assert result["success"] is False
        assert "between 1 and 20" in result["error"]


class TestKimiFormatting:
    def test_formats_single_result(self) -> None:
        tool = KimiWebSearchTool()
        formatted = tool._format_kimi_results(
            [
                SearchResult(
                    title="Title A",
                    date="2026-01-01",
                    url="https://example.com/a",
                    snippet="Summary A",
                )
            ]
        )
        assert formatted == (
            "Title: Title A\n"
            "Date: 2026-01-01\n"
            "URL: https://example.com/a\n"
            "Summary: Summary A\n\n"
        )

    def test_formats_content_and_separator(self) -> None:
        tool = KimiWebSearchTool()
        formatted = tool._format_kimi_results(
            [
                SearchResult(
                    title="Title A",
                    url="https://example.com/a",
                    snippet="Summary A",
                    content="Full content A",
                ),
                SearchResult(
                    title="Title B",
                    url="https://example.com/b",
                    snippet="Summary B",
                ),
            ]
        )
        assert "Full content A\n\n---\n\nTitle: Title B" in formatted
        assert formatted.count("---\n\n") == 1


class TestSharedProviders:
    def test_tavily_success_formats_kimi_style(self) -> None:
        wrapper, state = _make_wrapper(
            {
                "web_search_enabled": True,
                "web_search_provider": "tavily",
                "tavily_api_key": "tvly-test",
            }
        )
        mock_provider = MagicMock(spec=TavilyProvider)
        mock_provider.search = AsyncMock(
            return_value=SearchResponse(
                results=[
                    SearchResult(
                        title="Tavily Result",
                        url="https://example.com",
                        content="Tavily content",
                        date="2026-01-02",
                    )
                ],
                query="test",
            )
        )
        state["providers"]["tavily"] = mock_provider

        result = wrapper.execute_tool("SearchWeb", {"query": "test", "limit": 2}, state)
        assert result["success"] is True
        assert "Title: Tavily Result" in result["result"]
        assert "Summary: " in result["result"]
        assert "Tavily content" in result["result"]
        mock_provider.search.assert_awaited_once_with("test", limit=2)

    def test_gemini_success_formats_sources_as_kimi_results(self) -> None:
        wrapper, state = _make_wrapper(
            {
                "web_search_enabled": True,
                "web_search_provider": "gemini_api",
                "gemini_api_key": "gemini-test",
            }
        )
        mock_provider = MagicMock(spec=GeminiApiProvider)
        mock_provider.search = AsyncMock(
            return_value=SearchResponse(
                results=[
                    SearchResult(title="Gemini Source", url="https://example.com")
                ],
                answer="Grounded answer",
                query="test",
            )
        )
        state["providers"]["gemini_api"] = mock_provider

        result = wrapper.execute_tool("SearchWeb", {"query": "test"}, state)
        assert result["success"] is True
        assert "Title: Gemini Source" in result["result"]
        assert "Date: " in result["result"]
        assert "Summary: " in result["result"]

    def test_no_results(self) -> None:
        wrapper, state = _make_wrapper(
            {
                "web_search_enabled": True,
                "web_search_provider": "tavily",
                "tavily_api_key": "tvly-test",
            }
        )
        mock_provider = MagicMock(spec=TavilyProvider)
        mock_provider.search = AsyncMock(return_value=SearchResponse(results=[]))
        state["providers"]["tavily"] = mock_provider

        result = wrapper.execute_tool("SearchWeb", {"query": "empty"}, state)
        assert result == {"success": True, "result": "No matches found"}


@pytest_asyncio.fixture
async def mock_moonshot_server(aiohttp_server):
    captured: Dict[str, Any] = {}

    async def search_handler(request):
        captured["headers"] = dict(request.headers)
        captured["body"] = await request.json()
        if request.headers.get("Authorization") != "Bearer test-key":
            return web.Response(status=401, text="Unauthorized")
        return web.json_response(
            {
                "search_results": [
                    {
                        "site_name": "Example",
                        "title": "Moonshot Result",
                        "url": "https://example.com/moonshot",
                        "snippet": "Moonshot summary",
                        "content": "Moonshot page content",
                        "date": "2026-01-03",
                    }
                ]
            }
        )

    async def error_handler(request):
        return web.Response(status=503, text="Unavailable")

    async def invalid_json_handler(request):
        return web.Response(status=200, text="not json")

    app = web.Application()
    app["captured"] = captured
    app.router.add_post("/search", search_handler)
    app.router.add_post("/error", error_handler)
    app.router.add_post("/invalid", invalid_json_handler)
    server = await aiohttp_server(app)
    server.captured = captured
    return server


class TestMoonshotBackend:
    @pytest.mark.asyncio
    async def test_moonshot_request_body_headers_and_format(
        self, mock_moonshot_server
    ) -> None:
        tool = KimiWebSearchTool()
        state = tool.init(
            {
                "web_search_enabled": True,
                "services": {
                    "moonshot_search": {
                        "base_url": str(mock_moonshot_server.make_url("/search")),
                        "api_key": "test-key",
                        "custom_headers": {"X-Custom": "custom"},
                    }
                },
            }
        )

        result = await tool._execute_async(
            {"query": "kimi search", "limit": 7, "include_content": True},
            state,
            tool_call={"id": "call_123"},
        )

        assert result["success"] is True
        assert "Title: Moonshot Result" in result["result"]
        assert "Moonshot page content" in result["result"]
        assert mock_moonshot_server.captured["body"] == {
            "text_query": "kimi search",
            "limit": 7,
            "enable_page_crawling": True,
            "timeout_seconds": 30,
        }
        headers = mock_moonshot_server.captured["headers"]
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["X-Msh-Tool-Call-Id"] == "call_123"
        assert headers["X-Custom"] == "custom"

    @pytest.mark.asyncio
    async def test_moonshot_status_error(self, mock_moonshot_server) -> None:
        tool = KimiWebSearchTool()
        state = tool.init(
            {
                "web_search_enabled": True,
                "services": {
                    "moonshot_search": {
                        "base_url": str(mock_moonshot_server.make_url("/error")),
                        "api_key": "test-key",
                    }
                },
            }
        )
        result = await tool._execute_async({"query": "test"}, state)
        assert result["success"] is False
        assert "Status: 503" in result["error"]

    @pytest.mark.asyncio
    async def test_moonshot_parse_error(self, mock_moonshot_server) -> None:
        tool = KimiWebSearchTool()
        state = tool.init(
            {
                "web_search_enabled": True,
                "services": {
                    "moonshot_search": {
                        "base_url": str(mock_moonshot_server.make_url("/invalid")),
                        "api_key": "test-key",
                    }
                },
            }
        )
        result = await tool._execute_async({"query": "test"}, state)
        assert result["success"] is False
        assert "Failed to parse search results" in result["error"]


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("TAVILY_API_KEY"),
    reason="TAVILY_API_KEY not set",
)
def test_real_tavily_backend_formats_kimi_results() -> None:
    wrapper, state = _make_wrapper(
        {
            "web_search_enabled": True,
            "web_search_provider": "tavily",
            "tavily_api_key": os.environ["TAVILY_API_KEY"],
        }
    )

    result = wrapper.execute_tool(
        "SearchWeb",
        {"query": "Python programming language official website", "limit": 3},
        state,
    )

    assert result["success"] is True
    assert "Title: " in result["result"]
    assert "URL: " in result["result"]
    assert "Summary: " in result["result"]


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set",
)
def test_real_gemini_backend_formats_kimi_results() -> None:
    wrapper, state = _make_wrapper(
        {
            "web_search_enabled": True,
            "web_search_provider": "gemini_api",
            "gemini_api_key": os.environ["GEMINI_API_KEY"],
        }
    )

    result = wrapper.execute_tool(
        "SearchWeb",
        {"query": "Python programming language official website", "limit": 3},
        state,
    )

    if not result["success"] and "google-genai SDK not installed" in result["error"]:
        pytest.skip("google-genai SDK not installed")

    assert result["success"] is True
    assert "Title: " in result["result"]
    assert "URL: " in result["result"]
    assert "Date: " in result["result"]
    assert "Summary: " in result["result"]
