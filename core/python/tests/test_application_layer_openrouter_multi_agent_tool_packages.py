"""Application-level OpenRouter integration tests for multi-agent tool packages."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_CONFIG_DIR = Path(__file__).resolve().parent / "fixtures" / "configs"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter integration test")


def _prepare_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".temp").mkdir()
    (workspace / "codex.txt").write_text("CODEX integration line\nsecond line\n", encoding="utf-8")
    (workspace / "gemini.txt").write_text("GEMINI integration line\nsecond line\n", encoding="utf-8")
    (workspace / "qwen.txt").write_text("QWEN integration line\nsecond line\n", encoding="utf-8")
    (workspace / "grok.txt").write_text("GROK integration line\nsecond line\n", encoding="utf-8")
    return workspace


def _configure_env(monkeypatch: pytest.MonkeyPatch, workspace: Path, cache_dir: Path) -> None:
    monkeypatch.setenv("REPO_ROOT", str(REPO_ROOT))
    monkeypatch.setenv("PLUGIN_CACHE_DIR", str(cache_dir))
    monkeypatch.setenv("WORKSPACE_DIR", str(workspace))
    monkeypatch.setenv("OPENROUTER_API_KEY", OPENROUTER_API_KEY or "")


def _agent_expectations(workspace: Path) -> Dict[str, Dict[str, str]]:
    return {
        "codex-agent": {
            "file_name": "codex.txt",
            "tool_name": "shell",
            "arg_key": "command",
            "expected_line": "CODEX integration line",
            "module_prefix": "codex_tools.",
            "system_message": "Use the shell tool to inspect files. Do not answer from memory.",
            "user_message": (
                "Use the shell tool to print the first line of codex.txt and reply with exactly that line."
            ),
        },
        "gemini-agent": {
            "file_name": "gemini.txt",
            "tool_name": "read_file",
            "arg_key": "file_path",
            "expected_line": "GEMINI integration line",
            "module_prefix": "gemini_tools.",
            "system_message": "Use the read_file tool when a file must be read. Do not answer from memory.",
            "user_message": "Use read_file on gemini.txt and reply with exactly the first line.",
        },
        "qwen-agent": {
            "file_name": "qwen.txt",
            "tool_name": "read_file",
            "arg_key": "absolute_path",
            "expected_line": "QWEN integration line",
            "module_prefix": "qwen_tools.",
            "system_message": (
                "Use the read_file tool with an absolute path when a file must be read. "
                "Do not answer from memory."
            ),
            "user_message": (
                f"Use read_file with the absolute path {workspace / 'qwen.txt'} and reply with exactly the first line."
            ),
        },
        "grok-agent": {
            "file_name": "grok.txt",
            "tool_name": "view_file",
            "arg_key": "path",
            "expected_line": "GROK integration line",
            "module_prefix": "grok_tools.",
            "system_message": "Use the view_file tool when a file must be inspected. Do not answer from memory.",
            "user_message": "Use view_file on grok.txt and reply with exactly the first line.",
        },
    }


def _parse_tool_call(events: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    final_events = [ev for ev in events if ev.get("type") == "final"]
    assert final_events, "expected at least one final event"
    first_final = final_events[0]
    messages = first_final.get("messages") or []
    assistants = [m for m in messages if isinstance(m, dict) and m.get("role") == "assistant"]
    assert assistants, "expected assistant message in first final event"
    metadata = assistants[-1].get("metadata") or {}
    tool_calls = metadata.get("tool_calls") or []
    assert tool_calls, "expected at least one tool call"
    function_info = tool_calls[0].get("function") or {}
    arguments = function_info.get("arguments") or {}
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    return str(function_info.get("name") or ""), arguments if isinstance(arguments, dict) else {}


def _assert_agent_catalog(app: AgentApplication, agent_id: str, expected_prefix: str) -> None:
    class_paths = [entry["class_path"] for entry in app.list_plugins_for_agent(agent_id)]
    assert any(path.startswith("openrouter_plugins.") for path in class_paths)
    assert any(path.startswith(expected_prefix) for path in class_paths)

    other_prefixes = {"codex_tools.", "gemini_tools.", "qwen_tools.", "grok_tools."} - {expected_prefix}
    for prefix in other_prefixes:
        assert not any(path.startswith(prefix) for path in class_paths), (
            f"did not expect {prefix} plugins in catalog for {agent_id}: {class_paths}"
        )


def _run_multi_agent_fixture(config_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = _prepare_workspace(tmp_path)
    cache_dir = tmp_path / "plugin_cache"
    _configure_env(monkeypatch, workspace, cache_dir)

    config_path = FIXTURE_CONFIG_DIR / config_name
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), event_store=InMemoryEventStore())

    assert app.get_config_errors() == []

    expectations = _agent_expectations(workspace)
    for agent_id, expected in expectations.items():
        _assert_agent_catalog(app, agent_id, expected["module_prefix"])

        core, base_config, session = app.create_session(agent_id)
        session = core.add_message(
            session,
            "system",
            expected["system_message"],
            metadata=None,
            config=base_config,
        )
        session = core.add_message(
            session,
            "user",
            expected["user_message"],
            metadata=None,
            config=base_config,
        )
        app.save_session(session)

        events = list(app.send_request(core, session, base_config, stream=False))
        tool_name, arguments = _parse_tool_call(events)
        assert tool_name == expected["tool_name"]
        assert expected["arg_key"] in arguments

        tool_result_events = [ev for ev in events if ev.get("type") == "tool_results"]
        assert tool_result_events, "expected tool_results event"
        tool_messages = [msg for ev in tool_result_events for msg in (ev.get("messages") or [])]
        assert tool_messages, "expected tool message"
        first_tool_message = tool_messages[0]
        tool_metadata = first_tool_message.get("metadata") or {}
        assert tool_metadata.get("tool_name") == expected["tool_name"]

        final_events = [ev for ev in events if ev.get("type") == "final"]
        last_final = final_events[-1]
        final_messages = last_final.get("messages") or []
        assistants = [m for m in final_messages if isinstance(m, dict) and m.get("role") == "assistant"]
        assert assistants, "expected final assistant message"
        final_text = str(assistants[-1].get("content") or "")
        assert expected["expected_line"] in final_text


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_multi_agent_tool_packages_provider_plugins(
    ensure_api_key: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_multi_agent_fixture(
        "openrouter_multi_agent_provider_plugins.json",
        tmp_path,
        monkeypatch,
    )


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_multi_agent_tool_packages_agent_plugins(
    ensure_api_key: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_multi_agent_fixture(
        "openrouter_multi_agent_agent_plugins.json",
        tmp_path,
        monkeypatch,
    )