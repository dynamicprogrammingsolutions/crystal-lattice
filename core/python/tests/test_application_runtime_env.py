from __future__ import annotations

import gc
import json
import os
from pathlib import Path

import pytest

from agent_app.application_future import AgentApplication
from agent_app.config import build_agent_config
from agent_app.runtime_env import RuntimeEnvOverlay
from agent_core import AgentCore

from .dummy_app_plugin import DummyAppPlugin  # noqa: F401
from .dummy_provider import DummyProvider  # noqa: F401


def _write_config(tmp_path: Path) -> Path:
    cfg = {
        "providers": {"dummy": {"provider": "dummy_provider", "model": "test-model"}},
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_app_plugin.DummyAppPlugin",
        ],
        "agents": {
            "default": {"provider": "dummy"},
        },
        "application": {},
    }
    path = tmp_path / "config_runtime_env.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_application_plugins_receive_runtime_env_overlay_and_agent_config_stays_clean(
    tmp_path: Path,
) -> None:
    config_path = _write_config(tmp_path)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
        env_overrides={"CONFIG_DIR": str(tmp_path / "override-config")},
    )

    try:
        wrapper = app._app_plugins["dummy_app_plugin"]
        plugin = wrapper.plugin
        assert isinstance(plugin, DummyAppPlugin)
        assert plugin.init_config is not None
        assert os.environ["CONFIG_DIR"] == str(tmp_path / "override-config")

        base_config = build_agent_config(app._config, "default")
        assert "_resolved_env" not in base_config
        assert app.get_resolved_env()["CONFIG_DIR"] == str(tmp_path / "override-config")
    finally:
        app.close()


def test_agent_application_config_env_resolves_without_runtime_overlay(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config_config_env.json"
    config_path.write_text(
        json.dumps(
            {
                "providers": {
                    "dummy": {
                        "provider": "dummy_provider",
                        "model": "${env:CONFIG_ONLY_MODEL}",
                    }
                },
                "plugins": ["tests.dummy_provider.DummyProvider"],
                "agents": {"default": {"provider": "dummy"}},
            }
        ),
        encoding="utf-8",
    )
    previous = os.environ.get("CONFIG_ONLY_MODEL")
    os.environ.pop("CONFIG_ONLY_MODEL", None)

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
        config_env={"CONFIG_ONLY_MODEL": "from-config-env"},
    )
    try:
        assert app._agent_base_configs["default"]["model"] == "from-config-env"
        assert app.get_resolved_env()["CONFIG_ONLY_MODEL"] == "from-config-env"
        assert "CONFIG_ONLY_MODEL" not in os.environ
    finally:
        app.close()
        if previous is not None:
            os.environ["CONFIG_ONLY_MODEL"] = previous


def test_runtime_env_overlay_restores_previous_process_env(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    previous = os.environ.get("CONFIG_DIR")
    os.environ["CONFIG_DIR"] = "before-app"
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
        env_overrides={"CONFIG_DIR": str(tmp_path / "override-config")},
    )
    try:
        assert os.environ["CONFIG_DIR"] == str(tmp_path / "override-config")
    finally:
        app.close()
    if previous is None:
        assert os.environ["CONFIG_DIR"] == "before-app"
        os.environ.pop("CONFIG_DIR", None)
    else:
        assert os.environ["CONFIG_DIR"] == "before-app"
        os.environ["CONFIG_DIR"] = previous


def test_runtime_env_overlay_rejects_conflicting_live_apps(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
        env_overrides={"CONFIG_DIR": str(tmp_path / "config-a")},
    )
    try:
        with pytest.raises(
            RuntimeError, match="Conflicting runtime environment overlay"
        ):
            AgentApplication(
                str(config_path),
                str(tmp_path / "sessions-b"),
                core_factory=AgentCore,
                env_overrides={"CONFIG_DIR": str(tmp_path / "config-b")},
            )
    finally:
        app.close()


def test_runtime_env_overlay_gc_cleanup_during_install_does_not_deadlock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key = "CRYSTAL_TEST_RUNTIME_ENV_OVERLAY_DEADLOCK"
    previous = os.environ.get(key)
    os.environ.pop(key, None)

    first = RuntimeEnvOverlay({key: "first"})
    second = RuntimeEnvOverlay({key: "second"})
    first.install()

    def _collect() -> int:
        first.close()
        return 0

    monkeypatch.setattr(gc, "collect", _collect)
    try:
        second.install()
        assert os.environ[key] == "second"
    finally:
        second.close()
        first.close()
        if previous is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous
