from __future__ import annotations

import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

from sleep_prevention_app import (
    CaffeinateSleepPreventionController,
    SETTING_ENABLED,
    SleepPreventionAppPlugin,
    WakepySleepPreventionController,
    _parse_caffeinate_flags,
)


ROOT = Path(__file__).resolve().parents[3]


class FakeController:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = dict(config or {})
        self.active = False
        self.activate_calls = 0
        self.release_calls = 0

    def activate(self) -> None:
        if not self.active:
            self.activate_calls += 1
        self.active = True

    def release(self) -> None:
        if self.active:
            self.release_calls += 1
        self.active = False

    def status(self) -> dict[str, Any]:
        return {
            "backend": "fake",
            "active": self.active,
            "config": self.config,
        }


def _make_config(tmp_path: Path, *, plugin_spec: str | None = None) -> Path:
    cfg: dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"},
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            plugin_spec or f"path:{ROOT / 'plugins' / 'sleep-prevention-app'}",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "sleep_prevention_caffeinate_flags": "-i -s",
        },
    }
    path = tmp_path / "config_sleep_prevention.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_sleep_prevention_plugin_exposes_server_setting(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        SleepPreventionAppPlugin,
        "controller_factory",
        staticmethod(lambda config: FakeController(config)),
    )
    plugin = SleepPreventionAppPlugin()
    state = plugin.init({})

    elements = plugin.get_ui_elements(state)

    assert elements == [
        {
            "ui_type": "config",
            "scope": "server",
            "key": SETTING_ENABLED,
            "type": "checkbox",
            "label": "Prevent server sleep",
            "description": "Keep this server process awake while enabled.",
            "default": False,
        }
    ]


def test_sleep_prevention_lifecycle_toggles_controller_idempotently(
    monkeypatch: Any,
) -> None:
    controller = FakeController()
    monkeypatch.setattr(
        SleepPreventionAppPlugin,
        "controller_factory",
        staticmethod(lambda config: controller),
    )
    plugin = SleepPreventionAppPlugin()
    state = plugin.init({})

    first = plugin.execute_action(
        app=None,
        action_id="apply_sleep_prevention",
        params={},
        context={"new_settings": {SETTING_ENABLED: True}},
        state=state,
    )
    second = plugin.execute_action(
        app=None,
        action_id="apply_sleep_prevention",
        params={},
        context={"new_settings": {SETTING_ENABLED: True}},
        state=state,
    )
    disabled = plugin.execute_action(
        app=None,
        action_id="apply_sleep_prevention",
        params={},
        context={"new_settings": {SETTING_ENABLED: False}},
        state=state,
    )
    plugin.close(state)

    assert first["enabled"] is True
    assert second["enabled"] is True
    assert disabled["enabled"] is False
    assert controller.activate_calls == 1
    assert controller.release_calls == 1
    assert state["enabled"] is False


def test_sleep_prevention_reads_caffeinate_flags_from_application_config(
    monkeypatch: Any,
) -> None:
    controllers: list[FakeController] = []

    def factory(config: dict[str, Any]) -> FakeController:
        controller = FakeController(config)
        controllers.append(controller)
        return controller

    monkeypatch.setattr(
        SleepPreventionAppPlugin,
        "controller_factory",
        staticmethod(factory),
    )
    plugin = SleepPreventionAppPlugin()
    plugin.init(
        {
            "application": {
                "sleep_prevention": {"caffeinate_flags": "-dims"},
                "sleep_prevention_caffeinate_flags": "-i -s",
            }
        }
    )

    assert controllers[-1].config["caffeinate_flags"] == "-i -s"
    assert _parse_caffeinate_flags(controllers[-1].config["caffeinate_flags"]) == [
        "-i",
        "-s",
    ]


def test_caffeinate_controller_starts_configured_command_and_releases() -> None:
    class FakeProcess:
        def __init__(self) -> None:
            self.terminated = False
            self.killed = False

        def poll(self) -> int | None:
            return None if not self.terminated and not self.killed else 0

        def terminate(self) -> None:
            self.terminated = True

        def kill(self) -> None:
            self.killed = True

        def wait(self, timeout: int | None = None) -> int:
            _ = timeout
            return 0

    calls: list[dict[str, Any]] = []
    process = FakeProcess()

    def fake_popen(args: list[str], **kwargs: Any) -> FakeProcess:
        calls.append({"args": args, "kwargs": kwargs})
        return process

    controller = CaffeinateSleepPreventionController(
        flags=["-i", "-s"],
        popen=fake_popen,
    )

    controller.activate()
    controller.activate()
    controller.release()

    assert calls == [
        {
            "args": ["caffeinate", "-i", "-s"],
            "kwargs": {
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            },
        }
    ]
    assert process.terminated is True
    assert controller.status()["active"] is False


@pytest.mark.integration
def test_caffeinate_controller_releases_real_process_on_macos() -> None:
    if platform.system() != "Darwin":
        pytest.skip("real caffeinate integration is macOS-only")

    command = shutil.which("caffeinate")
    if command is None:
        pytest.skip("caffeinate is not available")

    controller = CaffeinateSleepPreventionController(
        flags=["-i"],
        command=command,
    )
    process: Any | None = None
    try:
        controller.activate()
        process = getattr(controller, "_process", None)
        assert process is not None
        assert process.poll() is None

        controller.release()

        assert process.poll() is not None
        assert controller.status()["active"] is False
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def test_wakepy_controller_uses_keep_running_context() -> None:
    class FakeMode:
        def __init__(self) -> None:
            self.entered = 0
            self.exited = 0

        def __enter__(self) -> "FakeMode":
            self.entered += 1
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            _ = exc_type, exc, tb
            self.exited += 1

    class FakeKeep:
        def __init__(self) -> None:
            self.mode = FakeMode()
            self.running_calls = 0

        def running(self) -> FakeMode:
            self.running_calls += 1
            return self.mode

    keep = FakeKeep()
    controller = WakepySleepPreventionController(keep=keep)

    controller.activate()
    controller.activate()
    controller.release()
    controller.release()

    assert keep.running_calls == 1
    assert keep.mode.entered == 1
    assert keep.mode.exited == 1
    assert controller.status() == {"backend": "wakepy", "active": False}


def test_agent_application_path_plugin_applies_server_setting_with_fake_controller(
    tmp_path: Path,
) -> None:
    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(
        str(config_path),
        str(session_root),
        event_store=InMemoryEventStore(),
    )

    wrapper = getattr(app, "_app_plugins")["sleep_prevention"]
    controller = FakeController({"caffeinate_flags": "-i -s"})
    wrapper.state["controller"] = controller

    app.patch_server_settings({SETTING_ENABLED: True}, source="test")
    assert controller.active is True
    app.close()
    assert controller.active is False


def test_sleep_prevention_applies_startup_replay_context(
    monkeypatch: Any,
) -> None:
    controller = FakeController({"caffeinate_flags": "-i -s"})
    monkeypatch.setattr(
        SleepPreventionAppPlugin,
        "controller_factory",
        staticmethod(lambda config: controller),
    )
    plugin = SleepPreventionAppPlugin()
    state = plugin.init({})

    result = plugin.execute_action(
        app=None,
        action_id="apply_sleep_prevention",
        params={},
        context={
            "source": "startup",
            "new_settings": {SETTING_ENABLED: True},
        },
        state=state,
    )

    assert result["enabled"] is True
    assert controller.active is True
    plugin.close(state)
    assert controller.active is False
