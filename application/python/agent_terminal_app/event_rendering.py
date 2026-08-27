from __future__ import annotations

from datetime import datetime, timezone
from logging import Logger
from typing import Any, Callable, Dict, List, Optional

from agent_core.types import Message
from agent_app.utils.ui_condition import evaluate_condition
from agent_core.utils import get_logger

from .terminal_app import TerminalApplication, TerminalUserError


WriteFn = Callable[[str], None]

# ANSI colors for terminal output
BLUE = "\x1b[34m"
YELLOW = "\x1b[33m"
GRAY = "\x1b[90m"
RED = "\x1b[31m"
RESET = "\x1b[0m"


def _render_terminal_exception(context: str, exc: Exception, write: WriteFn) -> None:
    """Render an exception for interactive terminal usage.

    ``TerminalUserError`` instances are treated as user-facing errors
    without a stack trace. All other exceptions are rendered as
    application errors in red with a traceback, but the UI remains
    running.
    """

    if isinstance(exc, TerminalUserError):
        write(f"[{context}] {exc}")
        return

    import traceback

    write(f"{RED}[{context}] error: {exc}{RESET}")
    tb_text = traceback.format_exc()
    for line in tb_text.rstrip().splitlines():
        write(f"{RED}{line}{RESET}")


_event_logger: Logger | None = None


def _require_event_logger() -> Logger:
    global _event_logger

    if not _event_logger:
        _event_logger = get_logger("terminal_event")

    return _event_logger


def _shorten_single_line(text: str, limit: int) -> str:
    single = " ".join((text or "").split())
    if len(single) <= limit:
        return single
    return single[: limit - 3] + "..."


def _apply_tool_limits(text: str, line_limit: int, char_limit: int) -> tuple[str, bool]:
    """Apply line/char limits to tool output and report truncation.

    Returns a pair ``(limited_text, truncated)`` where ``truncated`` is
    ``True`` if any limit was applied.
    """

    if line_limit <= 0 and char_limit <= 0:
        return text, False

    limited = text
    truncated = False

    if char_limit > 0 and len(limited) > char_limit:
        limited = limited[:char_limit]
        truncated = True

    if line_limit > 0:
        lines = limited.splitlines(keepends=True)
        if len(lines) > line_limit:
            limited = "".join(lines[:line_limit])
            truncated = True

    return limited, truncated


def _message_to_dict(message: Any) -> Dict[str, Any]:
    if isinstance(message, Message):
        return message.to_dict()
    if isinstance(message, dict):
        return message
    # Fallback best-effort conversion.
    role = getattr(message, "role", None)
    content = getattr(message, "content", None)
    metadata = getattr(message, "metadata", None)
    return {
        "role": role,
        "content": content,
        "metadata": metadata if isinstance(metadata, dict) else {},
    }


def _extract_by_path(obj: Any, path: str) -> Any:
    """Resolve a simple dot-separated JSON path against obj.

    Supports dict lookups and integer indices for lists.
    """

    if not isinstance(path, str) or not path:
        return None

    current: Any = obj
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
        elif isinstance(current, list):
            try:
                idx = int(part)
            except Exception:
                return None
            if idx < 0 or idx >= len(current):
                return None
            current = current[idx]
        else:
            return None
    return current


def _render_footer_template(template: str, value: Any) -> str:
    text = str(value) if value is not None else ""
    if not isinstance(template, str) or not template:
        return text
    # Very small templating: replace {{data}} and {{ data }}.
    out = template.replace("{{data}}", text).replace("{{ data }}", text)
    return out


def _format_ui_value(el: Dict[str, Any], value: Any) -> Any:
    metadata = el.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    if metadata.get("format") != "datetime":
        return value

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        dt = datetime.fromtimestamp(float(value), tz=timezone.utc).astimezone()
        return dt.strftime("%c")

    if isinstance(value, str) and value:
        try:
            dt = datetime.fromisoformat(value)
        except Exception:
            return value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%c")

    return value


class BaseMessageRenderer:
    """Interface for renderers that handle both events and stored messages."""

    def __init__(self, app: TerminalApplication) -> None:
        self._app = app

    @staticmethod
    def _write_message_header(write: WriteFn, header: str) -> None:
        """Write one explicit separator line before a semantic message header."""

        write("")
        write(header)

    def render_event(
        self, event: Dict[str, Any], write: WriteFn
    ) -> None:  # pragma: no cover - overridden
        return None

    def render_message(
        self, index: int, message: Any, write: WriteFn, *, short: bool = False
    ) -> None:  # pragma: no cover - overridden
        return None


class LifecycleRenderer(BaseMessageRenderer):
    """Render non-message lifecycle events (sessions, requests, errors)."""

    def render_event(self, event: Dict[str, Any], write: WriteFn) -> None:
        etype = event.get("type")
        if etype == "session_created":
            write(f"[session] created {event.get('session_id')}")
        elif etype == "messages_deleted":
            indices = event.get("indices")
            if isinstance(indices, list):
                try:
                    text_indices = ", ".join(str(i) for i in indices)
                except Exception:
                    text_indices = str(indices)
            else:
                text_indices = str(indices)
            write(f"[session] deleted messages at indices: {text_indices}")
        elif etype == "request_started":
            write(f"{BLUE}[request]{RESET} started ({event.get('request_id')})")
        elif etype == "error":
            write(f"[error] {event.get('detail')}")
        elif etype == "request_completed":
            write("[request] completed")
        elif etype == "request_cancelled":
            write("[request] cancelled")


class UserRenderer(BaseMessageRenderer):
    """Render user messages and user-append events."""

    def __init__(
        self,
        app: TerminalApplication,
        footer_elements_supplier: Callable[[], List[Dict[str, Any]]],
    ) -> None:
        super().__init__(app)
        self._footer_elements_supplier = footer_elements_supplier

    def render_event(self, event: Dict[str, Any], write: WriteFn) -> None:
        if event.get("type") == "message_appended" and (
            event.get("role") == "user" or event.get("role") == "system"
        ):
            index = event.get("index")
            self._render_message(
                message=event.get("message"),
                write=write,
                index=index if isinstance(index, int) else None,
            )

    def _render_header(
        self, role, write: WriteFn, *, include_index: bool, index: int | None = None
    ) -> None:
        prefix = (
            f"[{index}] " if include_index and index is not None and index >= 0 else ""
        )
        self._write_message_header(
            write,
            f"{prefix}{BLUE}{role.capitalize()}:{RESET}",
        )

    def _render_footer(
        self, md: Dict[str, Any], msg: Dict[str, Any], write: WriteFn
    ) -> None:
        parts: List[str] = []

        # Plugin-provided message_footer elements are rendered on the
        # same line so that all footer fields appear together, using
        # the same logic as AssistantRenderer.
        try:
            elements = self._footer_elements_supplier() or []
        except Exception:
            elements = []

        for el in elements:
            if not isinstance(el, dict) or el.get("ui_type") != "message_footer":
                continue
            condition = el.get("condition")
            if condition is not None and not evaluate_condition(condition, msg):
                continue
            data_path = el.get("data")
            template = el.get("template") or "{{data}}"
            if not isinstance(data_path, str) or not data_path:
                continue
            value = _extract_by_path(msg, data_path)
            if value is None or value == "":
                continue
            value = _format_ui_value(el, value)
            text = _render_footer_template(template, value)
            if text:
                parts.append(f"{GRAY}{text}{RESET}")

        if parts:
            write(" ".join(parts))

    def _render_message(
        self,
        message: Any,
        write: WriteFn,
        *,
        index: int | None = None,
        short: bool = False,
    ) -> None:
        msg = _message_to_dict(message)
        if msg.get("role") != "user" and msg.get("role") != "system":
            return
        md = msg.get("metadata") or {}
        if not isinstance(md, dict):
            md = {}
        self._render_header(msg.get("role"), write, include_index=True, index=index)
        content = msg.get("content")
        if isinstance(content, str) and content:
            text = _shorten_single_line(content, 200) if short else str(content)
            write(text)
        self._render_footer(md, msg, write)

    def render_message(
        self, index: int, message: Any, write: WriteFn, *, short: bool = False
    ) -> None:
        self._render_message(message, write, index=index, short=short)


class AssistantRenderer(BaseMessageRenderer):
    """Render assistant reasoning + content for events and list view."""

    def __init__(
        self,
        app: TerminalApplication,
        footer_elements_supplier: Callable[[], List[Dict[str, Any]]],
    ) -> None:
        super().__init__(app)
        # Line buffers for reasoning and content so that streaming output
        # is printed only once per complete line.
        self._reasoning_buffer: str = ""
        self._content_buffer: str = ""
        # Tracks whether the "thinking:" label has been printed for the
        # current streamed reasoning sequence.
        self._reasoning_open: bool = False
        self._footer_elements_supplier = footer_elements_supplier

    def _flush_buffers(self) -> None:
        """Flush any buffered reasoning/content as complete lines.

        Called when an assistant message finishes (or is interrupted)
        so that any trailing partial line is printed once with a
        newline appended.
        """

        if self._reasoning_buffer:
            print(f"{GRAY}{self._reasoning_buffer}{RESET}", flush=True)
            self._reasoning_buffer = ""
        if self._content_buffer:
            print(self._content_buffer, flush=True)
            self._content_buffer = ""

    def render_event(self, event: Dict[str, Any], write: WriteFn) -> None:
        """Render streaming assistant reasoning and content.

        Uses the same header/footer semantics as non-streaming rendering,
        with incremental content updates. The footer is rendered when the
        final event arrives.
        """

        etype = event.get("type")

        # Assistant message lifecycle events from the tool loop.
        if etype == "assistant_message":
            phase = event.get("phase")
            if phase == "start":
                # Start of a new assistant message: defensively flush any
                # leftover buffered content from a previous one, then
                # print the header so it appears before thinking/content.
                self._flush_buffers()
                self._reasoning_open = False
                index = event.get("message_index")
                self._render_header(
                    write,
                    include_index=isinstance(index, int),
                    index=index if isinstance(index, int) else None,
                )
            elif phase == "end":
                # End of the current assistant message. Flush any
                # remaining buffered fragments; footers are rendered on
                # the subsequent "final" event.
                self._flush_buffers()
                self._reasoning_open = False
            return

        if etype == "partial":
            message = event.get("message") or {}
            if not isinstance(message, dict):
                return
            metadata = message.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}

            reasoning = metadata.get("reasoning")
            content = message.get("content")

            # Streaming assistant reasoning in gray, line-buffered.
            if isinstance(reasoning, str) and reasoning:
                if not self._reasoning_open:
                    write(f"{GRAY}thinking:{RESET}")
                    self._reasoning_open = True
                self._reasoning_buffer += reasoning
                while True:
                    idx = self._reasoning_buffer.find("\n")
                    if idx == -1:
                        break
                    line = self._reasoning_buffer[:idx]
                    self._reasoning_buffer = self._reasoning_buffer[idx + 1 :]
                    print(f"{GRAY}{line}{RESET}", flush=True)

            # Streaming assistant content; the header is printed via the
            # "assistant_message" start event. Content is also
            # line-buffered so that only whole lines are printed.
            if isinstance(content, str) and content:
                # Ensure any remaining reasoning (without a trailing
                # newline) is printed before the first assistant
                # content line so that reasoning always appears
                # before the reply.
                if self._reasoning_buffer:
                    print(f"{GRAY}{self._reasoning_buffer}{RESET}", flush=True)
                    self._reasoning_buffer = ""
                self._content_buffer += content
                while True:
                    idx = self._content_buffer.find("\n")
                    if idx == -1:
                        break
                    line = self._content_buffer[:idx]
                    self._content_buffer = self._content_buffer[idx + 1 :]
                    print(line, flush=True)
            return

        # On the final event, render the footer once.
        if etype == "final":
            messages = event.get("messages") or []
            if isinstance(messages, list) and messages:
                # Use the last assistant message as the source for metadata.
                for msg in reversed(messages):
                    if not isinstance(msg, dict):
                        continue
                    if msg.get("role") != "assistant":
                        continue
                    md = msg.get("metadata") or {}
                    if not isinstance(md, dict):
                        md = {}
                    # Flush any open reasoning/content before footer.
                    self._flush_buffers()
                    self._reasoning_open = False
                    self._render_footer(md, msg, write)
                    break
            return

        # For any other event type, just flush open buffers if needed.
        if self._reasoning_buffer or self._content_buffer:
            self._flush_buffers()
            self._reasoning_open = False

    def _render_header(
        self, write: WriteFn, *, include_index: bool, index: int | None = None
    ) -> None:
        prefix = (
            f"[{index}] " if include_index and index is not None and index >= 0 else ""
        )
        self._write_message_header(
            write,
            f"{prefix}{BLUE}Assistant:{RESET}",
        )

    def _render_footer(
        self, md: Dict[str, Any], msg: Dict[str, Any], write: WriteFn
    ) -> None:
        parts: List[str] = []
        # Always include the current agent id when available.
        try:
            agent_id = self._app.current_agent_id()
        except Exception:
            agent_id = None
        if isinstance(agent_id, str) and agent_id:
            parts.append(f"{YELLOW}{agent_id}{RESET}")

        # Plugin-provided message_footer elements are rendered on the
        # same line as the agent id so that all footer fields appear
        # together.
        try:
            elements = self._footer_elements_supplier() or []
        except Exception:
            elements = []
        for el in elements:
            if not isinstance(el, dict) or el.get("ui_type") != "message_footer":
                continue
            condition = el.get("condition")
            if condition is not None and not evaluate_condition(condition, msg):
                continue
            data_path = el.get("data")
            template = el.get("template") or "{{data}}"
            if not isinstance(data_path, str) or not data_path:
                continue
            value = _extract_by_path(msg, data_path)
            if value is None or value == "":
                continue
            value = _format_ui_value(el, value)
            text = _render_footer_template(template, value)
            if text:
                parts.append(f"{GRAY}{text}{RESET}")
        if parts:
            write(" ".join(parts))

        # Render web-search metadata, when present, on dedicated gray
        # lines below the standard footer.
        citations = md.get("url_citations")
        if isinstance(citations, list) and citations:
            items: List[str] = []
            for idx, c in enumerate(citations, start=1):
                if not isinstance(c, dict):
                    continue
                url = c.get("url")
                title = c.get("title")
                label: Optional[str]
                if isinstance(title, str) and title:
                    label = title
                elif isinstance(url, str) and url:
                    label = url
                else:
                    # Skip entries without at least a label.
                    continue
                if isinstance(url, str) and url and label != url:
                    item_text = f"{idx}. {label} ({url})"
                else:
                    item_text = f"{idx}. {label}"
                items.append(item_text)

            if items:
                summary = "; ".join(items)
                write(f"{GRAY}citations: {summary}{RESET}")

        sources = md.get("web_search_sources")
        if isinstance(sources, list) and sources:
            items = []
            for idx, source in enumerate(sources, start=1):
                if not isinstance(source, dict):
                    continue
                url = source.get("url")
                title = source.get("title")
                label: Optional[str]
                if isinstance(title, str) and title:
                    label = title
                elif isinstance(url, str) and url:
                    label = url
                else:
                    continue
                if isinstance(url, str) and url and label != url:
                    item_text = f"{idx}. {label} ({url})"
                else:
                    item_text = f"{idx}. {label}"
                items.append(item_text)

            if items:
                summary = "; ".join(items)
                write(f"{GRAY}sources: {summary}{RESET}")

    def render_message(
        self, index: int, message: Any, write: WriteFn, *, short: bool = False
    ) -> None:
        msg = _message_to_dict(message)
        if msg.get("role") != "assistant":
            return
        md = msg.get("metadata") or {}
        if not isinstance(md, dict):
            md = {}
        self._render_header(write, include_index=True, index=index)
        reasoning = md.get("reasoning")
        if isinstance(reasoning, str) and reasoning:
            text = _shorten_single_line(reasoning, 200) if short else str(reasoning)
            write(f"{GRAY}thinking: {text}{RESET}")
        else:
            blocks = md.get("thinking_blocks")
            if blocks:
                text = _shorten_single_line(str(blocks), 200) if short else str(blocks)
                write(f"{GRAY}thinking: {text}{RESET}")
        content = msg.get("content")
        if isinstance(content, str) and content:
            text = _shorten_single_line(content, 200) if short else str(content)
            write(text)
        calls = md.get("tool_calls")
        if isinstance(calls, list) and calls:
            names: List[str] = []
            for tc in calls:
                if not isinstance(tc, dict):
                    continue
                func = tc.get("function") or {}
                name = func.get("name") if isinstance(func, dict) else None
                if not isinstance(name, str) or not name:
                    name = str(tc.get("type") or "tool")
                names.append(name)
            if names:
                summary = ", ".join(names)
                summary = _shorten_single_line(summary, 80) if short else summary
                write(f"{GRAY}tools: {len(names)} call(s): {summary}{RESET}")
        self._render_footer(md, msg, write)


class ToolRenderer(BaseMessageRenderer):
    """Render tool call output for events and list view."""

    def __init__(
        self,
        app: TerminalApplication,
        one_line_supplier: Optional[Callable[[], bool]] = None,
    ) -> None:
        super().__init__(app)
        self._open_calls: set[tuple[str, str]] = set()
        # Per-call line buffers so that streamed tool output is
        # printed only once per complete line.
        self._line_buffers: Dict[tuple[str, str], str] = {}
        # Per-call accounting for line/character limits so that
        # streaming respects the same bounds as non-streamed output.
        self._printed_lines: Dict[tuple[str, str], int] = {}
        self._printed_chars: Dict[tuple[str, str], int] = {}
        self._truncated_calls: set[tuple[str, str]] = set()
        # Live one-line-result mode. The supplier is read once per
        # tool call (at the first event seen for that call) so that
        # toggling mid-call never mixes full and compact rendering for
        # the same call.
        self._one_line_supplier = one_line_supplier
        self._call_modes: Dict[tuple[str, str], bool] = {}
        cfg = app.agent_app.get_application_config()
        self._line_limit: int = int(cfg.get("tool_output_line_limit", 100))
        self._char_limit: int = int(cfg.get("tool_output_char_limit", 8000))
        # Short-mode configuration for list views.
        self._short_char_limit: int = int(cfg.get("tool_output_short_char_limit", 200))
        self._short_one_line: bool = bool(cfg.get("tool_output_short_one_line", True))
        self._short_line_limit: int = int(cfg.get("tool_output_short_line_limit", 20))

    def _select_content_from_message(
        self, msg: Dict[str, Any], *, short: bool = False
    ) -> str | None:
        """Return display-aware content for a tool message/result.

        Prefers ``metadata.display.content`` when present, falling back to
        the core ``content`` field. This mirrors the semantics used when
        listing stored messages so that streaming and history views stay
        consistent.

        When ``short=True``, prefers ``metadata.display.single_line`` if
        available for collapsed/short views.
        """

        if not isinstance(msg, dict):
            return None

        md = msg.get("metadata") or {}
        if not isinstance(md, dict):
            md = {}
        display = md.get("display")

        # In short mode, prefer single_line if available
        if short and isinstance(display, dict):
            single_line = display.get("single_line")
            if isinstance(single_line, str) and single_line.strip():
                return single_line

        # Otherwise, prefer display content/fallbacks before raw message content.
        if isinstance(display, dict):
            if display.get("type") == "text":
                content = display.get("content")
            else:
                content = (
                    display.get("content_text")
                    or display.get("text_fallback")
                    or msg.get("content")
                )
        else:
            content = msg.get("content")

        if isinstance(content, str) and content:
            return content
        return None

    def _is_one_line(self) -> bool:
        supplier = self._one_line_supplier
        if supplier is None:
            return False
        try:
            return bool(supplier())
        except Exception:
            return False

    def _condense_short(self, content: str, *, one_line: bool) -> tuple[str, bool]:
        """Condense tool content using the short-view limits.

        Shared by the ``/list short`` view and the live compact
        rendering so both stay consistent. Returns ``(text, truncated)``.
        """

        if one_line:
            single = " ".join((content or "").split())
            limit = self._short_char_limit
            if limit > 0 and len(single) > limit:
                return single[: limit - 3] + "...", True
            return single, False
        return _apply_tool_limits(
            content, self._short_line_limit, self._short_char_limit
        )

    @staticmethod
    def _call_key(event: Dict[str, Any]) -> tuple[str, str]:
        request_id = event.get("request_id")
        call_id = event.get("tool_call_id")
        return (
            request_id if isinstance(request_id, str) else "",
            call_id if isinstance(call_id, str) else "",
        )

    def _clear_call_state(self, key: tuple[str, str]) -> None:
        self._open_calls.discard(key)
        self._line_buffers.pop(key, None)
        self._printed_lines.pop(key, None)
        self._printed_chars.pop(key, None)
        self._truncated_calls.discard(key)
        self._call_modes.pop(key, None)

    def _clear_request_state(self, request_id: Any) -> None:
        if isinstance(request_id, str):
            keys = {
                key
                for key in (
                    set(self._open_calls)
                    | set(self._line_buffers)
                    | set(self._printed_lines)
                    | set(self._printed_chars)
                    | set(self._truncated_calls)
                    | set(self._call_modes)
                )
                if key[0] == request_id
            }
            for key in keys:
                self._clear_call_state(key)
            return
        self.reset_transient_state()

    def reset_transient_state(self) -> None:
        self._open_calls.clear()
        self._line_buffers.clear()
        self._printed_lines.clear()
        self._printed_chars.clear()
        self._truncated_calls.clear()
        self._call_modes.clear()

    def _render_one_line_result(self, event: Dict[str, Any], write: WriteFn) -> None:
        """Render a finished tool call as a compact two-line block."""

        payload = event.get("payload") or {}
        result = payload.get("result") if isinstance(payload, dict) else None
        if not isinstance(result, dict):
            result = {}
        md = result.get("metadata") or {}
        if not isinstance(md, dict):
            md = {}

        index = event.get("message_index")
        prefix = f"[{index}] " if isinstance(index, int) and index >= 0 else ""

        tool_name = md.get("tool_name")
        name_part = (
            f" {YELLOW}{tool_name}{RESET}"
            if isinstance(tool_name, str) and tool_name
            else ""
        )

        content = self._select_content_from_message(result, short=True)
        text, _truncated = self._condense_short(content or "", one_line=True)
        self._write_message_header(
            write,
            f"{prefix}{BLUE}Tool:{RESET}{name_part}",
        )
        if text:
            write(f"    {GRAY}{text}{RESET}")

    def render_event(self, event: Dict[str, Any], write: WriteFn) -> None:
        event_type = event.get("type")
        if event_type in {
            "request_completed",
            "request_cancelled",
            "error",
        }:
            self._clear_request_state(event.get("request_id"))
            return
        if event_type == "session_created":
            self.reset_transient_state()
            return
        if event_type != "tool_partial":
            return

        phase = event.get("phase")
        payload = event.get("payload") or {}
        key = self._call_key(event)

        # Fix the rendering mode for this call at the first event seen
        # for it, so a mid-call toggle never mixes modes.
        one_line = self._call_modes.get(key)
        if one_line is None:
            one_line = self._is_one_line()
            self._call_modes[key] = one_line

        # Backwards compatibility: payloads from earlier versions without phase.
        if isinstance(payload, dict):
            part = payload.get("part") or payload.get("partial") or {}
        else:
            part = {}

        if phase == "end":
            if one_line:
                # One-line-result mode: the call renders as a compact block. Any
                # buffered per-call state is dropped (nothing was
                # streamed for one-line-result calls).
                result = payload.get("result") if isinstance(payload, dict) else None
                if isinstance(result, dict):
                    self._render_one_line_result(event, write)
                self._clear_call_state(key)
                return

            # End-of-call event with the final tool result. When no
            # streaming chunks were seen for this call, render a
            # one-shot header + content + footer; otherwise render
            # only the footer to avoid duplicating content.
            result = payload.get("result") if isinstance(payload, dict) else None
            if isinstance(result, dict):
                md = result.get("metadata") or {}
                if not isinstance(md, dict):
                    md = {}
                saw_stream = key in self._open_calls
                if not saw_stream:
                    self._render_header(write, include_index=False)
                    content = self._select_content_from_message(result)
                    if isinstance(content, str) and content:
                        # For the non-streamed case, render the tool
                        # output subject to the same line/character
                        # limits used for stored messages and, when
                        # truncated, append a gray notice.
                        text, truncated = _apply_tool_limits(
                            content, self._line_limit, self._char_limit
                        )
                        write(text)
                        if truncated:
                            write(f"{GRAY}[tool output truncated]{RESET}")
                self._render_footer(md, write)

                # Flush any buffered partial line for this call so that
                # trailing content without a newline is still printed
                # once with a newline appended, subject to the same
                # line/character limits.
                buf = self._line_buffers.pop(key, "")
                if buf:
                    lines = self._printed_lines.get(key, 0)
                    chars = self._printed_chars.get(key, 0)
                    already_truncated = key in self._truncated_calls

                    if self._line_limit <= 0 and self._char_limit <= 0:
                        # No limits configured; print any remainder.
                        print(buf, flush=True)
                    else:
                        would_exceed_lines = (
                            self._line_limit > 0 and lines + 1 > self._line_limit
                        )
                        would_exceed_chars = (
                            self._char_limit > 0 and chars + len(buf) > self._char_limit
                        )
                        if not already_truncated and (
                            would_exceed_lines or would_exceed_chars
                        ):
                            write(f"{GRAY}[tool output truncated]{RESET}")
                            self._truncated_calls.add(key)
                        elif not (would_exceed_lines or would_exceed_chars):
                            print(buf, flush=True)

            self._clear_call_state(key)
            return

        # In one-line-result mode, streamed start/stream output (including
        # summary parts) is suppressed entirely; the call renders as a
        # compact block on the end event instead.
        if one_line:
            return

        # For start/stream (or legacy payloads without phase), stream text.
        if not isinstance(part, dict):
            return

        part_type = part.get("type")

        # Summary payloads are rendered as-is at the end of a tool
        # call and are not subject to per-call line/character limits
        # so that exit codes and stderr are always visible even when
        # the main output was truncated.
        if part_type == "summary":
            summary = part.get("content")
            if isinstance(summary, str) and summary:
                write(summary.rstrip("\n"))
            return

        if part_type != "text":
            return

        content = part.get("content")
        if not isinstance(content, str) or not content:
            return

        # Print the header once per request/tool-call pair. Anonymous or reused
        # call ids remain isolated across requests.
        if key not in self._open_calls:
            self._open_calls.add(key)
            self._render_header(write, include_index=False)

        # Line-buffered streaming: accumulate content until a newline is
        # seen, then print whole lines. Any remainder is flushed when
        # the tool call ends. While streaming, enforce the same
        # line/character limits used for non-streamed output.
        buf = self._line_buffers.get(key, "") + content

        # Fast path when no limits are configured: behave like the
        # original streaming implementation.
        if self._line_limit <= 0 and self._char_limit <= 0:
            while True:
                idx = buf.find("\n")
                if idx == -1:
                    break
                line = buf[:idx]
                buf = buf[idx + 1 :]
                print(line, flush=True)
            self._line_buffers[key] = buf
            return

        lines = self._printed_lines.get(key, 0)
        chars = self._printed_chars.get(key, 0)
        already_truncated = key in self._truncated_calls

        while True:
            idx = buf.find("\n")
            if idx == -1:
                break
            line = buf[:idx]
            buf = buf[idx + 1 :]

            # Respect per-call line/character limits. Once a call has
            # been marked as truncated, suppress further output.
            if already_truncated:
                continue

            would_exceed_lines = self._line_limit > 0 and lines + 1 > self._line_limit
            would_exceed_chars = (
                self._char_limit > 0 and chars + len(line) > self._char_limit
            )
            if would_exceed_lines or would_exceed_chars:
                write(f"{GRAY}[tool output truncated]{RESET}")
                self._truncated_calls.add(key)
                already_truncated = True
                # Drop any remaining buffered content for this call.
                buf = ""
                break

            print(line, flush=True)
            lines += 1
            chars += len(line)

        self._line_buffers[key] = buf
        self._printed_lines[key] = lines
        self._printed_chars[key] = chars

    def _render_header(
        self, write: WriteFn, *, include_index: bool, index: int | None = None
    ) -> None:
        prefix = (
            f"[{index}] " if include_index and index is not None and index >= 0 else ""
        )
        self._write_message_header(
            write,
            f"{prefix}{BLUE}Tool:{RESET}",
        )

    def _render_footer(self, md: Dict[str, Any], write: WriteFn) -> None:
        parts: List[str] = []
        tool_name = md.get("tool_name")
        if isinstance(tool_name, str) and tool_name:
            parts.append(f"{YELLOW}{tool_name}{RESET}")
        ts = md.get("timestamp")
        if isinstance(ts, str) and ts:
            parts.append(f"{BLUE}{ts}{RESET}")
        call_id = md.get("tool_call_id")
        if isinstance(call_id, str) and call_id:
            parts.append(f"{GRAY}tool_call_id: {call_id}{RESET}")
        if parts:
            write(" ".join(parts))

    def render_message(
        self, index: int, message: Any, write: WriteFn, *, short: bool = False
    ) -> None:
        msg = _message_to_dict(message)
        if msg.get("role") != "tool":
            return
        md = msg.get("metadata") or {}
        if not isinstance(md, dict):
            md = {}
        self._render_header(write, include_index=True, index=index)
        content = self._select_content_from_message(msg, short=short)
        if isinstance(content, str) and content:
            truncated = False
            if short:
                text, truncated = self._condense_short(
                    content, one_line=self._short_one_line
                )
            else:
                text, truncated = _apply_tool_limits(
                    content, self._line_limit, self._char_limit
                )
            write(text)
            if truncated:
                write(f"{GRAY}[tool output truncated]{RESET}")
        self._render_footer(md, write)


class TerminalRenderContext:
    """Thin coordinator that delegates to renderer classes."""

    def __init__(
        self,
        app: TerminalApplication,
        footer_elements_supplier: Callable[[], List[Dict[str, Any]]],
        one_line_supplier: Optional[Callable[[], bool]] = None,
    ) -> None:
        self._log = _require_event_logger()
        self._tool_renderer = ToolRenderer(app, one_line_supplier=one_line_supplier)
        self._renderers: List[BaseMessageRenderer] = [
            LifecycleRenderer(app),
            UserRenderer(app, footer_elements_supplier),
            AssistantRenderer(app, footer_elements_supplier),
            self._tool_renderer,
        ]

    def reset_transient_state(self) -> None:
        self._tool_renderer.reset_transient_state()

    def render_event(self, event: Dict[str, Any], write: WriteFn) -> None:
        # self._log.debug("event received", ev=event)
        for renderer in self._renderers:
            try:
                renderer.render_event(event, write)
            except Exception:
                continue

    def render_message(
        self, index: int, message: Any, write: WriteFn, *, short: bool = False
    ) -> None:
        for renderer in self._renderers:
            try:
                renderer.render_message(index, message, write, short=short)
            except Exception:
                continue
