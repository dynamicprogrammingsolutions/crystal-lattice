from __future__ import annotations

import json
import runpy
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
FEATURE_SYSTEM_MESSAGE_SRC = ROOT / "plugins" / "feature-system-message" / "src"
if str(FEATURE_SYSTEM_MESSAGE_SRC) not in sys.path:
    sys.path.insert(0, str(FEATURE_SYSTEM_MESSAGE_SRC))


REPO_ROOT = Path(__file__).resolve().parents[3]
HELPERS_ROOT = (
    REPO_ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "system_messages"
    / "helpers"
)


def test_claude_runtime_resolves_relative_working_directory(
    monkeypatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "repo" / "workspace"
    workspace.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    namespace = runpy.run_path(
        str(HELPERS_ROOT / "claude_runtime.py"),
        init_globals={"CONFIG": {"working_directory": "repo/workspace"}},
    )

    assert namespace["cwd"] == str(workspace.resolve())
    assert isinstance(namespace["shell"], str)
    assert namespace["shell"]


def test_claude_environment_helper_renders_effective_working_directory(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    workspace = repo_root / "workspace"
    workspace.mkdir(parents=True)

    subprocess.run(
        ["git", "init"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    monkeypatch.chdir(tmp_path)

    runtime_ns = runpy.run_path(
        str(HELPERS_ROOT / "claude_runtime.py"),
        init_globals={
            "CONFIG": {
                "working_directory": "repo/workspace",
                "model": "anthropic/claude-haiku-4.5",
            }
        },
    )
    environment_ns = runpy.run_path(
        str(HELPERS_ROOT / "render_claude_environment_section.py"),
        init_globals=runtime_ns,
    )

    environment_text = str(environment_ns["SYSTEM_MESSAGE_VALUE"])

    assert "# Environment" in environment_text
    assert f" - Primary working directory: {workspace.resolve()}" in environment_text
    assert " - Is a git repository: true" in environment_text
    assert " - Platform:" in environment_text
    assert " - Shell:" in environment_text
    assert " - OS Version:" in environment_text
    assert (
        " - You are powered by the model anthropic/claude-haiku-4.5."
        in environment_text
    )


def test_default_config_claude_system_message_renders_sections_tasks_and_agents(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from feature_system_message.system_message_feature import SystemMessageFeature

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "AGENTS.md").write_text(
        "Workspace agent instructions.\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(workspace)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
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
    monkeypatch.setenv("BUILTIN_PLUGINS", str((ROOT / "plugins").resolve()))

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []

    _core, base_config, _session = app.create_session("claude")
    base_config = {**base_config, "include_tasks": True}

    feature = SystemMessageFeature()
    state = feature.init(base_config, {})
    native, _new_state = feature.initialize_request(
        [{"role": "user", "content": "Inspect the repo."}],
        state,
    )

    compiled = native[0]["_metadata"]["compiled_content"]

    assert native[0]["role"] == "system"
    assert "# System" in compiled
    assert "# Using your tools" in compiled
    assert "# Tone and style" in compiled
    assert "# Environment" in compiled
    assert "# Context management" in compiled
    assert "Primary working directory:" in compiled
    assert "When a file-oriented tool requires an absolute path" in compiled
    assert "Task files are a handoff mechanism" in compiled
    assert "# Contextual Instructions (AGENTS.md)" in compiled
    assert "Workspace agent instructions." in compiled


def test_default_config_claude_agent_uses_claude_tools(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
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

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []

    _core, base_config, _session = app.create_session("claude")

    assert base_config["provider"] == "openrouter"
    assert base_config["model"] == "anthropic/claude-haiku-4.5"
    assert base_config["gemini_api_key"] == "test-gemini-key"
    assert base_config["tavily_api_key"] == "test-tavily-key"
    assert base_config["web_search_enabled"] is True
    assert base_config["web_search_provider"] == "gemini_api"
    assert base_config["mcp_enabled"] is False
    assert base_config["mcp_reuse_runtime"] is True
    assert base_config["mcp_fail_on_startup_error"] is False
    assert "filesystem" in base_config["mcp_servers"]

    plugin_ids = {
        entry["id"]
        for entry in app.list_plugins_for_agent("claude")
        if entry["kind"] == "tools"
    }
    assert "claude_read_tool" in plugin_ids
    assert "claude_write_tool" in plugin_ids
    assert "claude_edit_tool" in plugin_ids
    assert "claude_glob_tool" in plugin_ids
    assert "claude_grep_tool" in plugin_ids
    assert "claude_bash_tool" in plugin_ids
    assert "claude_task_stop_tool" in plugin_ids
    assert "claude_web_fetch_tool" in plugin_ids
    assert "claude_web_search_tool" in plugin_ids
    assert "claude_mcp_tool" in plugin_ids
    assert "shell" not in plugin_ids

    config = json.loads(config_path.read_text(encoding="utf-8"))
    claude_agent = config["agents"]["claude"]
    assert "claude_mcp_defaults" in claude_agent["mixin_refs"]
    assert claude_agent["plugins"] == ["path:${env:BUILTIN_PLUGINS}/claude-tools"]
    assert "anthropic-openrouter" not in config["agents"]
