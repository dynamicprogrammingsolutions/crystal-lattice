"""
PrefixExtension example (class-based provider extension) derived from PLUGIN_EXAMPLES.md.
Adds a prefix to final assistant messages and counts processed chunks in metadata.
"""

from typing import Any, Dict, List, Tuple, Optional
from agent_core.types import ProviderExtensionPlugin

class PrefixExtension(ProviderExtensionPlugin):
    name: str = "prefix_extension"
    version: str = "1.0.0"
    target_provider: str = "echo"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {"type": "boolean", "default": True},
            "prefix": {"type": "string", "default": "[EXT]"},
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {"type": "checkbox", "key": "enabled", "label": "Enable Extension"},
            {"type": "text", "key": "prefix", "label": "Prefix"},
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            **state,
            "config": {**state.get("config", {}), **config},
            "extension_processed_chunks": 0,
        }

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return messages

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return messages

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return state

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        if not state.get("config", {}).get("enabled", True):
            return partial_messages, final_messages, native_messages, state
        processed = state.get("extension_processed_chunks", 0) + (
            1 if native_chunk is not None else 0
        )
        prefix = state.get("config", {}).get("prefix", "[EXT]")
        finals = (
            [{**m, "content": f"{prefix} {m['content']}"} for m in final_messages]
            if final_messages
            else final_messages
        )
        if finals:
            last = finals[-1]
            finals[-1] = {
                **last,
                "metadata": {
                    **last.get("metadata", {}),
                    "extension_processed_chunks": processed,
                },
            }
        return partial_messages, finals, native_messages, {
            **state,
            "extension_processed_chunks": processed,
        }

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not state.get("config", {}).get("enabled", True):
            return final_messages, native_messages, state
        prefix = state.get("config", {}).get("prefix", "[EXT]")
        finals = [{**m, "content": f"{prefix} {m['content']}"} for m in final_messages]
        if finals:
            count = state.get("extension_processed_chunks", 0)
            last = finals[-1]
            finals[-1] = {
                **last,
                "metadata": {
                    **last.get("metadata", {}),
                    "extension_processed_chunks": count,
                },
            }
        return finals, native_messages, state
