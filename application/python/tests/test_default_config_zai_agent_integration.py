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


def _assistant_reasoning_lengths(session) -> list[int]:
    lengths: list[int] = []
    for message in session.messages:
        if message.role != "assistant":
            continue
        metadata = message.metadata or {}
        reasoning = metadata.get("reasoning")
        lengths.append(len(reasoning) if isinstance(reasoning, str) else 0)
    return lengths


def _assistant_cost_records(session) -> list[dict[str, float]]:
    records: list[dict[str, float]] = []
    for message in session.messages:
        if message.role != "assistant":
            continue
        metadata = message.metadata or {}
        prompt_tokens = metadata.get("usage_prompt_tokens")
        cached_tokens = metadata.get("usage_cached_tokens")
        completion_tokens = metadata.get("usage_completion_tokens")
        total_cost = metadata.get("usage_total_cost")
        breakdown = metadata.get("usage_cost_breakdown")
        if not (
            isinstance(prompt_tokens, int)
            and isinstance(completion_tokens, int)
            and isinstance(total_cost, (int, float))
            and isinstance(breakdown, dict)
        ):
            continue
        cached = cached_tokens if isinstance(cached_tokens, int) else 0
        ordinary_input = max(0, prompt_tokens - cached)
        expected = (
            ordinary_input * 1.4 + cached * 0.26 + completion_tokens * 4.4
        ) / 1_000_000
        records.append(
            {
                "total": float(total_cost),
                "expected": expected,
                "breakdown_total": sum(
                    float(value)
                    for value in breakdown.values()
                    if isinstance(value, (int, float))
                ),
            }
        )
    return records


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.zai
def test_default_config_zai_agent_reads_file_with_claude_tool(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app.terminal_app import TerminalApplication

    api_key = get_repo_env("ZAI_API_KEY")
    if not api_key:
        pytest.skip("ZAI_API_KEY not set; skipping default-config Z.ai smoke test")

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "zai.txt"
    target.write_text("ZAI_TOKEN_QMV_4827\n", encoding="utf-8")
    monkeypatch.chdir(workspace)

    monkeypatch.setenv("ZAI_API_KEY", api_key)
    monkeypatch.setenv(
        "OPENROUTER_API_KEY",
        get_repo_env("OPENROUTER_API_KEY", "test-openrouter-key"),
    )
    monkeypatch.setenv(
        "ANTHROPIC_API_KEY",
        get_repo_env("ANTHROPIC_API_KEY", "test-anthropic-key"),
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
    agent_app = AgentApplication(
        str(config_path),
        str(session_root),
        event_store=InMemoryEventStore(),
    )
    try:
        assert agent_app.get_config_errors() == []
        term_app = TerminalApplication(
            config_path=str(config_path),
            session_root=str(session_root),
            agent_app=agent_app,
        )

        last_failure: tuple[str, list[str], list[int], list[dict[str, float]]] | None = (
            None
        )
        for _attempt in range(2):
            session = term_app.start_new_session(agent_id="zai")
            term_app.append_user_message(
                f"Use the Read tool to read {target}. "
                "Reply with exactly the file content and nothing else."
            )

            final_session_dict, _messages, _request_id = term_app.send_request(
                stream=False
            )
            assert final_session_dict is not None

            loaded = agent_app.load_session(session.session_id)
            assert loaded is not None
            _core, _base_config, final_session = loaded

            final_text = (final_session.messages[-1].content or "").strip()
            tool_names = _tool_names_from_events(
                term_app.list_events(session_id=session.session_id, limit=200)
            )
            reasoning_lengths = _assistant_reasoning_lengths(final_session)
            cost_records = _assistant_cost_records(final_session)

            if (
                final_text == "ZAI_TOKEN_QMV_4827"
                and "Read" in tool_names
                and any(length > 0 for length in reasoning_lengths)
                and cost_records
            ):
                for record in cost_records:
                    assert record["total"] == pytest.approx(record["expected"])
                    assert record["breakdown_total"] == pytest.approx(record["total"])
                return
            last_failure = (final_text, tool_names, reasoning_lengths, cost_records)

        pytest.fail(
            "The default Z.ai agent did not complete the Claude Read tool flow. "
            f"Last attempt: text={last_failure[0]!r}, tools={last_failure[1]}, "
            f"reasoning_lengths={last_failure[2]}, cost_records={last_failure[3]}",
            pytrace=False,
        )
    finally:
        agent_app.close()