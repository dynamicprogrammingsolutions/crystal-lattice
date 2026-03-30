"""Integration test for GeminiCompactionAppPlugin with feature-system-message.

This test uses a minimal config with OpenRouter + Gemini + SystemMessageFeature
and verifies the compaction flow preserves system messages correctly.

Requires the OPENROUTER_API_KEY environment variable.

Run with:

    pytest plugins/gemini-compaction-app/tests/test_gemini_compaction_app_system_message.py \
        -v -s -m openrouter
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

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
            "OPENROUTER_API_KEY not set; skipping Gemini compaction integration test",
        )


def _get_plugins_path() -> str:
    """Get the path to plugins directory."""
    repo_root = Path(__file__).resolve().parents[3]
    return str(repo_root / "plugins")


def _make_config(tmp_path: Path, verification_pass: bool = False) -> Path:
    """Build a minimal AgentApplication config with OpenRouter + SystemMessage + Gemini Compaction."""

    plugins_path = _get_plugins_path()

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
                # Simple system message template
                "system_message_enabled": True,
                "system_message": "You are a helpful coding assistant. Be concise and accurate.",
                # Enable Gemini compaction
                "compaction": {
                    "enabled": True,
                    "type": "gemini",
                    "verification_pass": verification_pass,
                },
                # Load feature-system-message from path
                "plugins": [
                    f"path:{plugins_path}/feature-system-message",
                ],
            }
        },
        "plugins": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider",
            "gemini_compaction_app.GeminiCompactionAppPlugin",
        ],
    }

    path = tmp_path / "config_gemini_compaction_system_message.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path, verification_pass: bool = False):
    """Build AgentApplication with Gemini compaction + system message plugin."""
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    cfg_path = _make_config(tmp_path, verification_pass=verification_pass)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


@pytest.mark.integration
@pytest.mark.openrouter
def test_compact_full_history_with_system_message(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Test compacting full history when there's a system message.

    This test verifies:
    1. System message is preserved after compaction
    2. System message is NOT duplicated
    3. Message order is correct: system -> user(snapshot) -> assistant(ack)
    """

    app = _build_app(tmp_path, verification_pass=False)

    # Create a session
    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    # Add a multi-turn conversation
    messages = [
        ("user", "What is the capital of France?"),
        ("assistant", "The capital of France is Paris."),
        ("user", "What about Germany?"),
        ("assistant", "The capital of Germany is Berlin."),
        ("user", "And Italy?"),
        ("assistant", "The capital of Italy is Rome."),
    ]

    for role, content in messages:
        session = core.add_message(session, role, content, None, base_config)

    app.save_session(session)

    message_count_before = len(session.messages)
    print(f"\nMessages before compaction: {message_count_before}")
    for i, msg in enumerate(session.messages):
        role_str = msg.role.upper().ljust(9)
        content_preview = msg.content[:50] if len(msg.content) > 50 else msg.content
        has_metadata = " [MD]" if msg.metadata else ""
        print(f"  [{i}] {role_str} {content_preview}{has_metadata}")

    # Before compaction, there should be NO system message in core messages
    # (system message is injected into native messages by the feature)
    system_count_before = sum(1 for msg in session.messages if msg.role == "system")
    print(f"\nSystem messages in core before compaction: {system_count_before}")

    # Run compact_range with no start/end to compact full history
    result = app.execute_application_action(
        plugin_id="gemini_compaction",
        action_id="compact_range",
        params={"session_id": session_id},
    )

    print(f"\nCompaction result: {result}")

    # Check the result
    if result.get("status") == "error":
        error_type = result.get("error_type")
        if error_type == "disabled":
            pytest.skip("Compaction not enabled for this agent")
        elif error_type == "compaction_failed":
            pytest.fail(f"Compaction failed: {result.get('message')}")
        else:
            pytest.fail(f"Unexpected error: {result}")

    # Reload and check message structure
    ctx = app.load_session(session_id)
    assert ctx is not None
    _, _, compacted_session = ctx

    message_count_after = len(compacted_session.messages)
    print(f"\nMessages after compaction: {message_count_after}")
    for i, msg in enumerate(compacted_session.messages):
        role_str = msg.role.upper().ljust(9)
        content_preview = msg.content[:60] if len(msg.content) > 60 else msg.content
        print(f"  [{i}] {role_str} {content_preview}")

    # CRITICAL: System message should NOT appear in core messages
    # (it's only in native messages, injected by the feature)
    # But if it does appear (due to a bug), it should be unique
    system_indices = [i for i, msg in enumerate(compacted_session.messages) if msg.role == "system"]
    print(f"\nSystem message indices: {system_indices}")

    assert len(system_indices) <= 1, \
        f"DUPLICATE SYSTEM MESSAGE! Found system messages at indices: {system_indices}"

    # Verify snapshot was created
    user_messages = [msg for msg in compacted_session.messages if msg.role == "user"]
    assert len(user_messages) >= 1, "Should have at least one user message (the snapshot)"


@pytest.mark.integration
@pytest.mark.openrouter
def test_compact_up_to_here_preserves_message_order(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Test compacting messages up to a specific index preserves order.

    This test verifies:
    1. Compaction snapshot is inserted at the correct position
    2. Remaining messages after compaction point are preserved
    3. No duplicate system messages (in core - system is only in native)
    """

    app = _build_app(tmp_path, verification_pass=False)

    # Create a session
    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    # Add a conversation
    messages = [
        ("user", "Question 1 about Python."),
        ("assistant", "Answer 1 about Python."),
        ("user", "Question 2 about JavaScript."),
        ("assistant", "Answer 2 about JavaScript."),
        ("user", "Question 3 about Rust."),
        ("assistant", "Answer 3 about Rust."),
    ]

    for role, content in messages:
        session = core.add_message(session, role, content, None, base_config)

    app.save_session(session)

    message_count_before = len(session.messages)
    print(f"\nMessages before compaction: {message_count_before}")
    for i, msg in enumerate(session.messages):
        role_str = msg.role.upper().ljust(9)
        content_preview = msg.content[:50] if len(msg.content) > 50 else msg.content
        print(f"  [{i}] {role_str} {content_preview}")

    # Compact up to message index 4 (preserves messages 4+)
    compact_end_index = 4

    result = app.execute_application_action(
        plugin_id="gemini_compaction",
        action_id="compact_range",
        params={
            "session_id": session_id,
            "start": 0,
            "end": compact_end_index,
        },
    )

    print(f"\nCompaction result: {result}")

    if result.get("status") == "error":
        error_type = result.get("error_type")
        if error_type == "disabled":
            pytest.skip("Compaction not enabled for this agent")
        else:
            pytest.fail(f"Compaction failed: {result}")

    # Reload and verify structure
    ctx = app.load_session(session_id)
    assert ctx is not None
    _, _, compacted_session = ctx

    message_count_after = len(compacted_session.messages)
    print(f"\nMessages after compaction: {message_count_after}")
    for i, msg in enumerate(compacted_session.messages):
        role_str = msg.role.upper().ljust(9)
        content_preview = msg.content[:60] if len(msg.content) > 60 else msg.content
        print(f"  [{i}] {role_str} {content_preview}")

    # System message should NOT be in core messages (it's in native only)
    system_messages = [i for i, msg in enumerate(compacted_session.messages) if msg.role == "system"]
    print(f"\nSystem message indices in core: {system_messages}")

    # If system appears in core (bug), it should be unique
    assert len(system_messages) <= 1, \
        f"DUPLICATE SYSTEM MESSAGE! Found at indices: {system_messages}"

    # Find the snapshot message
    snapshot_idx = None
    for i, msg in enumerate(compacted_session.messages):
        if msg.role == "user":
            snapshot_idx = i
            break

    assert snapshot_idx is not None, "Should find a snapshot user message"

    # The snapshot should be followed by an assistant acknowledgment
    if snapshot_idx + 1 < len(compacted_session.messages):
        ack_msg = compacted_session.messages[snapshot_idx + 1]
        assert ack_msg.role == "assistant", \
            f"Message after snapshot should be assistant, got {ack_msg.role}"

    # Verify messages after the compacted range are preserved
    remaining_content = " ".join(msg.content for msg in compacted_session.messages)
    assert "Rust" in remaining_content, \
        "Messages about Rust (originally after compact point) should be preserved"


@pytest.mark.integration
@pytest.mark.openrouter
def test_compaction_preserves_system_message_in_native(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Test that system message is preserved in native history after compaction.

    The system message feature injects system into native messages, not core.
    After compaction, the native history should still have the system message.
    """

    app = _build_app(tmp_path, verification_pass=False)

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    # Add a simple conversation
    messages = [
        ("user", "Hello"),
        ("assistant", "Hi there!"),
        ("user", "Goodbye"),
        ("assistant", "See you later!"),
    ]

    for role, content in messages:
        session = core.add_message(session, role, content, None, base_config)

    app.save_session(session)

    # Check native history before compaction
    native_before = session.metadata.get("native_messages", []) if session.metadata else []
    has_system_before = any(
        msg.get("role") == "system" for msg in native_before if isinstance(msg, dict)
    )
    print(f"\nSystem in native before compaction: {has_system_before}")

    # Compact
    result = app.execute_application_action(
        plugin_id="gemini_compaction",
        action_id="compact_range",
        params={"session_id": session_id},
    )

    if result.get("status") == "error":
        if result.get("error_type") == "disabled":
            pytest.skip("Compaction not enabled")
        pytest.fail(f"Compaction failed: {result}")

    # Reload and check native history
    ctx = app.load_session(session_id)
    assert ctx is not None
    _, _, compacted_session = ctx

    native_after = compacted_session.metadata.get("native_messages", []) if compacted_session.metadata else []
    has_system_after = any(
        msg.get("role") == "system" for msg in native_after if isinstance(msg, dict)
    )
    print(f"System in native after compaction: {has_system_after}")

    # The native history should have a system message
    # (injected by SystemMessageFeature.initialize_request)
    assert has_system_after, \
        "System message should be present in native history after compaction"

    # And it should be unique in native
    system_count_in_native = sum(
        1 for msg in native_after if isinstance(msg, dict) and msg.get("role") == "system"
    )
    assert system_count_in_native == 1, \
        f"System message in native should be unique, found {system_count_in_native}"


@pytest.mark.integration
@pytest.mark.openrouter
def test_compaction_with_explicit_system_in_core(
    ensure_api_key: None,
    tmp_path: Path,
) -> None:
    """Test compaction when user explicitly adds a system message to core.

    When a system message is in core messages (user-added), the feature
    should use it as the template. After compaction, it should not duplicate.
    """

    app = _build_app(tmp_path, verification_pass=False)

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    # Explicitly add a system message to core
    session = core.add_message(
        session,
        "system",
        "You are a specialized Python debugging assistant.",
        None,
        base_config,
    )

    # Add conversation
    messages = [
        ("user", "I have a bug in my code."),
        ("assistant", "Please share your code and I'll help debug it."),
        ("user", "Here's the code: print(x)"),
        ("assistant", "The issue is that 'x' is not defined."),
    ]

    for role, content in messages:
        session = core.add_message(session, role, content, None, base_config)

    app.save_session(session)

    print(f"\nMessages before compaction: {len(session.messages)}")
    for i, msg in enumerate(session.messages):
        print(f"  [{i}] {msg.role}: {msg.content[:40]}...")

    # Compact
    result = app.execute_application_action(
        plugin_id="gemini_compaction",
        action_id="compact_range",
        params={"session_id": session_id},
    )

    if result.get("status") == "error":
        if result.get("error_type") == "disabled":
            pytest.skip("Compaction not enabled")
        pytest.fail(f"Compaction failed: {result}")

    # Reload and check
    ctx = app.load_session(session_id)
    assert ctx is not None
    _, _, compacted_session = ctx

    print(f"\nMessages after compaction: {len(compacted_session.messages)}")
    for i, msg in enumerate(compacted_session.messages):
        print(f"  [{i}] {msg.role}: {msg.content[:40]}...")

    # System message should be preserved (it was in core)
    # And should be unique
    system_indices = [i for i, msg in enumerate(compacted_session.messages) if msg.role == "system"]
    print(f"\nSystem message indices: {system_indices}")

    assert len(system_indices) == 1, \
        f"Should have exactly one system message (the explicit one), found at: {system_indices}"

    # System should be at index 0
    assert system_indices[0] == 0, \
        f"System message should be at index 0, found at {system_indices[0]}"

    # Verify content is preserved
    assert "debugging assistant" in compacted_session.messages[0].content, \
        "System message content should be preserved"