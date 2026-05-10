from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any, Dict, List

from agent_evaluations import cli


@dataclass
class _FakeSession:
    session_id: str


class _FakeApp:
    def __init__(self) -> None:
        self.calls: List[tuple[str, str, Dict[str, Any]]] = []
        self.deleted: List[str] = []

    def execute_application_action(self, plugin: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append((plugin, action, dict(params)))
        return {"plugin": plugin, "action": action, "params": dict(params)}

    def create_session(self, agent_id: str):
        return object(), {}, _FakeSession(session_id=f"session-for-{agent_id}")

    def delete_session(self, session_id: str) -> None:
        self.deleted.append(session_id)


class _FakeEnv:
    def __init__(self, app: _FakeApp) -> None:
        self._app = app

    def build_application(self) -> _FakeApp:
        return self._app


def test_auth_status_uses_show_account_status_when_agent_id_is_provided(monkeypatch, capsys) -> None:
    app = _FakeApp()
    monkeypatch.setattr(cli, "load_evaluation_environment", lambda _config_dir: _FakeEnv(app))

    exit_code = cli.main(["auth", "status", "--config-dir", "/tmp/config", "--agent-id", "codex-openai"])

    assert exit_code == 0
    assert app.calls == [
        ("chatgpt_auth", "show_account_status", {"session_id": "session-for-codex-openai"})
    ]
    assert app.deleted == ["session-for-codex-openai"]
    assert "show_account_status" in capsys.readouterr().out


def test_auth_logout_wires_to_logout_action(monkeypatch, capsys) -> None:
    app = _FakeApp()
    monkeypatch.setattr(cli, "load_evaluation_environment", lambda _config_dir: _FakeEnv(app))

    exit_code = cli.main(["auth", "logout", "--config-dir", "/tmp/config"])

    assert exit_code == 0
    assert app.calls == [("chatgpt_auth", "logout", {})]
    assert "logout" in capsys.readouterr().out
