"""EchoOpenAILikeProvider: an OpenAI-style echo provider for testing.

This provider mimics the structure of the OpenAI-compatible provider but
avoids any network calls. It is intended primarily for testing
SystemMessageFeature and related request/message behaviors.

Behavior:
- ``to_native_messages`` converts core messages to OpenAI-like
  ``{"role", "content"}`` dicts.
- ``initialize_request`` records basic request metadata.
- ``call_api`` inspects either ``state["request"]["messages"]`` (if
  present) or the provided native messages and returns a single assistant
  message whose content is ``"SYS=<system>|USER=<user>"`` where:
    - ``<system>`` is the content of the first system message found.
    - ``<user>`` is the content of the last user message found.

Streaming is not used in the tests and is implemented as a minimal
no-op/compatibility layer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Iterator, Tuple

from agent_core.types import ProviderPlugin


class EchoOpenAILikeProvider(ProviderPlugin):
    name: str = "echo_openai_like"
    version: str = "0.1.0"

    # ---------- Schemas ----------
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "model": {"type": "string", "required": True},
            "base_url": {"type": "string", "required": False},
            "timeout": {"type": "number", "required": False, "default": 60},
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return []

    # ---------- State lifecycle ----------
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Provider state is opaque; this provider tracks configuration,
        # request metadata, and a partial accumulator for compatibility
        # with the OpenAI-style streaming helpers.
        return {"config": config, "request": {}, "partial": None}

    # ---------- Message conversion ----------
    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        native: List[Dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            md = msg.get("metadata")
            internal_md = dict(md) if isinstance(md, dict) else {}
            internal_md.pop("native_indices", None)

            if internal_md:
                native.append({"role": role, "content": content, "_metadata": internal_md})
            else:
                native.append({"role": role, "content": content})
        return native

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        finals: List[Dict[str, Any]] = []
        for m in native_messages:
            if not isinstance(m, dict):
                continue
            if "role" not in m or "content" not in m:
                continue

            raw_internal = m.get("_metadata") or {}
            internal_md = dict(raw_internal) if isinstance(raw_internal, dict) else {}
            internal_md.pop("native_indices", None)
            finals.append(
                {
                    "role": m.get("role", "assistant"),
                    "content": m.get("content", ""),
                    "metadata": internal_md,
                }
            )
        return finals

    # ---------- Request initialization ----------
    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:

        config = state.get("config", {})
        timeout = float(config.get("timeout", 60))
        request = {
            "url": "echo://local",
            "payload": {"model": config.get("model")},
            "headers": {},
            "timeout": timeout,
        }
        new_state: Dict[str, Any] = {**state, "request": request}
        return native_messages, new_state


    # ---------- Core API calls ----------
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
        messages_to_use = self._select_messages_for_call(native_messages, state)
        sys_content, user_content = self._extract_system_and_user(messages_to_use)
        content = f"SYS={sys_content} | USER={user_content}"
        final = {"role": "assistant", "content": content}
        # Use the override only for constructing the assistant response,
        # but keep the stored native history based on the original
        # native_messages plus the assistant reply. This mirrors the
        # convention that per-request rendering should not affect
        # persisted history.
        return [final], [], [*native_messages, final], state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:  # pragma: no cover - not used in tests
        # Minimal streaming wrapper that yields a single chunk equivalent to call_api.
        finals, _partials, _natives, _new_state = self.call_api(native_messages, state)
        for msg in finals:
            yield msg

    # ---------- Helpers for streaming protocol compatibility ----------
    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover
        return {"message": native_chunk}

    def process_delta(self, delta: Dict[str, Any], accumulated: Any):  # pragma: no cover
        return None, delta.get("message"), accumulated

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:  # pragma: no cover
        return [native_chunk], [], [*native_messages, native_chunk], state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # No additional finals; return native history as-is.
        return [], native_messages, state

    def to_display_format(
        self, message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover
        return message
