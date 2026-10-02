from __future__ import annotations

import os
import sys
from pathlib import Path

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


CONFIG_PATH = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "config.json"
)
GPT_6_DISTINCTIVE_SUBSTRING = "You are Codex, an agent based on GPT-6"
EXPECTED_REPLY_MARKER = "GPT61SOL_INSTRUCTIONS_OK"


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    api_key = get_repo_env("OPENAI_API_KEY")
    if not api_key:
        pytest.skip(
            "OPENAI_API_KEY not set; skipping default-config GPT-6.1-Sol Codex "
            "system-instruction tests"
        )
    return api_key


def _compiled_system_text(session: Session) -> str:
    """Extract the compiled system message from native_messages metadata.

    The SystemMessageFeature stamps ``compiled_content`` into the native
    system message's ``_metadata`` during ``initialize_request``. When
    ``system_message_as_instructions`` is disabled (as in the
    ``codex-openai-api`` agent), the system message persists in the
    provider-native history with the compiled content available for
    inspection.
    """

    native_messages = session.metadata.get("native_messages") or []
    for nm in native_messages:
        if not isinstance(nm, dict):
            continue
        if nm.get("role") != "system":
            continue
        metadata = nm.get("_metadata") or {}
        compiled = metadata.get("compiled_content")
        if isinstance(compiled, str) and compiled:
            return compiled
    raise AssertionError("expected a compiled system message in native_messages")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openai
def test_default_config_codex_gpt61_sol_system_instructions_real_api(
    ensure_openai_api_key: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_DIR", str(CONFIG_PATH.parent.resolve()))
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )
    monkeypatch.setenv("CLOUD_ORCHESTRATOR_URL", "http://cloud-orchestrator.test")
    monkeypatch.setenv("CLOUD_ORCHESTRATOR_TOKEN", "test-cloud-token")
    app = AgentApplication(
        str(CONFIG_PATH),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []

    model = os.getenv("OPENAI_CODEX_GPT61_TEST_MODEL") or "gpt-6.1-sol"

    # Override the agent's base config model so that the SystemMessageFeature
    # stamps the GPT-6.1-Sol compiled content during session creation. The
    # ``codex-openai-api`` agent is used because it has
    # ``system_message_as_instructions: false``, which keeps the system
    # message (with ``compiled_content``) in the provider-native history
    # for inspection.
    base_cfg = app._get_agent_base_config("codex-openai-api")
    original_model = base_cfg.get("model")
    base_cfg["model"] = model
    try:
        core, base_config, session = app.create_session("codex-openai-api")
    finally:
        base_cfg["model"] = original_model

    session = core.add_message(
        session,
        "user",
        f"Reply with exactly: {EXPECTED_REPLY_MARKER}",
        metadata=None,
        config=base_config,
    )
    session = app.save_session(session)

    events = list(
        app.send_request(
            core,
            session,
            base_config,
            overrides={"model": model},
            stream=False,
        )
    )
    checkpoints = [
        event for event in events if event.get("type") == "session_checkpoint"
    ]
    assert checkpoints, "expected at least one session checkpoint"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)

    system_text = _compiled_system_text(final_session)
    assert (
        GPT_6_DISTINCTIVE_SUBSTRING in system_text
    ), "expected GPT-6 distinctive substring in compiled system instructions"

    final_message = final_session.messages[-1]
    assert final_message.role == "assistant"
    content = final_message.content
    assert isinstance(content, str)
    assert EXPECTED_REPLY_MARKER in content
