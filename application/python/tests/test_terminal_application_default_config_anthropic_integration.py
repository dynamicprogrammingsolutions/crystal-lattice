from __future__ import annotations

from pathlib import Path

import pytest

from repo_test_env import get_repo_env


ROOT = Path(__file__).resolve().parents[3]


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


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.anthropic
def test_terminal_application_default_config_anthropic_reads_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app.terminal_app import TerminalApplication

    anthropic_key = get_repo_env("ANTHROPIC_API_KEY")
    if not anthropic_key:
        pytest.skip(
            "ANTHROPIC_API_KEY not set; skipping default-config Anthropic smoke test"
        )

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "claude-anthropic.txt"
    target.write_text(
        "CLAUDE ANTHROPIC integration line\nsecond line\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(workspace)

    monkeypatch.setenv("ANTHROPIC_API_KEY", anthropic_key)
    monkeypatch.setenv(
        "OPENROUTER_API_KEY",
        get_repo_env("OPENROUTER_API_KEY", "test-openrouter-key"),
    )
    monkeypatch.setenv(
        "GEMINI_API_KEY", get_repo_env("GEMINI_API_KEY", "test-gemini-key")
    )
    monkeypatch.setenv(
        "TAVILY_API_KEY", get_repo_env("TAVILY_API_KEY", "test-tavily-key")
    )
    monkeypatch.setenv(
        "OPENAI_API_KEY", get_repo_env("OPENAI_API_KEY", "test-openai-key")
    )
    monkeypatch.setenv(
        "FIREWORKS_API_KEY",
        get_repo_env("FIREWORKS_API_KEY", "test-fireworks-key"),
    )
    monkeypatch.setenv("ZAI_API_KEY", get_repo_env("ZAI_API_KEY", "test-zai-key"))
    monkeypatch.setenv(
        "CLOUD_ORCHESTRATOR_URL",
        get_repo_env("CLOUD_ORCHESTRATOR_URL", "http://cloud-orchestrator.test"),
    )
    monkeypatch.setenv(
        "CLOUD_ORCHESTRATOR_TOKEN",
        get_repo_env("CLOUD_ORCHESTRATOR_TOKEN", "test-cloud-token"),
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
    monkeypatch.setenv("BUILTIN_PLUGINS", str((ROOT / "plugins").resolve()))
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )

    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    agent_app = AgentApplication(
        str(config_path),
        str(session_root),
        event_store=events,
    )
    assert agent_app.get_config_errors() == []
    term_app = TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=agent_app,
    )

    last_failure: tuple[str, list[str]] | None = None
    for _attempt in range(2):
        session = term_app.start_new_session(agent_id="claude-anthropic")
        ui_by_key = {
            element["key"]: element
            for element in term_app.session_ui_elements()
            if isinstance(element, dict) and isinstance(element.get("key"), str)
        }
        assert ui_by_key["enable_reasoning"]["type"] == "checkbox"
        assert ui_by_key["reasoning_effort"]["type"] == "select"
        assert [
            option["value"] for option in ui_by_key["reasoning_effort"]["options"]
        ] == ["low", "medium", "high", "xhigh", "max"]
        assert ui_by_key["show_reasoning"]["type"] == "checkbox"
        term_app.append_user_message(
            f"Use the Read tool to read {target.resolve()} and reply with "
            "exactly the first line."
        )
        final_session_dict, _messages, _request_id = term_app.send_request(stream=False)
        assert final_session_dict is not None

        loaded = agent_app.load_session(session.session_id)
        assert loaded is not None
        _core, base_config, final_session = loaded
        assert base_config["provider"] == "anthropic"
        assert base_config["model"] == "claude-haiku-4-5-20251001"

        final_text = str(final_session.messages[-1].content or "").strip()
        tool_names = _tool_names_from_events(
            term_app.list_events(session_id=session.session_id, limit=200)
        )
        if (
            "CLAUDE ANTHROPIC integration line" in final_text
            and "Read" in tool_names
            and any(message.role == "tool" for message in final_session.messages)
        ):
            last_failure = None
            break
        last_failure = (final_text, tool_names)

    assert last_failure is None, last_failure
