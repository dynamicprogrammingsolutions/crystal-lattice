"""
OpenAI-Compatible Provider Plugin (plugins/providers/openai/python/openai_provider.py)

Minimal provider for OpenAI-compatible Chat Completions endpoints (e.g., Ollama at /v1).
Loads configuration only from the provided config dict (no environment variable usage).
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Tuple, Optional
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
        return {
            "config": config
        }

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        new_config = {**state.get("config", {}), **updates}
        return {**state, "config": new_config}

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
            "model": model,
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
        return list(native_messages)

    # ---------- Core API calls ----------
    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        request = state["request"]        
        try:
            r = requests.post(
                request["url"], json={**request["payload"], "messages": native_messages, "stream": False}, headers=request["headers"], timeout=request["timeout"]
            )
            r.raise_for_status()
            obj = r.json()
        except requests.RequestException as e:  # pragma: no cover
            raise RuntimeError(f"OpenAI-compatible call failed: {e}") from e
        content = obj.get("choices", [{}])[0].get("message", {}).get("content", "")
        final = [{"role": "assistant", "content": content, "metadata": {}}]
        return final, [], [], state

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        
        request = state["request"]        
        try:
            with requests.post(
                request["url"], json={**request["payload"], "messages": native_messages, "stream": True}, headers=request["headers"], timeout=request["timeout"]
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

    def delta_to_message(
        self, delta: Dict[str, Any], partial: Dict[str, Any]
    ):
        """
        Reduce a delta dict into a new partial accumulator, and optionally a final.
        Returns (partial_message_or_none, final_message_or_none).
        
        Full message:
        {'index': 0, 'message': {'role': 'assistant', 'content': "Here's a short poem:\n\nSilent stars shine bright and far,\nA midnight sky, with dreams afar.\nThe moon glows soft, like silver hue,\nAs night descends, all is new."}, 'finish_reason': 'stop'}
        
        Partial:
        {'index': 0, 'delta': {'role': 'assistant', 'content': 'Sil'}, 'finish_reason': None}
        """
        print(f"delta_to_message: {delta}\n")
        
        if not partial:
            return delta, None
        
        this_part = partial.get("delta")
        if (this_part) :
            new_partial = {**delta, **this_part, "content": delta.get("content", "") + this_part.get("content", "")}
            return (None, new_partial) if partial.get("finish_reason") == "stop" else (new_partial, None)
        
        this_part = partial.get("content")
        if (this_part):
            return None, this_part
        
        return None, None

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        print(f"chunk:{native_chunk}\n")
        
        # 1) Extract structured delta
        delta = self.extract_delta(native_chunk)

        # 2) Prepare current partial accumulator from state
        current_partial = state.get("partial", {})

        # 3) Reduce delta into partial/final message
        partial_msg, final_msg = self.delta_to_message(delta, current_partial)

        # 4) Prepare returns
        partials = [partial_msg] if partial_msg else []
        finals = [final_msg] if final_msg else []
        new_native_messages = [*native_messages, *finals]
        new_state = {**state, "partial": partial_msg}

        return finals, partials, new_native_messages, new_state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        current_partial = state.get("partial", None)
        new_finals = [current_partial] if current_partial else []
        new_native_messages = [*native_messages, *([current_partial] if current_partial else [])]
        return new_finals, new_native_messages, state

    def to_display_format(
        self, message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return message
