"""
Dummy feature plugin for testing purposes.

This plugin adds a prefix to all assistant responses.
Follows the state-based plugin protocol.
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from agent_core.types import FeaturePlugin


@dataclass
class DummyFeature(FeaturePlugin):
    """
    Dummy feature plugin operating on shared provider state.
    """

    name: str = "dummy_feature"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"prefix": {"type": "string", "default": "[TEST]"}}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [{"type": "text", "key": "prefix", "label": "Response Prefix"}]

    @staticmethod
    def init(config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **config}}

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **updates}}

    # Stateless transforms
    @staticmethod
    def to_native_messages(
        messages: List[Dict[str, Any]], native_messages
    ) -> List[Dict[str, Any]]:
        return messages

    @staticmethod
    def from_native_messages(
        native_messages: List[Dict[str, Any]], messages
    ) -> List[Dict[str, Any]]:
        return native_messages

    @staticmethod
    def initialize_request(
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return state

    @staticmethod
    def finalize(
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Add prefix to all final messages."""
        prefix = state.get("config", {}).get("prefix", "[TEST]")
        finals = [{**m, "content": f"{prefix} {m['content']}"} for m in final_messages]
        return finals, native_messages, state
