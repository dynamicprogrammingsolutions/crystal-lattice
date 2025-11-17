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
        return {"prefix": {"type": "string", "default": "[TEST]"}}

    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]:
        """Return UI elements."""
        return [{"type": "text", "key": "prefix", "label": "Response Prefix"}]

    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config, "capabilities": [], "runtime_state": {}, "ui_state": {}}

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state["config"], **updates}}

    @staticmethod
    def initialize_request(messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        # No-op for dummy feature
        return state

    @staticmethod
    def finalize(
        messages: List[Dict[str, Any]],
        output: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add prefix to all final messages."""
        prefix = state["config"].get("prefix", "[TEST]")
        final_messages = [
            {**m, "content": f"{prefix} {m['content']}"}
            for m in output.get("final_messages", [])
        ]
        return {**output, "final_messages": final_messages}
