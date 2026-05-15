from __future__ import annotations

import base64
import binascii
import mimetypes
import queue
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from agent_core.types import ProviderPlugin, ProviderRequestCancelled
from agent_core.utils import get_logger


_SESSION_ASSETS_METADATA_KEY = "session_assets"
_PROVIDER_REF_KEY = "openrouter_image_generation"


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


class OpenRouterImageGenerationProvider(ProviderPlugin):
    name: str = "openrouter_image_generation"
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

    def _clear_inflight(self, request_id: str | None, runtime: _InflightRequest) -> None:
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

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": True},
            "base_url": {
                "type": "string",
                "required": False,
                "default": "https://openrouter.ai/api/v1",
            },
            "timeout": {"type": "number", "required": False, "default": 120},
            "site_url": {"type": "string", "required": False},
            "app_name": {"type": "string", "required": False},
            "output_text": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Request text alongside generated images when the model supports it.",
            },
            "aspect_ratio": {"type": "string", "required": False},
            "image_size": {"type": "string", "required": False},
            "image_format": {"type": "string", "required": False},
            "moderation": {"type": "string", "required": False},
            "image_config": {
                "type": "object",
                "required": False,
                "description": "Additional OpenRouter image_config fields forwarded as-is.",
            },
            "modalities": {
                "type": "array",
                "required": False,
                "description": "Optional explicit modalities override.",
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        models = context.get("models", []) if isinstance(context, dict) else []
        model_options: List[Dict[str, str]] = []
        for model in models or []:
            if not isinstance(model, dict):
                continue
            model_id = model.get("id")
            if model_id is None:
                continue
            model_name = model.get("name")
            model_options.append(
                {
                    "label": str(model_name) if model_name is not None else str(model_id),
                    "value": str(model_id),
                }
            )

        use_dropdown = len(model_options) > 0
        return [
            {
                "ui_type": "config",
                "type": "dropdown" if use_dropdown else "text",
                "key": "model",
                "label": "OpenRouter Image Model",
                **({"options": model_options} if use_dropdown else {}),
            },
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": "output_text",
                "label": "Return text when supported",
            },
            {
                "ui_type": "config",
                "type": "text",
                "key": "aspect_ratio",
                "label": "Aspect ratio",
            },
            {
                "ui_type": "config",
                "type": "text",
                "key": "image_size",
                "label": "Image size",
            },
        ]

    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        base_url = (config.get("base_url") or "https://openrouter.ai/api/v1").rstrip("/")
        try:
            response = requests.get(
                f"{base_url}/models",
                params={"output_modalities": "image"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            get_logger("openrouter_image_generation_provider").warning(
                "failed_to_fetch_models",
                error=str(exc),
            )
            return []
        models = data.get("data")
        return [model for model in models if isinstance(model, dict)] if isinstance(models, list) else []

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        _ = config, models
        return ["provider:openrouter_image_generation", "openrouter_image_generation"]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        _ = request_id, context
        config = state.get("config") if isinstance(state.get("config"), dict) else {}
        api_key = config.get("api_key")
        if not isinstance(api_key, str) or not api_key:
            raise ValueError("[openrouter_image_generation_provider] api_key is required")

        base_url = (config.get("base_url") or "https://openrouter.ai/api/v1").rstrip("/")
        payload: Dict[str, Any] = {
            "model": config.get("model"),
            "stream": False,
        }

        modalities = config.get("modalities")
        if isinstance(modalities, list) and modalities:
            payload["modalities"] = [str(item) for item in modalities if isinstance(item, str) and item]
        else:
            payload["modalities"] = ["image", "text"] if bool(config.get("output_text")) else ["image"]

        image_config = dict(config.get("image_config") or {}) if isinstance(config.get("image_config"), dict) else {}
        for key in ("aspect_ratio", "image_size", "image_format", "moderation"):
            value = config.get(key)
            if isinstance(value, str) and value:
                image_config[key] = value
        if image_config:
            payload["image_config"] = image_config

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        site_url = config.get("site_url")
        if isinstance(site_url, str) and site_url:
            headers["HTTP-Referer"] = site_url
        app_name = config.get("app_name")
        if isinstance(app_name, str) and app_name:
            headers["X-Title"] = app_name

        timeout = float(config.get("timeout", 120))
        return native_messages, {
            **state,
            "request": {
                "url": f"{base_url}/chat/completions",
                "payload": payload,
                "headers": headers,
                "timeout": timeout,
            },
        }

    def _request_context(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        value = state.get("_request_context")
        return value if isinstance(value, dict) else None

    def _session_asset_store(
        self,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        resolved_context = context if isinstance(context, dict) else self._request_context(state)
        store = resolved_context.get("session_asset_store") if isinstance(resolved_context, dict) else None
        if store is None:
            raise RuntimeError(
                "[openrouter_image_generation_provider] session asset attachment requires session_asset_store in context"
            )
        return store

    def _session_id(self, state: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        resolved_context = context if isinstance(context, dict) else self._request_context(state)
        session_id = resolved_context.get("session_id") if isinstance(resolved_context, dict) else None
        if not isinstance(session_id, str) or not session_id:
            session_dict = resolved_context.get("session") if isinstance(resolved_context, dict) else None
            session_id = session_dict.get("session_id") if isinstance(session_dict, dict) else None
        if not isinstance(session_id, str) or not session_id:
            raise RuntimeError(
                "[openrouter_image_generation_provider] session_id missing from request context"
            )
        return session_id

    def _session_asset_index(
        self,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        resolved_context = context if isinstance(context, dict) else self._request_context(state)
        session_dict = resolved_context.get("session") if isinstance(resolved_context, dict) else None
        metadata = session_dict.get("metadata") if isinstance(session_dict, dict) else {}
        index = metadata.get(_SESSION_ASSETS_METADATA_KEY) if isinstance(metadata, dict) else {}
        return dict(index) if isinstance(index, dict) else {}

    def _resolve_input_image(
        self,
        content: Any,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not isinstance(content, dict):
            raise ValueError(
                "[openrouter_image_generation_provider] image multipartContent part requires dict content"
            )
        url = content.get("url")
        if isinstance(url, str) and url:
            return {"type": "image_url", "image_url": {"url": url}}

        asset_ref = content.get("asset_ref")
        if isinstance(asset_ref, dict) and asset_ref.get("kind") == "session_asset":
            store = self._session_asset_store(state, context)
            session_id = asset_ref.get("session_id")
            asset_id = asset_ref.get("asset_id")
            if not isinstance(session_id, str) or not isinstance(asset_id, str):
                raise ValueError(
                    "[openrouter_image_generation_provider] invalid session asset reference"
                )
            record = store.load(session_id, asset_id)
            payload_bytes = store.load_bytes(session_id, asset_id)
            data_url = f"data:{record.mime_type};base64,{base64.b64encode(payload_bytes).decode('ascii')}"
            return {"type": "image_url", "image_url": {"url": data_url}}

        data_base64 = content.get("data_base64")
        mime_type = content.get("mime_type")
        if isinstance(data_base64, str) and data_base64:
            if not isinstance(mime_type, str) or not mime_type:
                raise ValueError(
                    "[openrouter_image_generation_provider] image multipartContent part using data_base64 requires mime_type"
                )
            return {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{data_base64}"}}

        raise ValueError(
            "[openrouter_image_generation_provider] image multipartContent part requires content.url, content.asset_ref, or content.data_base64"
        )

    def _validate_v1_input(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(messages) != 1:
            raise ValueError(
                "[openrouter_image_generation_provider] V1 supports exactly one user message and rejects multi-turn history"
            )
        message = messages[0]
        if message.get("role") != "user":
            raise ValueError(
                "[openrouter_image_generation_provider] V1 requires the single request message to have role 'user'"
            )
        content = message.get("content")
        if not isinstance(content, list):
            raise ValueError(
                "[openrouter_image_generation_provider] expected provider-native user content list"
            )
        image_parts = [part for part in content if isinstance(part, dict) and part.get("type") == "image_url"]
        if len(image_parts) > 1:
            raise ValueError(
                "[openrouter_image_generation_provider] V1 supports at most one input image"
            )
        return message

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        native: List[Dict[str, Any]] = []
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            if role != "user":
                native.append({"role": role, "content": msg.get("content", "")})
                continue
            text = msg.get("content") if isinstance(msg.get("content"), str) else ""
            parts: List[Dict[str, Any]] = []
            if text:
                parts.append({"type": "text", "text": text})
            multipart = msg.get("multipartContent")
            if isinstance(multipart, list):
                for part in multipart:
                    if not isinstance(part, dict) or part.get("type") != "image":
                        continue
                    parts.append(self._resolve_input_image(part.get("content"), state, context))
            native.append({"role": "user", "content": parts})
        return native

    def _native_text_parts(self, content: Any) -> List[str]:
        if isinstance(content, str):
            return [content] if content else []
        if not isinstance(content, list):
            return []
        out: List[str] = []
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") in {"text", "output_text", "input_text"}:
                text = part.get("text")
                if isinstance(text, str) and text:
                    out.append(text)
        return out

    def _candidate_filename(self, mime_type: str, index: int) -> str:
        extension = mimetypes.guess_extension(mime_type) or ".png"
        return f"generated-image-{index + 1}{extension}"

    def _decode_data_url(self, value: str) -> Tuple[str, str]:
        prefix, _, payload = value.partition(",")
        if not payload or ";base64" not in prefix:
            raise ValueError("invalid data URL")
        mime_type = prefix[5:].split(";", 1)[0] or "image/png"
        return mime_type, payload

    def _store_generated_image(
        self,
        image_candidate: Dict[str, Any],
        *,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        index: int,
    ) -> Dict[str, Any]:
        store = self._session_asset_store(state, context)
        session_id = self._session_id(state, context)

        data_base64 = image_candidate.get("data_base64")
        mime_type = image_candidate.get("mime_type")
        filename = image_candidate.get("filename")
        if isinstance(image_candidate.get("url"), str) and image_candidate["url"].startswith("data:"):
            mime_type, data_base64 = self._decode_data_url(image_candidate["url"])

        if isinstance(image_candidate.get("url"), str) and image_candidate["url"].startswith(("http://", "https://")):
            response = requests.get(image_candidate["url"], timeout=60)
            response.raise_for_status()
            payload_bytes = response.content
            mime_type = response.headers.get("Content-Type") or mime_type or "image/png"
            data_base64 = base64.b64encode(payload_bytes).decode("ascii")
            if not isinstance(filename, str) or not filename:
                parsed = urlparse(image_candidate["url"])
                tail = parsed.path.rsplit("/", 1)[-1]
                filename = tail or self._candidate_filename(mime_type, index)

        if not isinstance(data_base64, str) or not data_base64:
            raise ValueError(
                "[openrouter_image_generation_provider] generated image missing storable payload"
            )
        if not isinstance(mime_type, str) or not mime_type:
            mime_type = "image/png"
        if not isinstance(filename, str) or not filename:
            filename = self._candidate_filename(mime_type, index)

        record = store.store_base64(
            session_id=session_id,
            attachment_type="image",
            filename=filename,
            mime_type=mime_type,
            data_base64=data_base64,
            provider_refs={_PROVIDER_REF_KEY: {"status": "generated"}},
        )
        asset_descriptor = record.public_descriptor()
        asset_index = self._session_asset_index(state, context)
        asset_index[record.asset_id] = asset_descriptor
        return {
            "asset_descriptor": asset_descriptor,
            "preview_data_base64": data_base64,
            "preview_mime_type": mime_type,
            "session_metadata_patch": {_SESSION_ASSETS_METADATA_KEY: asset_index},
        }

    def _extract_image_candidates(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        content = message.get("content")
        if isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                part_type = part.get("type")
                if part_type in {"image_url", "image"}:
                    image_url = part.get("image_url")
                    if isinstance(image_url, dict):
                        url = image_url.get("url")
                        if isinstance(url, str) and url:
                            candidates.append({"url": url})
                    elif isinstance(image_url, str) and image_url:
                        candidates.append({"url": image_url})
                    continue
                if part_type in {"output_image", "image_base64"}:
                    data_base64 = part.get("data_base64") or part.get("b64_json")
                    mime_type = part.get("mime_type") or "image/png"
                    if isinstance(data_base64, str) and data_base64:
                        candidates.append({"data_base64": data_base64, "mime_type": mime_type})
        images = message.get("images")
        if isinstance(images, list):
            for item in images:
                if isinstance(item, str) and item:
                    candidates.append({"url": item})
                    continue
                if not isinstance(item, dict):
                    continue
                image_url = item.get("image_url")
                url = item.get("url")
                if isinstance(image_url, dict):
                    nested_url = image_url.get("url")
                    if isinstance(nested_url, str) and nested_url:
                        url = nested_url
                elif isinstance(image_url, str) and image_url:
                    url = image_url
                data_base64 = item.get("data_base64") or item.get("b64_json")
                mime_type = item.get("mime_type") or "image/png"
                if isinstance(url, str) and url:
                    candidates.append({"url": url, "filename": item.get("filename")})
                elif isinstance(data_base64, str) and data_base64:
                    candidates.append(
                        {
                            "data_base64": data_base64,
                            "mime_type": mime_type,
                            "filename": item.get("filename"),
                        }
                    )
        return candidates

    def _normalize_response_message(
        self,
        response_obj: Dict[str, Any],
        *,
        state: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        choices = response_obj.get("choices")
        choice = choices[0] if isinstance(choices, list) and choices else {}
        message = choice.get("message") if isinstance(choice, dict) else {}
        if not isinstance(message, dict):
            message = {}

        context = self._request_context(state)
        multipart_out: List[Dict[str, Any]] = []
        metadata_patch: Dict[str, Any] = {}
        for idx, candidate in enumerate(self._extract_image_candidates(message)):
            stored = self._store_generated_image(
                candidate,
                state=state,
                context=context,
                index=idx,
            )
            metadata_patch = {
                **metadata_patch,
                **stored["session_metadata_patch"],
            }
            descriptor = stored["asset_descriptor"]
            multipart_out.append(
                {
                    "type": "image",
                    "content": {
                        "asset_ref": descriptor["asset_ref"],
                        "filename": descriptor["filename"],
                        "mime_type": descriptor["mime_type"],
                        "preview_data_base64": stored["preview_data_base64"],
                        "preview_mime_type": stored["preview_mime_type"],
                    },
                    "metadata": {
                        "download_plugin_id": "openrouter_image_generation_attachments",
                    },
                }
            )

        native_parts: List[Dict[str, Any]] = []
        text_parts = self._native_text_parts(message.get("content"))
        text_content = "\n".join(text_parts)
        if text_content:
            native_parts.append({"type": "text", "text": text_content})
        for part in multipart_out:
            native_parts.append(
                {
                    "type": "image_asset",
                    "asset_ref": part["content"]["asset_ref"],
                    "filename": part["content"].get("filename"),
                    "mime_type": part["content"].get("mime_type"),
                    "preview_data_base64": part["content"].get("preview_data_base64"),
                    "preview_mime_type": part["content"].get("preview_mime_type"),
                }
            )

        return {
            "role": "assistant",
            "content": native_parts,
            "_metadata": {
                "provider": _PROVIDER_REF_KEY,
                "response_id": response_obj.get("id"),
            },
        }, metadata_patch

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for native_idx, message in enumerate(native_messages):
            if not isinstance(message, dict):
                continue
            role = message.get("role")
            if not isinstance(role, str) or not role:
                continue
            content = message.get("content")
            text_parts: List[str] = []
            multipart_out: List[Dict[str, Any]] = []
            if role != "assistant":
                if isinstance(content, list):
                    for part in content:
                        if not isinstance(part, dict):
                            continue
                        part_type = part.get("type")
                        if part_type == "text":
                            text = part.get("text")
                            if isinstance(text, str) and text:
                                text_parts.append(text)
                        elif part_type == "image_url":
                            image_url = part.get("image_url")
                            url = image_url.get("url") if isinstance(image_url, dict) else None
                            if isinstance(url, str) and url:
                                multipart_out.append(
                                    {
                                        "type": "image",
                                        "content": {
                                            "url": url,
                                        },
                                        "metadata": {},
                                    }
                                )
                elif isinstance(content, str) and content:
                    text_parts.append(content)

                out.append(
                    {
                        "role": role,
                        "content": "\n".join(text_parts),
                        **({"multipartContent": multipart_out} if multipart_out else {}),
                        "metadata": {"native_indices": [native_idx]},
                    }
                )
                continue

            if isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    part_type = part.get("type")
                    if part_type == "text":
                        text = part.get("text")
                        if isinstance(text, str) and text:
                            text_parts.append(text)
                    elif part_type == "image_asset":
                        asset_ref = part.get("asset_ref")
                        if isinstance(asset_ref, dict):
                            preview_fields: Dict[str, Any] = {}
                            preview_data_base64 = part.get("preview_data_base64")
                            preview_mime_type = part.get("preview_mime_type")
                            if isinstance(preview_data_base64, str) and preview_data_base64:
                                preview_fields["preview_data_base64"] = preview_data_base64
                            if isinstance(preview_mime_type, str) and preview_mime_type:
                                preview_fields["preview_mime_type"] = preview_mime_type
                            multipart_out.append(
                                {
                                    "type": "image",
                                    "content": {
                                        "asset_ref": asset_ref,
                                        "filename": part.get("filename"),
                                        "mime_type": part.get("mime_type"),
                                        **preview_fields,
                                    },
                                    "metadata": {
                                        "download_plugin_id": "openrouter_image_generation_attachments",
                                    },
                                }
                            )
            out.append(
                {
                    "role": "assistant",
                    "content": "\n".join(text_parts),
                    **({"multipartContent": multipart_out} if multipart_out else {}),
                    "metadata": {"native_indices": [native_idx]},
                }
            )
        return out

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        request = state.get("request")
        if not isinstance(request, dict):
            raise RuntimeError("[openrouter_image_generation_provider] missing request in state")
        self._validate_v1_input(native_messages)
        payload = {
            **dict(request.get("payload") or {}),
            "messages": native_messages,
            "stream": False,
        }

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
                )
                runtime.add_closer(response.close)
                response.raise_for_status()
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
                            "OpenRouter image generation call failed: request ended without result"
                        )
                    continue
                if kind == "result":
                    response_obj = value
                    break
                exc = value
                if runtime.cancelled.is_set():
                    raise ProviderRequestCancelled(request_id) from exc
                raise RuntimeError(
                    f"OpenRouter image generation call failed: {exc}"
                ) from exc
        finally:
            self._clear_inflight(request_id, runtime)
            worker.join(timeout=1.0)

        assistant_message, metadata_patch = self._normalize_response_message(
            response_obj,
            state=state,
        )
        new_state = dict(state)
        if metadata_patch:
            new_state["session_metadata_patch"] = {
                **(
                    state.get("session_metadata_patch")
                    if isinstance(state.get("session_metadata_patch"), dict)
                    else {}
                ),
                **metadata_patch,
            }
        return [], [assistant_message], [*native_messages, assistant_message], new_state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Iterator[Dict[str, Any]]:
        _ = native_messages, state, request_id
        raise NotImplementedError(
            "[openrouter_image_generation_provider] V1 supports non-streaming requests only"
        )