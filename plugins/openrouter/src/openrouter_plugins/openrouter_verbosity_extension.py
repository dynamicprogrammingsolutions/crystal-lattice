"""OpenRouter verbosity extension.

This extension enables OpenAI-style ``verbosity`` control for GPT-5 models
accessed via OpenRouter.

OpenRouter exposes an OpenAI-compatible ``/chat/completions`` endpoint and
passes through many OpenAI request fields to the underlying model provider.
For GPT-5 models, setting ``verbosity`` allows callers to request shorter or
more detailed responses.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


_VERBOSITY_LEVELS = ("low", "medium", "high", "max")


class OpenRouterVerbosityExtension(ProviderExtensionPlugin):
    """Provider extension that injects GPT-5 verbosity configuration."""

    name: str = "openrouter_verbosity"
    version: str = "0.1.0"
    priority: int = 50  # Run before RequestOptionsFeature

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        """Add supports_verbosity when the selected model supports it (e.g. gpt-5)."""
        out: List[str] = []
        selected_id = config.get("model") if isinstance(config, dict) else None
        if isinstance(selected_id, str) and selected_id and "gpt-5" in selected_id:
            out.append("supports_verbosity")
        return out

    def required_tags(self) -> List[str]:
        """Require OpenRouter provider, verbosity support."""
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

    def init(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Set verbosity in state only when the selected model supports it (e.g. gpt-5)."""
        selected_id = config.get("model") if isinstance(config, dict) else None
        if not isinstance(selected_id, str) or not selected_id or "gpt-5" not in selected_id:
            return state
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
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Add verbosity to request_options when init already set it in state."""
        cfg = state.get("openrouter_verbosity") or {}
        verbosity = cfg.get("verbosity")
        if not isinstance(verbosity, str) or verbosity not in _VERBOSITY_LEVELS:
            return list(native_messages), state

        config = state.get("config", {})
        # RequestOptionsFeature (priority 200) will merge it into the payload
        request_options = dict(config.get("request_options", {}))
        request_options["verbosity"] = verbosity

        new_state = {
            **state,
            "config": {
                **config,
                "request_options": request_options,
            },
        }
        return list(native_messages), new_state
