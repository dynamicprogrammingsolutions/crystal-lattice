from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Tuple

from agent_core import AgentCore
from agent_core.types import ProviderExtensionPlugin

from template_python_provider.provider import TemplateProvider


class _RetentionMarkerExtension(ProviderExtensionPlugin):
    """Marks native history with a field that is not round-trippable from core."""

    name = "_retention_marker"
    version = "0.0.0"

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        marked = [
            ({**m, "_native_only_marker": True} if isinstance(m, dict) else m)
            for m in native_messages
        ]
        return final_messages, marked, state


class _TestProviderWithRetention(TemplateProvider):
    name = "_test_retention_provider"

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Emit different output depending on whether we saw the native-only marker.
        preserved = any(
            isinstance(m, dict) and m.get("_native_only_marker") is True
            for m in native_messages
        )
        last_user = next(
            (m.get("content", "") for m in reversed(native_messages) if m.get("role") == "user"),
            "",
        )
        suffix = " [preserved]" if preserved else ""
        final = {"role": "assistant", "content": f"Echo: {last_user}{suffix}"}
        return [final], [], [*native_messages, final], state

    # minimal streaming impl not required for this retention test
    def stream_api(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Iterator[Dict[str, Any]]:  # pragma: no cover
        return iter(())

    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover
        return {}

    def process_delta(
        self, delta: Dict[str, Any], accumulated: Dict[str, Any] | None
    ) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:  # pragma: no cover
        return None, accumulated or {}


def test_native_history_retention_across_core_instances() -> None:
    cfg: Dict[str, Any] = {"model": "m"}

    core1 = AgentCore()
    core1.register_provider(_TestProviderWithRetention, extensions=[_RetentionMarkerExtension])

    session = core1.create_session()
    session = core1.add_message(session, "user", "First")
    session1, _finals1 = core1.send_request(session, cfg)

    # New core instance should reuse retained native history.
    core2 = AgentCore()
    core2.register_provider(_TestProviderWithRetention, extensions=[_RetentionMarkerExtension])

    session2 = core2.add_message(session1, "user", "Second")
    _session3, finals2 = core2.send_request(session2, cfg)

    assert finals2[-1]["content"] == "Echo: Second [preserved]"
