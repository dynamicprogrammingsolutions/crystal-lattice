from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


def _write_config(tmp_path: Path, transfer_script: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {"echo": {"provider": "echo_openai_like", "model": "test-model"}},
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "plugins.cloud_agent_app_plugin.CloudAgentAppPlugin",
        ],
        "agents": {"default": {"provider": "echo"}},
        "application": {
            "cloud_agent": {
                "orchestrator_url": "http://orchestrator.test",
                "workspace_dir": str(tmp_path / "workspace"),
                "transfer_script": str(transfer_script),
                "transfer_method": "managed_ssh",
                "cloud_workspace_dir": "/workspace",
            }
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_cloud_start_session_action_runs_transfer_script_and_returns_copy_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    env_capture = tmp_path / "env.json"
    transfer_script = tmp_path / "transfer.py"
    transfer_script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, os, pathlib",
                f"path = pathlib.Path({str(env_capture)!r})",
                "path.write_text(json.dumps({",
                "  'LOCAL_WORKSPACE_DIR': os.environ.get('LOCAL_WORKSPACE_DIR'),",
                "  'CLOUD_WORKSPACE_DIR': os.environ.get('CLOUD_WORKSPACE_DIR'),",
                "  'TRANSFER_DIR': os.environ.get('TRANSFER_DIR'),",
                "}, sort_keys=True))",
            ]
        ),
        encoding="utf-8",
    )
    transfer_script.chmod(0o755)

    config_path = _write_config(tmp_path, transfer_script)
    app = AgentApplication(str(config_path), str(tmp_path / "sessions"), event_store=InMemoryEventStore())
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "hello cloud", {}, config=base_config)
    app.save_session(session)

    calls: List[Dict[str, Any]] = []

    class _Response:
        def __init__(self, payload: Dict[str, Any]) -> None:
            self.payload = payload

        def __enter__(self) -> "_Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(self.payload).encode("utf-8")

    def fake_urlopen(request: Any, timeout: float = 30) -> _Response:
        try:
            body = json.loads(request.data.decode("utf-8")) if request.data else {}
        except Exception:
            body = {"binary": True, "length": len(request.data or b"")}
        calls.append(
            {
                "url": request.full_url,
                "body": body,
            }
        )
        if request.full_url.endswith("/transfers"):
            return _Response({"transfer_id": "tr_test", "endpoint": {"host": "cloud.example.test", "port": 22000}})
        if request.full_url.endswith("/transfers/tr_test/upload"):
            assert request.get_method() == "PUT"
            assert request.data
            return _Response({"transfer_id": "tr_test", "state": "uploaded"})
        if request.full_url.endswith("/transfers/tr_test/ready"):
            return _Response({"transfer_id": "tr_test", "state": "ready"})
        if request.full_url.endswith("/instances"):
            return _Response({"instance_id": "inst_test", "session_id": session.session_id, "token": "tok_test"})
        raise AssertionError(f"unexpected URL {request.full_url}")

    monkeypatch.setattr("plugins.cloud_agent_app_plugin.urlopen", fake_urlopen)

    result = app.execute_application_action(
        "cloud",
        "cloud.start_session_agent",
        {"session_id": session.session_id},
    )

    assert result["connection_link"].startswith("crystal-lattice-cloud://connect?")
    display = result["display"]
    assert display["actions"][0]["kind"] == "copy_text"
    assert "inst_test" in display["actions"][0]["text"]
    assert calls[0]["url"] == "http://orchestrator.test/transfers"
    assert calls[3]["body"]["transfer_ref"] == {"transfer_id": "tr_test"}

    captured = json.loads(env_capture.read_text(encoding="utf-8"))
    assert captured["LOCAL_WORKSPACE_DIR"] == str(workspace.resolve())
    assert captured["CLOUD_WORKSPACE_DIR"] == "/workspace"
    assert captured["TRANSFER_DIR"]