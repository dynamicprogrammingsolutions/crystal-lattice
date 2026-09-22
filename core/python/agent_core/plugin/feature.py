"""
Feature plugin wrapper.

Stateless wrapper; features operate on shared provider state managed by the provider wrapper.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..types import FeaturePlugin, Session
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
        self.priority = getattr(plugin_class, "priority", 100)

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return self.plugin.init(config, state)

    def get_config_schema(self) -> Dict[str, Any]:
        return self.plugin.get_config_schema()

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return self.plugin.get_ui_elements(config, context)

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

    def forbidden_tags(self) -> List[str]:
        """Tags that must NOT be present for this feature to be enabled."""
        return self.plugin.forbidden_tags()

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Optional[bool]:
        """Return whether this feature should be enabled given the context."""
        return self.plugin.is_enabled(config, tags, models, context)

    def get_template(self, config: Dict[str, Any]) -> str:
        """Return a feature-specific template string, if any."""
        return self.plugin.get_template(config)

    # Stateless transforms
    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any] | None = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return self.plugin.to_native_messages(
            messages,
            native_messages,
            state,
            context=context,
        )

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any] | None = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return self.plugin.from_native_messages(
            native_messages,
            messages,
            state,
            context=context,
        )

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return self.plugin.initialize_request(
            native_messages,
            state,
            context=context,
        )

    def prepare_tools(
        self,
        config: Dict[str, Any],
        tools: List[Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """Allow the feature to filter or transform available tools."""
        return self.plugin.prepare_tools(config, tools, context)

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Run feature finalize; return (final_messages, native_messages, new_state)."""
        return self.plugin.finalize(
            final_messages,
            native_messages,
            state,
            context=context,
        )

    def prepare_tool_call(
        self,
        tool_call: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Run feature prepare_tool_call; return (tool_call, new_state)."""
        return self.plugin.prepare_tool_call(
            tool_call,
            state,
            context=context,
        )

    def finalize_tool_call(
        self,
        tool_message: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Run feature finalize_tool_call; return (tool_message, new_state)."""
        return self.plugin.finalize_tool_call(
            tool_message,
            state,
            context=context,
        )

    def prepare_appended_message(
        self,
        message: Dict[str, Any],
        state: Optional[Dict[str, Any]] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Run feature prepare_appended_message; return (message, new_state)."""
        return self.plugin.prepare_appended_message(
            message,
            state,
            context=context,
        )

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return session-scoped action definitions from the feature."""
        return self.plugin.get_actions(state)

    def execute_action(
        self,
        action_id: str,
        session: Session,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a session-scoped action from the feature."""
        return self.plugin.execute_action(
            action_id, session, native_messages, params, context, state
        )

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
