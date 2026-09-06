from __future__ import annotations

import os
from typing import Any

import pytest

from agent_core import AgentCore
from plugins.request_options_feature import RequestOptionsFeature

from anthropic_plugins import (
    AnthropicProvider,
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


def _model(provider: AnthropicProvider, config: dict[str, Any]) -> str:
    override = os.getenv("ANTHROPIC_TEST_MODEL")
    if override:
        return override
    models = provider.get_models(config)
    haiku = next(
        (
            model["id"]
            for model in models
            if "haiku" in str(model.get("id", "")).lower()
        ),
        None,
    )
    if isinstance(haiku, str):
        return haiku
    if models:
        return str(models[0]["id"])
    pytest.skip("Anthropic model discovery returned no models")


def _config() -> dict[str, Any]:
    key = _api_key()
    provider = AnthropicProvider()
    base = {
        "provider": "anthropic",
        "api_key": key,
        "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
        "timeout": 120,
        "max_tokens": 64,
    }
    return {**base, "model": _model(provider, base)}


class AddTool:
    name = "anthropic_hosted_test_add"
    version = "0.1.0"

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {}

    def get_tool_schemas(
        self, state: dict[str, Any], *, prepared: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "add",
                    "description": "Add two integers. Use this tool when instructed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "integer"},
                            "b": {"type": "integer"},
                        },
                        "required": ["a", "b"],
                    },
                },
            }
        ]

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        return {"success": True, "value": int(payload["a"]) + int(payload["b"])}

    def format_tool_result(self, result: dict[str, Any], state: dict[str, Any]) -> str:
        return str(result["value"])


@pytest.mark.timeout(180)
def test_anthropic_model_discovery_and_tiny_non_streaming_request() -> None:
    config = _config()
    core = AgentCore()
    core.register_feature(RequestOptionsFeature)
    core.register_provider(
        AnthropicProvider,
        extensions=[AnthropicReasoningExtension, AnthropicUsageExtension],
    )
    session = core.add_message(
        core.create_session(),
        "user",
        "Reply with exactly: api hello",
        config=config,
    )

    _session, finals = core.send_request(
        session,
        {
            **config,
            "request_options": {"thinking": {"type": "disabled"}},
        },
    )

    assert finals and finals[-1]["content"].strip()
    assert finals[-1]["metadata"]["usage_prompt_tokens"] > 0


@pytest.mark.timeout(240)
def test_anthropic_streamed_reasoning_tool_loop() -> None:
    config = {
        **_config(),
        "request_options": {"thinking": {"type": "enabled", "budget_tokens": 1024}},
        "max_tokens": 1200,
    }
    core = AgentCore()
    core.register_feature(RequestOptionsFeature)
    core.register_provider(
        AnthropicProvider,
        extensions=[
            AnthropicToolsExtension,
            AnthropicReasoningExtension,
            AnthropicUsageExtension,
        ],
    )
    core.register_tool(AddTool)
    session = core.add_message(
        core.create_session(),
        "user",
        (
            "You must use the available add tool to add 2 and 3. "
            "Do not calculate the result yourself. After the tool returns, "
            "report its result."
        ),
        config=config,
    )

    first_event = None
    reasoning_parts: list[str] = []
    for event in core.send_request_stream(session, config):
        if event.get("type") == "partial":
            metadata = (event.get("message") or {}).get("metadata") or {}
            reasoning = metadata.get("reasoning")
            if isinstance(reasoning, str):
                reasoning_parts.append(reasoning)
        elif event.get("type") == "final":
            first_event = event

    assert first_event is not None
    calls = first_event["messages"][-1]["metadata"].get("tool_calls") or []
    assert calls and calls[0]["name"] == "add"
    assert "".join(reasoning_parts).strip()

    session = first_event["session"]
    tool_messages = core.execute_tool_calls(calls, config)
    for message in tool_messages:
        session = core.add_message(
            session,
            message["role"],
            message["content"],
            metadata=message.get("metadata"),
            tool_result=message.get("toolResult"),
            config=config,
        )

    final_event = None
    for event in core.send_request_stream(session, config):
        if event.get("type") == "final":
            final_event = event

    assert final_event is not None
    final = final_event["messages"][-1]
    assert final["content"].strip()
    assert (
        final["metadata"]["usage_turn_input_tokens_cumulative"]
        > final["metadata"]["usage_prompt_tokens"]
    )
