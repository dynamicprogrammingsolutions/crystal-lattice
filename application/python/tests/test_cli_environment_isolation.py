from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
from typing import Any

from agent_terminal_app import server as server_mod
from agent_terminal_app.__main__ import (
    _application_action_map,
    _build_server_integration_config,
    _collect_additional_dotenv_values,
    _parse_contributed_command,
)


def _args(**overrides: Any) -> argparse.Namespace:
    values = {
        "host": "127.0.0.1",
        "port": 8765,
        "enable_bonjour": False,
        "bonjour_port": None,
        "bonjour_service_name": None,
        "bridge_url": None,
        "bridge_display_name": None,
        "bridge_location": None,
        "bridge_local_http_base": None,
        "bridge_server_id": None,
        "bridge_exit_on_superseded": False,
        "bridge_local_guard": False,
        "bridge_takeover_local": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_collect_additional_dotenv_values_does_not_mutate_process_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    (config_dir / ".env").write_text(
        "DOTENV_ONLY=from-config\n"
        "DOTENV_SHARED=from-config\n"
        "DOTENV_EXISTING=from-config\n",
        encoding="utf-8",
    )

    local_crystal = tmp_path / ".crystal"
    local_crystal.mkdir()
    (local_crystal / ".env").write_text(
        "DOTENV_SHARED=from-local\nDOTENV_LOCAL_ONLY=from-local\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DOTENV_EXISTING", "from-process")
    monkeypatch.delenv("DOTENV_ONLY", raising=False)
    monkeypatch.delenv("DOTENV_SHARED", raising=False)
    monkeypatch.delenv("DOTENV_LOCAL_ONLY", raising=False)

    values = _collect_additional_dotenv_values(config_path)

    assert values["DOTENV_ONLY"] == "from-config"
    assert values["DOTENV_SHARED"] == "from-config"
    assert values["DOTENV_LOCAL_ONLY"] == "from-local"
    assert "DOTENV_EXISTING" not in values
    assert "DOTENV_ONLY" not in os.environ
    assert os.environ["DOTENV_EXISTING"] == "from-process"


def test_cli_bridge_config_does_not_populate_process_env(monkeypatch) -> None:
    monkeypatch.delenv("BRIDGE_URL", raising=False)
    monkeypatch.delenv("BRIDGE_SERVER_ID", raising=False)

    config = _build_server_integration_config(
        _args(
            bridge_url="wss://bridge.example/ws/websocket",
            bridge_display_name="crystal",
            bridge_server_id="server-123",
        ),
        server_mod=server_mod,
    )

    assert config is not None
    assert config.bridge is not None
    assert config.bridge.bridge_url == "wss://bridge.example/ws/websocket"
    assert config.bridge.display_name == "crystal"
    assert config.bridge.server_id == "server-123"
    assert "BRIDGE_URL" not in os.environ
    assert "BRIDGE_SERVER_ID" not in os.environ


def test_cli_bonjour_config_does_not_populate_process_env(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_BONJOUR", raising=False)
    monkeypatch.delenv("BONJOUR_PORT", raising=False)
    monkeypatch.delenv("BONJOUR_SERVICE_NAME", raising=False)

    config = _build_server_integration_config(
        _args(
            enable_bonjour=True,
            bonjour_port=12345,
            bonjour_service_name="Crystal",
        ),
        server_mod=server_mod,
    )

    assert config is not None
    assert config.bonjour is not None
    assert config.bonjour.port == 12345
    assert config.bonjour.service_name == "Crystal"
    assert "ENABLE_BONJOUR" not in os.environ
    assert "BONJOUR_PORT" not in os.environ
    assert "BONJOUR_SERVICE_NAME" not in os.environ


def test_cli_bridge_config_preserves_external_env_as_fallback(monkeypatch) -> None:
    monkeypatch.setenv("BRIDGE_SERVER_ID", "from-process-env")

    config = _build_server_integration_config(
        _args(bridge_url="wss://bridge.example/ws/websocket"),
        server_mod=server_mod,
    )

    assert config is not None
    assert config.bridge is not None
    assert config.bridge.server_id == "from-process-env"
    assert os.environ["BRIDGE_SERVER_ID"] == "from-process-env"


def test_server_startup_uses_explicit_bridge_config_without_env(
    monkeypatch,
) -> None:
    created_configs: list[Any] = []

    class FakeBridgeClient:
        def __init__(self, config: Any) -> None:
            self.config = config
            created_configs.append(config)

        async def run(self) -> None:
            return None

        async def stop(self) -> None:
            return None

    monkeypatch.delenv("BRIDGE_URL", raising=False)
    monkeypatch.delenv("ENABLE_BONJOUR", raising=False)
    monkeypatch.setattr(server_mod.bridge_mod, "BridgeClient", FakeBridgeClient)
    config = server_mod.ServerIntegrationRuntimeConfig(
        bridge=server_mod.bridge_mod.BridgeConfig(
            bridge_url="wss://explicit.example/ws/websocket",
            server_id="explicit-server",
            display_name="Explicit",
            computer_name="test-host",
            location=None,
            local_http_base="http://127.0.0.1:8765",
        )
    )

    try:
        server_mod.configure_integrations(config)
        asyncio.run(server_mod._on_startup())

        assert len(created_configs) == 1
        assert created_configs[0].bridge_url == "wss://explicit.example/ws/websocket"
        assert created_configs[0].server_id == "explicit-server"
        assert "BRIDGE_URL" not in os.environ
    finally:
        asyncio.run(server_mod._on_shutdown())
        server_mod.clear_configured_integrations()


def test_server_startup_direct_env_bridge_fallback_still_works(monkeypatch) -> None:
    created_configs: list[Any] = []

    class FakeBridgeClient:
        def __init__(self, config: Any) -> None:
            self.config = config
            created_configs.append(config)

        async def run(self) -> None:
            return None

        async def stop(self) -> None:
            return None

    monkeypatch.setenv("BRIDGE_URL", "wss://env.example/ws/websocket")
    monkeypatch.setenv("BRIDGE_SERVER_ID", "env-server")
    monkeypatch.setenv("SERVER_HOST", "127.0.0.1")
    monkeypatch.setenv("SERVER_PORT", "9876")
    monkeypatch.delenv("ENABLE_BONJOUR", raising=False)
    monkeypatch.setattr(server_mod.bridge_mod, "BridgeClient", FakeBridgeClient)

    try:
        server_mod.clear_configured_integrations()
        asyncio.run(server_mod._on_startup())

        assert len(created_configs) == 1
        assert created_configs[0].bridge_url == "wss://env.example/ws/websocket"
        assert created_configs[0].server_id == "env-server"
        assert created_configs[0].local_http_base == "http://127.0.0.1:9876"
    finally:
        asyncio.run(server_mod._on_shutdown())
        server_mod.clear_configured_integrations()


def test_parse_contributed_command_uses_action_input_contract() -> None:
    command = {
        "name": "validate-cloud",
        "description": "Validate cloud workspace.",
        "action_id": "cloud.validate_cloud",
        "args": [
            {"name": "workspace_dir", "flags": ["--workspace-dir"]},
            {"name": "keep_temp_dir", "flags": ["--keep-temp-dir"]},
        ],
    }
    action = {
        "plugin": "cloud",
        "id": "cloud.validate_cloud",
        "inputs": {
            "workspace_dir": {"type": "string", "required": False},
            "keep_temp_dir": {"type": "boolean", "required": False, "default": False},
        },
    }

    parsed = _parse_contributed_command(
        command,
        action,
        ["--workspace-dir", "/tmp/project", "--keep-temp-dir"],
    )

    assert parsed == {
        "workspace_dir": "/tmp/project",
        "keep_temp_dir": True,
    }


def test_application_action_map_indexes_plugin_actions() -> None:
    class _FakeApp:
        def get_application_actions(self):
            return [
                {"plugin": "cloud", "id": "cloud.validate_cloud"},
                {"plugin": "dummy", "id": "dummy.do_it"},
            ]

    mapped = _application_action_map(_FakeApp())

    assert set(mapped) == {
        ("cloud", "cloud.validate_cloud"),
        ("dummy", "dummy.do_it"),
    }
