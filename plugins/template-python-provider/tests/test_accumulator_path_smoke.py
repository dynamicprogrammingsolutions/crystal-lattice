from __future__ import annotations

from typing import Any, Dict, Iterator, List, Tuple

from agent_core import AgentCore

from template_python_provider.provider import TemplateProvider


class _TestAccumulatorProvider(TemplateProvider):
    """Test-only provider that fills in the skeleton with deterministic behavior."""

    name = "_test_accumulator_provider"

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Non-streaming baseline: return a final assistant message.
        last_user = next(
            (m.get("content", "") for m in reversed(native_messages) if m.get("role") == "user"),
            "",
        )
        final = {"role": "assistant", "content": f"Echo: {last_user}"}
        return [final], [], [*native_messages, final], state

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        # Stream each character using an OpenAI-like chunk.
        last_user = next(
            (m.get("content", "") for m in reversed(native_messages) if m.get("role") == "user"),
            "",
        )
        text = f"Echo: {last_user}"
        for ch in text:
            yield {"choices": [{"delta": {"role": "assistant", "content": ch}}]}

    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        return native_chunk.get("choices", [{}])[0]

    def process_delta(
        self, delta: Dict[str, Any], accumulated: Dict[str, Any] | None
    ) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
        base = accumulated or {}
        d = delta.get("delta") or {}
        if not isinstance(d, dict):
            return None, base
        frag = {"role": d.get("role", "assistant"), "content": d.get("content", "")}
        new_acc = {
            "role": base.get("role", frag.get("role", "assistant")),
            "content": (base.get("content", "") + (frag.get("content") or "")),
        }
        return frag, new_acc


def test_non_streaming_smoke() -> None:
    core = AgentCore()
    core.register_provider(_TestAccumulatorProvider)

    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    _session2, finals = core.send_request(session, {"model": "m"})

    assert finals[-1]["content"] == "Echo: Hello"


def test_streaming_smoke() -> None:
    core = AgentCore()
    core.register_provider(_TestAccumulatorProvider)

    session = core.create_session()
    session = core.add_message(session, "user", "Hello")

    partial_text = ""
    final_event = None
    for event in core.send_request_stream(session, {"model": "m"}):
        if event["type"] == "partial":
            partial_text += event["message"].get("content", "")
        elif event["type"] == "final":
            final_event = event

    assert partial_text == "Echo: Hello"
    assert final_event is not None
    assert final_event["messages"][-1]["content"] == "Echo: Hello"
