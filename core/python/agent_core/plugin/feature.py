"""
Feature plugin wrapper and adapter.

Manages feature plugin state and provides typed interface.
"""

from typing import Dict, Any, List, Optional


class FeatureWrapper:
    """
    Wrapper for feature plugin.
    
    Holds feature state if needed. Many features are stateless.
    All protocol-facing methods are implemented here with state validation.
    Adapters must delegate without performing error handling.
    """
    
    def __init__(self, plugin_class: type):
        """
        Initialize wrapper with feature plugin class.
        
        Args:
            plugin_class: Feature plugin class with static methods
        """
        self.plugin_class = plugin_class
        self.state: Optional[Dict[str, Any]] = None
        self._name = getattr(plugin_class, "name", plugin_class.__name__)
        self._version = getattr(plugin_class, "version", "unknown")
    
    @property
    def name(self) -> str:
        """Get feature name."""
        return self._name
    
    @property
    def version(self) -> str:
        """Get feature version."""
        return self._version
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize feature state.
        
        Args:
            config: Feature configuration
        """
        if hasattr(self.plugin_class, "init"):
            self.state = self.plugin_class.init(config)
        else:
            # Stateless feature, just store config and default state buckets
            self.state = {"config": config, "capabilities": [], "runtime_state": {}, "ui_state": {}}
    
    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update feature state.
        
        Args:
            updates: State updates
        """
        if self.state is None:
            raise RuntimeError(f"Feature {self.name} not initialized")
        
        if hasattr(self.plugin_class, "update_state"):
            self.state = self.plugin_class.update_state(self.state, updates)
        else:
            # Simple config update
            self.state = {**self.state, "config": {**self.state.get("config", {}), **updates}}
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get feature configuration schema."""
        if hasattr(self.plugin_class, "get_config_schema"):
            return self.plugin_class.get_config_schema()
        return {}
    
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Get feature UI elements."""
        if hasattr(self.plugin_class, "get_ui_elements"):
            return self.plugin_class.get_ui_elements()
        return []

    def transform_messages(self, messages: List[Dict[str, Any]], direction: str = "to_compat") -> List[Dict[str, Any]]:
        """Transform messages via plugin if implemented; otherwise passthrough."""
        if self.state is None:
            raise RuntimeError(f"Feature {self.name} not initialized")
        if hasattr(self.plugin_class, "transform_messages"):
            return self.plugin_class.transform_messages(messages, self.state, direction)
        return messages

    def modify_request_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Modify request body via plugin if implemented; otherwise passthrough."""
        if self.state is None:
            raise RuntimeError(f"Feature {self.name} not initialized")
        if hasattr(self.plugin_class, "modify_request_body"):
            return self.plugin_class.modify_request_body(body, self.state)
        return body

    def process_final_message(self, message: Dict[str, Any], conversation_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process final message via plugin if implemented; otherwise passthrough."""
        if self.state is None:
            raise RuntimeError(f"Feature {self.name} not initialized")
        if hasattr(self.plugin_class, "process_final_message"):
            return self.plugin_class.process_final_message(message, conversation_dict, self.state)
        return message


class FeatureAdapter:
    """
    Passthrough adapter for feature plugins.
    
    Performs no validation or error handling; delegates to FeatureWrapper which
    enforces protocol and state.
    """
    
    def __init__(self, wrapper: FeatureWrapper):
        """
        Initialize adapter with feature wrapper.
        
        Args:
            wrapper: FeatureWrapper instance
        """
        self.wrapper = wrapper
    
    @property
    def name(self) -> str:
        """Get feature name."""
        return self.wrapper.name
    
    @property
    def version(self) -> str:
        """Get feature version."""
        return self.wrapper.version
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize feature with configuration.
        
        Args:
            config: Feature configuration
        """
        self.wrapper.initialize(config)
    
    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update feature state.
        
        Args:
            updates: State updates
        """
        self.wrapper.update_state(updates)
    
    def transform_messages(self, messages: List[Dict[str, Any]], direction: str = "to_compat") -> List[Dict[str, Any]]:
        """Transform messages (passthrough)."""
        return self.wrapper.transform_messages(messages, direction)
    
    def modify_request_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Modify API request body (passthrough)."""
        return self.wrapper.modify_request_body(body)
    
    def process_final_message(
        self,
        message: Dict[str, Any],
        conversation_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process final message (passthrough)."""
        return self.wrapper.process_final_message(message, conversation_dict)
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get feature configuration schema."""
        return self.wrapper.get_config_schema()
    
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Get feature UI elements."""
        return self.wrapper.get_ui_elements()
