from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable

import pytest
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))


def _get_env_key(key_name: str) -> str:
    value = os.environ.get(key_name, "")
    if value:
        return value
    env_path = ROOT / ".env"
    if not env_path.exists():
        return ""
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or not line.startswith(f"{key_name}="):
            continue
        return line[len(key_name) + 1 :].strip().strip('"').strip("'")
    return ""


def _prepare_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "docs").mkdir()
    (workspace / "logs").mkdir()
    (workspace / "docs" / "guide.md").write_text(
        "# Guide\n\nSMOKE_GREP_TARGET\n",
        encoding="utf-8",
    )
    (workspace / "docs" / "notes.md").write_text(
        "# Notes\n\nNo special token here.\n",
        encoding="utf-8",
    )
    (workspace / "AGENTS.md").write_text(
        "Smoke-test repository instructions.\n",
        encoding="utf-8",
    )
    return workspace


def _tool_names_from_events(events: list[dict]) -> list[str]:
    tool_names: list[str] = []
    for event in events:
        if event.get("type") != "tool_results":
            continue
        for message in event.get("messages") or []:
            if not isinstance(message, dict):
                continue
            metadata = message.get("metadata") or {}
            tool_name = metadata.get("tool_name")
            if isinstance(tool_name, str) and tool_name:
                tool_names.append(tool_name)
    return tool_names


def _build_terminal_app(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app.terminal_app import TerminalApplication

    load_dotenv(ROOT / ".env")

    openrouter_key = _get_env_key("OPENROUTER_API_KEY")
    if not openrouter_key:
        pytest.skip("OPENROUTER_API_KEY not set; skipping Claude default-config smoke tests")

    gemini_key = _get_env_key("GEMINI_API_KEY")
    if not gemini_key:
        pytest.skip("GEMINI_API_KEY not set; skipping Claude WebSearch smoke tests")

    monkeypatch.setenv("OPENROUTER_API_KEY", openrouter_key)
    monkeypatch.setenv("GEMINI_API_KEY", gemini_key)
    monkeypatch.setenv("TAVILY_API_KEY", _get_env_key("TAVILY_API_KEY") or "test-tavily-key")
    monkeypatch.setenv("OPENAI_API_KEY", _get_env_key("OPENAI_API_KEY") or "test-openai-key")
    monkeypatch.setenv("FIREWORKS_API_KEY", _get_env_key("FIREWORKS_API_KEY") or "test-fireworks-key")
    monkeypatch.setenv("ZAI_API_KEY", _get_env_key("ZAI_API_KEY") or "test-zai-key")
    monkeypatch.setenv(
        "CLOUD_ORCHESTRATOR_URL",
        _get_env_key("CLOUD_ORCHESTRATOR_URL") or "http://cloud-orchestrator.test",
    )
    monkeypatch.setenv(
        "CLOUD_ORCHESTRATOR_TOKEN",
        _get_env_key("CLOUD_ORCHESTRATOR_TOKEN") or "test-cloud-token",
    )

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    monkeypatch.setenv("CONFIG_DIR", str(config_path.parent.resolve()))
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    agent_app = AgentApplication(str(config_path), str(session_root), event_store=events)
    assert agent_app.get_config_errors() == []

    term_app = TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=agent_app,
    )
    return agent_app, term_app


def _run_claude_smoke_case(
    agent_app,
    term_app,
    *,
    prompt: str,
    expected_tools: set[str],
    final_check: Callable[[str], bool],
    retries: int = 2,
) -> tuple[str, list[str]]:
    last_failure: tuple[str, list[str]] | None = None
    for _attempt in range(retries):
        session = term_app.start_new_session(agent_id="claude")
        term_app.append_user_message(prompt)

        final_session_dict, _messages, _request_id = term_app.send_request(stream=False)
        assert final_session_dict is not None

        loaded = agent_app.load_session(session.session_id)
        assert loaded is not None
        _core, _base_config, final_session = loaded

        final_text = final_session.messages[-1].content.strip()
        tool_names = _tool_names_from_events(
            term_app.list_events(session_id=session.session_id, limit=400)
        )

        if final_check(final_text) and expected_tools.issubset(set(tool_names)):
            return final_text, tool_names
        last_failure = (final_text, tool_names)

    assert last_failure is None, last_failure
    raise AssertionError("unreachable")


@pytest.mark.integration
@pytest.mark.openrouter
def test_default_claude_smoke_write_read_edit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _prepare_workspace(tmp_path)
    monkeypatch.chdir(workspace)
    agent_app, term_app = _build_terminal_app(tmp_path, monkeypatch)

    target = workspace / "smoke-write.txt"
    prompt = (
        f"Use Write to create the file {target} with exactly these two lines:\n"
        "alpha\nbeta\n"
        f"Then use Read to verify the file. Then use Edit to replace alpha with gamma in {target}. "
        "After that, reply with exactly FINAL: gamma."
    )

    final_text, tool_names = _run_claude_smoke_case(
        agent_app,
        term_app,
        prompt=prompt,
        expected_tools={"Write", "Read", "Edit"},
        final_check=lambda text: "FINAL: gamma" in text,
    )

    assert "FINAL: gamma" in final_text
    assert target.read_text(encoding="utf-8").startswith("gamma\n")
    assert {"Write", "Read", "Edit"}.issubset(set(tool_names))


@pytest.mark.integration
@pytest.mark.openrouter
def test_default_claude_smoke_glob_grep(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _prepare_workspace(tmp_path)
    monkeypatch.chdir(workspace)
    agent_app, term_app = _build_terminal_app(tmp_path, monkeypatch)

    prompt = (
        "First use Glob to find the markdown files under docs. "
        "Then use Grep to find the token SMOKE_GREP_TARGET in those files. "
        "Reply with exactly FOUND: guide.md."
    )

    final_text, tool_names = _run_claude_smoke_case(
        agent_app,
        term_app,
        prompt=prompt,
        expected_tools={"Glob", "Grep"},
        final_check=lambda text: "FOUND: guide.md" in text,
    )

    assert "FOUND: guide.md" in final_text
    assert {"Glob", "Grep"}.issubset(set(tool_names))


@pytest.mark.integration
@pytest.mark.openrouter
def test_default_claude_smoke_bash_read_taskstop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _prepare_workspace(tmp_path)
    monkeypatch.chdir(workspace)
    agent_app, term_app = _build_terminal_app(tmp_path, monkeypatch)

    prompt = (
        "Use Bash with run_in_background set to true to run this exact command: "
        "sh -c 'echo SMOKE_TASK_READY; sleep 120'. "
        "Then use Read on the output file path returned by Bash to confirm the output contains "
        "SMOKE_TASK_READY. If a dedicated background-task stop tool exists, you must use it instead of a shell kill command. "
        "Stop the task and reply with exactly STOPPED: SMOKE_TASK_READY."
    )

    final_text, tool_names = _run_claude_smoke_case(
        agent_app,
        term_app,
        prompt=prompt,
        expected_tools={"Bash", "Read", "TaskStop"},
        final_check=lambda text: "STOPPED: SMOKE_TASK_READY" in text,
        retries=3,
    )

    assert "STOPPED: SMOKE_TASK_READY" in final_text
    assert {"Bash", "Read", "TaskStop"}.issubset(set(tool_names))


@pytest.mark.integration
@pytest.mark.openrouter
def test_default_claude_smoke_webfetch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _prepare_workspace(tmp_path)
    monkeypatch.chdir(workspace)
    agent_app, term_app = _build_terminal_app(tmp_path, monkeypatch)

    prompt = (
        "Use WebFetch on https://www.rfc-editor.org/rfc/rfc2606.txt and determine which RFC reserves the example domains. "
        "Reply with exactly RFC 2606."
    )

    final_text, tool_names = _run_claude_smoke_case(
        agent_app,
        term_app,
        prompt=prompt,
        expected_tools={"WebFetch"},
        final_check=lambda text: "RFC 2606" in text,
    )

    assert "RFC 2606" in final_text
    assert "WebFetch" in tool_names


@pytest.mark.integration
@pytest.mark.openrouter
def test_default_claude_smoke_websearch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _prepare_workspace(tmp_path)
    monkeypatch.chdir(workspace)
    agent_app, term_app = _build_terminal_app(tmp_path, monkeypatch)

    prompt = (
        "Use WebSearch to answer this question: which RFC reserves the example domain names? "
        "Reply with a short answer that mentions the RFC number and include a Sources: section."
    )

    final_text, tool_names = _run_claude_smoke_case(
        agent_app,
        term_app,
        prompt=prompt,
        expected_tools={"WebSearch"},
        final_check=lambda text: "2606" in text and "Sources:" in text,
    )

    assert "2606" in final_text
    assert "Sources:" in final_text
    assert "WebSearch" in tool_names