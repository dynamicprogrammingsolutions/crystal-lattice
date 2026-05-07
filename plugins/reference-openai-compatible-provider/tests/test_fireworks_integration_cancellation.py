from __future__ import annotations

import threading
import time

import pytest

from agent_core.types import ProviderRequestCancelled

from fireworks_test_utils import (
    FIREWORKS_QWEN_MODEL,
    build_fireworks_cfg,
    fireworks_model,
)
from reference_openai_compatible_provider.provider import OpenAICompatibleProvider


@pytest.mark.integration
@pytest.mark.fireworks
def test_fireworks_stream_cancel_soon_after_send():
    provider = OpenAICompatibleProvider()
    cfg = build_fireworks_cfg(
        fireworks_model("FIREWORKS_QWEN_MODEL", FIREWORKS_QWEN_MODEL),
        request_options={"reasoning_effort": "none"},
    )
    state = provider.init(cfg)
    native_messages = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "Write a long detailed essay about distributed systems.",
            }
        ],
        state,
    )
    native_messages, state = provider.initialize_request(
        native_messages,
        state,
        request_id="fireworks_cancel_soon",
    )

    outcome: dict[str, object] = {"chunks": []}

    def _consume() -> None:
        try:
            for chunk in provider.stream_api(
                native_messages,
                state,
                request_id="fireworks_cancel_soon",
            ):
                outcome["chunks"].append(chunk)
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    worker = threading.Thread(target=_consume)
    worker.start()

    deadline = time.time() + 15.0
    while time.time() < deadline:
        if provider.cancel_request("fireworks_cancel_soon"):
            break
        time.sleep(0.05)
    else:
        raise AssertionError("Fireworks request was never registered as active")

    worker.join(timeout=30.0)
    assert not worker.is_alive()
    assert not outcome["chunks"]
    assert outcome.get("error") is None or isinstance(
        outcome.get("error"), ProviderRequestCancelled
    )


@pytest.mark.integration
@pytest.mark.fireworks
def test_fireworks_stream_cancel_after_first_partial():
    provider = OpenAICompatibleProvider()
    cfg = build_fireworks_cfg(
        fireworks_model("FIREWORKS_QWEN_MODEL", FIREWORKS_QWEN_MODEL),
        request_options={"reasoning_effort": "none"},
    )
    state = provider.init(cfg)
    native_messages = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "Write a long detailed essay about concurrency.",
            }
        ],
        state,
    )
    native_messages, state = provider.initialize_request(
        native_messages,
        state,
        request_id="fireworks_cancel_after_partial",
    )

    outcome: dict[str, object] = {"chunks": []}

    def _consume() -> None:
        try:
            for chunk in provider.stream_api(
                native_messages,
                state,
                request_id="fireworks_cancel_after_partial",
            ):
                outcome["chunks"].append(chunk)
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    worker = threading.Thread(target=_consume)
    worker.start()

    deadline = time.time() + 45.0
    while time.time() < deadline:
        if outcome["chunks"]:
            break
        time.sleep(0.05)
    else:
        raise AssertionError("Fireworks stream did not emit a partial before cancellation")

    assert provider.cancel_request("fireworks_cancel_after_partial") is True

    worker.join(timeout=30.0)
    assert not worker.is_alive()
    assert outcome["chunks"]
    assert isinstance(outcome.get("error"), ProviderRequestCancelled)