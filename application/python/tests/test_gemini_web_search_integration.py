"""Integration tests for GeminiWebSearchTool via default config.

Tests that the web search tool is properly wired through the
application config with ${env:...} placeholder resolution, that
the UI schema reflects the available providers, and that actual
API calls work when keys are present.

Requires GEMINI_API_KEY (and optionally TAVILY_API_KEY) in the
environment or .env file.
"""

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
        pytest.skip("GEMINI_API_KEY not set; skipping web search integration test")
    return key


@pytest.fixture(scope="module")
def tavily_api_key() -> str:
    return get_repo_env("TAVILY_API_KEY")


@pytest.fixture(scope="module")
def openrouter_api_key() -> str:
    key = get_repo_env("OPENROUTER_API_KEY")
    if not key:
        pytest.skip("OPENROUTER_API_KEY not set; skipping web search integration test")
    return key


def _make_agent_app(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    openrouter_api_key: str,
    gemini_api_key: str,
    tavily_api_key: str,
):
    """Build an AgentApplication with the default config and env keys set."""
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    monkeypatch.setenv("OPENROUTER_API_KEY", openrouter_api_key)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("GEMINI_API_KEY", gemini_api_key)
    if tavily_api_key:
        monkeypatch.setenv("TAVILY_API_KEY", tavily_api_key)

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    agent_app = AgentApplication(
        str(config_path), str(session_root), event_store=events
    )
    assert agent_app.get_config_errors() == []
    return agent_app


# ---------------------------------------------------------------------------
# UI Schema Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.gemini
def test_web_search_ui_schema_with_gemini_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    openrouter_api_key: str,
    gemini_api_key: str,
) -> None:
    """When GEMINI_API_KEY is set, UI schema includes web_search_enabled checkbox."""
    from agent_terminal_app.terminal_app import TerminalApplication

    agent_app = _make_agent_app(
        tmp_path, monkeypatch, openrouter_api_key, gemini_api_key, ""
    )
    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    session_root = tmp_path / "sessions"

    term_app = TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=agent_app,
    )

    term_app.start_new_session(agent_id="gemini")
    elements = term_app.session_ui_elements()

    # Find web search UI elements
    ws_keys = [
        el.get("key")
        for el in elements
        if isinstance(el, dict)
        and isinstance(el.get("key"), str)
        and "web_search" in el.get("key", "")
    ]
    assert (
        "web_search_enabled" in ws_keys
    ), f"web_search_enabled not in UI keys: {ws_keys}"


@pytest.mark.integration
@pytest.mark.gemini
def test_web_search_ui_schema_with_both_keys_shows_provider_select(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    openrouter_api_key: str,
    gemini_api_key: str,
    tavily_api_key: str,
) -> None:
    """When both GEMINI_API_KEY and TAVILY_API_KEY are set, UI schema
    includes a provider selector in addition to the enable checkbox."""
    if not tavily_api_key:
        pytest.skip("TAVILY_API_KEY not set; skipping dual-provider UI test")

    from agent_terminal_app.terminal_app import TerminalApplication

    agent_app = _make_agent_app(
        tmp_path, monkeypatch, openrouter_api_key, gemini_api_key, tavily_api_key
    )
    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    session_root = tmp_path / "sessions"

    term_app = TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=agent_app,
    )

    term_app.start_new_session(agent_id="gemini")
    elements = term_app.session_ui_elements()

    ws_elements = [
        el
        for el in elements
        if isinstance(el, dict)
        and isinstance(el.get("key"), str)
        and "web_search" in el.get("key", "")
    ]
    ws_keys = [el.get("key") for el in ws_elements]
    assert "web_search_enabled" in ws_keys, f"web_search_enabled not in keys: {ws_keys}"
    assert (
        "web_search_provider" in ws_keys
    ), f"web_search_provider not in keys (should appear when both keys available): {ws_keys}"

    # The provider selector should have options for both backends
    provider_el = next(
        el for el in ws_elements if el.get("key") == "web_search_provider"
    )
    options = provider_el.get("options", [])
    option_values = [o.get("value") for o in options if isinstance(o, dict)]
    assert (
        "gemini_api" in option_values
    ), f"gemini_api not in provider options: {option_values}"
    assert "tavily" in option_values, f"tavily not in provider options: {option_values}"


# ---------------------------------------------------------------------------
# Available Tools Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.gemini
def test_google_web_search_in_available_tools(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    openrouter_api_key: str,
    gemini_api_key: str,
) -> None:
    """google_web_search should appear in available tools when enabled."""
    from agent_terminal_app.terminal_app import TerminalApplication

    agent_app = _make_agent_app(
        tmp_path, monkeypatch, openrouter_api_key, gemini_api_key, ""
    )
    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    session_root = tmp_path / "sessions"

    term_app = TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=agent_app,
    )

    session = term_app.start_new_session(agent_id="gemini")

    loaded = agent_app.load_session(session.session_id)
    assert loaded is not None
    core, base_config, _session = loaded

    available = core.get_available_tools(base_config)
    tool_names = [t.tool_name for t in available]
    assert (
        "google_web_search" in tool_names
    ), f"google_web_search not in available tools: {tool_names}"


# ---------------------------------------------------------------------------
# Real API Call Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.gemini
def test_web_search_gemini_api_real_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    openrouter_api_key: str,
    gemini_api_key: str,
) -> None:
    """Web search with gemini_api backend makes a real Gemini API call
    and returns grounded results with citations."""
    from agent_terminal_app.terminal_app import TerminalApplication

    agent_app = _make_agent_app(
        tmp_path, monkeypatch, openrouter_api_key, gemini_api_key, ""
    )
    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    session_root = tmp_path / "sessions"

    term_app = TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=agent_app,
    )

    session = term_app.start_new_session(agent_id="gemini")
    term_app.append_user_message(
        "Use the google_web_search tool to search for 'Python programming language'. "
        "Reply with a one-sentence summary of what you found."
    )

    final_session_dict, _messages, _request_id = term_app.send_request(stream=False)
    assert final_session_dict is not None

    loaded = agent_app.load_session(session.session_id)
    assert loaded is not None
    _core, _base_config, final_session = loaded

    # The model should have called google_web_search
    tool_messages = [m for m in final_session.messages if m.role == "tool"]
    tool_names_in_session = []
    for msg in tool_messages:
        metadata = msg.metadata if isinstance(msg.metadata, dict) else {}
        name = metadata.get("tool_name", "")
        if name:
            tool_names_in_session.append(name)

    assert (
        "google_web_search" in tool_names_in_session
    ), f"google_web_search not called. Tools called: {tool_names_in_session}"

    # The final assistant message should mention Python
    final_text = final_session.messages[-1].content.strip()
    assert (
        "Python" in final_text or "python" in final_text.lower()
    ), f"Final response doesn't mention Python: {final_text[:200]}"


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.gemini
def test_web_search_tavily_backend_real_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    openrouter_api_key: str,
    gemini_api_key: str,
    tavily_api_key: str,
) -> None:
    """Web search with tavily backend makes a real Tavily API call
    and returns results in Gemini-style format."""
    if not tavily_api_key:
        pytest.skip("TAVILY_API_KEY not set; skipping Tavily backend test")

    from agent_terminal_app.terminal_app import TerminalApplication

    agent_app = _make_agent_app(
        tmp_path, monkeypatch, openrouter_api_key, gemini_api_key, tavily_api_key
    )
    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    session_root = tmp_path / "sessions"

    term_app = TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=agent_app,
    )

    # Switch to tavily provider via session override
    session = term_app.start_new_session(agent_id="gemini")
    term_app.update_override("web_search_provider", "tavily")
    term_app.append_user_message(
        "Use the google_web_search tool to search for 'Python programming language'. "
        "Reply with a one-sentence summary of what you found."
    )

    final_session_dict, _messages, _request_id = term_app.send_request(stream=False)
    assert final_session_dict is not None

    loaded = agent_app.load_session(session.session_id)
    assert loaded is not None
    _core, _base_config, final_session = loaded

    # The model should have called google_web_search
    tool_messages = [m for m in final_session.messages if m.role == "tool"]
    tool_names_in_session = []
    for msg in tool_messages:
        metadata = msg.metadata if isinstance(msg.metadata, dict) else {}
        name = metadata.get("tool_name", "")
        if name:
            tool_names_in_session.append(name)

    assert (
        "google_web_search" in tool_names_in_session
    ), f"google_web_search not called. Tools called: {tool_names_in_session}"
