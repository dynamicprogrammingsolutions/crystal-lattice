from __future__ import annotations

from typing import Any

from agent_core import AgentCore, Session
from plugins.request_options_feature import RequestOptionsFeature

from anthropic_plugins import (
    AnthropicPromptCachingExtension,
    AnthropicProvider,
    AnthropicReasoningControlsExtension,
    AnthropicReasoningExtension,
    AnthropicToolsExtension,
    AnthropicUsageExtension,
)


class Dumpable:
    def __init__(self, value: dict[str, Any]):
        self.value = value

    def model_dump(self, **_: Any) -> dict[str, Any]:
        return self.value


class ScriptedMessages:
    responses: list[Any] = []
    calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        type(self).calls.append(kwargs)
        return type(self).responses.pop(0)


class ScriptedModels:
    def list(self, **_: Any) -> list[Dumpable]:
        return [Dumpable({"id": "scripted", "display_name": "Scripted"})]


class ScriptedClient:
    def __init__(self):
        self.messages = ScriptedMessages()
        self.models = ScriptedModels()

    def close(self) -> None:
        return None


class ScriptedAnthropicProvider(AnthropicProvider):
    def _client(self, config: dict[str, Any]) -> ScriptedClient:
        return ScriptedClient()


def _core(*, extensions: list[type] | None = None) -> AgentCore:
    core = AgentCore()
    core.register_feature(RequestOptionsFeature)
    core.register_provider(
        ScriptedAnthropicProvider,
        extensions=(
            extensions
            if extensions is not None
            else [
                AnthropicToolsExtension,
                AnthropicReasoningExtension,
                AnthropicUsageExtension,
            ]
        ),
    )
    return core


def _message(
    *,
    content: list[dict[str, Any]],
    usage: dict[str, Any],
    stop_reason: str = "end_turn",
) -> Dumpable:
    return Dumpable(
        {
            "id": "msg_scripted",
            "model": "scripted",
            "role": "assistant",
            "content": content,
            "stop_reason": stop_reason,
            "usage": usage,
        }
    )


def test_provider_operates_without_extensions() -> None:
    ScriptedMessages.responses = [
        _message(
            content=[{"type": "text", "text": "plain"}],
            usage={"input_tokens": 1, "output_tokens": 1},
        )
    ]
    core = _core(extensions=[])
    config = {"provider": "anthropic", "model": "scripted", "api_key": "test"}
    session = core.add_message(core.create_session(), "user", "hello", config=config)

    new_session, finals = core.send_request(session, config)

    assert finals == [
        {
            "role": "assistant",
            "content": "plain",
            "metadata": {
                "anthropic": {
                    "id": "msg_scripted",
                    "model": "scripted",
                    "stop_reason": "end_turn",
                },
                "anthropic_usage": {"input_tokens": 1, "output_tokens": 1},
                "native_indices": [1],
            },
        }
    ]
    assert len(new_session.metadata["native_messages"]) == 2


def test_reasoning_controls_and_prompt_caching_run_through_core_stack() -> None:
    ScriptedMessages.calls = []
    ScriptedMessages.responses = [
        _message(
            content=[{"type": "text", "text": "configured"}],
            usage={"input_tokens": 1, "output_tokens": 1},
        )
    ]
    core = _core(
        extensions=[
            AnthropicReasoningControlsExtension,
            AnthropicPromptCachingExtension,
            AnthropicUsageExtension,
        ]
    )
    config = {
        "provider": "anthropic",
        "model": "scripted",
        "api_key": "test",
        "capabilities": {
            "anthropic_reasoning_controls": True,
            "prompt_caching": True,
        },
        "anthropic_reasoning_capabilities": {
            "thinking_types": ["adaptive"],
            "effort_levels": ["low", "high"],
        },
        "anthropic_reasoning_mode": "adaptive",
        "anthropic_reasoning_effort": "high",
        "anthropic_reasoning_display": "summarized",
        "prompt_cache_ttl": "1h",
    }
    session = core.add_message(
        core.create_session(),
        "user",
        "hello",
        config=config,
    )

    _session, finals = core.send_request(session, config)

    assert finals[-1]["content"] == "configured"
    request = ScriptedMessages.calls[-1]
    assert request["thinking"] == {
        "type": "adaptive",
        "display": "summarized",
    }
    assert request["output_config"] == {"effort": "high"}
    assert request["cache_control"] == {"type": "ephemeral", "ttl": "1h"}


def test_reasoning_controls_auto_enable_from_selected_model_fallback() -> None:
    ScriptedMessages.calls = []
    ScriptedMessages.responses = [
        _message(
            content=[{"type": "text", "text": "configured"}],
            usage={"input_tokens": 1, "output_tokens": 1},
        )
    ]
    core = _core(extensions=[AnthropicReasoningControlsExtension])
    config = {
        "provider": "anthropic",
        "model": "claude-sonnet-5",
        "api_key": "test",
        "anthropic_reasoning_mode": "adaptive",
        "anthropic_reasoning_effort": "xhigh",
    }
    session = core.add_message(
        core.create_session(),
        "user",
        "hello",
        config=config,
    )

    core.send_request(session, config)

    request = ScriptedMessages.calls[-1]
    assert request["thinking"] == {"type": "adaptive"}
    assert request["output_config"] == {"effort": "xhigh"}


def test_prompt_caching_extension_is_inactive_without_capability_tag() -> None:
    ScriptedMessages.calls = []
    ScriptedMessages.responses = [
        _message(
            content=[{"type": "text", "text": "plain"}],
            usage={"input_tokens": 1, "output_tokens": 1},
        )
    ]
    core = _core(extensions=[AnthropicPromptCachingExtension])
    config = {
        "provider": "anthropic",
        "model": "scripted",
        "api_key": "test",
    }
    session = core.add_message(
        core.create_session(),
        "user",
        "hello",
        config=config,
    )

    core.send_request(session, config)

    assert "cache_control" not in ScriptedMessages.calls[-1]


def test_full_stack_persists_reasoning_usage_and_native_history() -> None:
    ScriptedMessages.responses = [
        _message(
            content=[
                {"type": "thinking", "thinking": "inspect", "signature": "sig"},
                {"type": "text", "text": "answer"},
            ],
            usage={
                "input_tokens": 5,
                "output_tokens": 3,
                "output_tokens_details": {"thinking_tokens": 2},
            },
        ),
        _message(
            content=[{"type": "text", "text": "follow-up"}],
            usage={"input_tokens": 8, "output_tokens": 2},
        ),
    ]
    core = _core()
    config = {
        "provider": "anthropic",
        "model": "scripted",
        "api_key": "test",
        "request_options": {"thinking": {"type": "enabled", "budget_tokens": 128}},
    }
    session = core.add_message(core.create_session(), "user", "question", config=config)

    session, finals = core.send_request(session, config)
    metadata = finals[0]["metadata"]

    assert metadata["reasoning"] == "inspect"
    assert metadata["anthropic_reasoning_blocks"][0]["signature"] == "sig"
    assert metadata["usage_prompt_tokens"] == 5
    assert metadata["usage_reasoning_tokens"] == 2

    reloaded = Session.from_dict(session.to_dict())
    reloaded = core.add_message(reloaded, "user", "again", config=config)
    reloaded, follow_up = core.send_request(reloaded, config)

    assert follow_up[0]["content"] == "follow-up"
    native = reloaded.metadata["native_messages"]
    first_assistant = native[1]
    assert first_assistant["content"][0] == {
        "type": "thinking",
        "thinking": "inspect",
        "signature": "sig",
    }
    assert native[-1]["_metadata"]["usage_input_tokens_cumulative"] == 13
