"""Tests for tool plugin context enrichment.

Tests that the core and application layers enrich context correctly
for tool plugins.
"""

from __future__ import annotations

import pytest
from typing import Any, Dict, List

from agent_core import AgentCore
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider

from tests.fixtures.context_recording_tool import ContextRecordingTool


def _config() -> Dict[str, Any]:
    return {
        "provider": "echo_openai_like",
        "model": "test-model",
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(EchoOpenAILikeProvider)
    core.register_tool(ContextRecordingTool)
    return core


def _make_tool_call(name: str = "record_tool_context", payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a simple tool call dict for testing."""
    return {
        "id": "call_test_1",
        "type": "function",
        "function": {
            "name": name,
            "arguments": '{"message": "test"}' if payload is None else '{}',
        },
    }


class TestCoreToolContextEnrichment:
    """Tests for Layer 1: Core-level context enrichment for tools."""

    def setup_method(self) -> None:
        """Clear captured contexts before each test."""
        ContextRecordingTool.get_captured_contexts()

    def test_iter_tool_messages_enriches_context_with_core(self) -> None:
        """Tool context should include 'core' key with AgentCore instance."""
        core = _build_core()
        config = _config()

        tool_call = _make_tool_call()

        # Execute tool via iter_tool_messages
        results = list(core.iter_tool_messages([tool_call], config))

        # Check captured context
        contexts = ContextRecordingTool.get_captured_contexts()
        assert len(contexts) == 1
        assert "core" in contexts[0]
        assert contexts[0]["core"] is core

    def test_iter_tool_messages_enriches_context_with_config(self) -> None:
        """Tool context should include 'config' key with the request config."""
        core = _build_core()
        config = _config()

        tool_call = _make_tool_call()

        # Execute tool
        results = list(core.iter_tool_messages([tool_call], config))

        # Check captured context
        contexts = ContextRecordingTool.get_captured_contexts()
        assert len(contexts) == 1
        assert "config" in contexts[0]
        assert contexts[0]["config"] == config

    def test_iter_tool_messages_sets_trigger_source_to_core(self) -> None:
        """Tool context should have trigger_source='core' when called directly."""
        core = _build_core()
        config = _config()

        tool_call = _make_tool_call()

        # Execute tool
        results = list(core.iter_tool_messages([tool_call], config))

        # Check captured context
        contexts = ContextRecordingTool.get_captured_contexts()
        assert len(contexts) == 1
        assert contexts[0].get("trigger_source") == "core"

    def test_execute_tool_calls_enriches_context(self) -> None:
        """execute_tool_calls should also enrich context."""
        core = _build_core()
        config = _config()

        tool_call = _make_tool_call()

        # Execute tool via execute_tool_calls
        results = core.execute_tool_calls([tool_call], config)

        # Check captured context
        contexts = ContextRecordingTool.get_captured_contexts()
        assert len(contexts) == 1
        assert "core" in contexts[0]
        assert "config" in contexts[0]
        assert contexts[0].get("trigger_source") == "core"

    def test_stream_tool_call_enriches_context(self) -> None:
        """stream_tool_call should also enrich context."""
        core = _build_core()
        config = _config()

        tool_call = _make_tool_call()

        # Execute tool via stream_tool_call
        results = list(core.stream_tool_call(tool_call, config))

        # Check captured context
        contexts = ContextRecordingTool.get_captured_contexts()
        assert len(contexts) == 1
        assert "core" in contexts[0]
        assert "config" in contexts[0]
        assert contexts[0].get("trigger_source") == "core"

    def test_context_enrichment_preserves_existing_values(self) -> None:
        """Context from caller should be preserved (setdefault behavior)."""
        core = _build_core()
        config = _config()

        tool_call = _make_tool_call()

        # Pass custom context
        custom_context = {
            "custom_key": "custom_value",
            "trigger_source": "custom_source",
        }

        results = list(core.iter_tool_messages([tool_call], config, context=custom_context))

        # Check captured context
        contexts = ContextRecordingTool.get_captured_contexts()
        assert len(contexts) == 1
        # Custom value should be preserved
        assert contexts[0].get("custom_key") == "custom_value"
        # Core's trigger_source should NOT overwrite custom value (setdefault behavior)
        assert contexts[0].get("trigger_source") == "custom_source"

    def test_context_can_be_used_to_call_core(self) -> None:
        """Tool can use context['core'] to access AgentCore methods."""
        core = _build_core()
        config = _config()

        tool_call = _make_tool_call()

        # Execute tool
        results = list(core.iter_tool_messages([tool_call], config))

        # Verify the context has core and it's the right instance
        contexts = ContextRecordingTool.get_captured_contexts()
        assert len(contexts) == 1
        assert contexts[0]["core"] is core
        # Verify we can use the core from context
        context_core = contexts[0]["core"]
        assert hasattr(context_core, "create_session")
        assert hasattr(context_core, "send_request")
        assert hasattr(context_core, "send_request_stream")


class TestBackwardCompatibility:
    """Tests for backward compatibility with tools that don't accept context."""

    def setup_method(self) -> None:
        """Clear captured contexts before each test."""
        ContextRecordingTool.get_captured_contexts()

    def test_tool_without_context_parameter_still_works(self) -> None:
        """Tools that don't accept context should still work."""

        class LegacyTool:
            """A tool that doesn't accept the context parameter."""

            name = "legacy_tool"
            version = "1.0.0"

            def get_config_schema(self) -> Dict[str, Any]:
                return {}

            def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
                return {"config": config}

            def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
                return [
                    {
                        "type": "function",
                        "function": {
                            "name": "legacy_operation",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    }
                ]

            def execute_tool(
                self,
                tool_name: str,
                payload: Any,
                state: Dict[str, Any],
            ) -> Dict[str, Any]:
                # This tool doesn't accept context parameter
                return {"success": True, "result": "legacy_result"}

            def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
                return f"Legacy result: {result.get('result')}"

        core = AgentCore()
        core.register_provider(EchoOpenAILikeProvider)
        core.register_tool(LegacyTool)

        config = _config()
        tool_call = {
            "id": "call_legacy_1",
            "type": "function",
            "function": {
                "name": "legacy_operation",
                "arguments": "{}",
            },
        }

        # Should work without error
        results = list(core.iter_tool_messages([tool_call], config))
        assert len(results) == 1
        assert results[0]["role"] == "tool"
        assert "Legacy result" in results[0]["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
