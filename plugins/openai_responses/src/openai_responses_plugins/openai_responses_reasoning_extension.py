"""OpenAI Responses reasoning extension scaffold."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


class OpenAIResponsesReasoningExtension(ProviderExtensionPlugin):
    name: str = "openai_responses_reasoning"
    version: str = "0.1.0"
    priority: int = 50

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return ["ext:openai_responses_reasoning"]

    def required_tags(self) -> List[str]:
        return ["openai_responses", "supports_reasoning", "feature:request_options"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enable_reasoning": {
                "type": "boolean",
                "required": False,
                "description": "Enable model reasoning when supported.",
            },
            "reasoning_effort": {
                "type": "string",
                "required": False,
                "enum": ["none", "minimal", "low", "medium", "high", "xhigh"],
            },
            "reasoning_summary": {
                "type": "string",
                "required": False,
                "enum": ["auto", "concise", "detailed"],
            },
            "reasoning_max_tokens": {
                "type": "number",
                "required": False,
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
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
