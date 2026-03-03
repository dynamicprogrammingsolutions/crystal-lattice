from __future__ import annotations

from typing import Any, Dict, Iterator, List, Tuple

from agent_core.types import ProviderPlugin

from _helpers import build_core, run_streaming


class _CustomStreamingProvider(ProviderPlugin):
    """Test-only provider that implements custom process_chunk/finalize."""

    name = "_test_custom_stream_provider"
    version = "0.0.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config, "acc": ""}

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), {**state, "acc": ""}

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Non-streaming baseline: no-op, finalize will emit from state.
        last_user = next(
            (m.get("content", "") for m in reversed(native_messages) if m.get("role") == "user"),
            "",
        )
        return [], [], list(native_messages), {**state, "final_text": f"Echo: {last_user}"}

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        last_user = next(
            (m.get("content", "") for m in reversed(native_messages) if m.get("role") == "user"),
            "",
        )
        for ch in f"Echo: {last_user}":
            yield {"content": ch}

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        ch = native_chunk.get("content", "")
        acc = (state.get("acc") or "") + (ch or "")
        partial = {"role": "assistant", "content": ch}
        # Keep native history unchanged while streaming.
        return [partial], [], list(native_messages), {**state, "acc": acc}

    def finalize(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        text = state.get("acc") or state.get("final_text") or ""
        if not text:
            return [], list(native_messages), state
        final = {"role": "assistant", "content": text}
        return [final], [*native_messages, final], state


def test_custom_streaming_provider_works() -> None:
    core = build_core(_CustomStreamingProvider)

    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    _session2, finals, partial_text = run_streaming(core, session, {})

    assert partial_text == "Echo: Hello"
    assert finals and finals[-1]["content"] == "Echo: Hello"
