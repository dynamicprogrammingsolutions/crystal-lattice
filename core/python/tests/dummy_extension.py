"""
Dummy provider extension plugin for testing purposes.

This plugin extends the dummy provider with additional processing during streaming.
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class DummyExtension:
    """
    Dummy provider extension (stateless with state parameter).
    Extends dummy_provider with additional chunk processing.
    """
    
    name: str = "dummy_extension"
    version: str = "1.0.0"
    target_provider: str = "dummy_provider"
    
    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        """Return configuration schema."""
        return {
            "prefix": {"type": "string", "default": "[EXT]"},
            "enabled": {"type": "boolean", "default": True}
        }
    
    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]:
        """Return UI elements."""
        return [
            {"type": "checkbox", "key": "enabled", "label": "Enable Extension"},
            {"type": "text", "key": "prefix", "label": "Extension Prefix"}
        ]
    
    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize extension state.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Initial state dictionary
        """
        return {
            "config": config,
            "capabilities": [],
            "runtime_state": {
                "processed_chunks": 0,
                "metadata_accumulator": {}
            },
            "ui_state": {}
        }
    
    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update extension state (pure function).
        
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
        return state["config"].get("enabled", True)
    
    @staticmethod
    def process_chunk(
        native_chunk: Dict[str, Any],
        provider_state: Dict[str, Any],
        extension_state: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process chunk from provider (hot path).
        
        Args:
            native_chunk: Chunk from provider
            provider_state: Provider's current state
            extension_state: Extension's current state
            
        Returns:
            Tuple of (partial_content, new_extension_state)
        """
        if not extension_state["config"].get("enabled", True):
            return "", extension_state
        
        # Count processed chunks
        new_state = {
            **extension_state,
            "runtime_state": {
                **extension_state["runtime_state"],
                "processed_chunks": extension_state["runtime_state"]["processed_chunks"] + 1
            }
        }
        
        # No content modification during streaming
        return "", new_state
    
    @staticmethod
    def enhance_final_message(
        message: Dict[str, Any],
        metadata: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Enhance final message with extension data.
        
        Args:
            message: Final message from provider
            metadata: Message metadata
            state: Extension state
            
        Returns:
            Tuple of (enhanced_message, enhanced_metadata)
        """
        if not state["config"].get("enabled", True):
            return message, metadata
        
        # Add prefix to content
        prefix = state["config"].get("prefix", "[EXT]")
        enhanced_message = {
            **message,
            "content": f"{prefix} {message['content']}"
        }
        
        # Add extension metadata
        enhanced_metadata = {
            **metadata,
            "extension_processed_chunks": state["runtime_state"]["processed_chunks"]
        }
        
        return enhanced_message, enhanced_metadata
