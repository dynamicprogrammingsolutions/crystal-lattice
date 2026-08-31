from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import AgentCore, Session
from plugins.request_options_feature import RequestOptionsFeature

from anthropic_plugins import (
    AnthropicProvider,
    AnthropicReasoningExtension,
    AnthropicToolsExtension,
    AnthropicUsageExtension,
)


def _config(**overrides: Any) -> dict[str, Any]:
    return {
        "provider": "anthropic",
        "base_url": os.getenv("OLLAMA_ANTHROPIC_BASE_URL", "http://localhost:11434"),
        "model": os.getenv("OLLAMA_ANTHROPIC_MODEL", "qwen3:0.6b"),
        "api_key": "ollama",
        "timeout": float(os.getenv("OLLAMA_ANTHROPIC_TIMEOUT", "60")),
        "max_tokens": 160,
        **overrides,
    }


def _require_ollama(config: dict[str, Any]) -> None:
    url = f"{str(config['base_url']).rstrip('/')}/api/tags"
    try:
        with urlopen(Request(url), timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        pytest.skip("local Ollama endpoint is not reachable")
    names = {
        model.get("name")
        for model in payload.get("models", [])
        if isinstance(model, dict)
    }
    if config["model"] not in names:
        pytest.skip(f"local Ollama model {config['model']} is not installed")


def _core(*, tool: type | None = None) -> AgentCore:
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
    if tool is not None:
        core.register_tool(tool)
    return core


class AddTool:
    name = "anthropic_test_add"
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
                    "description": "Add two integers. Always use this for arithmetic.",
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


@pytest.mark.integration
@pytest.mark.ollama
def test_ollama_ordinary_streaming_usage_and_reload() -> None:
    config = _config(
        request_options={"thinking": {"type": "disabled"}},
        max_tokens=64,
    )
    _require_ollama(config)
    core = _core()
    session = core.add_message(
        core.create_session(),
        "user",
        "Reply with exactly: local hello",
        config=config,
    )

    partial_text: list[str] = []
    final_event = None
    for event in core.send_request_stream(session, config):
        if event.get("type") == "partial":
            partial_text.append(str((event.get("message") or {}).get("content") or ""))
        elif event.get("type") == "final":
            final_event = event

    assert final_event is not None
    finals = final_event["messages"]
    assert finals[-1]["content"].strip()
    assert "".join(partial_text).strip()
    assert finals[-1]["metadata"]["usage_prompt_tokens"] > 0
    assert finals[-1]["metadata"]["usage_completion_tokens"] > 0
    reloaded = Session.from_dict(final_event["session"].to_dict())
    assert reloaded.metadata["native_messages"][-1]["role"] == "assistant"


@pytest.mark.integration
@pytest.mark.ollama
def test_ollama_reasoning_stream_is_visible_and_preserved() -> None:
    config = _config(
        request_options={
            "thinking": {"type": "enabled", "budget_tokens": 64},
            "output_config": {"effort": "low"},
        },
    )
    _require_ollama(config)
    core = _core()
    session = core.add_message(
        core.create_session(),
        "user",
        "What is 2 + 2? Answer briefly.",
        config=config,
    )

    reasoning_parts: list[str] = []
    final_event = None
    for event in core.send_request_stream(session, config):
        if event.get("type") == "partial":
            metadata = (event.get("message") or {}).get("metadata") or {}
            reasoning = metadata.get("reasoning")
            if isinstance(reasoning, str):
                reasoning_parts.append(reasoning)
        elif event.get("type") == "final":
            final_event = event

    assert final_event is not None
    final = final_event["messages"][-1]
    assert "".join(reasoning_parts).strip()
    assert final["metadata"]["reasoning"].strip()
    native = final_event["session"].metadata["native_messages"][-1]
    assert any(
        block.get("type") == "thinking"
        for block in native["content"]
        if isinstance(block, dict)
    )


@pytest.mark.integration
@pytest.mark.ollama
def test_ollama_tool_round_and_turn_cumulative_usage() -> None:
    config = _config(request_options={"thinking": {"type": "disabled"}})
    _require_ollama(config)
    core = _core(tool=AddTool)
    session = core.add_message(
        core.create_session(),
        "user",
        "Use the add tool to add 2 and 3. Do not calculate it yourself.",
        config=config,
    )

    session, first = core.send_request(session, config)
    calls = first[-1]["metadata"].get("tool_calls") or []
    assert calls and calls[0]["name"] == "add"

    tool_messages = core.execute_tool_calls(calls, config)
    assert tool_messages and tool_messages[0]["content"] == "5"
    for message in tool_messages:
        session = core.add_message(
            session,
            message["role"],
            message["content"],
            metadata=message.get("metadata"),
            tool_result=message.get("toolResult"),
            config=config,
        )

    session, second = core.send_request(session, config)
    metadata = second[-1]["metadata"]
    assert second[-1]["content"].strip()
    assert (
        metadata["usage_turn_input_tokens_cumulative"] > metadata["usage_prompt_tokens"]
    )
    native_messages = session.metadata.get("native_messages")
    assert isinstance(native_messages, list)
    native_blocks = [
        block
        for message in native_messages
        if isinstance(message, dict)
        for content in [message.get("content")]
        if isinstance(content, list)
        for block in content
        if isinstance(block, dict)
    ]
    assert any(block.get("type") == "tool_result" for block in native_blocks)


@pytest.mark.integration
@pytest.mark.ollama
def test_agent_application_loads_bundle_and_completes_request(tmp_path: Path) -> None:
    config = _config(
        request_options={"thinking": {"type": "disabled"}},
        max_tokens=64,
    )
    _require_ollama(config)
    plugin_root = Path(__file__).resolve().parents[1]
    request_options_root = plugin_root.parent / "feature-request-options"
    app_config = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "plugins": [f"path:{plugin_root}", f"path:{request_options_root}"],
        "providers": {"anthropic_local": config},
        "agents": {"default": {"provider": "anthropic_local"}},
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(app_config), encoding="utf-8")
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    core, base_config, session = app.create_session("default")
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: application hello",
        config=base_config,
    )
    app.save_session(session)

    events = list(
        app.send_request(core, session, base_config, overrides=None, stream=False)
    )

    checkpoints = [
        event for event in events if event.get("type") == "session_checkpoint"
    ]
    assert checkpoints
    saved = checkpoints[-1]["session"]
    assert saved.messages[-1].role == "assistant"
    assert str(saved.messages[-1].content).strip()
