from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any

import pytest


pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[3]


def _write_config(path: Path, *, delay_ms: int = 0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "providers": {
                    "deterministic": {
                        "provider": "deterministic_stream",
                        "model": "cli-test",
                        "stream_chunk_count": 3,
                        "stream_chunk_delay_ms": delay_ms,
                    }
                },
                "plugins": [
                    "plugins.deterministic_stream_provider.DeterministicStreamProvider"
                ],
                "agents": {
                    "alpha": {"provider": "deterministic"},
                    "beta": {"provider": "deterministic"},
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_long_tool_config(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "providers": {
                    "tool_provider": {
                        "provider": "deterministic_long_tool_provider",
                        "model": "cli-tool-test",
                    }
                },
                "plugins": [
                    "headless_runtime_plugins.DeterministicLongToolProvider",
                    "headless_runtime_plugins.DeterministicLongOutputTool",
                ],
                "agents": {
                    "tool-agent": {"provider": "tool_provider"},
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_failure_config(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "providers": {
                    "failure": {
                        "provider": "deterministic_failure_provider",
                        "model": "cli-failure-test",
                    }
                },
                "plugins": [
                    "headless_runtime_plugins.DeterministicFailureProvider",
                ],
                "agents": {
                    "failure-agent": {"provider": "failure"},
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def _env(home: Path) -> dict[str, str]:
    return {
        **os.environ,
        "HOME": str(home),
        "PYTHONPATH": os.pathsep.join(
            [
                str(ROOT / "core" / "python"),
                str(ROOT / "application" / "python"),
                str(ROOT / "application" / "python" / "tests" / "fixtures"),
            ]
        ),
        "PYTHONUNBUFFERED": "1",
    }


def _command(
    workspace: Path,
    config: Path,
    sessions: Path,
    *args: str,
) -> list[str]:
    return [
        sys.executable,
        "-m",
        "agent_terminal_app",
        "--config",
        str(config),
        "--sessions-dir",
        str(sessions),
        "--no-log-file",
        *args,
    ]


def _run(
    workspace: Path,
    config: Path,
    sessions: Path,
    *args: str,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _command(workspace, config, sessions, *args),
        cwd=workspace,
        env=_env(workspace / "home"),
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )


def _json_stdout(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"stdout was not one JSON document:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        ) from exc
    assert isinstance(parsed, dict)
    return parsed


def test_agents_and_json_run_follow_up_and_history(tmp_path: Path) -> None:
    config = _write_config(tmp_path / "config.json")
    sessions = tmp_path / "sessions"

    agents = _run(
        tmp_path,
        config,
        sessions,
        "agents",
        "--format",
        "json",
    )
    assert agents.returncode == 0, agents.stderr
    assert agents.stderr == ""
    assert _json_stdout(agents) == {"agents": ["alpha", "beta"]}

    first = _run(
        tmp_path,
        config,
        sessions,
        "run",
        "--agent",
        "alpha",
        "--prompt",
        "first CLI task",
        "--format",
        "json",
    )
    assert first.returncode == 0, first.stderr
    first_payload = _json_stdout(first)
    assert first_payload["status"] == "succeeded"
    assert first_payload["output_text"] == "SYS= | USER=first CLI task"
    assert "Request started" in first.stderr
    assert "Configuring logging" not in first.stdout
    session_id = first_payload["session_id"]

    follow_up = _run(
        tmp_path,
        config,
        sessions,
        "run",
        "--session",
        session_id,
        "--prompt",
        "follow-up CLI task",
        "--format",
        "json",
    )
    assert follow_up.returncode == 0, follow_up.stderr
    follow_payload = _json_stdout(follow_up)
    assert follow_payload["session_id"] == session_id
    assert follow_payload["output_text"] == "SYS= | USER=follow-up CLI task"

    history = _run(
        tmp_path,
        config,
        sessions,
        "history",
        "--session",
        session_id,
        "--start",
        "-3",
        "--format",
        "json",
    )
    assert history.returncode == 0, history.stderr
    history_payload = _json_stdout(history)
    assert [row["index"] for row in history_payload["messages"]] == [1, 2, 3]
    assert [row["role"] for row in history_payload["messages"]] == [
        "assistant",
        "user",
        "assistant",
    ]

    full = _run(
        tmp_path,
        config,
        sessions,
        "history",
        "--session",
        session_id,
        "--index",
        "-1",
        "--format",
        "json",
    )
    assert full.returncode == 0, full.stderr
    full_payload = _json_stdout(full)
    assert full_payload["index"] == 3
    assert full_payload["message"]["content"] == "SYS= | USER=follow-up CLI task"


@pytest.mark.parametrize("source", ["prompt", "file", "stdin"])
def test_run_accepts_each_prompt_source(tmp_path: Path, source: str) -> None:
    config = _write_config(tmp_path / "config.json")
    sessions = tmp_path / "sessions"
    prompt = f"{source} task"
    source_args: list[str]
    input_text = None
    if source == "prompt":
        source_args = ["--prompt", prompt]
    elif source == "file":
        prompt_path = tmp_path / "prompt.md"
        prompt_path.write_text(prompt, encoding="utf-8")
        source_args = ["--prompt-file", str(prompt_path)]
    else:
        source_args = ["--stdin"]
        input_text = prompt

    result = _run(
        tmp_path,
        config,
        sessions,
        "run",
        "--agent",
        "alpha",
        *source_args,
        "--format",
        "text",
        input_text=input_text,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == f"SYS= | USER={prompt}\n"
    assert "[session]" in result.stderr


def test_json_timeout_has_stable_result_and_exit_code(tmp_path: Path) -> None:
    config = _write_config(tmp_path / "config.json", delay_ms=100)
    result = _run(
        tmp_path,
        config,
        tmp_path / "sessions",
        "run",
        "--agent",
        "alpha",
        "--prompt",
        "timeout task",
        "--timeout",
        "0.02",
        "--format",
        "json",
    )

    assert result.returncode == 124
    payload = _json_stdout(result)
    assert payload["status"] == "cancelled"
    assert payload["error"]["category"] == "timeout"
    assert "exceeded the configured timeout" in result.stderr


def test_cli_long_tool_progress_and_result_remain_compact(tmp_path: Path) -> None:
    config = _write_long_tool_config(tmp_path / "config.json")
    result = _run(
        tmp_path,
        config,
        tmp_path / "sessions",
        "run",
        "--agent",
        "tool-agent",
        "--prompt",
        "use the long tool",
        "--format",
        "json",
    )

    assert result.returncode == 0, result.stderr
    payload = _json_stdout(result)
    assert payload["output_text"] == "Long tool workflow completed"
    assert "long-result-" not in result.stdout
    assert "long-result-" not in result.stderr
    assert "Generated deterministic long output" in result.stderr

    history = _run(
        tmp_path,
        config,
        tmp_path / "sessions",
        "history",
        "--session",
        payload["session_id"],
        "--format",
        "json",
    )
    history_payload = _json_stdout(history)
    tool_row = next(row for row in history_payload["messages"] if row["role"] == "tool")
    assert tool_row["content"] == "Generated deterministic long output"
    assert tool_row["content_truncated"] is True


def test_cli_provider_failure_returns_json_and_failure_exit(tmp_path: Path) -> None:
    config = _write_failure_config(tmp_path / "config.json")
    result = _run(
        tmp_path,
        config,
        tmp_path / "sessions",
        "run",
        "--agent",
        "failure-agent",
        "--prompt",
        "fail",
        "--format",
        "json",
    )

    assert result.returncode == 1
    payload = _json_stdout(result)
    assert payload["status"] == "failed"
    assert payload["error"]["category"] == "request_failed"
    assert "deterministic provider failure" in result.stderr
    assert "Traceback" not in result.stdout


def test_invalid_run_arguments_exit_with_usage_error(tmp_path: Path) -> None:
    config = _write_config(tmp_path / "config.json")
    result = _run(
        tmp_path,
        config,
        tmp_path / "sessions",
        "run",
        "--agent",
        "alpha",
        "--prompt",
        "",
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert "prompt must not be empty" in result.stderr


def test_two_distinct_cli_sessions_run_concurrently(tmp_path: Path) -> None:
    config = _write_config(tmp_path / "config.json", delay_ms=100)
    sessions = tmp_path / "sessions"
    env = _env(tmp_path / "home")
    first = subprocess.Popen(
        _command(
            tmp_path,
            config,
            sessions,
            "run",
            "--agent",
            "alpha",
            "--prompt",
            "parallel one",
            "--format",
            "json",
        ),
        cwd=tmp_path,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    second = subprocess.Popen(
        _command(
            tmp_path,
            config,
            sessions,
            "run",
            "--agent",
            "beta",
            "--prompt",
            "parallel two",
            "--format",
            "json",
        ),
        cwd=tmp_path,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    first_stdout, first_stderr = first.communicate(timeout=20)
    second_stdout, second_stderr = second.communicate(timeout=20)

    assert first.returncode == 0, first_stderr
    assert second.returncode == 0, second_stderr
    first_payload = json.loads(first_stdout)
    second_payload = json.loads(second_stdout)
    assert first_payload["session_id"] != second_payload["session_id"]
    assert first_payload["status"] == second_payload["status"] == "succeeded"


@pytest.mark.skipif(os.name == "nt", reason="POSIX SIGINT behavior")
def test_sigint_cancels_active_cli_request(tmp_path: Path) -> None:
    config = _write_config(tmp_path / "config.json", delay_ms=1000)
    sessions = tmp_path / "sessions"
    process = subprocess.Popen(
        _command(
            tmp_path,
            config,
            sessions,
            "run",
            "--agent",
            "alpha",
            "--prompt",
            "interrupt task",
            "--format",
            "json",
        ),
        cwd=tmp_path,
        env=_env(tmp_path / "home"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            time.sleep(0.05)
            # The provider has a three-second deterministic stream, so a short
            # startup allowance is enough without consuming a pipe line.
            if time.monotonic() > deadline - 9:
                process.send_signal(signal.SIGINT)
                break
        stdout, stderr = process.communicate(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)

    assert process.returncode == 130, stderr
    assert stdout == ""
    assert "Agent request interrupted" in stderr
