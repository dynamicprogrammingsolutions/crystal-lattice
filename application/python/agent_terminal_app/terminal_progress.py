from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, Iterable


@dataclass(frozen=True)
class TerminalProgressState:
    """Transient terminal progress derived from public application events."""

    phase: str = "idle"
    request_id: str | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    pending_tools: tuple[tuple[str, str], ...] = ()


IDLE_PROGRESS = TerminalProgressState()


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _tool_descriptors(tool_calls: Any) -> tuple[tuple[str, str], ...]:
    if not isinstance(tool_calls, list):
        return ()

    descriptors: list[tuple[str, str]] = []
    for call in tool_calls:
        if not isinstance(call, dict):
            continue
        call_id = _string(call.get("id")) or ""
        function = call.get("function")
        function_name = (
            _string(function.get("name")) if isinstance(function, dict) else None
        )
        name = function_name or _string(call.get("name")) or "tool"
        descriptors.append((call_id, name))
    return tuple(descriptors)


def _find_tool_name(
    pending_tools: Iterable[tuple[str, str]], call_id: str | None
) -> str | None:
    if call_id is None:
        return None
    for pending_id, name in pending_tools:
        if pending_id == call_id:
            return name
    return None


def _remove_tool(
    pending_tools: tuple[tuple[str, str], ...], call_id: str | None
) -> tuple[tuple[str, str], ...]:
    if not pending_tools:
        return ()
    if call_id is None:
        return pending_tools[1:]

    removed = False
    remaining: list[tuple[str, str]] = []
    for item in pending_tools:
        if not removed and item[0] == call_id:
            removed = True
            continue
        remaining.append(item)
    return tuple(remaining)


def reduce_terminal_progress(
    state: TerminalProgressState,
    event: Dict[str, Any],
) -> TerminalProgressState:
    """Return the next progress state for one public application event."""

    event_type = event.get("type")
    request_id = _string(event.get("request_id"))

    if event_type in {"session_created", "request_completed", "request_cancelled"}:
        return IDLE_PROGRESS
    if event_type == "error":
        if (
            state.request_id is None
            or request_id is None
            or request_id == state.request_id
        ):
            return IDLE_PROGRESS
        return state
    if event_type == "request_started":
        return TerminalProgressState(
            phase="request",
            request_id=request_id,
        )

    if state.request_id is not None and request_id not in {None, state.request_id}:
        return state

    if event_type == "assistant_message":
        phase = event.get("phase")
        if phase == "start":
            return replace(
                state,
                phase="llm",
                request_id=request_id or state.request_id,
                tool_call_id=None,
                tool_name=None,
            )
        if phase == "end":
            return replace(
                state,
                phase="request",
                request_id=request_id or state.request_id,
                tool_call_id=None,
                tool_name=None,
            )
        return state

    if event_type == "partial":
        return replace(
            state,
            phase="llm",
            request_id=request_id or state.request_id,
            tool_call_id=None,
            tool_name=None,
        )

    if event_type == "tool_calls":
        pending_tools = _tool_descriptors(event.get("tool_calls"))
        if not pending_tools:
            return state
        first_id, first_name = pending_tools[0]
        return TerminalProgressState(
            phase="tool",
            request_id=request_id or state.request_id,
            tool_call_id=first_id or None,
            tool_name=first_name,
            pending_tools=pending_tools,
        )

    if event_type == "tool_partial":
        call_id = _string(event.get("tool_call_id"))
        phase = event.get("phase")
        if phase == "end":
            remaining = _remove_tool(state.pending_tools, call_id)
            if remaining:
                next_id, next_name = remaining[0]
                return TerminalProgressState(
                    phase="tool",
                    request_id=request_id or state.request_id,
                    tool_call_id=next_id or None,
                    tool_name=next_name,
                    pending_tools=remaining,
                )
            return TerminalProgressState(
                phase="request",
                request_id=request_id or state.request_id,
            )

        tool_name = (
            _find_tool_name(state.pending_tools, call_id) or state.tool_name or "tool"
        )
        return replace(
            state,
            phase="tool",
            request_id=request_id or state.request_id,
            tool_call_id=call_id,
            tool_name=tool_name,
        )

    if event_type in {"tool_results", "final"}:
        return TerminalProgressState(
            phase="request",
            request_id=request_id or state.request_id,
        )

    return state


def format_terminal_progress(state: TerminalProgressState) -> str:
    """Return a stable toolbar label without animation or ANSI escapes."""

    if state.phase == "request":
        return "Running: request"
    if state.phase == "llm":
        return "Running: LLM"
    if state.phase == "tool":
        suffix = f" {state.tool_name}" if state.tool_name else ""
        return f"Running: tool{suffix}"
    return ""
