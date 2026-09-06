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


FIXTURE_PATH = ROOT / "application/python/tests/fixtures/view_image_text.png"
EXPECTED_TEXT = "CODEX VIEW IMAGE 7391"


@pytest.fixture(scope="module")
def ensure_openrouter_api_key() -> str:
    api_key = get_repo_env("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip(
            "OPENROUTER_API_KEY not set; skipping default-config OpenRouter view_image tests"
        )
    return api_key


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    api_key = get_repo_env("OPENAI_API_KEY")
    if not api_key:
        pytest.skip(
            "OPENAI_API_KEY not set; skipping default-config OpenAI view_image tests"
        )
    return api_key


def _run_request(
    app: AgentApplication,
    core: Any,
    session: Session,
    base_config: Dict[str, Any],
    *,
    overrides: Dict[str, Any],
) -> Session:
    events = list(
        app.send_request(core, session, base_config, overrides=overrides, stream=False)
    )
    checkpoints = [
        event for event in events if event.get("type") == "session_checkpoint"
    ]
    assert checkpoints, events
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


def _view_image_payloads(final_session: Session) -> list[Dict[str, Any]]:
    payloads: list[Dict[str, Any]] = []
    for call in _iter_tool_calls(final_session):
        inspected = DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(call)
        if inspected.tool_name == "view_image" and isinstance(inspected.payload, dict):
            payloads.append(inspected.payload)
    return payloads


def _view_image_tool_messages(final_session: Session) -> list[Any]:
    messages = []
    for message in final_session.messages:
        if message.role != "tool":
            continue
        metadata = message.metadata if isinstance(message.metadata, dict) else {}
        if metadata.get("tool_name") == "view_image":
            messages.append(message)
    return messages


def _assert_view_image_was_used(final_session: Session) -> None:
    payloads = _view_image_payloads(final_session)
    assert payloads, "expected a view_image tool call"
    resolved_fixture = FIXTURE_PATH.resolve()
    assert any(
        isinstance(payload.get("path"), str)
        and Path(payload["path"]).expanduser().resolve() == resolved_fixture
        for payload in payloads
    ), payloads

    tool_messages = _view_image_tool_messages(final_session)
    assert tool_messages, "expected a view_image tool result message"
    assert any(
        _message_has_structured_image_result(message) for message in tool_messages
    ), tool_messages


def _message_has_structured_image_result(message: Any) -> bool:
    metadata = message.metadata if isinstance(message.metadata, dict) else {}
    display = metadata.get("display")
    content = display.get("content") if isinstance(display, dict) else None
    if (
        isinstance(content, dict)
        and isinstance(content.get("asset_ref"), dict)
        and isinstance(content.get("preview_data_base64"), str)
    ):
        return True

    tool_result = getattr(message, "tool_result", None)
    if isinstance(tool_result, dict) and isinstance(tool_result.get("output"), list):
        return True

    return False


def _run_view_image_case(
    *,
    agent_id: str,
    model: str,
    session_root: Path,
    default_config_test_env,
    **env_overrides: str,
) -> Session:
    default_env = default_config_test_env(
        cloud_runtime_build_context=session_root / "cloud-runtime-context",
        **env_overrides,
    )
    app = AgentApplication(
        str(default_env.config_path),
        str(session_root),
        event_store=InMemoryEventStore(),
        env_overrides=default_env.env_overrides,
    )
    assert app.get_config_errors() == []

    core, base_config, session = app.create_session(agent_id)
    active_tools = core.get_plugins_for_config(base_config)["tools"]
    assert "view_image" in active_tools

    session = core.add_message(
        session,
        "user",
        (
            "Use the view_image tool to inspect this exact local image path: "
            f"{FIXTURE_PATH}. The image contains written text. After using the tool, "
            "reply with exactly the written text and nothing else."
        ),
        metadata=None,
        config=base_config,
    )
    session = app.save_session(session)

    last_failure: tuple[str, list[Dict[str, Any]], int] | None = None
    for _attempt in range(2):
        final_session = _run_request(
            app,
            core,
            session,
            base_config,
            overrides={
                "model": model,
                "working_directory": str(FIXTURE_PATH.parent),
                "allowed_paths": [str(FIXTURE_PATH.parent)],
            },
        )
        final_text = final_session.messages[-1].content.strip()
        payloads = _view_image_payloads(final_session)
        tool_messages = _view_image_tool_messages(final_session)
        if EXPECTED_TEXT in final_text and payloads and tool_messages:
            _assert_view_image_was_used(final_session)
            return final_session
        last_failure = (final_text, payloads, len(tool_messages))

    raise AssertionError((agent_id, last_failure))


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openrouter
def test_default_config_codex_openrouter_reads_text_from_image_with_view_image(
    ensure_openrouter_api_key: str,
    tmp_path: Path,
    default_config_test_env,
) -> None:
    _run_view_image_case(
        agent_id="codex-openrouter",
        model=os.getenv("OPENROUTER_CODEX_VIEW_IMAGE_TEST_MODEL")
        or "openai/gpt-5.4-mini",
        session_root=tmp_path / "sessions-openrouter",
        default_config_test_env=default_config_test_env,
        OPENROUTER_API_KEY=ensure_openrouter_api_key,
    )


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openai
def test_default_config_codex_openai_reads_text_from_image_with_view_image(
    ensure_openai_api_key: str,
    tmp_path: Path,
    default_config_test_env,
) -> None:
    _run_view_image_case(
        agent_id="codex-openai",
        model=os.getenv("OPENAI_CODEX_VIEW_IMAGE_TEST_MODEL") or "gpt-5.4-mini",
        session_root=tmp_path / "sessions-openai",
        default_config_test_env=default_config_test_env,
        OPENAI_API_KEY=ensure_openai_api_key,
    )
