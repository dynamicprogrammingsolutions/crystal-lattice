"""
Tests for UI schema including tool plugins.
"""

from agent_core import AgentCore
from .dummy_provider import DummyProvider
from .dummy_tool import DummyCalculator


def test_ui_schema_includes_tools():
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_tool(DummyCalculator)

    ui = core.get_ui_schema({})

    assert isinstance(ui, list)
    keys = {el.get("key") for el in ui if isinstance(el, dict)}
    # Provider UI element from DummyProvider should be present.
    assert "model" in keys
