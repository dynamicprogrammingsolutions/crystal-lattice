"""
Integration tests for complete request/response cycles (functional architecture).
"""

import pytest
from agent_core import AgentCore
from .dummy_provider import DummyProvider
from .dummy_feature import DummyFeature
from .dummy_tool import DummyCalculator


def test_basic_request_response():
    """Test basic non-streaming request/response cycle."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    
    config = {"model": "test-model"}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    
    # Send request (functional - returns new session)
    new_session, response = core.send_request(session, config)
    
    # Original session unchanged
    assert len(session.messages) == 1
    # New session has response
    assert len(new_session.messages) == 2
    
    assert response["role"] == "assistant"
    assert "Echo: Hello" in response["content"]


def test_streaming_request_response():
    """Test streaming request/response cycle."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    
    config = {"model": "test-model"}
    session = core.create_session()
    session = core.add_message(session, "user", "Test")
    
    partials = []
    final_session = None
    final_message = None
    
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "partial":
            partials.append(chunk["content"])
        elif chunk["type"] == "final":
            final_session = chunk["session"]
            final_message = chunk["message"]
    
    assert len(partials) > 0
    assert final_session is not None
    assert final_message is not None
    assert "Echo: Test" in final_message["content"]
    
    # Original session unchanged
    assert len(session.messages) == 1
    # Final session has response
    assert len(final_session.messages) == 2


def test_request_with_feature_plugin():
    """Test request with feature plugin modification."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(DummyFeature)
    
    config = {"model": "test", "prefix": "[PREFIX]"}
    session = core.create_session()
    session = core.add_message(session, "user", "Hi")
    
    session, response = core.send_request(session, config)
    
    assert response["content"].startswith("[PREFIX]")
    assert "Echo: Hi" in response["content"]


def test_functional_chaining():
    """Test functional chaining of operations."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    
    config = {"model": "test"}
    
    # Functional chaining (explicit)
    session = core.create_session()
    session = core.add_message(session, "system", "You are helpful")
    session = core.add_message(session, "user", "Hello")
    
    assert len(session.messages) == 2


def test_config_managed_by_application():
    """Test that config is managed by application, not core."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    
    # Application manages different configs
    config1 = {"model": "model-1"}
    config2 = {"model": "model-2"}
    
    session = core.create_session()
    session = core.add_message(session, "user", "Test")
    
    # Same session, different configs (application's responsibility)
    session1, response1 = core.send_request(session, config1)
    session2, response2 = core.send_request(session, config2)
    
    # Both work, application manages which config to use
    assert response1["content"] == "Echo: Test"
    assert response2["content"] == "Echo: Test"


def test_session_export_import():
    """Test exporting and importing sessions."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    
    config = {"model": "test"}
    session = core.create_session(session_id="test-123")
    session = core.add_message(session, "user", "Hello")
    session, response = core.send_request(session, config)
    
    # Export
    exported = core.export_session(session)
    
    # Import
    imported_session = core.import_session(exported)
    
    assert imported_session.session_id == "test-123"
    assert len(imported_session.messages) == 2
    assert imported_session.messages[0].content == "Hello"
    assert "Echo: Hello" in imported_session.messages[1].content


def test_conversation_flow():
    """Test complete conversation flow with multiple turns."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    
    config = {"model": "test"}
    
    # Turn 1
    session = core.create_session()
    session = core.add_message(session, "user", "What is 2+2?")
    session, response1 = core.send_request(session, config)
    assert "Echo: What is 2+2?" in response1["content"]
    assert len(session.messages) == 2
    
    # Turn 2
    session = core.add_message(session, "user", "Thank you")
    session, response2 = core.send_request(session, config)
    assert "Echo: Thank you" in response2["content"]
    assert len(session.messages) == 4


def test_streaming_with_feature():
    """Test streaming with feature plugin."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(DummyFeature)
    
    config = {"model": "test", "prefix": "[TEST]"}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    
    final_session = None
    final_message = None
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            final_session = chunk["session"]
            final_message = chunk["message"]
    
    assert final_session is not None
    assert final_message is not None
    assert "[TEST]" in final_message["content"]


def test_multiple_features():
    """Test multiple feature plugins."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(DummyFeature)
    
    config = {"model": "test", "prefix": "[A]"}
    session = core.create_session()
    session = core.add_message(session, "user", "Test")
    
    session, response = core.send_request(session, config)
    
    # Feature applied
    assert "[A]" in response["content"]


def test_tool_schemas():
    """Test getting tool schemas."""
    core = AgentCore()
    core.register_tool(DummyCalculator)
    
    config = {}
    schemas = core.get_tool_schemas(config)
    
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "add"


def test_error_handling_no_provider():
    """Test error when no provider registered."""
    core = AgentCore()
    session = core.create_session()
    config = {}
    
    with pytest.raises(RuntimeError, match="No provider registered"):
        core.send_request(session, config)


def test_pure_function_behavior():
    """Test that core methods are pure functions."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    
    config = {"model": "test"}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    
    # Same inputs should work consistently
    session1, response1 = core.send_request(session, config)
    session2, response2 = core.send_request(session, config)
    
    # Both produce same results
    assert response1["content"] == response2["content"]
    # Original session still unchanged
    assert len(session.messages) == 1


def test_application_state_management():
    """Test that application manages sessions independently."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    
    config = {"model": "test"}
    
    # Application creates multiple independent sessions
    session_a = core.create_session(session_id="user-a")
    session_b = core.create_session(session_id="user-b")
    
    session_a = core.add_message(session_a, "user", "Hello from A")
    session_b = core.add_message(session_b, "user", "Hello from B")
    
    # Sessions are independent (behavior test)
    assert session_a.messages[0].content == "Hello from A"
    assert session_b.messages[0].content == "Hello from B"
    assert session_a.session_id != session_b.session_id
