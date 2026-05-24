from __future__ import annotations

import pytest

from fireworks_test_utils import (
    FIREWORKS_GLM_MODEL,
    build_fireworks_cfg,
    build_reference_core,
    fireworks_model,
    iter_request_stream_or_skip,
)

pytestmark = pytest.mark.api


@pytest.mark.integration
@pytest.mark.fireworks
def test_reasoning_metadata_fireworks_glm_streaming():
    cfg = build_fireworks_cfg(
        fireworks_model("FIREWORKS_GLM_MODEL", FIREWORKS_GLM_MODEL),
        request_options={"stream_options": {"include_usage": True}},
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
    assert assistant.get("content", "").strip()
    assert isinstance(metadata.get("usage_total_tokens"), int)
