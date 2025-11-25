"""
Dummy feature plugin for testing purposes.

This plugin adds a prefix to all assistant responses.
Follows the state-based plugin protocol with explicit state dicts.
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

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **config}}


    # Stateless transforms
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages
    ) -> List[Dict[str, Any]]:
        return messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages
    ) -> List[Dict[str, Any]]:
        return native_messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Add prefix to all final messages."""
        prefix = state.get("config", {}).get("prefix", "[TEST]")
        finals = [{**m, "content": f"{prefix} {m['content']}"} for m in final_messages]
        return finals, native_messages, state
