from __future__ import annotations

import os
import sys
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
from agent_core.tool_interop import DEFAULT_TOOL_INTEROP_REGISTRY  # noqa: E402


CONFIG_PATH = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "config.json"
)
EXPECTED_GPT5_APPLY_PATCH_MARKER = (
    'Use the `apply_patch` shell command to edit files '
    '(NEVER try `applypatch` or `apply-patch`, only `apply_patch`): '
    '{"command":["apply_patch","*** Begin Patch'
)


@pytest.fixture(scope="module")
def ensure_openrouter_api_key() -> str:
    api_key = get_repo_env("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set; skipping default-config OpenRouter GPT-5 tests")
    return api_key


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    api_key = get_repo_env("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping default-config OpenAI GPT-5 tests")
    return api_key


def _run_request(
    app: AgentApplication,
    core: Any,
    session: Session,
    base_config: Dict[str, Any],
    *,
    overrides: Dict[str, Any],
) -> Session:
    events = list(app.send_request(core, session, base_config, overrides=overrides, stream=False))
    checkpoints = [event for event in events if event.get("type") == "session_checkpoint"]
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


def _compiled_system_text(session: Session) -> str:
    for message in session.messages:
        if message.role != "system":
            continue
        metadata = message.metadata if isinstance(message.metadata, dict) else {}
        compiled = metadata.get("compiled_content")
        if isinstance(compiled, str) and compiled:
            return compiled
        if isinstance(message.content, str) and message.content:
            return message.content
    raise AssertionError("expected a system message in the final session")


def _prepare_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "note.txt").write_text("alpha\n", encoding="utf-8")
    return workspace


def _assert_apply_patch_shell_call(final_session: Session) -> None:
    inspected_calls = [
        DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(call)
        for call in _iter_tool_calls(final_session)
    ]
    assert not any(call.tool_name == "apply_patch" for call in inspected_calls)

    shell_calls = [call for call in inspected_calls if call.tool_name == "shell"]
    assert shell_calls, "expected the model to call the shell tool"

    shell_payloads = [call.payload for call in shell_calls if isinstance(call.payload, dict)]
    assert any(
        (
            isinstance(payload.get("command"), list)
            and payload["command"][:1] == ["apply_patch"]
            and len(payload["command"]) >= 2
            and isinstance(payload["command"][1], str)
            and payload["command"][1].startswith("*** Begin Patch")
        )
        or (
            isinstance(payload.get("command"), list)
            and payload["command"][:2] == ["bash", "-lc"]
            and len(payload["command"]) >= 3
            and isinstance(payload["command"][2], str)
            and "apply_patch" in payload["command"][2]
            and "*** Begin Patch" in payload["command"][2]
        )
        for payload in shell_payloads
    ), shell_payloads


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openrouter
def test_default_config_gpt5_openrouter_agent_selects_gpt5_prompt_and_uses_apply_patch(
    ensure_openrouter_api_key: str,
    tmp_path: Path,
) -> None:
    app = AgentApplication(
        str(CONFIG_PATH),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )

    workspace = _prepare_workspace(tmp_path)
    core, base_config, session = app.create_session("gpt-5-openrouter")
    active_tools = core.get_plugins_for_config(base_config)["tools"]
    assert "apply_patch" not in active_tools
    assert "shell" in active_tools

    session = core.add_message(
        session,
        "user",
        (
            "Update note.txt so it contains exactly 'beta' followed by a newline. "
            f"Set workdir to {workspace}."
        ),
        metadata=None,
        config=base_config,
    )

    final_session = _run_request(
        app,
        core,
        session,
        base_config,
        overrides={
            "model": os.getenv("OPENROUTER_GPT5_SELECTION_TEST_MODEL") or "openai/gpt-5-mini",
            "working_directory": str(workspace),
            "allowed_paths": [str(workspace)],
        },
    )

    assert (workspace / "note.txt").read_text(encoding="utf-8") == "beta\n"
    system_text = _compiled_system_text(final_session)
    assert EXPECTED_GPT5_APPLY_PATCH_MARKER in system_text
    _assert_apply_patch_shell_call(final_session)


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openai
def test_default_config_gpt5_openai_agent_selects_gpt5_prompt_and_uses_apply_patch(
    ensure_openai_api_key: str,
    tmp_path: Path,
) -> None:
    app = AgentApplication(
        str(CONFIG_PATH),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )

    workspace = _prepare_workspace(tmp_path)
    core, base_config, session = app.create_session("gpt-5-openai")
    active_tools = core.get_plugins_for_config(base_config)["tools"]
    assert "apply_patch" not in active_tools
    assert "shell" in active_tools

    session = core.add_message(
        session,
        "user",
        (
            "Update note.txt so it contains exactly 'beta' followed by a newline. "
            f"Set workdir to {workspace}."
        ),
        metadata=None,
        config=base_config,
    )

    final_session = _run_request(
        app,
        core,
        session,
        base_config,
        overrides={
            "model": os.getenv("OPENAI_GPT5_SELECTION_TEST_MODEL") or "gpt-5-mini",
            "working_directory": str(workspace),
            "allowed_paths": [str(workspace)],
        },
    )

    assert (workspace / "note.txt").read_text(encoding="utf-8") == "beta\n"
    system_text = _compiled_system_text(final_session)
    assert EXPECTED_GPT5_APPLY_PATCH_MARKER in system_text
    _assert_apply_patch_shell_call(final_session)