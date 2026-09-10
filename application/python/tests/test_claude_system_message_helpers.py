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
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
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
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )
    monkeypatch.setenv("BUILTIN_PLUGINS", str((ROOT / "plugins").resolve()))

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []

    _core, base_config, _session = app.create_session("claude-openrouter")
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
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
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
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []

    expected_agents = {
        "claude-openrouter": {
            "provider": "openrouter",
            "model": "anthropic/claude-haiku-4.5",
        },
        "claude-anthropic": {
            "provider": "anthropic",
            "model": "claude-sonnet-5",
        },
    }
    for agent_id, expected in expected_agents.items():
        _core, base_config, _session = app.create_session(agent_id)

        assert base_config["provider"] == expected["provider"]
        assert base_config["model"] == expected["model"]
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
            for entry in app.list_plugins_for_agent(agent_id)
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
    assert "claude" not in config["agents"]
    for agent_id in (
        "claude-openrouter",
        "claude-anthropic",
    ):
        claude_agent = config["agents"][agent_id]
        assert "claude_mcp_defaults" in claude_agent["mixin_refs"]
        assert claude_agent["plugins"] == ["path:${env:BUILTIN_PLUGINS}/claude-tools"]
    assert (
        "claude_anthropic_model_variants"
        in config["agents"]["claude-anthropic"]["mixin_refs"]
    )


def test_default_config_claude_system_message_uses_permissive_tool_usage_variable() -> (
    None
):
    """The default config wires the claude system message to the permissive-cd
    tool-usage variable while keeping every tool-usage variant selectable."""
    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))
    system_message = config["mixins"]["claude_system_message"]["system_message"]

    template = system_message["template"]
    assert "{{TOOL_USAGE_PERMISSIVE_CD}}" in template
    assert "{{TOOL_USAGE}}" not in template

    variables = system_message["variables"]
    expected_tool_usage_variables = {
        "TOOL_USAGE": "tool-usage.md",
        "TOOL_USAGE_PERMISSIVE_CD": "tool-usage-permissive-cd.md",
        "TOOL_USAGE_PERMISSIVE_CD_NO_PERSISTENCE": (
            "tool-usage-permissive-cd-no-persistence.md"
        ),
    }
    for variable_name, filename in expected_tool_usage_variables.items():
        assert variable_name in variables
        # The variant file must exist so the variable renders real content.
        assert (
            ROOT / "plugins" / "claude-tools" / "system_messages" / "claude" / filename
        ).is_file()


def _resolve_default_config_with_env(monkeypatch, config_path: Path):
    from agent_app.config import (
        build_config_resolution_env,
        load_raw_config,
        resolve_placeholders,
    )

    for key in (
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "TAVILY_API_KEY",
        "OPENAI_API_KEY",
        "FIREWORKS_API_KEY",
        "ZAI_API_KEY",
        "CLOUD_ORCHESTRATOR_URL",
        "CLOUD_ORCHESTRATOR_TOKEN",
    ):
        monkeypatch.setenv(key, "test")
    monkeypatch.setenv("CONFIG_DIR", str(config_path.parent.resolve()))
    monkeypatch.setenv("BUILTIN_PLUGINS", str((ROOT / "plugins").resolve()))

    raw = load_raw_config(config_path)
    resolved_placeholders, _errors = resolve_placeholders(
        raw, env=build_config_resolution_env(config_path)
    )
    return resolved_placeholders


def test_default_config_claude_bash_presets_resolve_coherent_combinations(
    monkeypatch,
) -> None:
    """Each claude bash preset, listed right after ``claude_system_message``
    in an agent's ``mixin_refs`` with a per-key merge policy deep-merging
    ``system_message``, yields its documented Bash tool configuration keys and
    tool-usage template variable while keeping the base system-message
    variables. The configured claude agents resolve to a coherent combination:
    the template's persistence claim matches the actual Bash behavior."""
    from agent_app.config import build_agent_config, resolve_config_mixins

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    resolved_placeholders = _resolve_default_config_with_env(monkeypatch, config_path)

    expected_presets = {
        "claude_bash_upstream_parity": (True, False, False, "{{TOOL_USAGE}}"),
        "claude_bash_permissive": (
            True,
            False,
            True,
            "{{TOOL_USAGE_PERMISSIVE_CD}}",
        ),
        "claude_bash_permissive_visible": (
            True,
            True,
            True,
            "{{TOOL_USAGE_PERMISSIVE_CD}}",
        ),
        "claude_bash_permissive_no_persistence": (
            False,
            False,
            True,
            "{{TOOL_USAGE_PERMISSIVE_CD_NO_PERSISTENCE}}",
        ),
    }
    for preset_name, (
        persistence,
        include,
        permissive,
        variable,
    ) in expected_presets.items():
        probe_config = dict(resolved_placeholders)
        probe_config["agents"] = {
            **resolved_placeholders["agents"],
            "__preset_probe__": {
                "$merge": {"default": "shallow", "deep": ["system_message"]},
                "provider": "openrouter",
                "mixin_refs": ["claude_system_message", preset_name],
            },
        }
        resolved, errors = resolve_config_mixins(probe_config)
        assert errors == []

        agent_config = build_agent_config(resolved, "__preset_probe__")
        assert agent_config["bash_cwd_persistence"] == persistence
        assert agent_config["bash_include_cwd_in_result"] == include
        assert agent_config["bash_permissive_cd_guidance"] == permissive
        assert variable in agent_config["system_message"]["template"]
        # The agent-level deep merge keeps the base mixin's variables and
        # toggle while the preset overrides the template variable.
        assert agent_config["system_message"]["variables"]["TOOL_USAGE"]["files"]
        assert agent_config["system_message_enabled"] is True

    # The configured claude agents resolve to a coherent combination without
    # pinning which preset is the default: the template's persistence claim
    # must match the actual Bash cwd persistence, and the base variables must
    # survive the preset overlay.
    resolved, errors = resolve_config_mixins(resolved_placeholders)
    assert errors == []
    for agent_id in (
        "claude-openrouter",
        "claude-anthropic",
        "glm-ollama",
        "deepseek-ollama",
    ):
        agent_config = build_agent_config(resolved, agent_id)
        template = agent_config["system_message"]["template"]
        if agent_config["bash_cwd_persistence"]:
            assert "{{TOOL_USAGE_PERMISSIVE_CD_NO_PERSISTENCE}}" not in template
        else:
            assert "{{TOOL_USAGE_PERMISSIVE_CD}}" not in template
        assert agent_config["system_message"]["variables"]["TOOL_USAGE"]["files"]
        assert agent_config["system_message_enabled"] is True


def test_claude_bash_preset_applies_to_agent_and_renders_system_message(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Listing a preset mixin right after ``claude_system_message`` in an
    agent's ``mixin_refs`` yields the preset's Bash tool configuration keys
    and renders the preset's tool-usage section end to end."""
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from feature_system_message.system_message_feature import SystemMessageFeature

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["agents"]["glm-ollama"]["mixin_refs"] = [
        "claude_system_message",
        "claude_bash_permissive_no_persistence",
        "claude_mcp_defaults",
    ]
    preset_config_path = tmp_path / "config.json"
    preset_config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    _resolved_placeholders = _resolve_default_config_with_env(monkeypatch, config_path)
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )

    app = AgentApplication(
        str(preset_config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []

    _core, base_config, _session = app.create_session("glm-ollama")
    assert base_config["bash_cwd_persistence"] is False
    assert base_config["bash_include_cwd_in_result"] is False
    assert base_config["bash_permissive_cd_guidance"] is True

    feature = SystemMessageFeature()
    state = feature.init(base_config, {})
    native, _new_state = feature.initialize_request(
        [{"role": "user", "content": "Inspect the repo."}],
        state,
    )
    compiled = native[0]["_metadata"]["compiled_content"]
    assert "# Using your tools" in compiled
    assert (
        "The working directory does not persist between commands; chain "
        "`cd dir && cmd` in a single Bash call"
    ) in compiled
    assert "persists between commands, so `cd` alone" not in compiled
