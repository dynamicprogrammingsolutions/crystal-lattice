"""Integration test for GenerateTitleAppPlugin with OpenRouter (GPT-5 Mini).

This test runs against the real OpenRouter API and verifies that, given a
strong system message and prompt, the model responds with exactly two
non-empty lines representing a title and description.

Requires the OPENROUTER_API_KEY environment variable.

Run with:

    pytest core/python/tests/test_generate_title_app_openrouter_integration.py \
        -v -s -m openrouter
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import json
import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL_GPT5_MINI = "openai/gpt-5-mini"


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    """Skip tests if OpenRouter API key is not configured."""
    if not OPENROUTER_API_KEY:
        pytest.skip(
            "OPENROUTER_API_KEY not set; skipping GenerateTitle OpenRouter integration test",
        )


def _make_config(tmp_path: Path) -> Path:
    """Build a minimal AgentApplication config using OpenRouter + GenerateTitle."""

    cfg: Dict[str, Any] = {
        "providers": {
            "openrouter_title": {
                "provider": "openrouter",
                "model": MODEL_GPT5_MINI,
                "api_key": OPENROUTER_API_KEY,
                "base_url": BASE_URL,
                "timeout": 120,
            }
        },
        "agents": {
            "default": {"provider": "openrouter_title"},
        },
        "plugins": [
            "plugins.openrouter_provider.OpenRouterProvider",
            "plugins.generate_title_app.GenerateTitleAppPlugin",
        ],
        "application": {
            "generate_title_agent_id": "default",
            "generate_title_enable_description": True,
            "generate_title_prompt_template": (
                "Generate a short (max 8 words) title for this conversation "
                "on the first line and a one-line plain-text description on "
                "the second line. Respond with exactly two non-empty lines."
            ),
            "generate_title_system_message": (
                "You are a title and description generator. Respond with "
                "exactly two non-empty lines. Line 1 must be only a concise "
                "title for the conversation (maximum 8 words). Line 2 must "
                "be only a single-sentence plain-text description of the "
                "conversation. Do not include labels, numbering, bullet "
                "points, or any extra text before or after these two lines."
            ),
        },
    }

    path = tmp_path / "config_generate_title_openrouter.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


@pytest.mark.integration
@pytest.mark.openrouter
def test_generate_title_openrouter_gpt5_two_line_response(ensure_api_key: None, tmp_path: Path) -> None:
    """End-to-end test that GPT-5 Mini returns exactly two lines.

    The GenerateTitleAppPlugin is configured to talk to an OpenRouter-backed
    agent using a strong system message and prompt that require exactly two
    non-empty lines. This test asserts that the stored metadata reflects a
    title and description split across two lines.
    """

    app = _build_app(tmp_path)

    # Create a sample conversation.
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)

    session = core.add_message(
        session,
        "user",
        "We discussed migrating our backend from a monolith to microservices, "
        "including database sharding, deployment strategies, and monitoring.",
        None,
        base_config,
    )
    session = core.add_message(
        session,
        "assistant",
        "You outlined pros and cons and identified next steps.",
        None,
        base_config,
    )

    app.save_session(session)
    session_id = session.session_id

    # Run the generate_title_for_session action end-to-end.
    result = app.execute_application_action(
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id},
    )

    # Basic sanity: action succeeded and updated the session.
    mutations = result.get("mutations")
    assert isinstance(mutations, dict)
    updated = mutations.get("updated_session_ids") or []
    assert updated == [session_id]

    # Reload the session and inspect metadata.
    ctx = app.load_session(session_id)
    assert ctx is not None
    _core2, _base2, session2 = ctx
    metadata = session2.metadata if isinstance(session2.metadata, dict) else {}

    title = metadata.get("title")
    subtitle = metadata.get("subtitle")

    assert isinstance(title, str) and title.strip() != ""
    assert isinstance(subtitle, str) and subtitle.strip() != ""

    # As an extra guard, ensure that each field does not contain embedded
    # newlines; the split of the two-line response into title/description
    # should already have happened inside the plugin.
    assert "\n" not in title
    assert "\n" not in subtitle
