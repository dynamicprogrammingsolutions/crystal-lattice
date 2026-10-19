from __future__ import annotations

import asyncio
from dataclasses import dataclass
from logging import Logger
import shlex
import sys
import webbrowser
from typing import Any, Awaitable, Callable, Dict, List, Optional, cast, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout

from agent_app.utils.ui_condition import evaluate_condition
from agent_app.notifications import notification_revision_token
from .action_rendering import is_local_interactive_output, render_action_result
from .event_rendering import (
    TerminalRenderContext,
    _render_terminal_exception,
    _extract_by_path,
)
from .runtime_layout import load_runtime_layout
from .session_query import parse_session_query
from .terminal_progress import (
    IDLE_PROGRESS,
    TerminalProgressState,
    format_terminal_progress,
    reduce_terminal_progress,
)
from .terminal_app import (
    TerminalApplication,
    TerminalUserError,
    TerminalApplicationError,
)
from agent_app.config import resolve_request_config

_DEFAULT_RUNTIME_LAYOUT = load_runtime_layout()
_DEFAULT_CONFIG_PATH = _DEFAULT_RUNTIME_LAYOUT.config_examples / "config_fallback.json"
_DEFAULT_SESSION_ROOT = _DEFAULT_RUNTIME_LAYOUT.user_path("default_sessions_dir")


# ---------------------------------------------------------------------------
# Terminal UI wiring (prompt_toolkit)
# ---------------------------------------------------------------------------


CommandFn = Callable[
    [TerminalApplication, str, Callable[[str], None], Dict[str, Any]],
    Awaitable[None] | None,
]
SlashCompletionFn = Callable[[TerminalApplication, str], List[Completion]]


@dataclass(frozen=True)
class SlashCommand:
    name: str
    description: str
    handler: CommandFn
    completer: Optional[SlashCompletionFn] = None


@dataclass(frozen=True)
class Shortcut:
    keys: str
    description: str
    handler: CommandFn


_SLASH_COMMANDS: Dict[str, SlashCommand] = {}
_SHORTCUTS: Dict[str, Shortcut] = {}


def slash_command(
    name: str,
    description: str = "",
    completer: Optional[SlashCompletionFn] = None,
) -> Callable[[CommandFn], CommandFn]:
    cmd_name = name.lstrip("/")

    def decorator(func: CommandFn) -> CommandFn:
        text = description or (func.__doc__ or "").strip() or cmd_name
        _SLASH_COMMANDS[cmd_name] = SlashCommand(
            name=cmd_name,
            description=text,
            handler=func,
            completer=completer,
        )
        return func

    return decorator


def shortcut(keys: str, description: str = "") -> Callable[[CommandFn], CommandFn]:
    def decorator(func: CommandFn) -> CommandFn:
        text = description or (func.__doc__ or "").strip() or keys
        _SHORTCUTS[keys] = Shortcut(keys=keys, description=text, handler=func)
        return func

    return decorator


def get_slash_command(name: str) -> Optional[SlashCommand]:
    return _SLASH_COMMANDS.get(name.lstrip("/"))


def iter_slash_commands() -> List[SlashCommand]:
    return sorted(_SLASH_COMMANDS.values(), key=lambda c: c.name)


def iter_shortcuts() -> List[Shortcut]:
    return sorted(_SHORTCUTS.values(), key=lambda s: s.keys)


def _static_slash_names() -> List[str]:
    return sorted(_SLASH_COMMANDS)


def _dynamic_slash_commands(app: TerminalApplication) -> List[Dict[str, Any]]:
    try:
        return app.slash_command_elements(reserved_names=_static_slash_names())
    except Exception:
        return []


def _command_argument_names(element: Dict[str, Any]) -> List[str]:
    dialog = element.get("dialog")
    inputs = (
        dialog.get("inputs")
        if isinstance(dialog, dict) and dialog.get("kind") == "form"
        else []
    )
    return [
        field["name"]
        for field in (inputs if isinstance(inputs, list) else [])
        if isinstance(field, dict)
        and isinstance(field.get("name"), str)
        and field["name"]
        and field.get("type") not in {"secret", "password"}
    ]


class SlashCommandCompleter(Completer):
    """Autocomplete for slash commands and their arguments.

    This completer is generic: it knows how to complete command names
    and delegates per-command argument completion to the ``completer``
    callback registered with each :class:`SlashCommand` via the
    :func:`slash_command` decorator.
    """

    def __init__(self, get_app: Callable[[], TerminalApplication]) -> None:
        self._get_app = get_app

    def get_completions(self, document, complete_event):  # type: ignore[override]
        text = document.text_before_cursor
        if not isinstance(text, str) or not text:
            return

        # Slash-command completion
        if text.startswith("/"):
            body = text[1:]

            # No space yet: complete command names.
            if " " not in body:
                prefix = body
                for cmd in iter_slash_commands():
                    if not prefix or cmd.name.startswith(prefix):
                        yield Completion(
                            cmd.name,
                            start_position=-len(prefix),
                            display=f"/{cmd.name}",
                            display_meta=cmd.description,
                        )
                app = self._get_app()
                seen: set[str] = set()
                for element in _dynamic_slash_commands(app):
                    for route in [
                        element.get("path"),
                        *(element.get("aliases") or []),
                    ]:
                        if not isinstance(route, list) or not route:
                            continue
                        name = route[0]
                        if not isinstance(name, str) or name in seen:
                            continue
                        if not prefix or name.startswith(prefix):
                            seen.add(name)
                            yield Completion(
                                name,
                                start_position=-len(prefix),
                                display=f"/{name}",
                                display_meta=str(
                                    element.get("description") or ""
                                ),
                            )
                return

            cmd_name, _, rest = body.partition(" ")
            rest = rest.lstrip()

            cmd = get_slash_command(cmd_name)
            if cmd is None:
                app = self._get_app()
                try:
                    tokens = shlex.split(body)
                except ValueError:
                    return
                elements = _dynamic_slash_commands(app)
                token_prefix = tokens[-1] if body and not body.endswith(" ") else ""
                complete_tokens = tokens[:-1] if token_prefix else tokens
                seen: set[str] = set()
                for element in elements:
                    for route in [
                        element.get("path"),
                        *(element.get("aliases") or []),
                    ]:
                        if not isinstance(route, list):
                            continue
                        if list(route[: len(complete_tokens)]) != complete_tokens:
                            continue
                        if len(route) <= len(complete_tokens):
                            continue
                        candidate = route[len(complete_tokens)]
                        if (
                            isinstance(candidate, str)
                            and candidate.startswith(token_prefix)
                            and candidate not in seen
                        ):
                            seen.add(candidate)
                            yield Completion(
                                candidate,
                                start_position=-len(token_prefix),
                                display=candidate,
                                display_meta=str(
                                    element.get("description") or "plugin command"
                                ),
                            )
                try:
                    element, remaining = app.match_slash_command(
                        tokens,
                        reserved_names=_static_slash_names(),
                    )
                except Exception:
                    element, remaining = None, []
                if element is not None and len(remaining) <= 1:
                    argument_prefix = remaining[0] if remaining else ""
                    candidates = [
                        f"{name}=" for name in _command_argument_names(element)
                    ]
                    if isinstance(element.get("browser"), dict):
                        candidates.append("--no-open")
                    for candidate in candidates:
                        if (
                            candidate.startswith(argument_prefix)
                            and candidate not in seen
                        ):
                            seen.add(candidate)
                            yield Completion(
                                candidate,
                                start_position=-len(argument_prefix),
                                display=candidate,
                                display_meta="plugin command argument",
                            )
                return
            if cmd.completer is None:
                return

            app = self._get_app()
            try:
                completions = cmd.completer(app, rest) or []
            except Exception:
                completions = []

            for comp in completions:
                yield comp
            return

        # Non-slash input: delegate to feature-driven completions when
        # appropriate (for example, @file: path expansion).
        if "@" not in text:
            return

        app = self._get_app()
        try:
            items = app.get_feature_completions(text) or []
        except Exception:
            items = []

        cursor_pos = len(text)
        for item in items:
            if not isinstance(item, dict):
                continue
            replacement = item.get("replacement")
            start = item.get("start")
            if not isinstance(replacement, str) or not isinstance(start, int):
                continue

            display = item.get("display") or replacement
            display_meta = item.get("display_meta") or ""
            start_position = start - cursor_pos

            comp = Completion(
                replacement,
                start_position=start_position,
                display=display,
                display_meta=display_meta,
            )
            # Attach the original completion descriptor so that accept
            # handlers can delegate to feature-specific logic.
            setattr(comp, "_feature_completion", item)
            yield comp


def _render_status_bar_template(template: str, data: Any) -> str:
    """Render a status bar template string with the given data.

    Similar to _render_footer_template but for status bar usage.
    Simple {{data}} replacement.
    """
    if not isinstance(template, str):
        return ""

    # Simple string replacement (same logic as footer templates)
    text = template.replace("{{data}}", str(data))
    return text


def _status_bar_text(
    app: TerminalApplication,
    progress: TerminalProgressState = IDLE_PROGRESS,
) -> str:
    """Build status bar text with agent, session, and plugin-contributed fields."""

    # Base status info
    try:
        session_id = app.session_id
    except RuntimeError:
        session_id = "-"
    try:
        agent = app.current_agent_id()
    except RuntimeError:
        agent = ""

    parts: list[str] = []
    if isinstance(agent, str) and agent:
        parts.append(f"Agent: {agent}")
    parts.append(f"Session: {session_id}")
    progress_text = format_terminal_progress(progress)
    if progress_text:
        parts.append(progress_text)

    # Add plugin-contributed status_bar elements from last assistant message
    try:
        last_msg = app.get_last_assistant_message()
        if not last_msg:
            return "  ".join(parts)

        elements = app.status_bar_elements()

        if elements:
            for el in elements:
                if not isinstance(el, dict):
                    continue
                condition = el.get("condition")
                if condition is not None and not evaluate_condition(
                    condition, last_msg
                ):
                    continue
                data_path = el.get("data")
                template = el.get("template") or "{{data}}"

                if not isinstance(data_path, str) or not data_path:
                    continue

                # Extract value from the last assistant message
                value = _extract_by_path(last_msg, data_path)
                if value is None or value == "":
                    continue

                # Render the template
                text = _render_status_bar_template(template, value)
                if text:
                    parts.append(text)
    except Exception:
        # Silently ignore errors to keep the status bar functional
        pass

    return "  ".join(parts)


def _parse_range_or_index_arg(
    text: str,
    *,
    command: str,
    write: Callable[[str], None],
) -> Optional[Tuple[Optional[int], Optional[int]]]:
    """Parse a ``start:end``-style range argument.

    ``text`` must contain a colon and may omit either bound, following
    Python slice conventions (e.g. ``":3"``, ``"1:"``). Each side is
    parsed as an optional integer.

    Returns ``(start, end)`` where each element may be ``None``. On
    parse errors, prints a user-facing message using ``command`` as the
    prefix (e.g. ``"[list] ..."``) and returns ``None``.
    """

    start_str, _, end_str = text.partition(":")
    try:
        start_val = int(start_str) if start_str.strip() else None
    except ValueError:
        write(f"[{command}] invalid start index; expected an integer")
        return None
    try:
        end_val = int(end_str) if end_str.strip() else None
    except ValueError:
        write(f"[{command}] invalid end index; expected an integer")
        return None
    return start_val, end_val


def _normalize_setting_options(options: Any) -> List[tuple[str, str]]:
    """Normalize a UI element's options into ``(value, display)`` pairs.

    Supports both simple string options and objects like
    ``{"value": "low", "label": "Low"}``.
    """

    normalized: List[tuple[str, str]] = []
    if not isinstance(options, list):
        return normalized

    for opt in options:
        if isinstance(opt, str):
            if opt:
                normalized.append((opt, opt))
            continue

        if isinstance(opt, dict):
            val = opt.get("value")
            label = opt.get("label")
            if isinstance(val, str) and val:
                if isinstance(label, str) and label:
                    normalized.append((val, label))
                else:
                    normalized.append((val, val))

    return normalized


def _resolve_dotted_path(value: Any, path: str) -> Tuple[bool, Any]:
    """Resolve a dotted path from a nested mapping-like object."""

    if not isinstance(value, dict) or not isinstance(path, str) or not path:
        return False, None

    current: Any = value
    for part in [segment for segment in path.split(".") if segment]:
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]

    return True, current


def _resolve_setting_current_value(
    element: Dict[str, Any],
    base_config: Dict[str, Any],
    schema_entry: Optional[Dict[str, Any]],
) -> Tuple[bool, Any]:
    """Resolve the current/default value for a config UI element.

    Precedence mirrors the shared session settings logic used by the mobile
    and desktop UIs: direct flat config key, nested base config via
    ``config_path``, UI element ``default``, then schema ``default``.
    """

    key_val = element.get("key")
    key = key_val if isinstance(key_val, str) else ""
    if key and key in base_config:
        return True, base_config[key]

    config_path_val = element.get("config_path")
    config_path = config_path_val if isinstance(config_path_val, str) else ""
    found_nested, nested_value = _resolve_dotted_path(base_config, config_path)
    if found_nested:
        return True, nested_value

    if "default" in element:
        return True, element.get("default")

    if isinstance(schema_entry, dict) and "default" in schema_entry:
        return True, schema_entry.get("default")

    return False, None


def _action_path_value(context: Dict[str, Any], source: Any) -> Tuple[bool, Any]:
    if not isinstance(source, str) or not source.startswith("$") or "." not in source:
        return False, None
    prefix, _, path = source[1:].partition(".")
    root = context.get(prefix)
    current: Any = root
    for part in [piece for piece in path.split(".") if piece]:
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _coerce_action_value(raw: Any, field: Dict[str, Any]) -> Any:
    field_type = str(field.get("type") or "text")
    if field_type == "integer":
        if isinstance(raw, int) and not isinstance(raw, bool):
            return raw
        try:
            return int(str(raw))
        except ValueError as exc:
            raise TerminalUserError(
                f"{field.get('name')}: expected an integer"
            ) from exc
    if field_type == "number":
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            return raw
        try:
            return float(str(raw))
        except ValueError as exc:
            raise TerminalUserError(
                f"{field.get('name')}: expected a number"
            ) from exc
    if field_type in {"boolean", "checkbox"}:
        if isinstance(raw, bool):
            return raw
        normalized = str(raw).strip().lower()
        if normalized in {"true", "yes", "y", "1", "on"}:
            return True
        if normalized in {"false", "no", "n", "0", "off"}:
            return False
        raise TerminalUserError(
            f"{field.get('name')}: expected true/false or yes/no"
        )
    if field_type in {"select", "dropdown"}:
        options = field.get("options")
        allowed: List[Any] = []
        for option in options if isinstance(options, list) else []:
            allowed.append(option.get("value") if isinstance(option, dict) else option)
        candidate = raw
        if candidate not in allowed:
            raise TerminalUserError(
                f"{field.get('name')}: expected one of "
                + ", ".join(str(item) for item in allowed)
            )
        return candidate
    return str(raw)


async def _action_prompt(
    ui_state: Dict[str, Any],
    *,
    prompt: str,
    default: Any = None,
    secret: bool = False,
    multiline: bool = False,
) -> str | None:
    callback = ui_state.get("action_prompt")
    if not callable(callback):
        responses = ui_state.get("action_responses")
        if isinstance(responses, list) and responses:
            value = responses.pop(0)
            return None if value is None else str(value)
        raise TerminalUserError("interactive input is required for this action")
    value = callback(
        {
            "prompt": prompt,
            "default": default,
            "secret": secret,
            "multiline": multiline,
        }
    )
    if asyncio.iscoroutine(value):
        value = await value
    return None if value is None else str(value)


def _action_initial_value(
    field: Dict[str, Any],
    context: Dict[str, Any],
) -> Tuple[bool, Any]:
    if field.get("type") in {"secret", "password"}:
        return False, None
    found, value = _action_path_value(context, field.get("prefill_from"))
    if found and value is not None and value != "":
        return True, value
    if "default" in field:
        return True, field.get("default")
    return False, None


async def _collect_action_form(
    form: Any,
    *,
    context: Dict[str, Any],
    inline_values: Dict[str, str] | None,
    ui_state: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(form, dict):
        return {}
    kind = form.get("kind", "none")
    if kind == "none":
        if inline_values:
            raise TerminalUserError("this action has no form inputs")
        return {}
    if kind == "confirm":
        if inline_values:
            raise TerminalUserError("confirmation actions do not accept inline values")
        answer = await _action_prompt(
            ui_state,
            prompt=f"{form.get('title') or 'Confirm'} [yes/no]",
        )
        if answer is None or answer.strip().lower() not in {"yes", "y"}:
            raise TerminalUserError("action cancelled")
        return {}
    if kind != "form":
        raise TerminalUserError(f"unsupported action dialog kind {kind!r}")

    inputs = form.get("inputs")
    fields = [field for field in (inputs or []) if isinstance(field, dict)]
    known_names = {
        field.get("name")
        for field in fields
        if isinstance(field.get("name"), str) and field.get("name")
    }
    unknown = sorted(set(inline_values or {}) - known_names)
    if unknown:
        raise TerminalUserError(
            "unknown inline form fields: " + ", ".join(unknown)
        )

    values: Dict[str, Any] = {}
    for field in fields:
        name = field.get("name")
        if not isinstance(name, str) or not name:
            continue
        field_type = str(field.get("type") or "text")
        secret = field_type in {"secret", "password"}
        if secret and inline_values and name in inline_values:
            raise TerminalUserError(
                f"{name}: secret/password values cannot be supplied inline"
            )
        has_initial, initial = _action_initial_value(field, context)
        inline = bool(inline_values and name in inline_values)
        label = str(field.get("label") or name)
        options = field.get("options")
        option_suffix = ""
        if field_type in {"select", "dropdown"} and isinstance(options, list):
            labels = [
                str(option.get("label") or option.get("value"))
                if isinstance(option, dict)
                else str(option)
                for option in options
            ]
            option_suffix = f" ({', '.join(labels)})"
        validation_suffix = ""
        while True:
            if inline:
                raw: Any = inline_values[name]  # type: ignore[index]
            else:
                raw = await _action_prompt(
                    ui_state,
                    prompt=f"{label}{option_suffix}{validation_suffix}",
                    default=initial if has_initial and not secret else None,
                    secret=secret,
                    multiline=field_type == "multiline",
                )
                if raw is None:
                    raise TerminalUserError("action cancelled")
                if raw == "" and has_initial:
                    raw = initial

            if raw == ":skip":
                if field.get("required") is True:
                    if inline:
                        raise TerminalUserError(
                            f"{name}: required fields cannot be skipped"
                        )
                    validation_suffix = " [required]"
                    continue
                if field.get("submit_empty") is True:
                    values[name] = ""
                break
            if raw == "":
                if field.get("required") is True:
                    if inline:
                        raise TerminalUserError(f"{name}: a value is required")
                    validation_suffix = " [required]"
                    continue
                if field.get("submit_empty") is True:
                    values[name] = ""
                break
            try:
                values[name] = _coerce_action_value(raw, field)
            except TerminalUserError as exc:
                if inline:
                    raise
                validation_suffix = f" [{exc}]"
                continue
            break
    return values


def _inline_assignments(tokens: List[str]) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for token in tokens:
        if "=" not in token:
            raise TerminalUserError("inline action values must use NAME=VALUE")
        name, value = token.split("=", 1)
        if not name:
            raise TerminalUserError("inline action value name must not be empty")
        if name in values:
            raise TerminalUserError(f"duplicate inline action value {name!r}")
        values[name] = value
    return values


def _result_path(result: Dict[str, Any], path: Any) -> Any:
    if not isinstance(path, str) or not path:
        return None
    current: Any = result
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _sensitive_form_values(
    form: Any,
    values: Dict[str, Any],
) -> List[str]:
    if not isinstance(form, dict) or form.get("kind") != "form":
        return []
    inputs = form.get("inputs")
    sensitive_names = {
        field.get("name")
        for field in (inputs or [])
        if isinstance(field, dict)
        and field.get("type") in {"secret", "password"}
        and isinstance(field.get("name"), str)
    }
    return [
        str(value)
        for name, value in values.items()
        if name in sensitive_names and value is not None and str(value)
    ]


def _redact_sensitive_text(text: str, sensitive_values: List[str]) -> str:
    redacted = text
    for value in sorted(set(sensitive_values), key=len, reverse=True):
        redacted = redacted.replace(value, "[redacted]")
    return redacted


def _execute_ui_element_redacted(
    app: TerminalApplication,
    element: Dict[str, Any],
    *,
    context: Dict[str, Any],
    dialog_values: Dict[str, Any] | None = None,
    form_values: Dict[str, Any] | None = None,
    sensitive_values: List[str],
) -> Dict[str, Any]:
    try:
        return app.execute_ui_element(
            element,
            context=context,
            dialog_values=dialog_values,
            form_values=form_values,
        )
    except Exception as exc:
        message = _redact_sensitive_text(str(exc), sensitive_values)
        if message != str(exc):
            raise TerminalUserError(message) from exc
        raise


def _render_action_result(
    app: TerminalApplication,
    result: Dict[str, Any],
    write: Callable[[str], None],
    *,
    context: Dict[str, Any],
    notification: Dict[str, Any] | None = None,
    sensitive_values: List[str] | None = None,
) -> None:
    display = result.get("display")
    if notification is None and isinstance(display, dict):
        app.begin_action_display(display)

    def _register(action: Any) -> str:
        if not isinstance(display, dict):
            raise TerminalUserError("action result display is unavailable")
        return app.register_run_action_followup(
            action,
            display,
            context,
            notification=notification,
        )

    known_sensitive_values = sensitive_values or []

    def _write_redacted(line: str) -> None:
        write(_redact_sensitive_text(line, known_sensitive_values))

    render_action_result(result, _write_redacted, register_run_action=_register)


def _maybe_open_command_url(
    element: Dict[str, Any],
    result: Dict[str, Any],
    *,
    no_open: bool,
) -> None:
    browser = element.get("browser")
    if (
        no_open
        or not isinstance(browser, dict)
        or browser.get("auto_open_local") is not True
        or not is_local_interactive_output()
    ):
        return
    display = result.get("display")
    actions = display.get("actions") if isinstance(display, dict) else None
    url = next(
        (
            action.get("url")
            for action in (actions or [])
            if isinstance(action, dict)
            and action.get("kind") == "open_url"
            and isinstance(action.get("url"), str)
            and action.get("url")
        ),
        None,
    )
    if isinstance(url, str):
        try:
            webbrowser.open(url)
        except Exception:
            return


def _foreground_step_element(
    command: Dict[str, Any],
    step: Dict[str, Any],
    attempt_id: Any,
) -> Dict[str, Any]:
    fixed = step.get("fixed_params")
    fixed_params = dict(fixed) if isinstance(fixed, dict) else {}
    attempt_param = step.get("attempt_param")
    if isinstance(attempt_param, str) and attempt_param:
        fixed_params[attempt_param] = attempt_id
    return {
        "ui_type": "command_foreground_step",
        "plugin": step.get("plugin") or command.get("plugin"),
        "id": f"{command.get('id')}:{step.get('action_id')}",
        "label": step.get("label") or step.get("action_id"),
        "action_id": step.get("action_id"),
        "action_owner": step.get("action_owner") or command.get("action_owner"),
        "fixed_params": fixed_params,
    }


async def _execute_command_element(
    app: TerminalApplication,
    element: Dict[str, Any],
    inline_values: Dict[str, str],
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
    *,
    no_open: bool = False,
) -> None:
    if element.get("disabled") is True:
        reason = element.get("disabled_reason") or element.get("description")
        raise TerminalUserError(
            "command is disabled"
            + (f": {reason}" if isinstance(reason, str) and reason else "")
        )
    context = app.action_context()
    dialog_values = await _collect_action_form(
        element.get("dialog"),
        context=context,
        inline_values=inline_values,
        ui_state=ui_state,
    )
    sensitive_values = _sensitive_form_values(
        element.get("dialog"),
        dialog_values,
    )
    result = _execute_ui_element_redacted(
        app,
        element,
        context=context,
        dialog_values=dialog_values,
        sensitive_values=sensitive_values,
    )
    _render_action_result(
        app,
        result,
        write,
        context=context,
        sensitive_values=sensitive_values,
    )
    _maybe_open_command_url(element, result, no_open=no_open)

    foreground = element.get("foreground")
    if not isinstance(foreground, dict):
        return
    state_path = foreground.get("state_path")
    attempt_id = _result_path(result, foreground.get("attempt_id_path"))
    pending = set(foreground.get("pending_states") or ["pending"])
    terminal = set(
        (foreground.get("success_states") or [])
        + (foreground.get("failure_states") or [])
        + (foreground.get("cancelled_states") or [])
        + (foreground.get("expired_states") or [])
    )
    poll_interval = foreground.get("poll_interval_seconds", 0.5)
    if not isinstance(poll_interval, (int, float)) or poll_interval <= 0:
        poll_interval = 0.5
    poll_interval = min(float(poll_interval), 5.0)
    state = _result_path(result, state_path)
    try:
        while state in pending:
            await asyncio.sleep(poll_interval)
            status_step = foreground.get("status")
            if not isinstance(status_step, dict):
                raise TerminalUserError("foreground command is missing status action")
            status_element = _foreground_step_element(
                element,
                status_step,
                attempt_id,
            )
            result = _execute_ui_element_redacted(
                app,
                status_element,
                context=context,
                sensitive_values=sensitive_values,
            )
            next_state = _result_path(result, state_path)
            if next_state != state or next_state in terminal:
                _render_action_result(
                    app,
                    result,
                    write,
                    context=context,
                    sensitive_values=sensitive_values,
                )
            state = next_state
        if terminal and state not in terminal:
            raise TerminalUserError(
                f"foreground command returned undeclared state {state!r}"
            )
    except asyncio.CancelledError:
        cancel_step = foreground.get("cancel")
        if isinstance(cancel_step, dict):
            cancel_element = _foreground_step_element(
                element,
                cancel_step,
                attempt_id,
            )
            cancel_result = _execute_ui_element_redacted(
                app,
                cancel_element,
                context=context,
                sensitive_values=sensitive_values,
            )
            _render_action_result(
                app,
                cancel_result,
                write,
                context=context,
                sensitive_values=sensitive_values,
            )
        raise
    except KeyboardInterrupt:
        cancel_step = foreground.get("cancel")
        if isinstance(cancel_step, dict):
            cancel_element = _foreground_step_element(
                element,
                cancel_step,
                attempt_id,
            )
            cancel_result = _execute_ui_element_redacted(
                app,
                cancel_element,
                context=context,
                sensitive_values=sensitive_values,
            )
            _render_action_result(
                app,
                cancel_result,
                write,
                context=context,
                sensitive_values=sensitive_values,
            )
        raise TerminalUserError("foreground command cancelled")


async def _poll_events(
    app: TerminalApplication,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
    poll_interval: float = 0.1,
    invalidate: Optional[Callable[[], None]] = None,
) -> None:
    while ui_state.get("running", True):
        events = app.poll_new_events(limit=50)
        renderer = ui_state.get("renderer")
        for ev in events:
            current_progress = ui_state.get("progress_state")
            if not isinstance(current_progress, TerminalProgressState):
                current_progress = IDLE_PROGRESS
            next_progress = reduce_terminal_progress(current_progress, ev)
            if next_progress != current_progress:
                ui_state["progress_state"] = next_progress
                if invalidate is not None:
                    try:
                        invalidate()
                    except Exception:
                        pass

            # Prefer the shared TerminalRenderContext when available so that
            # streaming events and history listing share the same visuals.
            if isinstance(renderer, TerminalRenderContext):
                renderer.render_event(ev, write)

            etype = ev.get("type")
            if etype == "request_started":
                rid = ev.get("request_id")
                if isinstance(rid, str):
                    ui_state["active_request_id"] = rid
            elif etype in {"request_completed", "request_cancelled"}:
                rid = ev.get("request_id")
                active = ui_state.get("active_request_id")
                if active is None or active == rid:
                    ui_state["active_request_id"] = None

        poll_notifications = getattr(app, "poll_notification_updates", None)
        if callable(poll_notifications):
            try:
                notification_updates = poll_notifications(limit=100)
            except Exception as exc:
                notification_updates = []
                write(f"[notifications] unable to refresh: {exc}")
        else:
            notification_updates = []
        for update in notification_updates:
            notification = update.get("notification")
            if not isinstance(notification, dict):
                continue
            display = notification.get("display")
            if not isinstance(display, dict):
                continue
            try:
                context = app.action_context()
            except Exception:
                context = {}
            _render_action_result(
                app,
                {"display": display},
                write,
                context=context,
                notification={
                    "scope": update.get("scope"),
                    "session_id": update.get("session_id"),
                    "notification_id": notification.get("id"),
                    "revision": notification_revision_token(notification),
                },
            )

        await asyncio.sleep(poll_interval)


def _reset_terminal_transient_state(ui_state: Dict[str, Any]) -> None:
    renderer = ui_state.get("renderer")
    if isinstance(renderer, TerminalRenderContext):
        renderer.reset_transient_state()
    ui_state["progress_state"] = IDLE_PROGRESS
    ui_state["active_request_id"] = None
    invalidate = ui_state.get("invalidate")
    if callable(invalidate):
        try:
            invalidate()
        except Exception:
            pass


@slash_command("ui_schema", "Get schema for UI configuration")
async def _cmd_ui_schema(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    # Debug helper: rely on the centralized error handler. Reuse the
    # current session/core via TerminalApplication.require_session so
    # that any missing-session issues are surfaced consistently.

    core, base_config, session = app.require_session()
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    overrides_val = metadata.get("overrides")
    overrides = overrides_val if isinstance(overrides_val, dict) else {}
    config = resolve_request_config(base_config, overrides)
    schema = core.get_ui_schema(config=config)

    # Print directly so that the raw schema is visible for debugging.
    print(schema)


def _action_completion(app: TerminalApplication, text: str) -> List[Completion]:
    try:
        tokens = shlex.split(text)
    except ValueError:
        return []
    prefix = ""
    if text and not text.endswith(" ") and tokens:
        prefix = tokens[-1]
    if not tokens or (len(tokens) == 1 and prefix):
        return [
            Completion(
                str(element["id"]),
                start_position=-len(prefix),
                display=str(element["id"]),
                display_meta=f"{element.get('scope')} {element.get('plugin')}",
            )
            for element in app.action_elements()
            if str(element.get("id") or "").startswith(prefix)
        ]
    return []


def _write_action_inventory(
    elements: List[Dict[str, Any]],
    write: Callable[[str], None],
    *,
    message_index: int | None = None,
) -> None:
    if not elements:
        write("[action] no applicable actions")
        return
    write("[action] applicable actions:")
    for element in elements:
        scope = str(element.get("scope") or "session")
        plugin = str(element.get("plugin") or "")
        element_id = str(element.get("id") or "")
        label = str(element.get("label") or element_id)
        disabled = element.get("disabled") is True
        reason = element.get("disabled_reason") or element.get("description")
        if message_index is not None:
            command = (
                f"/action --message {message_index} --plugin {plugin} {element_id}"
            )
        else:
            command = (
                f"/action --scope {scope} --plugin {plugin} {element_id}"
            )
        suffix = ""
        if disabled:
            suffix = " [disabled"
            if isinstance(reason, str) and reason:
                suffix += f": {reason}"
            suffix += "]"
        write(f"  {label}{suffix}")
        if not disabled:
            write(f"    {command}")


@slash_command(
    "action",
    "List or run applicable plugin actions",
    completer=_action_completion,
)
async def _cmd_action(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    try:
        tokens = shlex.split(arg or "")
    except ValueError as exc:
        raise TerminalUserError(f"invalid /action arguments: {exc}") from exc

    if tokens[:1] == ["--ref"]:
        if len(tokens) != 2:
            raise TerminalUserError("usage: /action --ref REFERENCE")
        reference = tokens[1]
        entry = app.get_action_reference(reference)
        context = dict(entry.get("context") or {})
        element = dict(entry.get("element") or {})
        form_values = await _collect_action_form(
            element.get("form"),
            context=context,
            inline_values=None,
            ui_state=ui_state,
        )
        dialog_values = await _collect_action_form(
            element.get("dialog"),
            context=context,
            inline_values=None,
            ui_state=ui_state,
        )
        sensitive_values = [
            *_sensitive_form_values(element.get("form"), form_values),
            *_sensitive_form_values(element.get("dialog"), dialog_values),
        ]
        try:
            result, _element, result_context = app.execute_action_reference(
                reference,
                dialog_values=dialog_values,
                form_values=form_values,
            )
        except Exception as exc:
            message = _redact_sensitive_text(str(exc), sensitive_values)
            if message != str(exc):
                raise TerminalUserError(message) from exc
            raise
        _render_action_result(
            app,
            result,
            write,
            context=result_context,
            sensitive_values=sensitive_values,
        )
        return

    message_index: int | None = None
    plugin: str | None = None
    scope: str | None = None
    position = 0
    while position < len(tokens) and tokens[position].startswith("--"):
        option = tokens[position]
        if option not in {"--message", "--plugin", "--scope"}:
            raise TerminalUserError(f"unknown /action option {option!r}")
        if position + 1 >= len(tokens):
            raise TerminalUserError(f"{option} requires a value")
        value = tokens[position + 1]
        position += 2
        if option == "--message":
            try:
                message_index = int(value)
            except ValueError as exc:
                raise TerminalUserError("--message requires an integer") from exc
        elif option == "--plugin":
            plugin = value
        else:
            if value not in {"application", "session", "session-list"}:
                raise TerminalUserError(
                    "--scope must be application, session, or session-list"
                )
            scope = value

    remaining = tokens[position:]
    if not remaining:
        elements = app.action_elements(message_index=message_index)
        canonical_index = None
        if message_index is not None:
            canonical_index, _message = app.show_message(message_index)
        _write_action_inventory(
            elements,
            write,
            message_index=canonical_index,
        )
        return

    element_id = remaining[0]
    inline_values = _inline_assignments(remaining[1:])
    element = app.resolve_action_element(
        element_id,
        plugin=plugin,
        scope=scope,
        message_index=message_index,
    )
    context = app.action_context(message_index=message_index)
    dialog_values = await _collect_action_form(
        element.get("dialog"),
        context=context,
        inline_values=inline_values,
        ui_state=ui_state,
    )
    sensitive_values = _sensitive_form_values(
        element.get("dialog"),
        dialog_values,
    )
    result = _execute_ui_element_redacted(
        app,
        element,
        context=context,
        dialog_values=dialog_values,
        sensitive_values=sensitive_values,
    )
    _render_action_result(
        app,
        result,
        write,
        context=context,
        sensitive_values=sensitive_values,
    )


def _agent_completion(app: TerminalApplication, text: str) -> List[Completion]:
    agents = app.list_agents()

    prefix = text
    # Only complete a single token after /agent
    if " " in prefix:
        return []

    completions: List[Completion] = []
    for agent in agents:
        if not prefix or agent.startswith(prefix):
            completions.append(
                Completion(
                    agent,
                    start_position=-len(prefix),
                    display=agent,
                    display_meta="agent",
                )
            )
    return completions


def _session_completion(app: TerminalApplication, text: str) -> List[Completion]:
    stripped = text.lstrip()
    filter_marker = "--filter "
    marker_index = stripped.rfind(filter_marker)
    if marker_index >= 0:
        assignment = stripped[marker_index + len(filter_marker) :]
        if " " not in assignment:
            if "=" not in assignment:
                prefix = assignment
                schema = app.session_filter_schema()
                return [
                    Completion(
                        f"{declaration['id']}=",
                        start_position=-len(prefix),
                        display=declaration["id"],
                        display_meta=declaration.get("type", "filter"),
                    )
                    for declaration in schema.get("filters", [])
                    if isinstance(declaration, dict)
                    and isinstance(declaration.get("id"), str)
                    and declaration.get("main_search") is not True
                    and declaration["id"].startswith(prefix)
                ]

            filter_id, _, raw_prefix = assignment.partition("=")
            value_prefix = raw_prefix.rsplit(",", 1)[-1]
            values = app.session_filter_completion_values(filter_id)
            return [
                Completion(
                    value,
                    start_position=-len(value_prefix),
                    display=value,
                    display_meta=filter_id,
                )
                for value in values
                if value.startswith(value_prefix)
            ]

    last_token = stripped.rsplit(" ", 1)[-1]
    if last_token.startswith("--") and "--filter".startswith(last_token):
        return [
            Completion(
                "--filter",
                start_position=-len(last_token),
                display="--filter",
                display_meta="session filter",
            )
        ]

    try:
        query = parse_session_query(stripped)
    except ValueError:
        return []

    try:
        sessions = app.query_sessions_metadata(
            search_text=query.search_text,
            filter_inputs=query.filter_inputs,
        )
    except TerminalUserError:
        try:
            sessions = app.query_sessions_metadata(
                filter_inputs=query.filter_inputs,
            )
        except TerminalUserError:
            return []
        if query.search_text:
            sessions = [
                entry
                for entry in sessions
                if isinstance(entry.get("session_id"), str)
                and entry["session_id"].startswith(query.search_text)
            ]

    replacement_prefix = query.search_text
    completions: List[Completion] = []
    for entry in sessions:
        sid = entry.get("session_id")
        if not isinstance(sid, str) or not sid:
            continue
        presentation = entry.get("presentation")
        title = (
            presentation.get("title")
            if isinstance(presentation, dict)
            and isinstance(presentation.get("title"), str)
            else entry.get("preview")
        )
        meta = title if isinstance(title, str) else ""
        completions.append(
            Completion(
                sid,
                start_position=-len(replacement_prefix),
                display=sid,
                display_meta=meta,
            )
        )
    return completions


def _plugins_completion(app: TerminalApplication, text: str) -> List[Completion]:
    rest = text.lstrip()
    completions: List[Completion] = []

    # First token: subcommand
    if " " not in rest:
        prefix = rest
        for sub in ["on", "off", "reset"]:
            if not prefix or sub.startswith(prefix):
                completions.append(
                    Completion(
                        sub,
                        start_position=-len(prefix),
                        display=sub,
                        display_meta="subcommand",
                    )
                )
        return completions

    sub, _, tail = rest.partition(" ")
    tail = tail.lstrip()
    if sub not in {"on", "off"}:
        return completions

    prefix = tail
    try:
        plugins = app.list_plugins_for_session()
    except Exception:
        return completions

    for entry in plugins:
        pid = entry.get("id")
        if not isinstance(pid, str) or not pid:
            continue
        if prefix and not pid.startswith(prefix):
            continue
        kind = entry.get("kind")
        enabled = bool(entry.get("enabled"))
        status = "on" if enabled else "off"
        meta_parts: List[str] = []
        if isinstance(kind, str) and kind:
            meta_parts.append(kind)
        meta_parts.append(status)
        meta = " ".join(meta_parts)
        completions.append(
            Completion(
                pid,
                start_position=-len(prefix),
                display=pid,
                display_meta=meta,
            )
        )
    return completions


@slash_command(
    "agent", "Switch the active agent for this session", completer=_agent_completion
)
async def _cmd_agent(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    agents = app.list_agents()
    if not agents:
        raise TerminalUserError("no agents configured")

    selection = (arg or "").strip()
    current_agent = app.current_agent_id()

    # If an agent identifier (or index) is provided, switch immediately.
    if selection:
        target: Optional[str] = None
        if selection.isdigit():
            index = int(selection)
            if 1 <= index <= len(agents):
                target = agents[index - 1]
        if target is None and selection in agents:
            target = selection

        if target is None:
            raise TerminalUserError(f"unknown agent: {selection!r}")

        if target == current_agent:
            raise TerminalUserError(f"already using agent {target!r}")

        app.switch_agent(target)
        _reset_terminal_transient_state(ui_state)
        write(f"[agent] switched to {target!r}")
        return

    # No argument: fall back to a simple text-based selection.
    ui_state["pending_agent_choices"] = agents

    write("\n[agent] Available agents:")
    for index, agent in enumerate(agents, 1):
        marker = "*" if agent == current_agent else " "
        write(f"  {index}. [{marker}] {agent}")
    write("[agent] Enter agent name or number (empty to cancel):")


@slash_command(
    "session", "Switch to an existing session", completer=_session_completion
)
async def _cmd_session(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    try:
        query = parse_session_query(arg or "")
    except ValueError as exc:
        raise TerminalUserError(str(exc)) from exc

    if query.search_text and app.is_saved_session_id(query.search_text):
        session = app.switch_session(query.search_text)
        _reset_terminal_transient_state(ui_state)
        write(f"[session] switched to {session.session_id!r}")
        return

    all_sessions = app.list_sessions_metadata()
    if not all_sessions:
        raise TerminalUserError("no saved sessions found")

    sessions = app.query_sessions_metadata(
        search_text=query.search_text,
        filter_inputs=query.filter_inputs,
    )
    if not sessions:
        raise TerminalUserError("no sessions match the active filters")

    ui_state["pending_session_choices"] = [
        entry.get("session_id")
        for entry in sessions
        if isinstance(entry.get("session_id"), str) and entry.get("session_id")
    ]

    try:
        current_session_id = app.session_id
    except RuntimeError:
        current_session_id = None

    write("\n[session] Matching sessions:")
    for index, entry in enumerate(sessions, 1):
        sid = entry.get("session_id")
        if not isinstance(sid, str) or not sid:
            continue
        marker = "*" if sid == current_session_id else " "
        presentation = entry.get("presentation")
        title = (
            presentation.get("title")
            if isinstance(presentation, dict)
            and isinstance(presentation.get("title"), str)
            else entry.get("preview")
        )
        if isinstance(title, str) and title and title != sid:
            write(f"  {index}. [{marker}] {sid} - {title}")
        else:
            write(f"  {index}. [{marker}] {sid}")
    write("[session] Enter session id or number (empty to cancel):")


def _help_completion(app: TerminalApplication, text: str) -> List[Completion]:
    rest = text.lstrip()
    prefix = rest
    # Only complete a single token after /help
    if " " in rest:
        return []

    completions: List[Completion] = []
    sub = "config"
    if not prefix or sub.startswith(prefix):
        completions.append(
            Completion(
                sub,
                start_position=-len(prefix),
                display=sub,
                display_meta="subcommand",
            )
        )
    return completions


@slash_command("help", "Show commands and shortcuts", completer=_help_completion)
async def _cmd_help(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()

    if text == "config":
        # Show top-level config keys for the currently enabled plugins.
        core, base_config, session = app.require_session()
        schema_entries = core.get_config_schema()

        try:
            plugin_entries = app.list_plugins_for_session()
        except Exception:
            plugin_entries = []

        # Build plugin status mapping so we can consistently reflect
        # enabled/active state across config sections and tint
        # configuration for inactive or turned-off plugins.
        plugin_status: Dict[str, Dict[str, bool]] = {}
        for p in plugin_entries:
            pid = p.get("id")
            if not isinstance(pid, str) or not pid:
                continue
            enabled_flag = bool(p.get("enabled"))
            active_flag = bool(p.get("active", True))
            plugin_status[pid] = {"enabled": enabled_flag, "active": active_flag}

        if not isinstance(schema_entries, list) or not schema_entries:
            write("[help config] no config keys available for current plugins")
        else:
            # Sort config keys by plugin name, then key.
            items: List[Tuple[str, str, Dict[str, Any]]] = []
            for raw_entry in schema_entries:
                if not isinstance(raw_entry, dict):
                    continue
                key = raw_entry.get("key")
                if not isinstance(key, str) or not key:
                    continue
                plugin_name_val = raw_entry.get("plugin")
                plugin_name = (
                    plugin_name_val
                    if isinstance(plugin_name_val, str) and plugin_name_val
                    else "unknown"
                )
                items.append((plugin_name, key, raw_entry))

            items.sort(key=lambda item: (item[0], item[1]))

            write("\n[help] Config keys for enabled plugins:")
            for plugin_name, key, entry in items:
                type_name = entry.get("type", "?")
                default_val = entry.get("default")
                description = entry.get("description") or ""
                current_val = base_config.get(key, default_val)

                status = plugin_status.get(plugin_name)
                is_off_or_inactive = bool(
                    status
                    and (
                        not status.get("enabled", True)
                        or not status.get("active", True)
                    )
                )
                is_inactive_only = bool(status and not status.get("active", True))

                # If the key is not explicitly set in the base config,
                # the default is in effect; in that case omit the
                # "current" marker and show only the default.
                has_explicit = isinstance(base_config, dict) and key in base_config
                if has_explicit:
                    values_body = f"default={default_val!r}, current={current_val!r}"
                else:
                    values_body = f"default={default_val!r}"

                if is_off_or_inactive:
                    # For plugins that are disabled or inactive, show the
                    # entire line in gray to indicate that the
                    # configuration is not currently in effect.
                    inactive_suffix = " (inactive)" if is_inactive_only else ""
                    plain_desc = f" - {description}" if description else ""
                    plain_line = (
                        f"  {key} ({type_name}) "
                        f"[{plugin_name}{inactive_suffix}] {values_body}{plain_desc}"
                    )
                    write(f"\x1b[90m{plain_line}\x1b[0m")
                    continue

                # Bold when an explicit config value is in effect;
                # normal when only the default is used.
                if has_explicit:
                    key_str = f"\x1b[1;33m{key}\x1b[0m"
                else:
                    key_str = f"\x1b[33m{key}\x1b[0m"
                inactive_suffix = " (inactive)" if is_inactive_only else ""
                plugin_str = f"\x1b[34m[{plugin_name}{inactive_suffix}]\x1b[0m"
                type_str = f"\x1b[34m{type_name}\x1b[0m"
                values_str = f"\x1b[90m{values_body}\x1b[0m"

                if description:
                    desc_str = f"\x1b[90m{description}\x1b[0m"
                    write(
                        f"  {key_str} ({type_str}) {plugin_str} {values_str} - {desc_str}"
                    )
                else:
                    write(f"  {key_str} ({type_str}) {plugin_str} {values_str}")

        # List available plugins for this session with their enabled
        # status, mirroring the style of /plugins.
        if plugin_entries:
            write("\n[help] Plugins for this session:")
            kind_labels = {
                "providers": "provider",
                "extensions": "extension",
                "features": "feature",
                "tools": "tool",
            }
            for entry in plugin_entries:
                enabled = bool(entry.get("enabled"))
                raw_kind = entry.get("kind")
                kind = raw_kind if isinstance(raw_kind, str) else ""
                display_kind = kind_labels.get(kind, kind or "-")
                pid = entry.get("id") if isinstance(entry.get("id"), str) else ""
                active = bool(entry.get("active", True))

                # Name in yellow; bold when enabled and active, normal
                # yellow otherwise.
                if enabled and active:
                    name_str = f"\x1b[1;33m{pid}\x1b[0m"
                else:
                    name_str = f"\x1b[33m{pid}\x1b[0m"

                # Type in brackets, styled similarly to other type
                # annotations in the help output.
                type_str = f"\x1b[34m[{display_kind}]\x1b[0m"

                # Status marker [ON]/[OFF] in gray.
                status_label = "ON" if enabled else "OFF"
                status_str = f"\x1b[90m[{status_label}]\x1b[0m"

                # Inactive flag when the plugin is not active for this
                # session.
                inactive_str = "\x1b[90m (inactive)\x1b[0m" if not active else ""

                write(f"  {name_str} {type_str} {status_str}{inactive_str}")

        # Load any per-session configuration overrides stored in the
        # session metadata so that we can display current vs. override
        # values for configurable settings.
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides_val = metadata.get("overrides")
        overrides: Dict[str, Any] = (
            overrides_val if isinstance(overrides_val, dict) else {}
        )

        # Also show configurable settings exposed via /set (UI schema).
        ui_elements = app.session_ui_elements()

        if ui_elements:
            # Sort configurable settings by plugin name, then key.
            cfg_items: List[Tuple[str, str, Dict[str, Any]]] = []
            for el in ui_elements:
                key_val = el.get("key")
                if not isinstance(key_val, str) or not key_val:
                    continue
                plugin_name_val = el.get("plugin")
                plugin_name = (
                    plugin_name_val
                    if isinstance(plugin_name_val, str) and plugin_name_val
                    else "unknown"
                )
                cfg_items.append((plugin_name, key_val, el))

            cfg_items.sort(key=lambda item: (item[0], item[1]))

            write("\n[help] Configurable settings (via /set):")
            for plugin_name, key_val, el in cfg_items:
                schema_entry = None
                # Prefer an exact match on (plugin, key) when multiple
                # plugins contribute the same key.
                if isinstance(schema_entries, list):
                    for entry in schema_entries:
                        if not isinstance(entry, dict):
                            continue
                        if (
                            entry.get("key") == key_val
                            and entry.get("plugin") == plugin_name
                        ):
                            schema_entry = entry
                            break
                type_name = (
                    schema_entry.get("type", "?")
                    if isinstance(schema_entry, dict)
                    else "?"
                )
                label_val = el.get("label")
                desc_val = el.get("description")
                info = (
                    label_val
                    if isinstance(label_val, str) and label_val
                    else (desc_val if isinstance(desc_val, str) else "")
                )

                # Determine the effective current value for this key.
                has_current, current_value = _resolve_setting_current_value(
                    el,
                    base_config if isinstance(base_config, dict) else {},
                    schema_entry if isinstance(schema_entry, dict) else None,
                )
                current_str = repr(current_value) if has_current else "none"

                # Override value comes from per-session overrides. If
                # no override exists for this key, we omit it from the
                # display instead of showing a placeholder.
                has_override = key_val in overrides
                override_str = repr(overrides[key_val]) if has_override else "none"

                status = plugin_status.get(plugin_name)
                is_off_or_inactive = bool(
                    status
                    and (
                        not status.get("enabled", True)
                        or not status.get("active", True)
                    )
                )
                is_inactive_only = bool(status and not status.get("active", True))

                if is_off_or_inactive:
                    # Entire line gray for settings belonging to
                    # disabled or inactive plugins.
                    inactive_suffix = " (inactive)" if is_inactive_only else ""
                    if has_override:
                        values_body = f"current={current_str}, override={override_str}"
                    else:
                        values_body = f"current={current_str}"
                    info_suffix = f" - {info}" if info else ""
                    plain_line = (
                        f"  {key_val} ({type_name}) "
                        f"[{plugin_name}{inactive_suffix}] {values_body}{info_suffix}"
                    )
                    write(f"\x1b[90m{plain_line}\x1b[0m")
                    continue

                # Normal colouring for active/enabled plugins.
                if has_override:
                    key_str = f"\x1b[1;33m{key_val}\x1b[0m"
                else:
                    key_str = f"\x1b[33m{key_val}\x1b[0m"
                inactive_suffix = " (inactive)" if is_inactive_only else ""
                plugin_str = f"\x1b[34m[{plugin_name}{inactive_suffix}]\x1b[0m"
                type_str = f"\x1b[34m{type_name}\x1b[0m"
                if has_override:
                    values_body = f"current={current_str}, override={override_str}"
                else:
                    values_body = f"current={current_str}"
                values_str = f"\x1b[90m{values_body}\x1b[0m"
                if info:
                    info_str = f"\x1b[90m{info}\x1b[0m"
                    write(
                        f"  {key_str} ({type_str}) {plugin_str} {values_str} - {info_str}"
                    )
                else:
                    write(f"  {key_str} ({type_str}) {plugin_str} {values_str}")
        else:
            write(
                "\n[help] No configurable settings available via /set for this session"
            )

        # Finally, show application-level config options from the
        # top-level "application" section (used by the terminal app
        # itself for things like tool output limits). This is driven by
        # a static schema so that all options are visible even when they
        # are not explicitly set in the config file.
        app_cfg_schema = app.get_application_config_schema()
        app_cfg = app.agent_app.get_application_config()

        if app_cfg_schema:
            write('\n[help] Application-level config options (config["application"]):')
            for key in sorted(app_cfg_schema.keys()):
                meta = app_cfg_schema.get(key) or {}
                type_name = meta.get("type", "?")
                default_val = meta.get("default")
                desc = meta.get("description") or ""
                current_val = app_cfg.get(key, default_val)

                # Bold when an explicit application-level config value
                # is set for this key; normal when only the default is
                # in effect.
                has_explicit_app = isinstance(app_cfg, dict) and key in app_cfg
                if has_explicit_app:
                    key_str = f"\x1b[1;33m{key}\x1b[0m"
                else:
                    key_str = f"\x1b[33m{key}\x1b[0m"
                type_str = f"\x1b[34m{type_name}\x1b[0m"
                values_str = (
                    f"\x1b[90mdefault={default_val!r}, current={current_val!r}\x1b[0m"
                )
                if desc:
                    desc_str = f"\x1b[90m{desc}\x1b[0m"
                    write(f"  {key_str} ({type_str}) {values_str} - {desc_str}")
                else:
                    write(f"  {key_str} ({type_str}) {values_str}")
        else:
            write(
                "\n[help] No application-level config options defined (schema is empty)"
            )

        write("")
        return

    write("\nCommands:")
    for cmd in iter_slash_commands():
        write(f"  /{cmd.name:10s} - {cmd.description}")
    for element in _dynamic_slash_commands(app):
        path = element.get("path")
        if not isinstance(path, list) or not path:
            continue
        command = "/" + " ".join(str(token) for token in path)
        write(
            f"  {command:10s} - "
            f"{element.get('description') or element.get('label') or ''}"
        )
        aliases = [
            "/" + " ".join(str(token) for token in alias)
            for alias in (element.get("aliases") or [])
            if isinstance(alias, list) and alias
        ]
        if aliases:
            write(f"    aliases: {', '.join(aliases)}")
        arguments = [f"{name}=VALUE" for name in _command_argument_names(element)]
        if isinstance(element.get("browser"), dict):
            arguments.append("--no-open")
        if arguments:
            write(f"    arguments: {' '.join(arguments)}")
        if element.get("disabled") is True:
            reason = element.get("disabled_reason") or element.get("description")
            if isinstance(reason, str) and reason:
                write(f"    disabled: {reason}")

    write("\nShortcuts (while typing):")
    for sc in iter_shortcuts():
        write(f"  {sc.keys:10s} - {sc.description}")
    write("")


@slash_command("new", "Start a new session")
@shortcut("c-n", "Start a new session")
async def _cmd_new_session(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    session = app.start_new_session(agent_id=None, persist=False)
    app.reset_event_cursor()
    _reset_terminal_transient_state(ui_state)
    write(f"[session] switched to {session.session_id}")


@slash_command("exit", "Exit the terminal client")
@slash_command("quit")
@shortcut("c-q", "Exit the terminal client")
async def _cmd_exit(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    write("Exiting...")
    ui_state["running"] = False


def _handle_agent_selection(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    choices = ui_state.get("pending_agent_choices") or []
    ui_state["pending_agent_choices"] = None

    selection = text.strip()
    if not selection:
        write("[agent] selection cancelled")
        return

    target: Optional[str] = None
    if selection.isdigit():
        index = int(selection)
        if 1 <= index <= len(choices):
            target = choices[index - 1]
    if target is None and selection in choices:
        target = selection

    if target is None:
        write(f"[agent] invalid selection: {selection!r}")
        return

    current_agent = app.current_agent_id()
    if target == current_agent:
        write(f"[agent] already using agent {target!r}")
        return

    try:
        app.switch_agent(target)
    except Exception as exc:  # pragma: no cover - defensive
        _render_terminal_exception("agent", exc, write)
        return

    _reset_terminal_transient_state(ui_state)
    write(f"[agent] switched to {target!r}")


def _handle_session_selection(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    choices = ui_state.get("pending_session_choices") or []
    ui_state["pending_session_choices"] = None

    selection = text.strip()
    if not selection:
        write("[session] selection cancelled")
        return

    target: Optional[str] = None
    if selection.isdigit():
        index = int(selection)
        if 1 <= index <= len(choices):
            target = choices[index - 1]
    if target is None and selection in choices:
        target = selection

    if target is None:
        write(f"[session] invalid selection: {selection!r}")
        return

    try:
        session = app.switch_session(target)
    except Exception as exc:  # pragma: no cover - defensive
        _render_terminal_exception("session", exc, write)
        return

    _reset_terminal_transient_state(ui_state)
    write(f"[session] switched to {session.session_id!r}")


def _set_completion(app: TerminalApplication, text: str) -> List[Completion]:
    elements = app.session_ui_elements()
    rest = text.lstrip()
    completions: List[Completion] = []

    # No or single token after /set: complete keys.
    if " " not in rest:
        key_prefix = rest
        seen: set[str] = set()
        for el in elements:
            key = el.get("key")
            if not isinstance(key, str) or not key or key in seen:
                continue
            if not key_prefix or key.startswith(key_prefix):
                seen.add(key)
                completions.append(
                    Completion(
                        key,
                        start_position=-len(key_prefix),
                        display=key,
                        display_meta="setting",
                    )
                )
        return completions

    # Complete option values for a specific key.
    key_token, _, value_prefix = rest.partition(" ")
    value_prefix = value_prefix.lstrip()
    raw_prefix = value_prefix

    target_el: Optional[Dict[str, Any]] = None
    for el in elements:
        if el.get("key") == key_token:
            target_el = el
            break

    if target_el is None:
        return completions

    options = target_el.get("options") or []
    el_type = target_el.get("type")

    # Special-case boolean / checkbox settings: suggest "true" / "false"
    # without any extra meta information.
    if el_type == "checkbox":
        bool_options = ["true", "false"]
        lower_prefix = value_prefix.lower()
        for opt in bool_options:
            if not value_prefix or opt.startswith(lower_prefix):
                completions.append(
                    Completion(
                        opt,
                        start_position=-len(raw_prefix),
                        display=opt,
                    )
                )
        return completions

    # For non-boolean options, support both plain strings and
    # {"value", "label"} objects. Show the underlying value as the
    # primary suggestion and the human-friendly label as meta.
    normalized = _normalize_setting_options(options)
    for opt_value, opt_display in normalized:
        if not value_prefix or opt_value.startswith(value_prefix):
            completions.append(
                Completion(
                    opt_value,
                    start_position=-len(value_prefix),
                    display=opt_value,
                    display_meta=opt_display,
                )
            )
    return completions


@slash_command(
    "set", "Set a configuration override for this session", completer=_set_completion
)
async def _cmd_set(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    elements = app.session_ui_elements()
    if not elements:
        raise TerminalUserError("no configurable UI elements available")

    by_key: Dict[str, Dict[str, Any]] = {}
    for el in elements:
        key = el.get("key")
        if isinstance(key, str) and key:
            by_key[key] = el

    text = (arg or "").strip()
    if not text:
        write("[set] usage: /set <key> <value>")
        write("[set] Available keys:")
        for key in sorted(by_key.keys()):
            options = by_key[key].get("options") or []
            normalized = _normalize_setting_options(options)
            disabled_suffix = " [disabled]" if by_key[key].get("disabled") else ""
            if normalized:
                display_opts = [opt_display for _, opt_display in normalized]
                write(f"  {key} (options: {', '.join(display_opts)}){disabled_suffix}")
            else:
                write(f"  {key}{disabled_suffix}")
        return

    name_and_val = text.split(" ", 1)
    key = name_and_val[0]
    value = name_and_val[1].strip() if len(name_and_val) > 1 else ""

    el = by_key.get(key)
    if el is None:
        raise TerminalUserError(f"unknown key: {key!r}")

    if el.get("disabled"):
        desc = el.get("description")
        reason = f": {desc}" if isinstance(desc, str) and desc else ""
        raise TerminalUserError(f"setting {key!r} is disabled{reason}")

    if not value:
        raise TerminalUserError(f"missing value for {key!r}")

    options = el.get("options") or []
    normalized = _normalize_setting_options(options)

    coerced: Any = value
    if normalized:
        lowered = value.lower()
        canonical: Optional[str] = None
        for opt_value, opt_display in normalized:
            # Accept either the underlying value or the human label,
            # matching case-sensitively or case-insensitively.
            if (
                value == opt_value
                or value == opt_display
                or lowered == opt_value.lower()
                or lowered == opt_display.lower()
            ):
                canonical = opt_value
                break

        if canonical is None:
            allowed_labels = [opt_display for _, opt_display in normalized]
            raise TerminalUserError(
                f"invalid value for {key!r}. Allowed: {', '.join(allowed_labels)}"
            )

        coerced = canonical

    el_type = el.get("type")
    if el_type == "checkbox":
        lowered = value.lower()
        if lowered in {"true", "1", "yes", "on"}:
            coerced = True
        elif lowered in {"false", "0", "no", "off"}:
            coerced = False
        else:
            raise TerminalUserError(f"invalid boolean for {key!r}: {value!r}")
    elif el_type == "number":
        # Try int first, then float
        try:
            if "." in value or "e" in value.lower():
                coerced = float(value)
            else:
                coerced = int(value)
        except ValueError:
            raise TerminalUserError(f"invalid number for {key!r}: {value!r}")

    try:
        app.update_override(key, coerced)
    except Exception as exc:  # pragma: no cover - defensive
        # Surface configuration update failures as application errors so
        # that they include a stack trace but keep the UI responsive.
        raise TerminalApplicationError(f"failed to update overrides: {exc}")

    write(f"[set] {key}={coerced!r} saved for this session")


@slash_command(
    "plugins", "List or toggle plugins for this session", completer=_plugins_completion
)
async def _cmd_plugins(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()

    if not text:
        entries = app.list_plugins_for_session()

        if not entries:
            raise TerminalUserError("no plugins configured")

        ui_state["plugins_last_list"] = entries

        write("[plugins] Active plugin configuration for this session:")
        kind_labels = {
            "providers": "provider",
            "extensions": "extension",
            "features": "feature",
            "tools": "tool",
        }
        for index, entry in enumerate(entries, 1):
            enabled = bool(entry.get("enabled"))
            status = "on " if enabled else "off"
            raw_kind = entry.get("kind")
            kind = raw_kind if isinstance(raw_kind, str) else ""
            display_kind = kind_labels.get(kind, kind or "-")
            pid = entry.get("id") if isinstance(entry.get("id"), str) else ""
            active = bool(entry.get("active", True))
            inactive_suffix = " (inactive)" if not active else ""
            write(f"  {index}. [{status:3s}] {display_kind:<9s} {pid}{inactive_suffix}")
        return

    # Subcommands: on, off, reset
    parts = text.split(None, 1)
    sub = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    if sub == "reset":
        app.clear_session_plugins()
        write(
            "[plugins] cleared session-specific plugin overrides; using defaults again"
        )
        try:
            ui_state["plugins_last_list"] = app.list_plugins_for_session()
        except Exception:
            ui_state["plugins_last_list"] = []
        return

    if sub not in {"on", "off"}:
        raise TerminalUserError("usage: /plugins [on|off|reset] <id-or-index>")

    target = rest.strip()
    if not target:
        raise TerminalUserError(f"usage: /plugins {sub} <id-or-index>")

    entries = ui_state.get("plugins_last_list")
    if not isinstance(entries, list) or not entries:
        entries = app.list_plugins_for_session()
    ui_state["plugins_last_list"] = entries

    def _resolve_plugin_id(token: str, items: List[Dict[str, Any]]) -> Optional[str]:
        if token.isdigit():
            index = int(token)
            if 1 <= index <= len(items):
                pid = items[index - 1].get("id")
                if isinstance(pid, str) and pid:
                    return pid
        for entry in items:
            pid = entry.get("id")
            if isinstance(pid, str) and pid == token:
                return pid
        name_matches: List[Dict[str, Any]] = [
            entry
            for entry in items
            if isinstance(entry.get("name"), str) and entry["name"] == token
        ]
        if len(name_matches) == 1:
            pid = name_matches[0].get("id")
            if isinstance(pid, str) and pid:
                return pid
        return None

    plugin_id = _resolve_plugin_id(target, entries)
    if plugin_id is None:
        raise TerminalUserError(f"unknown plugin: {target!r}")

    try:
        session = app.session
    except RuntimeError as exc:
        # Treat a missing active session as an application-level
        # invariant violation for this command.
        raise TerminalApplicationError(f"no active session: {exc}")

    metadata = session.metadata or {}
    plugins_from_session = metadata.get("plugins")
    if isinstance(plugins_from_session, list):
        enabled_ids = [p for p in plugins_from_session if isinstance(p, str)]
    else:
        agent_val = metadata.get("agent_id")
        agent_id = agent_val.strip() if isinstance(agent_val, str) else ""
        if not agent_id:
            agents = app.available_agents()
            agent_id = agents[0] if agents else ""
        try:
            default_ids = app.agent_app.get_agent_plugins(agent_id)
        except Exception:  # pragma: no cover - defensive
            default_ids = None
        if default_ids is None:
            enabled_ids = [
                pid
                for pid in (entry.get("id") for entry in entries)
                if isinstance(pid, str) and pid
            ]
        else:
            enabled_ids = [p for p in default_ids if isinstance(p, str)]

    if sub == "on":
        if plugin_id not in enabled_ids:
            enabled_ids.append(plugin_id)
    else:
        enabled_ids = [p for p in enabled_ids if p != plugin_id]

    provider_ids = [
        entry.get("id")
        for entry in entries
        if entry.get("kind") == "providers"
        and isinstance(entry.get("id"), str)
        and entry.get("id")
    ]
    if sub == "off" and not any(pid in enabled_ids for pid in provider_ids):
        write("[plugins] warning: no providers will remain enabled after this change")

    try:
        app.set_session_plugins(cast(List[str], enabled_ids))
    except Exception as exc:  # pragma: no cover - defensive
        raise TerminalApplicationError(f"failed to update plugins: {exc}")

    action = "enabled" if sub == "on" else "disabled"
    write(f"[plugins] {action} plugin {plugin_id!r} for this session")
    try:
        ui_state["plugins_last_list"] = app.list_plugins_for_session()
    except Exception:
        ui_state["plugins_last_list"] = entries


@slash_command("send", "Send a request with the current history")
@shortcut("c-x s", "Send a request with the current history")
async def _cmd_send(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    # Ensure there is an active session; any missing-session issues are
    # treated as application errors and handled by the central wrapper.
    _ = app.session

    started = app.start_request(stream=True)
    if started.status == "already_running":
        write(f"[send] request already running: {started.request_id}")
        return
    write("[send] request started for current session")


@slash_command("append", "Append a message without sending")
async def _cmd_append(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()
    if not text:
        write("[append] usage: /append [user|system|assistant] <content>")
        return

    role = "user"
    content = text

    first, sep, rest = text.partition(" ")
    if first in {"user", "system", "assistant"} and sep:
        role = first
        content = rest.strip()
        if not content:
            raise TerminalUserError("missing content for message")

    # Let TerminalApplication manage session/core state and surface
    # any issues via the central error handler.
    session_id = app.session_id
    app.add_message(session_id, role=role, content=content, metadata=None)

    write(f"[append] appended {role} message without sending")


@shortcut("c-x a", "Append current input as user message without sending")
async def _shortcut_append_current_input(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    message = (text or "").strip()
    if not message:
        return

    try:
        # Let TerminalApplication manage session/core state and surface
        # any issues via the shared error renderer.
        session_id = app.session_id
        app.add_message(session_id, role="user", content=message, metadata=None)
    except Exception as exc:  # pragma: no cover - defensive
        _render_terminal_exception("append", exc, write)
        return

    write("[append] appended user message without sending")


@shortcut("c-x c", "Cancel the active request (if any)")
@slash_command("cancel", "Cancel the active request (if any)")
async def _shortcut_cancel_request(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    request_id = ui_state.get("active_request_id")
    if not isinstance(request_id, str) or not request_id:
        write("[cancel] no active request to cancel")
        return

    try:
        # Delegate cancellation to the application layer and render any
        # errors (including provider/tool issues) through the shared
        # exception renderer so that behaviour matches slash commands.
        app.agent_app.cancel_request(request_id)
    except Exception as exc:  # pragma: no cover - defensive
        _render_terminal_exception("cancel", exc, write)
        return

    write("[cancel] cancellation requested for active request")


@slash_command(
    "soft-cancel",
    "Cancel after the active tool finishes (if any)",
)
async def _cmd_soft_cancel_request(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    request_id = ui_state.get("active_request_id")
    if not isinstance(request_id, str) or not request_id:
        write("[soft-cancel] no active request to cancel")
        return

    try:
        app.agent_app.soft_cancel_request(request_id)
    except Exception as exc:  # pragma: no cover - defensive
        _render_terminal_exception("soft-cancel", exc, write)
        return

    write("[soft-cancel] request will stop after the active tool finishes")


@slash_command("delete", "Delete messages by index or range")
async def _cmd_delete(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()
    if not text:
        raise TerminalUserError("usage: /delete <index> or /delete <start>:<end>")

    # Parse arguments; ranges use slice semantics while a single integer
    # is interpreted as a Python-style index.
    if ":" in text:
        bounds = _parse_range_or_index_arg(text, command="delete", write=write)
        if bounds is None:
            return

        start_val, end_val = bounds

        _session, deleted = app.delete_messages_by_range(start_val, end_val)
    else:
        try:
            raw_index = int(text)
        except ValueError:
            raise TerminalUserError("invalid value; expected an integer or range")

        # Reuse the application's delete_messages helper so that
        # native-history semantics and events remain consistent.
        _session = app.delete_messages([raw_index])
        deleted = [raw_index]

    if deleted:
        write(
            "[delete] deleted messages at indices: "
            + ", ".join(str(i) for i in deleted)
        )
    else:
        write("[delete] no messages deleted")


@slash_command("modify", "Load a message by index for editing")
async def _cmd_modify(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()
    if not text:
        raise TerminalUserError("usage: /modify <index>")

    try:
        raw_index = int(text)
    except ValueError:
        raise TerminalUserError("invalid index; expected an integer")

    # Let TerminalApplication handle index normalization and session
    # state via show_message so that single-index semantics match other
    # history operations (including support for negative indices).
    target_index, message = app.show_message(raw_index)
    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")
    if not isinstance(content, str):
        write("[modify] target message has no string content")
        return

    ui_state["pending_modify_index"] = target_index
    ui_state["input_prefill"] = content
    write(f"[modify] loaded message at index {target_index} for editing")


@slash_command("list", "List messages by count or range")
async def _cmd_list(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()
    use_short = False

    # Optional "short" prefix switches renderers into compact mode.
    if text.startswith("short"):
        first, _, rest = text.partition(" ")
        if first == "short":
            use_short = True
            text = rest.strip()

    items: List[Tuple[int, Any]]

    # For listing, we either:
    # - list all messages when no bounds are provided,
    # - list a slice when a ``start:end`` range is supplied, or
    # - list a single message when given a Python-style index.

    if not text:
        items = app.list_messages_by_range(None, None)
    elif ":" in text:
        bounds = _parse_range_or_index_arg(text, command="list", write=write)
        if bounds is None:
            return
        start_val, end_val = bounds

        items = app.list_messages_by_range(start_val, end_val)
    else:
        # Single integer: interpret as a Python-style index selecting a
        # single message.
        try:
            raw_index = int(text)
        except ValueError:
            raise TerminalUserError("invalid value; expected an integer or range")

        # Delegate index normalization and session validation to the
        # application by selecting a single-element slice.
        items = app.list_messages_by_range(raw_index, raw_index + 1)

    if not items:
        write("[list] no messages to show")
        return

    renderer = ui_state.get("renderer")

    # When no renderer is present in ui_state (for example in tests
    # calling this command directly), create a fresh TerminalRenderContext
    # so that listing uses the same visuals as the interactive UI.
    if not isinstance(renderer, TerminalRenderContext):
        renderer = TerminalRenderContext(
            app=app,
            footer_elements_supplier=lambda: app.message_footer_elements(),
            one_line_supplier=lambda: bool(ui_state.get("tool_output_one_line")),
        )
        ui_state["renderer"] = renderer

    for idx, message in items:
        renderer.render_message(idx, message, write, short=use_short)


def _tool_output_completion(app: TerminalApplication, text: str) -> List[Completion]:
    rest = text.lstrip()
    # Only complete a single mode after /tool-output.
    if " " in rest:
        return []

    completions: List[Completion] = []
    for sub in ["one-line", "full"]:
        if not rest or sub.startswith(rest):
            completions.append(
                Completion(
                    sub,
                    start_position=-len(rest),
                    display=sub,
                    display_meta="mode",
                )
            )
    return completions


def _initial_tool_output_one_line_state(app: TerminalApplication) -> bool:
    """Resolve the startup default for one-line live tool results.

    Reads the application-level ``tool_output_live_one_line`` config key;
    the ``/tool-output`` command changes the runtime state from there.
    """

    try:
        cfg = app.agent_app.get_application_config()
    except Exception:
        return False
    return bool(cfg.get("tool_output_live_one_line", False))


def _startup_help_lines(app: TerminalApplication) -> List[str]:
    """Return the configured startup guidance for the interactive terminal."""

    try:
        cfg = app.agent_app.get_application_config()
    except Exception:
        cfg = {}
    raw_mode = cfg.get("terminal_startup_help", "summary")
    mode = raw_mode.strip().lower() if isinstance(raw_mode, str) else "summary"

    if mode == "off":
        return ["Session started."]
    if mode == "hint":
        return ["Session started. Type /help for commands. Press Ctrl-Q to exit."]
    return [
        "Session started.",
        "Quick help: type a message to send; /cancel stops the active request.",
        "Use /session to switch sessions and /tool-output to control tool results.",
        "Type /help for all commands. Press Ctrl-Q to exit.",
    ]


@slash_command(
    "tool-output",
    "Show or set live tool output mode (one-line|full)",
    completer=_tool_output_completion,
)
async def _cmd_tool_output(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip().lower()
    current = bool(ui_state.get("tool_output_one_line"))

    if not text:
        new_value = current
    elif text == "one-line":
        new_value = True
    elif text == "full":
        new_value = False
    else:
        raise TerminalUserError("usage: /tool-output [one-line|full]")

    ui_state["tool_output_one_line"] = new_value
    if new_value:
        write(
            "[tool-output] one-line - tool results use a compact preview; "
            "use /list <index> to expand one in full"
        )
    else:
        write("[tool-output] full - tool calls stream and render in full")


@slash_command("fork", "Fork the current session (optionally up to an index)")
async def _cmd_fork(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()
    # When no index is provided, default to ``-1`` so that ``/fork``
    # with no arguments copies the entire session (up to the last
    # message) by following Python-style negative index semantics.
    if not text:
        index = -1
    else:
        try:
            index = int(text)
        except ValueError:
            raise TerminalUserError("invalid index; expected an integer")

    source_session_id = app.session_id

    # Let TerminalApplication handle index validation and forking
    # semantics. Errors surface as TerminalUserError or
    # TerminalApplicationError.
    new_session = app.fork_session(index)

    write(f"[fork] forked {source_session_id!r} -> {new_session.session_id!r}")


async def _handle_slash_command(
    app: TerminalApplication,
    raw: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    name_and_arg = raw[1:].strip().split(" ", 1)
    name = name_and_arg[0] if name_and_arg else ""
    arg = name_and_arg[1] if len(name_and_arg) > 1 else ""

    if not name:
        write("[commands] empty command")
        return

    cmd = get_slash_command(name)
    if cmd is None:
        try:
            tokens = shlex.split(raw[1:].strip())
            element, remaining = app.match_slash_command(
                tokens,
                reserved_names=_static_slash_names(),
            )
            if element is None:
                write(f"[commands] unknown command: /{name}")
                return
            no_open = False
            if "--no-open" in remaining:
                if not isinstance(element.get("browser"), dict):
                    raise TerminalUserError(
                        "--no-open is only valid for browser commands"
                    )
                remaining = [token for token in remaining if token != "--no-open"]
                no_open = True
            await _execute_command_element(
                app,
                element,
                _inline_assignments(remaining),
                write,
                ui_state,
                no_open=no_open,
            )
        except Exception as exc:
            _render_terminal_exception(name, exc, write)
        return

    try:
        result = cmd.handler(app, arg, write, ui_state)
        if asyncio.iscoroutine(result):
            await result
    except Exception as exc:  # pragma: no cover - defensive
        # Delegate representation of user vs application errors to the
        # shared rendering helper so that behavior stays consistent
        # across all terminal entry points.
        _render_terminal_exception(cmd.name, exc, write)


async def _handle_user_message(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    try:
        started = app.append_user_message_and_start_request(text, stream=True)
    except RuntimeError:
        # Auto-recover when no active session is present by starting a
        # new ephemeral session and retrying the append.
        write("[error] session not found; starting a new one")
        app.start_new_session(agent_id=None, persist=False)
        started = app.append_user_message_and_start_request(text, stream=True)
    except Exception as exc:  # pragma: no cover - defensive
        # For user-caused errors (``TerminalUserError``) render a
        # simple message; for application errors, include a traceback.
        _render_terminal_exception("input", exc, write)
        return

    if started.status == "already_running":
        write(
            f"[error] request already running: {started.request_id}; "
            "message was not appended"
        )


async def _handle_modify_message(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    index = ui_state.get("pending_modify_index")
    ui_state["pending_modify_index"] = None
    ui_state["input_prefill"] = ""

    if index is None:
        await _handle_user_message(app, text, write, ui_state)
        return

    try:
        app.modify_message(index, text)
    except Exception as exc:  # pragma: no cover - defensive
        _render_terminal_exception("modify", exc, write)
        return

    write(f"[modify] updated message at index {index}")


def _build_key_bindings(
    app: TerminalApplication,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> KeyBindings:
    kb = KeyBindings()

    def _accept_completion(event: Any) -> None:
        """Accept the current or first completion without submitting.

        - If a completion menu is active and a completion is selected,
          apply that completion.
        - If no completion is selected, start completion and apply the
          first suggestion when available.
        - For file-context completions (identified by an ``@file:`` text
          and ``display_meta`` containing ``"file"``), log acceptance so
          that a later change can attach richer behavior.
        """

        buf = event.current_buffer
        state = buf.complete_state

        # Ensure we have a completion list. When none is active yet,
        # start completion and let the completer populate suggestions.
        if state is None or not getattr(state, "completions", None):
            buf.start_completion(select_first=True)
            state = buf.complete_state

        if state is None or not getattr(state, "completions", None):
            return

        # Prefer the currently selected completion when available;
        # otherwise fall back to the first suggestion.
        current = state.current_completion
        if current is not None:
            comp = current
        else:
            comps = list(state.completions)
            if not comps:
                return
            comp = comps[0]

        text = comp.text
        meta = getattr(comp, "display_meta_text", "") or ""

        # Apply the selected completion; fall back to inserting its text
        # directly if apply_completion is not available.
        apply = getattr(buf, "apply_completion", None)
        if callable(apply):
            apply(comp)
        else:  # pragma: no cover - defensive fallback
            buf.insert_text(comp.text)

        # After the completion is applied, give feature plugins a chance to
        # transform the accepted completion into a richer snippet. This is
        # used by FileContextFeature to turn "@file:path" into a multi-line
        # template snippet.
        completion_dict = getattr(comp, "_feature_completion", None)
        if not isinstance(completion_dict, dict):
            return

        try:
            core, base_config, session = app.require_session()
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            overrides_val = metadata.get("overrides")
            overrides: Dict[str, Any] = (
                overrides_val if isinstance(overrides_val, dict) else {}
            )
            config = resolve_request_config(base_config, overrides)
            buffer_text = buf.text
            snippet = core.apply_feature_completion(
                config, buffer_text, completion_dict
            )
        except Exception as exc:
            # Display a user-friendly error message while allowing
            # structlog-based logging inside the core/plugins to capture
            # details for debugging.
            if isinstance(text, str) and text.startswith("@file:") and "file" in meta:
                write(f"[file-context] {exc}")
            else:
                write(f"[completion] {exc}")
            return

        if not isinstance(snippet, str) or not snippet:
            return

        # Replace the just-applied completion text with the snippet. We
        # assume the completion was inserted contiguously before the
        # cursor.
        cursor_pos = buf.cursor_position
        if isinstance(text, str) and cursor_pos >= len(text):
            buf.cursor_position = cursor_pos
            buf.delete_before_cursor(len(text))
            buf.insert_text(snippet)

    # Ctrl-J inserts a newline without submitting the buffer.
    @kb.add("c-j")
    def _insert_newline(event: Any) -> None:  # type: ignore[no-redef]
        event.current_buffer.insert_text("\n")

    # Alt-Enter (Meta-Enter / Esc, Enter) also inserts a newline.
    @kb.add("escape", "enter")
    def _meta_enter_newline(event: Any) -> None:  # type: ignore[no-redef]
        event.current_buffer.insert_text("\n")

    # Esc alone: cancel the current completion menu (if any) without
    # modifying the buffer content.
    @kb.add("escape")
    def _escape_cancel_completion(event: Any) -> None:  # type: ignore[no-redef]
        buf = event.current_buffer
        state = buf.complete_state
        if state is None:
            return
        cancel = getattr(buf, "cancel_completion", None)
        if callable(cancel):
            cancel()
        else:  # pragma: no cover - defensive fallback
            buf.complete_state = None

    # Space: when a completion menu is open and a completion is already
    # selected, accept that completion and then insert a space. When no
    # completion menu is active, behave like a normal space key.
    @kb.add(" ")
    def _space_accept_or_insert(event: Any) -> None:  # type: ignore[no-redef]
        buf = event.current_buffer
        state = buf.complete_state
        if state is not None and getattr(state, "completions", None):
            _accept_completion(event)
        buf.insert_text(" ")

    # Tab: accept the selected completion (or the first one when none is
    # selected) without submitting the buffer.
    @kb.add("tab")
    def _tab_accept_completion(event: Any) -> None:  # type: ignore[no-redef]
        _accept_completion(event)

    # Enter: accept current completion (if any) or submit the buffer.
    # For file-context completions (identified by @file: prefix and
    # display metadata), we currently just log acceptance; later this
    # hook can apply a richer template.
    @kb.add("enter")
    def _enter_accept(event: Any) -> None:  # type: ignore[no-redef]
        _accept_completion(event)
        event.current_buffer.validate_and_handle()

    for sc in iter_shortcuts():
        key_parts = tuple(sc.keys.split()) if sc.keys else ()
        if not key_parts:
            continue

        @kb.add(*key_parts)
        def _(event: Any, _shortcut: Shortcut = sc) -> None:  # type: ignore[no-redef]
            buffer_text = event.current_buffer.text
            event.current_buffer.reset()
            result = _shortcut.handler(app, buffer_text, write, ui_state)
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)

            # For the exit shortcut (Ctrl-Q), also request that the
            # prompt_toolkit application exit the current prompt so
            # that the main loop can observe the updated ``ui_state``
            # and terminate cleanly.
            if _shortcut.keys == "c-q":
                try:
                    event.app.exit(result="")
                except Exception:  # pragma: no cover - defensive
                    pass

    return kb


def _set_terminal_title(title: str) -> None:
    """Best-effort update of the terminal window title.

    On POSIX terminals, use a standard ANSI escape sequence.
    On Windows, fall back to the ``title`` console command.
    Failures are silently ignored so that unsupported terminals
    are unaffected.
    """
    print(f"Setting terminal title to: {title}")
    try:
        # Windows consoles (cmd/PowerShell) don't reliably support the
        # xterm title escape, but they do support the "title" command.
        if sys.platform.startswith("win"):
            import os

            os.system(f"title {title}")
        else:
            sys.stdout.write(f"\x1b]0;{title}\x07")
            sys.stdout.flush()
    except Exception:
        # Never let title handling break startup.
        pass


async def _run_terminal(
    app: TerminalApplication,
    logger: Optional[Logger] = None,
) -> None:
    # Create an initial in-memory session so that the UI has a
    # session context from startup, but avoid persisting it until
    # the user sends the first message or otherwise modifies it.
    app.start_new_session(agent_id=app.available_agents()[0], persist=False)

    ui_state: Dict[str, Any] = {
        "running": True,
        "pending_agent_choices": None,
        "pending_session_choices": None,
        "pending_modify_index": None,
        "input_prefill": "",
        "renderer": None,
        "progress_state": IDLE_PROGRESS,
        # Live one-line-result tool rendering; selected at runtime via
        # /tool-output and seeded from application config.
        "tool_output_one_line": _initial_tool_output_one_line_state(app),
    }

    # Shared renderer context used for both streaming events and history
    # listing so that visuals stay consistent.
    renderer_ctx = TerminalRenderContext(
        app=app,
        footer_elements_supplier=lambda: app.message_footer_elements(),
        one_line_supplier=lambda: bool(ui_state.get("tool_output_one_line")),
    )
    ui_state["renderer"] = renderer_ctx

    def write(text: str) -> None:
        print(text, flush=True)
        if logger is not None:
            logger.info(text)

    completer = SlashCommandCompleter(lambda: app)
    prompt_session = PromptSession(
        multiline=False,
        completer=completer,
        complete_while_typing=True,
        bottom_toolbar=lambda: _status_bar_text(
            app,
            (
                ui_state.get("progress_state")
                if isinstance(ui_state.get("progress_state"), TerminalProgressState)
                else IDLE_PROGRESS
            ),
        ),
        erase_when_done=True,
    )
    key_bindings = _build_key_bindings(app, write, ui_state)

    async def prompt_action(request: Dict[str, Any]) -> str | None:
        label = str(request.get("prompt") or "Value")
        default = request.get("default")
        multiline = bool(request.get("multiline"))
        action_key_bindings = KeyBindings()

        @action_key_bindings.add("escape")
        def _cancel_action_prompt(event: Any) -> None:
            event.app.exit(result=None)

        if multiline:

            @action_key_bindings.add("c-d")
            def _submit_multiline_action_prompt(event: Any) -> None:
                event.app.exit(result=event.current_buffer.text)

        try:
            return await prompt_session.prompt_async(
                f"{label}: ",
                default="" if default is None else str(default),
                is_password=bool(request.get("secret")),
                multiline=multiline,
                key_bindings=action_key_bindings,
            )
        except (EOFError, KeyboardInterrupt):
            return None

    ui_state["action_prompt"] = prompt_action

    def invalidate_prompt() -> None:
        try:
            prompt_session.app.invalidate()
        except Exception:
            pass

    ui_state["invalidate"] = invalidate_prompt
    event_task = asyncio.create_task(
        _poll_events(app, write, ui_state, invalidate=invalidate_prompt)
    )

    for startup_line in _startup_help_lines(app):
        write(startup_line)

    with patch_stdout(True):
        _set_terminal_title("Crystal Lattice")
        while ui_state.get("running", True):
            try:
                default_text = ui_state.get("input_prefill") or ""
                ui_state["input_prefill"] = ""
                user_input = await prompt_session.prompt_async(
                    "> ",
                    key_bindings=key_bindings,
                    default=default_text,
                )
            except (EOFError, KeyboardInterrupt):  # pragma: no cover - console UX
                write("")
                break

            text = user_input.strip()
            if not text:
                continue

            if ui_state.get("pending_agent_choices") is not None:
                _handle_agent_selection(app, text, write, ui_state)
                continue

            if ui_state.get("pending_session_choices") is not None:
                _handle_session_selection(app, text, write, ui_state)
                continue

            if ui_state.get("pending_modify_index") is not None and not text.startswith(
                "/"
            ):
                await _handle_modify_message(app, text, write, ui_state)
                continue

            if text.startswith("/"):
                await _handle_slash_command(app, text, write, ui_state)
            else:
                await _handle_user_message(app, text, write, ui_state)

    ui_state["running"] = False
    event_task.cancel()
    try:
        await event_task
    except asyncio.CancelledError:  # pragma: no cover - shutdown path
        pass


def run_terminal(
    logger: Optional[Logger] = None,
    app_instance: Optional[TerminalApplication] = None,
) -> None:  # pragma: no cover - manual usage
    """Entry point for running the terminal client.

    If ``app_instance`` is provided, it is used; otherwise a default
    :class:`TerminalApplication` is constructed with the package's
    config and session root.
    """

    app = app_instance or TerminalApplication(
        config_path=_DEFAULT_CONFIG_PATH,
        session_root=_DEFAULT_SESSION_ROOT,
        env_overrides=_DEFAULT_RUNTIME_LAYOUT.env_overrides(),
    )

    asyncio.run(_run_terminal(app, logger=logger))
