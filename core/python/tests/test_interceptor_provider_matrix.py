"""
Provider-matrix integration test for tool interception.

Tests the full happy path (intercept, suspend, answer, resume, completion)
on both openrouter and openai_responses providers to ensure native-history
synchronization works correctly.
"""
import json
import os
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any

from agent_core.core import AgentCore
from agent_core.types import Session, Message
from agent_app.application_future import AgentApplication


def _skip_if_no_keys() -> None:
    """Skip test if API keys are not available."""
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set")
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")


def _make_interceptor_config(tmp_path: Path, provider: str) -> Path:
    """Create config with interceptor and specified provider."""
    if provider == "openrouter":
        provider_path = "path:${env:BUILTIN_PLUGINS}/openrouter"
        model = "openai/gpt-4o-mini"
    elif provider == "openai_responses":
        provider_path = "path:${env:BUILTIN_PLUGINS}/openai_responses"
        model = "gpt-4o-mini"
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    config = {
        "agents": {
            "default": {
                "provider": provider,
                "model": model,
                "plugins": [
                    provider_path,
                    "plugins.tool_interceptor_metadata_preserver.ToolInterceptorMetadataPreserver",
                ],
                "tools": [
                    "tests.interceptor_tool.InterceptorCalculator",
                ],
            }
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config, indent=2))
    return config_path


def _run_intercept_and_approve_flow(
    app: AgentApplication, provider: str
) -> Session:
    """Run a complete intercept, approve, and resume flow."""
    core, base_config, session = app.create_session("default")
    
    # Add a message that will trigger the interceptor
    tool_call: Dict[str, Any] = {
        "id": "call_matrix_test",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 5, "b": 7})},
    }
    session = core.add_message(
        session, "assistant", "", {"tool_calls": [tool_call]}, config=base_config
    )
    app.save_session(session)
    
    # Send request - should suspend at interceptor prompt
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    suspended_session = checkpoints[-1]["session"]
    assert isinstance(suspended_session, Session)
    
    # Verify suspension: no tool message, pending prompt exists
    assert not any(m.role == "tool" for m in suspended_session.messages)
    assistant = suspended_session.messages[-1]
    current = (assistant.metadata or {}).get("interception_current")
    assert isinstance(current, dict)
    pending_prompt = current.get("pending_prompt")
    assert isinstance(pending_prompt, dict)
    prompt_id = pending_prompt.get("id")
    assert isinstance(prompt_id, str)
    
    # Submit approval using new API
    result = app.submit_interceptor_prompt_answer(
        session_id=suspended_session.session_id,
        message_index=len(suspended_session.messages) - 1,
        phase="tool_call",
        tool_call_id="call_matrix_test",
        prompt_id=prompt_id,
        button_id="allow",
        values={},
    )
    assert result["resume_ready"] is True
    approved_session = result["session"]
    
    # Verify prompt cleared
    approved_md = approved_session.messages[-1].metadata
    assert approved_md.get("interception_current", {}).get("pending_prompt") is None
    assert len(approved_md.get("interception_phases", [])) == 1
    
    # Resume execution
    events2 = list(app.send_request(core, approved_session, base_config, overrides=None, stream=False))
    checkpoints2 = [ev for ev in events2 if ev.get("type") == "session_checkpoint"]
    final_session = checkpoints2[-1]["session"]
    assert isinstance(final_session, Session)
    
    # Verify completion: tool message exists, no pending prompt
    tool_messages = [m for m in final_session.messages if m.role == "tool"]
    assert tool_messages, f"No tool messages in {provider} final session"
    assert "Result:" in tool_messages[-1].content or "12" in tool_messages[-1].content
    
    # Verify no lingering pending prompt
    final_assistant = [m for m in final_session.messages if m.role == "assistant"][-1]
    final_current = (final_assistant.metadata or {}).get("interception_current")
    if final_current:
        assert final_current.get("pending_prompt") is None
    
    # Verify native_messages synchronized (if present)
    if "native_messages" in final_session.metadata:
        native = final_session.metadata["native_messages"]
        assert isinstance(native, list)
        # Check that _metadata has interception_phases
        for msg_idx, msg in enumerate(final_session.messages):
            if msg.role == "assistant" and msg.metadata and "interception_phases" in msg.metadata:
                native_indices = msg.metadata.get("native_indices")
                if native_indices:
                    for ni in native_indices:
                        native_msg = native[ni]
                        native_md = native_msg.get("_metadata", {})
                        assert "interception_phases" in native_md, \
                            f"{provider}: interception_phases missing from native message {ni}"
    
    return final_session


@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.requires_keys
def test_interceptor_happy_path_openrouter() -> None:
    """Test full intercept + approve flow on openrouter provider."""
    _skip_if_no_keys()
    
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        config_path = _make_interceptor_config(tmp_path, "openrouter")
        session_root = tmp_path / "sessions"
        app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
        
        final_session = _run_intercept_and_approve_flow(app, "openrouter")
        
        # Reload session and verify persistence
        reloaded = app.load_session_record(final_session.session_id)
        assert reloaded is not None
        assert len([m for m in reloaded.messages if m.role == "tool"]) > 0


@pytest.mark.integration
@pytest.mark.requires_keys
def test_interceptor_happy_path_openai_responses() -> None:
    """Test full intercept + approve flow on openai_responses provider."""
    _skip_if_no_keys()
    
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        config_path = _make_interceptor_config(tmp_path, "openai_responses")
        session_root = tmp_path / "sessions"
        app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
        
        final_session = _run_intercept_and_approve_flow(app, "openai_responses")
        
        # Reload session and verify persistence
        reloaded = app.load_session_record(final_session.session_id)
        assert reloaded is not None
        assert len([m for m in reloaded.messages if m.role == "tool"]) > 0


@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.requires_keys
def test_no_stale_prompt_after_reload_openrouter() -> None:
    """Verify no stale pending prompt persists after reload (openrouter)."""
    _skip_if_no_keys()
    
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        config_path = _make_interceptor_config(tmp_path, "openrouter")
        session_root = tmp_path / "sessions"
        app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
        
        final_session = _run_intercept_and_approve_flow(app, "openrouter")
        
        # Create new app instance and reload
        app2 = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
        reloaded = app2.load_session_record(final_session.session_id)
        assert reloaded is not None
        
        # Verify no pending prompt in any assistant message
        for msg in reloaded.messages:
            if msg.role == "assistant" and msg.metadata:
                current = msg.metadata.get("interception_current")
                if current:
                    assert current.get("pending_prompt") is None, \
                        f"Stale pending_prompt found after reload in {msg.metadata}"


@pytest.mark.integration
@pytest.mark.requires_keys
def test_no_stale_prompt_after_reload_openai_responses() -> None:
    """Verify no stale pending prompt persists after reload (openai_responses)."""
    _skip_if_no_keys()
    
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        config_path = _make_interceptor_config(tmp_path, "openai_responses")
        session_root = tmp_path / "sessions"
        app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
        
        final_session = _run_intercept_and_approve_flow(app, "openai_responses")
        
        # Create new app instance and reload
        app2 = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
        reloaded = app2.load_session_record(final_session.session_id)
        assert reloaded is not None
        
        # Verify no pending prompt in any assistant message
        for msg in reloaded.messages:
            if msg.role == "assistant" and msg.metadata:
                current = msg.metadata.get("interception_current")
                if current:
                    assert current.get("pending_prompt") is None, \
                        f"Stale pending_prompt found after reload in {msg.metadata}"
