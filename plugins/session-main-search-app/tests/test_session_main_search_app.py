from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator

import pytest

from agent_app.application_future import AgentApplication
from agent_core import Message, Session


ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = ROOT / "plugins" / "session-main-search-app"


@pytest.fixture
def application(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[AgentApplication]:
    monkeypatch.setenv("REPO_ROOT", str(ROOT))
    config: Dict[str, Any] = {
        "providers": {
            "echo": {
                "provider": "echo_openai_like",
                "model": "test-model",
            }
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            f"path:{ROOT / 'plugins' / 'session-title-app'}",
            f"path:{ROOT / 'plugins' / 'session-message-count-meta-app'}",
            f"path:{PLUGIN_ROOT}",
        ],
        "agents": {"default": {"provider": "echo"}},
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    app = AgentApplication(config_path, tmp_path / "sessions")
    try:
        yield app
    finally:
        app.close()


def _save(
    application: AgentApplication,
    *,
    session_id: str,
    preview: str,
    metadata: Dict[str, Any],
) -> None:
    application.save_session(
        Session(
            session_id=session_id,
            messages=(
                Message(role="system", content="system"),
                Message(role="user", content=preview),
            ),
            metadata={"agent_id": "default", **metadata},
        )
    )


def test_plugin_contributes_main_and_focused_search_filters(
    application: AgentApplication,
) -> None:
    schema = application.get_session_list_filter_schema()

    assert schema["main_search_id"] == "session_search"
    assert schema["main_search_conflict"] is False
    assert schema["filters"] == [
        {
            "ui_type": "session_list_filter",
            "id": "session_search",
            "label": "Search",
            "order": 0.0,
            "data": [
                "session_id",
                "preview",
                "first_user_message",
                "presentation.title",
                "presentation.subtitle",
                "presentation.meta",
            ],
            "type": "text",
            "match": "contains",
            "default": "",
            "main_search": True,
            "plugin": "session_main_search",
            "icon": "search",
            "case_sensitive": False,
        },
        {
            "ui_type": "session_list_filter",
            "id": "session_title_search",
            "label": "Title / subtitle",
            "order": 10.0,
            "data": [
                "presentation.title",
                "presentation.subtitle",
            ],
            "type": "text",
            "match": "contains",
            "default": "",
            "main_search": False,
            "plugin": "session_main_search",
            "icon": "type",
            "case_sensitive": False,
        },
        {
            "ui_type": "session_list_filter",
            "id": "session_first_message_search",
            "label": "First message",
            "order": 20.0,
            "data": "first_user_message",
            "type": "text",
            "match": "contains",
            "default": "",
            "main_search": False,
            "plugin": "session_main_search",
            "icon": "message-square",
            "case_sensitive": False,
        },
    ]
    assert [
        action
        for action in application.get_application_actions()
        if action.get("plugin") == "session_main_search"
    ] == [
        {
            "id": "compute_first_user_message",
            "label": "Compute first user message",
            "description": (
                "Expose the complete first non-empty user message for "
                "session-list filtering."
            ),
            "inputs": {
                "session": {"required": False},
            },
            "trigger": "session_list",
            "plugin": "session_main_search",
        }
    ]
    assert not any(
        element.get("ui_type") == "session_list_action"
        and element.get("plugin") == "session_main_search"
        for element in application.get_application_ui_schema()
    )


def test_plugin_searches_all_summary_presentation_paths_case_insensitively(
    application: AgentApplication,
) -> None:
    _save(
        application,
        session_id="needle-id",
        preview="ordinary preview",
        metadata={},
    )
    _save(
        application,
        session_id="preview",
        preview="Needle preview",
        metadata={},
    )
    _save(
        application,
        session_id="title",
        preview="fallback",
        metadata={"title": "Needle title"},
    )
    _save(
        application,
        session_id="subtitle",
        preview="fallback",
        metadata={"subtitle": "Needle subtitle"},
    )

    summaries = application.list_session_summaries(
        filter_values={"session_search": "NEEDLE"},
        apply_filter_defaults=True,
    )

    assert {summary["session_id"] for summary in summaries} == {
        "needle-id",
        "preview",
        "title",
        "subtitle",
    }

    meta_matches = application.list_session_summaries(
        filter_values={"session_search": "2 MESSAGES"},
        apply_filter_defaults=True,
    )
    assert {summary["session_id"] for summary in meta_matches} == {
        "needle-id",
        "preview",
        "title",
        "subtitle",
    }


def test_focused_filters_search_displayed_title_and_complete_first_user_message(
    application: AgentApplication,
) -> None:
    long_first_message = (
        "This opening request deliberately exceeds the abbreviated preview "
        "boundary by a wide margin before ending with DeepFirstNeedle."
    )
    _save(
        application,
        session_id="first-message",
        preview=long_first_message,
        metadata={"title": "Ordinary title", "subtitle": "Ordinary subtitle"},
    )
    _save(
        application,
        session_id="title",
        preview="ordinary opening request",
        metadata={"title": "FocusedTitleNeedle", "subtitle": "Other subtitle"},
    )
    _save(
        application,
        session_id="subtitle",
        preview="another ordinary request",
        metadata={"title": "Other title", "subtitle": "FocusedSubtitleNeedle"},
    )
    application.save_session(
        Session(
            session_id="no-user-message",
            messages=(Message(role="system", content="system only"),),
            metadata={"agent_id": "default"},
        )
    )

    title_matches = application.list_session_summaries(
        filter_values={"session_title_search": "focusedtitleneedle"},
        apply_filter_defaults=True,
    )
    assert [summary["session_id"] for summary in title_matches] == ["title"]

    subtitle_matches = application.list_session_summaries(
        filter_values={"session_title_search": "FOCUSEDSUBTITLENEEDLE"},
        apply_filter_defaults=True,
    )
    assert [summary["session_id"] for summary in subtitle_matches] == ["subtitle"]

    first_message_matches = application.list_session_summaries(
        filter_values={"session_first_message_search": "deepfirstneedle"},
        apply_filter_defaults=True,
    )
    assert [summary["session_id"] for summary in first_message_matches] == [
        "first-message"
    ]
    assert first_message_matches[0]["first_user_message"] == long_first_message
    assert "DeepFirstNeedle" not in first_message_matches[0]["preview"]

    main_search_matches = application.list_session_summaries(
        filter_values={"session_search": "DEEPFIRSTNEEDLE"},
        apply_filter_defaults=True,
    )
    assert [summary["session_id"] for summary in main_search_matches] == [
        "first-message"
    ]

    no_user_summary = application.get_session_summary("no-user-message")
    assert no_user_summary["first_user_message"] == ""
