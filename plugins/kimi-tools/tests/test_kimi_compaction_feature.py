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

import importlib

ROOT = Path(__file__).resolve().parents[3]
CORE_PY = ROOT / "core/python"
PLUGIN_SRC = ROOT / "plugins/kimi-tools/src"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
if str(PLUGIN_SRC) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SRC))

from agent_core import AgentCore, Message, Session  # noqa: E402
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: E402

# Import the compaction feature module directly to avoid pulling in
# tool_compat_shared through the kimi_tools package __init__.py.
_kcf = importlib.import_module("kimi_tools.kimi_compaction_feature")
_COMPACTION_METADATA_KEY = _kcf._COMPACTION_METADATA_KEY
_COMPACTION_PREFIX = _kcf._COMPACTION_PREFIX
_KIMI_COMPACTION_PROMPT = _kcf._KIMI_COMPACTION_PROMPT
KimiCompactionFeature = _kcf.KimiCompactionFeature
build_compact_summary_text = _kcf.build_compact_summary_text
build_compacted_session = _kcf.build_compacted_session
build_compaction_prompt = _kcf.build_compaction_prompt
build_compaction_request_session = _kcf.build_compaction_request_session
build_compaction_session = _kcf.build_compaction_session
extract_summary_sections = _kcf.extract_summary_sections
extract_summary_text = _kcf.extract_summary_text
validate_summary_text = _kcf.validate_summary_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Prompt tests
# ---------------------------------------------------------------------------


class TestBuildCompactionPrompt:
    def test_default_prompt_is_not_empty(self) -> None:
        prompt = build_compaction_prompt()
        assert prompt.strip()
        assert "<current_focus>" in prompt
        assert "<environment>" in prompt
        assert "<completed_tasks>" in prompt
        assert "<active_issues>" in prompt
        assert "<code_state>" in prompt
        assert "<important_context>" in prompt

    def test_default_prompt_matches_constant(self) -> None:
        assert build_compaction_prompt() == _KIMI_COMPACTION_PROMPT

    def test_custom_instructions_appended(self) -> None:
        prompt = build_compaction_prompt("Focus on database changes")
        assert "Focus on database changes" in prompt
        assert prompt.startswith(_KIMI_COMPACTION_PROMPT)

    def test_prompt_override_replaces_default(self) -> None:
        custom = "Custom prompt for testing"
        prompt = build_compaction_prompt(prompt_override=custom)
        assert prompt == custom

    def test_prompt_override_with_instructions_appends_instructions(self) -> None:
        custom = "Custom prompt"
        prompt = build_compaction_prompt(
            "Focus on testing", prompt_override=custom
        )
        assert prompt.startswith(custom)
        assert "Focus on testing" in prompt

    def test_blank_instructions_ignored(self) -> None:
        prompt = build_compaction_prompt("")
        assert prompt == _KIMI_COMPACTION_PROMPT

    def test_whitespace_instructions_ignored(self) -> None:
        prompt = build_compaction_prompt("   ")
        assert prompt == _KIMI_COMPACTION_PROMPT


# ---------------------------------------------------------------------------
# Summary extraction tests
# ---------------------------------------------------------------------------


class TestExtractSummaryText:
    def test_extracts_structured_sections(self) -> None:
        response = (
            "Some preamble text\n\n"
            "<current_focus>\nWorking on tests\n</current_focus>\n\n"
            "<environment>\nPython 3.12\n</environment>\n\n"
            "<completed_tasks>\nNone yet\n</completed_tasks>\n\n"
            "<active_issues>\nNone\n</active_issues>\n\n"
            "<code_state>\n\n<file>\nfoo.py\n**Summary:** test\n</file>\n</code_state>\n\n"
            "<important_context>\nNothing else\n</important_context>"
        )
        result = extract_summary_text(response)
        assert result.startswith("<current_focus>")
        assert result.endswith("</important_context>")
        assert "Working on tests" in result

    def test_fallback_to_full_text_when_no_sections(self) -> None:
        response = "Just plain text without any structured sections."
        result = extract_summary_text(response)
        assert result == "Just plain text without any structured sections."

    def test_raises_on_empty_response(self) -> None:
        with pytest.raises(ValueError, match="empty response"):
            extract_summary_text("   ")

    def test_extracts_from_middle_of_response(self) -> None:
        response = (
            "Here is my analysis:\n\n"
            "<current_focus>\nTask X\n</current_focus>\n\n"
            "<environment>\n- Node 18\n</environment>\n\n"
            "<completed_tasks>\n- Task A: done\n</completed_tasks>\n\n"
            "<active_issues>\n- Bug B: investigating\n</active_issues>\n\n"
            "<code_state>\n\n<file>\nmain.py\n**Summary:** entry point\n</file>\n</code_state>\n\n"
            "<important_context>\n- Deploy to prod\n</important_context>\n\n"
            "That's the summary."
        )
        result = extract_summary_text(response)
        assert result.startswith("<current_focus>")
        assert result.endswith("</important_context>")


class TestExtractSummarySections:
    def test_extracts_section_tags(self) -> None:
        text = (
            "<current_focus>foo</current_focus>"
            "<environment>bar</environment>"
            "<completed_tasks>baz</completed_tasks>"
            "<active_issues>qux</active_issues>"
            "<code_state>quux</code_state>"
            "<important_context>corge</important_context>"
        )
        sections = extract_summary_sections(text)
        assert sections == [
            "current_focus",
            "environment",
            "completed_tasks",
            "active_issues",
            "code_state",
            "important_context",
        ]

    def test_returns_empty_for_no_sections(self) -> None:
        assert extract_summary_sections("plain text") == []


class TestValidateSummaryText:
    def test_passes_with_all_sections(self) -> None:
        text = (
            "<current_focus>x</current_focus>"
            "<environment>x</environment>"
            "<completed_tasks>x</completed_tasks>"
            "<active_issues>x</active_issues>"
            "<code_state>x</code_state>"
            "<important_context>x</important_context>"
        )
        validate_summary_text(text)  # should not raise

    def test_raises_on_missing_sections(self) -> None:
        with pytest.raises(ValueError, match="missing required sections"):
            validate_summary_text("<current_focus>x</current_focus>")

    def test_raises_on_empty_text(self) -> None:
        with pytest.raises(ValueError, match="missing required sections"):
            validate_summary_text("")


# ---------------------------------------------------------------------------
# Session building tests
# ---------------------------------------------------------------------------


class TestBuildCompactionSession:
    def test_appends_prompt_to_last_user_message(self) -> None:
        session = _make_session(has_system=False)
        prompt = "Compact this conversation"
        result = build_compaction_session(session, prompt_text=prompt)
        assert result.messages[-1].role == "user"
        assert result.messages[-1].content.endswith(prompt)
        assert result.session_id == session.session_id

    def test_adds_new_user_message_when_last_is_assistant(self) -> None:
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there"),
        ]
        session = Session(session_id="test", messages=messages)
        result = build_compaction_session(session, prompt_text="Compact")
        assert result.messages[-1].role == "user"
        assert result.messages[-1].content == "Compact"

    def test_strips_native_history_from_metadata(self) -> None:
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi"),
        ]
        session = Session(
            session_id="test",
            messages=messages,
            metadata={
                "native_messages": [{"role": "user", "content": "Hello"}],
                "native_messages_integrity": "sha256:abc",
                "other_key": "preserved",
            },
        )
        result = build_compaction_session(session, prompt_text="Compact")
        assert "native_messages" not in result.metadata
        assert "native_messages_integrity" not in result.metadata
        assert result.metadata.get("other_key") == "preserved"


class TestBuildCompactionRequestSession:
    @pytest.mark.parametrize(
        ("has_system", "start", "end", "end_inclusive", "expected_roles"),
        [
            # Full range, no system
            (False, None, None, False, ["user", "assistant", "user", "assistant", "user", "assistant", "user"]),
            # Partial range, no system
            (False, 0, 3, False, ["user", "assistant", "user"]),
            # Partial range, no system
            (False, 1, 4, False, ["assistant", "user", "assistant", "user"]),
            # Full range, with system
            (True, None, None, False, [
                "system", "user", "assistant", "user", "assistant", "user", "assistant", "user",
            ]),
            # Partial range, with system (system preserved)
            (True, 0, 4, False, ["system", "user", "assistant", "user"]),
            # Partial range, with system
            (True, 2, 5, False, ["system", "assistant", "user", "assistant", "user"]),
        ],
    )
    def test_builds_correct_request_session(
        self,
        has_system: bool,
        start: int | None,
        end: int | None,
        end_inclusive: bool,
        expected_roles: list[str],
    ) -> None:
        session = _make_session(has_system)
        prompt = "Compact this"
        result, target_indices, request_indices = build_compaction_request_session(
            session, prompt_text=prompt, start=start, end=end, end_inclusive=end_inclusive
        )
        assert [message.role for message in result.messages] == expected_roles
        assert result.messages[-1].content.endswith(prompt)
        if has_system:
            assert result.messages[0].role == "system"
            assert 0 not in target_indices
        else:
            assert all(message.role != "system" for message in result.messages)

    def test_raises_on_empty_range(self) -> None:
        session = _make_session(has_system=False)
        with pytest.raises(ValueError, match="range selects no messages"):
            build_compaction_request_session(
                session, prompt_text="Compact", start=0, end=0
            )


# ---------------------------------------------------------------------------
# Compacted session tests
# ---------------------------------------------------------------------------


class TestBuildCompactedSession:
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
            # Full range, no system → summary replaces everything
            (
                False, None, None, False,
                ["user"],
                [],
                [],
            ),
            # Partial range, no system → summary + preserved tail
            (
                False, 0, 3, False,
                ["user", "assistant", "user", "assistant"],
                [],
                ["TWO", "Answer exactly THREE.", "THREE"],
            ),
            # Partial range, no system → summary + preserved tail
            (
                False, 1, 4, False,
                ["user", "user", "user", "assistant"],
                ["Answer exactly ONE."],
                ["Answer exactly THREE.", "THREE"],
            ),
            # Full range, with system → system preserved, summary replaces rest
            (
                True, None, None, False,
                ["system", "user"],
                ["System prompt"],
                [],
            ),
            # Partial range, with system → system + leading + summary + tail
            (
                True, 0, 4, False,
                ["system", "user", "assistant", "user", "assistant"],
                ["System prompt"],
                ["TWO", "Answer exactly THREE.", "THREE"],
            ),
            # Partial range, with system
            (
                True, 2, 5, False,
                ["system", "user", "user", "user", "assistant"],
                ["System prompt", "Answer exactly ONE."],
                ["Answer exactly THREE.", "THREE"],
            ),
        ],
    )
    def test_compacted_session_replaces_only_selected_range_and_preserves_system_invariant(
        self,
        has_system: bool,
        start: int | None,
        end: int | None,
        end_inclusive: bool,
        expected_roles: list[str],
        expected_leading_contents: list[str],
        expected_trailing_contents: list[str],
    ) -> None:
        core, config = _core_and_config()
        session = _make_session(has_system)
        summary_text = (
            "Previous context has been compacted. Here is the compaction output:\n\n"
            "<current_focus>Testing</current_focus>\n"
            "<environment>Python</environment>\n"
            "<completed_tasks>None</completed_tasks>\n"
            "<active_issues>None</active_issues>\n"
            "<code_state>\n\n<file>\ntest.py\n**Summary:** test\n</file>\n</code_state>\n"
            "<important_context>None</important_context>"
        )

        compacted = build_compacted_session(
            core,
            session,
            config,
            summary_text,
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
            if message.content == summary_text
        )
        assert compacted.messages[summary_index].content == summary_text
        assert [message.content for message in compacted.messages[:summary_index]] == (
            expected_leading_contents
        )
        trailing = compacted.messages[summary_index + 1 :]
        assert [message.content for message in trailing] == expected_trailing_contents

        summary_metadata = compacted.messages[summary_index].metadata or {}
        assert summary_metadata[_COMPACTION_METADATA_KEY]["is_compact_summary"] is True


# ---------------------------------------------------------------------------
# Feature class tests
# ---------------------------------------------------------------------------


class TestKimiCompactionFeature:
    def test_feature_schema_includes_expected_keys(self) -> None:
        feature = KimiCompactionFeature()
        schema = feature.get_config_schema()
        assert "compaction_model" in schema
        assert "kimi_compaction_prompt" in schema
        assert "kimi_compaction_settings_overrides" in schema

    def test_feature_ui_elements_include_compaction_model_and_message_action(self) -> None:
        feature = KimiCompactionFeature()
        elements = feature.get_ui_elements(
            models=[{"id": "moonshot-v1", "name": "Moonshot V1"}]
        )
        compaction_model = next(
            element
            for element in elements
            if element.get("ui_type") == "config"
            and element.get("key") == "compaction_model"
        )
        assert compaction_model["type"] == "dropdown"
        assert compaction_model["options"] == [
            {"label": "Moonshot V1", "value": "moonshot-v1"}
        ]

        message_action = next(
            element
            for element in elements
            if element.get("ui_type") == "message_action"
            and element.get("id") == "compact_up_to_here"
        )
        assert message_action["action_id"] == "compact_conversation"
        assert message_action["fixed_params"] == {"start": 0, "end_inclusive": True}

    def test_feature_ui_elements_fall_back_to_text_when_models_are_unavailable(self) -> None:
        feature = KimiCompactionFeature()
        elements = feature.get_ui_elements(models=[])
        compaction_model = next(
            element
            for element in elements
            if element.get("ui_type") == "config"
            and element.get("key") == "compaction_model"
        )
        assert compaction_model["type"] == "text"
        assert "options" not in compaction_model

    def test_feature_actions_include_compact_conversation(self) -> None:
        feature = KimiCompactionFeature()
        actions = feature.get_actions({})
        assert len(actions) == 1
        assert actions[0]["id"] == "compact_conversation"
        assert "start" in actions[0]["inputs"]
        assert "end" in actions[0]["inputs"]
        assert "end_inclusive" in actions[0]["inputs"]
        assert "instructions" in actions[0]["inputs"]

    def test_execute_action_returns_error_for_unknown_action(self) -> None:
        feature = KimiCompactionFeature()
        session = _make_session(has_system=False)
        result = feature.execute_action(
            "unknown_action",
            session,
            [],
            {},
            None,
            {},
        )
        assert "error" in result
        assert result["error"]["type"] == "unknown_action"

    def test_execute_action_returns_error_for_empty_session(self) -> None:
        feature = KimiCompactionFeature()
        session = Session(session_id="empty", messages=[])
        result = feature.execute_action(
            "compact_conversation",
            session,
            [],
            {},
            None,
            {},
        )
        assert "error" in result
        assert result["error"]["type"] == "no_messages"

    def test_execute_action_returns_error_for_too_few_messages(self) -> None:
        feature = KimiCompactionFeature()
        session = Session(
            session_id="short",
            messages=[Message(role="user", content="Hi")],
        )
        result = feature.execute_action(
            "compact_conversation",
            session,
            [],
            {},
            None,
            {},
        )
        assert "error" in result
        assert result["error"]["type"] == "not_enough_messages"

    def test_execute_action_returns_error_for_missing_core(self) -> None:
        feature = KimiCompactionFeature()
        session = _make_session(has_system=False)
        result = feature.execute_action(
            "compact_conversation",
            session,
            [],
            {},
            None,
            {},
        )
        assert "error" in result
        assert result["error"]["type"] == "missing_core"

    def test_execute_action_returns_error_for_invalid_range(self) -> None:
        feature = KimiCompactionFeature()
        core, config = _core_and_config()
        session = _make_session(has_system=False)
        result = feature.execute_action(
            "compact_conversation",
            session,
            [],
            {"start": 0, "end": 0},
            {"core": core, "config": config},
            {},
        )
        assert "error" in result
        assert result["error"]["type"] == "invalid_range"


# ---------------------------------------------------------------------------
# Build compact summary text tests
# ---------------------------------------------------------------------------


class TestBuildCompactSummaryText:
    def test_wraps_summary_with_prefix(self) -> None:
        summary_body = (
            "<current_focus>Task X</current_focus>"
            "<environment>Python</environment>"
            "<completed_tasks>None</completed_tasks>"
            "<active_issues>None</active_issues>"
            "<code_state>\n\n<file>\ntest.py\n</file>\n</code_state>"
            "<important_context>None</important_context>"
        )
        result = build_compact_summary_text(summary_body)
        assert result.startswith(_COMPACTION_PREFIX)
        assert summary_body in result

    def test_strips_whitespace_from_summary(self) -> None:
        result = build_compact_summary_text(
            "  <current_focus>x</current_focus>"
            "<environment>x</environment>"
            "<completed_tasks>x</completed_tasks>"
            "<active_issues>x</active_issues>"
            "<code_state>x</code_state>"
            "<important_context>x</important_context>  "
        )
        assert result.startswith(_COMPACTION_PREFIX)
        assert not result.endswith("  ")


# ---------------------------------------------------------------------------
# Plugin registration test
# ---------------------------------------------------------------------------


class TestPluginRegistration:
    def test_agent_plugin_bundle_registers_kimi_compaction_as_feature(self) -> None:
        payload = json.loads(
            (ROOT / "plugins/kimi-tools/agent_plugin.json").read_text(encoding="utf-8")
        )
        assert (
            "kimi_tools.kimi_compaction_feature.KimiCompactionFeature"
            in payload["entries"]
        )
        assert (
            payload["kinds"][
                "kimi_tools.kimi_compaction_feature.KimiCompactionFeature"
            ]
            == "features"
        )