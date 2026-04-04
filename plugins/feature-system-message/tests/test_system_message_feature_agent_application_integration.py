from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Session


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = (
    REPO_ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "config.json"
)
DEFAULT_CONFIG_DIR = DEFAULT_CONFIG_PATH.parent


def _provider_configs_with_echo_provider(
    source_config: dict[str, Any],
    provider_ids: tuple[str, ...],
) -> dict[str, Any]:
    providers: dict[str, Any] = {}
    for provider_id in provider_ids:
        provider_config = dict(source_config["providers"][provider_id])
        provider_config["provider"] = "echo_openai_like"
        provider_config["model"] = "echo-test-1"
        provider_config["timeout"] = 60
        provider_config.pop("api_key", None)
        provider_config.pop("base_url", None)
        provider_config.pop("plugins", None)
        provider_config.pop("disabled_plugins", None)
        providers[provider_id] = provider_config
    return providers


def _last_assistant_text(events: list[dict[str, Any]]) -> str:
    finals = [event for event in events if event.get("type") == "final"]
    assert finals

    messages = finals[-1].get("messages") or []
    assistants = [
        msg
        for msg in messages
        if isinstance(msg, dict) and msg.get("role") == "assistant"
    ]
    assert assistants
    return str(assistants[-1].get("content") or "")


def _compiled_system_text(events: list[dict[str, Any]]) -> str:
    assistant_text = _last_assistant_text(events)
    assert assistant_text.startswith("SYS=")
    system_text, separator, _user_text = assistant_text[4:].partition(" | USER=")
    assert separator == " | USER="
    return system_text


def test_system_message_feature_persists_single_template_system_message(
    tmp_path: Path,
) -> None:
    system_template = "You are a helpful {{STYLE}} system message for tests."
    config: Dict[str, Any] = {
        "providers": {
            "echo_with_system": {
                "provider": "echo_openai_like",
                "model": "echo-test-1",
                "timeout": 60,
                "system_message_enabled": True,
                "system_message": {
                    "template": system_template,
                    "variables": {"STYLE": "dynamic"},
                },
            }
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "feature_system_message.system_message_feature.SystemMessageFeature",
        ],
        "agents": {
            "default": {
                "provider": "echo_with_system",
            }
        },
    }

    cfg_path = tmp_path / "config_system_message_app.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(cfg_path), str(session_root), event_store=events_store)

    core, base_config, session = app.create_session("default")
    session = core.add_message(
        session, "user", "first", metadata=None, config=base_config
    )

    events1 = list(
        app.send_request(core, session, base_config, overrides=None, stream=False)
    )
    checkpoints1 = [ev for ev in events1 if ev.get("type") == "session_checkpoint"]
    assert checkpoints1
    session1 = checkpoints1[-1]["session"]
    assert isinstance(session1, Session)
    app.save_session(session1)

    native1 = session1.metadata.get("native_messages") or []
    sys_native1 = [
        m for m in native1 if isinstance(m, dict) and m.get("role") == "system"
    ]
    assert sys_native1 and sys_native1[0].get("content") == system_template
    assert [message.role for message in session1.messages] == ["system", "user", "assistant"]
    assert session1.messages[0].content == system_template
    assert session1.messages[0].metadata["compiled_content"] == (
        "You are a helpful dynamic system message for tests."
    )

    core2, base_config2, loaded1 = app.load_session(session1.session_id)
    session2 = core2.add_message(
        loaded1, "user", "second", metadata=None, config=base_config2
    )

    events2 = list(
        app.send_request(core2, session2, base_config2, overrides=None, stream=False)
    )
    checkpoints2 = [ev for ev in events2 if ev.get("type") == "session_checkpoint"]
    assert checkpoints2
    session3 = checkpoints2[-1]["session"]
    assert isinstance(session3, Session)

    native2 = session3.metadata.get("native_messages") or []
    sys_native2 = [
        m for m in native2 if isinstance(m, dict) and m.get("role") == "system"
    ]
    assert len(sys_native2) == 1
    assert sys_native2[0].get("content") == system_template
    assert len([message for message in session3.messages if message.role == "system"]) == 1
    assert session3.messages[0].metadata["compiled_content"] == (
        "You are a helpful dynamic system message for tests."
    )


def test_system_message_feature_renders_conditional_markdown_sections_for_git_and_cwd(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime_file = tmp_path / "runtime.py"
    runtime_file.write_text(
        "import subprocess\n"
        "from pathlib import Path\n\n"
        "cwd = str(Path.cwd().resolve())\n\n"
        "def git_root(path=None):\n"
        "    target = Path(path or cwd)\n"
        "    if target.is_file():\n"
        "        target = target.parent\n"
        '    proc = subprocess.run(["git", "-C", str(target), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)\n'
        "    if proc.returncode != 0:\n"
        "        return None\n"
        "    return proc.stdout.strip() or None\n\n"
        "def is_git_repo(path=None):\n"
        "    return git_root(path) is not None\n",
        encoding="utf-8",
    )

    template_file = tmp_path / "template.md"
    template_file.write_text(
        "{{BASE}}\n\n{{GIT_SECTION}}\n\n{{WORKING_DIRECTORY_LINE}}\n",
        encoding="utf-8",
    )

    base_file = tmp_path / "base.md"
    base_file.write_text("Base instructions", encoding="utf-8")

    git_section_file = tmp_path / "git-section.md"
    git_section_file.write_text(
        "# Git Repository\n\n- Review changes with git status before committing.\n",
        encoding="utf-8",
    )

    config: Dict[str, Any] = {
        "providers": {
            "echo_with_system": {
                "provider": "echo_openai_like",
                "model": "echo-test-1",
                "timeout": 60,
                "system_message_enabled": True,
            }
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "feature_system_message.system_message_feature.SystemMessageFeature",
        ],
        "agents": {
            "default": {
                "provider": "echo_with_system",
                "system_message": {
                    "template": f"${{file:{template_file}}}",
                    "runtime_code": str(runtime_file),
                    "variables": {
                        "BASE": {"files": [str(base_file)]},
                        "GIT_SECTION": {
                            "files": [str(git_section_file)],
                            "condition": {"inline_code": "is_git_repo()"},
                        },
                        "WORKING_DIRECTORY_LINE": {
                            "inline_code": "f'Current working directory: {cwd}'"
                        },
                    },
                },
            }
        },
    }

    cfg_path = tmp_path / "config_system_message_dynamic.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")

    def _render_for(workdir: Path, session_name: str) -> str:
        monkeypatch.chdir(workdir)
        app = AgentApplication(
            str(cfg_path),
            str(tmp_path / session_name),
            event_store=InMemoryEventStore(),
        )
        core, base_config, session = app.create_session("default")
        session = core.add_message(
            session, "user", "hello", metadata=None, config=base_config
        )
        events = list(
            app.send_request(core, session, base_config, overrides=None, stream=False)
        )
        return _last_assistant_text(events)

    git_repo = tmp_path / "repo"
    git_repo.mkdir()
    subprocess.run(
        ["git", "init"], cwd=git_repo, check=True, capture_output=True, text=True
    )

    non_repo = tmp_path / "plain"
    non_repo.mkdir()

    git_text = _render_for(git_repo, "sessions_git")
    assert "Base instructions" in git_text
    assert "# Git Repository" in git_text
    assert f"Current working directory: {git_repo.resolve()}" in git_text

    non_repo_text = _render_for(non_repo, "sessions_plain")
    assert "Base instructions" in non_repo_text
    assert "# Git Repository" not in non_repo_text
    assert f"Current working directory: {non_repo.resolve()}" in non_repo_text


def test_portable_default_config_compiles_vendor_and_codex_system_messages(
    tmp_path: Path,
    monkeypatch,
) -> None:
    portable_config = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    provider_ids = tuple(portable_config["providers"].keys())

    config: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / "plugin_cache" / "plugins"),
        "providers": _provider_configs_with_echo_provider(portable_config, provider_ids),
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "feature_system_message.system_message_feature.SystemMessageFeature",
        ],
        "agents": dict(portable_config["agents"]),
    }

    config_path = tmp_path / "config_portable_system_message_echo.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    subprocess.run(
        ["git", "init"], cwd=repo_dir, check=True, capture_output=True, text=True
    )
    (repo_dir / "AGENTS.md").write_text(
        "Repository policy from AGENTS.\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(repo_dir)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={
            "CONFIG_DIR": str(DEFAULT_CONFIG_DIR),
            "WORKING_DIR": str(repo_dir),
        },
    )

    assert app.get_config_errors() == []

    expected_substrings = {
        "codex-openrouter": [
            "You are Codex, a coding agent based on GPT-5.",
            "Repository policy from AGENTS.",
        ],
        "codex-openai": [
            "You are Codex, a coding agent based on GPT-5.",
            "Repository policy from AGENTS.",
        ],
        "gemini": [
            "You are Gemini CLI, an interactive CLI agent specializing in software engineering tasks.",
            "# Git Repository",
            "Never stage or commit changes unless explicitly instructed to do so.",
            "# Contextual Instructions (AGENTS.md)",
            "Repository policy from AGENTS.",
        ],
        "qwen": [
            "You are Qwen Code, an interactive CLI agent developed by Alibaba Group, specializing in software engineering tasks.",
            "# Git Repository",
            "Never push changes to a remote repository without explicit user instruction.",
            "Repository policy from AGENTS.",
        ],
        "grok": [
            "You are Grok CLI, an AI assistant that helps with file editing, coding tasks, and system operations.",
            "You have access to these tools:",
            "Repository policy from AGENTS.",
            f"Current working directory: {repo_dir.resolve()}",
        ],
        "kimi": [
            "You are Kimi Code CLI, an interactive general AI agent running on a user's computer.",
            "If you anticipate making multiple non-interfering tool calls, you are highly encouraged to make them in parallel to improve efficiency.",
            "Repository policy from AGENTS.",
        ],
        "claude": [
            "You are Claude Code, Anthropic's official CLI for Claude.",
            "Repository policy from AGENTS.",
        ],
    }

    for agent_id, substrings in expected_substrings.items():
        core, base_config, session = app.create_session(agent_id)
        session = core.add_message(
            session,
            "user",
            f"Inspect the compiled system message for {agent_id}.",
            metadata=None,
            config=base_config,
        )

        events = list(
            app.send_request(core, session, base_config, overrides=None, stream=False)
        )
        system_text = _compiled_system_text(events)

        assert "{{" not in system_text
        for substring in substrings:
            assert substring in system_text
        assert "Task Files and Subtasks" not in system_text


def test_portable_default_codex_system_message_selection_by_model_and_personality(
    tmp_path: Path,
) -> None:
    portable_config = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))

    config: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / "plugin_cache" / "plugins"),
        "providers": _provider_configs_with_echo_provider(
            portable_config,
            ("openrouter_codex_tools",),
        ),
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "feature_system_message.system_message_feature.SystemMessageFeature",
        ],
        "agents": {"codex-openrouter": dict(portable_config["agents"]["codex-openrouter"])},
    }

    config_path = tmp_path / "config_portable_codex_system_message_echo.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(DEFAULT_CONFIG_DIR)},
    )

    assert app.get_config_errors() == []

    cases = [
        (
            {"model": "openai/gpt-5.1"},
            "You are GPT-5.1 running in the Codex CLI, a terminal-based coding assistant.",
        ),
        (
            {"model": "openai/gpt-5.3-codex", "codex_personality": "friendly"},
            "You optimize for team morale and being a supportive teammate as much as code quality.",
        ),
        (
            {"model": "openai/gpt-5.3-codex", "codex_personality": "pragmatic"},
            "You are a deeply pragmatic, effective software engineer.",
        ),
    ]

    compiled_texts: list[str] = []
    for overrides, expected_substring in cases:
        core, base_config, session = app.create_session("codex-openrouter")
        session = core.add_message(
            session,
            "user",
            "Inspect the compiled Codex system message.",
            metadata=None,
            config=base_config,
        )

        events = list(
            app.send_request(
                core,
                session,
                base_config,
                overrides=overrides,
                stream=False,
            )
        )
        system_text = _compiled_system_text(events)
        compiled_texts.append(system_text)

        assert expected_substring in system_text
        assert "{{" not in system_text

    assert compiled_texts[1] != compiled_texts[2]


def test_portable_default_gpt5_agents_select_apply_patch_shell_instructions(
    tmp_path: Path,
) -> None:
    portable_config = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))

    config: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / "plugin_cache" / "plugins"),
        "providers": _provider_configs_with_echo_provider(
            portable_config,
            ("openrouter_codex_tools", "openai"),
        ),
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "feature_system_message.system_message_feature.SystemMessageFeature",
        ],
        "agents": {
            "gpt-5-openrouter": dict(portable_config["agents"]["gpt-5-openrouter"]),
            "gpt-5-openai": dict(portable_config["agents"]["gpt-5-openai"]),
        },
    }

    config_path = tmp_path / "config_portable_codex_gpt5_message_echo.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(DEFAULT_CONFIG_DIR)},
    )

    assert app.get_config_errors() == []

    cases = [
        ("gpt-5-openrouter", "openai/gpt-5"),
        ("gpt-5-openrouter", "gpt-5"),
        ("gpt-5-openrouter", "openai/gpt-5-mini"),
        ("gpt-5-openrouter", "gpt-5-mini"),
        ("gpt-5-openai", "gpt-5"),
        ("gpt-5-openai", "openai/gpt-5"),
        ("gpt-5-openai", "gpt-5-mini"),
        ("gpt-5-openai", "openai/gpt-5-mini"),
    ]

    expected_marker = (
        'Use the `apply_patch` tool to edit files '
        '(NEVER try `applypatch` or `apply-patch`, only `apply_patch`): '
        '{"command":["apply_patch","*** Begin Patch'
    )
    gpt54_marker = "Always use apply_patch for manual code edits."

    for agent_id, model_override in cases:
        core, base_config, session = app.create_session(agent_id)
        session = core.add_message(
            session,
            "user",
            "Inspect the compiled Codex system message.",
            metadata=None,
            config=base_config,
        )

        events = list(
            app.send_request(
                core,
                session,
                base_config,
                overrides={"model": model_override},
                stream=False,
            )
        )
        system_text = _compiled_system_text(events)

        assert expected_marker in system_text, (agent_id, model_override, system_text)
        assert gpt54_marker not in system_text, (agent_id, model_override, system_text)
        assert "{{" not in system_text


def test_portable_default_runtime_helpers_contribute_ui_schema(tmp_path: Path) -> None:
    portable_config = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))

    config: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / "plugin_cache" / "plugins"),
        "providers": _provider_configs_with_echo_provider(
            portable_config,
            ("openrouter_codex_tools",),
        ),
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "feature_system_message.system_message_feature.SystemMessageFeature",
        ],
        "agents": {"codex-openrouter": dict(portable_config["agents"]["codex-openrouter"])},
    }

    config_path = tmp_path / "config_portable_codex_ui_echo.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(DEFAULT_CONFIG_DIR)},
    )

    core, base_config, _session = app.create_session("codex-openrouter")
    schema = core.get_ui_schema(base_config)

    codex_personality = next(
        item for item in schema if isinstance(item, dict) and item.get("key") == "codex_personality"
    )
    assert codex_personality["type"] == "select"
    assert codex_personality["label"] == "Codex Personality"
    assert codex_personality["default"] == "default"
    assert codex_personality["options"] == [
        {"value": "default", "label": "default"},
        {"value": "friendly", "label": "friendly"},
        {"value": "pragmatic", "label": "pragmatic"},
    ]

    include_tasks = next(
        item for item in schema if isinstance(item, dict) and item.get("key") == "include_tasks"
    )
    assert include_tasks["type"] == "checkbox"
    assert include_tasks["label"] == "Include TASKS Guidance"
    assert include_tasks["default"] is False


def test_portable_default_tasks_toggle_includes_tasks_section_when_enabled(
    tmp_path: Path,
) -> None:
    portable_config = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    provider_ids = tuple(portable_config["providers"].keys())

    config: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / "plugin_cache" / "plugins"),
        "providers": _provider_configs_with_echo_provider(portable_config, provider_ids),
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "feature_system_message.system_message_feature.SystemMessageFeature",
        ],
        "agents": dict(portable_config["agents"]),
    }

    config_path = tmp_path / "config_portable_tasks_toggle_echo.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(DEFAULT_CONFIG_DIR)},
    )

    for agent_id in ("codex-openrouter", "codex-openai", "qwen", "gemini", "grok", "kimi", "claude"):
        core, base_config, session = app.create_session(agent_id)
        session = core.add_message(
            session,
            "user",
            f"Inspect the compiled system message for {agent_id} with tasks enabled.",
            metadata=None,
            config=base_config,
        )

        events = list(
            app.send_request(
                core,
                session,
                base_config,
                overrides={"include_tasks": True},
                stream=False,
            )
        )
        system_text = _compiled_system_text(events)

        assert "Task Files and Subtasks (`tasks/`)" in system_text
