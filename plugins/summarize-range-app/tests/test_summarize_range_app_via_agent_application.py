from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict

import pytest
import requests

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core.tool_result_payloads import (
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    make_provider_native_tool_result,
)


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "controlled": {
                "provider": "controllable_openai_test_provider",
                "model": "test-model",
                "response_text": "Range summary",
            },
        },
        "plugins": [
            "plugins.controllable_openai_test_provider.ControllableOpenAITestProvider",
            "summarize_range_app.SummarizeRangeAppPlugin",
        ],
        "agents": {
            "default": {"provider": "controlled"},
        },
        "application": {
            "summarize_range_agent_id": "default",
            "summarize_range_prompt": "Summarize this range succinctly.",
        },
    }

    path = tmp_path / "config_summarize_range_app.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def test_summarize_range_modifies_session_messages(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    for text in ["m0", "m1", "m2", "m3"]:
        session = core.add_message(session, "user", text, metadata=None, config=base_config)

    app.save_session(session)

    result = app.execute_application_action(
        "summarize_range",
        "summarize_range",
        {"session_id": session_id, "start": 1, "end": 3},
    )

    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]

    updated = app.load_session_record(session_id)
    assert updated is not None
    assert len(updated.messages) == 3
    assert updated.messages[0].role == "user"
    assert updated.messages[0].content == "m0"
    assert updated.messages[2].role == "user"
    assert updated.messages[2].content == "m3"
    assert updated.messages[1].role == "assistant"
    assert updated.messages[1].content == "Range summary"


def test_message_action_style_request_includes_selected_message(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    for text in ["m0", "m1", "m2", "m3"]:
        session = core.add_message(session, "user", text, metadata=None, config=base_config)

    app.save_session(session)

    result = app.execute_application_action(
        "summarize_range",
        "summarize_range",
        {
            "session_id": session_id,
            "start": 0,
            "end": 2,
            "end_inclusive": True,
        },
    )

    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]

    updated = app.load_session_record(session_id)
    assert updated is not None
    assert [message.content for message in updated.messages] == [
        "Range summary",
        "m3",
    ]
    assert updated.messages[0].role == "assistant"


def test_summarize_range_validation_error_bubbles(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    for text in ["one", "two"]:
        session = core.add_message(session, "user", text, metadata=None, config=base_config)

    app.save_session(session)

    with pytest.raises(Exception):
        app.execute_application_action(
            "summarize_range",
            "summarize_range",
            {"session_id": session_id, "start": 5, "end": 1},
        )


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


def _make_ollama_config(tmp_path: Path) -> Path:
    cfg = _ollama_cfg()
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
            "summarize_range_app.SummarizeRangeAppPlugin",
        ],
        "agents": {
            "default": {"provider": "ollama"},
        },
        "application": {
            "summarize_range_agent_id": "default",
            "summarize_range_prompt": "Summarize this range in one short sentence.",
        },
    }
    path = tmp_path / "config_ollama.json"
    path.write_text(json.dumps(full_cfg), encoding="utf-8")
    return path


def _build_ollama_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_ollama_config(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


@pytest.mark.integration
@pytest.mark.ollama
def test_summarize_range_with_asset_ref_requires_context_ollama(tmp_path: Path) -> None:
    """Regression test: summarize_range must pass context to send_request_stream
    so that providers can resolve session asset references in tool messages.

    Without the fix, the provider raises:
        "session asset attachment requires session_asset_store in context"
    because _expanded_request_messages cannot resolve the asset_ref without
    the context carrying session_asset_store.
    """
    cfg = _ollama_cfg()
    if not _ollama_available(cfg["base_url"]):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    app = _build_ollama_app(tmp_path)
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
        "summarize_range",
        "summarize_range",
        {"session_id": session_id, "start": 0, "end": 2},
    )

    # Without the fix, this is an error envelope.
    # With the fix, it succeeds and returns a mutation.
    if result.get("status") == "error":
        error_msg = result.get("message", "")
        assert "session asset attachment requires session_asset_store in context" in error_msg
        pytest.fail(
            f"Regression detected: summarize_range did not forward context to "
            f"send_request_stream. Error: {error_msg}"
        )

    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]
