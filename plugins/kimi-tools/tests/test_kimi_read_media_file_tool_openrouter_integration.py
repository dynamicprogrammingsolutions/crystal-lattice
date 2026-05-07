"""OpenRouter integration test for KimiReadMediaFileTool."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from agent_core.tool_interop import DEFAULT_TOOL_INTEROP_REGISTRY
from kimi_tools import KimiReadMediaFileTool


MODEL = os.getenv("OPENROUTER_MODEL_KIMI_READ_MEDIA", "moonshotai/kimi-k2.5")
EXPECTED_TEXT = "CODEX VIEW IMAGE 7391"
FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "codex-tools"
    / "tests"
    / "fixtures"
    / "view_image_text.png"
)


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
        "system",
        "Use the ReadMediaFile tool when an image file must be inspected. Do not answer from memory.",
    )
    session = core.add_message(
        session,
        "user",
        (
            "Use ReadMediaFile to inspect this exact local image path: "
            f"{FIXTURE_PATH}. The image contains written text. After using the tool, "
            "reply with exactly the written text and nothing else."
        ),
        config=config,
    )
    saw_read_media = False
    responses: List[Dict[str, Any]] = []

    for _ in range(max_iterations):
        session, responses = core.send_request(session, config)
        assert responses, "expected assistant response"

        tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
        if not isinstance(tool_calls, list) or not tool_calls:
            return session, responses, saw_read_media

        for call in tool_calls:
            inspected = DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(call)
            if inspected.tool_name == "ReadMediaFile":
                saw_read_media = True

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
@pytest.mark.openrouter
def test_openrouter_kimi_k2_5_reads_text_via_read_media_file() -> None:
    _load_env()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    if not FIXTURE_PATH.exists():
        pytest.skip(f"image fixture not found: {FIXTURE_PATH}")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import (
            OpenRouterToolsExtension,
        )
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(KimiReadMediaFileTool)

    config = {
        "model": MODEL,
        "api_key": api_key,
        "base_url": os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "working_directory": str(FIXTURE_PATH.parent),
        "allowed_paths": [str(FIXTURE_PATH.parent)],
        "kimi_read_media_capabilities": ["image_in"],
        "request_options": {
            "max_tokens": 512,
            "tool_choice": "auto",
        },
    }

    _session, responses, saw_read_media = _run_tool_loop(core, config)

    assert saw_read_media, "expected the model to call ReadMediaFile"
    final_text = responses[-1].get("content") or ""
    assert EXPECTED_TEXT in final_text
