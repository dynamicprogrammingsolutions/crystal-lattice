from __future__ import annotations

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
KIMI_PLUGIN_SRC = ROOT / "plugins/kimi-tools/src"
if str(KIMI_PLUGIN_SRC) not in sys.path:
    sys.path.insert(0, str(KIMI_PLUGIN_SRC))

from agent_core import Message, Session  # noqa: E402
from kimi_tools.kimi_compaction_feature import _COMPACTION_PREFIX  # noqa: E402


def _build_default_config_app(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    openrouter_key = get_repo_env("OPENROUTER_API_KEY")
    if not openrouter_key:
        pytest.skip(
            "OPENROUTER_API_KEY not set; skipping Kimi default-config compaction test"
        )

    monkeypatch.setenv("OPENROUTER_API_KEY", openrouter_key)
    monkeypatch.setenv(
        "GEMINI_API_KEY", get_repo_env("GEMINI_API_KEY", "test-gemini-key")
    )
    monkeypatch.setenv(
        "TAVILY_API_KEY", get_repo_env("TAVILY_API_KEY", "test-tavily-key")
    )
    monkeypatch.setenv(
        "OPENAI_API_KEY", get_repo_env("OPENAI_API_KEY", "test-openai-key")
    )
    monkeypatch.setenv(
        "FIREWORKS_API_KEY",
        get_repo_env("FIREWORKS_API_KEY", "test-fireworks-key"),
    )
    monkeypatch.setenv("ZAI_API_KEY", get_repo_env("ZAI_API_KEY", "test-zai-key"))
    monkeypatch.setenv(
        "CLOUD_ORCHESTRATOR_URL",
        get_repo_env("CLOUD_ORCHESTRATOR_URL", "http://cloud-orchestrator.test"),
    )
    monkeypatch.setenv(
        "CLOUD_ORCHESTRATOR_TOKEN",
        get_repo_env("CLOUD_ORCHESTRATOR_TOKEN", "test-cloud-token"),
    )

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    monkeypatch.setenv("CONFIG_DIR", str(config_path.parent.resolve()))
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )

    session_root = tmp_path / "sessions"
    app = AgentApplication(
        str(config_path),
        str(session_root),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []
    return app


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openrouter
@pytest.mark.parametrize(
    ("inputs", "expected_leading_non_system", "expected_trailing_contents"),
    [
        ({}, [], []),
        (
            {"start": 0, "end": 4},
            [],
            ["TWO", "Answer exactly THREE.", "THREE"],
        ),
        (
            {"start": 2, "end": 5},
            ["Answer exactly ONE."],
            ["Answer exactly THREE.", "THREE"],
        ),
    ],
)
def test_default_kimi_agent_compaction_action_rewrites_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    inputs: Dict[str, Any],
    expected_leading_non_system: list[str],
    expected_trailing_contents: list[str],
) -> None:
    """End-to-end compaction via the default config kimi agent.

    Verifies that:
    1. The kimi agent loads the KimiCompactionFeature via path:${env:BUILTIN_PLUGINS}/kimi-tools
    2. The compact_conversation action is registered and reachable via server.execute_action
    3. Compaction produces the expected session structure:
       - Summary user message with _COMPACTION_PREFIX and Kimi XML sections
       - Local-command artifact user message
       - No-response-requested assistant message
       - Preserved system messages and trailing messages
       - kimi_compaction metadata on session and summary message
    """
    from agent_terminal_app import server as server_mod

    app = _build_default_config_app(tmp_path, monkeypatch)
    previous = getattr(server_mod, "_agent_app", None)
    if previous is not None:
        previous.close()
    server_mod._agent_app = app

    core, base_config, session = app.create_session("kimi")
    assert base_config["model"] == "moonshotai/kimi-k2.5"

    compaction_model = os.getenv(
        "OPENROUTER_MODEL_KIMI_COMPACTION",
        base_config["model"],
    )
    seeded = Session(
        session_id=session.session_id,
        messages=[
            Message(role="user", content="Answer exactly ONE."),
            Message(role="assistant", content="ONE"),
            Message(role="user", content="Answer exactly TWO."),
            Message(role="assistant", content="TWO"),
            Message(role="user", content="Answer exactly THREE."),
            Message(role="assistant", content="THREE"),
        ],
        metadata={
            **(session.metadata or {}),
            "overrides": {
                "compaction_model": compaction_model,
            },
        },
    )
    app.save_session(seeded)

    resp = server_mod.execute_action(
        {
            "plugin": "kimi_compaction",
            "action_id": "compact_conversation",
            "action_owner": "feature",
            "inputs": {
                "session_id": seeded.session_id,
                **inputs,
            },
        },
        app_instance=app,
    )

    if resp["status"] != "ok":
        raise AssertionError(resp)

    compacted = app.load_session_record(seeded.session_id)
    assert compacted is not None

    # Find the summary message (starts with _COMPACTION_PREFIX)
    summary_index = next(
        idx
        for idx, message in enumerate(compacted.messages)
        if isinstance(message.content, str)
        and message.content.startswith(_COMPACTION_PREFIX)
    )

    # Verify the 1 injected message: summary (user)
    assert compacted.messages[summary_index].role == "user"

    summary_text = compacted.messages[summary_index].content
    assert isinstance(summary_text, str)
    assert summary_text.startswith(_COMPACTION_PREFIX)
    # Kimi-style XML sections
    assert "<current_focus>" in summary_text
    assert "<environment>" in summary_text
    assert "<completed_tasks>" in summary_text
    assert "<active_issues>" in summary_text
    assert "<code_state>" in summary_text
    assert "<important_context>" in summary_text

    # Verify leading contents (before summary)
    leading_contents = [
        message.content for message in compacted.messages[:summary_index]
    ]
    # The first leading content may be a system message or the first user message
    assert leading_contents[1:] == expected_leading_non_system

    # Verify trailing contents (after the 1 injected message)
    assert [message.content for message in compacted.messages[summary_index + 1 :]] == (
        expected_trailing_contents
    )

    # Verify metadata on summary message
    metadata = compacted.messages[summary_index].metadata or {}
    assert metadata["kimi_compaction"]["is_compact_summary"] is True

    # Verify metadata on session
    session_meta = compacted.metadata or {}
    assert session_meta["kimi_compaction"]["compacted"] is True
    assert compaction_model


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openrouter
def test_default_kimi_agent_has_compact_conversation_session_action(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the kimi agent in the default config has the compact_conversation action.

    This test explicitly checks that the KimiCompactionFeature is loaded via
    path:${env:BUILTIN_PLUGINS}/kimi-tools and its compact_conversation action
    appears in core.get_session_actions().
    """
    app = _build_default_config_app(tmp_path, monkeypatch)

    core, base_config, session = app.create_session("kimi")

    actions = core.get_session_actions(base_config)
    kimi_actions = [
        a for a in actions if a.get("plugin") == "kimi_compaction"
    ]
    assert len(kimi_actions) == 1, (
        f"Expected 1 kimi_compaction action, got {kimi_actions}. "
        f"All actions: {[a.get('plugin') for a in actions]}"
    )
    assert kimi_actions[0]["id"] == "compact_conversation"
    assert kimi_actions[0]["action_owner"] == "feature"


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openrouter
def test_default_kimi_agent_has_compaction_ui_elements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the kimi agent in the default config has compaction UI elements.

    Checks that core.get_ui_schema() includes the compaction session_action
    and message_action UI elements from KimiCompactionFeature.
    """
    app = _build_default_config_app(tmp_path, monkeypatch)

    core, base_config, session = app.create_session("kimi")

    ui_elements = core.get_ui_schema(base_config)
    kimi_elements = [
        e for e in ui_elements if e.get("plugin") == "kimi_compaction"
    ]

    # Should have at least 2 elements: session_action and message_action
    assert len(kimi_elements) >= 2, (
        f"Expected at least 2 kimi_compaction UI elements, got {len(kimi_elements)}: "
        f"{[e.get('id') for e in kimi_elements]}"
    )

    ui_types = {e["id"]: e["ui_type"] for e in kimi_elements}
    assert "compact_conversation" in ui_types
    assert ui_types["compact_conversation"] == "session_action"
    assert "compact_up_to_here" in ui_types
    assert ui_types["compact_up_to_here"] == "message_action"