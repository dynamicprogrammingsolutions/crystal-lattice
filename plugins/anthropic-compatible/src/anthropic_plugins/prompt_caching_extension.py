"""Anthropic automatic prompt caching controls."""

from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin


class AnthropicPromptCachingExtension(ProviderExtensionPlugin):
    name = "anthropic_prompt_caching"
    version = "0.1.0"
    priority = 70

    def required_tags(self) -> list[str]:
        return ["provider:anthropic", "supports_prompt_caching"]

    def get_tags(
        self,
        config: dict[str, Any],
        models: list[dict[str, Any]],
    ) -> list[str]:
        return ["ext:anthropic_prompt_caching"]

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "enable_prompt_caching": {
                "type": "boolean",
                "default": True,
            },
            "prompt_cache_ttl": {
                "type": "string",
                "enum": ["5m", "1h"],
                "default": "5m",
            },
        }

    def get_ui_elements(
        self,
        config: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "enable_prompt_caching",
                "label": "Enable Anthropic prompt caching",
                "default": bool(config.get("enable_prompt_caching", True)),
            },
            {
                "type": "select",
                "key": "prompt_cache_ttl",
                "label": "Anthropic prompt cache TTL",
                "options": [
                    {"value": "5m", "label": "5 minutes"},
                    {"value": "1h", "label": "1 hour"},
                ],
                "default": (
                    config.get("prompt_cache_ttl")
                    if config.get("prompt_cache_ttl") in {"5m", "1h"}
                    else "5m"
                ),
            },
        ]

    def init(self, config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        return state

    def initialize_request(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ):
        config = state.get("config")
        config = config if isinstance(config, dict) else {}
        if config.get("enable_prompt_caching") is False:
            return list(native_messages), state
        ttl = config.get("prompt_cache_ttl")
        ttl = ttl if ttl in {"5m", "1h"} else "5m"
        request = state.get("request")
        request = request if isinstance(request, dict) else {}
        payload = {
            **dict(request.get("payload") or {}),
            "cache_control": {"type": "ephemeral", "ttl": ttl},
        }
        return list(native_messages), {
            **state,
            "request": {**request, "payload": payload},
        }


__all__ = ["AnthropicPromptCachingExtension"]
