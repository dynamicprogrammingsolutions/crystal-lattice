"""Deterministic streaming provider for integration tests.

This provider is intentionally simple and fully deterministic. It is
designed to be used by end-to-end integration tests that exercise the
real FastAPI backend and the TypeScript SDK.

Key behaviors:

- Streaming emits a configurable number of partial assistant chunks, then
  a single final assistant message.
- The final assistant content is derived from the effective system/user
  messages visible to the provider for the request (respecting the
  SystemMessageFeature's state["request"]["messages"] override).
- No network I/O.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Iterator, List, Optional, Tuple

from agent_core.types import ProviderPlugin


class DeterministicStreamProvider(ProviderPlugin):
    name: str = "deterministic_stream"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "model": {"type": "string", "required": True},
            "timeout": {"type": "number", "required": False, "default": 60},
            "stream_chunk_count": {
                "type": "integer",
                "required": False,
                "default": 3,
                "description": "Number of partial chunks to emit before final.",
            },
            "stream_chunk_delay_ms": {
                "type": "integer",
                "required": False,
                "default": 0,
                "description": "Delay in milliseconds between partial chunks.",
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:  # pragma: no cover - not used
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config, "request": {}, "final_text": None}

    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        native: List[Dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            multipart_content = msg.get("multipartContent")
            md = msg.get("metadata")
            internal_md = dict(md) if isinstance(md, dict) else {}
            internal_md.pop("native_indices", None)

            native_msg: Dict[str, Any] = {"role": role, "content": content}
            if multipart_content is not None:
                native_msg["multipartContent"] = multipart_content
            if internal_md:
                native_msg["_metadata"] = internal_md

            native.append(native_msg)
        return native

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        finals: List[Dict[str, Any]] = []
        for msg in native_messages:
            if not isinstance(msg, dict):
                continue
            if "role" not in msg or "content" not in msg:
                continue
            raw_internal = msg.get("_metadata") or {}
            internal_md = dict(raw_internal) if isinstance(raw_internal, dict) else {}
            internal_md.pop("native_indices", None)

            final: Dict[str, Any] = {
                "role": msg.get("role", "assistant"),
                "content": msg.get("content", ""),
                "metadata": internal_md,
            }

            multipart_content = msg.get("multipartContent")
            if multipart_content is not None:
                final["multipartContent"] = multipart_content

            finals.append(final)
        return finals

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        config = state.get("config", {})
        timeout = float(config.get("timeout", 60))
        request = {
            "url": "deterministic://local",
            "payload": {"model": config.get("model")},
            "headers": {},
            "timeout": timeout,
        }
        return native_messages, {**state, "request": request}

    def _select_messages_for_call(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        request = state.get("request") or {}
        override = request.get("messages")
        if isinstance(override, list):
            return override
        return native_messages

    @staticmethod
    def _extract_system_and_user(messages: List[Dict[str, Any]]) -> Tuple[str, str]:
        system_content = ""
        user_content = ""
        for msg in messages:
            if msg.get("role") == "system" and not system_content:
                system_content = msg.get("content", "") or ""
        for msg in reversed(messages):
            if msg.get("role") == "user" and not user_content:
                user_content = msg.get("content", "") or ""
        return system_content, user_content

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Non-streaming path: compute the final message, but return it via
        # `finalize` so streaming and non-streaming share identical behavior.
        messages_to_use = self._select_messages_for_call(native_messages, state)
        sys_content, user_content = self._extract_system_and_user(messages_to_use)
        final_text = f"SYS={sys_content} | USER={user_content}"
        return [], [], list(native_messages), {**state, "final_text": final_text}

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        config = state.get("config", {})
        chunk_count = int(config.get("stream_chunk_count", 3) or 3)
        delay_ms = int(config.get("stream_chunk_delay_ms", 0) or 0)

        chunk_count = max(1, chunk_count)
        messages_to_use = self._select_messages_for_call(native_messages, state)
        sys_content, user_content = self._extract_system_and_user(messages_to_use)
        final_text = f"SYS={sys_content} | USER={user_content}"
        state["final_text"] = final_text

        # Emit partial chunks only; the final message is produced in `finalize`.
        for idx in range(chunk_count):
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            yield {
                "role": "assistant",
                "content": f"partial-{idx + 1}",
                "_partial": True,
            }

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # `stream_api` yields assistant-shaped message dicts directly.
        msg = {k: v for k, v in native_chunk.items() if not k.startswith("_")}
        # Partial: do not add to persisted native history.
        return [msg], [], native_messages, state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        final_text = state.get("final_text")
        if not isinstance(final_text, str) or not final_text:
            return [], native_messages, state

        final = {"role": "assistant", "content": final_text}
        return [final], [*native_messages, final], {**state, "final_text": None}


__all__ = ["DeterministicStreamProvider"]
