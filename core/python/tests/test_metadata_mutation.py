import pytest
from agent_core.core import AgentCore
from agent_core.types import Session, Message
from tests.dummy_provider import DummyProvider

def test_modify_message_metadata_core_only():
    core = AgentCore()
    session = Session(session_id="test", messages=[Message(role="user", content="hello", metadata={"foo": "bar"})], metadata={})
    
    new_session = core.modify_message_metadata(session, 0, {"foo": "baz", "extra": 1})
    assert len(new_session.messages) == 1
    assert new_session.messages[0].metadata == {"foo": "baz", "extra": 1}

def test_modify_message_metadata_with_native():
    core = AgentCore()
    core.register_provider(DummyProvider)
    config = {"provider": "dummy_provider", "model": "test"}
    session = Session(session_id="test", messages=[], metadata={})
    
    # Add a message to get native history
    session = core.add_message(session, "user", "hello", metadata={"foo": "bar"}, config=config)
    assert len(session.messages) == 1
    assert session.messages[0].metadata["foo"] == "bar"
    assert "native_indices" in session.messages[0].metadata
    
    # Update metadata
    new_session = core.modify_message_metadata(session, 0, {"foo": "baz", "extra": 1}, config=config)
    
    # Verify core message
    assert len(new_session.messages) == 1
    assert new_session.messages[0].metadata["foo"] == "baz"
    assert new_session.messages[0].metadata["extra"] == 1
    assert "native_indices" in new_session.messages[0].metadata
    
    # Verify native message _metadata
    native = new_session.metadata["native_messages"]
    assert len(native) == 1
    assert native[0]["_metadata"]["foo"] == "baz"
    assert native[0]["_metadata"]["extra"] == 1


def test_modify_message_metadata_syncs_interception_phases():
    """Verify interception_phases are synced to native _metadata correctly."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    config = {"provider": "dummy_provider", "model": "test"}
    session = Session(session_id="test", messages=[], metadata={})
    
    # Add a message
    session = core.add_message(session, "assistant", "thinking...", config=config)
    
    # Simulate interception lifecycle metadata
    interception_md = {
        "interception_current": {
            "phase": "tool_call",
            "tool_call_id": "call_sync_test",
        },
        "interception_phases": [
            {
                "type": "prompt_response",
                "phase": "tool_call",
                "tool_call_id": "call_sync_test",
                "prompt_id": "prompt_1",
                "button_id": "allow",
                "values": {},
            }
        ],
    }
    
    # Merge with existing metadata
    existing = dict(session.messages[0].metadata or {})
    existing.update(interception_md)
    
    # Update metadata
    updated_session = core.modify_message_metadata(session, 0, existing, config=config)
    
    # Verify interception_phases in native _metadata
    native = updated_session.metadata["native_messages"]
    assert len(native) == 1
    native_md = native[0]["_metadata"]
    
    assert "interception_current" in native_md
    assert native_md["interception_current"]["phase"] == "tool_call"
    assert native_md["interception_current"]["tool_call_id"] == "call_sync_test"
    
    assert "interception_phases" in native_md
    assert len(native_md["interception_phases"]) == 1
    assert native_md["interception_phases"][0]["type"] == "prompt_response"
    assert native_md["interception_phases"][0]["prompt_id"] == "prompt_1"


def test_modify_message_metadata_preserves_tool_result():
    """Verify tool_result is preserved during metadata mutation."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    config = {"provider": "dummy_provider", "model": "test"}
    session = Session(session_id="test", messages=[], metadata={})
    
    # Add a tool message
    tool_result = {"success": True, "result": 42}
    session = core.add_message(
        session, "tool", "Result: 42", 
        metadata={"tool_call_id": "call_123"},
        config=config
    )
    # Manually set tool_result (normally done by tool execution)
    messages = list(session.messages)
    tool_msg = messages[-1]
    from agent_core.types import Message as Msg
    messages[-1] = Msg(
        role=tool_msg.role,
        content=tool_msg.content,
        metadata=tool_msg.metadata,
        multipart_content=tool_msg.multipart_content,
        tool_result=tool_result,
    )
    session = Session(
        session_id=session.session_id,
        messages=messages,
        metadata=session.metadata,
    )
    
    # Update metadata
    new_md = dict(tool_msg.metadata or {})
    new_md["extra_field"] = "preserved"
    updated_session = core.modify_message_metadata(session, 0, new_md, config=config)
    
    # Verify tool_result is preserved
    assert updated_session.messages[0].tool_result == tool_result
    assert updated_session.messages[0].metadata["extra_field"] == "preserved"

