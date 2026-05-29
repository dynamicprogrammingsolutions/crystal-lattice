from __future__ import annotations

import os
import sys
from pathlib import Path

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

from agent_core import Message, Session  # noqa: E402


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
def test_default_claude_agent_compaction_action_rewrites_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_default_config_app(tmp_path, monkeypatch)
    previous = getattr(server_mod, "_agent_app", None)
    if previous is not None:
        previous.close()
    server_mod._agent_app = app

    core, base_config, session = app.create_session("claude")
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
                "claude_compaction_settings_overrides": {
                    "model": compaction_model,
                }
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
            },
        },
        app_instance=app,
    )

    if resp["status"] != "ok":
        raise AssertionError(resp)

    compacted = app.load_session_record(seeded.session_id)
    assert compacted is not None
    assert [message.role for message in compacted.messages[-3:]] == [
        "user",
        "user",
        "assistant",
    ]
    summary_text = compacted.messages[-3].content
    assert isinstance(summary_text, str)
    assert (
        "This session is being continued from a previous conversation" in summary_text
    )
    assert "1. Primary Request and Intent:" in summary_text
    assert "9. Optional Next Step:" in summary_text
    assert "Resume directly" in summary_text
    metadata = compacted.messages[-3].metadata or {}
    assert metadata["claude_compaction"]["is_compact_summary"] is True
    session_meta = compacted.metadata or {}
    assert session_meta["claude_compaction"]["compacted"] is True

    # Configuration note: the action currently inherits the normal agent model,
    # but callers can override it explicitly with this existing feature config key.
    assert compaction_model
