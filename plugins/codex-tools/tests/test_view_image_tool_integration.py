from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from agent_core.tool_interop import DEFAULT_TOOL_INTEROP_REGISTRY
from codex_tools import ViewImageTool


EXPECTED_TEXT = "CODEX VIEW IMAGE 7391"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "view_image_text.png"


def _load_env() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")


def _run_tool_loop(
    core: AgentCore,
    config: Dict[str, Any],
    *,
    max_iterations: int = 5,
) -> Tuple[Any, List[Dict[str, Any]], bool]:
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Use the view_image tool to inspect this exact local image path: "
            f"{FIXTURE_PATH}. The image contains written text. After using the tool, "
            "reply with exactly the written text and nothing else."
        ),
        config=config,
    )
    saw_view_image = False
    responses: List[Dict[str, Any]] = []

    for _ in range(max_iterations):
        session, responses = core.send_request(session, config)
        assert responses, "expected assistant response"

        tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
        if not isinstance(tool_calls, list) or not tool_calls:
            return session, responses, saw_view_image

        for call in tool_calls:
            inspected = DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(call)
            if inspected.tool_name == "view_image":
                saw_view_image = True

        tool_messages = core.execute_tool_calls(tool_calls, config)
        assert tool_messages, "expected tool execution results"
        for tool_message in tool_messages:
            session = core.add_message(
                session,
                role=tool_message.get("role", "tool"),
                content=tool_message.get("content", ""),
                metadata=tool_message.get("metadata"),
                config=config,
                multipart_content=tool_message.get("multipartContent"),
            )

    pytest.fail(f"tool loop did not settle within {max_iterations} iterations")


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_gpt_5_4_mini_reads_text_via_view_image() -> None:
    _load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    from openai_responses_plugins.openai_responses_provider import (
        OpenAIResponsesProvider,
    )
    from openai_responses_plugins.openai_responses_tools_extension import (
        OpenAIResponsesToolsExtension,
    )
    from plugins.request_options_feature import RequestOptionsFeature

    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesToolsExtension],
    )
    core.register_feature(RequestOptionsFeature)
    core.register_tool(ViewImageTool)

    config = {
        "model": "gpt-5.4-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 180,
        "working_directory": str(FIXTURE_PATH.parent),
        "allowed_paths": [str(FIXTURE_PATH.parent)],
        "request_options": {
            "max_output_tokens": 512,
            "tool_choice": "auto",
        },
    }

    _session, responses, saw_view_image = _run_tool_loop(core, config)

    assert saw_view_image, "expected the model to call view_image"
    assert EXPECTED_TEXT in (responses[-1].get("content") or "")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_gpt_5_4_mini_reads_text_via_view_image() -> None:
    _load_env()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    from openrouter_plugins.openrouter_provider import OpenRouterProvider
    from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
    from plugins.request_options_feature import RequestOptionsFeature

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(ViewImageTool)

    config = {
        "model": "openai/gpt-5.4-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
        "timeout": 180,
        "working_directory": str(FIXTURE_PATH.parent),
        "allowed_paths": [str(FIXTURE_PATH.parent)],
        "request_options": {
            "max_tokens": 512,
            "tool_choice": "auto",
        },
    }

    _session, responses, saw_view_image = _run_tool_loop(core, config)

    assert saw_view_image, "expected the model to call view_image"
    assert EXPECTED_TEXT in (responses[-1].get("content") or "")
