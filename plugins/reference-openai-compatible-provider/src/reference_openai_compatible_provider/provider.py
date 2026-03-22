from __future__ import annotations

import json
from typing import Any, Iterator

import requests

from agent_core.types import ProviderPlugin
from agent_core.utils import get_logger

log = get_logger("reference_openai_compatible_provider")

_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_MODELS_TIMEOUT_CAP_SECONDS = 10.0


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
        }

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"config": config}

    def get_models(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        base_url = str(config.get("base_url") or _DEFAULT_BASE_URL).rstrip("/")

        url = f"{base_url}/models"

        headers: dict[str, str] = {}
        api_key = config.get("api_key")
        if isinstance(api_key, str) and api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        timeout = min(float(config.get("timeout", 60)), _MODELS_TIMEOUT_CAP_SECONDS)

        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
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
            "type": "select" if options else "text",
            "key": "model",
            "label": "Model",
        }
        if options:
            model_el["options"] = options

        return [
            {
                "ui_type": "config",
                "type": "text",
                "key": "base_url",
                "label": "Base URL",
            },
            model_el,
            {"ui_type": "config", "type": "text", "key": "api_key", "label": "API key"},
            {
                "ui_type": "config",
                "type": "text",
                "key": "timeout",
                "label": "Timeout (seconds)",
            },
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": "debug_stream",
                "label": "Debug streaming chunks",
            },
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
            "partial": None,
            "debug_stream": bool(cfg.get("debug_stream", False)),
        }

    def call_api(self, native_messages: list[dict[str, Any]], state: dict[str, Any]):
        request = state.get("request") or {}
        payload = dict(request.get("payload") or {})
        override = request.get("messages")
        base_history = override if isinstance(override, list) else native_messages
        messages_to_send = [
            {k: v for k, v in m.items() if k != "_metadata"}
            for m in base_history
            if isinstance(m, dict)
        ]
        payload |= {"messages": messages_to_send, "stream": False}

        resp = requests.post(
            str(request.get("url")),
            headers=dict(request.get("headers") or {}),
            json=payload,
            timeout=float(request.get("timeout", 60)),
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
        payload = dict(request.get("payload") or {})
        override = request.get("messages")
        base_history = override if isinstance(override, list) else native_messages
        messages_to_send = [
            {k: v for k, v in m.items() if k != "_metadata"}
            for m in base_history
            if isinstance(m, dict)
        ]
        payload |= {"messages": messages_to_send, "stream": True}

        resp = requests.post(
            str(request.get("url")),
            headers=dict(request.get("headers") or {}),
            json=payload,
            timeout=float(request.get("timeout", 60)),
            stream=True,
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
