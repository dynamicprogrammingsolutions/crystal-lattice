from __future__ import annotations

import json
import threading
import time
from typing import Any, Iterator

import requests

from agent_core.types import ProviderPlugin
from agent_core.utils import get_logger

log = get_logger("reference_openai_compatible_provider")

_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_MODELS_TIMEOUT_CAP_SECONDS = 10.0
_DEFAULT_MIN_REQUEST_INTERVAL_SECONDS = 0.0

_request_pacing_lock = threading.Lock()
_next_request_time_by_scope: dict[str, float] = {}


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
        _next_request_time_by_scope[scope_key] = (
            target + max(min_request_interval_seconds, 0.0)
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
        response = request_fn()
        if getattr(response, "status_code", None) != 429:
            return response

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
            state.get("partial") if isinstance(state.get("partial"), dict) else {}
        )
        patch, new_acc = self.process_delta(delta, accumulated)

        partials: list[dict[str, Any]] = []
        if isinstance(patch, dict) and patch:
            partials = [patch]

        return partials, [], list(native_messages), {**state, "partial": new_acc}

    def finalize(self, native_messages: list[dict[str, Any]], state: dict[str, Any]):
        final = state.get("partial")
        if isinstance(final, dict) and final:
            return [final], [*native_messages, final], state
        return [], list(native_messages), state


class OpenAICompatibleProvider(AccumulatorStreamingMixin, ProviderPlugin):
    """OpenAI-compatible chat-completions provider.

    Designed to work with OpenAI-like endpoints, including Ollama's OpenAI-compatible API.
    """

    name = "reference_openai_compatible"
    version = "0.1.0"

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "base_url": {
                "type": "string",
                "required": False,
                "default": "https://api.openai.com/v1",
                "description": "OpenAI-compatible base URL (no trailing slash required)",
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
            "type": "dropdown" if options else "text",
            "key": "model",
            "label": "Model",
        }

        if options:
            model_el["options"] = options

        return [
            model_el
        ]

    def get_tags(self, config: dict[str, Any], models: list[dict[str, Any]]):
        return [
            "provider:openai_compatible",
            "supports_streaming",
            "supports_tools",
        ]

    def initialize_request(
        self, native_messages: list[dict[str, Any]], state: dict[str, Any]
    ):
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
        return list(native_messages), {
            **state,
            "request": request,
            "rate_limit_policy": _rate_limit_policy_from_config(cfg),
            "partial": None,
            "debug_stream": bool(cfg.get("debug_stream", False)),
        }

    def call_api(self, native_messages: list[dict[str, Any]], state: dict[str, Any]):
        request = state.get("request") or {}
        rate_limit_policy = state.get("rate_limit_policy") or {}
        payload = dict(request.get("payload") or {})
        override = request.get("messages")
        base_history = override if isinstance(override, list) else native_messages
        messages_to_send = [
            {k: v for k, v in m.items() if k != "_metadata"}
            for m in base_history
            if isinstance(m, dict)
        ]
        payload |= {"messages": messages_to_send, "stream": False}

        resp = _request_with_rate_limit_retry(
            request_fn=lambda: requests.post(
                str(request.get("url")),
                headers=dict(request.get("headers") or {}),
                json=payload,
                timeout=float(request.get("timeout", 60)),
            ),
            rate_limit_policy=rate_limit_policy,
            action="call_api",
        )
        resp.encoding = "utf-8"
        if not resp.ok:
            raise RuntimeError(
                f"OpenAI-compatible call failed: {resp.status_code} {resp.text[:2000]}"
            )

        raw = resp.json()
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
        self, native_messages: list[dict[str, Any]], state: dict[str, Any]
    ) -> Iterator[dict[str, Any]]:
        request = state.get("request") or {}
        rate_limit_policy = state.get("rate_limit_policy") or {}
        payload = dict(request.get("payload") or {})
        override = request.get("messages")
        base_history = override if isinstance(override, list) else native_messages
        messages_to_send = [
            {k: v for k, v in m.items() if k != "_metadata"}
            for m in base_history
            if isinstance(m, dict)
        ]
        payload |= {"messages": messages_to_send, "stream": True}

        resp = _request_with_rate_limit_retry(
            request_fn=lambda: requests.post(
                str(request.get("url")),
                headers=dict(request.get("headers") or {}),
                json=payload,
                timeout=float(request.get("timeout", 60)),
                stream=True,
            ),
            rate_limit_policy=rate_limit_policy,
            action="stream_api",
        )
        resp.encoding = "utf-8"
        if not resp.ok:
            raise RuntimeError(
                f"OpenAI-compatible stream failed: {resp.status_code} {resp.text[:2000]}"
            )

        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line:
                continue

            line = raw_line.strip()
            data = line
            if data.startswith("data:"):
                data = data[len("data:") :].strip()

            if data == "[DONE]":
                break

            try:
                chunk = json.loads(data)
            except Exception:
                continue

            if state.get("debug_stream"):
                log.info("chunk", chunk=str(chunk)[:2000])
            yield chunk

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
