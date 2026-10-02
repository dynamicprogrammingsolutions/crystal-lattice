from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import pytest

from agent_core import AgentCore
from agent_core.tool_interop import DEFAULT_TOOL_INTEROP_REGISTRY

from embedded_claude_tools import (
    ClaudeLikeEditTool,
    ClaudeLikeGlobTool,
    ClaudeLikeGrepTool,
    ClaudeLikeReadTool,
    ClaudeLikeWebFetchTool,
    ClaudeLikeWriteTool,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def _api_key(name: str) -> str:
    load_dotenv(REPO_ROOT / ".env")
    value = os.getenv(name)
    if not value:
        pytest.skip(f"{name} is not configured")
    return value


def _anthropic_model(config: dict[str, Any]) -> str:
    override = os.getenv("ANTHROPIC_EMBEDDED_CLAUDE_TEST_MODEL")
    if override:
        return override
    from anthropic_plugins.provider import AnthropicProvider

    models = AnthropicProvider().get_models(config)
    for model in models:
        model_id = model.get("id")
        if isinstance(model_id, str) and "haiku" in model_id.lower():
            return model_id
    pytest.skip("Anthropic model discovery returned no Haiku model")


def _build_provider(
    provider_id: str,
) -> tuple[AgentCore, dict[str, Any]]:
    core = AgentCore()
    if provider_id == "openrouter":
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import (
            OpenRouterToolsExtension,
        )

        core.register_provider(
            OpenRouterProvider,
            extensions=[OpenRouterToolsExtension],
        )
        config = {
            "provider": "openrouter",
            "api_key": _api_key("OPENROUTER_API_KEY"),
            "base_url": os.getenv("OPENROUTER_BASE_URL")
            or "https://openrouter.ai/api/v1",
            "model": os.getenv("OPENROUTER_EMBEDDED_CLAUDE_TEST_MODEL")
            or "anthropic/claude-haiku-4.5",
            "timeout": 180,
        }
    elif provider_id == "anthropic":
        from anthropic_plugins.provider import AnthropicProvider
        from anthropic_plugins.tools_extension import AnthropicToolsExtension

        core.register_provider(
            AnthropicProvider,
            extensions=[AnthropicToolsExtension],
        )
        config = {
            "provider": "anthropic",
            "provider_transport": "requests",
            "api_key": _api_key("ANTHROPIC_API_KEY"),
            "base_url": os.getenv("ANTHROPIC_BASE_URL")
            or "https://api.anthropic.com",
            "timeout": 180,
            "max_tokens": 512,
        }
        config["model"] = _anthropic_model(config)
    else:  # pragma: no cover - fixed parametrization
        raise AssertionError(provider_id)

    for tool in (
        ClaudeLikeReadTool,
        ClaudeLikeWriteTool,
        ClaudeLikeEditTool,
        ClaudeLikeGlobTool,
        ClaudeLikeGrepTool,
        ClaudeLikeWebFetchTool,
    ):
        core.register_tool(tool)
    return core, config


def _run_turn(
    core: AgentCore,
    session: Any,
    config: dict[str, Any],
    prompt: str,
) -> tuple[Any, set[str]]:
    session = core.add_message(session, "user", prompt, config=config)
    used: set[str] = set()
    for _ in range(8):
        session, responses = core.send_request(session, config)
        assert responses
        metadata = responses[-1].get("metadata") or {}
        tool_calls = metadata.get("tool_calls") or []
        if not tool_calls:
            return session, used
        for call in tool_calls:
            name = call.get("name") if isinstance(call, dict) else None
            if not isinstance(name, str) or not name:
                name = DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(call).tool_name
            if name:
                used.add(name)
        for tool_message in core.execute_tool_calls(tool_calls, config):
            session = core.add_message(
                session,
                role=tool_message.get("role", "tool"),
                content=tool_message.get("content", ""),
                metadata=tool_message.get("metadata"),
                config=config,
            )
    pytest.fail("Claude-like provider tool loop did not settle within 8 rounds")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.parametrize(
    "provider_id",
    [
        pytest.param("openrouter", marks=pytest.mark.openrouter),
        pytest.param("anthropic", marks=pytest.mark.anthropic),
    ],
)
def test_provider_uses_embedded_claude_file_and_fetch_tools(
    provider_id: str,
    tmp_path: Path,
) -> None:
    core, config = _build_provider(provider_id)
    config = {
        **config,
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
    }
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        (
            "Use the specifically named tool when instructed. All file paths are "
            "bare workspace-relative paths under the configured working directory."
        ),
        config=config,
    )

    used: set[str] = set()
    session, turn_used = _run_turn(
        core,
        session,
        config,
        (
            "Call Write exactly once with file_path `provider-check.txt` and "
            "content exactly `CLAUDE_TOOL_MATRIX_OK`. Then briefly confirm."
        ),
    )
    used.update(turn_used)
    session, turn_used = _run_turn(
        core,
        session,
        config,
        (
            "Call Read exactly once with file_path `provider-check.txt`. "
            "Confirm that it contains CLAUDE_TOOL_MATRIX_OK."
        ),
    )
    used.update(turn_used)
    session, turn_used = _run_turn(
        core,
        session,
        config,
        (
            "Call WebFetch exactly once with url `https://www.python.org/`. "
            "Briefly report the returned page title."
        ),
    )
    used.update(turn_used)

    assert {"Write", "Read", "WebFetch"} <= used
    assert (tmp_path / "provider-check.txt").read_text(encoding="utf-8") == (
        "CLAUDE_TOOL_MATRIX_OK"
    )
    assert session.messages[-1].role == "assistant"
    assert session.messages[-1].content.strip()