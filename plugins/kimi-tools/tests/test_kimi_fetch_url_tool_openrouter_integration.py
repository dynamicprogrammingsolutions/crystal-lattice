"""Integration tests for KimiFetchURLTool with OpenRouter provider.

These tests exercise the full tool pipeline with a real OpenRouter provider.
Moonshot service tests only run when MOONSHOT_API_KEY environment variable is set.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from agent_core import AgentCore

from kimi_tools import KimiFetchURLTool


# Skip all tests in this file if OPENROUTER_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)


def _make_core_with_tool() -> AgentCore:
    """Create an AgentCore with KimiFetchURLTool registered."""
    core = AgentCore()
    core.register_tool(KimiFetchURLTool)
    return core


class TestOpenRouterIntegration:
    """Integration tests with OpenRouter provider."""

    @pytest.mark.openrouter
    def test_tool_registered_and_available(self, tmp_path: Path) -> None:
        """Tool should be registered and available."""
        core = _make_core_with_tool()

        # Get tool schemas
        schemas = core.get_tool_schemas({})

        tool_names = [s["function"]["name"] for s in schemas]
        assert "FetchURL" in tool_names

    @pytest.mark.openrouter
    def test_tool_execution_produces_valid_message(self, tmp_path: Path) -> None:
        """Tool execution should produce a valid tool message."""
        core = _make_core_with_tool()

        # Mock the fetch to avoid actual network calls
        from web_fetch_shared import FetchResult

        mock_result = FetchResult(
            content="Test content from URL",
            content_type="text/plain",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch(
            "kimi_tools.kimi_fetch_url_tool.fetch_url",
            return_value=mock_result,
        ):
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
                {},
            )

        assert len(messages) == 1
        assert messages[0]["role"] == "tool"
        assert messages[0]["metadata"]["tool_name"] == "FetchURL"
        assert "Test content from URL" in messages[0]["content"]


class TestMoonshotServiceIntegration:
    """Integration tests for Moonshot fetch service.

    These tests only run when MOONSHOT_API_KEY is set.
    """

    @pytest.fixture
    def moonshot_config(self) -> Dict[str, Any]:
        """Get Moonshot service config from environment."""
        api_key = os.environ.get("MOONSHOT_API_KEY")
        if not api_key:
            pytest.skip("MOONSHOT_API_KEY not set")
        return {
            "moonshot_enabled": True,
            "moonshot_api_key": api_key,
        }

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.environ.get("MOONSHOT_API_KEY"),
        reason="MOONSHOT_API_KEY not set",
    )
    def test_moonshot_service_fetch(self, moonshot_config: Dict[str, Any]) -> None:
        """Test real Moonshot service fetch when API key is available."""
        tool = KimiFetchURLTool()
        state = tool.init(moonshot_config)

        # Make a real API call to Moonshot fetch service
        result = asyncio.run(
            tool._fetch_with_service(
                "https://example.com",
                state["moonshot_config"],
                state,
            )
        )

        if not result["success"]:
            # If the API key is invalid, skip with a message rather than fail
            error_msg = result.get("error", "")
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                pytest.skip(f"Moonshot API key appears to be invalid or expired. Please verify credentials.")
            # Otherwise, fail with the error message
            pytest.fail(f"Moonshot service fetch failed: {error_msg}")

        assert result["success"] is True
        assert len(result["result"]) > 0
        assert "extracted" in result["message"].lower() or "content" in result["message"].lower()

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.environ.get("MOONSHOT_API_KEY"),
        reason="MOONSHOT_API_KEY not set",
    )
    def test_moonshot_service_fallback_on_error(
        self, moonshot_config: Dict[str, Any]
    ) -> None:
        """Test that local fetch is used when Moonshot service fails."""
        from web_fetch_shared import FetchResult

        # Create a config with invalid service URL to trigger failure
        bad_config = {
            "moonshot_enabled": True,
            "moonshot_api_key": moonshot_config["moonshot_api_key"],
            "moonshot_base_url": "https://invalid.kimi.url/fetch",
        }

        tool = KimiFetchURLTool()
        state = tool.init(bad_config)

        mock_local_result = FetchResult(
            content="Local fallback content",
            content_type="text/plain",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with patch(
            "kimi_tools.kimi_fetch_url_tool.fetch_url",
            return_value=mock_local_result,
        ):
            result = asyncio.run(
                tool._execute_async(
                    {"url": "https://example.com"},
                    state,
                    None,
                )
            )

        assert result["success"] is True
        assert result["result"] == "Local fallback content"

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.environ.get("MOONSHOT_API_KEY"),
        reason="MOONSHOT_API_KEY not set",
    )
    def test_moonshot_service_full_flow(self, moonshot_config: Dict[str, Any]) -> None:
        """Test full flow from tool call to Moonshot service fetch."""
        core = AgentCore()
        core.register_tool(KimiFetchURLTool)

        # Execute a real tool call with Moonshot config
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
            moonshot_config,
        )

        assert len(messages) == 1
        assert messages[0]["role"] == "tool"
        assert messages[0]["metadata"]["tool_name"] == "FetchURL"
        # Should have extracted content
        assert len(messages[0]["content"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
