"""OpenRouter verbosity extension.

This extension enables OpenAI-style ``verbosity`` control for GPT-5 models
accessed via OpenRouter.

OpenRouter exposes an OpenAI-compatible ``/chat/completions`` endpoint and
passes through many OpenAI request fields to the underlying model provider.
For GPT-5 models, setting ``verbosity`` allows callers to request shorter or
more detailed responses.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agent_core.types import ProviderExtensionPlugin


_VERBOSITY_LEVELS = ("low", "medium", "high")


def _is_gpt5_model(model_id: Any) -> bool:
    if not isinstance(model_id, str):
        return False
    lowered = model_id.lower()
    return "gpt-5" in lowered


class OpenRouterVerbosityExtension(ProviderExtensionPlugin):
    """Provider extension that injects GPT-5 verbosity configuration."""

    name: str = "openrouter_verbosity"
    version: str = "0.1.0"

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return ["ext:openrouter_verbosity"]

    def required_tags(self) -> List[str]:
        return ["openrouter"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "verbosity": {
                "type": "string",
                "required": False,
                "enum": list(_VERBOSITY_LEVELS),
                "description": "GPT-5 response verbosity (OpenAI-style).",
            }
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "select",
                "key": "verbosity",
                "label": "Verbosity (GPT-5)",
                "options": [{"value": v, "label": v} for v in _VERBOSITY_LEVELS],
            }
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        verbosity = config.get("verbosity")
        if not isinstance(verbosity, str) or verbosity not in _VERBOSITY_LEVELS:
            return state

        return {
            **state,
            "openrouter_verbosity": {
                "verbosity": verbosity,
            },
        }

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        cfg = state.get("openrouter_verbosity") or {}
        verbosity = cfg.get("verbosity")
        if not isinstance(verbosity, str) or verbosity not in _VERBOSITY_LEVELS:
            return state

        request = state.get("request") or {}
        payload = dict(request.get("payload", {}))
        model_id = payload.get("model")
        if not _is_gpt5_model(model_id):
            return state

        payload["verbosity"] = verbosity
        return {
            **state,
            "request": {
                **request,
                "payload": payload,
            },
        }
