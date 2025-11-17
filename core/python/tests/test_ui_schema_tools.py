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

    ui = core.get_ui_schema()

    # Provider present
    assert ("dummy_provider" in ui) or ("DummyProvider" in ui)
    # Tool present
    assert ("dummy_calculator" in ui) or ("DummyCalculator" in ui)
