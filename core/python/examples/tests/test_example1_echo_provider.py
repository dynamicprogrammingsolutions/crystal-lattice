"""
Tests for examples/echo_provider.py
"""

import os
import sys



def test_echo_provider_streaming_and_finalize():
    from agent_core import AgentCore

    from examples.example1_echo_provider import EchoProvider

    core = AgentCore()
    core.register_provider(EchoProvider)

    config = {"model": "echo-1"}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")

    partials = []
    final_msg = None
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "partial":
            partials.append(chunk["message"]["content"])
        elif chunk["type"] == "final":
            final_msg = chunk["messages"][-1]

    assert partials
    assert final_msg is not None
    assert final_msg["content"].startswith("Echo: Hello")
