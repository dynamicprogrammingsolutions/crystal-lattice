"""Integration-style tests for SystemMessageFeature using an echo provider.

These tests exercise both:

- Structural / permanent system message behavior via AgentCore flows
  (persistent template-level system messages in the session's native history).
- Per-request rendered system message behavior via a provider that echoes
  the effective system and user messages it sees for a given request.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agent_core import AgentCore
from feature_system_message.system_message_feature import SystemMessageFeature
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider


def _get_system_native(native_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [m for m in native_messages or [] if m.get("role") == "system"]


def _make_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(EchoOpenAILikeProvider)
    core.register_feature(SystemMessageFeature)
    return core


def test_permanent_system_message_added_and_persisted_in_native_history() -> None:
    """First request without a user system should insert a template system
    message into the provider-native history and keep it across turns.
    """

    core = _make_core()
    config: Dict[str, Any] = {
        "model": "test-model",
        "system_message": {"template": "Hello {{NAME}}"},
    }

    # Turn 1: only user message
    session = core.create_session()
    session = core.add_message(session, "user", "Hi")

    session1, responses1 = core.send_request(session, config)
    _ = responses1

    # Original session unchanged
    assert len(session.messages) == 1

    native1 = session1.metadata.get("native_messages") or []
    sys_native1 = _get_system_native(native1)
    assert len(sys_native1) == 1
    assert sys_native1[0].get("content") == "Hello {{NAME}}"
    assert [message.role for message in session1.messages] == ["system", "user", "assistant"]
    assert session1.messages[0].content == "Hello {{NAME}}"

    # Turn 2: add another user message, ensure we still have exactly one
    # permanent system template in native history (no duplication).
    session1 = core.add_message(session1, "user", "Hi again", config=config)
    session2, responses2 = core.send_request(session1, config)
    _ = responses2

    native2 = session2.metadata.get("native_messages") or []
    sys_native2 = _get_system_native(native2)
    assert len(sys_native2) == 1
    assert sys_native2[0].get("content") == "Hello {{NAME}}"
    assert len([message for message in session2.messages if message.role == "system"]) == 1


def test_no_permanent_system_message_when_user_system_present() -> None:
    """If the user supplies a system message, the feature must not insert
    an additional permanent system message.
    """

    core = _make_core()
    config: Dict[str, Any] = {
        "model": "test-model",
        "system_message": {"template": "Hello {{NAME}}"},
    }

    session = core.create_session()
    session = core.add_message(session, "system", "User system {{NAME}}")
    session = core.add_message(session, "user", "Hi")

    session1, responses = core.send_request(session, config)
    _ = responses

    native = session1.metadata.get("native_messages") or []
    sys_native = _get_system_native(native)

    # Only the user-provided system message should be present
    assert len(sys_native) == 1
    assert sys_native[0].get("content") == "User system {{NAME}}"


def test_rendered_system_message_uses_config_template_when_no_user_system() -> None:
    """Per-request rendering should use the config template when there is
    no user system message, and the rendered content should appear in the
    echo provider's assistant response.
    """

    core = _make_core()
    config: Dict[str, Any] = {
        "model": "test-model",
        "system_message": {
            "template": "Hello {{NAME}}",
            "variables": {"NAME": "Alice"},
        },
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Hi")

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert responses
    final = responses[-1]
    text = final.get("content", "") or ""

    # Echo provider should see the rendered system message for this
    # request, even though the stored history keeps the template.
    assert "Hello Alice" in text


def test_rendered_system_message_uses_user_system_template_when_present() -> None:
    """When the user supplies a system message containing a template, that
    template should take precedence over the config template during
    per-request rendering.
    """

    core = _make_core()
    config: Dict[str, Any] = {
        "model": "test-model",
        "system_message": {
            "template": "IGNORED TEMPLATE",
            "variables": {"NAME": "Bob"},
        },
    }

    session = core.create_session()
    session = core.add_message(session, "system", "User system {{NAME}}")
    session = core.add_message(session, "user", "Hi")

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert responses
    final = responses[-1]
    text = final.get("content", "") or ""

    # Response must reflect the rendered *user* system message.
    assert "User system Bob" in text


def test_rendered_variables_change_between_requests_but_history_kept_templated() -> None:
    """Variable values should be recomputed per request while the stored
    system message template in native history remains unchanged.
    """

    core = _make_core()

    # Session with a user system template
    session = core.create_session()
    session = core.add_message(session, "system", "Value: {{VAL}}")
    session = core.add_message(session, "user", "Hi")

    # Turn 1: VAL = one
    config1: Dict[str, Any] = {
        "model": "test-model",
        "system_message": {
            "template": "IGNORED",
            "variables": {"VAL": "one"},
        },
    }
    session1, responses1 = core.send_request(session, config1)
    final1 = responses1[-1]
    text1 = final1.get("content", "") or ""
    assert "Value: one" in text1

    # Native history should still have the template, not the rendered text
    native1 = session1.metadata.get("native_messages") or []
    sys_native1 = _get_system_native(native1)
    assert sys_native1
    assert sys_native1[0].get("content") == "Value: {{VAL}}"

    # Turn 2: VAL = two
    config2: Dict[str, Any] = {
        "model": "test-model",
        "system_message": {
            "template": "IGNORED",
            "variables": {"VAL": "two"},
        },
    }
    session2, responses2 = core.send_request(session1, config2)
    final2 = responses2[-1]
    text2 = final2.get("content", "") or ""
    assert "Value: two" in text2

    # Stored native history should still hold the template.
    native2 = session2.metadata.get("native_messages") or []
    sys_native2 = _get_system_native(native2)
    assert sys_native2
    assert sys_native2[0].get("content") == "Value: {{VAL}}"
