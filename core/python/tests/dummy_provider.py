"""
Dummy provider plugin for testing purposes.

This plugin simulates a basic LLM provider without making actual API calls.
Follows the state-based plugin protocol with init/update_state methods.
"""

from typing import Dict, Any, List, Iterator, Tuple
from dataclasses import dataclass


@dataclass
class DummyProvider:
    """
    Dummy provider plugin (stateless with state parameter).
    All methods are static and take state as parameter.
    """
    
    name: str = "dummy_provider"
    version: str = "1.0.0"
    
    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        """Return configuration schema."""
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": False},
        }
    
    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]:
        """Return UI elements."""
        return [
            {"type": "text", "key": "model", "label": "Model Name"}
        ]
    
    @staticmethod
    def get_capabilities() -> List[str]:
        """Return provider capabilities."""
        return ["text_generation", "streaming"]
    
    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize provider state.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Initial state dictionary
        """
        return {
            "config": config,
            "capabilities": DummyProvider.get_capabilities(),
            "runtime_state": {
                "accumulated_content": "",
                "native_chunks": []
            },
            "ui_state": {}
        }
    
    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update provider state (pure function).
        
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
        return capability_id in state.get("capabilities", [])
    
    @staticmethod
    def to_native_messages(
        messages: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert to native message format (passthrough for dummy)."""
        return messages
    
    @staticmethod
    def build_request_body(
        messages: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build request body."""
        return {
            "model": state["config"]["model"],
            "messages": messages,
            "stream": True
        }
    
    @staticmethod
    def process_chunk(
        native_chunk: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process streaming chunk and update state.
        
        Args:
            native_chunk: Native chunk from API
            state: Current state
            
        Returns:
            Tuple of (partial_content, new_state)
        """
        partial_content = native_chunk.get("content", "")
        
        # Accumulate in state
        new_state = {
            **state,
            "runtime_state": {
                **state["runtime_state"],
                "accumulated_content": state["runtime_state"]["accumulated_content"] + partial_content,
                "native_chunks": state["runtime_state"]["native_chunks"] + [native_chunk]
            }
        }
        
        return partial_content, new_state
    
    @staticmethod
    def finalize(state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Finalize message from accumulated state.
        
        Args:
            state: Current state with accumulated content
            
        Returns:
            Tuple of (message, metadata)
        """
        content = state["runtime_state"]["accumulated_content"]
        
        message = {
            "role": "assistant",
            "content": content,
            "metadata": {}
        }
        
        metadata = {
            "chunk_count": len(state["runtime_state"]["native_chunks"])
        }
        
        return message, metadata
    
    @staticmethod
    def call_api(body: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Make non-streaming API call (simulated)."""
        messages = body.get("messages", [])
        last_message = messages[-1] if messages else {}
        user_content = last_message.get("content", "")
        
        return {
            "role": "assistant",
            "content": f"Echo: {user_content}",
            "metadata": {}
        }
    
    @staticmethod
    def stream_api(
        body: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (simulated)."""
        messages = body.get("messages", [])
        last_message = messages[-1] if messages else {}
        user_content = last_message.get("content", "")
        
        response_text = f"Echo: {user_content}"
        
        for char in response_text:
            yield {"content": char}
