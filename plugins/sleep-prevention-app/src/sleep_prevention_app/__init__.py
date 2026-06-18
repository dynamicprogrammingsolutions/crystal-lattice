from __future__ import annotations

"""Application plugin for process-lifetime sleep prevention."""

import platform
import shlex
import subprocess
from typing import Any, Protocol


SETTING_ENABLED = "sleep_prevention_enabled"
DEFAULT_CAFFEINATE_FLAGS = ["-is"]


class SleepPreventionController(Protocol):
    def activate(self) -> None:
        ...

    def release(self) -> None:
        ...

    def status(self) -> dict[str, Any]:
        ...


def _parse_caffeinate_flags(raw: Any) -> list[str]:
    if raw is None:
        return list(DEFAULT_CAFFEINATE_FLAGS)
    if isinstance(raw, str):
        parsed = shlex.split(raw)
        return parsed or list(DEFAULT_CAFFEINATE_FLAGS)
    if isinstance(raw, list):
        parsed = [item for item in raw if isinstance(item, str) and item.strip()]
        return parsed or list(DEFAULT_CAFFEINATE_FLAGS)
    return list(DEFAULT_CAFFEINATE_FLAGS)


def _sleep_prevention_config(app_config: dict[str, Any]) -> dict[str, Any]:
    application = app_config.get("application")
    if not isinstance(application, dict):
        return {}
    nested = application.get("sleep_prevention")
    if isinstance(nested, dict):
        merged = dict(nested)
    else:
        merged = {}
    if "sleep_prevention_caffeinate_flags" in application:
        merged["caffeinate_flags"] = application["sleep_prevention_caffeinate_flags"]
    return merged


class CaffeinateSleepPreventionController:
    def __init__(
        self,
        *,
        flags: list[str] | None = None,
        command: str = "caffeinate",
        popen: Any = subprocess.Popen,
    ) -> None:
        self._flags = list(flags or DEFAULT_CAFFEINATE_FLAGS)
        self._command = command
        self._popen = popen
        self._process: Any | None = None

    @property
    def command_line(self) -> list[str]:
        return [self._command, *self._flags]

    def activate(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return
        self._process = self._popen(
            self.command_line,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def release(self) -> None:
        process = self._process
        self._process = None
        if process is None:
            return
        if process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    def status(self) -> dict[str, Any]:
        active = self._process is not None and self._process.poll() is None
        return {
            "backend": "caffeinate",
            "active": active,
            "command": self.command_line,
        }


class WakepySleepPreventionController:
    def __init__(self, *, keep: Any | None = None) -> None:
        self._keep = keep
        self._mode: Any | None = None

    def _load_keep(self) -> Any:
        if self._keep is not None:
            return self._keep
        from wakepy import keep  # type: ignore[import-not-found]

        self._keep = keep
        return keep

    def activate(self) -> None:
        if self._mode is not None:
            return
        keep = self._load_keep()
        mode = keep.running()
        mode.__enter__()
        self._mode = mode

    def release(self) -> None:
        mode = self._mode
        self._mode = None
        if mode is None:
            return
        mode.__exit__(None, None, None)

    def status(self) -> dict[str, Any]:
        return {
            "backend": "wakepy",
            "active": self._mode is not None,
        }


def build_sleep_prevention_controller(
    config: dict[str, Any],
    *,
    system_name: str | None = None,
) -> SleepPreventionController:
    if system_name is None:
        system_name = platform.system()
    if system_name == "Darwin":
        return CaffeinateSleepPreventionController(
            flags=_parse_caffeinate_flags(config.get("caffeinate_flags")),
        )
    return WakepySleepPreventionController()


class SleepPreventionAppPlugin:
    name = "sleep_prevention"
    version = "1.0.0"

    controller_factory = staticmethod(build_sleep_prevention_controller)

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "sleep_prevention_caffeinate_flags": {
                "type": ["string", "array"],
                "description": (
                    "macOS caffeinate flags used when sleep prevention is "
                    "enabled. Defaults to '-is'."
                ),
                "default": "-is",
            }
        }

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        config = _sleep_prevention_config(app_config)
        controller = self.controller_factory(config)
        return {
            "config": config,
            "controller": controller,
            "enabled": False,
            "last_status": controller.status(),
        }

    def get_ui_elements(
        self,
        state: dict[str, Any],
        config: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        _ = state, config, context
        return [
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

    def get_commands(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return []

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [
            {
                "id": "apply_sleep_prevention",
                "label": "Apply sleep prevention setting",
                "description": "Apply the process-level sleep prevention setting.",
                "inputs": {},
                "trigger": "server_settings_changed",
            }
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: dict[str, Any],
        context: dict[str, Any] | None,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        _ = params
        if action_id != "apply_sleep_prevention":
            raise ValueError(f"Unknown action_id {action_id!r} for SleepPreventionAppPlugin")

        settings = {}
        if isinstance(context, dict):
            raw_settings = context.get("new_settings")
            if isinstance(raw_settings, dict):
                settings = raw_settings
        if not settings and hasattr(app, "get_server_settings"):
            raw_settings = app.get_server_settings()
            if isinstance(raw_settings, dict):
                settings = raw_settings

        enabled = bool(settings.get(SETTING_ENABLED, False))
        controller = state.get("controller")
        if not _is_controller(controller):
            controller = self.controller_factory(state.get("config") or {})
            state["controller"] = controller

        if enabled:
            controller.activate()
        else:
            controller.release()

        status = controller.status()
        state["enabled"] = enabled
        state["last_status"] = status
        return {
            "enabled": enabled,
            "status": status,
        }

    def close(self, state: dict[str, Any]) -> None:
        controller = state.get("controller")
        if _is_controller(controller):
            controller.release()
            state["enabled"] = False
            state["last_status"] = controller.status()


def _is_controller(value: Any) -> bool:
    return (
        hasattr(value, "activate")
        and callable(value.activate)
        and hasattr(value, "release")
        and callable(value.release)
        and hasattr(value, "status")
        and callable(value.status)
    )


__all__ = [
    "CaffeinateSleepPreventionController",
    "DEFAULT_CAFFEINATE_FLAGS",
    "SETTING_ENABLED",
    "SleepPreventionAppPlugin",
    "WakepySleepPreventionController",
    "build_sleep_prevention_controller",
]