"""OpenRouter Responses Provider Plugin.

Implements OpenRouter's `POST /responses` endpoint with SSE streaming.

Native history for this provider is stored as a list of Responses API items
(`"input"` items). Internal per-item metadata may be attached under the
special `"_metadata"` key and must be stripped out just before sending a
request.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import requests

from agent_core.tool_interop import (
    DEFAULT_TOOL_INTEROP_REGISTRY,
    OpenAIChatToolSchemaToOpenAIResponsesToolSchema,
    OpenAIResponsesToolCallToOpenAIChatToolCall,
    ToolInteropTarget,
)
from agent_core.types import ProviderPlugin
from agent_core.utils import get_logger


JsonObject = Dict[str, Any]


class OpenRouterResponsesProvider(ProviderPlugin):
    name: str = "openrouter_responses"
    version: str = "0.1.0"

    # ---------------------------------------------------------------------
    # Config/UI
    # ---------------------------------------------------------------------

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
            "debug_sse_path": {
                "type": "string",
                "required": False,
                "description": "Optional path to append raw SSE frames/events for debugging.",
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
                "label": "OpenRouter Model",
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

    # ---------------------------------------------------------------------
    # Models / capabilities
    # ---------------------------------------------------------------------

    def _fetch_models_from_api(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        base_url = (config.get("base_url") or "https://openrouter.ai/api/v1").rstrip("/")
        models_url = f"{base_url}/models"

        try:
            response = requests.get(models_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            models = data.get("data", [])
            if not isinstance(models, list):
                get_logger("openrouter_responses_provider").warning(
                    "Invalid models response format",
                    response=data,
                )
                return []
            return models
        except requests.RequestException as e:
            get_logger("openrouter_responses_provider").warning(
                "Failed to fetch models from OpenRouter API",
                error=str(e),
                url=models_url,
            )
            return []
        except Exception as e:
            get_logger("openrouter_responses_provider").warning(
                "Unexpected error fetching models",
                error=str(e),
            )
            return []

    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        all_models = self._fetch_models_from_api(config)
        if not all_models:
            return []
        return all_models

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        tags: List[str] = [
            "provider:openrouter_responses",
            "openrouter_responses",
            "supports_streaming",
        ]

        selected_id = config.get("model")
        if isinstance(selected_id, str) and selected_id:
            if models and isinstance(models, list):
                for m in models:
                    if isinstance(m, dict) and m.get("id") == selected_id:
                        supported_params = m.get("supported_parameters", [])
                        if isinstance(supported_params, list) and supported_params:
                            if "tools" in supported_params or "tool" in supported_params:
                                tags.append("supports_tools")
                            if "reasoning" in supported_params:
                                tags.append("supports_reasoning")
                                tags.append("supports_reasoning_effort")
                        break

            # OpenRouter model metadata is not always complete; add conservative
            # fallbacks for known OpenAI GPT-5 family capabilities.
            if "gpt-5" in selected_id:
                tags.append("supports_verbosity")
                tags.append("supports_reasoning")
                tags.append("supports_reasoning_effort")

        return tags

    # ---------------------------------------------------------------------
    # State lifecycle
    # ---------------------------------------------------------------------

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        config = state["config"]

        base_url = (config.get("base_url") or "https://openrouter.ai/api/v1").rstrip("/")
        api_key = config.get("api_key")
        model = config.get("model")
        timeout = float(config.get("timeout", 60))

        url = f"{base_url}/responses"
        payload: Dict[str, Any] = {"model": model}
        headers = {"Content-Type": "application/json"}

        if not api_key:
            raise ValueError("[openrouter_responses_provider] api_key is required")
        headers["Authorization"] = f"Bearer {api_key}"

        site_url = config.get("site_url")
        if site_url:
            headers["HTTP-Referer"] = site_url
        app_name = config.get("app_name")
        if app_name:
            headers["X-Title"] = app_name

        # Note: tool schema injection is normally handled by the
        # OpenRouterResponsesToolsExtension. Keep a provider-level fallback so
        # AgentCore usage without extensions still works.
        tools_value = config.get("tools")
        if isinstance(tools_value, list) and tools_value:
            payload_tools = DEFAULT_TOOL_INTEROP_REGISTRY.convert_schemas(
                [t for t in tools_value if isinstance(t, dict)],
                adapters=[OpenAIChatToolSchemaToOpenAIResponsesToolSchema()],
                target=ToolInteropTarget("openai.responses"),
            )
            payload["tools"] = payload_tools
            payload.setdefault("tool_choice", "auto")

        return native_messages, {
            **state,
            "request": {
                "url": url,
                "payload": payload,
                "headers": headers,
                "timeout": timeout,
            },
        }

    # ---------------------------------------------------------------------
    # Message conversion (core <-> provider-native Responses items)
    # ---------------------------------------------------------------------

    def _strip_internal_metadata(self, item: JsonObject) -> JsonObject:
        if not isinstance(item, dict):
            return {}
        if "_metadata" not in item:
            return item
        return {k: v for k, v in item.items() if k != "_metadata"}

    def _core_metadata_from_native_internal(self, internal: Any) -> Dict[str, Any]:
        if not isinstance(internal, dict) or not internal:
            return {}
        out = dict(internal)
        out.pop("native_indices", None)
        return out

    def _native_internal_from_core_metadata(self, metadata: Any) -> Dict[str, Any]:
        if not isinstance(metadata, dict) or not metadata:
            return {}
        out = dict(metadata)
        out.pop("native_indices", None)
        return out

    def _native_internal_from_core_metadata_excluding(
        self, metadata: Any, *, exclude_keys: List[str]
    ) -> Dict[str, Any]:
        internal = self._native_internal_from_core_metadata(metadata)
        for key in exclude_keys:
            internal.pop(key, None)
        return internal

    def _message_item_text_and_images(
        self, content: Any
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
                url = part.get("image_url")
                if isinstance(url, dict):
                    url = url.get("url")
                if isinstance(url, str) and url:
                    images.append({"type": "image", "content": {"url": url}, "metadata": {}})
                continue
        return "\n".join(text_parts).strip(), images

    def _assistant_candidate_from_response_item(
        self,
        item: JsonObject,
        *,
        native_index: int,
        internal_md: Dict[str, Any],
    ) -> Optional[JsonObject]:
        if item.get("type") != "message":
            return None

        role = item.get("role")
        if role is not None and role != "assistant":
            return None

        text, images = self._message_item_text_and_images(item.get("content"))
        metadata = dict(internal_md)
        phase = item.get("phase")
        if isinstance(phase, str) and phase:
            metadata["phase"] = phase

        candidate: JsonObject = {
            "role": "assistant",
            "content": text,
            "metadata": metadata,
            "_segment_native_index": native_index,
        }
        if images:
            candidate["multipartContent"] = images
        return candidate

    def _build_response_segment_assistant(
        self,
        segment: List[Tuple[int, JsonObject, Dict[str, Any]]],
    ) -> JsonObject:
        response_id: Optional[str] = None
        segment_indices: List[int] = []
        assistant_candidates: List[JsonObject] = []
        tool_calls: List[JsonObject] = []

        for native_index, item, internal_md in segment:
            segment_indices.append(native_index)
            if response_id is None:
                rid = internal_md.get("response_id")
                if isinstance(rid, str) and rid:
                    response_id = rid

            if item.get("type") == "function_call":
                try:
                    converted = DEFAULT_TOOL_INTEROP_REGISTRY.convert_tool_calls(
                        [item],
                        adapters=[OpenAIResponsesToolCallToOpenAIChatToolCall()],
                        target=ToolInteropTarget("openai.chat_completions"),
                    )
                except Exception:
                    converted = []
                if converted and isinstance(converted[0], dict):
                    tool_calls.append(converted[0])

            candidate = self._assistant_candidate_from_response_item(
                item,
                native_index=native_index,
                internal_md=internal_md,
            )
            if candidate is not None:
                assistant_candidates.append(candidate)

        canonical: Optional[JsonObject] = None
        for candidate in reversed(assistant_candidates):
            content = candidate.get("content")
            if isinstance(content, str) and content.strip():
                canonical = candidate
                break
        if canonical is None and assistant_candidates:
            for candidate in reversed(assistant_candidates):
                phase = (candidate.get("metadata") or {}).get("phase")
                if phase == "final_answer":
                    canonical = candidate
                    break
        if canonical is None and assistant_candidates:
            canonical = assistant_candidates[-1]

        phase_messages: List[JsonObject] = []
        for candidate in assistant_candidates:
            candidate_md = candidate.get("metadata") or {}
            phase_entry: JsonObject = {
                "content": candidate.get("content") if isinstance(candidate.get("content"), str) else "",
                "native_index": candidate.get("_segment_native_index"),
            }
            phase = candidate_md.get("phase")
            if isinstance(phase, str) and phase:
                phase_entry["phase"] = phase
            multipart = candidate.get("multipartContent")
            if isinstance(multipart, list) and multipart:
                phase_entry["multipartContent"] = multipart
            extra_md = {k: v for k, v in candidate_md.items() if k not in {"phase", "response_id"}}
            if extra_md:
                phase_entry["metadata"] = extra_md
            phase_messages.append(phase_entry)

        metadata: Dict[str, Any] = {}
        if canonical is not None:
            canonical_md = canonical.get("metadata")
            if isinstance(canonical_md, dict):
                metadata.update(canonical_md)
        if response_id:
            metadata["response_id"] = response_id
        metadata["native_indices"] = sorted(set(segment_indices))
        if phase_messages:
            metadata["phase_messages"] = phase_messages
        if tool_calls:
            metadata["tool_calls"] = tool_calls

        out: JsonObject = {
            "role": "assistant",
            "content": canonical.get("content") if canonical is not None and isinstance(canonical.get("content"), str) else "",
            "metadata": metadata,
        }
        if canonical is not None:
            multipart = canonical.get("multipartContent")
            if isinstance(multipart, list) and multipart:
                out["multipartContent"] = multipart
        return out

    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        native: List[Dict[str, Any]] = []
        for msg in messages:
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", "user")
            md = msg.get("metadata")

            if role in ("system", "user", "assistant"):
                content = msg.get("content", "")
                text = content if isinstance(content, str) else ""
                multipart = msg.get("multipartContent")

                parts: List[Dict[str, Any]] = []
                if text:
                    parts.append({"type": "input_text", "text": text})

                if isinstance(multipart, list) and multipart:
                    for part in multipart:
                        if not isinstance(part, dict) or part.get("type") != "image":
                            continue
                        part_content = part.get("content")
                        if not isinstance(part_content, dict):
                            continue
                        url = part_content.get("url")
                        if not isinstance(url, str) or not url:
                            data_base64 = part_content.get("data_base64")
                            mime_type = part_content.get("mime_type")
                            if isinstance(data_base64, str) and data_base64:
                                if not isinstance(mime_type, str) or not mime_type:
                                    raise ValueError(
                                        "[openrouter_responses_provider] image multipartContent part using data_base64 requires mime_type"
                                    )
                                url = f"data:{mime_type};base64,{data_base64}"
                        if isinstance(url, str) and url:
                            parts.append({"type": "input_image", "image_url": url})

                item: Dict[str, Any] = {"type": "message", "role": role, "content": parts}
                if role == "assistant" and isinstance(md, dict):
                    phase = md.get("phase")
                    if isinstance(phase, str) and phase:
                        item["phase"] = phase

                internal_md = self._native_internal_from_core_metadata_excluding(
                    md,
                    exclude_keys=[
                        # These are represented directly in Responses-native fields.
                        "phase",
                        "tool_calls",
                        "tool_call_id",
                    ],
                )

                if role == "assistant" and isinstance(md, dict):
                    tool_calls = md.get("tool_calls")
                    if isinstance(tool_calls, list) and tool_calls and not parts:
                        tool_items: List[Dict[str, Any]] = []
                        for tc in tool_calls:
                            converted = (
                                self._chat_tool_call_to_responses_function_call(tc)
                                if isinstance(tc, dict)
                                else None
                            )
                            if converted is None:
                                continue
                            if internal_md:
                                tool_items.append({**converted, "_metadata": internal_md})
                            else:
                                tool_items.append(converted)
                        native.extend(tool_items)
                        continue

                if internal_md:
                    item["_metadata"] = internal_md
                native.append(item)
                if role == "assistant" and isinstance(md, dict):
                    tool_calls = md.get("tool_calls")
                    if isinstance(tool_calls, list) and tool_calls:
                        # Append tool call items after the assistant message item.
                        tool_items: List[Dict[str, Any]] = []
                        for tc in tool_calls:
                            converted = (
                                self._chat_tool_call_to_responses_function_call(tc)
                                if isinstance(tc, dict)
                                else None
                            )
                            if converted is None:
                                continue
                            if internal_md:
                                tool_items.append({**converted, "_metadata": internal_md})
                            else:
                                tool_items.append(converted)
                        native.extend(tool_items)
                continue

            if role == "tool":
                tcid = md.get("tool_call_id") if isinstance(md, dict) else None
                if not isinstance(tcid, str) or not tcid:
                    tcid = f"call_{hash(str(msg)) % 1000000:06d}"
                output_val = msg.get("content", "")
                output = output_val if isinstance(output_val, str) else ""

                internal_md = self._native_internal_from_core_metadata_excluding(
                    md,
                    exclude_keys=[
                        # call_id is the native field.
                        "tool_call_id",
                    ],
                )
                item: Dict[str, Any] = {"type": "function_call_output", "call_id": tcid, "output": output}
                if internal_md:
                    item["_metadata"] = internal_md
                native.append(item)
                continue

        return native

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []

        response_items: Dict[str, List[JsonObject]] = {}
        current_segment: List[Tuple[int, JsonObject, Dict[str, Any]]] = []
        current_response_id: Optional[str] = None

        def _append_normalized(message: Dict[str, Any]) -> None:
            normalized.append(message)

        def _flush_response_segment() -> None:
            nonlocal current_segment, current_response_id
            if not current_segment:
                current_response_id = None
                return

            assistant_message = self._build_response_segment_assistant(current_segment)
            _append_normalized(assistant_message)

            for native_index, item, internal_md in current_segment:
                if item.get("type") != "function_call_output":
                    continue
                call_id = item.get("call_id")
                if not isinstance(call_id, str) or not call_id:
                    continue
                output = item.get("output")
                if not isinstance(output, str):
                    try:
                        output = json.dumps(output, ensure_ascii=False)
                    except Exception:
                        output = ""
                core_md = dict(internal_md)
                core_md.setdefault("tool_call_id", call_id)
                core_md["native_indices"] = [native_index]
                _append_normalized({"role": "tool", "content": output, "metadata": core_md})

            current_segment = []
            current_response_id = None

        for native_index, m in enumerate(native_messages):
            if not isinstance(m, dict):
                continue

            # Streaming partials may be emitted in a chat-like shape.
            if "type" not in m and ("role" in m and "content" in m):
                _flush_response_segment()
                role = m.get("role", "assistant")
                content = m.get("content", "")
                core_msg: Dict[str, Any] = {"role": role, "content": content if isinstance(content, str) else ""}
                internal_md = self._core_metadata_from_native_internal(m.get("_metadata"))
                core_msg["metadata"] = {**internal_md, "native_indices": [native_index]}
                normalized.append(core_msg)
                continue

            itype = m.get("type")
            internal_md = self._core_metadata_from_native_internal(m.get("_metadata"))
            rid = internal_md.get("response_id") if isinstance(internal_md.get("response_id"), str) else None
            if rid is not None:
                response_items.setdefault(rid, []).append(m)

            if rid:
                if current_segment and rid != current_response_id:
                    _flush_response_segment()
                current_response_id = rid
                current_segment.append((native_index, m, internal_md))
                continue

            _flush_response_segment()

            if itype == "message":
                role = m.get("role")
                if not isinstance(role, str) or not role:
                    role = "assistant"
                text, images = self._message_item_text_and_images(m.get("content"))
                core_md = dict(internal_md)
                phase = m.get("phase")
                if isinstance(phase, str) and phase:
                    core_md.setdefault("phase", phase)
                core_md.setdefault("native_indices", [native_index])
                core_msg: Dict[str, Any] = {"role": role, "content": text, "metadata": core_md}
                if images:
                    core_msg["multipartContent"] = images
                normalized.append(core_msg)
                continue

            if itype == "function_call_output":
                call_id = m.get("call_id")
                if not isinstance(call_id, str) or not call_id:
                    continue
                output = m.get("output")
                if not isinstance(output, str):
                    try:
                        output = json.dumps(output, ensure_ascii=False)
                    except Exception:
                        output = ""
                core_md = dict(internal_md)
                core_md.setdefault("tool_call_id", call_id)
                core_md.setdefault("native_indices", [native_index])
                normalized.append({"role": "tool", "content": output, "metadata": core_md})
                continue

            # Ignore other items (e.g. reasoning). They remain in native history.

        _flush_response_segment()

        # UI metadata required by terminal/mobile.
        # Derive from Responses-native items (single source of truth).
        for rid, items in response_items.items():
            citations: List[JsonObject] = []
            try:
                citations = self._extract_url_citations(items)
            except Exception:
                citations = []

            reasoning_summary = ""
            try:
                reasoning_items = self._extract_reasoning_items(items)
                reasoning_summary = self._summarize_reasoning_items(reasoning_items)
            except Exception:
                reasoning_summary = ""

            candidate_indices = [
                idx
                for idx, msg in enumerate(normalized)
                if msg.get("role") == "assistant" and (msg.get("metadata") or {}).get("response_id") == rid
            ]
            if not candidate_indices:
                continue

            chosen_index = self._select_response_primary_assistant_message_index(
                normalized,
                candidate_indices,
                items,
            )

            base = dict(normalized[chosen_index])
            md = dict(base.get("metadata") or {})
            if citations:
                md["url_citations"] = citations
            if reasoning_summary:
                md.setdefault("reasoning", reasoning_summary)
            normalized[chosen_index] = {**base, "metadata": md}

        return normalized

    def _select_response_primary_assistant_message_index(
        self,
        normalized: List[JsonObject],
        candidate_indices: List[int],
        response_items: List[JsonObject],
    ) -> int:
        for idx in reversed(candidate_indices):
            md = normalized[idx].get("metadata") or {}
            if isinstance(md, dict) and md.get("phase") == "final_answer":
                return idx

        response_has_tool_calls = any(
            isinstance(item, dict) and item.get("type") == "function_call"
            for item in response_items
        )
        if response_has_tool_calls:
            for idx in reversed(candidate_indices):
                md = normalized[idx].get("metadata") or {}
                if not isinstance(md, dict):
                    continue
                tool_calls = md.get("tool_calls")
                if isinstance(tool_calls, list) and tool_calls:
                    return idx

        for idx in reversed(candidate_indices):
            content = normalized[idx].get("content")
            if isinstance(content, str) and content.strip():
                return idx

        return candidate_indices[-1]

    # ---------------------------------------------------------------------
    # HTTP helpers
    # ---------------------------------------------------------------------

    def _validate_message_list(self, history: List[Dict[str, Any]]) -> None:
        for idx, item in enumerate(history):
            if not isinstance(item, dict):
                raise RuntimeError(
                    f"[openrouter_responses_provider] invalid item at index {idx}: expected dict, got {type(item).__name__} -> {item}"
                )
            itype = item.get("type")
            if not isinstance(itype, str) or not itype:
                raise RuntimeError(
                    f"[openrouter_responses_provider] invalid item at index {idx}: missing 'type' -> {json.dumps(item, ensure_ascii=False)}"
                )

    def _chat_tool_call_to_responses_function_call(self, tool_call: JsonObject) -> Optional[JsonObject]:
        if not isinstance(tool_call, dict):
            return None
        if tool_call.get("type") != "function":
            return None
        call_id = tool_call.get("id")
        fn = tool_call.get("function")
        if not isinstance(call_id, str) or not call_id:
            return None
        if not isinstance(fn, dict):
            return None
        name = fn.get("name")
        arguments = fn.get("arguments")
        if not isinstance(name, str) or not name:
            return None
        if not isinstance(arguments, str):
            try:
                arguments = json.dumps(arguments, ensure_ascii=False)
            except Exception:
                arguments = "{}"
        return {
            "type": "function_call",
            "call_id": call_id,
            "name": name,
            "arguments": arguments,
        }

    def _build_request_body(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        request = state["request"]
        override = request.get("messages")
        items = override if isinstance(override, list) else native_messages
        self._validate_message_list(items)
        items_to_send = [self._strip_internal_metadata(m) for m in items if isinstance(m, dict)]
        return {**request["payload"], "input": items_to_send}

    def _response_internal_metadata(self, resp: JsonObject) -> Dict[str, Any]:
        md: Dict[str, Any] = {}
        rid = resp.get("id")
        if isinstance(rid, str) and rid:
            md["response_id"] = rid
        usage = resp.get("usage")
        if isinstance(usage, dict) and usage:
            md["usage"] = usage
        return md

    def _select_primary_output_item_index(self, output: List[JsonObject]) -> Optional[int]:
        if not output:
            return None

        # Prefer a phased assistant message with final_answer.
        for idx in range(len(output) - 1, -1, -1):
            item = output[idx]
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            role = item.get("role")
            if role is not None and role != "assistant":
                continue
            if item.get("phase") == "final_answer":
                return idx

        # Otherwise prefer the last assistant message item.
        for idx in range(len(output) - 1, -1, -1):
            item = output[idx]
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            role = item.get("role")
            if role is None or role == "assistant":
                return idx

        # Fallback: last item.
        return len(output) - 1

    def _attach_internal_metadata_to_output(
        self, output: List[JsonObject], md: Dict[str, Any]
    ) -> List[JsonObject]:
        if not output or not md:
            return list(output)

        response_id = md.get("response_id")
        out: List[JsonObject] = []
        for item in output:
            if not isinstance(item, dict):
                out.append(item)
                continue
            if isinstance(response_id, str) and response_id:
                base_internal = item.get("_metadata")
                base_internal_dict = base_internal if isinstance(base_internal, dict) else {}
                out.append({**item, "_metadata": {**base_internal_dict, "response_id": response_id}})
            else:
                out.append(item)

        md_primary = {k: v for k, v in md.items() if k != "response_id"}
        if not md_primary:
            return out

        idx = self._select_primary_output_item_index(out)
        if idx is None:
            return out

        final: List[JsonObject] = []
        for i, item in enumerate(out):
            if i != idx or not isinstance(item, dict):
                final.append(item)
                continue
            base_internal = item.get("_metadata")
            base_internal_dict = base_internal if isinstance(base_internal, dict) else {}
            final.append({**item, "_metadata": {**base_internal_dict, **md_primary}})
        return final

    # ---------------------------------------------------------------------
    # API calls
    # ---------------------------------------------------------------------

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        request = state["request"]
        payload: Dict[str, Any] = {}
        logger = get_logger("openrouter_responses_provider")

        try:
            payload = {**self._build_request_body(native_messages, state), "include": ['reasoning.encrypted_content'], "stream": False}
            logger.info(
                "sending request",
                payload=str({**payload, "input": "stripped", "tools": "stripped"}),
            )
            r = requests.post(
                request["url"],
                json=payload,
                headers=request["headers"],
                timeout=request["timeout"],
            )
            r.encoding = "utf-8"
            if r.status_code != 200:
                try:
                    err_detail = r.json()
                except Exception:
                    err_detail = r.text
                raise RuntimeError(
                    f"OpenRouter /responses call failed: {r.status_code} {r.reason}. Error: {err_detail}"
                )
            obj = r.json()
        except requests.RequestException as e:
            raise RuntimeError(f"OpenRouter /responses call failed: {e}") from e

        output = obj.get("output")
        output_items = output if isinstance(output, list) else []
        output_items = [it for it in output_items if isinstance(it, dict)]
        md = self._response_internal_metadata(obj if isinstance(obj, dict) else {})
        annotated = self._attach_internal_metadata_to_output(output_items, md)

        return [], annotated, [*native_messages, *annotated], state

    def stream_api(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        request = state["request"]
        logger = get_logger("openrouter_responses_provider")

        cfg = state.get("config") or {}
        debug_path = cfg.get("debug_sse_path")
        debug_file: Optional[Path] = None
        if isinstance(debug_path, str) and debug_path:
            debug_file = Path(debug_path)

        payload: Dict[str, Any] = {**self._build_request_body(native_messages, state), "include": ['reasoning.encrypted_content'], "stream": True}
        logger.info(
            "sending streaming request",
            payload=str({**payload, "input": "stripped", "tools": "stripped"}),
        )

        logger.debug(
            "sending streaming request (full payload)",
            payload=str({**payload}),
        )

        try:
            with requests.post(
                request["url"],
                json=payload,
                headers=request["headers"],
                timeout=request["timeout"],
                stream=True,
            ) as r:
                r.encoding = "utf-8"
                if r.status_code != 200:
                    try:
                        error_detail = r.json()
                    except Exception:
                        error_detail = r.text
                    raise RuntimeError(
                        f"OpenRouter /responses stream failed: {r.status_code} {r.reason}. Error: {error_detail}"
                    )

                dbg_handle = None
                try:
                    if debug_file is not None:
                        debug_file.parent.mkdir(parents=True, exist_ok=True)
                        dbg_handle = debug_file.open("a", encoding="utf-8")
                        dbg_handle.write("\n--- stream start ---\n")

                    for event_name, data, raw in self._iter_sse_frames(r.iter_lines(decode_unicode=True)):
                        if dbg_handle is not None:
                            dbg_handle.write("\n--- frame ---\n")
                            for ln in raw:
                                dbg_handle.write(ln)
                                dbg_handle.write("\n")
                        if not data:
                            continue
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(obj, dict) and event_name and "type" not in obj:
                            obj["_sse_event"] = event_name
                        if dbg_handle is not None:
                            try:
                                dbg_handle.write("parsed: ")
                                dbg_handle.write(json.dumps(obj, ensure_ascii=False))
                                dbg_handle.write("\n")
                            except Exception:
                                pass
                        yield obj
                finally:
                    if dbg_handle is not None:
                        dbg_handle.write("\n--- stream end ---\n")
                        dbg_handle.close()
        except requests.RequestException as e:
            raise RuntimeError(f"OpenRouter /responses stream failed: {e}") from e

    def _iter_sse_frames(self, lines: Iterator[str]) -> Iterator[Tuple[Optional[str], str, List[str]]]:
        event_name: Optional[str] = None
        data_lines: List[str] = []
        raw_lines: List[str] = []

        for line in lines:
            if line is None:
                continue
            if line == "":
                if not raw_lines and not data_lines and event_name is None:
                    continue
                data = "\n".join(data_lines).strip() if data_lines else ""
                yield event_name, data, list(raw_lines)
                event_name = None
                data_lines = []
                raw_lines = []
                continue

            raw_lines.append(line)
            if line.startswith(":"):
                continue
            if line.startswith("event:"):
                event_name = line[len("event:") :].strip() or None
                continue
            if line.startswith("data:"):
                data_lines.append(line[len("data:") :].lstrip())
                continue

        if raw_lines or data_lines or event_name is not None:
            data = "\n".join(data_lines).strip() if data_lines else ""
            yield event_name, data, list(raw_lines)

    # ---------------------------------------------------------------------
    # Streaming reduction
    # ---------------------------------------------------------------------

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        event = native_chunk if isinstance(native_chunk, dict) else {}
        etype = event.get("type") or event.get("_sse_event")
        emitted_partials: List[Dict[str, Any]] = []
        emitted_finals: List[Dict[str, Any]] = []
        updated_native = native_messages

        if etype == "response.output_text.delta":
            delta = event.get("delta")
            if isinstance(delta, str) and delta:
                emitted_partials.append({"role": "assistant", "content": delta})

        if etype in (
            "response.reasoning_summary_text.delta",
            "response.reasoning_summary.delta",
            "response.reasoning.delta",
        ):
            delta = event.get("delta")
            if isinstance(delta, str) and delta:
                emitted_partials.append({"role": "assistant", "content": "", "_metadata": {"reasoning": delta}})

        if etype in ("response.completed", "response.done"):
            resp = event.get("response")
            if isinstance(resp, dict):
                output = resp.get("output")
                output_items = output if isinstance(output, list) else []
                output_items = [it for it in output_items if isinstance(it, dict)]
                md = self._response_internal_metadata(resp)
                annotated = self._attach_internal_metadata_to_output(output_items, md)
                if annotated:
                    emitted_finals.extend(annotated)
                    updated_native = [*native_messages, *annotated]

        return emitted_partials, emitted_finals, updated_native, state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return [], native_messages, state

    # ---------------------------------------------------------------------
    # Response JSON parsing
    # ---------------------------------------------------------------------

    def _extract_phase_message_items(self, output: List[JsonObject]) -> List[JsonObject]:
        """Extract assistant message phases as compact records.

        OpenRouter GPT-5.4 may emit multiple assistant message output items in
        the same response, tagged with a `phase` (e.g. `commentary` vs
        `final_answer`). We persist a compact representation so it can be
        passed back into subsequent `/responses` requests.
        """

        items: List[JsonObject] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "message":
                continue
            role = item.get("role")
            if role is not None and role != "assistant":
                continue
            phase = item.get("phase")
            if not isinstance(phase, str) or not phase:
                continue

            content = item.get("content")
            if not isinstance(content, list):
                continue
            text_parts: List[str] = []
            for part in content:
                if not isinstance(part, dict):
                    continue
                ptype = part.get("type")
                if ptype not in ("output_text", "text"):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text:
                    text_parts.append(text)
            text = "\n".join(text_parts).strip()
            if not text:
                continue

            entry: JsonObject = {"phase": phase, "text": text}
            mid = item.get("id")
            if isinstance(mid, str) and mid:
                entry["id"] = mid
            status = item.get("status")
            if isinstance(status, str) and status:
                entry["status"] = status
            items.append(entry)
        return items

    def _extract_reasoning_items(self, output: List[JsonObject]) -> List[JsonObject]:
        items: List[JsonObject] = []
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "reasoning":
                continue
            entry: JsonObject = {}
            rid = item.get("id")
            if isinstance(rid, str) and rid:
                entry["id"] = rid
            phase = item.get("phase")
            if isinstance(phase, str) and phase:
                entry["phase"] = phase
            status = item.get("status")
            if isinstance(status, str) and status:
                entry["status"] = status
            summary = item.get("summary")
            if isinstance(summary, list) and summary:
                entry["summary"] = summary
            encrypted = item.get("encrypted_content")
            if isinstance(encrypted, str) and encrypted:
                entry["encrypted_content"] = encrypted
            fmt = item.get("format")
            if isinstance(fmt, str) and fmt:
                entry["format"] = fmt
            if entry:
                items.append(entry)
        return items

    def _summarize_reasoning_items(self, reasoning_items: List[JsonObject]) -> str:
        parts: List[str] = []
        for item in reasoning_items:
            summary = item.get("summary")
            if not isinstance(summary, list):
                continue
            for block in summary:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "summary_text":
                    continue
                text = block.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        return "\n\n".join(parts).strip()

    def _extract_url_citations(self, output: List[JsonObject]) -> List[JsonObject]:
        citations: List[JsonObject] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict) or part.get("type") != "output_text":
                    continue
                anns = part.get("annotations")
                if not isinstance(anns, list):
                    continue
                for ann in anns:
                    if not isinstance(ann, dict) or ann.get("type") != "url_citation":
                        continue
                    # OpenRouter may emit either a nested shape:
                    #   {"type":"url_citation","url_citation":{...}}
                    # or a flat shape:
                    #   {"type":"url_citation","url":...,"title":...,...}
                    payload = ann.get("url_citation") if isinstance(ann.get("url_citation"), dict) else ann
                    if not isinstance(payload, dict):
                        continue
                    entry: JsonObject = {}
                    url = payload.get("url")
                    if isinstance(url, str) and url:
                        entry["url"] = url
                    title = payload.get("title")
                    if isinstance(title, str) and title:
                        entry["title"] = title
                    snippet = payload.get("content")
                    if isinstance(snippet, str) and snippet:
                        entry["content"] = snippet
                    start = payload.get("start_index")
                    end = payload.get("end_index")
                    if isinstance(start, int):
                        entry["start_index"] = start
                    if isinstance(end, int):
                        entry["end_index"] = end
                    if entry and not any(
                        entry.get("url") == e.get("url")
                        and entry.get("start_index") == e.get("start_index")
                        and entry.get("end_index") == e.get("end_index")
                        for e in citations
                    ):
                        citations.append(entry)
        return citations
