"""OpenRouter verbosity extension.

This extension enables OpenAI-style ``verbosity`` control for GPT-5 models
accessed via OpenRouter.

OpenRouter exposes an OpenAI-compatible ``/chat/completions`` endpoint and
passes through many OpenAI request fields to the underlying model provider.
For GPT-5 models, setting ``verbosity`` allows callers to request shorter or
more detailed responses.

This extension only injects request configuration; it does not process
streaming chunks.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agent_core.types import ProviderExtensionPlugin


_VERBOSITY_LEVELS = ("low", "medium", "high", "max")





class OpenRouterVerbosityExtension(ProviderExtensionPlugin):
    """Provider extension that injects GPT-5 verbosity configuration."""

    name: str = "openrouter_verbosity"
    version: str = "0.1.0"
    priority: int = 50  # Run before RequestOptionsFeature

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        return ["ext:openrouter_verbosity"]

    def required_tags(self) -> List[str]:
        """Require OpenRouter provider and verbosity support."""
        return ["openrouter", "supports_verbosity"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "verbosity": {
                "type": "string",
                "required": False,
                "enum": list(_VERBOSITY_LEVELS),
                "description": "Response verbosity level (model-specific).",
            }
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "select",
                "key": "verbosity",
                "label": "Verbosity",
                "options": [{"value": v, "label": v} for v in _VERBOSITY_LEVELS],
            }
        ]

    def get_ui_elements_for_config(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return verbosity UI only when not hidden by config (e.g. show_verbosity_ui)."""
        if config.get("show_verbosity_ui") is False:
            return []
        return self.get_ui_elements()

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

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        cfg = state.get("openrouter_verbosity") or {}
        verbosity = cfg.get("verbosity")
        if not isinstance(verbosity, str) or verbosity not in _VERBOSITY_LEVELS:
            return state

        config = state.get("config", {})
        request_options = dict(config.get("request_options", {}))
        request_options["verbosity"] = verbosity

        return {
            **state,
            "config": {
                **config,
                "request_options": request_options,
            },
        }
