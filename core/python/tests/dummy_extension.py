"""
Dummy provider extension plugin for testing purposes.

This plugin extends the dummy provider with additional processing during streaming.
"""

from typing import Dict, Any, List, Tuple, Optional
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
        return {**state, "config": {**state["config"], **updates}}

    @staticmethod
    def process_chunk(
        native_chunk: Optional[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        provider_state: Dict[str, Any],
        extension_state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not extension_state["config"].get("enabled", True):
            return partial_messages, final_messages, native_messages, extension_state
        # Count processed native chunk if present
        processed = extension_state["runtime_state"]["processed_chunks"] + (1 if native_chunk is not None else 0)
        new_state = {
            **extension_state,
            "runtime_state": {**extension_state["runtime_state"], "processed_chunks": processed},
        }
        # If we have final messages, add prefix
        prefix = extension_state["config"].get("prefix", "[EXT]")
        enhanced_finals = [
            {**m, "content": f"{prefix} {m['content']}"}
            for m in final_messages
        ] if final_messages else final_messages
        # Add metadata about processed chunks to last final message if exists
        if enhanced_finals:
            last = enhanced_finals[-1]
            meta = {**last.get("metadata", {}), "extension_processed_chunks": processed}
            enhanced_finals[-1] = {**last, "metadata": meta}
        return partial_messages, enhanced_finals, native_messages, new_state
