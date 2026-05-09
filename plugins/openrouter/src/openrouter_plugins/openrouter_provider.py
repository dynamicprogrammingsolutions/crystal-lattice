"""
OpenRouter Provider Plugin

Provides access to multiple LLM providers through OpenRouter's unified API.
Compatible with OpenAI Chat Completions API format.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterator, List, Tuple, Optional
from dataclasses import dataclass, field
import base64
import json
import queue
import threading

import requests

from agent_core.tool_result_payloads import (
    TOOL_RESULT_FIELD,
    make_text_tool_result,
    openai_chat_tool_result_content,
    provider_native_tool_result_display,
)
from agent_core.types import ProviderPlugin, ProviderRequestCancelled
from agent_core.utils import get_logger


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


class OpenRouterProvider(ProviderPlugin):
    name: str = "openrouter"
    version: str = "0.1.0"

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

    def _native_internal_from_core_metadata(self, metadata: Any) -> Dict[str, Any]:
        if not isinstance(metadata, dict):
            return {}
        out = dict(metadata)
        out.pop("native_indices", None)
        out.pop("tool_calls", None)
        out.pop("tool_call_id", None)
        out.pop("display", None)
        return out

    def _core_metadata_from_native_internal(self, internal: Any) -> Dict[str, Any]:
        if not isinstance(internal, dict):
            return {}
        out = {
            key: value
            for key, value in internal.items()
            if key not in {"native_indices", "tool_calls", "tool_call_id"}
        }
        return out

    def _session_asset_store(self, context: Optional[Dict[str, Any]]) -> Any:
        if isinstance(context, dict):
            store = context.get("session_asset_store")
            if store is not None:
                return store
        raise RuntimeError(
            "[openrouter_provider] session asset attachment requires session_asset_store in context"
        )

    def _resolve_session_asset(
        self,
        context: Optional[Dict[str, Any]],
        asset_ref: Dict[str, Any],
        expected_attachment_type: str,
    ) -> Tuple[str, str, bytes]:
        store = self._session_asset_store(context)
        session_id = asset_ref.get("session_id")
        asset_id = asset_ref.get("asset_id")
        if not isinstance(session_id, str) or not isinstance(asset_id, str):
            raise ValueError("[openrouter_provider] invalid session asset reference")
        record = store.load(session_id, asset_id)
        if record.attachment_type != expected_attachment_type:
            raise ValueError(
                f"[openrouter_provider] session asset {asset_id!r} is not a {expected_attachment_type} attachment"
            )
        return record.filename, record.mime_type, store.load_bytes(session_id, asset_id)

    def _expanded_tool_content(
        self,
        content: Any,
        context: Optional[Dict[str, Any]],
    ) -> Any:
        if not isinstance(content, list):
            return content

        parts: List[Dict[str, Any]] = []
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") != "image_url":
                parts.append(dict(part))
                continue

            image_url = part.get("image_url")
            if isinstance(image_url, dict) and image_url.get("asset_ref"):
                _, mime_type, payload_bytes = self._resolve_session_asset(
                    context,
                    image_url["asset_ref"],
                    "image",
                )
                parts.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64.b64encode(payload_bytes).decode('ascii')}"
                        },
                    }
                )
                continue

            parts.append(dict(part))
        return parts

    def _expanded_request_messages(
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        context = state.get("_request_context")
        context = context if isinstance(context, dict) else None
        return [
            (
                {
                    **msg,
                    "content": self._expanded_tool_content(
                        msg.get("content"),
                        context,
                    ),
                }
                if msg.get("role") == "tool"
                else msg
            )
            for msg in messages
        ]

    # ---------- Schemas ----------
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": True},
            "base_url": {
                "type": "string",
                "required": False,
                "default": "https://openrouter.ai/api/v1",
            },
            "timeout": {"type": "number", "required": False, "default": 60},
            "site_url": {
                "type": "string",
                "required": False,
                "description": "Optional URL for ranking/tracking",
            },
            "app_name": {
                "type": "string",
                "required": False,
                "description": "Optional application name for identification",
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        model_options = []
        if models:
            for m in models:
                if m and isinstance(m, dict):
                    mid = m.get("id")
                    name = m.get("name")
                    if mid is not None:
                        model_options.append(
                            {
                                "label": name if name is not None else str(mid),
                                "value": str(mid),
                            }
                        )
        use_dropdown = len(model_options) > 0
        return [
            {
                "ui_type": "config",
                "type": "dropdown" if use_dropdown else "text",
                "key": "model",
                "label": "Openrouter Model",
                **({"options": model_options} if use_dropdown else {}),
            },
            {
                "ui_type": "model_picker",
                "key": "model",
                "attachment_type": "dropdown",
                "display_placement": "left",
                "options": model_options,
                "label": "model",
            },
            {
                "ui_type": "composer_attachment",
                "key": "openrouter:attachment:image",
                "attachment_type": "image",
                "supports_url": True,
                "supported_file_types": ["png", "jpg", "jpeg", "webp", "gif"],
                "display_placement": "below",
                "label": "Image",
                "icon": "image",
            },
        ]

    # ---------- Models / capabilities ----------
    def _fetch_models_from_api(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch model data from OpenRouter /models API.

        Returns list of model descriptors with id, name, and supported_parameters.
        Returns empty list on error (logs warning).
        """
        base_url = (config.get("base_url") or "https://openrouter.ai/api/v1").rstrip(
            "/"
        )
        models_url = f"{base_url}/models"

        try:
            response = requests.get(models_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extract models array from response
            models = data.get("data", [])
            if not isinstance(models, list):
                get_logger("openrouter_provider").warning(
                    "Invalid models response format", response=data
                )
                return []

            return models

        except requests.RequestException as e:
            get_logger("openrouter_provider").warning(
                "Failed to fetch models from OpenRouter API",
                error=str(e),
                url=models_url,
            )
            return []
        except Exception as e:
            get_logger("openrouter_provider").warning(
                "Unexpected error fetching models", error=str(e)
            )
            return []

    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return model descriptors from OpenRouter API.

        Fetches all models and filters by config.
        Core framework caches results per config.
        """
        all_models = self._fetch_models_from_api(config)
        if not all_models:
            return []
        return all_models

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability tags based on model's supported_parameters.

        Checks the model's supported_parameters array from the OpenRouter API:
        - 'reasoning' → 'supports_reasoning'
        - 'verbosity' → 'supports_verbosity'
        - 'tools' → 'supports_tools'

        Always includes: provider:openrouter, openrouter, supports_streaming
        Falls back to hardcoded tags if model data unavailable.
        """
        tags: List[str] = ["provider:openrouter", "openrouter"]
        tags.append("supports_streaming")  # All OpenRouter models support streaming

        selected_id = config.get("model")
        if (
            isinstance(selected_id, str)
            and selected_id
            and models
            and isinstance(models, list)
        ):
            for m in models:
                if isinstance(m, dict) and m.get("id") == selected_id:
                    supported_params = m.get("supported_parameters", [])
                    if isinstance(supported_params, list) and len(supported_params) > 0:
                        # Map supported_parameters to capability tags
                        if "tools" in supported_params or "tool" in supported_params:
                            tags.append("supports_tools")
                        if "reasoning" in supported_params:
                            tags.append("supports_reasoning")
                            tags.append("supports_reasoning_effort")
                        if "gpt-5" in selected_id:
                            tags.append("supports_verbosity")

                        return tags

        return tags

    # ---------- State lifecycle ----------
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
        request_id: str | None = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        _ = request_id

        config = state["config"]

        base_url = (config.get("base_url") or "https://openrouter.ai/api/v1").rstrip(
            "/"
        )
        api_key = config.get("api_key")
        model = config.get("model")
        timeout = float(config.get("timeout", 60))

        url = f"{base_url}/chat/completions"
        payload: Dict[str, Any] = {"model": model}
        headers = {"Content-Type": "application/json"}

        if not api_key:
            raise ValueError("[openrouter_provider] api_key is required")

        headers["Authorization"] = f"Bearer {api_key}"

        # Add OpenRouter-specific headers
        site_url = config.get("site_url")
        if site_url:
            headers["HTTP-Referer"] = site_url

        app_name = config.get("app_name")
        if app_name:
            headers["X-Title"] = app_name

        return native_messages, {
            **state,
            "request": {
                "url": url,
                "payload": payload,
                "messages": list(native_messages),
                "headers": headers,
                "timeout": timeout,
            },
            "partial": None,
        }

    # ---------- Message conversion ----------
    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        native: List[Dict[str, Any]] = []

        for msg in messages:
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", "user")
            raw_content = msg.get("content", "")
            tool_result = msg.get(TOOL_RESULT_FIELD)
            raw_metadata = msg.get("metadata")
            metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
            native_tool_content = (
                openai_chat_tool_result_content(tool_result)
                if role == "tool"
                else None
            )
            content = raw_content
            if not isinstance(content, str):
                content = ""

            native_message: Dict[str, Any] = {
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

            parts: List[Dict[str, Any]] = [{"type": "text", "text": content}]
            for part in multipart:
                if not isinstance(part, dict):
                    continue

                part_type = part.get("type")
                part_content = part.get("content")
                if part_type != "image":
                    # UI may advertise additional attachment types for
                    # testing, but OpenRouter only supports images in the
                    # request format used here. Silently ignore others.
                    continue
                if not isinstance(part_content, dict):
                    raise ValueError(
                        "[openrouter_provider] image multipartContent part requires dict content"
                    )

                url = part_content.get("url")
                if not isinstance(url, str) or not url:
                    data_base64 = part_content.get("data_base64")
                    mime_type = part_content.get("mime_type")
                    if isinstance(data_base64, str) and data_base64:
                        if not isinstance(mime_type, str) or not mime_type:
                            raise ValueError(
                                "[openrouter_provider] image multipartContent part using data_base64 requires mime_type"
                            )
                        url = f"data:{mime_type};base64,{data_base64}"

                if not isinstance(url, str) or not url:
                    raise ValueError(
                        "[openrouter_provider] image multipartContent part requires content.url or content.data_base64"
                    )

                parts.append({"type": "image_url", "image_url": {"url": url}})

            native.append({**native_message, "content": parts})

        return native

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert provider-native finals to core messages.

        Reasoning fields are intentionally ignored here; the
        OpenRouterReasoningExtension is responsible for exposing
        reasoning and reasoning_details via message metadata.
        """
        normalized: List[Dict[str, Any]] = []
        for native_idx, m in enumerate(native_messages):
            if not isinstance(m, dict):
                continue
            if not ("role" in m or "content" in m):
                continue

            role = m.get("role", "assistant")
            content = m.get("content", "")
            metadata = self._core_metadata_from_native_internal(m.get("_metadata"))

            msg: Dict[str, Any] = {"role": role, "content": ""}
            multipart_out: List[Dict[str, Any]] = []

            if isinstance(content, list):
                text_parts: List[str] = []
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

            tool_calls = m.get("tool_calls")
            if isinstance(tool_calls, list) and tool_calls:
                metadata["tool_calls"] = tool_calls

            tool_call_id = m.get("tool_call_id")
            if isinstance(tool_call_id, str) and tool_call_id:
                metadata["tool_call_id"] = tool_call_id

            metadata["native_indices"] = [native_idx]
            normalized.append({**msg, "metadata": metadata})

        return normalized

    # ---------- Core API calls ----------
    def _validate_message_list(self, history: List[Dict[str, Any]]) -> None:
        """Validate that every item is a message-shaped dict with role and content.
        Other keys are allowed. Raise with details if invalid.
        """
        for idx, item in enumerate(history):
            if not isinstance(item, dict):
                raise RuntimeError(
                    f"[openrouter_provider] invalid message at index {idx}: expected dict, got {type(item).__name__} -> {item}"
                )
            if "role" not in item or "content" not in item:
                raise RuntimeError(
                    f"[openrouter_provider] invalid message at index {idx}: missing 'role' or 'content' -> {json.dumps(item, ensure_ascii=False)}"
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
        payload: Dict[str, Any] = {}
        logger = get_logger("openrouter_provider")
        self._validate_message_list(native_messages)
        override = request.get("messages")
        messages = override if isinstance(override, list) else native_messages
        messages = self._expanded_request_messages(
            [m for m in messages if isinstance(m, dict)],
            state,
        )
        messages_to_send = [
            {k: v for k, v in m.items() if k != "_metadata"}
            for m in messages
            if isinstance(m, dict)
        ]
        payload = {**request["payload"], "messages": messages_to_send, "stream": False}
        logger.info(
            "sending request",
            payload=str(
                {**payload, "messages": "***REDACTED***", "tools": "***REDACTED***"}
            ),
        )
        # logger.debug("full payload for non-streaming request", payload=payload)

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
                            "OpenRouter API call failed: request ended without result"
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
                    try:  # pragma: no cover - debug aid
                        debug_payload = json.dumps(payload, ensure_ascii=False)[:2000]
                        print(
                            "[openrouter_provider] call_api error payload:",
                            debug_payload,
                        )
                    except Exception:
                        print(
                            "[openrouter_provider] call_api error payload: <unserializable>"
                        )
                    resp = getattr(exc, "response", None)
                    if resp is not None:
                        try:
                            err_detail = resp.json()
                        except Exception:
                            err_detail = resp.text
                        print(
                            "[openrouter_provider] call_api error response:", err_detail
                        )
                    raise RuntimeError(f"OpenRouter API call failed: {exc}") from exc
                raise RuntimeError(f"OpenRouter API call failed: {exc}") from exc
        finally:
            self._clear_inflight(request_id, runtime)
            worker.join(timeout=1.0)

        message = obj.get("choices", [{}])[0].get("message", {})

        # TODO: Check why this was added here instead of in ClaudeCachingExtension - maybe an agent wasn't able to make a test working without it?
        # Attach cached_tokens from usage.prompt_tokens_details (when present)
        # as provider-native internal metadata on the assistant message. This
        # is later surfaced into core message metadata by provider extensions
        # (for example, ClaudeCachingExtension).
        # try:  # pragma: no cover - defensive, best-effort only
        #     usage = obj.get("usage") or {}
        #     cached_tokens = None
        #     if isinstance(usage, dict):
        #         details = usage.get("prompt_tokens_details") or {}
        #         if isinstance(details, dict) and "cached_tokens" in details:
        #             cached_tokens = details.get("cached_tokens")
        #     if cached_tokens is not None and isinstance(message, dict):
        #         internal_md = dict(message.get("_metadata") or {})
        #         internal_md["cached_tokens"] = cached_tokens
        #         message["_metadata"] = internal_md
        # except Exception:
        #     # Never allow usage-metadata extraction to break the provider.
        #     pass

        return [], [message], [*native_messages, message], state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Iterator[Dict[str, Any]]:
        request = state["request"]
        payload: Dict[str, Any] = {}
        logger = get_logger("openrouter_provider")
        self._validate_message_list(native_messages)
        override = request.get("messages")
        messages = override if isinstance(override, list) else native_messages
        messages = self._expanded_request_messages(
            [m for m in messages if isinstance(m, dict)],
            state,
        )
        messages_to_send = [
            {k: v for k, v in m.items() if k != "_metadata"}
            for m in messages
            if isinstance(m, dict)
        ]
        payload = {**request["payload"], "messages": messages_to_send, "stream": True}
        logger.info(
            "sending request",
            payload=str({**payload, "messages": "stripped", "tools": "stripped"}),
        )
        logger.debug("full payload for streaming request", payload=payload)

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
                if response.status_code != 200:
                    try:
                        error_detail = response.json()
                    except Exception:
                        error_detail = response.text
                    raise RuntimeError(
                        f"OpenRouter stream failed: {response.status_code} {response.reason}. "
                        f"Error: {error_detail}"
                    )
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
                    raise RuntimeError(f"OpenRouter stream failed: {exc}") from exc
                raise RuntimeError(f"OpenRouter stream failed: {exc}") from exc
        finally:
            self._clear_inflight(request_id, runtime)
            worker.join(timeout=1.0)

    # ---------- Helpers (default/general implementations) ----------
    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract a provider-native delta dictionary from a streaming chunk.
        Return the first choice if present.
        """
        if "choices" in native_chunk and native_chunk["choices"]:
            return native_chunk["choices"][0]

        return {}

    def process_delta(
        self, delta: Dict[str, Any], accumulated
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Reduce a delta dict into a new partial accumulator, and optionally a final.
        Returns (partial_message_or_none, final_message_or_none, new_accumulated).
        """
        content = delta.get("message") or delta.get("delta") or {}
        return content, self._merge_delta_content(
            accumulated or {}, content, override=["role"], accumulate=["content"]
        )

    def _merge_delta_content(
        self,
        current: Dict[str, Any],
        delta: Dict[str, Any],
        override: List[str] = [],
        accumulate: List[str] = [],
    ) -> Dict[str, Any]:
        return {
            **current,
            **{key: delta.get(key, current.get(key, "")) for key in override},
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
        # print("chunk:", native_chunk)
        partial, accumulated = self.process_delta(
            delta=self.extract_delta(native_chunk), accumulated=state.get("partial", {})
        )
        new_state = {**state, "partial": accumulated}
        return_values = [partial] if partial else [], [], native_messages, new_state
        return return_values

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        current_partial = state.get("partial", None)
        finals = [current_partial] if current_partial else []
        full_history = (
            [*native_messages, current_partial] if current_partial else native_messages
        )
        return finals, full_history, state

    def to_display_format(
        self, message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return message
