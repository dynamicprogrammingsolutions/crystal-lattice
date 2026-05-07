"""Integration tests for QwenWebFetchTool with OpenRouter provider.

Tests the full fetch + summarize pipeline with a real LLM provider.
Requires OPENROUTER_API_KEY environment variable.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import pytest

from agent_app.plugin_manager import PluginManager
from agent_core import AgentCore
from agent_core.plugin import ToolWrapper

from qwen_tools import QwenWebFetchTool
from qwen_tools.qwen_web_fetch_tool import _rate_limit_cache


# Skip all tests in this module if OPENROUTER_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)


@pytest.fixture(autouse=True)
def clear_rate_limit_cache():
    """Clear rate limit cache before each test."""
    _rate_limit_cache.clear()


class TestOpenRouterIntegration:
    """Integration tests with OpenRouter provider."""

    @pytest.mark.openrouter
    def test_fetch_and_summarize_with_openrouter(self, tmp_path: Path) -> None:
        """End-to-end fetch and summarize using OpenRouter."""
        from agent_app import AgentApplication

        # Create application with OpenRouter config
        config = {
            "provider": "openrouter",
            "model": "openai/gpt-4.1-mini",
            "api_key": os.environ.get("OPENROUTER_API_KEY"),
        }

        # Create tool wrapper
        wrapper = ToolWrapper(QwenWebFetchTool)
        state = wrapper.init(config)

        # Create core with tool
        core = AgentCore()
        core.register_tool(QwenWebFetchTool)

        # Execute fetch on a known URL (httpbin.org or similar)
        # Use a simple, reliable URL for testing
        result = core.execute_tool_calls(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "web_fetch",
                        "arguments": {
                            "url": "https://httpbin.org/html",
                            "prompt": "What is the main heading on this page?",
                        },
                    },
                }
            ],
            config,
        )

        assert len(messages) == 1
        assert messages[0]["role"] == "tool"
        # The content should be summarized, not raw HTML
        assert len(messages[0]["content"]) < 50000  # Should be summarized

    @pytest.mark.openrouter
    def test_fetch_text_url_returns_content(self, tmp_path: Path) -> None:
        """Fetch of text URL should return the content."""
        from agent_core import AgentCore

        core = AgentCore()
        core.register_tool(QwenWebFetchTool)

        config = {
            "provider": "openrouter",
            "model": "openai/gpt-4.1-mini",
            "api_key": os.environ.get("OPENROUTER_API_KEY"),
        }

        # Use a text file URL
        messages = core.execute_tool_calls(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "web_fetch",
                        "arguments": {
                            "url": "https://raw.githubusercontent.com/httpie/httpie/master/README.md",
                            "prompt": "Summarize what this project is about",
                        },
                    },
                }
            ],
            config,
        )

        assert len(messages) == 1
        # Should contain a summary
        assert "httpie" in messages[0]["content"].lower() or "http" in messages[0]["content"].lower()


class TestSingleToolLoading:
    """Tests loading only the web fetch tool."""

    @pytest.mark.openrouter
    def test_single_tool_with_openrouter(self, tmp_path: Path) -> None:
        """Verify web fetch works when loaded as a single tool."""
        wrapper = ToolWrapper(QwenWebFetchTool)

        config = {
            "provider": "openrouter",
            "model": "openai/gpt-4.1-mini",
            "api_key": os.environ.get("OPENROUTER_API_KEY"),
        }

        state = wrapper.init(config)

        # Verify schema is correct
        schemas = wrapper.get_tool_schemas(state)
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "web_fetch"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "openrouter"])
