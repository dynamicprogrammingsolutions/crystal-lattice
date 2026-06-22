# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Ollama OpenAI-compatible integration test for Gemini compaction.

Tests the complete compaction flow using the reference OpenAI-compatible
provider with a local Ollama instance. Verifies that compaction produces
correct session structure (snapshot user message, acknowledgment assistant
message, preserved system and trailing messages) and consistent native history.

Also includes a regression test for context forwarding to send_request_stream
so that providers can resolve session asset references in tool messages.
"""

from __future__ import annotations

# ruff: noqa: E402

import base64
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest
import requests

ROOT = Path(__file__).resolve().parents[3]
for rel in (
    "core/python",
    "plugins/gemini-compaction-feature/src",
    "plugins/gemini-compaction-app/src",
    "plugins/reference-openai-compatible-provider/src",
):
    path = ROOT / rel
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core import AgentCore, Message, Session  # noqa: E402
from agent_core.tool_result_payloads import (  # noqa: E402
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    make_provider_native_tool_result,
)
from gemini_compaction_feature import (  # noqa: E402
    GeminiCompactionFeaturePlugin,
    _ACKNOWLEDGMENT_MESSAGE,
)

import importlib  # noqa: E402

_gcf = importlib.import_module("gemini_compaction_feature")

MODEL = os.getenv("OLLAMA_OPENAI_MODEL", "qwen3:0.6b")
BASE_URL = os.getenv("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1")
TIMEOUT = float(os.getenv("OLLAMA_OPENAI_TIMEOUT", "180"))


def _ollama_available(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/models", timeout=3)
        return bool(r.ok)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Core-level tests (no AgentApplication)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.parametrize(
    ("params", "expected_leading_contents", "expected_trailing_contents"),
    [
        ({}, [], []),
        ({"start": 0, "end": 3}, [], ["TWO", "Answer exactly THREE.", "THREE"]),
        (
            {"start": 1, "end": 4},
            ["Answer exactly ONE."],
            ["Answer exactly THREE.", "THREE"],
        ),
    ],
)
def test_ollama_compaction_rewrites_selected_range_into_state_snapshot(
    params: dict[str, int],
    expected_leading_contents: list[str],
    expected_trailing_contents: list[str],
) -> None:
    """End-to-end compaction with Ollama reference provider.

    Verifies that the compacted session has:
    - A snapshot user message containing <state_snapshot>
    - An acknowledgment assistant message
    - Preserved system messages (if any)
    - Preserved trailing messages
    - Consistent native history
    """
    if not _ollama_available(BASE_URL):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    try:
        from reference_openai_compatible_provider.provider import (
            OpenAICompatibleProvider,
        )
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Ollama compaction test dependencies not installed: {exc}")

    core = AgentCore()
    core.register_provider(OpenAICompatibleProvider)
    core.register_feature(GeminiCompactionFeaturePlugin)

    config: dict[str, Any] = {
        "provider": "reference_openai_compatible",
        "model": MODEL,
        "base_url": BASE_URL,
        "timeout": TIMEOUT,
        "compaction": {
            "enabled": True,
            "type": "gemini",
            "verification_pass": False,
        },
    }

    session = Session(
        session_id="gemini-compaction-ollama-test",
        messages=[
            Message(role="user", content="Answer exactly ONE."),
            Message(role="assistant", content="ONE"),
            Message(role="user", content="Answer exactly TWO."),
            Message(role="assistant", content="TWO"),
            Message(role="user", content="Answer exactly THREE."),
            Message(role="assistant", content="THREE"),
        ],
        metadata={},
    )

    compacted_session, result = core.execute_session_action(
        session,
        config,
        "gemini_compaction_feature",
        "compact_range",
        params,
    )

    assert result.get("compaction_result", {}).get("status") == "ok", (
        f"Expected ok status, got: {result}"
    )

    # Find the snapshot message
    snapshot_msgs = [
        m for m in compacted_session.messages
        if isinstance(m.content, str) and "<state_snapshot>" in m.content
    ]
    assert len(snapshot_msgs) >= 1, (
        f"Expected at least one snapshot message, got: "
        f"{[m.content[:50] for m in compacted_session.messages]}"
    )
    snapshot_index = next(
        idx
        for idx, m in enumerate(compacted_session.messages)
        if isinstance(m.content, str) and "<state_snapshot>" in m.content
    )

    # Verify acknowledgment message follows snapshot
    assert compacted_session.messages[snapshot_index + 1].content == _ACKNOWLEDGMENT_MESSAGE
    assert compacted_session.messages[snapshot_index + 1].role == "assistant"

    # Verify leading contents
    assert [
        m.content for m in compacted_session.messages[:snapshot_index]
    ] == expected_leading_contents

    # Verify trailing contents
    trailing = compacted_session.messages[snapshot_index + 2:]
    assert [m.content for m in trailing] == expected_trailing_contents

    # Verify native history is consistent
    native_messages = compacted_session.metadata.get("native_messages", [])
    assert isinstance(native_messages, list)
    assert len(native_messages) == len(compacted_session.messages)


# ---------------------------------------------------------------------------
# Application-level context forwarding regression test
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.ollama
def test_compact_range_with_asset_ref_requires_context_ollama(tmp_path: Path) -> None:
    """Regression test: gemini_compaction_feature must pass context to send_request_stream
    so that providers can resolve session asset references in tool messages."""
    if not _ollama_available(BASE_URL):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    try:
        from reference_openai_compatible_provider.provider import (
            OpenAICompatibleProvider,
        )
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Ollama compaction test dependencies not installed: {exc}")

    full_cfg: dict[str, Any] = {
        "providers": {
            "ollama": {
                "provider": "reference_openai_compatible",
                "model": MODEL,
                "base_url": BASE_URL,
                "timeout": TIMEOUT,
            },
        },
        "plugins": [
            "reference_openai_compatible_provider.provider.OpenAICompatibleProvider",
            "gemini_compaction_feature.GeminiCompactionFeaturePlugin",
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
    session = core.add_message(session, "assistant", "Hi there", metadata=None, config=base_config)
    session = core.add_message(session, "user", "How are you?", metadata=None, config=base_config)

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

    try:
        result = app.execute_session_action(
            "gemini_compaction_feature",
            "compact_range",
            {"session_id": session_id, "start": 0, "end": 4},
        )
    except RuntimeError as exc:
        error_msg = str(exc)
        if "session asset attachment requires session_asset_store in context" in error_msg:
            pytest.fail(
                f"Regression detected: gemini_compaction_feature did not forward context to "
                f"send_request_stream. Error: {error_msg}"
            )
        # If the asset was resolved but the model rejects images, that's an environment
        # limitation, not a regression — the fix worked.
        if "does not support image" in error_msg.lower():
            pytest.skip(f"Ollama model does not support image input: {error_msg}")
        raise

    # With the fix, it succeeds and returns a mutation.
    assert result.get("compaction_result", {}).get("status") == "ok", (
        f"Expected ok status, got: {result}"
    )