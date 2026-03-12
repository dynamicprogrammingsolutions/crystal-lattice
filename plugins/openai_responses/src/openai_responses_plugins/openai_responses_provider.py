"""OpenAI Responses provider implementation.

Provider scope for subtask 030:
- provider identity/config/tags
- request initialization for /responses
- generic core <-> Responses-native conversion
- non-streaming SDK call path

Extension-owned business logic (tools/reasoning/usage/verbosity shaping and
extraction) is intentionally out of scope here.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterator, List, Optional, Tuple

from openai import OpenAI

from agent_core.types import ProviderPlugin


JsonObject = Dict[str, Any]
_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_DEFAULT_TIMEOUT = 60.0
_RAW_USAGE_METADATA_KEY = "_openai_responses_usage_raw"


class OpenAIResponsesProvider(ProviderPlugin):
    name: str = "openai_responses"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "model": {"type": "string", "required": True},
            "api_key": {
                "type": "string",
                "required": False,
                "description": "OpenAI API key (defaults to OPENAI_API_KEY env var).",
            },
            "base_url": {
                "type": "string",
                "required": False,
                "default": _DEFAULT_BASE_URL,
            },
            "timeout": {
                "type": "number",
                "required": False,
                "default": _DEFAULT_TIMEOUT,
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return []

    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        model = config.get("model")
        if isinstance(model, str) and model.strip():
            return [{"id": model.strip()}]
        return []

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        tags = [
            "provider:openai_responses",
            "openai_responses",
            "supports_streaming",
            "supports_reasoning",
            "supports_reasoning_effort",
            "supports_tools",
        ]

        model = config.get("model")
        if isinstance(model, str) and "gpt-5" in model:
            tags.append("supports_verbosity")

        return tags

    def _coerce_timeout(self, raw: Any) -> float:
        try:
            timeout = float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("[openai_responses_provider] timeout must be numeric") from exc
        if timeout <= 0:
            raise ValueError("[openai_responses_provider] timeout must be > 0")
        return timeout

    def _resolve_api_key(self, config: Dict[str, Any]) -> str:
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError(
                "[openai_responses_provider] api_key is required (config.api_key or OPENAI_API_KEY)"
            )
        return api_key.strip()

    def _resolve_model(self, config: Dict[str, Any]) -> str:
        model = config.get("model")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("[openai_responses_provider] model is required")
        return model.strip()

    def _resolve_base_url(self, config: Dict[str, Any]) -> str:
        base_url = config.get("base_url") or _DEFAULT_BASE_URL
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("[openai_responses_provider] base_url must be a non-empty string")
        return base_url.rstrip("/")

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(config, dict):
            raise TypeError("[openai_responses_provider] config must be a dict")

        model = self._resolve_model(config)
        api_key = self._resolve_api_key(config)
        base_url = self._resolve_base_url(config)
        timeout = self._coerce_timeout(config.get("timeout", _DEFAULT_TIMEOUT))

        normalized_config = {
            **config,
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
            "timeout": timeout,
        }

        client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        return {"config": normalized_config, "client": client}

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        cfg = state.get("config") or {}

        model = self._resolve_model(cfg)
        api_key = self._resolve_api_key(cfg)
        base_url = self._resolve_base_url(cfg)
        timeout = self._coerce_timeout(cfg.get("timeout", _DEFAULT_TIMEOUT))

        request = {
            "url": f"{base_url}/responses",
            "payload": {"model": model},
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            "timeout": timeout,
        }

        return list(native_messages), {**state, "request": request}

    def _native_internal_from_core_metadata(self, metadata: Any) -> Dict[str, Any]:
        if not isinstance(metadata, dict):
            return {}
        out = dict(metadata)
        out.pop("native_indices", None)
        return out

    def _core_metadata_from_native_internal(self, internal: Any) -> Dict[str, Any]:
        if not isinstance(internal, dict):
            return {}
        out = {
            key: value
            for key, value in internal.items()
            if key != "native_indices" and not str(key).startswith("_openai_responses_")
        }
        return out

    def _extract_text_and_images_from_content(
        self,
        content: Any,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        text_parts: List[str] = []
        images: List[Dict[str, Any]] = []

        if not isinstance(content, list):
            return "", images

        for part in content:
            if not isinstance(part, dict):
                continue

            ptype = part.get("type")
            if ptype in ("input_text", "output_text", "text"):
                text = part.get("text")
                if isinstance(text, str) and text:
                    text_parts.append(text)
                continue

            if ptype in ("input_image", "image_url"):
                image_url = part.get("image_url")
                if isinstance(image_url, dict):
                    image_url = image_url.get("url")
                if isinstance(image_url, str) and image_url:
                    images.append({"type": "image", "content": {"url": image_url}, "metadata": {}})

        return "\n".join(text_parts).strip(), images

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        native: List[Dict[str, Any]] = []

        for msg in messages:
            if not isinstance(msg, dict):
                continue

            # Allow explicit provider-native pass-through.
            if isinstance(msg.get("type"), str):
                native.append(msg)
                continue

            role = msg.get("role")
            metadata = msg.get("metadata")
            internal_md = self._native_internal_from_core_metadata(metadata)

            if role in ("system", "user", "assistant", "developer"):
                content = msg.get("content", "")
                text = content if isinstance(content, str) else ""

                parts: List[Dict[str, Any]] = []
                if text:
                    parts.append({"type": "input_text", "text": text})

                multipart = msg.get("multipartContent")
                if isinstance(multipart, list):
                    for part in multipart:
                        if not isinstance(part, dict) or part.get("type") != "image":
                            continue
                        pcontent = part.get("content")
                        if not isinstance(pcontent, dict):
                            continue
                        url = pcontent.get("url")
                        if isinstance(url, str) and url:
                            parts.append({"type": "input_image", "image_url": url})

                item: Dict[str, Any] = {
                    "type": "message",
                    "role": role,
                    "content": parts,
                }

                if role == "assistant" and isinstance(metadata, dict):
                    phase = metadata.get("phase")
                    if isinstance(phase, str) and phase:
                        item["phase"] = phase

                if internal_md:
                    item["_metadata"] = internal_md
                native.append(item)
                continue

            if role == "tool":
                tool_call_id = None
                if isinstance(metadata, dict):
                    tool_call_id = metadata.get("tool_call_id")
                if not isinstance(tool_call_id, str) or not tool_call_id:
                    raise ValueError(
                        "[openai_responses_provider] tool message requires metadata.tool_call_id"
                    )

                output = msg.get("content", "")
                if not isinstance(output, str):
                    try:
                        output = json.dumps(output, ensure_ascii=False)
                    except Exception:
                        output = ""

                item = {
                    "type": "function_call_output",
                    "call_id": tool_call_id,
                    "output": output,
                }

                internal_tool_md = dict(internal_md)
                internal_tool_md.pop("tool_call_id", None)
                if internal_tool_md:
                    item["_metadata"] = internal_tool_md

                native.append(item)
                continue

            raise ValueError(f"[openai_responses_provider] unsupported role: {role}")

        return native

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        owned_native_indices: set[int] = set()
        response_segments: Dict[str, List[int]] = {}
        response_order: List[str] = []
        response_candidates: Dict[str, List[int]] = {}

        def _record_response_index(response_id: Optional[str], native_index: int) -> None:
            if not isinstance(response_id, str) or not response_id:
                return
            bucket = response_segments.get(response_id)
            if bucket is None:
                response_segments[response_id] = [native_index]
                response_order.append(response_id)
            else:
                bucket.append(native_index)

        def _append_core_message(
            core_msg: Dict[str, Any],
            *,
            native_index: int,
            response_id: Optional[str],
        ) -> None:
            out.append(core_msg)
            owned_native_indices.add(native_index)
            if isinstance(response_id, str) and response_id:
                response_candidates.setdefault(response_id, []).append(len(out) - 1)

        def _merge_native_indices(core_index: int, indices: List[int]) -> None:
            raw_md = out[core_index].get("metadata") or {}
            md = dict(raw_md) if isinstance(raw_md, dict) else {}
            existing = md.get("native_indices")
            existing_indices = (
                [i for i in existing if isinstance(i, int)] if isinstance(existing, list) else []
            )
            merged = sorted(set(existing_indices + [i for i in indices if isinstance(i, int)]))
            md["native_indices"] = merged
            out[core_index] = {**out[core_index], "metadata": md}
            owned_native_indices.update(merged)

        for native_index, item in enumerate(native_messages):
            if not isinstance(item, dict):
                continue

            internal_md = self._core_metadata_from_native_internal(item.get("_metadata"))
            response_id = (
                internal_md.get("response_id") if isinstance(internal_md.get("response_id"), str) else None
            )
            _record_response_index(response_id, native_index)

            # Streaming partial compatibility: allow chat-like shape.
            if "type" not in item and ("role" in item or "content" in item):
                role = item.get("role") if isinstance(item.get("role"), str) else "assistant"
                content = item.get("content") if isinstance(item.get("content"), str) else ""
                md = dict(internal_md)
                md["native_indices"] = [native_index]
                _append_core_message(
                    {"role": role, "content": content, "metadata": md},
                    native_index=native_index,
                    response_id=response_id,
                )
                continue

            item_type = item.get("type")

            if item_type == "message":
                role = item.get("role") if isinstance(item.get("role"), str) else "assistant"
                text, images = self._extract_text_and_images_from_content(item.get("content"))

                md = dict(internal_md)
                phase = item.get("phase")
                if isinstance(phase, str) and phase:
                    md.setdefault("phase", phase)
                md["native_indices"] = [native_index]

                core_msg: Dict[str, Any] = {
                    "role": role,
                    "content": text,
                    "metadata": md,
                }
                if images:
                    core_msg["multipartContent"] = images

                _append_core_message(
                    core_msg,
                    native_index=native_index,
                    response_id=response_id,
                )
                continue

            if item_type == "function_call_output":
                call_id = item.get("call_id")
                if not isinstance(call_id, str) or not call_id:
                    continue

                output = item.get("output")
                if not isinstance(output, str):
                    try:
                        output = json.dumps(output, ensure_ascii=False)
                    except Exception:
                        output = ""

                md = dict(internal_md)
                md.setdefault("tool_call_id", call_id)
                md["native_indices"] = [native_index]

                _append_core_message(
                    {
                        "role": "tool",
                        "content": output,
                        "metadata": md,
                    },
                    native_index=native_index,
                    response_id=response_id,
                )

        for response_id in response_order:
            segment_indices = sorted(set(response_segments.get(response_id) or []))
            if not segment_indices:
                continue

            candidates = response_candidates.get(response_id) or []
            if candidates:
                owner_index: Optional[int] = None
                for core_index in reversed(candidates):
                    if out[core_index].get("role") == "assistant":
                        owner_index = core_index
                        break
                if owner_index is None:
                    owner_index = candidates[-1]

                _merge_native_indices(owner_index, segment_indices)
                continue

            # Preserve native ownership when a segment has only non-converted
            # item types (e.g. reasoning/function_call without tool output).
            out.append(
                {
                    "role": "assistant",
                    "content": "",
                    "metadata": {
                        "response_id": response_id,
                        "native_indices": segment_indices,
                    },
                }
            )
            owned_native_indices.update(segment_indices)

        dict_native_indices = {
            idx
            for idx, item in enumerate(native_messages)
            if isinstance(item, dict)
        }
        orphan_indices = sorted(dict_native_indices.difference(owned_native_indices))
        if not orphan_indices:
            return out

        owner_index: Optional[int] = None
        for core_index in range(len(out) - 1, -1, -1):
            if out[core_index].get("role") == "assistant":
                owner_index = core_index
                break
        if owner_index is None and out:
            owner_index = len(out) - 1

        if owner_index is None:
            out.append(
                {
                    "role": "assistant",
                    "content": "",
                    "metadata": {"native_indices": orphan_indices},
                }
            )
            return out

        _merge_native_indices(owner_index, orphan_indices)
        return out

    def _validate_native_item_list(self, items: List[Dict[str, Any]]) -> None:
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                raise RuntimeError(
                    f"[openai_responses_provider] invalid input item at index {idx}: expected dict"
                )
            item_type = item.get("type")
            if not isinstance(item_type, str) or not item_type:
                raise RuntimeError(
                    f"[openai_responses_provider] invalid input item at index {idx}: missing 'type'"
                )

    def _strip_internal_metadata(self, item: JsonObject) -> JsonObject:
        if "_metadata" not in item:
            return item
        return {k: v for k, v in item.items() if k != "_metadata"}

    def _sanitize_input_item(self, item: JsonObject) -> JsonObject:
        sanitized = dict(self._strip_internal_metadata(item))
        item_type = sanitized.get("type")

        if item_type == "compaction":
            compacted: JsonObject = {
                "type": "compaction",
                "encrypted_content": sanitized.get("encrypted_content", ""),
            }
            if isinstance(sanitized.get("id"), str) and sanitized.get("id"):
                compacted["id"] = sanitized["id"]
            return compacted

        for key in ("id", "status", "namespace", "phase"):
            sanitized.pop(key, None)

        content = sanitized.get("content")
        if isinstance(content, list):
            cleaned_content: List[Dict[str, Any]] = []
            for part in content:
                if not isinstance(part, dict):
                    continue
                cleaned_part = dict(part)
                cleaned_part.pop("annotations", None)
                cleaned_part.pop("logprobs", None)
                cleaned_content.append(cleaned_part)
            sanitized["content"] = cleaned_content

        return sanitized

    def _response_to_dict(self, response: Any) -> Dict[str, Any]:
        if isinstance(response, dict):
            return response
        if hasattr(response, "model_dump"):
            dumped = response.model_dump(mode="python")
            if isinstance(dumped, dict):
                return dumped
        raise RuntimeError("[openai_responses_provider] invalid SDK response payload")

    def _stream_event_to_dict(self, event: Any) -> Dict[str, Any]:
        if isinstance(event, dict):
            return event
        if hasattr(event, "model_dump"):
            dumped = event.model_dump(mode="python")
            if isinstance(dumped, dict):
                return dumped
        raise RuntimeError("[openai_responses_provider] invalid SDK stream event payload")

    def _safe_dict_payload(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        if hasattr(payload, "model_dump"):
            dumped = payload.model_dump(mode="python")
            if isinstance(dumped, dict):
                return dumped
        return {}

    def _terminal_stream_error_message(self, event: Dict[str, Any]) -> Optional[str]:
        event_type = event.get("type")
        if not isinstance(event_type, str):
            return None

        if event_type == "error":
            message = event.get("message") if isinstance(event.get("message"), str) else "unknown error"
            code = event.get("code") if isinstance(event.get("code"), str) else None
            details = f" code={code}" if code else ""
            return f"OpenAI Responses stream failed: terminal event error{details}: {message}"

        if event_type == "response.failed":
            response_obj = self._safe_dict_payload(event.get("response"))
            response_id = response_obj.get("id") if isinstance(response_obj.get("id"), str) else None
            error_obj = response_obj.get("error") if isinstance(response_obj.get("error"), dict) else {}
            code = error_obj.get("code") if isinstance(error_obj.get("code"), str) else None
            message = (
                error_obj.get("message")
                if isinstance(error_obj.get("message"), str)
                else "response failed"
            )
            context: List[str] = []
            if isinstance(response_id, str) and response_id:
                context.append(f"response_id={response_id}")
            if isinstance(code, str) and code:
                context.append(f"code={code}")
            suffix = f" ({', '.join(context)})" if context else ""
            return f"OpenAI Responses stream failed: terminal event response.failed{suffix}: {message}"

        if event_type == "response.incomplete":
            response_obj = self._safe_dict_payload(event.get("response"))
            response_id = response_obj.get("id") if isinstance(response_obj.get("id"), str) else None
            details_obj = (
                response_obj.get("incomplete_details")
                if isinstance(response_obj.get("incomplete_details"), dict)
                else {}
            )
            reason = details_obj.get("reason") if isinstance(details_obj.get("reason"), str) else None
            context: List[str] = []
            if isinstance(response_id, str) and response_id:
                context.append(f"response_id={response_id}")
            if isinstance(reason, str) and reason:
                context.append(f"reason={reason}")
            suffix = f" ({', '.join(context)})" if context else ""
            return f"OpenAI Responses stream failed: terminal event response.incomplete{suffix}"

        return None

    def _response_internal_metadata(self, response_obj: Dict[str, Any]) -> Dict[str, Any]:
        md: Dict[str, Any] = {}

        response_id = response_obj.get("id")
        if isinstance(response_id, str) and response_id:
            md["response_id"] = response_id

        # Keep raw usage available to extensions without exposing provider-owned
        # usage fields directly in core message metadata.
        usage = self._safe_dict_payload(response_obj.get("usage"))
        if usage:
            md[_RAW_USAGE_METADATA_KEY] = usage

        return md

    def _attach_internal_metadata_to_output(
        self,
        output_items: List[JsonObject],
        response_md: Dict[str, Any],
    ) -> List[JsonObject]:
        if not output_items:
            return list(output_items)

        annotated: List[JsonObject] = []
        for item in output_items:
            if not isinstance(item, dict):
                annotated.append(item)
                continue

            base_internal = item.get("_metadata")
            base_internal_dict = base_internal if isinstance(base_internal, dict) else {}

            if response_md:
                annotated.append({**item, "_metadata": {**base_internal_dict, **response_md}})
                continue

            annotated.append(item)
        return annotated

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        request = state.get("request")
        if not isinstance(request, dict):
            raise RuntimeError("[openai_responses_provider] missing request in state")

        payload = dict(request.get("payload") or {})

        override = request.get("messages")
        base_history = override if isinstance(override, list) else native_messages
        self._validate_native_item_list(base_history)

        input_items = [
            self._sanitize_input_item(item)
            for item in base_history
            if isinstance(item, dict)
        ]

        timeout = self._coerce_timeout(request.get("timeout", _DEFAULT_TIMEOUT))
        extra_headers = dict(request.get("headers") or {})

        client = state.get("client")
        if client is None:
            cfg = state.get("config") or {}
            client = OpenAI(
                api_key=self._resolve_api_key(cfg),
                base_url=self._resolve_base_url(cfg),
                timeout=timeout,
            )

        try:
            sdk_response = client.responses.create(  # type: ignore[union-attr]
                **{**payload, "input": input_items, "stream": False},
                extra_headers=extra_headers,
                timeout=timeout,
            )
        except Exception as exc:
            raise RuntimeError(f"OpenAI Responses call failed: {exc}") from exc

        response_obj = self._response_to_dict(sdk_response)

        output = response_obj.get("output")
        if not isinstance(output, list):
            raise RuntimeError("OpenAI Responses call failed: missing output list in response")

        output_items = [item for item in output if isinstance(item, dict)]

        response_md = self._response_internal_metadata(response_obj)
        annotated_output = self._attach_internal_metadata_to_output(output_items, response_md)

        return [], annotated_output, [*native_messages, *annotated_output], state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        request = state.get("request")
        if not isinstance(request, dict):
            raise RuntimeError("[openai_responses_provider] missing request in state")

        payload = dict(request.get("payload") or {})

        override = request.get("messages")
        base_history = override if isinstance(override, list) else native_messages
        self._validate_native_item_list(base_history)

        input_items = [
            self._sanitize_input_item(item)
            for item in base_history
            if isinstance(item, dict)
        ]

        timeout = self._coerce_timeout(request.get("timeout", _DEFAULT_TIMEOUT))
        extra_headers = dict(request.get("headers") or {})

        client = state.get("client")
        if client is None:
            cfg = state.get("config") or {}
            client = OpenAI(
                api_key=self._resolve_api_key(cfg),
                base_url=self._resolve_base_url(cfg),
                timeout=timeout,
            )

        try:
            sdk_stream = client.responses.create(  # type: ignore[union-attr]
                **{**payload, "input": input_items, "stream": True},
                extra_headers=extra_headers,
                timeout=timeout,
            )
        except Exception as exc:
            raise RuntimeError(f"OpenAI Responses stream failed: {exc}") from exc

        try:
            if hasattr(sdk_stream, "__enter__") and hasattr(sdk_stream, "__exit__"):
                with sdk_stream as stream:
                    for event in stream:
                        yield self._stream_event_to_dict(event)
                return

            for event in sdk_stream:
                yield self._stream_event_to_dict(event)
        except Exception as exc:
            raise RuntimeError(f"OpenAI Responses stream failed: {exc}") from exc

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        event = native_chunk if isinstance(native_chunk, dict) else {}
        event_type = event.get("type")

        new_state: Dict[str, Any] = {
            **state,
            "_openai_responses_stream_started": True,
        }

        terminal_error_message = self._terminal_stream_error_message(event)
        if terminal_error_message is not None:
            raise RuntimeError(terminal_error_message)

        emitted_partials: List[Dict[str, Any]] = []
        emitted_finals: List[Dict[str, Any]] = []

        if event_type == "response.output_text.delta":
            delta = event.get("delta")
            if isinstance(delta, str) and delta:
                emitted_partials.append({"role": "assistant", "content": delta})

        if event_type in (
            "response.reasoning_summary_text.delta",
            "response.reasoning_summary.delta",
            "response.reasoning.delta",
        ):
            delta = event.get("delta")
            if not isinstance(delta, str) and isinstance(delta, dict):
                raw_text = delta.get("text")
                delta = raw_text if isinstance(raw_text, str) else None
            if isinstance(delta, str) and delta:
                emitted_partials.append(
                    {"role": "assistant", "content": "", "_metadata": {"reasoning": delta}}
                )

        if event_type == "response.completed":
            response_payload = event.get("response")
            response_obj = self._response_to_dict(response_payload)

            output = response_obj.get("output")
            if not isinstance(output, list):
                raise RuntimeError(
                    "OpenAI Responses stream failed: missing output list in response.completed event"
                )

            output_items = [item for item in output if isinstance(item, dict)]
            response_md = self._response_internal_metadata(response_obj)
            emitted_finals = self._attach_internal_metadata_to_output(output_items, response_md)

            new_state = {
                **new_state,
                "_openai_responses_stream_completed": True,
            }

            if emitted_finals:
                return emitted_partials, emitted_finals, [*native_messages, *emitted_finals], new_state

        return emitted_partials, emitted_finals, list(native_messages), new_state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        started = bool(state.get("_openai_responses_stream_started"))
        completed = bool(state.get("_openai_responses_stream_completed"))
        if started and not completed:
            raise RuntimeError(
                "OpenAI Responses stream failed: stream ended without response.completed terminal event"
            )
        return [], list(native_messages), state
