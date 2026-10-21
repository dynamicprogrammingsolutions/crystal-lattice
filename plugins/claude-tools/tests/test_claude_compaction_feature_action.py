"""Application-style tests for the Claude compaction feature action."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

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
CLAUDE_PLUGIN_SRC = ROOT / "plugins/claude-tools/src"
if str(CLAUDE_PLUGIN_SRC) not in sys.path:
    sys.path.insert(0, str(CLAUDE_PLUGIN_SRC))
SYSTEM_MESSAGE_PLUGIN_SRC = ROOT / "plugins/feature-system-message/src"
if str(SYSTEM_MESSAGE_PLUGIN_SRC) not in sys.path:
    sys.path.insert(0, str(SYSTEM_MESSAGE_PLUGIN_SRC))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core import Session  # noqa: E402
from claude_tools.claude_compaction_feature import (  # noqa: E402
    _COMPACTION_MODEL_KEY,
    _LOCAL_COMMAND_ARTIFACT,
    _NO_RESPONSE_REQUESTED,
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


def _make_config(tmp_path: Path, *, include_system_feature: bool = False) -> Path:
    plugins = [
        "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
        "claude_tools.claude_compaction_feature.ClaudeCompactionFeature",
        "claude_tools.claude_compaction_app.ClaudeCompactionAppPlugin",
    ]
    agent_cfg: Dict[str, Any] = {"provider": "echo"}
    if include_system_feature:
        plugins.insert(
            1,
            "feature_system_message.system_message_feature.SystemMessageFeature",
        )
        agent_cfg.update(
            {
                "system_message_enabled": True,
                "system_message": {"template": "Synthetic system prompt"},
            }
        )
    cfg: Dict[str, Any] = {
        "providers": {"echo": {"provider": "echo_openai_like", "model": "test-model"}},
        "plugins": plugins,
        "agents": {"default": agent_cfg},
        "application": {},
    }
    path = tmp_path / "config_claude_compaction_feature.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(
    tmp_path: Path, *, include_system_feature: bool = False
) -> AgentApplication:
    from agent_terminal_app import server as server_mod

    previous = getattr(server_mod, "_agent_app", None)
    if previous is not None:
        previous.close()
    app = AgentApplication(
        str(_make_config(tmp_path, include_system_feature=include_system_feature)),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    server_mod._agent_app = app
    return app


def _seed_session(app: AgentApplication) -> Session:
    core, base_config, session = app.create_session("default")
    session = core.add_message(
        session, "user", "Answer exactly ONE.", config=base_config
    )
    session = core.add_message(session, "assistant", "ONE", config=base_config)
    session = core.add_message(
        session, "user", "Answer exactly TWO.", config=base_config
    )
    session = core.add_message(session, "assistant", "TWO", config=base_config)
    session = core.add_message(
        session, "user", "Answer exactly THREE.", config=base_config
    )
    session = core.add_message(session, "assistant", "THREE", config=base_config)
    app.save_session(session)
    return session


def test_session_ui_schema_includes_claude_compaction_fields_and_actions(
    tmp_path: Path,
) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)
    _core, _base_config, session = app.create_session("default")

    resp = server_mod.get_session_ui_schema(session.session_id, app_instance=app)

    feature_matches = [
        el for el in resp["elements"] if el.get("plugin") == "claude_compaction"
    ]
    compaction_model = next(
        element
        for element in feature_matches
        if element.get("key") == _COMPACTION_MODEL_KEY
    )
    assert compaction_model["ui_type"] == "config"
    # Manual compaction actions moved from the feature to the application
    # plugin, so the core schema no longer exposes them.
    assert not any(
        element.get("ui_type") in {"session_action", "message_action"}
        for element in feature_matches
    )

    app_resp = server_mod.get_session_application_ui_schema(
        session.session_id, app_instance=app
    )
    app_matches = [
        el for el in app_resp["elements"] if el.get("plugin") == "claude_compaction_app"
    ]
    action_ids = {element.get("id") for element in app_matches}
    assert "compact_conversation" in action_ids
    assert "compact_up_to_here" in action_ids
    for element in app_matches:
        assert element.get("action_owner") == "application"


def test_session_config_schema_includes_claude_compaction_model_key(
    tmp_path: Path,
) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)
    _core, _base_config, session = app.create_session("default")

    resp = server_mod.get_session_config_schema(session.session_id, app_instance=app)
    keys = {entry.get("key") for entry in resp["schema"] if isinstance(entry, dict)}

    assert _COMPACTION_MODEL_KEY in keys
    assert "claude_compaction_prompt" in keys
    assert "claude_compaction_settings_overrides" in keys


def _assert_rewrite_shape(
    loaded: Session,
    expected_summary: str,
    *,
    expect_system: bool,
    expected_leading_contents: list[str],
    expected_trailing_contents: list[str],
) -> None:
    if expect_system:
        assert loaded.messages[0].role == "system"
        assert loaded.messages[0].content == "Synthetic system prompt"
        assert sum(1 for message in loaded.messages if message.role == "system") == 1
    else:
        assert all(message.role != "system" for message in loaded.messages)
    summary_index = next(
        idx
        for idx, message in enumerate(loaded.messages)
        if message.content == expected_summary
    )

    assert [
        message.role for message in loaded.messages[summary_index : summary_index + 3]
    ] == [
        "user",
        "user",
        "assistant",
    ]
    assert [
        message.content
        for message in loaded.messages[summary_index : summary_index + 3]
    ] == [
        expected_summary,
        _LOCAL_COMMAND_ARTIFACT,
        _NO_RESPONSE_REQUESTED,
    ]
    assert [message.content for message in loaded.messages[:summary_index]] == (
        expected_leading_contents
    )
    assert [message.content for message in loaded.messages[summary_index + 3 :]] == (
        expected_trailing_contents
    )


@pytest.mark.parametrize(
    (
        "include_system_feature",
        "inputs",
        "expected_leading_contents",
        "expected_trailing_contents",
    ),
    [
        (False, {}, [], []),
        (False, {"start": 0, "end": 3}, [], ["TWO", "Answer exactly THREE.", "THREE"]),
        (
            False,
            {"start": 1, "end": 4},
            ["Answer exactly ONE."],
            ["Answer exactly THREE.", "THREE"],
        ),
        (True, {}, ["Synthetic system prompt"], []),
        (
            True,
            {"start": 0, "end": 4},
            ["Synthetic system prompt"],
            ["TWO", "Answer exactly THREE.", "THREE"],
        ),
        (
            True,
            {"start": 2, "end": 5},
            ["Synthetic system prompt", "Answer exactly ONE."],
            ["Answer exactly THREE.", "THREE"],
        ),
    ],
)
def test_claude_compaction_action_rewrites_selected_range(
    tmp_path: Path,
    monkeypatch,
    include_system_feature: bool,
    inputs: Dict[str, Any],
    expected_leading_contents: list[str],
    expected_trailing_contents: list[str],
) -> None:
    from agent_terminal_app import server as server_mod
    from claude_tools import claude_compaction_feature as feature_mod

    fixture = _fixture("success-basic")
    summary_body = _summary_body_from_fixture(fixture)
    captured: Dict[str, Any] = {}

    def _fake_run_compaction_request(
        core: Any,
        session: Session,
        config: Dict[str, Any],
        *,
        context: Dict[str, Any] | None = None,
    ) -> str:
        captured["session"] = session
        captured["config"] = dict(config)
        _ = core, context
        return f"<analysis>ok</analysis>\n<summary>\n{summary_body}\n</summary>"

    monkeypatch.setattr(
        feature_mod,
        "_run_compaction_request",
        _fake_run_compaction_request,
        raising=True,
    )

    app = _build_app(tmp_path, include_system_feature=include_system_feature)
    session = _seed_session(app)

    resp = server_mod.execute_action(
        {
            "plugin": "claude_compaction",
            "action_id": "compact_conversation",
            "action_owner": "feature",
            "inputs": {
                "session_id": session.session_id,
                **inputs,
            },
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    assert resp["plugin"] == "claude_compaction"
    assert resp["result"]["message"] == "Compacted conversation."

    loaded = app.load_session_record(session.session_id)
    assert loaded is not None
    expected_summary = resp["result"]["compact_summary_text"]
    assert expected_summary == build_compact_summary_text(
        summary_body,
        transcript_path=str(_transcript_path_from_summary(expected_summary)),
    )
    _assert_rewrite_shape(
        loaded,
        expected_summary,
        expect_system=include_system_feature,
        expected_leading_contents=expected_leading_contents,
        expected_trailing_contents=expected_trailing_contents,
    )

    request_session = captured["session"]
    if include_system_feature:
        assert request_session.messages[0].role == "system"
    else:
        assert all(message.role != "system" for message in request_session.messages)
    assert captured["config"]["model"] == "test-model"

    transcript_path = _transcript_path_from_summary(expected_summary)
    assert transcript_path.exists()
    assert (
        transcript_path.parent
        == tmp_path / "sessions" / "claude-compaction-transcripts"
    )
    assert transcript_path.suffix == ".jsonl"
    assert transcript_path != tmp_path / "sessions" / f"{session.session_id}.json"
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
    assert transcript_entries[1]["message"]["content"][0]["text"] == "ONE"
    assert transcript_entries[3]["message"]["content"][0]["text"] == "TWO"
    assert transcript_entries[5]["message"]["content"][0]["text"] == "THREE"


def test_claude_compaction_action_accepts_summary_with_inapplicable_section(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Regression test: a summary missing an inapplicable section must not
    fail the compaction.

    Models legitimately omit sections such as "Errors and fixes:" when the
    conversation had no errors. Before the relax, the action failed with
    "summary is missing required sections" even though the summary was
    usable; snapshots and the Retry followup are the safety net.
    """

    from agent_terminal_app import server as server_mod
    from claude_tools import claude_compaction_feature as feature_mod

    fixture = _fixture("success-basic")
    summary_body = _summary_body_from_fixture(fixture)
    # Drop the "4. Errors and fixes:" section header (and its content lines
    # up to the next numbered header) to simulate an inapplicable section.
    # The fixture's "All user messages" section quotes the compaction prompt
    # verbatim; that quote contains the same header text, so it is dropped
    # too. Otherwise the header substring would still be present and the
    # strict validator would not treat the section as missing.
    remaining_lines: list[str] = []
    skipping = False
    for line in summary_body.splitlines():
        if line.startswith("4. Errors and fixes:"):
            skipping = True
            continue
        if skipping and re.match(r"^\d+\.\s", line):
            skipping = False
        if "CRITICAL: Respond with TEXT ONLY" in line:
            continue
        if not skipping:
            remaining_lines.append(line)
    partial_body = "\n".join(remaining_lines).strip()
    assert "4. Errors and fixes:" not in partial_body
    assert "5. Problem Solving:" in partial_body

    def _fake_run_compaction_request(
        core: Any,
        session: Session,
        config: Dict[str, Any],
        *,
        context: Dict[str, Any] | None = None,
    ) -> str:
        _ = core, context
        return f"<analysis>ok</analysis>\n<summary>\n{partial_body}\n</summary>"

    monkeypatch.setattr(
        feature_mod,
        "_run_compaction_request",
        _fake_run_compaction_request,
        raising=True,
    )

    app = _build_app(tmp_path)
    session = _seed_session(app)

    resp = server_mod.execute_action(
        {
            "plugin": "claude_compaction",
            "action_id": "compact_conversation",
            "action_owner": "feature",
            "inputs": {"session_id": session.session_id},
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    assert resp["result"]["message"] == "Compacted conversation."

    loaded = app.load_session_record(session.session_id)
    assert loaded is not None
    summary = resp["result"]["compact_summary_text"]
    summary_index = next(
        idx for idx, message in enumerate(loaded.messages) if message.content == summary
    )
    assert loaded.messages[summary_index].content == summary
    assert "4. Errors and fixes:" not in summary
