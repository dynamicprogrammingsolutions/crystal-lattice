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

"""Kimi-style compaction feature plugin.

This plugin provides manual context compaction using Kimi CLI's priority-based
compression prompt format. It operates at the core level, using layered context
to access LLM capabilities.

The compaction prompt asks the model to compress conversation context according
to specific priorities (current task state, errors & solutions, code evolution,
system context, design decisions, TODO items) and produce a structured summary
with sections: <current_focus>, <environment>, <completed_tasks>,
<active_issues>, <code_state>, <important_context>.

Configuration is agent-level with explicit enablement control. The plugin is
only active when the agent's compaction config has:
- enabled: true
- type: "kimi"

Dependencies:
    agent_core (core SDK)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from agent_core import Message, Session


# ---------------------------------------------------------------------------
# Kimi-style compaction prompt (adapted from kimi-cli/src/kimi_cli/prompts/compact.md)
# ---------------------------------------------------------------------------

_KIMI_COMPACTION_PROMPT = """CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.

- Do NOT use ReadFile, WriteFile, StrReplaceFile, Glob, Grep, Shell, FetchURL, ReadMediaFile, WebSearch, or ANY other tool.
- You already have all the context you need in the conversation above.
- Tool calls will be REJECTED and will waste your only turn — you will fail the task.
- Your entire response must be plain text following the structured format below.

The above is a list of messages in an agent conversation. You are now given a task to compact this conversation context according to specific priorities and rules.

**Compression Priorities (in order):**
1. **Current Task State**: What is being worked on RIGHT NOW
2. **Errors & Solutions**: All encountered errors and their resolutions
3. **Code Evolution**: Final working versions only (remove intermediate attempts)
4. **System Context**: Project structure, dependencies, environment setup
5. **Design Decisions**: Architectural choices and their rationale
6. **TODO Items**: Unfinished tasks and known issues

**Compression Rules:**
- MUST KEEP: Error messages, stack traces, working solutions, current task
- MERGE: Similar discussions into single summary points
- REMOVE: Redundant explanations, failed attempts (keep lessons learned), verbose comments
- CONDENSE: Long code blocks → keep signatures + key logic only

**Special Handling:**
- For code: Keep full version if < 20 lines, otherwise keep signature + key logic
- For errors: Keep full error message + final solution
- For discussions: Extract decisions and action items only

**Required Output Structure:**

<current_focus>
[What we're working on now]
</current_focus>

<environment>
- [Key setup/config points]
- ...more...
</environment>

<completed_tasks>
- [Task]: [Brief outcome]
- ...more...
</completed_tasks>

<active_issues>
- [Issue]: [Status/Next steps]
- ...more...
</active_issues>

<code_state>

<file>
[filename]

**Summary:**
[What this code file does]

**Key elements:**
- [Important functions/classes]
- ...more...

**Latest version:**
[Critical code snippets in this file]
</file>

<file>
[filename]
...Similar as above...
</file>

...more files...
</code_state>

<important_context>
- [Any crucial information not covered above]
- ...more...
</important_context>

REMINDER: Do NOT call any tools. Respond with plain text only following the structured format above. Tool calls will be rejected and you will fail the task."""

_SUMMARY_HEADER = (
    "This session is being continued from a previous conversation that ran out "
    "of context. The summary below covers the earlier portion of the conversation."
)
_SUMMARY_FOOTER = (
    "If you need specific details from before compaction (like exact code snippets, "
    "error messages, or content you generated), read the full transcript at: {transcript_path}\n"
    "Continue the conversation from where it left off without asking the user any further questions. "
    "Resume directly — do not acknowledge the summary, do not recap what was happening, "
    "do not preface with \"I'll continue\" or similar. Pick up the last task as if the break never happened."
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
_COMPACTION_METADATA_KEY = "kimi_compaction"
_COMPACTION_MODEL_KEY = "compaction_model"
_PROMPT_KEY = "kimi_compaction_prompt"
_SETTINGS_OVERRIDES_KEY = "kimi_compaction_settings_overrides"
_MAX_PRESERVED_MESSAGES_KEY = "max_preserved_messages"
_TRANSCRIPT_FALLBACK = "<PROJECT_TRANSCRIPT>"
_MIN_COMPACTABLE_MESSAGE_COUNT = 3
_REQUIRED_SUMMARY_SECTIONS = [
    "<current_focus>",
    "<environment>",
    "<completed_tasks>",
    "<active_issues>",
    "<code_state>",
    "<important_context>",
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


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
        else _KIMI_COMPACTION_PROMPT
    )
    if not isinstance(instructions, str) or not instructions.strip():
        return prompt_text
    return (
        f"{prompt_text}\n\n"
        "**User's Custom Compaction Instruction:**\n"
        "The user has specifically requested the following focus during compaction. "
        "You MUST prioritize this instruction above the default compression priorities:\n"
        f"{instructions.strip()}"
    )


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
    context: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    final_messages: List[Dict[str, Any]] = []
    for event in core.send_request_stream(session, config, context=context):
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
    context: Dict[str, Any] | None = None,
) -> str:
    final_messages = _collect_final_messages_from_stream(core, session, config, context=context)
    for message in reversed(final_messages):
        if message.get("role") != "assistant":
            continue
        content = _message_text(message.get("content"))
        if content.strip():
            return content
    raise RuntimeError(
        "[kimi_compaction] compaction request produced no assistant summary"
    )


def extract_summary_text(response_text: str) -> str:
    """Extract the structured summary from the model response.

    Kimi-style compaction produces output with XML-style section tags.
    We look for the structured sections and extract the content between
    the first <current_focus> and the last </important_context>.
    If no structured sections are found, we fall back to the full text.
    """
    # Try to find the structured output between the section tags
    first_section = None
    last_section_end = None

    for tag in _REQUIRED_SUMMARY_SECTIONS:
        match = re.search(re.escape(tag), response_text)
        if match and (first_section is None or match.start() < first_section):
            first_section = match.start()

    if first_section is not None:
        # Find the closing tag of the last section
        last_close = re.search(r"</important_context>", response_text)
        if last_close:
            return response_text[first_section : last_close.end()].strip()

    # Fallback: return the full text stripped
    text = response_text.strip()
    if not text:
        raise ValueError(
            "[kimi_compaction] empty response from compaction request"
        )
    return text


def extract_summary_sections(summary_text: str) -> List[str]:
    """Extract section tag names from the summary text."""
    return re.findall(r"<(current_focus|environment|completed_tasks|active_issues|code_state|important_context)>", summary_text)


def validate_summary_text(summary_text: str) -> None:
    missing = [
        section for section in _REQUIRED_SUMMARY_SECTIONS if section not in summary_text
    ]
    if missing:
        raise ValueError(
            "[kimi_compaction] summary is missing required sections: "
            + ", ".join(missing)
        )


def build_compact_summary_text(
    summary_text: str,
    *,
    transcript_path: str,
) -> str:
    cleaned = summary_text.strip()
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
            "[kimi_compaction] compacted session is missing rebuilt native history"
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
            from pathlib import Path
            return str(Path(root_dir) / f"{session.session_id}.json")
        except Exception:
            return _TRANSCRIPT_FALLBACK
    return _TRANSCRIPT_FALLBACK


# ---------------------------------------------------------------------------
# Feature plugin class
# ---------------------------------------------------------------------------


class KimiCompactionFeature:
    """Feature-level plugin implementing Kimi-style context compaction.

    This plugin operates at the core level, using the layered context approach:
    - Layer 1 (core): Uses ``context["core"]`` for session/message operations
    - Layer 2 (app): Optionally uses ``context.get("app")`` for enhanced features

    Configuration is read from the agent config under the ``compaction`` key:

    .. code-block:: yaml

        compaction:
          enabled: false          # Must be true to enable
          type: null              # Must be "kimi" for this plugin
          compaction_model: null  # Optional model override for compaction requests
          prompt: null            # Custom prompt override
          settings_overrides: {}  # Model/params for compaction requests
          max_preserved_messages: 2  # Messages to preserve at end (for default range)

    The plugin is only active when both ``enabled`` is true and ``type`` is
    ``"kimi"``.
    """

    name = "kimi_compaction"
    version = "0.1.0"
    priority = 100

    COMPACTION_TYPE = "kimi"

    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # FeaturePlugin protocol methods
    # ------------------------------------------------------------------

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            _COMPACTION_MODEL_KEY: {
                "type": "string",
                "required": False,
                "default": "",
                "description": (
                    "Optional model used for Kimi compaction. Leave empty to use "
                    "the normal request model."
                ),
            },
            _PROMPT_KEY: {
                "type": "string",
                "required": False,
                "description": "Optional override for the Kimi compaction prompt.",
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

    def get_models(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        return []

    def required_tags(self) -> List[str]:
        return []

    def forbidden_tags(self) -> List[str]:
        return []

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return list(messages)

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[list[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]], Dict[str, Any]]:
        return list(final_messages), list(native_messages), state

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
                        "will be compacted into a Kimi-style structured summary."
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
                        "The messages up to here will be compacted into a "
                        "Kimi-style structured summary."
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
                "description": "Compact a selected conversation range into a Kimi-style structured summary.",
                "inputs": {
                    "start": {"type": "integer", "required": False},
                    "end": {"type": "integer", "required": False},
                    "end_inclusive": {"type": "boolean", "required": False},
                    "instructions": {"type": "string", "required": False},
                },
            }
        ]

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
                    "message": "Context must include 'core' for Kimi compaction.",
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
            context=context,
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
    "KimiCompactionFeature",
    "build_compact_summary_text",
    "build_compacted_session",
    "build_compaction_prompt",
    "build_compaction_request_session",
    "build_compaction_session",
    "extract_summary_sections",
    "extract_summary_text",
    "validate_summary_text",
]