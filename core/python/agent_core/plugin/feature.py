"""
Feature plugin wrapper and adapter.

Manages feature plugin state and provides typed interface.
"""

from typing import Dict, Any, List, Optional


class FeatureWrapper:
    """
    Wrapper for feature plugin.

    Holds feature state if needed. Many features are stateless.
    Implements initialize_request and finalize orchestration.
    """

    def __init__(self, plugin_class: type):
        self.plugin_class = plugin_class
        self.state: Optional[Dict[str, Any]] = None
        self._name = getattr(plugin_class, "name", plugin_class.__name__)
        self._version = getattr(plugin_class, "version", "unknown")

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    def initialize(self, config: Dict[str, Any]) -> None:
        if hasattr(self.plugin_class, "init"):
            self.state = self.plugin_class.init(config)
        else:
            self.state = {"config": config, "capabilities": [], "runtime_state": {}, "ui_state": {}}

    def update_state(self, updates: Dict[str, Any]) -> None:
        if self.state is None:
            raise RuntimeError(f"Feature {self.name} not initialized")
        if hasattr(self.plugin_class, "update_state"):
            self.state = self.plugin_class.update_state(self.state, updates)
        else:
            self.state = {**self.state, "config": {**self.state.get("config", {}), **updates}}

    def get_config_schema(self) -> Dict[str, Any]:
        if hasattr(self.plugin_class, "get_config_schema"):
            return self.plugin_class.get_config_schema()
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        if hasattr(self.plugin_class, "get_ui_elements"):
            return self.plugin_class.get_ui_elements()
        return []

    def initialize_request(self, messages: List[Dict[str, Any]]) -> None:
        if self.state is None:
            raise RuntimeError(f"Feature {self.name} not initialized")
        if hasattr(self.plugin_class, "initialize_request"):
            self.state = self.plugin_class.initialize_request(messages, self.state)

    def finalize(self, messages: List[Dict[str, Any]], output: Dict[str, Any]) -> Dict[str, Any]:
        """Run feature finalize to possibly modify/discard outputs.
        Output shape: {"final_messages": [...], "native_messages": [...]}.
        Returns the same shape.
        """
        if self.state is None:
            raise RuntimeError(f"Feature {self.name} not initialized")
        if hasattr(self.plugin_class, "finalize"):
            return self.plugin_class.finalize(messages, output, self.state)
        return output


class FeatureAdapter:
    """
    Passthrough adapter for feature plugins.

    Performs no validation or error handling; delegates to FeatureWrapper which
    enforces protocol and state.
    """

    def __init__(self, wrapper: FeatureWrapper):
        self.wrapper = wrapper

    @property
    def name(self) -> str:
        return self.wrapper.name

    @property
    def version(self) -> str:
        return self.wrapper.version

    def initialize(self, config: Dict[str, Any]) -> None:
        self.wrapper.initialize(config)

    def update_state(self, updates: Dict[str, Any]) -> None:
        self.wrapper.update_state(updates)

    def initialize_request(self, messages: List[Dict[str, Any]]) -> None:
        self.wrapper.initialize_request(messages)

    def finalize(self, messages: List[Dict[str, Any]], output: Dict[str, Any]) -> Dict[str, Any]:
        return self.wrapper.finalize(messages, output)

    def get_config_schema(self) -> Dict[str, Any]:
        return self.wrapper.get_config_schema()

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return self.wrapper.get_ui_elements()
