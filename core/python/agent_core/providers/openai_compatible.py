"""
OpenAI-Compatible Provider Plugin

A minimal provider that talks to any OpenAI-compatible Chat Completions API,
including local runtimes like Ollama (at http://localhost:11434/v1).

Design goals:
- Pure, stateless methods that accept/return state explicitly
- Use a clear HTTP client (requests)
- Basic support for non-streaming and streaming chat completions

Config keys used (flat dict):
- model: str (required) – model name/id
- api_key: str (optional) – API key for Authorization header
- base_url: str (default "https://api.openai.com/v1") – API base
- timeout: int|float seconds (default 60)

This plugin intentionally implements only the basics needed for simple text chat.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Tuple
import json
import os

import requests

from ..types import ProviderPlugin


class OpenAICompatibleProvider(ProviderPlugin):
    name: str = "openai_compatible"
    version: str = "0.2.0"

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
        # No UI elements for this minimal provider
        return []

    # ---------- State lifecycle ----------
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        base_url = config.get("base_url") or os.getenv(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        )
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        model = config.get("model") or os.getenv("OPENAI_MODEL")
        timeout = float(config.get("timeout", 60))
        state: Dict[str, Any] = {
            "config": {
                "base_url": (base_url or "https://api.openai.com/v1").rstrip("/"),
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
        return state

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        # Merge updates into config
        new_config = {**state.get("config", {}), **updates}
        return {**state, "config": new_config}

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Reset runtime accumulators for a new turn
        return {
            **state,
            "runtime_state": {
                **state.get("runtime_state", {}),
                "accumulated_content": "",
                "native_chunks": [],
            },
        }

    # ---------- Message conversion ----------
    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        # OpenAI-compatible apis accept the same {role, content}
        return [{"role": m["role"], "content": m.get("content", "")} for m in messages]

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        # Passthrough
        return list(native_messages)

    # ---------- Core API calls ----------
    def call_api(
        self,
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
        except requests.RequestException as e:  # pragma: no cover - network failures
            raise RuntimeError(f"OpenAI-compatible call failed: {e}") from e

        content = obj.get("choices", [{}])[0].get("message", {}).get("content", "")
        final = [{"role": "assistant", "content": content, "metadata": {}}]
        # Non-streaming path returns final here; finalize should return none
        return final, [], [], state

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
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
        except requests.RequestException as e:  # pragma: no cover - network failures
            raise RuntimeError(f"OpenAI-compatible stream failed: {e}") from e

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        # Extract incremental content from various possible shapes
        delta_text = ""
        if "content" in native_chunk and isinstance(native_chunk["content"], str):
            delta_text = native_chunk["content"]
        elif "choices" in native_chunk and native_chunk["choices"]:
            choice = native_chunk["choices"][0]
            # OpenAI streaming: choices[].delta.content
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

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        content = state.get("runtime_state", {}).get("accumulated_content", "")
        if not content:
            return [], [], state
        final = {"role": "assistant", "content": content, "metadata": {}}
        return [final], [], state

    def to_display_format(
        self, message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return message
