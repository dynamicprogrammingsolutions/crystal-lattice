"""OpenAI Responses Fast mode extension.

Owns Fast mode configuration and request-state injection. The current
service-tier name for Fast mode is ``fast``; the previous name
``priority`` is obsolete upstream and kept there only for compatibility.
The official API accepts ``fast``, but the ChatGPT backend
(``chatgpt.com/backend-api/codex``) rejects it with a 400 and only
accepts the legacy ``priority`` name, so the wire value is auth-mode
dependent: ``fast`` for API-key auth and ``priority`` for ChatGPT auth.
Responses may report either name (the official API still reports
``priority``), and both resolve the same fast-tier prices through the
pricing snapshot's tier normalization. Fast mode applies to both
API-key and ChatGPT auth modes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


_ENABLE_FAST_MODE_KEY = "enable_fast_mode"
_FAST_MODE_STATE_KEY = "openai_responses_fast_mode"
_RAW_SERVICE_TIER_METADATA_KEY = "_openai_responses_service_tier"
_PUBLIC_SERVICE_TIER_KEY = "openai_service_tier"
_PUBLIC_FAST_MODE_APPLIED_KEY = "fast_mode_applied"

# The ChatGPT backend only accepts the legacy ``priority`` tier name; the
# official API accepts the current ``fast`` name.
_CHATGPT_WIRE_SERVICE_TIER = "priority"
_API_WIRE_SERVICE_TIER = "fast"


class OpenAIResponsesFastModeExtension(ProviderExtensionPlugin):
    name: str = "openai_responses_fast_mode"
    version: str = "0.1.0"
    priority: int = 55

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        _ = config, models
        return ["ext:openai_responses_fast_mode"]

    def required_tags(self) -> List[str]:
        return ["openai_responses"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            _ENABLE_FAST_MODE_KEY: {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": (
                    "Applies the fast processing tier "
                    f'(``service_tier: "{_API_WIRE_SERVICE_TIER}"``, or the '
                    f'legacy ``"{_CHATGPT_WIRE_SERVICE_TIER}"`` name required '
                    "by the ChatGPT backend) to Responses calls for both "
                    "API-key and ChatGPT auth modes."
                ),
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = tags, models
        return [
            {
                "type": "checkbox",
                "key": _ENABLE_FAST_MODE_KEY,
                "label": "Enable Fast mode",
                "description": (
                    "Applies the fast processing tier "
                    f'(``service_tier: "{_API_WIRE_SERVICE_TIER}"``, or the '
                    f'legacy ``"{_CHATGPT_WIRE_SERVICE_TIER}"`` name required '
                    "by the ChatGPT backend) to Responses calls for both "
                    "API-key and ChatGPT auth modes."
                ),
            },
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if config.get(_ENABLE_FAST_MODE_KEY) is not True:
            return state
        return {**state, _FAST_MODE_STATE_KEY: {"enabled": True}}

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
        out: List[Dict[str, Any]] = []

        for message in messages:
            if not isinstance(message, dict) or message.get("role") != "assistant":
                out.append(message)
                continue

            metadata = (
                message.get("metadata")
                if isinstance(message.get("metadata"), dict)
                else {}
            )
            native_indices = (
                metadata.get("native_indices") if isinstance(metadata, dict) else None
            )
            if not isinstance(native_indices, list):
                out.append(message)
                continue

            service_tier = self._service_tier_from_native_indices(
                native_messages, native_indices
            )
            if not isinstance(service_tier, str) or not service_tier:
                out.append(message)
                continue

            out.append(
                {
                    **message,
                    "metadata": {
                        **metadata,
                        _PUBLIC_SERVICE_TIER_KEY: service_tier,
                        # ``priority`` is the obsolete name for the same tier;
                        # backends may still report it during the transition.
                        _PUBLIC_FAST_MODE_APPLIED_KEY: service_tier
                        in (_API_WIRE_SERVICE_TIER, _CHATGPT_WIRE_SERVICE_TIER),
                    },
                }
            )

        return out

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        fast_settings = state.get(_FAST_MODE_STATE_KEY)
        if not isinstance(fast_settings, dict):
            return native_messages, state

        request = state.get("request")
        if not isinstance(request, dict):
            return native_messages, state

        payload = dict(request.get("payload") or {})
        payload["service_tier"] = self._wire_service_tier_for_state(state)
        return native_messages, {**state, "request": {**request, "payload": payload}}

    @staticmethod
    def _effective_auth_mode(state: Dict[str, Any]) -> str:
        config = state.get("config") if isinstance(state, dict) else None
        if not isinstance(config, dict):
            return "api"
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

    def _wire_service_tier_for_state(self, state: Dict[str, Any]) -> str:
        if self._effective_auth_mode(state) == "chatgpt":
            return _CHATGPT_WIRE_SERVICE_TIER
        return _API_WIRE_SERVICE_TIER

    def _service_tier_from_native_indices(
        self,
        native_messages: List[Dict[str, Any]],
        native_indices: List[Any],
    ) -> Optional[str]:
        for index in reversed(native_indices):
            if not isinstance(index, int) or not (0 <= index < len(native_messages)):
                continue
            item = native_messages[index]
            if not isinstance(item, dict):
                continue
            internal = item.get("_metadata")
            if not isinstance(internal, dict):
                continue
            service_tier = internal.get(_RAW_SERVICE_TIER_METADATA_KEY)
            if isinstance(service_tier, str) and service_tier:
                return service_tier
        return None
