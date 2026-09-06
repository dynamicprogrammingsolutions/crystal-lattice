from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable

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

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core import Session  # noqa: E402
from agent_terminal_app import server as server_mod  # noqa: E402


CONFIG_PATH = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "config.json"
)
TEST_MODEL = "openai/gpt-5.4-nano"


@pytest.fixture(scope="module")
def ensure_openrouter_api_key() -> str:
    api_key = get_repo_env("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip(
            "OPENROUTER_API_KEY not set; skipping default-config Codex MCP integration test"
        )
    return api_key


def _run_request(
    app: AgentApplication,
    core: Any,
    session: Session,
    base_config: Dict[str, Any],
) -> Session:
    events = list(
        app.send_request(core, session, base_config, overrides=None, stream=False)
    )
    checkpoints = [
        event for event in events if event.get("type") == "session_checkpoint"
    ]
    assert checkpoints, "expected at least one session checkpoint"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)
    return final_session


def _iter_tool_messages(session: Session) -> Iterable[Session]:
    for message in session.messages:
        if message.role == "tool":
            yield message


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openrouter
def test_default_config_codex_mcp_via_real_ui_flow(
    ensure_openrouter_api_key: str,
    monkeypatch: pytest.MonkeyPatch,
    default_config_test_env,
) -> None:
    if shutil.which("npx") is None:
        pytest.skip("npx not available; cannot launch filesystem MCP server")

    workspace_root = ROOT / ".tmp-mcp-e2e"
    workspace_root.mkdir(exist_ok=True)
    workspace_dir = Path(tempfile.mkdtemp(prefix="codex-mcp-", dir=workspace_root))
    target = workspace_dir / "note.txt"
    target.write_text("alpha from mcp\nsecond line\n", encoding="utf-8")
    shutil.rmtree(CONFIG_PATH.parent / ".plugin_cache", ignore_errors=True)
    default_env = default_config_test_env(
        cloud_runtime_build_context=workspace_dir / "cloud-runtime-context",
        OPENROUTER_API_KEY=ensure_openrouter_api_key,
    )

    app = AgentApplication(
        str(default_env.config_path),
        str(workspace_dir / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides=default_env.env_overrides,
    )

    try:
        create_resp = server_mod.create_session(
            {"agent_id": "codex-openrouter"}, app_instance=app
        )
        session_id = create_resp["session"]["session_id"]

        plugins_resp = server_mod.get_session_plugins(session_id, app_instance=app)
        plugins = plugins_resp["plugins"]
        enabled_plugin_ids = [
            entry["id"]
            for entry in plugins
            if isinstance(entry, dict)
            and entry.get("enabled") is True
            and (entry.get("kind") != "tools" or entry.get("id") == "codex_mcp_tool")
        ]
        assert "codex_mcp_tool" in enabled_plugin_ids

        put_resp = server_mod.put_session_plugins(
            session_id,
            {"enabled": enabled_plugin_ids},
            app_instance=app,
        )
        assert any(
            entry.get("id") == "codex_mcp_tool" and entry.get("enabled") is True
            for entry in put_resp["plugins"]
        )
        assert all(
            not (
                entry.get("kind") == "tools"
                and entry.get("id") in {"shell", "shell_command"}
            )
            or entry.get("enabled") is False
            for entry in put_resp["plugins"]
        )

        ui_resp = server_mod.get_session_ui_schema(session_id, app_instance=app)
        ui_elements = ui_resp["elements"]
        global_toggle = next(
            element
            for element in ui_elements
            if isinstance(element, dict) and element.get("key") == "mcp_enabled"
        )
        server_toggle = next(
            element
            for element in ui_elements
            if isinstance(element, dict)
            and isinstance(element.get("key"), str)
            and str(element.get("key")).startswith("mcp_server__")
        )
        assert global_toggle["type"] == "checkbox"
        assert server_toggle["type"] == "checkbox"

        schema_resp = server_mod.get_session_config_schema(session_id, app_instance=app)
        schema = schema_resp["schema"]
        model_entry = next(
            entry
            for entry in schema
            if isinstance(entry, dict) and entry.get("key") == "model"
        )
        assert model_entry["key"] == "model"

        server_mod.patch_session_overrides(
            session_id,
            {
                "values": {
                    "model": TEST_MODEL,
                    "mcp_enabled": True,
                    str(server_toggle["key"]): True,
                }
            },
            app_instance=app,
        )

        app_ui_before = server_mod.get_session_application_ui_schema(
            session_id, app_instance=app
        )
        app_elements_before = app_ui_before["elements"]
        next(
            element
            for element in app_elements_before
            if isinstance(element, dict)
            and element.get("plugin") == "mcp_runtime_app"
            and element.get("action_id") == "mcp_show_status"
        )

        status_before = server_mod.execute_action(
            {
                "plugin": "mcp_runtime_app",
                "action_id": "mcp_show_status",
                "inputs": {"session_id": session_id},
            },
            app_instance=app,
        )
        assert status_before["status"] == "ok"
        assert (
            "No MCP runtimes are currently stored."
            in status_before["result"]["display"]["body"]
        )

        server_mod.add_message(
            session_id,
            {
                "role": "user",
                "content": (
                    "Use an MCP filesystem tool to read the file at "
                    f"{target.resolve()} and then answer with exactly the first line of that file and nothing else."
                ),
            },
            app_instance=app,
        )

        loaded = app.load_session(session_id)
        assert loaded is not None
        core, base_config, session = loaded
        final_session = _run_request(app, core, session, base_config)

        tool_messages = list(_iter_tool_messages(final_session))
        assert tool_messages, "expected at least one tool message"
        assert any(
            isinstance((message.metadata or {}).get("tool_name"), str)
            and str((message.metadata or {}).get("tool_name")).startswith(
                "mcp__filesystem__"
            )
            for message in tool_messages
        )

        assistant_messages = [
            message for message in final_session.messages if message.role == "assistant"
        ]
        assert assistant_messages, "expected assistant response"
        final_text = str(assistant_messages[-1].content or "").strip()
        assert final_text == "alpha from mcp"

        status_after = server_mod.execute_action(
            {
                "plugin": "mcp_runtime_app",
                "action_id": "mcp_show_status",
                "inputs": {"session_id": session_id},
            },
            app_instance=app,
        )
        assert status_after["status"] == "ok"
        body = status_after["result"]["display"]["body"]
        assert "filesystem" in body
        assert "connected" in body
    finally:
        app.close()
        shutil.rmtree(workspace_dir, ignore_errors=True)
