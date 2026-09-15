from __future__ import annotations

import json
from pathlib import Path
import runpy
from typing import Any

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
    "codex-openrouter",
    "codex-openai",
    "qwen",
    "gemini",
    "grok",
    "kimi",
    "claude-openrouter",
)


def _write_echo_config(path: Path) -> Path:
    layout = load_runtime_layout()
    resolved, _errors, _environment = load_resolved_config(
        DEFAULT_CONFIG,
        env_overrides={
            **layout.env_overrides(),
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
    return path


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


def test_access_helper_renders_quoted_same_runtime_commands(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "config with spaces.json"
    session_root = tmp_path / "sessions with spaces"
    docs = tmp_path / "docs with spaces"
    docs.mkdir()
    cli_argv = [
        str(tmp_path / "python with spaces"),
        "-m",
        "agent_terminal_app",
        "--config",
        str(config_path),
        "--sessions-dir",
        str(session_root),
    ]
    monkeypatch.setenv("CRYSTAL_LATTICE_CLI_ARGV_JSON", json.dumps(cli_argv))
    monkeypatch.setenv("CRYSTAL_LATTICE_CONFIG", str(config_path))
    monkeypatch.setenv("CRYSTAL_LATTICE_SESSIONS", str(session_root))
    monkeypatch.setenv("CRYSTAL_LATTICE_PYTHON", cli_argv[0])
    monkeypatch.setenv("CRYSTAL_LATTICE_PYTHON_API_MODULE", "agent_terminal_app")
    monkeypatch.setenv("CRYSTAL_LATTICE_DOCS", str(docs))
    monkeypatch.setenv(
        "CRYSTAL_LATTICE_DOCS_URL",
        "https://docs.crystallattice.dev/packages/application-python/"
        "headless-agent-runs/",
    )

    namespace = runpy.run_path(
        str(ACCESS_HELPER),
        init_globals={"CONFIG": {"include_crystal_lattice_access": True}},
    )
    rendered = namespace["get_value"]()

    assert "# Crystal Lattice Access" in rendered
    assert "agent_terminal_app" in rendered
    assert str(config_path) in rendered
    assert str(session_root) in rendered
    assert str(docs) in rendered
    assert "run --agent" in rendered
    assert "ordinary synchronous requests" in rendered


def test_access_helper_does_not_claim_python_api_when_unavailable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "CRYSTAL_LATTICE_CLI_ARGV_JSON",
        json.dumps([str(tmp_path / "crystal-lattice")]),
    )
    monkeypatch.delenv("CRYSTAL_LATTICE_PYTHON", raising=False)
    monkeypatch.delenv("CRYSTAL_LATTICE_PYTHON_API_MODULE", raising=False)

    namespace = runpy.run_path(
        str(ACCESS_HELPER),
        init_globals={"CONFIG": {"include_crystal_lattice_access": True}},
    )
    rendered = namespace["get_value"]()

    assert "does not expose a general Python interpreter" in rendered
    assert "from agent_terminal_app import open_runtime" not in rendered


def test_default_access_toggle_is_independent_and_compiles_for_all_agents(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = _write_echo_config(tmp_path / "config.json")
    sessions = tmp_path / "sessions"
    access_env = load_runtime_layout().application_env_overrides(
        config_path=config,
        session_root=sessions,
    )
    monkeypatch.setenv("UNRELATED_CREDENTIAL_MARKER", "must-not-appear")

    app = AgentApplication(
        config,
        sessions,
        application_notification_store=InMemoryApplicationNotificationStore(),
        env_overrides=access_env,
    )
    try:
        core, base_config, _session = app.create_session("codex-openrouter")
        schema = core.get_ui_schema(base_config)
        toggle = next(
            item
            for item in schema
            if item.get("key") == "include_crystal_lattice_access"
        )
        assert toggle["ui_type"] == "config"
        assert toggle["type"] == "checkbox"
        assert toggle["label"] == "Include Crystal Lattice Access Guidance"
        assert toggle["default"] is False

        for agent_id in AGENT_IDS:
            disabled = _compiled_system_text(
                app,
                agent_id,
                include_access=False,
            )
            enabled = _compiled_system_text(
                app,
                agent_id,
                include_access=True,
            )

            assert "# Crystal Lattice Access" not in disabled, agent_id
            assert "# Crystal Lattice Access" in enabled, agent_id
            assert str(config.resolve()) in enabled
            assert str(sessions.resolve()) in enabled
            assert "from agent_terminal_app import open_runtime" in enabled
            assert "Task Files and Subtasks" not in enabled
            assert "must-not-appear" not in enabled
    finally:
        app.close()
