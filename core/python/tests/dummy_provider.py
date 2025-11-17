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
        """Update provider state (pure function)."""
        return {**state, "config": {**state["config"], **updates}}

    @staticmethod
    def to_native_messages(
        messages: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert to native message format (passthrough for dummy)."""
        return messages

    @staticmethod
    def from_native_messages(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return native_messages

    @staticmethod
    def initialize_request(messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        # Reset runtime accumulators
        return {
            **state,
            "runtime_state": {
                **state.get("runtime_state", {}),
                "accumulated_content": "",
                "native_chunks": []
            }
        }

    @staticmethod
    def process_chunk(
        native_chunk: Dict[str, Any],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Process streaming chunk and update state.
        Returns (final_messages, partial_messages, native_messages, new_state).
        """
        partial_content = native_chunk.get("content", "")
        new_state = {
            **state,
            "runtime_state": {
                **state["runtime_state"],
                "accumulated_content": state["runtime_state"]["accumulated_content"] + partial_content,
                "native_chunks": state["runtime_state"]["native_chunks"] + [native_chunk],
            },
        }
        partial_msg = {"role": "assistant", "content": partial_content, "metadata": {}}
        return [], ([partial_msg] if partial_content else []), [native_chunk], new_state

    @staticmethod
    def finalize(
        messages: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Finalize message from accumulated state.
        Returns (final_messages, native_messages, new_state).
        """
        content = state["runtime_state"]["accumulated_content"]
        message = {"role": "assistant", "content": content, "metadata": {"chunk_count": len(state["runtime_state"]["native_chunks"])}}
        return [message], [], state

    @staticmethod
    def call_api(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Make non-streaming API call (simulated). Returns finals, partials, natives, state."""
        last_message = native_messages[-1] if native_messages else {}
        user_content = last_message.get("content", "")
        final = {"role": "assistant", "content": f"Echo: {user_content}", "metadata": {}}
        return [final], [], [], state

    @staticmethod
    def stream_api(
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (simulated)."""
        last_message = native_messages[-1] if native_messages else {}
        user_content = last_message.get("content", "")
        response_text = f"Echo: {user_content}"
        for char in response_text:
            yield {"content": char}
