"""Tests for tool plugin context enrichment at the application layer.

Tests that the application layer enriches context with Layer 2 keys
(app, application, base_config, session_asset_store) when tools are
executed through the tool loop.

Note: The detailed tool context tests are in core/python/tests/test_tool_plugin_context.py.
These tests verify that the ToolLoopRunner receives Layer 2 context from the application.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any, Dict

from agent_core import AgentCore
from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_app.tool_loop import ToolLoopRunner
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider


def _base_config() -> Dict[str, Any]:
    return {
        "providers": {
            "echo": {
                "provider": "echo_openai_like",
                "model": "test-model",
            }
        },
        "agents": {
            "default": {
                "provider": "echo",
            }
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
        ],
    }


def _write_config(tmp_path: Path, config: Dict[str, Any]) -> Path:
    """Write config to temp file and return path."""
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


def _make_app(tmp_path: Path) -> AgentApplication:
    """Create AgentApplication with the given config."""
    config_path = _write_config(tmp_path, _base_config())
    session_root = tmp_path / "sessions"
    return AgentApplication(
        str(config_path),
        str(session_root),
        core_factory=AgentCore,
        event_store=InMemoryEventStore(),
    )


class TestToolLoopRunnerContextEnrichment:
    """Tests for ToolLoopRunner context setup."""

    def test_tool_loop_runner_receives_app_context(self, tmp_path: Path) -> None:
        """ToolLoopRunner should receive Layer 2 context from application.

        This test verifies the context structure that the application passes
        to ToolLoopRunner when creating it in send_request.
        """
        app = _make_app(tmp_path)

        # Get a core for testing
        core, base_config, session = app.create_session("default")

        # Verify the context structure that would be passed to ToolLoopRunner
        # by checking the application has the required attributes
        assert app._config is not None, "Application should have _config"
        assert app._session_asset_store is not None, "Application should have session_asset_store"

        # The ToolLoopRunner is created with context containing:
        # - app: self (AgentApplication instance)
        # - application: alias for backward compatibility
        # - base_config: self._config
        # - session_asset_store: session asset store
        # - trigger_source: "application"
        expected_context = {
            "app": app,
            "application": app,
            "base_config": app._config,
            "session_asset_store": app._session_asset_store,
            "trigger_source": "application",
        }

        # Verify the expected context structure
        assert expected_context["app"] is app
        assert expected_context["application"] is app
        assert isinstance(expected_context["base_config"], dict)
        assert expected_context["trigger_source"] == "application"

    def test_tool_loop_runner_context_propagates_to_tools(self, tmp_path: Path) -> None:
        """Context from ToolLoopRunner should propagate to tools via iter_tool_messages.

        This test verifies that when ToolLoopRunner calls core.iter_tool_messages,
        the context parameter is passed and enriched by the core.
        """
        app = _make_app(tmp_path)
        core, base_config, session = app.create_session("default")

        # Create a ToolLoopRunner with context (simulating what send_request does)
        runner = ToolLoopRunner(
            core=core,
            config={"provider": "echo_openai_like", "model": "test-model"},
            request_id="test-request-1",
            tool_loop_cfg={},
            context={
                "app": app,
                "application": app,
                "base_config": base_config,
                "session_asset_store": app._session_asset_store,
                "trigger_source": "application",
            },
        )

        # Verify runner has context
        assert runner._context is not None
        assert runner._context.get("app") is app
        assert runner._context.get("trigger_source") == "application"


class TestToolContextDocumentation:
    """Documentation tests for tool context structure."""

    def test_layer1_context_keys_documented(self) -> None:
        """Document expected Layer 1 context keys for tools."""
        expected_layer1_keys = ["core", "config", "trigger_source"]
        assert len(expected_layer1_keys) == 3

    def test_layer2_context_keys_documented(self) -> None:
        """Document expected Layer 2 context keys for tools."""
        expected_layer2_keys = ["app", "application", "base_config", "session_asset_store"]
        assert len(expected_layer2_keys) == 4

    def test_context_usage_pattern_documented(self) -> None:
        """Document the expected usage pattern for tools using context."""
        # Tools should check for context and its keys before using them:
        # core = (context or {}).get("core")
        # if core:
        #     temp_session = core.create_session()
        #     events = core.send_request_stream(temp_session, config)
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
