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

import hashlib
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
_GENERIC_COMPACTION_SYSTEM_PROMPT = _kcf._GENERIC_COMPACTION_SYSTEM_PROMPT
_KIMI_COMPACTION_PROMPT = _kcf._KIMI_COMPACTION_PROMPT
KimiCompactionFeature = _kcf.KimiCompactionFeature
build_compact_summary_text = _kcf.build_compact_summary_text
build_compacted_session = _kcf.build_compacted_session
build_compaction_prompt = _kcf.build_compaction_prompt
build_kimi_compaction_request_session = _kcf.build_kimi_compaction_request_session
extract_summary_sections = _kcf.extract_summary_sections
extract_summary_text = _kcf.extract_summary_text
validate_summary_text = _kcf.validate_summary_text
_get_compaction_config = _kcf._get_compaction_config
_get_effective_compaction_config = _kcf._get_effective_compaction_config
_is_compaction_enabled = _kcf._is_compaction_enabled
_merge_request_config = _kcf._merge_request_config


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


def _core_and_config_with_compaction() -> tuple[AgentCore, dict]:
    core, config = _core_and_config()
    config = {
        **config,
        "compaction": {
            "enabled": True,
            "type": "kimi",
        },
    }
    return core, config


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

    def test_default_prompt_matches_pinned_kimi_cli_prompt_hash(self) -> None:
        """Keep parity coverage when the sibling kimi-cli checkout is absent."""
        digest = hashlib.sha256(build_compaction_prompt().encode("utf-8")).hexdigest()
        assert (
            digest == "24753a19a3c0dfabc5545a103666a559cc7dd8caa963715fdc6ca7dd787a0e0a"
        )

    def test_default_prompt_matches_kimi_cli_compact_md(self) -> None:
        """The prompt body must match kimi-cli/src/kimi_cli/prompts/compact.md exactly."""
        kimi_cli_root = ROOT.parent / "kimi-cli"
        compact_md = kimi_cli_root / "src/kimi_cli/prompts/compact.md"
        if not compact_md.exists():
            pytest.skip("kimi-cli compact.md not available in sibling repo")
        expected = compact_md.read_text(encoding="utf-8")
        assert build_compaction_prompt() == expected

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
        prompt = build_compaction_prompt("Focus on testing", prompt_override=custom)
        assert prompt.startswith(custom)
        assert "Focus on testing" in prompt

    def test_blank_instructions_ignored(self) -> None:
        prompt = build_compaction_prompt("")
        assert prompt == _KIMI_COMPACTION_PROMPT

    def test_whitespace_instructions_ignored(self) -> None:
        prompt = build_compaction_prompt("   ")
        assert prompt == _KIMI_COMPACTION_PROMPT

    def test_custom_instructions_in_same_text_block(self) -> None:
        """Custom instructions must be appended in the same text block as the prompt."""
        prompt = build_compaction_prompt("Preserve all discussions about the database")
        assert "User's Custom Compaction Instruction" in prompt
        assert "Preserve all discussions about the database" in prompt
        # The custom instruction block is separated from the prompt by \n\n
        assert "**User's Custom Compaction Instruction:**" in prompt


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
# Kimi compaction request session builder tests
# ---------------------------------------------------------------------------


class TestBuildKimiCompactionRequestSession:
    def test_request_session_has_generic_compactor_system_prompt(self) -> None:
        session = _make_session(has_system=False)
        result, _compact, _preserved = build_kimi_compaction_request_session(
            session, prompt_text="Compact this"
        )
        assert result is not None
        assert len(result.messages) == 2
        assert result.messages[0].role == "system"
        assert result.messages[0].content == _GENERIC_COMPACTION_SYSTEM_PROMPT
        assert result.messages[1].role == "user"

    def test_synthetic_message_uses_message_n_block_format(self) -> None:
        session = _make_session(has_system=False)
        result, compact_indices, _preserved = build_kimi_compaction_request_session(
            session, prompt_text="Compact this"
        )
        assert result is not None
        synthetic = result.messages[1].content
        # With default max_preserved_messages=2, the last 2 messages
        # (user(4), assistant(5)) are preserved. Compactable range is [0, 4).
        assert "## Message 1\nRole: user\nContent:\nAnswer exactly ONE." in synthetic
        assert "## Message 2\nRole: assistant\nContent:\nONE" in synthetic
        assert "## Message 3\nRole: user\nContent:\nAnswer exactly TWO." in synthetic
        assert "## Message 4\nRole: assistant\nContent:\nTWO" in synthetic
        # Preserved messages are NOT in the synthetic message
        assert "Answer exactly THREE." not in synthetic
        assert "\nTHREE" not in synthetic
        # Compact indices are the first 4
        assert compact_indices == [0, 1, 2, 3]

    def test_synthetic_message_appends_prompt_at_end(self) -> None:
        session = _make_session(has_system=False)
        result, _compact, _preserved = build_kimi_compaction_request_session(
            session, prompt_text="COMPACT_PROMPT_BODY"
        )
        assert result is not None
        synthetic = result.messages[1].content
        assert synthetic.endswith("\nCOMPACT_PROMPT_BODY")

    def test_text_only_filtering_drops_media_and_think_parts(self) -> None:
        messages = [
            Message(
                role="user",
                content=[
                    {"type": "text", "text": "Analyze these files:"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,IMG"},
                    },
                    {"type": "think", "think": "internal reasoning"},
                ],
            ),
            Message(role="assistant", content="I can see the files."),
            Message(role="user", content="What's your conclusion?"),
            Message(role="assistant", content="All good."),
        ]
        session = Session(session_id="multipart", messages=messages)
        result, _compact, _preserved = build_kimi_compaction_request_session(
            session, prompt_text="PROMPT", max_preserved_messages=2
        )
        assert result is not None
        synthetic = result.messages[1].content
        # Text content is included
        assert "Analyze these files:" in synthetic
        assert "I can see the files." in synthetic
        # Media and think parts are dropped
        assert "data:image/png" not in synthetic
        assert "internal reasoning" not in synthetic

    def test_text_tool_message_keeps_text_but_drops_structured_result(self) -> None:
        messages = [
            Message(
                role="tool",
                content="Visible tool result",
                tool_result={"type": "provider_native", "secret": "structured payload"},
            ),
            Message(role="assistant", content="Old response"),
            Message(role="user", content="Latest question"),
            Message(role="assistant", content="Latest response"),
        ]
        session = Session(session_id="tool-text", messages=messages)
        result, _compact, _preserved = build_kimi_compaction_request_session(
            session, prompt_text="PROMPT"
        )
        assert result is not None
        synthetic = result.messages[1].content
        assert "Role: tool\nContent:\nVisible tool result" in synthetic
        assert "structured payload" not in synthetic

    def test_preserved_tail_with_default_max_preserved_messages(self) -> None:
        session = _make_session(has_system=False)
        result, compact_indices, preserved_indices = (
            build_kimi_compaction_request_session(session, prompt_text="PROMPT")
        )
        assert result is not None
        # Last 2 user/assistant messages preserved
        assert preserved_indices == [4, 5]
        assert compact_indices == [0, 1, 2, 3]

    def test_noop_when_too_few_user_assistant_messages(self) -> None:
        messages = [
            Message(role="user", content="Only one"),
        ]
        session = Session(session_id="short", messages=messages)
        result, compact_indices, preserved_indices = (
            build_kimi_compaction_request_session(
                session, prompt_text="PROMPT", max_preserved_messages=2
            )
        )
        assert result is None
        assert compact_indices == []
        assert preserved_indices == []

    def test_noop_when_only_preserved_messages_exist(self) -> None:
        messages = [
            Message(role="user", content="Latest question"),
            Message(role="assistant", content="Latest reply"),
        ]
        session = Session(session_id="preserved-only", messages=messages)
        result, compact_indices, preserved_indices = (
            build_kimi_compaction_request_session(
                session, prompt_text="PROMPT", max_preserved_messages=2
            )
        )
        assert result is None
        assert compact_indices == []
        assert preserved_indices == []

    def test_explicit_end_compacts_exactly_selected_range(self) -> None:
        session = _make_session(has_system=False)
        result, compact_indices, preserved_indices = (
            build_kimi_compaction_request_session(
                session, prompt_text="PROMPT", start=0, end=3
            )
        )
        assert result is not None
        # Explicit end → no preserved tail
        assert preserved_indices == []
        assert compact_indices == [0, 1, 2]
        synthetic = result.messages[1].content
        assert "## Message 1\nRole: user\nContent:\nAnswer exactly ONE." in synthetic
        assert "## Message 2\nRole: assistant\nContent:\nONE" in synthetic
        assert "## Message 3\nRole: user\nContent:\nAnswer exactly TWO." in synthetic
        # Messages after the range are NOT in the synthetic message
        assert "TWO" not in synthetic.replace("Answer exactly TWO.", "")
        assert "THREE" not in synthetic

    def test_leading_system_message_is_in_request_but_preserved_in_session(
        self,
    ) -> None:
        session = _make_session(has_system=True)
        result, compact_indices, preserved_indices = (
            build_kimi_compaction_request_session(session, prompt_text="PROMPT")
        )
        assert result is not None
        # The system message is not deleted from the platform session.
        assert 0 not in compact_indices
        assert compact_indices == [1, 2, 3, 4]
        # Last 2 user/assistant messages preserved
        assert preserved_indices == [5, 6]
        # Request session uses generic compactor system prompt, not the agent's
        assert result.messages[0].content == _GENERIC_COMPACTION_SYSTEM_PROMPT
        assert result.messages[0].content != "System prompt"
        # Upstream SimpleCompaction includes the original system message in the
        # numbered transcript given to the compactor.
        synthetic = result.messages[1].content
        assert "## Message 1\nRole: system\nContent:\nSystem prompt" in synthetic
        assert "## Message 2\nRole: user\nContent:\nAnswer exactly ONE." in synthetic

    def test_explicit_end_with_leading_system_includes_system_in_request(self) -> None:
        session = _make_session(has_system=True)
        result, compact_indices, preserved_indices = (
            build_kimi_compaction_request_session(
                session, prompt_text="PROMPT", start=0, end=4
            )
        )
        assert result is not None
        # System (index 0) is preserved in the final session while [1, 4) is
        # replaced by the summary.
        assert compact_indices == [1, 2, 3]
        assert preserved_indices == []
        synthetic = result.messages[1].content
        assert "## Message 1\nRole: system\nContent:\nSystem prompt" in synthetic
        assert "## Message 2\nRole: user\nContent:\nAnswer exactly ONE." in synthetic
        assert "## Message 3\nRole: assistant\nContent:\nONE" in synthetic
        assert "## Message 4\nRole: user\nContent:\nAnswer exactly TWO." in synthetic

    def test_raises_on_empty_range(self) -> None:
        session = _make_session(has_system=False)
        with pytest.raises(ValueError, match="range selects no messages"):
            build_kimi_compaction_request_session(
                session, prompt_text="PROMPT", start=0, end=0
            )

    def test_raises_when_range_selects_only_system(self) -> None:
        session = _make_session(has_system=True)
        with pytest.raises(ValueError, match="range selects no compactable messages"):
            build_kimi_compaction_request_session(
                session, prompt_text="PROMPT", start=0, end=1
            )

    def test_custom_max_preserved_messages(self) -> None:
        session = _make_session(has_system=False)
        result, compact_indices, preserved_indices = (
            build_kimi_compaction_request_session(
                session, prompt_text="PROMPT", max_preserved_messages=3
            )
        )
        assert result is not None
        # Last 3 user/assistant messages preserved: assistant(3), user(4), assistant(5)
        # Wait: backward scan from 5: assistant(5)→1, user(4)→2, assistant(3)→3
        # preserve_start = 3
        assert preserved_indices == [3, 4, 5]
        assert compact_indices == [0, 1, 2]

    @pytest.mark.parametrize("max_preserved_messages", [0, -1])
    def test_nonpositive_max_preserved_messages_is_noop_like_kimi_cli(
        self,
        max_preserved_messages: int,
    ) -> None:
        session = _make_session(has_system=False)
        result, compact_indices, preserved_indices = (
            build_kimi_compaction_request_session(
                session,
                prompt_text="PROMPT",
                max_preserved_messages=max_preserved_messages,
            )
        )
        assert result is None
        assert compact_indices == []
        assert preserved_indices == []


# ---------------------------------------------------------------------------
# Merged request config tests
# ---------------------------------------------------------------------------


class TestMergeRequestConfig:
    def test_disable_all_tools_set_unconditionally(self) -> None:
        config = {"provider": "echo", "model": "test"}
        compaction_cfg = {
            "settings_overrides": {},
            "compaction_model": None,
        }
        merged = _merge_request_config(config, compaction_cfg)
        assert merged["disable_all_tools"] is True

    def test_settings_overrides_are_applied_without_enabling_tools(self) -> None:
        config = {"provider": "echo", "model": "test"}
        compaction_cfg = {
            "settings_overrides": {"temperature": 0.1, "model": "override-model"},
            "compaction_model": None,
        }
        merged = _merge_request_config(config, compaction_cfg)
        assert merged["disable_all_tools"] is True
        assert merged["temperature"] == 0.1
        assert merged["model"] == "override-model"

    def test_settings_overrides_cannot_reenable_tools(self) -> None:
        merged = _merge_request_config(
            {"provider": "echo", "model": "test"},
            {
                "settings_overrides": {"disable_all_tools": False},
                "compaction_model": None,
            },
        )
        assert merged["disable_all_tools"] is True

    def test_compaction_model_overrides_model(self) -> None:
        config = {"provider": "echo", "model": "test"}
        compaction_cfg = {
            "settings_overrides": {},
            "compaction_model": "kimi-compaction-model",
        }
        merged = _merge_request_config(config, compaction_cfg)
        assert merged["model"] == "kimi-compaction-model"
        assert merged["disable_all_tools"] is True

    def test_compaction_model_takes_precedence_over_settings_overrides_model(
        self,
    ) -> None:
        config = {"provider": "echo", "model": "test"}
        compaction_cfg = {
            "settings_overrides": {"model": "override-model"},
            "compaction_model": "kimi-compaction-model",
        }
        merged = _merge_request_config(config, compaction_cfg)
        assert merged["model"] == "kimi-compaction-model"

    def test_blank_compaction_model_ignored(self) -> None:
        config = {"provider": "echo", "model": "test"}
        compaction_cfg = {
            "settings_overrides": {},
            "compaction_model": "  ",
        }
        merged = _merge_request_config(config, compaction_cfg)
        assert merged["model"] == "test"


# ---------------------------------------------------------------------------
# Compacted session tests
# ---------------------------------------------------------------------------


class TestBuildCompactedSession:
    def test_compacted_session_replaces_compact_indices_with_summary(self) -> None:
        core, config = _core_and_config()
        session = _make_session(has_system=False)
        summary_text = build_compact_summary_text(
            "<current_focus>Testing</current_focus>"
            "<environment>Python</environment>"
            "<completed_tasks>None</completed_tasks>"
            "<active_issues>None</active_issues>"
            "<code_state>\n\n<file>\ntest.py\n</file>\n</code_state>"
            "<important_context>None</important_context>"
        )
        compact_indices = [0, 1, 2, 3]
        compacted = build_compacted_session(
            core,
            session,
            config,
            summary_text,
            compact_indices=compact_indices,
        )
        # [user: summary, user(4), assistant(5)]
        assert [message.role for message in compacted.messages] == [
            "user",
            "user",
            "assistant",
        ]
        assert compacted.messages[0].content == summary_text
        assert compacted.messages[1].content == "Answer exactly THREE."
        assert compacted.messages[2].content == "THREE"

    def test_compacted_session_with_explicit_range(self) -> None:
        core, config = _core_and_config()
        session = _make_session(has_system=False)
        summary_text = build_compact_summary_text(
            "<current_focus>Testing</current_focus>"
            "<environment>Python</environment>"
            "<completed_tasks>None</completed_tasks>"
            "<active_issues>None</active_issues>"
            "<code_state>x</code_state>"
            "<important_context>None</important_context>"
        )
        compact_indices = [0, 1, 2]
        compacted = build_compacted_session(
            core,
            session,
            config,
            summary_text,
            compact_indices=compact_indices,
        )
        # [user: summary, assistant(3), user(4), assistant(5)]
        assert [message.role for message in compacted.messages] == [
            "user",
            "assistant",
            "user",
            "assistant",
        ]
        assert compacted.messages[0].content == summary_text
        assert compacted.messages[1].content == "TWO"
        assert compacted.messages[2].content == "Answer exactly THREE."
        assert compacted.messages[3].content == "THREE"

    def test_compacted_session_preserves_leading_system(self) -> None:
        core, config = _core_and_config()
        session = _make_session(has_system=True)
        summary_text = build_compact_summary_text(
            "<current_focus>Testing</current_focus>"
            "<environment>Python</environment>"
            "<completed_tasks>None</completed_tasks>"
            "<active_issues>None</active_issues>"
            "<code_state>x</code_state>"
            "<important_context>None</important_context>"
        )
        compact_indices = [1, 2, 3, 4]
        compacted = build_compacted_session(
            core,
            session,
            config,
            summary_text,
            compact_indices=compact_indices,
        )
        # [system, user: summary, user(5), assistant(6)]
        assert [message.role for message in compacted.messages] == [
            "system",
            "user",
            "user",
            "assistant",
        ]
        assert compacted.messages[0].content == "System prompt"
        assert compacted.messages[1].content == summary_text
        assert compacted.messages[2].content == "Answer exactly THREE."
        assert compacted.messages[3].content == "THREE"

    def test_compacted_session_with_explicit_range_and_system(self) -> None:
        core, config = _core_and_config()
        session = _make_session(has_system=True)
        summary_text = build_compact_summary_text(
            "<current_focus>Testing</current_focus>"
            "<environment>Python</environment>"
            "<completed_tasks>None</completed_tasks>"
            "<active_issues>None</active_issues>"
            "<code_state>x</code_state>"
            "<important_context>None</important_context>"
        )
        compact_indices = [1, 2, 3]
        compacted = build_compacted_session(
            core,
            session,
            config,
            summary_text,
            compact_indices=compact_indices,
        )
        # [system, user: summary, assistant(4), user(5), assistant(6)]
        assert [message.role for message in compacted.messages] == [
            "system",
            "user",
            "assistant",
            "user",
            "assistant",
        ]
        assert compacted.messages[0].content == "System prompt"
        assert compacted.messages[1].content == summary_text
        assert compacted.messages[2].content == "TWO"
        assert compacted.messages[3].content == "Answer exactly THREE."
        assert compacted.messages[4].content == "THREE"

    def test_summary_message_has_compaction_metadata(self) -> None:
        core, config = _core_and_config()
        session = _make_session(has_system=False)
        summary_text = build_compact_summary_text(
            "<current_focus>Testing</current_focus>"
            "<environment>Python</environment>"
            "<completed_tasks>None</completed_tasks>"
            "<active_issues>None</active_issues>"
            "<code_state>x</code_state>"
            "<important_context>None</important_context>"
        )
        compacted = build_compacted_session(
            core,
            session,
            config,
            summary_text,
            compact_indices=[0, 1, 2, 3],
        )
        summary_metadata = compacted.messages[0].metadata or {}
        assert summary_metadata[_COMPACTION_METADATA_KEY]["is_compact_summary"] is True


# ---------------------------------------------------------------------------
# Build compact summary text tests
# ---------------------------------------------------------------------------


class TestBuildCompactSummaryText:
    def test_wraps_prefix_with_system_tags(self) -> None:
        summary_body = (
            "<current_focus>Task X</current_focus>"
            "<environment>Python</environment>"
            "<completed_tasks>None</completed_tasks>"
            "<active_issues>None</active_issues>"
            "<code_state>\n\n<file>\ntest.py\n</file>\n</code_state>"
            "<important_context>None</important_context>"
        )
        result = build_compact_summary_text(summary_body)
        assert result.startswith(
            "<system>Previous context has been compacted. Here is the compaction output:</system>"
        )
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
        assert result.startswith(
            "<system>Previous context has been compacted. Here is the compaction output:</system>"
        )
        assert not result.endswith("  ")

    def test_summary_body_follows_system_prefix_on_new_line(self) -> None:
        result = build_compact_summary_text("<current_focus>x</current_focus>")
        assert "</system>\n<current_focus>" in result


# ---------------------------------------------------------------------------
# Enablement tests
# ---------------------------------------------------------------------------


class TestIsCompactionEnabled:
    def test_enabled_true_and_type_kimi(self) -> None:
        assert (
            _is_compaction_enabled({"compaction": {"enabled": True, "type": "kimi"}})
            is True
        )

    def test_enabled_false(self) -> None:
        assert (
            _is_compaction_enabled({"compaction": {"enabled": False, "type": "kimi"}})
            is False
        )

    def test_wrong_type(self) -> None:
        assert (
            _is_compaction_enabled({"compaction": {"enabled": True, "type": "gemini"}})
            is False
        )

    def test_missing_compaction_block(self) -> None:
        assert _is_compaction_enabled({}) is False

    def test_compaction_block_not_dict(self) -> None:
        assert _is_compaction_enabled({"compaction": "kimi"}) is False

    def test_base_config_not_dict(self) -> None:
        assert _is_compaction_enabled(None) is False

    def test_enabled_must_be_true_not_truthy(self) -> None:
        assert (
            _is_compaction_enabled({"compaction": {"enabled": "true", "type": "kimi"}})
            is False
        )


class TestGetCompactionConfig:
    def test_defaults_when_no_compaction_block(self) -> None:
        cfg = _get_compaction_config({})
        assert cfg["max_preserved_messages"] == 2
        assert cfg["prompt"] is None
        assert cfg["settings_overrides"] == {}
        assert cfg["compaction_model"] is None
        assert cfg["enabled"] is False
        assert cfg["type"] is None

    def test_reads_values_from_compaction_block(self) -> None:
        base = {
            "compaction": {
                "enabled": True,
                "type": "kimi",
                "max_preserved_messages": 5,
                "compaction_model": "kimi-k2",
                "prompt": "Custom prompt",
                "settings_overrides": {"temperature": 0.2},
            }
        }
        cfg = _get_compaction_config(base)
        assert cfg["max_preserved_messages"] == 5
        assert cfg["compaction_model"] == "kimi-k2"
        assert cfg["prompt"] == "Custom prompt"
        assert cfg["settings_overrides"] == {"temperature": 0.2}
        assert cfg["enabled"] is True
        assert cfg["type"] == "kimi"

    def test_invalid_max_preserved_messages_falls_back_to_default(self) -> None:
        base = {"compaction": {"max_preserved_messages": "two"}}
        cfg = _get_compaction_config(base)
        assert cfg["max_preserved_messages"] == 2

    def test_negative_max_preserved_messages_is_retained_for_noop(self) -> None:
        base = {"compaction": {"max_preserved_messages": -1}}
        cfg = _get_compaction_config(base)
        assert cfg["max_preserved_messages"] == -1

    def test_blank_prompt_treated_as_none(self) -> None:
        base = {"compaction": {"prompt": "  "}}
        cfg = _get_compaction_config(base)
        assert cfg["prompt"] is None

    def test_blank_compaction_model_treated_as_none(self) -> None:
        base = {"compaction": {"compaction_model": "  "}}
        cfg = _get_compaction_config(base)
        assert cfg["compaction_model"] is None

    def test_settings_overrides_not_dict_uses_empty_dict(self) -> None:
        base = {"compaction": {"settings_overrides": "not a dict"}}
        cfg = _get_compaction_config(base)
        assert cfg["settings_overrides"] == {}


class TestGetEffectiveCompactionConfig:
    def test_top_level_session_model_override_wins(self) -> None:
        base = {
            "compaction": {
                "enabled": True,
                "type": "kimi",
                "compaction_model": "agent-model",
            }
        }
        effective = _get_effective_compaction_config(
            base,
            {**base, "compaction_model": "session-model"},
        )
        assert effective["compaction_model"] == "session-model"

    def test_agent_compaction_model_is_used_without_session_override(self) -> None:
        base = {
            "compaction": {
                "enabled": True,
                "type": "kimi",
                "compaction_model": "agent-model",
            }
        }
        effective = _get_effective_compaction_config(base, base)
        assert effective["compaction_model"] == "agent-model"


# ---------------------------------------------------------------------------
# Feature class tests
# ---------------------------------------------------------------------------


class TestKimiCompactionFeature:
    def test_config_schema_is_empty(self) -> None:
        feature = KimiCompactionFeature()
        schema = feature.get_config_schema()
        assert schema == {}

    def test_feature_ui_elements_include_compaction_model_and_message_action(
        self,
    ) -> None:
        feature = KimiCompactionFeature()
        elements = feature.get_ui_elements(
            config={"compaction": {"enabled": True, "type": "kimi"}},
            models=[{"id": "moonshot-v1", "name": "Moonshot V1"}],
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

    def test_feature_ui_elements_fall_back_to_text_when_models_are_unavailable(
        self,
    ) -> None:
        feature = KimiCompactionFeature()
        elements = feature.get_ui_elements(
            config={"compaction": {"enabled": True, "type": "kimi"}},
            models=[],
        )
        compaction_model = next(
            element
            for element in elements
            if element.get("ui_type") == "config"
            and element.get("key") == "compaction_model"
        )
        assert compaction_model["type"] == "text"
        assert "options" not in compaction_model

    def test_feature_ui_elements_empty_when_compaction_disabled(self) -> None:
        feature = KimiCompactionFeature()
        elements = feature.get_ui_elements(
            config={"compaction": {"enabled": False, "type": "kimi"}},
            models=[{"id": "moonshot-v1", "name": "Moonshot V1"}],
        )
        assert elements == []

    def test_feature_ui_elements_empty_when_type_not_kimi(self) -> None:
        feature = KimiCompactionFeature()
        elements = feature.get_ui_elements(
            config={"compaction": {"enabled": True, "type": "gemini"}},
            models=[{"id": "moonshot-v1", "name": "Moonshot V1"}],
        )
        assert elements == []

    def test_feature_ui_elements_returned_when_config_is_none(self) -> None:
        feature = KimiCompactionFeature()
        elements = feature.get_ui_elements(
            config=None,
            models=[{"id": "moonshot-v1", "name": "Moonshot V1"}],
        )
        assert len(elements) > 0

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

    def test_execute_action_returns_disabled_when_compaction_not_enabled(self) -> None:
        feature = KimiCompactionFeature()
        core, config = _core_and_config()
        session = _make_session(has_system=False)
        result = feature.execute_action(
            "compact_conversation",
            session,
            [],
            {},
            {"core": core, "config": config},
            {},
        )
        assert "error" in result
        assert result["error"]["type"] == "disabled"

    def test_execute_action_returns_disabled_when_type_not_kimi(self) -> None:
        feature = KimiCompactionFeature()
        core, config = _core_and_config()
        config = {**config, "compaction": {"enabled": True, "type": "gemini"}}
        session = _make_session(has_system=False)
        result = feature.execute_action(
            "compact_conversation",
            session,
            [],
            {},
            {"core": core, "config": config},
            {},
        )
        assert "error" in result
        assert result["error"]["type"] == "disabled"

    def test_execute_action_returns_invalid_range_for_empty_range(self) -> None:
        feature = KimiCompactionFeature()
        core, config = _core_and_config_with_compaction()
        session = _make_session(has_system=False)
        result = feature.execute_action(
            "compact_conversation",
            session,
            [],
            {"start": 0, "end": 0},
            {"core": core, "config": config, "base_config": config},
            {},
        )
        assert "error" in result
        assert result["error"]["type"] == "invalid_range"

    def test_execute_action_returns_noop_when_too_few_for_preserved_tail(self) -> None:
        feature = KimiCompactionFeature()
        core, config = _core_and_config_with_compaction()
        session = Session(
            session_id="short",
            messages=[
                Message(role="user", content="Hi"),
                Message(role="assistant", content="Hello"),
            ],
        )
        result = feature.execute_action(
            "compact_conversation",
            session,
            [],
            {},
            {"core": core, "config": config, "base_config": config},
            {},
        )
        # Session has 2 messages, but _MIN_COMPACTABLE_MESSAGE_COUNT is 3
        assert "error" in result
        assert result["error"]["type"] == "not_enough_messages"

    def test_execute_action_returns_noop_when_only_preserved_tail_exists(self) -> None:
        """A session with a leading system + 2 user/assistant messages passes
        the ``_MIN_COMPACTABLE_MESSAGE_COUNT`` check but yields no compactable
        range after preserved-tail, so the builder returns no-op.
        """
        feature = KimiCompactionFeature()
        core, config = _core_and_config_with_compaction()
        session = Session(
            session_id="system-plus-two",
            messages=[
                Message(role="system", content="System prompt"),
                Message(role="user", content="Hi"),
                Message(role="assistant", content="Hello"),
            ],
        )
        result = feature.execute_action(
            "compact_conversation",
            session,
            [],
            {},
            {"core": core, "config": config, "base_config": config},
            {},
        )
        assert result.get("status") == "noop"

    def test_execute_action_uses_corrected_request_contract(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        feature = KimiCompactionFeature()
        core, base_config = _core_and_config_with_compaction()
        effective_config = {
            **base_config,
            "compaction_model": "session-compaction-model",
            "compaction": {
                **base_config["compaction"],
                "settings_overrides": {"disable_all_tools": False},
            },
        }
        session = _make_session(has_system=True)
        captured: dict = {}

        def fake_run_compaction_request(
            request_core,
            request_session,
            request_config,
            context=None,
        ) -> str:
            captured["core"] = request_core
            captured["session"] = request_session
            captured["config"] = request_config
            captured["context"] = context
            return (
                "<current_focus>Testing</current_focus>"
                "<environment>Python</environment>"
                "<completed_tasks>None</completed_tasks>"
                "<active_issues>None</active_issues>"
                "<code_state>Current</code_state>"
                "<important_context>None</important_context>"
            )

        monkeypatch.setattr(
            _kcf, "_run_compaction_request", fake_run_compaction_request
        )

        result = feature.execute_action(
            "compact_conversation",
            session,
            [],
            {},
            {
                "core": core,
                "config": effective_config,
                "base_config": base_config,
            },
            {},
        )

        assert result["message"] == "Compacted conversation."
        request_session = captured["session"]
        assert request_session.messages[0].content == _GENERIC_COMPACTION_SYSTEM_PROMPT
        assert (
            "## Message 1\nRole: system\nContent:\nSystem prompt"
            in request_session.messages[1].content
        )
        assert captured["config"]["model"] == "session-compaction-model"
        assert captured["config"]["disable_all_tools"] is True


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
            payload["kinds"]["kimi_tools.kimi_compaction_feature.KimiCompactionFeature"]
            == "features"
        )
