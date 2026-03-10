"""OpenRouter verbosity extension for `/responses`.

Injects OpenRouter `/responses` `text.verbosity`.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agent_core.types import ProviderExtensionPlugin


_VERBOSITY_LEVELS = ("low", "medium", "high", "max")


class OpenRouterResponsesVerbosityExtension(ProviderExtensionPlugin):
    name: str = "openrouter_responses_verbosity"
    version: str = "0.1.0"
    priority: int = 50

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return ["ext:openrouter_responses_verbosity"]

    def required_tags(self) -> List[str]:
        return ["openrouter_responses", "supports_verbosity"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "verbosity": {
                "type": "string",
                "required": False,
                "enum": list(_VERBOSITY_LEVELS),
                "description": "Response verbosity level (model-specific).",
            }
        }

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if "ext:openrouter_responses_verbosity" not in tags:
            return []
        if config.get("show_verbosity_ui") is False:
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
        if not isinstance(verbosity, str) or verbosity not in _VERBOSITY_LEVELS:
            return state
        return {**state, "openrouter_responses_verbosity": {"verbosity": verbosity}}

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        cfg = state.get("openrouter_responses_verbosity") or {}
        verbosity = cfg.get("verbosity")
        if not isinstance(verbosity, str) or verbosity not in _VERBOSITY_LEVELS:
            return state

        request = state.get("request") or {}
        payload = dict(request.get("payload", {}))

        text_cfg = payload.get("text")
        if isinstance(text_cfg, dict):
            next_text_cfg = dict(text_cfg)
        else:
            # OpenRouter /responses uses a `text` object with properties such as
            # `format` and `verbosity`.
            next_text_cfg = {"format": {"type": "text"}}

        fmt = next_text_cfg.get("format")
        if not isinstance(fmt, dict) or not fmt:
            next_text_cfg["format"] = {"type": "text"}

        next_text_cfg["verbosity"] = verbosity
        payload["text"] = next_text_cfg
        return {**state, "request": {**request, "payload": payload}}
