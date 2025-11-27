"""
SystemMessageFeature plugin.

Adds or templates a system message for OpenAI-like providers without
mutating the stored core message history.

Behavior overview
-----------------
- If the user has added at least one ``system`` message to the session,
  that message's content is treated as the template and takes
  precedence over any configured default.
- If there is no user ``system`` message, the feature uses the
  configured ``system_message`` template (if non-empty) and injects a
  synthetic provider-native ``system`` message at the beginning of the
  native message list.
- Templates may contain placeholders like ``{{NAME}}``. Variable
  definitions live under a single top-level ``system_message`` key.
- On every request, placeholders are resolved to concrete values, but
  the original core messages (session history) remain unchanged. Only
  the provider-native messages for that request are modified.

Config shape
------------
Top-level keys used by this feature:

- ``system_message_enabled``: bool (default True)
- ``system_message``: string or object

If ``system_message`` is a *string*, it is treated as the template
verbatim (no variables are defined by this feature).

If ``system_message`` is an *object*, it has the following shape::

    {
        "template": "You are a helper for {{PROJECT}}.",
        "variables": {
            "PROJECT": "AI Agent Platform",
            "FILES": {"files": ["AGENTS.md", "docs/prompt.txt"]},
            "NOTE": {"text": "inline text"},
            "CODED": {"code": "path/to/value_generator.py"},
        },
    }

Variable values:

- string
    Used directly as the replacement value.
- object with one of the following keys (mutually exclusive):
    - ``files``: list[str]
        Paths to read and concatenate into a single string. Paths may be
        absolute or relative; relative paths are resolved against the
        current working directory.
    - ``text``: str
        Inline text value (equivalent to providing the string directly).
    - ``code``: str
        Path to a Python file. The file is executed in a fresh namespace
        using ``runpy.run_path`` and the feature looks for either a
        ``SYSTEM_MESSAGE_VALUE`` variable or a callable ``get_value``
        function. If found and non-None, its value (or return value) is
        converted to ``str`` and used as the variable value.
"""

from __future__ import annotations

import os
import runpy
from typing import Any, Dict, List, Tuple

from agent_core.types import FeaturePlugin


class SystemMessageFeature(FeaturePlugin):
    """Feature plugin that templates a system message per request.

    This plugin operates entirely on provider-native messages in
    :meth:`to_native_messages` and never mutates the core session
    history. It computes variable values from the flat config for each
    request and performs a straightforward ``"{{NAME}}" -> value``
    substitution.
    """

    name: str = "system_message"
    version: str = "0.2.0"

    def __init__(self) -> None:  # pragma: no cover - trivial initializer
        # Per-request configuration snapshot extracted from the flat
        # config in ``init``. This keeps ``to_native_messages`` simple
        # while still letting the application change config between
        # requests.
        self._config: Dict[str, Any] = {
            "enabled": True,
            "template": "",
            # variables: Dict[str, Dict[str, Any]] where each value is a
            # normalized spec of the form:
            #   {"kind": "text", "value": str}
            #   {"kind": "files", "files": List[str]}
            #   {"kind": "code", "path": str}
            "variables": {},
        }

    # ---- Config / UI ----
    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON-schema-like description of this feature's config.

        The schema is intentionally permissive; it documents the
        supported structure but does not attempt to encode all typing
        rules exactly.
        """

        return {
            "system_message_enabled": {
                "type": "boolean",
                "default": True,
                "description": "Enable or disable the system message feature.",
            },
            "system_message": {
                "description": (
                    "System message configuration. Either a string template "
                    "or an object with 'template' and 'variables'."
                ),
                "oneOf": [
                    {"type": "string"},
                    {
                        "type": "object",
                        "properties": {
                            "template": {
                                "type": "string",
                                "description": (
                                    "System message template when no user "
                                    "system message is present. May contain "
                                    "{{VAR}} placeholders."
                                ),
                            },
                            "variables": {
                                "type": "object",
                                "description": (
                                    "Mapping from placeholder name (without "
                                    "braces) to values or value descriptors. "
                                    "Values may be strings or objects with "
                                    "one of: 'files', 'text', 'code'."
                                ),
                                "additionalProperties": {
                                    "oneOf": [
                                        {"type": "string"},
                                        {
                                            "type": "object",
                                            "properties": {
                                                "files": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                },
                                                "text": {"type": "string"},
                                                "code": {"type": "string"},
                                            },
                                        },
                                    ]
                                },
                            },
                        },
                    },
                ],
            },
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        # UI wiring is application-specific; keep this feature config-only.
        return []

    # Uses adapter default get_models (no-op on models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify this feature for dependency resolution."""
        return ["feature:system_message"]

    def required_tags(self) -> List[str]:
        """This feature does not currently require specific tags."""
        return []

    # ---- Internal helpers (pure-ish) ----
    @staticmethod
    def _normalize_variable_value(raw: Any) -> Dict[str, Any] | None:
        """Normalize a single variable value description.

        Returns a dict with a ``kind`` key or ``None`` if the value
        cannot be meaningfully normalized.
        """

        if raw is None:
            return None

        if isinstance(raw, str):
            return {"kind": "text", "value": raw}

        if isinstance(raw, dict):
            if "files" in raw and isinstance(raw.get("files"), (list, tuple)):
                files = [str(p) for p in raw["files"] if isinstance(p, str)]
                if files:
                    return {"kind": "files", "files": files}
            if "text" in raw:
                return {"kind": "text", "value": str(raw.get("text", ""))}
            if "code" in raw:
                code_path = raw.get("code")
                if isinstance(code_path, str) and code_path:
                    return {"kind": "code", "path": code_path}

        # Fallback: coerce to text.
        return {"kind": "text", "value": str(raw)}

    @staticmethod
    def _extract_plugin_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize the flat config into an internal representation.

        This method is deterministic and side-effect free, making it
        straightforward to unit test.
        """

        enabled = bool(config.get("system_message_enabled", True))

        raw_sm = config.get("system_message")
        template = ""
        variables: Dict[str, Dict[str, Any]] = {}

        if isinstance(raw_sm, str):
            template = raw_sm
        elif isinstance(raw_sm, dict):
            template = str(raw_sm.get("template", "") or "")
            raw_vars = raw_sm.get("variables") or {}
            if isinstance(raw_vars, dict):
                for name, value in raw_vars.items():
                    spec = SystemMessageFeature._normalize_variable_value(value)
                    if spec is not None:
                        variables[str(name)] = spec

        return {
            "enabled": enabled,
            "template": template,
            "variables": variables,
        }

    @staticmethod
    def _render_template(template: str, variables: Dict[str, str]) -> str:
        """Render ``template`` by replacing ``{{NAME}}`` placeholders.

        This is intentionally simple and one-way: it performs a sequence
        of ``str.replace`` calls without attempting to parse nested or
        complex expressions.
        """

        rendered = template
        for name, value in variables.items():
            placeholder = "{{" + name + "}}"
            rendered = rendered.replace(placeholder, value)
        return rendered

    @staticmethod
    def _read_files(paths: List[str]) -> str:
        """Read and concatenate multiple files.

        Paths may be absolute or relative. Relative paths are resolved
        against the current working directory. Any file that cannot be
        read is silently skipped.
        """

        contents: List[str] = []
        for path in paths:
            try:
                with open(os.path.expanduser(path), "r", encoding="utf-8") as f:
                    contents.append(f.read())
            except Exception:
                # On any I/O error, skip the file; callers can still use
                # other variables or provide direct text.
                continue
        return "\n\n".join(contents)

    @staticmethod
    def _execute_code(path: str) -> str:
        """Execute a Python file and extract a string value.

        The file is executed with :func:`runpy.run_path`. The resulting
        globals are inspected for either:

        - ``SYSTEM_MESSAGE_VALUE``: used directly if present, or
        - ``get_value``: a callable returning the string value.

        Any errors result in an empty string.
        """

        try:
            namespace = runpy.run_path(os.path.expanduser(path))
        except Exception:
            return ""

        if "SYSTEM_MESSAGE_VALUE" in namespace:
            value = namespace.get("SYSTEM_MESSAGE_VALUE")
        else:
            getter = namespace.get("get_value")
            if callable(getter):
                try:
                    value = getter()
                except Exception:
                    value = None
            else:
                value = None

        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _resolve_variables(variable_specs: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Resolve normalized variable specs into concrete string values."""

        resolved: Dict[str, str] = {}
        for name, spec in (variable_specs or {}).items():
            kind = spec.get("kind")
            if kind == "text":
                value = spec.get("value")
                if value is not None:
                    resolved[name] = str(value)
            elif kind == "files":
                paths = spec.get("files") or []
                if isinstance(paths, list):
                    value = SystemMessageFeature._read_files(paths)
                    if value:
                        resolved[name] = value
            elif kind == "code":
                code_path = spec.get("path")
                if isinstance(code_path, str) and code_path:
                    value = SystemMessageFeature._execute_code(code_path)
                    if value:
                        resolved[name] = value
        return resolved

    # ---- Lifecycle ----
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize plugin from flat config and shared state.

        The flat config is also merged into ``state['config']`` so other
        plugins see the same view. A per-request snapshot relevant to
        this feature is stored on the instance for use by
        :meth:`to_native_messages`.
        """

        self._config = self._extract_plugin_config(config)
        return {**state, "config": {**state.get("config", {}), **config}}

    # ---- Stateless transforms (native side) ----
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        cfg = self._config
        if not cfg.get("enabled", True):
            return native_messages

        # Structural step only: ensure that a permanent template-level
        # system message exists in the provider-native history. Variable
        # rendering happens later in initialize_request.
        has_system = any(m.get("role") == "system" for m in native_messages)
        if has_system:
            return native_messages

        template = cfg.get("template", "") or ""
        if not template:
            # No configured template and no user system -> leave history
            # unchanged.
            return native_messages

        synthetic = {"role": "system", "content": template}
        return [synthetic, *native_messages]

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Do not alter core messages on the way back; the history should
        # remain as the application created it.
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare per-request rendered system message into request state.

        This method computes concrete variable values and renders the
        chosen system message template (user-provided system has
        precedence). The rendered history is stored under
        ``state["request"]["messages"]`` and is meant to be consumed by
        providers instead of the raw ``native_messages`` when present.
        The original ``native_messages`` remain unmodified so that the
        stored history retains templates.
        """

        cfg = self._config
        if not cfg.get("enabled", True):
            return state

        if not isinstance(native_messages, list) or not native_messages:
            return state

        # Resolve variables for this request.
        variables = self._resolve_variables(cfg.get("variables") or {})

        # Choose the system template to render. Prefer the *last* system
        # message in the native history so that user-supplied system
        # messages take precedence over any earlier, config-derived one.
        system_index: int | None = None
        for idx in range(len(native_messages) - 1, -1, -1):
            if native_messages[idx].get("role") == "system":
                system_index = idx
                break

        if system_index is not None:
            base_template = str(native_messages[system_index].get("content", "") or "")
        else:
            base_template = cfg.get("template", "") or ""

        if not base_template:
            return state

        rendered = self._render_template(base_template, variables)

        # Build override messages: same as native history, but with the
        # chosen system message rendered. If no system existed, prepend a
        # synthetic rendered system just for this request.
        override_messages = list(native_messages)
        if system_index is not None:
            original = dict(override_messages[system_index])
            override_messages[system_index] = {**original, "content": rendered}
        else:
            override_messages = [{"role": "system", "content": rendered}, *override_messages]

        request = state.get("request") or {}
        new_request = {**request, "messages": override_messages}
        return {**state, "request": new_request}

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # System prompting only affects inputs; responses are unchanged.
        return final_messages, native_messages, state
