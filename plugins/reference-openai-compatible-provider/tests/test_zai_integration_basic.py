from __future__ import annotations

import pytest

from zai_test_utils import (
    ZAI_BASIC_MODEL,
    ZAI_REASONING_MODEL,
    build_reference_core,
    build_zai_cfg,
    iter_request_stream_or_skip,
    send_request_or_skip,
    zai_model,
)

pytestmark = pytest.mark.api


@pytest.mark.integration
@pytest.mark.zai
def test_basic_non_streaming_zai_openai_compat():
    cfg = build_zai_cfg(
        zai_model("ZAI_BASIC_MODEL", ZAI_BASIC_MODEL),
        request_options={"thinking": {"type": "disabled"}, "temperature": 0},
    )

    core = build_reference_core()
    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly pong.")

    _session2, finals = send_request_or_skip(core, session, cfg)
    assert finals and finals[-1]["role"] == "assistant"
    assert finals[-1].get("content", "").strip().lower() == "pong"


@pytest.mark.integration
@pytest.mark.zai
def test_basic_streaming_zai_openai_compat():
    cfg = build_zai_cfg(
        zai_model("ZAI_BASIC_MODEL", ZAI_BASIC_MODEL),
        request_options={"thinking": {"type": "disabled"}, "temperature": 0},
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
@pytest.mark.zai
def test_models_ui_schema_lists_available_zai_models():
    cfg = build_zai_cfg(zai_model("ZAI_REASONING_MODEL", ZAI_REASONING_MODEL))

    core = build_reference_core()
    schema = core.get_ui_schema(cfg)
    model_el = next(
        (el for el in schema if isinstance(el, dict) and el.get("key") == "model"), None
    )

    assert model_el is not None
    options = model_el.get("options")
    assert isinstance(options, list) and options
    assert any(
        isinstance(option, dict)
        and isinstance(option.get("value"), str)
        and option["value"].startswith("glm-")
        for option in options
    )