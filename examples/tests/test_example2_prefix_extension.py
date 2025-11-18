"""
Tests for examples/prefix_extension.py working with EchoProvider.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)


def test_prefix_extension_applies_prefix_and_metadata():
    from agent_core import AgentCore
    EchoProvider = __import__("examples.example1_echo_provider", fromlist=["EchoProvider"]).EchoProvider
    PrefixExtension = __import__("examples.example2_prefix_extension", fromlist=["PrefixExtension"]).PrefixExtension

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
