"""OpenAI Responses flex processing extension.

Owns user-facing flex configuration, normalization, and request-state injection.
The provider remains responsible for applying transport-level SDK behavior.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


_ENABLE_FLEX_KEY = "enable_flex_processing"
_FLEX_TIMEOUT_KEY = "flex_timeout_seconds"
_ENABLE_FLEX_RETRIES_KEY = "enable_flex_retries"
_FLEX_MAX_RETRIES_KEY = "flex_max_retries"

_DEFAULT_FLEX_TIMEOUT_SECONDS = 300.0
_DEFAULT_FLEX_MAX_RETRIES = 2
_FLEX_STATE_KEY = "openai_responses_flex_processing"
_RAW_SERVICE_TIER_METADATA_KEY = "_openai_responses_service_tier"
_PUBLIC_SERVICE_TIER_KEY = "openai_service_tier"
_PUBLIC_FLEX_APPLIED_KEY = "flex_processing_applied"


class OpenAIResponsesFlexProcessingExtension(ProviderExtensionPlugin):
    name: str = "openai_responses_flex_processing"
    version: str = "0.1.0"
    priority: int = 54

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        _ = config, models
        return ["ext:openai_responses_flex_processing"]

    def required_tags(self) -> List[str]:
        return ["openai_responses"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            _ENABLE_FLEX_KEY: {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Enable OpenAI flex processing.",
            },
            _FLEX_TIMEOUT_KEY: {
                "type": "number",
                "required": False,
                "default": _DEFAULT_FLEX_TIMEOUT_SECONDS,
                "description": "Timeout to use for flex processing requests, in seconds.",
            },
            _ENABLE_FLEX_RETRIES_KEY: {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Enable automatic retries for flex processing requests.",
            },
            _FLEX_MAX_RETRIES_KEY: {
                "type": "integer",
                "required": False,
                "default": _DEFAULT_FLEX_MAX_RETRIES,
                "description": "Maximum retry count for flex processing requests.",
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
                "key": _ENABLE_FLEX_KEY,
                "label": "Enable flex processing",
            },
            {
                "type": "number",
                "key": _FLEX_TIMEOUT_KEY,
                "label": "Flex timeout (seconds)",
            },
            {
                "type": "checkbox",
                "key": _ENABLE_FLEX_RETRIES_KEY,
                "label": "Enable flex retries",
            },
            {
                "type": "number",
                "key": _FLEX_MAX_RETRIES_KEY,
                "label": "Flex max retries",
            },
        ]

    def init(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        normalized = self._normalized_flex_settings(config)
        if normalized is None:
            return state
        return {**state, _FLEX_STATE_KEY: normalized}

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

            metadata = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
            native_indices = metadata.get("native_indices") if isinstance(metadata, dict) else None
            if not isinstance(native_indices, list):
                out.append(message)
                continue

            service_tier = self._service_tier_from_native_indices(native_messages, native_indices)
            if not isinstance(service_tier, str) or not service_tier:
                out.append(message)
                continue

            out.append(
                {
                    **message,
                    "metadata": {
                        **metadata,
                        _PUBLIC_SERVICE_TIER_KEY: service_tier,
                        _PUBLIC_FLEX_APPLIED_KEY: service_tier == "flex",
                    },
                }
            )

        return out

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        flex_settings = state.get(_FLEX_STATE_KEY)
        if not isinstance(flex_settings, dict):
            return native_messages, state

        request = state.get("request")
        if not isinstance(request, dict):
            return native_messages, state

        payload = dict(request.get("payload") or {})
        payload["service_tier"] = "flex"

        next_request: Dict[str, Any] = {
            **request,
            "payload": payload,
            "timeout": flex_settings["timeout"],
        }

        max_retries = flex_settings.get("max_retries")
        if isinstance(max_retries, int):
            next_request["max_retries"] = max_retries
        else:
            next_request.pop("max_retries", None)

        return native_messages, {**state, "request": next_request}

    def _normalized_flex_settings(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if config.get(_ENABLE_FLEX_KEY) is not True:
            return None

        timeout = self._normalized_timeout(config.get(_FLEX_TIMEOUT_KEY))
        enable_retries = self._normalized_retry_enabled(config.get(_ENABLE_FLEX_RETRIES_KEY))

        settings: Dict[str, Any] = {"timeout": timeout}
        if enable_retries:
            settings["max_retries"] = self._normalized_max_retries(config.get(_FLEX_MAX_RETRIES_KEY))

        return settings

    @staticmethod
    def _normalized_timeout(raw: Any) -> float:
        try:
            timeout = float(raw)
        except (TypeError, ValueError):
            return _DEFAULT_FLEX_TIMEOUT_SECONDS
        if timeout <= 0:
            return _DEFAULT_FLEX_TIMEOUT_SECONDS
        return timeout

    @staticmethod
    def _normalized_retry_enabled(raw: Any) -> bool:
        if raw is False:
            return False
        return True

    @staticmethod
    def _normalized_max_retries(raw: Any) -> int:
        try:
            retries = int(raw)
        except (TypeError, ValueError):
            return _DEFAULT_FLEX_MAX_RETRIES
        if retries < 0:
            return _DEFAULT_FLEX_MAX_RETRIES
        return retries

    @staticmethod
    def _service_tier_from_native_indices(
        native_messages: List[Dict[str, Any]],
        native_indices: List[Any],
    ) -> Optional[str]:
        for index in native_indices:
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
