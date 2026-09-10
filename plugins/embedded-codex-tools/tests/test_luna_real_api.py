from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from agent_core.tool_interop import DEFAULT_TOOL_INTEROP_REGISTRY

from embedded_codex_tools import (
    CodexLikeApplyPatchTool,
    CodexLikeCurlTool,
    CodexLikeFindTool,
    CodexLikeRgTool,
    CodexLikeSedTool,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
CODEX_INSTRUCTIONS = (
    REPO_ROOT
    / "application/python/agent_terminal_app/default_config/codex"
    / "gpt-5.6-luna/instructions_default.md"
)


def _build_core() -> AgentCore:
    try:
        from openai_responses_plugins.openai_responses_provider import (
            OpenAIResponsesProvider,
        )
        from openai_responses_plugins.openai_responses_reasoning_extension import (
            OpenAIResponsesReasoningExtension,
        )
        from openai_responses_plugins.openai_responses_tools_extension import (
            OpenAIResponsesToolsExtension,
        )
    except ImportError as error:
        pytest.skip(f"OpenAI Responses plugin is not installed: {error}")

    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[
            OpenAIResponsesReasoningExtension,
            OpenAIResponsesToolsExtension,
        ],
    )
    for tool in (
        CodexLikeSedTool,
        CodexLikeRgTool,
        CodexLikeFindTool,
        CodexLikeCurlTool,
        CodexLikeApplyPatchTool,
    ):
        core.register_tool(tool)
    return core


def _run_tool_loop(
    core: AgentCore,
    session: Any,
    config: dict[str, Any],
) -> tuple[Any, set[str]]:
    used: set[str] = set()
    for _ in range(10):
        session, responses = core.send_request(session, config)
        assert responses
        metadata = responses[-1].get("metadata") or {}
        tool_calls = metadata.get("tool_calls") or []
        if not tool_calls:
            return session, used
        for call in tool_calls:
            used.add(DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(call).tool_name or "")
        for tool_message in core.execute_tool_calls(tool_calls, config):
            session = core.add_message(
                session,
                role=tool_message.get("role", "tool"),
                content=tool_message.get("content", ""),
                metadata=tool_message.get("metadata"),
                config=config,
            )
    pytest.fail("Luna Codex-like tool loop did not settle within 10 rounds")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openai
def test_luna_uses_complete_embedded_codex_tool_set(tmp_path: Path) -> None:
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY is not configured")

    (tmp_path / "docs").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / "notes.txt").write_text(
        "one\ntwo\nORBITAL_MARKER\nfour\n",
        encoding="utf-8",
    )
    (tmp_path / "docs/guide.md").write_text(
        "ORBITAL_MARKER documentation\n",
        encoding="utf-8",
    )
    (tmp_path / "config/settings.txt").write_text(
        "mode=old\n",
        encoding="utf-8",
    )

    core = _build_core()
    model = os.getenv("OPENAI_EMBEDDED_CODEX_TEST_MODEL") or "gpt-5.6-luna"
    config = {
        "model": model,
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "auth_mode": "api",
        "timeout": 180,
        "reasoning_effort": "low",
        "reasoning_summary": "concise",
        "working_directory": str(tmp_path),
        "max_patch_bytes": 64 * 1024,
    }
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        (
            CODEX_INSTRUCTIONS.read_text(encoding="utf-8")
            + "\n\nUse only the provided command-specific tools in this synthetic "
            f"workspace: {tmp_path}. Do not access parent paths or credentials."
        ),
    )
    session = core.add_message(
        session,
        "user",
        (
            "Complete every numbered operation using the specifically named tool: "
            "(1) call sed to read notes.txt lines 2 through 4; "
            "(2) call rg to find ORBITAL_MARKER recursively; "
            "(3) call find to list Markdown files under docs; "
            "(4) call apply_patch to change config/settings.txt from mode=old to "
            "mode=new; "
            "(5) call curl to fetch https://www.python.org/ and identify its title. "
            "After all tool results, briefly confirm completion."
        ),
    )

    final_session, used = _run_tool_loop(core, session, config)
    assert {"sed", "rg", "find", "apply_patch", "curl"} <= used
    assert (tmp_path / "config/settings.txt").read_text(encoding="utf-8") == (
        "mode=new\n"
    )
    assert final_session.messages[-1].role == "assistant"
    assert final_session.messages[-1].content.strip()