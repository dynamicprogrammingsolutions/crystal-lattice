"""HTTP-style tests for provider-extension session actions."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from tests.dummy_provider_extension_session_action import (  # noqa: E402
    DummySessionActionExtension,
)


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {},
    }

    path = tmp_path / "config_provider_extension_session_actions.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    from agent_terminal_app import server as server_mod

    previous = getattr(server_mod, "_agent_app", None)
    if previous is not None:
        previous.close()
    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), event_store=InMemoryEventStore())
    app._plugin_classes.setdefault("extensions", []).append(DummySessionActionExtension)
    app._plugins_by_kind_and_id.setdefault("extensions", {})[
        DummySessionActionExtension.name
    ] = DummySessionActionExtension
    runtime = app._agent_plugin_runtimes["default"]
    runtime.plugin_classes.setdefault("extensions", []).append(DummySessionActionExtension)
    runtime.plugins_by_kind_and_id.setdefault("extensions", {})[
        DummySessionActionExtension.name
    ] = DummySessionActionExtension
    if runtime.default_enabled_ids is not None:
        runtime.default_enabled_ids.append(DummySessionActionExtension.name)
    server_mod._agent_app = app
    return app


def test_session_ui_schema_includes_provider_extension_action(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)
    _core, _base_config, session = app.create_session("default")

    resp = server_mod.get_session_ui_schema(session.session_id, app_instance=app)

    elements = resp["elements"]
    matching = [el for el in elements if el.get("plugin") == "dummy_session_action"]
    assert len(matching) == 1
    assert matching[0]["action_id"] == "append_native_marker"
    assert matching[0]["action_owner"] == "provider_extension"


def test_actions_endpoint_executes_provider_extension_session_action(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "hello from app", config=base_config)
    app.save_session(session)

    resp = server_mod.execute_action(
        {
            "plugin": "dummy_session_action",
            "action_id": "append_native_marker",
            "inputs": {
                "session_id": session.session_id,
                "marker": "server-path",
            },
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    assert resp["plugin"] == "dummy_session_action"
    result = resp["result"]
    assert result["message"] == "Appended marker server-path"
    assert result["mutations"]["updated_session_ids"] == [session.session_id]
    assert result["ui_effects"]["reload_session_ids"] == [session.session_id]

    loaded = app.load_session_record(session.session_id)
    assert loaded is not None
    assert [message.content for message in loaded.messages] == [
        "hello from app",
        "MARKER=server-path",
    ]
    native_history = (loaded.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert native_history[-1] == {"role": "assistant", "content": "MARKER=server-path"}