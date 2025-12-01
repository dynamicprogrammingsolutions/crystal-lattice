"""
OpenRouter Provider Plugin

Provides access to multiple LLM providers through OpenRouter's unified API.
Compatible with OpenAI Chat Completions API format.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Tuple
import json

import requests

from agent_core.types import ProviderPlugin


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

    def get_ui_elements(self) -> List[Dict[str, Any]]:
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
        """Return capability tags for the OpenRouter provider.

        OpenRouter supports streaming, tool calling, and reasoning across
        multiple model providers.
        """
        tags: List[str] = ["provider:openrouter", "openrouter"]
        tags.append("supports_streaming")
        tags.append("supports_tools")
        tags.append("supports_reasoning")
        return tags

    # ---------- State lifecycle ----------
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
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

        return {
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
        return [{"role": m["role"], "content": m.get("content", "")} for m in messages]

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
            msg = {
                "role": m.get("role", "assistant"),
                "content": m.get("content", ""),
            }
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

    def _sanitize_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize provider-native history before sending to OpenRouter.

        - Drop top-level ``refusal`` fields when they are ``None`` (they are
          response-only metadata and not meaningful when replayed as history).
        - Drop ``index`` fields from ``tool_calls`` entries so streaming and
          non-streaming payloads share the same tool_calls shape.
        """
        sanitized: List[Dict[str, Any]] = []
        for msg in history:
            if not isinstance(msg, dict):
                sanitized.append(msg)
                continue
            m = dict(msg)
            if m.get("refusal") is None:
                m.pop("refusal", None)
            tool_calls = m.get("tool_calls")
            if isinstance(tool_calls, list):
                cleaned_tcs = []
                for tc in tool_calls:
                    if not isinstance(tc, dict):
                        cleaned_tcs.append(tc)
                        continue
                    cleaned_tcs.append({k: v for k, v in tc.items() if k != "index"})
                m["tool_calls"] = cleaned_tcs
            sanitized.append(m)
        return sanitized

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
            base_history = override if isinstance(override, list) else native_messages
            messages_to_send = self._sanitize_history(base_history)
            payload = {**request["payload"], "messages": messages_to_send, "stream": False}
            print("payload (non-streaming):", payload)
            r = requests.post(
                request["url"],
                json=payload,
                headers=request["headers"],
                timeout=request["timeout"],
            )
            r.raise_for_status()
            obj = r.json()
            print("response (non-streaming):", obj)
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
        return [message], [], [*native_messages, message], state


    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        request = state["request"]
        payload: Dict[str, Any] = {}
        try:
            self._validate_message_list(native_messages)
            override = request.get("messages")
            base_history = override if isinstance(override, list) else native_messages
            messages_to_send = self._sanitize_history(base_history)
            payload = {**request["payload"], "messages": messages_to_send, "stream": True}
            print("payload (stream):", payload)
            with requests.post(
                request["url"],
                json=payload,
                headers=request["headers"],
                timeout=request["timeout"],
                stream=True,
            ) as r:
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
            return dict(native_chunk["choices"][0])

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
        return [current_partial] if current_partial else [], [*native_messages, current_partial] if current_partial else native_messages, state

    def to_display_format(self, message: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return message
