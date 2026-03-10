"""OpenAI Responses provider scaffold.

This file intentionally keeps implementation minimal for the package-scaffolding
subtask. Full Responses API transport and conversion behavior is implemented in
later subtasks.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Iterator, List, Optional, Tuple

from agent_core.types import ProviderPlugin


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
                "default": "https://api.openai.com/v1",
            },
            "timeout": {"type": "number", "required": False, "default": 60},
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
        if isinstance(model, str) and model:
            return [{"id": model}]
        return []

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return [
            "provider:openai_responses",
            "openai_responses",
            "supports_streaming",
        ]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        cfg = state.get("config") or {}

        api_key = cfg.get("api_key") or os.getenv("OPENAI_API_KEY")
        base_url = str(cfg.get("base_url") or "https://api.openai.com/v1").rstrip("/")
        model = cfg.get("model")
        timeout = float(cfg.get("timeout", 60))

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if isinstance(api_key, str) and api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        request = {
            "url": f"{base_url}/responses",
            "payload": {"model": model},
            "headers": headers,
            "timeout": timeout,
        }

        return list(native_messages), {**state, "request": request}

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return [m for m in messages if isinstance(m, dict)]

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for msg in native_messages:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            content = msg.get("content")
            if isinstance(role, str) and isinstance(content, str):
                out.append({"role": role, "content": content, "metadata": {}})
        return out

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return [], [], list(native_messages), state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        return iter(())

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return [], [], list(native_messages), state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return [], list(native_messages), state
