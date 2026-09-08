from __future__ import annotations

import os
import threading
import time
import uuid
from typing import Any

import pytest

from agent_core import AgentCore
from agent_core.types import ProviderRequestCancelled
from plugins.request_options_feature import RequestOptionsFeature

from anthropic_plugins import (
    AnthropicPromptCachingExtension,
    AnthropicProvider,
    AnthropicReasoningControlsExtension,
    AnthropicReasoningExtension,
    AnthropicToolsExtension,
    AnthropicUsageExtension,
)


pytestmark = [
    pytest.mark.integration,
    pytest.mark.api,
    pytest.mark.anthropic,
]


def _api_key() -> str:
    value = os.getenv("ANTHROPIC_API_KEY")
    if not value:
        pytest.skip("ANTHROPIC_API_KEY is required")
    return value


def _official_models() -> list[dict[str, Any]]:
    return AnthropicProvider().get_models(
        {
            "api_key": _api_key(),
            "base_url": "https://api.anthropic.com",
            "timeout": 60,
            "max_retries": 1,
        }
    )


def _require_model(model_id: str) -> None:
    if not any(model.get("id") == model_id for model in _official_models()):
        pytest.skip(f"required Anthropic model {model_id!r} is unavailable")


def _contains_cache_control(value: Any) -> bool:
    if isinstance(value, list):
        return any(_contains_cache_control(item) for item in value)
    if not isinstance(value, dict):
        return False
    if "cache_control" in value:
        return True
    return any(_contains_cache_control(item) for item in value.values())


def _cache_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        AnthropicProvider,
        extensions=[
            AnthropicPromptCachingExtension,
            AnthropicUsageExtension,
        ],
    )
    return core


def _send(
    core: AgentCore,
    session: Any,
    config: dict[str, Any],
    *,
    stream: bool,
) -> tuple[Any, list[dict[str, Any]]]:
    if not stream:
        return core.send_request(session, config)
    final_event = None
    for event in core.send_request_stream(session, config):
        if event.get("type") == "final":
            final_event = event
    assert final_event is not None
    return final_event["session"], final_event["messages"]


@pytest.mark.timeout(180)
def test_official_models_drive_reasoning_control_descriptors() -> None:
    models = _official_models()
    extension = AnthropicReasoningControlsExtension()
    enriched = extension.get_models({"model": "claude-sonnet-5"}, models)
    by_id = {model["id"]: model for model in enriched}

    haiku = by_id["claude-haiku-4-5-20251001"]["anthropic_reasoning_controls"]
    assert haiku["thinking_types"] == ["enabled"]
    assert haiku.get("effort_levels", []) == []

    sonnet_46 = by_id["claude-sonnet-4-6"]["anthropic_reasoning_controls"]
    assert sonnet_46["thinking_types"] == ["enabled", "adaptive"]
    assert sonnet_46["effort_levels"] == ["low", "medium", "high", "max"]

    sonnet_5 = by_id["claude-sonnet-5"]["anthropic_reasoning_controls"]
    assert sonnet_5["thinking_types"] == ["adaptive"]
    assert sonnet_5["effort_levels"] == [
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
    ]
    ui = {
        element["key"]: element
        for element in extension.get_ui_elements(
            {"model": "claude-sonnet-5"},
            {"models": enriched},
        )
    }
    assert [
        option["value"] for option in ui["anthropic_reasoning_mode"]["options"]
    ] == [
        "disabled",
        "adaptive",
    ]
    assert [
        option["value"] for option in ui["anthropic_reasoning_effort"]["options"]
    ] == ["low", "medium", "high", "xhigh", "max"]


@pytest.mark.timeout(300)
@pytest.mark.parametrize(
    ("ttl", "stream", "breakdown_key"),
    [
        ("5m", False, "usage_cache_write_5m_tokens"),
        ("1h", True, "usage_cache_write_1h_tokens"),
    ],
)
def test_official_automatic_prompt_cache_write_and_hit(
    ttl: str,
    stream: bool,
    breakdown_key: str,
) -> None:
    model = "claude-sonnet-4-6"
    _require_model(model)
    config = {
        "provider": "anthropic",
        "api_key": _api_key(),
        "base_url": "https://api.anthropic.com",
        "model": model,
        "timeout": 120,
        "max_tokens": 32,
        "capabilities": {"prompt_caching": True},
        "prompt_cache_ttl": ttl,
    }
    core = _cache_core()
    stable_prefix = f"CACHE_STAGE3_{uuid.uuid4()} " + " ".join(
        [
            "Prompt caching preserves a stable prefix so repeated requests "
            "can reuse prior input processing."
        ]
        * 180
    )
    session = core.add_message(
        core.create_session(),
        "system",
        stable_prefix,
        config=config,
    )
    session = core.add_message(
        session,
        "user",
        "Reply with one word: ready",
        config=config,
    )

    session, first = _send(core, session, config, stream=stream)
    first_metadata = first[-1]["metadata"]
    assert first_metadata["usage_cache_write_tokens"] > 0
    assert first_metadata[breakdown_key] > 0

    session = core.add_message(
        session,
        "user",
        "Reply with one word: again",
        config=config,
    )
    session, second = _send(core, session, config, stream=stream)
    second_metadata = second[-1]["metadata"]
    assert second_metadata["usage_cached_tokens"] > 0
    assert not _contains_cache_control(session.metadata["native_messages"])


class SequentialTool:
    name = "anthropic_stage3_sequential"
    version = "0.1.0"

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {}

    def get_tool_schemas(
        self,
        state: dict[str, Any],
        *,
        prepared: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "hidden_number",
                    "description": (
                        "Return a hidden integer that is not available in the "
                        "conversation. Call this before using add."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "add",
                    "description": "Add two integers. Always use this when instructed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "integer"},
                            "b": {"type": "integer"},
                        },
                        "required": ["a", "b"],
                    },
                },
            },
        ]

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        if tool_name == "hidden_number":
            return {"success": True, "value": 37}
        return {"success": True, "value": int(payload["a"]) + int(payload["b"])}

    def format_tool_result(
        self,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> str:
        return str(result["value"])


@pytest.mark.timeout(300)
def test_official_adaptive_reasoning_is_interleaved_around_tool_result() -> None:
    model = "claude-sonnet-5"
    _require_model(model)
    config = {
        "provider": "anthropic",
        "api_key": _api_key(),
        "base_url": "https://api.anthropic.com",
        "model": model,
        "timeout": 180,
        "max_tokens": 1000,
        "capabilities": {"anthropic_reasoning_controls": True},
        "anthropic_reasoning_mode": "adaptive",
        "anthropic_reasoning_effort": "max",
        "anthropic_reasoning_display": "summarized",
    }
    core = AgentCore()
    core.register_feature(RequestOptionsFeature)
    core.register_provider(
        AnthropicProvider,
        extensions=[
            AnthropicToolsExtension,
            AnthropicReasoningExtension,
            AnthropicReasoningControlsExtension,
            AnthropicUsageExtension,
        ],
    )
    core.register_tool(SequentialTool)
    session = core.add_message(
        core.create_session(),
        "user",
        (
            "First reason carefully and call hidden_number. Its value is not "
            "available in this conversation. After that tool returns, reason "
            "again about the next step, then call add to add exactly 8 to the "
            "hidden value. Do not combine or skip the two tool calls. After the "
            "add result, report the final number."
        ),
        config=config,
    )

    session, first = core.send_request(session, config)
    first_metadata = first[-1]["metadata"]
    calls = first_metadata.get("tool_calls") or []
    assert calls and calls[0]["name"] == "hidden_number"
    assert str(first_metadata.get("reasoning") or "").strip()

    for message in core.execute_tool_calls(calls, config):
        session = core.add_message(
            session,
            message["role"],
            message["content"],
            metadata=message.get("metadata"),
            tool_result=message.get("toolResult"),
            config=config,
        )

    session, second = core.send_request(session, config)
    second_metadata = second[-1]["metadata"]
    assert str(second_metadata.get("reasoning") or "").strip()
    second_calls = second_metadata.get("tool_calls") or []
    assert second_calls and second_calls[0]["name"] == "add"

    for message in core.execute_tool_calls(second_calls, config):
        session = core.add_message(
            session,
            message["role"],
            message["content"],
            metadata=message.get("metadata"),
            tool_result=message.get("toolResult"),
            config=config,
        )

    session, third = core.send_request(session, config)
    assert "45" in str(third[-1]["content"])
    native = session.metadata["native_messages"]
    assistant_blocks = [
        block
        for message in native
        if isinstance(message, dict) and message.get("role") == "assistant"
        for content in [message.get("content")]
        if isinstance(content, list)
        for block in content
        if isinstance(block, dict)
    ]
    assert sum(block.get("type") == "thinking" for block in assistant_blocks) >= 2
    assert sum(block.get("type") == "tool_use" for block in assistant_blocks) >= 2
    assert not any(key.startswith("_") for block in assistant_blocks for key in block)


@pytest.mark.timeout(180)
def test_official_invalid_auth_error_is_redacted() -> None:
    invalid_key = f"invalid-{uuid.uuid4()}"
    core = AgentCore()
    core.register_provider(AnthropicProvider)
    config = {
        "provider": "anthropic",
        "api_key": invalid_key,
        "base_url": "https://api.anthropic.com",
        "model": "claude-haiku-4-5-20251001",
        "timeout": 60,
        "max_retries": 0,
        "max_tokens": 8,
    }
    session = core.add_message(
        core.create_session(),
        "user",
        "Reply with one word.",
        config=config,
    )

    with pytest.raises(RuntimeError) as exc_info:
        core.send_request(session, config)

    assert invalid_key not in str(exc_info.value)
    assert (
        "<redacted>" in str(exc_info.value)
        or "authentication" in str(exc_info.value).lower()
    )


@pytest.mark.timeout(240)
def test_official_stream_cancellation_after_first_partial() -> None:
    model = "claude-haiku-4-5-20251001"
    _require_model(model)
    provider = AnthropicProvider()
    config = {
        "provider": "anthropic",
        "api_key": _api_key(),
        "base_url": "https://api.anthropic.com",
        "model": model,
        "timeout": 180,
        "max_tokens": 1200,
    }
    state = provider.init(config)
    native, state = provider.initialize_request(
        [
            {
                "role": "user",
                "content": (
                    "Write a detailed numbered explanation of ten distinct "
                    "ways to improve software reliability."
                ),
            }
        ],
        state,
        request_id="stage3-cancel",
    )
    outcome: dict[str, Any] = {}
    first_event = threading.Event()

    def _consume() -> None:
        try:
            for _event in provider.stream_api(
                native,
                state,
                request_id="stage3-cancel",
            ):
                first_event.set()
        except Exception as exc:
            outcome["error"] = exc

    thread = threading.Thread(target=_consume, daemon=True)
    thread.start()
    assert first_event.wait(timeout=60)
    assert provider.cancel_request("stage3-cancel") is True
    thread.join(timeout=30)
    if thread.is_alive():
        pytest.fail("Anthropic stream did not stop after cancellation")
    assert isinstance(outcome.get("error"), ProviderRequestCancelled)
    time.sleep(0.01)
    assert provider.cancel_request("stage3-cancel") is False
