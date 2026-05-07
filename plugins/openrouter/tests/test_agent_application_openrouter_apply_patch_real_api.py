from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable

import pytest
from dotenv import load_dotenv

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Session
from agent_core.tool_interop import DEFAULT_TOOL_INTEROP_REGISTRY


REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def ensure_openrouter_api_key() -> str:
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter apply_patch integration tests")
    return api_key


def _plugin_entry(repo_name: str, entry: str) -> Dict[str, str]:
    return {"path": str(REPO_ROOT / "plugins" / repo_name), "entry": entry}


def _run_request(
    app: AgentApplication,
    core: Any,
    session: Session,
    base_config: Dict[str, Any],
) -> Session:
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints, "expected at least one session checkpoint"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)
    return final_session


def _iter_tool_calls(session: Session) -> Iterable[Dict[str, Any]]:
    for message in session.messages:
        metadata = message.metadata if isinstance(message.metadata, dict) else {}
        tool_calls = metadata.get("tool_calls") or []
        if not isinstance(tool_calls, list):
            continue
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                yield tool_call


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


def _make_shell_config(tmp_path: Path, api_key: str) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "model": os.getenv("OPENROUTER_APPLY_PATCH_SHELL_MODEL") or "openai/gpt-5-mini",
                "api_key": api_key,
                "base_url": os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
                "timeout": 240,
                "working_directory": str(tmp_path),
                "allowed_paths": [str(tmp_path)],
                "intercept_apply_patch": True,
                "shell_tool_mode": "shell",
                "request_options": {**_openai_provider_options(), "seed": 42},
            }
        },
        "plugins": [
            _plugin_entry("openrouter", "openrouter_plugins.openrouter_provider.OpenRouterProvider"),
            _plugin_entry(
                "openrouter",
                "openrouter_plugins.openrouter_tools_extension.OpenRouterToolsExtension",
            ),
            "plugins.request_options_feature.RequestOptionsFeature",
            _plugin_entry("codex-tools", "codex_tools.shell_tool.ShellArrayTool"),
            _plugin_entry("codex-tools", "codex_tools.apply_patch_tool.ApplyPatchTool"),
        ],
        "agents": {
            "default": {
                "provider": "openrouter",
                "disabled_plugins": ["apply_patch"],
            }
        },
    }

    path = tmp_path / "config_openrouter_apply_patch_shell.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _make_apply_patch_config(tmp_path: Path, api_key: str) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "model": os.getenv("OPENROUTER_APPLY_PATCH_TOOL_MODEL") or "openai/gpt-5.4-mini",
                "api_key": api_key,
                "base_url": os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
                "timeout": 240,
                "working_directory": str(tmp_path),
                "allowed_paths": [str(tmp_path)],
                "request_options": {**_openai_provider_options(), "seed": 42},
            }
        },
        "plugins": [
            _plugin_entry("openrouter", "openrouter_plugins.openrouter_provider.OpenRouterProvider"),
            _plugin_entry(
                "openrouter",
                "openrouter_plugins.openrouter_tools_extension.OpenRouterToolsExtension",
            ),
            "plugins.request_options_feature.RequestOptionsFeature",
            _plugin_entry("codex-tools", "codex_tools.apply_patch_tool.ApplyPatchTool"),
            _plugin_entry("codex-tools", "codex_tools.shell_tool.ShellArrayTool"),
        ],
        "agents": {
            "default": {
                "provider": "openrouter",
                "disabled_plugins": ["shell", "shell_command"],
            }
        },
    }

    path = tmp_path / "config_openrouter_apply_patch_tool.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


@pytest.mark.integration
@pytest.mark.openrouter
def test_agent_application_openrouter_gpt5_mini_shell_intercepts_apply_patch(
    tmp_path: Path,
    ensure_openrouter_api_key: str,
) -> None:
    config_path = _make_shell_config(tmp_path, ensure_openrouter_api_key)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )

    core, base_config, session = app.create_session("default")
    active_tools = core.get_plugins_for_config(base_config)["tools"]
    assert "apply_patch" not in active_tools
    assert "shell" in active_tools

    target = tmp_path / "note.txt"
    target.write_text("alpha\n", encoding="utf-8")

    session = core.add_message(
        session,
        "system",
        (
            "Use the shell tool to edit files. The dedicated apply_patch tool is unavailable. "
            "To modify files, run the internal apply_patch command through the shell tool using "
            "a bash heredoc in this exact style: apply_patch <<'PATCH' ... PATCH. "
            f"Always set workdir to {tmp_path}. Do not use Python."
        ),
        config=base_config,
    )
    session = core.add_message(
        session,
        "user",
        "Change note.txt so it contains exactly 'beta' followed by a newline.",
        config=base_config,
    )

    final_session = _run_request(app, core, session, base_config)

    updated = target.read_text(encoding="utf-8")
    assert updated.startswith("beta\n")
    assert "alpha" not in updated
    inspected_calls = [DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(call) for call in _iter_tool_calls(final_session)]
    shell_calls = [call for call in inspected_calls if call.tool_name == "shell"]
    assert shell_calls, "expected the model to call the shell tool"
    shell_payloads = [call.payload for call in shell_calls if isinstance(call.payload, dict)]
    assert any("apply_patch" in "\n".join(payload.get("command", [])) for payload in shell_payloads)


@pytest.mark.integration
@pytest.mark.openrouter
def test_agent_application_openrouter_gpt54_mini_uses_apply_patch_tool(
    tmp_path: Path,
    ensure_openrouter_api_key: str,
) -> None:
    config_path = _make_apply_patch_config(tmp_path, ensure_openrouter_api_key)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )

    core, base_config, session = app.create_session("default")
    active_tools = core.get_plugins_for_config(base_config)["tools"]
    assert "apply_patch" in active_tools
    assert "shell" not in active_tools
    assert "shell_command" not in active_tools

    target = tmp_path / "note.txt"
    target.write_text("alpha\n", encoding="utf-8")

    session = core.add_message(
        session,
        "system",
        "Use the apply_patch tool to edit files. Do not use shell commands.",
        config=base_config,
    )
    session = core.add_message(
        session,
        "user",
        "Change note.txt so it contains exactly 'beta' followed by a newline.",
        config=base_config,
    )

    final_session = _run_request(app, core, session, base_config)

    assert target.read_text(encoding="utf-8") == "beta\n"
    inspected_calls = [DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(call) for call in _iter_tool_calls(final_session)]
    assert any(call.tool_name == "apply_patch" for call in inspected_calls)