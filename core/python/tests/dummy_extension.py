"""
Dummy provider extension plugin for testing purposes.

This plugin extends the dummy provider with additional processing during streaming.
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from agent_core.types import ProviderExtensionPlugin

@dataclass
class DummyExtension(ProviderExtensionPlugin):
    """
    Dummy provider extension using shared provider state.
    """

    name: str = "dummy_extension"
    version: str = "1.0.0"
    target_provider: str = "dummy_provider"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "prefix": {"type": "string", "default": "[EXT]"},
            "enabled": {"type": "boolean", "default": True},
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {"type": "checkbox", "key": "enabled", "label": "Enable Extension"},
            {"type": "text", "key": "prefix", "label": "Extension Prefix"},
        ]

    # New lifecycle: init accepts shared state
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        # Store extension config under provider state's config
        new_config = {**state.get("config", {}), **config}
        # Initialize extension counters within provider runtime_state
        rs = state.get("runtime_state", {})
        rs = {**rs, "extension_processed_chunks": 0}
        return {**state, "config": new_config, "runtime_state": rs}

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **updates}}

    # Stateless transforms
    def to_native_messages(
        self,
        messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return messages

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return native_messages

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
        enabled = state.get("config", {}).get("enabled", True)
        if not enabled:
            return partial_messages, final_messages, native_messages, state
        processed = state.get("runtime_state", {}).get(
            "extension_processed_chunks", 0
        ) + (1 if native_chunk is not None else 0)
        rs = {**state.get("runtime_state", {}), "extension_processed_chunks": processed}
        prefix = state.get("config", {}).get("prefix", "[EXT]")
        enhanced_finals = (
            [{**m, "content": f"{prefix} {m['content']}"} for m in final_messages]
            if final_messages
            else final_messages
        )
        if enhanced_finals:
            last = enhanced_finals[-1]
            meta = {**last.get("metadata", {}), "extension_processed_chunks": processed}
            enhanced_finals[-1] = {**last, "metadata": meta}
        return (
            partial_messages,
            enhanced_finals,
            native_messages,
            {**state, "runtime_state": rs},
        )

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        enabled = state.get("config", {}).get("enabled", True)
        if not enabled:
            return final_messages, native_messages, state
        prefix = state.get("config", {}).get("prefix", "[EXT]")
        finals = [{**m, "content": f"{prefix} {m['content']}"} for m in final_messages]
        # Attach processed chunk count metadata to last final if present
        if finals:
            count = state.get("runtime_state", {}).get("extension_processed_chunks", 0)
            last = finals[-1]
            finals[-1] = {
                **last,
                "metadata": {
                    **last.get("metadata", {}),
                    "extension_processed_chunks": count,
                },
            }
        return finals, native_messages, state
