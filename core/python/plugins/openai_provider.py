"""
OpenAI-Compatible Provider Plugin (plugins/providers/openai/python/openai_provider.py)

Minimal provider for OpenAI-compatible Chat Completions endpoints (e.g., Ollama at /v1).
Loads configuration only from the provided config dict (no environment variable usage).
"""

from __future__ import annotations

from typing import List, Any, Dict, Iterator, List, Tuple, Optional
import json

import requests

from agent_core.types import ProviderPlugin

class OpenAICompatibleProvider(ProviderPlugin):
    name: str = "openai_compatible"
    version: str = "0.3.0"

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

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        # No UI elements
        return []

    # ---------- State lifecycle ----------
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Provider state is an opaque dict owned by the provider and its
        # extensions/features. This implementation only needs configuration,
        # request metadata, and a partial accumulator for streaming.
        return {"config": config}

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:

        config = state["config"]
        
        base_url = (config.get("base_url") or "https://api.openai.com/v1").rstrip("/")
        api_key = config.get("api_key")
        model = config.get("model")
        timeout = float(config.get("timeout", 60))

        url = f"{base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        return {
            **state,
            "request": {
                "url": url,
                "payload": payload,
                "headers": headers,
                "timeout": timeout,
            },
            "partial": None
        }

    # ---------- Message conversion ----------
    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return [{"role": m["role"], "content": m.get("content", "")} for m in messages]

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Convert provider-native finals to core messages. Expects message-like dicts
        (e.g., {"role": ..., "content": ...}). Non-message shapes are ignored.
        """
        normalized: List[Dict[str, Any]] = []
        for m in native_messages:
            if not isinstance(m, dict):
                continue
            if not ("role" in m or "content" in m or "reasoning" in m):
                # Ignore non-message shapes (like full completion objects)
                continue
            msg = {
                "role": m.get("role", "assistant"),
                "content": m.get("content", ""),
            }
            if "reasoning" in m:
                msg["reasoning"] = m.get("reasoning")
            normalized.append({**msg, "metadata": {}})
        return normalized

    # ---------- Core API calls ----------
    def _validate_message_list(self, history: List[Dict[str, Any]]) -> None:
        """Validate that every item is a message-shaped dict with role and content.
        Other keys are allowed. Raise with details if invalid.
        """
        for idx, item in enumerate(history):
            if not isinstance(item, dict):
                raise RuntimeError(f"[openai_provider] invalid message at index {idx}: expected dict, got {type(item).__name__} -> {item}")
            if "role" not in item or "content" not in item:
                raise RuntimeError(
                    f"[openai_provider] invalid message at index {idx}: missing 'role' or 'content' -> {json.dumps(item, ensure_ascii=False)}"
                )

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:        
        request = state["request"]
        try:
            # Validate native_messages are proper message objects
            self._validate_message_list(native_messages)
            # Allow features to override the message history for this
            # request by placing a rendered list under
            # state["request"]["messages"].
            override = request.get("messages")
            messages_to_send = override if isinstance(override, list) else native_messages
            r = requests.post(
                request["url"],
                json={**request["payload"], "messages": messages_to_send, "stream": False},
                headers=request["headers"],
                timeout=request["timeout"],
            )
            r.raise_for_status()
            obj = r.json()
        except requests.RequestException as e:  # pragma: no cover
            raise RuntimeError(f"OpenAI-compatible call failed: {e}") from e

        message = obj.get("choices", [{}])[0].get("message", {})        
        return [message], [], [*native_messages, message], state

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        
        request = state["request"]
        try:
            # Validate native_messages before sending stream request
            self._validate_message_list(native_messages)
            override = request.get("messages")
            messages_to_send = override if isinstance(override, list) else native_messages
            with requests.post(
                request["url"], json={**request["payload"], "messages": messages_to_send, "stream": True}, headers=request["headers"], timeout=request["timeout"], stream=True
            ) as r:
                r.raise_for_status()
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
        except requests.RequestException as e:  # pragma: no cover
            raise RuntimeError(f"OpenAI-compatible stream failed: {e}") from e

    # ---------- Helpers (default/general implementations) ----------
    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract a provider-native delta dictionary from a streaming chunk.
        Return the first choice if present.
        """
        if "choices" in native_chunk and native_chunk["choices"]:
            return dict(native_chunk["choices"][0])
        
        return {}

    def process_delta(
        self, delta: Dict[str, Any], accumulated
    ):
        """
        Reduce a delta dict into a new partial accumulator, and optionally a final.
        Returns (partial_message_or_none, final_message_or_none, new_accumulated).
        """
        accumulated = accumulated or {}

        # Full message chunk
        if "message" in delta:
            full_msg = delta.get("message") or None
            return None, full_msg, accumulated

        # Delta chunk
        delta_content = delta.get("delta")
        if not delta_content:
            return None, None, accumulated

        # Merge role/content fragments
        accumulated = self._merge_delta_content(
            accumulated, delta_content, override=["role"], accumulate=["content"]
        )

        if delta.get("finish_reason") == "stop":
            # Only emit a final if we have something meaningful accumulated
            has_meaning = bool((accumulated.get("content") or accumulated.get("role")))
            if has_meaning:
                return None, accumulated, accumulated
            else:
                # Keep accumulated as-is for potential finalize step
                return None, None, accumulated

        # Regular delta chunk -> partial
        return delta_content, None, accumulated

    def _merge_delta_content(self, current: Dict[str, Any], delta: Dict[str, Any], override: List[str] = [], accumulate: List[str] = []) -> Dict[str, Any]:
        return {
            **current,
            # For override keys, prefer the incoming delta value, falling back to current
            **{key: delta.get(key, current.get(key, "")) for key in override},
            # For accumulate keys, append incoming delta fragments to current value
            **{key: (current.get(key, "") + delta.get(key, "")) for key in accumulate}
        }

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        partial_msg, final_msg, accumulated = self.process_delta(delta=self.extract_delta(native_chunk), accumulated=state.get("partial", {}))

        # returns
        partials = [partial_msg] if partial_msg else []
        finals = [final_msg] if final_msg else []
        if any(isinstance(f, dict) and not f for f in finals):
            print("[openai_provider] WARNING: emitting empty final message from stream chunk")
        new_native_messages = [*native_messages, *finals]
        new_state = {**state, "partial": accumulated}
    
        #print(f"[openai_provider] partials: {partials}")
        #print(f"[openai_provider] finals: {finals}, accumulated: {accumulated}")
        return finals, partials, new_native_messages, new_state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        
        current_partial = state.get("partial", None)
        if isinstance(current_partial, dict) and (
            current_partial.get("content") or current_partial.get("role") or current_partial.get("reasoning")
        ):
            # Streaming path: finalize from accumulated partial message.
            return [current_partial], [*native_messages, current_partial], state

        return [], native_messages, state

    def to_display_format(
        self, message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return message


