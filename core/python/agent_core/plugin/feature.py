"""
Feature plugin wrapper and adapter.

Stateless wrapper; features operate on shared provider state managed by the provider wrapper.
"""

from typing import Dict, Any, List
from ..types import FeatureWrapperProtocol


class FeatureWrapper(FeatureWrapperProtocol):
    """
    Wrapper for feature plugin (no internal state).
    Orchestrates initialize_request and finalize using shared state passed in/out.
    """

    def __init__(self, plugin_class: type):
        self.plugin_class = plugin_class
        self.name = getattr(plugin_class, "name", plugin_class.__name__)
        self.version = getattr(plugin_class, "version", "unknown")

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if hasattr(self.plugin_class, "init"):
            return self.plugin_class.init(config, state)
        return state

    def update_state(
        self, state: Dict[str, Any], updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        if hasattr(self.plugin_class, "update_state"):
            return self.plugin_class.update_state(state, updates)
        return {**state, "config": {**state.get("config", {}), **updates}}

    def get_config_schema(self) -> Dict[str, Any]:
        if hasattr(self.plugin_class, "get_config_schema"):
            return self.plugin_class.get_config_schema()
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        if hasattr(self.plugin_class, "get_ui_elements"):
            return self.plugin_class.get_ui_elements()
        return []

    # Stateless transforms
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if hasattr(self.plugin_class, "to_native_messages"):
            return self.plugin_class.to_native_messages(messages, native_messages)
        return messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if hasattr(self.plugin_class, "from_native_messages"):
            return self.plugin_class.from_native_messages(native_messages, messages)
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if hasattr(self.plugin_class, "initialize_request"):
            return self.plugin_class.initialize_request(native_messages, state)
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Run feature finalize; return (final_messages, native_messages, new_state)."""
        if hasattr(self.plugin_class, "finalize"):
            return self.plugin_class.finalize(final_messages, native_messages, state)
        return final_messages, native_messages, state


class FeatureAdapter(FeatureWrapperProtocol):
    """
    Passthrough adapter for feature plugins.
    """

    def __init__(self, wrapper: FeatureWrapper):
        self.wrapper = wrapper
        self.name: str = wrapper.name
        self.version: str = wrapper.version

    # Lifecycle
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return self.wrapper.init(config, state)

    def update_state(
        self, state: Dict[str, Any], updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self.wrapper.update_state(state, updates)

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self.wrapper.initialize_request(native_messages, state)

    # Stateless transforms
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return self.wrapper.to_native_messages(messages, native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return self.wrapper.from_native_messages(native_messages, messages)

    # Finalize
    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return self.wrapper.finalize(final_messages, native_messages, state)

    def get_config_schema(self) -> Dict[str, Any]:
        return self.wrapper.get_config_schema()

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return self.wrapper.get_ui_elements()
