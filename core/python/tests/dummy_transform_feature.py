"""
Dummy transform feature updated to finalize outputs.
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
    def initialize_request(messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    @staticmethod
    def finalize(messages: List[Dict[str, Any]], output: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        # Uppercase assistant response content
        finals = [
            {**m, "content": (m.get("content", "").upper() if isinstance(m.get("content"), str) else m.get("content"))}
            for m in output.get("final_messages", [])
        ]
        return {**output, "final_messages": finals}
