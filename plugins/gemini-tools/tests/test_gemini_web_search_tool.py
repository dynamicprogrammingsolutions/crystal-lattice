"""Unit tests for GeminiWebSearchTool.

Tests cover schema validation, UTF-8 byte-offset citation formatting,
result formatting, provider selection, conditional enabling,
and configuration.
"""

from __future__ import annotations

import os
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_core import AgentCore
from agent_core.plugin import ToolWrapper

from gemini_tools import GeminiWebSearchTool
from gemini_tools.gemini_web_search_tool import format_gemini_citations_utf8
from tool_compat_shared import (
    GeminiApiProvider,
    SearchProviderError,
    SearchResponse,
    SearchResult,
    TavilyProvider,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_wrapper(
    config: Dict[str, Any] = None,
    api_key: str = "test-gemini-key",
) -> tuple[ToolWrapper, Dict[str, Any]]:
    """Create a configured tool wrapper for testing."""
    wrapper = ToolWrapper(GeminiWebSearchTool)
    cfg = config or {}
    if api_key:
        cfg["gemini_api_key"] = api_key
    state = wrapper.init(cfg)
    return wrapper, state


# ---------------------------------------------------------------------------
# Schema Tests
# ---------------------------------------------------------------------------


class TestSchema:
    """Tests for tool schema matching Gemini CLI spec."""

    def test_tool_name_is_google_web_search(self) -> None:
        """Tool name in schema should be 'google_web_search'."""
        wrapper, state = _make_wrapper()
        schemas = wrapper.get_tool_schemas(state)
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "google_web_search"

    def test_query_is_required_parameter(self) -> None:
        """The 'query' parameter should be required."""
        wrapper, state = _make_wrapper()
        schemas = wrapper.get_tool_schemas(state)
        params = schemas[0]["function"]["parameters"]
        assert "query" in params["properties"]
        assert params["required"] == ["query"]

    def test_query_type_is_string(self) -> None:
        """The 'query' parameter should be type string."""
        wrapper, state = _make_wrapper()
        schemas = wrapper.get_tool_schemas(state)
        props = schemas[0]["function"]["parameters"]["properties"]
        assert props["query"]["type"] == "string"

    def test_description_matches_cli(self) -> None:
        """Description should match Gemini CLI's web search tool."""
        wrapper, state = _make_wrapper()
        schemas = wrapper.get_tool_schemas(state)
        desc = schemas[0]["function"]["description"]
        assert "web search" in desc.lower()
        assert "Google Search" in desc
        assert "Gemini API" in desc

    def test_no_provider_param(self) -> None:
        """Schema should have only 'query' parameter, not 'provider'."""
        wrapper, state = _make_wrapper()
        schemas = wrapper.get_tool_schemas(state)
        props = schemas[0]["function"]["parameters"]["properties"]
        assert list(props.keys()) == ["query"]

    def test_schema_type_is_function(self) -> None:
        """Schema type should be 'function'."""
        wrapper, state = _make_wrapper()
        schemas = wrapper.get_tool_schemas(state)
        assert schemas[0]["type"] == "function"


# ---------------------------------------------------------------------------
# UTF-8 Citation Formatting Tests
# ---------------------------------------------------------------------------


class TestCitationFormatting:
    """Tests for format_gemini_citations_utf8 function."""

    def test_basic_single_citation(self) -> None:
        """Single chunk, single support inserts [1] at byte offset."""
        text = "This is a test response."
        chunks = [
            {"web": {"uri": "https://example.com", "title": "Example Site"}}
        ]
        supports = [
            {
                "segment": {"startIndex": 0, "endIndex": 10},
                "groundingChunkIndices": [0],
            }
        ]
        result = format_gemini_citations_utf8(text, chunks, supports)
        # "This is a " is 10 bytes, then [1] inserted
        assert "[1]" in result
        assert "Example Site" in result
        assert "https://example.com" in result
        assert result.startswith("This is a [1]")
        assert "Sources:" in result
        assert "[1] Example Site (https://example.com)" in result

    def test_multiple_citations(self) -> None:
        """Multiple chunks and supports insert [1], [2], etc."""
        text = "First fact. Second fact."
        chunks = [
            {"web": {"uri": "https://example.com", "title": "Example"}},
            {"web": {"uri": "https://google.com", "title": "Google"}},
        ]
        supports = [
            {
                "segment": {"startIndex": 0, "endIndex": 11},
                "groundingChunkIndices": [0],
            },
            {
                "segment": {"startIndex": 12, "endIndex": 23},
                "groundingChunkIndices": [1],
            },
        ]
        result = format_gemini_citations_utf8(text, chunks, supports)
        assert "[1]" in result
        assert "[2]" in result
        assert "Sources:" in result
        assert "[1] Example (https://example.com)" in result
        assert "[2] Google (https://google.com)" in result

    def test_utf8_byte_offsets_multibyte(self) -> None:
        """Citation markers at UTF-8 byte positions for multi-byte chars.

        '日本語' is 3 characters but 9 bytes in UTF-8.
        If endIndex=9, the marker should be inserted after the full
        multibyte sequence, not in the middle.
        """
        text = "日本語 is Japanese"
        # '日本語' = 9 bytes, space = 1 byte
        # endIndex=9 means after '日本語'
        chunks = [
            {"web": {"uri": "https://example.com", "title": "Japanese"}}
        ]
        supports = [
            {
                "segment": {"startIndex": 0, "endIndex": 9},
                "groundingChunkIndices": [0],
            }
        ]
        result = format_gemini_citations_utf8(text, chunks, supports)
        # The [1] should appear right after 日本語, not in the middle
        assert "日本語[1]" in result
        assert "Sources:" in result

    def test_utf8_byte_offsets_emoji(self) -> None:
        """Citation markers at UTF-8 byte positions for emoji.

        '🎉' is 1 character but 4 bytes in UTF-8.
        """
        text = "Hello 🎉 world"
        # 'Hello ' = 6 bytes, '🎉' = 4 bytes → endIndex=10
        chunks = [
            {"web": {"uri": "https://example.com", "title": "Emoji"}}
        ]
        supports = [
            {
                "segment": {"startIndex": 0, "endIndex": 10},
                "groundingChunkIndices": [0],
            }
        ]
        result = format_gemini_citations_utf8(text, chunks, supports)
        assert "🎉[1]" in result

    def test_no_grounding(self) -> None:
        """No grounding chunks returns plain text."""
        text = "Just some text without grounding."
        result = format_gemini_citations_utf8(text, [], [])
        assert result == text

    def test_chunks_without_supports(self) -> None:
        """Chunks without supports appends source list only."""
        text = "Some grounded text."
        chunks = [
            {"web": {"uri": "https://example.com", "title": "Example"}},
        ]
        result = format_gemini_citations_utf8(text, chunks, [])
        # No inline markers, just text + Sources footer
        assert result.startswith("Some grounded text.")
        assert "Sources:" in result
        assert "[1] Example (https://example.com)" in result
        # No inline citation marker
        assert "[1] Example" not in result[:20]

    def test_multiple_chunk_indices_per_support(self) -> None:
        """Support referencing multiple chunks produces [1][2] marker."""
        text = "Overlapping claim."
        chunks = [
            {"web": {"uri": "https://a.com", "title": "A"}},
            {"web": {"uri": "https://b.com", "title": "B"}},
        ]
        supports = [
            {
                "segment": {"startIndex": 0, "endIndex": 18},
                "groundingChunkIndices": [0, 1],
            }
        ]
        result = format_gemini_citations_utf8(text, chunks, supports)
        assert "[1][2]" in result
        assert "Sources:" in result
        assert "[1] A (https://a.com)" in result
        assert "[2] B (https://b.com)" in result

    def test_chunks_not_in_supports_appear_in_footer(self) -> None:
        """Chunks not referenced by any support still appear in footer."""
        text = "Partial claim."
        chunks = [
            {"web": {"uri": "https://a.com", "title": "A"}},
            {"web": {"uri": "https://b.com", "title": "B"}},
        ]
        supports = [
            {
                "segment": {"startIndex": 0, "endIndex": 14},
                "groundingChunkIndices": [0],
            }
        ]
        result = format_gemini_citations_utf8(text, chunks, supports)
        assert "[1]" in result
        assert "[1] A (https://a.com)" in result
        assert "[2] B (https://b.com)" in result

    def test_result_format_matches_cli(self) -> None:
        """Full result format matches Gemini CLI output structure."""
        text = "This is a test response."
        chunks = [
            {"web": {"uri": "https://example.com", "title": "Example Site"}},
            {"web": {"uri": "https://google.com", "title": "Google"}},
        ]
        supports = [
            {
                "segment": {"startIndex": 0, "endIndex": 10},
                "groundingChunkIndices": [0],
            },
            {
                "segment": {"startIndex": 11, "endIndex": 24},
                "groundingChunkIndices": [1],
            },
        ]
        result = format_gemini_citations_utf8(text, chunks, supports)
        # Should have inline markers
        assert "[1]" in result.split("\n")[0]
        assert "[2]" in result.split("\n")[0]
        # Should have Sources footer
        lines = result.split("\n")
        assert "Sources:" in lines
        # Footer entries
        assert any("Example Site" in line and "https://example.com" in line for line in lines)
        assert any("Google" in line and "https://google.com" in line for line in lines)


# ---------------------------------------------------------------------------
# Result Format Tests
# ---------------------------------------------------------------------------


class TestResultFormat:
    """Tests for result formatting across backends."""

    def test_gemini_api_success_with_citations(self) -> None:
        """Gemini API backend returns Gemini-style result with citations."""
        wrapper, state = _make_wrapper(
            config={"web_search_enabled": True, "web_search_provider": "gemini_api"}
        )
        # Mock the provider
        mock_response = SearchResponse(
            results=[SearchResult(title="Example", url="https://example.com")],
            answer="This is grounded text.",
            query="test query",
            grounding_chunks=[
                {"web": {"uri": "https://example.com", "title": "Example"}}
            ],
            grounding_supports=[
                {
                    "segment": {"startIndex": 0, "endIndex": 10},
                    "groundingChunkIndices": [0],
                }
            ],
        )
        mock_provider = MagicMock(spec=GeminiApiProvider)
        mock_provider.search = AsyncMock(return_value=mock_response)
        state["providers"]["gemini_api"] = mock_provider

        result = wrapper.execute_tool(
            "google_web_search", {"query": "test query"}, state
        )

        assert result["success"] is True
        assert result["result"].startswith('Web search results for "test query":')
        assert "[1]" in result["result"]
        assert "Sources:" in result["result"]

    def test_tavily_success_without_citations(self) -> None:
        """Tavily backend returns Gemini-style result without inline citations."""
        wrapper, state = _make_wrapper(
            config={
                "web_search_enabled": True,
                "web_search_provider": "tavily",
                "tavily_api_key": "tvly-test",
            }
        )
        # Mock the provider
        mock_response = SearchResponse(
            results=[
                SearchResult(
                    title="Result 1",
                    url="https://example.com",
                    snippet="A snippet",
                ),
            ],
            answer="AI answer text",
            query="test query",
        )
        mock_provider = MagicMock(spec=TavilyProvider)
        mock_provider.search = AsyncMock(return_value=mock_response)
        state["providers"]["tavily"] = mock_provider

        result = wrapper.execute_tool(
            "google_web_search", {"query": "test query"}, state
        )

        assert result["success"] is True
        assert result["result"].startswith('Web search results for "test query":')
        assert "Sources:" in result["result"]
        assert "[1] Result 1 (https://example.com)" in result["result"]

    def test_no_results_format(self) -> None:
        """No results returns the Gemini CLI 'no results' message."""
        wrapper, state = _make_wrapper(
            config={"web_search_enabled": True, "web_search_provider": "gemini_api"}
        )
        mock_response = SearchResponse(
            results=[],
            answer="",
            query="no results query",
        )
        mock_provider = MagicMock(spec=GeminiApiProvider)
        mock_provider.search = AsyncMock(return_value=mock_response)
        state["providers"]["gemini_api"] = mock_provider

        result = wrapper.execute_tool(
            "google_web_search", {"query": "no results query"}, state
        )

        assert result["success"] is True
        assert (
            result["result"]
            == 'No search results or information found for query: "no results query"'
        )

    def test_error_format(self) -> None:
        """Error returns the Gemini CLI error message format."""
        wrapper, state = _make_wrapper(
            config={"web_search_enabled": True, "web_search_provider": "gemini_api"}
        )
        mock_provider = MagicMock(spec=GeminiApiProvider)
        mock_provider.search = AsyncMock(
            side_effect=SearchProviderError("Gemini API", "API error: 429")
        )
        state["providers"]["gemini_api"] = mock_provider

        result = wrapper.execute_tool(
            "google_web_search", {"query": "error query"}, state
        )

        assert result["success"] is False
        assert 'Error during web search for query "error query"' in result["error"]
        assert "429" in result["error"]


# ---------------------------------------------------------------------------
# Provider Selection Tests
# ---------------------------------------------------------------------------


class TestProviderSelection:
    """Tests for backend provider selection."""

    def test_default_with_gemini_key(self) -> None:
        """Default provider is gemini_api when Gemini key is present."""
        wrapper, state = _make_wrapper(
            config={"web_search_enabled": True}
        )
        assert state["provider_name"] == "gemini_api"
        assert "gemini_api" in state["providers"]

    def test_explicit_tavily(self) -> None:
        """Explicit tavily provider with Tavily key."""
        with patch.dict(os.environ, {}, clear=True):
            wrapper, state = _make_wrapper(
                config={
                    "web_search_enabled": True,
                    "web_search_provider": "tavily",
                    "tavily_api_key": "tvly-test",
                },
                api_key=None,
            )
        assert state["provider_name"] == "tavily"
        assert "tavily" in state["providers"]
        assert "gemini_api" not in state["providers"]

    def test_unavailable_provider_error(self) -> None:
        """Requesting unavailable provider returns error."""
        with patch.dict(os.environ, {}, clear=True):
            wrapper, state = _make_wrapper(
                config={
                    "web_search_enabled": True,
                    "web_search_provider": "tavily",
                },
                api_key=None,
            )
        # tavily not configured (no key), but provider_name is tavily
        assert "tavily" not in state["providers"]

        result = wrapper.execute_tool(
            "google_web_search", {"query": "test"}, state
        )
        assert result["success"] is False
        assert "not configured" in result["error"]

    def test_fallback_no_gemini_key_but_tavily(self) -> None:
        """When no Gemini key but Tavily key, tavily is available."""
        with patch.dict(os.environ, {}, clear=True):
            wrapper, state = _make_wrapper(
                config={
                    "web_search_enabled": True,
                    "web_search_provider": "tavily",
                    "tavily_api_key": "tvly-test",
                },
                api_key=None,
            )
        assert "tavily" in state["providers"]
        assert "gemini_api" not in state["providers"]


# ---------------------------------------------------------------------------
# Conditional Tests
# ---------------------------------------------------------------------------


class TestConditional:
    """Tests for conditional tool enabling.

    is_enabled controls tool visibility (UI + catalog), not execution.
    - Returns None (visible) when at least one provider key is present
    - Returns False (hidden) when no provider keys are configured
    - web_search_enabled only controls execution, not visibility
    """

    def test_visible_with_gemini_key_regardless_of_enabled_flag(self) -> None:
        """Tool is visible (None) with Gemini key even when not enabled."""
        wrapper = ToolWrapper(GeminiWebSearchTool)
        config = {"gemini_api_key": "test-key"}
        result = wrapper.is_enabled(config, [], [], {})
        assert result is None

    def test_visible_with_tavily_key_regardless_of_enabled_flag(self) -> None:
        """Tool is visible (None) with Tavily key even when not enabled."""
        wrapper = ToolWrapper(GeminiWebSearchTool)
        config = {"tavily_api_key": "tvly-test"}
        result = wrapper.is_enabled(config, [], [], {})
        assert result is None

    def test_visible_with_gemini_key_and_enabled(self) -> None:
        """Tool is visible (None) when enabled with Gemini key."""
        wrapper = ToolWrapper(GeminiWebSearchTool)
        config = {
            "web_search_enabled": True,
            "gemini_api_key": "test-key",
        }
        result = wrapper.is_enabled(config, [], [], {})
        assert result is None

    def test_hidden_without_any_key(self) -> None:
        """Tool is hidden (False) when no provider keys are configured."""
        wrapper = ToolWrapper(GeminiWebSearchTool)
        config = {}
        with patch.dict(os.environ, {}, clear=True):
            result = wrapper.is_enabled(config, [], [], {})
        assert result is False

    def test_hidden_with_enabled_but_no_key(self) -> None:
        """Tool is hidden (False) when enabled but no provider configured."""
        wrapper = ToolWrapper(GeminiWebSearchTool)
        config = {"web_search_enabled": True}
        with patch.dict(os.environ, {}, clear=True):
            result = wrapper.is_enabled(config, [], [], {})
        assert result is False

    def test_execute_when_disabled(self) -> None:
        """Executing when disabled returns error (visibility ≠ execution)."""
        wrapper, state = _make_wrapper(
            config={"web_search_enabled": False}
        )
        result = wrapper.execute_tool(
            "google_web_search", {"query": "test"}, state
        )
        assert result["success"] is False
        assert "disabled" in result["error"].lower()


# ---------------------------------------------------------------------------
# Config Schema Tests
# ---------------------------------------------------------------------------


class TestConfigSchema:
    """Tests for configuration schema."""

    def test_config_schema_has_enabled(self) -> None:
        """Config schema includes web_search_enabled."""
        tool = GeminiWebSearchTool()
        schema = tool.get_config_schema()
        assert "web_search_enabled" in schema
        assert schema["web_search_enabled"]["type"] == "boolean"
        assert schema["web_search_enabled"]["default"] is False

    def test_config_schema_has_provider(self) -> None:
        """Config schema includes web_search_provider."""
        tool = GeminiWebSearchTool()
        schema = tool.get_config_schema()
        assert "web_search_provider" in schema
        assert schema["web_search_provider"]["default"] == "gemini_api"

    def test_config_schema_has_tavily_key(self) -> None:
        """Config schema includes tavily_api_key."""
        tool = GeminiWebSearchTool()
        schema = tool.get_config_schema()
        assert "tavily_api_key" in schema

    def test_ui_uses_outer_fallback_icon_for_rich_toggle(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        tool = GeminiWebSearchTool()
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        disabled = tool.get_ui_elements({})[0]
        enabled = tool.get_ui_elements({"gemini_api_key": "test-key"})[0]

        for element in (disabled, enabled):
            assert element["icon"] == "globe"
            assert element["rich_ui"]["kind"] == "toggle"
            assert "icon" not in element["rich_ui"]

    def test_init_state_structure(self) -> None:
        """Init returns expected state structure."""
        wrapper, state = _make_wrapper(
            config={"web_search_enabled": True}
        )
        assert "enabled" in state
        assert "provider_name" in state
        assert "providers" in state
        assert "config" in state
        assert state["enabled"] is True
        assert state["provider_name"] == "gemini_api"


# ---------------------------------------------------------------------------
# Format Tool Result Tests
# ---------------------------------------------------------------------------


class TestFormatToolResult:
    """Tests for format_tool_result and to_display_format."""

    def test_format_success(self) -> None:
        """Success result returns the result text."""
        tool = GeminiWebSearchTool()
        result = {"success": True, "result": "Web search results..."}
        assert tool.format_tool_result(result, {}) == "Web search results..."

    def test_format_error(self) -> None:
        """Error result returns 'Error: ...' format."""
        tool = GeminiWebSearchTool()
        result = {"success": False, "error": "Something went wrong"}
        assert tool.format_tool_result(result, {}) == "Error: Something went wrong"

    def test_display_format(self) -> None:
        """Display format returns text type."""
        tool = GeminiWebSearchTool()
        result = {"success": True, "result": "content"}
        display = tool.to_display_format("content", result, {})
        assert display["type"] == "text"
        assert display["content"] == "content"


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------


class TestValidation:
    """Tests for input validation."""

    def test_empty_query(self) -> None:
        """Empty query returns error."""
        wrapper, state = _make_wrapper(
            config={"web_search_enabled": True}
        )
        result = wrapper.execute_tool(
            "google_web_search", {"query": ""}, state
        )
        assert result["success"] is False
        assert "cannot be empty" in result["error"]

    def test_whitespace_query(self) -> None:
        """Whitespace-only query returns error."""
        wrapper, state = _make_wrapper(
            config={"web_search_enabled": True}
        )
        result = wrapper.execute_tool(
            "google_web_search", {"query": "   "}, state
        )
        assert result["success"] is False
        assert "cannot be empty" in result["error"]

    def test_unknown_tool_name(self) -> None:
        """Unknown tool name returns error."""
        wrapper, state = _make_wrapper(
            config={"web_search_enabled": True}
        )
        result = wrapper.execute_tool(
            "wrong_tool_name", {"query": "test"}, state
        )
        assert result["success"] is False
        assert "Unknown tool" in result["error"]


# ---------------------------------------------------------------------------
# Shared Results Formatting Tests
# ---------------------------------------------------------------------------


class TestFormatSharedResults:
    """Tests for _format_shared_results method."""

    def test_basic_format(self) -> None:
        """Basic shared results formatting with snippet."""
        tool = GeminiWebSearchTool()
        results = [
            SearchResult(
                title="Example",
                url="https://example.com",
                snippet="A test snippet",
            ),
        ]
        formatted = tool._format_shared_results(results)
        assert "1. Example" in formatted
        assert "A test snippet" in formatted
        assert "Sources:" in formatted
        assert "[1] Example (https://example.com)" in formatted

    def test_no_snippet(self) -> None:
        """Results without snippet omit snippet line."""
        tool = GeminiWebSearchTool()
        results = [
            SearchResult(title="No Snippet", url="https://example.com"),
        ]
        formatted = tool._format_shared_results(results)
        assert "1. No Snippet" in formatted
        # No second line with snippet
        lines = formatted.split("\n")
        # Find the title line
        title_line_idx = next(i for i, l in enumerate(lines) if "No Snippet" in l)
        # Next line should be empty or Sources section
        assert "A test snippet" not in formatted

    def test_max_five_results(self) -> None:
        """Only top 5 results are included in content summary."""
        tool = GeminiWebSearchTool()
        results = [
            SearchResult(title=f"Result {i}", url=f"https://example.com/{i}")
            for i in range(7)
        ]
        formatted = tool._format_shared_results(results)
        # Content summary should only have 5 items
        content_section = formatted.split("Sources:")[0]
        assert "5. Result 4" in content_section
        assert "6. Result 5" not in content_section
        # Sources footer should have all 7
        sources_section = formatted.split("Sources:")[1]
        assert "[7] Result 6 (https://example.com/6)" in sources_section
