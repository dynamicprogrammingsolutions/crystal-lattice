from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

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

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core import Session  # noqa: E402


@pytest.fixture(scope="module")
def ensure_openrouter_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip(
            "OPENROUTER_API_KEY not set; skipping Claude default-config integration test"
        )
    return api_key


def _run_request(
    app: AgentApplication,
    core: Any,
    session: Session,
    base_config: Dict[str, Any],
) -> tuple[Session, List[Dict[str, Any]], List[Dict[str, Any]]]:
    events = list(
        app.send_request(core, session, base_config, overrides=None, stream=True)
    )
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints, "expected at least one session checkpoint"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)
    finals = [ev for ev in events if ev.get("type") == "final"]
    assert finals, "expected a final event"
    final_messages = finals[-1].get("messages") or []
    return final_session, final_messages, events


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openrouter
def test_agent_application_default_config_claude_reads_files_and_reasons(
    ensure_openrouter_api_key: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "bank_a.txt").write_text("3\n4\n5\n", encoding="utf-8")
    (workspace / "bank_b.txt").write_text("6\n8\n7\n", encoding="utf-8")
    monkeypatch.chdir(workspace)

    monkeypatch.setenv("OPENROUTER_API_KEY", ensure_openrouter_api_key)
    monkeypatch.setenv(
        "ANTHROPIC_API_KEY",
        os.getenv("ANTHROPIC_API_KEY", "test-anthropic-key"),
    )
    monkeypatch.setenv("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "test-gemini-key"))
    monkeypatch.setenv("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY", "test-tavily-key"))
    monkeypatch.setenv("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "test-openai-key"))
    monkeypatch.setenv(
        "FIREWORKS_API_KEY", os.getenv("FIREWORKS_API_KEY", "test-fireworks-key")
    )
    monkeypatch.setenv("ZAI_API_KEY", os.getenv("ZAI_API_KEY", "test-zai-key"))
    monkeypatch.setenv(
        "CLOUD_ORCHESTRATOR_URL",
        os.getenv("CLOUD_ORCHESTRATOR_URL", "http://cloud-orchestrator.test"),
    )
    monkeypatch.setenv(
        "CLOUD_ORCHESTRATOR_TOKEN",
        os.getenv("CLOUD_ORCHESTRATOR_TOKEN", "test-cloud-token"),
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
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)
    assert app.get_config_errors() == []

    core, base_config, session = app.create_session("claude-openrouter")
    assert base_config["request_options"]["provider"] == {
        "order": ["anthropic"],
        "allow_fallbacks": False,
    }

    session = core.add_message(
        session,
        "user",
        (
            "Use the Read tool to read bank_a.txt and bank_b.txt. "
            "Each file contains one integer per line. Add the integers in each file, "
            "decide which file has the larger total, and reply with exactly "
            "`bank_a: 12` or `bank_b: 21` for the winner."
        ),
        config=base_config,
    )
    app.save_session(session)

    final_session, final_messages, request_events = _run_request(
        app, core, session, base_config
    )
    assert final_session.messages, "expected final session messages"
    assert final_messages, "expected final messages"

    assistant_messages = [
        message
        for message in final_messages
        if isinstance(message, dict) and message.get("role") == "assistant"
    ]
    assert assistant_messages, "expected assistant final message"
    final_text = str(assistant_messages[-1].get("content") or "").strip()
    assert "bank_b: 21" in final_text, final_text

    tool_result_events = [
        ev
        for ev in request_events
        if isinstance(ev, dict) and ev.get("type") == "tool_results"
    ]
    assert tool_result_events, "expected tool_results events"
    tool_names = []
    for event in tool_result_events:
        for message in event.get("messages") or []:
            if not isinstance(message, dict):
                continue
            metadata = message.get("metadata") or {}
            tool_name = metadata.get("tool_name")
            if isinstance(tool_name, str) and tool_name:
                tool_names.append(tool_name)
    assert "Read" in tool_names, tool_names
