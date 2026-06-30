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

import pytest

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
    _COMPACTION_MODEL_KEY,
    _LOCAL_COMMAND_ARTIFACT,
    _NO_RESPONSE_REQUESTED,
    ClaudeCompactionFeature,
    build_compact_summary_text,
    build_compacted_session,
    build_compaction_prompt,
    build_compaction_request_session,
    extract_prompt_sections,
    extract_summary_sections,
    validate_summary_text,
    write_pre_compaction_transcript,
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


def _make_session(has_system: bool) -> Session:
    messages = [
        Message(role="user", content="Answer exactly ONE."),
        Message(role="assistant", content="ONE"),
        Message(role="user", content="Answer exactly TWO."),
        Message(role="assistant", content="TWO"),
        Message(role="user", content="Answer exactly THREE."),
        Message(role="assistant", content="THREE"),
    ]
    if has_system:
        messages = [Message(role="system", content="System prompt")] + messages
    return Session(
        session_id=f"session-{'system' if has_system else 'plain'}", messages=messages
    )


def _core_and_config() -> tuple[AgentCore, dict]:
    core = AgentCore()
    core.register_provider(EchoOpenAILikeProvider)
    return core, {"provider": "echo_openai_like", "model": "test-model"}


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _counter_factory(prefix: str):
    counter = {"value": 0}

    def _next() -> str:
        counter["value"] += 1
        return f"<{prefix}_{counter['value']:03d}>"

    return _next


def test_prompt_matches_observed_fixture() -> None:
    fixture = _fixture("success-basic")

    assert build_compaction_prompt() == fixture["compact_request_prompt_text"]
    assert (
        extract_prompt_sections(build_compaction_prompt())
        == fixture["compact_request_prompt_sections"]
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


def test_pre_compaction_transcript_writer_matches_fixture_entry_schema(
    tmp_path: Path,
) -> None:
    fixture = _fixture("success-basic")
    expected_user = fixture["project_transcript_pre_compaction_message_events"][0]
    expected_assistant = fixture["project_transcript_pre_compaction_message_events"][1]
    session = Session(
        session_id="<SESSION_ID>",
        messages=[
            Message(role="user", content="Answer exactly ONE."),
            Message(role="assistant", content="ONE"),
        ],
    )

    output = write_pre_compaction_transcript(
        session,
        tmp_path / "transcript.jsonl",
        cwd="<WORKSPACE>",
        uuid_factory=_counter_factory("UUID"),
        prompt_id_factory=_counter_factory("PROMPT_ID"),
        message_id_factory=_counter_factory("MESSAGE_ID"),
        timestamp_factory=_counter_factory("TIMESTAMP"),
        entrypoint="sdk-cli",
        version="2.1.154",
        git_branch="HEAD",
    )
    entries = _read_jsonl(output)

    assert len(entries) == 2
    assert set(entries[0]) == set(expected_user)
    assert set(entries[1]) == set(expected_assistant)
    assert set(entries[0]["message"]) == set(expected_user["message"])
    assert set(entries[1]["message"]) == set(expected_assistant["message"])
    assert entries[0]["type"] == "user"
    assert entries[0]["message"] == {
        "role": "user",
        "content": "Answer exactly ONE.",
    }
    assert entries[1]["type"] == "assistant"
    assert entries[1]["message"]["content"] == [{"type": "text", "text": "ONE"}]
    assert entries[0]["parentUuid"] is None
    assert entries[1]["parentUuid"] == entries[0]["uuid"]
    assert entries[0]["sessionId"] == "<SESSION_ID>"
    assert entries[1]["sessionId"] == "<SESSION_ID>"
    assert entries[0]["timestamp"] == "<TIMESTAMP_001>"
    assert entries[1]["timestamp"] == "<TIMESTAMP_002>"


def test_pre_compaction_transcript_writer_preserves_original_conversation(
    tmp_path: Path,
) -> None:
    session = _make_session(has_system=False)

    output = write_pre_compaction_transcript(
        session,
        tmp_path / "transcript.jsonl",
        cwd="<WORKSPACE>",
        uuid_factory=_counter_factory("UUID"),
        prompt_id_factory=_counter_factory("PROMPT_ID"),
        message_id_factory=_counter_factory("MESSAGE_ID"),
        timestamp_factory=_counter_factory("TIMESTAMP"),
    )
    entries = _read_jsonl(output)

    assert [entry["type"] for entry in entries] == [
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert entries[0]["message"]["content"] == "Answer exactly ONE."
    assert entries[2]["message"]["content"] == "Answer exactly TWO."
    assert entries[4]["message"]["content"] == "Answer exactly THREE."
    assert entries[1]["message"]["content"][0]["text"] == "ONE"
    assert entries[3]["message"]["content"][0]["text"] == "TWO"
    assert entries[5]["message"]["content"][0]["text"] == "THREE"
    assert [entry["parentUuid"] for entry in entries] == [
        None,
        "<UUID_001>",
        "<UUID_002>",
        "<UUID_003>",
        "<UUID_004>",
        "<UUID_005>",
    ]


def test_feature_schema_includes_compaction_model_and_existing_keys() -> None:
    feature = ClaudeCompactionFeature()

    schema = feature.get_config_schema()

    assert _COMPACTION_MODEL_KEY in schema
    assert "claude_compaction_prompt" in schema
    assert "claude_compaction_settings_overrides" in schema


def test_feature_ui_elements_include_compaction_model_and_message_action() -> None:
    feature = ClaudeCompactionFeature()

    elements = feature.get_ui_elements(
        models=[{"id": "claude-sonnet", "name": "Claude Sonnet"}]
    )

    compaction_model = next(
        element
        for element in elements
        if element.get("ui_type") == "config"
        and element.get("key") == _COMPACTION_MODEL_KEY
    )
    assert compaction_model["type"] == "dropdown"
    assert compaction_model["options"] == [
        {"label": "Claude Sonnet", "value": "claude-sonnet"}
    ]

    message_action = next(
        element
        for element in elements
        if element.get("ui_type") == "message_action"
        and element.get("id") == "compact_up_to_here"
    )
    assert message_action["action_id"] == "compact_conversation"
    assert message_action["fixed_params"] == {"start": 0, "end_inclusive": True}


def test_feature_ui_elements_fall_back_to_text_when_models_are_unavailable() -> None:
    feature = ClaudeCompactionFeature()

    elements = feature.get_ui_elements(models=[])

    compaction_model = next(
        element
        for element in elements
        if element.get("ui_type") == "config"
        and element.get("key") == _COMPACTION_MODEL_KEY
    )
    assert compaction_model["type"] == "text"
    assert "options" not in compaction_model


@pytest.mark.parametrize(
    ("has_system", "start", "end", "end_inclusive", "expected_roles"),
    [
        (
            False,
            None,
            None,
            False,
            ["user", "assistant", "user", "assistant", "user", "assistant", "user"],
        ),
        (False, 0, 3, False, ["user", "assistant", "user"]),
        (False, 1, 4, False, ["assistant", "user", "assistant", "user"]),
        (
            True,
            None,
            None,
            False,
            [
                "system",
                "user",
                "assistant",
                "user",
                "assistant",
                "user",
                "assistant",
                "user",
            ],
        ),
        (True, 0, 4, False, ["system", "user", "assistant", "user"]),
        (True, 2, 5, False, ["system", "assistant", "user", "assistant", "user"]),
    ],
)
def test_build_compaction_request_session_handles_system_and_no_system_cases(
    has_system: bool,
    start: int | None,
    end: int | None,
    end_inclusive: bool,
    expected_roles: list[str],
) -> None:
    fixture = _fixture("success-basic")
    session = _make_session(has_system)

    request_session, target_indices, _request_indices = (
        build_compaction_request_session(
            session,
            prompt_text=fixture["compact_request_prompt_text"],
            start=start,
            end=end,
            end_inclusive=end_inclusive,
        )
    )

    assert [message.role for message in request_session.messages] == expected_roles
    assert request_session.messages[-1].content.endswith(
        fixture["compact_request_prompt_text"]
    )
    if has_system:
        assert request_session.messages[0].role == "system"
        assert 0 not in target_indices
    else:
        assert all(message.role != "system" for message in request_session.messages)


@pytest.mark.parametrize(
    (
        "has_system",
        "start",
        "end",
        "end_inclusive",
        "expected_roles",
        "expected_leading_contents",
        "expected_trailing_contents",
    ),
    [
        (
            False,
            None,
            None,
            False,
            ["user", "user", "assistant"],
            [],
            [],
        ),
        (
            False,
            0,
            3,
            False,
            ["user", "user", "assistant", "assistant", "user", "assistant"],
            [],
            ["TWO", "Answer exactly THREE.", "THREE"],
        ),
        (
            False,
            1,
            4,
            False,
            ["user", "user", "user", "assistant", "user", "assistant"],
            ["Answer exactly ONE."],
            ["Answer exactly THREE.", "THREE"],
        ),
        (
            True,
            None,
            None,
            False,
            ["system", "user", "user", "assistant"],
            ["System prompt"],
            [],
        ),
        (
            True,
            0,
            4,
            False,
            ["system", "user", "user", "assistant", "assistant", "user", "assistant"],
            ["System prompt"],
            ["TWO", "Answer exactly THREE.", "THREE"],
        ),
        (
            True,
            2,
            5,
            False,
            ["system", "user", "user", "user", "assistant", "user", "assistant"],
            ["System prompt", "Answer exactly ONE."],
            ["Answer exactly THREE.", "THREE"],
        ),
    ],
)
def test_compacted_session_replaces_only_selected_range_and_preserves_system_invariant(
    has_system: bool,
    start: int | None,
    end: int | None,
    end_inclusive: bool,
    expected_roles: list[str],
    expected_leading_contents: list[str],
    expected_trailing_contents: list[str],
) -> None:
    fixture = _fixture("success-basic")
    core, config = _core_and_config()
    session = _make_session(has_system)

    compacted = build_compacted_session(
        core,
        session,
        config,
        fixture["compact_summary_text"],
        start=start,
        end=end,
        end_inclusive=end_inclusive,
    )

    assert [message.role for message in compacted.messages] == expected_roles
    if has_system:
        assert compacted.messages[0].role == "system"
        assert compacted.messages[0].content == "System prompt"
        assert sum(1 for message in compacted.messages if message.role == "system") == 1
    else:
        assert all(message.role != "system" for message in compacted.messages)

    summary_index = next(
        idx
        for idx, message in enumerate(compacted.messages)
        if message.content == fixture["compact_summary_text"]
    )
    assert compacted.messages[summary_index].content == fixture["compact_summary_text"]
    assert compacted.messages[summary_index + 1].content == _LOCAL_COMMAND_ARTIFACT
    assert compacted.messages[summary_index + 2].content == _NO_RESPONSE_REQUESTED
    assert [message.content for message in compacted.messages[:summary_index]] == (
        expected_leading_contents
    )
    trailing = compacted.messages[summary_index + 3 :]
    assert [message.content for message in trailing] == expected_trailing_contents

    native_messages = compacted.metadata["native_messages"]
    assert native_messages[summary_index + 1]["content"] == _LOCAL_COMMAND_ARTIFACT
    summary_metadata = compacted.messages[summary_index].metadata or {}
    assert summary_metadata["claude_compaction"]["is_compact_summary"] is True


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
