"""SystemMessageFeature plugin.

Adds or templates a system message for OpenAI-like providers without mutating
the stored core message history.

Behavior overview
-----------------
- If the user has added at least one ``system`` message to the session, that
  message's content is treated as the template and takes precedence over any
  configured default.
- If there is no user ``system`` message, the feature uses the configured
  ``system_message`` template (if non-empty) and injects a synthetic
  provider-native ``system`` message at the beginning of the native message
  list.
- Templates may contain placeholders like ``{{NAME}}``. Variable definitions
  live under a single top-level ``system_message`` key.
- On every request, placeholders are resolved to concrete values, but the
  original core messages (session history) remain unchanged. Only the
  provider-native messages for that request are modified.

Config shape
------------
Top-level keys used by this feature:

- ``system_message_enabled``: bool (default True)
- ``system_message``: string or object

If ``system_message`` is a *string*, it is treated as the template verbatim
(no variables are defined by this feature).

If ``system_message`` is an *object*, it has the following shape::

    {
        "template": "You are a helper for {{PROJECT}}.",
        "runtime_code": "path/to/runtime_context.py",
        "variables": {
            "PROJECT": "AI Agent Platform",
            "FILES": {"files": ["AGENTS.md", "docs/prompt.txt"]},
            "NOTE": {"text": "inline text"},
            "CODED": {"code": "path/to/value_generator.py"},
            "DYNAMIC": {"inline_code": "f'Current working directory: {cwd}'"},
            "GIT_SECTION": {
                "files": ["git-section.md"],
                "condition": {"inline_code": "is_git_repo()"},
            },
        },
    }

Variable values:

- string
    Used directly as the replacement value.
- object with one primary source key and optional ``condition``:
    - ``files``: list[str]
        Paths to read and concatenate into a single string. Paths may be
        absolute or relative; relative paths are resolved against the current
        working directory.
    - ``text``: str
        Inline text value (equivalent to providing the string directly).
    - ``code``: str
        Path to a Python file. The file is executed in a fresh namespace using
        ``runpy.run_path`` and the feature looks for either a
        ``SYSTEM_MESSAGE_VALUE`` variable or a callable ``get_value``
        function.
    - ``inline_code``: str
        Inline Python. If it compiles as a single expression, the expression's
        result is used directly. Otherwise the snippet is executed as a block
        and the feature reads ``VALUE`` from the resulting namespace.
    - ``condition``: object with ``code`` or ``inline_code``
        If the condition evaluates falsey, the variable resolves to ``""`` and
        the main value is not read or executed.

Runtime code
------------
If ``system_message.runtime_code`` is configured, the referenced Python file is
executed once per request and all exported non-underscore globals from that
file become the runtime namespace for file-backed ``code``, ``inline_code``,
and their condition variants.

The runtime namespace always includes ``CONFIG`` with the effective request
config. When UI schema is queried through :meth:`get_ui_elements`, the runtime
namespace also includes ``TAGS`` and ``MODELS`` and may optionally export a
zero-argument ``get_ui_elements()`` helper.

This keeps the feature generic while letting config authors define convenience
helpers such as ``cwd`` or ``is_git_repo()`` entirely in configuration.
"""

from __future__ import annotations

import os
import runpy
import json
from typing import Any, Dict, List, Optional, Tuple

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
    version: str = "0.5.0"
    _COMPILED_CONTENT_KEY = "compiled_content"
    _COMPILED_LOGGED_KEY = "system_message_compiled_logged"

    def __init__(self) -> None:  # pragma: no cover - trivial initializer
        # Per-request configuration snapshot extracted from the flat
        # config in ``init``. This keeps ``to_native_messages`` simple
        # while still letting the application change config between
        # requests.
        self._config: Dict[str, Any] = {
            "enabled": True,
            "template": "",
            "runtime_code": "",
            # variables: Dict[str, Dict[str, Any]] where each value is a
            # normalized spec of the form:
            #   {"kind": "text", "value": str}
            #   {"kind": "files", "files": List[str]}
            #   {"kind": "code", "path": str}
            #   {"kind": "inline_code", "value": str}
            # Specs may also carry an optional normalized ``condition``.
            "variables": {},
        }
        self._effective_config: Dict[str, Any] = {}

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
                    "or an object with 'template', optional 'runtime_code', "
                    "and 'variables'."
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
                            "runtime_code": {
                                "type": "string",
                                "description": (
                                    "Optional Python file executed once per "
                                    "request to provide runtime globals for "
                                    "inline_code, code, and conditions."
                                ),
                            },
                            "variables": {
                                "type": "object",
                                "description": (
                                    "Mapping from placeholder name (without "
                                    "braces) to values or value descriptors. "
                                    "Values may be strings or objects with "
                                    "one of: 'files', 'text', 'code', "
                                    "'inline_code'. Variable objects may also "
                                    "define 'runtime_code' to extend the "
                                    "runtime namespace just for that variable, "
                                    "and may also include a 'condition' with "
                                    "'code' or "
                                    "'inline_code'."
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
                                                "inline_code": {"type": "string"},
                                                "runtime_code": {
                                                    "type": "string"
                                                },
                                                "condition": {
                                                    "type": "object",
                                                    "properties": {
                                                        "code": {"type": "string"},
                                                        "inline_code": {
                                                            "type": "string"
                                                        },
                                                    },
                                                },
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

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        plugin_cfg = self._extract_plugin_config(config or {})
        runtime_paths = self._ui_runtime_paths(plugin_cfg)
        if not runtime_paths:
            return []

        base_context = self._build_base_runtime_context(
            config=config,
            tags=tags,
            models=models,
        )

        elements: List[Dict[str, Any]] = []
        seen_entries: set[str] = set()
        for runtime_path in runtime_paths:
            runtime_context = self._load_runtime_context(
                runtime_path,
                base_context=base_context,
            )
            getter = runtime_context.get("get_ui_elements")
            if not callable(getter):
                continue

            try:
                raw = getter()
            except Exception:
                continue

            if not isinstance(raw, list):
                continue

            for item in raw:
                if not isinstance(item, dict):
                    continue
                try:
                    fingerprint = json.dumps(item, sort_keys=True, default=str)
                except Exception:
                    fingerprint = ""
                if fingerprint and fingerprint in seen_entries:
                    continue
                if fingerprint:
                    seen_entries.add(fingerprint)
                elements.append(item)

        return elements

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
    def _normalize_condition(raw: Any) -> Dict[str, Any] | None:
        """Normalize a condition spec into ``code`` or ``inline_code`` form."""

        if not isinstance(raw, dict):
            return None

        if "code" in raw:
            code_path = raw.get("code")
            if isinstance(code_path, str) and code_path:
                return {"kind": "code", "path": code_path}

        if "inline_code" in raw:
            inline_code = raw.get("inline_code")
            if isinstance(inline_code, str):
                return {"kind": "inline_code", "value": inline_code}

        return None

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
            condition = SystemMessageFeature._normalize_condition(raw.get("condition"))
            variable_runtime = raw.get("runtime_code")
            runtime_code = (
                str(variable_runtime)
                if isinstance(variable_runtime, str) and variable_runtime
                else None
            )
            if "files" in raw and isinstance(raw.get("files"), (list, tuple)):
                files = [str(p) for p in raw["files"] if isinstance(p, str)]
                if files:
                    spec = {"kind": "files", "files": files}
                    if runtime_code is not None:
                        spec["runtime_code"] = runtime_code
                    if condition is not None:
                        spec["condition"] = condition
                    return spec
            if "text" in raw:
                spec = {"kind": "text", "value": str(raw.get("text", ""))}
                if runtime_code is not None:
                    spec["runtime_code"] = runtime_code
                if condition is not None:
                    spec["condition"] = condition
                return spec
            if "code" in raw:
                code_path = raw.get("code")
                if isinstance(code_path, str) and code_path:
                    spec = {"kind": "code", "path": code_path}
                    if runtime_code is not None:
                        spec["runtime_code"] = runtime_code
                    if condition is not None:
                        spec["condition"] = condition
                    return spec
            if "inline_code" in raw:
                inline_code = raw.get("inline_code")
                if isinstance(inline_code, str):
                    spec = {"kind": "inline_code", "value": inline_code}
                    if runtime_code is not None:
                        spec["runtime_code"] = runtime_code
                    if condition is not None:
                        spec["condition"] = condition
                    return spec

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
        runtime_code = ""
        variables: Dict[str, Dict[str, Any]] = {}

        if isinstance(raw_sm, str):
            template = raw_sm
        elif isinstance(raw_sm, dict):
            template = str(raw_sm.get("template", "") or "")
            runtime_code = str(raw_sm.get("runtime_code", "") or "")
            raw_vars = raw_sm.get("variables") or {}
            if isinstance(raw_vars, dict):
                for name, value in raw_vars.items():
                    spec = SystemMessageFeature._normalize_variable_value(value)
                    if spec is not None:
                        variables[str(name)] = spec

        return {
            "enabled": enabled,
            "template": template,
            "runtime_code": runtime_code,
            "variables": variables,
        }

    @staticmethod
    def _ui_runtime_paths(plugin_cfg: Dict[str, Any]) -> List[str]:
        """Return top-level and variable-level runtime helpers for UI schema."""

        paths: List[str] = []

        runtime_path = plugin_cfg.get("runtime_code")
        if isinstance(runtime_path, str) and runtime_path:
            paths.append(runtime_path)

        for spec in (plugin_cfg.get("variables") or {}).values():
            if not isinstance(spec, dict):
                continue
            variable_runtime = spec.get("runtime_code")
            if not isinstance(variable_runtime, str) or not variable_runtime:
                continue
            if variable_runtime not in paths:
                paths.append(variable_runtime)

        return paths

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
    def _export_runtime_context(namespace: Dict[str, Any]) -> Dict[str, Any]:
        """Return exported names from a runtime namespace.

        All non-underscore globals are exported. This keeps the contract simple
        and lets config authors decide which imports, helpers, or constants are
        part of the runtime context.
        """

        exported: Dict[str, Any] = {}
        for name, value in namespace.items():
            if name == "__builtins__" or name.startswith("_"):
                continue
            exported[name] = value
        return exported

    @staticmethod
    def _build_base_runtime_context(
        config: Dict[str, Any] | None = None,
        tags: List[str] | None = None,
        models: List[Dict[str, Any]] | None = None,
        previous_metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Build the base runtime namespace exposed to helper code."""

        return {
            "CONFIG": dict(config or {}),
            "TAGS": list(tags or []),
            "MODELS": list(models or []),
            "PREVIOUS_METADATA": dict(previous_metadata or {}),
        }

    @classmethod
    def _load_runtime_context(
        cls,
        path: str | None,
        base_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Load optional request-scoped runtime globals from ``runtime_code``."""

        if not isinstance(path, str) or not path:
            return dict(base_context or {})

        try:
            namespace = runpy.run_path(
                os.path.expanduser(path),
                init_globals=cls._build_exec_globals(base_context),
            )
        except Exception:
            return dict(base_context or {})

        return cls._export_runtime_context(namespace)

    @classmethod
    def _merge_runtime_contexts(
        cls,
        base_context: Dict[str, Any] | None,
        runtime_paths: List[str] | None,
    ) -> Dict[str, Any]:
        """Load runtime helpers in sequence, letting later helpers override."""

        merged = dict(base_context or {})
        for path in runtime_paths or []:
            if not isinstance(path, str) or not path:
                continue
            merged = cls._load_runtime_context(path, base_context=merged)
        return merged

    @staticmethod
    def _build_exec_globals(
        runtime_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Build globals for inline execution from optional runtime context."""

        return {"__builtins__": __builtins__, **dict(runtime_context or {})}

    @classmethod
    def _extract_code_result(cls, namespace: Dict[str, Any]) -> Any:
        """Extract the result value from a file-backed code namespace.

        The file is executed with :func:`runpy.run_path`. The resulting
        globals are inspected for either:

        - ``SYSTEM_MESSAGE_VALUE``: used directly if present, or
        - ``get_value``: a callable returning the raw value.
        """

        if "SYSTEM_MESSAGE_VALUE" in namespace:
            return namespace.get("SYSTEM_MESSAGE_VALUE")

        getter = namespace.get("get_value")
        if callable(getter):
            try:
                return getter()
            except Exception:
                return None

        return None

    @classmethod
    def _execute_code_raw(
        cls,
        path: str,
        runtime_context: Dict[str, Any] | None = None,
    ) -> Any:
        """Execute a Python file and return its raw extracted result."""

        try:
            namespace = runpy.run_path(
                os.path.expanduser(path),
                init_globals=dict(runtime_context or {}),
            )
        except Exception:
            return None

        return cls._extract_code_result(namespace)

    @classmethod
    def _execute_code(
        cls,
        path: str,
        runtime_context: Dict[str, Any] | None = None,
    ) -> str:
        """Execute a Python file and extract a string value."""

        value = cls._execute_code_raw(path, runtime_context=runtime_context)
        if value is None:
            return ""
        return str(value)

    @classmethod
    def _execute_code_with_metadata(
        cls,
        path: str,
        runtime_context: Dict[str, Any] | None = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Execute a Python file and extract both value and metadata updates.

        Code files can set METADATA_UPDATES dict to persist values across
        requests via the system message _metadata.

        Returns:
            Tuple of (string value, metadata updates dict)
        """
        try:
            namespace = runpy.run_path(
                os.path.expanduser(path),
                init_globals=cls._build_exec_globals(runtime_context),
            )
        except Exception:
            return "", {}

        value = cls._extract_code_result(namespace)
        metadata_updates = namespace.get("METADATA_UPDATES")
        return (
            str(value) if value is not None else "",
            dict(metadata_updates) if isinstance(metadata_updates, dict) else {},
        )

    @classmethod
    def _execute_inline_code_raw(
        cls,
        source: str,
        runtime_context: Dict[str, Any] | None = None,
    ) -> Any:
        """Execute inline Python as an expression or block and return the raw value."""

        if not isinstance(source, str):
            return None

        try:
            compiled = compile(source, "<system_message:inline_code>", "eval")
        except SyntaxError:
            try:
                namespace = {
                    **cls._build_exec_globals(runtime_context),
                    "VALUE": None,
                }
                exec(compile(source, "<system_message:inline_code>", "exec"), namespace)
            except Exception:
                return None
            return namespace.get("VALUE")

        try:
            namespace = cls._build_exec_globals(runtime_context)
            return eval(compiled, namespace)
        except Exception:
            return None

    @classmethod
    def _execute_inline_code(
        cls,
        source: str,
        runtime_context: Dict[str, Any] | None = None,
    ) -> str:
        """Execute inline Python and coerce the result to string."""

        value = cls._execute_inline_code_raw(source, runtime_context=runtime_context)
        if value is None:
            return ""
        return str(value)

    @classmethod
    def _stamp_compiled_content_once(
        cls,
        native_messages: List[Dict[str, Any]],
        system_index: int,
        rendered: str,
    ) -> List[Dict[str, Any]]:
        """Persist the first compiled prompt snapshot in native metadata.

        The retained native ``content`` stays templated so users can edit the
        template later. Only the native ``_metadata`` gains the compiled text.
        """

        try:
            original = native_messages[system_index]
        except Exception:
            return native_messages
        if not isinstance(original, dict):
            return native_messages

        raw_metadata = original.get("_metadata") or {}
        metadata = dict(raw_metadata) if isinstance(raw_metadata, dict) else {}
        if metadata.get(cls._COMPILED_LOGGED_KEY):
            return native_messages

        metadata[cls._COMPILED_CONTENT_KEY] = rendered
        metadata[cls._COMPILED_LOGGED_KEY] = True

        print(f"[system_message compiled]\n{rendered}")

        stamped_messages = list(native_messages)
        stamped_messages[system_index] = {**original, "_metadata": metadata}
        return stamped_messages

    @classmethod
    def _evaluate_condition(
        cls,
        spec: Dict[str, Any] | None,
        runtime_context: Dict[str, Any] | None = None,
    ) -> bool:
        """Evaluate an optional condition spec for a variable."""

        if spec is None:
            return True

        kind = spec.get("kind")
        if kind == "code":
            code_path = spec.get("path")
            if isinstance(code_path, str) and code_path:
                return bool(
                    cls._execute_code_raw(
                        code_path,
                        runtime_context=runtime_context,
                    )
                )
            return False
        if kind == "inline_code":
            return bool(
                cls._execute_inline_code_raw(
                    str(spec.get("value", "")),
                    runtime_context=runtime_context,
                )
            )
        return False

    @classmethod
    def _resolve_variables(
        cls,
        variable_specs: Dict[str, Dict[str, Any]],
        runtime_context: Dict[str, Any] | None = None,
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Resolve normalized variable specs into concrete string values.

        Returns:
            Tuple of (resolved variables dict, accumulated metadata updates dict)
        """

        resolved: Dict[str, str] = {}
        metadata_updates: Dict[str, Any] = {}
        for name, spec in (variable_specs or {}).items():
            variable_runtime = spec.get("runtime_code")
            variable_context = dict(runtime_context or {})
            if isinstance(variable_runtime, str) and variable_runtime:
                variable_context = cls._merge_runtime_contexts(
                    variable_context,
                    [variable_runtime],
                )

            if not cls._evaluate_condition(
                spec.get("condition"),
                runtime_context=variable_context,
            ):
                resolved[name] = ""
                continue

            kind = spec.get("kind")
            if kind == "text":
                value = spec.get("value", "")
                resolved[name] = "" if value is None else str(value)
            elif kind == "files":
                paths = spec.get("files") or []
                if isinstance(paths, list):
                    resolved[name] = cls._read_files(paths)
            elif kind == "code":
                code_path = spec.get("path")
                if isinstance(code_path, str) and code_path:
                    value, updates = cls._execute_code_with_metadata(
                        code_path,
                        runtime_context=variable_context,
                    )
                    resolved[name] = value
                    metadata_updates.update(updates)
                else:
                    resolved[name] = ""
            elif kind == "inline_code":
                resolved[name] = cls._execute_inline_code(
                    str(spec.get("value", "")),
                    runtime_context=variable_context,
                )
            else:
                resolved[name] = ""
        return resolved, metadata_updates

    # ---- Lifecycle ----
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize plugin from flat config and shared state.

        The flat config is also merged into ``state['config']`` so other
        plugins see the same view. A per-request snapshot relevant to
        this feature is stored on the instance for use by
        :meth:`to_native_messages`.
        """

        self._config = self._extract_plugin_config(config)
        self._effective_config = dict(config)
        return {**state, "config": {**state.get("config", {}), **config}}

    # ---- Stateless transforms (native side) ----
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Leave provider-native messages unchanged.

        Permanent template-level system messages are now inserted during
        :meth:`initialize_request` so that structural behavior and
        per-request rendering share a single implementation.
        """

        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Do not alter core messages on the way back; the history should
        # remain as the application created it.
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Insert permanent template system (when missing) and render per-request.

        This method mirrors the previous behavior that lived partly in
        :meth:`to_native_messages` and partly in
        :meth:`initialize_request` by:

        - Ensuring that a single template-level ``system`` message exists
          in the provider-native history when the feature is enabled and
          a template is configured but no user ``system`` message is
          present. This permanent message is inserted into the returned
          ``native_messages`` with its *template* content.
        - Computing concrete variable values and rendering the chosen
          system message template into ``state["request"]["messages"]``
          for this request only. The stored native history keeps the
          template content.
        """

        cfg = self._config
        if not cfg.get("enabled", True):
            return native_messages, state

        if not isinstance(native_messages, list):
            return native_messages, state

        working_native = native_messages

        is_responses_items = False
        for m in native_messages:
            if isinstance(m, dict):
                is_responses_items = isinstance(m.get("type"), str) and bool(
                    m.get("type")
                )
                break
        if not working_native:
            req = state.get("request") if isinstance(state, dict) else None
            url = req.get("url") if isinstance(req, dict) else None
            if isinstance(url, str) and "/responses" in url:
                is_responses_items = True

        # Structural step: ensure a permanent template-level system
        # message exists in the provider-native history when no user
        # system message is present and a template is configured.
        if is_responses_items:
            has_system = any(
                isinstance(m, dict)
                and m.get("type") == "message"
                and m.get("role") == "system"
                for m in native_messages
            )
        else:
            has_system = any(
                isinstance(m, dict) and m.get("role") == "system" for m in native_messages
            )
        if not has_system:
            template = cfg.get("template", "") or ""
            if template:
                if is_responses_items:
                    synthetic = {
                        "type": "message",
                        "role": "system",
                        "content": [{"type": "input_text", "text": template}],
                    }
                else:
                    synthetic = {"role": "system", "content": template}
                working_native = [synthetic, *native_messages]

        if not working_native:
            return working_native, state

        # Determine system message index first to access previous metadata
        system_index: int | None = None
        for idx in range(len(working_native) - 1, -1, -1):
            msg = working_native[idx]
            if not isinstance(msg, dict):
                continue
            if is_responses_items:
                if msg.get("type") == "message" and msg.get("role") == "system":
                    system_index = idx
                    break
            else:
                if msg.get("role") == "system":
                    system_index = idx
                    break

        # Extract previous metadata from existing system message for caching
        previous_metadata: Dict[str, Any] = {}
        if system_index is not None:
            sys_msg = working_native[system_index]
            if isinstance(sys_msg, dict):
                raw_metadata = sys_msg.get("_metadata")
                if isinstance(raw_metadata, dict):
                    previous_metadata = raw_metadata

        # Resolve request-scoped runtime globals once, then use them for all
        # dynamic value and condition evaluation in this request.
        runtime_context = self._load_runtime_context(
            cfg.get("runtime_code"),
            base_context=self._build_base_runtime_context(
                config=self._effective_config,
                previous_metadata=previous_metadata,
            ),
        )
        variables, metadata_updates = self._resolve_variables(
            cfg.get("variables") or {},
            runtime_context=runtime_context,
        )

        # Choose the system template to render. Prefer the *last* system
        # message in the native history so that user-supplied system
        # messages take precedence over any earlier, config-derived one.
        if system_index is not None:
            sys_msg = working_native[system_index]
            if is_responses_items:
                content = sys_msg.get("content") if isinstance(sys_msg, dict) else None
                text_parts: List[str] = []
                if isinstance(content, list):
                    for part in content:
                        if not isinstance(part, dict):
                            continue
                        if part.get("type") != "input_text":
                            continue
                        text = part.get("text")
                        if isinstance(text, str) and text:
                            text_parts.append(text)
                base_template = "\n".join(text_parts)
            else:
                base_template = str(sys_msg.get("content", "") or "")
        else:
            base_template = cfg.get("template", "") or ""

        if not base_template:
            return working_native, state

        rendered = self._render_template(base_template, variables)
        if system_index is not None:
            working_native = self._stamp_compiled_content_once(
                working_native,
                system_index,
                rendered,
            )
            # Apply metadata updates from code execution to system message
            if metadata_updates:
                sys_msg = working_native[system_index]
                if isinstance(sys_msg, dict):
                    existing_metadata = sys_msg.get("_metadata") or {}
                    new_metadata = {**existing_metadata, **metadata_updates}
                    working_native = list(working_native)
                    working_native[system_index] = {**sys_msg, "_metadata": new_metadata}

        # Build override messages: same as native history, but with the
        # chosen system message rendered at the selected index.
        override_messages = list(working_native)
        if system_index is not None:
            original = dict(override_messages[system_index])
            if is_responses_items:
                content = original.get("content")
                parts = list(content) if isinstance(content, list) else []

                replaced = False
                new_parts: List[Dict[str, Any]] = []
                for part in parts:
                    if not isinstance(part, dict) or replaced:
                        new_parts.append(part)
                        continue
                    if part.get("type") != "input_text":
                        new_parts.append(part)
                        continue
                    new_parts.append({**part, "text": rendered})
                    replaced = True

                if not replaced:
                    new_parts = [{"type": "input_text", "text": rendered}, *new_parts]

                override_messages[system_index] = {**original, "content": new_parts}
            else:
                override_messages[system_index] = {**original, "content": rendered}
        else:
            if is_responses_items:
                override_messages = [
                    {
                        "type": "message",
                        "role": "system",
                        "content": [{"type": "input_text", "text": rendered}],
                    },
                    *override_messages,
                ]
            else:
                override_messages = [
                    {"role": "system", "content": rendered},
                    *override_messages,
                ]

        request = state.get("request") or {}
        new_request = {**request, "messages": override_messages}
        new_state = {**state, "request": new_request}
        return working_native, new_state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # System prompting only affects inputs; responses are unchanged.
        return final_messages, native_messages, state
