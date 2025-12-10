"""
Dummy provider plugin for testing purposes.

This plugin simulates a basic LLM provider without making actual API calls.
Follows the state-based plugin protocol with explicit state dicts.
"""

from typing import Dict, Any, List, Iterator, Tuple
from dataclasses import dataclass
from agent_core.types import ProviderPlugin
import time


@dataclass
class DummyProvider(ProviderPlugin):
    """
    Dummy provider plugin (stateless with explicit state parameter).
    Instance methods operate on provided state; instances are short‑lived per request.
    """

    name: str = "dummy_provider"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema."""
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": False},
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Return UI elements."""
        return [{"type": "text", "key": "model", "label": "Model Name"}]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize provider state.
        """
        return {
            "config": config,
            "runtime_state": {"accumulated_content": "", "native_chunks": []},
        }

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return native_messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Prepare for a new request and reset runtime accumulators.

        Returns the (possibly unmodified) provider-native history along with
        the updated shared state so that callers following the newer
        ``(native_messages, state)`` contract can preserve history while
        resetting per-request runtime fields.
        """

        new_state = {
            **state,
            "runtime_state": {
                **state.get("runtime_state", {}),
                "accumulated_content": "",
                "native_chunks": [],
            },
        }
        return list(native_messages), new_state

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Process a streaming chunk and update state.
 
        Returns ``(partial_messages, final_messages, native_messages, new_state)``.
 
        For this dummy provider, per-character streaming chunks are tracked only
        in ``runtime_state['native_chunks']`` and are **not** persisted into the
        provider-native history. The retained ``native_messages`` list therefore
        contains only full chat messages (e.g., user and final assistant), which
        keeps provider-native history compatible with native-history rebuilds.
        Final messages are produced in :meth:`finalize`.
        """
        partial_content = native_chunk.get("content", "")
        new_state = {
            **state,
            "runtime_state": {
                **state["runtime_state"],
                "accumulated_content": state["runtime_state"]["accumulated_content"]
                + partial_content,
                "native_chunks": state["runtime_state"]["native_chunks"] + [native_chunk],
            },
        }
        partial_msg = {"role": "assistant", "content": partial_content, "metadata": {}}
        # Do not append the raw chunk object into native_messages; only full
        # chat messages (user/assistant) are preserved in native history.
        full_history = list(native_messages)
        return ([partial_msg] if partial_content else []), [], full_history, new_state


    def finalize(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Finalize message from accumulated state.

        When streaming has produced incremental chunks, this aggregates them
        into a single assistant message. For non-streaming usage where no
        chunks were recorded, it simply preserves the existing native history
        without adding a new final message.
        """
        content = state["runtime_state"]["accumulated_content"]
        if not content:
            # No aggregated streaming content; keep native history as-is.
            return [], list(native_messages), state
        message = {
            "role": "assistant",
            "content": content,
            "metadata": {"chunk_count": len(state["runtime_state"]["native_chunks"])},
        }
        full_native = list(native_messages) + [message]
        return [message], full_native, state

    def call_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Make a non-streaming API call (simulated).

        Returns ``(final_messages, partial_messages, native_messages, state)``
        where ``native_messages`` contains the full history including the new
        assistant reply so that callers can retain provider-native history
        across turns.
        """
        last_message = native_messages[-1] if native_messages else {}
        user_content = last_message.get("content", "")
        final = {
            "role": "assistant",
            "content": f"Echo: {user_content}",
            "metadata": {},
        }
        full_native = list(native_messages) + [final]
        return [final], [], full_native, state

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (simulated)."""
        last_message = native_messages[-1] if native_messages else {}
        user_content = last_message.get("content", "")
        response_text = f"Echo: {user_content}"

        cfg = state.get("config") if isinstance(state, dict) else {}
        sleep_per_char = 0.0
        if isinstance(cfg, dict):
            try:
                sleep_per_char = float(cfg.get("sleep_per_char") or 0.0)
            except Exception:
                sleep_per_char = 0.0

        for char in response_text:
            if sleep_per_char > 0.0:
                time.sleep(sleep_per_char)
            yield {"content": char}


_failure_toggle: Dict[str, Any] = {"should_fail_once": True}


@dataclass
class FailingOnceDummyProvider(ProviderPlugin):
    """Dummy provider that fails once, then behaves like DummyProvider.

    Used to test application-layer failure handling and subsequent recovery.
    """

    name: str = "failing_dummy_provider"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"model": {"type": "string", "required": True}}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return native_messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return state

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return [], [], [], state

    def finalize(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return [], [], state

    def call_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if _failure_toggle.get("should_fail_once"):
            _failure_toggle["should_fail_once"] = False
            raise RuntimeError("Simulated provider failure")

        last_message = native_messages[-1] if native_messages else {}
        user_content = last_message.get("content", "")
        final = {
            "role": "assistant",
            "content": f"Echo: {user_content}",
            "metadata": {},
        }
        return [final], [], [], state

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        last_message = native_messages[-1] if native_messages else {}
        user_content = last_message.get("content", "")
        response_text = f"Echo: {user_content}"
        for ch in response_text:
            yield {"content": ch}


def reset_failing_dummy_provider_state() -> None:
    """Reset global failure toggle for FailingOnceDummyProvider tests."""

    _failure_toggle["should_fail_once"] = True
