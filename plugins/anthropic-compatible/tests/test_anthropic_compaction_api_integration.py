from __future__ import annotations

import os
import uuid
from typing import Any

import pytest

from agent_core import AgentCore, Session

from anthropic_plugins import (
    AnthropicCompactionExtension,
    AnthropicProvider,
    AnthropicUsageExtension,
)


pytestmark = [
    pytest.mark.integration,
    pytest.mark.api,
    pytest.mark.anthropic,
    pytest.mark.slow_integration,
]


def _api_key() -> str:
    value = os.getenv("ANTHROPIC_API_KEY")
    if not value:
        pytest.skip("ANTHROPIC_API_KEY is required")
    return value


def _send_stream(
    core: AgentCore,
    session: Session,
    config: dict[str, Any],
) -> tuple[Session, list[dict[str, Any]]]:
    final_event = None
    for event in core.send_request_stream(session, config):
        if event.get("type") == "final":
            final_event = event
    assert final_event is not None
    return final_event["session"], final_event["messages"]


@pytest.mark.timeout(600)
def test_official_streaming_compaction_persists_and_continues() -> None:
    model = os.getenv("ANTHROPIC_COMPACTION_TEST_MODEL", "claude-sonnet-5")
    secret = f"ORCHID-{uuid.uuid4().hex[:12]}"
    core = AgentCore()
    core.register_provider(
        AnthropicProvider,
        extensions=[
            AnthropicCompactionExtension,
            AnthropicUsageExtension,
        ],
    )
    config = {
        "provider": "anthropic",
        "api_key": _api_key(),
        "base_url": "https://api.anthropic.com",
        "model": model,
        "timeout": 300,
        "max_retries": 1,
        "max_tokens": 512,
        "capabilities": {"anthropic_compaction": True},
        "enable_anthropic_compaction": True,
        "anthropic_compaction_trigger_tokens": 50000,
        "anthropic_compaction_instructions": (
            "Preserve explicitly labeled durable codes and final user requests."
        ),
    }
    filler = "context " * 65000
    prompt = (
        f"The durable code is {secret}. Remember it exactly.\n\n"
        f"{filler}\n\n"
        "Reply with exactly READY."
    )
    session = core.add_message(
        core.create_session(),
        "user",
        prompt,
        config=config,
    )

    session, first = _send_stream(core, session, config)

    assert first
    first_metadata = first[-1]["metadata"]
    assert first_metadata["anthropic_compaction"]["occurred"] is True
    assert first_metadata["usage_compaction_iterations"] >= 1
    native = session.metadata["native_messages"]
    compaction_blocks = [
        block
        for message in native
        if isinstance(message, dict) and message.get("role") == "assistant"
        for content in [message.get("content")]
        if isinstance(content, list)
        for block in content
        if isinstance(block, dict) and block.get("type") == "compaction"
    ]
    assert compaction_blocks
    encrypted_values = [
        value
        for block in compaction_blocks
        for value in [block.get("encrypted_content")]
        if isinstance(value, str) and value
    ]
    assert all(value not in repr(first_metadata) for value in encrypted_values)

    reloaded = Session.from_dict(session.to_dict())
    reloaded = core.add_message(
        reloaded,
        "user",
        "What is the durable code? Reply with only the code.",
        config=config,
    )
    reloaded, second = core.send_request(reloaded, config)

    assert second
    assert secret in str(second[-1]["content"])
    replayed_blocks = [
        block
        for message in reloaded.metadata["native_messages"]
        if isinstance(message, dict) and message.get("role") == "assistant"
        for content in [message.get("content")]
        if isinstance(content, list)
        for block in content
        if isinstance(block, dict) and block.get("type") == "compaction"
    ]
    assert replayed_blocks[: len(compaction_blocks)] == compaction_blocks
