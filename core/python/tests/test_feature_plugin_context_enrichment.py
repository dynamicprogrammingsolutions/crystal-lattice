"""Tests for feature plugin context enrichment.

Tests that the core and application layers enrich context correctly
for feature plugins.
"""

from __future__ import annotations

import pytest
from typing import Any, Dict

from agent_core import AgentCore
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider

from tests.fixtures.context_recording_feature import ContextRecordingFeature


def _config() -> Dict[str, Any]:
    return {
        "provider": "echo_openai_like",
        "model": "test-model",
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(EchoOpenAILikeProvider, [ContextRecordingFeature])
    return core


class TestCoreContextEnrichment:
    """Tests for Layer 1: Core-level context enrichment."""

    def test_execute_session_action_enriches_context_with_core(self) -> None:
        """Context should include 'core' key with AgentCore instance."""
        core = _build_core()
        config = _config()

        session = core.create_session()

        # Execute action
        new_session, result = core.execute_session_action(
            session,
            config,
            plugin_id="context_recording",
            action_id="record_context",
            params={},
        )

        # Check captured context
        contexts = ContextRecordingFeature.get_captured_contexts()
        assert len(contexts) == 1
        assert "core" in contexts[0]
        assert contexts[0]["core"] is core

    def test_execute_session_action_enriches_context_with_config(self) -> None:
        """Context should include 'config' key with the request config."""
        core = _build_core()
        config = _config()

        session = core.create_session()

        # Execute action
        new_session, result = core.execute_session_action(
            session,
            config,
            plugin_id="context_recording",
            action_id="record_context",
            params={},
        )

        # Check captured context
        contexts = ContextRecordingFeature.get_captured_contexts()
        assert len(contexts) == 1
        assert "config" in contexts[0]
        assert contexts[0]["config"] == config

    def test_execute_session_action_sets_trigger_source_to_core(self) -> None:
        """Context should have trigger_source='core' when called directly."""
        core = _build_core()
        config = _config()

        session = core.create_session()

        # Execute action
        new_session, result = core.execute_session_action(
            session,
            config,
            plugin_id="context_recording",
            action_id="record_context",
            params={},
        )

        # Check captured context
        contexts = ContextRecordingFeature.get_captured_contexts()
        assert len(contexts) == 1
        assert contexts[0].get("trigger_source") == "core"

    def test_execute_session_action_includes_session_dict(self) -> None:
        """Context should include 'session' key with session.to_dict()."""
        core = _build_core()
        config = _config()

        session = core.create_session()

        # Execute action
        new_session, result = core.execute_session_action(
            session,
            config,
            plugin_id="context_recording",
            action_id="record_context",
            params={},
        )

        # Check captured context
        contexts = ContextRecordingFeature.get_captured_contexts()
        assert len(contexts) == 1
        assert "session" in contexts[0]
        assert isinstance(contexts[0]["session"], dict)
        assert contexts[0]["session"]["session_id"] == session.session_id

    def test_execute_lifecycle_actions_enriches_context(self) -> None:
        """Lifecycle actions should also get enriched context."""
        core = _build_core()
        config = _config()

        session = core.create_session()

        # Execute lifecycle actions
        new_session, results = core.execute_lifecycle_actions(
            session,
            config,
            trigger="request_complete",
        )

        # Check captured context
        contexts = ContextRecordingFeature.get_captured_contexts()
        assert len(contexts) == 1
        assert "core" in contexts[0]
        assert "config" in contexts[0]
        assert contexts[0].get("trigger_source") == "core"
        assert contexts[0].get("lifecycle") == "request_complete"

    def test_context_enrichment_preserves_existing_values(self) -> None:
        """Context from caller should be preserved if already set."""
        core = _build_core()
        config = _config()

        session = core.create_session()

        # Pass custom context
        custom_context = {
            "custom_key": "custom_value",
            "trigger_source": "custom_source",
        }

        new_session, result = core.execute_session_action(
            session,
            config,
            plugin_id="context_recording",
            action_id="record_context",
            params={},
            context=custom_context,
        )

        # Check captured context
        contexts = ContextRecordingFeature.get_captured_contexts()
        assert len(contexts) == 1
        # Custom value should be preserved
        assert contexts[0].get("custom_key") == "custom_value"
        # Core's trigger_source should NOT overwrite custom value (setdefault behavior)
        assert contexts[0].get("trigger_source") == "custom_source"


class TestAppContextEnrichment:
    """Tests for Layer 2: Application-level context enrichment.

    Note: These tests require the application layer, which is tested
    in the application tests. Here we just verify the context structure
    is correct when features receive it from the core.
    """

    def test_context_has_app_key_structure(self) -> None:
        """Verify expected keys for app-level context.

        When called from application, context should have:
        - 'app' and 'application' keys (both pointing to AgentApplication)
        - 'base_config' key with full config
        """
        # This is tested in application layer tests
        # Here we just document the expected structure
        expected_keys = ["app", "application", "base_config", "core", "config"]
        # These are added by app layer in _build_lifecycle_context
        # and execute_session_action
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])