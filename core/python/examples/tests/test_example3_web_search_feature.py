"""
Tests for examples/web_search_feature.py with EchoProvider.
"""

import os
import sys



def test_web_search_feature_metadata_toggle():
    from agent_core import AgentCore

    from examples.example1_echo_provider import EchoProvider
    from examples.example3_web_search_feature import WebSearchFeature

    core = AgentCore()
    core.register_provider(EchoProvider)
    core.register_feature(WebSearchFeature)

    session = core.create_session()
    session = core.add_message(session, "user", "Latest AI news")

    # Without feature enabled
    config1 = {"model": "echo-1", "web_search_enabled": False}
    _, messages1 = core.send_request(session, config1)

    # With feature enabled
    config2 = {**config1, "web_search_enabled": True}
    _, messages2 = core.send_request(session, config2)

    assert "web_search_used" not in (messages1[-1].get("metadata") or {})
    assert (messages2[-1].get("metadata") or {}).get("web_search_used") is True
