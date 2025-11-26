"""
Dummy provider plugin for testing purposes.

This plugin simulates a basic LLM provider without making actual API calls.
Follows the state-based plugin protocol with explicit state dicts.
"""

from typing import Dict, Any, List, Iterator, Tuple
from dataclasses import dataclass
from agent_core.types import ProviderPlugin


@dataclass
class DummyProvider(ProviderPlugin):
    """
    Dummy provider plugin (stateless with explicit state parameter).
    Instance methods operate on provided state; instances are short‑lived per request.
    """

    name: str = "dummy_provider"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema."""
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": False},
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Return UI elements."""
        return [{"type": "text", "key": "model", "label": "Model Name"}]


    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize provider state.
        """
        return {
            "config": dict(config),
            "runtime_state": {"accumulated_content": "", "native_chunks": []},
        }


    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return native_messages

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Reset runtime accumulators
        return {
            **state,
            "runtime_state": {
                **state.get("runtime_state", {}),
                "accumulated_content": "",
                "native_chunks": [],
            },
        }

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """
        Process streaming chunk and update state.
        Returns (final_messages, partial_messages, native_messages, new_state).
        """
        partial_content = native_chunk.get("content", "")
        new_state = {
            **state,
            "runtime_state": {
                **state["runtime_state"],
                "accumulated_content": state["runtime_state"]["accumulated_content"]
                + partial_content,
                "native_chunks": state["runtime_state"]["native_chunks"]
                + [native_chunk],
            },
        }
        partial_msg = {"role": "assistant", "content": partial_content, "metadata": {}}
        return [], ([partial_msg] if partial_content else []), [native_chunk], new_state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Finalize message from accumulated state.
        Returns (final_messages, native_messages, new_state).
        """
        content = state["runtime_state"]["accumulated_content"]
        if not content:
            return [], [], state
        message = {
            "role": "assistant",
            "content": content,
            "metadata": {"chunk_count": len(state["runtime_state"]["native_chunks"])},
        }
        return [message], [], state

    def call_api(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """Make non-streaming API call (simulated). Returns finals, partials, natives, state."""
        last_message = native_messages[-1] if native_messages else {}
        user_content = last_message.get("content", "")
        final = {
            "role": "assistant",
            "content": f"Echo: {user_content}",
            "metadata": {},
        }
        return [final], [], [], state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (simulated)."""
        last_message = native_messages[-1] if native_messages else {}
        user_content = last_message.get("content", "")
        response_text = f"Echo: {user_content}"
        for char in response_text:
            yield {"content": char}
