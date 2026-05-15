"""Ollama OpenAI-compatible integration test for ClaudeReadTool."""

from __future__ import annotations

# ruff: noqa: E402

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
import requests

ROOT = Path(__file__).resolve().parents[3]
for rel in (
    "core/python",
    "plugins/claude-tools/src",
    "plugins/tool-compat-shared/src",
    "plugins/reference-openai-compatible-provider/src",
):
    path = ROOT / rel
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from agent_core import AgentCore  # noqa: E402
from agent_core.tool_interop import DEFAULT_TOOL_INTEROP_REGISTRY  # noqa: E402
from agent_core.tool_result_payloads import (
    FORMAT_ANTHROPIC_MESSAGES,
    TOOL_RESULT_FIELD,
)  # noqa: E402
from claude_tools import ClaudeReadTool  # noqa: E402


MODEL = os.getenv("OLLAMA_OPENAI_CLAUDE_READ_MODEL", "glm-5:cloud")
BASE_URL = os.getenv("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1")
TIMEOUT = float(os.getenv("OLLAMA_OPENAI_TIMEOUT", "180"))
EXPECTED_TEXT = "CLAUDE_READ_OLLAMA_SENTINEL_7391"


def _ollama_available(base_url: str) -> bool:
    try:
        response = requests.get(f"{base_url.rstrip('/')}/models", timeout=3)
        return bool(response.ok)
    except Exception:
        return False


def _run_tool_loop(
    core: AgentCore,
    config: Dict[str, Any],
    fixture_path: Path,
    *,
    max_iterations: int = 5,
) -> Tuple[Any, List[Dict[str, Any]], bool, List[Dict[str, Any]]]:
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You must use the Read tool when asked to inspect a local file path. Do not answer from memory.",
    )
    session = core.add_message(
        session,
        "user",
        (
            "Use the Read tool to read this exact local file path: "
            f"{fixture_path}. After using the tool, reply with exactly the sentinel "
            "text from the file and nothing else."
        ),
        config=config,
    )
    saw_read = False
    responses: List[Dict[str, Any]] = []
    tool_messages_seen: List[Dict[str, Any]] = []

    for _ in range(max_iterations):
        session, responses = core.send_request(session, config)
        assert responses, "expected assistant response"

        tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
        if not isinstance(tool_calls, list) or not tool_calls:
            return session, responses, saw_read, tool_messages_seen

        for call in tool_calls:
            inspected = DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(call)
            if inspected.tool_name == "Read":
                saw_read = True

        tool_messages = core.execute_tool_calls(tool_calls, config)
        assert tool_messages, "expected tool execution results"
        tool_messages_seen.extend(tool_messages)
        for tool_message in tool_messages:
            session = core.add_message(
                session,
                role=tool_message.get("role", "tool"),
                content=tool_message.get("content", ""),
                metadata=tool_message.get("metadata"),
                config=config,
                tool_result=tool_message.get(TOOL_RESULT_FIELD),
            )

    pytest.fail(f"tool loop did not settle within {max_iterations} iterations")


@pytest.mark.integration
@pytest.mark.ollama
def test_ollama_glm_5_cloud_reads_text_via_claude_read(tmp_path: Path) -> None:
    if not _ollama_available(BASE_URL):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    try:
        from plugins.request_options_feature import RequestOptionsFeature
        from reference_openai_compatible_provider.provider import (
            OpenAICompatibleProvider,
        )
        from reference_openai_compatible_provider.tools_extension import (
            OpenAICompatibleToolsExtension,
        )
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Ollama test dependencies not installed: {exc}")

    fixture_path = tmp_path / "sentinel.txt"
    fixture_path.write_text(EXPECTED_TEXT + "\n", encoding="utf-8")

    core = AgentCore()
    core.register_provider(
        OpenAICompatibleProvider,
        extensions=[OpenAICompatibleToolsExtension],
    )
    core.register_feature(RequestOptionsFeature)
    core.register_tool(ClaudeReadTool)

    config = {
        "model": MODEL,
        "base_url": BASE_URL,
        "timeout": TIMEOUT,
        "temperature": 0.0,
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "request_options": {
            "temperature": 0.0,
            "tool_choice": "auto",
        },
    }

    _session, responses, saw_read, tool_messages = _run_tool_loop(
        core, config, fixture_path
    )

    assert saw_read, "expected the model to call Read"
    read_tool_results = [
        message.get(TOOL_RESULT_FIELD)
        for message in tool_messages
        if (message.get("metadata") or {}).get("tool_name") == "Read"
    ]
    assert read_tool_results
    assert read_tool_results[-1]["format"] == FORMAT_ANTHROPIC_MESSAGES
    assert EXPECTED_TEXT in (responses[-1].get("content") or "")
