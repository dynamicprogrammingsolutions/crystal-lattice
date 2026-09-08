"""Anthropic-compatible provider transport and native history."""

from __future__ import annotations

import os
import queue
from threading import Lock, Thread
from typing import Any, Iterator

from agent_core.types import ProviderPlugin, ProviderRequestCancelled
from agent_core.utils import get_logger
from anthropic import Anthropic

from .content_blocks import (
    object_to_dict,
    reduce_event,
    strip_runtime_fields,
)

logger = get_logger("anthropic_provider")

_STANDARD_MESSAGE_KEYS = {
    "cache_control",
    "container",
    "extra_body",
    "extra_headers",
    "extra_query",
    "inference_geo",
    "max_tokens",
    "messages",
    "metadata",
    "model",
    "output_config",
    "service_tier",
    "stop_sequences",
    "system",
    "thinking",
    "timeout",
    "tool_choice",
    "tools",
    "user_profile_id",
}
_BETA_MESSAGE_KEYS = {
    *_STANDARD_MESSAGE_KEYS,
    "context_management",
    "diagnostics",
    "fallback_credit_token",
    "fallbacks",
    "mcp_servers",
    "speed",
}
_RESERVED_REQUEST_OPTION_KEYS = {"messages", "stream", "system"}
_CONTEXT_MANAGEMENT_BETA = "context-management-2025-06-27"


def _effective_api_key(config: dict[str, Any]) -> str:
    value = config.get("api_key")
    if isinstance(value, str) and value:
        return value
    return os.environ.get("ANTHROPIC_API_KEY", "")


def _redacted_error(exc: Exception, api_key: str) -> str:
    message = str(exc)
    if api_key:
        message = message.replace(api_key, "<redacted>")
    return f"Anthropic request failed: {type(exc).__name__}: {message[:500]}"


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _dedupe_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _header_value(headers: Any, name: str) -> str | None:
    if not isinstance(headers, dict):
        return None
    lowered = name.lower()
    for key, value in headers.items():
        if isinstance(key, str) and key.lower() == lowered and isinstance(value, str):
            return value
    return None


def _split_beta_header(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "".join(
        str(block.get("text") or "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    )


def _merge_consecutive_messages(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        if role not in {"user", "assistant"}:
            continue
        content = strip_runtime_fields(message.get("content", ""))
        item = {"role": role, "content": content}
        if merged and merged[-1].get("role") == role:
            previous = merged[-1].get("content")
            previous_blocks = (
                list(previous)
                if isinstance(previous, list)
                else [{"type": "text", "text": str(previous or "")}]
            )
            new_blocks = (
                list(content)
                if isinstance(content, list)
                else [{"type": "text", "text": str(content or "")}]
            )
            merged[-1] = {"role": role, "content": [*previous_blocks, *new_blocks]}
        else:
            merged.append(item)
    return merged


class AnthropicProvider(ProviderPlugin):
    name = "anthropic"
    version = "0.1.0"

    def __init__(self) -> None:
        self._active: dict[str, tuple[Any, Any]] = {}
        self._cancelled: set[str] = set()
        self._lock = Lock()

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "auth_mode": {"type": "string", "default": "api"},
            "api_key": {"type": "string", "required": False},
            "base_url": {
                "type": "string",
                "default": "https://api.anthropic.com",
            },
            "model": {"type": "string", "required": True},
            "anthropic_version": {"type": "string", "default": "2023-06-01"},
            "timeout": {"type": "number", "default": 300},
            "max_retries": {"type": "integer", "default": 2},
            "max_tokens": {"type": "integer", "default": 4096},
            "headers": {"type": "object", "required": False},
            "betas": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
            },
            "beta_headers": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
            },
            "capabilities": {
                "type": "object",
                "default": {},
            },
        }

    def get_ui_elements(
        self,
        config: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        models = (context or {}).get("models")
        models = models if isinstance(models, list) else []
        options = [
            {"value": model["id"], "label": model.get("name") or model["id"]}
            for model in models
            if isinstance(model, dict)
            and isinstance(model.get("id"), str)
            and model["id"]
        ]
        model_ui = {
            "ui_type": "config",
            "type": "dropdown",
            "key": "model",
            "label": "Model",
            "icon": "cpu",
            "options": options,
            "placeholder": "Search models or enter a model ID",
            "custom_value": {
                "enabled": True,
                "pattern": r"^[^\s]+$",
                "option_label": "Use '{value}' as a custom model ID",
            },
            "rich_ui": {
                "kind": "dropdown",
                "label": "Model",
                "show_label": False,
                "options": options,
                "placeholder": "Search models or enter a model ID",
                "custom_value": {
                    "enabled": True,
                    "pattern": r"^[^\s]+$",
                    "option_label": "Use '{value}' as a custom model ID",
                },
                "placements": ["composer"],
                "default_pinned": True,
            },
        }
        return [
            model_ui,
            {"type": "text", "key": "base_url", "label": "Base URL"},
        ]

    def get_tags(
        self, config: dict[str, Any], models: list[dict[str, Any]]
    ) -> list[str]:
        tags = [
            "provider:anthropic",
            "supports_streaming",
            "supports_tools",
            "supports_reasoning",
            "supports_usage",
        ]
        capabilities = config.get("capabilities")
        capabilities = capabilities if isinstance(capabilities, dict) else {}
        if capabilities.get("prompt_caching") is True:
            tags.append("supports_prompt_caching")

        controls = capabilities.get("anthropic_reasoning_controls")
        if controls is True:
            tags.append("supports_anthropic_reasoning_controls")
        elif controls is not False:
            selected = config.get("model")
            if isinstance(selected, str) and any(
                model.get("id") == selected
                and isinstance(model.get("anthropic_reasoning_controls"), dict)
                and bool(model["anthropic_reasoning_controls"])
                for model in models
                if isinstance(model, dict)
            ):
                tags.append("supports_anthropic_reasoning_controls")
        return tags

    def _client(self, config: dict[str, Any]) -> Any:
        api_key = _effective_api_key(config)
        headers = config.get("headers")
        default_headers = dict(headers) if isinstance(headers, dict) else {}
        version = config.get("anthropic_version")
        if isinstance(version, str) and version:
            default_headers.setdefault("anthropic-version", version)
        return Anthropic(
            api_key=api_key or "missing",
            base_url=str(config.get("base_url") or "https://api.anthropic.com"),
            timeout=float(config.get("timeout") or 300),
            max_retries=max(0, int(config.get("max_retries") or 0)),
            default_headers=default_headers,
        )

    def get_models(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        client = self._client(config)
        try:
            page = client.models.list(limit=1000)
            models: list[dict[str, Any]] = []
            seen_ids: set[str] = set()
            for model in page:
                raw = object_to_dict(model)
                model_id = raw.get("id")
                if (
                    not isinstance(model_id, str)
                    or not model_id
                    or model_id in seen_ids
                ):
                    continue
                seen_ids.add(model_id)
                models.append(
                    {
                        "id": model_id,
                        "name": raw.get("display_name") or model_id,
                        "created_at": raw.get("created_at"),
                        "max_input_tokens": raw.get("max_input_tokens"),
                        "max_output_tokens": raw.get("max_tokens"),
                        "capabilities": raw.get("capabilities") or {},
                        "raw": raw,
                    }
                )
            return models
        except Exception as exc:
            logger.warning("anthropic model discovery failed", error=type(exc).__name__)
            return []
        finally:
            client.close()

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {
            "config": dict(config),
            "request": {},
            "accumulator": None,
            "anthropic_runtime": {
                "raw_usage": {},
                "completed": False,
            },
        }

    def to_native_messages(
        self,
        messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        native: list[dict[str, Any]] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = message.get("role", "user")
            metadata = dict(message.get("metadata") or {})
            item: dict[str, Any] = {
                "role": role,
                "content": message.get("content", ""),
            }
            if metadata:
                item["_metadata"] = metadata
            if "toolResult" in message:
                item["toolResult"] = message["toolResult"]
            native.append(item)
        return native

    def from_native_messages(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        for native in native_messages:
            if not isinstance(native, dict):
                continue
            metadata = dict(native.get("_metadata") or {})
            messages.append(
                {
                    "role": native.get("role", "assistant"),
                    "content": _content_text(native.get("content")),
                    "metadata": metadata,
                }
            )
        return messages

    def initialize_request(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        request_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        config = state.get("config") or {}
        system_parts = [
            _content_text(message.get("content"))
            for message in native_messages
            if isinstance(message, dict) and message.get("role") == "system"
        ]
        request_messages = _merge_consecutive_messages(
            [
                message
                for message in native_messages
                if isinstance(message, dict) and message.get("role") != "system"
            ]
        )
        payload: dict[str, Any] = {
            "model": config.get("model"),
            "max_tokens": int(config.get("max_tokens") or 4096),
            "messages": request_messages,
        }
        system = "\n\n".join(part for part in system_parts if part)
        if system:
            payload["system"] = system
        return list(native_messages), {
            **state,
            "request": {"payload": payload},
            "accumulator": None,
            "anthropic_runtime": {
                "raw_usage": {},
                "completed": False,
                "request_id": request_id,
                "protected_request_fields": {
                    "messages": request_messages,
                    **({"system": system} if system else {}),
                },
            },
        }

    def _request_payload(self, state: dict[str, Any]) -> dict[str, Any]:
        request = state.get("request") or {}
        payload = dict(request.get("payload") or {})
        runtime = state.get("anthropic_runtime") or {}
        protected = runtime.get("protected_request_fields") or {}
        if isinstance(protected, dict):
            payload["messages"] = protected.get("messages", [])
            if "system" in protected:
                payload["system"] = protected["system"]
            else:
                payload.pop("system", None)
        payload.pop("stream", None)
        return payload

    def _explicit_beta_header(
        self,
        config: dict[str, Any],
        payload: dict[str, Any],
    ) -> str | None:
        request_header = _header_value(payload.get("extra_headers"), "anthropic-beta")
        if request_header is not None:
            return request_header
        return _header_value(config.get("headers"), "anthropic-beta")

    def _configured_beta_ids(
        self,
        config: dict[str, Any],
        payload: dict[str, Any],
    ) -> list[str]:
        explicit = self._explicit_beta_header(config, payload)
        if explicit is not None:
            return _dedupe_strings(_split_beta_header(explicit))
        return _dedupe_strings(
            [
                *_string_list(config.get("betas")),
                *_string_list(config.get("beta_headers")),
            ]
        )

    def _uses_beta_api(
        self,
        config: dict[str, Any],
        payload: dict[str, Any],
    ) -> bool:
        return bool(_string_list(config.get("betas"))) or any(
            key in payload for key in _BETA_MESSAGE_KEYS - _STANDARD_MESSAGE_KEYS
        )

    def _request_kwargs(
        self,
        config: dict[str, Any],
        payload: dict[str, Any],
        *,
        stream: bool,
    ) -> tuple[dict[str, Any], bool]:
        beta_ids = self._configured_beta_ids(config, payload)
        if "context_management" in payload and _CONTEXT_MANAGEMENT_BETA not in beta_ids:
            raise RuntimeError(
                "Anthropic request option 'context_management' requires "
                f"provider beta {_CONTEXT_MANAGEMENT_BETA!r}"
            )

        use_beta = self._uses_beta_api(config, payload)
        supported_keys = _BETA_MESSAGE_KEYS if use_beta else _STANDARD_MESSAGE_KEYS
        explicit_extra_body = payload.get("extra_body")
        extra_body = (
            dict(explicit_extra_body) if isinstance(explicit_extra_body, dict) else {}
        )
        unknown_body: dict[str, Any] = {}
        kwargs: dict[str, Any] = {}
        for key, value in payload.items():
            if key in _RESERVED_REQUEST_OPTION_KEYS:
                if key != "stream":
                    kwargs[key] = value
                continue
            if key == "extra_body":
                continue
            if key in supported_keys:
                kwargs[key] = value
            else:
                unknown_body[key] = value
        if unknown_body or extra_body:
            kwargs["extra_body"] = {**unknown_body, **extra_body}
        kwargs["stream"] = stream

        if use_beta and self._explicit_beta_header(config, payload) is None:
            sdk_betas = _dedupe_strings(
                [
                    *_string_list(config.get("betas")),
                    *_string_list(config.get("beta_headers")),
                ]
            )
            if sdk_betas:
                kwargs["betas"] = sdk_betas
        elif not use_beta and self._explicit_beta_header(config, payload) is None:
            beta_headers = _dedupe_strings(_string_list(config.get("beta_headers")))
            if beta_headers:
                extra_headers = kwargs.get("extra_headers")
                merged_headers = (
                    dict(extra_headers) if isinstance(extra_headers, dict) else {}
                )
                merged_headers["anthropic-beta"] = ",".join(beta_headers)
                kwargs["extra_headers"] = merged_headers
        return kwargs, use_beta

    @staticmethod
    def _messages_resource(client: Any, use_beta: bool) -> Any:
        if not use_beta:
            return client.messages
        beta = getattr(client, "beta", None)
        messages = getattr(beta, "messages", None)
        if messages is None:
            raise RuntimeError("Anthropic SDK beta Messages API is unavailable")
        return messages

    def call_api(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        request_id: str | None = None,
    ):
        config = state.get("config") or {}
        api_key = _effective_api_key(config)
        payload = self._request_payload(state)
        client = None
        try:
            request_kwargs, use_beta = self._request_kwargs(
                config, payload, stream=False
            )
            client = self._client(config)
            response = self._messages_resource(client, use_beta).create(
                **request_kwargs
            )
            raw = object_to_dict(response)
            metadata = {
                "anthropic": {
                    key: raw.get(key)
                    for key in (
                        "id",
                        "model",
                        "stop_reason",
                        "stop_sequence",
                        "context_management",
                    )
                    if raw.get(key) is not None
                },
                "anthropic_usage": raw.get("usage") or {},
            }
            final = {
                "role": "assistant",
                "content": raw.get("content") or [],
                "_metadata": metadata,
            }
            return (
                [],
                [final],
                [*native_messages, final],
                {
                    **state,
                    "anthropic_runtime": {
                        **dict(state.get("anthropic_runtime") or {}),
                        "raw_usage": raw.get("usage") or {},
                        "completed": True,
                    },
                },
            )
        except Exception as exc:
            raise RuntimeError(_redacted_error(exc, api_key)) from exc
        finally:
            if client is not None:
                client.close()

    def stream_api(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        config = state.get("config") or {}
        api_key = _effective_api_key(config)
        payload = self._request_payload(state)
        stream = None
        client = None
        try:
            request_kwargs, use_beta = self._request_kwargs(
                config, payload, stream=True
            )
            client = self._client(config)
            stream = self._messages_resource(client, use_beta).create(**request_kwargs)
            if request_id:
                with self._lock:
                    self._active[request_id] = (stream, client)
            events: queue.Queue[tuple[str, Any]] = queue.Queue()

            def _read_stream() -> None:
                try:
                    for event in stream:
                        events.put(("event", event))
                except BaseException as exc:
                    events.put(("error", exc))
                finally:
                    events.put(("done", None))

            reader = Thread(
                target=_read_stream,
                name=f"anthropic-stream-{request_id or 'request'}",
                daemon=True,
            )
            reader.start()
            while True:
                if request_id and request_id in self._cancelled:
                    raise ProviderRequestCancelled(request_id)
                try:
                    kind, value = events.get(timeout=0.1)
                except queue.Empty:
                    continue
                if kind == "event":
                    yield object_to_dict(value)
                    continue
                if kind == "error":
                    if request_id and request_id in self._cancelled:
                        raise ProviderRequestCancelled(request_id) from value
                    if isinstance(value, BaseException):
                        raise value
                    raise RuntimeError("Anthropic stream failed")
                break
        except ProviderRequestCancelled:
            raise
        except Exception as exc:
            if request_id and request_id in self._cancelled:
                raise ProviderRequestCancelled(request_id) from exc
            raise RuntimeError(_redacted_error(exc, api_key)) from exc
        finally:
            if request_id:
                with self._lock:
                    self._active.pop(request_id, None)
                    self._cancelled.discard(request_id)
            close = getattr(stream, "close", None)
            if callable(close):
                close()
            if client is not None:
                client.close()

    def process_chunk(
        self,
        native_chunk: dict[str, Any],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ):
        partial, accumulator, completed = reduce_event(
            state.get("accumulator"), native_chunk
        )
        runtime = dict(state.get("anthropic_runtime") or {})
        usage = native_chunk.get("usage")
        if native_chunk.get("type") == "message_start":
            message = native_chunk.get("message")
            usage = message.get("usage") if isinstance(message, dict) else usage
        if isinstance(usage, dict):
            runtime["raw_usage"] = {**dict(runtime.get("raw_usage") or {}), **usage}
        runtime["completed"] = bool(runtime.get("completed")) or completed
        return (
            [partial] if isinstance(partial, dict) else [],
            [],
            list(native_messages),
            {
                **state,
                "accumulator": accumulator,
                "anthropic_runtime": runtime,
            },
        )

    def finalize(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ):
        accumulator = state.get("accumulator")
        runtime = dict(state.get("anthropic_runtime") or {})
        if not isinstance(accumulator, dict) or not runtime.get("completed"):
            return [], list(native_messages), {**state, "accumulator": None}
        metadata = dict(accumulator.get("_metadata") or {})
        metadata["anthropic_usage"] = dict(runtime.get("raw_usage") or {})
        final = {**accumulator, "_metadata": metadata}
        return [final], [*native_messages, final], {**state, "accumulator": None}

    def cancel_request(self, request_id: str) -> bool:
        with self._lock:
            active = self._active.get(request_id)
            if active is None:
                return False
            self._cancelled.add(request_id)
        stream, client = active
        for candidate in (stream, client):
            close = getattr(candidate, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
        return True
