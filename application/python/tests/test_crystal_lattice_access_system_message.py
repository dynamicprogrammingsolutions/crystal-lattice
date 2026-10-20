from __future__ import annotations

import json
from pathlib import Path
import runpy
import sys
from typing import Any

import pytest

from agent_app import AgentApplication, InMemoryApplicationNotificationStore
from agent_app.config import build_agent_config, load_resolved_config
from agent_terminal_app.runtime_layout import load_runtime_layout


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "config.json"
)
ACCESS_HELPER = (
    DEFAULT_CONFIG.parent / "system_messages" / "helpers" / "crystal_lattice_access.py"
)
AGENT_IDS = (
    "cloud-script-author",
    "codex-openrouter",
    "codex-openai",
    "codex-openai-api",
    "gpt-5-openrouter",
    "gpt-5-openai",
    "qwen",
    "gemini",
    "grok",
    "kimi",
    "claude-openrouter",
    "claude-anthropic",
    "glm",
    "glm-ollama",
    "deepseek-ollama",
    "kimi-ollama",
)


def _access_env(
    config_path: Path,
    session_root: Path,
    *,
    full: bool = True,
) -> dict[str, str]:
    session_root.mkdir(parents=True, exist_ok=True)
    values = load_runtime_layout().application_env_overrides(
        config_path=config_path,
        session_root=session_root,
    )
    if not full:
        values.pop("CRYSTAL_LATTICE_PYTHON", None)
        values.pop("CRYSTAL_LATTICE_PYTHON_API_MODULE", None)
    return values


def _write_echo_config(
    path: Path,
    session_root: Path,
    *,
    full: bool,
) -> tuple[Path, dict[str, str]]:
    access_env = _access_env(path, session_root, full=full)
    resolved, _errors, _environment = load_resolved_config(
        DEFAULT_CONFIG,
        env_overrides={
            **access_env,
            "CONFIG_DIR": str(DEFAULT_CONFIG.parent),
        },
    )
    agents: dict[str, dict[str, Any]] = {}
    for agent_id in AGENT_IDS:
        agent = build_agent_config(resolved, agent_id)
        agent["provider"] = "echo"
        agent["system_message_as_instructions"] = False
        agents[agent_id] = agent

    path.write_text(
        json.dumps(
            {
                "providers": {
                    "echo": {
                        "provider": "echo_openai_like",
                        "model": "access-system-message-test",
                    }
                },
                "plugins": [
                    "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
                    "feature_system_message.system_message_feature.SystemMessageFeature",
                ],
                "agents": agents,
            }
        ),
        encoding="utf-8",
    )
    return path, access_env


def _compiled_system_text(
    app: AgentApplication,
    agent_id: str,
    *,
    include_access: bool,
) -> str:
    _core, _base, session = app.create_session(agent_id)
    result = app.run_session_request_with_message(
        session.session_id,
        role="user",
        content="Inspect access guidance.",
        overrides={
            "include_crystal_lattice_access": include_access,
            "include_tasks": False,
        },
        stream=False,
    )
    assert result.status == "succeeded"
    content = result.final_messages[-1]["content"]
    assert isinstance(content, str)
    prefix = "SYS="
    suffix = " | USER=Inspect access guidance."
    assert content.startswith(prefix)
    assert content.endswith(suffix)
    return content[len(prefix) : -len(suffix)]


def _load_helper(
    monkeypatch,
    access_env: dict[str, str],
    *,
    requested: bool,
) -> dict[str, Any]:
    for name in (
        "CRYSTAL_LATTICE_CLI_ARGV_JSON",
        "CRYSTAL_LATTICE_CLI_COMMAND",
        "CRYSTAL_LATTICE_CONFIG",
        "CRYSTAL_LATTICE_SESSIONS",
        "CRYSTAL_LATTICE_PYTHON",
        "CRYSTAL_LATTICE_PYTHON_API_MODULE",
        "CRYSTAL_LATTICE_DOCS",
        "CRYSTAL_LATTICE_DOCS_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    for name, value in access_env.items():
        monkeypatch.setenv(name, value)
    return runpy.run_path(
        str(ACCESS_HELPER),
        init_globals={"CONFIG": {"include_crystal_lattice_access": requested}},
    )


def test_runtime_access_values_render_a_shell_command(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config with spaces.json"
    config_path.write_text("{}", encoding="utf-8")
    session_root = tmp_path / "sessions with spaces"
    values = _access_env(config_path, session_root)

    argv = json.loads(values["CRYSTAL_LATTICE_CLI_ARGV_JSON"])
    assert argv[0] == str(Path(sys.executable).absolute())
    assert argv[-4:] == [
        "--config",
        str(config_path.resolve()),
        "--sessions-dir",
        str(session_root.resolve()),
    ]
    assert str(config_path.resolve()) in values["CRYSTAL_LATTICE_CLI_COMMAND"]
    assert str(session_root.resolve()) in values["CRYSTAL_LATTICE_CLI_COMMAND"]


def test_access_helper_reports_full_cli_only_and_unavailable_modes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    session_root = tmp_path / "sessions"

    full_namespace = _load_helper(
        monkeypatch,
        _access_env(config_path, session_root),
        requested=True,
    )
    assert full_namespace["include_crystal_lattice_access"]() is True
    assert full_namespace["include_crystal_lattice_cli_access"]() is False
    assert full_namespace["include_crystal_lattice_delegation_guidance"]() is True
    full_element = full_namespace["get_ui_elements"]()[0]
    assert full_element["disabled"] is False
    assert full_element["label"] == "Include Crystal Lattice Access Guidance"
    assert full_element["description"] == "CLI and Python SDK guidance are available."

    cli_namespace = _load_helper(
        monkeypatch,
        _access_env(config_path, session_root, full=False),
        requested=True,
    )
    assert cli_namespace["include_crystal_lattice_access"]() is False
    assert cli_namespace["include_crystal_lattice_cli_access"]() is True
    assert cli_namespace["include_crystal_lattice_delegation_guidance"]() is True
    cli_element = cli_namespace["get_ui_elements"]()[0]
    assert cli_element["disabled"] is False
    assert cli_element["label"].endswith("(CLI only)")
    assert "Python SDK guidance is unavailable" in cli_element["description"]

    unavailable = _access_env(config_path, session_root)
    unavailable.pop("CRYSTAL_LATTICE_CLI_COMMAND")
    unavailable_namespace = _load_helper(
        monkeypatch,
        unavailable,
        requested=True,
    )
    assert unavailable_namespace["include_crystal_lattice_access"]() is False
    assert unavailable_namespace["include_crystal_lattice_cli_access"]() is False
    assert (
        unavailable_namespace["include_crystal_lattice_delegation_guidance"]() is False
    )
    unavailable_element = unavailable_namespace["get_ui_elements"]()[0]
    assert unavailable_element["disabled"] is True
    assert unavailable_element["default"] is False
    assert unavailable_element["label"].endswith("(unavailable)")
    assert "CRYSTAL_LATTICE_CLI_COMMAND" in unavailable_element["description"]


@pytest.mark.parametrize(
    "missing_name",
    [
        "CRYSTAL_LATTICE_CLI_ARGV_JSON",
        "CRYSTAL_LATTICE_CLI_COMMAND",
        "CRYSTAL_LATTICE_CONFIG",
        "CRYSTAL_LATTICE_SESSIONS",
        "CRYSTAL_LATTICE_DOCS",
        "CRYSTAL_LATTICE_DOCS_URL",
    ],
)
def test_each_missing_cli_value_disables_access_with_a_named_reason(
    tmp_path: Path,
    monkeypatch,
    missing_name: str,
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    values = _access_env(config_path, tmp_path / "sessions")
    values.pop(missing_name)

    namespace = _load_helper(monkeypatch, values, requested=True)

    assert namespace["include_crystal_lattice_access"]() is False
    assert namespace["include_crystal_lattice_cli_access"]() is False
    element = namespace["get_ui_elements"]()[0]
    assert element["disabled"] is True
    assert element["default"] is False
    assert missing_name in element["description"]


@pytest.mark.parametrize(
    "missing_name",
    [
        "CRYSTAL_LATTICE_PYTHON",
        "CRYSTAL_LATTICE_PYTHON_API_MODULE",
    ],
)
def test_each_missing_sdk_value_selects_cli_only_with_a_named_reason(
    tmp_path: Path,
    monkeypatch,
    missing_name: str,
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    values = _access_env(config_path, tmp_path / "sessions")
    values.pop(missing_name)

    namespace = _load_helper(monkeypatch, values, requested=True)

    assert namespace["include_crystal_lattice_access"]() is False
    assert namespace["include_crystal_lattice_cli_access"]() is True
    element = namespace["get_ui_elements"]()[0]
    assert element["disabled"] is False
    assert element["label"].endswith("(CLI only)")
    assert missing_name in element["description"]


def test_access_message_is_owned_by_one_config_mixin_not_helper_code() -> None:
    raw_config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    access_mixin = raw_config["mixins"]["crystal_lattice_access"]
    variables = access_mixin["system_message"]["variables"]

    assert {
        "CRYSTAL_LATTICE_ACCESS",
        "CRYSTAL_LATTICE_CLI_ACCESS",
        "CRYSTAL_LATTICE_DELEGATION_GUIDANCE",
    }.issubset(variables)
    assert variables["CRYSTAL_LATTICE_ACCESS"]["text"].startswith(
        "# Crystal Lattice Access (CLI and Python SDK)"
    )
    assert variables["CRYSTAL_LATTICE_CLI_ACCESS"]["text"].startswith(
        "# Crystal Lattice Access (CLI only)"
    )
    assert (
        "{{CRYSTAL_LATTICE_CLI_COMMAND_VALUE}}"
        in variables["CRYSTAL_LATTICE_ACCESS"]["text"]
    )
    for variable_name in (
        "CRYSTAL_LATTICE_ACCESS",
        "CRYSTAL_LATTICE_CLI_ACCESS",
    ):
        text = variables[variable_name]["text"]
        assert (
            text.count("Active session root: `{{CRYSTAL_LATTICE_SESSIONS_VALUE}}`") == 1
        )
        assert "Shared session root:" not in text
        assert "~/.crystal/sessions" not in text
        assert text.endswith("{{CRYSTAL_LATTICE_DELEGATION_GUIDANCE}}")
    delegation_text = variables["CRYSTAL_LATTICE_DELEGATION_GUIDANCE"]["text"]
    assert delegation_text.startswith("# Delegating work through Crystal Lattice")
    assert "These instructions are for you, the parent agent." in delegation_text
    assert "construct a self-contained child user prompt" in delegation_text
    assert '--prompt-file "<path>"' in delegation_text
    assert "--stdin" in delegation_text
    assert "Discover capabilities from the active config" in delegation_text
    assert "${env:BUILTIN_PLUGINS}" in delegation_text
    assert (
        "selected Crystal Lattice agent's own configured system/developer message"
        in delegation_text
    )
    assert "Do not copy your system message" in delegation_text
    assert "code" not in variables["CRYSTAL_LATTICE_ACCESS"]
    assert "code" not in variables["CRYSTAL_LATTICE_CLI_ACCESS"]
    assert "code" not in variables["CRYSTAL_LATTICE_DELEGATION_GUIDANCE"]

    helper_text = ACCESS_HELPER.read_text(encoding="utf-8")
    assert "Start a delegated task" not in helper_text
    assert "Inspect bounded history" not in helper_text
    assert "from agent_terminal_app import open_runtime" not in helper_text
    configured_access_agents = {
        agent_id
        for agent_id, config in raw_config["agents"].items()
        if "crystal_lattice_access" in config.get("mixin_refs", [])
    }
    assert configured_access_agents == set(AGENT_IDS)


def test_default_access_variants_compile_exclusively_for_all_agents(
    tmp_path: Path,
    monkeypatch,
) -> None:
    full_sessions = tmp_path / "full-sessions"
    full_config, full_env = _write_echo_config(
        tmp_path / "full-config.json",
        full_sessions,
        full=True,
    )
    monkeypatch.setenv("UNRELATED_CREDENTIAL_MARKER", "must-not-appear")

    full_app = AgentApplication(
        full_config,
        full_sessions,
        application_notification_store=InMemoryApplicationNotificationStore(),
        env_overrides=full_env,
    )
    try:
        core, base_config, _session = full_app.create_session("codex-openrouter")
        toggle = next(
            item
            for item in core.get_ui_schema(base_config)
            if item.get("key") == "include_crystal_lattice_access"
        )
        assert toggle["disabled"] is False
        assert toggle["default"] is False

        for agent_id in AGENT_IDS:
            disabled = _compiled_system_text(
                full_app,
                agent_id,
                include_access=False,
            )
            enabled = _compiled_system_text(
                full_app,
                agent_id,
                include_access=True,
            )
            assert "# Crystal Lattice Access" not in disabled, agent_id
            assert "# Delegating work through Crystal Lattice" not in disabled
            assert "# Crystal Lattice Access (CLI and Python SDK)" in enabled, agent_id
            assert "# Crystal Lattice Access (CLI only)" not in enabled, agent_id
            assert enabled.count("# Delegating work through Crystal Lattice") == 1
            assert str(full_config.resolve()) in enabled
            assert str(full_sessions.resolve()) in enabled
            assert (
                enabled.count(f"Active session root: `{full_sessions.resolve()}`") == 1
            )
            assert "from agent_terminal_app import open_runtime" in enabled
            assert 'models --agent "<agent-id>" --format json' in enabled
            assert 'runtime.list_models(agent_id="<agent-id>")' in enabled
            assert '--prompt-file "<path>"' in enabled
            assert "Built-in plugin docs and source:" in enabled
            assert str(Path(full_env["BUILTIN_PLUGINS"]).resolve()) in enabled
            assert "Task Files and Subtasks" not in enabled
            assert "must-not-appear" not in enabled
    finally:
        full_app.close()

    # A CLI-only runtime can be launched from a shell owned by another
    # Crystal Lattice process; isolate the simulated runtime's capabilities.
    monkeypatch.delenv("CRYSTAL_LATTICE_PYTHON", raising=False)
    monkeypatch.delenv("CRYSTAL_LATTICE_PYTHON_API_MODULE", raising=False)
    cli_sessions = tmp_path / "cli-sessions"
    cli_config, cli_env = _write_echo_config(
        tmp_path / "cli-config.json",
        cli_sessions,
        full=False,
    )
    cli_app = AgentApplication(
        cli_config,
        cli_sessions,
        application_notification_store=InMemoryApplicationNotificationStore(),
        env_overrides=cli_env,
    )
    try:
        for agent_id in AGENT_IDS:
            enabled = _compiled_system_text(
                cli_app,
                agent_id,
                include_access=True,
            )
            assert "# Crystal Lattice Access (CLI only)" in enabled, agent_id
            assert "# Crystal Lattice Access (CLI and Python SDK)" not in enabled
            assert enabled.count("# Delegating work through Crystal Lattice") == 1
            assert "from agent_terminal_app import open_runtime" not in enabled
            assert 'models --agent "<agent-id>" --format json' in enabled
            assert "runtime.list_models" not in enabled
            assert '--prompt-file "<path>"' in enabled
            assert str(Path(cli_env["BUILTIN_PLUGINS"]).resolve()) in enabled
    finally:
        cli_app.close()
