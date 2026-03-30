"""RequestOptionsFeature plugin.

Merges arbitrary request options from config into the OpenAI-compatible
provider request payload during initialize_request.

Config keys (flat, optional):
- request_options: dict[Any, Any]  # merged into state["request"]["payload"]
- request_options_ui: dict[str, Any]  # defines UI controls for request_options

When request_options_ui is defined, the plugin generates:
- Flat config keys like ``request_options__temperature`` for UI/session overrides
- UI elements with flat keys plus nested source metadata
- During init(), flat keys are extracted, inflated into nested objects, and
  deep-merged back into ``request_options``

This keeps the feature simple and provider-agnostic while working
naturally with the OpenAI-compatible provider (which reads
state["request"]["payload"] when building the JSON body).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import FeaturePlugin


class RequestOptionsFeature(FeaturePlugin):
    """Feature plugin that injects request options into provider payload.

    The application supplies a flat config containing ``request_options``:

    .. code-block:: python

        config = {
            "model": "gpt-4o",
            "base_url": "https://api.openai.com/v1",
            "request_options": {"temperature": 0.3, "max_tokens": 512},
        }

    For dynamic UI controls, add ``request_options_ui``:

    .. code-block:: python

        config = {
            "request_options": {"temperature": 0.7},
            "request_options_ui": {
                "temperature": "number",
                "max_tokens": ["512", "1024", "2048"],
            }
        }

    This generates flat config keys like ``request_options__temperature``
    and UI elements with those keys. Nested UI config is also supported,
    for example ``{"thinking": {"type": ["disabled", "enabled"]}}``,
    which becomes the flat key ``request_options__thinking__type``.

    Generated UI elements also include:

    - ``config_path``: the nested source path in the effective config, such as
      ``request_options.thinking.type``
    - ``default``: the current nested default value from ``request_options``
      when one exists in config

    During ``init()``, flat keys are extracted, inflated into nested objects,
    and deep-merged into ``request_options``.

    During :meth:`initialize_request`, the plugin merges these options into
    ``state["request"]["payload"]`` so the provider call can include any
    additional OpenAI-style parameters. Keys from ``request_options``
    override existing payload keys.
    """

    name: str = "request_options"
    version: str = "0.3.0"
    priority: int = 200  # Run after extensions that prepare request_options (e.g., verbosity, reasoning)

    # Prefix for flat UI keys
    FLAT_KEY_PREFIX: str = "request_options__"

    # ---- Config / UI ----
    @staticmethod
    def _normalize_ui_leaf_type(ui_spec: Any) -> str | None:
        if isinstance(ui_spec, list):
            options = [str(v) for v in ui_spec if isinstance(v, str)]
            return "select" if options else None
        if isinstance(ui_spec, str) and ui_spec == "string":
            return "text"
        if isinstance(ui_spec, str) and ui_spec == "number":
            return "number"
        if isinstance(ui_spec, str) and ui_spec in {"boolean", "checkbox"}:
            return "checkbox"
        return None

    @staticmethod
    def _nested_value(options: Dict[str, Any], path: List[str]) -> tuple[bool, Any]:
        current: Any = options
        for part in path:
            if not isinstance(current, dict) or part not in current:
                return False, None
            current = current[part]
        return True, current

    @staticmethod
    def _flat_key_from_path(path: List[str], key_prefix: str) -> str:
        return f"{key_prefix}{'__'.join(path)}"

    @staticmethod
    def _config_path_from_path(path: List[str]) -> str:
        return f"request_options.{'.'.join(path)}"

    @staticmethod
    def _label_from_path(path: List[str]) -> str:
        return " ".join(part.replace("_", " ").title() for part in path)

    @classmethod
    def _build_ui_element(
        cls,
        path: List[str],
        ui_spec: Any,
        request_options: Dict[str, Any],
        key_prefix: str,
    ) -> Dict[str, Any] | None:
        ui_type = cls._normalize_ui_leaf_type(ui_spec)
        if ui_type is None:
            return None

        element: Dict[str, Any] = {
            "type": ui_type,
            "key": cls._flat_key_from_path(path, key_prefix),
            "label": cls._label_from_path(path),
            "config_path": cls._config_path_from_path(path),
        }

        if ui_type == "select":
            options = [
                {"value": str(v), "label": str(v)}
                for v in ui_spec
                if isinstance(v, str)
            ]
            if not options:
                return None
            element["options"] = options

        found_default, default_value = cls._nested_value(request_options, path)
        if found_default:
            element["default"] = default_value

        return element

    @staticmethod
    def _set_nested_value(target: Dict[str, Any], path: List[str], value: Any) -> None:
        current = target
        for part in path[:-1]:
            child = current.get(part)
            if not isinstance(child, dict):
                child = {}
                current[part] = child
            current = child
        current[path[-1]] = value

    @classmethod
    def _deep_merge(cls, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        merged: Dict[str, Any] = dict(base)
        for key, value in overlay.items():
            existing = merged.get(key)
            if isinstance(existing, dict) and isinstance(value, dict):
                merged[key] = cls._deep_merge(existing, value)
            elif isinstance(value, dict):
                merged[key] = cls._deep_merge({}, value)
            else:
                merged[key] = value
        return merged

    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema for this feature's configuration.

        Keys used by this feature:
        - ``request_options``: arbitrary mapping merged into request payload.
        - ``request_options_ui``: declarative UI element definitions that
          generate flat config keys like ``request_options__temperature``.
        """

        # Base schema with the two main keys
        schema: Dict[str, Any] = {
            "request_options": {
                "type": "object",
                "default": {},
                "description": (
                    "Additional request JSON options merged into the provider "
                    "payload during initialize_request. Keys override any "
                    "existing payload values."
                ),
            },
            "request_options_ui": {
                "type": "object",
                "default": {},
                "description": (
                    "Declarative UI element definitions that generate flat "
                    "config keys. Each key names a request_options field. "
                    "Array values create select dropdowns, 'string' creates "
                    "text input, 'number' creates number input, and "
                    "'boolean'/'checkbox' creates a checkbox. Values may "
                    "also be nested objects. Generated flat keys use the "
                    "prefix 'request_options__'."
                ),
                "additionalProperties": {
                    "oneOf": [
                        {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Options for a select dropdown",
                        },
                        {
                            "type": "string",
                            "enum": ["string", "number", "boolean", "checkbox"],
                            "description": (
                                "Input type: 'string' for text, 'number' for numeric, "
                                "'boolean'/'checkbox' for booleans"
                            ),
                        },
                        {
                            "type": "object",
                            "description": "Nested request_options_ui subtree",
                        },
                    ]
                },
            },
        }

        return schema

    @staticmethod
    def _generate_ui_elements_from_options(
        options_config: Dict[str, Any],
        key_prefix: str = "request_options__",
        path_prefix: Optional[List[str]] = None,
        request_options: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate UI elements from request_options_ui config.

        Args:
            options_config: Dict mapping keys to:
                - list of strings → select dropdown
                - "string" → text input
                - "number" → number input
                - "boolean"/"checkbox" → checkbox
                - nested dicts containing the same leaf forms
            key_prefix: Prefix for generated element keys
            path_prefix: Current nested request_options path
            request_options: Nested default values from config["request_options"]

        Returns:
            List of UI element dictionaries with flat keys for get_ui_elements().
        """
        elements: List[Dict[str, Any]] = []
        path_prefix = list(path_prefix or [])
        request_options = request_options if isinstance(request_options, dict) else {}

        for key, value in (options_config or {}).items():
            if not isinstance(key, str) or not key:
                continue

            path = [*path_prefix, key]
            if isinstance(value, dict):
                elements.extend(
                    RequestOptionsFeature._generate_ui_elements_from_options(
                        value,
                        key_prefix=key_prefix,
                        path_prefix=path,
                        request_options=request_options,
                    )
                )
                continue

            element = RequestOptionsFeature._build_ui_element(
                path,
                value,
                request_options=request_options,
                key_prefix=key_prefix,
            )
            if element is not None:
                elements.append(element)

        return elements

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate UI elements from request_options_ui config.

        Elements have flat keys like "request_options__temperature".
        """
        cfg = config or {}
        options_ui = cfg.get("request_options_ui")

        if not isinstance(options_ui, dict):
            return []

        request_options = cfg.get("request_options")
        return self._generate_ui_elements_from_options(
            options_ui,
            key_prefix=self.FLAT_KEY_PREFIX,
            request_options=request_options if isinstance(request_options, dict) else {},
        )

    # Uses adapter default get_models (no-op on models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify this feature for dependency resolution."""
        return ["feature:request_options"]

    def required_tags(self) -> List[str]:
        """This feature does not require any specific tags."""
        return []

    # ---- Lifecycle ----
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Merge config into shared state, extracting flat UI keys.

        Flat keys like "request_options__temperature" are extracted and
        merged into "request_options". The flat keys are removed from the
        resulting config to keep the state clean.

        The plugin itself remains stateless; request options are read from
        ``state["config"]`` during :meth:`initialize_request`.
        """
        # Extract flat keys and build a nested request_options overlay.
        overlay: Dict[str, Any] = {}
        prefix = self.FLAT_KEY_PREFIX

        for key, value in config.items():
            if key.startswith(prefix):
                option_name = key[len(prefix) :]
                path = [segment for segment in option_name.split("__") if segment]
                if path:
                    self._set_nested_value(overlay, path, value)

        existing_raw = config.get("request_options")
        existing_options = existing_raw if isinstance(existing_raw, dict) else {}

        # Merge nested overrides into existing options without clobbering
        # sibling keys inside the same provider-specific object.
        merged_options = self._deep_merge(existing_options, overlay)

        # Build new config without flat keys but with merged request_options
        new_config: Dict[str, Any] = {
            k: v for k, v in config.items() if not k.startswith(prefix)
        }
        new_config["request_options"] = merged_options

        return {**state, "config": {**state.get("config", {}), **new_config}}

    # ---- Stateless transforms (no-ops for this feature) ----
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return messages

    # ---- Request initialization ----
    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Merge ``request_options`` from config into request payload.

        Works best with the OpenAI-compatible provider, which expects
        ``state["request"]`` to contain ``{"url", "payload", "headers", "timeout"}``.
        If either the request structure or ``request_options`` are missing,
        the state and native_messages are returned unchanged.
        """
        config = state.get("config", {})
        options = config.get("request_options")
        if not isinstance(options, dict) or not options:
            return native_messages, state

        request = state.get("request") or {}
        payload = dict(request.get("payload", {}))

        # Merge arbitrary request options, letting them override existing keys.
        merged_payload = {**payload, **options}

        new_state: Dict[str, Any] = {
            **state,
            "request": {**request, "payload": merged_payload},
        }
        return native_messages, new_state

    # ---- Finalize (no-op) ----
    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state
