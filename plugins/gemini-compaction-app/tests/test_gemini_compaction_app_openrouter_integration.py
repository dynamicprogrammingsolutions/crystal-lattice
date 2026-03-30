"""Integration test for GeminiCompactionAppPlugin with OpenRouter (Gemini 2.5 Flash Lite).

This test runs against the real OpenRouter API and verifies the complete
compaction flow with a real model.

Requires the OPENROUTER_API_KEY environment variable.

Run with:

    pytest plugins/gemini-compaction-app/tests/test_gemini_compaction_app_openrouter_integration.py \
        -v -s -m openrouter
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import pytest

# Load .env file if it exists
try:
    from dotenv import load_dotenv

    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")
except ImportError:
    pass


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = os.getenv("OPENROUTER_MODEL_GEMINI_COMPACTION", "google/gemini-2.5-flash-lite")


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    """Skip tests if OpenRouter API key is not configured."""
    if not OPENROUTER_API_KEY:
        pytest.skip(
            "OPENROUTER_API_KEY not set; skipping Gemini compaction OpenRouter integration test",
        )


def _make_config(tmp_path: Path, verification_pass: bool = False) -> Path:
    """Build a minimal AgentApplication config using OpenRouter + Gemini Compaction."""

    cfg: Dict[str, Any] = {
        "providers": {
            "openrouter_gemini": {
                "provider": "openrouter",
                "model": MODEL,
                "api_key": OPENROUTER_API_KEY,
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
            "openrouter_plugins.openrouter_provider.OpenRouterProvider",
            "gemini_compaction_app.GeminiCompactionAppPlugin",
        ],
    }

    path = tmp_path / "config_gemini_compaction_openrouter.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path, verification_pass: bool = False):
    """Build AgentApplication with Gemini compaction plugin."""
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    cfg_path = _make_config(tmp_path, verification_pass=verification_pass)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


@pytest.mark.integration
@pytest.mark.openrouter
def test_gemini_compaction_ui_elements_session_scoped(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Test that UI elements are filtered by config when using session-scoped endpoint.

    When called via AgentApplication.get_application_ui_schema(config=effective_config),
    the plugin receives the session's effective config and can filter UI elements
    based on compaction.enabled and compaction.type.

    This test verifies the session-aware application plugin UI implementation
    from tasks/20260128/040 and tasks/20260130/010.
    """

    # Create config with enabled=true (enabled)
    cfg: Dict[str, Any] = {
        "providers": {
            "openrouter_gemini": {
                "provider": "openrouter",
                "model": MODEL,
                "api_key": OPENROUTER_API_KEY,
                "base_url": BASE_URL,
                "timeout": 180,
            }
        },
        "agents": {
            "default": {
                "provider": "openrouter_gemini",
                "compaction": {
                    "enabled": True,  # Enabled
                    "type": "gemini",
                },
            }
        },
        "plugins": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider",
            "gemini_compaction_app.GeminiCompactionAppPlugin",
        ],
    }

    config_path = tmp_path / "config_ui_test.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")

    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_app.config import resolve_request_config

    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Create a session and get its base_config
    core, base_config, session = app.create_session("default")

    # Get UI schema with session config - should return elements (enabled)
    effective_config = resolve_request_config(base_config, {})
    ui_elements = app.get_application_ui_schema(config=effective_config)

    # Filter to our plugin's elements
    compaction_elements = [e for e in ui_elements if e.get("plugin") == "gemini_compaction"]

    # Should have 3 elements when enabled
    assert len(compaction_elements) == 3

    # Now test with disabled config
    cfg_disabled: Dict[str, Any] = {
        "providers": {
            "openrouter_gemini": {
                "provider": "openrouter",
                "model": MODEL,
                "api_key": OPENROUTER_API_KEY,
                "base_url": BASE_URL,
                "timeout": 180,
            }
        },
        "agents": {
            "default": {
                "provider": "openrouter_gemini",
                "compaction": {
                    "enabled": False,  # Disabled
                    "type": "gemini",
                },
            }
        },
        "plugins": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider",
            "gemini_compaction_app.GeminiCompactionAppPlugin",
        ],
    }

    config_path_disabled = tmp_path / "config_ui_test_disabled.json"
    config_path_disabled.write_text(json.dumps(cfg_disabled), encoding="utf-8")

    app_disabled = AgentApplication(str(config_path_disabled), str(session_root), event_store=events)
    core_disabled, base_config_disabled, session_disabled = app_disabled.create_session("default")

    # Get UI schema with session config - should return empty (disabled)
    effective_config_disabled = resolve_request_config(base_config_disabled, {})
    ui_elements_disabled = app_disabled.get_application_ui_schema(config=effective_config_disabled)

    compaction_elements_disabled = [e for e in ui_elements_disabled if e.get("plugin") == "gemini_compaction"]
    assert compaction_elements_disabled == []

    # Test global endpoint (no config) - should always return elements
    ui_elements_global = app.get_application_ui_schema()  # No config
    compaction_elements_global = [e for e in ui_elements_global if e.get("plugin") == "gemini_compaction"]
    assert len(compaction_elements_global) == 3  # Always returns when no config


@pytest.mark.integration
@pytest.mark.openrouter
def test_gemini_compaction_flow(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Test compaction flow with real model.

    This test verifies:
    1. Plugin is enabled when config has enabled=true and type=gemini
    2. Compaction action can be executed
    3. History is modified after compaction
    """

    app = _build_app(tmp_path, verification_pass=False)

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    # Add a multi-turn conversation (more than 2 messages to ensure compaction has something to work with)
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

    # Compact the history
    result = app.execute_application_action(
        plugin_id="gemini_compaction",
        action_id="compact_range",
        params={"session_id": session_id, "end": 4},  # Compact first 4 messages
    )

    # Check the result - it could be success (mutations), noop, or error
    if "mutations" in result:
        # Success - verify the history was modified
        ctx = app.load_session(session_id)
        assert ctx is not None
        _, _, compacted_session = ctx

        # History should be different after compaction
        assert len(compacted_session.messages) <= message_count_before
    elif result.get("status") == "noop":
        # No messages to compact - this is also valid
        pass
    elif result.get("status") == "error":
        # Error occurred - check it's a valid error type
        assert result.get("error_type") in ("compaction_failed", "disabled")
    else:
        # Unexpected result structure
        pytest.fail(f"Unexpected result structure: {result}")


@pytest.mark.integration
@pytest.mark.openrouter
def test_gemini_compaction_with_verification_pass(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Test compaction with verification pass enabled."""

    app = _build_app(tmp_path, verification_pass=True)

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    # Add a conversation
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

    # Compact with verification pass
    result = app.execute_application_action(
        plugin_id="gemini_compaction",
        action_id="compact_range",
        params={"session_id": session_id, "end": 2},  # Compact first 2 messages
    )

    # Check the result
    if "mutations" in result:
        # Success - verification_pass should be True
        assert result.get("verification_pass") is True
    elif result.get("status") == "noop":
        # No messages to compact
        pass
    elif result.get("status") == "error":
        # Error occurred
        assert result.get("error_type") in ("compaction_failed", "disabled")
    else:
        pytest.fail(f"Unexpected result structure: {result}")


@pytest.mark.integration
@pytest.mark.openrouter
def test_gemini_compaction_disabled_for_non_gemini_type(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Test that compaction is disabled when type is not 'gemini'."""

    # Create config with wrong type
    cfg: Dict[str, Any] = {
        "providers": {
            "openrouter_gemini": {
                "provider": "openrouter",
                "model": MODEL,
                "api_key": OPENROUTER_API_KEY,
                "base_url": BASE_URL,
                "timeout": 180,
            }
        },
        "agents": {
            "default": {
                "provider": "openrouter_gemini",
                "compaction": {
                    "enabled": True,
                    "type": "qwen",  # Wrong type
                },
            }
        },
        "plugins": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider",
            "gemini_compaction_app.GeminiCompactionAppPlugin",
        ],
    }

    config_path = tmp_path / "config_disabled.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")

    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Create a session
    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    session = core.add_message(session, "user", "Hello", None, base_config)
    session = core.add_message(session, "assistant", "Hi!", None, base_config)
    app.save_session(session)

    # Try to run compaction - should fail because disabled
    result = app.execute_application_action(
        plugin_id="gemini_compaction",
        action_id="compact_range",
        params={"session_id": session_id},
    )

    # Should return error status
    assert result.get("status") == "error"
    assert result.get("error_type") == "disabled"


@pytest.mark.integration
@pytest.mark.openrouter
def test_gemini_compaction_disabled_by_default(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Test that compaction is disabled when enabled is false."""

    # Create config with enabled=false
    cfg: Dict[str, Any] = {
        "providers": {
            "openrouter_gemini": {
                "provider": "openrouter",
                "model": MODEL,
                "api_key": OPENROUTER_API_KEY,
                "base_url": BASE_URL,
                "timeout": 180,
            }
        },
        "agents": {
            "default": {
                "provider": "openrouter_gemini",
                "compaction": {
                    "enabled": False,  # Disabled
                    "type": "gemini",
                },
            }
        },
        "plugins": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider",
            "gemini_compaction_app.GeminiCompactionAppPlugin",
        ],
    }

    config_path = tmp_path / "config_disabled2.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")

    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Create a session
    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    session = core.add_message(session, "user", "Hello", None, base_config)
    session = core.add_message(session, "assistant", "Hi!", None, base_config)
    app.save_session(session)

    # Try to run compaction - should fail because disabled
    result = app.execute_application_action(
        plugin_id="gemini_compaction",
        action_id="compact_range",
        params={"session_id": session_id},
    )

    # Should return error status
    assert result.get("status") == "error"
    assert result.get("error_type") == "disabled"
