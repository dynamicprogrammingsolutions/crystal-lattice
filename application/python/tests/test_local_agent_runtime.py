from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
from typing import Any

import pytest

from agent_app import SessionRequestAlreadyRunningError
from agent_terminal_app import AgentRunResult, RunProgress, open_runtime
from agent_terminal_app.local_runtime import normalize_run_progress


def _write_config(
    path: Path,
    *,
    delay_ms: int = 0,
    model: str = "deterministic-test",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "providers": {
                    "deterministic": {
                        "provider": "deterministic_stream",
                        "model": model,
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
                        "model": "tool-test",
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
                        "model": "failure-test",
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


def test_open_runtime_runs_and_follows_up_with_bounded_progress(
    tmp_path: Path,
) -> None:
    config = _write_config(tmp_path / ".crystal" / "config.json")
    progress: list[RunProgress] = []

    with open_runtime(
        config_path=config,
        session_root=tmp_path / "sessions",
    ) as runtime:
        assert runtime.list_agents() == ("alpha", "beta")
        resolved_env = runtime.application.get_resolved_env()
        cli_argv = json.loads(resolved_env["CRYSTAL_LATTICE_CLI_ARGV_JSON"])
        assert cli_argv[-4:] == [
            "--config",
            str(config.resolve()),
            "--sessions-dir",
            str((tmp_path / "sessions").resolve()),
        ]
        first = runtime.run(
            "first task",
            agent_id="alpha",
            on_progress=progress.append,
        )
        follow_up = runtime.run(
            "follow up",
            session_id=first.session_id,
            on_progress=progress.append,
        )

        assert isinstance(first, AgentRunResult)
        assert first.status == "succeeded"
        assert first.agent_id == "alpha"
        assert first.output_text == "SYS= | USER=first task"
        assert not hasattr(first, "final_session")
        assert follow_up.status == "succeeded"
        assert follow_up.session_id == first.session_id
        assert follow_up.agent_id == "alpha"
        assert follow_up.output_text == "SYS= | USER=follow up"

        stored = runtime.application.load_session_record(first.session_id)
        assert stored is not None
        assert [message.role for message in stored.messages] == [
            "user",
            "assistant",
            "user",
            "assistant",
        ]

    progress_kinds = [item.kind for item in progress]
    assert progress_kinds.count("request_started") == 2
    assert progress_kinds.count("assistant_started") == 2
    assert progress_kinds.count("request_completed") == 2
    assert all(len(item.message) <= 240 for item in progress)


def test_open_runtime_discovers_local_config_and_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _write_config(
        tmp_path / ".crystal" / "config.json",
        model="${env:HEADLESS_TEST_MODEL}",
    )
    (config.parent / ".env").write_text(
        "HEADLESS_TEST_MODEL=dotenv-model\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HEADLESS_TEST_MODEL", raising=False)

    with open_runtime(session_root=tmp_path / "sessions") as runtime:
        assert runtime.config_path == config.resolve()
        assert (
            runtime.application.get_resolved_env()["HEADLESS_TEST_MODEL"]
            == "dotenv-model"
        )
        result = runtime.run("dotenv task", agent_id="alpha")
        assert result.status == "succeeded"


def test_open_runtime_requires_an_existing_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    with pytest.raises(FileNotFoundError, match="Crystal Lattice config not found"):
        open_runtime(runtime_layout=None)


def test_distinct_sessions_run_concurrently(tmp_path: Path) -> None:
    config = _write_config(
        tmp_path / "config.json",
        delay_ms=30,
    )
    with open_runtime(
        config_path=config,
        session_root=tmp_path / "sessions",
    ) as runtime:
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(runtime.run, "task one", agent_id="alpha")
            second = executor.submit(runtime.run, "task two", agent_id="beta")
            results = [first.result(timeout=5), second.result(timeout=5)]

    assert [result.status for result in results] == ["succeeded", "succeeded"]
    assert results[0].session_id != results[1].session_id


def test_same_session_rejection_does_not_append_losing_prompt(
    tmp_path: Path,
) -> None:
    config = _write_config(
        tmp_path / "config.json",
        delay_ms=100,
    )
    started = threading.Event()

    with open_runtime(
        config_path=config,
        session_root=tmp_path / "sessions",
    ) as runtime:
        _core, _base, session = runtime.application.create_session("alpha")

        def observe(progress: RunProgress) -> None:
            if progress.kind == "request_started":
                started.set()

        with ThreadPoolExecutor(max_workers=1) as executor:
            running = executor.submit(
                runtime.run,
                "winning prompt",
                session_id=session.session_id,
                on_progress=observe,
            )
            assert started.wait(timeout=2)
            with pytest.raises(SessionRequestAlreadyRunningError):
                runtime.run(
                    "losing prompt",
                    session_id=session.session_id,
                )
            assert running.result(timeout=5).status == "succeeded"

        stored = runtime.application.load_session_record(session.session_id)
        assert stored is not None
        assert "losing prompt" not in [message.content for message in stored.messages]


def test_timeout_returns_cancelled_result(tmp_path: Path) -> None:
    config = _write_config(
        tmp_path / "config.json",
        delay_ms=100,
    )

    with open_runtime(
        config_path=config,
        session_root=tmp_path / "sessions",
    ) as runtime:
        result = runtime.run(
            "slow task",
            agent_id="alpha",
            timeout=0.02,
        )

    assert result.status == "cancelled"
    assert result.error is not None
    assert result.error.category == "timeout"


def test_caller_can_cancel_an_active_request(tmp_path: Path) -> None:
    config = _write_config(
        tmp_path / "config.json",
        delay_ms=100,
    )
    started = threading.Event()
    request_id: list[str] = []

    with open_runtime(
        config_path=config,
        session_root=tmp_path / "sessions",
    ) as runtime:

        def observe(progress: RunProgress) -> None:
            if progress.kind == "request_started":
                request_id.append(progress.request_id)
                started.set()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                runtime.run,
                "cancel task",
                agent_id="alpha",
                on_progress=observe,
            )
            assert started.wait(timeout=2)
            runtime.cancel_request(request_id[0])
            result = future.result(timeout=5)

    assert result.status == "cancelled"
    assert result.error is None


def test_runtime_returns_structured_provider_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parent / "fixtures"))
    config = _write_failure_config(tmp_path / "config.json")
    progress: list[RunProgress] = []

    with open_runtime(
        config_path=config,
        session_root=tmp_path / "sessions",
    ) as runtime:
        result = runtime.run(
            "fail",
            agent_id="failure-agent",
            on_progress=progress.append,
        )

    assert result.status == "failed"
    assert result.output_text == ""
    assert result.error is not None
    assert result.error.category == "request_failed"
    assert result.error.message == "deterministic provider failure"
    assert "request_failed" in [item.kind for item in progress]


def test_progress_normalization_omits_long_tool_output() -> None:
    long_output = "secret tool output " * 1000
    progress = normalize_run_progress(
        {
            "type": "tool_results",
            "session_id": "session",
            "request_id": "request",
            "messages": [
                {
                    "role": "tool",
                    "content": long_output,
                    "metadata": {
                        "tool_name": "shell",
                        "tool_call_id": "call",
                        "display": {
                            "single_line": "Command completed",
                            "content": long_output,
                        },
                    },
                }
            ],
        }
    )

    assert len(progress) == 1
    assert progress[0].message == "Tool completed: shell — Command completed"
    assert long_output not in repr(progress[0])
    assert len(progress[0].message) <= 240


def test_runtime_tool_progress_and_result_omit_persisted_long_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parent / "fixtures"))
    config = _write_long_tool_config(tmp_path / "config.json")
    progress: list[RunProgress] = []

    with open_runtime(
        config_path=config,
        session_root=tmp_path / "sessions",
    ) as runtime:
        result = runtime.run(
            "use the deterministic tool",
            agent_id="tool-agent",
            on_progress=progress.append,
        )
        stored = runtime.application.load_session_record(result.session_id)
        history = runtime.history(result.session_id)

    assert result.status == "succeeded"
    assert result.output_text == "Long tool workflow completed"
    assert "long-result-" not in repr(result)
    assert [item.kind for item in progress].count("tool_started") == 1
    assert [item.kind for item in progress].count("tool_completed") == 1
    assert "long-result-" not in repr(progress)
    assert "Generated deterministic long output" in repr(progress)
    assert stored is not None
    tool_messages = [message for message in stored.messages if message.role == "tool"]
    assert len(tool_messages) == 1
    assert len(tool_messages[0].content) > 20_000
    compact_tool = next(
        message for message in history.messages if message.role == "tool"
    )
    assert compact_tool.content == "Generated deterministic long output"
    assert compact_tool.content_truncated is True


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"agent_id": "alpha", "session_id": "session"},
    ],
)
def test_run_requires_exactly_one_agent_or_session(
    tmp_path: Path,
    kwargs: dict[str, Any],
) -> None:
    config = _write_config(tmp_path / "config.json")

    with open_runtime(
        config_path=config,
        session_root=tmp_path / "sessions",
    ) as runtime:
        with pytest.raises(ValueError, match="exactly one"):
            runtime.run("task", **kwargs)


def test_invalid_timeout_does_not_create_a_session(tmp_path: Path) -> None:
    config = _write_config(tmp_path / "config.json")
    session_root = tmp_path / "sessions"

    with open_runtime(
        config_path=config,
        session_root=session_root,
    ) as runtime:
        with pytest.raises(ValueError, match="finite positive"):
            runtime.run("task", agent_id="alpha", timeout=0)
        assert runtime.application.list_session_summaries() == []
