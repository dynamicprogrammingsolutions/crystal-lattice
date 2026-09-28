from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient
import pytest

from agent_app import AgentApplication
from agent_core import Message, Session
from agent_terminal_app import server as server_mod


pytestmark = pytest.mark.integration


class DateFilterApplicationPlugin:
    name = "date_filter_http_fixture"
    version = "1.0.0"

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config, context
        return [
            {
                "ui_type": "session_list_filter",
                "id": "modified_after",
                "label": "Modified after",
                "data": "modified",
                "type": "datetime",
                "match": "on_or_after",
                "default": None,
            }
        ]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return []


def _application(tmp_path: Path) -> tuple[AgentApplication, Path]:
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "providers": {
                    "echo": {
                        "provider": "echo_openai_like",
                        "model": "query-test",
                    }
                },
                "plugins": [
                    "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
                    "test_session_data_query_http.DateFilterApplicationPlugin",
                ],
                "agents": {"default": {"provider": "echo"}},
            }
        ),
        encoding="utf-8",
    )
    session_root = tmp_path / "sessions"
    return AgentApplication(config, session_root), session_root


def _save(
    application: AgentApplication,
    *,
    session_id: str,
    messages: list[Message],
) -> None:
    application.save_session(
        Session(
            session_id=session_id,
            messages=messages,
            metadata={"agent_id": "default"},
        )
    )


# Requirements:
# - SLIST-021: Exercises a plugin-declared timezone-aware datetime comparison.
# - SLIST-022: Exercises UTC normalization also covered by the shared Python/TS fixture.
# - SLIST-023: Passes a plugin filter ID through the production HTTP adapter.
# - SLIST-024: Preserves the default envelope and projects only after filtering.
@pytest.mark.integration
def test_http_session_query_reuses_plugin_filters_and_preserves_default(
    tmp_path: Path,
) -> None:
    application, session_root = _application(tmp_path)
    server_mod.app.dependency_overrides[server_mod.get_agent_app] = lambda: application
    client = TestClient(server_mod.app)
    try:
        _save(
            application,
            session_id="older",
            messages=[Message(role="user", content="older")],
        )
        _save(
            application,
            session_id="newer",
            messages=[Message(role="user", content="newer")],
        )
        os.utime(
            session_root / "older.json",
            ns=(1_000_000_000, 1_000_000_000),
        )
        os.utime(
            session_root / "newer.json",
            ns=(2_000_000_000, 2_000_000_000),
        )

        default_response = client.get("/sessions")
        assert default_response.status_code == 200
        assert default_response.json() == {
            "sessions": application.list_session_summaries()
        }

        projected = client.get(
            "/sessions",
            params=[
                ("filter", "modified_after=1970-01-01T00:00:01.500000Z"),
                ("include", "$.sessions[*].session_id"),
            ],
        )
        assert projected.status_code == 200
        assert projected.json() == {"sessions": [{"session_id": "newer"}]}

        invalid = client.get(
            "/sessions",
            params={"filter": "modified_after=2026-09-01T00:00:00"},
        )
        assert invalid.status_code == 400
        assert "timezone-aware" in invalid.json()["detail"]
    finally:
        server_mod.app.dependency_overrides.clear()
        application.close()


def test_http_message_query_projects_visible_fields_and_omits_tools(
    tmp_path: Path,
) -> None:
    application, _session_root = _application(tmp_path)
    server_mod.app.dependency_overrides[server_mod.get_agent_app] = lambda: application
    client = TestClient(server_mod.app)
    try:
        _save(
            application,
            session_id="messages",
            messages=[
                Message(
                    role="tool",
                    content="large tool data",
                    metadata={"tool_name": "shell"},
                    tool_result={"result": "large"},
                ),
                Message(
                    role="assistant",
                    content="Crystal Lattice result",
                    metadata={
                        "reasoning": "Inspect the configuration",
                        "tool_calls": [{"id": "call"}],
                    },
                ),
                Message(role="future-role", content="future content"),
            ],
        )

        default_response = client.get("/sessions/messages/messages")
        assert default_response.status_code == 200
        default_payload = default_response.json()
        assert default_payload["messages"][0]["message"]["toolResult"] == {
            "result": "large"
        }
        assert "cursor_event_id" in default_payload

        projected = client.get(
            "/sessions/messages/messages",
            params=[
                ("include", "$.messages[*].index"),
                ("include", "$.messages[*].message.role"),
                ("include", "$.messages[*].message.content"),
                ("include", "$.messages[*].message.metadata.reasoning"),
                ("exclude", '$.messages[?(@.message.role == "tool")]'),
            ],
        )
        assert projected.status_code == 200
        assert projected.json() == {
            "messages": [
                {
                    "index": 1,
                    "message": {
                        "role": "assistant",
                        "content": "Crystal Lattice result",
                        "metadata": {"reasoning": "Inspect the configuration"},
                    },
                },
                {
                    "index": 2,
                    "message": {
                        "role": "future-role",
                        "content": "future content",
                    },
                },
            ]
        }

        invalid = client.get(
            "/sessions/messages/messages",
            params={"include": "$["},
        )
        assert invalid.status_code == 400
        assert "invalid include JSONPath" in invalid.json()["detail"]
    finally:
        server_mod.app.dependency_overrides.clear()
        application.close()
