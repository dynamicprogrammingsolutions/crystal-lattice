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

"""OpenAI Responses provider integration test for Gemini compaction.

This test verifies that the Gemini compaction feature produces correct session
structure and consistent native history when using the OpenAI Responses provider.

The OpenAI Responses provider uses a different native message format
(`type`/`role`/`phase` items) than the standard OpenAI chat-completions format
(`role`/`content` dicts). This test exposes a known issue where the current
Gemini compaction implementation manually splices `native_messages` as
`{role, content, metadata}` dicts, which the OpenAI Responses provider's
`from_native_messages` cannot convert back to core messages correctly.

After the refactoring to use `core.rebuild_native_history()` +
`core.add_message()` instead of manual native_messages splicing, this test
should pass.

Run with:

    pytest plugins/gemini-compaction-feature/tests/test_gemini_compaction_feature_openai_responses_integration.py \\
        -v -s -m openai_responses
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore, Message, Session
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider

pytestmark = [pytest.mark.integration, pytest.mark.api, pytest.mark.openai_responses]


class _SecretValue(str):
    def __repr__(self) -> str:
        return "<redacted secret>"


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI Responses integration tests")
    return _SecretValue(api_key)


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(OpenAIResponsesProvider)
    core.register_feature(
        __import__(
            "gemini_compaction_feature", fromlist=["GeminiCompactionFeaturePlugin"]
        ).GeminiCompactionFeaturePlugin
    )
    return core


def _config(
    api_key: str,
    *,
    model: str = "gpt-4o-mini",
) -> dict[str, object]:
    return {
        "provider": "openai_responses",
        "model": model,
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
        "compaction": {
            "enabled": True,
            "type": "gemini",
            "verification_pass": False,
        },
    }


def _native_history(session: Any) -> list[dict[str, Any]]:
    native_history = (session.metadata or {}).get("native_messages")
    if not isinstance(native_history, list):
        return []
    return [item for item in native_history if isinstance(item, dict)]


@pytest.mark.integration
@pytest.mark.openai_responses
def test_compaction_with_openai_responses_produces_valid_session(
    ensure_openai_api_key: str,
) -> None:
    """End-to-end compaction using OpenAI Responses provider.

    Verifies that:
    1. Compaction returns success (not an error)
    2. The compacted session has a snapshot user message containing <state_snapshot>
    3. The compacted session has an acknowledgment assistant message
    4. Native history is consistent with core messages
    5. System messages are preserved

    This test is expected to FAIL before the refactoring (when Gemini compaction
    manually splices native_messages as {role, content, metadata} dicts) and
    PASS after (when it uses core.rebuild_native_history + core.add_message).
    """
    core = _build_core()
    config = _config(ensure_openai_api_key)

    session = Session(
        session_id="gemini-compaction-openai-responses-test",
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
        {"start": 0, "end": 4},
    )

    # The compaction must succeed
    assert "error" not in result, (
        f"Compaction returned error: {result.get('error')}"
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

    # Verify acknowledgment message follows snapshot
    snapshot_index = next(
        idx
        for idx, m in enumerate(compacted_session.messages)
        if isinstance(m.content, str) and "<state_snapshot>" in m.content
    )
    assert compacted_session.messages[snapshot_index + 1].role == "assistant"

    # Verify native history is consistent with core messages
    native_messages = _native_history(compacted_session)
    assert len(native_messages) == len(compacted_session.messages), (
        f"Native history length ({len(native_messages)}) != "
        f"core messages length ({len(compacted_session.messages)}). "
        f"Native history items: {[n.get('role', n.get('type')) for n in native_messages]}"
    )

    # Verify trailing messages are preserved
    trailing = compacted_session.messages[snapshot_index + 2:]
    trailing_contents = [m.content for m in trailing if isinstance(m.content, str)]
    assert "Answer exactly THREE." in trailing_contents
    assert "THREE" in trailing_contents


@pytest.mark.integration
@pytest.mark.openai_responses
def test_compaction_with_openai_responses_preserves_system_messages(
    ensure_openai_api_key: str,
) -> None:
    """Compaction with system messages preserves them in the result."""
    core = _build_core()
    config = _config(ensure_openai_api_key)

    session = Session(
        session_id="gemini-compaction-openai-responses-system-test",
        messages=[
            Message(role="system", content="System prompt"),
            Message(role="user", content="Answer exactly ONE."),
            Message(role="assistant", content="ONE"),
            Message(role="user", content="Answer exactly TWO."),
            Message(role="assistant", content="TWO"),
        ],
        metadata={},
    )

    compacted_session, result = core.execute_session_action(
        session,
        config,
        "gemini_compaction_feature",
        "compact_range",
        {"start": 0, "end": 4},
    )

    assert "error" not in result, (
        f"Compaction returned error: {result.get('error')}"
    )

    # System message must be preserved
    system_msgs = [m for m in compacted_session.messages if m.role == "system"]
    assert len(system_msgs) == 1, (
        f"Expected exactly 1 system message, got {len(system_msgs)}: "
        f"{[m.content[:50] for m in system_msgs]}"
    )
    assert system_msgs[0].content == "System prompt"