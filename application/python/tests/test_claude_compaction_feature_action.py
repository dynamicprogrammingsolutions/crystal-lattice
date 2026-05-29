"""Application-style tests for the Claude compaction feature action."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict


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

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core import Session  # noqa: E402
from claude_tools.claude_compaction_feature import (  # noqa: E402
    build_compact_summary_text,
)


def _fixture(name: str) -> dict:
    path = (
        ROOT / "plugins/claude-tools/investigation/fixtures/compaction" / f"{name}.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _summary_body_from_fixture(fixture: dict) -> str:
    text = fixture["compact_summary_text"]
    _, summary_and_footer = text.split("\n\nSummary:\n", 1)
    summary_body, _footer = summary_and_footer.split(
        "\n\nIf you need specific details from before compaction",
        1,
    )
    return summary_body


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {"echo": {"provider": "echo_openai_like", "model": "test-model"}},
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "claude_tools.claude_compaction_feature.ClaudeCompactionFeature",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {},
    }
    path = tmp_path / "config_claude_compaction_feature.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    from agent_terminal_app import server as server_mod

    previous = getattr(server_mod, "_agent_app", None)
    if previous is not None:
        previous.close()
    app = AgentApplication(
        str(_make_config(tmp_path)),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    server_mod._agent_app = app
    return app


def test_session_ui_schema_includes_claude_compaction_action(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)
    _core, _base_config, session = app.create_session("default")

    resp = server_mod.get_session_ui_schema(session.session_id, app_instance=app)

    matches = [el for el in resp["elements"] if el.get("plugin") == "claude_compaction"]
    assert len(matches) == 1
    assert matches[0]["action_id"] == "compact_conversation"
    assert matches[0]["action_owner"] == "feature"


def test_claude_compaction_action_rewrites_session_history(
    tmp_path: Path, monkeypatch
) -> None:
    from agent_terminal_app import server as server_mod
    from claude_tools import claude_compaction_feature as feature_mod

    fixture = _fixture("success-basic")
    summary_body = _summary_body_from_fixture(fixture)

    def _fake_run_compaction_request(
        core: Any, session: Session, config: Dict[str, Any]
    ) -> str:
        _ = core, session, config
        return f"<analysis>ok</analysis>\n<summary>\n{summary_body}\n</summary>"

    monkeypatch.setattr(
        feature_mod,
        "_run_compaction_request",
        _fake_run_compaction_request,
        raising=True,
    )

    app = _build_app(tmp_path)
    core, base_config, session = app.create_session("default")
    session = core.add_message(
        session, "user", "Answer exactly ONE.", config=base_config
    )
    session = core.add_message(
        session, "assistant", "Need more context.", config=base_config
    )
    session = core.add_message(
        session, "user", "Answer exactly THREE.", config=base_config
    )
    app.save_session(session)

    resp = server_mod.execute_action(
        {
            "plugin": "claude_compaction",
            "action_id": "compact_conversation",
            "action_owner": "feature",
            "inputs": {
                "session_id": session.session_id,
            },
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    assert resp["plugin"] == "claude_compaction"
    assert resp["result"]["message"] == "Compacted conversation."

    loaded = app.load_session_record(session.session_id)
    assert loaded is not None
    expected_summary = build_compact_summary_text(
        summary_body,
        transcript_path=str(tmp_path / "sessions" / f"{session.session_id}.json"),
    )
    assert [message.role for message in loaded.messages] == [
        "user",
        "user",
        "assistant",
    ]
    assert [message.content for message in loaded.messages] == [
        expected_summary,
        feature_mod._LOCAL_COMMAND_ARTIFACT,
        feature_mod._NO_RESPONSE_REQUESTED,
    ]
    summary_metadata = loaded.messages[0].metadata or {}
    assert summary_metadata["claude_compaction"]["is_compact_summary"] is True
