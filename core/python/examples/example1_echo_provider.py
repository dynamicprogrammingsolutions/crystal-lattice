"""
EchoProvider example (class-based provider plugin) derived from PLUGIN_EXAMPLES.md.
Streams characters of "Echo: <last user message>" as native chunks, and finalizes the full message.
"""

from typing import Any, Dict, Iterator, List, Optional, Tuple
from agent_core.types import ProviderPlugin


class EchoProvider(ProviderPlugin):
    name = "echo"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"model": {"type": "string", "default": "echo-1"}}

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [{"type": "text", "key": "model", "label": "Model"}]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Provider state is an opaque dict owned by the provider and its
        # extensions/features. This example only tracks an accumulated string
        # during streaming.
        return {"config": config, "accumulated": ""}

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), {**state, "accumulated": ""}

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return native_messages

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        last_user = next(
            (m for m in reversed(native_messages) if m.get("role") == "user"),
            {"content": ""},
        )
        text = f"Echo: {last_user.get('content', '')}"
        for ch in text:
            yield {"content": ch}

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        acc = state.get("accumulated", "") + native_chunk.get("content", "")
        new_state = {**state, "accumulated": acc}
        partial = (
            [
                {
                    "role": "assistant",
                    "content": native_chunk.get("content", ""),
                    "metadata": {},
                }
            ]
            if native_chunk.get("content")
            else []
        )
        # Keep provider-native history unchanged during streaming.
        return partial, [], list(native_messages), new_state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        content = state.get("accumulated", "")
        if not content:
            return [], list(native_messages), state
        final = {"role": "assistant", "content": content, "metadata": {}}
        return [final], [*native_messages, final], {**state, "accumulated": ""}

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        last_user = next(
            (m for m in reversed(native_messages) if m.get("role") == "user"),
            {"content": ""},
        )
        content = f"Echo: {last_user.get('content', '')}"
        final = {"role": "assistant", "content": content, "metadata": {}}
        return [], [final], [*native_messages, final], state
