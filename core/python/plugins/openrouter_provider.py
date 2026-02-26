"""
OpenRouter Provider Plugin

Provides access to multiple LLM providers through OpenRouter's unified API.
Compatible with OpenAI Chat Completions API format.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Tuple
import json

import requests

from agent_core.types import ProviderPlugin
from agent_core.utils import get_logger


class OpenRouterProvider(ProviderPlugin):
    name: str = "openrouter"
    version: str = "0.1.0"

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
        return [
            {
                "ui_type": "config",
                "type": "string",
                "key": "model",
                "label": "Openrouter Model ID",
            },
            {
                "ui_type": "composer_attachment",
                "attachment_type": "image",
                "supports_url": True,
                "supported_file_types": ["png", "jpg", "jpeg", "webp", "gif"],
                "display_placement": "below",
                "label": "Image",
            },
        ]

    # ---------- Models / capabilities ----------
    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch models from OpenRouter API with full capability data.
        
        Returns model descriptors with supported_parameters for capability detection.
        Falls back to configured model if API call fails.
        """
        base_url = config.get("base_url", "https://openrouter.ai/api/v1").rstrip("/")
        
        try:
            response = requests.get(f"{base_url}/models", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            get_logger("openrouter_provider").warning(
                "Failed to fetch models from API", error=str(e)
            )
            # Fallback: return configured model without capability data
            model = config.get("model")
            if isinstance(model, str) and model:
                return [{"id": model}]
            return []

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability tags including model-specific features.
        
        Detects capabilities from the model's supported_parameters array.
        Falls back to basic capabilities if model data is unavailable.
        """
        tags: List[str] = ["provider:openrouter", "openrouter", "supports_streaming"]
        
        # Find current model in models list
        current_model_id = config.get("model")
        current_model = None
        for model in models:
            if model.get("id") == current_model_id:
                current_model = model
                break
        
        if current_model:
            supported_params = current_model.get("supported_parameters", [])
            
            # Add capability tags based on supported_parameters
            if "tools" in supported_params:
                tags.append("supports_tools")
            
            if "reasoning" in supported_params or "include_reasoning" in supported_params:
                tags.append("supports_reasoning")
                
                # Check if model natively supports reasoning_effort parameter
                # Only 5 models have this: Z.AI GLM, OpenAI OSS, Qwen, Auto Router
                if "reasoning_effort" in supported_params:
                    tags.append("supports_reasoning_effort")
            
            if "verbosity" in supported_params:
                tags.append("supports_verbosity")
        else:
            # Fallback: assume basic capabilities when model data unavailable
            tags.extend(["supports_tools", "supports_reasoning"])
        
        return tags

    # ---------- State lifecycle ----------
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
            content = msg.get("content", "")
            if not isinstance(content, str):
                content = ""

            multipart = msg.get("multipartContent")
            if not isinstance(multipart, list) or not multipart:
                native.append({"role": role, "content": content})
                continue

            parts: List[Dict[str, Any]] = [{"type": "text", "text": content}]
            for part in multipart:
                if not isinstance(part, dict):
                    continue

                part_type = part.get("type")
                part_content = part.get("content")
                if part_type != "image":
                    raise ValueError(
                        f"[openrouter_provider] unsupported multipartContent part type: {part_type!r}"
                    )
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

                parts.append({"type": "image_url", "imageUrl": {"url": url}})

            native.append({"role": role, "content": parts})

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
        for m in native_messages:
            if not isinstance(m, dict):
                continue
            if not ("role" in m or "content" in m):
                continue

            role = m.get("role", "assistant")
            content = m.get("content", "")

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
                if multipart_out:
                    msg["multipartContent"] = multipart_out

            else:
                msg["content"] = content if isinstance(content, str) else ""

            normalized.append({**msg, "metadata": {}})

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
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        request = state["request"]
        payload: Dict[str, Any] = {}
        try:
            self._validate_message_list(native_messages)
            override = request.get("messages")
            messages = override if isinstance(override, list) else native_messages
            payload = {**request["payload"], "messages": messages, "stream": False}
            try:
                payload_preview = json.dumps(payload, ensure_ascii=False)
            except Exception:  # pragma: no cover - defensive
                payload_preview = str(payload)
            if len(payload_preview) > 2000:
                payload_preview = payload_preview[:2000] + "...<truncated>"

            get_logger("openrouter_provider").info(
                "sending request",
                payload=payload_preview,
            )
            r = requests.post(
                request["url"],
                json=payload,
                headers=request["headers"],
                timeout=request["timeout"],
            )
            # OpenRouter responses are JSON and should always be UTF-8. Some
            # environments mis-detect the charset (for example defaulting to
            # ISO-8859-1), which corrupts non-ASCII characters like en/em
            # dashes inside tool arguments. Force UTF-8 before JSON parsing
            # so that we never depend on the response headers for encoding.
            r.encoding = "utf-8"
            obj = r.json()
            # Debug log full non-streaming response for investigation
            try:  # pragma: no cover - debug aid
                get_logger("openrouter_provider").info(
                    "received response",
                    response=obj,
                )
            except Exception:
                # Logging must never break the provider
                pass
        except requests.RequestException as e:
            # Debug payload and error details for investigation (no auth headers included)
            try:  # pragma: no cover - debug aid
                debug_payload = json.dumps(payload, ensure_ascii=False)[:2000]
                print("[openrouter_provider] call_api error payload:", debug_payload)
            except Exception:
                print("[openrouter_provider] call_api error payload: <unserializable>")
            resp = getattr(e, "response", None)
            if resp is not None:
                try:
                    err_detail = resp.json()
                except Exception:
                    err_detail = resp.text
                print("[openrouter_provider] call_api error response:", err_detail)
            raise RuntimeError(f"OpenRouter API call failed: {e}") from e

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

        return [message], [], [*native_messages, message], state


    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        request = state["request"]
        payload: Dict[str, Any] = {}
        try:
            self._validate_message_list(native_messages)
            override = request.get("messages")
            messages = override if isinstance(override, list) else native_messages
            payload = {**request["payload"], "messages": messages, "stream": True}
            try:
                payload_preview = json.dumps(payload, ensure_ascii=False)
            except Exception:  # pragma: no cover - defensive
                payload_preview = str(payload)
            if len(payload_preview) > 2000:
                payload_preview = payload_preview[:2000] + "...<truncated>"
            get_logger("openrouter_provider").info("sending request", payload=payload_preview)
            with requests.post(
                request["url"],
                json=payload,
                headers=request["headers"],
                timeout=request["timeout"],
                stream=True,
            ) as r:
                # See call_api above: OpenRouter uses UTF-8 JSON for
                # streaming chunks as well. Force UTF-8 so that
                # iter_lines(decode_unicode=True) does not incorrectly
                # decode bytes as ISO-8859-1 and garble characters like
                # em dashes in tool_call.function.arguments.
                r.encoding = "utf-8"
                if r.status_code != 200:
                    # Get error details before raising
                    try:
                        error_detail = r.json()
                    except Exception:
                        error_detail = r.text
                    raise RuntimeError(
                        f"OpenRouter stream failed: {r.status_code} {r.reason}. "
                        f"Error: {error_detail}"
                    )
                for line in r.iter_lines(decode_unicode=True):
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
                    yield obj
        except requests.RequestException as e:
            raise RuntimeError(f"OpenRouter stream failed: {e}") from e


    # ---------- Helpers (default/general implementations) ----------
    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract a provider-native delta dictionary from a streaming chunk.
        Return the first choice if present.
        """
        if "choices" in native_chunk and native_chunk["choices"]:
            return native_chunk["choices"][0]

        return {}

    def process_delta(self, delta: Dict[str, Any], accumulated) -> Tuple[Dict[str, Any],Dict[str, Any]]:
        """
        Reduce a delta dict into a new partial accumulator, and optionally a final.
        Returns (partial_message_or_none, final_message_or_none, new_accumulated).
        """
        content = delta.get("message") or delta.get("delta") or None
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
            **{key: ((current.get(key) or "") + (delta.get(key) or "")) for key in accumulate},
        }

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        #print("chunk:", native_chunk)
        partial, accumulated = self.process_delta(
            delta=self.extract_delta(native_chunk), accumulated=state.get("partial", {})
        )
        new_state = {**state, "partial": accumulated}
        return_values = [partial] if partial else [], [], native_messages, new_state
        return  return_values

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        current_partial = state.get("partial", None)
        finals = [current_partial] if current_partial else []
        full_history = [*native_messages, current_partial] if current_partial else native_messages
        return finals, full_history, state

    def to_display_format(self, message: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return message
