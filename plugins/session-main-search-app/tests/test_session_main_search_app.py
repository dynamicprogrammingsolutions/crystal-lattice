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


def test_plugin_contributes_main_search_without_actions(
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
        }
    ]
    assert [
        action
        for action in application.get_application_actions()
        if action.get("plugin") == "session_main_search"
    ] == []


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
