from __future__ import annotations

"""Feature template (skeleton).

Features are cold-path only. They run during:

- init (shared provider state setup)
- initialize_request (per-turn setup)
- finalize (transform provider-native finals and/or native history)

This skeleton is intentionally minimal/no-op.
"""

from typing import Any, Dict, List, Tuple

from agent_core.types import FeaturePlugin


class TemplateFeature(FeaturePlugin):
    name: str = "template_feature"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state


__all__ = ["TemplateFeature"]
