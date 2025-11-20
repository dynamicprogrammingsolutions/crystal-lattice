"""
OpenAI-Compatible Provider Plugin (plugins/providers/openai/python/openai_provider.py)

Minimal provider for OpenAI-compatible Chat Completions endpoints (e.g., Ollama at /v1).
Loads configuration only from the provided config dict (no environment variable usage).
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Tuple
import json

import requests

from agent_core.types import ProviderPlugin


class OpenAICompatibleProvider(ProviderPlugin):
    name: str = "openai_compatible"
    version: str = "0.3.0"

    # ---------- Schemas ----------
    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
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

    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]:
        # No UI elements
        return []

    # ---------- State lifecycle ----------
    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]:
        # Use only provided config values
        base_url = (config.get("base_url") or "https://api.openai.com/v1").rstrip("/")
        api_key = config.get("api_key")
        model = config.get("model")
        timeout = float(config.get("timeout", 60))
        return {
            "config": {
                "base_url": base_url,
                "api_key": api_key,
                "model": model,
                "timeout": timeout,
            },
            "runtime_state": {
                "accumulated_content": "",
                "native_chunks": [],
            },
            "ui_state": {},
        }

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        new_config = {**state.get("config", {}), **updates}
        return {**state, "config": new_config}

    @staticmethod
    def initialize_request(
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            **state,
            "runtime_state": {
                **state.get("runtime_state", {}),
                "accumulated_content": "",
                "native_chunks": [],
            },
        }

    # ---------- Message conversion ----------
    @staticmethod
    def to_native_messages(
        messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return [{"role": m["role"], "content": m.get("content", "")} for m in messages]

    @staticmethod
    def from_native_messages(
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

    # ---------- Core API calls ----------
    @staticmethod
    def call_api(
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        cfg = state["config"]
        url = f"{cfg['base_url']}/chat/completions"
        payload: Dict[str, Any] = {
            "model": cfg["model"],
            "messages": native_messages,
            "stream": False,
        }
        headers = {"Content-Type": "application/json"}
        if cfg.get("api_key"):
            headers["Authorization"] = f"Bearer {cfg['api_key']}"
        try:
            r = requests.post(
                url, json=payload, headers=headers, timeout=cfg.get("timeout", 60)
            )
            r.raise_for_status()
            obj = r.json()
        except requests.RequestException as e:  # pragma: no cover
            raise RuntimeError(f"OpenAI-compatible call failed: {e}") from e
        content = obj.get("choices", [{}])[0].get("message", {}).get("content", "")
        final = [{"role": "assistant", "content": content, "metadata": {}}]
        return final, [], [], state

    @staticmethod
    def stream_api(
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        cfg = state["config"]
        url = f"{cfg['base_url']}/chat/completions"
        payload: Dict[str, Any] = {
            "model": cfg["model"],
            "messages": native_messages,
            "stream": True,
        }
        headers = {"Content-Type": "application/json"}
        if cfg.get("api_key"):
            headers["Authorization"] = f"Bearer {cfg['api_key']}"
        try:
            with requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=cfg.get("timeout", 60),
                stream=True,
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

    @staticmethod
    def process_chunk(
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        delta_text = ""
        if "content" in native_chunk and isinstance(native_chunk["content"], str):
            delta_text = native_chunk["content"]
        elif "choices" in native_chunk and native_chunk["choices"]:
            choice = native_chunk["choices"][0]
            delta_text = (
                choice.get("delta", {}).get("content")
                or choice.get("message", {}).get("content")
                or choice.get("text")
                or ""
            )
        elif "text" in native_chunk:
            delta_text = native_chunk["text"]
        new_accum = state["runtime_state"].get("accumulated_content", "") + (
            delta_text or ""
        )
        new_native = state["runtime_state"].get("native_chunks", []) + [native_chunk]
        new_state = {
            **state,
            "runtime_state": {
                **state.get("runtime_state", {}),
                "accumulated_content": new_accum,
                "native_chunks": new_native,
            },
        }
        partial = (
            {"role": "assistant", "content": delta_text, "metadata": {}}
            if delta_text
            else None
        )
        partials = [partial] if partial else []
        return [], partials, [native_chunk], new_state

    @staticmethod
    def finalize(
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        content = state.get("runtime_state", {}).get("accumulated_content", "")
        if not content:
            return [], [], state
        final = {"role": "assistant", "content": content, "metadata": {}}
        return [final], [], state

    @staticmethod
    def to_display_format(
        message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return message
