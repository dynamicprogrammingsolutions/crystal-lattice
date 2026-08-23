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

This plugin provides manual context compaction that targets parity with
``kimi-cli``'s ``SimpleCompaction`` for the compaction request shape, system
prompt, tool suppression, preserved-tail behavior, summary injection format,
prompt body, and enablement enforcement.

Manual actions
--------------

Two session actions are exposed:

- ``compact_conversation`` — compact the full history or an explicit
  ``start``/``end`` range.
- ``compact_up_to_here`` — compact the prefix ending at an anchor message
  (message-anchored, explicit ``end``).

Compaction request
------------------

The compaction request session contains exactly two messages:

1. ``system``: ``"You are a helpful assistant that compacts conversation
   context."`` (a generic compactor prompt, not the agent's normal system
   message).
2. ``user``: a single synthetic message built from the compactable range.

The synthetic user message flattens each message in the compactable prefix,
including a selected leading agent system message, into:

::

    ## Message N
    Role: <role>
    Content:
    <text-only content>

followed by ``\n<compaction prompt>``. Only text content is included.
Structured tool-call and tool-result payloads, media parts, and think parts are
dropped; textual content from any message role is retained.

The merged compaction request config sets ``disable_all_tools: True``
after all configurable request overrides so no tool schemas are serialized
into the request payload.

Preserved tail
--------------

When no explicit ``end`` is supplied, the last ``max_preserved_messages``
user/assistant messages (default 2) are preserved verbatim and excluded from
the synthetic compaction message. If fewer than ``max_preserved_messages``
user/assistant messages exist in the compactable range, the action returns a
no-op result instead of forcing compaction with no preserved tail.

When an explicit ``end`` is supplied (including ``compact_up_to_here``), the
selected range is compacted exactly and preserved-tail does not apply.

Compacted session
-----------------

The compacted session replaces the compacted range with one user message whose
content is:

::

    <system>Previous context has been compacted. Here is the compaction output:</system>
    <structured summary body>

The structured summary body uses ``kimi-cli``'s required XML-style sections:
``<current_focus>``, ``<environment>``, ``<completed_tasks>``,
``<active_issues>``, ``<code_state>``, and ``<important_context>``. The prompt
requests those sections, but a non-empty unstructured model response is
retained rather than rejected, matching ``kimi-cli``. No assistant
acknowledgment message is added. Preserved-tail messages, if any, follow the
summary user message unchanged.

Enablement
----------

The plugin is only active when the agent's ``compaction`` config block has:

::

    compaction:
      enabled: true
      type: "kimi"
      max_preserved_messages: 2   # optional, default 2
      compaction_model: null      # optional, overrides the request model
      prompt: null                # optional, overrides the compaction prompt
      settings_overrides: {}      # optional, merged into the compaction request config

When ``config`` is provided to ``get_ui_elements`` and compaction is not
enabled, ``get_ui_elements`` returns ``[]``. When ``execute_action`` is called
and compaction is not enabled, it returns an error with ``type: "disabled"``.

Deviations from ``kimi-cli`` (auto-compaction, checkpoint/context rewrite,
D-Mail) are documented in the specification under
``plugins/kimi-tools/docs/development/specifications/kimi-compaction-parity/``.

Dependencies:
    agent_core (core SDK)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from agent_core import Message, Session


# ---------------------------------------------------------------------------
# Kimi-style compaction prompt (verbatim from kimi-cli/src/kimi_cli/prompts/compact.md)
# ---------------------------------------------------------------------------

_KIMI_COMPACTION_PROMPT = """
---

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
"""

_COMPACTION_PREFIX = (
    "Previous context has been compacted. Here is the compaction output:"
)
_GENERIC_COMPACTION_SYSTEM_PROMPT = (
    "You are a helpful assistant that compacts conversation context."
)
_COMPACTION_METADATA_KEY = "kimi_compaction"
_MIN_COMPACTABLE_MESSAGE_COUNT = 3
_DEFAULT_MAX_PRESERVED_MESSAGES = 2
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


def _rebuild_context(context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(context, dict):
        return context
    return {
        key: value for key, value in context.items() if key not in {"core", "config"}
    }


def _is_compaction_enabled(base_config: Any) -> bool:
    """Return ``True`` only when ``compaction.enabled`` is ``True`` and ``compaction.type`` is ``"kimi"``."""
    if not isinstance(base_config, dict):
        return False
    compaction_cfg = base_config.get("compaction")
    if not isinstance(compaction_cfg, dict):
        return False
    enabled = compaction_cfg.get("enabled", False)
    compaction_type = compaction_cfg.get("type")
    return enabled is True and compaction_type == "kimi"


def _get_compaction_config(base_config: Any) -> Dict[str, Any]:
    """Extract compaction settings from the agent ``compaction`` block with defaults."""
    if not isinstance(base_config, dict):
        base_config = {}
    compaction_cfg = base_config.get("compaction")
    if not isinstance(compaction_cfg, dict):
        compaction_cfg = {}

    max_preserved = compaction_cfg.get(
        "max_preserved_messages", _DEFAULT_MAX_PRESERVED_MESSAGES
    )
    if not isinstance(max_preserved, int):
        max_preserved = _DEFAULT_MAX_PRESERVED_MESSAGES

    prompt_val = compaction_cfg.get("prompt")
    prompt: Optional[str]
    if isinstance(prompt_val, str) and prompt_val.strip():
        prompt = prompt_val.strip()
    else:
        prompt = None

    overrides_val = compaction_cfg.get("settings_overrides")
    settings_overrides: Dict[str, Any]
    if isinstance(overrides_val, dict):
        settings_overrides = dict(overrides_val)
    else:
        settings_overrides = {}

    compaction_model_val = compaction_cfg.get("compaction_model")
    compaction_model: Optional[str]
    if isinstance(compaction_model_val, str) and compaction_model_val.strip():
        compaction_model = compaction_model_val.strip()
    else:
        compaction_model = None

    return {
        "enabled": compaction_cfg.get("enabled", False),
        "type": compaction_cfg.get("type"),
        "max_preserved_messages": max_preserved,
        "prompt": prompt,
        "settings_overrides": settings_overrides,
        "compaction_model": compaction_model,
    }


def _get_effective_compaction_config(
    base_config: Any,
    request_config: Any,
) -> Dict[str, Any]:
    """Resolve agent compaction settings plus the session model override.

    Agent-owned compaction settings live under ``base_config["compaction"]``.
    The existing configuration UI writes ``compaction_model`` as a top-level
    per-session override, which is present only in the effective request config.
    Preserve that public UI behavior while keeping the agent configuration
    block as the source for the remaining compaction settings.
    """
    compaction_cfg = _get_compaction_config(base_config)
    if not isinstance(request_config, dict):
        return compaction_cfg

    model_override = request_config.get("compaction_model")
    if not isinstance(model_override, str) or not model_override.strip():
        return compaction_cfg
    return {
        **compaction_cfg,
        "compaction_model": model_override.strip(),
    }


def _merge_request_config(
    config: Dict[str, Any],
    compaction_cfg: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge compaction overrides while keeping all tools disabled."""
    settings_overrides = compaction_cfg.get("settings_overrides") or {}
    merged = {**config, **settings_overrides, "disable_all_tools": True}
    compaction_model = compaction_cfg.get("compaction_model")
    if isinstance(compaction_model, str) and compaction_model.strip():
        merged["model"] = compaction_model.strip()
    return merged


def build_compaction_prompt(
    instructions: str | None = None,
    *,
    prompt_override: str | None = None,
) -> str:
    """Build the compaction prompt text, optionally with custom instructions.

    Custom instructions are appended in the same text block, matching
    ``kimi-cli``'s ``SimpleCompaction.prepare`` custom-instruction handling.
    """
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
    """Extract plain text from message content (str or multipart list)."""
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


def build_kimi_compaction_request_session(
    session: Session,
    *,
    prompt_text: str,
    start: int | None = None,
    end: int | None = None,
    end_inclusive: bool = False,
    max_preserved_messages: int = _DEFAULT_MAX_PRESERVED_MESSAGES,
) -> tuple[Optional[Session], List[int], List[int]]:
    """Build the Kimi-shaped compaction request session.

    Returns ``(request_session, compact_indices, preserved_indices)``.

    - ``request_session`` is a :class:`Session` with exactly two messages:
      ``[system: generic compactor prompt, user: synthetic message]``. It is
      ``None`` when compaction is a no-op (fewer than
      ``max_preserved_messages`` user/assistant messages in the compactable
      range and no explicit ``end`` was supplied).
    - ``compact_indices`` are the indices to remove from the original session.
    - ``preserved_indices`` are the preserved-tail indices (empty when an
      explicit ``end`` is supplied).

    A selected leading system message is included in the synthetic request,
    matching ``kimi-cli``, but is excluded from ``compact_indices`` so the
    platform keeps it in the final session. When ``end`` is ``None``, the last
    ``max_preserved_messages`` user/assistant messages are preserved verbatim.
    When ``end`` is supplied, the selected non-system range is compacted exactly
    and preserved-tail does not apply.
    """
    start_idx, end_idx = _normalize_slice_bounds(
        len(session.messages),
        start,
        end,
        end_inclusive=end_inclusive,
    )
    has_leading_system = _has_leading_system_message(session)
    if has_leading_system and start_idx == 0:
        compact_start = 1
    else:
        compact_start = start_idx
    compact_end = end_idx

    if compact_start >= compact_end:
        raise ValueError("range selects no compactable messages")

    explicit_end = end is not None
    preserved_indices: List[int] = []

    if not explicit_end:
        if max_preserved_messages <= 0:
            return None, [], []
        n_preserved = 0
        preserve_start = compact_end
        for index in range(compact_end - 1, compact_start - 1, -1):
            role = session.messages[index].role
            if role in {"user", "assistant"}:
                n_preserved += 1
                if n_preserved == max_preserved_messages:
                    preserve_start = index
                    break
        if n_preserved < max_preserved_messages:
            return None, [], []
        compact_end = preserve_start
        preserved_indices = list(range(preserve_start, end_idx))

    compact_indices = list(range(compact_start, compact_end))
    if not compact_indices:
        return None, [], []

    request_indices = list(range(start_idx, compact_end))
    parts: List[str] = []
    for offset, idx in enumerate(request_indices):
        msg = session.messages[idx]
        parts.append(f"## Message {offset + 1}\nRole: {msg.role}\nContent:\n")
        parts.append(_message_text(msg.content))
    parts.append(f"\n{prompt_text}")
    synthetic_content = "".join(parts)

    request_session = Session(
        session_id=session.session_id,
        messages=[
            Message(role="system", content=_GENERIC_COMPACTION_SYSTEM_PROMPT),
            Message(role="user", content=synthetic_content),
        ],
        metadata=_strip_native_history(session.metadata),
    )
    return request_session, compact_indices, preserved_indices


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
    final_messages = _collect_final_messages_from_stream(
        core, session, config, context=context
    )
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
    first_section = None

    for tag in _REQUIRED_SUMMARY_SECTIONS:
        match = re.search(re.escape(tag), response_text)
        if match and (first_section is None or match.start() < first_section):
            first_section = match.start()

    if first_section is not None:
        last_close = re.search(r"</important_context>", response_text)
        if last_close:
            return response_text[first_section : last_close.end()].strip()

    text = response_text.strip()
    if not text:
        raise ValueError("[kimi_compaction] empty response from compaction request")
    return text


def extract_summary_sections(summary_text: str) -> List[str]:
    """Extract section tag names from the summary text."""
    return re.findall(
        r"<(current_focus|environment|completed_tasks|active_issues|code_state|important_context)>",
        summary_text,
    )


def validate_summary_text(summary_text: str) -> None:
    missing = [
        section for section in _REQUIRED_SUMMARY_SECTIONS if section not in summary_text
    ]
    if missing:
        raise ValueError(
            "[kimi_compaction] summary is missing required sections: "
            + ", ".join(missing)
        )


def build_compact_summary_text(summary_text: str) -> str:
    """Wrap the compaction output with the ``kimi-cli`` ``<system>…</system>`` prefix.

    Matches ``kimi-cli``'s ``SimpleCompaction`` output format: a single user
    message whose content starts with
    ``<system>Previous context has been compacted. Here is the compaction
    output:</system>`` followed by the LLM's structured XML sections.
    """
    cleaned = summary_text.strip()
    return f"<system>{_COMPACTION_PREFIX}</system>\n{cleaned}"


def _summary_message_metadata(summary_text: str) -> Dict[str, Any]:
    return {
        _COMPACTION_METADATA_KEY: {
            "kind": "summary",
            "is_compact_summary": True,
            "is_visible_in_transcript_only": True,
            "summary_sections": extract_summary_sections(summary_text),
        }
    }


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


def build_compacted_session(
    core: Any,
    session: Session,
    config: Dict[str, Any],
    summary_text: str,
    *,
    compact_indices: List[int],
    context: Optional[Dict[str, Any]] = None,
) -> Session:
    """Build the compacted session by replacing ``compact_indices`` with the summary.

    1. Rebuild native history via ``core.rebuild_native_history``.
    2. Remove ``compact_indices`` via ``core.slice_session``.
    3. Insert the summary user message at the position of the first removed
       message.
    4. Leave preserved-tail messages (messages after ``compact_indices``) in
       place.
    """
    rebuilt = core.rebuild_native_history(
        session,
        config,
        context=_rebuild_context(context),
    )
    session_after_delete = core.slice_session(
        rebuilt,
        config,
        remove_indices=list(compact_indices),
    )
    insert_after = compact_indices[0] - 1
    compacted = core.add_message(
        session_after_delete,
        "user",
        summary_text,
        metadata=_summary_message_metadata(summary_text),
        config=config,
        after_index=insert_after,
        context=context,
    )
    return compacted


# ---------------------------------------------------------------------------
# Feature plugin class
# ---------------------------------------------------------------------------


class KimiCompactionFeature:
    """Feature-level plugin implementing Kimi-style context compaction.

    See the module docstring for the full description of the compaction request
    shape, preserved-tail behavior, summary injection format, and enablement
    enforcement.
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
        """Return empty schema — config is read from the agent ``compaction`` block."""
        return {}

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
        _ = tags
        if config is not None and not _is_compaction_enabled(config):
            return []

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
                "key": "compaction_model",
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

        base_config = context.get("base_config")
        if not isinstance(base_config, dict):
            base_config = (
                context.get("config") if isinstance(context.get("config"), dict) else {}
            )
        if not _is_compaction_enabled(base_config):
            return {
                "native_messages": list(native_messages),
                "error": {
                    "type": "disabled",
                    "message": "Kimi compaction is not enabled for this agent.",
                },
            }

        request_config = context.get("config")
        if not isinstance(request_config, dict):
            request_config = base_config
        compaction_cfg = _get_effective_compaction_config(
            base_config,
            request_config,
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

        instructions = params.get("instructions")
        instructions_text = (
            instructions.strip() if isinstance(instructions, str) else None
        )
        prompt_override = compaction_cfg.get("prompt")
        prompt_text = build_compaction_prompt(
            instructions_text,
            prompt_override=(
                prompt_override if isinstance(prompt_override, str) else None
            ),
        )

        try:
            request_session, compact_indices, _preserved_indices = (
                build_kimi_compaction_request_session(
                    prepared_session,
                    prompt_text=prompt_text,
                    start=start_int,
                    end=end_int,
                    end_inclusive=bool(end_inclusive),
                    max_preserved_messages=compaction_cfg["max_preserved_messages"],
                )
            )
        except ValueError as exc:
            return {
                "native_messages": list(native_messages),
                "error": {
                    "type": "invalid_range",
                    "message": str(exc),
                },
            }

        if request_session is None:
            return {
                "native_messages": list(native_messages),
                "status": "noop",
                "message": "Not enough messages to compact after preserving tail.",
            }

        compaction_response = _run_compaction_request(
            context["core"],
            request_session,
            _merge_request_config(request_config, compaction_cfg),
            context=context,
        )
        summary_body = extract_summary_text(compaction_response)
        summary_text = build_compact_summary_text(summary_body)
        compacted_session = build_compacted_session(
            context["core"],
            prepared_session,
            request_config,
            summary_text,
            compact_indices=compact_indices,
            context=context,
        )
        compacted_native = _native_messages_from_session(compacted_session)
        return {
            "native_messages": compacted_native,
            "session_metadata": {
                _COMPACTION_METADATA_KEY: {
                    "compacted": True,
                    "summary_sections": extract_summary_sections(summary_text),
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
    "build_kimi_compaction_request_session",
    "extract_summary_sections",
    "extract_summary_text",
    "validate_summary_text",
]
