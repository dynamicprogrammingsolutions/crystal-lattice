"""
Unit tests for core data types (functional architecture).
"""

import pytest
from agent_core.types import Message, Session


def test_message_creation():
    """Test message creation."""
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert msg.metadata is None


def test_message_with_metadata():
    """Test message with metadata."""
    metadata = {"model": "gpt-4", "tokens": 100}
    msg = Message(role="assistant", content="Hi", metadata=metadata)
    assert msg.metadata == metadata


def test_message_to_dict():
    """Test message serialization."""
    msg = Message(role="user", content="Test", metadata={"key": "value"})
    data = msg.to_dict()

    assert data["role"] == "user"
    assert data["content"] == "Test"
    assert data["metadata"]["key"] == "value"


def test_message_from_dict():
    """Test message deserialization."""
    data = {"role": "assistant", "content": "Response", "metadata": {"tokens": 50}}
    msg = Message.from_dict(data)

    assert msg.role == "assistant"
    assert msg.content == "Response"
    assert msg.metadata is not None
    assert msg.metadata["tokens"] == 50


def test_session_creation():
    """Test session creation."""
    session = Session(session_id="test-123")
    assert session.session_id == "test-123"
    assert len(session.messages) == 0
    assert isinstance(session.messages, list)


def test_session_with_messages():
    """Test session with messages."""
    msg1 = Message(role="user", content="Hello")
    msg2 = Message(role="assistant", content="Hi")

    session = Session(session_id="test", messages=[msg1, msg2])

    assert len(session.messages) == 2
    assert session.messages[0].content == "Hello"
    assert session.messages[1].content == "Hi"


def test_session_to_dict():
    """Test session serialization."""
    msg = Message(role="user", content="Test")
    session = Session(session_id="test", messages=[msg], metadata={"key": "value"})

    data = session.to_dict()

    assert data["session_id"] == "test"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["content"] == "Test"
    assert data["metadata"]["key"] == "value"


def test_session_from_dict():
    """Test session deserialization."""
    data = {
        "session_id": "test",
        "messages": [
            {"role": "user", "content": "Hello", "metadata": None},
            {"role": "assistant", "content": "Hi", "metadata": None},
        ],
        "metadata": {"key": "value"},
    }

    session = Session.from_dict(data)

    assert session.session_id == "test"
    assert len(session.messages) == 2
    assert session.messages[0].content == "Hello"
    assert session.messages[1].content == "Hi"
    assert session.metadata["key"] == "value"


def test_session_functional_update():
    """Test that session updates return new instances (functional pattern)."""
    msg1 = Message(role="user", content="First")
    session1 = Session(session_id="test", messages=[msg1])

    # Create new session with additional message
    msg2 = Message(role="assistant", content="Second")
    session2 = Session(
        session_id=session1.session_id,
        messages=[*session1.messages, msg2],
        metadata=session1.metadata,
    )

    # Original unchanged
    assert len(session1.messages) == 1
    # New session has both
    assert len(session2.messages) == 2
    # Different objects
    assert session1 is not session2
