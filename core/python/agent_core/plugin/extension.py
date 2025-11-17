"""
Provider extension plugin wrapper.

Stateless wrapper around provider extension plugins operating on shared provider state.
Extensions must be the same language as the provider and are invoked directly
by the provider wrapper.
"""

from typing import Dict, Any, List, Tuple, Optional
from ..types import ExtensionWrapperProtocol


class ExtensionWrapper(ExtensionWrapperProtocol):
    """
    Wrapper for provider extension plugin (no internal state).
    Coordinates calls with shared provider state managed by the provider wrapper.
    """

    def __init__(self, plugin_class: type):
        self.plugin_class = plugin_class
        self.name = getattr(plugin_class, "name", plugin_class.__name__)
        self.version = getattr(plugin_class, "version", "unknown")
        self.target_provider = getattr(plugin_class, "target_provider", None)

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize with config and shared state; return updated shared state."""
        if hasattr(self.plugin_class, "init"):
            return self.plugin_class.init(config, state)
        return state

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Apply updates (e.g., UI) to shared state; return new state."""
        if hasattr(self.plugin_class, "update_state"):
            return self.plugin_class.update_state(state, updates)
        # Default: merge into config bucket
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
    def to_native_messages(self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if hasattr(self.plugin_class, "to_native_messages"):
            return self.plugin_class.to_native_messages(messages, native_messages)
        return messages

    def from_native_messages(self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if hasattr(self.plugin_class, "from_native_messages"):
            return self.plugin_class.from_native_messages(native_messages, messages)
        return messages

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare for a new turn; MUST return shared state (updated or unchanged)."""
        if hasattr(self.plugin_class, "initialize_request"):
            return self.plugin_class.initialize_request(native_messages, state)
        return state

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Process provider outputs during streaming or after finalization (hot path).
        Returns updated (partial_messages, final_messages, native_messages, new_shared_state).
        """
        if hasattr(self.plugin_class, "process_chunk"):
            return self.plugin_class.process_chunk(
                native_chunk,
                messages,
                state,
                partial_messages,
                final_messages,
                native_messages,
            )
        # Default: no changes
        return partial_messages, final_messages, native_messages, state

    def finalize(
        self,
        messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Finalize after provider; return (final_messages, native_messages, new_state)."""
        if hasattr(self.plugin_class, "finalize"):
            return self.plugin_class.finalize(messages, final_messages, native_messages, state)
        return final_messages, native_messages, state
