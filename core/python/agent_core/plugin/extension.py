"""
Provider extension plugin wrapper.

Stateless wrapper around provider extension plugins operating on shared provider state.
Extensions must be the same language as the provider and are invoked directly
by the provider wrapper.
"""

from typing import Dict, Any, List, Tuple, Optional
from ..types import ProviderExtensionPlugin


class ExtensionWrapper(ProviderExtensionPlugin):
    """
    Wrapper for provider extension plugin (no internal state).
    Coordinates calls with shared provider state managed by the provider wrapper.
    """

    def __init__(self, plugin_class: type):
        self.plugin_class = plugin_class
        self.plugin = plugin_class()
        self.name = getattr(plugin_class, "name", plugin_class.__name__)
        self.version = getattr(plugin_class, "version", "unknown")

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize with config and shared state; return updated shared state."""
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
        """Return capability/environment tags from the underlying extension if any."""
        if hasattr(self.plugin, "get_tags"):
            return self.plugin.get_tags(config, models)
        return []

    def required_tags(self) -> List[str]:
        """Tags required for this extension to be enabled."""
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
        """Prepare for a new turn; MUST return shared state (updated or unchanged)."""
        if hasattr(self.plugin, "initialize_request"):
            return self.plugin.initialize_request(native_messages, state)
        return state

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """
        Process provider outputs during streaming or after finalization (hot path).
        Returns updated (partial_messages, final_messages, native_messages, new_shared_state).
        """
        if hasattr(self.plugin, "process_chunk"):
            return self.plugin.process_chunk(
                native_chunk,
                state,
                partial_messages,
                final_messages,
                native_messages,
            )
        # Default: no changes
        return partial_messages, final_messages, native_messages, state


    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Finalize after provider; return (final_messages, native_messages, new_state)."""
        if hasattr(self.plugin, "finalize"):
            return self.plugin.finalize(final_messages, native_messages, state)
        return final_messages, native_messages, state
