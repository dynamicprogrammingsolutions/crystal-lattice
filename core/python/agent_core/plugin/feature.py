"""
Feature plugin wrapper.

Stateless wrapper; features operate on shared provider state managed by the provider wrapper.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..types import FeaturePlugin
from .adapters import FeatureDefaultsAdapter


class FeatureWrapper(FeaturePlugin):
    """Wrapper for feature plugin (no internal state).

    Orchestrates initialize_request and finalize using shared state passed in/out.
    """

    def __init__(self, plugin_class: type) -> None:
        self.plugin_class = plugin_class
        self.plugin = FeatureDefaultsAdapter(plugin_class())
        self.name = getattr(plugin_class, "name", plugin_class.__name__)
        self.version = getattr(plugin_class, "version", "unknown")

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return self.plugin.init(config, state)

    def get_config_schema(self) -> Dict[str, Any]:
        return self.plugin.get_config_schema()

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return self.plugin.get_ui_elements()

    def get_models(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Statelessly transform or forward model descriptors."""
        return self.plugin.get_models(config, models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability/environment tags from the underlying feature if any."""
        return self.plugin.get_tags(config, models)

    def required_tags(self) -> List[str]:
        """Tags required for this feature to be enabled."""
        return self.plugin.required_tags()

    def get_template(self, config: Dict[str, Any]) -> str:
        """Return a feature-specific template string, if any."""
        return self.plugin.get_template(config)

    # Stateless transforms
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return self.plugin.to_native_messages(messages, native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return self.plugin.from_native_messages(native_messages, messages)

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return self.plugin.initialize_request(native_messages, state)

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Run feature finalize; return (final_messages, native_messages, new_state)."""
        return self.plugin.finalize(final_messages, native_messages, state)

    def get_completions(
        self,
        config: Dict[str, Any],
        text: str,
    ) -> List[Dict[str, Any]]:
        """Delegate completion suggestions to the underlying feature implementation."""
        return self.plugin.get_completions(config, text)

    def apply_completion(
        self,
        config: Dict[str, Any],
        text: str,
        completion: Dict[str, Any],
    ) -> str:
        """Delegate completion-accept handling to the underlying feature implementation."""
        return self.plugin.apply_completion(config, text, completion)
