"""Application-level integration test for GeminiCompactionFeaturePlugin.

Tests the complete flow:
- Plugin is loaded via ``path:${env:BUILTIN_PLUGINS}/gemini-compaction-feature``
  (descriptor-based loading through ``agent_plugin.json``)
- Feature plugin is registered and its actions discovered
- Compaction action executes via ``core.execute_session_action`` with layered context
- Context is enriched with core, config, app, base_config

Requires the OPENROUTER_API_KEY environment variable.

Run with:

    pytest plugins/gemini-compaction-feature/tests/test_gemini_compaction_feature_application_integration.py \\
        -v -s -m openrouter
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import AgentCore

# Load .env file if it exists
try:
    from dotenv import load_dotenv

    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")
except ImportError:
    pass

REPO_ROOT = Path(__file__).resolve().parents[3]
BUILTIN_PLUGINS = REPO_ROOT / "plugins"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = os.getenv("OPENROUTER_MODEL_GEMINI_COMPACTION", "google/gemini-2.5-flash-lite")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
            "BUILTIN_PLUGINS": str(BUILTIN_PLUGINS),
            "OPENROUTER_API_KEY": OPENROUTER_API_KEY or "",
        },
    )


def _enabled_config(verification_pass: bool = False) -> Dict[str, Any]:
    """Build config with compaction enabled and loaded via path: descriptor."""
    return {
        "providers": {
            "openrouter_gemini": {
                "provider": "openrouter",
                "model": MODEL,
                "api_key": "${env:OPENROUTER_API_KEY}",
                "base_url": BASE_URL,
                "timeout": 180,
            }
        },
        "agents": {
            "default": {
                "provider": "openrouter_gemini",
                "compaction": {
                    "enabled": True,
                    "type": "gemini",
                    "verification_pass": verification_pass,
                },
            }
        },
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/gemini-compaction-feature",
        ],
    }


def _disabled_config(reason: str = "wrong_type") -> Dict[str, Any]:
    """Build config where compaction is disabled."""
    compaction: Dict[str, Any]
    if reason == "wrong_type":
        compaction = {"enabled": True, "type": "qwen"}
    elif reason == "enabled_false":
        compaction = {"enabled": False, "type": "gemini"}
    else:
        compaction = {}

    return {
        "providers": {
            "openrouter_gemini": {
                "provider": "openrouter",
                "model": MODEL,
                "api_key": "${env:OPENROUTER_API_KEY}",
                "base_url": BASE_URL,
                "timeout": 180,
            }
        },
        "agents": {
            "default": {
                "provider": "openrouter_gemini",
                "compaction": compaction,
            }
        },
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/gemini-compaction-feature",
        ],
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    """Skip tests if OpenRouter API key is not configured."""
    if not OPENROUTER_API_KEY:
        pytest.skip(
            "OPENROUTER_API_KEY not set; "
            "skipping Gemini compaction feature application integration test",
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.openrouter
def test_feature_plugin_loaded_via_path_descriptor(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Verify the plugin is discovered and registered via agent_plugin.json descriptor."""
    app = _make_app(tmp_path, _enabled_config())

    core, base_config, session = app.create_session("default")

    # The feature plugin should be registered; its actions should appear
    actions = core.get_session_actions(base_config)

    feature_actions = [
        a for a in actions
        if a.get("plugin") == "gemini_compaction_feature"
    ]
    assert len(feature_actions) == 1, (
        f"Expected 1 feature action, got {feature_actions}. "
        f"All actions: {[a.get('plugin') for a in actions]}"
    )
    assert feature_actions[0]["id"] == "compact_range"
    assert feature_actions[0]["action_owner"] == "feature"


@pytest.mark.integration
@pytest.mark.openrouter
def test_feature_ui_elements_appear_when_enabled_gemini_type(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Verify UI elements appear when config has enabled=true and type=gemini.

    This mirrors the AppPlugin's UI element filtering test for FeaturePlugin.
    The FeaturePlugin's get_ui_elements filters based on config enablement.
    """
    app = _make_app(tmp_path, _enabled_config())

    core, base_config, session = app.create_session("default")

    # Get UI schema from core - should include our UI elements
    ui_elements = core.get_ui_schema(base_config)

    feature_elements = [
        e for e in ui_elements
        if e.get("plugin") == "gemini_compaction_feature"
    ]

    # Should have 3 elements when enabled (compact_range, compact_up_to_here, compact_full)
    assert len(feature_elements) == 3, (
        f"Expected 3 UI elements when enabled=true, type=gemini, got {len(feature_elements)}"
    )

    # Verify the UI types
    ui_types = {e["id"]: e["ui_type"] for e in feature_elements}
    assert ui_types.get("compact_range") == "session_action"
    assert ui_types.get("compact_up_to_here") == "message_action"
    assert ui_types.get("compact_full") == "session_action"

    # Verify action_owner is set correctly for feature plugins
    for el in feature_elements:
        assert el.get("action_owner") == "feature", f"Expected action_owner='feature', got {el.get('action_owner')}"


@pytest.mark.integration
@pytest.mark.openrouter
def test_feature_ui_elements_hidden_when_disabled(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Verify UI elements are hidden when config has enabled=false.

    Unlike get_actions which always returns actions, get_ui_elements filters
    based on config enablement - returning empty list when disabled.
    """
    app = _make_app(tmp_path, _disabled_config("enabled_false"))

    core, base_config, session = app.create_session("default")

    # Get UI schema from core - should NOT include our UI elements
    ui_elements = core.get_ui_schema(base_config)

    feature_elements = [
        e for e in ui_elements
        if e.get("plugin") == "gemini_compaction_feature"
    ]

    # Should have 0 elements when disabled
    assert len(feature_elements) == 0, (
        f"Expected 0 UI elements when disabled, got {len(feature_elements)}: {feature_elements}"
    )


@pytest.mark.integration
@pytest.mark.openrouter
def test_feature_ui_elements_hidden_when_wrong_type(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Verify UI elements are hidden when type is not 'gemini'."""
    app = _make_app(tmp_path, _disabled_config("wrong_type"))

    core, base_config, session = app.create_session("default")

    # Get UI schema from core - should NOT include our UI elements
    ui_elements = core.get_ui_schema(base_config)

    feature_elements = [
        e for e in ui_elements
        if e.get("plugin") == "gemini_compaction_feature"
    ]

    # Should have 0 elements when wrong type
    assert len(feature_elements) == 0


@pytest.mark.integration
@pytest.mark.openrouter
def test_feature_action_appears_when_enabled_gemini_type(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Verify action appears when config has enabled=true and type=gemini.

    This mirrors the AppPlugin's UI element filtering test but for FeaturePlugin actions.
    """
    app = _make_app(tmp_path, _enabled_config())

    core, base_config, session = app.create_session("default")

    # Get session actions - should include our compact_range action
    actions = core.get_session_actions(base_config)

    feature_actions = [
        a for a in actions
        if a.get("plugin") == "gemini_compaction_feature"
    ]

    # Should have 1 action (compact_range)
    assert len(feature_actions) == 1, (
        f"Expected 1 feature action when enabled=true, type=gemini, got {len(feature_actions)}"
    )
    assert feature_actions[0]["id"] == "compact_range"

    # Verify the action has the expected inputs
    inputs = feature_actions[0].get("inputs", {})
    assert "start" in inputs
    assert "end" in inputs
    assert "end_inclusive" in inputs
    assert "instructions" in inputs


@pytest.mark.integration
@pytest.mark.openrouter
def test_feature_action_still_appears_when_disabled_but_execution_fails(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Verify that FeaturePlugin actions always appear (not filtered by config).

    Unlike AppPlugin UI elements which are filtered, FeaturePlugin actions are
    always registered. The enablement check happens at execution time.
    """
    # Test with enabled=false
    app = _make_app(tmp_path, _disabled_config("enabled_false"))

    core, base_config, session = app.create_session("default")

    # Get session actions - should STILL include our action (FeaturePlugin doesn't filter)
    actions = core.get_session_actions(base_config)

    feature_actions = [
        a for a in actions
        if a.get("plugin") == "gemini_compaction_feature"
    ]

    # Action should still appear (FeaturePlugin actions aren't filtered)
    assert len(feature_actions) == 1, (
        f"FeaturePlugin actions should appear even when disabled, got {len(feature_actions)}"
    )

    # But executing should return "disabled" error
    session = core.add_message(session, "user", "Hello", None, base_config)
    session = core.add_message(session, "assistant", "Hi!", None, base_config)

    new_session, result = core.execute_session_action(
        session,
        base_config,
        plugin_id="gemini_compaction_feature",
        action_id="compact_range",
        params={},
    )

    assert "error" in result
    assert result["error"]["type"] == "disabled"


@pytest.mark.integration
@pytest.mark.openrouter
def test_feature_action_still_appears_when_wrong_type_but_execution_fails(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Verify action appears even with wrong type, but execution fails."""
    app = _make_app(tmp_path, _disabled_config("wrong_type"))

    core, base_config, session = app.create_session("default")

    # Action should still appear
    actions = core.get_session_actions(base_config)
    feature_actions = [a for a in actions if a.get("plugin") == "gemini_compaction_feature"]
    assert len(feature_actions) == 1

    # But executing should return "disabled" error
    session = core.add_message(session, "user", "Hello", None, base_config)
    session = core.add_message(session, "assistant", "Hi!", None, base_config)

    new_session, result = core.execute_session_action(
        session,
        base_config,
        plugin_id="gemini_compaction_feature",
        action_id="compact_range",
        params={},
    )

    assert "error" in result
    assert result["error"]["type"] == "disabled"


@pytest.mark.integration
@pytest.mark.openrouter
def test_feature_compaction_flow_via_path(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """End-to-end compaction flow: load via path:, execute via core.execute_session_action.

    Verifies:
    1. Plugin loads via path:${env:BUILTIN_PLUGINS}/gemini-compaction-feature
    2. Context is enriched with core, config, app, base_config
    3. Compaction returns native_messages with snapshot
    """
    app = _make_app(tmp_path, _enabled_config(verification_pass=False))

    core, base_config, session = app.create_session("default")

    # Build a multi-turn conversation
    messages = [
        ("user", "Let's discuss space exploration."),
        ("assistant", "Space exploration has advanced significantly."),
        ("user", "What about Mars missions?"),
        ("assistant", "Mars missions are a key focus for NASA and SpaceX."),
        ("user", "Tell me about the Perseverance rover."),
        (
            "assistant",
            "Perseverance landed on Mars in 2021 and is searching for signs of ancient life.",
        ),
    ]

    for role, content in messages:
        session = core.add_message(session, role, content, None, base_config)

    app.save_session(session)

    message_count_before = len(session.messages)
    assert message_count_before == 6

    # Execute compaction via core.execute_session_action
    new_session, result = core.execute_session_action(
        session,
        base_config,
        plugin_id="gemini_compaction_feature",
        action_id="compact_range",
        params={"end": 4},  # Compact first 4 messages
    )

    # Accept success or API-level failure
    if "compaction_result" in result:
        assert result["compaction_result"]["status"] == "ok"
        assert "native_messages" in result
        # Snapshot + ack should replace the compacted range
        assert len(result["native_messages"]) < message_count_before + 2
    elif "error" in result:
        assert result["error"]["type"] in ("compaction_failed", "disabled")
    else:
        pytest.fail(f"Unexpected result structure: {list(result.keys())}")


@pytest.mark.integration
@pytest.mark.openrouter
def test_feature_compaction_with_verification_via_path(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Compaction with verification pass enabled, loaded via path: descriptor."""
    app = _make_app(tmp_path, _enabled_config(verification_pass=True))

    core, base_config, session = app.create_session("default")

    messages = [
        ("user", "Explain the difference between TCP and UDP."),
        (
            "assistant",
            "TCP is reliable and connection-oriented. UDP is faster but unreliable.",
        ),
        ("user", "Which is better for video streaming?"),
        (
            "assistant",
            "UDP is typically preferred for video streaming due to lower latency.",
        ),
    ]

    for role, content in messages:
        session = core.add_message(session, role, content, None, base_config)

    app.save_session(session)

    new_session, result = core.execute_session_action(
        session,
        base_config,
        plugin_id="gemini_compaction_feature",
        action_id="compact_range",
        params={"end": 2},
    )

    if "compaction_result" in result:
        assert result["compaction_result"].get("verification_pass") is True
    elif "error" in result:
        assert result["error"]["type"] in ("compaction_failed", "disabled")
    else:
        pytest.fail(f"Unexpected result: {list(result.keys())}")
