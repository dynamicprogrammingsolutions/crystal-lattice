"""OpenAI Responses verbosity extension scaffold."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


_VERBOSITY_LEVELS = ("low", "medium", "high")


class OpenAIResponsesVerbosityExtension(ProviderExtensionPlugin):
    name: str = "openai_responses_verbosity"
    version: str = "0.1.0"
    priority: int = 50

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return ["ext:openai_responses_verbosity"]

    def required_tags(self) -> List[str]:
        return ["openai_responses", "supports_verbosity"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "verbosity": {
                "type": "string",
                "required": False,
                "enum": list(_VERBOSITY_LEVELS),
            }
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        if isinstance(config, dict) and config.get("show_verbosity_ui") is False:
            return []
        return [
            {
                "type": "select",
                "key": "verbosity",
                "label": "Verbosity",
                "options": [{"value": v, "label": v} for v in _VERBOSITY_LEVELS],
            }
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        verbosity = config.get("verbosity")
        if isinstance(verbosity, str) and verbosity in _VERBOSITY_LEVELS:
            return {**state, "openai_responses_verbosity": verbosity}
        return state

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return list(messages)

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), state
