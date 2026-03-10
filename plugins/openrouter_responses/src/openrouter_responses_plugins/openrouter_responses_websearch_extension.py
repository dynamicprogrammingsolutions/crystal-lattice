"""OpenRouter web search extension for `/responses`.

Request-side behavior is OpenRouter-specific and likely shared across
endpoints: inject the `plugins` entry for web search.

Response-side citation extraction for `/responses` is handled by the provider
(citations are carried as annotations on `output_text` parts).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core.types import ProviderExtensionPlugin


class OpenRouterResponsesWebSearchExtension(ProviderExtensionPlugin):
    name: str = "openrouter_responses_websearch"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enable_web_search": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Enable OpenRouter web search plugin.",
            },
            "web_search_plugin_id": {
                "type": "string",
                "required": False,
                "default": "web",
                "description": "OpenRouter plugin id for web search.",
            },
            "web_search_engine": {
                "type": "string",
                "required": False,
                "default": "native",
                "description": "Engine name for OpenRouter web search.",
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        if tags is not None and "ext:openrouter_responses_websearch" not in tags:
            return []
        return [
            {
                "type": "checkbox",
                "key": "enable_web_search",
                "label": "Enable Web Search (OpenRouter /responses)",
            }
        ]

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return ["ext:openrouter_responses_websearch"]

    def required_tags(self) -> List[str]:
        return ["openrouter_responses"]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        enabled = config.get("enable_web_search", False)
        if not enabled:
            return state

        plugin_id = config.get("web_search_plugin_id") or "web"
        engine = config.get("web_search_engine") or "native"
        return {
            **state,
            "openrouter_responses_websearch": {
                "enabled": True,
                "plugin_id": str(plugin_id),
                "engine": str(engine),
            },
        }

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Provider surfaces URL citations into `metadata.url_citations`.
        return messages

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        cfg = state.get("openrouter_responses_websearch") or {}
        if not isinstance(cfg, dict) or not cfg.get("enabled"):
            return state

        request = state.get("request") or {}
        payload = dict(request.get("payload", {}))

        plugin_id = cfg.get("plugin_id") or "web"
        engine = cfg.get("engine") or "native"

        plugins_value = payload.get("plugins")
        if isinstance(plugins_value, list):
            plugins: List[Any] = list(plugins_value)
        elif plugins_value is None:
            plugins = []
        else:
            plugins = []

        entry = {"id": plugin_id, "engine": engine}
        if not any(
            isinstance(p, dict) and p.get("id") == entry["id"] and p.get("engine") == entry["engine"]
            for p in plugins
        ):
            plugins.append(entry)

        payload["plugins"] = plugins
        return {**state, "request": {**request, "payload": payload}}
