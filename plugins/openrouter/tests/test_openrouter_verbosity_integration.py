"""Integration test for OpenRouter GPT-5 verbosity.

Requires ``OPENROUTER_API_KEY`` (loaded from ``.env`` when available).

Run with:

    pytest plugins/openrouter/tests/test_openrouter_verbosity_integration.py -v -s -m openrouter
"""

from __future__ import annotations

import os

import pytest

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from agent_core import AgentCore
from openrouter_plugins.openrouter_provider import OpenRouterProvider
from openrouter_plugins.openrouter_verbosity_extension import OpenRouterVerbosityExtension
from plugins.request_options_feature import RequestOptionsFeature


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-5-mini"
pytestmark = pytest.mark.api


@pytest.fixture(scope="module")
def ensure_api_key():
    if not OPENROUTER_API_KEY:
        pytest.skip(
            "OPENROUTER_API_KEY not set; skipping OpenRouter verbosity integration tests"
        )


def _make_config(verbosity: str) -> dict[str, object]:
    return {
        "model": MODEL,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        "verbosity": verbosity,
        # Reduce variance so the length comparison is stable.
        "request_options": {
            "temperature": 0,
            "seed": 1234,
        },
    }


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_gpt5_verbosity_high_is_longer_than_low(ensure_api_key):
    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterVerbosityExtension])
    core.register_feature(RequestOptionsFeature)

    prompt = "What is the meaning of the life?"

    session_low = core.create_session()
    session_low = core.add_message(session_low, "user", prompt)
    _new_session_low, responses_low = core.send_request(session_low, _make_config("low"))
    low_text = (responses_low[-1].get("content") or "").strip()

    session_high = core.create_session()
    session_high = core.add_message(session_high, "user", prompt)
    _new_session_high, responses_high = core.send_request(session_high, _make_config("high"))
    high_text = (responses_high[-1].get("content") or "").strip()

    assert low_text
    assert high_text

    low_len = len(low_text)
    high_len = len(high_text)
    print("low_len:", low_len)
    print("high_len:", high_len)

    # This is intentionally a coarse integration assertion. On GPT-5 models,
    # OpenAI-style verbosity should have a large impact on response length.
    assert high_len > low_len
    assert high_len - low_len >= 500
