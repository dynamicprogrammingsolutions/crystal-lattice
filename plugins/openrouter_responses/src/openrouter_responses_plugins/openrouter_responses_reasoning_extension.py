"""OpenRouter reasoning extension for `/responses`.

This extension currently focuses on request-side configuration by writing
reasoning options into `request_options`, which `RequestOptionsFeature` merges
into the outbound request payload.

Reasoning output extraction for `/responses` is handled by the provider (it is
carried as output items rather than chat-style `reasoning` fields).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core.types import ProviderExtensionPlugin


class OpenRouterResponsesReasoningExtension(ProviderExtensionPlugin):
    name: str = "openrouter_responses_reasoning"
    version: str = "0.1.0"
    priority: int = 50  # Run before RequestOptionsFeature

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return ["ext:openrouter_responses_reasoning"]

    def required_tags(self) -> List[str]:
        return ["openrouter_responses", "supports_reasoning", "feature:request_options"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "reasoning_effort": {
                "type": "string",
                "required": False,
                "enum": ["low", "medium", "high", "xhigh"],
                "description": "Control reasoning depth (model-specific)",
            },
            "reasoning_summary": {
                "type": "string",
                "required": False,
                "enum": ["auto", "none"],
                "description": "Whether to request a reasoning summary (Responses API)",
            },
            "enable_reasoning": {
                "type": "boolean",
                "required": False,
                "description": "Enable reasoning/thinking for models that support it",
            },
            "reasoning_max_tokens": {
                "type": "number",
                "required": False,
                "description": "Specific token limit (model/provider-specific)",
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        if tags is not None and "supports_reasoning" not in tags:
            return []
        ui: List[Dict[str, Any]] = [
            {"type": "checkbox", "key": "enable_reasoning", "label": "Enable Reasoning"}
        ]
        if tags is not None and "supports_reasoning_effort" in tags:
            ui.append(
                {
                    "type": "select",
                    "key": "reasoning_effort",
                    "label": "Reasoning Effort",
                    "options": [
                        {"value": "low", "label": "low"},
                        {"value": "medium", "label": "medium"},
                        {"value": "high", "label": "high"},
                        {"value": "xhigh", "label": "xhigh"},
                    ],
                }
            )
        return ui

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        has_reasoning_config = any(
            [
                config.get("enable_reasoning"),
                config.get("reasoning_effort"),
                config.get("reasoning_max_tokens"),
                config.get("reasoning_summary"),
            ]
        )
        if not has_reasoning_config:
            return state

        reasoning_config: Dict[str, Any] = {"reasoning": {}}
        if "enable_reasoning" in config:
            reasoning_config["reasoning"]["enabled"] = config["enable_reasoning"]
        if "reasoning_effort" in config:
            reasoning_config["reasoning"]["effort"] = config["reasoning_effort"]
        if "reasoning_max_tokens" in config:
            reasoning_config["reasoning"]["max_tokens"] = config["reasoning_max_tokens"]

        summary = config.get("reasoning_summary")
        if summary == "auto":
            reasoning_config["reasoning"]["summary"] = "auto"
        elif summary == "none":
            pass

        return {**state, "openrouter_responses_reasoning": reasoning_config}

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return messages

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        reasoning_config = state.get("openrouter_responses_reasoning")
        if not isinstance(reasoning_config, dict):
            return state

        config = state.get("config", {})
        if not isinstance(config, dict):
            config = {}
        request_options = dict(config.get("request_options", {}))
        request_options["reasoning"] = {
            **request_options.get("reasoning", {}),
            **(reasoning_config.get("reasoning") or {}),
        }

        return {**state, "config": {**config, "request_options": request_options}}
