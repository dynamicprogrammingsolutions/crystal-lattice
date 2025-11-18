"""
Unit tests for AgentCore (functional architecture).
"""

import pytest
from agent_core import AgentCore, Session, Message
from .dummy_provider import DummyProvider
from .dummy_feature import DummyFeature
from .dummy_tool import DummyCalculator


def test_create_session():
    """Test session creation."""
    core = AgentCore()
    session = core.create_session()
    
    assert isinstance(session, Session)
    assert len(session.messages) == 0
    assert session.session_id is not None


def test_create_session_with_id():
    """Test session creation with specific ID."""
    core = AgentCore()
    session = core.create_session(session_id="my-session")
    
    assert session.session_id == "my-session"


def test_add_message():
    """Test adding message to session (functional)."""
    core = AgentCore()
    session = core.create_session()
    
    new_session = core.add_message(session, "user", "Hello!")
    
    # Original unchanged
    assert len(session.messages) == 0
    # New session has message
    assert len(new_session.messages) == 1
    assert new_session.messages[0].role == "user"
    assert new_session.messages[0].content == "Hello!"


def test_add_multiple_messages():
    """Test adding multiple messages (functional chaining)."""
    core = AgentCore()
    session = core.create_session()
    
    session = core.add_message(session, "system", "You are helpful")
    session = core.add_message(session, "user", "Hello")
    session = core.add_message(session, "assistant", "Hi there")
    
    assert len(session.messages) == 3
    assert session.messages[0].role == "system"
    assert session.messages[1].role == "user"
    assert session.messages[2].role == "assistant"


def test_add_message_with_metadata():
    """Test adding message with metadata."""
    core = AgentCore()
    session = core.create_session()
    
    session = core.add_message(
        session,
        "assistant",
        "Response",
        metadata={"model": "gpt-4"}
    )
    
    assert session.messages[0].metadata
    assert session.messages[0].metadata["model"] == "gpt-4"


def test_get_config_schema_empty():
    """Test config schema with no plugins."""
    core = AgentCore()
    schema = core.get_config_schema()
    
    assert isinstance(schema, dict)
    assert len(schema) == 0


def test_get_config_schema_with_plugins():
    """Test config schema with registered plugins."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(DummyFeature)
    core.register_tool(DummyCalculator)
    
    schema = core.get_config_schema()
    
    # Check that all plugins are in schema
    assert "dummy_provider" in schema or "DummyProvider" in schema
    assert "dummy_feature" in schema or "DummyFeature" in schema
    assert "dummy_calculator" in schema or "DummyCalculator" in schema
    
    # Check schema structure (behavioral test)
    provider_schema = schema.get("dummy_provider", schema.get("DummyProvider"))
    assert provider_schema is not None
    assert "model" in provider_schema
    
    feature_schema = schema.get("dummy_feature", schema.get("DummyFeature"))
    assert feature_schema is not None
    assert "prefix" in feature_schema


def test_get_ui_schema_empty():
    """Test UI schema with no plugins."""
    core = AgentCore()
    schema = core.get_ui_schema()
    
    assert isinstance(schema, dict)
    assert len(schema) == 0


def test_get_ui_schema_with_plugins():
    """Test UI schema with registered plugins."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(DummyFeature)
    
    schema = core.get_ui_schema()
    
    assert "dummy_provider" in schema or "DummyProvider" in schema
    assert "dummy_feature" in schema or "DummyFeature" in schema


def test_get_tool_schemas():
    """Test getting tool schemas."""
    core = AgentCore()
    core.register_tool(DummyCalculator)
    
    config = {}
    schemas = core.get_tool_schemas(config)
    
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "add"


def test_export_session():
    """Test session export."""
    core = AgentCore()
    session = core.create_session(session_id="test")
    session = core.add_message(session, "user", "Hello")
    
    exported = core.export_session(session)
    
    assert isinstance(exported, str)
    assert "test" in exported
    assert "Hello" in exported


def test_import_session():
    """Test session import."""
    core = AgentCore()
    session1 = core.create_session(session_id="test")
    session1 = core.add_message(session1, "user", "Hello")
    
    exported = core.export_session(session1)
    session2 = core.import_session(exported)
    
    assert session2.session_id == "test"
    assert len(session2.messages) == 1
    assert session2.messages[0].content == "Hello"


def test_send_request_without_provider():
    """Test error when sending request without provider."""
    core = AgentCore()
    session = core.create_session()
    config = {}
    
    with pytest.raises(RuntimeError, match="No provider registered"):
        core.send_request(session, config)

def test_discover_and_register_plugins():
    core = AgentCore()
    summary = core.discover_and_register([
        "tests.dummy_provider",
        "tests.dummy_feature",
        "tests.dummy_tool",
        "tests.dummy_extension",
    ])

    # At least provider discovered
    assert summary["providers"]

    # Run a basic streaming flow to ensure discovered registration works
    config = {"model": "test-model", "enabled": True}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")

    final_message = None
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            final_message = chunk["messages"][-1]

    assert final_message is not None
    assert "Echo: Hello" in final_message["content"]
    # Extension may add metadata
    assert "metadata" in final_message
