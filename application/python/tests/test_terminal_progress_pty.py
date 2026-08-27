from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time

import pytest


pytestmark = [
    pytest.mark.terminal_ui,
    pytest.mark.skipif(os.name == "nt", reason="POSIX pseudo-terminal test"),
]

pexpect = pytest.importorskip("pexpect")
pyte = pytest.importorskip("pyte")

ROOT = Path(__file__).resolve().parents[3]
HARNESS = Path(__file__).resolve().parent / "fixtures" / "terminal_progress_harness.py"


def _append_event(path: Path, event: dict) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event))
        stream.write("\n")
        stream.flush()


class _ScreenWriter:
    def __init__(self, stream) -> None:
        self._stream = stream

    def write(self, data: str) -> None:
        self._stream.feed(data)

    def flush(self) -> None:
        return None


def _screen_contains(screen, text: str) -> bool:
    return any(text in line for line in screen.display)


def _wait_for_screen_text(child, screen, text: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _screen_contains(screen, text):
            return
        matched = child.expect_exact(
            ["\x1b[6n", pexpect.TIMEOUT, pexpect.EOF],
            timeout=min(0.2, max(0.01, deadline - time.monotonic())),
        )
        if matched == 0:
            child.send("\x1b[24;1R")
            continue
        if matched == 2:
            raise AssertionError(
                f"terminal exited before rendering expected text: {text!r}"
            )
    visible = "\n".join(screen.display)
    raise AssertionError(
        f"terminal did not render expected text: {text!r}\n"
        f"visible screen:\n{visible}"
    )


def test_progress_toolbar_redraws_for_request_llm_and_tool_phases(
    tmp_path: Path,
) -> None:
    event_path = tmp_path / "events.jsonl"
    event_path.touch()
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(
            [
                str(ROOT / "application" / "python"),
                str(ROOT / "core" / "python"),
                os.environ.get("PYTHONPATH", ""),
            ]
        ).rstrip(os.pathsep),
        "TERMINAL_PROGRESS_EVENT_FILE": str(event_path),
        "TERM": "xterm-256color",
    }
    child = pexpect.spawn(
        sys.executable,
        [str(HARNESS)],
        env=env,
        encoding="utf-8",
        timeout=10,
        dimensions=(24, 100),
    )
    screen = pyte.Screen(100, 24)
    child.logfile_read = _ScreenWriter(pyte.Stream(screen))
    try:
        _wait_for_screen_text(child, screen, "Session started")
        # prompt_toolkit requests a cursor-position report before it knows
        # terminal height and enables the bottom toolbar. A real terminal
        # answers this; emulate every request while waiting for semantic text.
        _wait_for_screen_text(child, screen, "Agent: default")
        assert _screen_contains(screen, "terminal-progress-harness")

        _append_event(
            event_path,
            {"type": "request_started", "request_id": "request-1"},
        )
        _wait_for_screen_text(child, screen, "Running: request")

        _append_event(
            event_path,
            {
                "type": "assistant_message",
                "phase": "start",
                "request_id": "request-1",
            },
        )
        _wait_for_screen_text(child, screen, "Running: LLM")

        _append_event(
            event_path,
            {
                "type": "tool_calls",
                "request_id": "request-1",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": "{}"},
                    }
                ],
            },
        )
        _wait_for_screen_text(child, screen, "Running: tool read_file")

        child.send("draft")
        _wait_for_screen_text(child, screen, "draft")

        _append_event(
            event_path,
            {
                "type": "tool_partial",
                "phase": "end",
                "request_id": "request-1",
                "tool_call_id": "call-1",
                "message_index": 1,
                "payload": {
                    "result": {
                        "role": "tool",
                        "content": "README",
                        "metadata": {
                            "tool_call_id": "call-1",
                            "tool_name": "read_file",
                            "display": {
                                "type": "text",
                                "content": "README",
                                "single_line": "Read: README.md",
                            },
                        },
                    }
                },
            },
        )
        _append_event(
            event_path,
            {"type": "request_completed", "request_id": "request-1"},
        )
        _wait_for_screen_text(child, screen, "[request] completed")
        _wait_for_screen_text(child, screen, "draft")

        child.sendcontrol("q")
        _wait_for_screen_text(child, screen, "Exiting...")
        child.expect(pexpect.EOF)
        child.close()
        assert child.exitstatus == 0
    finally:
        if child.isalive():
            child.terminate(force=True)
