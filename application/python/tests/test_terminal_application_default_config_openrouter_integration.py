from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))


def _prepare_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".temp").mkdir()
    (workspace / "codex.txt").write_text(
        "CODEX integration line\nsecond line\n", encoding="utf-8"
    )
    (workspace / "gemini.txt").write_text(
        "GEMINI integration line\nsecond line\n", encoding="utf-8"
    )
    (workspace / "qwen.txt").write_text(
        "QWEN integration line\nsecond line\n", encoding="utf-8"
    )
    (workspace / "grok.txt").write_text(
        "GROK integration line\nsecond line\n", encoding="utf-8"
    )
    (workspace / "kimi.txt").write_text(
        "KIMI integration line\nsecond line\n", encoding="utf-8"
    )
    (workspace / "claude.txt").write_text(
        "CLAUDE integration line\nsecond line\n", encoding="utf-8"
    )
    (workspace / "AGENTS.md").write_text(
        "Repository policy from AGENTS.\n",
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


@pytest.fixture(scope="module")
def ensure_openrouter_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip(
            "OPENROUTER_API_KEY not set; skipping terminal default-config OpenRouter integration test"
        )
    return api_key


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openrouter
def test_terminal_application_default_config_agents_make_real_tool_calls(
    ensure_openrouter_api_key: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app.terminal_app import TerminalApplication

    workspace = _prepare_workspace(tmp_path)
    monkeypatch.chdir(workspace)
    monkeypatch.setenv("OPENROUTER_API_KEY", ensure_openrouter_api_key)

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    agent_app = AgentApplication(
        str(config_path), str(session_root), event_store=events
    )
    assert agent_app.get_config_errors() == []

    term_app = TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=agent_app,
    )

    cases = {
        "codex-openrouter": {
            "prompt": "Use the shell tool to print the first line of codex.txt and reply with exactly that line.",
            "expected_tools": {"shell", "shell_command"},
            "expected_text": "CODEX integration line",
        },
        "gemini": {
            "prompt": "Use read_file on gemini.txt and reply with exactly the first line.",
            "expected_tools": {"read_file"},
            "expected_text": "GEMINI integration line",
        },
        "qwen": {
            "prompt": f"Use read_file with the absolute path {workspace / 'qwen.txt'} and reply with exactly the first line.",
            "expected_tools": {"read_file"},
            "expected_text": "QWEN integration line",
        },
        "grok": {
            "prompt": "Use view_file on grok.txt and reply with exactly the first line.",
            "expected_tools": {"view_file"},
            "expected_text": "GROK integration line",
        },
        "kimi": {
            "prompt": "Use ReadFile on kimi.txt and reply with exactly the first line.",
            "expected_tools": {"ReadFile"},
            "expected_text": "KIMI integration line",
        },
        "claude": {
            "prompt": "Use the Read tool to read claude.txt and reply with exactly the first line.",
            "expected_tools": {"Read"},
            "expected_text": "CLAUDE integration line",
        },
    }

    for agent_id, expected in cases.items():
        last_failure: tuple[str, list[str]] | None = None
        for _attempt in range(2):
            session = term_app.start_new_session(agent_id=agent_id)
            term_app.append_user_message(expected["prompt"])

            final_session_dict, _messages, _request_id = term_app.send_request(
                stream=False
            )
            assert final_session_dict is not None

            loaded = agent_app.load_session(session.session_id)
            assert loaded is not None
            _core, _base_config, final_session = loaded

            final_text = final_session.messages[-1].content.strip()
            tool_names = _tool_names_from_events(
                term_app.list_events(session_id=session.session_id, limit=200)
            )
            if (
                expected["expected_text"] in final_text
                and expected["expected_tools"].intersection(tool_names)
                and any(message.role == "tool" for message in final_session.messages)
            ):
                last_failure = None
                break
            last_failure = (final_text, tool_names)

        assert last_failure is None, (agent_id, last_failure)
