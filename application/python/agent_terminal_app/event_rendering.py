from __future__ import annotations

from logging import Logger
from typing import Any, Callable, Dict, List

from agent_core.utils import get_logger


def get_reasoning_event_renderer():
    last_request_id = None

    def renderer(event: Dict[str, Any], write: Callable[[str], None]) -> None:
        nonlocal last_request_id
        match event:
            case {
                "type": "partial",
                "request_id": str(request_id),
                "message": {"metadata": {"reasoning": str(content), **rest1}},
                **rest2,
            } if content:
                if last_request_id != request_id:
                    print("\033[34mAssistant Reasoning\033[0m", flush=True)
                print(content, flush=True, end="")
                last_request_id = request_id
            case _:
                if last_request_id is not None:
                    print("", flush=True)
                    last_request_id = None
                return

    return renderer


def get_assistant_event_renderer():
    last_request_id = None

    def renderer(event: Dict[str, Any], write: Callable[[str], None]) -> None:
        nonlocal last_request_id
        match event:
            case {
                "type": "partial",
                "request_id": str(request_id),
                "message": {"content": str(content), **rest1},
                **rest2,
            } if content:
                if last_request_id != request_id:
                    print("\033[34mAssistant message:\033[0m", flush=True)
                    last_request_id = request_id
                print(content, flush=True, end="")
            case _:
                if last_request_id is not None:
                    print("", flush=True)
                    last_request_id = None
                return

    return renderer


# Test:  Use the shell tool to write Hello World 10 times.
def get_tool_result_renderer():
    last_tool_call_id = None

    def renderer(event: Dict[str, Any], write: Callable[[str], None]) -> None:
        nonlocal last_tool_call_id
        match event:
            case {
                "type": "tool_partial",
                "request_id": str(request_id),
                "tool_call_id": str(tool_call_id),
                "payload": {"part": {"type": "text", "content": str(content)}},
                **rest1,
            } if content:
                if last_tool_call_id != tool_call_id:
                    print(f"\033[34mTool call {tool_call_id}:\033[0m", flush=True)
                    last_tool_call_id = tool_call_id
                print(content, flush=True, end="")
            case _:
                if last_tool_call_id is not None:
                    last_tool_call_id = None
                return

    return renderer


def get_request_header_and_footer_renderer():
    last_request_id = None

    def renderer(event: Dict[str, Any], write: Callable[[str], None]) -> None:
        nonlocal last_request_id
        match event:
            case {"type": "partial", "request_id": str(request_id)} if last_request_id != request_id:
                print(f"\n\033[34mrequest {request_id} started\033[0m", flush=True)
                last_request_id = request_id
            case {"type": "final", "request_id": str(request_id)} if request_id == last_request_id:
                print(f"\033[34mrequest {request_id} completed\033[0m", flush=True)
                last_request_id = None

    return renderer


renderers = [
    get_reasoning_event_renderer(),
    get_assistant_event_renderer(),
    get_tool_result_renderer(),
    get_request_header_and_footer_renderer(),
]


_event_logger: Logger | None = None


def _require_event_logger() -> Logger:
    global _event_logger

    if not _event_logger:
        _event_logger = get_logger("terminal_event")

    return _event_logger


def _render_event(event: Dict[str, Any], write: Callable[[str], None]) -> None:
    event_logger = _require_event_logger()
    event_logger.debug("event received", ev=event)

    for renderer in renderers:
        try:
            renderer(event, write)
        except Exception:
            continue

    etype = event.get("type")

    if etype == "session_created":
        write(f"[session] created {event.get('session_id')}")
        return
    if etype == "message_appended":
        role = event.get("role")
        content = event.get("content", "") or ""
        if role == "user":
            write(f"You: {content}")
        elif role == "assistant":
            write(f"Assistant: {content}")
        return
    if etype == "messages_deleted":
        indices = event.get("indices")
        if isinstance(indices, list):
            try:
                text_indices = ", ".join(str(i) for i in indices)
            except Exception:
                text_indices = str(indices)
        else:
            text_indices = str(indices)
        write(f"[session] deleted messages at indices: {text_indices}")
        return
    if etype == "request_started":
        write(f"\033[34m[request]\033[0m started ({event.get('request_id')})")
        return
    if etype == "partial":
        message = event.get("message") or {}
        content = message.get("content", "") or ""
        if content:
            pass
        return
    if etype == "final":
        messages = event.get("messages") or []
        text = ""
        if messages:
            text = messages[-1].get("content", "") or ""
        return
    if etype == "tool_calls":
        return
    if etype == "tool_partial":
        payload = event.get("payload") or {}
        if isinstance(payload, dict):
            if "partial" in payload:
                payload = payload.get("partial") or {}
            elif "part" in payload:
                payload = payload.get("part") or {}
        if isinstance(payload, dict):
            ptype = payload.get("type")
            content = payload.get("content", "") or ""
            if ptype == "text" and content:
                call_id = event.get("tool_call_id")
                prefix = f"[tool:{call_id}] " if call_id else "[tool] "
        return
    if etype == "tool_results":
        messages = event.get("messages") or []
        if not isinstance(messages, list) or not messages:
            return
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            metadata = msg.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}
            display = metadata.get("display") or {}
            text: str | None = None
            if isinstance(display, dict) and display.get("type") == "text":
                raw = display.get("content", "")
                if isinstance(raw, str) and raw:
                    text = raw
            if not isinstance(text, str) or not text:
                raw_content = msg.get("content", "")
                text = raw_content if isinstance(raw_content, str) else ""
            if not text:
                continue
            call_id = metadata.get("tool_call_id")
            prefix = f"[tool:{call_id}] " if call_id else "[tool] "
        return
    if etype == "error":
        write(f"[error] {event.get('detail')}")
        return
    if etype == "request_completed":
        write("[request] completed")
        return
    if etype == "request_cancelled":
        write("[request] cancelled")
        return


def _format_message_for_list(index: int, message: Any) -> List[str]:
    """Return display lines for a session message.

    Shows the role, content/result, thinking, and a minimal summary of any
    tool calls or tool results attached to the message.
    """

    role = getattr(message, "role", None)
    if role is None and isinstance(message, dict):
        role = message.get("role")

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")

    metadata = getattr(message, "metadata", None)
    if metadata is None and isinstance(message, dict):
        metadata = message.get("metadata")

    lines: List[str] = []
    role_text = str(role) if role is not None else "unknown"
    lines.append(f"[{index}] {role_text}")

    def _shorten(text: str, limit: int = 200) -> str:
        single = " ".join((text or "").split())
        if len(single) <= limit:
            return single
        return single[: limit - 3] + "..."

    if isinstance(content, str) and content:
        label = "result" if role_text == "tool" else "content"
        lines.append(f"  {label}: {_shorten(content)}")

    md = metadata if isinstance(metadata, dict) else {}

    reasoning = md.get("reasoning")
    if isinstance(reasoning, str) and reasoning:
        lines.append(f"  thinking: {_shorten(reasoning)}")
    else:
        thinking_blocks = md.get("thinking_blocks")
        if thinking_blocks:
            lines.append(f"  thinking: {_shorten(str(thinking_blocks))}")

    tool_calls = md.get("tool_calls")
    if isinstance(tool_calls, list) and tool_calls:
        names: List[str] = []
        for tc in tool_calls:
            if not isinstance(tc, dict):
                continue
            func = tc.get("function") or {}
            name = func.get("name") if isinstance(func, dict) else None
            if not isinstance(name, str) or not name:
                name = str(tc.get("type") or "tool")
            names.append(name)
        if names:
            summary = ", ".join(names)
            summary = _shorten(summary, limit=80)
            lines.append(f"  tools: {len(names)} call(s): {summary}")

    tool_call_id = md.get("tool_call_id")
    if tool_call_id:
        lines.append(f"  tool_call_id: {tool_call_id}")

    return lines
