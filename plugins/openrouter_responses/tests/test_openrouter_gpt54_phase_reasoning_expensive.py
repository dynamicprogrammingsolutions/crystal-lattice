"""Expensive GPT-5.4 `/responses` integration checks.

Guards:
- Requires `OPENROUTER_API_KEY`
- Requires `OPENROUTER_RUN_EXPENSIVE=1`

This suite is split so that phase preservation is always validated when the
test runs, while reasoning-delta streaming is only asserted when the server
actually emits reasoning delta events.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

from agent_core import AgentCore
from openrouter_responses_plugins.openrouter_responses_provider import OpenRouterResponsesProvider
from openrouter_responses_plugins.openrouter_responses_reasoning_extension import (
    OpenRouterResponsesReasoningExtension,
)
from plugins.request_options_feature import RequestOptionsFeature


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_RUN_EXPENSIVE = os.getenv("OPENROUTER_RUN_EXPENSIVE")
BASE_URL = "https://openrouter.ai/api/v1"


def _get_openai_provider_options() -> Dict[str, Any]:
    provider_id = os.getenv("OPENAI_PROVIDER") or "openai"
    return {
        "provider": {
            "order": [provider_id],
            "allow_fallbacks": False,
        }
    }


def _parse_debug_sse_events(path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("parsed:"):
            continue
        raw = line[len("parsed:") :].strip()
        try:
            obj = json.loads(raw)
        except Exception:
            continue
        if isinstance(obj, dict):
            events.append(obj)
    return events


def _count_reasoning_delta_events(events: List[Dict[str, Any]]) -> int:
    count = 0
    for ev in events:
        etype = ev.get("type") if isinstance(ev, dict) else None
        if etype not in {
            "response.reasoning.delta",
            "response.reasoning_summary_text.delta",
            "response.reasoning_summary.delta",
        }:
            continue
        delta = ev.get("delta")
        if isinstance(delta, str) and delta:
            count += 1
    return count


def _extract_assistant_phase_texts_from_completed(events: List[Dict[str, Any]]) -> Dict[str, str]:
    for ev in reversed(events):
        if ev.get("type") != "response.completed":
            continue
        resp = ev.get("response")
        if not isinstance(resp, dict):
            continue
        output = resp.get("output")
        if not isinstance(output, list):
            continue
        out: Dict[str, List[str]] = {}
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            role = item.get("role")
            if role is not None and role != "assistant":
                continue
            phase = item.get("phase")
            if not isinstance(phase, str) or not phase:
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            texts: List[str] = []
            for part in content:
                if not isinstance(part, dict) or part.get("type") != "output_text":
                    continue
                text = part.get("text")
                if isinstance(text, str) and text:
                    texts.append(text)
            joined = "\n".join(texts).strip()
            if joined:
                out.setdefault(phase, []).append(joined)
        return {k: "\n".join(v).strip() for k, v in out.items() if v}
    return {}


def _extract_assistant_phase_texts_from_native_messages(native: List[Dict[str, Any]]) -> Dict[str, str]:
    out: Dict[str, List[str]] = {}
    for item in native:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        role = item.get("role")
        if role is not None and role != "assistant":
            continue
        phase = item.get("phase")
        if not isinstance(phase, str) or not phase:
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        texts: List[str] = []
        for part in content:
            if not isinstance(part, dict) or part.get("type") != "output_text":
                continue
            text = part.get("text")
            if isinstance(text, str) and text:
                texts.append(text)
        joined = "\n".join(texts).strip()
        if joined:
            out.setdefault(phase, []).append(joined)
    return {k: "\n".join(v).strip() for k, v in out.items() if v}


@pytest.fixture(scope="module")
def gpt54_stream_result(tmp_path_factory: pytest.TempPathFactory) -> Tuple[
    Path, List[Dict[str, Any]], int, Dict[str, Any], Any
]:
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set")
    if OPENROUTER_RUN_EXPENSIVE != "1":
        pytest.skip("OPENROUTER_RUN_EXPENSIVE != '1'")

    tmp_path = tmp_path_factory.mktemp("openrouter_gpt54")
    debug_path = tmp_path / "openrouter_gpt54_sse.log"

    core = AgentCore()
    core.register_provider(OpenRouterResponsesProvider, extensions=[OpenRouterResponsesReasoningExtension])
    core.register_feature(RequestOptionsFeature)

    config: Dict[str, Any] = {
        "model": "openai/gpt-5.4-20260305",
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 180,
        "enable_reasoning": True,
        "reasoning_effort": "high",
        "reasoning_summary": "auto",
        "debug_sse_path": str(debug_path),
        "request_options": {
            **_get_openai_provider_options(),
            "max_output_tokens": 800,
            "temperature": 0,
        },
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Solve this step by step: If a train travels 60 mph for 2.5 hours, how far does it go?",
    )

    reasoning_partial_count = 0
    final_message: Optional[Dict[str, Any]] = None
    final_session: Any | None = None
    for chunk in core.send_request_stream(session, config):
        if chunk.get("type") == "partial":
            msg = chunk.get("message") or {}
            if not isinstance(msg, dict):
                continue
            md = msg.get("metadata") or {}
            if isinstance(md, dict) and isinstance(md.get("reasoning"), str) and md.get("reasoning"):
                reasoning_partial_count += 1
        elif chunk.get("type") == "final":
            msgs = chunk.get("messages") or []
            if isinstance(msgs, list) and msgs:
                last = msgs[-1]
                if isinstance(last, dict):
                    final_message = last
            final_session = chunk.get("session")

    assert isinstance(final_message, dict)
    assert final_session is not None
    return debug_path, _parse_debug_sse_events(debug_path), reasoning_partial_count, final_message, final_session


@pytest.mark.openrouter
@pytest.mark.integration
@pytest.mark.expensive
def test_gpt54_phase_preservation(gpt54_stream_result) -> None:
    _debug_path, events, _reasoning_partial_count, final_message, final_session = gpt54_stream_result

    assert final_message.get("role") == "assistant"
    phase_texts = _extract_assistant_phase_texts_from_completed(events)
    final_answer = phase_texts.get("final_answer")
    if not final_answer:
        pytest.skip("No assistant phase 'final_answer' found in response.completed")

    assert final_message.get("content") == final_answer

    # Primary invariant for this provider: phased message items are preserved
    # in provider-native history and replayed verbatim next turn.
    session_md = getattr(final_session, "metadata", None) or {}
    native = session_md.get("native_messages") or []
    assert isinstance(native, list)
    native_phase_texts = _extract_assistant_phase_texts_from_native_messages(
        [m for m in native if isinstance(m, dict)]
    )
    assert native_phase_texts.get("final_answer") == final_answer


@pytest.mark.openrouter
@pytest.mark.integration
@pytest.mark.expensive
def test_gpt54_reasoning_delta_streaming_when_present(gpt54_stream_result) -> None:
    _debug_path, events, reasoning_partial_count, _final_message, _final_session = gpt54_stream_result

    if _count_reasoning_delta_events(events) == 0:
        pytest.skip("No reasoning delta events observed; cannot assert reasoning streaming")
    assert reasoning_partial_count > 0, "expected at least one reasoning partial"
