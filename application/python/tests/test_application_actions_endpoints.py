"""Tests for application-level actions and UI schema endpoints.

These tests call the FastAPI-style route functions in
``agent_terminal_app.server`` directly, injecting a custom
AgentApplication configured with a dummy application plugin.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


def _make_config_with_dummy_app_plugin(tmp_path: Path) -> Path:
    """Return a config path wiring DummyApplicationPlugin into the app.

    The configuration uses the echo-like provider from plugins so that
    sessions can be created without external dependencies.
    """

    cfg: Dict[str, Any] = {
        "providers": {"echo": {"provider": "echo_openai_like", "model": "test-model"}},
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "tests.dummy_app_plugin.DummyAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {},
    }

    path = tmp_path / "config_app_actions.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _make_config_with_generic_callback_plugin(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {"echo": {"provider": "echo_openai_like", "model": "test-model"}},
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            {
                "path": str(ROOT / "plugins" / "generic-callback-app"),
                "entry": "generic_callback_app.GenericCallbackAppPlugin",
            },
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {},
    }
    path = tmp_path / "config_generic_callback_actions.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    from agent_terminal_app import server as server_mod

    previous = getattr(server_mod, "_agent_app", None)
    if previous is not None:
        previous.close()
    config_path = _make_config_with_dummy_app_plugin(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Ensure the server uses this application instance when needed.
    server_mod._agent_app = app
    return app


def _build_generic_callback_app(tmp_path: Path) -> AgentApplication:
    from agent_terminal_app import server as server_mod

    previous = getattr(server_mod, "_agent_app", None)
    if previous is not None:
        previous.close()
    config_path = _make_config_with_generic_callback_plugin(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)
    server_mod._agent_app = app
    return app


def _plugin_entry(repo_name: str, entry: str) -> Dict[str, str]:
    return {"path": str(ROOT / "plugins" / repo_name), "entry": entry}


def _make_config_with_chatgpt_auth(tmp_path: Path, *, auth_mode: str) -> Path:
    provider_config: Dict[str, Any] = {
        "provider": "openai_responses",
        "model": "gpt-5",
        "auth_mode": auth_mode,
    }
    if auth_mode == "api":
        provider_config["api_key"] = "test-openai-api-key"

    cfg: Dict[str, Any] = {
        "providers": {"chatgpt": provider_config},
        "plugins": [
            _plugin_entry("chatgpt-auth-app", "chatgpt_auth_app.ChatGPTAuthAppPlugin"),
            _plugin_entry(
                "openai_responses", "openai_responses_plugins.OpenAIResponsesProvider"
            ),
        ],
        "agents": {
            "default": {"provider": "chatgpt"},
        },
        "application": {
            "chatgpt_auth": {
                "credentials_path": "${env:CONFIG_DIR}/auth/chatgpt-auth.json",
                "rate_limits_path": "${env:CONFIG_DIR}/auth/chatgpt-rate-limits.json",
            }
        },
    }
    path = tmp_path / f"config_chatgpt_auth_{auth_mode}.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _build_chatgpt_auth_app(tmp_path: Path, *, auth_mode: str) -> AgentApplication:
    from agent_terminal_app import server as server_mod

    previous = getattr(server_mod, "_agent_app", None)
    if previous is not None:
        previous.close()
    config_path = _make_config_with_chatgpt_auth(tmp_path, auth_mode=auth_mode)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(
        str(config_path),
        str(session_root),
        event_store=events,
        env_overrides={"CONFIG_DIR": str(tmp_path)},
    )
    server_mod._agent_app = app
    return app


def test_list_application_actions_includes_dummy_plugin(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    resp = server_mod.list_application_actions(app_instance=app)
    actions = resp.get("actions")
    assert isinstance(actions, list)
    assert actions

    action = actions[0]
    assert action["plugin"] == "dummy_app_plugin"
    assert action["id"] == "do_dummy"

    # Filtering by plugin id should keep only matching entries.
    filtered = server_mod.list_application_actions(
        plugin="dummy_app_plugin", app_instance=app
    )
    assert filtered["actions"]
    assert all(a["plugin"] == "dummy_app_plugin" for a in filtered["actions"])

    # Non-matching plugin id should yield an empty list.
    none = server_mod.list_application_actions(plugin="no_such", app_instance=app)
    assert none["actions"] == []


def test_list_application_ui_schema_includes_dummy_element(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    resp = server_mod.list_application_ui_schema(app_instance=app)
    elements = resp.get("elements")
    assert isinstance(elements, list)
    assert elements

    el = elements[0]
    assert el["plugin"] == "dummy_app_plugin"
    assert el["ui_type"] == "session_action"
    assert el["action_id"] == "do_dummy"

    filtered = server_mod.list_application_ui_schema(
        plugin="dummy_app_plugin", app_instance=app
    )
    assert filtered["elements"]
    assert all(e["plugin"] == "dummy_app_plugin" for e in filtered["elements"])


def test_execute_action_success_path_calls_plugin(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod
    from tests.dummy_app_plugin import DummyAppPlugin

    app = _build_app(tmp_path)

    resp = server_mod.execute_action(
        {
            "plugin": "dummy_app_plugin",
            "action_id": "do_dummy",
            "inputs": {"value": "hello"},
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    assert resp["plugin"] == "dummy_app_plugin"
    assert resp["action_id"] == "do_dummy"

    result = resp.get("result") or {}
    # DummyAppPlugin echoes the validated params mapping under "echo".
    assert result["echo"] == {"value": "hello"}

    wrappers = getattr(app, "_app_plugins")
    wrapper = wrappers["dummy_app_plugin"]
    plugin = wrapper.plugin
    assert isinstance(plugin, DummyAppPlugin)
    assert plugin.executed
    last = plugin.executed[-1]
    assert last["action_id"] == "do_dummy"
    assert last["params"] == {"value": "hello"}


def test_execute_action_resolves_omitted_plugin_when_action_id_is_unique(
    tmp_path: Path,
) -> None:
    from agent_terminal_app import server as server_mod
    from tests.dummy_app_plugin import DummyAppPlugin

    app = _build_app(tmp_path)

    resp = server_mod.execute_action(
        {
            "action_id": "do_dummy",
            "inputs": {"value": "hello"},
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    assert resp["plugin"] == "dummy_app_plugin"
    assert resp["action_id"] == "do_dummy"
    assert (resp.get("result") or {})["echo"] == {"value": "hello"}

    wrappers = getattr(app, "_app_plugins")
    plugin = wrappers["dummy_app_plugin"].plugin
    assert isinstance(plugin, DummyAppPlugin)
    assert plugin.executed[-1]["params"] == {"value": "hello"}


def test_execute_action_without_plugin_reports_unknown_action(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    resp = server_mod.execute_action(
        {
            "action_id": "no_such",
            "inputs": {},
        },
        app_instance=app,
    )

    assert resp["status"] == "error"
    assert resp["error_type"] == "unknown_action"
    assert resp["details"]["action_id"] == "no_such"


def test_execute_action_without_plugin_reports_ambiguous_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    monkeypatch.setattr(
        app,
        "get_application_actions",
        lambda: [
            {"plugin": "plugin_one", "id": "same_action", "inputs": {}},
            {"plugin": "plugin_two", "id": "same_action", "inputs": {}},
        ],
    )

    resp = server_mod.execute_action(
        {
            "action_id": "same_action",
            "inputs": {},
        },
        app_instance=app,
    )

    assert resp["status"] == "error"
    assert resp["error_type"] == "ambiguous_action"
    candidates = resp["details"]["candidates"]
    assert candidates == [
        {
            "plugin": "plugin_one",
            "action_id": "same_action",
            "action_owner": "application",
        },
        {
            "plugin": "plugin_two",
            "action_id": "same_action",
            "action_owner": "application",
        },
    ]


def test_execute_session_action_resolves_generic_callback_action_with_session_context(
    tmp_path: Path,
) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_generic_callback_app(tmp_path)
    _core, _base_config, session = app.create_session("default")

    start_resp = server_mod.execute_session_action(
        session.session_id,
        {
            "plugin": "generic_callback_app",
            "action_id": "start_external_flow",
            "inputs": {
                "connection_id": "test-connection",
                "result": "approved",
                "nonce": "n-123",
            },
        },
        app_instance=app,
    )
    assert start_resp["status"] == "ok"
    start_result = start_resp["result"]
    callback_url = (
        "crystal-lattice://action/test-connection/"
        f"{session.session_id}/complete_external_flow?result=approved&nonce=n-123"
    )
    assert start_result["callback_url"] == callback_url
    open_action = next(
        action
        for action in start_result["display"]["actions"]
        if action["kind"] == "open_url"
    )
    assert open_action["id"] == "open-generic-callback-link"
    assert open_action["label"] == "Open link"
    assert open_action["url"] == callback_url
    copy_action = next(
        action
        for action in start_result["display"]["actions"]
        if action["kind"] == "copy_text"
    )
    assert copy_action["kind"] == "copy_text"
    assert copy_action["id"] == "copy-generic-callback-link"
    assert copy_action["label"] == "Copy link"
    assert copy_action["text"] == callback_url
    assert copy_action["copied_label"] == "Copied"

    resp = server_mod.execute_session_action(
        session.session_id,
        {
            "action_id": "complete_external_flow",
            "inputs": {
                "result": "approved",
                "nonce": "n-123",
                "redirect_url": callback_url,
            },
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    assert resp["plugin"] == "generic_callback_app"
    assert resp["action_id"] == "complete_external_flow"
    assert resp["action_owner"] == "application"
    result = resp["result"]
    assert result["message"] == "Generic action complete"
    assert result["inputs"] == {
        "result": "approved",
        "nonce": "n-123",
        "redirect_url": callback_url,
    }
    assert result["context"]["session_id"] == session.session_id


def test_execute_session_action_alias_calls_same_plugin_path(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod
    from tests.dummy_app_plugin import DummyAppPlugin

    app = _build_app(tmp_path)

    resp = server_mod.execute_session_action(
        "session-1",
        {
            "plugin": "dummy_app_plugin",
            "action_id": "do_dummy",
            "inputs": {"value": "hello"},
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    assert resp["plugin"] == "dummy_app_plugin"
    assert resp["action_id"] == "do_dummy"
    assert (resp.get("result") or {})["echo"] == {"value": "hello"}

    wrappers = getattr(app, "_app_plugins")
    wrapper = wrappers["dummy_app_plugin"]
    plugin = wrapper.plugin
    assert isinstance(plugin, DummyAppPlugin)
    assert plugin.executed
    assert plugin.executed[-1]["params"] == {"value": "hello"}


def test_execute_session_action_alias_preserves_error_envelope(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    resp = server_mod.execute_session_action(
        "session-1",
        {
            "plugin": "dummy_app_plugin",
            "action_id": "do_dummy",
            "inputs": {},
        },
        app_instance=app,
    )

    assert resp["status"] == "error"
    assert resp["plugin"] == "dummy_app_plugin"
    assert resp["action_id"] == "do_dummy"
    assert resp["error_type"] == "validation"
    assert "details" in resp


def test_execute_action_unknown_plugin_or_action(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    resp1 = server_mod.execute_action(
        {"plugin": "no_such", "action_id": "do_dummy", "inputs": {}},
        app_instance=app,
    )
    assert resp1["status"] == "error"
    assert resp1["error_type"] == "not_found"

    resp2 = server_mod.execute_action(
        {
            "plugin": "dummy_app_plugin",
            "action_id": "no_such",
            "inputs": {},
        },
        app_instance=app,
    )
    assert resp2["status"] == "error"
    assert resp2["error_type"] == "not_found"


def test_execute_action_validation_errors_for_missing_and_type(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    # Missing required "value" parameter.
    missing = server_mod.execute_action(
        {
            "plugin": "dummy_app_plugin",
            "action_id": "do_dummy",
            "inputs": {},
        },
        app_instance=app,
    )
    assert missing["status"] == "error"
    assert missing["error_type"] == "validation"
    details = missing.get("details") or {}
    assert "missing_params" in details and "value" in details["missing_params"]

    # Wrong type for "value" parameter.
    wrong_type = server_mod.execute_action(
        {
            "plugin": "dummy_app_plugin",
            "action_id": "do_dummy",
            "inputs": {"value": 123},
        },
        app_instance=app,
    )
    assert wrong_type["status"] == "error"
    assert wrong_type["error_type"] == "validation"
    details2 = wrong_type.get("details") or {}
    invalid = details2.get("invalid_types") or {}
    assert "value" in invalid


def test_execute_action_rejects_extra_params(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    resp = server_mod.execute_action(
        {
            "plugin": "dummy_app_plugin",
            "action_id": "do_dummy",
            "inputs": {"value": "ok", "extra": 123},
        },
        app_instance=app,
    )

    assert resp["status"] == "error"
    assert resp["error_type"] == "validation"
    details = resp.get("details") or {}
    extra = details.get("extra_params") or []
    assert "extra" in extra


def test_execute_action_envelope_never_embeds_sessions(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    resp = server_mod.execute_action(
        {
            "plugin": "dummy_app_plugin",
            "action_id": "do_dummy",
            "inputs": {"value": "hello"},
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    assert "session" not in resp
    result = resp.get("result") or {}
    assert "session" not in result


def test_session_application_ui_schema_hides_chatgpt_actions_for_api_mode(
    tmp_path: Path,
) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_chatgpt_auth_app(tmp_path, auth_mode="api")
    _core, _base_config, session = app.create_session("default")
    app.save_session(session)

    resp = server_mod.get_session_application_ui_schema(
        session.session_id, app_instance=app
    )
    labels = {element.get("label") for element in resp["elements"]}
    assert "Sign in with ChatGPT" not in labels
    assert "Show ChatGPT account status" not in labels


def test_session_application_ui_schema_shows_chatgpt_actions_for_auto_mode(
    tmp_path: Path,
) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_chatgpt_auth_app(tmp_path, auth_mode="auto")
    _core, _base_config, session = app.create_session("default")
    app.save_session(session)

    resp = server_mod.get_session_application_ui_schema(
        session.session_id, app_instance=app
    )
    labels = {element.get("label") for element in resp["elements"]}
    assert "Sign in with ChatGPT" in labels
    assert "Show ChatGPT account status" in labels
