"""
Tests for FeatureAdapter.transform_messages with direction support.
"""

from agent_core import AgentCore
from .dummy_provider import DummyProvider
from .dummy_transform_feature import DummyTransformFeature


def test_transform_messages_direction_to_compat():
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(DummyTransformFeature)

    config = {"model": "test"}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    session, response = core.send_request(session, config)

    # User message transformed to uppercase before provider saw it
    assert response["content"] == "Echo: HELLO"
