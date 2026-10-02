"""Reusable Crystal Lattice review projections for completed runs.

The projection turns a saved Crystal Lattice session, observation, and
effective configuration into lean review material for result packages and
other evaluation consumers. It is designed for review, not session
restoration: it preserves visible messages and tool-call intent, omits full
tool results and encrypted reasoning, redacts secret values, and normalizes
machine-specific paths while recording the original hash and replacement
map.

The projection records whether important information was captured directly,
reconstructed by the caller, or unavailable. It contains no suite semantics:
task files, documentation pages, semantic scores, assessment prompts, and
suite stages stay with their owning suites.

Path normalization applies to projected material — delivered instructions,
tool-call arguments, and failure excerpts — while user and assistant message
text stays verbatim because it is model-produced content.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from agent_eval.result_packages import (
    CAPTURED,
    INHERITED,
    RECONSTRUCTED,
    UNAVAILABLE,
    apply_replacements,
    availability,
    sha256_text,
)
from agent_eval.services import jsonable

REVIEW_SCHEMA_VERSION = 1

_TOOL_ARGUMENT_LIMIT = 2000
_TRANSCRIPT_ARGUMENT_LIMIT = 160
_FAILURE_EXCERPT_LIMIT = 400
_FAILURE_INDICATORS = re.compile(
    r"(?:\berror\b|\bfailure\b|\bfailed\b|\btraceback\b"
    r"|exit code:?\s*[1-9]\d*"
    r"|\bexception\b|\bdenied\b|\bnot found\b|no such file)",
    re.IGNORECASE,
)


def project_session_review(
    session: Mapping[str, Any],
    *,
    observation: Mapping[str, Any] | None = None,
    supplied_instructions: Mapping[str, Any] | None = None,
    inherited_prefix: Mapping[str, Any] | None = None,
    path_replacements: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Project one saved session into a lean review representation.

    ``supplied_instructions`` lets the caller supply a reconstructed system
    message (for example one rebuilt from saved sources and verified against
    a recorded hash) when the session itself retains no system or developer
    message. ``inherited_prefix`` declares how many leading messages were
    restored from a parent run; its ``length`` may be ``None`` when the
    boundary is unknown.
    """

    messages = _messages(session)
    replacements = dict(path_replacements or {})
    prefix = _normalize_inherited_prefix(inherited_prefix)
    instructions = _project_instructions(
        messages,
        supplied_instructions=supplied_instructions,
        replacements=replacements,
    )
    conversation = _project_conversation(
        messages,
        prefix_length=prefix["length"],
        replacements=replacements,
    )
    usage = _project_usage(messages, prefix_length=prefix["length"])
    review: dict[str, Any] = {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "instructions": instructions,
        "inherited_prefix": prefix,
        "conversation": conversation,
        "execution": _project_execution(messages, observation),
        "usage": usage,
        "omitted": [
            "full tool-result content",
            "encrypted reasoning content",
        ],
    }
    if replacements:
        review["path_normalization"] = {
            "applied": True,
            "replacements": dict(replacements),
            "note": (
                "machine-specific paths were replaced by placeholders; the "
                "recorded original hash covers the un-normalized text"
            ),
        }
    return review


def project_effective_config_view(
    config: Mapping[str, Any],
    *,
    path_replacements: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Return a sanitized, path-normalized effective-configuration view."""

    replacements = dict(path_replacements or {})
    rendered = json.dumps(jsonable(config), sort_keys=True, ensure_ascii=False)
    if replacements:
        rendered = apply_replacements(rendered, replacements)
    value = json.loads(rendered)
    if not isinstance(value, dict):
        raise ValueError("effective configuration must be a mapping")
    return value


def render_session_markdown(
    review: Mapping[str, Any],
    *,
    title: str,
    context: Mapping[str, str] | None = None,
) -> str:
    """Render one review projection as a concise full-session transcript.

    Every turn stays visible: user and assistant text in full, tool calls as
    one line each, and tool results as a single status line — except genuine
    failure indicators, which keep a short excerpt. ``context`` supplies
    ordered header entries owned by the caller (run identity, model, links
    to shared records); activity counts and usage come from the review.
    """

    lines = [f"# Session — {title}", ""]
    for key in context or {}:
        lines.append(f"- {key}: {context[key]}")
    execution = review.get("execution") or {}
    activity = []
    for key, label in (
        ("message_count", "messages"),
        ("tool_call_count", "tool calls"),
        ("tool_result_count", "tool results"),
    ):
        value = execution.get(key)
        if isinstance(value, int):
            activity.append(f"{value} {label}")
    if activity:
        lines.append("- Activity: " + " · ".join(activity))
    usage_line = _usage_markdown_line(review.get("usage") or {})
    if usage_line:
        lines.append(f"- Usage: {usage_line}")
    lines.extend(["", "## Transcript", ""])
    for entry in review.get("conversation") or ():
        role = str(entry.get("role"))
        if entry.get("inherited"):
            lines.append(f"**{_role_label(role)}** *(inherited from the parent run)*")
            lines.append("")
            continue
        if role == "assistant":
            suffix = " *(reasoning present)*" if entry.get("reasoning_present") else ""
            lines.append(f"**Assistant**{suffix}")
            lines.append("")
            content = str(entry.get("content") or "")
            if content:
                lines.extend([content, ""])
            for call in entry.get("tool_calls") or ():
                arguments = str(call.get("arguments") or "")
                if len(arguments) > _TRANSCRIPT_ARGUMENT_LIMIT:
                    arguments = arguments[:_TRANSCRIPT_ARGUMENT_LIMIT] + "…"
                lines.append(f"- `{call.get('name')}` {arguments}")
            if entry.get("tool_calls"):
                lines.append("")
        elif role == "tool":
            name = entry.get("tool_name")
            excerpt = entry.get("failure_excerpt")
            if isinstance(excerpt, str) and excerpt:
                lines.append(f"**Tool `{name}`** — failed")
                lines.append("")
                for excerpt_line in excerpt.splitlines():
                    lines.append(f"> {excerpt_line}" if excerpt_line else ">")
                lines.append("")
            else:
                lines.append(f"**Tool `{name}`** — *(result omitted)*")
                lines.append("")
        else:
            lines.append(f"**{_role_label(role)}**")
            lines.append("")
            lines.append(str(entry.get("content") or ""))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _role_label(role: str) -> str:
    return role.capitalize() if role else "Message"


def _usage_markdown_line(usage: Mapping[str, Any]) -> str:
    state = (usage.get("availability") or {}).get("state")
    if state != CAPTURED:
        detail = (usage.get("availability") or {}).get("detail")
        return f"unknown — {detail}" if detail else "unknown"
    parts: list[str] = []
    input_tokens = usage.get("input_tokens")
    if isinstance(input_tokens, int):
        parts.append(f"{input_tokens:,} input")
    cached = usage.get("cached_input_tokens")
    if isinstance(cached, int):
        suffix = " (estimated)" if usage.get("cached_input_estimated") else ""
        parts.append(f"{cached:,} cached{suffix}")
    cache_write = usage.get("cache_write_tokens")
    if isinstance(cache_write, int) and cache_write:
        parts.append(f"{cache_write:,} cache write")
    output_tokens = usage.get("output_tokens")
    if isinstance(output_tokens, int):
        parts.append(f"{output_tokens:,} output")
    cost = usage.get("provider_reported_cost")
    if isinstance(cost, (int, float)):
        parts.append(f"provider cost ${cost:.7f}")
    return " · ".join(parts) if parts else "captured"


def _messages(session: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw = session.get("messages")
    if not isinstance(raw, list):
        return []
    return [message for message in raw if isinstance(message, Mapping)]


def _normalize_inherited_prefix(
    inherited_prefix: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if inherited_prefix is None:
        return {
            "length": 0,
            "availability": availability(
                CAPTURED, detail="no inherited prefix declared"
            ),
        }
    length = inherited_prefix.get("length")
    record = inherited_prefix.get("availability")
    if length is None:
        return {
            "length": None,
            "availability": _as_availability(
                record,
                default=availability(
                    UNAVAILABLE, detail="inherited prefix length unknown"
                ),
            ),
        }
    if not isinstance(length, int) or length < 0:
        raise ValueError("inherited_prefix length must be a non-negative int")
    return {
        "length": length,
        "availability": _as_availability(record, default=availability(CAPTURED)),
    }


def _as_availability(
    value: Any,
    *,
    default: Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(value, Mapping) and value.get("state") in (
        CAPTURED,
        RECONSTRUCTED,
        INHERITED,
        UNAVAILABLE,
    ):
        return dict(value)
    return dict(default)


def _project_instructions(
    messages: list[Mapping[str, Any]],
    *,
    supplied_instructions: Mapping[str, Any] | None,
    replacements: Mapping[str, str],
) -> dict[str, Any]:
    captured: list[tuple[str, str]] = []
    for message in messages:
        if message.get("role") not in {"system", "developer"}:
            continue
        metadata = message.get("metadata")
        compiled = (
            metadata.get("compiled_content") if isinstance(metadata, Mapping) else None
        )
        if isinstance(compiled, str) and compiled.strip():
            captured.append(("session.compiled_content", compiled))
            continue
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            captured.append((f"session.{message.get('role')}", content))
    if captured:
        source, text = captured[0]
        return _instruction_view(
            text,
            source=source,
            record=availability(CAPTURED, detail="retained by the saved session"),
            replacements=replacements,
        )
    if isinstance(supplied_instructions, Mapping):
        text = supplied_instructions.get("text")
        record = supplied_instructions.get("availability")
        detail = supplied_instructions.get("detail")
        if isinstance(text, str) and text.strip():
            merged = _as_availability(
                record,
                default=availability(
                    RECONSTRUCTED,
                    detail=detail,
                    verified=False,
                ),
            )
            if merged.get("detail") is None and detail is not None:
                merged["detail"] = detail
            return _instruction_view(
                text,
                source=str(supplied_instructions.get("source", "supplied")),
                record=merged,
                replacements=replacements,
            )
    return {
        "text": None,
        "original_sha256": None,
        "normalized_sha256": None,
        "availability": availability(
            UNAVAILABLE,
            detail="saved session retains no system or developer message",
        ),
        "source": None,
        "path_normalization": {"applied": False},
    }


def _instruction_view(
    text: str,
    *,
    source: str,
    record: Mapping[str, Any],
    replacements: Mapping[str, str],
) -> dict[str, Any]:
    normalized = apply_replacements(text, replacements) if replacements else text
    return {
        "text": normalized,
        "original_sha256": sha256_text(text),
        "normalized_sha256": sha256_text(normalized),
        "availability": dict(record),
        "source": source,
        "path_normalization": {"applied": bool(replacements)},
    }


def _project_conversation(
    messages: list[Mapping[str, Any]],
    *,
    prefix_length: int | None,
    replacements: Mapping[str, str],
) -> list[dict[str, Any]]:
    conversation: list[dict[str, Any]] = []
    for index, message in enumerate(messages):
        role = str(message.get("role"))
        if prefix_length is not None and index < prefix_length:
            conversation.append({"index": index, "role": role, "inherited": True})
            continue
        if role in {"system", "developer"}:
            continue
        if role == "assistant":
            conversation.append(
                _assistant_entry(index, message, replacements=replacements)
            )
        elif role == "tool":
            conversation.append(_tool_entry(index, message, replacements=replacements))
        else:
            content = message.get("content")
            text = content if isinstance(content, str) else _content_summary(content)
            conversation.append({"index": index, "role": role, "content": text})
    return conversation


def _assistant_entry(
    index: int,
    message: Mapping[str, Any],
    *,
    replacements: Mapping[str, str],
) -> dict[str, Any]:
    metadata = message.get("metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    content = message.get("content")
    text = content if isinstance(content, str) else _content_summary(content)
    entry: dict[str, Any] = {"index": index, "role": "assistant", "content": text}
    calls = metadata.get("tool_calls")
    if isinstance(calls, list) and calls:
        entry["tool_calls"] = [
            _tool_call_summary(call, replacements=replacements)
            for call in calls
            if isinstance(call, Mapping)
        ]
    if metadata.get("reasoning") is not None:
        entry["reasoning_present"] = True
    return entry


def _tool_call_summary(
    call: Mapping[str, Any],
    *,
    replacements: Mapping[str, str],
) -> dict[str, Any]:
    function = call.get("function")
    name = None
    arguments: Any = None
    if isinstance(function, Mapping):
        name = function.get("name")
        arguments = function.get("arguments")
    if name is None:
        name = call.get("name")
        arguments = call.get("input")
    summary: dict[str, Any] = {"name": str(name or "unknown")}
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            arguments = arguments[:_TOOL_ARGUMENT_LIMIT]
    if arguments is not None:
        rendered = json.dumps(jsonable(arguments), sort_keys=True, ensure_ascii=False)
        if replacements:
            rendered = apply_replacements(rendered, replacements)
        if len(rendered) > _TOOL_ARGUMENT_LIMIT:
            rendered = rendered[:_TOOL_ARGUMENT_LIMIT] + "…"
        summary["arguments"] = rendered
    return summary


def _tool_entry(
    index: int,
    message: Mapping[str, Any],
    *,
    replacements: Mapping[str, str],
) -> dict[str, Any]:
    metadata = message.get("metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    entry: dict[str, Any] = {
        "index": index,
        "role": "tool",
        "tool_name": str(metadata.get("tool_name") or "unknown"),
    }
    content = message.get("content")
    text = content if isinstance(content, str) else _content_summary(content)
    excerpt_window = text[:_FAILURE_EXCERPT_LIMIT]
    if excerpt_window and _FAILURE_INDICATORS.search(excerpt_window):
        if replacements:
            excerpt_window = apply_replacements(excerpt_window, replacements)
        entry["failure_excerpt"] = excerpt_window
    return entry


def _project_execution(
    messages: list[Mapping[str, Any]],
    observation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    tool_call_count = 0
    tool_result_count = 0
    for message in messages:
        role = message.get("role")
        metadata = message.get("metadata")
        if role == "assistant" and isinstance(metadata, Mapping):
            calls = metadata.get("tool_calls")
            if isinstance(calls, list):
                tool_call_count += len(calls)
        elif role == "tool":
            tool_result_count += 1
    execution: dict[str, Any] = {
        "message_count": len(messages),
        "tool_call_count": tool_call_count,
        "tool_result_count": tool_result_count,
    }
    if isinstance(observation, Mapping):
        for key in (
            "request_count",
            "tool_event_count",
            "mutation_count",
            "error_count",
        ):
            value = observation.get(key)
            if isinstance(value, int):
                execution[key] = value
    return execution


def _project_usage(
    messages: list[Mapping[str, Any]],
    *,
    prefix_length: int | None,
) -> dict[str, Any]:
    unavailable = {
        "availability": availability(
            UNAVAILABLE,
            detail="saved session contains no provider usage metadata",
        ),
        "input_tokens": None,
        "cached_input_tokens": None,
        "cached_input_estimated": None,
        "cache_write_tokens": None,
        "output_tokens": None,
        "reasoning_tokens": None,
        "provider_reported_cost": None,
        "provider_reported_cost_cumulative": None,
    }
    if prefix_length is None:
        return {
            **unavailable,
            "availability": availability(
                UNAVAILABLE,
                detail="inherited prefix length unknown; per-run usage cannot"
                " be bounded",
            ),
        }
    input_tokens = 0
    output_tokens = 0
    reasoning_tokens = 0
    cached_input_tokens = 0
    cache_write_tokens = 0
    cached_estimated = False
    provider_reported_cost = 0.0
    provider_reported_cost_cumulative = 0.0
    found = False
    for index, message in enumerate(messages):
        if message.get("role") != "assistant" or index < prefix_length:
            continue
        metadata = message.get("metadata")
        if not isinstance(metadata, Mapping):
            continue
        usage = metadata.get("usage")
        if not isinstance(usage, Mapping):
            continue
        found = True
        input_value = usage.get("input_tokens")
        output_value = usage.get("output_tokens")
        if isinstance(input_value, int):
            input_tokens += input_value
        if isinstance(output_value, int):
            output_tokens += output_value
        output_details = usage.get("output_tokens_details")
        if isinstance(output_details, Mapping):
            reasoning = output_details.get("reasoning_tokens")
            if isinstance(reasoning, int):
                reasoning_tokens += reasoning
        input_details = usage.get("input_tokens_details")
        if isinstance(input_details, Mapping):
            cache_write = input_details.get("cache_write_tokens")
            if isinstance(cache_write, int):
                cache_write_tokens += cache_write
        estimated = metadata.get("usage_estimated_cached_tokens")
        if isinstance(estimated, int):
            cached_input_tokens += estimated
            cached_estimated = True
        elif isinstance(input_details, Mapping):
            reported = input_details.get("cached_tokens")
            if isinstance(reported, int):
                cached_input_tokens += reported
        turn_cost = metadata.get("usage_total_cost")
        if isinstance(turn_cost, (int, float)):
            provider_reported_cost += float(turn_cost)
        cumulative = metadata.get("usage_total_cost_cumulative")
        if isinstance(cumulative, (int, float)):
            provider_reported_cost_cumulative = max(
                provider_reported_cost_cumulative, float(cumulative)
            )
    if not found:
        return unavailable
    return {
        "availability": availability(
            CAPTURED, detail="provider usage metadata retained by the saved session"
        ),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "cached_input_estimated": cached_estimated,
        "cache_write_tokens": cache_write_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "provider_reported_cost": provider_reported_cost,
        "provider_reported_cost_cumulative": provider_reported_cost_cumulative,
    }


def _content_summary(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    try:
        rendered = json.dumps(jsonable(content), sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(content)
    return rendered
