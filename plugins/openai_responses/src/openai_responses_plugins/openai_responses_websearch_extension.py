"""OpenAI Responses web search extension.

Owns request-side web search enablement and optional source inclusion while
leaving response-derived citation/source normalization in the provider.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from agent_core.types import ProviderExtensionPlugin


_STATE_KEY = "_openai_responses_websearch"
_FULL_SOURCES_INCLUDE_KEY = "web_search_call.action.sources"
_SEARCH_CONTEXT_SIZES = ("low", "medium", "high")


class OpenAIResponsesWebSearchExtension(ProviderExtensionPlugin):
    name: str = "openai_responses_websearch"
    version: str = "0.1.0"
    priority: int = 110

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        _ = config, models
        return ["ext:openai_responses_websearch"]

    def required_tags(self) -> List[str]:
        return ["openai_responses"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enable_web_search": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Enable OpenAI Responses web search.",
            },
            "include_full_web_search_sources": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Include the full consulted source list in response metadata.",
            },
            "web_search_allowed_domains": {
                "type": "array",
                "required": False,
                "items": {"type": "string"},
                "description": "Optional allow-list of domains for web search.",
            },
            "web_search_search_context_size": {
                "type": "string",
                "required": False,
                "enum": list(_SEARCH_CONTEXT_SIZES),
                "description": "Optional web search context size.",
            },
            "web_search_user_location_country": {
                "type": "string",
                "required": False,
            },
            "web_search_user_location_city": {
                "type": "string",
                "required": False,
            },
            "web_search_user_location_region": {
                "type": "string",
                "required": False,
            },
            "web_search_user_location_timezone": {
                "type": "string",
                "required": False,
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = config, models
        if isinstance(tags, list) and "ext:openai_responses_websearch" not in tags:
            return []
        return [
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": "enable_web_search",
                "label": "Enable web search",
                "icon": "globe",
                "rich_ui": {
                    "kind": "toggle",
                    "label": "Web search",
                    "show_label": False,
                    "placements": ["composer"],
                    "default_pinned": True,
                    "options": [
                        {
                            "value": False,
                            "label": "Off",
                            "icon": "globe",
                            "tone": "primary",
                        },
                        {
                            "value": True,
                            "label": "On",
                            "icon": "globe",
                            "tone": "success",
                        },
                    ],
                },
            },
            {
                "type": "checkbox",
                "key": "include_full_web_search_sources",
                "label": "Include full consulted source list",
            },
            {
                "type": "text",
                "key": "web_search_allowed_domains",
                "label": "Allowed domains",
            },
            {
                "type": "select",
                "key": "web_search_search_context_size",
                "label": "Web search context size",
                "options": [
                    {"value": value, "label": value} for value in _SEARCH_CONTEXT_SIZES
                ],
            },
            {
                "type": "text",
                "key": "web_search_user_location_country",
                "label": "User location country",
            },
            {
                "type": "text",
                "key": "web_search_user_location_city",
                "label": "User location city",
            },
            {
                "type": "text",
                "key": "web_search_user_location_region",
                "label": "User location region",
            },
            {
                "type": "text",
                "key": "web_search_user_location_timezone",
                "label": "User location timezone",
            },
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if not self._truthy(config.get("enable_web_search")):
            return state

        normalized: Dict[str, Any] = {"enabled": True}

        allowed_domains = self._normalize_allowed_domains(
            config.get("web_search_allowed_domains")
        )
        if allowed_domains:
            normalized["allowed_domains"] = allowed_domains

        context_size = config.get("web_search_search_context_size")
        if isinstance(context_size, str) and context_size in _SEARCH_CONTEXT_SIZES:
            normalized["search_context_size"] = context_size

        user_location = self._normalize_user_location(config)
        if user_location:
            normalized["user_location"] = user_location

        if self._truthy(config.get("include_full_web_search_sources")):
            normalized["include_full_sources"] = True

        return {**state, _STATE_KEY: normalized}

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        _ = messages
        return list(native_messages)

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        _ = native_messages
        return list(messages)

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        cfg = state.get(_STATE_KEY)
        if not isinstance(cfg, dict) or not cfg.get("enabled"):
            return list(native_messages), state

        request = state.get("request")
        if not isinstance(request, dict):
            return list(native_messages), state

        payload = dict(request.get("payload") or {})
        payload_tools = (
            list(payload.get("tools")) if isinstance(payload.get("tools"), list) else []
        )

        if not any(self._is_web_search_tool_entry(entry) for entry in payload_tools):
            payload_tools.append(self._build_web_search_tool(cfg))
        payload["tools"] = payload_tools

        if cfg.get("include_full_sources"):
            payload["include"] = self._merge_include_values(
                payload.get("include"), _FULL_SOURCES_INCLUDE_KEY
            )

        return list(native_messages), {
            **state,
            "request": {**request, "payload": payload},
        }

    def _truthy(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    def _normalize_allowed_domains(self, raw: Any) -> List[str]:
        values: List[str] = []
        if isinstance(raw, (list, tuple)):
            values = [
                self._normalize_domain_entry(item) for item in raw if item is not None
            ]
        elif isinstance(raw, str):
            values = [self._normalize_domain_entry(part) for part in raw.split(",")]

        normalized: List[str] = []
        for value in values:
            if not value or value in normalized:
                continue
            normalized.append(value)
        return normalized

    def _normalize_domain_entry(self, raw: Any) -> str:
        if not isinstance(raw, str):
            return ""
        candidate = raw.strip()
        if not candidate:
            return ""

        parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
        domain = parsed.netloc or parsed.path
        domain = domain.strip().rstrip("/")
        if not domain:
            return ""
        return domain.lower()

    def _normalize_user_location(
        self, config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        user_location: Dict[str, Any] = {}
        for config_key, target_key in (
            ("web_search_user_location_country", "country"),
            ("web_search_user_location_city", "city"),
            ("web_search_user_location_region", "region"),
            ("web_search_user_location_timezone", "timezone"),
        ):
            value = config.get(config_key)
            if not isinstance(value, str) or not value.strip():
                continue
            user_location[target_key] = value.strip()

        if not user_location:
            return None

        return {"type": "approximate", **user_location}

    def _build_web_search_tool(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        tool: Dict[str, Any] = {"type": "web_search"}

        allowed_domains = cfg.get("allowed_domains")
        if isinstance(allowed_domains, list) and allowed_domains:
            tool["filters"] = {"allowed_domains": list(allowed_domains)}

        context_size = cfg.get("search_context_size")
        if isinstance(context_size, str) and context_size in _SEARCH_CONTEXT_SIZES:
            tool["search_context_size"] = context_size

        user_location = cfg.get("user_location")
        if isinstance(user_location, dict) and user_location:
            tool["user_location"] = dict(user_location)

        return tool

    def _is_web_search_tool_entry(self, entry: Any) -> bool:
        if not isinstance(entry, dict):
            return False
        entry_type = entry.get("type")
        return isinstance(entry_type, str) and entry_type.startswith("web_search")

    def _merge_include_values(self, raw_include: Any, required_value: str) -> List[str]:
        include_values: List[str] = []
        if isinstance(raw_include, list):
            include_values = [
                item for item in raw_include if isinstance(item, str) and item
            ]
        elif isinstance(raw_include, tuple):
            include_values = [
                item for item in raw_include if isinstance(item, str) and item
            ]
        elif isinstance(raw_include, str) and raw_include:
            include_values = [raw_include]

        if required_value not in include_values:
            include_values.append(required_value)
        return include_values
