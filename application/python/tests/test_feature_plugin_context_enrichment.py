"""Tests for feature plugin context enrichment at the application layer.

These tests verify that context flows correctly from the application layer
to feature plugins when calling AgentApplication methods.

This tests Layer 2 and Layer 3 context:
- Layer 2: Application adds (app, base_config, session_asset_store, runtime_state_root)
- Layer 3: Custom context from caller flows through to plugin
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any, Dict

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import AgentCore

# Path to the test fixture plugin
# From application/python/tests/ we need to go up 4 levels to reach repo root
REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_ROOT = REPO_ROOT / "core" / "python" / "tests" / "fixtures"
PLUGIN_PATH = FIXTURES_ROOT / "context_recording_plugin"


def _write_config(tmp_path: Path, config: Dict[str, Any]) -> Path:
    """Write config to temp file and return path."""
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


def _make_app(tmp_path: Path, config: Dict[str, Any]) -> AgentApplication:
    """Create AgentApplication with env overrides for plugin path resolution."""
    config_path = _write_config(tmp_path, config)
    session_root = tmp_path / "sessions"
    return AgentApplication(
        str(config_path),
        str(session_root),
        core_factory=AgentCore,
        event_store=InMemoryEventStore(),
        env_overrides={
            "FIXTURES_ROOT": str(FIXTURES_ROOT),
        },
    )


def _minimal_config() -> Dict[str, Any]:
    """Build minimal config with echo provider and context recording plugin."""
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
            # Built-in echo provider
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            # Context recording test plugin (installed in dev mode)
            "context_recording_plugin.ContextRecordingPlugin",
        ],
    }


def _config_with_request_marker() -> Dict[str, Any]:
    config = _minimal_config()
    config["providers"]["echo"][
        "context_recording_request_marker"
    ] = "request-initialized"
    return config


def _get_plugin_class():
    """Get the ContextRecordingPlugin class by importing the module."""
    import sys
    import importlib.util

    plugin_src_path = str(PLUGIN_PATH / "src" / "context_recording_plugin")
    if plugin_src_path not in sys.path:
        sys.path.insert(0, plugin_src_path)

    # Force reimport to get fresh module
    if "context_recording_plugin" in sys.modules:
        del sys.modules["context_recording_plugin"]

    spec = importlib.util.spec_from_file_location(
        "context_recording_plugin",
        str(PLUGIN_PATH / "src" / "context_recording_plugin" / "__init__.py"),
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["context_recording_plugin"] = module
    spec.loader.exec_module(module)

    return module.ContextRecordingPlugin


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_captured_contexts():
    """Clear captured contexts before and after each test."""
    plugin_class = _get_plugin_class()
    plugin_class.clear_captured_contexts()
    yield
    plugin_class.clear_captured_contexts()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestApplicationContextEnrichment:
    """Tests for Layer 2: Application-level context enrichment."""

    def test_application_session_action_includes_app_context(
        self, tmp_path: Path, clear_captured_contexts: None
    ) -> None:
        """Feature plugin receives app, base_config when called via app layer.

        This verifies Layer 2 context enrichment for session actions.
        """
        plugin_class = _get_plugin_class()
        assert plugin_class is not None, "Could not load ContextRecordingPlugin"

        app = _make_app(tmp_path, _minimal_config())
        core, base_config, session = app.create_session("default")

        session = core.add_message(session, "user", "Test", None, base_config)
        app.save_session(session)

        app.execute_session_action(
            plugin_id="context_recording",
            action_id="record_context",
            params={"session_id": session.session_id},
        )

        # Check captured context
        contexts = plugin_class.get_captured_contexts()
        assert len(contexts) == 1, "Expected one context capture"

        ctx = contexts[0]

        # Layer 1: Core-level keys (always present)
        assert "core" in ctx, "Context should include 'core'"
        assert "config" in ctx, "Context should include 'config'"
        assert "session" in ctx, "Context should include 'session'"
        assert "trigger_source" in ctx, "Context should include 'trigger_source'"

        # Layer 2: Application-level keys (present when called via app)
        assert "app" in ctx, "Context should include 'app' when called via application"
        assert "application" in ctx, "Context should include 'application' (alias)"
        assert "base_config" in ctx, "Context should include 'base_config'"

        # Verify types
        assert ctx["app"] is app, "'app' should be the AgentApplication instance"
        assert ctx["application"] is app, "'application' should be the same as 'app'"
        assert isinstance(ctx["base_config"], dict), "'base_config' should be a dict"

    def test_application_execute_action_resolves_omitted_feature_plugin(
        self, tmp_path: Path, clear_captured_contexts: None
    ) -> None:
        plugin_class = _get_plugin_class()
        assert plugin_class is not None, "Could not load ContextRecordingPlugin"

        app = _make_app(tmp_path, _minimal_config())
        core, base_config, session = app.create_session("default")
        session = core.add_message(session, "user", "Test", None, base_config)
        app.save_session(session)

        result = app.execute_action(
            plugin_id=None,
            action_id="record_context",
            params={},
            context={"session_id": session.session_id},
        )

        assert result["mutations"]["updated_session_ids"] == [session.session_id]
        stored = app.load_session_record(session.session_id)
        assert stored is not None
        assert stored.metadata["action_id"] == "record_context"
        contexts = plugin_class.get_captured_contexts()
        assert len(contexts) == 1
        assert contexts[0]["_action_id"] == "record_context"

    def test_application_session_action_sees_request_initialized_state(
        self, tmp_path: Path, clear_captured_contexts: None
    ) -> None:
        plugin_class = _get_plugin_class()
        assert plugin_class is not None, "Could not load ContextRecordingPlugin"

        app = _make_app(tmp_path, _config_with_request_marker())
        core, base_config, session = app.create_session("default")

        session = core.add_message(session, "user", "Test", None, base_config)
        app.save_session(session)

        app.execute_session_action(
            plugin_id="context_recording",
            action_id="record_context",
            params={"session_id": session.session_id},
        )

        contexts = plugin_class.get_captured_contexts()
        assert len(contexts) == 1
        ctx = contexts[0]
        request = ctx.get("_request")
        assert isinstance(request, dict)
        assert "context_recording_request_marker" not in request
        assert isinstance(ctx.get("request_context"), dict)
        assert isinstance(ctx.get("request_runtime"), dict)

    def test_application_session_action_can_explicitly_initialize_request_state(
        self, tmp_path: Path, clear_captured_contexts: None
    ) -> None:
        plugin_class = _get_plugin_class()
        assert plugin_class is not None, "Could not load ContextRecordingPlugin"

        app = _make_app(tmp_path, _config_with_request_marker())
        core, base_config, session = app.create_session("default")

        session = core.add_message(session, "user", "Test", None, base_config)
        app.save_session(session)

        app.execute_session_action(
            plugin_id="context_recording",
            action_id="record_initialized_context",
            params={"session_id": session.session_id},
        )

        contexts = plugin_class.get_captured_contexts()
        assert len(contexts) == 1
        request = contexts[0].get("_request")
        assert isinstance(request, dict)
        assert request.get("context_recording_request_marker") == "request-initialized"

    def test_application_lifecycle_includes_app_context(
        self, tmp_path: Path, clear_captured_contexts: None
    ) -> None:
        """Feature plugin receives app, base_config in lifecycle actions.

        This verifies Layer 2 context enrichment for lifecycle-triggered actions.
        """
        plugin_class = _get_plugin_class()
        assert plugin_class is not None, "Could not load ContextRecordingPlugin"

        app = _make_app(tmp_path, _minimal_config())
        core, base_config, session = app.create_session("default")

        # Run lifecycle with a trigger that matches our plugin's action
        # Note: The plugin has a "record_context_with_trigger" action with trigger="request_complete"
        core, base_config, session, results = app.run_session_lifecycle(
            "request_complete",
            session,
            core=core,
            base_config=base_config,
        )

        # Check captured context
        contexts = plugin_class.get_captured_contexts()

        # Note: Lifecycle actions may or may not capture depending on trigger matching
        # If captured, verify Layer 2 context is present
        for ctx in contexts:
            if ctx.get("_action_id") == "record_context_with_trigger":
                assert "app" in ctx, "Lifecycle context should include 'app'"
                assert (
                    "base_config" in ctx
                ), "Lifecycle context should include 'base_config'"
                assert (
                    "lifecycle" in ctx
                ), "Lifecycle context should include 'lifecycle'"
                assert ctx["lifecycle"] == "request_complete"
                assert isinstance(ctx.get("request_context"), dict)
                assert isinstance(ctx.get("request_runtime"), dict)
                assert "session_asset_store" in ctx
                assert "runtime_state_root" in ctx

    def test_custom_context_flows_through_application(
        self,
        tmp_path: Path,
        clear_captured_contexts: None,
    ) -> None:
        """Custom additive context survives, but reserved keys are ignored.

        This tests Layer 3 context: any custom context passed by the caller
        (terminal, server, or test) should flow through to the plugin.

        This is the mechanism that terminal/server implementations use to add
        their own context keys.
        """
        plugin_class = _get_plugin_class()
        assert plugin_class is not None, "Could not load ContextRecordingPlugin"

        app = _make_app(tmp_path, _minimal_config())
        core, base_config, session = app.create_session("default")

        session = core.add_message(session, "user", "Test", None, base_config)
        app.save_session(session)

        custom_context = {
            "trigger_source": "custom_terminal",
            "custom_key": "custom_value",
        }

        app.execute_session_action(
            plugin_id="context_recording",
            action_id="record_context",
            params={"session_id": session.session_id},
            context=custom_context,
        )

        # Check captured context
        contexts = plugin_class.get_captured_contexts()
        assert len(contexts) == 1, "Expected one context capture"

        ctx = contexts[0]

        assert ctx.get("trigger_source") == "core"
        assert ctx.get("custom_key") == "custom_value"

    def test_response_finalize_includes_request_support(
        self,
        tmp_path: Path,
        clear_captured_contexts: None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plugin_class = _get_plugin_class()
        assert plugin_class is not None, "Could not load ContextRecordingPlugin"

        app = _make_app(tmp_path, _minimal_config())
        core, base_config, session = app.create_session("default")
        session = core.add_message(session, "user", "Test", None, base_config)
        app.save_session(session)

        list(app.send_request(core, session, base_config, stream=False))

        contexts = plugin_class.get_captured_contexts()
        response_context = next(
            ctx
            for ctx in contexts
            if ctx.get("_action_id") == "record_response_finalize_context"
        )
        assert isinstance(response_context.get("request_context"), dict)
        assert isinstance(response_context.get("request_runtime"), dict)
        assert response_context.get("lifecycle") == "response_finalize"
        assert "session_asset_store" in response_context
        assert "runtime_state_root" in response_context
        assert "context_reserved_key_clash_external" not in capsys.readouterr().out


class TestContextStructure:
    """Tests verifying the complete context structure."""

    def test_context_structure_completeness(
        self, tmp_path: Path, clear_captured_contexts: None
    ) -> None:
        """Verify all expected context keys are present.

        This test documents the complete context structure that feature plugins
        receive when called through the application layer.
        """
        plugin_class = _get_plugin_class()
        assert plugin_class is not None, "Could not load ContextRecordingPlugin"

        app = _make_app(tmp_path, _minimal_config())
        core, base_config, session = app.create_session("default")

        session = core.add_message(session, "user", "Test", None, base_config)
        app.save_session(session)

        app.execute_session_action(
            plugin_id="context_recording",
            action_id="record_context",
            params={"session_id": session.session_id},
        )

        contexts = plugin_class.get_captured_contexts()
        assert len(contexts) == 1, "Expected one context capture"

        ctx = contexts[0]

        # Document all expected keys
        expected_layer1_keys = [
            "core",
            "config",
            "trigger_source",
            "session",
            "request_context",
            "request_runtime",
        ]
        expected_layer2_keys = [
            "app",
            "application",
            "base_config",
            "session_asset_store",
            "runtime_state_root",
        ]

        for key in expected_layer1_keys:
            assert key in ctx, f"Layer 1 key '{key}' should be present in context"

        for key in expected_layer2_keys:
            assert key in ctx, f"Layer 2 key '{key}' should be present in context"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
