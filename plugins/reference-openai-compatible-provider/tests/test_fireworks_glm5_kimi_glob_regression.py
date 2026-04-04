from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fireworks_test_utils import (
    build_fireworks_cfg,
    build_reference_core,
    fireworks_model,
    iter_request_stream_or_skip,
    send_request_or_skip,
)
from kimi_tools.kimi_glob_tool import KimiGlobTool


GLM5_FIREWORKS_MODEL = "fireworks/glm-5"
REPO_ROOT = Path(__file__).resolve().parents[3]
GLOB_PATTERN = "**/*openai*responses*/**"


def _collect_response(core, session, config: dict[str, Any], *, stream: bool):
    if not stream:
        return send_request_or_skip(core, session, config)

    final_event = None
    for event in iter_request_stream_or_skip(core, session, config):
        if event.get("type") == "final":
            final_event = event
    assert final_event is not None, "expected a final streaming event"
    return final_event["session"], final_event["messages"]


def _decode_arguments(tool_call: dict[str, Any]) -> dict[str, Any]:
    function = tool_call.get("function") or {}
    raw_arguments = function.get("arguments")
    if isinstance(raw_arguments, str):
        try:
            parsed = json.loads(raw_arguments)
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return raw_arguments if isinstance(raw_arguments, dict) else {}


@pytest.mark.integration
@pytest.mark.fireworks
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_fireworks_glm5_preserves_kimi_glob_tool_call_shape(stream: bool) -> None:
    cfg = {
        **build_fireworks_cfg(
            fireworks_model("FIREWORKS_GLM5_MODEL", GLM5_FIREWORKS_MODEL),
            request_options={"temperature": 0, "seed": 2},
        ),
        "allowed_paths": [str(REPO_ROOT)],
        "working_directory": str(REPO_ROOT),
    }

    core = build_reference_core(KimiGlobTool)
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        (
            "You have access to exactly one tool named Glob. "
            "You must call Glob exactly once before answering. "
            "Do not rename the tool. Do not include XML or tag markup in the tool name. "
            f"Use the exact pattern `{GLOB_PATTERN}` as the pattern argument."
        ),
    )
    session = core.add_message(
        session,
        "user",
        (
            "Use the Glob tool now. "
            f"Search with the exact pattern `{GLOB_PATTERN}` from the working directory. "
            "Your first response must be the tool call."
        ),
    )

    _session, responses = _collect_response(core, session, cfg, stream=stream)
    assert responses, "expected assistant response"

    assistant = responses[-1]
    tool_calls = (assistant.get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, f"expected tool calls, got assistant message: {assistant!r}"

    first_tool_call = tool_calls[0]
    function = first_tool_call.get("function") or {}
    tool_name = function.get("name")
    assert tool_name == "Glob", f"expected function.name='Glob', got {first_tool_call!r}"

    arguments = _decode_arguments(first_tool_call)
    assert arguments.get("pattern") == GLOB_PATTERN, (
        f"expected Glob pattern {GLOB_PATTERN!r}, got {first_tool_call!r}"
    )

    tool_messages = core.execute_tool_calls(tool_calls, cfg)
    assert tool_messages, "expected tool execution results"
    for tool_message in tool_messages:
        content = tool_message.get("content", "")
        assert "no tool handled" not in content, (
            f"malformed tool call propagated into core execution: {tool_calls!r} -> {tool_message!r}"
        )