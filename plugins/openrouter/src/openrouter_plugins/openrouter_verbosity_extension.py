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


_VERBOSITY_LEVELS = ("low", "medium", "high", "max")


class OpenRouterVerbosityExtension(ProviderExtensionPlugin):
    """Provider extension that injects GPT-5 verbosity configuration."""

    name: str = "openrouter_verbosity"
    version: str = "0.1.0"
    priority: int = 50  # Run before RequestOptionsFeature

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        """Add supports_verbosity when the selected model supports it (e.g. gpt-5)."""
       # out: List[str] = ["ext:openrouter_verbosity"]
        out: List[str] = []
        selected_id = config.get("model") if isinstance(config, dict) else None
        if isinstance(selected_id, str) and selected_id:
            if "gpt-5" in selected_id:
                out.append("supports_verbosity")
            elif isinstance(models, list):
                for m in models:
                    if isinstance(m, dict) and m.get("id") == selected_id:
                        supported_params = m.get("supported_parameters") or []
                        if isinstance(supported_params, list) and "verbosity" in supported_params:
                            out.append("supports_verbosity")
                        break
        return out

    def required_tags(self) -> List[str]:
        """Require OpenRouter provider, verbosity support, and request_options feature."""
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

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if "supports_verbosity" not in tags:
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

        return {
            **state,
            "openrouter_verbosity": {
                "verbosity": verbosity,
            },
        }

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        if "supports_verbosity" not in state.get("available_tags", []):
            return state
        cfg = state.get("openrouter_verbosity") or {}
        verbosity = cfg.get("verbosity")
        if not isinstance(verbosity, str) or verbosity not in _VERBOSITY_LEVELS:
            return state

        config = state.get("config", {})
        # RequestOptionsFeature (priority 200) will merge it into the payload
        request_options = dict(config.get("request_options", {}))
        request_options["verbosity"] = verbosity

        return {
            **state,
            "config": {
                **config,
                "request_options": request_options,
            },
        }
