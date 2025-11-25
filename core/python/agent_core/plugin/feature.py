"""
Feature plugin wrapper.

Stateless wrapper; features operate on shared provider state managed by the provider wrapper.
"""

from typing import Dict, Any, List
from ..types import FeaturePlugin


class FeatureWrapper(FeaturePlugin):
    """
    Wrapper for feature plugin (no internal state).
    Orchestrates initialize_request and finalize using shared state passed in/out.
    """

    def __init__(self, plugin_class: type):
        self.plugin_class = plugin_class
        self.plugin = plugin_class()
        self.name = getattr(plugin_class, "name", plugin_class.__name__)
        self.version = getattr(plugin_class, "version", "unknown")

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if hasattr(self.plugin, "init"):
            return self.plugin.init(config, state)
        return state

    def get_config_schema(self) -> Dict[str, Any]:
        if hasattr(self.plugin, "get_config_schema"):
            return self.plugin.get_config_schema()
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        if hasattr(self.plugin, "get_ui_elements"):
            return self.plugin.get_ui_elements()
        return []

    def get_models(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Statelessly transform or forward model descriptors."""
        if hasattr(self.plugin, "get_models"):
            return self.plugin.get_models(config, models)
        return list(models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability/environment tags from the underlying feature if any."""
        if hasattr(self.plugin, "get_tags"):
            return self.plugin.get_tags(config, models)
        return []

    def required_tags(self) -> List[str]:
        """Tags required for this feature to be enabled."""
        if hasattr(self.plugin, "required_tags"):
            return self.plugin.required_tags()
        return []
 
    # Stateless transforms
    def to_native_messages(

        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if hasattr(self.plugin, "to_native_messages"):
            return self.plugin.to_native_messages(messages, native_messages)
        return messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if hasattr(self.plugin, "from_native_messages"):
            return self.plugin.from_native_messages(native_messages, messages)
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if hasattr(self.plugin, "initialize_request"):
            return self.plugin.initialize_request(native_messages, state)
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Run feature finalize; return (final_messages, native_messages, new_state)."""
        if hasattr(self.plugin, "finalize"):
            return self.plugin.finalize(final_messages, native_messages, state)
        return final_messages, native_messages, state
