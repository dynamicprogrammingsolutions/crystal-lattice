"""Unit tests for KimiFetchURLTool.

Tests cover schema validation, Moonshot service integration,
local fetch behavior, trafilatura extraction, and error handling.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_core import AgentCore
from agent_core.plugin import ToolWrapper

from kimi_tools import KimiFetchURLTool


def _make_tool(
    config: Dict[str, Any] = None,
) -> tuple[KimiFetchURLTool, Dict[str, Any]]:
    """Create a configured tool for testing."""
    tool = KimiFetchURLTool()
    cfg = config or {}
    state = tool.init(cfg)
    return tool, state


def _make_wrapper(
    config: Dict[str, Any] = None,
) -> tuple[ToolWrapper, Dict[str, Any]]:
    """Create a configured tool wrapper for testing."""
    wrapper = ToolWrapper(KimiFetchURLTool)
    cfg = config or {}
    state = wrapper.init(cfg)
    return wrapper, state


class TestSchema:
    """Tests for tool schema matching Kimi CLI spec."""

    def test_tool_name_is_fetch_url_pascal_case(self, tmp_path: Path) -> None:
        """Tool name in schema should be 'FetchURL' (PascalCase)."""
        tool, state = _make_tool()
        schemas = tool.get_tool_schemas(state)
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "FetchURL"

    def test_url_is_required_parameter(self, tmp_path: Path) -> None:
        """The 'url' parameter should be required."""
        tool, state = _make_tool()
        schemas = tool.get_tool_schemas(state)
        params = schemas[0]["function"]["parameters"]
        assert "url" in params["properties"]
        assert params["required"] == ["url"]

    def test_description_matches_kimi_cli(self, tmp_path: Path) -> None:
        """Description should match Kimi CLI description."""
        tool, state = _make_tool()
        schemas = tool.get_tool_schemas(state)
        desc = schemas[0]["function"]["description"]
        assert "fetch" in desc.lower()
        assert "extract" in desc.lower()


class TestInitialization:
    """Tests for tool initialization."""

    def test_init_without_moonshot_config(self, tmp_path: Path) -> None:
        """Should initialize without Moonshot service config when disabled."""
        tool, state = _make_tool()
        assert state["moonshot_config"] is None
        assert state["fetch_config"]["timeout_seconds"] == 10
        assert state["fetch_config"]["max_chars"] == 50000

    def test_init_with_moonshot_enabled(self, tmp_path: Path) -> None:
        """Should initialize with Moonshot service config when enabled with API key."""
        config = {
            "moonshot_enabled": True,
            "moonshot_api_key": "test-key",
        }
        tool, state = _make_tool(config)
        assert state["moonshot_config"] is not None
        assert state["moonshot_config"]["base_url"] == "https://api.kimi.com/coding/v1/fetch"

    def test_init_disabled_even_with_api_key(self, tmp_path: Path) -> None:
        """Should NOT use service when disabled even with API key set."""
        config = {
            "moonshot_enabled": False,
            "moonshot_api_key": "test-key",
        }
        tool, state = _make_tool(config)
        assert state["moonshot_config"] is None

    def test_init_requires_api_key_when_enabled(self, tmp_path: Path) -> None:
        """Should NOT use service when enabled but no API key."""
        config = {
            "moonshot_enabled": True,
        }
        tool, state = _make_tool(config)
        assert state["moonshot_config"] is None

    def test_init_with_custom_timeout(self, tmp_path: Path) -> None:
        """Should use custom timeout from config."""
        config = {"web_fetch_timeout_seconds": 30}
        tool, state = _make_tool(config)
        assert state["fetch_config"]["timeout_seconds"] == 30

    def test_init_with_custom_max_chars(self, tmp_path: Path) -> None:
        """Should use custom max_chars from config."""
        config = {"web_fetch_max_chars": 100000}
        tool, state = _make_tool(config)
        assert state["fetch_config"]["max_chars"] == 100000

    def test_init_with_custom_base_url(self, tmp_path: Path) -> None:
        """Should use custom base_url when enabled."""
        config = {
            "moonshot_enabled": True,
            "moonshot_api_key": "test-key",
            "moonshot_base_url": "https://custom.moonshot.url/fetch",
        }
        tool, state = _make_tool(config)
        assert state["moonshot_config"]["base_url"] == "https://custom.moonshot.url/fetch"


class TestURLValidation:
    """Tests for URL validation."""

    def test_validates_missing_url(self, tmp_path: Path) -> None:
        """Should fail when URL is missing."""
        tool, state = _make_tool()
        result = tool.execute_tool("FetchURL", {}, state)
        assert result["success"] is False
        assert "required" in result["error"].lower()

    def test_validates_empty_url(self, tmp_path: Path) -> None:
        """Should fail when URL is empty."""
        tool, state = _make_tool()
        result = tool.execute_tool("FetchURL", {"url": ""}, state)
        assert result["success"] is False
        assert "required" in result["error"].lower()

    def test_validates_unsupported_protocol(self, tmp_path: Path) -> None:
        """Should fail for non-http(s) URLs."""
        tool, state = _make_tool()
        result = tool.execute_tool("FetchURL", {"url": "ftp://example.com"}, state)
        assert result["success"] is False
        assert "unsupported" in result["error"].lower()

    def test_validates_missing_hostname(self, tmp_path: Path) -> None:
        """Should fail for URLs without hostname."""
        tool, state = _make_tool()
        result = tool.execute_tool("FetchURL", {"url": "https://"}, state)
        assert result["success"] is False
        assert "hostname" in result["error"].lower()


class TestLocalFetch:
    """Tests for local HTTP fetch path."""

    def test_fetch_text_plain_passthrough(self, tmp_path: Path) -> None:
        """text/plain content should be returned as-is."""
        from web_fetch_shared import FetchResult

        mock_result = FetchResult(
            content="Plain text content",
            content_type="text/plain",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch(
            "kimi_tools.kimi_fetch_url_tool.fetch_url",
            return_value=mock_result,
        ):
            tool, state = _make_tool()
            result = tool.execute_tool(
                "FetchURL",
                {"url": "https://example.com/file.txt"},
                state,
            )

        assert result["success"] is True
        assert result["result"] == "Plain text content"
        assert "full content" in result["message"]

    def test_fetch_text_markdown_passthrough(self, tmp_path: Path) -> None:
        """text/markdown content should be returned as-is."""
        from web_fetch_shared import FetchResult

        mock_result = FetchResult(
            content="# Title\n\nMarkdown content",
            content_type="text/markdown",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch(
            "kimi_tools.kimi_fetch_url_tool.fetch_url",
            return_value=mock_result,
        ):
            tool, state = _make_tool()
            result = tool.execute_tool(
                "FetchURL",
                {"url": "https://example.com/file.md"},
                state,
            )

        assert result["success"] is True
        assert "# Title" in result["result"]
        assert "full content" in result["message"]

    def test_fetch_html_extraction(self, tmp_path: Path) -> None:
        """HTML content should be extracted with trafilatura."""
        from web_fetch_shared import FetchResult

        mock_result = FetchResult(
            content="<html><body><h1>Test</h1><p>Content</p></body></html>",
            content_type="text/html",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch(
            "kimi_tools.kimi_fetch_url_tool.fetch_url",
            return_value=mock_result,
        ):
            with patch.object(
                KimiFetchURLTool,
                "_extract_with_trafilatura",
                return_value="Extracted content",
            ):
                tool, state = _make_tool()
                result = tool.execute_tool(
                    "FetchURL",
                    {"url": "https://example.com"},
                    state,
                )

        assert result["success"] is True
        assert result["result"] == "Extracted content"
        assert "main text content" in result["message"]

    def test_fetch_empty_response(self, tmp_path: Path) -> None:
        """Empty response should return empty message."""
        from web_fetch_shared import FetchResult

        mock_result = FetchResult(
            content="",
            content_type="text/html",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch(
            "kimi_tools.kimi_fetch_url_tool.fetch_url",
            return_value=mock_result,
        ):
            tool, state = _make_tool()
            result = tool.execute_tool(
                "FetchURL",
                {"url": "https://example.com"},
                state,
            )

        assert result["success"] is True
        assert result["result"] == ""
        assert "empty" in result["message"].lower()

    def test_fetch_extraction_failure(self, tmp_path: Path) -> None:
        """Failed extraction should return error."""
        from web_fetch_shared import FetchResult

        mock_result = FetchResult(
            content="<html><body></body></html>",
            content_type="text/html",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch(
            "kimi_tools.kimi_fetch_url_tool.fetch_url",
            return_value=mock_result,
        ):
            with patch.object(
                KimiFetchURLTool,
                "_extract_with_trafilatura",
                return_value="",
            ):
                tool, state = _make_tool()
                result = tool.execute_tool(
                    "FetchURL",
                    {"url": "https://example.com"},
                    state,
                )

        assert result["success"] is False
        assert "Failed to extract" in result["error"]

    def test_fetch_http_error(self, tmp_path: Path) -> None:
        """HTTP error should return appropriate error message."""
        from web_fetch_shared import FetchResult

        mock_result = FetchResult(
            content="",
            content_type="text/plain",
            status_code=404,
            headers={},
            url="https://example.com",
            is_error=True,
            error_message="HTTP 404",
        )

        with patch(
            "kimi_tools.kimi_fetch_url_tool.fetch_url",
            return_value=mock_result,
        ):
            tool, state = _make_tool()
            result = tool.execute_tool(
                "FetchURL",
                {"url": "https://example.com/notfound"},
                state,
            )

        assert result["success"] is False
        assert "404" in result["error"]
        assert "not accessible" in result["error"]

    def test_fetch_network_error(self, tmp_path: Path) -> None:
        """Network error should return appropriate error message."""
        from web_fetch_shared import FetchResult

        mock_result = FetchResult(
            content="",
            content_type="",
            status_code=0,
            headers={},
            url="https://example.com",
            is_error=True,
            error_message="Connection refused",
        )

        with patch(
            "kimi_tools.kimi_fetch_url_tool.fetch_url",
            return_value=mock_result,
        ):
            tool, state = _make_tool()
            result = tool.execute_tool(
                "FetchURL",
                {"url": "https://example.com"},
                state,
            )

        assert result["success"] is False
        assert "network error" in result["error"]


class TestConfigSchema:
    """Tests for configuration schema."""

    def test_config_schema_returns_expected_keys(self) -> None:
        """Config schema should return all expected keys."""
        tool = KimiFetchURLTool()
        schema = tool.get_config_schema()

        expected_keys = [
            "moonshot_enabled",
            "moonshot_base_url",
            "moonshot_api_key",
            "moonshot_custom_headers",
            "web_fetch_timeout_seconds",
            "web_fetch_max_chars",
        ]

        for key in expected_keys:
            assert key in schema, f"Missing key: {key}"

    def test_config_schema_defaults(self) -> None:
        """Config schema should have correct defaults."""
        tool = KimiFetchURLTool()
        schema = tool.get_config_schema()

        assert schema["moonshot_enabled"]["default"] is False
        assert schema["moonshot_base_url"]["default"] == "https://api.kimi.com/coding/v1/fetch"
        assert schema["web_fetch_timeout_seconds"]["default"] == 10
        assert schema["web_fetch_max_chars"]["default"] == 50000


class TestUIElements:
    """Tests for UI elements."""

    def test_ui_elements_shows_enable_checkbox(self) -> None:
        """Should show enable checkbox by default."""
        tool = KimiFetchURLTool()
        elements = tool.get_ui_elements({})

        keys = [e["key"] for e in elements]
        assert "moonshot_enabled" in keys

    def test_ui_elements_shows_api_key_when_enabled(self) -> None:
        """Should show API key field when enabled."""
        tool = KimiFetchURLTool()
        elements = tool.get_ui_elements({"moonshot_enabled": True})

        keys = [e["key"] for e in elements]
        assert "moonshot_api_key" in keys
        assert "moonshot_base_url" in keys

    def test_ui_elements_hides_api_key_when_disabled(self) -> None:
        """Should hide API key field when disabled."""
        tool = KimiFetchURLTool()
        elements = tool.get_ui_elements({"moonshot_enabled": False})

        keys = [e["key"] for e in elements]
        assert "moonshot_api_key" not in keys

    def test_ui_elements_always_shows_timeout(self) -> None:
        """Should always show timeout setting."""
        tool = KimiFetchURLTool()
        elements = tool.get_ui_elements({})

        keys = [e["key"] for e in elements]
        assert "web_fetch_timeout_seconds" in keys
        assert "web_fetch_max_chars" in keys


class TestTrafilaturaExtraction:
    """Tests for trafilatura extraction options."""

    def test_extraction_options_match_kimi(self, tmp_path: Path) -> None:
        """Extraction should use Kimi-specific options."""
        tool, state = _make_tool()

        # Patch trafilatura.extract directly at module level
        with patch("trafilatura.extract") as mock_extract:
            mock_extract.return_value = "Extracted"

            result = tool._extract_with_trafilatura("<html><body>Test</body></html>")

            # Verify Kimi-specific options
            mock_extract.assert_called_once()
            call_kwargs = mock_extract.call_args[1]
            assert call_kwargs["include_comments"] is True
            assert call_kwargs["include_tables"] is True
            assert call_kwargs["include_formatting"] is False
            assert call_kwargs["output_format"] == "txt"
            assert call_kwargs["with_metadata"] is True
            assert result == "Extracted"

    def test_extraction_returns_empty_on_none(self, tmp_path: Path) -> None:
        """Should return empty string when trafilatura returns None."""
        tool, state = _make_tool()

        with patch("trafilatura.extract", return_value=None):
            result = tool._extract_with_trafilatura("<html><body></body></html>")
            assert result == ""

    def test_extraction_handles_exception(self, tmp_path: Path) -> None:
        """Should return empty string on exception."""
        tool, state = _make_tool()

        with patch("trafilatura.extract", side_effect=Exception("Extraction failed")):
            result = tool._extract_with_trafilatura("<html><body>Test</body></html>")
            assert result == ""


class TestMoonshotService:
    """Tests for Moonshot fetch service integration."""

    def test_service_not_used_when_disabled(self, tmp_path: Path) -> None:
        """Should skip service fetch when disabled."""
        from web_fetch_shared import FetchResult

        # Disabled by default
        mock_result = FetchResult(
            content="Local content",
            content_type="text/plain",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch(
            "kimi_tools.kimi_fetch_url_tool.fetch_url",
            return_value=mock_result,
        ):
            tool, state = _make_tool()  # Disabled by default
            result = tool.execute_tool(
                "FetchURL",
                {"url": "https://example.com"},
                state,
            )

        assert result["success"] is True
        assert result["result"] == "Local content"

    def test_service_fetch_success(self, tmp_path: Path) -> None:
        """Should return content from Moonshot service when enabled."""
        config = {
            "moonshot_enabled": True,
            "moonshot_api_key": "test-key",
        }

        async def mock_service_fetch(url, service_config, state):
            return {
                "success": True,
                "result": "Service content",
                "message": "The returned content is the main content extracted from the page.",
            }

        with patch.object(
            KimiFetchURLTool,
            "_fetch_with_service",
            side_effect=mock_service_fetch,
        ):
            tool, state = _make_tool(config)
            result = tool.execute_tool(
                "FetchURL",
                {"url": "https://example.com"},
                state,
            )

        assert result["success"] is True
        assert result["result"] == "Service content"

    def test_service_fetch_failure_fallback(self, tmp_path: Path) -> None:
        """Should fall back to local fetch when service fails."""
        from web_fetch_shared import FetchResult

        config = {
            "moonshot_enabled": True,
            "moonshot_api_key": "test-key",
        }

        async def mock_service_fetch(url, service_config, state):
            return {
                "success": False,
                "error": "Service failed",
            }

        mock_local_result = FetchResult(
            content="Local fallback content",
            content_type="text/plain",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch.object(
            KimiFetchURLTool,
            "_fetch_with_service",
            side_effect=mock_service_fetch,
        ):
            with patch(
                "kimi_tools.kimi_fetch_url_tool.fetch_url",
                return_value=mock_local_result,
            ):
                tool, state = _make_tool(config)
                result = tool.execute_tool(
                    "FetchURL",
                    {"url": "https://example.com"},
                    state,
                )

        assert result["success"] is True
        assert result["result"] == "Local fallback content"

    def test_service_resolves_env_var_api_key(self, tmp_path: Path) -> None:
        """Should resolve API key from environment variable."""
        config = {
            "moonshot_enabled": True,
            "moonshot_api_key": "${MOONSHOT_API_KEY}",
        }

        with patch.dict(os.environ, {"MOONSHOT_API_KEY": "env-api-key"}):
            tool, state = _make_tool(config)
            # Verify the env var was resolved
            assert state["moonshot_config"]["api_key"] == "env-api-key"

    def test_service_missing_api_key_returns_none(self, tmp_path: Path) -> None:
        """Should return None for moonshot_config when enabled but no API key."""
        config = {
            "moonshot_enabled": True,
            "moonshot_api_key": "${MOONSHOT_API_KEY}",
        }

        with patch.dict(os.environ, {}, clear=True):
            tool, state = _make_tool(config)
            # Should be None since no API key is available
            assert state["moonshot_config"] is None


class TestContentTruncation:
    """Tests for content truncation."""

    def test_truncates_long_content(self, tmp_path: Path) -> None:
        """Should truncate content exceeding max_chars."""
        from web_fetch_shared import FetchResult

        long_content = "x" * 100000
        mock_result = FetchResult(
            content=long_content,
            content_type="text/plain",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch(
            "kimi_tools.kimi_fetch_url_tool.fetch_url",
            return_value=mock_result,
        ):
            tool, state = _make_tool({"web_fetch_max_chars": 50000})
            result = tool.execute_tool(
                "FetchURL",
                {"url": "https://example.com"},
                state,
            )

        assert result["success"] is True
        assert len(result["result"]) < len(long_content)
        assert "truncated" in result["result"].lower()


class TestFormatToolResult:
    """Tests for result formatting."""

    def test_format_success_with_message(self, tmp_path: Path) -> None:
        """Should format success with message prefix."""
        tool, state = _make_tool()
        result = {
            "success": True,
            "result": "Content",
            "message": "Test message",
        }
        formatted = tool.format_tool_result(result, state)
        assert "Test message" in formatted
        assert "Content" in formatted

    def test_format_success_without_message(self, tmp_path: Path) -> None:
        """Should format success without message prefix."""
        tool, state = _make_tool()
        result = {
            "success": True,
            "result": "Content",
        }
        formatted = tool.format_tool_result(result, state)
        assert formatted == "Content"

    def test_format_error(self, tmp_path: Path) -> None:
        """Should format error with Error: prefix."""
        tool, state = _make_tool()
        result = {
            "success": False,
            "error": "Something went wrong",
        }
        formatted = tool.format_tool_result(result, state)
        assert formatted == "Error: Something went wrong"


class TestUnknownTool:
    """Tests for unknown tool handling."""

    def test_unknown_tool_error(self, tmp_path: Path) -> None:
        """Unknown tool name should return error."""
        tool, state = _make_tool()
        result = tool.execute_tool("UnknownTool", {"url": "https://example.com"}, state)
        assert result["success"] is False
        assert "Unknown tool" in result["error"]


class TestToolPipeline:
    """Tests for tool pipeline integration."""

    def test_execute_tool_returns_tool_message(self, tmp_path: Path) -> None:
        """Tool should produce valid tool message format."""
        core = AgentCore()
        core.register_tool(KimiFetchURLTool)

        config = {}

        # Test that the tool is registered
        messages = core.execute_tool_calls(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "FetchURL",
                        "arguments": {"url": "https://example.com"},
                    },
                }
            ],
            config,
        )

        assert len(messages) == 1
        assert messages[0]["role"] == "tool"
        assert messages[0]["metadata"]["tool_name"] == "FetchURL"


# Import asyncio for async test helpers
import asyncio


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
