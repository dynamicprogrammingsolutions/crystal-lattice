"""
Dummy feature plugin for testing purposes.

This plugin adds a prefix to all assistant responses.
Follows the state-based plugin protocol.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class DummyFeature:
    """
    Dummy feature plugin (stateless with state parameter).
    All methods are static and take state as parameter.
    """
    
    name: str = "dummy_feature"
    version: str = "1.0.0"
    
    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        """Return configuration schema."""
        return {
            "prefix": {"type": "string", "default": "[TEST]"}
        }
    
    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]:
        """Return UI elements."""
        return [
            {"type": "text", "key": "prefix", "label": "Response Prefix"}
        ]
    
    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize feature state.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Initial state dictionary
        """
        return {
            "config": config,
            "capabilities": [],
            "runtime_state": {},
            "ui_state": {}
        }
    
    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update feature state (pure function).
        
        Args:
            state: Current state
            updates: Dictionary of updates
            
        Returns:
            New state
        """
        return {
            **state,
            "config": {**state["config"], **updates}
        }
    
    @staticmethod
    def can_handle(capability_id: str, state: Dict[str, Any]) -> bool:
        """Check if capability is supported."""
        return False
    
    @staticmethod
    def process_final_message(
        message: Dict[str, Any],
        conversation_dict: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add prefix to final message (pure function)."""
        prefix = state["config"].get("prefix", "[TEST]")
        
        return {
            **message,
            "content": f"{prefix} {message['content']}"
        }
