from __future__ import annotations

import time
from typing import Any


def command_result(
    command: str,
    output: str,
    *,
    exit_code: int = 0,
    started: float | None = None,
    truncated: bool = False,
) -> dict[str, Any]:
    duration = max(0.0, time.monotonic() - started) if started is not None else 0.0
    lines = [
        f"Command: {command}",
        f"Exit code: {exit_code}",
        f"Wall time: {duration:.1f} seconds",
    ]
    if truncated:
        lines.append("Output truncated: yes")
    lines.append(output)
    return {
        "success": exit_code == 0,
        "output": "\n".join(lines),
        "command": command,
        "exit_code": exit_code,
        "duration_seconds": duration,
        "truncated": truncated,
    }


def command_error(
    command: str,
    message: str,
    *,
    exit_code: int = 2,
    started: float | None = None,
) -> dict[str, Any]:
    return command_result(
        command,
        message,
        exit_code=exit_code,
        started=started,
    )


class CommandResultMixin:
    def format_tool_result(
        self,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> str:
        _ = state
        return str(result.get("output") or result.get("error") or "")

    def to_display_format(
        self,
        text: str,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        _ = state
        return {
            "type": "text",
            "content": text,
            "single_line": str(result.get("command") or self.name),
        }