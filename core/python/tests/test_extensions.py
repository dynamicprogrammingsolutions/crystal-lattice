"""
Tests for provider extension functionality.
"""

import pytest
from agent_core import AgentCore
from .dummy_provider import DummyProvider
from .dummy_extension import DummyExtension


def test_provider_with_extension():
    """Test provider with extension plugin."""
    core = AgentCore()
    core.register_provider(DummyProvider, extensions=[DummyExtension])
    
    config = {"model": "test", "prefix": "[EXT]", "enabled": True}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    
    final_session = None
    final_message = None
    
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            final_session = chunk["session"]
            final_message = chunk["messages"][-1]
    
    assert final_session is not None
    assert final_message is not None
    # Extension should add prefix
    assert "[EXT]" in final_message["content"]
    assert "Echo: Hello" in final_message["content"]
    # Check extension metadata
    assert "extension_processed_chunks" in final_message.get("metadata", {})


def test_extension_can_be_disabled():
    """Test that extension can be disabled via config."""
    core = AgentCore()
    core.register_provider(DummyProvider, extensions=[DummyExtension])
    
    config = {"model": "test", "prefix": "[EXT]", "enabled": False}
    session = core.create_session()
    session = core.add_message(session, "user", "Test")
    
    final_message = None
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            final_message = chunk["messages"][-1]
    
    # Extension disabled, so no prefix
    assert final_message is not None
    assert "[EXT]" not in final_message["content"]
    assert "Echo: Test" in final_message["content"]


def test_extension_chunk_counting():
    """Test that extension counts processed chunks."""
    core = AgentCore()
    core.register_provider(DummyProvider, extensions=[DummyExtension])
    
    config = {"model": "test", "enabled": True}
    session = core.create_session()
    session = core.add_message(session, "user", "Count chunks")
    
    chunk_count = 0
    final_message = None
    
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "partial":
            chunk_count += 1
        elif chunk["type"] == "final":
            final_message = chunk["messages"][-1]
    
    # Extension should have counted the same number of chunks
    assert final_message is not None
    assert final_message["metadata"]["extension_processed_chunks"] == chunk_count


def test_multiple_extensions():
    """Test provider with multiple extensions (future capability)."""
    # For now, we only support one extension, but the architecture supports multiple
    core = AgentCore()
    core.register_provider(DummyProvider, extensions=[DummyExtension])
    
    config = {"model": "test"}
    session = core.create_session()
    session = core.add_message(session, "user", "Test")
    
    final_message = None
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            final_message = chunk["messages"][-1]
    
    assert final_message is not None


def test_extension_with_feature():
    """Test extension working alongside feature plugins."""
    core = AgentCore()
    core.register_provider(DummyProvider, extensions=[DummyExtension])
    
    from .dummy_feature import DummyFeature
    core.register_feature(DummyFeature)
    
    config = {
        "model": "test",
        "prefix": "[EXT]",  # Extension prefix
        "enabled": True
    }
    session = core.create_session()
    session = core.add_message(session, "user", "Test")
    
    final_message = None
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            final_message = chunk["messages"][-1]
    
    # Both extension and feature should process
    # Extension adds prefix first, then feature adds prefix
    # So we get "[TEST] [EXT] Echo: Test" (feature prefix applied last)
    assert final_message is not None
    assert "[EXT]" in final_message["content"]
    assert "Echo: Test" in final_message["content"]


@pytest.mark.asyncio
async def test_extension_with_async_streaming():
    """Test extension with async streaming."""
    core = AgentCore()
    core.register_provider(DummyProvider, extensions=[DummyExtension])
    
    config = {"model": "test", "prefix": "[ASYNC-EXT]", "enabled": True}
    session = core.create_session()
    session = core.add_message(session, "user", "Async test")
    
    final_message = None
    async for chunk in core.send_request_stream_async(session, config):
        if chunk["type"] == "final":
            final_message = chunk["messages"][-1]
    
    assert final_message is not None
    assert "[ASYNC-EXT]" in final_message["content"]
    assert "extension_processed_chunks" in final_message["metadata"]
