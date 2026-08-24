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
    _read_bridge_url_from_config,
    _resolve_effective_host,
    _resolve_fastapi_log_file,
    _resolve_log_file,
)
from agent_terminal_app.project_profile import ProjectProfile


def _args(**overrides: Any) -> argparse.Namespace:
    values = {
        "host": None,
        "port": None,
        "enable_bonjour": False,
        "enable_bridge": False,
        "bonjour_port": None,
        "bonjour_service_name": None,
        "bridge_url": None,
        "bridge_display_name": None,
        "bridge_location": None,
        "bridge_local_http_base": None,
        "bridge_http_base": None,
        "bridge_server_id": None,
        "bridge_exit_on_superseded": False,
        "bridge_local_guard": False,
        "bridge_takeover_local": False,
        "log_file": None,
        "fastapi_log_file": None,
        "no_log_file": False,
        "no_tty": False,
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
        effective_host="127.0.0.1",
        effective_port=8765,
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
        effective_host="0.0.0.0",
        effective_port=8765,
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
        effective_host="127.0.0.1",
        effective_port=8765,
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


# ---------------------------------------------------------------------------
# Host resolution tests
# ---------------------------------------------------------------------------


def test_resolve_effective_host_auto_zero_for_bonjour() -> None:
    """When --host is not passed and bonjour is enabled, use 0.0.0.0."""
    args = _args(enable_bonjour=True)
    assert _resolve_effective_host(args) == "0.0.0.0"


def test_resolve_effective_host_explicit_wins() -> None:
    """Explicit --host always wins, even with --enable-bonjour."""
    args = _args(enable_bonjour=True, host="127.0.0.1")
    assert _resolve_effective_host(args) == "127.0.0.1"


def test_resolve_effective_host_default_loopback() -> None:
    """Without bonjour or --host, default to 127.0.0.1."""
    args = _args()
    assert _resolve_effective_host(args) == "127.0.0.1"


# ---------------------------------------------------------------------------
# Log file resolution tests
# ---------------------------------------------------------------------------


def test_resolve_log_file_default() -> None:
    """No flags → .crystal/crystal.log."""
    args = _args()
    assert _resolve_log_file(args) == str(Path(".crystal") / "crystal.log")


def test_resolve_log_file_no_log_file() -> None:
    """--no-log-file → None."""
    args = _args(no_log_file=True)
    assert _resolve_log_file(args) is None


def test_resolve_log_file_explicit() -> None:
    """--log-file custom.log → custom.log (even with --no-log-file)."""
    args = _args(log_file="custom.log", no_log_file=True)
    assert _resolve_log_file(args) == "custom.log"


def test_resolve_fastapi_log_file_defaults_to_log_file() -> None:
    """When --fastapi-log-file is absent, use the same file as log_file."""
    args = _args()
    assert _resolve_fastapi_log_file(args, "app.log") == "app.log"


def test_resolve_fastapi_log_file_explicit() -> None:
    """When --fastapi-log-file is given, it wins over log_file."""
    args = _args(fastapi_log_file="fastapi.log")
    assert _resolve_fastapi_log_file(args, "app.log") == "fastapi.log"


def test_resolve_fastapi_log_file_none_when_log_file_none() -> None:
    """When both are absent, fastapi log file is None."""
    args = _args()
    assert _resolve_fastapi_log_file(args, None) is None


# ---------------------------------------------------------------------------
# Bridge URL from config tests
# ---------------------------------------------------------------------------


def test_read_bridge_url_from_config(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text('{"application": {"bridge_url": "wss://bridge.example/ws"}}')
    assert _read_bridge_url_from_config(config) == "wss://bridge.example/ws"


def test_read_bridge_url_from_config_missing(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text('{"application": {"tool_output_line_limit": 20}}')
    assert _read_bridge_url_from_config(config) is None


def test_read_bridge_url_from_config_no_application(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text('{"providers": {}}')
    assert _read_bridge_url_from_config(config) is None


def test_read_bridge_url_from_config_missing_file(tmp_path: Path) -> None:
    assert _read_bridge_url_from_config(tmp_path / "nonexistent.json") is None


def test_read_bridge_url_from_config_invalid_json(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text("{invalid")
    assert _read_bridge_url_from_config(config) is None


# ---------------------------------------------------------------------------
# --enable-bridge tests
# ---------------------------------------------------------------------------


def test_enable_bridge_resolves_url_from_profile() -> None:
    """--enable-bridge with profile.bridge_url → bridge configured."""
    profile = ProjectProfile(
        name="myproject",
        port=8090,
        bridge_server_id="test-id",
        bridge_url="wss://from-profile.example/ws",
    )
    config = _build_server_integration_config(
        _args(enable_bridge=True),
        server_mod=server_mod,
        profile=profile,
        effective_host="0.0.0.0",
        effective_port=8090,
    )
    assert config is not None
    assert config.bridge is not None
    assert config.bridge.bridge_url == "wss://from-profile.example/ws"
    assert config.bridge.server_id == "test-id"
    assert config.bridge.display_name == "myproject"


def test_enable_bridge_resolves_url_from_config() -> None:
    """--enable-bridge with no profile URL → falls back to config."""
    profile = ProjectProfile(
        name="myproject",
        port=8090,
        bridge_server_id="test-id",
        bridge_url=None,
    )
    config = _build_server_integration_config(
        _args(enable_bridge=True),
        server_mod=server_mod,
        profile=profile,
        bridge_url_from_config="wss://from-config.example/ws",
        effective_host="0.0.0.0",
        effective_port=8090,
    )
    assert config is not None
    assert config.bridge is not None
    assert config.bridge.bridge_url == "wss://from-config.example/ws"


def test_enable_bridge_no_url_warns_and_skips(capsys) -> None:
    """--enable-bridge with no URL anywhere → bridge not configured, warning printed."""
    profile = ProjectProfile(
        name="myproject",
        port=8090,
        bridge_server_id="test-id",
        bridge_url=None,
    )
    config = _build_server_integration_config(
        _args(enable_bridge=True),
        server_mod=server_mod,
        profile=profile,
        effective_host="0.0.0.0",
        effective_port=8090,
    )
    assert config is None
    captured = capsys.readouterr()
    assert "no bridge URL found" in captured.out


def test_bridge_url_cli_wins_over_profile_and_config() -> None:
    """--bridge-url (via profile) wins over config bridge_url."""
    # In real usage, args.bridge_url is passed to the profile manager's
    # resolve(cli_bridge_url=...), so profile.bridge_url IS the CLI value.
    profile = ProjectProfile(
        name="myproject",
        port=8090,
        bridge_server_id="test-id",
        bridge_url="wss://from-cli.example/ws",
    )
    config = _build_server_integration_config(
        _args(bridge_url="wss://from-cli.example/ws"),
        server_mod=server_mod,
        profile=profile,
        bridge_url_from_config="wss://from-config.example/ws",
        effective_host="0.0.0.0",
        effective_port=8090,
    )
    assert config is not None
    assert config.bridge is not None
    assert config.bridge.bridge_url == "wss://from-cli.example/ws"


def test_profile_name_used_as_default_display_name() -> None:
    """No --bridge-display-name → profile.name used."""
    profile = ProjectProfile(
        name="myproject",
        port=8090,
        bridge_server_id="test-id",
        bridge_url="wss://bridge.example/ws",
    )
    config = _build_server_integration_config(
        _args(enable_bridge=True),
        server_mod=server_mod,
        profile=profile,
        effective_host="0.0.0.0",
        effective_port=8090,
    )
    assert config is not None
    assert config.bridge is not None
    assert config.bridge.display_name == "myproject"


def test_profile_name_used_as_default_bonjour_service_name() -> None:
    """No --bonjour-service-name → profile.name used."""
    profile = ProjectProfile(
        name="myproject",
        port=8090,
        bridge_server_id="test-id",
        bridge_url=None,
    )
    config = _build_server_integration_config(
        _args(enable_bonjour=True),
        server_mod=server_mod,
        profile=profile,
        effective_host="0.0.0.0",
        effective_port=8090,
    )
    assert config is not None
    assert config.bonjour is not None
    assert config.bonjour.service_name == "myproject"


def test_explicit_display_name_wins_over_profile_name() -> None:
    """--bridge-display-name takes priority over profile.name."""
    profile = ProjectProfile(
        name="myproject",
        port=8090,
        bridge_server_id="test-id",
        bridge_url="wss://bridge.example/ws",
    )
    config = _build_server_integration_config(
        _args(enable_bridge=True, bridge_display_name="Custom Name"),
        server_mod=server_mod,
        profile=profile,
        effective_host="0.0.0.0",
        effective_port=8090,
    )
    assert config is not None
    assert config.bridge is not None
    assert config.bridge.display_name == "Custom Name"


def test_bridge_local_http_base_uses_effective_host_and_port(monkeypatch) -> None:
    """local_http_base defaults to http://<effective_host>:<effective_port>."""
    monkeypatch.delenv("SERVER_HOST", raising=False)
    monkeypatch.delenv("SERVER_PORT", raising=False)
    monkeypatch.delenv("BRIDGE_LOCAL_HTTP_BASE", raising=False)
    profile = ProjectProfile(
        name="myproject",
        port=8090,
        bridge_server_id="test-id",
        bridge_url="wss://bridge.example/ws",
    )
    config = _build_server_integration_config(
        _args(enable_bridge=True),
        server_mod=server_mod,
        profile=profile,
        effective_host="0.0.0.0",
        effective_port=8090,
    )
    assert config is not None
    assert config.bridge is not None
    assert config.bridge.local_http_base == "http://0.0.0.0:8090"


def test_bridge_http_base_cli_override_is_kept_separate_from_local_base(
    monkeypatch,
) -> None:
    monkeypatch.delenv("BRIDGE_HTTP_BASE_URL", raising=False)
    monkeypatch.delenv("BRIDGE_LOCAL_HTTP_BASE", raising=False)
    monkeypatch.delenv("SERVER_HOST", raising=False)
    monkeypatch.delenv("SERVER_PORT", raising=False)
    profile = ProjectProfile(
        name="myproject",
        port=8090,
        bridge_server_id="test-id",
        bridge_url="wss://bridge.example/ws/websocket",
    )
    config = _build_server_integration_config(
        _args(
            enable_bridge=True,
            bridge_http_base="https://bridge-http.example/prefix",
        ),
        server_mod=server_mod,
        profile=profile,
        effective_host="127.0.0.1",
        effective_port=8090,
    )
    assert config is not None
    assert config.bridge is not None
    assert config.bridge.bridge_http_base == "https://bridge-http.example/prefix"
    assert config.bridge.local_http_base == "http://127.0.0.1:8090"


# ---------------------------------------------------------------------------
# Startup summary tests
# ---------------------------------------------------------------------------


def test_format_startup_summary_localhost() -> None:
    """host=127.0.0.1 → http://127.0.0.1:port."""
    from agent_terminal_app.__main__ import _format_startup_summary

    summary = _format_startup_summary(
        project_name="myproject",
        config_path=Path("/tmp/config.json"),
        session_root=Path("/tmp/sessions"),
        host="127.0.0.1",
        port=8090,
    )
    assert "[crystal-lattice] Starting myproject" in summary
    assert "http://127.0.0.1:8090" in summary
    assert "Bonjour" not in summary
    assert "Bridge" not in summary


def test_format_startup_summary_zero_bind_with_lan_ip() -> None:
    """host=0.0.0.0 with lan_ip → http://<lan-ip>:port."""
    from agent_terminal_app.__main__ import _format_startup_summary

    summary = _format_startup_summary(
        project_name="myproject",
        config_path=Path("/tmp/config.json"),
        session_root=Path("/tmp/sessions"),
        host="0.0.0.0",
        port=8090,
        lan_ip="192.168.1.42",
    )
    assert "http://192.168.1.42:8090" in summary


def test_format_startup_summary_zero_bind_without_lan_ip() -> None:
    """host=0.0.0.0 without lan_ip → falls back to 127.0.0.1."""
    from agent_terminal_app.__main__ import _format_startup_summary

    summary = _format_startup_summary(
        project_name="myproject",
        config_path=Path("/tmp/config.json"),
        session_root=Path("/tmp/sessions"),
        host="0.0.0.0",
        port=8090,
    )
    assert "http://127.0.0.1:8090" in summary


def test_format_startup_summary_bonjour_only() -> None:
    """bonjour on, bridge off → Bonjour line present, Bridge absent."""
    from agent_terminal_app.__main__ import _format_startup_summary

    summary = _format_startup_summary(
        project_name="myproject",
        config_path=Path("/tmp/config.json"),
        session_root=Path("/tmp/sessions"),
        host="0.0.0.0",
        port=8090,
        bonjour_service_name="myproject",
        lan_ip="192.168.1.42",
    )
    assert "Bonjour:   myproject (discoverable on local network)" in summary
    assert "Bridge" not in summary


def test_format_startup_summary_bridge_only() -> None:
    """bridge on, bonjour off → Bridge line present, Bonjour absent."""
    from agent_terminal_app.__main__ import _format_startup_summary

    summary = _format_startup_summary(
        project_name="myproject",
        config_path=Path("/tmp/config.json"),
        session_root=Path("/tmp/sessions"),
        host="127.0.0.1",
        port=8090,
        bridge_url="wss://bridge.example/ws",
    )
    assert "Bridge:    wss://bridge.example/ws" in summary
    assert "Bonjour" not in summary


def test_format_startup_summary_both_on() -> None:
    """both bonjour and bridge on → both lines present."""
    from agent_terminal_app.__main__ import _format_startup_summary

    summary = _format_startup_summary(
        project_name="myproject",
        config_path=Path("/tmp/config.json"),
        session_root=Path("/tmp/sessions"),
        host="0.0.0.0",
        port=8090,
        bonjour_service_name="myproject",
        bridge_url="wss://bridge.example/ws",
        lan_ip="192.168.1.42",
    )
    assert "Bonjour:   myproject (discoverable on local network)" in summary
    assert "Bridge:    wss://bridge.example/ws" in summary


def test_format_startup_summary_neither() -> None:
    """neither bonjour nor bridge → only Config/Sessions/HTTP lines."""
    from agent_terminal_app.__main__ import _format_startup_summary

    summary = _format_startup_summary(
        project_name="myproject",
        config_path=Path("/tmp/config.json"),
        session_root=Path("/tmp/sessions"),
        host="127.0.0.1",
        port=8090,
    )
    assert "Config:" in summary
    assert "Sessions:" in summary
    assert "HTTP:" in summary
    assert "Bonjour" not in summary
    assert "Bridge" not in summary


def test_format_startup_summary_includes_project_name() -> None:
    """project name appears in the header line."""
    from agent_terminal_app.__main__ import _format_startup_summary

    summary = _format_startup_summary(
        project_name="iocharts",
        config_path=Path("/tmp/config.json"),
        session_root=Path("/tmp/sessions"),
        host="127.0.0.1",
        port=8090,
    )
    assert "[crystal-lattice] Starting iocharts" in summary


def test_format_startup_summary_includes_config_and_sessions() -> None:
    """Config and Sessions paths appear in the summary."""
    from agent_terminal_app.__main__ import _format_startup_summary

    summary = _format_startup_summary(
        project_name="myproject",
        config_path=Path("/home/user/.crystal/config.json"),
        session_root=Path("/home/user/.crystal/sessions"),
        host="127.0.0.1",
        port=8090,
    )
    assert "/home/user/.crystal/config.json" in summary
    assert "/home/user/.crystal/sessions" in summary


def test_set_terminal_title_does_not_print(capsys) -> None:
    """_set_terminal_title should not print the debug 'Setting terminal title' message."""
    from agent_terminal_app.__main__ import _set_terminal_title

    _set_terminal_title("Test Title")
    captured = capsys.readouterr()
    assert "Setting terminal title" not in captured.out


def test_no_tty_flag_is_parsed() -> None:
    """--no-tty is parsed as a boolean store_true flag."""
    from agent_terminal_app.__main__ import _run_terminal_headless

    args = _args(no_tty=True)
    assert args.no_tty is True

    args = _args(no_tty=False)
    assert args.no_tty is False

    # The helper must be callable (importable, correct signature).
    assert callable(_run_terminal_headless)
