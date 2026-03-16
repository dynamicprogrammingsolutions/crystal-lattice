from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Session


REPO_ROOT = Path(__file__).resolve().parents[3]
SIMPLIFIED_CONFIG_PATH = (
    REPO_ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "config_v2_multi_family_tools_simplified.json"
)
SIMPLIFIED_CONFIG_DIR = SIMPLIFIED_CONFIG_PATH.parent


def _simplified_agent_with_echo_provider(
    simplified_config: dict[str, Any],
    agent_id: str,
) -> dict[str, Any]:
    agent_config = dict(simplified_config["agents"][agent_id])
    agent_config["provider"] = "echo_with_system"
    return agent_config


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
    system_template = "You are a helpful system message for tests."
    config: Dict[str, Any] = {
        "providers": {
            "echo_with_system": {
                "provider": "echo_openai_like",
                "model": "echo-test-1",
                "timeout": 60,
                "system_message_enabled": True,
                "system_message": system_template,
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


def test_simplified_vendor_system_messages_compile_in_application_requests(
    tmp_path: Path,
    monkeypatch,
) -> None:
    simplified_config = json.loads(SIMPLIFIED_CONFIG_PATH.read_text(encoding="utf-8"))

    config: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / "plugin_cache" / "plugins"),
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
            agent_id: _simplified_agent_with_echo_provider(simplified_config, agent_id)
            for agent_id in ("gemini", "qwen", "grok")
        },
    }

    config_path = tmp_path / "config_simplified_system_message_echo.json"
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
            "CONFIG_DIR": str(SIMPLIFIED_CONFIG_DIR),
            "WORKING_DIR": str(repo_dir),
        },
    )

    assert app.get_config_errors() == []

    expected_substrings = {
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
        ],
        "grok": [
            "You are Grok CLI, an AI assistant that helps with file editing, coding tasks, and system operations.",
            "You have access to these tools:",
            f"Current working directory: {repo_dir.resolve()}",
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


def test_simplified_codex_system_message_selection_by_model_and_personality(
    tmp_path: Path,
) -> None:
    simplified_config = json.loads(SIMPLIFIED_CONFIG_PATH.read_text(encoding="utf-8"))

    config: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / "plugin_cache" / "plugins"),
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
            "codex": _simplified_agent_with_echo_provider(simplified_config, "codex")
        },
    }

    config_path = tmp_path / "config_simplified_codex_system_message_echo.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(SIMPLIFIED_CONFIG_DIR)},
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
        core, base_config, session = app.create_session("codex")
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


def test_simplified_codex_runtime_helper_contributes_ui_schema(tmp_path: Path) -> None:
    simplified_config = json.loads(SIMPLIFIED_CONFIG_PATH.read_text(encoding="utf-8"))

    config: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / "plugin_cache" / "plugins"),
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
            "codex": _simplified_agent_with_echo_provider(simplified_config, "codex")
        },
    }

    config_path = tmp_path / "config_simplified_codex_ui_echo.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(SIMPLIFIED_CONFIG_DIR)},
    )

    core, base_config, _session = app.create_session("codex")
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
