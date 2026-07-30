from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import threading
from typing import Any, Dict, List

import pytest
import requests

from agent_app.application_future import AgentApplication, SessionConflictError
from agent_app.events import InMemoryEventStore
from agent_core.tool_result_payloads import (
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    make_provider_native_tool_result,
)
from plugins.controllable_openai_test_provider import (
    release_controllable_openai_test_provider_call,
    reset_controllable_openai_test_provider_state,
    wait_for_controllable_openai_test_provider_call,
)


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "controlled": {
                "provider": "controllable_openai_test_provider",
                "model": "test-model",
                "response_text": (
                    "<state_snapshot><overall_goal>Keep going</overall_goal></state_snapshot>"
                ),
                "block_until_released": True,
                "block_wait_timeout": 5.0,
            },
        },
        "plugins": [
            "plugins.controllable_openai_test_provider.ControllableOpenAITestProvider",
            "gemini_compaction_app.GeminiCompactionAppPlugin",
        ],
        "agents": {
            "default": {
                "provider": "controlled",
                "compaction": {
                    "enabled": True,
                    "type": "gemini",
                    "verification_pass": False,
                },
            },
        },
    }

    path = tmp_path / "config_gemini_compaction_app.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def test_compact_range_conflicts_when_session_changes_mid_action(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path)

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    for role, content in [
        ("user", "u0"),
        ("assistant", "a0"),
        ("user", "u1"),
        ("assistant", "a1"),
    ]:
        session = core.add_message(session, role, content, None, base_config)

    app.save_session(session)

    outcome: Dict[str, Any] = {}

    def _run_action() -> None:
        try:
            outcome["result"] = app.execute_application_action(
                "gemini_compaction",
                "compact_range",
                {"session_id": session_id},
            )
        except Exception as exc:  # pragma: no cover - asserted below
            outcome["exception"] = exc

    thread = threading.Thread(target=_run_action)
    thread.start()

    try:
        assert wait_for_controllable_openai_test_provider_call(2.0)
        ctx = app.load_session(session_id)
        assert ctx is not None
        core_live, base_live, live_session = ctx
        advanced = core_live.add_message(
            live_session,
            "user",
            "concurrent edit",
            None,
            base_live,
        )
        app.save_session(advanced)
    finally:
        release_controllable_openai_test_provider_call()

    thread.join(timeout=2.0)
    assert not thread.is_alive()

    exc = outcome.get("exception")
    assert isinstance(exc, SessionConflictError)
    assert "Concurrent session modification detected while compacting messages" in str(exc)

    stored = app.load_session_record(session_id)
    assert stored is not None
    assert [msg.content for msg in stored.messages] == [
        "u0",
        "a0",
        "u1",
        "a1",
        "concurrent edit",
    ]

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
def test_compact_range_with_asset_ref_requires_context_ollama(tmp_path: Path) -> None:
    """Regression test: gemini_compaction_app must pass context to send_request_stream
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
            "gemini_compaction_app.GeminiCompactionAppPlugin",
        ],
        "agents": {
            "default": {
                "provider": "ollama",
                "compaction": {
                    "enabled": True,
                    "type": "gemini",
                    "verification_pass": False,
                },
            },
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
        "gemini_compaction",
        "compact_range",
        {"session_id": session_id, "start": 0, "end": 2},
    )

    # Without the fix, this is an error envelope.
    # With the fix, it succeeds and returns a mutation.
    if result.get("status") == "error":
        error_msg = result.get("message", "")
        assert "session asset attachment requires session_asset_store in context" in error_msg
        pytest.fail(
            f"Regression detected: gemini_compaction_app did not forward context to "
            f"send_request_stream. Error: {error_msg}"
        )

    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]
