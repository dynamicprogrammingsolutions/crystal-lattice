import pytest
import tempfile
from pathlib import Path
from agent_core.types import Session, Message
from agent_app.application_future import AgentApplication
from agent_app.sessions import FilesystemSessionStore
from agent_app.events import InMemoryEventStore
from agent_core.core import AgentCore

@pytest.fixture
def test_app():
    with tempfile.TemporaryDirectory() as td:
        dummy_cfg = Path(td) / "config.json"
        dummy_cfg.write_text('{"agents": {}}')
        app = AgentApplication(
            config_path=str(dummy_cfg),
            session_root=td
        )
        core = AgentCore()
        app._session_store = FilesystemSessionStore(Path(td), core)
        app._event_store = InMemoryEventStore()
        
        # Add basic provider for _resolve_runtime_for_session
        app._get_agent_base_config = lambda agent_id: {"provider": "dummy"}
        app._resolve_runtime_for_session = lambda session, overrides=None: (core, {"provider": "dummy"}, {"provider": "dummy"})
        
        yield app

def test_submit_interceptor_prompt_answer_valid(test_app):
    session = Session(
        session_id="test",
        messages=[
            Message(
                role="assistant",
                content="test",
                metadata={
                    "interception_current": {
                        "phase": "tool_call",
                        "tool_call_id": "call_123",
                        "pending_prompt": {"id": "prompt_1"},
                        "request_overrides": {"model": "foo"}
                    }
                }
            )
        ]
    )
    test_app.save_session(session)
    
    result = test_app.submit_interceptor_prompt_answer(
        session_id="test",
        message_index=0,
        phase="tool_call",
        tool_call_id="call_123",
        prompt_id="prompt_1",
        button_id="btn_1",
        values={"x": 1}
    )
    
    assert result["resume_ready"] is True
    assert result["overrides"] == {"model": "foo"}
    updated_session = result["session"]
    md = updated_session.messages[0].metadata
    
    assert md["interception_current"].get("pending_prompt") is None
    assert len(md["interception_phases"]) == 1
    assert md["interception_phases"][0]["type"] == "prompt_response"
    assert md["interception_phases"][0]["button_id"] == "btn_1"
    assert md["interception_phases"][0]["values"] == {"x": 1}

def test_submit_interceptor_prompt_answer_invalid(test_app):
    session = Session(
        session_id="test",
        messages=[
            Message(
                role="assistant",
                content="test",
                metadata={
                    "interception_current": {
                        "phase": "tool_call",
                        "tool_call_id": "call_123",
                        "pending_prompt": {"id": "prompt_1"},
                    }
                }
            )
        ]
    )
    test_app.save_session(session)
    
    with pytest.raises(ValueError, match="message_index out of range"):
        test_app.submit_interceptor_prompt_answer("test", 1, "tool_call", "call_123", "prompt_1", "btn_1")

    with pytest.raises(ValueError, match="Phase mismatch"):
        test_app.submit_interceptor_prompt_answer("test", 0, "tool_result", "call_123", "prompt_1", "btn_1")

    with pytest.raises(ValueError, match="Tool call ID mismatch"):
        test_app.submit_interceptor_prompt_answer("test", 0, "tool_call", "call_456", "prompt_1", "btn_1")

    with pytest.raises(ValueError, match="Prompt ID mismatch"):
        test_app.submit_interceptor_prompt_answer("test", 0, "tool_call", "call_123", "prompt_2", "btn_1")


def test_submit_interceptor_prompt_answer_preserves_overrides(test_app):
    """Verify that original request overrides are preserved and returned."""
    original_overrides = {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000}
    session = Session(
        session_id="test_overrides",
        messages=[
            Message(
                role="assistant",
                content="test",
                metadata={
                    "interception_current": {
                        "phase": "tool_call",
                        "tool_call_id": "call_override",
                        "pending_prompt": {"id": "prompt_override"},
                        "request_overrides": original_overrides
                    }
                }
            )
        ]
    )
    test_app.save_session(session)
    
    result = test_app.submit_interceptor_prompt_answer(
        session_id="test_overrides",
        message_index=0,
        phase="tool_call",
        tool_call_id="call_override",
        prompt_id="prompt_override",
        button_id="allow",
        values={}
    )
    
    # Verify overrides are preserved exactly
    assert result["overrides"] == original_overrides
    assert result["resume_ready"] is True


def test_submit_interceptor_prompt_answer_no_overrides(test_app):
    """Verify graceful handling when no request_overrides exist."""
    session = Session(
        session_id="test_no_overrides",
        messages=[
            Message(
                role="assistant",
                content="test",
                metadata={
                    "interception_current": {
                        "phase": "tool_call",
                        "tool_call_id": "call_no_override",
                        "pending_prompt": {"id": "prompt_no_override"},
                        # No request_overrides field
                    }
                }
            )
        ]
    )
    test_app.save_session(session)
    
    result = test_app.submit_interceptor_prompt_answer(
        session_id="test_no_overrides",
        message_index=0,
        phase="tool_call",
        tool_call_id="call_no_override",
        prompt_id="prompt_no_override",
        button_id="allow",
        values={}
    )
    
    # Should return empty dict when no overrides
    assert result["overrides"] == {}
    assert result["resume_ready"] is True
