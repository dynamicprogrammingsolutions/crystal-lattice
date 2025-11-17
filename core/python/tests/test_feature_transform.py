"""
Tests for Feature finalize behavior.
"""

from agent_core import AgentCore
from .dummy_provider import DummyProvider
from .dummy_transform_feature import DummyTransformFeature


def test_feature_finalize_transforms_response():
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(DummyTransformFeature)

    config = {"model": "test"}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    session, responses = core.send_request(session, config)

    # Assistant response content uppercased by feature finalize
    assert responses[-1]["content"] == "ECHO: HELLO"
