from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agent_core import AgentCore, Message, Session


class DummyProvider:
    name = "dummy_provider_for_rebuild_core"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - trivial
        return {"config": dict(config)}

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        native: List[Dict[str, Any]] = []
        for m in messages:
            nm = {"role": m.get("role", "assistant"), "content": m.get("content", "")}
            nm["_core_metadata"] = dict(m.get("metadata") or {})
            native.append(nm)
        return native

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        core: List[Dict[str, Any]] = []
        for nm in native_messages:
            core.append(
                {
                    "role": nm.get("role", "assistant"),
                    "content": nm.get("content", ""),
                    "metadata": dict(nm.get("_core_metadata") or {}),
                }
            )
        return core

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover - passthrough
        return list(native_messages), dict(state)

    def apply_extension_transforms(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:  # pragma: no cover - passthrough
        return native_messages


def test_rebuild_native_history_round_trip():
    core = AgentCore()
    core.register_provider(DummyProvider)

    base_config: Dict[str, Any] = {"provider": DummyProvider.name}

    m0 = Message(role="assistant", content="hello", metadata={})
    m1 = Message(role="assistant", content="world", metadata={})
    session = Session(session_id="s-rebuild-core", messages=[m0, m1], metadata={})

    rebuilt = core.rebuild_native_history(session, base_config)

    assert [m.content for m in rebuilt.messages] == ["hello", "world"]

    md = rebuilt.metadata or {}
    native = md.get("native_messages")
    integ = md.get("native_messages_integrity")
    assert isinstance(native, list) and len(native) == 2
    assert isinstance(integ, dict)
