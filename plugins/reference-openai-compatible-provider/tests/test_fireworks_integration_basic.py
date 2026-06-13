from __future__ import annotations

import pytest

from fireworks_test_utils import (
    FIREWORKS_GLM_MODEL,
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
def test_basic_non_streaming_fireworks_openai_compat():
    cfg = build_fireworks_cfg(
        fireworks_model("FIREWORKS_QWEN_MODEL", FIREWORKS_QWEN_MODEL),
        request_options={"reasoning_effort": "none"},
    )

    core = build_reference_core()
    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly pong.")

    _session2, finals = send_request_or_skip(core, session, cfg)
    assert finals and finals[-1]["role"] == "assistant"
    assert finals[-1].get("content", "").strip().lower() == "pong"


@pytest.mark.integration
@pytest.mark.fireworks
def test_basic_streaming_fireworks_openai_compat():
    cfg = build_fireworks_cfg(
        fireworks_model("FIREWORKS_QWEN_MODEL", FIREWORKS_QWEN_MODEL),
        request_options={"reasoning_effort": "none"},
    )

    core = build_reference_core()
    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly pong.")

    saw_partial = False
    final_event = None
    for event in iter_request_stream_or_skip(core, session, cfg):
        if event.get("type") == "partial":
            saw_partial = True
        if event.get("type") == "final":
            final_event = event

    assert saw_partial
    assert final_event is not None
    assistant = final_event["messages"][-1]
    assert assistant["role"] == "assistant"
    assert assistant.get("content", "").strip().lower() == "pong"


@pytest.mark.integration
@pytest.mark.fireworks
def test_models_ui_schema_lists_available_fireworks_models():
    cfg = build_fireworks_cfg(
        fireworks_model("FIREWORKS_GLM_MODEL", FIREWORKS_GLM_MODEL)
    )

    core = build_reference_core()
    schema = core.get_ui_schema(cfg)
    model_el = next(
        (el for el in schema if isinstance(el, dict) and el.get("key") == "model"), None
    )

    assert model_el is not None
    assert model_el.get("type") in {"select", "dropdown"}
    options = model_el.get("options")
    assert isinstance(options, list) and options
    assert any(
        isinstance(option, dict)
        and isinstance(option.get("value"), str)
        and option["value"].startswith("accounts/fireworks/models/")
        for option in options
    )
