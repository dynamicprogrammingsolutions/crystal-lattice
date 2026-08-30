from __future__ import annotations

from typing import Any

from agent_core import AgentCore, Session

from anthropic_plugins import (
    AnthropicProvider,
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
        "enable_reasoning": True,
        "reasoning_budget_tokens": 128,
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
