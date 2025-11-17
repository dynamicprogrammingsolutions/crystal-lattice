"""
Tests for plugin discovery and registration.
"""

from agent_core import AgentCore


def test_discover_and_register_plugins():
    core = AgentCore()
    summary = core.discover_and_register([
        "tests.dummy_provider",
        "tests.dummy_feature",
        "tests.dummy_tool",
        "tests.dummy_extension",
    ])

    # At least provider discovered
    assert summary["providers"]

    # Run a basic streaming flow to ensure discovered registration works
    config = {"model": "test-model", "enabled": True}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")

    final_message = None
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            final_message = chunk["message"]

    assert final_message is not None
    assert "Echo: Hello" in final_message["content"]
    # Extension may add metadata
    assert "metadata" in final_message
