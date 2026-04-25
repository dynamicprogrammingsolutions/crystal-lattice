"""Controllable OpenAI-compatible provider used by tests."""

from __future__ import annotations

from dataclasses import dataclass
import threading
import time
from typing import Any, Dict, Iterator, List, Optional, Tuple

from agent_core.types import ProviderPlugin


_last_payload: Dict[str, Any] | None = None
_last_user_message: str | None = None
_last_native_messages: List[Dict[str, Any]] = []
_call_started = threading.Event()
_call_release = threading.Event()


def _record_request_state(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> str | None:
    global _last_payload, _last_user_message, _last_native_messages

    payload = dict((state.get("request") or {}).get("payload") or {})
    _last_payload = payload
    _last_native_messages = [dict(message) for message in native_messages]

    last_user_message = None
    for message in reversed(native_messages):
        if message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            last_user_message = content
            break
    _last_user_message = last_user_message
    return last_user_message


def reset_controllable_openai_test_provider_state() -> None:
    """Reset recorded request state and arm blocking for blocking tests."""

    global _last_payload, _last_user_message, _last_native_messages
    _last_payload = None
    _last_user_message = None
    _last_native_messages = []
    _call_started.clear()
    _call_release.clear()


def get_controllable_openai_test_provider_state() -> Dict[str, Any]:
    """Return a snapshot of the last observed provider request."""

    return {
        "payload": dict(_last_payload or {}),
        "last_user_message": _last_user_message,
        "native_messages": [dict(message) for message in _last_native_messages],
    }


def wait_for_controllable_openai_test_provider_call(timeout: float = 1.0) -> bool:
    """Wait until the provider begins handling a request."""

    return _call_started.wait(timeout)


def release_controllable_openai_test_provider_call() -> None:
    """Release a provider call that is blocked for test synchronization."""

    _call_release.set()


@dataclass
class ControllableOpenAITestProvider(ProviderPlugin):
    """OpenAI-compatible provider whose reply is driven by test config."""

    name: str = "controllable_openai_test_provider"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "model": {"type": "string", "required": True},
            "response_text": {"type": "string", "required": False},
            "response_mode": {"type": "string", "required": False},
            "sleep_before_response": {"type": "number", "required": False},
            "block_until_released": {"type": "boolean", "required": False},
            "block_wait_timeout": {"type": "number", "required": False},
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "config": dict(config),
            "runtime_state": {"accumulated_content": "", "native_chunks": []},
        }

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return ["provider:openai_compatible", "supports_tools"]

    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return list(messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        config = state.get("config") or {}
        payload = {"model": config.get("model", "test-model")}
        return list(native_messages), {
            **state,
            "request": {"payload": payload},
            "runtime_state": {"accumulated_content": "", "native_chunks": []},
        }

    def call_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        config = state.get("config") or {}
        last_user_message = _record_request_state(native_messages, state)
        _call_started.set()

        if config.get("block_until_released"):
            wait_timeout = float(config.get("block_wait_timeout") or 5.0)
            _call_release.wait(wait_timeout)

        sleep_before = float(config.get("sleep_before_response") or 0.0)
        if sleep_before > 0.0:
            time.sleep(sleep_before)

        response_mode = config.get("response_mode") or "static"
        if response_mode == "none":
            return [], [], list(native_messages), state

        if response_mode == "echo_last_user":
            response_text = last_user_message or ""
        else:
            response_text = str(config.get("response_text") or "Generated title")

        assistant = {"role": "assistant", "content": response_text}
        return [], [assistant], [*native_messages, assistant], state

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        config = state.get("config") or {}
        last_user_message = _record_request_state(native_messages, state)

        _call_started.set()

        if config.get("block_until_released"):
            wait_timeout = float(config.get("block_wait_timeout") or 5.0)
            _call_release.wait(wait_timeout)

        sleep_before = float(config.get("sleep_before_response") or 0.0)
        if sleep_before > 0.0:
            time.sleep(sleep_before)

        response_mode = config.get("response_mode") or "static"
        if response_mode == "none":
            return

        if response_mode == "echo_last_user":
            response_text = last_user_message or ""
        else:
            response_text = str(config.get("response_text") or "Generated title")

        for char in response_text:
            yield {"content": char}

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        partial_content = native_chunk.get("content", "")
        runtime_state = state.get("runtime_state") or {}
        new_state = {
            **state,
            "runtime_state": {
                **runtime_state,
                "accumulated_content": str(runtime_state.get("accumulated_content") or "")
                + str(partial_content),
                "native_chunks": list(runtime_state.get("native_chunks") or []) + [native_chunk],
            },
        }
        partial_msg = {"role": "assistant", "content": partial_content, "metadata": {}}
        return ([partial_msg] if partial_content else []), [], list(native_messages), new_state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        runtime_state = state.get("runtime_state") or {}
        content = runtime_state.get("accumulated_content") or ""
        if not isinstance(content, str) or not content:
            return [], list(native_messages), state
        assistant = {"role": "assistant", "content": content}
        return [assistant], [*native_messages, assistant], state