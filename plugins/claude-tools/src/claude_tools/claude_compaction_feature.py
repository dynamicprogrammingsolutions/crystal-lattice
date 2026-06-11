# Licensing note:
# This file may contain both original code authored for this repository and
# material derived from or adapted from Claude Code or other
# Anthropic-authored materials.
#
# Original code in this file authored for this repository is licensed under
# the Apache License, Version 2.0.
#
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
#
# Anthropic-derived material in this file is not licensed by us under
# Apache-2.0, and are instead subject to Anthropic's terms:
#
# © Anthropic PBC. All rights reserved. Use is subject to Anthropic's
# Commercial Terms of Service:
# https://www.anthropic.com/legal/commercial-terms

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_core import Message, Session


_COMPACTION_PROMPT = """CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.

- Do NOT use Read, Bash, Grep, Glob, Edit, Write, or ANY other tool.
- You already have all the context you need in the conversation above.
- Tool calls will be REJECTED and will waste your only turn — you will fail the task.
- Your entire response must be plain text: an <analysis> block followed by a <summary> block.

Your task is to create a detailed summary of the conversation so far, paying close attention to the user's explicit requests and your previous actions.
This summary should be thorough in capturing technical details, code patterns, and architectural decisions that would be essential for continuing development work without losing context.

Before providing your final summary, wrap your analysis in <analysis> tags to organize your thoughts and ensure you've covered all necessary points. In your analysis process:

1. Chronologically analyze each message and section of the conversation. For each section thoroughly identify:
   - The user's explicit requests and intents
   - Your approach to addressing the user's requests
   - Key decisions, technical concepts and code patterns
   - Specific details like:
     - file names
     - full code snippets
     - function signatures
     - file edits
   - Errors that you ran into and how you fixed them
   - Pay special attention to specific user feedback that you received, especially if the user told you to do something differently.
   - Note any security-relevant instructions or constraints the user stated (e.g., sensitive files or data to avoid, operations that must not be performed, credential or secret handling rules). These MUST be preserved verbatim in the summary so they continue to apply after compaction.
2. Double-check for technical accuracy and completeness, addressing each required element thoroughly.

Your summary should include the following sections:

1. Primary Request and Intent: Capture all of the user's explicit requests and intents in detail
2. Key Technical Concepts: List all important technical concepts, technologies, and frameworks discussed.
3. Files and Code Sections: Enumerate specific files and code sections examined, modified, or created. Pay special attention to the most recent messages and include full code snippets where applicable and include a summary of why this file read or edit is important.
4. Errors and fixes: List all errors that you ran into, and how you fixed them. Pay special attention to specific user feedback that you received, especially if the user told you to do something differently.
5. Problem Solving: Document problems solved and any ongoing troubleshooting efforts.
6. All user messages: List ALL user messages that are not tool results. These are critical for understanding the users' feedback and changing intent. Preserve any security-relevant instructions or constraints verbatim so they remain in effect after compaction.
7. Pending Tasks: Outline any pending tasks that you have explicitly been asked to work on.
8. Current Work: Describe in detail precisely what was being worked on immediately before this summary request, paying special attention to the most recent messages from both user and assistant. Include file names and code snippets where applicable.
9. Optional Next Step: List the next step that you will take that is related to the most recent work you were doing. IMPORTANT: ensure that this step is DIRECTLY in line with the user's most recent explicit requests, and the task you were working on immediately before this summary request. If your last task was concluded, then only list next steps if they are explicitly in line with the users request. Do not start on tangential requests or really old requests that were already completed without confirming with the user first.
                       If there is a next step, include direct quotes from the most recent conversation showing exactly what task you were working on and where you left off. This should be verbatim to ensure there's no drift in task interpretation.

Here's an example of how your output should be structured:

<example>
<analysis>
[Your thought process, ensuring all points are covered thoroughly and accurately]
</analysis>

<summary>
1. Primary Request and Intent:
   [Detailed description]

2. Key Technical Concepts:
   - [Concept 1]
   - [Concept 2]
   - [...]

3. Files and Code Sections:
   - [File Name 1]
      - [Summary of why this file is important]
      - [Summary of the changes made to this file, if any]
      - [Important Code Snippet]
   - [File Name 2]
      - [Important Code Snippet]
   - [...]

4. Errors and fixes:
    - [Detailed description of error 1]:
      - [How you fixed the error]
      - [User feedback on the error if any]
    - [...]

5. Problem Solving:
   [Description of solved problems and ongoing troubleshooting]

6. All user messages:
    - [Detailed non tool use user message]
    - [...]

7. Pending Tasks:
   - [Task 1]
   - [Task 2]
   - [...]

8. Current Work:
   [Precise description of current work]

9. Optional Next Step:
   [Optional Next step to take]

</summary>
</example>

Please provide your summary based on the conversation so far, following this structure and ensuring precision and thoroughness in your response.

There may be additional summarization instructions provided in the included context. If so, remember to follow these instructions when creating the above summary. Examples of instructions include:
<example>
## Compact Instructions
When summarizing the conversation focus on typescript code changes and also remember the mistakes you made and how you fixed them.
</example>

<example>
# Summary instructions
When you are using compact - please focus on test output and code changes. Include file reads verbatim.
</example>


REMINDER: Do NOT call any tools. Respond with plain text only — an <analysis> block followed by a <summary> block. Tool calls will be rejected and you will fail the task."""

_SUMMARY_HEADER = (
    "This session is being continued from a previous conversation that ran out "
    "of context. The summary below covers the earlier portion of the conversation."
)
_SUMMARY_FOOTER = (
    "If you need specific details from before compaction (like exact code snippets, "
    "error messages, or content you generated), read the full transcript at: {transcript_path}\n"
    "Continue the conversation from where it left off without asking the user any further questions. "
    "Resume directly — do not acknowledge the summary, do not recap what was happening, "
    'do not preface with "I\'ll continue" or similar. Pick up the last task as if the break never happened.'
)
_LOCAL_COMMAND_ARTIFACT = (
    "<local-command-caveat>Caveat: The messages below were generated by the user while "
    "running local commands. DO NOT respond to these messages or otherwise consider them "
    "in your response unless the user explicitly asks about them.</local-command-caveat>\n"
    "<command-name>/compact</command-name>\n"
    "<command-message>compact</command-message>\n"
    "<command-args></command-args>\n"
    "<local-command-stdout>Compacted </local-command-stdout>"
)
_NO_RESPONSE_REQUESTED = "No response requested."
_COMPACTION_METADATA_KEY = "claude_compaction"
_COMPACTION_MODEL_KEY = "compaction_model"
_PROMPT_KEY = "claude_compaction_prompt"
_SETTINGS_OVERRIDES_KEY = "claude_compaction_settings_overrides"
_TRANSCRIPT_FALLBACK = "<PROJECT_TRANSCRIPT>"
_MIN_COMPACTABLE_MESSAGE_COUNT = 3
_REQUIRED_SUMMARY_SECTIONS = [
    "1. Primary Request and Intent:",
    "2. Key Technical Concepts:",
    "3. Files and Code Sections:",
    "4. Errors and fixes:",
    "5. Problem Solving:",
    "6. All user messages:",
    "7. Pending Tasks:",
    "8. Current Work:",
    "9. Optional Next Step:",
]


def _strip_native_history(metadata: Any) -> Dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    sanitized = dict(metadata)
    sanitized.pop("native_messages", None)
    sanitized.pop("native_messages_integrity", None)
    return sanitized


def _merge_request_config(config: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(config)
    overrides = config.get(_SETTINGS_OVERRIDES_KEY)
    if isinstance(overrides, dict):
        merged.update(overrides)
    compaction_model = config.get(_COMPACTION_MODEL_KEY)
    if isinstance(compaction_model, str) and compaction_model.strip():
        merged["model"] = compaction_model.strip()
    return merged


def build_compaction_prompt(
    instructions: str | None = None,
    *,
    prompt_override: str | None = None,
) -> str:
    prompt_text = (
        prompt_override.strip()
        if isinstance(prompt_override, str) and prompt_override.strip()
        else _COMPACTION_PROMPT
    )
    if not isinstance(instructions, str) or not instructions.strip():
        return prompt_text
    return f"{prompt_text}\n\n" "## Compact Instructions\n" f"{instructions.strip()}"


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return str(content)


def build_compaction_session(
    session: Session,
    *,
    prompt_text: str,
) -> Session:
    messages = list(session.messages)
    if (
        messages
        and messages[-1].role == "user"
        and isinstance(messages[-1].content, str)
    ):
        previous = messages[-1]
        separator = "" if previous.content.endswith("\n") else "\n"
        messages[-1] = Message(
            role=previous.role,
            content=f"{previous.content}{separator}{prompt_text}",
            metadata=previous.metadata,
            multipart_content=previous.multipart_content,
            tool_result=previous.tool_result,
        )
    else:
        messages.append(Message(role="user", content=prompt_text, metadata={}))

    return Session(
        session_id=session.session_id,
        messages=messages,
        metadata=_strip_native_history(session.metadata),
    )


def _normalize_slice_bounds(
    message_count: int,
    start: int | None,
    end: int | None,
    *,
    end_inclusive: bool = False,
) -> tuple[int, int]:
    def _bound(value: int | None, default: int) -> int:
        if value is None:
            return default
        idx = value
        if idx < 0:
            idx = message_count + idx
        if idx < 0:
            return 0
        if idx > message_count:
            return message_count
        return idx

    start_idx = _bound(start, 0)
    end_idx = _bound(end, message_count)
    if end_inclusive and end is not None:
        end_idx = min(end_idx + 1, message_count)
    if start_idx >= end_idx:
        raise ValueError("range selects no messages")
    return start_idx, end_idx


def _has_leading_system_message(session: Session) -> bool:
    return bool(session.messages) and session.messages[0].role == "system"


def _resolve_compaction_indices(
    session: Session,
    *,
    start: int | None,
    end: int | None,
    end_inclusive: bool = False,
) -> tuple[List[int], List[int]]:
    start_idx, end_idx = _normalize_slice_bounds(
        len(session.messages),
        start,
        end,
        end_inclusive=end_inclusive,
    )
    has_leading_system = _has_leading_system_message(session)
    selected_indices = list(range(start_idx, end_idx))
    target_indices = [
        idx for idx in selected_indices if not (has_leading_system and idx == 0)
    ]
    if not target_indices:
        raise ValueError("range selects no compactable messages")
    request_indices = list(target_indices)
    if has_leading_system and 0 not in request_indices:
        request_indices = [0, *request_indices]
    return target_indices, request_indices


def build_compaction_request_session(
    session: Session,
    *,
    prompt_text: str,
    start: int | None = None,
    end: int | None = None,
    end_inclusive: bool = False,
) -> tuple[Session, List[int], List[int]]:
    target_indices, request_indices = _resolve_compaction_indices(
        session,
        start=start,
        end=end,
        end_inclusive=end_inclusive,
    )
    request_session = Session(
        session_id=session.session_id,
        messages=[session.messages[idx] for idx in request_indices],
        metadata=_strip_native_history(session.metadata),
    )
    return (
        build_compaction_session(request_session, prompt_text=prompt_text),
        target_indices,
        request_indices,
    )


def _collect_final_messages_from_stream(
    core: Any,
    session: Session,
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    final_messages: List[Dict[str, Any]] = []
    for event in core.send_request_stream(session, config):
        if event.get("type") != "final":
            continue
        raw_messages = event.get("messages")
        if isinstance(raw_messages, list):
            final_messages = [item for item in raw_messages if isinstance(item, dict)]
    return final_messages


def _run_compaction_request(
    core: Any,
    session: Session,
    config: Dict[str, Any],
) -> str:
    final_messages = _collect_final_messages_from_stream(core, session, config)
    for message in reversed(final_messages):
        if message.get("role") != "assistant":
            continue
        content = _message_text(message.get("content"))
        if content.strip():
            return content
    raise RuntimeError(
        "[claude_compaction] compaction request produced no assistant summary"
    )


def extract_summary_text(response_text: str) -> str:
    match = re.search(r"<summary>\s*(.*?)\s*</summary>", response_text, re.DOTALL)
    if match is None:
        raise ValueError(
            "[claude_compaction] missing <summary> block in compaction response"
        )
    summary_text = match.group(1).strip()
    if not summary_text:
        raise ValueError(
            "[claude_compaction] empty <summary> block in compaction response"
        )
    return summary_text


def extract_summary_sections(summary_text: str) -> List[str]:
    return re.findall(r"(?m)^[0-9]+\.\s+[^:\n]+:", summary_text)


def extract_prompt_sections(prompt_text: str) -> List[str]:
    return [line.rstrip() for line in re.findall(r"(?m)^[0-9]+\.\s+.+$", prompt_text)]


def validate_summary_text(summary_text: str) -> None:
    missing = [
        section for section in _REQUIRED_SUMMARY_SECTIONS if section not in summary_text
    ]
    if missing:
        raise ValueError(
            "[claude_compaction] summary is missing required sections: "
            + ", ".join(missing)
        )


def build_compact_summary_text(
    summary_text: str,
    *,
    transcript_path: str,
) -> str:
    cleaned = summary_text.strip()
    validate_summary_text(cleaned)
    return (
        f"{_SUMMARY_HEADER}\n\n"
        f"Summary:\n{cleaned}\n\n"
        f"{_SUMMARY_FOOTER.format(transcript_path=transcript_path)}"
    )


def _summary_message_metadata(summary_text: str) -> Dict[str, Any]:
    return {
        _COMPACTION_METADATA_KEY: {
            "kind": "summary",
            "is_compact_summary": True,
            "is_visible_in_transcript_only": True,
            "summary_sections": extract_summary_sections(summary_text),
        }
    }


def _local_command_message_metadata() -> Dict[str, Any]:
    return {
        _COMPACTION_METADATA_KEY: {
            "kind": "local_command",
            "command": "/compact",
            "is_replay": True,
        }
    }


def _local_command_result_metadata() -> Dict[str, Any]:
    return {
        _COMPACTION_METADATA_KEY: {
            "kind": "local_command_result",
            "is_replay": True,
        }
    }


def _leading_system_message_count(session: Session) -> int:
    count = 0
    for message in session.messages:
        if message.role != "system":
            break
        count += 1
    return count


def _native_messages_from_session(session: Session) -> List[Dict[str, Any]]:
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    native = metadata.get("native_messages")
    if not isinstance(native, list) or not all(
        isinstance(item, dict) for item in native
    ):
        raise RuntimeError(
            "[claude_compaction] compacted session is missing rebuilt native history"
        )
    return [item for item in native if isinstance(item, dict)]


def _rebuild_context(context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(context, dict):
        return context
    return {
        key: value for key, value in context.items() if key not in {"core", "config"}
    }


def build_compacted_session(
    core: Any,
    session: Session,
    config: Dict[str, Any],
    summary_text: str,
    *,
    start: int | None = None,
    end: int | None = None,
    end_inclusive: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> Session:
    rebuilt = core.rebuild_native_history(
        session,
        config,
        context=_rebuild_context(context),
    )
    target_indices, _request_indices = _resolve_compaction_indices(
        rebuilt,
        start=start,
        end=end,
        end_inclusive=end_inclusive,
    )
    remove_indices = list(target_indices)
    session_after_delete = core.slice_session(
        rebuilt,
        config,
        remove_indices=remove_indices,
    )

    insert_after = target_indices[0] - 1
    compacted = core.add_message(
        session_after_delete,
        "user",
        summary_text,
        metadata=_summary_message_metadata(summary_text),
        config=config,
        after_index=insert_after,
        context=context,
    )
    compacted = core.add_message(
        compacted,
        "user",
        _LOCAL_COMMAND_ARTIFACT,
        metadata=_local_command_message_metadata(),
        config=config,
        after_index=insert_after + 1,
        context=context,
    )
    compacted = core.add_message(
        compacted,
        "assistant",
        _NO_RESPONSE_REQUESTED,
        metadata=_local_command_result_metadata(),
        config=config,
        after_index=insert_after + 2,
        context=context,
    )
    return compacted


def _session_transcript_path(
    context: Optional[Dict[str, Any]],
    session: Session,
) -> str:
    if not isinstance(context, dict):
        return _TRANSCRIPT_FALLBACK
    app = context.get("app")
    store = getattr(app, "_session_store", None)
    path_for = getattr(store, "_path_for", None)
    if callable(path_for):
        try:
            return str(path_for(session.session_id))
        except Exception:
            return _TRANSCRIPT_FALLBACK
    root_dir = getattr(store, "_root_dir", None)
    if root_dir is not None:
        try:
            return str(Path(root_dir) / f"{session.session_id}.json")
        except Exception:
            return _TRANSCRIPT_FALLBACK
    return _TRANSCRIPT_FALLBACK


class ClaudeCompactionFeature:
    name = "claude_compaction"
    version = "0.1.0"
    priority = 100

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            _COMPACTION_MODEL_KEY: {
                "type": "string",
                "required": False,
                "default": "",
                "description": (
                    "Optional model used for Claude compaction. Leave empty to use "
                    "the normal request model."
                ),
            },
            _PROMPT_KEY: {
                "type": "string",
                "required": False,
                "description": "Optional override for the Claude compaction prompt.",
            },
            _SETTINGS_OVERRIDES_KEY: {
                "type": "object",
                "required": False,
                "description": (
                    "Optional request settings overrides applied only to the "
                    "internal compaction request."
                ),
            },
        }

    def init(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        return state

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = config, tags
        model_options: List[Dict[str, str]] = []
        for model in models or []:
            if not isinstance(model, dict):
                continue
            model_id = model.get("id")
            if model_id is None:
                continue
            model_name = model.get("name")
            model_options.append(
                {
                    "label": (
                        str(model_name) if model_name is not None else str(model_id)
                    ),
                    "value": str(model_id),
                }
            )

        use_dropdown = len(model_options) > 0
        return [
            {
                "ui_type": "config",
                "type": "dropdown" if use_dropdown else "text",
                "key": _COMPACTION_MODEL_KEY,
                "label": "Compaction model",
                "placeholder": "Use current model",
                **({"options": model_options} if use_dropdown else {}),
            },
            {
                "ui_type": "session_action",
                "id": "compact_conversation",
                "label": "Compact conversation",
                "icon": "archive",
                "order": 46,
                "action_id": "compact_conversation",
                "action_owner": "feature",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "start": "$dialog.start",
                    "end": "$dialog.end",
                    "instructions": "$dialog.instructions",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Compact conversation",
                    "message": (
                        "Python-style range (start:end). The selected messages "
                        "will be compacted into a Claude-style compact summary."
                    ),
                    "inputs": [
                        {
                            "name": "start",
                            "type": "integer",
                            "label": "Start index",
                            "required": False,
                            "placeholder": "e.g. 0 or -10 (leave blank for start)",
                        },
                        {
                            "name": "end",
                            "type": "integer",
                            "label": "End index",
                            "required": False,
                            "placeholder": "e.g. 10 or -1 (leave blank for end)",
                        },
                        {
                            "name": "instructions",
                            "type": "multiline",
                            "label": "Instructions",
                            "required": False,
                            "placeholder": "Optional extra instructions for the compaction summary",
                        },
                    ],
                },
            },
            {
                "ui_type": "message_action",
                "id": "compact_up_to_here",
                "label": "Compact messages up to here",
                "icon": "archive",
                "order": 25,
                "action_id": "compact_conversation",
                "action_owner": "feature",
                "fixed_params": {"start": 0, "end_inclusive": True},
                "param_map": {
                    "session_id": "$session.session_id",
                    "end": "$message.index",
                    "instructions": "$dialog.instructions",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Compact messages up to here",
                    "message": (
                        "The messages up to here will be compacted into a Claude-style compact summary."
                    ),
                    "inputs": [
                        {
                            "name": "instructions",
                            "type": "multiline",
                            "label": "Instructions",
                            "required": False,
                            "placeholder": "Optional extra instructions for the compaction summary",
                        }
                    ],
                },
            },
        ]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "compact_conversation",
                "label": "Compact conversation",
                "description": "Compact a selected conversation range into a Claude-style summary.",
                "inputs": {
                    "start": {"type": "integer", "required": False},
                    "end": {"type": "integer", "required": False},
                    "end_inclusive": {"type": "boolean", "required": False},
                    "instructions": {"type": "string", "required": False},
                },
            }
        ]

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        _ = messages
        return list(native_messages)

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        _ = native_messages
        return list(messages)

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return list(final_messages), list(native_messages), state

    def execute_action(
        self,
        action_id: str,
        session: Session,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action_id != "compact_conversation":
            return {
                "native_messages": list(native_messages),
                "error": {
                    "type": "unknown_action",
                    "message": f"Unknown action: {action_id}",
                },
            }

        if len(session.messages) == 0:
            return {
                "native_messages": list(native_messages),
                "error": {
                    "type": "no_messages",
                    "message": "Error: No messages to compact",
                },
            }

        if len(session.messages) < _MIN_COMPACTABLE_MESSAGE_COUNT:
            return {
                "native_messages": list(native_messages),
                "error": {
                    "type": "not_enough_messages",
                    "message": "Not enough messages to compact.",
                },
            }

        if not isinstance(context, dict) or context.get("core") is None:
            return {
                "native_messages": list(native_messages),
                "error": {
                    "type": "missing_core",
                    "message": "Context must include 'core' for Claude compaction.",
                },
            }

        request_config = context.get("config")
        if not isinstance(request_config, dict):
            request_config = (
                state.get("config") if isinstance(state.get("config"), dict) else {}
            )
        prepared_session = context["core"].rebuild_native_history(
            session,
            request_config,
            context=_rebuild_context(context),
        )

        start_raw = params.get("start")
        end_raw = params.get("end")
        end_inclusive = params.get("end_inclusive", False)
        start_int = start_raw if isinstance(start_raw, int) else None
        end_int = end_raw if isinstance(end_raw, int) else None
        try:
            target_indices, _request_indices = _resolve_compaction_indices(
                prepared_session,
                start=start_int,
                end=end_int,
                end_inclusive=bool(end_inclusive),
            )
        except ValueError as exc:
            return {
                "native_messages": list(native_messages),
                "error": {
                    "type": "invalid_range",
                    "message": str(exc),
                },
            }
        if len(target_indices) < _MIN_COMPACTABLE_MESSAGE_COUNT:
            return {
                "native_messages": list(native_messages),
                "error": {
                    "type": "not_enough_messages",
                    "message": "Not enough messages to compact.",
                },
            }

        instructions = params.get("instructions")
        instructions_text = (
            instructions.strip() if isinstance(instructions, str) else None
        )
        prompt_override = request_config.get(_PROMPT_KEY)
        prompt_text = build_compaction_prompt(
            instructions_text,
            prompt_override=(
                prompt_override if isinstance(prompt_override, str) else None
            ),
        )
        compaction_session, _target_indices, _request_indices = (
            build_compaction_request_session(
                prepared_session,
                prompt_text=prompt_text,
                start=start_int,
                end=end_int,
                end_inclusive=bool(end_inclusive),
            )
        )
        compaction_response = _run_compaction_request(
            context["core"],
            compaction_session,
            _merge_request_config(request_config),
        )
        summary_body = extract_summary_text(compaction_response)
        transcript_path = _session_transcript_path(context, session)
        summary_text = build_compact_summary_text(
            summary_body,
            transcript_path=transcript_path,
        )
        compacted_session = build_compacted_session(
            context["core"],
            prepared_session,
            request_config,
            summary_text,
            start=start_int,
            end=end_int,
            end_inclusive=bool(end_inclusive),
            context=context,
        )
        compacted_native = _native_messages_from_session(compacted_session)
        return {
            "native_messages": compacted_native,
            "session_metadata": {
                _COMPACTION_METADATA_KEY: {
                    "compacted": True,
                    "summary_sections": extract_summary_sections(summary_text),
                    "transcript_path": transcript_path,
                }
            },
            "message": "Compacted conversation.",
            "compact_summary_text": summary_text,
            "summary_sections": extract_summary_sections(summary_text),
        }


__all__ = [
    "ClaudeCompactionFeature",
    "build_compact_summary_text",
    "build_compacted_session",
    "build_compaction_prompt",
    "build_compaction_request_session",
    "build_compaction_session",
    "extract_prompt_sections",
    "extract_summary_sections",
    "extract_summary_text",
    "validate_summary_text",
]
