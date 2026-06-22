from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest
import requests

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core.tool_result_payloads import (
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    make_provider_native_tool_result,
)

from plugins.controllable_openai_test_provider import (
    reset_controllable_openai_test_provider_state,
)


def _make_config(
    tmp_path: Path,
    *,
    provider_config: Dict[str, Any] | None = None,
    application_config: Dict[str, Any] | None = None,
) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "controlled": {
                "provider": "controllable_openai_test_provider",
                "model": "test-model",
                **dict(provider_config or {}),
            },
        },
        "plugins": [
            "plugins.controllable_openai_test_provider.ControllableOpenAITestProvider",
            "generate_title_app.GenerateTitleAppPlugin",
        ],
        "agents": {
            "default": {"provider": "controlled"},
        },
        "application": {
            "generate_title_agent_id": "default",
            "generate_title_prompt_template": "Generate a concise title.",
            "generate_title_max_messages": 10,
            **dict(application_config or {}),
        },
    }

    path = tmp_path / "config_generate_title_app.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(
    tmp_path: Path,
    *,
    provider_config: Dict[str, Any] | None = None,
    application_config: Dict[str, Any] | None = None,
) -> AgentApplication:
    config_path = _make_config(
        tmp_path,
        provider_config=provider_config,
        application_config=application_config,
    )
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(config_path), str(session_root), event_store=events)


def _create_session_with_messages(app: AgentApplication, contents: List[str]) -> str:
    core, base_config, session = app.create_session("default")

    for text in contents:
        session = core.add_message(session, "user", text, metadata=None, config=base_config)

    app.save_session(session)
    return session.session_id


def test_generate_title_action_updates_session_metadata(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path)
    session_id = _create_session_with_messages(app, ["hello", "world"])

    result = app.execute_application_action(
        "generate_title",
        "generate_title_for_session",
        {"session_id": session_id},
    )

    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]

    updated = app.load_session_record(session_id)
    assert updated is not None
    md = updated.metadata if isinstance(updated.metadata, dict) else {}
    assert md.get("title") == "Generated title"


def test_application_ui_schema_includes_generate_title_actions(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path)
    elements = app.get_application_ui_schema()

    list_actions = [
        el
        for el in elements
        if isinstance(el, dict)
        and el.get("plugin") == "generate_title"
        and el.get("ui_type") == "session_list_action"
    ]
    assert list_actions
    assert any(el.get("action_id") == "generate_title_for_session" for el in list_actions)

    view_actions = [
        el
        for el in elements
        if isinstance(el, dict)
        and el.get("plugin") == "generate_title"
        and el.get("ui_type") == "session_action"
    ]
    assert view_actions
    assert any(el.get("action_id") == "generate_title_for_session" for el in view_actions)


def test_generate_title_error_does_not_modify_session(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path, provider_config={"response_mode": "none"})
    session_id = _create_session_with_messages(app, ["one", "two"])

    result = app.execute_application_action(
        "generate_title",
        "generate_title_for_session",
        {"session_id": session_id},
    )

    assert result.get("status") == "error"
    assert result.get("error_type") == "plugin_error"

    updated = app.load_session_record(session_id)
    assert updated is not None
    md = updated.metadata if isinstance(updated.metadata, dict) else {}
    assert "title" not in md


def test_generate_title_sets_description_metadata_when_enabled(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_text": "Server Title\nServer description"},
    )
    session_id = _create_session_with_messages(app, ["hello", "world"])

    result = app.execute_application_action(
        "generate_title",
        "generate_title_for_session",
        {"session_id": session_id},
    )

    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]

    updated = app.load_session_record(session_id)
    assert updated is not None
    md = updated.metadata if isinstance(updated.metadata, dict) else {}
    assert md.get("title") == "Server Title"
    assert md.get("subtitle") == "Server description"

# ---------------------------------------------------------------------------
# Ollama-backed regression test for session_asset_store context forwarding
# ---------------------------------------------------------------------------


def _ollama_available(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/models", timeout=2)
        return bool(r.ok)
    except Exception:
        return False


def _ollama_cfg() -> dict:
    return {
        "base_url": os.environ.get("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1"),
        "model": os.environ.get("OLLAMA_OPENAI_MODEL", "qwen3:0.6b"),
        "timeout": float(os.environ.get("OLLAMA_OPENAI_TIMEOUT", "60")),
    }


@pytest.mark.integration
@pytest.mark.ollama
def test_generate_title_with_asset_ref_requires_context_ollama(tmp_path: Path) -> None:
    """Regression test: generate_title must pass context to send_request_stream
    so that providers can resolve session asset references in tool messages."""
    cfg = _ollama_cfg()
    if not _ollama_available(cfg["base_url"]):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    full_cfg: Dict[str, Any] = {
        "providers": {
            "ollama": {
                "provider": "reference_openai_compatible",
                "model": cfg["model"],
                "base_url": cfg["base_url"],
                "timeout": cfg["timeout"],
            },
        },
        "plugins": [
            "reference_openai_compatible_provider.provider.OpenAICompatibleProvider",
            "generate_title_app.GenerateTitleAppPlugin",
        ],
        "agents": {
            "default": {"provider": "ollama"},
        },
        "application": {
            "generate_title_agent_id": "default",
            "generate_title_prompt_template": "Generate a concise title.",
            "generate_title_max_messages": 10,
        },
    }
    config_path = tmp_path / "config_ollama.json"
    config_path.write_text(json.dumps(full_cfg), encoding="utf-8")

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    asset_store = app.get_session_asset_store()

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    # Store a fake image asset
    record = asset_store.store_base64(
        session_id=session_id,
        attachment_type="image",
        filename="test.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"fake-image").decode("ascii"),
    )
    asset_id = record.asset_id

    # Add a user message
    session = core.add_message(session, "user", "Hello", metadata=None, config=base_config)

    # Add a tool message with an asset_ref in the tool result
    tool_result = make_provider_native_tool_result(
        format=FORMAT_OPENAI_CHAT_COMPLETIONS,
        content=[
            {"type": "text", "text": "Tool result with image"},
            {
                "type": "image_url",
                "image_url": {
                    "asset_ref": {
                        "kind": "session_asset",
                        "session_id": session_id,
                        "asset_id": asset_id,
                        "attachment_type": "image",
                    }
                },
            },
        ],
    )
    session = core.add_message(
        session,
        "tool",
        "",
        metadata={"tool_call_id": "tc1"},
        config=base_config,
        tool_result=tool_result,
    )

    app.save_session(session)

    result = app.execute_application_action(
        "generate_title",
        "generate_title_for_session",
        {"session_id": session_id},
    )

    # Without the fix, this is an error envelope.
    # With the fix, it succeeds and returns a mutation.
    if result.get("status") == "error":
        error_msg = result.get("message", "")
        assert "session asset attachment requires session_asset_store in context" in error_msg
        pytest.fail(
            f"Regression detected: generate_title did not forward context to "
            f"send_request_stream. Error: {error_msg}"
        )

    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]
