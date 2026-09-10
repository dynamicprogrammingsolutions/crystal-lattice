from __future__ import annotations

import json
import queue
import threading
import time
from typing import Any, Iterator
from dataclasses import dataclass, field

import requests

from agent_core.tool_result_payloads import (
    TOOL_RESULT_FIELD,
    make_text_tool_result,
    openai_chat_tool_result_content,
    provider_native_tool_result_display,
)
from agent_core.types import ProviderPlugin, ProviderRequestCancelled
from agent_core.utils import get_logger
from reference_openai_compatible_provider.attachment_parts import (
    image_content_to_image_url_part,
)
from reference_openai_compatible_provider.attachment_policy import (
    allow_image_attachment_base64,
    allow_image_attachment_url,
)

log = get_logger("reference_openai_compatible_provider")

_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_MODELS_TIMEOUT_CAP_SECONDS = 10.0
_DEFAULT_MIN_REQUEST_INTERVAL_SECONDS = 0.0
_STREAM_RECOVERY_MODES = ("disabled", "early_only", "aggressive")
_DEFAULT_STREAM_RECOVERY_MODE = "early_only"
_DEFAULT_STREAM_RECOVERY_MAX_RETRIES = 3

_request_pacing_lock = threading.Lock()
_next_request_time_by_scope: dict[str, float] = {}


@dataclass
class _InflightRequest:
    cancelled: threading.Event = field(default_factory=threading.Event)
    done: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)
    closers: list[Any] = field(default_factory=list)

    def add_closer(self, closer: Any) -> None:
        if not callable(closer):
            return
        with self.lock:
            self.closers.append(closer)
            already_cancelled = self.cancelled.is_set()
        if already_cancelled:
            try:
                closer()
            except Exception:
                pass

    def cancel(self) -> None:
        self.cancelled.set()
        with self.lock:
            closers = list(self.closers)
        for closer in closers:
            try:
                closer()
            except Exception:
                continue


def _parse_non_negative_float(value: Any, *, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return max(float(value), 0.0)
    if isinstance(value, str):
        try:
            return max(float(value.strip()), 0.0)
        except ValueError:
            return default
    return default


def _parse_retry_delays(value: Any) -> tuple[float, ...]:
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        return tuple(
            parsed
            for parsed in (
                _parse_non_negative_float(part, default=-1.0) for part in parts if part
            )
            if parsed >= 0.0
        )
    if isinstance(value, (list, tuple)):
        out: list[float] = []
        for item in value:
            parsed = _parse_non_negative_float(item, default=-1.0)
            if parsed >= 0.0:
                out.append(parsed)
        return tuple(out)
    return ()


def _parse_retry_after_seconds(value: Any) -> float | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = float(value.strip())
    except ValueError:
        return None
    return parsed if parsed >= 0.0 else None


def _parse_retry_on_status(value: Any) -> dict[int, tuple[float, ...]]:
    if not isinstance(value, dict):
        return {}
    result: dict[int, tuple[float, ...]] = {}
    for key, delays in value.items():
        try:
            status_code = int(key)
        except (ValueError, TypeError):
            continue
        parsed = _parse_retry_delays(delays)
        if parsed:
            result[status_code] = parsed
    return result


def _parse_stream_recovery(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"mode": "disabled", "max_retries": 0}
    mode = value.get("mode")
    if not isinstance(mode, str):
        return {"mode": "disabled", "max_retries": 0}
    normalized = mode.strip().lower()
    if normalized not in _STREAM_RECOVERY_MODES:
        return {"mode": "disabled", "max_retries": 0}
    if normalized == "disabled":
        return {"mode": "disabled", "max_retries": 0}
    max_retries = value.get("max_retries")
    try:
        max_retries = int(max_retries)
    except (TypeError, ValueError):
        max_retries = _DEFAULT_STREAM_RECOVERY_MAX_RETRIES
    if max_retries < 0:
        max_retries = _DEFAULT_STREAM_RECOVERY_MAX_RETRIES
    return {"mode": normalized, "max_retries": max_retries}


def _rate_limit_policy_from_config(config: dict[str, Any]) -> dict[str, Any]:
    base_url = str(config.get("base_url") or _DEFAULT_BASE_URL).rstrip("/")
    return {
        "scope_key": base_url,
        "min_request_interval_seconds": _parse_non_negative_float(
            config.get("min_request_interval_seconds"),
            default=_DEFAULT_MIN_REQUEST_INTERVAL_SECONDS,
        ),
        "retry_delays_seconds": _parse_retry_delays(
            config.get("rate_limit_retry_delays_seconds")
        ),
        "respect_retry_after_header": bool(
            config.get("respect_retry_after_header", True)
        ),
        "retry_on_status": _parse_retry_on_status(config.get("retry_on_status")),
        "retry_on_timeout": _parse_retry_delays(config.get("retry_on_timeout")),
        "stream_recovery": _parse_stream_recovery(config.get("stream_recovery")),
    }


def _wait_for_request_slot(
    *,
    scope_key: str,
    min_request_interval_seconds: float,
    delay_seconds: float,
) -> None:
    now = time.monotonic()
    with _request_pacing_lock:
        next_allowed = _next_request_time_by_scope.get(scope_key, 0.0)
        target = max(next_allowed, now + max(delay_seconds, 0.0))
        _next_request_time_by_scope[scope_key] = target + max(
            min_request_interval_seconds, 0.0
        )

    wait_seconds = target - now
    if wait_seconds > 0.0:
        time.sleep(wait_seconds)


def _retry_delay_for_429(
    response: Any,
    *,
    retry_delays_seconds: tuple[float, ...],
    attempt_index: int,
    respect_retry_after_header: bool,
) -> float | None:
    if attempt_index >= len(retry_delays_seconds):
        return None

    delay_seconds = retry_delays_seconds[attempt_index]
    if not respect_retry_after_header:
        return delay_seconds

    headers = getattr(response, "headers", None)
    retry_after = headers.get("Retry-After") if isinstance(headers, dict) else None
    retry_after_seconds = _parse_retry_after_seconds(retry_after)
    if retry_after_seconds is None:
        return delay_seconds
    return max(delay_seconds, retry_after_seconds)


def _retry_delay_for_status(
    status_code: int,
    attempt_index: int,
    retry_on_status: dict[int, tuple[float, ...]],
) -> float | None:
    delays = retry_on_status.get(status_code)
    if delays is None or attempt_index >= len(delays):
        return None
    return delays[attempt_index]


def _request_with_rate_limit_retry(
    *,
    request_fn,
    rate_limit_policy: dict[str, Any],
    action: str,
):
    retry_delay_seconds = 0.0
    attempt_index = 0

    while True:
        _wait_for_request_slot(
            scope_key=str(rate_limit_policy.get("scope_key") or _DEFAULT_BASE_URL),
            min_request_interval_seconds=_parse_non_negative_float(
                rate_limit_policy.get("min_request_interval_seconds"),
                default=_DEFAULT_MIN_REQUEST_INTERVAL_SECONDS,
            ),
            delay_seconds=retry_delay_seconds,
        )
        try:
            response = request_fn()
        except requests.exceptions.Timeout as exc:
            retry_on_timeout: tuple[float, ...] = (
                rate_limit_policy.get("retry_on_timeout") or ()
            )
            if attempt_index < len(retry_on_timeout):
                retry_delay_seconds = retry_on_timeout[attempt_index]
                log.warning(
                    "timeout_retrying",
                    action=action,
                    retry_delay_seconds=retry_delay_seconds,
                    attempt=attempt_index + 1,
                    error=str(exc)[:500],
                )
                attempt_index += 1
                continue
            raise

        status_code = getattr(response, "status_code", None)

        # --- 429: rate-limit retry (with Retry-After support) ---
        if status_code == 429:
            retry_delay_seconds = _retry_delay_for_429(
                response,
                retry_delays_seconds=tuple(
                    rate_limit_policy.get("retry_delays_seconds") or ()
                ),
                attempt_index=attempt_index,
                respect_retry_after_header=bool(
                    rate_limit_policy.get("respect_retry_after_header", True)
                ),
            )
            if retry_delay_seconds is None:
                return response

            log.warning(
                "rate_limited_retrying",
                action=action,
                status_code=429,
                retry_delay_seconds=retry_delay_seconds,
                attempt=attempt_index + 1,
            )
            if hasattr(response, "close"):
                response.close()
            attempt_index += 1
            continue

        # --- Configured status codes (e.g. 500, 502, 503) ---
        retry_on_status: dict[int, tuple[float, ...]] = (
            rate_limit_policy.get("retry_on_status") or {}
        )
        if isinstance(status_code, int) and status_code in retry_on_status:
            retry_delay_seconds = _retry_delay_for_status(
                status_code,
                attempt_index,
                retry_on_status,
            )
            if retry_delay_seconds is not None:
                log.warning(
                    "status_retrying",
                    action=action,
                    status_code=status_code,
                    retry_delay_seconds=retry_delay_seconds,
                    attempt=attempt_index + 1,
                )
                if hasattr(response, "close"):
                    response.close()
                attempt_index += 1
                continue

        return response


def _chunk_has_content(chunk: dict[str, Any]) -> bool:
    """Check whether a streaming chunk carries visible content."""
    choice0 = chunk.get("choices")
    if isinstance(choice0, list) and choice0:
        delta = choice0[0].get("delta") if isinstance(choice0[0], dict) else None
        if isinstance(delta, dict):
            content = delta.get("content")
            if isinstance(content, str) and content:
                return True
    return False


class AccumulatorStreamingMixin:
    """Generic streaming hot path using extract_delta + process_delta.

    This follows the accumulator pattern described in `plugins/docs/provider-plugins.md`.
    """

    def extract_delta(
        self, chunk: dict[str, Any]
    ) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def process_delta(
        self,
        delta: dict[str, Any],
        accumulated: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError

    def process_chunk(
        self,
        native_chunk: dict[str, Any],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ):
        delta = self.extract_delta(native_chunk or {})
        accumulated = (
            state.get("accumulator")
            if isinstance(state.get("accumulator"), dict)
            else {}
        )
        patch, new_acc = self.process_delta(delta, accumulated)

        partials: list[dict[str, Any]] = []
        if isinstance(patch, dict) and patch:
            partials = [patch]

        return partials, [], list(native_messages), {**state, "accumulator": new_acc}

    def finalize(self, native_messages: list[dict[str, Any]], state: dict[str, Any]):
        final = state.get("accumulator")
        if isinstance(final, dict) and final:
            return [final], [*native_messages, final], state
        return [], list(native_messages), state


class OpenAICompatibleProvider(AccumulatorStreamingMixin, ProviderPlugin):
    """OpenAI-compatible chat-completions provider.

    Designed to work with OpenAI-like endpoints, including Ollama's OpenAI-compatible API.
    """

    name = "reference_openai_compatible"
    version = "0.2.0"

    def __init__(self) -> None:
        self._inflight_lock = threading.Lock()
        self._inflight_requests: dict[str, _InflightRequest] = {}

    def _register_inflight(self, request_id: str | None) -> _InflightRequest:
        runtime = _InflightRequest()
        if isinstance(request_id, str) and request_id:
            with self._inflight_lock:
                self._inflight_requests[request_id] = runtime
        return runtime

    def _clear_inflight(
        self, request_id: str | None, runtime: _InflightRequest
    ) -> None:
        runtime.done.set()
        if isinstance(request_id, str) and request_id:
            with self._inflight_lock:
                current = self._inflight_requests.get(request_id)
                if current is runtime:
                    self._inflight_requests.pop(request_id, None)

    def cancel_request(self, request_id: str) -> bool:
        if not isinstance(request_id, str) or not request_id:
            return False
        with self._inflight_lock:
            runtime = self._inflight_requests.get(request_id)
        if runtime is None:
            return False
        runtime.cancel()
        return True

    def _native_internal_from_core_metadata(self, metadata: Any) -> dict[str, Any]:
        if not isinstance(metadata, dict):
            return {}
        out = dict(metadata)
        out.pop("native_indices", None)
        out.pop("tool_calls", None)
        out.pop("tool_call_id", None)
        out.pop("display", None)
        return out

    def _core_metadata_from_native_internal(self, internal: Any) -> dict[str, Any]:
        if not isinstance(internal, dict):
            return {}
        return {
            key: value
            for key, value in internal.items()
            if key not in {"native_indices", "tool_calls", "tool_call_id"}
        }

    def _request_context(self, state: dict[str, Any]) -> dict[str, Any] | None:
        value = state.get("_request_context")
        return value if isinstance(value, dict) else None

    def _session_asset_store(
        self,
        state: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        resolved_context = (
            context if isinstance(context, dict) else self._request_context(state)
        )
        store = (
            resolved_context.get("session_asset_store")
            if isinstance(resolved_context, dict)
            else None
        )
        if store is None:
            raise RuntimeError(
                "[reference_openai_compatible_provider] session asset attachment requires session_asset_store in context"
            )
        return store

    def _resolve_session_asset(
        self,
        state: dict[str, Any],
        context: dict[str, Any] | None,
        asset_ref: dict[str, Any],
        expected_attachment_type: str,
    ) -> tuple[str, str, bytes]:
        store = self._session_asset_store(state, context)
        session_id = asset_ref.get("session_id")
        asset_id = asset_ref.get("asset_id")
        if not isinstance(session_id, str) or not isinstance(asset_id, str):
            raise ValueError(
                "[reference_openai_compatible_provider] invalid session asset reference"
            )
        record = store.load(session_id, asset_id)
        if record.attachment_type != expected_attachment_type:
            raise ValueError(
                f"[reference_openai_compatible_provider] session asset {asset_id!r} is not a {expected_attachment_type} attachment"
            )
        return record.filename, record.mime_type, store.load_bytes(session_id, asset_id)

    def _expanded_tool_content(
        self,
        content: Any,
        state: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> Any:
        if not isinstance(content, list):
            return content

        parts: list[dict[str, Any]] = []
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") != "image_url":
                parts.append(dict(part))
                continue

            image_url = part.get("image_url")
            if isinstance(image_url, dict) and image_url.get("asset_ref"):
                expanded = image_content_to_image_url_part(
                    image_url,
                    resolve_session_asset=lambda asset_ref, expected_attachment_type: self._resolve_session_asset(
                        state,
                        context,
                        asset_ref,
                        expected_attachment_type,
                    ),
                    allow_base64=allow_image_attachment_base64(state),
                    allow_url=allow_image_attachment_url(state),
                )
                parts.append(expanded)
                continue

            parts.append(dict(part))

        return parts

    def _expanded_request_messages(
        self,
        messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        context = self._request_context(state)
        return [
            (
                {
                    **msg,
                    "content": self._expanded_tool_content(
                        msg.get("content"),
                        state,
                        context,
                    ),
                }
                if msg.get("role") == "tool"
                else msg
            )
            for msg in messages
        ]

    def to_native_messages(
        self,
        messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        native: list[dict[str, Any]] = []

        for msg in messages:
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", "user")
            raw_content = msg.get("content", "")
            tool_result = msg.get(TOOL_RESULT_FIELD)
            raw_metadata = msg.get("metadata")
            metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
            native_tool_content = (
                openai_chat_tool_result_content(tool_result) if role == "tool" else None
            )
            content = raw_content
            if not isinstance(content, str):
                content = ""

            native_message: dict[str, Any] = {
                "role": role,
                "content": (
                    native_tool_content if native_tool_content is not None else content
                ),
            }

            tool_calls = metadata.get("tool_calls")
            if role == "assistant" and isinstance(tool_calls, list) and tool_calls:
                native_message["tool_calls"] = tool_calls

            tool_call_id = metadata.get("tool_call_id")
            if role == "tool" and isinstance(tool_call_id, str) and tool_call_id:
                native_message["tool_call_id"] = tool_call_id

            internal_metadata = self._native_internal_from_core_metadata(metadata)
            if internal_metadata:
                native_message["_metadata"] = internal_metadata

            if native_tool_content is not None:
                native.append(native_message)
                continue

            multipart = msg.get("multipartContent")
            if not isinstance(multipart, list) or not multipart:
                native.append(native_message)
                continue

            parts: list[dict[str, Any]] = [{"type": "text", "text": content}]
            for part in multipart:
                if not isinstance(part, dict):
                    continue

                part_type = part.get("type")
                part_content = part.get("content")
                if part_type != "image":
                    continue

                parts.append(
                    image_content_to_image_url_part(
                        part_content,
                        resolve_session_asset=lambda asset_ref, expected_attachment_type: self._resolve_session_asset(
                            state,
                            context,
                            asset_ref,
                            expected_attachment_type,
                        ),
                        allow_base64=allow_image_attachment_base64(state),
                        allow_url=allow_image_attachment_url(state),
                    )
                )

            native.append({**native_message, "content": parts})

        return native

    def from_native_messages(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for native_idx, native_message in enumerate(native_messages):
            if not isinstance(native_message, dict):
                continue
            if not ("role" in native_message or "content" in native_message):
                continue

            role = native_message.get("role", "assistant")
            content = native_message.get("content", "")
            metadata = self._core_metadata_from_native_internal(
                native_message.get("_metadata")
            )

            msg: dict[str, Any] = {"role": role, "content": ""}
            multipart_out: list[dict[str, Any]] = []

            if isinstance(content, list):
                text_parts: list[str] = []
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    part_type = part.get("type")
                    if part_type == "text":
                        text = part.get("text")
                        if isinstance(text, str) and text:
                            text_parts.append(text)
                        continue
                    if part_type == "image_url":
                        image_url = part.get("image_url")
                        if isinstance(image_url, dict):
                            url = image_url.get("url")
                            if isinstance(url, str) and url:
                                multipart_out.append(
                                    {
                                        "type": "image",
                                        "content": {"url": url},
                                        "metadata": {},
                                    }
                                )
                        continue

                msg["content"] = "\n".join(text_parts)
                if role == "tool":
                    tool_result = {
                        "type": "provider_native_tool_result",
                        "format": "openai.chat_completions",
                        "content": [
                            dict(part) for part in content if isinstance(part, dict)
                        ],
                        "text": msg["content"],
                    }
                    msg[TOOL_RESULT_FIELD] = tool_result
                    tool_name = metadata.get("tool_name")
                    display = provider_native_tool_result_display(
                        tool_result,
                        tool_name=tool_name if isinstance(tool_name, str) else None,
                    )
                    if isinstance(display, dict):
                        metadata["display"] = display
                elif multipart_out:
                    msg["multipartContent"] = multipart_out
            else:
                msg["content"] = content if isinstance(content, str) else ""

            if role == "tool" and TOOL_RESULT_FIELD not in msg:
                msg[TOOL_RESULT_FIELD] = make_text_tool_result(
                    text=msg["content"] if isinstance(msg.get("content"), str) else ""
                )

            tool_calls = native_message.get("tool_calls")
            if isinstance(tool_calls, list) and tool_calls:
                metadata["tool_calls"] = tool_calls

            tool_call_id = native_message.get("tool_call_id")
            if isinstance(tool_call_id, str) and tool_call_id:
                metadata["tool_call_id"] = tool_call_id

            metadata["native_indices"] = [native_idx]
            normalized.append({**msg, "metadata": metadata})

        return normalized

    @staticmethod
    def _endpoint_options_from_config(config: dict[str, Any]) -> list[dict[str, str]]:
        raw_options = config.get("endpoint_options")
        if not isinstance(raw_options, dict):
            return []

        options: list[dict[str, str]] = []
        for label, value in raw_options.items():
            if not isinstance(label, str) or not label:
                continue
            if not isinstance(value, str) or not value:
                continue
            options.append({"value": value, "label": label})
        return options

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "base_url": {
                "type": "string",
                "required": False,
                "default": "https://api.openai.com/v1",
                "description": "OpenAI-compatible base URL (no trailing slash required)",
            },
            "endpoint_options": {
                "type": "object",
                "required": False,
                "default": {},
                "description": "Optional labeled base URL choices for rendering an endpoint selector bound to base_url",
            },
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": False},
            "timeout": {"type": "number", "default": 60},
            "debug_stream": {"type": "boolean", "default": False},
            "min_request_interval_seconds": {
                "type": "number",
                "default": 0,
                "description": "Minimum spacing between requests sent to the same base URL",
            },
            "rate_limit_retry_delays_seconds": {
                "type": "string",
                "default": "",
                "description": "Comma-separated retry delays used after HTTP 429 responses",
            },
            "respect_retry_after_header": {
                "type": "boolean",
                "default": True,
                "description": "Honor Retry-After when retrying HTTP 429 responses",
            },
            "reasoning_field": {
                "type": "string",
                "required": False,
                "default": "",
                "description": "Provider-specific field name for reasoning content (e.g., 'reasoning', 'reasoning_content'). If set, only this field is used for reasoning. If empty, all supported reasoning fields are used.",
            },
        }

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"config": config}

    def get_models(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        base_url = str(config.get("base_url") or _DEFAULT_BASE_URL).rstrip("/")
        rate_limit_policy = _rate_limit_policy_from_config(config)

        url = f"{base_url}/models"

        headers: dict[str, str] = {}
        api_key = config.get("api_key")
        if isinstance(api_key, str) and api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        timeout = min(float(config.get("timeout", 60)), _MODELS_TIMEOUT_CAP_SECONDS)

        try:
            resp = _request_with_rate_limit_retry(
                request_fn=lambda: requests.get(url, headers=headers, timeout=timeout),
                rate_limit_policy=rate_limit_policy,
                action="get_models",
            )
        except Exception as exc:
            log.warning("models_request_failed", url=url, error=str(exc))
            return []

        if not resp.ok:
            log.warning(
                "models_request_not_ok",
                url=url,
                status_code=resp.status_code,
                body=str(resp.text)[:2000],
            )
            return []

        try:
            payload = resp.json()
        except Exception as exc:
            log.warning("models_parse_failed", url=url, error=str(exc))
            return []

        items = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return []

        out: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            model_id = item.get("id")
            if not isinstance(model_id, str) or not model_id:
                continue
            entry: dict[str, Any] = {"id": model_id}
            name = item.get("name")
            if isinstance(name, str) and name:
                entry["name"] = name
            out.append(entry)
        return out

    def get_ui_elements(
        self,
        config: dict[str, Any],
        tags: list[str],
        models: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        elements: list[dict[str, Any]] = []

        endpoint_options = self._endpoint_options_from_config(config)
        if endpoint_options:
            elements.append(
                {
                    "ui_type": "config",
                    "type": "select",
                    "key": "base_url",
                    "label": "Endpoint",
                    "options": endpoint_options,
                }
            )

        options: list[dict[str, str]] = []
        for m in models:
            model_id = m.get("id")
            if not isinstance(model_id, str) or not model_id:
                continue
            label = m.get("name")
            label = label if isinstance(label, str) and label else model_id
            options.append({"value": model_id, "label": label})

        model_el: dict[str, Any] = {
            "ui_type": "config",
            "type": "dropdown",
            "key": "model",
            "label": "Model",
            "icon": "cpu",
            "options": options,
            "placeholder": "Search models or enter a model ID",
            "custom_value": {
                "enabled": True,
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
                    "option_label": "Use '{value}' as a custom model ID",
                },
                "placements": ["composer"],
                "default_pinned": True,
            },
        }

        elements.append(model_el)
        return elements

    def get_tags(self, config: dict[str, Any], models: list[dict[str, Any]]):
        return [
            "provider:openai_compatible",
            "supports_streaming",
            "supports_tools",
        ]

    def initialize_request(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        _ = request_id
        cfg = state.get("config") or {}
        base_url = str(cfg.get("base_url") or _DEFAULT_BASE_URL).rstrip("/")
        url = f"{base_url}/chat/completions"

        headers: dict[str, str] = {"Content-Type": "application/json"}
        api_key = cfg.get("api_key")
        if isinstance(api_key, str) and api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        request: dict[str, Any] = {
            "url": url,
            "payload": {"model": cfg.get("model")},
            "headers": headers,
            "timeout": float(cfg.get("timeout", 60)),
        }
        request["messages"] = list(native_messages)
        return list(native_messages), {
            **state,
            "request": request,
            "rate_limit_policy": _rate_limit_policy_from_config(cfg),
            "accumulator": None,
            "debug_stream": bool(cfg.get("debug_stream", False)),
        }

    def call_api(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        request_id: str | None = None,
    ):
        request = state.get("request") or {}
        rate_limit_policy = state.get("rate_limit_policy") or {}
        payload = dict(request.get("payload") or {})
        override = request.get("messages")
        base_history = override if isinstance(override, list) else native_messages
        base_history = self._expanded_request_messages(
            [m for m in base_history if isinstance(m, dict)],
            state,
        )
        messages_to_send = [
            {k: v for k, v in m.items() if k != "_metadata"}
            for m in base_history
            if isinstance(m, dict)
        ]
        payload |= {"messages": messages_to_send, "stream": False}
        runtime = self._register_inflight(request_id)
        results: queue.Queue[tuple[str, Any]] = queue.Queue()

        def _worker() -> None:
            session = requests.Session()
            response: requests.Response | None = None
            runtime.add_closer(session.close)
            try:
                if runtime.cancelled.is_set():
                    raise ProviderRequestCancelled(request_id)
                response = _request_with_rate_limit_retry(
                    request_fn=lambda: session.post(
                        str(request.get("url")),
                        headers=dict(request.get("headers") or {}),
                        json=payload,
                        timeout=float(request.get("timeout", 60)),
                        stream=True,
                    ),
                    rate_limit_policy=rate_limit_policy,
                    action="call_api",
                )
                runtime.add_closer(response.close)
                response.encoding = "utf-8"
                if not response.ok:
                    raise RuntimeError(
                        f"OpenAI-compatible call failed: {response.status_code} {response.text[:2000]}"
                    )
                results.put(("result", response.json()))
            except Exception as exc:
                results.put(("error", exc))
            finally:
                try:
                    if response is not None:
                        response.close()
                finally:
                    session.close()
                    runtime.done.set()

        worker = threading.Thread(target=_worker, daemon=True)
        worker.start()

        try:
            while True:
                try:
                    kind, value = results.get(timeout=0.1)
                except queue.Empty:
                    if runtime.cancelled.is_set():
                        raise ProviderRequestCancelled(request_id)
                    if runtime.done.is_set() and results.empty():
                        raise RuntimeError(
                            "OpenAI-compatible call failed: request ended without result"
                        )
                    continue
                if kind == "result":
                    raw = value
                    break
                exc = value
                if runtime.cancelled.is_set():
                    raise ProviderRequestCancelled(request_id) from exc
                if isinstance(exc, ProviderRequestCancelled):
                    raise exc
                if isinstance(exc, requests.RequestException):
                    raise RuntimeError(f"OpenAI-compatible call failed: {exc}") from exc
                raise RuntimeError(f"OpenAI-compatible call failed: {exc}") from exc
        finally:
            self._clear_inflight(request_id, runtime)
            worker.join(timeout=1.0)

        choice0 = (raw.get("choices") or [{}])[0]
        msg = choice0.get("message") if isinstance(choice0, dict) else None
        msg = msg if isinstance(msg, dict) else {"role": "assistant", "content": ""}

        msg = {"role": msg.get("role", "assistant"), **msg}
        usage = raw.get("usage") if isinstance(raw, dict) else None
        if isinstance(usage, dict):
            internal_md = msg.get("_metadata")
            base_internal_md = internal_md if isinstance(internal_md, dict) else {}
            msg = {**msg, "_metadata": {**base_internal_md, "usage": usage}}
        return [], [msg], [*native_messages, msg], state

    def stream_api(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        request = state.get("request") or {}
        rate_limit_policy = state.get("rate_limit_policy") or {}
        stream_recovery: dict[str, Any] = rate_limit_policy.get("stream_recovery") or {}
        payload = dict(request.get("payload") or {})
        override = request.get("messages")
        base_history = override if isinstance(override, list) else native_messages
        base_history = self._expanded_request_messages(
            [m for m in base_history if isinstance(m, dict)],
            state,
        )
        messages_to_send = [
            {k: v for k, v in m.items() if k != "_metadata"}
            for m in base_history
            if isinstance(m, dict)
        ]
        payload |= {"messages": messages_to_send, "stream": True}

        get_logger("openai-compatible-provider").debug(
            "sendig openai request",
            payload={
                **payload,
                "messages": "<redacted>" if payload.get("messages") else None,
                "tools": "<redacted>" if payload.get("tools") else None,
            },
        )

        recovery_mode = stream_recovery.get("mode", "disabled")
        recovery_max_retries = stream_recovery.get("max_retries", 0)
        runtime = self._register_inflight(request_id)
        results: queue.Queue[tuple[str, Any]] = queue.Queue()

        def _worker() -> None:
            session = requests.Session()
            runtime.add_closer(session.close)
            recovery_attempts = 0
            try:
                while True:
                    if runtime.cancelled.is_set():
                        raise ProviderRequestCancelled(request_id)
                    response = _request_with_rate_limit_retry(
                        request_fn=lambda: session.post(
                            str(request.get("url")),
                            headers=dict(request.get("headers") or {}),
                            json=payload,
                            timeout=float(request.get("timeout", 60)),
                            stream=True,
                        ),
                        rate_limit_policy=rate_limit_policy,
                        action="stream_api",
                    )
                    runtime.add_closer(response.close)
                    response.encoding = "utf-8"
                    if not response.ok:
                        raise RuntimeError(
                            f"OpenAI-compatible stream failed: {response.status_code} {response.text[:2000]}"
                        )

                    stream_error: Exception | None = None
                    saw_done = False
                    emitted_content = False

                    try:
                        for raw_line in response.iter_lines(decode_unicode=True):
                            if runtime.cancelled.is_set():
                                raise ProviderRequestCancelled(request_id)
                            if not raw_line:
                                continue

                            line = raw_line.strip()
                            data = line
                            if data.startswith("data:"):
                                data = data[len("data:") :].strip()

                            if data == "[DONE]":
                                saw_done = True
                                break

                            try:
                                chunk = json.loads(data)
                            except Exception:
                                continue

                            if _chunk_has_content(chunk):
                                emitted_content = True

                            if state.get("debug_stream"):
                                log.info("chunk", chunk=str(chunk)[:2000])
                            results.put(("chunk", chunk))
                    except (
                        requests.exceptions.ConnectionError,
                        requests.exceptions.ChunkedEncodingError,
                    ) as exc:
                        stream_error = exc
                    finally:
                        response.close()

                    if saw_done:
                        results.put(("done", None))
                        return

                    should_recover = (
                        recovery_mode != "disabled"
                        and recovery_attempts < recovery_max_retries
                        and (recovery_mode == "aggressive" or not emitted_content)
                    )
                    if should_recover:
                        recovery_attempts += 1
                        log.warning(
                            "stream_recovering",
                            recovery_mode=recovery_mode,
                            recovery_attempt=recovery_attempts,
                            emitted_content=emitted_content,
                            error=str(stream_error)[:500] if stream_error else None,
                        )
                        continue

                    if stream_error is not None:
                        raise RuntimeError(
                            f"OpenAI-compatible stream failed: {stream_error}"
                        ) from stream_error
                    results.put(("done", None))
                    return
            except Exception as exc:
                results.put(("error", exc))
            finally:
                session.close()
                runtime.done.set()

        worker = threading.Thread(target=_worker, daemon=True)
        worker.start()

        try:
            while True:
                try:
                    kind, value = results.get(timeout=0.1)
                except queue.Empty:
                    if runtime.cancelled.is_set():
                        raise ProviderRequestCancelled(request_id)
                    if runtime.done.is_set() and results.empty():
                        break
                    continue
                if kind == "chunk":
                    yield value
                    continue
                if kind == "done":
                    return
                exc = value
                if runtime.cancelled.is_set():
                    raise ProviderRequestCancelled(request_id) from exc
                if isinstance(exc, ProviderRequestCancelled):
                    raise exc
                if isinstance(exc, requests.RequestException):
                    raise RuntimeError(
                        f"OpenAI-compatible stream failed: {exc}"
                    ) from exc
                raise RuntimeError(f"OpenAI-compatible stream failed: {exc}") from exc
        finally:
            self._clear_inflight(request_id, runtime)
            worker.join(timeout=1.0)

    def extract_delta(self, chunk: dict[str, Any]) -> dict[str, Any]:
        choice0 = (chunk.get("choices") or [{}])[0]
        return choice0 if isinstance(choice0, dict) else {}

    def process_delta(self, delta: dict[str, Any], accumulated: dict[str, Any] | None):
        base = accumulated or {}
        d = delta.get("delta")
        d = d if isinstance(d, dict) else {}

        role = d.get("role") or base.get("role") or "assistant"
        content = d.get("content")
        content = content if isinstance(content, str) else ""

        patch: dict[str, Any] | None = {"role": role, "content": content}
        if not content and "role" not in d:
            patch = None

        new_acc: dict[str, Any] = {
            **base,
            "role": base.get("role", role),
            "content": (base.get("content") or "") + content,
        }
        return patch, new_acc
