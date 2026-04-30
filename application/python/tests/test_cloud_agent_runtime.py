from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_PATH = REPO_ROOT / "cloud-orchestrator" / "runtime" / "python" / "runtime.py"


@pytest.fixture(autouse=True)
def _restore_server_app_state() -> Iterator[None]:
    from agent_terminal_app import server as server_mod

    previous_overrides = dict(server_mod.app.dependency_overrides)
    previous_agent_app = server_mod._agent_app
    try:
        yield
    finally:
        server_mod.app.dependency_overrides.clear()
        server_mod.app.dependency_overrides.update(previous_overrides)
        server_mod._agent_app = previous_agent_app


def _load_runtime_module(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, RUNTIME_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _wait_ready(client: TestClient, timeout: float = 5.0) -> dict[str, Any]:
    deadline = time.time() + timeout
    last: dict[str, Any] = {}
    while time.time() < deadline:
        ready = client.get("/cloud-agent/runtime/ready")
        try:
            last = ready.json()
        except Exception:
            last = {}
        if ready.status_code == 200:
            return last
        time.sleep(0.05)
    raise AssertionError(f"runtime did not become ready: {last}")


def test_cloud_runtime_boots_agent_application_and_runs_echo_request(
    tmp_path: Path,
    monkeypatch,
) -> None:
    instance_dir = tmp_path / "instance"
    workspace = instance_dir / "workspace"
    sessions = instance_dir / "sessions"
    config_dir = instance_dir / "config"
    assets = config_dir / "assets"
    state = instance_dir / "state"
    for path in (workspace, sessions, assets, state):
        path.mkdir(parents=True, exist_ok=True)
    (state / ".cloud-agent-runtime-ready").write_text("ready", encoding="utf-8")

    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "providers": {
                    "echo": {
                        "provider": "echo_openai_like",
                        "model": "test-model",
                        "stream": False,
                    }
                },
                "plugins": ["plugins.echo_openai_like_provider.EchoOpenAILikeProvider"],
                "agents": {"default": {"provider": "echo"}},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("CLOUD_AGENT_INSTANCE_DIR", str(instance_dir))
    monkeypatch.setenv("CLOUD_AGENT_WORKSPACE_DIR", str(workspace))
    monkeypatch.setenv("CLOUD_AGENT_SESSIONS_DIR", str(sessions))
    monkeypatch.setenv("CLOUD_AGENT_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("CONFIG_DIR", str(assets))
    monkeypatch.setenv("WORKING_DIR", str(workspace))
    monkeypatch.setenv("TRANSFER_DIR", str(tmp_path / "missing-transfer"))
    monkeypatch.delenv("ENABLE_BONJOUR", raising=False)
    monkeypatch.delenv("BRIDGE_URL", raising=False)

    runtime = _load_runtime_module("cloud_agent_runtime_test")
    runtime.server_mod._agent_app = None
    with TestClient(runtime.app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert "runtime_ready" in health.json()
        assert _wait_ready(client)["ready"] is True

        created = client.post("/sessions", json={"agent_id": "default"})
        assert created.status_code == 200
        session_id = created.json()["session"]["session_id"]

        sent = client.post(
            f"/sessions/{session_id}/send_message",
            json={"message": {"role": "user", "content": "hello cloud"}},
        )
        assert sent.status_code == 200

        deadline = time.time() + 5
        contents = []
        while time.time() < deadline:
            messages = client.get(f"/sessions/{session_id}/messages")
            assert messages.status_code == 200
            contents = [
                entry["message"]["content"] for entry in messages.json()["messages"]
            ]
            if len(contents) >= 2:
                break
            time.sleep(0.05)
        assert "hello cloud" in contents
        assert len(contents) >= 2


def test_cloud_runtime_materializes_transfer_and_runs_setup_and_export_scripts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    instance_dir = tmp_path / "instance"
    transfer_dir = tmp_path / "transfer"
    cloud_root = transfer_dir / ".cloud-agent"
    scripts_dir = cloud_root / "scripts"
    config_dir = cloud_root / "config"
    for path in (scripts_dir, config_dir / "assets"):
        path.mkdir(parents=True, exist_ok=True)
    (transfer_dir / "local.txt").write_text("from local\n", encoding="utf-8")
    (config_dir / "config.json").write_text(
        json.dumps(
            {
                "providers": {
                    "echo": {
                        "provider": "echo_openai_like",
                        "model": "test-model",
                        "stream": False,
                    }
                },
                "plugins": ["plugins.echo_openai_like_provider.EchoOpenAILikeProvider"],
                "agents": {"default": {"provider": "echo"}},
            }
        ),
        encoding="utf-8",
    )
    setup_script = scripts_dir / "setup"
    setup_script.write_text(
        '#!/usr/bin/env bash\nset -euo pipefail\nprintf setup > "$CLOUD_WORKSPACE_DIR/setup-ran.txt"\n',
        encoding="utf-8",
    )
    setup_script.chmod(0o755)
    export_script = scripts_dir / "export"
    export_script.write_text(
        '#!/usr/bin/env bash\nset -euo pipefail\ncp "$CLOUD_WORKSPACE_DIR/local.txt" "$TRANSFER_DIR/exported.txt"\n',
        encoding="utf-8",
    )
    export_script.chmod(0o755)

    monkeypatch.setenv("CLOUD_AGENT_INSTANCE_DIR", str(instance_dir))
    monkeypatch.setenv("CLOUD_AGENT_WORKSPACE_DIR", str(instance_dir / "workspace"))
    monkeypatch.setenv("CLOUD_AGENT_SESSIONS_DIR", str(instance_dir / "sessions"))
    monkeypatch.setenv(
        "CLOUD_AGENT_CONFIG_PATH", str(instance_dir / "config" / "config.json")
    )
    monkeypatch.setenv("CONFIG_DIR", str(instance_dir / "config" / "assets"))
    monkeypatch.setenv("WORKING_DIR", str(instance_dir / "workspace"))
    monkeypatch.setenv("TRANSFER_DIR", str(transfer_dir))
    monkeypatch.delenv("ENABLE_BONJOUR", raising=False)
    monkeypatch.delenv("BRIDGE_URL", raising=False)

    runtime = _load_runtime_module("cloud_agent_runtime_scripts_test")
    runtime.server_mod._agent_app = None
    with TestClient(runtime.app) as client:
        assert client.get("/health").status_code == 200
        assert _wait_ready(client)["ready"] is True
        assert (instance_dir / "workspace" / "local.txt").read_text(
            encoding="utf-8"
        ) == "from local\n"
        assert (instance_dir / "workspace" / "setup-ran.txt").read_text(
            encoding="utf-8"
        ) == "setup"

        exported = client.post("/cloud-agent/runtime/export")
        assert exported.status_code == 200
        assert (instance_dir / "transfer" / "export" / "exported.txt").read_text(
            encoding="utf-8"
        ) == "from local\n"


def test_cloud_runtime_health_is_available_before_agent_application_ready(
    tmp_path: Path,
    monkeypatch,
) -> None:
    instance_dir = tmp_path / "instance"
    workspace = instance_dir / "workspace"
    sessions = instance_dir / "sessions"
    config_dir = instance_dir / "config"
    assets = config_dir / "assets"
    state = instance_dir / "state"
    for path in (workspace, sessions, assets, state):
        path.mkdir(parents=True, exist_ok=True)
    (state / ".cloud-agent-runtime-ready").write_text("ready", encoding="utf-8")

    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps({"providers": {}, "plugins": [], "agents": {}}),
        encoding="utf-8",
    )

    monkeypatch.setenv("CLOUD_AGENT_INSTANCE_DIR", str(instance_dir))
    monkeypatch.setenv("CLOUD_AGENT_WORKSPACE_DIR", str(workspace))
    monkeypatch.setenv("CLOUD_AGENT_SESSIONS_DIR", str(sessions))
    monkeypatch.setenv("CLOUD_AGENT_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("CONFIG_DIR", str(assets))
    monkeypatch.setenv("WORKING_DIR", str(workspace))
    monkeypatch.setenv("TRANSFER_DIR", str(tmp_path / "missing-transfer"))
    monkeypatch.delenv("ENABLE_BONJOUR", raising=False)
    monkeypatch.delenv("BRIDGE_URL", raising=False)

    runtime = _load_runtime_module("cloud_agent_runtime_readiness_split_test")
    runtime.server_mod._agent_app = None

    release = False

    class BlockingAgentApplication:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            deadline = time.time() + 2
            while not release and time.time() < deadline:
                time.sleep(0.01)

    monkeypatch.setattr(runtime, "AgentApplication", BlockingAgentApplication)

    with TestClient(runtime.app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["service"] == "cloud-agent-runtime"

        ready = client.get("/cloud-agent/runtime/ready")
        assert ready.status_code == 503
        assert ready.json()["startup_stage"] in {
            "bootstrap_starting",
            "bootstrap_prepare",
            "runtime_env_loading",
            "agent_application_initializing",
        }

        sessions = client.get("/sessions")
        assert sessions.status_code == 503
        assert sessions.json()["detail"]["error"] == "runtime_not_ready"

        release = True
        assert _wait_ready(client)["ready"] is True
