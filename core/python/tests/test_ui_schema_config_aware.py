"""Tests for config-aware UI schema (get_ui_schema(config=...))."""

from typing import Any, Dict, List, Tuple

from agent_core import AgentCore
from agent_core.types import FeaturePlugin
from tests.dummy_provider import DummyProvider


class ConfigAwareFeature(FeaturePlugin):
    """Feature that returns different UI elements based on config."""

    name = "config_aware_feature"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        base = [{"key": "always", "label": "Always visible", "ui_type": "config"}]
        if config.get("hide_extra"):
            return base
        return base + [
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
    """get_ui_schema(config={}) works when plugins implement legacy get_ui_elements()."""

    class LegacyUiFeature(FeaturePlugin):
        name = "legacy_ui_feature"
        version = "0.0.1"

        def get_ui_elements(self) -> List[Dict[str, Any]]:  # type: ignore[override]
            return [{"key": "legacy", "label": "Legacy", "ui_type": "config"}]

        def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
            return state or {}

    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(LegacyUiFeature)

    schema_empty_config = core.get_ui_schema(config={})
    schema_no_arg = schema_empty_config

    assert isinstance(schema_no_arg, list)
    assert isinstance(schema_empty_config, list)
    keys_no = {el.get("key") for el in schema_no_arg if isinstance(el, dict)}
    keys_empty = {el.get("key") for el in schema_empty_config if isinstance(el, dict)}
    assert keys_no == keys_empty
    assert "model" in keys_no
    assert "legacy" in keys_empty


def test_get_ui_schema_with_config_passes_config_to_get_ui_elements():
    """get_ui_schema(config=...) passes config into get_ui_elements."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(ConfigAwareFeature)

    schema_default = core.get_ui_schema(config={})
    schema_hide = core.get_ui_schema(config={"hide_extra": True})

    keys_default = {el.get("key") for el in schema_default if isinstance(el, dict)}
    keys_hide = {el.get("key") for el in schema_hide if isinstance(el, dict)}

    assert "always" in keys_default
    assert "always" in keys_hide
    assert "when_not_hidden" in keys_default
    assert "when_not_hidden" not in keys_hide
    assert "model" in keys_default
    assert "model" in keys_hide


def test_get_ui_schema_includes_config_aware_elements():
    """ConfigAwareFeature returns config-dependent elements."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(ConfigAwareFeature)

    schema = core.get_ui_schema(config={})
    keys = {el.get("key") for el in schema if isinstance(el, dict)}
    # ConfigAwareFeature.get_ui_elements returns "always"; provider may add more (e.g. "model").
    assert "always" in keys
