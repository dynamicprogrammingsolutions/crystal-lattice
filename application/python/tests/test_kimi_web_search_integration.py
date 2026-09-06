"""Integration tests for Kimi SearchWeb via default config."""

from __future__ import annotations

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


@pytest.fixture(scope="module")
def gemini_api_key() -> str:
    key = get_repo_env("GEMINI_API_KEY")
    if not key:
        pytest.skip("GEMINI_API_KEY not set; skipping Kimi SearchWeb integration")
    return key


@pytest.fixture(scope="module")
def openrouter_api_key() -> str:
    key = get_repo_env("OPENROUTER_API_KEY")
    if not key:
        pytest.skip("OPENROUTER_API_KEY not set; skipping default config test")
    return key


def _make_agent_app(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    openrouter_api_key: str,
    gemini_api_key: str,
    default_config_test_env,
):
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    default_env = default_config_test_env(
        OPENROUTER_API_KEY=openrouter_api_key,
        GEMINI_API_KEY=gemini_api_key,
        WORKING_DIR=workspace,
    )
    session_root = tmp_path / "sessions"
    app = AgentApplication(
        str(default_env.config_path),
        str(session_root),
        event_store=InMemoryEventStore(),
        env_overrides=default_env.env_overrides,
    )
    assert app.get_config_errors() == []
    return app, default_env.config_path, session_root


@pytest.mark.integration
@pytest.mark.api
def test_kimi_default_config_search_web_with_gemini_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    openrouter_api_key: str,
    gemini_api_key: str,
    default_config_test_env,
) -> None:
    from agent_app.config import resolve_request_config
    from agent_terminal_app.terminal_app import TerminalApplication

    agent_app, config_path, session_root = _make_agent_app(
        tmp_path,
        monkeypatch,
        openrouter_api_key,
        gemini_api_key,
        default_config_test_env,
    )
    term_app = TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=agent_app,
    )

    session = term_app.start_new_session(agent_id="kimi")
    term_app.update_override("web_search_enabled", True)
    term_app.update_override("web_search_provider", "gemini_api")

    loaded = agent_app.load_session(session.session_id)
    assert loaded is not None
    core, base_config, loaded_session = loaded
    overrides = loaded_session.metadata.get("overrides")
    assert isinstance(overrides, dict)
    effective_config = resolve_request_config(base_config, overrides)

    available = core.get_available_tools(effective_config)
    tool_names = [tool.tool_name for tool in available]
    assert "SearchWeb" in tool_names

    messages = core.execute_tool_calls(
        [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "SearchWeb",
                    "arguments": {
                        "query": "Python programming language official website",
                        "limit": 3,
                    },
                },
            }
        ],
        effective_config,
    )

    assert len(messages) == 1
    assert messages[0]["role"] == "tool"
    assert messages[0]["metadata"]["tool_name"] == "SearchWeb"
    assert "Title: " in messages[0]["content"]
    assert "URL: " in messages[0]["content"]
    assert "Summary: " in messages[0]["content"]
