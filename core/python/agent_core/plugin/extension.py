"""
Provider extension plugin wrapper.

Stateless wrapper around provider extension plugins operating on shared provider state.
Extensions must be the same language as the provider and are invoked directly
by the provider wrapper.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional

from ..types import ProviderExtensionPlugin, Session
from .adapters import ProviderExtensionDefaultsAdapter


class ExtensionWrapper(ProviderExtensionPlugin):
    """Wrapper for provider extension plugin (no internal state).

    Coordinates calls with shared provider state managed by the provider wrapper.
    """

    def __init__(self, plugin_class: type) -> None:
        self.plugin_class = plugin_class
        self.plugin = ProviderExtensionDefaultsAdapter(plugin_class())
        self.name = getattr(plugin_class, "name", plugin_class.__name__)
        self.version = getattr(plugin_class, "version", "unknown")
        self.priority = getattr(plugin_class, "priority", 100)

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize with config and shared state; return updated shared state."""
        return self.plugin.init(config, state)

    def get_config_schema(self) -> Dict[str, Any]:
        return self.plugin.get_config_schema()

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return self.plugin.get_ui_elements(config, tags, models)

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
        """Return capability/environment tags from the underlying extension if any."""
        return self.plugin.get_tags(config, models)

    def required_tags(self) -> List[str]:
        """Tags required for this extension to be enabled."""
        return self.plugin.required_tags()

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
        """Prepare for a new turn; MUST return (native_messages, shared state)."""
        return self.plugin.initialize_request(native_messages, state)

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        """Process provider outputs during streaming or after finalization (hot path).

        Returns updated (partial_messages, final_messages, native_messages, new_shared_state).
        """
        return self.plugin.process_chunk(
            native_chunk,
            partial_messages,
            final_messages,
            native_messages,
            state,
        )

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Finalize after provider; return (final_messages, native_messages, new_state)."""
        return self.plugin.finalize(final_messages, native_messages, state)

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return session-scoped action definitions from the extension."""
        return self.plugin.get_actions(state)

    def execute_action(
        self,
        action_id: str,
        session: Session,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a session-scoped action from the extension."""
        return self.plugin.execute_action(action_id, session, native_messages, params, state)
