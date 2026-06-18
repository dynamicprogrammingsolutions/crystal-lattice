"""
OpenAI-Compatible Provider Plugin (plugins/providers/openai/python/openai_provider.py)

Minimal provider for OpenAI-compatible Chat Completions endpoints (e.g., Ollama at /v1).
Loads configuration only from the provided config dict (no environment variable usage).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple
from dataclasses import dataclass, field
import json
import queue
import threading

import requests

from agent_core.types import ProviderPlugin, ProviderRequestCancelled


@dataclass
class _InflightRequest:
    cancelled: threading.Event = field(default_factory=threading.Event)
    done: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)
    closers: List[Callable[[], None]] = field(default_factory=list)

    def add_closer(self, closer: Callable[[], None]) -> None:
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


class OpenAICompatibleProvider(ProviderPlugin):
    name: str = "openai_compatible"
    version: str = "0.3.0"

    def __init__(self) -> None:
        self._inflight_lock = threading.Lock()
        self._inflight_requests: Dict[str, _InflightRequest] = {}

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

    # ---------- Schemas ----------
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": False},
            "base_url": {
                "type": "string",
                "required": False,
                "default": "https://api.openai.com/v1",
            },
            "timeout": {"type": "number", "required": False, "default": 60},
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        # No UI elements
        return []

    # ---------- Models / capabilities ----------
    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return minimal model descriptors for this provider.

        Currently returns the configured `model` (if any) as a single
        ModelDescriptor with only an `id` field.
        """
        model = config.get("model")
        if isinstance(model, str) and model:
            return [{"id": model}]
        return []

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability tags for the OpenAI-compatible provider.

        This implementation is intentionally simple and conservative; it
        assumes chat-completions style models with tool calling and
        streaming support.
        """
        tags: List[str] = ["provider:openai_compatible"]
        tags.append("supports_streaming")
        tags.append("supports_tools")
        tags.append("supports_thinking")
        return tags

    # ---------- State lifecycle ----------
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:

        # Provider state is an opaque dict owned by the provider and its
        # extensions/features. This implementation only needs configuration,
        # request metadata, and a streaming accumulator.
        return {"config": config}

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        _ = request_id

        config = state["config"]

        base_url = (config.get("base_url") or "https://api.openai.com/v1").rstrip("/")
        api_key = config.get("api_key")
        model = config.get("model")
        timeout = float(config.get("timeout", 60))

        url = f"{base_url}/chat/completions"
        payload: Dict[str, Any] = {"model": model}
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        return native_messages, {
            **state,
            "request": {
                "url": url,
                "payload": payload,
                "headers": headers,
                "timeout": timeout,
            },
            "accumulator": None,
        }

    # ---------- Message conversion ----------
    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        native: List[Dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            md = msg.get("metadata")
            internal_md = dict(md) if isinstance(md, dict) else {}
            internal_md.pop("native_indices", None)

            if internal_md:
                native.append(
                    {"role": role, "content": content, "_metadata": internal_md}
                )
            else:
                native.append({"role": role, "content": content})
        return native

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert provider-native finals to core messages.

        This provider-level conversion intentionally ignores any
        provider-specific reasoning fields. Reasoning content should be
        surfaced by dedicated extensions (e.g., thinking extensions)
        via message metadata rather than as a top-level field.
        """
        normalized: List[Dict[str, Any]] = []
        for m in native_messages:
            if not isinstance(m, dict):
                continue
            if not ("role" in m or "content" in m):
                # Ignore non-message shapes (like full completion objects)
                continue

            raw_internal = m.get("_metadata") or {}
            internal_md = dict(raw_internal) if isinstance(raw_internal, dict) else {}
            internal_md.pop("native_indices", None)
            msg = {
                "role": m.get("role", "assistant"),
                "content": m.get("content", ""),
            }
            normalized.append({**msg, "metadata": internal_md})
        return normalized

    # ---------- Core API calls ----------
    def _validate_message_list(self, history: List[Dict[str, Any]]) -> None:
        """Validate that every item is a message-shaped dict with role and content.
        Other keys are allowed. Raise with details if invalid.
        """
        for idx, item in enumerate(history):
            if not isinstance(item, dict):
                raise RuntimeError(
                    f"[openai_provider] invalid message at index {idx}: expected dict, got {type(item).__name__} -> {item}"
                )
            if "role" not in item or "content" not in item:
                raise RuntimeError(
                    f"[openai_provider] invalid message at index {idx}: missing 'role' or 'content' -> {json.dumps(item, ensure_ascii=False)}"
                )

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        request = state["request"]
        # Validate native_messages are proper message objects
        self._validate_message_list(native_messages)
        # Allow features to override the message history for this
        # request by placing a rendered list under
        # state["request"]["messages"].
        override = request.get("messages")
        base_history = override if isinstance(override, list) else native_messages
        # Strip any internal _metadata field before sending to the provider.
        messages_to_send = [
            {k: v for k, v in m.items() if k != "_metadata"}
            for m in base_history
            if isinstance(m, dict)
        ]
        payload = {**request["payload"], "messages": messages_to_send, "stream": False}

        runtime = self._register_inflight(request_id)
        results: queue.Queue[Tuple[str, Any]] = queue.Queue()

        def _worker() -> None:
            session = requests.Session()
            response: requests.Response | None = None
            runtime.add_closer(session.close)
            try:
                if runtime.cancelled.is_set():
                    raise ProviderRequestCancelled(request_id)
                response = session.post(
                    request["url"],
                    json=payload,
                    headers=request["headers"],
                    timeout=request["timeout"],
                    stream=True,
                )
                runtime.add_closer(response.close)
                response.encoding = "utf-8"
                obj = response.json()
                results.put(("result", obj))
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
                    obj = value
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

        message = obj.get("choices", [{}])[0].get("message", {})
        return [], [message], [*native_messages, message], state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Iterator[Dict[str, Any]]:
        request = state["request"]
        # Validate native_messages before sending stream request
        self._validate_message_list(native_messages)
        override = request.get("messages")
        base_history = override if isinstance(override, list) else native_messages
        # Strip any internal _metadata field before sending to the provider.
        messages_to_send = [
            {k: v for k, v in m.items() if k != "_metadata"}
            for m in base_history
            if isinstance(m, dict)
        ]
        payload = {**request["payload"], "messages": messages_to_send, "stream": True}

        runtime = self._register_inflight(request_id)
        results: queue.Queue[Tuple[str, Any]] = queue.Queue()

        def _worker() -> None:
            session = requests.Session()
            response: requests.Response | None = None
            runtime.add_closer(session.close)
            try:
                if runtime.cancelled.is_set():
                    raise ProviderRequestCancelled(request_id)
                response = session.post(
                    request["url"],
                    json=payload,
                    headers=request["headers"],
                    timeout=request["timeout"],
                    stream=True,
                )
                runtime.add_closer(response.close)
                # See call_api above: streaming chunks are UTF-8 JSON.
                # Force UTF-8 so iter_lines(decode_unicode=True) does not
                # decode bytes with a legacy charset and garble characters
                # in tool_call.function.arguments.
                response.encoding = "utf-8"
                response.raise_for_status()
                for line in response.iter_lines(decode_unicode=True):
                    if runtime.cancelled.is_set():
                        raise ProviderRequestCancelled(request_id)
                    if not line:
                        continue
                    data_str = line
                    if data_str.startswith("data:"):
                        data_str = data_str[len("data:") :].strip()
                    if not data_str or data_str == "[DONE]":
                        if data_str == "[DONE]":
                            break
                        continue
                    try:
                        obj = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    results.put(("chunk", obj))
                results.put(("done", None))
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
                        break
                    continue
                if kind == "chunk":
                    yield value
                    continue
                if kind == "done":
                    break
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

    # ---------- Helpers (default/general implementations) ----------
    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a provider-native delta dictionary from a streaming chunk.

        Returns the first choice object when present, or an empty dict.
        """
        if "choices" in native_chunk and native_chunk["choices"]:
            return native_chunk["choices"][0]

        return {}

    def process_delta(self, delta: Dict[str, Any], accumulated):
        """Reduce a delta dict into a new partial and accumulator.

        Returns the current partial fragment from this chunk and an updated
        accumulator used later by :meth:`finalize` to build the final message.
        """
        # Normalize accumulator once
        base = accumulated or {}

        # Prefer full message objects, then deltas
        content = delta.get("message") or delta.get("delta") or None
        if content is None:
            return None, base

        new_accumulated = self._merge_delta_content(
            base,
            content,
            override=["role"],
            accumulate=["content"],
        )
        return content, new_accumulated

    def _merge_delta_content(
        self,
        current: Dict[str, Any],
        delta: Dict[str, Any],
        override: List[str] = [],
        accumulate: List[str] = [],
    ) -> Dict[str, Any]:
        return {
            **current,
            # For override keys, prefer the incoming delta value, falling back to current
            **{key: delta.get(key, current.get(key, "")) for key in override},
            # For accumulate keys, append incoming delta fragments to current value
            **{
                key: ((current.get(key) or "") + (delta.get(key) or ""))
                for key in accumulate
            },
        }

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """Process a streaming chunk into provider-native partials.

        Pattern:
        - Extract a delta from the chunk
        - Reduce it into a partial fragment and update the accumulator
        - Do not emit finals or modify history; :meth:`finalize` is responsible
          for producing the final message from the accumulator.
        """
        partial_msg, accumulated = self.process_delta(
            delta=self.extract_delta(native_chunk),
            accumulated=state.get("accumulator", {}),
        )

        partials = [partial_msg] if partial_msg else []
        finals: List[Dict[str, Any]] = []
        new_state = {**state, "accumulator": accumulated}

        return partials, finals, native_messages, new_state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Finalize streaming by emitting the accumulator as a final.

        When streaming was used, `state["accumulator"]` holds the merged assistant
        message (content, role, reasoning, tool_calls, etc.) built up across
        chunks by the provider and any extensions. Non-streaming calls leave it
        as ``None``.
        """
        accumulator = state.get("accumulator", None)

        if accumulator:
            return [accumulator], [*native_messages, accumulator], state

        return [], native_messages, state

    def to_display_format(
        self, message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return message
