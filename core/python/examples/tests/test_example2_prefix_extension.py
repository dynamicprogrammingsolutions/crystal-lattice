"""
Tests for examples/prefix_extension.py working with EchoProvider.
"""

import os
import sys



def test_prefix_extension_applies_prefix_and_metadata():
    from agent_core import AgentCore

    from examples.example1_echo_provider import EchoProvider
    from examples.example2_prefix_extension import PrefixExtension

    core = AgentCore()
    core.register_provider(EchoProvider, extensions=[PrefixExtension])

    config = {"model": "echo-1", "enabled": True, "prefix": "[EXT]"}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")

    final_msg = None
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            final_msg = chunk["messages"][-1]

    assert final_msg is not None
    assert final_msg["content"].startswith("[EXT] Echo: Hello")
    assert "extension_processed_chunks" in final_msg.get("metadata", {})
