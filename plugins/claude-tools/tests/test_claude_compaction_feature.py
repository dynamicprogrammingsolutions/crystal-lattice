# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORE_PY = ROOT / "core/python"
PLUGIN_SRC = ROOT / "plugins/claude-tools/src"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
if str(PLUGIN_SRC) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SRC))

from agent_core import AgentCore, Message, Session  # noqa: E402
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: E402
from claude_tools.claude_compaction_feature import (  # noqa: E402
    _LOCAL_COMMAND_ARTIFACT,
    _NO_RESPONSE_REQUESTED,
    build_compact_summary_text,
    build_compacted_session,
    build_compaction_prompt,
    build_compaction_session,
    extract_prompt_sections,
    extract_summary_sections,
    validate_summary_text,
)


def _fixture(name: str) -> dict:
    path = (
        Path(__file__).resolve().parents[1]
        / "investigation"
        / "fixtures"
        / "compaction"
        / f"{name}.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _summary_body_from_fixture(fixture: dict) -> str:
    text = fixture["compact_summary_text"]
    _, summary_and_footer = text.split("\n\nSummary:\n", 1)
    summary_body, _footer = summary_and_footer.split(
        "\n\nIf you need specific details from before compaction",
        1,
    )
    return summary_body


def test_prompt_matches_observed_fixture() -> None:
    fixture = _fixture("success-basic")

    assert build_compaction_prompt() == fixture["compact_request_prompt_text"]
    assert (
        extract_prompt_sections(build_compaction_prompt())
        == fixture["compact_request_prompt_sections"]
    )


def test_build_compaction_session_appends_prompt_to_last_user_message() -> None:
    fixture = _fixture("success-basic")
    session = Session(
        session_id="session-1",
        messages=[
            Message(role="user", content="Answer exactly ONE."),
            Message(role="assistant", content="Need more context."),
            Message(role="user", content="Answer exactly TWO."),
            Message(role="assistant", content="Still need more context."),
            Message(role="user", content="Answer exactly THREE."),
        ],
        metadata={"native_messages": [{"role": "user", "content": "old"}]},
    )

    compacted = build_compaction_session(
        session,
        prompt_text=fixture["compact_request_prompt_text"],
    )

    assert "native_messages" not in (compacted.metadata or {})
    assert compacted.messages[-1].content == (
        "Answer exactly THREE.\n" + fixture["compact_request_prompt_text"]
    )


def test_summary_wrapper_matches_observed_fixture() -> None:
    fixture = _fixture("success-basic")
    summary_body = _summary_body_from_fixture(fixture)

    wrapped = build_compact_summary_text(
        summary_body,
        transcript_path="<PROJECT_TRANSCRIPT>",
    )

    assert wrapped == fixture["compact_summary_text"]


def test_fixture_summaries_pass_validation_for_basic_and_tool_history_cases() -> None:
    for name in ("success-basic", "success-tool-history", "success-prior-summary"):
        fixture = _fixture(name)
        summary_body = _summary_body_from_fixture(fixture)
        validate_summary_text(summary_body)
        assert (
            extract_summary_sections(summary_body)
            == fixture["compact_summary_sections"]
        )


def test_compacted_session_rebuilds_native_history_with_claude_style_artifacts() -> (
    None
):
    fixture = _fixture("success-basic")
    core = AgentCore()
    core.register_provider(EchoOpenAILikeProvider)

    config = {"provider": "echo_openai_like", "model": "test-model"}
    session = core.create_session("compaction-test")
    session = core.add_message(session, "user", "Answer exactly ONE.", config=config)
    session = core.add_message(session, "assistant", "ONE", config=config)
    session = core.add_message(session, "user", "Answer exactly TWO.", config=config)

    compacted = build_compacted_session(
        core,
        session,
        config,
        fixture["compact_summary_text"],
    )
    native_messages = compacted.metadata["native_messages"]

    assert [message.role for message in compacted.messages] == [
        "user",
        "user",
        "assistant",
    ]
    assert [message["role"] for message in native_messages] == [
        "user",
        "user",
        "assistant",
    ]
    assert compacted.messages[0].content == fixture["compact_summary_text"]
    assert native_messages[1]["content"] == _LOCAL_COMMAND_ARTIFACT
    assert native_messages[2]["content"] == _NO_RESPONSE_REQUESTED
    summary_metadata = compacted.messages[0].metadata or {}
    assert summary_metadata["claude_compaction"]["is_compact_summary"] is True
    assert (
        summary_metadata["claude_compaction"]["is_visible_in_transcript_only"] is True
    )


def test_agent_plugin_bundle_registers_claude_compaction_as_feature() -> None:
    payload = json.loads(
        (ROOT / "plugins/claude-tools/agent_plugin.json").read_text(encoding="utf-8")
    )

    assert (
        "claude_tools.claude_compaction_feature.ClaudeCompactionFeature"
        in payload["entries"]
    )
    assert (
        payload["kinds"][
            "claude_tools.claude_compaction_feature.ClaudeCompactionFeature"
        ]
        == "features"
    )
