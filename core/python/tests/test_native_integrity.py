from typing import Dict, Tuple
import pytest

from agent_core import AgentCore, Session, Message
from .dummy_provider import DummyProvider


def make_two_turn_session() -> Tuple[AgentCore, Dict, Session]:
    core = AgentCore()
    core.register_provider(DummyProvider)
    config = {"model": "test"}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    session, _ = core.send_request(session, config)
    return core, config, session


def test_integrity_violation_on_modified_messages():
    core, config, session = make_two_turn_session()
    # Tamper with messages directly without removing native history (delete last assistant message)
    hacked = Session(
        session_id=session.session_id,
        messages=session.messages[:-1],
        metadata=dict(session.metadata),
    )
    with pytest.raises(RuntimeError):
        core.add_message(hacked, "user", "Oops")


def test_integrity_violation_on_changed_content():
    core, config, session = make_two_turn_session()
    # Modify existing message content
    msgs = list(session.messages)
    msgs[0] = Message(role=msgs[0].role, content="Changed", metadata=msgs[0].metadata)
    hacked = Session(session_id=session.session_id, messages=msgs, metadata=dict(session.metadata))
    with pytest.raises(RuntimeError):
        core.add_message(hacked, "user", "Next")


def test_integrity_happy_path_add_via_core():
    core, config, session = make_two_turn_session()
    # Add via core (should succeed)
    session = core.add_message(session, "user", "Thanks")
    # Next send_request should work
    session, finals = core.send_request(session, config)
    assert finals[-1]["role"] == "assistant"


def test_bypass_by_removing_native_history():
    core, config, session = make_two_turn_session()
    # User intentionally removes native history to modify conversation
    md = dict(session.metadata)
    md.pop("native_messages", None)
    md.pop("native_messages_integrity", None)
    mutated = Session(session_id=session.session_id, messages=session.messages[:-1], metadata=md)
    # Should not raise, as there is no native history
    mutated = core.add_message(mutated, "user", "After removal")
    mutated, finals = core.send_request(mutated, config)
    assert finals[-1]["role"] == "assistant"
