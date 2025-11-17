"""
Tests for async streaming functionality.
"""

import pytest
from agent_core import AgentCore
from .dummy_provider import DummyProvider
from .dummy_feature import DummyFeature


@pytest.mark.asyncio
async def test_async_streaming_basic():
    """Test basic async streaming."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    
    config = {"model": "test-model"}
    session = core.create_session()
    session = core.add_message(session, "user", "Test message")
    
    partials = []
    final_session = None
    final_message = None
    
    async for chunk in core.send_request_stream_async(session, config):
        if chunk["type"] == "partial":
            partials.append(chunk["message"]["content"])
        elif chunk["type"] == "final":
            final_session = chunk["session"]
            final_message = chunk["messages"][-1]
    
    assert len(partials) > 0
    assert final_session is not None
    assert final_message is not None
    assert "Echo: Test message" in final_message["content"]
    
    # Original session unchanged
    assert len(session.messages) == 1
    # Final session has response
    assert len(final_session.messages) == 2


@pytest.mark.asyncio
async def test_async_streaming_with_feature():
    """Test async streaming with feature plugin."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(DummyFeature)
    
    config = {"model": "test", "prefix": "[ASYNC]"}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    
    final_session = None
    final_message = None
    
    async for chunk in core.send_request_stream_async(session, config):
        if chunk["type"] == "final":
            final_session = chunk["session"]
            final_message = chunk["messages"][-1]
    
    assert final_session is not None
    assert final_message is not None
    assert "[ASYNC]" in final_message["content"]
    assert "Echo: Hello" in final_message["content"]


@pytest.mark.asyncio
async def test_async_streaming_accumulation():
    """Test that async streaming properly accumulates content."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    
    config = {"model": "test"}
    session = core.create_session()
    session = core.add_message(session, "user", "ABC")
    
    accumulated = ""
    final_content = ""
    async for chunk in core.send_request_stream_async(session, config):
        if chunk["type"] == "partial":
            accumulated += chunk["message"]["content"]
        elif chunk["type"] == "final":
            final_content = chunk["messages"][-1]["content"]
    
    # Accumulated partials should match final
    assert accumulated == final_content


@pytest.mark.asyncio
async def test_async_streaming_multiple_turns():
    """Test async streaming across multiple conversation turns."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    
    config = {"model": "test"}
    session = core.create_session()
    
    # Turn 1
    session = core.add_message(session, "user", "Turn 1")
    async for chunk in core.send_request_stream_async(session, config):
        if chunk["type"] == "final":
            session = chunk["session"]
            break
    
    assert len(session.messages) == 2
    
    # Turn 2
    response = None
    session = core.add_message(session, "user", "Turn 2")
    async for chunk in core.send_request_stream_async(session, config):
        if chunk["type"] == "final":
            session = chunk["session"]
            response = chunk["messages"][-1]
            break
    
    assert len(session.messages) == 4
    assert response is not None
    assert "Echo: Turn 2" in response["content"]


@pytest.mark.asyncio
async def test_provider_stream_api_async_preferred(monkeypatch):
    """Ensure ProviderAdapter prefers plugin's stream_api_async when available."""
    # Monkeypatch a native async stream on DummyProvider
    from .dummy_provider import DummyProvider as DP

    async def fake_async_stream(native_messages, state):
        # Ignore body/state; yield fixed chunks
        for _ in range(3):
            yield {"content": "Z"}

    monkeypatch.setattr(DP, "stream_api_async", staticmethod(fake_async_stream), raising=False)

    core = AgentCore()
    core.register_provider(DP)

    config = {"model": "test"}
    session = core.create_session()
    session = core.add_message(session, "user", "ignored")

    final = None
    async for chunk in core.send_request_stream_async(session, config):
        if chunk["type"] == "final":
            final = chunk["messages"][-1]

    assert final is not None
    # Accumulated ZZZ from fake async stream
    assert final["content"] == "ZZZ"
