"""
Tests for examples/echo_provider.py
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)


def test_echo_provider_streaming_and_finalize():
    from agent_core import AgentCore

    EchoProvider = __import__(
        "examples.example1_echo_provider", fromlist=["EchoProvider"]
    ).EchoProvider

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
