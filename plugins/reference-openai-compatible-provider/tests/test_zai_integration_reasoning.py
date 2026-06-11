from __future__ import annotations

import pytest

from zai_test_utils import (
    ZAI_REASONING_MODEL,
    build_reference_core,
    build_zai_cfg,
    iter_request_stream_or_skip,
    zai_model,
)

pytestmark = pytest.mark.api


@pytest.mark.integration
@pytest.mark.zai
def test_reasoning_metadata_zai_streaming():
    cfg = build_zai_cfg(
        zai_model("ZAI_REASONING_MODEL", ZAI_REASONING_MODEL),
        request_options={
            "thinking": {"type": "enabled"},
            "temperature": 0,
            "stream_options": {"include_usage": True},
        },
    )

    core = build_reference_core()
    session = core.create_session()
    session = core.add_message(
        session, "user", "Compute 12*12 and return only the answer."
    )

    final_event = None
    for event in iter_request_stream_or_skip(core, session, cfg):
        if event.get("type") == "final":
            final_event = event

    assert final_event is not None
    assistant = final_event["messages"][-1]
    metadata = assistant.get("metadata") or {}

    reasoning = metadata.get("reasoning_content") or metadata.get("reasoning")
    assert isinstance(reasoning, str) and reasoning.strip()
    assert assistant.get("content", "").strip() == "144"
    assert isinstance(metadata.get("usage_total_tokens"), int)