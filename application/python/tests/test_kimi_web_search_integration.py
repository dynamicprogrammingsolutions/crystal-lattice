"""Integration tests for Kimi SearchWeb via default config."""

from __future__ import annotations

import os
import sys
from pathlib import Path

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


def _get_env_key(key_name: str) -> str:
    value = os.environ.get(key_name, "")
    if value:
        return value
    env_path = ROOT / ".env"
    if not env_path.exists():
        return ""
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(f"{key_name}="):
                return line[len(key_name) + 1 :].strip().strip('"').strip("'")
    return ""


@pytest.fixture(scope="module")
def gemini_api_key() -> str:
    key = _get_env_key("GEMINI_API_KEY")
    if not key:
        pytest.skip("GEMINI_API_KEY not set; skipping Kimi SearchWeb integration")
    return key


@pytest.fixture(scope="module")
def openrouter_api_key() -> str:
    key = _get_env_key("OPENROUTER_API_KEY")
    if not key:
        pytest.skip("OPENROUTER_API_KEY not set; skipping default config test")
    return key


def _make_agent_app(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    openrouter_api_key: str,
    gemini_api_key: str,
):
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    monkeypatch.setenv("OPENROUTER_API_KEY", openrouter_api_key)
    monkeypatch.setenv("GEMINI_API_KEY", gemini_api_key)
    monkeypatch.setenv("TAVILY_API_KEY", _get_env_key("TAVILY_API_KEY"))
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-fireworks-key")
    monkeypatch.setenv("ZAI_API_KEY", "test-zai-key")
    monkeypatch.setenv("CLOUD_ORCHESTRATOR_URL", "http://cloud-orchestrator.test")
    monkeypatch.setenv("CLOUD_ORCHESTRATOR_TOKEN", "test-cloud-token")

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    monkeypatch.setenv("CONFIG_DIR", str(config_path.parent.resolve()))
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("WORKING_DIR", str(workspace))
    session_root = tmp_path / "sessions"
    app = AgentApplication(
        str(config_path),
        str(session_root),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []
    return app, config_path, session_root


@pytest.mark.integration
def test_kimi_default_config_search_web_with_gemini_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    openrouter_api_key: str,
    gemini_api_key: str,
) -> None:
    from agent_app.config import resolve_request_config
    from agent_terminal_app.terminal_app import TerminalApplication

    agent_app, config_path, session_root = _make_agent_app(
        tmp_path,
        monkeypatch,
        openrouter_api_key,
        gemini_api_key,
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