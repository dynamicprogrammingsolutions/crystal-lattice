from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

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


SKILL_NAME = "manual-activation-probe"
SKILL_DESCRIPTION = "Runs one shell command and then replies with the activation sentinel."
SKILL_SENTINEL = "MANUAL_SKILL_SENTINEL_8731"
TOOL_SENTINEL = "MANUAL_SKILL_TOOL_SENTINEL_2145"


@pytest.fixture(scope="module")
def ensure_openrouter_api_key() -> str:
    api_key = get_repo_env("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip(
            "OPENROUTER_API_KEY not set; skipping Codex skill activation integration test"
        )
    return api_key


def _plugin_entry(repo_name: str, entry: str) -> Dict[str, str]:
    return {"path": str(ROOT / "plugins" / repo_name), "entry": entry}


def _openai_provider_options() -> Dict[str, Any]:
    provider_id = os.getenv("OPENAI_PROVIDER")
    if not provider_id:
        return {}
    return {
        "provider": {
            "order": [provider_id],
            "allow_fallbacks": False,
        }
    }


def _write_skill_fixture(workspace: Path) -> None:
    skill_dir = workspace / ".agents" / "skills" / SKILL_NAME
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        (
            "---\n"
            f"name: {SKILL_NAME}\n"
            f"description: {SKILL_DESCRIPTION}\n"
            "---\n\n"
            "# Manual Activation Probe\n\n"
            f"Activation sentinel: `{SKILL_SENTINEL}`\n\n"
            "When this skill is activated, first use the shell tool exactly once to run:\n"
            f"`printf '{TOOL_SENTINEL}\\n'`\n\n"
            "After that tool call succeeds, reply with exactly:\n"
            f"`{SKILL_SENTINEL}`\n"
        ),
        encoding="utf-8",
    )


def _make_config(tmp_path: Path, workspace: Path, api_key: str) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "model": os.getenv("OPENROUTER_CODEX_SKILL_TEST_MODEL")
                or "openai/gpt-5.4-nano",
                "api_key": api_key,
                "base_url": os.getenv("OPENROUTER_BASE_URL")
                or "https://openrouter.ai/api/v1",
                "timeout": 240,
                "working_directory": str(workspace),
                "allowed_paths": [str(workspace)],
                "request_options": {**_openai_provider_options(), "seed": 42},
            }
        },
        "plugins": [
            _plugin_entry(
                "openrouter",
                "openrouter_plugins.openrouter_provider.OpenRouterProvider",
            ),
            _plugin_entry(
                "openrouter",
                "openrouter_plugins.openrouter_tools_extension.OpenRouterToolsExtension",
            ),
            "plugins.request_options_feature.RequestOptionsFeature",
            _plugin_entry(
                "feature-system-message",
                "feature_system_message.system_message_feature.SystemMessageFeature",
            ),
            _plugin_entry(
                "codex-tools",
                "codex_tools.codex_skills_feature.CodexSkillsFeature",
            ),
            _plugin_entry(
                "codex-tools",
                "codex_tools.shell_tool.ShellArrayTool",
            ),
        ],
        "agents": {
            "default": {
                "provider": "openrouter",
                "skills_enabled": True,
                "skills_roots": [".agents/skills"],
                "shell_tool_mode": "shell",
                "system_message_enabled": True,
                "system_message": {
                    "template": "You are Codex.\n\n{{CODEX_SKILLS_SECTION}}",
                    "variables": {
                        "CODEX_SKILLS_SECTION": {"text": ""},
                    },
                },
            }
        },
    }

    config_path = tmp_path / "config_codex_skill_activation.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")
    return config_path


def _run_request(
    app: AgentApplication,
    core: Any,
    session: Session,
    base_config: Dict[str, Any],
) -> Session:
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints = [event for event in events if event.get("type") == "session_checkpoint"]
    assert checkpoints, "expected at least one session checkpoint"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)
    return final_session


def _native_message_text(message: Dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        text = part.get("text")
        if isinstance(text, str):
            parts.append(text)
    return "\n".join(parts)


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openrouter
def test_codex_manual_skill_activation_injects_skill_into_real_request(
    tmp_path: Path,
    ensure_openrouter_api_key: str,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_skill_fixture(workspace)

    config_path = _make_config(tmp_path, workspace, ensure_openrouter_api_key)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []

    core, base_config, session = app.create_session("default")
    session = core.add_message(
        session,
        "user",
        (
            f"What is the activation sentinel from ${SKILL_NAME}? "
            "Reply with exactly the sentinel and nothing else."
        ),
        config=base_config,
    )
    session = app.save_session(session)

    final_session = _run_request(app, core, session, base_config)

    assistant_messages = [
        message for message in final_session.messages if message.role == "assistant"
    ]
    assert assistant_messages, "expected assistant response"
    assert assistant_messages[-1].content.strip() == SKILL_SENTINEL

    native_history = (final_session.metadata or {}).get("native_messages") or []
    assert isinstance(native_history, list)
    injected_skill_messages = [
        message
        for message in native_history
        if isinstance(message, dict)
        and message.get("role") == "user"
        and "<skill>" in _native_message_text(message)
    ]
    assert injected_skill_messages, "expected an injected skill user message"
    assert len(injected_skill_messages) == 1, injected_skill_messages

    skill_payload = _native_message_text(injected_skill_messages[-1])
    assert f"name: {SKILL_NAME}" in skill_payload
    assert f"description: {SKILL_DESCRIPTION}" in skill_payload
    assert SKILL_SENTINEL in skill_payload
    assert TOOL_SENTINEL in skill_payload