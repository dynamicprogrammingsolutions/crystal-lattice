"""
EchoProvider example (class-based provider plugin) derived from PLUGIN_EXAMPLES.md.
Streams characters of "Echo: <last user message>" as native chunks, and finalizes the full message.
"""
from typing import Any, Dict, List, Iterator, Tuple


class EchoProvider:
    name = "echo"
    version = "1.0.0"

    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        return {"model": {"type": "string", "default": "echo-1"}}

    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]:
        return [{"type": "text", "key": "model", "label": "Model"}]

    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config, "runtime_state": {"accumulated": ""}}

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **updates}}

    @staticmethod
    def initialize_request(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "runtime_state": {**state.get("runtime_state", {}), "accumulated": ""}}

    @staticmethod
    def to_native_messages(messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return list(messages)

    @staticmethod
    def from_native_messages(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return list(native_messages)

    @staticmethod
    def stream_api(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        last_user = next((m for m in reversed(native_messages) if m.get("role") == "user"), {"content": ""})
        text = f"Echo: {last_user.get('content', '')}"
        for ch in text:
            yield {"content": ch}

    @staticmethod
    def process_chunk(
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        acc = state.get("runtime_state", {}).get("accumulated", "") + native_chunk.get("content", "")
        new_state = {**state, "runtime_state": {**state.get("runtime_state", {}), "accumulated": acc}}
        partial = (
            [{"role": "assistant", "content": native_chunk.get("content", ""), "metadata": {}}]
            if native_chunk.get("content")
            else []
        )
        return [], partial, [], new_state

    @staticmethod
    def finalize(
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        content = state.get("runtime_state", {}).get("accumulated", "")
        if not content:
            return [], [], state
        final = [{"role": "assistant", "content": content, "metadata": {}}]
        return final, [], state

    @staticmethod
    def call_api(
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        last_user = next((m for m in reversed(native_messages) if m.get("role") == "user"), {"content": ""})
        content = f"Echo: {last_user.get('content', '')}"
        return ([{"role": "assistant", "content": content, "metadata": {}}], [], [], state)
