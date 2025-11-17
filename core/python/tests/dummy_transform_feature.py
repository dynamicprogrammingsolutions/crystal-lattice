"""
Dummy transform feature implementing transform_messages with direction.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class DummyTransformFeature:
    name: str = "dummy_transform_feature"
    version: str = "1.0.0"

    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        return {}

    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]:
        return []

    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config, "capabilities": [], "runtime_state": {}, "ui_state": {}}

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state["config"], **updates}}

    @staticmethod
    def transform_messages(messages: List[Dict[str, Any]], state: Dict[str, Any], direction: str) -> List[Dict[str, Any]]:
        # Uppercase user content when going to_compat, identity otherwise
        if direction == "to_compat":
            transformed = []
            for m in messages:
                if m.get("role") == "user" and isinstance(m.get("content"), str):
                    transformed.append({**m, "content": m["content"].upper()})
                else:
                    transformed.append(m)
            return transformed
        return messages

    @staticmethod
    def process_final_message(message: Dict[str, Any], conversation_dict: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        # No-op
        return message
