from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

from repo_test_env import get_repo_env


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
CLAUDE_PLUGIN_SRC = ROOT / "plugins/claude-tools/src"
if str(CLAUDE_PLUGIN_SRC) not in sys.path:
    sys.path.insert(0, str(CLAUDE_PLUGIN_SRC))

from agent_core import Message, Session  # noqa: E402
from claude_tools.claude_compaction_feature import (  # noqa: E402
    _LOCAL_COMMAND_ARTIFACT,
    _NO_RESPONSE_REQUESTED,
)


def _transcript_path_from_summary(summary_text: str) -> Path:
    marker = "read the full transcript at: "
    _, tail = summary_text.split(marker, 1)
    path_text, _ = tail.split("\nContinue the conversation", 1)
    return Path(path_text)


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _build_default_config_app(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    openrouter_key = get_repo_env("OPENROUTER_API_KEY")
    if not openrouter_key:
        pytest.skip(
            "OPENROUTER_API_KEY not set; skipping Claude default-config compaction test"
        )

    monkeypatch.setenv("OPENROUTER_API_KEY", openrouter_key)
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
    app = AgentApplication(
        str(config_path),
        str(session_root),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []
    return app


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openrouter
@pytest.mark.parametrize(
    ("inputs", "expected_leading_non_system", "expected_trailing_contents"),
    [
        ({}, [], []),
        (
            {"start": 0, "end": 4},
            [],
            ["TWO", "Answer exactly THREE.", "THREE"],
        ),
        (
            {"start": 2, "end": 5},
            ["Answer exactly ONE."],
            ["Answer exactly THREE.", "THREE"],
        ),
    ],
)
def test_default_claude_agent_compaction_action_rewrites_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    inputs: Dict[str, Any],
    expected_leading_non_system: list[str],
    expected_trailing_contents: list[str],
) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_default_config_app(tmp_path, monkeypatch)
    previous = getattr(server_mod, "_agent_app", None)
    if previous is not None:
        previous.close()
    server_mod._agent_app = app

    core, base_config, session = app.create_session("claude-openrouter")
    assert base_config["model"] == "anthropic/claude-haiku-4.5"

    compaction_model = os.getenv(
        "OPENROUTER_MODEL_CLAUDE_COMPACTION",
        base_config["model"],
    )
    seeded = Session(
        session_id=session.session_id,
        messages=[
            Message(role="user", content="Answer exactly ONE."),
            Message(role="assistant", content="ONE"),
            Message(role="user", content="Answer exactly TWO."),
            Message(role="assistant", content="TWO"),
            Message(role="user", content="Answer exactly THREE."),
            Message(role="assistant", content="THREE"),
        ],
        metadata={
            **(session.metadata or {}),
            "overrides": {
                "compaction_model": compaction_model,
            },
        },
    )
    app.save_session(seeded)

    resp = server_mod.execute_action(
        {
            "plugin": "claude_compaction",
            "action_id": "compact_conversation",
            "action_owner": "feature",
            "inputs": {
                "session_id": seeded.session_id,
                **inputs,
            },
        },
        app_instance=app,
    )

    if resp["status"] != "ok":
        raise AssertionError(resp)

    compacted = app.load_session_record(seeded.session_id)
    assert compacted is not None
    assert compacted.messages[0].role == "system"
    assert sum(1 for message in compacted.messages if message.role == "system") == 1
    summary_index = next(
        idx
        for idx, message in enumerate(compacted.messages)
        if isinstance(message.content, str)
        and "This session is being continued from a previous conversation"
        in message.content
    )
    assert [
        message.role
        for message in compacted.messages[summary_index : summary_index + 3]
    ] == [
        "user",
        "user",
        "assistant",
    ]

    summary_text = compacted.messages[summary_index].content
    assert isinstance(summary_text, str)
    assert (
        "This session is being continued from a previous conversation" in summary_text
    )
    assert "1. Primary Request and Intent:" in summary_text
    assert "9. Optional Next Step:" in summary_text
    assert "Resume directly" in summary_text
    transcript_path = _transcript_path_from_summary(summary_text)
    assert transcript_path.exists()
    assert (
        transcript_path.parent
        == tmp_path / "sessions" / "claude-compaction-transcripts"
    )
    assert transcript_path.suffix == ".jsonl"
    transcript_entries = _read_jsonl(transcript_path)
    assert [entry["type"] for entry in transcript_entries] == [
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert transcript_entries[0]["message"]["content"] == "Answer exactly ONE."
    assert transcript_entries[2]["message"]["content"] == "Answer exactly TWO."
    assert transcript_entries[4]["message"]["content"] == "Answer exactly THREE."
    assert compacted.messages[summary_index + 1].content == _LOCAL_COMMAND_ARTIFACT
    assert compacted.messages[summary_index + 2].content == _NO_RESPONSE_REQUESTED
    leading_contents = [
        message.content for message in compacted.messages[:summary_index]
    ]
    assert leading_contents[0] is not None
    assert leading_contents[1:] == expected_leading_non_system
    assert [message.content for message in compacted.messages[summary_index + 3 :]] == (
        expected_trailing_contents
    )
    metadata = compacted.messages[summary_index].metadata or {}
    assert metadata["claude_compaction"]["is_compact_summary"] is True
    session_meta = compacted.metadata or {}
    assert session_meta["claude_compaction"]["compacted"] is True
    assert compaction_model
