"""Shared terminal rendering for action results and follow-ups."""

from __future__ import annotations

import os
import sys
from typing import Any, Callable, Mapping, TextIO


RunActionReference = Callable[[Mapping[str, Any]], str]


def render_action_result(
    result: Mapping[str, Any],
    write: Callable[[str], None],
    *,
    register_run_action: RunActionReference | None = None,
) -> None:
    """Render one action result consistently across terminal frontends."""

    display = result.get("display")
    if not isinstance(display, Mapping):
        write("[action] completed")
        return

    title = display.get("title")
    body = display.get("body")
    variant = display.get("variant")
    if isinstance(title, str) and title:
        prefix = f"[{variant}] " if isinstance(variant, str) and variant else ""
        write(f"{prefix}{title}")
    if isinstance(body, str) and body:
        write(body)

    actions = display.get("actions")
    for action in actions if isinstance(actions, list) else []:
        if not isinstance(action, Mapping):
            continue
        kind = action.get("kind")
        label = action.get("label") or action.get("id") or kind
        if kind == "run_action":
            if register_run_action is None:
                write(
                    f"[follow-up] {label}: available in an interactive "
                    "terminal action surface"
                )
                continue
            try:
                reference = register_run_action(action)
            except Exception as exc:
                write(f"[follow-up] {label}: unavailable ({exc})")
                continue
            write(f"[follow-up] {label}: /action --ref {reference}")
        elif kind == "open_url":
            write(f"[link] {label}: {action.get('url')}")
        elif kind == "copy_text":
            write(f"[copy] {label}: {action.get('text')}")
        elif kind == "download_attachment_asset":
            write(
                f"[download] {label}: "
                f"{action.get('filename') or action.get('asset_id')}"
            )
        elif kind == "dismiss":
            write(f"[dismiss] {label}")


def is_local_interactive_output(stream: TextIO | None = None) -> bool:
    """Return whether best-effort browser opening is appropriate."""

    output = stream if stream is not None else sys.stdout
    if not output.isatty():
        return False
    if any(
        os.environ.get(name) for name in ("SSH_CLIENT", "SSH_CONNECTION", "SSH_TTY")
    ):
        return False
    if sys.platform.startswith("linux") and not any(
        os.environ.get(name) for name in ("DISPLAY", "WAYLAND_DISPLAY")
    ):
        return False
    return True


__all__ = ["is_local_interactive_output", "render_action_result"]
