"""OpenAI Responses prompt caching extension.

Owns prompt-cache request shaping plus the session-owned prompt cache key
lifecycle described in subtask 130.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin, Session


_ENABLE_KEY = "enable_prompt_cache_key"
_PROMPT_CACHE_KEY = "prompt_cache_key"
_RETENTION_24H_KEY = "enable_prompt_cache_retention_24h"
_RETENTION_VALUE = "24h"


def _effective_auth_mode(config: Dict[str, Any]) -> str:
    raw = config.get("_openai_responses_effective_auth_mode")
    if isinstance(raw, str) and raw.strip().lower() in {"api", "chatgpt"}:
        return raw.strip().lower()
    requested = config.get("auth_mode")
    if not isinstance(requested, str):
        return "api"
    normalized = requested.strip().lower()
    if normalized == "api_key":
        return "api"
    if normalized == "chatgpt":
        return "chatgpt"
    return "api"


class OpenAIResponsesPromptCachingExtension(ProviderExtensionPlugin):
    name: str = "openai_responses_prompt_caching"
    version: str = "0.1.0"
    priority: int = 55

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        _ = config, models
        return ["ext:openai_responses_prompt_caching"]

    def required_tags(self) -> List[str]:
        return ["openai_responses"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            _ENABLE_KEY: {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Enable session-owned prompt cache key injection.",
            },
            _PROMPT_CACHE_KEY: {
                "type": "string",
                "required": False,
                "description": "Session-owned OpenAI prompt cache key.",
            },
            _RETENTION_24H_KEY: {
                "type": "boolean",
                "required": False,
                "description": "Request 24-hour prompt cache retention for eligible requests.",
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = config, tags, models
        return [
            {
                "type": "checkbox",
                "key": _ENABLE_KEY,
                "label": "Enable prompt cache key",
            },
            {
                "type": "text",
                "key": _PROMPT_CACHE_KEY,
                "label": "Prompt cache key",
            },
            {
                "type": "checkbox",
                "key": _RETENTION_24H_KEY,
                "label": "Use 24-hour prompt cache retention",
            },
            {
                "ui_type": "session_action",
                "id": "regenerate_prompt_cache_key",
                "label": "Regenerate prompt cache key",
                "icon": "refresh-cw",
                "order": 47,
                "action_id": "regenerate_prompt_cache_key",
                "action_owner": "provider_extension",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                },
                "rich_ui": {
                    "kind": "button",
                    "placements": ["session_settings"],
                    "anchor_key": _PROMPT_CACHE_KEY,
                    "position": "after",
                },
            },
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        _ = config
        return state

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        _ = messages
        return native_messages

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        _ = native_messages
        return messages

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        config = state.get("config") if isinstance(state.get("config"), dict) else {}
        request = state.get("request") or {}
        payload = dict(request.get("payload", {}))
        changed = False
        chatgpt_mode = _effective_auth_mode(config) == "chatgpt"

        if self._prompt_cache_key_enabled(config):
            prompt_cache_key = self._normalized_prompt_cache_key(config)
            if prompt_cache_key is not None:
                if payload.get(_PROMPT_CACHE_KEY) != prompt_cache_key:
                    payload[_PROMPT_CACHE_KEY] = prompt_cache_key
                    changed = True
            else:
                if _PROMPT_CACHE_KEY in payload:
                    payload.pop(_PROMPT_CACHE_KEY, None)
                    changed = True
        else:
            if _PROMPT_CACHE_KEY in payload:
                payload.pop(_PROMPT_CACHE_KEY, None)
                changed = True

        if not chatgpt_mode and self._truthy(config.get(_RETENTION_24H_KEY)):
            if payload.get("prompt_cache_retention") != _RETENTION_VALUE:
                payload["prompt_cache_retention"] = _RETENTION_VALUE
                changed = True
        else:
            if "prompt_cache_retention" in payload:
                payload.pop("prompt_cache_retention", None)
                changed = True

        if not changed:
            return native_messages, state

        return native_messages, {**state, "request": {**request, "payload": payload}}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "ensure_prompt_cache_key",
                "label": "Ensure prompt cache key",
                "inputs": {},
                "trigger": ["session_create", "request_prepare"],
            },
            {
                "id": "regenerate_prompt_cache_key",
                "label": "Regenerate prompt cache key",
                "description": "Generate a fresh session-owned prompt cache key.",
                "inputs": {},
            },
        ]

    def execute_action(
        self,
        action_id: str,
        session: Session,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = params, context
        config = state.get("config") if isinstance(state.get("config"), dict) else {}

        if action_id == "ensure_prompt_cache_key":
            return self._ensure_prompt_cache_key(session, native_messages, config)

        if action_id == "regenerate_prompt_cache_key":
            next_key = self._generate_prompt_cache_key()
            return {
                "native_messages": native_messages,
                "session_metadata": self._session_metadata_with_overrides(
                    session,
                    {_PROMPT_CACHE_KEY: next_key},
                ),
                "message": "Regenerated prompt cache key",
            }

        raise ValueError(f"Unknown action_id {action_id!r}")

    def _ensure_prompt_cache_key(
        self,
        session: Session,
        native_messages: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not self._prompt_cache_key_enabled(config):
            return {"native_messages": native_messages}

        if self._current_session_prompt_cache_key(session) is not None:
            return {"native_messages": native_messages}

        next_key = self._generate_prompt_cache_key()
        return {
            "native_messages": native_messages,
            "session_metadata": self._session_metadata_with_overrides(
                session,
                {_PROMPT_CACHE_KEY: next_key},
            ),
        }

    def _session_metadata_with_overrides(
        self,
        session: Session,
        overrides_patch: Dict[str, Any],
    ) -> Dict[str, Any]:
        metadata = dict(session.metadata) if isinstance(session.metadata, dict) else {}
        current_overrides = metadata.get("overrides")
        normalized_overrides = current_overrides if isinstance(current_overrides, dict) else {}
        metadata["overrides"] = {**normalized_overrides, **overrides_patch}
        return metadata

    def _current_session_prompt_cache_key(self, session: Session) -> Optional[str]:
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        if not isinstance(overrides, dict):
            return None
        return self._normalized_prompt_cache_key(overrides)

    @staticmethod
    def _truthy(value: Any) -> bool:
        return value is True

    def _prompt_cache_key_enabled(self, config: Dict[str, Any]) -> bool:
        raw = config.get(_ENABLE_KEY)
        return raw is not False

    @staticmethod
    def _normalized_prompt_cache_key(config: Dict[str, Any]) -> Optional[str]:
        raw = config.get(_PROMPT_CACHE_KEY)
        if not isinstance(raw, str):
            return None
        cleaned = raw.strip()
        return cleaned or None

    @staticmethod
    def _generate_prompt_cache_key() -> str:
        return f"opcache_{uuid.uuid4().hex}"