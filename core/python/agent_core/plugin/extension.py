"""
Provider extension plugin wrapper.

Manages extension plugin state during hot-path streaming. No adapter layer—
extensions must be the same language as the provider and are invoked directly
by the provider wrapper.
"""

from typing import Dict, Any, List, Tuple, Optional


class ExtensionWrapper:
    """
    Wrapper for provider extension plugin.
    
    Holds extension state during streaming and accumulates metadata.
    """
    
    def __init__(self, plugin_class: type):
        """
        Initialize wrapper with extension plugin class.
        
        Args:
            plugin_class: Extension plugin class with static methods
        """
        self.plugin_class = plugin_class
        self.state: Optional[Dict[str, Any]] = None
        self._name = getattr(plugin_class, "name", plugin_class.__name__)
        self._version = getattr(plugin_class, "version", "unknown")
        self._target_provider = getattr(plugin_class, "target_provider", None)
    
    @property
    def name(self) -> str:
        """Get extension name."""
        return self._name
    
    @property
    def version(self) -> str:
        """Get extension version."""
        return self._version
    
    @property
    def target_provider(self) -> Optional[str]:
        """Get target provider name."""
        return self._target_provider
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize extension state.
        
        Args:
            config: Extension configuration
        """
        self.state = self.plugin_class.init(config)
    
    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update extension state.
        
        Args:
            updates: State updates
        """
        if self.state is None:
            raise RuntimeError(f"Extension {self.name} not initialized")
        self.state = self.plugin_class.update_state(self.state, updates)
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get extension configuration schema."""
        if hasattr(self.plugin_class, "get_config_schema"):
            return self.plugin_class.get_config_schema()
        return {}
    
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Get extension UI elements."""
        if hasattr(self.plugin_class, "get_ui_elements"):
            return self.plugin_class.get_ui_elements()
        return []
    
    def process_chunk(self, native_chunk: Dict[str, Any], provider_state: Dict[str, Any]) -> str:
        """
        Process chunk during streaming (hot path).
        Updates internal extension state.
        
        Returns partial content (usually empty).
        """
        if self.state is None:
            raise RuntimeError(f"Extension {self.name} not initialized")
        partial, new_state = self.plugin_class.process_chunk(
            native_chunk,
            provider_state,
            self.state
        )
        self.state = new_state
        return partial
    
    def enhance_final_message(
        self,
        message: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Enhance final message with extension data.
        """
        if self.state is None:
            raise RuntimeError(f"Extension {self.name} not initialized")
        return self.plugin_class.enhance_final_message(message, metadata, self.state)
