from __future__ import annotations

from typing import Any, Dict, List, Tuple

import types

from agent_core import AgentCore, Message, Session

from plugins.rebuild_native_app import RebuildNativeAppPlugin


class DummyProvider:
    name = "dummy_provider_for_rebuild"

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
            # Preserve core metadata under a private key so from_native can
            # reconstruct core messages.
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


class DummyApp:
    """Minimal stand-in for AgentApplication used in tests."""

    def __init__(self, core: AgentCore, base_config: Dict[str, Any], session: Session):
        self._core = core
        self._base_config = base_config
        self._session = session
        self.saved_session: Session | None = None

    class _Lock:
        def __enter__(self_inner):  # pragma: no cover - trivial
            return None

        def __exit__(self_inner, exc_type, exc, tb):  # pragma: no cover - trivial
            return False

    def acquire_session_lock(self, session_id: str):  # pragma: no cover - context manager shim
        return DummyApp._Lock()

    def load_session(self, session_id: str):
        return (self._core, self._base_config, self._session)

    def save_session(self, session: Session):
        self.saved_session = session


def _build_core_and_session_for_rebuild() -> Tuple[AgentCore, Dict[str, Any], Session]:
    core = AgentCore()
    core.register_provider(DummyProvider)

    base_config: Dict[str, Any] = {"provider": DummyProvider.name}

    m0 = Message(role="assistant", content="hello", metadata={})
    m1 = Message(role="assistant", content="world", metadata={})
    session = Session(session_id="s-rebuild", messages=[m0, m1], metadata={})
    return core, base_config, session


def test_rebuild_native_core_method_round_trip():
    core, base_config, session = _build_core_and_session_for_rebuild()

    rebuilt = core.rebuild_native_history(session, base_config)

    # Messages should survive round-trip.
    assert [m.content for m in rebuilt.messages] == ["hello", "world"]

    # Native history and integrity should be present.
    md = rebuilt.metadata or {}
    native = md.get("native_messages")
    integ = md.get("native_messages_integrity")
    assert isinstance(native, list) and len(native) == 2
    assert isinstance(integ, dict)


def test_rebuild_native_app_ui_elements():
    plugin = RebuildNativeAppPlugin()
    state = plugin.init({"application": {"rebuild_native_enabled": True}})

    ui = plugin.get_ui_elements(state)
    ids = {el.get("id") for el in ui}
    assert "rebuild_native_history" in ids


def test_rebuild_native_app_execute_action_rebuilds_session():
    core, base_config, session = _build_core_and_session_for_rebuild()
    app = DummyApp(core, base_config, session)
    plugin = RebuildNativeAppPlugin()
    state = plugin.init({"application": {"rebuild_native_enabled": True}})

    result = plugin.execute_action(
        app,
        "rebuild_native_history",
        {"session_id": session.session_id},
        state,
    )

    mutations = result.get("mutations")
    assert isinstance(mutations, dict)
    assert mutations.get("updated_session_ids") == [session.session_id]

    ui_effects = result.get("ui_effects")
    assert isinstance(ui_effects, dict)
    assert ui_effects.get("reload_session_ids") == [session.session_id]

    saved = app.saved_session
    assert saved is not None
    md = saved.metadata or {}
    assert isinstance(md.get("native_messages"), list)
    assert isinstance(md.get("native_messages_integrity"), dict)
