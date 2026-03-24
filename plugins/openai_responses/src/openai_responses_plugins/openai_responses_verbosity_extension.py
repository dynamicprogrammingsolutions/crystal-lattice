"""OpenAI Responses verbosity extension.

Injects Responses API ``text.verbosity`` for models that advertise the
``supports_verbosity`` capability tag.
"""

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
                "description": "Response verbosity level for supported models.",
            }
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        if isinstance(tags, list) and "ext:openai_responses_verbosity" not in tags:
            return []
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

    def init(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        verbosity = config.get("verbosity")
        if isinstance(verbosity, str) and verbosity in _VERBOSITY_LEVELS:
            return {**state, "openai_responses_verbosity": {"verbosity": verbosity}}
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
        cfg = state.get("openai_responses_verbosity") or {}
        verbosity = cfg.get("verbosity")
        if not isinstance(verbosity, str) or verbosity not in _VERBOSITY_LEVELS:
            return list(native_messages), state

        request = state.get("request") or {}
        payload = dict(request.get("payload", {}))

        text_cfg = payload.get("text")
        if isinstance(text_cfg, dict):
            next_text_cfg = dict(text_cfg)
        else:
            next_text_cfg = {"format": {"type": "text"}}

        fmt = next_text_cfg.get("format")
        if not isinstance(fmt, dict) or not fmt:
            next_text_cfg["format"] = {"type": "text"}

        next_text_cfg["verbosity"] = verbosity
        payload["text"] = next_text_cfg

        return list(native_messages), {**state, "request": {**request, "payload": payload}}
