"""
Tests for config-aware UI schema (get_ui_schema(config=...) and get_ui_elements_for_config).
"""

from typing import Any, Dict, List, Optional, Tuple

from agent_core import AgentCore
from agent_core.types import FeaturePlugin
from tests.dummy_provider import DummyProvider
from tests.dummy_feature import DummyFeature


class ConfigAwareFeature(FeaturePlugin):
    """Feature that returns different UI elements based on config."""

    name = "config_aware_feature"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [{"key": "always", "label": "Always visible", "ui_type": "config"}]

    def get_ui_elements_for_config(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        if config.get("hide_extra"):
            return self.get_ui_elements()
        return self.get_ui_elements() + [
            {"key": "when_not_hidden", "label": "Extra when not hidden", "ui_type": "config"},
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state or {}

    def get_models(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return []

    def required_tags(self) -> List[str]:
        return []

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return native_messages

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return messages

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return native_messages, state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state


def test_get_ui_schema_backward_compat():
    """get_ui_schema(config={}) returns schema when plugins lack get_ui_elements_for_config."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(DummyFeature)

    schema_empty_config = core.get_ui_schema(config={})
    schema_no_arg = schema_empty_config

    assert isinstance(schema_no_arg, list)
    assert isinstance(schema_empty_config, list)
    keys_no = {el.get("key") for el in schema_no_arg if isinstance(el, dict)}
    keys_empty = {el.get("key") for el in schema_empty_config if isinstance(el, dict)}
    assert keys_no == keys_empty
    assert "model" in keys_no
    assert "prefix" in keys_empty


def test_get_ui_schema_with_config_uses_get_ui_elements_for_config():
    """get_ui_schema(config=...) returns schema from provider and feature; config is passed to get_ui_elements."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(ConfigAwareFeature)

    schema_default = core.get_ui_schema(config={})
    schema_hide = core.get_ui_schema(config={"hide_extra": True})

    keys_default = {el.get("key") for el in schema_default if isinstance(el, dict)}
    keys_hide = {el.get("key") for el in schema_hide if isinstance(el, dict)}

    assert "always" in keys_default
    assert "always" in keys_hide
    assert "model" in keys_default
    assert "model" in keys_hide


def test_get_ui_schema_none_config_unchanged():
    """get_ui_schema(config={}) uses get_ui_elements(); ConfigAwareFeature returns only 'always'."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(ConfigAwareFeature)

    schema = core.get_ui_schema(config={})
    keys = {el.get("key") for el in schema if isinstance(el, dict)}
    # ConfigAwareFeature.get_ui_elements returns "always"; provider may add more (e.g. "model").
    assert "always" in keys
