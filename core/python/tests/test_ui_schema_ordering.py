"""
Tests for UI schema element ordering.

Contract: every UI element may carry an optional numeric ``order``. The
core stamps an effective order on each element — the explicit value when
set, else a kind-and-position default — and returns the element list
sorted by it.

Default bands: provider 1000, provider extension 2000, feature 3000,
tool 4000. Within a band the Nth plugin (in the current iteration
order) defaults to ``band + N * 10`` (2010, 2020, ...). Multiple
elements from one plugin share the plugin default; the stable sort
keeps the plugin's declared element order.
"""

from typing import Any, Dict, List, Optional

from agent_core import AgentCore
from agent_core.types import FeaturePlugin, ProviderExtensionPlugin, ToolPlugin

from .dummy_provider import DummyProvider


class FooterExtensionA(ProviderExtensionPlugin):
    name: str = "footer_extension_a"
    version: str = "0.0.0"

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "message_footer",
                "data": "metadata.a1",
                "template": "a1: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.a2",
                "template": "a2: {{data}}",
            },
        ]


class FooterExtensionB(ProviderExtensionPlugin):
    name: str = "footer_extension_b"
    version: str = "0.0.0"

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "message_footer",
                "data": "metadata.b1",
                "template": "b1: {{data}}",
            },
        ]


class PlainFeature(FeaturePlugin):
    name: str = "plain_feature"
    version: str = "0.0.0"

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "message_footer",
                "data": "metadata.plain",
                "template": "plain: {{data}}",
            },
        ]


class LowPriorityFeature(FeaturePlugin):
    name: str = "low_priority_feature"
    version: str = "0.0.0"
    priority: int = 50

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "message_footer",
                "data": "metadata.low",
                "template": "low: {{data}}",
            },
        ]


class HighPriorityFeature(FeaturePlugin):
    name: str = "high_priority_feature"
    version: str = "0.0.0"
    priority: int = 150

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "message_footer",
                "data": "metadata.high",
                "template": "high: {{data}}",
            },
        ]


class OrderedFeature(FeaturePlugin):
    name: str = "ordered_feature"
    version: str = "0.0.0"

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "message_footer",
                "data": "metadata.before_extensions",
                "template": "before extensions: {{data}}",
                "order": 1990,
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.second_in_extension_band",
                "template": "second in extension band: {{data}}",
                "order": 2015,
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.feature_default",
                "template": "feature default: {{data}}",
            },
        ]


class ConfigFeature(FeaturePlugin):
    name: str = "config_feature"
    version: str = "0.0.0"

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": "config_feature_flag",
                "label": "Config feature flag",
            },
        ]


class FooterTool(ToolPlugin):
    name: str = "footer_tool"
    version: str = "0.0.0"

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "message_footer",
                "data": "metadata.tool",
                "template": "tool: {{data}}",
            },
        ]


def _elements_by_plugin(ui: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    by_plugin: Dict[str, List[Dict[str, Any]]] = {}
    for el in ui:
        by_plugin.setdefault(el.get("plugin"), []).append(el)
    return by_plugin


def test_defaults_by_kind_and_position() -> None:
    core = AgentCore()
    core.register_provider(
        DummyProvider, extensions=[FooterExtensionA, FooterExtensionB]
    )
    core.register_feature(PlainFeature)
    core.register_tool(FooterTool)

    ui = core.get_ui_schema(config={"model": "m"})

    by_plugin = _elements_by_plugin(ui)
    assert all(el.get("order") == 1010 for el in by_plugin["dummy_provider"])
    assert all(el.get("order") == 2010 for el in by_plugin["footer_extension_a"])
    assert all(el.get("order") == 2020 for el in by_plugin["footer_extension_b"])
    assert all(el.get("order") == 3010 for el in by_plugin["plain_feature"])
    assert all(el.get("order") == 4010 for el in by_plugin["footer_tool"])


def test_feature_position_follows_priority_order() -> None:
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(HighPriorityFeature)
    core.register_feature(LowPriorityFeature)

    ui = core.get_ui_schema(config={"model": "m"})

    by_plugin = _elements_by_plugin(ui)
    assert all(el.get("order") == 3010 for el in by_plugin["low_priority_feature"])
    assert all(el.get("order") == 3020 for el in by_plugin["high_priority_feature"])


def test_explicit_order_overrides_default() -> None:
    core = AgentCore()
    core.register_provider(
        DummyProvider, extensions=[FooterExtensionA, FooterExtensionB]
    )
    core.register_feature(OrderedFeature)

    ui = core.get_ui_schema(config={"model": "m"})

    orders = [(el.get("plugin"), el.get("data"), el.get("order")) for el in ui]
    ordered_feature = [entry for entry in orders if entry[0] == "ordered_feature"]
    assert ("ordered_feature", "metadata.before_extensions", 1990) in ordered_feature
    assert (
        "ordered_feature",
        "metadata.second_in_extension_band",
        2015,
    ) in ordered_feature
    assert ("ordered_feature", "metadata.feature_default", 3010) in ordered_feature

    # The full list is sorted by effective order.
    effective = [el.get("order") for el in ui]
    assert effective == sorted(effective)

    # 1990 lands before every extension element; 2015 lands between the
    # two extension plugins (2010 and 2020).
    positions = {entry[1]: idx for idx, entry in enumerate(orders)}
    extension_positions = [
        positions[entry[1]]
        for entry in orders
        if entry[0].startswith("footer_extension")
    ]
    assert positions["metadata.before_extensions"] < min(extension_positions)
    assert positions["metadata.second_in_extension_band"] > min(extension_positions)
    assert positions["metadata.second_in_extension_band"] < max(extension_positions)


def test_stable_within_plugin_element_order() -> None:
    core = AgentCore()
    core.register_provider(DummyProvider, extensions=[FooterExtensionA])

    ui = core.get_ui_schema(config={"model": "m"})

    extension_elements = [el for el in ui if el.get("plugin") == "footer_extension_a"]
    assert [el.get("data") for el in extension_elements] == [
        "metadata.a1",
        "metadata.a2",
    ]
    assert extension_elements[0].get("order") == extension_elements[1].get("order")


def test_config_entries_carry_order() -> None:
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(ConfigFeature)

    ui = core.get_ui_schema(config={"model": "m"})

    config_entries = [el for el in ui if el.get("ui_type") == "config"]
    by_key = {el.get("key"): el for el in config_entries}
    assert by_key["model"].get("order") == 1010
    assert by_key["config_feature_flag"].get("order") == 3010

    orders = [el.get("order") for el in ui]
    assert orders == sorted(orders)


def test_every_element_has_numeric_order() -> None:
    core = AgentCore()
    core.register_provider(
        DummyProvider, extensions=[FooterExtensionA, FooterExtensionB]
    )
    core.register_feature(PlainFeature)
    core.register_feature(ConfigFeature)
    core.register_tool(FooterTool)

    ui = core.get_ui_schema(config={"model": "m"})

    assert ui
    for el in ui:
        order = el.get("order")
        assert isinstance(order, (int, float))
        assert not isinstance(order, bool)
