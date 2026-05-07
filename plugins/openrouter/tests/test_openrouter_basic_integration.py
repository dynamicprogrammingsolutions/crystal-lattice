"""Basic integration test for OpenRouter provider.

This test verifies basic connectivity and message handling with OpenRouter API.
Requires OPENROUTER_API_KEY environment variable.

Run with: pytest tests/test_openrouter_basic_integration.py -v
"""

from __future__ import annotations

import os
import threading
import time
import pytest

# Load .env file if it exists
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from agent_core import AgentCore
from agent_core.types import ProviderRequestCancelled
from openrouter_plugins.openrouter_provider import OpenRouterProvider


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL_GEMINI_FLASH_LITE = "google/gemini-2.5-flash-lite"


@pytest.fixture(scope="module")
def ensure_api_key():
    """Skip tests unless OPENROUTER_API_KEY is set."""
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter integration tests")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_basic_non_streaming(ensure_api_key):
    """Test basic non-streaming request with OpenRouter."""
    core = AgentCore()
    core.register_provider(OpenRouterProvider)

    config = {
        "model": MODEL_GEMINI_FLASH_LITE,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Say 'Hello' and nothing else.")

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert len(responses) > 0

    assistant_msg = responses[-1]
    assert assistant_msg["role"] == "assistant"
    assert isinstance(assistant_msg.get("content"), str)
    assert len(assistant_msg["content"]) > 0
    print(f"\nResponse: {assistant_msg['content']}")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_basic_streaming(ensure_api_key):
    """Test basic streaming request with OpenRouter."""
    core = AgentCore()
    core.register_provider(OpenRouterProvider)

    config = {
        "model": "openai/gpt-5-mini",
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Write a poem about programming.")

    partial_count = 0
    final_message = None

    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "partial":
            text = chunk["message"].get("content", "")
            if text:
                partial_count += 1
                print(text, end="", flush=True)
        elif chunk["type"] == "final":
            final_message = chunk["messages"][-1]
            print(f"\n\nFinal: {final_message}")

    assert partial_count > 0, "expected streaming partials"
    assert final_message is not None
    assert final_message["role"] == "assistant"
    assert isinstance(final_message.get("content"), str)
    assert len(final_message["content"]) > 0


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_multiple_models(ensure_api_key):
    """Test that different models work through OpenRouter."""
    core = AgentCore()
    core.register_provider(OpenRouterProvider)

    models_to_test = [
        "google/gemini-2.5-flash-lite",
        "x-ai/grok-4.1-fast",
    ]

    for model in models_to_test:
        config = {
            "model": model,
            "api_key": OPENROUTER_API_KEY,
            "base_url": BASE_URL,
            "timeout": 60,
        }

        session = core.create_session()
        session = core.add_message(session, "user", "Reply with the word 'OK'.")

        try:
            new_session, responses = core.send_request(session, config)
            assert len(responses) > 0
            assert responses[-1]["role"] == "assistant"
            print(f"\n{model}: {responses[-1]['content'][:50]}")
        except Exception as e:
            pytest.fail(f"Model {model} failed: {e}")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_with_optional_headers(ensure_api_key):
    """Test OpenRouter with optional site_url and app_name headers."""
    core = AgentCore()
    core.register_provider(OpenRouterProvider)

    config = {
        "model": MODEL_GEMINI_FLASH_LITE,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        "site_url": "https://github.com/ai-agent-platform",
        "app_name": "AI Agent Platform Tests",
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Say 'Headers work'.")

    new_session, responses = core.send_request(session, config)

    assert len(responses) > 0
    assert responses[-1]["role"] == "assistant"
    print(f"\nWith headers: {responses[-1]['content']}")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_stream_cancel_soon_after_send_real_api(ensure_api_key):
    provider = OpenRouterProvider()
    config = {
        "model": "openai/gpt-5-mini",
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
    }
    state = provider.init(config)
    native_messages = provider.to_native_messages(
        [{"role": "user", "content": "Write a long detailed essay about distributed systems."}],
        state,
    )
    native_messages, state = provider.initialize_request(
        native_messages,
        state,
        request_id="openrouter_cancel_soon",
    )

    outcome: dict[str, object] = {"chunks": []}

    def _consume() -> None:
        try:
            for chunk in provider.stream_api(
                native_messages,
                state,
                request_id="openrouter_cancel_soon",
            ):
                outcome["chunks"].append(chunk)
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    worker = threading.Thread(target=_consume)
    worker.start()

    deadline = time.time() + 10.0
    while time.time() < deadline:
        if provider.cancel_request("openrouter_cancel_soon"):
            break
        time.sleep(0.02)
    else:
        raise AssertionError("OpenRouter request was never registered as active")

    worker.join(timeout=20)
    assert not worker.is_alive()
    assert isinstance(outcome.get("error"), ProviderRequestCancelled)


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_stream_cancel_after_first_partial_real_api(ensure_api_key):
    provider = OpenRouterProvider()
    config = {
        "model": "openai/gpt-5-mini",
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
    }
    state = provider.init(config)
    native_messages = provider.to_native_messages(
        [{"role": "user", "content": "Write a long detailed essay about concurrency."}],
        state,
    )
    native_messages, state = provider.initialize_request(
        native_messages,
        state,
        request_id="openrouter_cancel_after_partial",
    )

    outcome: dict[str, object] = {"chunks": []}

    def _consume() -> None:
        try:
            for chunk in provider.stream_api(
                native_messages,
                state,
                request_id="openrouter_cancel_after_partial",
            ):
                outcome["chunks"].append(chunk)
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    worker = threading.Thread(target=_consume)
    worker.start()

    deadline = time.time() + 30.0
    while time.time() < deadline:
        if outcome["chunks"]:
            break
        time.sleep(0.05)
    else:
        raise AssertionError("OpenRouter stream did not emit a partial before cancellation")

    assert provider.cancel_request("openrouter_cancel_after_partial") is True

    worker.join(timeout=20)
    assert not worker.is_alive()
    assert outcome["chunks"]
    assert isinstance(outcome.get("error"), ProviderRequestCancelled)
