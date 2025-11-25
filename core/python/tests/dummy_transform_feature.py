"""
Dummy transform feature updated to finalize outputs.
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from agent_core.types import FeaturePlugin


@dataclass
class DummyTransformFeature(FeaturePlugin):
    name: str = "dummy_transform_feature"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **config}}


    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return state

    # Stateless transforms
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages
    ) -> List[Dict[str, Any]]:
        return messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages
    ) -> List[Dict[str, Any]]:
        return native_messages

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Uppercase assistant response content
        finals = [
            {
                **m,
                "content": (
                    m.get("content", "").upper()
                    if isinstance(m.get("content"), str)
                    else m.get("content")
                ),
            }
            for m in final_messages
        ]
        return finals, native_messages, state
