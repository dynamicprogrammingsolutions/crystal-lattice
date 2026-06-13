from __future__ import annotations

import pytest

from fireworks_test_utils import (
    FIREWORKS_QWEN_MODEL,
    build_fireworks_cfg,
    build_reference_core,
    fireworks_model,
    iter_request_stream_or_skip,
    send_request_or_skip,
)

pytestmark = pytest.mark.api


@pytest.mark.integration
@pytest.mark.fireworks
def test_usage_metadata_fireworks_openai_compat():
    cfg = build_fireworks_cfg(
        fireworks_model("FIREWORKS_QWEN_MODEL", FIREWORKS_QWEN_MODEL),
        request_options={"reasoning_effort": "none"},
    )

    core = build_reference_core()
    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly pong.")

    _session2, finals = send_request_or_skip(core, session, cfg)
    assert finals and finals[-1]["role"] == "assistant"

    metadata = finals[-1].get("metadata") or {}
    assert isinstance(metadata.get("usage"), dict)
    assert isinstance(metadata.get("usage_prompt_tokens"), int)
    assert isinstance(metadata.get("usage_completion_tokens"), int)
    assert isinstance(metadata.get("usage_total_tokens"), int)


@pytest.mark.integration
@pytest.mark.fireworks
def test_streaming_usage_metadata_fireworks_openai_compat():
    cfg = build_fireworks_cfg(
        fireworks_model("FIREWORKS_QWEN_MODEL", FIREWORKS_QWEN_MODEL),
        request_options={
            "reasoning_effort": "none",
            "stream_options": {"include_usage": True},
        },
    )

    core = build_reference_core()
    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly pong.")

    final_event = None
    for event in iter_request_stream_or_skip(core, session, cfg):
        if event.get("type") == "final":
            final_event = event

    assert final_event is not None
    assistant = final_event["messages"][-1]
    metadata = assistant.get("metadata") or {}

    assert assistant.get("content", "").strip().lower() == "pong"
    assert isinstance(metadata.get("usage"), dict)
    assert isinstance(metadata.get("usage_total_tokens"), int)
