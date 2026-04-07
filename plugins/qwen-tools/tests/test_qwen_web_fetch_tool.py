"""Unit tests for QwenWebFetchTool.

Tests cover schema validation, URL validation, rate limiting,
configuration, and error handling.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

from agent_core import AgentCore
from agent_core.plugin import ToolWrapper

from qwen_tools import QwenWebFetchTool
from qwen_tools.qwen_web_fetch_tool import _rate_limit_cache
from web_fetch_shared import LRUCache


def _make_wrapper(
    config: Dict[str, Any] = None,
) -> tuple[ToolWrapper, Dict[str, Any]]:
    """Create a configured tool wrapper for testing."""
    # Reset rate limit cache for each test
    _rate_limit_cache.clear()

    wrapper = ToolWrapper(QwenWebFetchTool)
    cfg = config or {}
    state = wrapper.init(cfg)
    return wrapper, state


class TestSchema:
    """Tests for tool schema matching Qwen CLI spec."""

    def test_tool_name_is_web_fetch(self, tmp_path: Path) -> None:
        """Tool name in schema should be 'web_fetch'."""
        wrapper, state = _make_wrapper()
        schemas = wrapper.get_tool_schemas(state)
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "web_fetch"

    def test_url_and_prompt_are_required_parameters(self, tmp_path: Path) -> None:
        """Both 'url' and 'prompt' parameters should be required."""
        wrapper, state = _make_wrapper()
        schemas = wrapper.get_tool_schemas(state)
        params = schemas[0]["function"]["parameters"]
        assert "url" in params["properties"]
        assert "prompt" in params["properties"]
        assert set(params["required"]) == {"url", "prompt"}

    def test_description_mentions_url_processing(self, tmp_path: Path) -> None:
        """Description should mention URL processing capability."""
        wrapper, state = _make_wrapper()
        schemas = wrapper.get_tool_schemas(state)
        desc = schemas[0]["function"]["description"]
        assert "URL" in desc or "url" in desc
        assert "prompt" in desc.lower()

    def test_description_mentions_private_urls(self, tmp_path: Path) -> None:
        """Description should mention support for private/localhost URLs."""
        wrapper, state = _make_wrapper()
        schemas = wrapper.get_tool_schemas(state)
        desc = schemas[0]["function"]["description"]
        assert "private" in desc.lower() or "localhost" in desc.lower()


class TestURLValidation:
    """Tests for URL parameter validation."""

    def test_valid_http_url_accepted(self, tmp_path: Path) -> None:
        """Valid http:// URL should be accepted."""
        wrapper, state = _make_wrapper()

        result = wrapper.execute_tool(
            "web_fetch",
            {"url": "http://example.com", "prompt": "summarize"},
            state,
        )

        # Should not fail with URL validation error
        assert "required" not in result.get("error", "").lower()
        assert "invalid" not in result.get("error", "").lower()

    def test_valid_https_url_accepted(self, tmp_path: Path) -> None:
        """Valid https:// URL should be accepted."""
        wrapper, state = _make_wrapper()

        result = wrapper.execute_tool(
            "web_fetch",
            {"url": "https://example.com", "prompt": "summarize"},
            state,
        )

        # Should not fail with URL validation error
        assert "required" not in result.get("error", "").lower()
        assert "invalid" not in result.get("error", "").lower()

    def test_invalid_url_scheme_error(self, tmp_path: Path) -> None:
        """Invalid URL scheme should return error."""
        wrapper, state = _make_wrapper()

        result = wrapper.execute_tool(
            "web_fetch",
            {"url": "ftp://example.com", "prompt": "summarize"},
            state,
        )

        assert result["success"] is False
        assert "Unsupported protocol" in result["error"]

    def test_empty_url_error(self, tmp_path: Path) -> None:
        """Empty URL should return error."""
        wrapper, state = _make_wrapper()

        result = wrapper.execute_tool(
            "web_fetch",
            {"url": "", "prompt": "summarize"},
            state,
        )

        assert result["success"] is False
        assert "required" in result["error"].lower()

    def test_missing_url_error(self, tmp_path: Path) -> None:
        """Missing URL should return error."""
        wrapper, state = _make_wrapper()

        result = wrapper.execute_tool(
            "web_fetch",
            {"prompt": "summarize"},
            state,
        )

        assert result["success"] is False
        assert "required" in result["error"].lower()

    def test_empty_prompt_error(self, tmp_path: Path) -> None:
        """Empty prompt should return error."""
        wrapper, state = _make_wrapper()

        result = wrapper.execute_tool(
            "web_fetch",
            {"url": "https://example.com", "prompt": ""},
            state,
        )

        assert result["success"] is False
        assert "required" in result["error"].lower()

    def test_missing_prompt_error(self, tmp_path: Path) -> None:
        """Missing prompt should return error."""
        wrapper, state = _make_wrapper()

        result = wrapper.execute_tool(
            "web_fetch",
            {"url": "https://example.com"},
            state,
        )

        assert result["success"] is False
        assert "required" in result["error"].lower()


class TestRateLimiting:
    """Tests for per-host rate limiting."""

    def setup_method(self) -> None:
        """Clear rate limit cache before each test."""
        _rate_limit_cache.clear()

    def test_first_requests_allowed(self, tmp_path: Path) -> None:
        """First 10 requests to a host should be allowed."""
        tool = QwenWebFetchTool()
        state = tool.init({})

        for i in range(10):
            allowed, wait = tool._check_rate_limit("https://example.com/page", state)
            assert allowed is True
            assert wait is None

    def test_eleventh_request_blocked(self, tmp_path: Path) -> None:
        """11th request should be blocked with wait time."""
        tool = QwenWebFetchTool()
        state = tool.init({})

        # Make 10 allowed requests
        for i in range(10):
            tool._check_rate_limit("https://example.com/page", state)

        # 11th should be blocked
        allowed, wait = tool._check_rate_limit("https://example.com/page", state)
        assert allowed is False
        assert wait is not None
        assert wait > 0

    def test_different_hosts_tracked_separately(self, tmp_path: Path) -> None:
        """Rate limits should be tracked per-host."""
        tool = QwenWebFetchTool()
        state = tool.init({})

        # Make 10 requests to example.com
        for i in range(10):
            tool._check_rate_limit("https://example.com/page", state)

        # Should still allow requests to other.com
        allowed, wait = tool._check_rate_limit("https://other.com/page", state)
        assert allowed is True

    def test_configurable_rate_limits(self, tmp_path: Path) -> None:
        """Rate limits should be configurable."""
        tool = QwenWebFetchTool()
        # Configure 5 requests per 30 seconds
        state = tool.init(
            {
                "web_fetch_rate_limit_requests": 5,
                "web_fetch_rate_limit_window": 30,
            }
        )

        # Make 5 allowed requests
        for i in range(5):
            allowed, _ = tool._check_rate_limit("https://example.com/page", state)
            assert allowed is True

        # 6th should be blocked
        allowed, wait = tool._check_rate_limit("https://example.com/page", state)
        assert allowed is False


class TestConfigSchema:
    """Tests for configuration schema."""

    def test_config_schema_returns_expected_keys(self) -> None:
        """Config schema should return all expected keys."""
        tool = QwenWebFetchTool()
        schema = tool.get_config_schema()

        expected_keys = [
            "web_fetch_enabled",
            "web_fetch_timeout_seconds",
            "web_fetch_max_content_chars",
            "web_fetch_rate_limit_requests",
            "web_fetch_rate_limit_window",
            "web_fetch_summarization_agent_id",
            "web_fetch_summarization_model",
        ]

        for key in expected_keys:
            assert key in schema, f"Missing key: {key}"

    def test_config_schema_has_defaults(self) -> None:
        """Config schema should have default values."""
        tool = QwenWebFetchTool()
        schema = tool.get_config_schema()

        assert schema["web_fetch_enabled"]["default"] is True
        assert schema["web_fetch_timeout_seconds"]["default"] == 10
        assert schema["web_fetch_max_content_chars"]["default"] == 100000
        assert schema["web_fetch_rate_limit_requests"]["default"] == 10
        assert schema["web_fetch_rate_limit_window"]["default"] == 60


class TestUIElements:
    """Tests for UI elements."""

    def test_ui_elements_returns_expected_elements(self) -> None:
        """UI elements should include expected keys."""
        tool = QwenWebFetchTool()
        elements = tool.get_ui_elements({})

        keys = [e["key"] for e in elements]
        assert "web_fetch_enabled" in keys
        assert "web_fetch_timeout_seconds" in keys
        assert "web_fetch_summarization_agent_id" in keys

    def test_ui_elements_has_correct_types(self) -> None:
        """UI elements should have correct types."""
        tool = QwenWebFetchTool()
        elements = tool.get_ui_elements({})

        by_key = {e["key"]: e for e in elements}

        assert by_key["web_fetch_enabled"]["type"] == "checkbox"
        assert by_key["web_fetch_timeout_seconds"]["type"] == "number"
        assert by_key["web_fetch_summarization_agent_id"]["type"] == "text"


class TestGitHubURLNormalization:
    """Tests for GitHub blob URL normalization."""

    def test_converts_blob_to_raw(self, tmp_path: Path) -> None:
        """GitHub blob URLs should be converted to raw URLs."""
        from web_fetch_shared import normalize_github_url

        blob_url = "https://github.com/user/repo/blob/main/file.md"
        result = normalize_github_url(blob_url)

        assert result == "https://raw.githubusercontent.com/user/repo/main/file.md"


class TestFetchBehavior:
    """Tests for fetch behavior with mocked HTTP."""

    def setup_method(self) -> None:
        """Clear rate limit cache before each test."""
        _rate_limit_cache.clear()

    def test_fetch_success_returns_content(self, tmp_path: Path) -> None:
        """Successful fetch should return content."""
        from web_fetch_shared import FetchResult

        mock_result = FetchResult(
            content="Test content",
            content_type="text/plain",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch("qwen_tools.qwen_web_fetch_tool.fetch_url", return_value=mock_result):
            wrapper, state = _make_wrapper()

            result = wrapper.execute_tool(
                "web_fetch",
                {"url": "https://example.com", "prompt": "summarize"},
                state,
            )

        assert result["success"] is True
        assert "Test content" in result["result"]

    def test_fetch_html_extracts_text(self, tmp_path: Path) -> None:
        """HTML content should be extracted to text."""
        from web_fetch_shared import FetchResult

        mock_result = FetchResult(
            content="<html><body><p>Test paragraph</p></body></html>",
            content_type="text/html",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch("qwen_tools.qwen_web_fetch_tool.fetch_url", return_value=mock_result):
            wrapper, state = _make_wrapper()

            result = wrapper.execute_tool(
                "web_fetch",
                {"url": "https://example.com", "prompt": "summarize"},
                state,
            )

        assert result["success"] is True

    def test_fetch_error_returns_error_message(self, tmp_path: Path) -> None:
        """Fetch error should return error message."""
        from web_fetch_shared import FetchResult

        mock_result = FetchResult(
            content="",
            content_type="",
            status_code=404,
            headers={},
            url="https://example.com/notfound",
            is_error=True,
            error_message="HTTP 404",
        )

        with patch("qwen_tools.qwen_web_fetch_tool.fetch_url", return_value=mock_result):
            wrapper, state = _make_wrapper()

            result = wrapper.execute_tool(
                "web_fetch",
                {"url": "https://example.com/notfound", "prompt": "summarize"},
                state,
            )

        assert result["success"] is False
        assert "404" in result["error"] or "Error during fetch" in result["error"]


class TestErrorHandling:
    """Tests for error handling."""

    def test_unknown_tool_error(self, tmp_path: Path) -> None:
        """Unknown tool name should return error."""
        wrapper, state = _make_wrapper()

        result = wrapper.execute_tool(
            "unknown_tool",
            {"url": "https://example.com", "prompt": "test"},
            state,
        )

        assert result["success"] is False
        assert "Unknown tool" in result["error"]

    def test_format_tool_result_success(self, tmp_path: Path) -> None:
        """Successful result should be formatted as text."""
        wrapper, state = _make_wrapper()

        result = {"success": True, "result": "Some content"}
        text = wrapper.format_tool_result(result, state)

        assert text == "Some content"

    def test_format_tool_result_error(self, tmp_path: Path) -> None:
        """Error result should be formatted with Error: prefix."""
        wrapper, state = _make_wrapper()

        result = {"success": False, "error": "Something went wrong"}
        text = wrapper.format_tool_result(result, state)

        assert text == "Error: Something went wrong"


class TestEnabledConfig:
    """Tests for enabled/disabled configuration."""

    def test_tool_enabled_by_default(self, tmp_path: Path) -> None:
        """Tool should be enabled by default."""
        wrapper = ToolWrapper(QwenWebFetchTool)
        state = wrapper.init({})
        result = wrapper.is_enabled({}, [], [], {})
        assert result is None  # Falls through to tag checks

    def test_tool_disabled_when_config_disabled(self, tmp_path: Path) -> None:
        """Tool should be disabled when config says so."""
        wrapper = ToolWrapper(QwenWebFetchTool)
        state = wrapper.init({"web_fetch_enabled": False})
        result = wrapper.is_enabled({"web_fetch_enabled": False}, [], [], {})
        assert result is False

    def test_execution_fails_when_disabled(self, tmp_path: Path) -> None:
        """Execution should fail when tool is disabled."""
        wrapper, state = _make_wrapper({"web_fetch_enabled": False})

        result = wrapper.execute_tool(
            "web_fetch",
            {"url": "https://example.com", "prompt": "test"},
            state,
        )

        assert result["success"] is False
        assert "disabled" in result["error"].lower()


class TestToolPipeline:
    """Tests for tool pipeline integration."""

    def setup_method(self) -> None:
        """Clear rate limit cache before each test."""
        _rate_limit_cache.clear()

    def test_execute_tool_returns_tool_message(self, tmp_path: Path) -> None:
        """Tool should produce valid tool message format."""
        from web_fetch_shared import FetchResult

        mock_result = FetchResult(
            content="Test content",
            content_type="text/plain",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch("qwen_tools.qwen_web_fetch_tool.fetch_url", return_value=mock_result):
            core = AgentCore()
            core.register_tool(QwenWebFetchTool)

            messages = core.execute_tool_calls(
                [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "web_fetch",
                            "arguments": {
                                "url": "https://example.com",
                                "prompt": "summarize",
                            },
                        },
                    }
                ],
                {},
            )

        assert len(messages) == 1
        assert messages[0]["role"] == "tool"
        assert messages[0]["metadata"]["tool_name"] == "web_fetch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
