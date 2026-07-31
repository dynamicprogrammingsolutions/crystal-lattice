from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from dotenv import dotenv_values

from application_config_app import ApplicationConfigAppPlugin


class _FakeApplication:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.requests: list[dict[str, Any]] = []

    def request_application_reload(self, **kwargs: Any) -> dict[str, Any]:
        self.requests.append(kwargs)
        if self.fail:
            raise RuntimeError("reload rejected")
        return {
            "status": "ok",
            "reload_status": "accepted",
            "reload_id": "reload-test",
        }


def _state(plugin: ApplicationConfigAppPlugin, env_file: Path) -> dict[str, Any]:
    return plugin.init(
        {
            "application": {
                "application_config": {
                    "env_file": str(env_file),
                    "editable_env_keys": ["OPENAI_API_KEY"],
                    "provider_env_keys": {
                        "openai": "OPENAI_API_KEY",
                        "blocked": "NOT_ALLOWED",
                    },
                }
            }
        }
    )


def test_plugin_declares_application_actions_and_secret_input(tmp_path: Path) -> None:
    plugin = ApplicationConfigAppPlugin()
    state = _state(plugin, tmp_path / ".env")

    elements = plugin.get_ui_elements(state)

    assert [element["ui_type"] for element in elements] == [
        "application_action",
        "application_action",
    ]
    assert elements[1]["dialog"]["inputs"][1]["type"] == "secret"
    assert elements[1]["dialog"]["inputs"][0]["options"] == [
        {"value": "openai", "label": "openai"}
    ]


def test_key_action_updates_allowlisted_dotenv_and_registers_rollback(
    tmp_path: Path,
) -> None:
    plugin = ApplicationConfigAppPlugin()
    env_file = tmp_path / ".env"
    env_file.write_text("OTHER=value\n", encoding="utf-8")
    state = _state(plugin, env_file)
    app = _FakeApplication()

    result = plugin.execute_action(
        app,
        "set_provider_api_key",
        {"provider_id": "openai", "api_key": "synthetic-secret"},
        None,
        state,
    )

    assert result["status"] == "ok"
    assert result["reload_status"] == "accepted"
    assert dotenv_values(env_file)["OPENAI_API_KEY"] == "synthetic-secret"
    app.requests[0]["on_failure"]()
    assert env_file.read_text(encoding="utf-8") == "OTHER=value\n"


def test_key_action_rolls_back_when_reload_request_fails(tmp_path: Path) -> None:
    plugin = ApplicationConfigAppPlugin()
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY='old'\n", encoding="utf-8")
    state = _state(plugin, env_file)

    with pytest.raises(RuntimeError, match="reload rejected"):
        plugin.execute_action(
            _FakeApplication(fail=True),
            "set_provider_api_key",
            {"provider_id": "openai", "api_key": "new"},
            None,
            state,
        )

    assert dotenv_values(env_file)["OPENAI_API_KEY"] == "old"


def test_key_action_rejects_process_environment_value(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin = ApplicationConfigAppPlugin()
    state = _state(plugin, tmp_path / ".env")
    monkeypatch.setenv("OPENAI_API_KEY", "external")

    with pytest.raises(ValueError, match="externally managed"):
        plugin.execute_action(
            _FakeApplication(),
            "set_provider_api_key",
            {"provider_id": "openai", "api_key": "new"},
            None,
            state,
        )
