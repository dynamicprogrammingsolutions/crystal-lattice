from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Session


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
